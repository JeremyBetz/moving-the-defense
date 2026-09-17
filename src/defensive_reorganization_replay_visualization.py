"""Static and animated views of trailing defender-relative replay scores.

This module renders a retrospective analyst replay.  It does not calculate a
new score, infer tactics, or turn the trailing score into a live measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from mplsoccer import Pitch

from defensive_reorganization_replay import (
    SUPPORTED,
    DefensiveReorganizationScores,
    normalize_scores_for_display,
)
from tracking_animation import (
    AnimationBundle,
    TrackingClipSpec,
    _prepare,
    centered_to_pitch,
)


PITCH_COLOR = "#315d3a"
LINE_COLOR = "#f5f5f0"
ATTACKER_COLOR = "#ed8b32"
DEFENDER_TRAIL_COLOR = "#2767a8"
NEUTRAL_EDGE = "#252525"
UNSUPPORTED_EDGE = "#b7b7b7"
SCORE_LABEL = "Trailing 2 s defender-relative path (m)"
INTERPRETATION_NOTE = (
    "Higher values indicate more accumulated movement relative to the defensive unit, "
    "not better or worse defending."
)
ANIMATION_NOTE = "Higher = more movement relative to the unit · not better/worse defending"


@dataclass(frozen=True)
class _PreparedVisualization:
    tracking: pd.DataFrame
    frames: pd.DataFrame
    player_by_key: Mapping[tuple[object, str], Mapping[str, object]]
    team_by_frame: Mapping[object, Mapping[str, object]]
    defender_keys: tuple[str, ...]
    source_fps: float


def _prepare_visualization(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    clip_spec: TrackingClipSpec,
) -> _PreparedVisualization:
    source_fps = float(scores.metadata.get("source_fps", np.nan))
    if not np.isfinite(source_fps) or source_fps <= 0:
        raise ValueError("scores metadata must contain a finite positive source_fps")
    q, frames = _prepare(tracking, clip_spec, source_fps)

    players = scores.player_scores.copy(deep=True)
    teams = scores.team_scores.copy(deep=True)
    player_key = ["match_id", "period", "frame_id_provider", "team_key", "player_key"]
    team_key = ["match_id", "period", "frame_id_provider", "team_key"]
    if players.duplicated(player_key).any():
        raise ValueError("duplicate player score keys")
    if teams.duplicated(team_key).any():
        raise ValueError("duplicate team score keys")

    players = players.loc[
        players["match_id"].eq(clip_spec.match_id)
        & players["period"].eq(clip_spec.period)
        & players["team_key"].eq(clip_spec.defending_team_key)
    ].copy()
    teams = teams.loc[
        teams["match_id"].eq(clip_spec.match_id)
        & teams["period"].eq(clip_spec.period)
        & teams["team_key"].eq(clip_spec.defending_team_key)
    ].copy()
    if players.empty or teams.empty:
        raise ValueError("scores do not contain the requested match, period, and defending team")

    tracked_defenders = q.loc[
        q["entity_type"].eq("player") & q["team_key"].eq(clip_spec.defending_team_key),
        "player_key",
    ].astype(str)
    defender_keys = tuple(sorted(tracked_defenders.unique()))
    if len(defender_keys) != 10:
        raise ValueError("visualization requires exactly ten defending-player identities")
    if set(players["player_key"].astype(str).unique()) != set(defender_keys):
        raise ValueError("score and tracking defender identities differ")

    frame_ids = frames["frame_id_provider"].tolist()
    player_rows: dict[tuple[object, str], Mapping[str, object]] = {}
    team_rows: dict[object, Mapping[str, object]] = {}
    for frame_id, time_s in frames[["frame_id_provider", "time_match_s"]].itertuples(index=False):
        frame_players = players.loc[players["frame_id_provider"].eq(frame_id)]
        frame_team = teams.loc[teams["frame_id_provider"].eq(frame_id)]
        if len(frame_players) != 10 or len(frame_team) != 1:
            raise ValueError("every displayed frame requires ten player scores and one team score")
        if set(frame_players["player_key"].astype(str)) != set(defender_keys):
            raise ValueError("displayed frame has missing or unexpected defender scores")
        if not np.allclose(frame_players["time_match_s"].to_numpy(float), time_s, atol=1e-7, rtol=0):
            raise ValueError("player score timestamps do not match tracking")
        team_row = frame_team.iloc[0]
        if not np.isclose(float(team_row["time_match_s"]), time_s, atol=1e-7, rtol=0):
            raise ValueError("team score timestamps do not match tracking")

        statuses = set(frame_players["support_status"].astype(str))
        if len(statuses) != 1 or str(team_row["support_status"]) not in statuses:
            raise ValueError("player and team support statuses disagree")
        status = next(iter(statuses))
        values = frame_players["trailing_relative_path_m"].to_numpy(float)
        if status == SUPPORTED:
            if not np.isfinite(values).all():
                raise ValueError("supported player scores must be finite")
            if int(team_row["supported_defender_count"]) != 10:
                raise ValueError("supported team score must contain ten defenders")
            team_value = float(team_row["mean_trailing_relative_path_m"])
            if not np.isfinite(team_value) or not np.isclose(team_value, values.mean(), atol=1e-12):
                raise ValueError("team mean does not equal the ten-player arithmetic mean")
        else:
            if np.isfinite(values).any() or int(team_row["supported_defender_count"]) != 0:
                raise ValueError("unsupported frames cannot contain partial player support")
            if np.isfinite(float(team_row["mean_trailing_relative_path_m"])):
                raise ValueError("unsupported frame cannot contain a team mean")

        for row in frame_players.to_dict(orient="records"):
            player_rows[(frame_id, str(row["player_key"]))] = MappingProxyType(dict(row))
        team_rows[frame_id] = MappingProxyType(dict(team_row))

    if set(team_rows) != set(frame_ids):
        raise ValueError("score frame keys do not match displayed tracking frames")
    return _PreparedVisualization(
        tracking=q,
        frames=frames,
        player_by_key=MappingProxyType(player_rows),
        team_by_frame=MappingProxyType(team_rows),
        defender_keys=defender_keys,
        source_fps=source_fps,
    )


def _draw_trails(
    ax,
    prepared: _PreparedVisualization,
    now: float,
    trail_seconds: float,
    artists: list,
) -> dict[str, int]:
    if trail_seconds <= 0:
        return {}
    times = prepared.frames.loc[
        (prepared.frames["time_match_s"] <= now)
        & (prepared.frames["time_match_s"] >= now - trail_seconds - 1e-7),
        "time_match_s",
    ]
    counts: dict[str, int] = {}
    for key, group in prepared.tracking.loc[
        prepared.tracking["player_key"].notna()
    ].groupby("player_key", sort=True):
        trace = group.loc[group["time_match_s"].isin(times)].sort_values("time_match_s")
        ok = (
            trace["coordinate_valid"].astype(bool).to_numpy()
            & np.isfinite(trace["x_m"].to_numpy(float))
            & np.isfinite(trace["y_m"].to_numpy(float))
        )
        if not ok.any() or not ok[-1]:
            continue
        start = len(ok) - 1
        while start > 0 and ok[start - 1]:
            start -= 1
        trace = trace.iloc[start:]
        if len(trace) >= 2:
            tx, ty = centered_to_pitch(trace["x_m"], trace["y_m"])
            color = DEFENDER_TRAIL_COLOR if str(key) in prepared.defender_keys else ATTACKER_COLOR
            artists.append(ax.plot(tx, ty, color=color, alpha=.42, linewidth=1.2, zorder=3)[0])
            counts[str(key)] = len(trace)
    return counts


def _draw_snapshot(
    ax,
    prepared: _PreparedVisualization,
    clip_spec: TrackingClipSpec,
    frame_id: object,
    *,
    cmap,
    norm: Normalize,
    trail_seconds: float,
    show_trails: bool,
    artists: list,
) -> dict[str, object]:
    time_s = float(
        prepared.frames.loc[prepared.frames["frame_id_provider"].eq(frame_id), "time_match_s"].iloc[0]
    )
    current = prepared.tracking.loc[prepared.tracking["frame_id_provider"].eq(frame_id)]
    valid = current.loc[
        current["coordinate_valid"].astype(bool)
        & np.isfinite(current["x_m"])
        & np.isfinite(current["y_m"])
    ]
    players = valid.loc[valid["entity_type"].eq("player")]

    trail_counts = (
        _draw_trails(ax, prepared, time_s, trail_seconds, artists) if show_trails else {}
    )
    attackers = players.loc[
        players["team_key"].eq(clip_spec.attacking_team_key)
        & ~players["player_key"].eq(clip_spec.focal_player_key)
    ]
    if not attackers.empty:
        x, y = centered_to_pitch(attackers["x_m"], attackers["y_m"])
        artists.append(
            ax.scatter(x, y, s=75, c=ATTACKER_COLOR, edgecolors="#f7f7f7", linewidths=.7, zorder=4)
        )
    focal = players.loc[players["player_key"].eq(clip_spec.focal_player_key)]
    if not focal.empty:
        x, y = centered_to_pitch(focal["x_m"], focal["y_m"])
        artists.append(
            ax.scatter(x, y, s=145, c=ATTACKER_COLOR, edgecolors=NEUTRAL_EDGE, linewidths=1.8, zorder=6)
        )

    supported_keys: list[str] = []
    unsupported_keys: list[str] = []
    raw_scores: dict[str, float | None] = {}
    supported_rows: list[pd.Series] = []
    unsupported_rows: list[pd.Series] = []
    for key in prepared.defender_keys:
        tracked = players.loc[players["player_key"].astype(str).eq(key)]
        score = prepared.player_by_key[(frame_id, key)]
        value = float(score["trailing_relative_path_m"])
        is_supported = str(score["support_status"]) == SUPPORTED and np.isfinite(value)
        raw_scores[key] = value if is_supported else None
        if is_supported:
            supported_keys.append(key)
            if not tracked.empty:
                supported_rows.append(tracked.iloc[0])
        else:
            unsupported_keys.append(key)
            if not tracked.empty:
                unsupported_rows.append(tracked.iloc[0])
    if supported_rows:
        table = pd.DataFrame(supported_rows)
        values = np.asarray([raw_scores[str(key)] for key in table["player_key"]], dtype=float)
        x, y = centered_to_pitch(table["x_m"], table["y_m"])
        artists.append(
            ax.scatter(
                x,
                y,
                s=92,
                c=cmap(norm(values)),
                edgecolors=NEUTRAL_EDGE,
                linewidths=.8,
                zorder=5,
            )
        )
    if unsupported_rows:
        table = pd.DataFrame(unsupported_rows)
        x, y = centered_to_pitch(table["x_m"], table["y_m"])
        artists.append(
            ax.scatter(
                x,
                y,
                s=92,
                facecolors="none",
                edgecolors=UNSUPPORTED_EDGE,
                linewidths=1.5,
                zorder=5,
            )
        )

    ball = valid.loc[valid["entity_type"].eq("ball")]
    if not ball.empty:
        x, y = centered_to_pitch(ball["x_m"], ball["y_m"])
        artists.append(
            ax.scatter(x, y, s=35, c="white", edgecolors=NEUTRAL_EDGE, linewidths=1.1, zorder=7)
        )
    team = prepared.team_by_frame[frame_id]
    team_value = float(team["mean_trailing_relative_path_m"])
    finite_scores = np.asarray([value for value in raw_scores.values() if value is not None], dtype=float)
    return {
        "frame_id_provider": str(frame_id),
        "time_match_s": time_s,
        "player_scores_m": MappingProxyType(raw_scores),
        "supported_defender_keys": tuple(supported_keys),
        "unsupported_defender_keys": tuple(unsupported_keys),
        "supported_marker_count": len(supported_rows),
        "unsupported_marker_count": len(unsupported_rows),
        "team_mean_m": team_value if np.isfinite(team_value) else None,
        "frame_saturation_count": int(np.count_nonzero(finite_scores > norm.vmax)),
        "trail_point_counts": MappingProxyType(trail_counts),
    }


def _add_team_meter(fig: Figure, score_vmin_m: float, score_vmax_m: float):
    meter = fig.add_axes([.13, .035, .30, .035])
    meter.set_xlim(score_vmin_m, score_vmax_m)
    meter.set_ylim(-.55, .55)
    meter.set_yticks([])
    meter.set_xticks([score_vmin_m, score_vmax_m])
    meter.tick_params(axis="x", labelsize=7, length=2)
    meter.set_xlabel("Team mean (m)", fontsize=8, labelpad=-1)
    for spine in meter.spines.values():
        spine.set_color("#777777")
        spine.set_linewidth(.7)
    return meter


def animate_defensive_reorganization(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    clip_spec: TrackingClipSpec,
    *,
    frame_step: int = 2,
    playback_fps: float = 12.5,
    trail_seconds: float = 0.4,
    score_vmin_m: float = 0.0,
    score_vmax_m: float = 4.0,
    show_team_meter: bool = True,
    show_trails: bool = True,
) -> AnimationBundle:
    """Animate committed trailing scores as a retrospective analyst replay."""
    if frame_step < 1 or playback_fps <= 0 or trail_seconds < 0:
        raise ValueError("invalid frame_step, playback_fps, or trail_seconds")
    # Validate the fixed visual transform independently of any current values.
    normalize_scores_for_display([], vmin_m=score_vmin_m, vmax_m=score_vmax_m)
    prepared = _prepare_visualization(tracking, scores, clip_spec)
    shown = prepared.frames.iloc[::frame_step].copy()
    if shown.index[-1] != prepared.frames.index[-1]:
        shown = pd.concat([shown, prepared.frames.tail(1)]).drop_duplicates("frame_id_provider")
    frame_ids = tuple(shown["frame_id_provider"].astype(str))

    pitch = Pitch(
        pitch_type="custom",
        pitch_length=105,
        pitch_width=68,
        pitch_color=PITCH_COLOR,
        line_color=LINE_COLOR,
    )
    fig, ax = pitch.draw(figsize=(11, 7.2))
    fig.subplots_adjust(bottom=.16, top=.87, right=.88)
    fig.suptitle("Defender-relative movement replay", color="#202124", fontsize=13, y=.965)
    semantics = ax.text(
        .01,
        1.02,
        "Retrospective analyst replay · score interval [t−2, t]",
        transform=ax.transAxes,
        fontsize=9,
        color="#202124",
    )
    time_text = ax.text(
        .99, 1.02, "", transform=ax.transAxes, ha="right", fontsize=9, color="#202124"
    )
    note = ax.text(
        .99,
        -.10,
        ANIMATION_NOTE,
        transform=ax.transAxes,
        ha="right",
        fontsize=8,
        color="#303030",
        clip_on=False,
    )
    cmap = plt.get_cmap("cividis")
    norm = Normalize(vmin=score_vmin_m, vmax=score_vmax_m, clip=True)
    scalar = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, ax=ax, fraction=.028, pad=.025, extend="max")
    colorbar.set_label(SCORE_LABEL, fontsize=8)
    colorbar.ax.tick_params(labelsize=8)
    meter_ax = _add_team_meter(fig, score_vmin_m, score_vmax_m) if show_team_meter else None

    artists: list = []
    state: dict[str, object] = {}

    def clear_dynamic() -> None:
        while artists:
            artists.pop().remove()

    def draw(index: int):
        clear_dynamic()
        frame_id = shown.iloc[index]["frame_id_provider"]
        current_state = _draw_snapshot(
            ax,
            prepared,
            clip_spec,
            frame_id,
            cmap=cmap,
            norm=norm,
            trail_seconds=trail_seconds,
            show_trails=show_trails,
            artists=artists,
        )
        relative = float(current_state["time_match_s"]) - clip_spec.anchor_time_s
        time_text.set_text(f"t {relative:+.2f} s")
        if meter_ax is not None:
            team_value = current_state["team_mean_m"]
            if team_value is not None:
                width = float(np.clip(team_value, score_vmin_m, score_vmax_m))
                artists.extend(meter_ax.barh([0], [width], left=score_vmin_m, height=.65, color="#6f7d83"))
                artists.append(
                    meter_ax.text(
                        score_vmax_m,
                        0,
                        f" {team_value:.2f}",
                        va="center",
                        ha="left",
                        fontsize=8,
                        color="#202124",
                        clip_on=False,
                    )
                )
        state.clear()
        state.update(current_state)
        return [*artists, semantics, time_text, note]

    animation = FuncAnimation(
        fig,
        draw,
        frames=len(shown),
        interval=1000.0 / playback_fps,
        blit=False,
        repeat=False,
    )
    animation._draw_frame = draw
    animation._reorganization_state = state
    displayed_player_scores = [
        prepared.player_by_key[(frame_id, key)]["trailing_relative_path_m"]
        for frame_id in shown["frame_id_provider"]
        for key in prepared.defender_keys
        if prepared.player_by_key[(frame_id, key)]["support_status"] == SUPPORTED
    ]
    display = normalize_scores_for_display(
        displayed_player_scores, vmin_m=score_vmin_m, vmax_m=score_vmax_m
    )
    unsupported_frames = sum(
        prepared.team_by_frame[frame_id]["support_status"] != SUPPORTED
        for frame_id in shown["frame_id_provider"]
    )
    animation._reorganization_metadata = MappingProxyType(
        {
            "retrospective_analyst_replay": True,
            "score_interval": "[t-2,t]",
            "score_vmin_m": float(score_vmin_m),
            "score_vmax_m": float(score_vmax_m),
            "saturation_count": int(display.saturation_count),
            "unsupported_score_frame_count": int(unsupported_frames),
            "trail_seconds": float(trail_seconds),
            "show_team_meter": bool(show_team_meter),
            "pitch_background": PITCH_COLOR,
        }
    )
    return AnimationBundle(
        figure=fig,
        animation=animation,
        native_frame_count=len(prepared.frames),
        displayed_frame_count=len(shown),
        source_fps=prepared.source_fps,
        playback_fps=float(playback_fps),
        elapsed_duration_s=float(
            prepared.frames["time_match_s"].iloc[-1] - prepared.frames["time_match_s"].iloc[0]
        ),
        playback_duration_s=float((len(shown) - 1) / playback_fps),
        displayed_frame_ids=frame_ids,
    )


def plot_defensive_reorganization_diagnostic(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    clip_spec: TrackingClipSpec,
    *,
    selected_time_s: float | None = None,
    trail_seconds: float = 0.4,
    score_vmin_m: float = 0.0,
    score_vmax_m: float = 4.0,
) -> Figure:
    """Create the two-panel static explanation of the committed score."""
    prepared = _prepare_visualization(tracking, scores, clip_spec)
    selected = clip_spec.anchor_time_s if selected_time_s is None else float(selected_time_s)
    matches = prepared.frames.loc[np.isclose(prepared.frames["time_match_s"], selected, atol=1e-7)]
    if len(matches) != 1:
        raise ValueError("selected diagnostic timestamp is unavailable exactly")
    frame_id = matches.iloc[0]["frame_id_provider"]
    cmap = plt.get_cmap("cividis")
    norm = Normalize(vmin=score_vmin_m, vmax=score_vmax_m, clip=True)

    fig = plt.figure(figsize=(13, 6.2))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.05, 1.35), wspace=.16)
    series_ax = fig.add_subplot(grid[0, 0])
    pitch_ax = fig.add_subplot(grid[0, 1])
    pitch = Pitch(
        pitch_type="custom",
        pitch_length=105,
        pitch_width=68,
        pitch_color=PITCH_COLOR,
        line_color=LINE_COLOR,
    )
    pitch.draw(ax=pitch_ax)

    player = scores.player_scores.loc[
        scores.player_scores["match_id"].eq(clip_spec.match_id)
        & scores.player_scores["period"].eq(clip_spec.period)
        & scores.player_scores["team_key"].eq(clip_spec.defending_team_key)
        & scores.player_scores["time_match_s"].between(clip_spec.start_time_s, clip_spec.end_time_s)
    ]
    team = scores.team_scores.loc[
        scores.team_scores["match_id"].eq(clip_spec.match_id)
        & scores.team_scores["period"].eq(clip_spec.period)
        & scores.team_scores["team_key"].eq(clip_spec.defending_team_key)
        & scores.team_scores["time_match_s"].between(clip_spec.start_time_s, clip_spec.end_time_s)
    ]
    for _, group in player.groupby("player_key", sort=True):
        series_ax.plot(
            group["time_match_s"] - clip_spec.anchor_time_s,
            group["trailing_relative_path_m"],
            color="#7d7d7d",
            linewidth=.8,
            alpha=.58,
        )
    series_ax.plot(
        team["time_match_s"] - clip_spec.anchor_time_s,
        team["mean_trailing_relative_path_m"],
        color="#162b4d",
        linewidth=2.4,
        label="Team mean",
    )
    series_ax.axvline(selected - clip_spec.anchor_time_s, color="#202124", linewidth=1, linestyle="--")
    series_ax.set_ylim(score_vmin_m, score_vmax_m)
    series_ax.set_xlabel("Time relative to governed anchor (s)")
    series_ax.set_ylabel(SCORE_LABEL)
    series_ax.set_title("A  Trailing scores")
    series_ax.grid(alpha=.2)
    series_ax.legend(frameon=False, loc="upper right")
    finite = player["trailing_relative_path_m"].to_numpy(float)
    saturation_count = int(np.count_nonzero(np.isfinite(finite) & (finite > score_vmax_m)))
    if saturation_count:
        series_ax.text(
            .02,
            .98,
            f"Saturation: {saturation_count} player-frame values >4 m\n(raw values retained)",
            transform=series_ax.transAxes,
            va="top",
            fontsize=7.5,
            color="#303030",
            bbox={"boxstyle": "round,pad=.2", "facecolor": "white", "alpha": .82, "edgecolor": "none"},
        )

    artists: list = []
    state = _draw_snapshot(
        pitch_ax,
        prepared,
        clip_spec,
        frame_id,
        cmap=cmap,
        norm=norm,
        trail_seconds=trail_seconds,
        show_trails=True,
        artists=artists,
    )
    pitch_ax.set_title(f"B  Physical replay frame · t {selected - clip_spec.anchor_time_s:+.2f} s")
    scalar = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, ax=pitch_ax, fraction=.035, pad=.02, extend="max")
    colorbar.set_label(SCORE_LABEL, fontsize=8)
    team_value = state["team_mean_m"]
    pitch_ax.text(
        .02,
        .025,
        "Team mean: unsupported" if team_value is None else f"Team mean: {team_value:.2f} m",
        transform=pitch_ax.transAxes,
        fontsize=9,
        color="white",
        bbox={"boxstyle": "round,pad=.25", "facecolor": "#202124", "alpha": .82, "edgecolor": "none"},
        zorder=10,
    )
    fig.suptitle("Retrospective trailing defender-relative movement diagnostic", fontsize=13)
    fig.text(.5, .015, INTERPRETATION_NOTE, ha="center", fontsize=8, color="#303030")
    fig._reorganization_metadata = MappingProxyType(
        {
            "selected_time_s": selected,
            "saturation_count": saturation_count,
            "snapshot_state": state,
            "pitch_background": PITCH_COLOR,
        }
    )
    return fig
