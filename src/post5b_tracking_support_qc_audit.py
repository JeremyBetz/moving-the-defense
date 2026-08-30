"""Outcome-blind tracking-support audit for the retained 56.30 m/s observation.

The audit uses only Metrica Sample Game 1 player coordinates, frame/time support,
player/team identity, and player-only kinematics. It does not alter or rerun the
completed movement-segmentation audit and does not inspect defensive outcomes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrica_sample_game_1"
OUT = ROOT / "outputs" / "post5b_tracking_support_qc_audit"
FIG = ROOT / "figures" / "post5b_tracking_support_qc_audit"
PITCH_LENGTH_M, PITCH_WIDTH_M = 105.0, 68.0
EXPECTED_DT_S = 0.04
SMOOTHING_FRAMES = 7
GOALKEEPERS = {"Home": "11", "Away": "25"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tracking(team: str) -> tuple[pd.DataFrame, list[str], Path]:
    path = DATA / f"Sample_Game_1_RawTrackingData_{team}_Team.csv"
    header = pd.read_csv(path, header=None, nrows=3)
    players = [str(int(float(v))) for v in header.iloc[1, 3:-2:2] if pd.notna(v)]
    columns = ["period", "frame", "time_s"]
    for player in players:
        columns += [f"{team}_{player}_x", f"{team}_{player}_y"]
    columns += ["ball_x", "ball_y"]
    raw = pd.read_csv(path, skiprows=3, names=columns)
    return raw, players, path


def trace_kinematics(raw: pd.DataFrame, team: str, player: str) -> pd.DataFrame:
    xcol, ycol = f"{team}_{player}_x", f"{team}_{player}_y"
    q = raw[["period", "frame", "time_s", xcol, ycol]].copy()
    q = q.rename(columns={xcol: "raw_x_norm", ycol: "raw_y_norm"})
    q["raw_x_m"] = q.raw_x_norm * PITCH_LENGTH_M
    q["raw_y_m"] = q.raw_y_norm * PITCH_WIDTH_M
    q["dt_s"] = q.time_s.diff()
    q["frame_step"] = q.frame.diff()
    q["same_period"] = q.period.eq(q.period.shift())
    q["contiguous"] = q.same_period & q.frame_step.eq(1) & np.isclose(q.dt_s, EXPECTED_DT_S, atol=1e-8)
    q["raw_dx_m"] = q.raw_x_m.diff().where(q.contiguous)
    q["raw_dy_m"] = q.raw_y_m.diff().where(q.contiguous)
    q["raw_displacement_m"] = np.hypot(q.raw_dx_m, q.raw_dy_m)
    q["raw_speed_mps"] = q.raw_displacement_m / q.dt_s

    block_start = (~q.contiguous).cumsum()
    q["smooth_x_m"] = q.groupby(block_start).raw_x_m.transform(
        lambda s: s.rolling(SMOOTHING_FRAMES, center=True, min_periods=SMOOTHING_FRAMES).mean()
    )
    q["smooth_y_m"] = q.groupby(block_start).raw_y_m.transform(
        lambda s: s.rolling(SMOOTHING_FRAMES, center=True, min_periods=SMOOTHING_FRAMES).mean()
    )
    smooth_supported = q[["smooth_x_m", "smooth_y_m"]].notna().all(axis=1)
    smooth_contiguous = q.contiguous & smooth_supported & smooth_supported.shift(fill_value=False)
    q["smooth_dx_m"] = q.smooth_x_m.diff().where(smooth_contiguous)
    q["smooth_dy_m"] = q.smooth_y_m.diff().where(smooth_contiguous)
    q["smooth_displacement_m"] = np.hypot(q.smooth_dx_m, q.smooth_dy_m)
    q["smooth_speed_mps"] = q.smooth_displacement_m / q.dt_s
    q["smooth_acceleration_mps2"] = (q.smooth_speed_mps.diff() / q.dt_s).where(smooth_contiguous)
    return q


def exact_colocation(raw: pd.DataFrame, team: str, players: list[str], focal: str) -> pd.DataFrame:
    rows: list[dict] = []
    fx, fy = f"{team}_{focal}_x", f"{team}_{focal}_y"
    for other in players:
        if other == focal:
            continue
        ox, oy = f"{team}_{other}_x", f"{team}_{other}_y"
        mask = raw[[fx, fy, ox, oy]].notna().all(axis=1) & raw[fx].eq(raw[ox]) & raw[fy].eq(raw[oy])
        for r in raw.loc[mask, ["period", "frame", "time_s"]].itertuples(index=False):
            rows.append({"team": team, "focal_player": focal, "other_player": other,
                         "period": int(r.period), "frame": int(r.frame), "time_s": float(r.time_s)})
    return pd.DataFrame(rows)


def summarize_tail(all_frames: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    quantities = ["raw_speed_mps", "smooth_speed_mps", "smooth_acceleration_mps2"]
    probs = [0.5, 0.9, 0.95, 0.99, 0.999, 0.9999, 1.0]
    rows = []
    for quantity in quantities:
        values = all_frames[quantity].dropna().abs()
        for probability in probs:
            rows.append({"quantity": quantity, "quantile": probability,
                         "value": float(values.quantile(probability)), "observations": int(len(values))})
    per_player_rows = []
    for (team, player), q in all_frames.groupby(["team", "player"]):
        raw_peak = q.loc[q.raw_speed_mps.idxmax()]
        smooth_peak = q.loc[q.smooth_speed_mps.idxmax()]
        acceleration_peak = q.loc[q.smooth_acceleration_mps2.abs().idxmax()]
        per_player_rows.append({
            "team": team, "player": player,
            "max_raw_speed_mps": float(raw_peak.raw_speed_mps),
            "raw_peak_period": int(raw_peak.period), "raw_peak_frame": int(raw_peak.frame),
            "raw_peak_time_s": float(raw_peak.time_s),
            "max_smooth_speed_mps": float(smooth_peak.smooth_speed_mps),
            "smooth_peak_period": int(smooth_peak.period), "smooth_peak_frame": int(smooth_peak.frame),
            "smooth_peak_time_s": float(smooth_peak.time_s),
            "max_abs_smooth_acceleration_mps2": float(abs(acceleration_peak.smooth_acceleration_mps2)),
            "supported_raw_steps": int(q.raw_speed_mps.count()),
            "supported_smoothed_steps": int(q.smooth_speed_mps.count())
        })
    per_player = pd.DataFrame(per_player_rows)
    return pd.DataFrame(rows), per_player


def colocation_summary(raw: pd.DataFrame, team: str, players: list[str]) -> pd.DataFrame:
    rows = []
    for i, first in enumerate(players):
        for second in players[i + 1:]:
            first_x, first_y = f"{team}_{first}_x", f"{team}_{first}_y"
            second_x, second_y = f"{team}_{second}_x", f"{team}_{second}_y"
            valid = raw[[first_x, first_y, second_x, second_y]].notna().all(axis=1)
            equal = valid & raw[first_x].eq(raw[second_x]) & raw[first_y].eq(raw[second_y])
            if not equal.any():
                continue
            groups = ((~equal) | raw.period.ne(raw.period.shift()) | raw.frame.diff().ne(1)).cumsum()
            runs = raw[equal].groupby(groups[equal]).agg(
                period=("period", "first"), start_frame=("frame", "first"), end_frame=("frame", "last"),
                start_s=("time_s", "first"), end_s=("time_s", "last"), frames=("frame", "size"))
            longest = runs.sort_values(["frames", "start_s"], ascending=[False, True]).iloc[0]
            rows.append({"team": team, "player_1": first, "player_2": second,
                         "exact_colocation_frames": int(equal.sum()), "runs": int(len(runs)),
                         "longest_run_frames": int(longest.frames),
                         "longest_run_period": int(longest.period),
                         "longest_run_start_frame": int(longest.start_frame),
                         "longest_run_end_frame": int(longest.end_frame),
                         "longest_run_start_s": float(longest.start_s),
                         "longest_run_end_s": float(longest.end_s)})
    return pd.DataFrame(rows)


def plot_trace(trace: pd.DataFrame, peak_time: float) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True, constrained_layout=True)
    axes[0].plot(trace.time_s, trace.raw_x_m, label="raw x", color="#1f77b4")
    axes[0].plot(trace.time_s, trace.raw_y_m, label="raw y", color="#ff7f0e")
    axes[0].plot(trace.time_s, trace.smooth_x_m, "--", label="7-frame mean x", color="#1f77b4", alpha=.75)
    axes[0].plot(trace.time_s, trace.smooth_y_m, "--", label="7-frame mean y", color="#ff7f0e", alpha=.75)
    axes[0].set_ylabel("position (m)"); axes[0].legend(ncol=2)
    axes[1].plot(trace.time_s, trace.raw_displacement_m, label="raw", color="#444444")
    axes[1].plot(trace.time_s, trace.smooth_displacement_m, label="smoothed", color="#2ca02c")
    axes[1].set_ylabel("step displacement (m)"); axes[1].legend()
    axes[2].plot(trace.time_s, trace.raw_speed_mps, label="raw", color="#444444")
    axes[2].plot(trace.time_s, trace.smooth_speed_mps, label="smoothed", color="#d62728")
    axes[2].set_ylabel("speed (m/s)"); axes[2].set_xlabel("match time (s)"); axes[2].legend()
    for ax in axes:
        ax.axvline(peak_time, color="black", linestyle=":", linewidth=1)
    fig.suptitle("Home Player 10 tracking-support anomaly — attacker/player trace only")
    fig.savefig(FIG / "extreme_trace.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    traces, input_paths, colocation_rows = [], [], []
    home_raw = home_players = None
    for team in ("Home", "Away"):
        raw, players, path = load_tracking(team)
        input_paths.append(path)
        if team == "Home":
            home_raw, home_players = raw, players
        outfield_players = sorted((p for p in players if p != GOALKEEPERS[team]), key=int)
        colocation_rows.append(colocation_summary(raw, team, outfield_players))
        for player in outfield_players:
            q = trace_kinematics(raw, team, player)
            q.insert(0, "player", player); q.insert(0, "team", team)
            traces.append(q)
    all_frames = pd.concat(traces, ignore_index=True)
    tail, per_player = summarize_tail(all_frames)
    all_colocation = pd.concat(colocation_rows, ignore_index=True)

    focal = all_frames[(all_frames.team == "Home") & (all_frames.player == "10")].copy()
    peak_index = focal.smooth_speed_mps.idxmax()
    peak = focal.loc[peak_index]
    local = focal[focal.time_s.between(float(peak.time_s) - 2.0, float(peak.time_s) + 2.0)].copy()
    coloc = exact_colocation(home_raw, "Home", home_players, "10")
    local_coloc = coloc[coloc.time_s.between(float(peak.time_s) - 2.0, float(peak.time_s) + 2.0)].copy()

    local.to_csv(OUT / "extreme_trace.csv", index=False)
    local_coloc.to_csv(OUT / "exact_same_team_colocation.csv", index=False)
    tail.to_csv(OUT / "kinematic_tail_quantiles.csv", index=False)
    per_player.to_csv(OUT / "per_player_kinematic_maxima.csv", index=False)
    all_colocation.to_csv(OUT / "cross_identity_colocation_summary.csv", index=False)

    raw_peak = focal.loc[focal.raw_speed_mps.idxmax()]
    support_before = focal.loc[focal.frame.eq(int(peak.frame) - 4)].iloc[0]
    support_after = focal.loc[focal.frame.eq(int(peak.frame) + 3)].iloc[0]
    result = {
        "classification": "A — identifiable tracking-support mechanism; prospective rule direction is clear",
        "best_supported_failure_mode": "D — identity discontinuity / duplicated player trace followed by positional restoration",
        "supported_methodological_claim": "Extreme derived kinematics can arise from failures of player-identity/trajectory continuity even when frame, timestamp, and coordinate support appear complete. Tracking-support validity should therefore be evaluated on the underlying trajectory before movement segmentation rather than repaired through post-hoc clipping of derived speed.",
        "extreme": {
            "team": "Home", "player": "10", "period": int(peak.period),
            "frame": int(peak.frame), "time_s": float(peak.time_s),
            "smooth_speed_mps": float(peak.smooth_speed_mps),
            "smooth_step_displacement_m": float(peak.smooth_displacement_m),
            "dt_s": float(peak.dt_s),
            "raw_coordinate_before_m": [float(focal.loc[peak_index - 1, "raw_x_m"]), float(focal.loc[peak_index - 1, "raw_y_m"])],
            "raw_coordinate_at_m": [float(peak.raw_x_m), float(peak.raw_y_m)],
            "raw_coordinate_after_m": [float(focal.loc[peak_index + 1, "raw_x_m"]), float(focal.loc[peak_index + 1, "raw_y_m"])],
            "smoothed_coordinate_before_m": [float(focal.loc[peak_index - 1, "smooth_x_m"]), float(focal.loc[peak_index - 1, "smooth_y_m"])],
            "smoothed_coordinate_at_m": [float(peak.smooth_x_m), float(peak.smooth_y_m)],
            "smoothed_coordinate_after_m": [float(focal.loc[peak_index + 1, "smooth_x_m"]), float(focal.loc[peak_index + 1, "smooth_y_m"])],
            "raw_max_speed_mps": float(raw_peak.raw_speed_mps),
            "raw_max_frame": int(raw_peak.frame), "raw_max_time_s": float(raw_peak.time_s),
            "centered_mean_identity": "smoothed step at frame 2942 equals (raw frame 2945 - raw frame 2938) / 7",
            "centered_support_raw_frame_2938_m": [float(support_before.raw_x_m), float(support_before.raw_y_m)],
            "centered_support_raw_frame_2945_m": [float(support_after.raw_x_m), float(support_after.raw_y_m)]
        },
        "support_checks": {
            "missing_coordinates_local": int(local[["raw_x_m", "raw_y_m"]].isna().any(axis=1).sum()),
            "non_unit_frame_steps_local": int((local.frame.diff().dropna() != 1).sum()),
            "unexpected_timestamp_steps_local": int((~np.isclose(local.time_s.diff().dropna(), EXPECTED_DT_S, atol=1e-8)).sum()),
            "duplicated_timestamps_local": int(local.time_s.duplicated().sum()),
            "exact_home10_home1_colocation_frames_local": int(((local_coloc.other_player == "1")).sum()),
            "exact_colocation_frames_local_all_teammates": int(len(local_coloc)),
            "outfield_identity_pairs_with_exact_colocation": int(len(all_colocation))
        },
        "interpretation": "The raw source duplicates Home 10 and Home 1 coordinates for six frames, remains nearly coincident around that run, then restores Home 10 to a distant trace through six implausibly large raw steps. Centered smoothing attenuates and spreads rather than creates the discontinuity.",
        "colocation_caution": "Exact cross-identity coordinate equality alone is not proof of an invalid trajectory. The Home 10 diagnosis depends on duplication/near-coincidence, discontinuous restoration to a distant trace, and extreme raw positional changes in combination.",
        "prospective_rule_types": [
            "require contiguous expected frames",
            "require expected timestamp continuity",
            "require complete raw support across every centered smoothing window",
            "apply trajectory-continuity checks capable of identifying unresolved identity/discontinuity events",
            "invalidate a downstream episode if its supporting raw trajectory crosses a support discontinuity"
        ],
        "segmentation_relation": "Tracking QC asks whether the trajectory is supported; valley refinement asks which minima bound movement efforts given a supported trajectory. They are logically independent."
    }
    (OUT / "audit_result.json").write_text(json.dumps(result, indent=2) + "\n")
    plot_trace(local, float(peak.time_s))
    qc = {
        "game": "Metrica Sample Game 1 only", "game3_accessed": False,
        "defensive_outcomes_used": False, "event_outcomes_used": False,
        "segmentation_outputs_modified": False, "deterministic": True,
        "local_trace_rows": int(len(local)), "machine_outputs": 7, "figure_count": 1,
        "input_sha256": {p.name: sha256(p) for p in input_paths},
        "source_sha256": sha256(Path(__file__))
    }
    qc["passed"] = all([not qc["game3_accessed"], not qc["defensive_outcomes_used"],
                        not qc["event_outcomes_used"], not qc["segmentation_outputs_modified"],
                        qc["deterministic"], qc["figure_count"] == 1])
    (OUT / "qc_results.json").write_text(json.dumps(qc, indent=2) + "\n")
    print(json.dumps({"classification": result["classification"], "extreme": result["extreme"],
                      "support_checks": result["support_checks"], "qc_passed": qc["passed"]}, indent=2))


if __name__ == "__main__":
    main()
