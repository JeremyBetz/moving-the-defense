"""Post-Phase-5B Measurement Audit A: direction and response onset.

This is a descriptive Metrica Sample Game 1 audit. It does not fit a model,
select opponents, classify responses, or define an onset threshold.
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
OUT = ROOT / "outputs" / "post5b_measurement_audit_a"
FIG = ROOT / "figures" / "post5b_measurement_audit_a"
LENGTH_M, WIDTH_M, FPS = 105.0, 68.0, 25.0
HORIZONS_S = (0.4, 0.8, 1.2)
GOALKEEPER = {"Home": "11", "Away": "25"}

ANCHORS = [
    {"case": "1888_translation", "label": "1888–1896 coordinated collective movement", "period": 1, "start": 1888.0, "end": 1896.0, "team": "Home", "focal": "2", "tau": 1892.0},
    {"case": "590_excursion", "label": "590–598 apparent focal excursion", "period": 1, "start": 590.0, "end": 598.0, "team": "Home", "focal": "2", "tau": 594.0},
    {"case": "550_tackle", "label": "550.76–555.76 tackle/engagement", "period": 1, "start": 550.76, "end": 555.76, "team": "Away", "focal": "16", "tau": 550.76},
    {"case": "1230_interior", "label": "1228.12–1232.12 interior-threat anchor", "period": 1, "start": 1228.12, "end": 1232.12, "team": "Away", "focal": "19", "tau": 1230.12},
    {"case": "1232_accommodation", "label": "1229.28–1234.28 accommodation sequence", "period": 1, "start": 1229.28, "end": 1234.28, "team": "Away", "focal": "19", "tau": 1232.28},
    {"case": "3682_translation", "label": "3679.88–3684.88 collective-translation contrast", "period": 2, "start": 3679.88, "end": 3684.88, "team": "Home", "focal": "8", "tau": 3682.88},
    {"case": "4197_negative", "label": "4195.04–4199.04 heterogeneous negative", "period": 2, "start": 4195.04, "end": 4199.04, "team": "Away", "focal": "16", "tau": 4197.04},
]

# Predeclared before viewing audit figures:
# 8 s windows at 300 s grid points from 300 through 5700 s. Exclude a window
# if it crosses periods, overlaps an anchor, or contains a SET PIECE/BALL OUT
# event from start-2 s through end. Team alternates by original grid index.
# Focal is the lowest numeric non-GK ID with complete required support.
NEUTRAL_GRID_STARTS = tuple(range(300, 5701, 300))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tracking(path: Path, team: str) -> tuple[pd.DataFrame, list[str]]:
    header = pd.read_csv(path, header=None, nrows=3)
    ids = [str(int(float(v))) for v in header.iloc[1, 3:-2:2] if pd.notna(v)]
    columns = ["Period", "Frame", "Time [s]"]
    for player in ids:
        columns += [f"{team}_{player}_x", f"{team}_{player}_y"]
    columns += [f"{team}_ball_x", f"{team}_ball_y"]
    return pd.read_csv(path, skiprows=3, names=columns), ids


def outfield(players: dict[str, list[str]], team: str) -> list[str]:
    return [p for p in players[team] if p != GOALKEEPER[team]]


def overlaps(a0: float, a1: float, b0: float, b1: float) -> bool:
    return a0 < b1 and a1 > b0


def choose_neutrals(
    tracking: dict[str, pd.DataFrame], players: dict[str, list[str]], events: pd.DataFrame
) -> tuple[list[dict], pd.DataFrame]:
    periods = {
        int(period): (float(g["Time [s]"].min()), float(g["Time [s]"].max()))
        for period, g in tracking["Home"].groupby("Period")
    }
    chosen, audit = [], []
    for grid_index, start in enumerate(NEUTRAL_GRID_STARTS, start=1):
        end = float(start + 8)
        period = next((p for p, (lo, hi) in periods.items() if start >= lo and end <= hi), None)
        anchor_overlap = any(overlaps(start, end, a["start"], a["end"]) for a in ANCHORS)
        restart = bool((
            events["Type"].isin(["SET PIECE", "BALL OUT"])
            & events["Start Time [s]"].between(start - 2.0, end, inclusive="both")
        ).any())
        team = "Home" if grid_index % 2 else "Away"
        reason = "selected"
        focal = None
        if period is None:
            reason = "period_boundary"
        elif anchor_overlap:
            reason = "anchor_overlap"
        elif restart:
            reason = "restart_or_ball_out"
        else:
            support = tracking[team][
                (tracking[team]["Period"] == period)
                & tracking[team]["Time [s]"].between(start - 2.0, end + max(HORIZONS_S))
            ]
            for candidate in sorted(outfield(players, team), key=int):
                refs = [p for p in outfield(players, team) if p != candidate]
                focal_ok = support[[f"{team}_{candidate}_x", f"{team}_{candidate}_y"]].notna().all().all()
                ref_count = pd.concat(
                    [support[[f"{team}_{p}_x", f"{team}_{p}_y"]].notna().all(axis=1) for p in refs], axis=1
                ).sum(axis=1)
                if focal_ok and bool((ref_count >= 8).all()):
                    focal = candidate
                    break
            if focal is None:
                reason = "insufficient_tracking_support"
            else:
                chosen.append({"case": f"neutral_{start}", "label": f"Neutral {start}–{end}s", "period": period, "start": float(start), "end": end, "team": team, "focal": focal, "tau": float(start + 4), "grid_index": grid_index})
        audit.append({"grid_index": grid_index, "start_s": start, "end_s": end, "period": period, "team": team, "selected": reason == "selected", "reason": reason, "focal": focal})
    return chosen, pd.DataFrame(audit)


def construct_series(case: dict, tracking: dict[str, pd.DataFrame], players: dict[str, list[str]]) -> pd.DataFrame:
    team, focal = case["team"], case["focal"]
    refs = [p for p in outfield(players, team) if p != focal]
    d = tracking[team]
    w = d[(d["Period"] == case["period"]) & d["Time [s]"].between(case["start"] - 2.0, case["end"] + max(HORIZONS_S))].copy()
    w["focal_x_m"] = w[f"{team}_{focal}_x"] * LENGTH_M
    w["focal_y_m"] = w[f"{team}_{focal}_y"] * WIDTH_M
    w["centroid_x_m"] = w[[f"{team}_{p}_x" for p in refs]].mean(axis=1) * LENGTH_M
    w["centroid_y_m"] = w[[f"{team}_{p}_y" for p in refs]].mean(axis=1) * WIDTH_M
    w["rel_x_m"] = w["focal_x_m"] - w["centroid_x_m"]
    w["rel_y_m"] = w["focal_y_m"] - w["centroid_y_m"]
    w["rel_dx_m"] = w["rel_x_m"].diff()
    w["rel_dy_m"] = w["rel_y_m"].diff()
    base = ["focal_x_m", "focal_y_m", "centroid_x_m", "centroid_y_m", "rel_x_m", "rel_y_m"]
    for col in base:
        w[f"{col}_causal7"] = w[col].rolling(7, min_periods=7).mean()
    dt = w["Time [s]"].diff()
    for prefix in ("focal", "centroid", "rel"):
        for axis in ("x", "y"):
            w[f"{prefix}_v{axis}_mps"] = w[f"{prefix}_{axis}_m_causal7"].diff() / dt
        w[f"{prefix}_speed_mps"] = np.hypot(w[f"{prefix}_vx_mps"], w[f"{prefix}_vy_mps"])
    for horizon in HORIZONS_S:
        frames = int(round(horizon * FPS))
        for axis in ("x", "y"):
            observed = w[f"rel_{axis}_m_causal7"].shift(-frames)
            predicted = w[f"rel_{axis}_m_causal7"] + w[f"rel_v{axis}_mps"] * horizon
            w[f"innovation_{axis}_{horizon:.1f}s_m"] = observed - predicted
        w[f"innovation_mag_{horizon:.1f}s_m"] = np.hypot(w[f"innovation_x_{horizon:.1f}s_m"], w[f"innovation_y_{horizon:.1f}s_m"])
    unit_x, unit_y = [], []
    for horizon in HORIZONS_S:
        mag = w[f"innovation_mag_{horizon:.1f}s_m"].replace(0, np.nan)
        unit_x.append(w[f"innovation_x_{horizon:.1f}s_m"] / mag)
        unit_y.append(w[f"innovation_y_{horizon:.1f}s_m"] / mag)
    w["innovation_horizon_direction_coherence"] = np.hypot(pd.concat(unit_x, axis=1).mean(axis=1), pd.concat(unit_y, axis=1).mean(axis=1))
    h08_mag = w["innovation_mag_0.8s_m"].replace(0, np.nan)
    h08_ux = w["innovation_x_0.8s_m"] / h08_mag
    h08_uy = w["innovation_y_0.8s_m"] / h08_mag
    # Forward five-frame resultant, aligned to the first frame. This is a
    # descriptive persistence view, not a thresholded onset decision.
    w["innovation_0.8s_next5_direction_coherence"] = np.hypot(
        h08_ux.rolling(5).mean().shift(-4), h08_uy.rolling(5).mean().shift(-4)
    )
    return w


def path_and_displacement(w: pd.DataFrame, case: dict, prefix: str) -> tuple[float, float, float, float, float]:
    q = w[w["Time [s]"].between(case["start"], case["end"])][["Time [s]", f"{prefix}_x_m", f"{prefix}_y_m"]].copy()
    q[["sx", "sy"]] = q[[f"{prefix}_x_m", f"{prefix}_y_m"]].rolling(7, center=True, min_periods=7).mean()
    q = q.dropna(subset=["sx", "sy"])
    increments = np.diff(q[["sx", "sy"]].to_numpy(), axis=0)
    path = float(np.linalg.norm(increments, axis=1).sum())
    delta = q[["sx", "sy"]].iloc[-1].to_numpy() - q[["sx", "sy"]].iloc[0].to_numpy()
    mag = float(np.linalg.norm(delta))
    angle = float(np.degrees(np.arctan2(delta[1], delta[0]))) if mag > 1e-9 else np.nan
    return path, float(delta[0]), float(delta[1]), mag, angle


def nearest_row(w: pd.DataFrame, t: float) -> pd.Series:
    return w.iloc[(w["Time [s]"] - t).abs().argmin()]


def summarize(case: dict, w: pd.DataFrame, kind: str) -> dict:
    rel = path_and_displacement(w, case, "rel")
    focal = path_and_displacement(w, case, "focal")
    centroid = path_and_displacement(w, case, "centroid")
    tau = nearest_row(w, case["tau"])
    row = {
        "kind": kind, "case": case["case"], "label": case["label"], "period": case["period"],
        "start_s": case["start"], "end_s": case["end"], "tau_s": float(tau["Time [s]"]), "team": case["team"], "focal": case["focal"],
        "relative_path_m": rel[0], "relative_displacement_x_m": rel[1], "relative_displacement_y_m": rel[2],
        "relative_displacement_m": rel[3], "relative_displacement_angle_deg": rel[4],
        "focal_absolute_path_m": focal[0], "centroid_path_m": centroid[0],
        "path_to_displacement_ratio": rel[0] / rel[3] if rel[3] > 1e-9 else np.nan,
    }
    for h in HORIZONS_S:
        row[f"innovation_x_{h:.1f}s_m"] = float(tau[f"innovation_x_{h:.1f}s_m"])
        row[f"innovation_y_{h:.1f}s_m"] = float(tau[f"innovation_y_{h:.1f}s_m"])
        row[f"innovation_mag_{h:.1f}s_m"] = float(tau[f"innovation_mag_{h:.1f}s_m"])
    row["innovation_horizon_direction_coherence"] = float(tau["innovation_horizon_direction_coherence"])
    row["innovation_0.8s_next5_direction_coherence"] = float(tau["innovation_0.8s_next5_direction_coherence"])
    before = w[w["Time [s]"].between(case["tau"] - 2.0, case["tau"])]
    row["pre_tau_relative_path_causal_m"] = float(np.hypot(before["rel_x_m_causal7"].diff(), before["rel_y_m_causal7"].diff()).sum())
    return row


def plot_case(case: dict, w: pd.DataFrame) -> None:
    q = w[w["Time [s]"].between(case["start"] - 2.0, case["end"])].copy()
    tau = nearest_row(w, case["tau"])
    fig = plt.figure(figsize=(15, 10), constrained_layout=True)
    gs = fig.add_gridspec(2, 3)
    ax_pitch = fig.add_subplot(gs[0, 0]); ax_rel = fig.add_subplot(gs[0, 1]); ax_vec = fig.add_subplot(gs[0, 2])
    ax_xy = fig.add_subplot(gs[1, 0]); ax_innov = fig.add_subplot(gs[1, 1]); ax_activity = fig.add_subplot(gs[1, 2])
    main = q[q["Time [s]"] >= case["start"]]
    ax_pitch.plot(main["focal_x_m"], main["focal_y_m"], color="#d62728", label=f"{case['team']} {case['focal']}")
    ax_pitch.plot(main["centroid_x_m"], main["centroid_y_m"], color="#1f77b4", label="leave-one-out centroid")
    ax_pitch.scatter([tau["focal_x_m"]], [tau["focal_y_m"]], color="black", marker="x", zorder=5, label="candidate τ")
    ax_pitch.set(xlim=(0, LENGTH_M), ylim=(0, WIDTH_M), xlabel="pitch x (m)", ylabel="pitch y (m)", title="Absolute pitch trajectories"); ax_pitch.set_aspect("equal"); ax_pitch.legend(fontsize=8)
    ax_rel.plot(main["rel_x_m"], main["rel_y_m"], color="#9467bd")
    ax_rel.scatter([tau["rel_x_m"]], [tau["rel_y_m"]], color="black", marker="x")
    ax_rel.set(xlabel="relative x (m)", ylabel="relative y (m)", title="Focal-minus-centroid trajectory"); ax_rel.set_aspect("equal", adjustable="datalim")
    h = 0.8
    origin = np.array([tau["rel_x_m_causal7"], tau["rel_y_m_causal7"]])
    pred = origin + np.array([tau["rel_vx_mps"], tau["rel_vy_mps"]]) * h
    obs = pred + np.array([tau[f"innovation_x_{h:.1f}s_m"], tau[f"innovation_y_{h:.1f}s_m"]])
    ax_vec.scatter(*origin, color="black", label="τ")
    ax_vec.arrow(*origin, *(pred-origin), color="#1f77b4", width=.03, length_includes_head=True, label="continuation")
    ax_vec.arrow(*origin, *(obs-origin), color="#d62728", width=.03, length_includes_head=True, label="observed")
    ax_vec.arrow(*pred, *(obs-pred), color="#2ca02c", width=.025, length_includes_head=True, label="innovation")
    ax_vec.set(xlabel="relative x (m)", ylabel="relative y (m)", title="0.8 s vector comparison"); ax_vec.set_aspect("equal", adjustable="datalim"); ax_vec.legend(fontsize=8)
    t = q["Time [s]"] - case["tau"]
    ax_xy.plot(t, q["rel_x_m_causal7"], label="relative x"); ax_xy.plot(t, q["rel_y_m_causal7"], label="relative y")
    ax_xy.axvspan(-2, 0, color="0.85", label="preceding 2 s"); ax_xy.axvline(0, color="black", ls="--"); ax_xy.set(xlabel="time from τ (s)", ylabel="metres", title="Directional relative position"); ax_xy.legend(fontsize=8)
    for horizon in HORIZONS_S: ax_innov.plot(t, q[f"innovation_mag_{horizon:.1f}s_m"], label=f"{horizon:.1f} s")
    ax_innov.axvspan(-2, 0, color="0.85"); ax_innov.axvline(0, color="black", ls="--"); ax_innov.set(xlabel="time from τ (s)", ylabel="innovation (m)", title="Continuation innovation"); ax_innov.legend(fontsize=8)
    ax_activity.plot(t, q["focal_speed_mps"], label="focal absolute speed", color="#d62728")
    ax_activity.plot(t, q["centroid_speed_mps"], label="centroid speed", color="#1f77b4")
    ax_activity.plot(t, q["rel_speed_mps"], label="focal-relative speed", color="#9467bd")
    ax_activity.axvspan(-2, 0, color="0.85"); ax_activity.axvline(0, color="black", ls="--"); ax_activity.set(xlabel="time from τ (s)", ylabel="m/s", title="Activity context"); ax_activity.legend(fontsize=8)
    cumulative = np.hypot(main["rel_x_m"].diff(), main["rel_y_m"].diff()).fillna(0).cumsum()
    ax_path = ax_activity.twinx()
    ax_path.plot(main["Time [s]"] - case["tau"], cumulative, color="black", ls=":", label="relative path accumulation")
    ax_path.set_ylabel("cumulative relative path (m)")
    fig.suptitle(case["label"] + " — geometric audit only", fontsize=14)
    fig.savefig(FIG / f"{case['case']}.png", dpi=160); plt.close(fig)


def plot_summary(summary: pd.DataFrame) -> None:
    colors = summary["kind"].map({"anchor": "#d62728", "neutral": "#1f77b4"})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    axes[0].scatter(summary["relative_path_m"], summary["relative_displacement_m"], c=colors)
    axes[0].set(xlabel="relative path (m)", ylabel="net displacement (m)", title="Path versus net displacement")
    axes[1].scatter(summary["focal_absolute_path_m"], summary["innovation_mag_0.8s_m"], c=colors)
    axes[1].set(xlabel="focal absolute path (m)", ylabel="0.8 s innovation at τ (m)", title="Activity versus innovation")
    axes[2].scatter(summary["centroid_path_m"], summary["innovation_mag_0.8s_m"], c=colors)
    axes[2].set(xlabel="centroid path (m)", ylabel="0.8 s innovation at τ (m)", title="Collective motion versus innovation")
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("Post-5B Measurement Audit A — anchors (red) and deterministic neutral windows (blue)")
    fig.savefig(FIG / "anchor_neutral_summary.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    anchor = summary[summary["kind"] == "anchor"]
    neutral = summary[summary["kind"] == "neutral"]
    ax.scatter(neutral["relative_displacement_x_m"], neutral["relative_displacement_y_m"], c="#1f77b4", label="neutral")
    ax.scatter(anchor["relative_displacement_x_m"], anchor["relative_displacement_y_m"], c="#d62728", label="anchor")
    for _, row in anchor.iterrows(): ax.annotate(row["case"], (row["relative_displacement_x_m"], row["relative_displacement_y_m"]), fontsize=8)
    ax.axhline(0, color="0.7"); ax.axvline(0, color="0.7"); ax.set_aspect("equal", adjustable="datalim")
    ax.set(xlabel="net relative x displacement (m)", ylabel="net relative y displacement (m)", title="Directional displacement preserves sign and axis"); ax.legend()
    fig.savefig(FIG / "directional_displacement_comparison.png", dpi=180); plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    home_path = DATA / "Sample_Game_1_RawTrackingData_Home_Team.csv"
    away_path = DATA / "Sample_Game_1_RawTrackingData_Away_Team.csv"
    event_path = DATA / "Sample_Game_1_RawEventsData.csv"
    home, home_ids = load_tracking(home_path, "Home"); away, away_ids = load_tracking(away_path, "Away")
    tracking = {"Home": home, "Away": away}; players = {"Home": home_ids, "Away": away_ids}; events = pd.read_csv(event_path)
    neutrals, neutral_audit = choose_neutrals(tracking, players, events)
    neutral_audit.to_csv(OUT / "neutral_window_selection_audit.csv", index=False)
    pd.DataFrame(neutrals).to_csv(OUT / "neutral_windows.csv", index=False)
    all_rows, time_rows = [], []
    for kind, cases in (("anchor", ANCHORS), ("neutral", neutrals)):
        for case in cases:
            w = construct_series(case, tracking, players)
            all_rows.append(summarize(case, w, kind))
            keep = w[w["Time [s]"].between(case["start"] - 2.0, case["end"])].copy()
            keep.insert(0, "kind", kind); keep.insert(1, "case", case["case"])
            cols = ["kind", "case", "Time [s]", "rel_x_m", "rel_y_m", "rel_dx_m", "rel_dy_m", "rel_x_m_causal7", "rel_y_m_causal7", "focal_speed_mps", "centroid_speed_mps", "rel_speed_mps", "innovation_horizon_direction_coherence", "innovation_0.8s_next5_direction_coherence"]
            cols += [f"innovation_{v}_{h:.1f}s_m" for h in HORIZONS_S for v in ("x", "y", "mag")]
            time_rows.append(keep[cols])
            if kind == "anchor": plot_case(case, w)
    summary = pd.DataFrame(all_rows)
    summary.to_csv(OUT / "window_summary.csv", index=False)
    pd.concat(time_rows, ignore_index=True).to_csv(OUT / "window_timeseries.csv", index=False)
    plot_summary(summary)
    manifest = {
        "audit": "Post-5B Measurement Audit A — direction and response onset",
        "data": "Metrica Sample Game 1 only", "metrica_game3_accessed": False,
        "horizons_s": list(HORIZONS_S), "fps": FPS, "pitch_m": [LENGTH_M, WIDTH_M],
        "continuation": "causal trailing-7-frame relative position; terminal one-frame velocity; constant-velocity projection",
        "neutral_rule": "8 s windows at 300 s grid points 300..5700; exclude period crossing, anchor overlap, or SET PIECE/BALL OUT in [start-2,end]; alternate team by original grid index; lowest numeric supported outfield focal",
        "neutral_count": len(neutrals), "anchor_count": len(ANCHORS),
        "input_sha256": {home_path.name: sha256(home_path), away_path.name: sha256(away_path), event_path.name: sha256(event_path)},
        "source_sha256": sha256(Path(__file__)),
    }
    (OUT / "execution_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    qc = {
        "anchor_count": len(ANCHORS), "neutral_count": len(neutrals), "horizons_s": list(HORIZONS_S),
        "all_anchor_summaries_finite": bool(np.isfinite(summary[summary.kind == "anchor"].select_dtypes(include=[np.number])).all().all()),
        "no_opponent_features": True, "no_model_fit": True, "no_threshold_fit": True,
        "metrica_game3_accessed": False,
    }
    qc["passed"] = all([qc["anchor_count"] == 7, 10 <= qc["neutral_count"] <= 20, qc["all_anchor_summaries_finite"], qc["no_opponent_features"], qc["no_model_fit"], qc["no_threshold_fit"], not qc["metrica_game3_accessed"]])
    (OUT / "qc_results.json").write_text(json.dumps(qc, indent=2) + "\n")
    print(json.dumps({"neutral_windows": len(neutrals), "anchors": len(ANCHORS), "qc_passed": qc["passed"]}, indent=2))


if __name__ == "__main__":
    main()
