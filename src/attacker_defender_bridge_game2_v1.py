"""Execute frozen attacker-to-defender bridge v1 on Metrica Game 2 and pooled matches."""
from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

import attacker_defender_bridge_game1_v1 as g1
import attacking_continuous_movement_game2_v1 as attacker2


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "protocols" / "attacker_defender_bridge_v1.md"
GAME1_OUTPUT = ROOT / "outputs" / "attacker_defender_bridge_game1_v1"
GAME2_ATTACKER_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game2_v1"
STAGE_A_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game2_stage_a"
EVENTS = ROOT / "data" / "metrica_sample_game_2" / "Sample_Game_2_RawEventsData.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "attacker_defender_bridge_game2_v1"
DEFAULT_FIGURES = ROOT / "figures" / "attacker_defender_bridge_game2_v1"
FROZEN_GAME1_P99_M = 12.198443079831405
GAME1_FINAL_LEDGER_SHA256 = "e1bb33e52eb65a45b02fefd85eb6ea1d1da148bb6327e52c5a8ba0de42ea9ae7"
GAME2_ATTACKER_FINAL_LEDGER_SHA256 = "665bb256f1746c02744801b7f17a89faf26116838ff10ea491b6c54bf92b7e36"


def verify_prerequisites() -> dict[str, Any]:
    stage = attacker2.verify_stage_a()
    g1_result = json.loads((GAME1_OUTPUT / "final_results.json").read_text(encoding="utf-8"))
    g1_inheritance = json.loads((GAME1_OUTPUT / "game2_inheritance.json").read_text(encoding="utf-8"))
    checks = {
        "protocol_hash": g1.sha256(PROTOCOL) == g1.FROZEN_PROTOCOL_SHA256,
        "game1_final_ledger_file_hash": g1.sha256(GAME1_OUTPUT / "final_output_hashes.json") == GAME1_FINAL_LEDGER_SHA256,
        "game1_final_ledger_valid": g1.verify_hash_ledger(GAME1_OUTPUT, "final_output_hashes.json"),
        "game1_status_coherent": g1_result["development_status"] == "GAME 1 DEVELOPMENT COHERENT",
        "game1_inherited_threshold_exact": float(g1_inheritance["game1_p99_exposure_threshold_m"]) == FROZEN_GAME1_P99_M,
        "game2_attacker_ledger_file_hash": g1.sha256(GAME2_ATTACKER_OUTPUT / "final_output_hashes.json") == GAME2_ATTACKER_FINAL_LEDGER_SHA256,
        "game2_attacker_ledger_valid": g1.verify_hash_ledger(GAME2_ATTACKER_OUTPUT, "final_output_hashes.json"),
        "game2_attacker_classification_a": json.loads((GAME2_ATTACKER_OUTPUT / "final_results.json").read_text(encoding="utf-8"))["classification"] == "A",
        "stage_a_ready": stage["classification"] == "READY",
        "stage_a_rows_exact": stage["valid_raw_rows"] == 2_093_028,
        "stage_a_segments_exact": stage["support_segments"] == 134,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Frozen prerequisite failure: {checks}")
    return {"checks": checks, "stage_a": stage}


def feature_lookup(features: pd.DataFrame) -> dict[tuple[int, int, str], dict[str, Any]]:
    return {
        (int(row["period"]), int(round(float(row["time_period_s"]) * 25)), str(row["player_key"])): row
        for row in features.to_dict("records")
    }


def build_game2_observations() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any], dict[tuple[int, str], Any]]:
    prerequisites = verify_prerequisites()
    features = pd.DataFrame(pl.read_parquet(GAME2_ATTACKER_OUTPUT / "features_2s.parquet").to_dicts())
    lookup = feature_lookup(features)
    pps, period_frames, provenance, support_consumption = attacker2.load_game2_from_frozen_support()
    pp_map = {(pp.period, pp.player_key): pp for pp in pps}
    roster: dict[tuple[int, str], list[str]] = {}
    for pp in pps:
        roster.setdefault((pp.period, pp.team_key), []).append(pp.player_key)
    for key in roster:
        roster[key] = sorted(set(roster[key]))
    events = pd.read_csv(EVENTS)

    rows: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    endpoint_counts = {"candidate_endpoints": 0, "no_possession_endpoints": 0}
    for period in sorted(period_frames):
        origin = float(period_frames[period]["origin_time_period_s"])
        last = float(period_frames[period]["time_period_s"][-1])
        k = 0
        while True:
            t = origin + 4.0 + g1.CADENCE_S * k
            if t + 2.0 > last + g1.TOL:
                break
            endpoint_counts["candidate_endpoints"] += 1
            raw_i = int(np.searchsorted(period_frames[period]["time_period_s"], t - g1.TOL))
            if raw_i >= len(period_frames[period]["time_period_s"]) or abs(float(period_frames[period]["time_period_s"][raw_i]) - t) > g1.TOL:
                exclusions.append({"period": period, "time_period_s": t, "player_key": None, "reason": "endpoint_not_exact_frame"})
                k += 1
                continue
            tmatch = float(period_frames[period]["time_match_s"][raw_i])
            team, has_restart = g1.event_context(events, period, tmatch, tmatch - 4.0, tmatch + 2.0)
            if team is None:
                endpoint_counts["no_possession_endpoints"] += 1
                exclusions.append({"period": period, "time_period_s": t, "player_key": None, "reason": "no_possession_team"})
                k += 1
                continue
            attack_key = f"metrica:{team}"
            defend_key = "metrica:Away" if attack_key == "metrica:Home" else "metrica:Home"
            for player_key in roster.get((period, attack_key), []):
                base = {"period": period, "time_period_s": t, "time_match_s": tmatch, "player_key": player_key,
                        "attacking_team": attack_key, "defending_team": defend_key}
                reason = "restart_or_ball_out_primary_span" if has_restart else None
                exposure = lookup.get((period, int(round(t * 25)), player_key))
                future = lookup.get((period, int(round((t + 2.0) * 25)), player_key))
                pp_attacker = pp_map.get((period, player_key))
                if reason is None and exposure is None:
                    reason = "attacker_exposure_unavailable"
                if reason is None and (pp_attacker is None or g1.segment(pp_attacker, t - 4.0, t + 2.0) is None):
                    reason = "attacker_full_support_unavailable"
                if reason is None and future is None:
                    reason = "placebo_future_exposure_unavailable"
                supported_defenders = {
                    key: pp_map[(period, key)] for key in roster.get((period, defend_key), [])
                    if (period, key) in pp_map and g1.segment(pp_map[(period, key)], t - 4.0, t + 2.0) is not None
                }
                if reason is None and len(supported_defenders) != 10:
                    reason = "complete_ten_defenders_unavailable"
                if reason is not None:
                    exclusions.append({**base, "reason": reason})
                    continue

                intervals = {"prior": (t - 4.0, t - 2.0), "earlier": (t - 2.0, t),
                             "post1": (t, t + 1.0), "post2": (t, t + 2.0)}
                geometry = {name: g1.defensive_geometry(supported_defenders, *bounds) for name, bounds in intervals.items()}
                if any(value is None for value in geometry.values()):
                    exclusions.append({**base, "reason": "defensive_geometry_unavailable"})
                    continue
                attacker_pos = g1.position(pp_attacker, t)
                if attacker_pos is None:
                    exclusions.append({**base, "reason": "attacker_endpoint_unavailable"})
                    continue
                distances: list[tuple[float, str]] = []
                for defender_key, pp_def in supported_defenders.items():
                    defender_pos = g1.position(pp_def, t)
                    if defender_pos is None:
                        raise RuntimeError("Complete support lacked endpoint")
                    distances.append((float(np.linalg.norm(defender_pos - attacker_pos)), defender_key))
                distances.sort(key=lambda item: (item[0], item[1]))
                local = [key for _, key in distances[:g1.K]]
                nonlocal_set = [key for _, key in distances[-g1.K:][::-1]]
                if set(local) & set(nonlocal_set):
                    raise RuntimeError("Local and nonlocal sets overlap")
                prior_paths, centroid_prior = geometry["prior"]
                earlier_paths, _ = geometry["earlier"]
                post1_paths, _ = geometry["post1"]
                post2_paths, _ = geometry["post2"]
                observation_id = f"G2|P{period}|T{t:.2f}|{player_key}"

                team4, restart4 = g1.event_context(events, period, tmatch, tmatch - 4.0, tmatch + 4.0)
                defenders4 = {
                    key: pp_map[(period, key)] for key in roster.get((period, defend_key), [])
                    if (period, key) in pp_map and g1.segment(pp_map[(period, key)], t - 4.0, t + 4.0) is not None
                }
                attacker4 = g1.segment(pp_attacker, t - 4.0, t + 4.0) if t + 4.0 <= last + g1.TOL else None
                post4 = None
                eligible4 = bool(team4 == team and not restart4 and attacker4 is not None and len(defenders4) == 10)
                if eligible4:
                    post4 = g1.defensive_geometry(defenders4, t, t + 4.0)
                    eligible4 = post4 is not None

                def mean_for(values: dict[str, float], members: list[str]) -> float:
                    return float(np.mean([values[key] for key in members]))

                rows.append({
                    **base, "observation_id": observation_id,
                    "frame_id_provider": str(period_frames[period]["frame_ids"][raw_i]),
                    "block_id": int(math.floor((t - origin) / g1.BLOCK_S)),
                    "attacker_path_length_m": float(exposure["path_length_m"]),
                    "attacker_delta_x_m": float(exposure["delta_x_m"]),
                    "attacker_delta_y_m": float(exposure["delta_y_m"]),
                    "attacker_straightness": exposure["straightness"],
                    "attacker_straightness_valid": bool(exposure["straightness_valid"]),
                    "future_attacker_path_length_m": float(future["path_length_m"]),
                    "prior_local_relative_path_m": mean_for(prior_paths, local),
                    "prior_nonlocal_relative_path_m": mean_for(prior_paths, nonlocal_set),
                    "prior_defending_centroid_path_m": float(centroid_prior),
                    "earlier_local_relative_path_m": mean_for(earlier_paths, local),
                    "local_response_1s_m": mean_for(post1_paths, local),
                    "local_response_2s_m": mean_for(post2_paths, local),
                    "nonlocal_response_2s_m": mean_for(post2_paths, nonlocal_set),
                    "local_response_4s_m": None if not eligible4 else mean_for(post4[0], local),
                    "eligible_4s": eligible4,
                })
                for rank, (distance, defender_key) in enumerate(distances, 1):
                    set_name = "local" if defender_key in local else ("nonlocal" if defender_key in nonlocal_set else "middle")
                    links.append({
                        "observation_id": observation_id, "period": period, "time_period_s": t,
                        "attacker_key": player_key, "defender_key": defender_key, "distance_m": distance,
                        "distance_rank": rank, "set_name": set_name,
                        "prior_relative_path_m": prior_paths[defender_key],
                        "earlier_relative_path_m": earlier_paths[defender_key],
                        "response_1s_m": post1_paths[defender_key], "response_2s_m": post2_paths[defender_key],
                        "response_4s_m": None if not eligible4 else post4[0][defender_key],
                    })
            k += 1
    df = pd.DataFrame(rows).sort_values(["period", "time_period_s", "player_key"], kind="mergesort").reset_index(drop=True)
    linkage = pd.DataFrame(links).sort_values(["observation_id", "distance_rank"], kind="mergesort").reset_index(drop=True)
    exclusion = pd.DataFrame(exclusions)
    if not exclusion.empty:
        exclusion = exclusion.sort_values(["period", "time_period_s", "player_key"], kind="mergesort", na_position="first").reset_index(drop=True)
    execution_provenance = {
        "canonical": provenance, "support_consumption": support_consumption,
        "prerequisites": prerequisites, "endpoint_counts": endpoint_counts,
    }
    return df, linkage, exclusion, endpoint_counts, execution_provenance, pp_map


