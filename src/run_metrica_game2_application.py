"""Run the exploratory replay application over public Metrica Sample Game 2.

Outputs are local product artifacts, not governed scientific results. The
script scores both teams, discovers passages before viewing them, and aligns
the defending-team timeline to every recorded shot.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from defensive_reorganization_application import (
    EventWindowQuery,
    MomentDiscoverySpec,
    align_events,
    discover_moments,
    export_scores,
    query_event_windows,
    render_selected_passage,
    score_stable_runs,
)
from defensive_reorganization_replay import DefensiveReorganizationScores
from defensive_reorganization_replay_visualization import plot_defensive_reorganization_diagnostic
from tracking_animation import TrackingClipSpec


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrica_sample_game_2"
MATCH_ID = "metrica_sample_game_2"
SOURCE_FPS = 25.0
TEAM_FILES = {
    "metrica:Home": "Sample_Game_2_RawTrackingData_Home_Team.csv",
    "metrica:Away": "Sample_Game_2_RawTrackingData_Away_Team.csv",
}
GOALKEEPERS = {
    "metrica:Home": "metrica:Home:11",
    "metrica:Away": "metrica:Away:25",
}
CLIP_CONTEXT_SECONDS = 3.0
ANALYST_CLIP_CONTEXT_SECONDS = 5.0
ANALYST_INTERIOR_GUARD_SECONDS = 8.0
MAX_VISUAL_SPEED_MPS = 15.0
REVIEWED_PRIMARY_MOMENTS = {
    "high": ("metrica:Home", 1, 845.16),
    "rapid_increase": ("metrica:Home", 1, 335.68),
}


@dataclass(frozen=True)
class MetricaApplicationPreset:
    game_number: int
    match_id: str
    data_dir: Path
    team_files: dict[str, str]
    events_file: str
    reviewed_primary: dict[str, tuple[str, int, float]] | None = None


def metrica_sample_preset(
    game_number: int,
    *,
    data_dir: str | Path | None = None,
    reviewed_game2_case_study: bool = False,
) -> MetricaApplicationPreset:
    """Resolve one public Metrica sample match without changing analysis rules."""
    if game_number not in {1, 2}:
        raise ValueError("game_number must be 1 or 2")
    if reviewed_game2_case_study and game_number != 2:
        raise ValueError("reviewed identities exist only for the Game 2 case study")
    base = (
        ROOT / "data" / f"metrica_sample_game_{game_number}"
        if data_dir is None
        else Path(data_dir)
    )
    prefix = f"Sample_Game_{game_number}"
    return MetricaApplicationPreset(
        game_number=game_number,
        match_id=f"metrica_sample_game_{game_number}",
        data_dir=base,
        team_files={
            "metrica:Home": f"{prefix}_RawTrackingData_Home_Team.csv",
            "metrica:Away": f"{prefix}_RawTrackingData_Away_Team.csv",
        },
        events_file=f"{prefix}_RawEventsData.csv",
        reviewed_primary=(
            REVIEWED_PRIMARY_MOMENTS if reviewed_game2_case_study else None
        ),
    )


def _stoppage_intervals(events: pd.DataFrame) -> list[tuple[int, float, float]]:
    """Return provider-event dead-ball intervals ending at the next restart."""
    intervals: list[tuple[int, float, float]] = []
    for period, group in events.sort_values("Start Time [s]").groupby("Period"):
        rows = group.reset_index(drop=True)
        for index, row in rows.iterrows():
            subtype = str(row.get("Subtype", ""))
            starts_stoppage = (
                row["Type"] in {"BALL OUT", "FAULT RECEIVED", "CARD"}
                or (row["Type"] == "SHOT" and "GOAL" in subtype)
                or (row["Type"] == "BALL LOST" and "FORCED" in subtype)
            )
            if not starts_stoppage:
                continue
            next_restart = rows.loc[
                (rows.index > index) & rows["Type"].eq("SET PIECE"), "Start Time [s]"
            ]
            if not next_restart.empty:
                intervals.append(
                    (int(period), float(row["Start Time [s]"]), float(next_restart.iloc[0]))
                )
    return intervals


def audit_visual_suitability(
    moments: pd.DataFrame,
    tracking_by_team: dict[str, pd.DataFrame],
    events: pd.DataFrame,
    *,
    ball_tracking: pd.DataFrame | None = None,
    clip_context_seconds: float = CLIP_CONTEXT_SECONDS,
    max_visual_speed_mps: float = MAX_VISUAL_SPEED_MPS,
    source_fps: float = SOURCE_FPS,
) -> pd.DataFrame:
    """Flag restart/dead-ball and gross tracking-discontinuity clip candidates."""
    if max_visual_speed_mps <= 0 or clip_context_seconds <= 0:
        raise ValueError("visual suitability thresholds must be positive")
    tracking = pd.concat(tracking_by_team.values(), ignore_index=True)
    tracking = tracking.loc[
        tracking["entity_type"].eq("player")
        & ~tracking["player_key"].astype(str).isin(GOALKEEPERS.values())
    ].sort_values(["team_key", "player_key", "period", "time_match_s"], kind="mergesort")
    grouped = tracking.groupby(["team_key", "player_key", "period"], sort=False)
    dt = grouped["time_match_s"].diff()
    speed = np.hypot(grouped["x_m"].diff(), grouped["y_m"].diff()) / dt
    implausible = speed.gt(max_visual_speed_mps) | tracking["x_m"].abs().gt(52.5) | tracking[
        "y_m"
    ].abs().gt(34.0)
    bad_times = {
        int(period): np.sort(group.loc[implausible.loc[group.index], "time_match_s"].unique())
        for period, group in tracking.groupby("period", sort=False)
    }
    stoppages = _stoppage_intervals(events)
    restart_times = {
        int(period): np.sort(
            group.loc[
                group["Type"].isin({"SET PIECE", "BALL OUT"})
                | group["Subtype"].astype(str).str.contains(
                    "KICK OFF|GOAL KICK|THROW IN|FREE KICK|PENALTY", regex=True, na=False
                ),
                "Start Time [s]",
            ].to_numpy(float)
        )
        for period, group in events.groupby("Period", sort=False)
    }
    ball_times: dict[int, np.ndarray] = {}
    invalid_ball_times: dict[int, np.ndarray] = {}
    if ball_tracking is not None:
        for period, group in ball_tracking.groupby("period", sort=False):
            ball_times[int(period)] = np.sort(group["time_match_s"].to_numpy(float))
            invalid_ball_times[int(period)] = np.sort(
                group.loc[~group["coordinate_valid"].astype(bool), "time_match_s"].to_numpy(float)
            )
    result = moments.copy()
    reasons = []
    for row in result.itertuples(index=False):
        start = float(row.peak_time_s) - clip_context_seconds
        end = float(row.peak_time_s) + clip_context_seconds
        period_times = bad_times.get(int(row.period), np.array([], dtype=float))
        has_bad_tracking = np.searchsorted(period_times, end, side="right") > np.searchsorted(
            period_times, start, side="left"
        )
        reason = []
        if has_bad_tracking:
            reason.append("tracking_discontinuity_or_out_of_pitch")
        if any(
            period == int(row.period) and max(start, stop) <= min(end, restart)
            for period, stop, restart in stoppages
        ):
            reason.append("dead_ball_or_restart")
        period_restarts = restart_times.get(int(row.period), np.array([], dtype=float))
        if np.searchsorted(period_restarts, end, side="right") > np.searchsorted(
            period_restarts, start, side="left"
        ):
            reason.append("restart_event_in_clip")
        if ball_tracking is not None:
            expected_frames = int(round(2 * clip_context_seconds * source_fps)) + 1
            times = ball_times.get(int(row.period), np.array([], dtype=float))
            invalid = invalid_ball_times.get(int(row.period), np.array([], dtype=float))
            count = np.searchsorted(times, end, side="right") - np.searchsorted(
                times, start, side="left"
            )
            invalid_count = np.searchsorted(invalid, end, side="right") - np.searchsorted(
                invalid, start, side="left"
            )
            if count != expected_frames or invalid_count:
                reason.append("incomplete_ball_support")
        reasons.append(";".join(reason))
    result["visual_suitability_reason"] = reasons
    result["visual_suitable"] = result["visual_suitability_reason"].eq("")
    return result


def _clock_label(time_s: float) -> str:
    minutes = int(float(time_s) // 60)
    seconds = int(round(float(time_s) - 60 * minutes))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def _event_label(row: pd.Series) -> str:
    subtype = "" if pd.isna(row.get("Subtype")) else f" {row['Subtype']}"
    return f"{row['Team']} {row['Type']}{subtype}"


def classify_attacking_activity(
    *,
    possession_matches_attack: bool,
    ball_path_length_m: float,
    endpoint_change_m: float,
    directed_ball_progress_m: float,
    attacking_action_count: int,
    attacker_centroid_shift_m: float,
    attacker_shape_change_m: float,
) -> tuple[int, bool, dict[str, bool]]:
    """Apply the transparent analyst-window activity gate."""
    components = {
        "ball_path_15m": ball_path_length_m >= 15.0,
        "endpoint_change_10m": endpoint_change_m >= 10.0,
        "directed_progress_5m": directed_ball_progress_m >= 5.0,
        "two_attacking_actions": attacking_action_count >= 2,
        "attacker_centroid_shift_5m": attacker_centroid_shift_m >= 5.0,
        "attacker_shape_change_5m": attacker_shape_change_m >= 5.0,
    }
    score = int(sum(components.values()))
    on_ball_score = int(
        components["ball_path_15m"]
        + components["endpoint_change_10m"]
        + components["directed_progress_5m"]
        + components["two_attacking_actions"]
    )
    return score, bool(possession_matches_attack and on_ball_score >= 2), components


def add_analyst_context(
    moments: pd.DataFrame,
    tracking_by_team: dict[str, pd.DataFrame],
    ball_tracking: pd.DataFrame,
    events: pd.DataFrame,
    *,
    context_seconds: float = ANALYST_CLIP_CONTEXT_SECONDS,
) -> pd.DataFrame:
    """Add descriptive match, ball, event, and defensive-shape context."""
    result = moments.copy()
    records: list[dict[str, object]] = []
    event_rows = events.sort_values(["Period", "Start Time [s]"], kind="mergesort")
    for row in result.itertuples(index=False):
        period = int(row.period)
        peak = float(row.peak_time_s)
        start, end = peak - context_seconds, peak + context_seconds
        defending = str(row.team_key)
        attacking = "metrica:Away" if defending == "metrica:Home" else "metrica:Home"
        ball = ball_tracking.loc[
            ball_tracking["period"].eq(period)
            & ball_tracking["time_match_s"].between(start, end)
            & ball_tracking["coordinate_valid"].astype(bool)
        ].sort_values("time_match_s")
        at_peak = ball.iloc[(ball["time_match_s"] - peak).abs().argsort()[:1]]
        ball_x = float(at_peak.iloc[0]["x_m"]) if not at_peak.empty else np.nan
        if ball_x < -17.5:
            zone = "physical left third"
        elif ball_x > 17.5:
            zone = "physical right third"
        else:
            zone = "physical middle third"
        dx = float(ball.iloc[-1].x_m - ball.iloc[0].x_m) if len(ball) else np.nan
        dy = float(ball.iloc[-1].y_m - ball.iloc[0].y_m) if len(ball) else np.nan
        ball_path = float(
            np.hypot(ball["x_m"].diff(), ball["y_m"].diff()).iloc[1:].sum()
        )
        prior = event_rows.loc[
            event_rows["Period"].eq(period) & event_rows["Start Time [s]"].le(peak)
        ]
        following = event_rows.loc[
            event_rows["Period"].eq(period) & event_rows["Start Time [s]"].gt(peak)
        ]
        previous_event = (
            "none"
            if prior.empty
            else _event_label(prior.iloc[-1])
        )
        next_event = (
            "none"
            if following.empty
            else _event_label(following.iloc[0])
        )
        possession = "unknown" if prior.empty else f"metrica:{prior.iloc[-1]['Team']}"
        previous_offset = np.nan if prior.empty else float(prior.iloc[-1]["Start Time [s]"] - peak)
        next_offset = np.nan if following.empty else float(following.iloc[0]["Start Time [s]"] - peak)
        direction = "direction unavailable"
        if possession in tracking_by_team:
            goalkeeper = GOALKEEPERS[possession]
            keeper = tracking_by_team[possession].loc[
                tracking_by_team[possession]["period"].eq(period)
                & tracking_by_team[possession]["player_key"].eq(goalkeeper)
                & tracking_by_team[possession]["coordinate_valid"].astype(bool)
            ]
            if not keeper.empty:
                direction = (
                    "toward physical right"
                    if float(keeper.x_m.median()) < 0
                    else "toward physical left"
                )
        direction_sign = 1.0 if direction.endswith("right") else -1.0 if direction.endswith("left") else np.nan
        directed_ball_progress = float(direction_sign * dx) if np.isfinite(direction_sign) else np.nan
        clip_events = event_rows.loc[
            event_rows["Period"].eq(period)
            & event_rows["Start Time [s]"].between(start, end)
        ]
        attacking_provider = attacking.split(":")[-1]
        attacking_events = clip_events.loc[clip_events["Team"].eq(attacking_provider)]
        attacking_actions = int(
            attacking_events["Type"].isin(
                {"PASS", "CHALLENGE", "RECOVERY", "BALL LOST", "SHOT", "SET PIECE"}
            ).sum()
        )
        goals = event_rows.loc[
            event_rows["Start Time [s]"].le(peak)
            & event_rows["Type"].eq("SHOT")
            & event_rows["Subtype"].astype(str).str.contains("GOAL", na=False)
        ]
        home_goals = int(goals["Team"].eq("Home").sum())
        away_goals = int(goals["Team"].eq("Away").sum())

        defenders = tracking_by_team[defending].loc[
            tracking_by_team[defending]["period"].eq(period)
            & tracking_by_team[defending]["time_match_s"].between(start, end)
            & ~tracking_by_team[defending]["player_key"].eq(GOALKEEPERS[defending])
            & tracking_by_team[defending]["coordinate_valid"].astype(bool)
        ]
        shape = []
        for label, target in (("start", start), ("end", end)):
            frame = defenders.loc[
                np.isclose(defenders["time_match_s"], target, atol=1e-7, rtol=0)
            ].drop_duplicates("player_key")
            if len(frame) != 10:
                raise RuntimeError(
                    f"defensive {label} shape requires exactly ten outfield players"
                )
            shape.append(
                {
                    "label": label,
                    "width": float(frame.y_m.max() - frame.y_m.min()),
                    "depth": float(frame.x_m.max() - frame.x_m.min()),
                    "cx": float(frame.x_m.mean()),
                    "cy": float(frame.y_m.mean()),
                }
            )
        centroid_shift = float(
            np.hypot(shape[1]["cx"] - shape[0]["cx"], shape[1]["cy"] - shape[0]["cy"])
        )
        attackers = tracking_by_team[attacking].loc[
            tracking_by_team[attacking]["period"].eq(period)
            & tracking_by_team[attacking]["time_match_s"].between(start, end)
            & ~tracking_by_team[attacking]["player_key"].eq(GOALKEEPERS[attacking])
            & tracking_by_team[attacking]["coordinate_valid"].astype(bool)
        ]
        attacker_shape = []
        for target in (start, end):
            frame = attackers.loc[
                np.isclose(attackers["time_match_s"], target, atol=1e-7, rtol=0)
            ].drop_duplicates("player_key")
            if len(frame) != 10:
                raise RuntimeError(
                    "attacking endpoint shape requires exactly ten outfield players"
                )
            attacker_shape.append(
                {
                    "cx": float(frame.x_m.mean()),
                    "cy": float(frame.y_m.mean()),
                    "width": float(frame.y_m.max() - frame.y_m.min()),
                    "depth": float(frame.x_m.max() - frame.x_m.min()),
                }
            )
        attacker_centroid_shift = float(
            np.hypot(
                attacker_shape[1]["cx"] - attacker_shape[0]["cx"],
                attacker_shape[1]["cy"] - attacker_shape[0]["cy"],
            )
        )
        attacker_shape_change = float(
            max(
                abs(attacker_shape[1]["width"] - attacker_shape[0]["width"]),
                abs(attacker_shape[1]["depth"] - attacker_shape[0]["depth"]),
            )
        )
        possession_matches_attack = possession == attacking
        activity_score, meaningful_attack, activity_components = classify_attacking_activity(
            possession_matches_attack=possession_matches_attack,
            ball_path_length_m=ball_path,
            endpoint_change_m=float(np.hypot(dx, dy)),
            directed_ball_progress_m=directed_ball_progress,
            attacking_action_count=attacking_actions,
            attacker_centroid_shift_m=attacker_centroid_shift,
            attacker_shape_change_m=attacker_shape_change,
        )
        on_ball_activity_score = int(
            sum(
                activity_components[key]
                for key in (
                    "ball_path_15m",
                    "endpoint_change_10m",
                    "directed_progress_5m",
                    "two_attacking_actions",
                )
            )
        )
        records.append(
            {
                "match_clock": _clock_label(peak),
                "attacking_team_key": attacking,
                "possession_team_key": possession,
                "score_state": f"Home {home_goals}–{away_goals} Away",
                "field_zone": zone,
                "ball_start_x_m": float(ball.iloc[0].x_m),
                "ball_start_y_m": float(ball.iloc[0].y_m),
                "ball_end_x_m": float(ball.iloc[-1].x_m),
                "ball_end_y_m": float(ball.iloc[-1].y_m),
                "ball_dx_m": dx,
                "ball_dy_m": dy,
                "ball_progression_m": float(np.hypot(dx, dy)),
                "ball_path_length_m": ball_path,
                "directed_ball_progress_m": directed_ball_progress,
                "attacking_action_count": attacking_actions,
                "attacker_centroid_shift_m": attacker_centroid_shift,
                "attacker_shape_change_m": attacker_shape_change,
                "attack_possession_proxy_matches": possession_matches_attack,
                "attacking_activity_score": activity_score,
                "attacking_on_ball_score": on_ball_activity_score,
                "meaningful_attacking_activity": meaningful_attack,
                "attacking_activity_components": json.dumps(
                    activity_components, sort_keys=True, separators=(",", ":")
                ),
                "previous_event": previous_event,
                "next_event": next_event,
                "previous_event_offset_s": previous_offset,
                "next_event_offset_s": next_offset,
                "previous_event_inside_clip": bool(np.isfinite(previous_offset) and previous_offset >= -context_seconds),
                "next_event_inside_clip": bool(np.isfinite(next_offset) and next_offset <= context_seconds),
                "attacking_direction": direction,
                "defensive_width_start_m": shape[0]["width"],
                "defensive_width_end_m": shape[1]["width"],
                "defensive_depth_start_m": shape[0]["depth"],
                "defensive_depth_end_m": shape[1]["depth"],
                "defensive_centroid_shift_m": centroid_shift,
            }
        )
    return pd.concat([result.reset_index(drop=True), pd.DataFrame(records)], axis=1)


def select_analyst_moments(
    candidates: pd.DataFrame,
    *,
    reviewed_primary: dict[str, tuple[str, int, float]] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Choose primary passages, conditioning low response on attacking activity."""
    pool = candidates.loc[candidates["visual_suitable"]].copy()
    highs = pool.loc[pool.moment_type.eq("high")]
    lows = pool.loc[
        pool.moment_type.eq("low") & pool.meaningful_attacking_activity.astype(bool)
    ]
    if highs.empty:
        raise RuntimeError("no suitable high passage exists")
    if reviewed_primary is None:
        high = next(
            highs.sort_values("team_score_m", ascending=False, kind="mergesort").itertuples(index=False)
        )
    else:
        key = reviewed_primary["high"]
        fixed_high = highs.loc[
            highs.team_key.eq(key[0])
            & highs.period.eq(key[1])
            & np.isclose(highs.peak_time_s, key[2], atol=1e-7, rtol=0)
        ]
        if len(fixed_high) != 1:
            raise RuntimeError("reviewed high passage is unavailable")
        high = next(fixed_high.itertuples(index=False))
    pairs = []
    for low in lows.itertuples(index=False):
        mismatch = (
            -int(low.attacking_activity_score),
            int(high.team_key != low.team_key),
            int(high.period != low.period),
            int(high.possession_team_key != low.possession_team_key),
            int(high.field_zone != low.field_zone),
            float(low.team_score_m),
        )
        pairs.append((mismatch, high, low))
    if pairs:
        mismatch, high, low = min(pairs, key=lambda item: item[0])
        chosen = [dict(zip(pool.columns, high, strict=True)), dict(zip(pool.columns, low, strict=True))]
    else:
        mismatch = (0, 1, 1, 1, 1, 0.0)
        chosen = [dict(zip(pool.columns, high, strict=True))]
    rapid = pool.loc[pool.moment_type.eq("rapid_increase")].sort_values(
        "positive_change_m", ascending=False, kind="mergesort"
    )
    if reviewed_primary is not None:
        key = reviewed_primary["rapid_increase"]
        rapid = rapid.loc[
            rapid.team_key.eq(key[0])
            & rapid.period.eq(key[1])
            & np.isclose(rapid.peak_time_s, key[2], atol=1e-7, rtol=0)
        ]
    for row in rapid.itertuples(index=False):
        if all(
            row.period != selected["period"]
            or abs(float(row.peak_time_s) - float(selected["peak_time_s"])) > 10.0
            for selected in chosen
        ):
            chosen.append(dict(zip(pool.columns, row, strict=True)))
            break
    expected = 3 if pairs else 2
    if len(chosen) != expected:
        raise RuntimeError("no distinct suitable rapid-increase passage exists")
    selected = pd.DataFrame(chosen)
    if pairs:
        selected["public_category"] = (
            "high movement",
            "low trailing movement during active attack",
            "rapid increase",
        )
        selected["selection_reason"] = (
            "primary high-movement review passage",
            "primary low response under meaningful attacking activity",
            "primary strongest non-overlapping rapid increase",
        )
        selected["analyst_interpretation"] = (
            "High within-unit movement candidate",
            "Low trailing within-unit movement at the selected anchor during active attack",
            "Rapid increase in within-unit movement",
        )
        selected["display_order"] = (1, 3, 2)
    else:
        selected["public_category"] = ("high movement", "rapid increase")
        selected["selection_reason"] = (
            "primary high-movement review passage",
            "primary strongest non-overlapping rapid increase",
        )
        selected["analyst_interpretation"] = (
            "High within-unit movement candidate",
            "Rapid increase in within-unit movement",
        )
        selected["display_order"] = (1, 2)
    selected["presentation_role"] = "primary_example"
    selected["coach_review_question"] = [
        (
            "What team or opponent action explains the unusually large "
            "within-unit movement?"
            if row.moment_type == "high"
            else (
                "What attacking action is occurring while trailing defensive "
                "movement is still low at this anchor?"
                if row.moment_type == "low"
                else (
                    "Does the video show a counter-pressing action, or another "
                    "cause of the rapid increase?"
                    if reviewed_primary is not None
                    else "What changes immediately before the within-unit movement increases?"
                )
            )
        )
        for row in selected.itertuples(index=False)
    ]
    selected["review_question_source"] = (
        "human-authored Game 2 case-study question"
        if reviewed_primary is not None
        else "neutral review-question template"
    )
    selected["selected_for_clip"] = True
    selected["default_render"] = True
    selected = selected.sort_values("display_order", kind="mergesort")
    metadata = {
        "matching_priority": [
            "meaningful_attacking_activity",
            "defending_team",
            "period",
            "possession_team",
            "field_zone",
        ],
        "activity_gate": "attack possession proxy matches and at least 2 of 4 on-ball activity components",
        "conditional_low_available": bool(pairs),
        "conditional_low_activity_score": None if not pairs else int(low.attacking_activity_score),
        "reviewed_primary_passages_preserved": bool(reviewed_primary is not None),
        "mismatch_vector": list(mismatch[1:5]),
        "matched_defending_team": bool(mismatch[1] == 0),
        "matched_period": bool(mismatch[2] == 0),
        "matched_possession": bool(mismatch[3] == 0),
        "matched_field_zone": bool(mismatch[4] == 0),
    }
    return selected.reset_index(drop=True), metadata


