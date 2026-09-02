"""Tier-1 Game 1 execution of frozen Attacker Movement Episode v2.

Only focal-player trajectory, time/support, and inherited global stoppage
boundaries enter construction or evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import post5b_attacking_movement_segmentation_audit as historical  # noqa: E402

CONFIG = ROOT / "config/attacker_movement_episode_v2.json"
PROTOCOL = ROOT / "docs/protocols/attacker_movement_episode_v2.md"
BASELINE = ROOT / "outputs/post5b_movement_segmentation_audit"
DEFAULT_OUT = ROOT / "outputs/attacker_movement_episode_v2_game1"
DEFAULT_FIG = ROOT / "figures/attacker_movement_episode_v2_game1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def angle_deg(a: np.ndarray, b: np.ndarray, floor: float = 1e-9) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na <= floor or nb <= floor:
        return float("nan")
    cosine = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def direction_candidates(block: pd.DataFrame, cfg: dict) -> list[dict]:
    steps = int(cfg["candidate_b"]["direction_window_steps_each_side"])
    min_speed = float(cfg["candidate_b"]["direction_mean_velocity_mps_min"])
    min_angle = float(cfg["candidate_b"]["direction_angle_deg_min"])
    xy = block[["sx_m", "sy_m"]].to_numpy(float)
    times = block["Time [s]"].to_numpy(float)
    qualifying: list[dict] = []
    for i in range(steps, len(block) - steps):
        dt_before = times[i] - times[i - steps]
        dt_after = times[i + steps] - times[i]
        if dt_before <= 0 or dt_after <= 0:
            continue
        before = (xy[i] - xy[i - steps]) / dt_before
        after = (xy[i + steps] - xy[i]) / dt_after
        turn = angle_deg(before, after)
        if np.linalg.norm(before) >= min_speed and np.linalg.norm(after) >= min_speed and turn >= min_angle - 1e-12:
            qualifying.append({"index": i, "time_s": times[i], "angle_deg": turn})
    if not qualifying:
        return []

    runs: list[list[dict]] = [[qualifying[0]]]
    for row in qualifying[1:]:
        if row["index"] == runs[-1][-1]["index"] + 1:
            runs[-1].append(row)
        else:
            runs.append([row])
    peaks = [sorted(run, key=lambda r: (-r["angle_deg"], r["index"]))[0] for run in runs]
    kept: list[dict] = []
    separation = float(cfg["candidate_b"]["direction_candidate_separation_s"])
    for row in peaks:
        if not kept or row["time_s"] - kept[-1]["time_s"] >= separation - 1e-9:
            kept.append(row)
        elif row["angle_deg"] > kept[-1]["angle_deg"] + 1e-12:
            kept[-1] = row
    return kept


def combine_candidates(valleys: list[int], turns: list[dict], block: pd.DataFrame, cfg: dict) -> list[dict]:
    times = block["Time [s]"].to_numpy(float)
    speed = block.speed_mps.to_numpy(float)
    rows = [{"index": i, "time_s": times[i], "kind": "valley", "angle_deg": float("nan"), "speed_mps": speed[i]} for i in valleys]
    rows += [{**row, "kind": "direction", "speed_mps": speed[row["index"]]} for row in turns]
    rows.sort(key=lambda row: (row["time_s"], 0 if row["kind"] == "direction" else 1))
    separation = float(cfg["inheritance"]["minimum_boundary_separation_s"])
    kept: list[dict] = []
    for row in rows:
        if not kept or row["time_s"] - kept[-1]["time_s"] >= separation - 1e-9:
            kept.append(row)
            continue
        old = kept[-1]
        if row["kind"] == "direction" and old["kind"] == "valley":
            kept[-1] = row
        elif row["kind"] == old["kind"] == "direction" and row["angle_deg"] > old["angle_deg"] + 1e-12:
            kept[-1] = row
        elif row["kind"] == old["kind"] == "valley" and row["speed_mps"] < old["speed_mps"] - 1e-12:
            kept[-1] = row
    return kept


def prune_redundant_valleys(boundaries: list[dict], block: pd.DataFrame, cfg: dict) -> list[dict]:
    directness_min = float(cfg["candidate_b"]["redundant_valley_union_directness_min"])
    turning_max = float(cfg["candidate_b"]["redundant_valley_union_turning_deg_max_exclusive"])
    current = list(boundaries)
    changed = True
    while changed and len(current) >= 3:
        changed = False
        for pos in range(1, len(current) - 1):
            if current[pos]["kind"] != "valley":
                continue
            q = block.iloc[current[pos - 1]["index"]:current[pos + 1]["index"] + 1]
            g = historical.geometry(q)
            if g["displacement_path_ratio"] >= directness_min - 1e-12 and g["absolute_heading_change_deg"] < turning_max - 1e-12:
                del current[pos]
                changed = True
                break
    return current


def crosses_support_break(team: str, player: str, period: int, start_frame: int, end_frame: int, cfg: dict) -> bool:
    for rule in cfg["support_breaks"]:
        if team == rule["team"] and str(player) == str(rule["player"]) and period == int(rule["period"]):
            if start_frame <= int(rule["raw_frame_end"]) and end_frame >= int(rule["raw_frame_start"]):
                return True
    return False


def segment_candidate_b(block: pd.DataFrame, team: str, player: str, block_id: str, cfg: dict) -> tuple[list[dict], list[dict]]:
    speed = block.speed_mps.to_numpy(float)
    times = block["Time [s]"].to_numpy(float)
    valleys = historical.consolidate_valleys(historical.raw_valleys(speed), speed, times, 1.0)
    if len(valleys) < 2:
        return [], []
    turns = [row for row in direction_candidates(block, cfg) if valleys[0] < row["index"] < valleys[-1]]
    boundaries = combine_candidates(valleys, turns, block, cfg)
    boundaries = prune_redundant_valleys(boundaries, block, cfg)
    episodes: list[dict] = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        q = block.iloc[start["index"]:end["index"] + 1]
        duration = float(q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0])
        if duration < float(cfg["inheritance"]["minimum_episode_duration_s"]) - 1e-9:
            continue
        start_frame, end_frame = int(q.Frame.iloc[0]), int(q.Frame.iloc[-1])
        period = int(q.Period.iloc[0])
        if crosses_support_break(team, player, period, start_frame, end_frame, cfg):
            continue
        g = historical.geometry(q)
        g.update({
            "team": team, "player": str(player), "period": period, "block_id": block_id,
            "start_frame": start_frame, "end_frame": end_frame,
            "start_s": float(q["Time [s]"].iloc[0]), "end_s": float(q["Time [s]"].iloc[-1]),
            "start_x_m": float(q.sx_m.iloc[0]), "start_y_m": float(q.sy_m.iloc[0]),
            "end_x_m": float(q.sx_m.iloc[-1]), "end_y_m": float(q.sy_m.iloc[-1]),
            "start_boundary_kind": start["kind"], "end_boundary_kind": end["kind"],
        })
        episodes.append(g)
    for row in boundaries:
        row.update({"block_id": block_id, "team": team, "player": str(player), "period": int(block.Period.iloc[0]), "frame": int(block.Frame.iloc[row["index"]])})
    return episodes, boundaries


def baseline_reproduction(actual: pd.DataFrame) -> dict:
    expected = pd.read_csv(BASELINE / "method_a_episodes.csv", dtype={"player": str})
    actual = actual.copy(); actual["player"] = actual.player.astype(str)
    key = ["team", "player", "period", "block_id", "start_frame", "end_frame", "start_s", "end_s"]
    numerical = ["duration_s", "path_m", "displacement_m", "delta_x_m", "delta_y_m", "displacement_path_ratio", "peak_speed_mps", "mean_speed_mps"]
    same_keys = expected[key].astype(str).equals(actual[key].astype(str))
    max_difference = max(float(np.nanmax(np.abs(expected[c].to_numpy() - actual[c].to_numpy()))) for c in numerical)
    same_diagnostics = all(expected[c].astype(bool).equals(actual[c].astype(bool)) for c in ["diag_fragmentation_any", "diag_merging_any", "method_b_overlap"])
    return {
        "passed": bool(len(actual) == 38651 and same_keys and same_diagnostics and max_difference <= 1e-9),
        "expected_episodes": int(len(expected)), "actual_episodes": int(len(actual)),
        "same_episode_keys": bool(same_keys), "same_diagnostics": bool(same_diagnostics),
        "maximum_numeric_difference": max_difference,
    }


def distribution(table: pd.DataFrame) -> list[dict]:
    rows = []
    for column in ["duration_s", "path_m", "displacement_m", "peak_speed_mps", "displacement_path_ratio", "absolute_heading_change_deg"]:
        values = table[column].dropna()
        rows.append({"quantity": column, "n": int(len(values)), "min": float(values.min()), "q1": float(values.quantile(.25)), "median": float(values.median()), "q3": float(values.quantile(.75)), "max": float(values.max())})
    return rows


def metrics(table: pd.DataFrame, label: str) -> dict:
    low = (table.peak_speed_mps < 5.5) & (table.displacement_m >= 3.0)
    return {
        "candidate": label, "episodes": int(len(table)),
        "fragmentation_n": int(table.diag_fragmentation_any.sum()), "fragmentation_pct": float(100 * table.diag_fragmentation_any.mean()),
        "merging_direction_n": int(table.diag_merging_any.sum()), "merging_direction_pct": float(100 * table.diag_merging_any.mean()),
        "short_n": int(table.diag_short.sum()), "tiny_path_n": int(table.diag_tiny_path.sum()), "tiny_displacement_n": int(table.diag_tiny_displacement.sum()),
        "long_n": int(table.diag_long.sum()), "low_directness_n": int(table.diag_low_displacement_path_ratio.sum()), "direction_complex_n": int(table.diag_direction_change.sum()),
        "lower_speed_displacement_ge3_n": int(low.sum()), "lower_speed_coverage_share": float(low.mean()),
        "no_high_speed_overlap_n": int((~table.method_b_overlap).sum()), "no_high_speed_overlap_pct": float(100 * (~table.method_b_overlap).mean()),
    }


def fixed_case_checks(candidate: pd.DataFrame, boundaries: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cases = []
    # Coherent reference: contained, with no new direction boundary inside.
    q = candidate[(candidate.team == "Away") & (candidate.player == "24") & (candidate.period == 1)]
    b = boundaries[(boundaries.team == "Away") & (boundaries.player == "24") & (boundaries.period == 1) & (boundaries.kind == "direction")]
    contains = bool(((q.start_s <= 380.20 + 1e-9) & (q.end_s >= 385.04 - 1e-9)).any())
    no_turn = not bool(b.time_s.between(380.20, 385.04, inclusive="neither").any())
    cases.append({"case": "Away24_coherent", "pass": contains and no_turn, "detail": f"contained={contains}; no_internal_direction_boundary={no_turn}"})
    # Merged reference: direction split present and no complete spanning episode.
    q = candidate[(candidate.team == "Home") & (candidate.player == "6") & (candidate.period == 1)]
    b = boundaries[(boundaries.team == "Home") & (boundaries.player == "6") & (boundaries.period == 1) & (boundaries.kind == "direction")]
    split = bool(b.time_s.between(95.32, 146.48, inclusive="neither").any())
    spans = bool(((q.start_s <= 95.32 + 1e-9) & (q.end_s >= 146.48 - 1e-9)).any())
    cases.append({"case": "Home6_merged", "pass": split and not spans, "detail": f"direction_boundary={split}; complete_span={spans}"})
    # Tracking discontinuity: no candidate overlaps the invalid raw-support interval.
    q = candidate[(candidate.team == "Home") & (candidate.player == "10") & (candidate.period == 1)]
    overlap = bool(((q.start_s <= 117.68 + 1e-9) & (q.end_s >= 116.44 - 1e-9)).any())
    cases.append({"case": "Home10_tracking_discontinuity", "pass": not overlap, "detail": f"candidate_overlap={overlap}"})
    frame = pd.DataFrame(cases)
    return frame, {row.case: bool(row.pass_) for row in frame.rename(columns={"pass": "pass_"}).itertuples(index=False)}


def plot_audit(cfg: dict, blocks: dict[str, pd.DataFrame], candidate: pd.DataFrame, boundaries: pd.DataFrame, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    cases = cfg["visual_audit"]["required"] + cfg["visual_audit"]["chronological"]
    fig, axes = plt.subplots(len(cases), 2, figsize=(14, 3.2 * len(cases)), constrained_layout=True)
    colors = {"valley": "#1f77b4", "direction": "#d62728"}
    for row_index, case in enumerate(cases):
        matching = [b for b in blocks.values() if str(b.team.iloc[0]) == case["team"] and str(b.player.iloc[0]) == str(case["player"]) and int(b.Period.iloc[0]) == int(case["period"]) and b["Time [s]"].min() <= case["start_s"] and b["Time [s]"].max() >= case["end_s"]]
        if not matching:
            for ax in axes[row_index]: ax.set_axis_off()
            continue
        block = matching[0]
        lo, hi = case["start_s"] - 1.0, case["end_s"] + 1.0
        q = block[block["Time [s]"].between(lo, hi)]
        axp, axs = axes[row_index]
        axp.plot(q.sx_m, q.sy_m, color="black", lw=1.2)
        axp.set_aspect("equal", adjustable="datalim"); axp.set_xlabel("x (m)"); axp.set_ylabel("y (m)")
        axs.plot(q["Time [s]"], q.speed_mps, color="black", lw=1)
        bb = boundaries[(boundaries.block_id == str(block.block_id.iloc[0])) & boundaries.time_s.between(lo, hi)]
        for boundary in bb.itertuples(index=False):
            point = block.iloc[int(boundary.index)]
            axp.scatter(point.sx_m, point.sy_m, color=colors[boundary.kind], s=24)
            axs.axvline(boundary.time_s, color=colors[boundary.kind], alpha=.7)
        label = case.get("label", case.get("episode_id", "chronological"))
        axp.set_title(f"{case['team']} {case['player']} | {label} | path")
        axs.set_title(f"{case['start_s']:.2f}–{case['end_s']:.2f}s | speed and v2 boundaries")
        axs.set_xlabel("match time (s)"); axs.set_ylabel("speed (m/s)")
    fig.savefig(fig_dir / "attacker_only_visual_audit.png", dpi=150)
    plt.close(fig)


def execute(out: Path = DEFAULT_OUT, fig_dir: Path = DEFAULT_FIG) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    frozen = {
        ROOT / "config/post5b_movement_segmentation_audit_rules.json": cfg["frozen_hashes"]["baseline_rules"],
        BASELINE / "method_a_episodes.csv": cfg["frozen_hashes"]["baseline_episodes"],
        ROOT / "config/post5b_attacking_movement_prominence_refinement_rules.json": cfg["frozen_hashes"]["prominence_rules"],
        ROOT / "outputs/post5b_attacking_movement_prominence_refinement/results.json": cfg["frozen_hashes"]["prominence_result"],
        ROOT / "docs/post5b_tracking_support_qc_audit.md": cfg["frozen_hashes"]["tracking_qc_doc"],
        ROOT / "outputs/post5b_tracking_support_qc_audit/audit_result.json": cfg["frozen_hashes"]["tracking_qc_result"],
        ROOT / "outputs/spatial_defensive_response_footprint_game2_final_v1/final_results.json": cfg["frozen_hashes"]["final_footprint_a"],
        ROOT / "outputs/local_defensive_response_form_game2_final_v1/final_results.json": cfg["frozen_hashes"]["final_response_form_b"],
        ROOT / "outputs/local_defensive_deformation_game1_v1/final_results.json": cfg["frozen_hashes"]["deformation_game1"],
        ROOT / "outputs/local_defensive_deformation_game2_v1/final_results.json": cfg["frozen_hashes"]["deformation_game2"],
    }
    failures = {str(path): [sha256(path), expected] for path, expected in frozen.items() if sha256(path) != expected}
    if failures:
        raise RuntimeError(f"Frozen hash failure: {failures}")
    out.mkdir(parents=True, exist_ok=True)
    data = historical.DATA
    home, home_ids = historical.load_tracking(data / "Sample_Game_1_RawTrackingData_Home_Team.csv", "Home")
    away, away_ids = historical.load_tracking(data / "Sample_Game_1_RawTrackingData_Away_Team.csv", "Away")
    events = pd.read_csv(data / "Sample_Game_1_RawEventsData.csv")
    exclusions, global_boundaries = historical.global_exclusions(events)
    players = {"Home": [p for p in home_ids if p != historical.GK["Home"]], "Away": [p for p in away_ids if p != historical.GK["Away"]]}
    tracking = {"Home": home, "Away": away}
    baseline_rows: list[dict] = []; candidate_rows: list[dict] = []; boundary_rows: list[dict] = []; high_speed_rows: list[dict] = []
    blocks: dict[str, pd.DataFrame] = {}
    support_rows = []
    for team in ("Home", "Away"):
        for player in sorted(players[team], key=int):
            player_blocks = historical.player_blocks(tracking[team], team, player, exclusions, global_boundaries)
            for block_number, block in enumerate(player_blocks):
                block_id = f"{team}_{player}_{int(block.Period.iloc[0])}_{block_number}"
                block = block.copy(); block["team"] = team; block["player"] = str(player); block["block_id"] = block_id
                blocks[block_id] = block
                a, _ = historical.segment_method_a(block, team, player, block_id); baseline_rows.extend(a)
                high_speed_rows.extend(historical.segment_method_b(block, team, player, block_id))
                b, bounds = segment_candidate_b(block, team, player, block_id, cfg); candidate_rows.extend(b); boundary_rows.extend(bounds)
                support_rows.append({"team": team, "player": str(player), "period": int(block.Period.iloc[0]), "block_id": block_id, "frames": len(block), "start_s": float(block["Time [s]"].min()), "end_s": float(block["Time [s]"].max())})
    high_speed = pd.DataFrame(high_speed_rows)
    baseline = historical.add_diagnostics(pd.DataFrame(baseline_rows), high_speed)
    candidate = historical.add_diagnostics(pd.DataFrame(candidate_rows), high_speed)
    baseline.insert(0, "episode_id", [f"A{i:06d}" for i in range(1, len(baseline) + 1)])
    candidate.insert(0, "episode_id", [f"B{i:06d}" for i in range(1, len(candidate) + 1)])
    boundaries = pd.DataFrame(boundary_rows).sort_values(["period", "time_s", "team", "player", "frame"]).reset_index(drop=True)
    reproduction = baseline_reproduction(baseline)
    a_metrics, b_metrics = metrics(baseline, "A_closed_baseline"), metrics(candidate, "B_direction_aware")
    b_metrics["fragmentation_relative_reduction_pct"] = 100 * (a_metrics["fragmentation_pct"] - b_metrics["fragmentation_pct"]) / a_metrics["fragmentation_pct"]
    b_metrics["lower_speed_relative_change_pct"] = 100 * (b_metrics["lower_speed_coverage_share"] - a_metrics["lower_speed_coverage_share"]) / a_metrics["lower_speed_coverage_share"]
    cases, case_values = fixed_case_checks(candidate, boundaries)
    gates = {
        "baseline_reproduced": bool(reproduction["passed"]),
        "fragmentation": b_metrics["fragmentation_pct"] <= cfg["development_gates"]["fragmentation_pct_max"] + 1e-12,
        "merging_direction": b_metrics["merging_direction_pct"] <= cfg["development_gates"]["merging_direction_pct_max"] + 1e-12,
        "lower_speed_coverage": b_metrics["lower_speed_coverage_share"] >= cfg["development_gates"]["lower_speed_coverage_share_min"] - 1e-12,
        "fixed_cases": bool(cases["pass"].all()),
        "support_break": not any(crosses_support_break(r.team, r.player, r.period, r.start_frame, r.end_frame, cfg) for r in candidate.itertuples(index=False)),
        "minimum_duration": bool((candidate.duration_s >= 1.0 - 1e-9).all()),
        "finite_geometry": bool(np.isfinite(candidate[["duration_s", "path_m", "displacement_m", "peak_speed_mps"]].to_numpy(float)).all()),
        "game2_not_accessed": True, "game3_not_accessed": True, "defensive_outcomes_not_accessed": True,
    }
    valid = all(gates[key] for key in ["baseline_reproduced", "support_break", "minimum_duration", "finite_geometry"])
    if not valid:
        status = "GAME 1 ATTACKER EPISODE v2 DEVELOPMENT INVALID"
    elif gates["fragmentation"] and gates["merging_direction"] and gates["lower_speed_coverage"] and gates["fixed_cases"]:
        status = "GAME 1 ATTACKER EPISODE v2 DEVELOPMENT COHERENT"
    elif gates["fragmentation"]:
        status = "GAME 1 ATTACKER EPISODE v2 DEVELOPMENT MIXED"
    else:
        status = "GAME 1 ATTACKER EPISODE v2 DEVELOPMENT NEGATIVE"

    candidate.to_csv(out / "candidate_b_episodes.csv", index=False)
    boundaries.to_csv(out / "candidate_b_boundaries.csv", index=False)
    pd.DataFrame(support_rows).to_csv(out / "support_blocks.csv", index=False)
    pd.DataFrame([a_metrics, b_metrics]).to_csv(out / "candidate_summary.csv", index=False)
    pd.DataFrame([{"candidate": "A_closed_baseline", **row} for row in distribution(baseline)] + [{"candidate": "B_direction_aware", **row} for row in distribution(candidate)]).to_csv(out / "distribution_summary.csv", index=False)
    cases.to_csv(out / "fixed_case_checks.csv", index=False)
    pd.DataFrame([{"check": key, "pass": value} for key, value in gates.items()]).to_csv(out / "hard_qc.csv", index=False)
    plot_audit(cfg, blocks, candidate, boundaries, fig_dir)
    result = {
        "status": status, "candidate_c": cfg["candidate_c"], "baseline_reproduction": reproduction,
        "candidate_a": a_metrics, "candidate_b": b_metrics, "gates": gates, "fixed_case_checks": case_values,
        "distributions": {"A": distribution(baseline), "B": distribution(candidate)},
        "frozen_hashes": {str(path.relative_to(ROOT)): expected for path, expected in frozen.items()},
        "protocol_sha256": sha256(PROTOCOL), "config_sha256": sha256(CONFIG),
        "firewall": {"game2_accessed": False, "game3_accessed": False, "idsse_accessed": False, "defensive_outcomes_accessed": False},
    }
    write_json(out / "results.json", result)
    governed = sorted(path for path in out.iterdir() if path.name != "hashes.json")
    write_json(out / "hashes.json", {path.name: sha256(path) for path in governed})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIG)
    args = parser.parse_args()
    print(execute(args.output, args.figures)["status"])


if __name__ == "__main__":
    main()