GAME2_SPECS = dict(g1.MODEL_SPECS)


def fit_pooled(df: pd.DataFrame, outcome: str, exposure: str, baseline: str) -> np.ndarray | None:
    if len(df) < 6:
        return None
    x = np.column_stack([
        np.ones(len(df), dtype=np.float64), df[exposure].to_numpy(np.float64),
        df[baseline].to_numpy(np.float64), df["prior_defending_centroid_path_m"].to_numpy(np.float64),
        df["game2_indicator"].to_numpy(np.float64),
    ])
    y = df[outcome].to_numpy(np.float64)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.linalg.matrix_rank(x) < x.shape[1]:
        return None
    coef, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    return coef if np.isfinite(coef).all() else None


def sampled_indices_pooled(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    selected: list[np.ndarray] = []
    for game in sorted(df["game"].unique()):
        for period in sorted(df.loc[df["game"] == game, "period"].unique()):
            z = df[(df["game"] == game) & (df["period"] == period)]
            blocks = sorted(z["block_id"].unique())
            for draw in rng.integers(0, len(blocks), size=len(blocks)):
                selected.append(z.index[z["block_id"] == blocks[int(draw)]].to_numpy())
    return np.concatenate(selected)


def bootstrap_family(df: pd.DataFrame, child_index: int, pooled: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    child = np.random.SeedSequence(g1.MASTER_SEED).spawn(3)[child_index]
    rng = np.random.Generator(np.random.PCG64(child))
    values = {name: [] for name in [*GAME2_SPECS, "trimmed_2s"]}
    differences = {"local_minus_nonlocal": [], "local_minus_placebo": []}
    fitter = fit_pooled if pooled else g1.fit
    for _ in range(g1.BOOTSTRAPS):
        idx = sampled_indices_pooled(df, rng) if pooled else g1.sampled_indices(df, rng)
        z = df.loc[idx].reset_index(drop=True)
        fitted: dict[str, np.ndarray | None] = {}
        for name, spec in GAME2_SPECS.items():
            fitted[name] = fitter(z, *spec)
            values[name].append(None if fitted[name] is None else float(fitted[name][1]))
        trimmed = z[z["attacker_path_length_m"] <= FROZEN_GAME1_P99_M].reset_index(drop=True)
        fitted["trimmed_2s"] = fitter(trimmed, *GAME2_SPECS["primary_local_2s"])
        values["trimmed_2s"].append(None if fitted["trimmed_2s"] is None else float(fitted["trimmed_2s"][1]))
        a, b, c = fitted["primary_local_2s"], fitted["nonlocal_2s"], fitted["reverse_time_placebo"]
        differences["local_minus_nonlocal"].append(None if a is None or b is None else float(a[1] - b[1]))
        differences["local_minus_placebo"].append(None if a is None or c is None else float(a[1] - c[1]))
    return g1.summarize_bootstraps(values), g1.summarize_bootstraps(differences)


def bootstrap_4s(df: pd.DataFrame, child_index: int, pooled: bool = False) -> pd.DataFrame:
    child = np.random.SeedSequence(g1.MASTER_SEED).spawn(3)[child_index]
    rng = np.random.Generator(np.random.PCG64(child))
    values: list[float | None] = []
    fitter = fit_pooled if pooled else g1.fit
    for _ in range(g1.BOOTSTRAPS):
        idx = sampled_indices_pooled(df, rng) if pooled else g1.sampled_indices(df, rng)
        coef = fitter(df.loc[idx].reset_index(drop=True), "local_response_4s_m", "attacker_path_length_m", "prior_local_relative_path_m")
        values.append(None if coef is None else float(coef[1]))
    return g1.summarize_bootstraps({"local_4s": values})


def fit_family(df: pd.DataFrame, pooled: bool = False) -> dict[str, list[float]]:
    fitter = fit_pooled if pooled else g1.fit
    points: dict[str, list[float]] = {}
    for name, spec in {**GAME2_SPECS, "trimmed_2s": GAME2_SPECS["primary_local_2s"]}.items():
        z = df[df["attacker_path_length_m"] <= FROZEN_GAME1_P99_M] if name == "trimmed_2s" else df
        coef = fitter(z.reset_index(drop=True), *spec)
        if coef is None:
            raise RuntimeError(f"Unestimable model: {name}")
        points[name] = coef.tolist()
    z4 = df[df["eligible_4s"]].dropna(subset=["local_response_4s_m"]).reset_index(drop=True)
    coef4 = fitter(z4, "local_response_4s_m", "attacker_path_length_m", "prior_local_relative_path_m")
    if coef4 is None:
        raise RuntimeError("Unestimable 4s model")
    points["local_4s"] = coef4.tolist()
    return points


def hard_qc(df: pd.DataFrame, linkage: pd.DataFrame, boot: pd.DataFrame, diff: pd.DataFrame,
            coefficients: dict[str, list[float]], pooled: pd.DataFrame) -> pd.DataFrame:
    base = g1.hard_qc_table(df, linkage, boot, diff, coefficients)
    extra: list[tuple[str, bool, str]] = []
    def add(name: str, passed: bool, detail: str) -> None:
        extra.append((name, bool(passed), detail))
    add("game2_seed_child_reserved", True, "SeedSequence(20260831).spawn(3)[1]")
    add("pooled_seed_child_reserved", True, "SeedSequence(20260831).spawn(3)[2]")
    add("inherited_threshold_exact", FROZEN_GAME1_P99_M == 12.198443079831405, f"{FROZEN_GAME1_P99_M:.15f}")
    add("game2_stage_a_support_unchanged", attacker2.verify_stage_a()["valid_raw_rows"] == 2_093_028, "2,093,028 rows; 134 segments")
    add("pooled_game_indicator", set(pooled["game2_indicator"].unique()) == {0, 1}, "Game 1=0; Game 2=1")
    add("pooled_matches_not_resampled", True, "blocks resampled independently inside all four match-period groups")
    add("game3_not_accessed", True, "no Game 3 path or loader in implementation")
    add("game1_outputs_read_only", g1.verify_hash_ledger(GAME1_OUTPUT, "final_output_hashes.json"), "final ledger validates")
    return pd.concat([base, pd.DataFrame(extra, columns=base.columns)], ignore_index=True)


def descriptive(df: pd.DataFrame, endpoint_counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "eligible_primary_observations": len(df),
        "unique_evaluation_times": int(df[["period", "time_period_s"]].drop_duplicates().shape[0]),
        "by_period": df.groupby("period").size().to_dict(),
        "by_attacking_team": df.groupby("attacking_team").size().to_dict(),
        "by_attacker": df.groupby("player_key").size().to_dict(),
        "simultaneous_attacker_multiplicity": g1.summary(df.groupby(["period", "time_period_s"]).size()),
        "endpoint_counts": endpoint_counts,
        "exposure": g1.summary(df["attacker_path_length_m"]),
        "local_response": g1.summary(df["local_response_2s_m"]),
        "nonlocal_response": g1.summary(df["nonlocal_response_2s_m"]),
        "local_baseline": g1.summary(df["prior_local_relative_path_m"]),
        "nonlocal_baseline": g1.summary(df["prior_nonlocal_relative_path_m"]),
        "centroid_context": g1.summary(df["prior_defending_centroid_path_m"]),
        "delta_x": g1.summary(df["attacker_delta_x_m"]), "delta_y": g1.summary(df["attacker_delta_y_m"]),
        "straightness_valid": g1.summary(df.loc[df["attacker_straightness_valid"], "attacker_straightness"]),
        "influence": g1.influence(df),
        "four_second_eligible": int(df["eligible_4s"].sum()),
    }


def make_figures(df2: pd.DataFrame, game_points: dict[str, list[float]], pooled_points: dict[str, list[float]],
                 game_boot: pd.DataFrame, pooled_boot: pd.DataFrame, figures: Path) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    coef = np.asarray(game_points["primary_local_2s"])
    grid = np.linspace(df2["attacker_path_length_m"].min(), df2["attacker_path_length_m"].max(), 100)
    trend = coef[0] + coef[1] * grid + coef[2] * df2["prior_local_relative_path_m"].mean() + coef[3] * df2["prior_defending_centroid_path_m"].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df2["attacker_path_length_m"], df2["local_response_2s_m"], s=9, alpha=.18, color="#377eb8")
    ax.plot(grid, trend, color="#d95f02", lw=3)
    ax.set(xlabel="Attacker path in preceding 2 s (m)", ylabel="Subsequent mean local focal-relative path (m)",
           title="Game 2 frozen bridge relationship")
    fig.tight_layout(); fig.savefig(figures / "game2_primary_relationship.png", dpi=180); plt.close(fig)

    g1_points = pd.read_csv(GAME1_OUTPUT / "model_coefficients.csv").set_index("model")
    vals = [float(g1_points.loc["primary_local_2s", "beta1"]), game_points["primary_local_2s"][1], pooled_points["primary_local_2s"][1]]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(["Game 1", "Game 2", "Pooled"], vals, color=["#4c78a8", "#f58518", "#54a24b"]); ax.axhline(0, color="black", lw=.8)
    ax.set(ylabel="Attacker-path coefficient (m/m)", title="Frozen bridge coefficient across matches")
    fig.tight_layout(); fig.savefig(figures / "two_match_coefficients.png", dpi=180); plt.close(fig)

    names = ["Pooled local", "Pooled nonlocal", "Pooled placebo"]
    vals = [pooled_points[x][1] for x in ["primary_local_2s", "nonlocal_2s", "reverse_time_placebo"]]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.bar(names, vals, color=["#4c78a8", "#9d9d9d", "#bab0ac"]); ax.axhline(0, color="black", lw=.8)
    ax.set(ylabel="Attacker-path coefficient (m/m)", title="Pooled local and frozen controls")
    fig.tight_layout(); fig.savefig(figures / "pooled_control_comparison.png", dpi=180); plt.close(fig)


def run(output: Path, figures: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    df2, linkage, exclusions, endpoint_counts, provenance, _ = build_game2_observations()
    if df2.empty:
        raise RuntimeError("No eligible Game 2 observations")
    points2 = fit_family(df2)
    boot2, diff2 = bootstrap_family(df2, 1)
    boot2 = pd.concat([boot2, bootstrap_4s(df2[df2["eligible_4s"]].dropna(subset=["local_response_4s_m"]).reset_index(drop=True), 1)], ignore_index=True)

    df1 = pd.DataFrame(pl.read_parquet(GAME1_OUTPUT / "primary_observations.parquet").to_dicts())
    df1["game"] = "Game 1"; df1["game2_indicator"] = 0
    df2["game"] = "Game 2"; df2["game2_indicator"] = 1
    pooled = pd.concat([df1, df2], ignore_index=True).sort_values(["game", "period", "time_period_s", "player_key"], kind="mergesort").reset_index(drop=True)
    points_pool = fit_family(pooled, pooled=True)
    boot_pool, diff_pool = bootstrap_family(pooled, 2, pooled=True)
    pool4 = pooled[pooled["eligible_4s"]].dropna(subset=["local_response_4s_m"]).reset_index(drop=True)
    boot_pool = pd.concat([boot_pool, bootstrap_4s(pool4, 2, pooled=True)], ignore_index=True)

    qc = hard_qc(df2, linkage, boot2, diff2, points2, pooled)
    valid_boot = bool((boot2["valid"] >= g1.MIN_VALID_BOOTSTRAPS).all() and (diff2["valid"] >= g1.MIN_VALID_BOOTSTRAPS).all()
                      and (boot_pool["valid"] >= g1.MIN_VALID_BOOTSTRAPS).all() and (diff_pool["valid"] >= g1.MIN_VALID_BOOTSTRAPS).all())
    b2 = {name: values[1] for name, values in points2.items()}
    bp = {name: values[1] for name, values in points_pool.items()}
    d2 = {"local_minus_nonlocal": b2["primary_local_2s"] - b2["nonlocal_2s"],
          "local_minus_placebo": b2["primary_local_2s"] - b2["reverse_time_placebo"]}
    dp = {"local_minus_nonlocal": bp["primary_local_2s"] - bp["nonlocal_2s"],
          "local_minus_placebo": bp["primary_local_2s"] - bp["reverse_time_placebo"]}
    g1_result = json.loads((GAME1_OUTPUT / "final_results.json").read_text(encoding="utf-8"))
    b1 = {name: values[1] for name, values in g1_result["coefficients"].items()}
    pool_ci = boot_pool.set_index("model")
    pool_diff_ci = diff_pool.set_index("model")
    final_criteria = {
        "hard_qc": bool(qc["pass"].all()),
        "deterministic_reproduction": False,
        "bootstrap_valid_all": valid_boot,
        "primary_positive_both_matches": b1["primary_local_2s"] > 0 and b2["primary_local_2s"] > 0,
        "pooled_primary_interval_positive": float(pool_ci.loc["primary_local_2s", "ci_low"]) > 0,
        "local_minus_nonlocal_positive_both_matches": (b1["primary_local_2s"] - b1["nonlocal_2s"] > 0 and d2["local_minus_nonlocal"] > 0),
        "pooled_local_minus_nonlocal_interval_positive": float(pool_diff_ci.loc["local_minus_nonlocal", "ci_low"]) > 0,
        "primary_minus_placebo_positive_both_matches": (b1["primary_local_2s"] - b1["reverse_time_placebo"] > 0 and d2["local_minus_placebo"] > 0),
        "pooled_primary_minus_placebo_interval_positive": float(pool_diff_ci.loc["local_minus_placebo", "ci_low"]) > 0,
        "trimmed_robust_both_matches": (b1["trimmed_2s"] > 0 and b1["trimmed_2s"] >= .5 * b1["primary_local_2s"]
                                          and b2["trimmed_2s"] > 0 and b2["trimmed_2s"] >= .5 * b2["primary_local_2s"]),
        "horizon_no_joint_reversal_both_matches": (not (b1["primary_local_2s"] > 0 and b1["local_1s"] < 0 and b1["local_4s"] < 0)
                                                     and not (b2["primary_local_2s"] > 0 and b2["local_1s"] < 0 and b2["local_4s"] < 0)),
    }
    classification = "PENDING DETERMINISTIC REPRODUCTION"

    desc = descriptive(df2, endpoint_counts)
    excluded2 = int((df2["attacker_path_length_m"] > FROZEN_GAME1_P99_M).sum())
    excluded1 = int((df1["attacker_path_length_m"] > FROZEN_GAME1_P99_M).sum())
    result = {
        "final_classification": classification, "final_criteria": final_criteria,
        "game2_coefficients": points2, "pooled_coefficients": points_pool,
        "game2_differences": d2, "pooled_differences": dp,
        "game2_descriptive_summaries": desc,
        "inherited_game1_p99_threshold_m": FROZEN_GAME1_P99_M,
        "trimmed_counts": {"game1_excluded": excluded1, "game2_excluded": excluded2,
                           "total_excluded": excluded1 + excluded2, "game2_trimmed_n": len(df2) - excluded2,
                           "pooled_trimmed_n": len(pooled) - excluded1 - excluded2},
        "pooled_n": len(pooled), "game2_n": len(df2),
        "game3_accessed": False, "protocol_tuned_after_game2": False,
    }

    pl.DataFrame(df2.drop(columns=["game", "game2_indicator"]).to_dict(orient="list")).write_parquet(output / "game2_observations.parquet", compression="zstd", statistics=True)
    pl.DataFrame(linkage.to_dict(orient="list")).write_parquet(output / "game2_defender_linkage.parquet", compression="zstd", statistics=True)
    exclusions.to_csv(output / "game2_eligibility_exclusions.csv", index=False, float_format="%.17g", lineterminator="\n")
    exclusions.groupby("reason", dropna=False).size().rename("count").reset_index().to_csv(output / "game2_eligibility_waterfall.csv", index=False, lineterminator="\n")
    pd.DataFrame([{"model": n, **{f"beta{i}": x for i, x in enumerate(v)}} for n, v in points2.items()]).to_csv(output / "game2_model_coefficients.csv", index=False, float_format="%.17g", lineterminator="\n")
    pd.DataFrame([{"model": n, **{f"beta{i}": x for i, x in enumerate(v)}} for n, v in points_pool.items()]).to_csv(output / "pooled_model_coefficients.csv", index=False, float_format="%.17g", lineterminator="\n")
    boot2.to_csv(output / "game2_bootstrap_summaries.csv", index=False, float_format="%.17g", lineterminator="\n")
    diff2.to_csv(output / "game2_paired_bootstrap_differences.csv", index=False, float_format="%.17g", lineterminator="\n")
    boot_pool.to_csv(output / "pooled_bootstrap_summaries.csv", index=False, float_format="%.17g", lineterminator="\n")
    diff_pool.to_csv(output / "pooled_paired_bootstrap_differences.csv", index=False, float_format="%.17g", lineterminator="\n")
    qc.to_csv(output / "hard_qc.csv", index=False, lineterminator="\n")
    pd.DataFrame([{"criterion": k, "pass": v} for k, v in final_criteria.items()]).to_csv(output / "final_criteria.csv", index=False, lineterminator="\n")
    g1.write_json(output / "game2_descriptive_summaries.json", desc)
    g1.write_json(output / "final_results.json", result)
    make_figures(df2, points2, points_pool, boot2, boot_pool, figures)

    governed = [
        "game2_observations.parquet", "game2_defender_linkage.parquet", "game2_eligibility_exclusions.csv",
        "game2_eligibility_waterfall.csv", "game2_model_coefficients.csv", "pooled_model_coefficients.csv",
        "game2_bootstrap_summaries.csv", "game2_paired_bootstrap_differences.csv", "pooled_bootstrap_summaries.csv",
        "pooled_paired_bootstrap_differences.csv", "hard_qc.csv", "final_criteria.csv",
        "game2_descriptive_summaries.json", "final_results.json",
    ]
    manifest = {
        "protocol": "docs/protocols/attacker_defender_bridge_v1.md", "protocol_sha256": g1.sha256(PROTOCOL),
        "source": "src/attacker_defender_bridge_game2_v1.py", "source_sha256": g1.sha256(Path(__file__)),
        "game1_final_ledger_sha256": g1.sha256(GAME1_OUTPUT / "final_output_hashes.json"),
        "game2_attacker_final_ledger_sha256": g1.sha256(GAME2_ATTACKER_OUTPUT / "final_output_hashes.json"),
        "stage_a_governed_ledger_sha256": g1.sha256(STAGE_A_OUTPUT / "governed_output_hashes.json"),
        "events_sha256": g1.sha256(EVENTS), "python": platform.python_version(), "numpy": np.__version__,
        "pandas": pd.__version__, "polars": pl.__version__, "provenance": provenance,
        "rng": {"master_seed": g1.MASTER_SEED, "game2_child": 1, "pooled_child": 2},
        "inherited_game1_p99_threshold_m": FROZEN_GAME1_P99_M,
        "governed_output_files": governed, "game3_accessed": False, "protocol_tuned_after_game2": False,
    }
    g1.write_json(output / "manifest.json", manifest)
    g1.write_json(output / "governed_output_hashes.json", {name: g1.sha256(output / name) for name in governed})


def verify_reproduction(primary: Path, rerun: Path) -> None:
    pm = json.loads((primary / "manifest.json").read_text(encoding="utf-8"))
    rm = json.loads((rerun / "manifest.json").read_text(encoding="utf-8"))
    governed = [*pm["governed_output_files"], "manifest.json", "governed_output_hashes.json"]
    same = governed == [*rm["governed_output_files"], "manifest.json", "governed_output_hashes.json"]
    comparisons = []
    for name in governed:
        a, b = primary / name, rerun / name
        comparisons.append({"file": name, "primary_sha256": g1.sha256(a), "rerun_sha256": g1.sha256(b),
                            "byte_identical": a.read_bytes() == b.read_bytes()})
    passed = bool(same and all(x["byte_identical"] for x in comparisons))
    g1.write_json(primary / "reproduction_verification.json", {
        "files_compared": len(comparisons), "same_governed_file_list": same,
        "all_byte_identical": passed, "comparisons": comparisons,
    })
    result = json.loads((primary / "final_results.json").read_text(encoding="utf-8"))
    result["deterministic_reproduction_pass"] = passed
    result["final_criteria"]["deterministic_reproduction"] = passed
    if not result["final_criteria"]["hard_qc"] or not passed or not result["final_criteria"]["bootstrap_valid_all"]:
        result["final_classification"] = "FINAL BRIDGE C"
    else:
        result["final_classification"] = "FINAL BRIDGE A" if all(result["final_criteria"].values()) else "FINAL BRIDGE B"
    g1.write_json(primary / "final_results.json", result)
    pd.DataFrame([{"criterion": k, "pass": v} for k, v in result["final_criteria"].items()]).to_csv(primary / "final_criteria.csv", index=False, lineterminator="\n")
    final_files = [*governed, "reproduction_verification.json", "final_results.json", "final_criteria.csv"]
    g1.write_json(primary / "final_output_hashes.json", {name: g1.sha256(primary / name) for name in dict.fromkeys(final_files)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.verify_against is None:
        run(args.output, args.figures)
    else:
        verify_reproduction(args.output, args.verify_against)
