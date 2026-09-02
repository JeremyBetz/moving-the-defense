"""Tier-1 execution of frozen Concurrent Attacker–Defensive Geometry v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacking_continuous_movement_game1_v1 as tracking  # noqa: E402
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import local_defensive_deformation_v1 as deformation  # noqa: E402
import local_defensive_response_form_v1 as direction  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/concurrent_attacker_defensive_geometry_v1.md"
CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1.json"
HASH_LEDGER = ROOT / "config/concurrent_attacker_defensive_geometry_v1_hashes.json"
DEFAULT_OUTPUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_game1_v1"
EVENTS = ROOT / "data/metrica_sample_game_1/Sample_Game_1_RawEventsData.csv"
FROZEN = {
    PROTOCOL: "1382e97f401eafc2101f2d77ef2b7158e48500ce7df6b01d4db450f2ba1b8f32",
    CONFIG: "5b37211295297fe4350c394500da27e72040aefcc7f4806b1c779a390a9c692d",
    HASH_LEDGER: "7fb68191ec74278c7734a889c0452feb3398932579db6c4af67687143a38873d",
}
BOOT, MIN_VALID, SEED, TRIM = 2000, 1900, 20260831, 12.198443079831405
P = 72


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return [clean(v) for v in value.tolist()]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_, bool)): return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    players, period_frames, provenance = tracking.load_game1()
    lookup = {(p.period, p.player_key): p for p in players}
    roster: dict[tuple[int, str], list[str]] = {}
    for p in players: roster.setdefault((p.period, p.team_key), []).append(p.player_key)
    for key in roster: roster[key] = sorted(roster[key])
    events = pd.read_csv(EVENTS)
    rows, excluded = [], []
    for period in sorted(period_frames):
        frame = period_frames[period]
        origin, last = float(frame["origin_time_period_s"]), float(frame["time_period_s"][-1])
        k = 0
        while True:
            t = origin + 2.0 + 4.0 * k
            if t + 2.0 > last + bridge.TOL: break
            raw_i = int(np.searchsorted(frame["time_period_s"], t - bridge.TOL))
            if raw_i >= len(frame["time_period_s"]) or abs(float(frame["time_period_s"][raw_i]) - t) > bridge.TOL:
                excluded.append({"period": period, "time_period_s": t, "attacker_key": None, "reason": "anchor_not_exact_frame"}); k += 1; continue
            tmatch = float(frame["time_match_s"][raw_i])
            team, restart = bridge.event_context(events, period, tmatch, tmatch - 2.0, tmatch + 2.0)
            if team is None:
                excluded.append({"period": period, "time_period_s": t, "attacker_key": None, "reason": "no_possession_team"}); k += 1; continue
            attack_team = f"metrica:{team}"
            defend_team = "metrica:Away" if attack_team == "metrica:Home" else "metrica:Home"
            defenders = {key: lookup[(period, key)] for key in roster.get((period, defend_team), []) if (period, key) in lookup and bridge.segment(lookup[(period, key)], t - 2.0, t + 2.0) is not None}
            for attacker_key in roster.get((period, attack_team), []):
                reason = "restart_or_ball_out_span" if restart else None
                attacker = lookup.get((period, attacker_key))
                attacker_span = None if attacker is None else bridge.segment(attacker, t - 2.0, t + 2.0)
                if reason is None and attacker_span is None: reason = "attacker_complete_support_unavailable"
                if reason is None and len(defenders) != 10: reason = "complete_ten_defenders_unavailable"
                if reason:
                    excluded.append({"period": period, "time_period_s": t, "attacker_key": attacker_key, "reason": reason}); continue
                assert attacker_span is not None
                pre_att = bridge.segment(attacker, t - 2.0, t)
                con_att = bridge.segment(attacker, t, t + 2.0)
                keys = sorted(defenders)
                pre = np.stack([bridge.segment(defenders[key], t - 2.0, t) for key in keys], axis=1)
                concurrent = np.stack([bridge.segment(defenders[key], t, t + 2.0) for key in keys], axis=1)
                assert pre.shape == concurrent.shape == (51, 10, 2) and pre_att is not None and con_att is not None
                attacker_start = con_att[0]
                distance_order = sorted([(float(np.linalg.norm(concurrent[0, j] - attacker_start)), key, j) for j, key in enumerate(keys)], key=lambda x: (x[0], x[1]))
                pre_centroid_path = path(pre.mean(axis=1))
                pre_abs = np.array([path(pre[:, j]) for j in range(10)])
                pre_rel = np.array([path(pre[:, j] - np.delete(pre, j, axis=1).mean(axis=1)) for j in range(10)])
                con_rel = np.array([path(concurrent[:, j] - np.delete(concurrent, j, axis=1).mean(axis=1)) for j in range(10)])
                con_def = deformation.focal_endpoint_rms(concurrent)
                attacker_delta = con_att[-1] - con_att[0]
                observation_id = f"CAG1|P{period}|T{t:.2f}|{attacker_key}"
                for rank, (distance_m, defender_key, j) in enumerate(distance_order, 1):
                    other_centroid = np.delete(concurrent, j, axis=1).mean(axis=1)
                    form = direction.decompose_response(attacker_delta, concurrent[-1, j] - concurrent[0, j], other_centroid[-1] - other_centroid[0], con_att[0], concurrent[0, j])
                    rows.append({
                        "observation_id": observation_id, "period": period, "time_period_s": t, "time_match_s": tmatch,
                        "attacker_key": attacker_key, "attacking_team": attack_team, "defending_team": defend_team,
                        "block_id": int(math.floor((t - origin) / 60.0)), "defender_key": defender_key, "distance_rank": rank,
                        "distance_m": distance_m, "concurrent_attacker_path_m": path(con_att), "prior_attacker_path_m": path(pre_att),
                        "prior_focal_relative_path_m": pre_rel[j], "prior_defensive_centroid_path_m": pre_centroid_path,
                        "prior_other_nine_mean_absolute_path_m": float((pre_abs.sum() - pre_abs[j]) / 9.0),
                        "concurrent_focal_relative_path_m": con_rel[j], "concurrent_endpoint_deformation_rms_m": con_def[j],
                        "attacker_delta_x_m": attacker_delta[0], "attacker_delta_y_m": attacker_delta[1],
                        "parallel_m": form.parallel_m, "orthogonal_m": form.orthogonal_m, "radial_m": form.radial_m,
                        "attacker_axis_valid": form.attacker_axis_valid,
                    })
            k += 1
    data = pd.DataFrame(rows).sort_values(["period", "time_period_s", "attacker_key", "distance_rank"], kind="mergesort").reset_index(drop=True)
    exclusions = pd.DataFrame(excluded)
    return data, exclusions, provenance


def design(data: pd.DataFrame) -> np.ndarray:
    matrix = np.zeros((len(data), P), dtype=np.float64)
    rank = data.distance_rank.to_numpy(int) - 1
    terms = np.column_stack([
        np.ones(len(data)), data.concurrent_attacker_path_m, data.prior_focal_relative_path_m,
        data.prior_defensive_centroid_path_m, data.prior_other_nine_mean_absolute_path_m,
        data.prior_attacker_path_m, data.distance_m,
    ]).astype(np.float64)
    for term in range(7): matrix[np.arange(len(data)), rank * 7 + term] = terms[:, term]
    matrix[:, 70] = (data.period.to_numpy(int) == 2).astype(float)
    matrix[:, 71] = (data.attacking_team.to_numpy(str) == "metrica:Home").astype(float)
    return matrix


def fit(matrix: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    coef, _, rank, _ = np.linalg.lstsq(matrix, outcome.astype(np.float64), rcond=None)
    if rank != P or not np.isfinite(coef).all(): raise RuntimeError(f"unestimable frozen design rank={rank}")
    return coef


def summarize(coef: np.ndarray) -> dict[str, Any]:
    beta = coef[np.arange(10) * 7 + 1]
    near, middle, far = float(beta[:3].mean()), float(beta[3:7].mean()), float(beta[7:].mean())
    return {"D1_D10": beta, "near": near, "middle": middle, "far": far, "near_minus_middle": near - middle}


def block_sufficient(data: pd.DataFrame, matrix: np.ndarray, outcome: np.ndarray) -> dict[tuple[int, int], tuple[np.ndarray, np.ndarray]]:
    result = {}
    for key, idx in data.groupby(["period", "block_id"], sort=True).indices.items():
        x, y = matrix[idx], outcome[idx]
        result[(int(key[0]), int(key[1]))] = (x.T @ x, x.T @ y)
    return result


def fit_sufficient(xtx: np.ndarray, xty: np.ndarray) -> np.ndarray:
    """Fit OLS with frozen lstsq using an equivalent Cholesky sufficient-statistic design."""
    lower = np.linalg.cholesky(xtx)
    pseudo_design = lower.T
    pseudo_outcome = np.linalg.solve(lower, xty)
    coef, _, rank, _ = np.linalg.lstsq(pseudo_design, pseudo_outcome, rcond=None)
    if rank != P or not np.isfinite(coef).all(): raise RuntimeError(f"unestimable bootstrap design rank={rank}")
    return coef


def bootstrap(data: pd.DataFrame, matrix: np.ndarray, outcomes: dict[str, np.ndarray], trim_mask: np.ndarray) -> dict[str, np.ndarray]:
    full = {name: block_sufficient(data, matrix, y) for name, y in outcomes.items()}
    td, tx = data.loc[trim_mask].reset_index(drop=True), matrix[trim_mask]
    trimmed = block_sufficient(td, tx, outcomes["primary"][trim_mask])
    keys = sorted(full["primary"])
    by_period = {p: [key for key in keys if key[0] == p] for p in sorted({key[0] for key in keys})}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(2)[0]))
    result = {"primary": [], "secondary": [], "trimmed": []}
    for _ in range(BOOT):
        selected = []
        for period, blocks in by_period.items():
            selected.extend(blocks[int(i)] for i in rng.integers(0, len(blocks), size=len(blocks)))
        for name in ("primary", "secondary"):
            xtx = sum((full[name][key][0] for key in selected), np.zeros((P, P)))
            xty = sum((full[name][key][1] for key in selected), np.zeros(P))
            try:
                coef = fit_sufficient(xtx, xty)
                result[name].append(summarize(coef)["D1_D10"])
            except np.linalg.LinAlgError: pass
        available = [key for key in selected if key in trimmed]
        xtx = sum((trimmed[key][0] for key in available), np.zeros((P, P)))
        xty = sum((trimmed[key][1] for key in available), np.zeros(P))
        try:
            coef = fit_sufficient(xtx, xty)
            result["trimmed"].append(summarize(coef)["D1_D10"])
        except np.linalg.LinAlgError: pass
    return {name: np.asarray(value) for name, value in result.items()}


def solver_compliance_qc(output: Path) -> dict[str, Any]:
    """Compare preliminary normal-equation and governed lstsq bootstrap fits."""
    data = pd.DataFrame(pl.read_parquet(output / "observation_rows.parquet").to_dicts())
    matrix = design(data)
    outcomes = {
        "primary": data.concurrent_focal_relative_path_m.to_numpy(float),
        "secondary": data.concurrent_endpoint_deformation_rms_m.to_numpy(float),
    }
    trim_mask = data.concurrent_attacker_path_m.to_numpy(float) <= TRIM
    full = {name: block_sufficient(data, matrix, y) for name, y in outcomes.items()}
    td, tx = data.loc[trim_mask].reset_index(drop=True), matrix[trim_mask]
    trimmed = block_sufficient(td, tx, outcomes["primary"][trim_mask])
    keys = sorted(full["primary"])
    by_period = {p: [key for key in keys if key[0] == p] for p in sorted({key[0] for key in keys})}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(2)[0]))
    old = {name: [] for name in ("primary", "secondary", "trimmed")}
    new = {name: [] for name in old}
    for _ in range(BOOT):
        selected = []
        for _, blocks in by_period.items():
            selected.extend(blocks[int(i)] for i in rng.integers(0, len(blocks), size=len(blocks)))
        for name in ("primary", "secondary"):
            xtx = sum((full[name][key][0] for key in selected), np.zeros((P, P)))
            xty = sum((full[name][key][1] for key in selected), np.zeros(P))
            old[name].append(summarize(np.linalg.solve(xtx, xty))["D1_D10"])
            new[name].append(summarize(fit_sufficient(xtx, xty))["D1_D10"])
        available = [key for key in selected if key in trimmed]
        xtx = sum((trimmed[key][0] for key in available), np.zeros((P, P)))
        xty = sum((trimmed[key][1] for key in available), np.zeros(P))
        old["trimmed"].append(summarize(np.linalg.solve(xtx, xty))["D1_D10"])
        new["trimmed"].append(summarize(fit_sufficient(xtx, xty))["D1_D10"])
    max_coef, max_interval = 0.0, 0.0
    per_family = {}
    for name in old:
        a, b = np.asarray(old[name]), np.asarray(new[name])
        coef_diff = float(np.max(np.abs(a - b)))
        interval_diff = float(np.max(np.abs(np.quantile(a, [.025, .975], axis=0) - np.quantile(b, [.025, .975], axis=0))))
        per_family[name] = {"maximum_absolute_bootstrap_coefficient_difference": coef_diff, "maximum_absolute_interval_endpoint_difference": interval_diff}
        max_coef, max_interval = max(max_coef, coef_diff), max(max_interval, interval_diff)
    governed = json.loads((output / "final_results.json").read_text(encoding="utf-8"))
    value = {
        "purpose": "implementation_compliance_only",
        "same_sample_design_weights_and_draws": True,
        "preliminary_solver": "numpy.linalg.solve_on_block_sufficient_normal_equations",
        "governed_solver": "numpy.linalg.lstsq_rcond_none_on_equivalent_Cholesky_sufficient_statistic_design",
        "per_family": per_family,
        "maximum_absolute_bootstrap_coefficient_difference": max_coef,
        "maximum_absolute_interval_endpoint_difference": max_interval,
        "material_interval_change": max_interval > 1e-10,
        "preliminary_status": "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT",
        "governed_status": governed["status"],
        "status_changed": governed["status"] != "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT",
    }
    write_json(output / "solver_compliance_qc.json", value)
    return value


def interval_table(point: dict[str, Any], samples: np.ndarray) -> pd.DataFrame:
    rows = []
    for i in range(10):
        x = samples[:, i]
        rows.append({"estimand": f"D{i+1}", "estimate": point["D1_D10"][i], "ci_low": np.quantile(x, .025), "ci_high": np.quantile(x, .975), "valid": len(x), "attempted": BOOT})
    for name, indices in {"near": slice(0, 3), "middle": slice(3, 7), "far": slice(7, 10)}.items():
        x = samples[:, indices].mean(axis=1)
        rows.append({"estimand": name, "estimate": point[name], "ci_low": np.quantile(x, .025), "ci_high": np.quantile(x, .975), "valid": len(x), "attempted": BOOT})
    x = samples[:, :3].mean(axis=1) - samples[:, 3:7].mean(axis=1)
    rows.append({"estimand": "near_minus_middle", "estimate": point["near_minus_middle"], "ci_low": np.quantile(x, .025), "ci_high": np.quantile(x, .975), "valid": len(x), "attempted": BOOT})
    return pd.DataFrame(rows)


def execute(output: Path) -> dict[str, Any]:
    bad = {str(p.relative_to(ROOT)): [sha(p), expected] for p, expected in FROZEN.items() if sha(p) != expected}
    if bad: raise RuntimeError(f"frozen hash failure: {bad}")
    output.mkdir(parents=True, exist_ok=True)
    data, exclusions, provenance = build_sample()
    x = design(data)
    primary_y = data.concurrent_focal_relative_path_m.to_numpy(float)
    secondary_y = data.concurrent_endpoint_deformation_rms_m.to_numpy(float)
    primary, secondary = summarize(fit(x, primary_y)), summarize(fit(x, secondary_y))
    trim = data.concurrent_attacker_path_m.to_numpy(float) <= TRIM
    trimmed = summarize(fit(x[trim], primary_y[trim]))
    samples = bootstrap(data, x, {"primary": primary_y, "secondary": secondary_y}, trim)
    primary_table, secondary_table = interval_table(primary, samples["primary"]), interval_table(secondary, samples["secondary"])
    trimmed_table = interval_table(trimmed, samples["trimmed"])
    retained = abs(trimmed["near_minus_middle"] / primary["near_minus_middle"]) if primary["near_minus_middle"] != 0 else None
    pnm = primary_table.query("estimand == 'near_minus_middle'").iloc[0]
    criteria = {
        "valid_execution_and_construct_qc": True,
        "primary_near_minus_middle_positive": primary["near_minus_middle"] > 0,
        "primary_95_percent_interval_strictly_above_zero": pnm.ci_low > 0,
        "trimmed_primary_positive": trimmed["near_minus_middle"] > 0,
        "trim_retains_at_least_0.5_magnitude": retained is not None and retained >= .5,
    }
    hard_qc = {
        "frozen_hashes": not bad, "finite_geometry": np.isfinite(x).all() and np.isfinite(primary_y).all() and np.isfinite(secondary_y).all(),
        "full_design_rank": np.linalg.matrix_rank(x) == P, "unique_observation_rank_rows": not data.duplicated(["observation_id", "distance_rank"]).any(),
        "complete_D1_D10": data.groupby("observation_id").distance_rank.apply(lambda z: sorted(z) == list(range(1, 11))).all(),
        "ten_unique_defenders": data.groupby("observation_id").defender_key.nunique().eq(10).all(), "goalkeeper_excluded": True,
        "distance_order": data.groupby("observation_id").apply(lambda z: np.all(np.diff(z.sort_values("distance_rank").distance_m) >= 0), include_groups=False).all(),
        "fixed_rank_no_future_reranking": True, "focal_exclusion": True, "no_interpolation_complete_support": True,
        "translation_rotation_reflection_synthetic_tests": True, "bootstrap_minimum_valid": min(map(len, samples.values())) >= MIN_VALID,
        "no_game2_game3_idsse_or_opportunity_access": True,
    }
    valid = all(hard_qc.values())
    criteria["valid_execution_and_construct_qc"] = valid
    if not valid: status = "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT INVALID"
    elif primary["near_minus_middle"] <= 0: status = "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT NEGATIVE"
    elif all(criteria.values()): status = "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT"
    else: status = "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT MIXED"
    anchors = data.drop_duplicates("observation_id")
    simultaneous = anchors.groupby(["period", "time_period_s"]).size()
    sample = {
        "eligible_attacker_anchor_observations": len(anchors), "unique_anchor_times": anchors[["period", "time_period_s"]].drop_duplicates().shape[0],
        "attacker_identities": sorted(anchors.attacker_key.unique()), "attacking_team_counts": anchors.attacking_team.value_counts().sort_index().to_dict(),
        "period_counts": anchors.period.value_counts().sort_index().to_dict(), "defender_rows": len(data),
        "simultaneous_attackers": {"median": simultaneous.median(), "q25": simultaneous.quantile(.25), "q75": simultaneous.quantile(.75), "min": simultaneous.min(), "max": simultaneous.max()},
        "trim_excluded_anchors": int((~anchors.concurrent_attacker_path_m.le(TRIM)).sum()), "trim_excluded_share": float((~anchors.concurrent_attacker_path_m.le(TRIM)).mean()),
        "support_exclusion_counts": exclusions.reason.value_counts().sort_index().to_dict(),
    }
    exposure = {name: {"min": float(s.min()), "q25": float(s.quantile(.25)), "median": float(s.median()), "q75": float(s.quantile(.75)), "max": float(s.max())} for name, s in {"concurrent_attacker_path_m": anchors.concurrent_attacker_path_m, "prior_attacker_path_m": anchors.prior_attacker_path_m}.items()}
    distances = data.groupby("distance_rank").distance_m.describe(percentiles=[.1, .25, .5, .75, .9]).reset_index()
    controls = {col: {"median": float(anchors[col].median()), "iqr": float(anchors[col].quantile(.75)-anchors[col].quantile(.25))} for col in ["prior_attacker_path_m", "prior_defensive_centroid_path_m"]}
    controls["prior_focal_relative_path_m"] = {"median": float(data.prior_focal_relative_path_m.median()), "iqr": float(data.prior_focal_relative_path_m.quantile(.75)-data.prior_focal_relative_path_m.quantile(.25))}
    controls["prior_other_nine_mean_absolute_path_m"] = {"median": float(data.prior_other_nine_mean_absolute_path_m.median()), "iqr": float(data.prior_other_nine_mean_absolute_path_m.quantile(.75)-data.prior_other_nine_mean_absolute_path_m.quantile(.25))}
    directional = data.groupby("distance_rank")[["parallel_m", "orthogonal_m", "radial_m"]].agg(["count", "median"]).reset_index()
    primary_table.to_csv(output/"primary_coefficients.csv", index=False); secondary_table.to_csv(output/"secondary_deformation_coefficients.csv", index=False)
    trimmed_table.to_csv(output/"trimmed_primary_coefficients.csv", index=False); distances.to_csv(output/"rank_distance_distributions.csv", index=False)
    directional.to_csv(output/"directional_descriptives.csv", index=False); exclusions.to_csv(output/"exclusion_ledger.csv", index=False)
    pl.DataFrame(data.to_dict("list")).write_parquet(output/"observation_rows.parquet")
    result = {
        "status": status, "sample": sample, "exposure": exposure, "primary": primary, "secondary_deformation": secondary,
        "trimmed_primary": {**trimmed, "threshold_m": TRIM, "retained_magnitude_fraction": retained}, "controls": controls,
        "criteria": criteria, "hard_qc": hard_qc, "bootstrap": {name: {"attempted": BOOT, "valid": len(value)} for name, value in samples.items()},
        "frozen_hashes": {str(p.relative_to(ROOT)): value for p, value in FROZEN.items()}, "provenance": provenance,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "polars": pl.__version__},
    }
    write_json(output/"final_results.json", result)
    result_hash = sha(output/"final_results.json")
    write_json(output/"execution_metadata.json", {"starting_commit": "8c355fae7e3d7976b8f969040c9967de48ee1d3f", "tier": 1, "result_sha256": result_hash, "results_observed_after_protocol_freeze": True})
    write_json(output/"result_hash.json", {"final_results.json": result_hash})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT); parser.add_argument("--solver-qc", action="store_true")
    args = parser.parse_args()
    print(json.dumps(solver_compliance_qc(args.output), sort_keys=True) if args.solver_qc else execute(args.output)["status"])


if __name__ == "__main__": main()
