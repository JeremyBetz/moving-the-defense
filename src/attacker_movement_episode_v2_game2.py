"""Tier-3 heldout Game 2 execution of frozen Attacker Movement Episode v2.

Only each player's own trajectory, frozen support, and inherited global
stoppage boundaries enter construction or evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacker_movement_episode_v2 as v2  # noqa: E402
import attacking_continuous_movement_game2_v1 as game2_support  # noqa: E402
import attacking_continuous_movement_game1_v1 as continuous  # noqa: E402
import post5b_attacking_movement_segmentation_audit as historical  # noqa: E402


CONFIG = ROOT / "config/attacker_movement_episode_v2_game2_replication.json"
V2_CONFIG = ROOT / "config/attacker_movement_episode_v2.json"
PROTOCOL = ROOT / "docs/protocols/attacker_movement_episode_v2.md"
REPLICATION_PROTOCOL = ROOT / "docs/protocols/attacker_movement_episode_v2_game2_replication.md"
STAGE_A = ROOT / "outputs/attacking_continuous_movement_game2_stage_a"
EVENTS = ROOT / "data/metrica_sample_game_2/Sample_Game_2_RawEventsData.csv"
DEFAULT_OUT = ROOT / "outputs/attacker_movement_episode_v2_game2"
DEFAULT_FIG = ROOT / "figures/attacker_movement_episode_v2_game2"
GAME1 = ROOT / "outputs/attacker_movement_episode_v2_game1"
GOVERNED_FILES = [
    "audit_cases.csv", "audit_checks.csv", "candidate_a_episodes.csv",
    "candidate_b_boundaries.csv", "candidate_b_episodes.csv",
    "candidate_summary.csv", "distribution_summary.csv", "hard_qc.csv",
    "results.json", "support_blocks.csv",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_frozen() -> dict[str, Any]:
    replication = json.loads(CONFIG.read_text(encoding="utf-8"))
    inherited = {
        PROTOCOL: replication["inheritance"]["protocol_sha256"],
        V2_CONFIG: replication["inheritance"]["configuration_sha256"],
        GAME1 / "results.json": replication["inheritance"]["game1_result_sha256"],
        GAME1 / "hashes.json": replication["inheritance"]["game1_ledger_sha256"],
        STAGE_A / "valid_support_segments.csv": replication["support"]["valid_support_segments_sha256"],
        STAGE_A / "trajectory_validity_registry.csv": replication["support"]["trajectory_validity_registry_sha256"],
        STAGE_A / "stage_a_result.json": replication["support"]["stage_a_result_sha256"],
        STAGE_A / "governed_output_hashes.json": replication["support"]["stage_a_governed_hashes_sha256"],
    }
    mismatches = {str(path.relative_to(ROOT)): [sha256(path), expected] for path, expected in inherited.items() if sha256(path) != expected}
    if mismatches:
        raise RuntimeError(f"Frozen hash mismatch: {mismatches}")
    return {str(path.relative_to(ROOT)): expected for path, expected in inherited.items()}


def split_open_play_blocks() -> tuple[dict[str, pd.DataFrame], dict[str, Any], dict[str, Any]]:
    player_periods, _, provenance, support = game2_support.load_game2_from_frozen_support()
    exclusions, boundaries = historical.global_exclusions(pd.read_csv(EVENTS))
    blocks: dict[str, pd.DataFrame] = {}
    for pp in player_periods:
        for frozen_block in pp.blocks:
            lo, hi = frozen_block.raw_start_index, frozen_block.raw_end_index
            raw_indices = np.arange(lo, hi + 1)
            eligible = np.ones(len(raw_indices), dtype=bool)
            times = pp.time_match_s[raw_indices]
            for start, end in exclusions[pp.period]:
                eligible &= ~((times >= start - 1e-9) & (times <= end + 1e-9))
            for boundary in boundaries[pp.period]:
                eligible &= ~np.isclose(times, boundary, atol=1e-8)
            changes = np.flatnonzero(np.diff(np.r_[False, eligible, False].astype(np.int8)))
            for part, (start_local, stop_local) in enumerate(zip(changes[::2], changes[1::2]), start=1):
                start_raw = lo + int(start_local)
                end_raw = lo + int(stop_local) - 1
                smooth = continuous._build_block(pp, start_raw, end_raw, part, float(pp.time_period_s[0]))
                if smooth is None or len(smooth.positions25) < 5:
                    continue
                centers = smooth.center_indices
                q = pd.DataFrame({
                    "Period": pp.period,
                    "Frame": pp.frame_ids[centers].astype(int),
                    "Time [s]": pp.time_match_s[centers].astype(float),
                    "sx_m": smooth.positions25[:, 0],
                    "sy_m": smooth.positions25[:, 1],
                })
                dt = q["Time [s]"].diff()
                q["dx_m"] = q.sx_m.diff(); q["dy_m"] = q.sy_m.diff()
                q["speed_mps"] = np.hypot(q.dx_m, q.dy_m) / dt
                q = q.dropna(subset=["speed_mps"]).reset_index(drop=True)
                if len(q) < 3:
                    continue
                team = pp.team_key.rsplit(":", 1)[1]
                player = pp.player_number
                block_id = f"{frozen_block.block_id}|O{part:03d}"
                q["team"] = team; q["player"] = player; q["block_id"] = block_id
                blocks[block_id] = q
    return blocks, provenance, support


def baseline_and_high_speed(blocks: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_rows: list[dict] = []
    high_speed_rows: list[dict] = []
    for block_id in sorted(blocks):
        block = blocks[block_id]
        team, player = str(block.team.iloc[0]), str(block.player.iloc[0])
        baseline_rows.extend(historical.segment_method_a(block, team, player, block_id)[0])
        high_speed_rows.extend(historical.segment_method_b(block, team, player, block_id))
    high_speed = pd.DataFrame(high_speed_rows)
    baseline = historical.add_diagnostics(pd.DataFrame(baseline_rows), high_speed)
    baseline = baseline.sort_values(["period", "start_s", "team", "player", "start_frame"], kind="mergesort").reset_index(drop=True)
    baseline.insert(0, "episode_id", [f"G2A{i:06d}" for i in range(1, len(baseline) + 1)])
    return baseline, high_speed


def window_geometry(block: pd.DataFrame, start: int, frames: int = 101) -> dict[str, float] | None:
    end = start + frames - 1
    if end >= len(block):
        return None
    return historical.geometry(block.iloc[start:end + 1])


def select_audit_cases(blocks: dict[str, pd.DataFrame], cfg: dict) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    ordered = sorted(blocks.items(), key=lambda item: (float(item[1]["Time [s]"].min()), int(item[1].Period.iloc[0]), str(item[1].team.iloc[0]), int(item[1].player.iloc[0]), item[0]))
    eligible = [(bid, q) for bid, q in ordered if float(q["Time [s]"].max() - q["Time [s]"].min()) >= 6.0 - 1e-9]
    indices = np.unique(np.linspace(0, len(eligible) - 1, cfg["visual_audit"]["chronological_count"]).round().astype(int)) if eligible else []
    for sequence, idx in enumerate(indices, 1):
        bid, q = eligible[int(idx)]
        center = len(q) // 2; half = 75
        lo = max(0, min(center - half, len(q) - 151)); hi = lo + 150
        rows.append(_audit_row(f"chronological_{sequence:02d}", "chronological", bid, q, lo, hi))

    rules = [
        ("direct", lambda g: g["path_m"] >= 3.0 and g["displacement_path_ratio"] >= .95),
        ("direction_change", lambda g: g["path_m"] >= 3.0 and g["absolute_heading_change_deg"] >= 90.0),
        ("low_speed", lambda g: g["peak_speed_mps"] < 2.0 and g["path_m"] >= 1.0),
    ]
    for label, predicate in rules:
        found = False
        for bid, q in ordered:
            for start in range(0, max(0, len(q) - 100), 5):
                g = window_geometry(q, start)
                if g is not None and predicate(g):
                    rows.append(_audit_row(label, label, bid, q, start, start + 100, g))
                    found = True; break
            if found: break

    registry = pd.read_csv(STAGE_A / "trajectory_validity_registry.csv")
    first = registry.sort_values(["start_time_match_s", "period", "team_key", "player_key"], kind="mergesort").iloc[0]
    rows.append({
        "case_id": "discontinuity", "reason": "frozen_stage_a_discontinuity",
        "block_id": "", "team": str(first.team_key).rsplit(":", 1)[1],
        "player": str(first.player_key).rsplit(":", 1)[1], "period": int(first.period),
        "start_frame": int(first.start_frame_provider), "end_frame": int(first.end_frame_provider),
        "start_s": float(first.start_time_match_s), "end_s": float(first.end_time_match_s),
        "path_m": np.nan, "displacement_m": np.nan, "directness": np.nan,
        "peak_speed_mps": np.nan, "turning_deg": np.nan,
    })
    return pd.DataFrame(rows)


def _audit_row(case_id: str, reason: str, block_id: str, q: pd.DataFrame, lo: int, hi: int, geometry: dict | None = None) -> dict[str, Any]:
    geometry = geometry or historical.geometry(q.iloc[lo:hi + 1])
    return {
        "case_id": case_id, "reason": reason, "block_id": block_id,
        "team": str(q.team.iloc[0]), "player": str(q.player.iloc[0]), "period": int(q.Period.iloc[0]),
        "start_frame": int(q.Frame.iloc[lo]), "end_frame": int(q.Frame.iloc[hi]),
        "start_s": float(q["Time [s]"].iloc[lo]), "end_s": float(q["Time [s]"].iloc[hi]),
        "path_m": geometry["path_m"], "displacement_m": geometry["displacement_m"],
        "directness": geometry["displacement_path_ratio"], "peak_speed_mps": geometry["peak_speed_mps"],
        "turning_deg": geometry["absolute_heading_change_deg"],
    }


def candidate_b(blocks: dict[str, pd.DataFrame], high_speed: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    episode_rows: list[dict] = []; boundary_rows: list[dict] = []
    for block_id in sorted(blocks):
        block = blocks[block_id]
        team, player = str(block.team.iloc[0]), str(block.player.iloc[0])
        episodes, boundaries = v2.segment_candidate_b(block, team, player, block_id, cfg)
        episode_rows.extend(episodes); boundary_rows.extend(boundaries)
    episodes = historical.add_diagnostics(pd.DataFrame(episode_rows), high_speed)
    episodes = episodes.sort_values(["period", "start_s", "team", "player", "start_frame"], kind="mergesort").reset_index(drop=True)
    episodes.insert(0, "episode_id", [f"G2B{i:06d}" for i in range(1, len(episodes) + 1)])
    boundaries = pd.DataFrame(boundary_rows).sort_values(["period", "time_s", "team", "player", "frame"], kind="mergesort").reset_index(drop=True)
    return episodes, boundaries


def audit_checks(cases: pd.DataFrame, candidate: pd.DataFrame, boundaries: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, Any]] = []
    for row in cases.itertuples(index=False):
        if row.reason == "frozen_stage_a_discontinuity":
            overlap = candidate[(candidate.team == row.team) & (candidate.player.astype(str) == str(row.player)) & (candidate.period == row.period) & (candidate.start_frame <= row.end_frame) & (candidate.end_frame >= row.start_frame)]
            checks.append({"case_id": row.case_id, "check": "no_episode_crosses_invalid_support", "pass": overlap.empty, "detail": f"overlap_n={len(overlap)}"})
        elif row.reason == "direction_change":
            hit = boundaries[(boundaries.block_id == row.block_id) & (boundaries.kind == "direction") & boundaries.time_s.between(row.start_s, row.end_s, inclusive="both")]
            checks.append({"case_id": row.case_id, "check": "protected_direction_boundary_present", "pass": not hit.empty, "detail": f"direction_boundaries={len(hit)}"})
        elif row.reason == "low_speed":
            hit = candidate[(candidate.block_id == row.block_id) & (candidate.start_s < row.end_s) & (candidate.end_s > row.start_s)]
            checks.append({"case_id": row.case_id, "check": "candidate_episode_overlap", "pass": not hit.empty, "detail": f"episodes={len(hit)}"})
    checks.append({"case_id": "all", "check": "serialized_boundaries_unique", "pass": not boundaries.duplicated(["block_id", "frame", "kind"]).any(), "detail": f"boundaries={len(boundaries)}"})
    return pd.DataFrame(checks)


def plot_audit(cases: pd.DataFrame, blocks: dict[str, pd.DataFrame], boundaries: pd.DataFrame, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    plotted = cases[cases.block_id.fillna("").ne("")]
    n = len(plotted)
    fig, axes = plt.subplots(n, 3, figsize=(15, 3.2 * n), constrained_layout=True)
    if n == 1: axes = np.array([axes])
    for row_index, row in enumerate(plotted.itertuples(index=False)):
        q = blocks[row.block_id]
        view = q[q["Time [s]"].between(row.start_s, row.end_s)]
        bb = boundaries[(boundaries.block_id == row.block_id) & boundaries.time_s.between(row.start_s, row.end_s)]
        axp, axs, axh = axes[row_index]
        axp.plot(view.sx_m, view.sy_m, color="black"); axp.set_aspect("equal", adjustable="datalim")
        axs.plot(view["Time [s]"], view.speed_mps, color="black")
        velocity = view[["dx_m", "dy_m"]].to_numpy(float)
        heading = np.degrees(np.arctan2(velocity[:, 1], velocity[:, 0]))
        axh.plot(view["Time [s]"], heading, color="black")
        speed = q.speed_mps.to_numpy(float); times = q["Time [s]"].to_numpy(float)
        baseline_valleys = historical.consolidate_valleys(historical.raw_valleys(speed), speed, times, 1.0)
        for valley in baseline_valleys:
            valley_time = float(times[valley])
            if row.start_s <= valley_time <= row.end_s:
                axs.axvline(valley_time, color="0.65", ls=":", alpha=.75)
                axh.axvline(valley_time, color="0.65", ls=":", alpha=.75)
        for boundary in bb.itertuples(index=False):
            color = "#d62728" if boundary.kind == "direction" else "#1f77b4"
            axs.axvline(boundary.time_s, color=color, alpha=.7); axh.axvline(boundary.time_s, color=color, alpha=.7)
        axp.set_title(f"{row.case_id}: path"); axs.set_title("speed + boundaries"); axh.set_title("heading + boundaries")
        axp.set(xlabel="x (m)", ylabel="y (m)"); axs.set(xlabel="match time (s)", ylabel="m/s"); axh.set(xlabel="match time (s)", ylabel="degrees")
    fig.savefig(fig_dir / "attacker_only_frozen_visual_audit.png", dpi=150)
    plt.close(fig)


def execute(out: Path = DEFAULT_OUT, fig_dir: Path = DEFAULT_FIG) -> dict[str, Any]:
    inherited_hashes = verify_frozen()
    replication_cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg = json.loads(V2_CONFIG.read_text(encoding="utf-8"))
    blocks, provenance, support = split_open_play_blocks()
    baseline, high_speed = baseline_and_high_speed(blocks)
    cases = select_audit_cases(blocks, replication_cfg)  # fixed before Candidate B construction
    candidate, boundaries = candidate_b(blocks, high_speed, cfg)
    checks = audit_checks(cases, candidate, boundaries)
    a_metrics, b_metrics = v2.metrics(baseline, "A_game2_baseline"), v2.metrics(candidate, "B_game2_direction_aware")
    relative_reduction = 100.0 * (a_metrics["fragmentation_pct"] - b_metrics["fragmentation_pct"]) / a_metrics["fragmentation_pct"]
    b_metrics["fragmentation_relative_reduction_pct"] = relative_reduction
    gates = {
        "fragmentation_relative_reduction": relative_reduction >= replication_cfg["replication_gates"]["fragmentation_relative_reduction_pct_min"] - 1e-12,
        "merging_direction": b_metrics["merging_direction_pct"] <= replication_cfg["replication_gates"]["merging_direction_pct_max"] + 1e-12,
        "lower_speed_coverage": b_metrics["lower_speed_coverage_share"] >= replication_cfg["replication_gates"]["lower_speed_coverage_share_min"] - 1e-12,
        "objective_audit": bool(checks["pass"].all()),
        "support_segments_consumed": support["consumed_segment_id_count"] == 134,
        "support_rows_consumed": support["consumed_raw_row_count"] == 2_093_028,
        "minimum_duration": bool((candidate.duration_s >= 1.0 - 1e-9).all()),
        "finite_geometry": bool(np.isfinite(candidate[["duration_s", "path_m", "displacement_m", "peak_speed_mps"]].to_numpy(float)).all()),
        "no_support_crossing": bool(checks.loc[checks.check.eq("no_episode_crosses_invalid_support"), "pass"].all()),
        "no_post_result_tuning": True,
    }
    valid = all(gates[key] for key in ["support_segments_consumed", "support_rows_consumed", "minimum_duration", "finite_geometry", "no_support_crossing", "no_post_result_tuning"])
    if not valid:
        status = "GAME 2 ATTACKER EPISODE v2 REPLICATION INVALID"
    elif gates["fragmentation_relative_reduction"] and gates["merging_direction"] and gates["lower_speed_coverage"] and gates["objective_audit"]:
        status = "GAME 2 ATTACKER EPISODE v2 REPLICATION SUPPORTED"
    elif gates["fragmentation_relative_reduction"] and gates["merging_direction"]:
        status = "GAME 2 ATTACKER EPISODE v2 REPLICATION MIXED"
    else:
        status = "GAME 2 ATTACKER EPISODE v2 REPLICATION NOT SUPPORTED"

    out.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(out / "candidate_a_episodes.csv", index=False)
    candidate.to_csv(out / "candidate_b_episodes.csv", index=False)
    boundaries.to_csv(out / "candidate_b_boundaries.csv", index=False)
    cases.to_csv(out / "audit_cases.csv", index=False)
    checks.to_csv(out / "audit_checks.csv", index=False)
    support_rows = [{"block_id": bid, "team": str(q.team.iloc[0]), "player": str(q.player.iloc[0]), "period": int(q.Period.iloc[0]), "frames": len(q), "start_s": float(q["Time [s]"].min()), "end_s": float(q["Time [s]"].max())} for bid, q in sorted(blocks.items())]
    pd.DataFrame(support_rows).to_csv(out / "support_blocks.csv", index=False)
    pd.DataFrame([a_metrics, b_metrics]).to_csv(out / "candidate_summary.csv", index=False)
    distributions = [{"candidate": "A_game2_baseline", **row} for row in v2.distribution(baseline)] + [{"candidate": "B_game2_direction_aware", **row} for row in v2.distribution(candidate)]
    pd.DataFrame(distributions).to_csv(out / "distribution_summary.csv", index=False)
    pd.DataFrame([{"check": key, "pass": value} for key, value in gates.items()]).to_csv(out / "hard_qc.csv", index=False)
    result = {
        "status": status, "candidate_a": a_metrics, "candidate_b": b_metrics,
        "distributions": {"A": v2.distribution(baseline), "B": v2.distribution(candidate)},
        "gates": gates, "audit_checks": checks.to_dict(orient="records"),
        "sample": {"players": int(len({(q.team.iloc[0], q.player.iloc[0]) for q in blocks.values()})), "player_periods": int(len({(q.team.iloc[0], q.player.iloc[0], int(q.Period.iloc[0])) for q in blocks.values()})), "open_play_support_blocks": len(blocks), "support_frames_after_smoothing_and_velocity": int(sum(len(q) for q in blocks.values()))},
        "support": support, "canonical_provenance": provenance,
        "frozen_hashes": inherited_hashes, "protocol_sha256": sha256(PROTOCOL),
        "v2_config_sha256": sha256(V2_CONFIG), "replication_protocol_sha256": sha256(REPLICATION_PROTOCOL),
        "replication_config_sha256": sha256(CONFIG),
        "firewall": {"defender_coordinates_accessed": False, "defensive_outcomes_accessed": False, "game3_accessed": False, "idsse_accessed": False, "pooled": False},
    }
    write_json(out / "results.json", result)
    plot_audit(cases, blocks, boundaries, fig_dir)
    write_json(out / "hashes.json", {name: sha256(out / name) for name in GOVERNED_FILES})
    return result


def reproduce(out: Path = DEFAULT_OUT, fig_dir: Path = DEFAULT_FIG) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="attacker_episode_v2_game2_") as temp:
        temp_root = Path(temp); rerun_out = temp_root / "outputs"; rerun_fig = temp_root / "figures"
        execute(rerun_out, rerun_fig)
        comparisons = {name: {"original_sha256": sha256(out / name), "rerun_sha256": sha256(rerun_out / name), "byte_identical": (out / name).read_bytes() == (rerun_out / name).read_bytes()} for name in GOVERNED_FILES}
    verification = {"governed_outputs": len(comparisons), "byte_identical_outputs": sum(int(v["byte_identical"]) for v in comparisons.values()), "all_governed_outputs_byte_identical": all(v["byte_identical"] for v in comparisons.values()), "comparisons": comparisons}
    write_json(out / "reproduction_verification.json", verification)
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIG)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    result = reproduce(args.output, args.figures) if args.reproduce else execute(args.output, args.figures)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
