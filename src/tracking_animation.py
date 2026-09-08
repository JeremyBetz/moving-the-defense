"""Outcome-independent tracking replay on a physical 105 x 68 metre pitch."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import pandas as pd
from mplsoccer import Pitch


REQUIRED_COLUMNS = (
    "match_id", "period", "frame_id_provider", "time_match_s", "entity_type",
    "team_key", "player_key", "x_m", "y_m", "coordinate_valid",
    "pitch_length_m", "pitch_width_m",
)


@dataclass(frozen=True)
class TrackingClipSpec:
    match_id: str
    period: int
    anchor_time_s: float
    start_time_s: float
    end_time_s: float
    focal_player_key: str
    attacking_team_key: str
    defending_team_key: str
    defender_ranks: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.end_time_s <= self.start_time_s:
            raise ValueError("Clip end must be after clip start")
        if not self.start_time_s <= self.anchor_time_s <= self.end_time_s:
            raise ValueError("Anchor must lie inside the clip")
        if self.defender_ranks is not None:
            ranks = dict(self.defender_ranks)
            if len(ranks) != len(set(ranks)) or len(set(ranks.values())) != len(ranks):
                raise ValueError("Defender rank keys and values must be unique")
            object.__setattr__(self, "defender_ranks", MappingProxyType(ranks))


@dataclass(frozen=True)
class AnimationBundle:
    figure: plt.Figure
    animation: FuncAnimation
    native_frame_count: int
    displayed_frame_count: int
    source_fps: float
    playback_fps: float
    elapsed_duration_s: float
    playback_duration_s: float
    displayed_frame_ids: tuple[str, ...]


def centered_to_pitch(x_m, y_m):
    """Translate project-centred coordinates for mplsoccer; never clip."""
    return np.asarray(x_m, dtype=float) + 52.5, np.asarray(y_m, dtype=float) + 34.0


def _prepare(tracking: pd.DataFrame, spec: TrackingClipSpec, source_fps: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = set(REQUIRED_COLUMNS) - set(tracking.columns)
    if missing:
        raise ValueError(f"Missing normalized tracking columns: {sorted(missing)}")
    if source_fps <= 0:
        raise ValueError("source_fps must be positive")
    q = tracking.loc[
        (tracking["match_id"] == spec.match_id)
        & (tracking["period"] == spec.period)
        & tracking["time_match_s"].between(spec.start_time_s, spec.end_time_s)
    ].copy(deep=True)
    if q.empty:
        raise ValueError("Requested interval is unavailable")
    if not set(q["entity_type"].dropna().unique()) <= {"player", "ball"}:
        raise ValueError("entity_type must be player or ball")
    if not np.allclose(q["pitch_length_m"].astype(float), 105.0) or not np.allclose(q["pitch_width_m"].astype(float), 68.0):
        raise ValueError("Tracking must use a constant 105 x 68 m pitch")
    q["_entity_key"] = np.where(q["entity_type"].eq("ball"), "__ball__", q["player_key"].astype(str))
    if q.duplicated(["period", "frame_id_provider", "_entity_key"]).any():
        raise ValueError("Duplicate frame/entity rows")
    players = q.loc[q["entity_type"].eq("player")]
    identities = players.groupby("player_key", dropna=False)["team_key"].nunique(dropna=False)
    if (identities != 1).any():
        raise ValueError("Player/team identity changes within clip")
    frames = q[["frame_id_provider", "time_match_s"]].drop_duplicates().sort_values(
        ["time_match_s", "frame_id_provider"], kind="mergesort"
    ).reset_index(drop=True)
    if len(frames) < 2:
        raise ValueError("Requested interval must contain at least two native frames")
    expected = 1.0 / float(source_fps)
    gaps = np.diff(frames["time_match_s"].to_numpy(float))
    if not np.allclose(gaps, expected, atol=1e-7, rtol=0):
        raise ValueError("Native frame cadence is irregular")
    if not np.isclose(frames["time_match_s"].iloc[0], spec.start_time_s, atol=1e-7) or not np.isclose(
        frames["time_match_s"].iloc[-1], spec.end_time_s, atol=1e-7
    ):
        raise ValueError("Requested interval endpoints are unavailable exactly")
    focal = q.loc[q["player_key"].eq(spec.focal_player_key)]
    if len(focal) != len(frames) or not focal["coordinate_valid"].astype(bool).all() or not np.isfinite(focal[["x_m", "y_m"]]).all().all():
        raise ValueError("Focal attacker lacks complete observed coordinates")
    q = q.sort_values(["time_match_s", "entity_type", "team_key", "player_key"], kind="mergesort", na_position="last")
    return q, frames


def _phase(relative_s: float) -> str:
    if relative_s < -2.0:
        return "Context"
    if relative_s < 0.0:
        return "Exposure"
    if np.isclose(relative_s, 0.0):
        return "Exposure endpoint / Response start"
    return "Response"


def animate_tracking_window(
    tracking: pd.DataFrame,
    spec: TrackingClipSpec,
    *,
    source_fps: float,
    frame_step: int = 2,
    playback_fps: float = 12.5,
    trail_seconds: float = 0.4,
    show_trails: bool = True,
    show_annotations: bool = True,
    show_rank_highlights: bool = True,
) -> AnimationBundle:
    if frame_step < 1 or playback_fps <= 0 or trail_seconds < 0:
        raise ValueError("Invalid frame_step, playback_fps, or trail_seconds")
    q, frames = _prepare(tracking, spec, source_fps)
    shown = frames.iloc[::frame_step].copy()
    if shown.index[-1] != frames.index[-1]:
        shown = pd.concat([shown, frames.tail(1)]).drop_duplicates("frame_id_provider")
    frame_ids = tuple(shown["frame_id_provider"].astype(str))

    pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68, pitch_color="#315d3a", line_color="#f5f5f0")
    fig, ax = pitch.draw(figsize=(11, 7.2))
    ax.set_title("Physical tracking replay", color="#202124", fontsize=13)
    phase_text = ax.text(.01, 1.015, "", transform=ax.transAxes, fontsize=10, color="#202124")
    time_text = ax.text(.99, 1.015, "", transform=ax.transAxes, ha="right", fontsize=10, color="#202124")
    artists: list = []
    trail_native = int(np.floor(trail_seconds * source_fps + 1e-9))

    def clear_dynamic() -> None:
        while artists:
            artists.pop().remove()

    def draw(index: int):
        clear_dynamic()
        row = shown.iloc[index]
        now = float(row["time_match_s"])
        frame = str(row["frame_id_provider"])
        current = q.loc[q["frame_id_provider"].astype(str).eq(frame)]
        valid = current.loc[current["coordinate_valid"].astype(bool) & np.isfinite(current["x_m"]) & np.isfinite(current["y_m"])]
        players = valid.loc[valid["entity_type"].eq("player")]
        for team, color in ((spec.attacking_team_key, "#ed8b32"), (spec.defending_team_key, "#2767a8")):
            team_rows = players.loc[players["team_key"].eq(team) & ~players["player_key"].eq(spec.focal_player_key)]
            if not team_rows.empty:
                x, y = centered_to_pitch(team_rows["x_m"], team_rows["y_m"])
                artists.append(ax.scatter(x, y, s=75, c=color, edgecolors="#f7f7f7", linewidths=.7, zorder=4))
        focal = players.loc[players["player_key"].eq(spec.focal_player_key)]
        fx, fy = centered_to_pitch(focal["x_m"], focal["y_m"])
        artists.append(ax.scatter(fx, fy, s=150, c="#ed8b32", edgecolors="#202124", linewidths=2, zorder=6))
        ball = valid.loc[valid["entity_type"].eq("ball")]
        if not ball.empty:
            bx, by = centered_to_pitch(ball["x_m"], ball["y_m"])
            artists.append(ax.scatter(bx, by, s=35, c="white", edgecolors="#202124", linewidths=1.2, zorder=7))

        ranks = dict(spec.defender_ranks or {})
        if show_rank_highlights:
            for key, rank in sorted(ranks.items(), key=lambda item: item[1]):
                p = players.loc[players["player_key"].eq(key)]
                if p.empty:
                    continue
                px, py = centered_to_pitch(p["x_m"], p["y_m"])
                edge = "#34c759" if rank <= 3 else ("#9fb3c8" if rank <= 7 else "#2767a8")
                artists.append(ax.scatter(px, py, s=125 if rank <= 3 else 100, facecolors="none", edgecolors=edge, linewidths=2.2 if rank <= 3 else 1.4, zorder=8))
                if show_annotations and rank <= 7:
                    artists.append(ax.text(float(px[0]) + .8, float(py[0]) + .8, f"D{rank}", color=edge, fontsize=8, weight="bold", zorder=9))

        if show_trails and trail_native > 0:
            times = frames.loc[(frames["time_match_s"] <= now) & (frames["time_match_s"] >= now - trail_seconds - 1e-7), "time_match_s"]
            for key, group in q.loc[q["player_key"].notna()].groupby("player_key", sort=True):
                trace = group.loc[group["time_match_s"].isin(times)].sort_values("time_match_s")
                # A missing coordinate breaks support; keep only the consecutive valid tail.
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
                    color = "#ed8b32" if trace["team_key"].iloc[0] == spec.attacking_team_key else "#2767a8"
                    artists.append(ax.plot(tx, ty, color=color, alpha=.4, linewidth=1.2, zorder=3)[0])
        relative = now - spec.anchor_time_s
        phase_text.set_text(_phase(relative) if show_annotations else "")
        time_text.set_text(f"t {relative:+.2f} s" if show_annotations else "")
        return [*artists, phase_text, time_text]

    animation = FuncAnimation(fig, draw, frames=len(shown), interval=1000.0 / playback_fps, blit=False, repeat=False)
    animation._draw_frame = draw  # stable inspection hook for tests/notebooks
    return AnimationBundle(
        figure=fig,
        animation=animation,
        native_frame_count=len(frames),
        displayed_frame_count=len(shown),
        source_fps=float(source_fps),
        playback_fps=float(playback_fps),
        elapsed_duration_s=float(frames["time_match_s"].iloc[-1] - frames["time_match_s"].iloc[0]),
        playback_duration_s=float((len(shown) - 1) / playback_fps),
        displayed_frame_ids=frame_ids,
    )


def to_inline_html(bundle: AnimationBundle):
    from IPython.display import HTML
    return HTML(bundle.animation.to_jshtml(default_mode="once"))


def export_animation(bundle: AnimationBundle, path: str | Path) -> Path:
    destination = Path(path)
    suffix = destination.suffix.lower()
    if suffix == ".html":
        destination.write_text(bundle.animation.to_jshtml(default_mode="once"), encoding="utf-8")
    elif suffix == ".gif":
        bundle.animation.save(destination, writer=PillowWriter(fps=bundle.playback_fps))
    else:
        raise ValueError("Only .html and .gif animation exports are supported")
    return destination
