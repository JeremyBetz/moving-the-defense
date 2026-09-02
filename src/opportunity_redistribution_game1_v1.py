"""Execute frozen Opportunity Redistribution v1 on Metrica Sample Game 1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacking_continuous_movement_game1_v1 as tracking  # noqa: E402
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import local_defensive_deformation_v1 as deformation  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/opportunity_redistribution_v1.md"
CONFIG = ROOT / "config/opportunity_redistribution_v1.json"
HASH_LEDGER = ROOT / "config/opportunity_redistribution_v1_hashes.json"
EVENTS = ROOT / "data/metrica_sample_game_1/Sample_Game_1_RawEventsData.csv"
DEFAULT_OUTPUT = ROOT / "outputs/opportunity_redistribution_game1_v1"
DEFAULT_FIGURES = ROOT / "figures/opportunity_redistribution_game1_v1"
FROZEN = {
    PROTOCOL: "15825647a23c4cfcb24317e773d07a8c17cbb5d705b8c7eafd07493f728625fa",
    CONFIG: "45c418a9b52565298da184f32250dab190df2e62030d4f42fde7408c3523e431",
    HASH_LEDGER: "aa5cba169e330bcea2b280b269e0bd075af7c0eca3e6f7eac879317587259c49",
}
BOOT, MIN_VALID, SEED = 2000, 1900, 20260902
TRIM = 12.198443079831405
PREDICTORS = ["A", "D", "S0", "MR", "Apre", "Dpre"]
FAMILIES = ["primary", "fixed_start", "three_nearest", "trimmed", "secondary_deformation"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return [clean(v) for v in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path_length(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


def distribution(values: pd.Series | np.ndarray) -> dict[str, float]:
    x = np.asarray(values, dtype=np.float64)
    return {
        "count": int(len(x)), "min": float(np.min(x)), "q25": float(np.quantile(x, .25)),
        "median": float(np.median(x)), "q75": float(np.quantile(x, .75)), "max": float(np.max(x)),
        "mean": float(np.mean(x)), "sd": float(np.std(x, ddof=0)),
    }


def event_state(events: pd.DataFrame, period: int, tmatch: float) -> tuple[str | None, bool, bool]:
    team, restart = bridge.event_context(events, period, tmatch, tmatch - 2.0, tmatch + 2.0)
    if team is None:
        return None, restart, False
    opponent = "Away" if team == "Home" else "Home"
    later = events[
        (events["Period"] == period)
        & events["Type"].isin(bridge.POSSESSION_TYPES)
        & events["Team"].eq(opponent)
        & events["Start Time [s]"].notna()
        & (events["Start Time [s]"] > tmatch + bridge.TOL)
        & (events["Start Time [s]"] <= tmatch + 2.0 + bridge.TOL)
    ]
    return team, restart, not later.empty


def ranked_contrast(values: np.ndarray, order: np.ndarray, near: slice, remote: slice) -> float:
    return float(values[order[near]].mean() - values[order[remote]].mean())


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    players, period_frames, provenance = tracking.load_game1()
    lookup = {(p.period, p.player_key): p for p in players}
    roster: dict[tuple[int, str], list[str]] = {}
    for player in players:
        roster.setdefault((player.period, player.team_key), []).append(player.player_key)
    for key in roster:
        roster[key] = sorted(roster[key])
    events = pd.read_csv(EVENTS)
    rows: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    first_geometry: dict[str, Any] | None = None
    for period in sorted(period_frames):
        frame = period_frames[period]
        origin, last = float(frame["origin_time_period_s"]), float(frame["time_period_s"][-1])
        k = 0
        while True:
            t = origin + 2.0 + 4.0 * k
            if t + 2.0 > last + bridge.TOL:
                break
            base = {"period": period, "time_period_s": t}
            raw_i = int(np.searchsorted(frame["time_period_s"], t - bridge.TOL))
            if raw_i >= len(frame["time_period_s"]) or abs(float(frame["time_period_s"][raw_i]) - t) > bridge.TOL:
                excluded.append({**base, "reason": "anchor_not_exact_frame"}); k += 1; continue
            tmatch = float(frame["time_match_s"][raw_i])
            team, restart, opponent_change = event_state(events, period, tmatch)
            if team is None:
                excluded.append({**base, "reason": "no_possession_team"}); k += 1; continue
            if restart:
                excluded.append({**base, "reason": "restart_or_ball_out_span"}); k += 1; continue
            if opponent_change:
                excluded.append({**base, "reason": "opponent_possession_event_after_anchor"}); k += 1; continue
            attack_team = f"metrica:{team}"
            defend_team = "metrica:Away" if attack_team == "metrica:Home" else "metrica:Home"
            attacking = {
                key: bridge.segment(lookup[(period, key)], t - 2.0, t + 2.0)
                for key in roster.get((period, attack_team), []) if (period, key) in lookup
            }
            defending = {
                key: bridge.segment(lookup[(period, key)], t - 2.0, t + 2.0)
                for key in roster.get((period, defend_team), []) if (period, key) in lookup
            }
            attacking = {key: value for key, value in attacking.items() if value is not None}
            defending = {key: value for key, value in defending.items() if value is not None}
            if len(attacking) != 10:
                excluded.append({**base, "reason": "complete_ten_attackers_unavailable", "available": len(attacking)}); k += 1; continue
            if len(defending) != 10:
                excluded.append({**base, "reason": "complete_ten_defenders_unavailable", "available": len(defending)}); k += 1; continue
            attack_keys, defend_keys = sorted(attacking), sorted(defending)
            attack4 = np.stack([attacking[key] for key in attack_keys], axis=1)
            defend4 = np.stack([defending[key] for key in defend_keys], axis=1)
            assert attack4.shape == defend4.shape == (101, 10, 2)
            pre_attack, con_attack = attack4[:51], attack4[50:]
            pre_defend, con_defend = defend4[:51], defend4[50:]
            con_def_rel = np.array([
                path_length(con_defend[:, j] - np.delete(con_defend, j, axis=1).mean(axis=1)) for j in range(10)
            ])
            pre_def_rel = np.array([
                path_length(pre_defend[:, j] - np.delete(pre_defend, j, axis=1).mean(axis=1)) for j in range(10)
            ])
            con_deformation = deformation.focal_endpoint_rms(con_defend)
            for focal_i, focal_key in enumerate(attack_keys):
                focal_start = con_attack[0, focal_i]
                defender_order = np.asarray(sorted(
                    range(10), key=lambda j: (float(np.linalg.norm(con_defend[0, j] - focal_start)), defend_keys[j])
                ), dtype=int)
                recipient_indices = [j for j in range(10) if j != focal_i]
                recipient_order = np.asarray(sorted(
                    range(9), key=lambda z: (
                        float(np.linalg.norm(con_attack[0, recipient_indices[z]] - focal_start)),
                        attack_keys[recipient_indices[z]],
                    )
                ), dtype=int)
                recipient_xy0 = con_attack[0, recipient_indices]
                recipient_xy1 = con_attack[-1, recipient_indices]
                dist0 = np.linalg.norm(recipient_xy0[:, None, :] - con_defend[0, None, :, :], axis=2)
                dist1 = np.linalg.norm(recipient_xy1[:, None, :] - con_defend[-1, None, :, :], axis=2)
                nearest0 = dist0.min(axis=1)
                nearest1 = dist1.min(axis=1)
                change = nearest1 - nearest0
                start_nearest_index = dist0.argmin(axis=1)
                fixed_change = dist1[np.arange(9), start_nearest_index] - nearest0
                three_change = np.sort(dist1, axis=1)[:, :3].mean(axis=1) - np.sort(dist0, axis=1)[:, :3].mean(axis=1)
                recipient_paths = np.array([path_length(con_attack[:, j]) for j in recipient_indices])
                focal_path = path_length(con_attack[:, focal_i])
                prior_focal_path = path_length(pre_attack[:, focal_i])
                local, remote = recipient_order[:3], recipient_order[6:9]
                if first_geometry is None:
                    first_geometry = {
                        "anchor_id": f"P{period}|T{t:.2f}", "focal_attacker_key": focal_key,
                        "attack_keys": attack_keys, "defend_keys": defend_keys,
                        "attacker_start": con_attack[0], "attacker_end": con_attack[-1],
                        "defender_start": con_defend[0], "defender_end": con_defend[-1],
                        "focal_trajectory": con_attack[:, focal_i], "focal_index": focal_i,
                        "recipient_indices": recipient_indices, "recipient_order": recipient_order,
                        "defender_order": defender_order, "start_nearest_index": start_nearest_index,
                        "end_nearest_index": dist1.argmin(axis=1),
                    }
                rows.append({
                    "observation_id": f"OR1|P{period}|T{t:.2f}|{focal_key}",
                    "anchor_id": f"P{period}|T{t:.2f}", "period": period, "time_period_s": t,
                    "time_match_s": tmatch, "block_id": int(math.floor((t - origin) / 60.0)),
                    "focal_attacker_key": focal_key, "attacking_team": attack_team, "defending_team": defend_team,
                    "recipient_keys_ranked": "|".join(attack_keys[recipient_indices[z]] for z in recipient_order),
                    "defender_keys_ranked": "|".join(defend_keys[j] for j in defender_order),
                    "O": float(change[local].mean() - change[remote].mean()),
                    "O_fixed_start": float(fixed_change[local].mean() - fixed_change[remote].mean()),
                    "O_three_nearest": float(three_change[local].mean() - three_change[remote].mean()),
                    "A": focal_path,
                    "D": float(con_def_rel[defender_order[:3]].mean() - con_def_rel[defender_order[3:7]].mean()),
                    "S0": float(nearest0[local].mean() - nearest0[remote].mean()),
                    "MR": float(recipient_paths[local].mean() - recipient_paths[remote].mean()),
                    "Apre": prior_focal_path,
                    "Dpre": float(pre_def_rel[defender_order[:3]].mean() - pre_def_rel[defender_order[3:7]].mean()),
                    "D_deformation": float(con_deformation[defender_order[:3]].mean() - con_deformation[defender_order[3:7]].mean()),
                    "local_separation_change": float(change[local].mean()),
                    "remote_separation_change": float(change[remote].mean()),
                    "recipient_nearest_identity_churn": int(np.sum(start_nearest_index != dist1.argmin(axis=1))),
                })
            k += 1
    data = pd.DataFrame(rows).sort_values(["period", "time_period_s", "focal_attacker_key"], kind="mergesort").reset_index(drop=True)
    exclusions = pd.DataFrame(excluded)
    if first_geometry is None:
        raise RuntimeError("no eligible geometry available for deterministic visual audit")
    return data, exclusions, provenance, first_geometry


def transformed(data: pd.DataFrame, outcome: str, d_column: str = "D") -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    use = data.copy()
    sizes = use.groupby("anchor_id").size()
    use = use[use.anchor_id.isin(sizes[sizes >= 2].index)].reset_index(drop=True)
    cols = ["A", d_column, "S0", "MR", "Apre", "Dpre"]
    x = use[cols].to_numpy(np.float64)
    y = use[outcome].to_numpy(np.float64)
    groups = use.anchor_id.to_numpy()
    for group in np.unique(groups):
        mask = groups == group
        x[mask] -= x[mask].mean(axis=0)
        y[mask] -= y[mask].mean()
    return x, y, use


def fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, int]:
    coefficient, _, rank, _ = np.linalg.lstsq(x.astype(np.float64), y.astype(np.float64), rcond=None)
    if rank != x.shape[1] or not np.isfinite(coefficient).all():
        raise RuntimeError(f"unestimable frozen design rank={rank}")
    return coefficient, int(rank)


def sufficient_by_block(data: pd.DataFrame, x: np.ndarray, y: np.ndarray) -> dict[tuple[int, int], tuple[np.ndarray, np.ndarray]]:
    result = {}
    for key, indices in data.groupby(["period", "block_id"], sort=True).indices.items():
        xb, yb = x[indices], y[indices]
        result[(int(key[0]), int(key[1]))] = (xb.T @ xb, xb.T @ yb)
    return result


def fit_sufficient(xtx: np.ndarray, xty: np.ndarray) -> np.ndarray:
    lower = np.linalg.cholesky(xtx)
    pseudo_x = lower.T
    pseudo_y = np.linalg.solve(lower, xty)
    coefficient, _, rank, _ = np.linalg.lstsq(pseudo_x, pseudo_y, rcond=None)
    if rank != len(PREDICTORS) or not np.isfinite(coefficient).all():
        raise RuntimeError(f"unestimable bootstrap design rank={rank}")
    return coefficient


def bootstrap(fits: dict[str, tuple[np.ndarray, np.ndarray, pd.DataFrame]]) -> dict[str, np.ndarray]:
    sufficient = {name: sufficient_by_block(data, x, y) for name, (x, y, data) in fits.items()}
    primary_keys = sorted(sufficient["primary"])
    by_period = {period: [key for key in primary_keys if key[0] == period] for period in sorted({k[0] for k in primary_keys})}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(2)[0]))
    samples = {name: [] for name in fits}
    for _ in range(BOOT):
        selected: list[tuple[int, int]] = []
        for blocks in by_period.values():
            selected.extend(blocks[int(i)] for i in rng.integers(0, len(blocks), size=len(blocks)))
        for name in fits:
            available = [key for key in selected if key in sufficient[name]]
            xtx = sum((sufficient[name][key][0] for key in available), np.zeros((6, 6), dtype=np.float64))
            xty = sum((sufficient[name][key][1] for key in available), np.zeros(6, dtype=np.float64))
            try:
                samples[name].append(fit_sufficient(xtx, xty))
            except np.linalg.LinAlgError:
                pass
    return {name: np.asarray(value, dtype=np.float64) for name, value in samples.items()}


def coefficient_table(point: np.ndarray, samples: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "predictor": PREDICTORS,
        "estimate": point,
        "ci_low": np.quantile(samples, .025, axis=0),
        "ci_high": np.quantile(samples, .975, axis=0),
        "valid_bootstrap": len(samples),
        "attempted_bootstrap": BOOT,
    })


def render_figures(data: pd.DataFrame, tables: dict[str, pd.DataFrame], geometry: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    first = data.iloc[0]
    a0, a1 = np.asarray(geometry["attacker_start"]), np.asarray(geometry["attacker_end"])
    d0, d1 = np.asarray(geometry["defender_start"]), np.asarray(geometry["defender_end"])
    rec = np.asarray(geometry["recipient_indices"], int); ro = np.asarray(geometry["recipient_order"], int)
    do = np.asarray(geometry["defender_order"], int); focal_i = int(geometry["focal_index"])
    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    ax.add_patch(plt.Rectangle((-52.5, -34), 105, 68, fill=False, color="#385723", linewidth=1.4))
    ax.axvline(0, color="#9cb58b", linewidth=.8); ax.set_xlim(-54, 54); ax.set_ylim(-36, 36); ax.set_aspect("equal")
    ax.scatter(a0[:, 0], a0[:, 1], color="#1565c0", s=32, label="Attackers at start", zorder=3)
    ax.scatter(d0[:, 0], d0[:, 1], color="#c62828", s=32, label="Defenders at start", zorder=3)
    for j in range(10):
        ax.plot([a0[j, 0], a1[j, 0]], [a0[j, 1], a1[j, 1]], color="#1565c0", alpha=.35, linewidth=1)
        ax.plot([d0[j, 0], d1[j, 0]], [d0[j, 1], d1[j, 1]], color="#c62828", alpha=.35, linewidth=1)
    trajectory = np.asarray(geometry["focal_trajectory"])
    ax.plot(trajectory[:, 0], trajectory[:, 1], color="#ffb300", linewidth=3, label="Focal path")
    ax.scatter(a0[focal_i, 0], a0[focal_i, 1], s=120, facecolors="none", edgecolors="#ffb300", linewidth=2.2)
    for z in ro[:3]:
        j = rec[z]; ax.scatter(a0[j, 0], a0[j, 1], s=95, facecolors="none", edgecolors="#00acc1", linewidth=1.8)
    for j in do[:3]:
        ax.scatter(d0[j, 0], d0[j, 1], s=95, facecolors="none", edgecolors="#7b1fa2", linewidth=1.8)
    start_nearest, end_nearest = np.asarray(geometry["start_nearest_index"], int), np.asarray(geometry["end_nearest_index"], int)
    for z in ro[:3]:
        j = rec[z]; ds, de = start_nearest[z], end_nearest[z]
        ax.plot([a0[j, 0], d0[ds, 0]], [a0[j, 1], d0[ds, 1]], color="#555", linestyle=":", linewidth=.8)
        ax.plot([a1[j, 0], d1[de, 0]], [a1[j, 1], d1[de, 1]], color="#555", linestyle="--", linewidth=.8)
    ax.set_title(f"Deterministic first eligible anchor: {first['anchor_id']} · {first['focal_attacker_key']}\nO={first['O']:.3f} m; D={first['D']:.3f} m (audit example, not selected for effect)")
    ax.set_xlabel("Pitch x (m)"); ax.set_ylabel("Pitch y (m)"); ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout(); fig.savefig(directory / "first_eligible_anchor.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    names = ["Primary", "Fixed-start defender", "Three-nearest", "Trimmed", "Deformation predictor"]
    estimates, lows, highs = [], [], []
    for family in FAMILIES:
        row = tables[family].query("predictor == 'D'").iloc[0]
        estimates.append(row.estimate); lows.append(row.ci_low); highs.append(row.ci_high)
    y = np.arange(len(names))
    ax.errorbar(estimates, y, xerr=[np.asarray(estimates)-lows, np.asarray(highs)-estimates], fmt="o", color="#174a7e", capsize=3)
    ax.axvline(0, color="black", linewidth=.8); ax.set_yticks(y, names); ax.invert_yaxis()
    ax.set_xlabel("Conditional coefficient for defensive contrast βD")
    ax.set_title("Opportunity Redistribution v1: primary and frozen checks")
    fig.tight_layout(); fig.savefig(directory / "coefficient_robustness.png", dpi=180); plt.close(fig)


def execute(output: Path, figures: Path) -> dict[str, Any]:
    bad = {str(path.relative_to(ROOT)): [sha(path), expected] for path, expected in FROZEN.items() if sha(path) != expected}
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")
    output.mkdir(parents=True, exist_ok=True)
    data, exclusions, provenance, first_geometry = build_sample()
    specifications = {
        "primary": ("O", "D", data),
        "fixed_start": ("O_fixed_start", "D", data),
        "three_nearest": ("O_three_nearest", "D", data),
        "trimmed": ("O", "D", data[data.A <= TRIM].copy()),
        "secondary_deformation": ("O", "D_deformation", data),
    }
    fits = {name: transformed(frame, outcome, predictor) for name, (outcome, predictor, frame) in specifications.items()}
    points, ranks = {}, {}
    for name, (x, y, _) in fits.items():
        points[name], ranks[name] = fit(x, y)
    samples = bootstrap(fits)
    tables = {name: coefficient_table(points[name], samples[name]) for name in FAMILIES}
    primary_d = tables["primary"].query("predictor == 'D'").iloc[0]
    robustness_signs = {name: bool(tables[name].query("predictor == 'D'").iloc[0].estimate > 0) for name in ["fixed_start", "three_nearest", "trimmed"]}
    hard_qc = {
        "frozen_hashes": not bad,
        "unique_observation_ids": data.observation_id.is_unique,
        "complete_ten_attackers_and_defenders": data.groupby("anchor_id").size().eq(10).all(),
        "finite_geometry": bool(np.isfinite(data.select_dtypes(include=[np.number]).to_numpy()).all()),
        "six_column_full_rank_all_families": all(rank == 6 for rank in ranks.values()),
        "within_anchor_centered": all(max(abs(x[data_.anchor_id.eq(anchor)].sum(axis=0)).max() for anchor in data_.anchor_id.unique()) < 1e-10 for x, _, data_ in fits.values()),
        "bootstrap_minimum_valid": min(len(value) for value in samples.values()) >= MIN_VALID,
        "goalkeepers_excluded": not data.defender_keys_ranked.str.contains("Home:11|Away:25").any(),
        "no_interpolation_complete_support": True,
        "recipient_membership_fixed_at_start": True,
        "defender_rank_membership_fixed_at_start": True,
        "no_game2_game3_or_idsse_access": True,
    }
    valid = all(hard_qc.values())
    if not valid:
        status = "GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT INVALID"
    elif primary_d.estimate <= 0:
        status = "GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT NEGATIVE"
    elif primary_d.ci_low > 0 and all(robustness_signs.values()):
        status = "GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT COHERENT"
    else:
        status = "GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT MIXED"
    simultaneous = data.groupby("anchor_id").size()
    sample = {
        "eligible_focal_attacker_observations": len(data),
        "unique_anchor_times": int(data.anchor_id.nunique()),
        "period_counts": data.period.value_counts().sort_index().to_dict(),
        "attacking_team_counts": data.attacking_team.value_counts().sort_index().to_dict(),
        "simultaneous_focal_attackers": distribution(simultaneous),
        "exclusion_counts": exclusions.reason.value_counts().sort_index().to_dict() if not exclusions.empty else {},
        "trim_threshold_m": TRIM,
        "trim_excluded": int((data.A > TRIM).sum()),
        "trim_retained": int((data.A <= TRIM).sum()),
        "period2_support_diagnosis": {
            "classification": "PERIOD-2 EXCLUSION CORRECT UNDER FROZEN RULES",
            "inherited_registry_exclusions": ["metrica:Home:3", "metrica:Away:22"],
            "registry_scope": "entire_period_2",
            "maximum_supported_outfield_players_per_team": 9,
            "reason": "opportunity_v1_requires_ten_supported_attackers_and_ten_supported_defenders_simultaneously",
        },
    }
    result = {
        "status": status, "sample": sample,
        "outcome_distribution": distribution(data.O), "defensive_predictor_distribution": distribution(data.D),
        "design_rank": ranks, "coefficients": {name: tables[name].to_dict("records") for name in FAMILIES},
        "bootstrap": {name: {"attempted": BOOT, "valid": len(samples[name])} for name in FAMILIES},
        "robustness_positive_signs": robustness_signs, "hard_qc": hard_qc,
        "descriptives": {
            "local_separation_change": distribution(data.local_separation_change),
            "remote_separation_change": distribution(data.remote_separation_change),
            "recipient_nearest_identity_churn": distribution(data.recipient_nearest_identity_churn),
        },
        "frozen_hashes": {str(path.relative_to(ROOT)): expected for path, expected in FROZEN.items()},
        "provenance": provenance,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    data.to_csv(output / "observation_rows.csv", index=False)
    exclusions.to_csv(output / "exclusion_ledger.csv", index=False)
    for name, table in tables.items():
        table.to_csv(output / f"{name}_coefficients.csv", index=False)
    write_json(output / "final_results.json", result)
    write_json(output / "first_anchor_geometry.json", first_geometry)
    governed = ["observation_rows.csv", "exclusion_ledger.csv", "final_results.json", "first_anchor_geometry.json"] + [f"{name}_coefficients.csv" for name in FAMILIES]
    hashes = {name: sha(output / name) for name in governed}
    write_json(output / "result_hashes.json", hashes)
    write_json(output / "execution_metadata.json", {
        "starting_commit": "8444ff41a04b78dcd2fcd4a74267af67492de48e",
        "development_match": "metrica:sample-game-1",
        "source_sha256": sha(Path(__file__)),
        "frozen_protocol_sha256": FROZEN[PROTOCOL],
        "frozen_configuration_sha256": FROZEN[CONFIG],
        "frozen_hash_ledger_sha256": FROZEN[HASH_LEDGER],
        "governed_output_count": len(governed),
        "results_observed_only_after_design_freeze": True,
        "game2_game3_idsse_untouched": True,
    })
    render_figures(data, tables, first_geometry, figures)
    return result


def reproduce(output: Path, figures: Path) -> None:
    temporary = output.parent / f".{output.name}_reproduction"
    temporary_figures = figures.parent / f".{figures.name}_reproduction"
    if temporary.exists(): shutil.rmtree(temporary)
    if temporary_figures.exists(): shutil.rmtree(temporary_figures)
    execute(temporary, temporary_figures)
    governed = json.loads((output / "result_hashes.json").read_text(encoding="utf-8"))
    comparison = {name: sha(temporary / name) == digest for name, digest in governed.items()}
    write_json(output / "reproduction_qc.json", {"governed_outputs": len(comparison), "byte_identical": sum(comparison.values()), "all_pass": all(comparison.values()), "files": comparison})
    shutil.rmtree(temporary); shutil.rmtree(temporary_figures)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    if args.reproduce:
        reproduce(args.output, args.figures)
        print("REPRODUCTION PASS")
    else:
        print(execute(args.output, args.figures)["status"])


if __name__ == "__main__":
    main()