def load_normalized_team(
    path: Path, team_key: str, *, match_id: str = MATCH_ID
) -> pd.DataFrame:
    wide = pd.read_csv(path, skiprows=2)
    rows: list[pd.DataFrame] = []
    team = team_key.split(":")[-1]
    for index, column in enumerate(wide.columns[:-1]):
        if not str(column).startswith("Player"):
            continue
        number = str(column).replace("Player", "").strip()
        x = pd.to_numeric(wide.iloc[:, index], errors="coerce")
        y = pd.to_numeric(wide.iloc[:, index + 1], errors="coerce")
        valid = np.isfinite(x) & np.isfinite(y)
        rows.append(
            pd.DataFrame(
                {
                    "match_id": match_id,
                    "period": wide["Period"].astype(int),
                    "frame_id_provider": wide["Frame"].astype(int).astype(str),
                    "time_match_s": wide["Time [s]"].astype(float),
                    "entity_type": "player",
                    "team_key": team_key,
                    "player_key": f"metrica:{team}:{number}",
                    "x_m": x * 105.0 - 52.5,
                    "y_m": y * 68.0 - 34.0,
                    "coordinate_valid": valid,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
        )
    if not rows:
        raise RuntimeError(f"no player columns found in {path}")
    return pd.concat(rows, ignore_index=True)


def load_shots(path: Path, *, match_id: str = MATCH_ID) -> pd.DataFrame:
    events = pd.read_csv(path)
    shots = events.loc[events["Type"].eq("SHOT")].copy().reset_index(drop=True)
    return pd.DataFrame(
        {
            "event_id": [f"{match_id}-shot-{index + 1:02d}" for index in range(len(shots))],
            "match_id": match_id,
            "period": shots["Period"].astype(int),
            "event_time_s": shots["Start Time [s]"].astype(float),
            "event_type": np.where(
                shots["Subtype"].astype(str).str.contains("GOAL", na=False), "GOAL", "SHOT"
            ),
            "event_detail": shots["Subtype"].fillna("UNSPECIFIED").astype(str),
            "team_key": "metrica:" + shots["Team"].astype(str),
        }
    )


def load_ball(path: Path, *, match_id: str = MATCH_ID) -> pd.DataFrame:
    wide = pd.read_csv(path, skiprows=2)
    index = list(wide.columns).index("Ball")
    x = pd.to_numeric(wide.iloc[:, index], errors="coerce")
    y = pd.to_numeric(wide.iloc[:, index + 1], errors="coerce")
    valid = np.isfinite(x) & np.isfinite(y)
    return pd.DataFrame(
        {
            "match_id": match_id,
            "period": wide["Period"].astype(int),
            "frame_id_provider": wide["Frame"].astype(int).astype(str),
            "time_match_s": wide["Time [s]"].astype(float),
            "entity_type": "ball",
            "team_key": pd.NA,
            "player_key": pd.NA,
            "x_m": x * 105.0 - 52.5,
            "y_m": y * 68.0 - 34.0,
            "coordinate_valid": valid,
            "pitch_length_m": 105.0,
            "pitch_width_m": 68.0,
        }
    )


def render_selected(
    selected: pd.DataFrame,
    tracking_by_team: dict[str, pd.DataFrame],
    score_by_team: dict[str, DefensiveReorganizationScores],
    output_dir: Path,
    data_dir: Path,
    *,
    match_id: str = MATCH_ID,
    team_files: dict[str, str] = TEAM_FILES,
    clip_context_seconds: float = ANALYST_CLIP_CONTEXT_SECONDS,
) -> list[dict[str, object]]:
    combined = pd.concat(
        [
            *tracking_by_team.values(),
            load_ball(data_dir / team_files["metrica:Home"], match_id=match_id),
        ],
        ignore_index=True,
    )
    rendered = []
    destination = output_dir / "primary_examples"
    destination.mkdir(parents=True, exist_ok=True)
    for number, row in enumerate(selected.itertuples(index=False), start=1):
        defending = str(row.team_key)
        attacking = "metrica:Away" if defending == "metrica:Home" else "metrica:Home"
        peak = float(row.peak_time_s)
        start, end = peak - clip_context_seconds, peak + clip_context_seconds
        scores = score_by_team[defending]
        at_peak = scores.player_scores.loc[
            scores.player_scores["period"].eq(row.period)
            & np.isclose(scores.player_scores["time_match_s"], peak, atol=1e-7)
        ]
        defender_keys = set(at_peak.player_key.astype(str))
        if len(defender_keys) != 10:
            raise RuntimeError("selected peak lacks exactly ten scored defenders")
        clip_tracking = combined.loc[
            combined["period"].eq(row.period)
            & combined["time_match_s"].between(start, end)
            & ~(
                combined["team_key"].eq(defending)
                & ~combined["player_key"].astype(str).isin(defender_keys)
            )
        ].copy()
        frame_count = clip_tracking[["frame_id_provider", "time_match_s"]].drop_duplicates().shape[0]
        focal_candidates = []
        for key, group in clip_tracking.loc[
            clip_tracking["entity_type"].eq("player")
            & clip_tracking["team_key"].eq(attacking)
        ].groupby("player_key", sort=True):
            valid = group["coordinate_valid"].astype(bool) & np.isfinite(
                group[["x_m", "y_m"]]
            ).all(axis=1)
            if len(group) == frame_count and valid.all():
                focal_candidates.append(str(key))
        if not focal_candidates:
            raise RuntimeError("selected clip lacks one complete attacking reference player")
        clip_spec = TrackingClipSpec(
            match_id=match_id,
            period=int(row.period),
            anchor_time_s=peak,
            start_time_s=start,
            end_time_s=end,
            focal_player_key=focal_candidates[0],
            attacking_team_key=attacking,
            defending_team_key=defending,
            defender_ranks=None,
        )
        clip_scores = DefensiveReorganizationScores(
            scores.player_scores.loc[
                scores.player_scores["period"].eq(row.period)
                & scores.player_scores["time_match_s"].between(start, end)
                & scores.player_scores["player_key"].astype(str).isin(defender_keys)
            ].reset_index(drop=True),
            scores.team_scores.loc[
                scores.team_scores["period"].eq(row.period)
                & scores.team_scores["time_match_s"].between(start, end)
            ].reset_index(drop=True),
            {**scores.metadata, "source_fps": SOURCE_FPS},
        )
        stem = f"{number:02d}_{row.moment_type}_{defending.split(':')[-1].lower()}_{peak:.2f}"
        paths = render_selected_passage(
            clip_tracking,
            clip_scores,
            clip_spec,
            destination,
            stem=stem,
            selected_time_s=peak,
            show_focal_highlight=False,
            diagnostic_anchor_label=(
                "Time relative to selected event (s)"
                if str(getattr(row, "presentation_role", "")) == "event_window"
                else None
            ),
        )
        technical = destination / f"{stem}_technical_appendix.png"
        Path(paths["diagnostic_png"]).replace(technical)
        analyst_figure = plot_defensive_reorganization_diagnostic(
            clip_tracking,
            clip_scores,
            clip_spec,
            selected_time_s=peak,
            show_focal_highlight=False,
            technical=False,
        )
        if str(getattr(row, "presentation_role", "")) == "event_window":
            analyst_figure.axes[0].set_xlabel("Time relative to selected event (s)")
        analyst = destination / f"{stem}_analyst_diagnostic.png"
        analyst_figure.savefig(analyst, dpi=160, bbox_inches="tight")
        import matplotlib.pyplot as plt

        plt.close(analyst_figure)
        if str(getattr(row, "presentation_role", "")) == "event_window":
            card = render_event_review_card(
                row, destination / f"{stem}_event_review_card.png"
            )
            coach_card = card
        else:
            card = render_moment_card(row, destination / f"{stem}_moment_card.png")
            coach_card = render_coach_card(
                row, destination / f"{stem}_coach_review_card.png"
            )
        rendered.append(
            {
                "moment_type": row.moment_type,
                "presentation_role": row.presentation_role,
                "analyst_interpretation": row.analyst_interpretation,
                "defending_team_key": defending,
                "period": int(row.period),
                "peak_time_s": peak,
                "analyst_diagnostic_png": str(analyst),
                "technical_appendix_png": str(technical),
                "gif": str(paths["gif"]),
                "moment_card_png": str(card),
                "coach_review_card_png": str(coach_card),
            }
        )
    return rendered


def event_review_card_content(row: object) -> dict[str, str]:
    """Return sparse event-first content without automatic tactical interpretation."""
    defending = str(row.team_key).split(":")[-1]
    attacking = str(row.attacking_team_key).split(":")[-1]
    change = float(row.post_minus_pre_change_m)
    direction = "increased" if change > 0 else "decreased" if change < 0 else "was unchanged"
    return {
        "title": f"{str(row.event_type).title()} review · {row.match_clock}",
        "teams": f"Attacking: {attacking} · Defending: {defending}",
        "description": (
            f"Mean trailing defender-relative path {direction} by {abs(change):.2f} m "
            f"from the pre-event to post-event sample; the local maximum was "
            f"{float(row.maximum_score_m):.2f} m."
        ),
        "question": "What movement pattern accompanied this football event?",
        "boundary": (
            "Analyst review question: the event anchor and score do not identify a tactic, "
            "intent, quality, cause, success, or value."
        ),
    }


def render_event_review_card(row: object, path: Path) -> Path:
    """Render one sparse event-first review card."""
    import matplotlib.pyplot as plt

    content = event_review_card_content(row)
    fig = plt.figure(figsize=(10, 5.625), facecolor="#f7f4ed")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.text(.07, .84, content["title"], fontsize=23, weight="bold")
    fig.text(.07, .72, content["teams"], fontsize=15)
    fig.text(.07, .54, "Observed movement", fontsize=13, weight="bold", color="#8f1d14")
    fig.text(.07, .43, content["description"], fontsize=15, wrap=True)
    fig.text(.07, .27, "Analyst review question", fontsize=13, weight="bold")
    fig.text(.07, .19, content["question"], fontsize=17)
    fig.text(.07, .06, content["boundary"], fontsize=10.5, color="#444444")
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def write_event_query_summary(path: Path, windows: pd.DataFrame, metadata: dict[str, object]) -> Path:
    """Write a human-readable event-first result or explicit no-result."""
    lines = [
        "# Event-window analyst review", "",
        f"**Football question:** {metadata['question']}", "",
        f"**Ranking basis:** `{metadata['rank_by']}`", "",
        f"**Selected windows:** {metadata['result_count']} of {metadata['candidate_count']} matching events", "",
    ]
    if windows.empty:
        lines.extend(["## No result", "", *[f"- {reason}" for reason in metadata["no_result_reasons"]]])
    else:
        lines.extend(["## Ranked windows", ""])
        for row in windows.itertuples(index=False):
            lines.append(
                f"- **#{int(row.rank)} {row.event_type} · P{int(row.period)} "
                f"{_clock_label(float(row.event_time_s))}:** maximum {float(row.maximum_score_m):.2f} m; "
                f"post-minus-pre {float(row.post_minus_pre_change_m):+.2f} m."
            )
    lines.extend(["", "Event anchors organize human review; they do not classify counter-pressing or any other tactic.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def render_moment_card(row: object, path: Path) -> Path:
    """Render a compact descriptive review card for one selected passage."""
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 5.625), facecolor="#f7f4ed")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    category = str(getattr(row, "public_category", row.moment_type)).replace("_", " ").title()
    team = str(row.team_key).split(":")[-1]
    leaders = json.loads(row.leading_player_contributors)
    leader_text = ", ".join(
        f"{item['player_key'].split(':')[-1]} ({item['score_m']:.1f} m)" for item in leaders
    )
    fig.text(.06, .90, f"{category} review moment · {row.match_clock}", fontsize=22, weight="bold")
    fig.text(.06, .83, f"Defending: {team}  ·  {row.score_state}  ·  {row.field_zone}", fontsize=14)
    fig.text(
        .06,
        .73,
        f"Team movement: {row.team_score_m:.2f} m ({100*row.within_match_percentile:.1f}th percentile)",
        fontsize=18,
        color="#8f1d14",
        weight="bold",
    )
    fig.text(.06, .65, f"Review role: {row.selection_reason}", fontsize=13)
    fig.text(.06, .60, f"Analyst interpretation: {row.analyst_interpretation}", fontsize=12)
    fig.text(
        .06,
        .53,
        f"Possession proxy: {str(row.possession_team_key).split(':')[-1]} · {row.attacking_direction}",
        fontsize=13,
    )
    fig.text(
        .06,
        .47,
        f"Activity gate: {'PASS' if row.meaningful_attacking_activity else 'below'} "
        f"({row.attacking_on_ball_score}/4 on-ball) · "
        f"path {row.ball_path_length_m:.1f} m · "
        f"directed {row.directed_ball_progress_m:+.1f} m · {row.attacking_action_count} actions",
        fontsize=11.5,
    )
    fig.text(
        .06,
        .42,
        f"Ball: Δx {row.ball_dx_m:+.1f} m · Δy {row.ball_dy_m:+.1f} m · {row.ball_progression_m:.1f} m endpoint change",
        fontsize=12,
    )
    prev_scope = "inside clip" if row.previous_event_inside_clip else "outside clip"
    next_scope = "inside clip" if row.next_event_inside_clip else "outside clip"
    fig.text(
        .06, .36,
        f"Previous: {row.previous_event}, {row.previous_event_offset_s:+.1f} s ({prev_scope})",
        fontsize=12,
    )
    fig.text(
        .06, .31,
        f"Next: {row.next_event}, {row.next_event_offset_s:+.1f} s ({next_scope})",
        fontsize=12,
    )
    fig.text(
        .06,
        .225,
        f"Defensive shape: width {row.defensive_width_start_m:.1f}→{row.defensive_width_end_m:.1f} m · "
        f"depth {row.defensive_depth_start_m:.1f}→{row.defensive_depth_end_m:.1f} m · "
        f"centroid shift {row.defensive_centroid_shift_m:.1f} m",
        fontsize=13,
    )
    fig.text(.06, .15, f"Leading defender-relative paths: {leader_text}", fontsize=13)
    arrow = fig.add_axes([.80, .405, .13, .055])
    arrow.set_xlim(-52.5, 52.5)
    arrow.set_ylim(-1, 1)
    arrow.axhline(0, color="#bbbbbb", linewidth=2)
    arrow.annotate(
        "",
        xy=(row.ball_end_x_m, 0),
        xytext=(row.ball_start_x_m, 0),
        arrowprops={"arrowstyle": "->", "linewidth": 3, "color": "#0b3d91"},
    )
    arrow.scatter([row.ball_start_x_m], [0], color="white", edgecolor="#222222", zorder=3)
    arrow.set_title("Ball x: start → end", fontsize=8)
    arrow.axis("off")
    fig.text(
        .06,
        .055,
        "Descriptive retrospective geometry only—this does not identify tactical quality, cause, or value.",
        fontsize=11,
        color="#444444",
    )
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def coach_card_content(row: object) -> dict[str, str]:
    """Return the deliberately sparse, non-tactical coach-review content."""
    defending = str(row.team_key).split(":")[-1]
    attacking = str(row.attacking_team_key).split(":")[-1]
    if row.moment_type == "high":
        why = "Trailing within-unit movement was unusually high at this anchor."
    elif row.moment_type == "rapid_increase":
        why = "Trailing within-unit movement increased rapidly near this anchor."
    else:
        why = (
            "Trailing within-unit movement was low at this anchor while the "
            "unchanged attacking-activity gate passed."
        )
    return {
        "title": str(row.public_category).title(),
        "match_context": f"{row.match_clock} · {row.score_state}",
        "teams": f"Defending: {defending} · Attacking: {attacking}",
        "why_surfaced": why,
        "review_question_label": f"Review question ({row.review_question_source})",
        "review_question": str(row.coach_review_question),
        "boundary": (
            "Review prompt only: the metric does not identify intent, quality, "
            "cause, tactical success, or value."
        ),
    }


def render_coach_card(row: object, path: Path) -> Path:
    """Render one low-density coach-facing review prompt."""
    import matplotlib.pyplot as plt

    content = coach_card_content(row)
    fig = plt.figure(figsize=(10, 5.625), facecolor="#f7f4ed")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.text(.07, .86, content["title"], fontsize=24, weight="bold")
    fig.text(.07, .76, content["match_context"], fontsize=15)
    fig.text(.07, .68, content["teams"], fontsize=15)
    fig.text(.07, .52, "Why surfaced", fontsize=13, weight="bold", color="#8f1d14")
    fig.text(.07, .45, content["why_surfaced"], fontsize=16)
    fig.text(.07, .30, content["review_question_label"], fontsize=13, weight="bold")
    fig.text(.07, .22, content["review_question"], fontsize=16)
    fig.text(.07, .07, content["boundary"], fontsize=11, color="#444444")
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_no_result_card(path: Path) -> Path:
    """Render an intentional no-result surface for the conditional low category."""
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 5.625), facecolor="#f7f4ed")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.text(.07, .82, "No qualifying low-trailing-movement passage", fontsize=22, weight="bold")
    fig.text(
        .07,
        .59,
        "No visually suitable low-trailing-movement candidate passed the\n"
        "unchanged attacking-activity gate in this match.",
        fontsize=17,
        linespacing=1.5,
    )
    fig.text(
        .07,
        .36,
        "This is a valid no-result outcome, not a failed run or missing render.",
        fontsize=15,
    )
    fig.text(
        .07,
        .12,
        "No threshold was relaxed and no substitute passage was selected.",
        fontsize=12,
        color="#444444",
    )
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def write_match_review_summary(
    path: Path,
    selected: pd.DataFrame,
    *,
    reviewed_primary: bool,
) -> Path:
    """Write a compact human-readable selection and no-result summary."""
    lines = [
        "# Defensive reorganization match review",
        "",
        "This application organizes passages for human review. It does not classify tactics, quality, intent, cause, or value.",
        "",
        "## Selection provenance",
        "",
        (
            "Game 2 high and rapid identities are fixed reviewed case-study examples; the low-trailing-movement passage is selected by the unchanged automatic gate."
            if reviewed_primary
            else "All displayed passages were selected automatically under the unchanged rules."
        ),
        "",
        "## Selected passages",
        "",
    ]
    for row in selected.sort_values("display_order", kind="mergesort").itertuples(index=False):
        lines.append(
            f"- **{row.public_category.title()} — {row.match_clock}:** "
            f"{coach_card_content(row)['why_surfaced']}"
        )
    if not selected["moment_type"].eq("low").any():
        lines.extend(
            [
                "",
                "## Valid no-result",
                "",
                "No visually suitable low-trailing-movement candidate passed the unchanged attacking-activity gate in this match.",
                "",
                "No threshold was relaxed and no substitute passage was selected.",
            ]
        )
    lines.extend(
        [
            "",
            "## Audience guide",
            "",
            "- Coach review: GIF plus coach card and a human analyst's video note.",
            "- Analyst appendix: moment card, team trace, player traces, CSV, and Parquet outputs.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(
    output_dir: Path,
    data_dir: Path = DATA,
    *,
    match_id: str = MATCH_ID,
    team_files: dict[str, str] = TEAM_FILES,
    events_file: str = "Sample_Game_2_RawEventsData.csv",
    reviewed_primary: dict[str, tuple[str, int, float]] | None = None,
    render_selected_clips: bool = False,
    discovery_audit: bool = False,
    event_query_limit: int = 2,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    score_by_team = {}
    tracking_by_team = {}
    moment_tables = []
    distribution_rows = []
    for team_key, filename in team_files.items():
        tracking = load_normalized_team(
            data_dir / filename, team_key, match_id=match_id
        )
        tracking_by_team[team_key] = tracking
        scores = score_stable_runs(
            tracking,
            defending_team_key=team_key,
            source_fps=SOURCE_FPS,
            smoothing_frames=7,
            window_seconds=2.0,
            excluded_player_keys=(GOALKEEPERS[team_key],),
        )
        score_by_team[team_key] = scores
        export_scores(scores, output_dir / team_key.replace(":", "_"), formats=("parquet",))
        moments = discover_moments(
            scores,
            MomentDiscoverySpec(
                top_n_per_type=2,
                tail_fraction=.05,
                adjacency_seconds=1.0,
                interior_guard_seconds=ANALYST_INTERIOR_GUARD_SECONDS,
            ),
            audit=True,
        )
        moment_tables.append(moments)
        supported = scores.team_scores.loc[scores.team_scores.support_status.eq("supported")]
        values = supported.mean_trailing_relative_path_m.to_numpy(float)
        quantiles = np.quantile(values, [0, .05, .25, .5, .75, .95, 1])
        distribution_rows.append(
            {
                "match_id": match_id,
                "defending_team_key": team_key,
                "supported_frames": int(len(values)),
                "stable_runs": int(len(scores.metadata["stable_runs"])),
                **{
                    name: float(value)
                    for name, value in zip(
                        ("min_m", "p05_m", "p25_m", "median_m", "p75_m", "p95_m", "max_m"),
                        quantiles,
                        strict=True,
                    )
                },
            }
        )

    raw_events = pd.read_csv(data_dir / events_file)
    ball_tracking = load_ball(
        data_dir / team_files["metrica:Home"], match_id=match_id
    )
    moment_audit = audit_visual_suitability(
        pd.concat(moment_tables, ignore_index=True),
        tracking_by_team,
        raw_events,
        ball_tracking=ball_tracking,
        clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
    )
    contextual_candidates = add_analyst_context(
        moment_audit.loc[
            moment_audit.interior_eligible & moment_audit.visual_suitable
        ].copy(),
        tracking_by_team,
        ball_tracking,
        raw_events,
        context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
    )
    moment_audit["selected_for_clip"] = False
    moments, matching_metadata = select_analyst_moments(
        contextual_candidates, reviewed_primary=reviewed_primary
    )
    context_columns = [
        column for column in contextual_candidates.columns if column not in moment_audit.columns
    ]
    moment_audit = moment_audit.merge(
        contextual_candidates[["moment_type", "team_key", "period", "peak_time_s", *context_columns]],
        on=["moment_type", "team_key", "period", "peak_time_s"],
        how="left",
        validate="one_to_one",
    )
    selected_keys = {
        (row.moment_type, row.team_key, row.period, row.peak_time_s)
        for row in moments.itertuples(index=False)
    }
    moment_audit["selected_for_clip"] = [
        (row.moment_type, row.team_key, row.period, row.peak_time_s) in selected_keys
        for row in moment_audit.itertuples(index=False)
    ]
    if discovery_audit:
        moment_audit.to_csv(output_dir / "moment_audit.csv", index=False, lineterminator="\n")
        moments.to_csv(output_dir / "selected_moments.csv", index=False, lineterminator="\n")
    distributions = pd.DataFrame(distribution_rows)
    distributions.to_csv(output_dir / "team_score_distributions.csv", index=False, lineterminator="\n")

    shots = load_shots(data_dir / events_file, match_id=match_id)
    event_tables = []
    for defending_team, scores in score_by_team.items():
        attacking_team = "metrica:Away" if defending_team == "metrica:Home" else "metrica:Home"
        relevant = shots.loc[shots.team_key.eq(attacking_team)]
        aligned = align_events(relevant, scores, defending_team_key=defending_team)
        aligned = aligned.merge(
            relevant[["event_id", "event_detail"]], on="event_id", how="left", validate="one_to_one"
        )
        event_tables.append(aligned)
    event_summary = pd.concat(event_tables, ignore_index=True).sort_values(
        ["period", "event_time_s", "event_id"], kind="mergesort"
    )
    event_summary.to_csv(output_dir / "shot_event_summary.csv", index=False, lineterminator="\n")

    shot_suitability = audit_visual_suitability(
        shots.rename(columns={"event_time_s": "peak_time_s"}),
        tracking_by_team,
        raw_events,
        ball_tracking=ball_tracking,
        clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
    ).rename(columns={"peak_time_s": "event_time_s"})
    event_window_tables = []
    query_metadata = []
    for defending_team, scores in score_by_team.items():
        attacking_team = "metrica:Away" if defending_team == "metrica:Home" else "metrica:Home"
        query = EventWindowQuery(
            defending_team_key=defending_team,
            attacking_team_key=attacking_team,
            event_types=("SHOT", "GOAL"),
            pre_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
            post_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
            rank_by="maximum_score",
            limit=event_query_limit,
            require_suitable=True,
        )
        queried = query_event_windows(shot_suitability, scores, query)
        event_window_tables.append(queried.windows)
        query_metadata.append(dict(queried.metadata))
    event_windows = (
        pd.concat(event_window_tables, ignore_index=True)
        .sort_values(["rank_value", "event_time_s", "event_id"], ascending=[False, True, True], kind="mergesort")
        .head(event_query_limit)
        .reset_index(drop=True)
    )
    event_windows["rank"] = np.arange(1, len(event_windows) + 1)
    event_windows.to_csv(output_dir / "ranked_event_windows.csv", index=False, lineterminator="\n")
    (output_dir / "ranked_event_windows.json").write_text(
        event_windows.to_json(orient="records", indent=2) + "\n", encoding="utf-8"
    )
    combined_query_metadata = {
        "question": "What defensive reorganization happened around shots and goals?",
        "candidate_count": sum(int(item["candidate_count"]) for item in query_metadata),
        "result_count": int(len(event_windows)),
        "rank_by": "maximum_score",
        "no_result_reasons": tuple(
            reason for item in query_metadata for reason in item["no_result_reasons"]
        ),
    }
    event_query_summary = write_event_query_summary(
        output_dir / "event_window_review_summary.md", event_windows, combined_query_metadata
    )

    event_render_rows = pd.DataFrame()
    if not event_windows.empty:
        event_render_rows = event_windows.rename(
            columns={"defending_team_key": "team_key", "event_time_s": "peak_time_s"}
        ).copy()
        event_render_rows["moment_type"] = "event_window"
        event_render_rows["public_category"] = event_render_rows["event_type"].str.lower() + " window"
        event_render_rows["presentation_role"] = "event_window"
        event_render_rows["analyst_interpretation"] = "Event-anchored descriptive movement window"
        event_render_rows["display_order"] = event_render_rows["rank"].astype(int)
        event_render_rows["selected_for_clip"] = True
        event_render_rows["default_render"] = True
        event_render_rows = add_analyst_context(
            event_render_rows,
            tracking_by_team,
            ball_tracking,
            raw_events,
            context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
        )

    rendered_events = (
        render_selected(
            event_render_rows,
            tracking_by_team,
            score_by_team,
            output_dir / "event_review",
            data_dir,
            match_id=match_id,
            team_files=team_files,
            clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
        )
        if render_selected_clips and not event_render_rows.empty
        else []
    )
    rendered = (
        render_selected(
            moments, tracking_by_team, score_by_team, output_dir / "discovery_audit",
            data_dir, match_id=match_id, team_files=team_files,
            clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
        )
        if render_selected_clips and discovery_audit else []
    )
    no_result_cards: list[str] = []
    if render_selected_clips and discovery_audit and not moments["moment_type"].eq("low").any():
        no_result = output_dir / "discovery_audit" / "primary_examples" / "03_low_no_result.png"
        no_result_cards.append(str(render_no_result_card(no_result)))
    review_summary = (
        write_match_review_summary(
            output_dir / "match_review_summary.md",
            moments,
            reviewed_primary=reviewed_primary is not None,
        )
        if discovery_audit
        else None
    )

    result = {
        "status": "EXPLORATORY_APPLICATION_COMPLETE",
        "match_id": match_id,
        "teams": sorted(score_by_team),
        "shot_count": int(len(event_summary)),
        "goal_count": int(event_summary.event_type.eq("GOAL").sum()),
        "selected_moment_count": int(len(moments)) if discovery_audit else 0,
        "primary_moment_count": (
            int(moments.default_render.astype(bool).sum()) if discovery_audit else 0
        ),
        "rendered_clip_count": int(len(rendered)),
        "rendered_clips": rendered,
        "event_window_count": int(len(event_windows)),
        "event_window_review_summary": event_query_summary.name,
        "rendered_event_window_count": int(len(rendered_events)),
        "rendered_event_windows": rendered_events,
        "default_workflow": "event_first",
        "discovery_audit_enabled": bool(discovery_audit),
        "no_result_cards": no_result_cards,
        "match_review_summary": None if review_summary is None else review_summary.name,
        "boundary_candidate_count": int(moment_audit.boundary_flag.sum()),
        "interior_guard_seconds": ANALYST_INTERIOR_GUARD_SECONDS,
        "analyst_clip_duration_seconds": 2 * ANALYST_CLIP_CONTEXT_SECONDS,
        "context_matching": matching_metadata,
        "visual_suitability": {
            "clip_context_seconds": ANALYST_CLIP_CONTEXT_SECONDS,
            "max_visual_speed_mps": MAX_VISUAL_SPEED_MPS,
            "dead_ball_intervals": "provider event stoppage through next set piece",
            "rejected_candidate_count": int((~moment_audit.visual_suitable).sum()),
        },
        "distribution_rows": distribution_rows,
        "claim_boundary": (
            "descriptive retrospective geometry only; not causal, predictive, tactical, or validated utility"
        ),
    }
    (output_dir / "application_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def analyze_metrica_game2(
    data_dir: str | Path,
    output_dir: str | Path,
    *,
    render_selected: bool = True,
    discovery_audit: bool = False,
) -> dict[str, object]:
    """Low-decision preset for the public Metrica Sample Game 2 files."""
    return run(
        Path(output_dir),
        Path(data_dir),
        match_id=MATCH_ID,
        team_files=TEAM_FILES,
        events_file="Sample_Game_2_RawEventsData.csv",
        reviewed_primary=REVIEWED_PRIMARY_MOMENTS,
        render_selected_clips=render_selected,
        discovery_audit=discovery_audit,
    )


def analyze_metrica_sample_match(
    game_number: int,
    output_dir: str | Path,
    *,
    data_dir: str | Path | None = None,
    render_selected: bool = True,
    reviewed_game2_case_study: bool = False,
    discovery_audit: bool = False,
) -> dict[str, object]:
    """Run the same automatic workflow over public Sample Game 1 or 2."""
    preset = metrica_sample_preset(
        game_number,
        data_dir=data_dir,
        reviewed_game2_case_study=reviewed_game2_case_study,
    )
    return run(
        Path(output_dir),
        preset.data_dir,
        match_id=preset.match_id,
        team_files=preset.team_files,
        events_file=preset.events_file,
        reviewed_primary=preset.reviewed_primary,
        render_selected_clips=render_selected,
        discovery_audit=discovery_audit,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )
    parser.add_argument("--game", type=int, choices=(1, 2), default=2)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument(
        "--reviewed-game2-case-study",
        action="store_true",
        help="reproduce the fixed reviewed Game 2 high/rapid examples",
    )
    parser.add_argument("--render-selected", action="store_true")
    parser.add_argument(
        "--discovery-audit",
        action="store_true",
        help="also render high/rapid/low-under-activity audit examples",
    )
    args = parser.parse_args()
    output_dir = args.output_dir or Path(
        f"/tmp/moving_the_defense_game{args.game}_application"
    )
    print(
        json.dumps(
            analyze_metrica_sample_match(
                args.game,
                output_dir,
                data_dir=args.data_dir,
                render_selected=args.render_selected,
                reviewed_game2_case_study=args.reviewed_game2_case_study,
                discovery_audit=args.discovery_audit,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
