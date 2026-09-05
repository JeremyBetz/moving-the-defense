"""Build the Sloan-facing temporal-footprint figure from governed results.

Panel A renders one bounded, deterministic Metrica Game 2 passage.  It selects
the earliest chronological Game 2 anchor in the upper quartile of the already
governed two-second attacker-path registry, before looking at any defensive
response quantity.  The source opens only the small local tracking slice needed
to draw that passage; it never writes provider coordinates, fits a model, or
calculates a new scientific result.  Panels B and C read closed compact result
tables unchanged.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import polars as pl


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures" / "sloan"

NAVY = "#1F5A82"
TEAL = "#0B746A"
ORANGE = "#D97706"
GREY = "#667085"
LIGHT_GREY = "#D0D5DD"
NEAR = "#176B55"
MIDDLE = "#6B7C93"
FAR = "#B8C2CC"
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
GAME2_OUTPUT = ROOT / "outputs" / "spatial_defensive_response_footprint_game2_final_v1"
matplotlib.rcParams["svg.hashsalt"] = "moving-the-defense-temporal-footprint-v1"


def row(path: str, *, estimand: str) -> dict[str, float]:
    table = pd.read_csv(ROOT / path)
    match = table.loc[table["estimand"] == estimand]
    if len(match) != 1:
        raise ValueError(f"Expected one {estimand!r} row in {path}, found {len(match)}")
    return match.iloc[0].to_dict()


def interval_item(label: str, source: str, item: dict[str, float], colour: str, marker: str = "o") -> dict:
    return {
        "label": label,
        "source": source,
        "estimate": float(item["estimate"]),
        "low": float(item["ci_low"]),
        "high": float(item["ci_high"]),
        "colour": colour,
        "marker": marker,
    }


def _bounded_tracking_rows(path: Path, period: int, frame_start: int, frame_end: int) -> pd.DataFrame:
    """Keep only the locally bounded provider rows needed for the displayed passage."""
    retained: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, skiprows=2, chunksize=10_000):
        q = chunk.loc[(chunk["Period"] == period) & (chunk["Frame"] >= frame_start) & (chunk["Frame"] <= frame_end)]
        if not q.empty:
            retained.append(q)
        if int(chunk["Frame"].iloc[-1]) > frame_end:
            break
    if not retained:
        raise RuntimeError("The deterministic Game 2 display passage was unavailable")
    return pd.concat(retained, ignore_index=True).sort_values("Frame", kind="mergesort").reset_index(drop=True)


def _team_positions(rows: pd.DataFrame, team: str) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], np.ndarray, np.ndarray]:
    """Return only local physical-coordinate traces; raw provider values are never written."""
    frames = rows["Frame"].to_numpy(dtype=int)
    positions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    columns = list(rows.columns)
    for index, column in enumerate(columns[:-1]):
        if not column.startswith("Player"):
            continue
        number = column.removeprefix("Player")
        x = rows.iloc[:, index].to_numpy(dtype=float) * PITCH_LENGTH_M
        y = rows.iloc[:, index + 1].to_numpy(dtype=float) * PITCH_WIDTH_M
        positions[f"metrica:{team}:{number}"] = (frames, np.column_stack([x, y]))
    ball_index = columns.index("Ball")
    ball = np.column_stack([
        rows.iloc[:, ball_index].to_numpy(dtype=float) * PITCH_LENGTH_M,
        rows.iloc[:, ball_index + 1].to_numpy(dtype=float) * PITCH_WIDTH_M,
    ])
    return positions, frames, ball


def _smooth_trace(frames: np.ndarray, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The established centred seven-frame mean; no interpolation is introduced."""
    if len(xy) < 7 or not np.isfinite(xy).all():
        raise RuntimeError("Selected governed passage lacks complete local display support")
    kernel = np.ones(7, dtype=float) / 7.0
    return frames[3:-3], np.column_stack([np.convolve(xy[:, column], kernel, mode="valid") for column in range(2)])


def heldout_game2_geometry() -> dict[str, Any]:
    """Select one Game 2 visual passage from attacker-only governed information."""
    anchors = pl.read_parquet(GAME2_OUTPUT / "game2_anchors.parquet")
    q75 = float(anchors.select(pl.col("attacker_path_length_m").quantile(0.75, interpolation="linear")).item())
    selected = (
        anchors.filter(pl.col("attacker_path_length_m") >= q75)
        .sort(["time_match_s", "period", "time_period_s", "player_key", "observation_id"])
        .head(1)
        .to_dicts()[0]
    )
    links = (
        pl.read_parquet(GAME2_OUTPUT / "game2_linkage.parquet")
        .filter(pl.col("observation_id") == selected["observation_id"])
        .sort("distance_rank")
        .to_dicts()
    )
    if [int(item["distance_rank"]) for item in links] != list(range(1, 11)):
        raise RuntimeError("The selected governed anchor did not retain D1–D10 exactly once")

    # Seven-frame smoothing needs three observed frames on each side of the shown interval.
    anchor_frame = int(selected["frame_id_provider"])
    frame_start, frame_end = anchor_frame - 53, anchor_frame + 53
    data = ROOT / "data" / "metrica_sample_game_2"
    home, home_frames, home_ball = _team_positions(
        _bounded_tracking_rows(data / "Sample_Game_2_RawTrackingData_Home_Team.csv", int(selected["period"]), frame_start, frame_end),
        "Home",
    )
    away, away_frames, away_ball = _team_positions(
        _bounded_tracking_rows(data / "Sample_Game_2_RawTrackingData_Away_Team.csv", int(selected["period"]), frame_start, frame_end),
        "Away",
    )
    if not np.array_equal(home_frames, away_frames):
        raise RuntimeError("Home and away display frame grids differ")
    all_positions = {**home, **away}
    # Substitute/inactive columns remain in the provider file as all-missing; they are not display players.
    smoothed = {
        key: _smooth_trace(frames, xy)
        for key, (frames, xy) in all_positions.items()
        if np.isfinite(xy).all()
    }
    defender_keys = [str(item["player_key_defender"]) for item in links]
    attacker_key = str(selected["player_key"])
    required = [attacker_key, *defender_keys]
    if any(key not in smoothed for key in required):
        raise RuntimeError("Selected governed player identity was unavailable in the bounded display slice")

    # Orient this display left-to-right solely from the selected attacker's pre-anchor x displacement.
    flip_x = float(selected["attacker_delta_x_m"]) < 0.0

    def display(xy: np.ndarray) -> np.ndarray:
        x = PITCH_LENGTH_M - xy[:, 0] if flip_x else xy[:, 0]
        return np.column_stack([x, PITCH_WIDTH_M - xy[:, 1]])

    def exact_position(key: str, frame: int) -> np.ndarray:
        trace_frames, xy = smoothed[key]
        found = np.flatnonzero(trace_frames == frame)
        if len(found) != 1:
            raise RuntimeError(f"No unique smoothed display position for {key} at frame {frame}")
        return display(xy[found]) [0]

    def interval(key: str, start_frame: int, end_frame: int) -> np.ndarray:
        trace_frames, xy = smoothed[key]
        keep = (trace_frames >= start_frame) & (trace_frames <= end_frame)
        if not keep.any() or trace_frames[keep][0] != start_frame or trace_frames[keep][-1] != end_frame:
            raise RuntimeError(f"Incomplete display interval for {key}")
        return display(xy[keep])

    # All non-goalkeeping players actually present at the anchor are shown faintly in A1.
    goalkeeper_keys = {"metrica:Home:11", "metrica:Away:25"}
    attackers = [key for key in sorted(home) if key not in goalkeeper_keys and key in smoothed]
    ball_source = home_ball if np.isfinite(home_ball).all() else away_ball
    ball_index = np.flatnonzero(home_frames == anchor_frame)
    ball = None if len(ball_index) != 1 or not np.isfinite(ball_source[ball_index[0]]).all() else display(ball_source[ball_index]) [0]
    rank_by_key = {key: rank for rank, key in enumerate(defender_keys, start=1)}
    defender_start = {key: exact_position(key, anchor_frame) for key in defender_keys}
    defender_end = {key: exact_position(key, anchor_frame + 50) for key in defender_keys}
    unit_start = np.mean(np.vstack([defender_start[key] for key in defender_keys]), axis=0)
    unit_end = np.mean(np.vstack([defender_end[key] for key in defender_keys]), axis=0)
    relative_end: dict[str, np.ndarray] = {}
    for key in defender_keys:
        others = [other for other in defender_keys if other != key]
        shift = np.mean(np.vstack([defender_end[other] for other in others]), axis=0) - np.mean(
            np.vstack([defender_start[other] for other in others]), axis=0
        )
        relative_end[key] = defender_start[key] + (defender_end[key] - defender_start[key] - shift)
    return {
        "selected": selected,
        "q75": q75,
        "anchor_frame": anchor_frame,
        "attacker_key": attacker_key,
        "attacker_path": interval(attacker_key, anchor_frame - 50, anchor_frame),
        "attackers_at_anchor": {key: exact_position(key, anchor_frame) for key in attackers},
        "defender_keys": defender_keys,
        "rank_by_key": rank_by_key,
        "defender_start": defender_start,
        "defender_end": defender_end,
        "defender_paths": {key: interval(key, anchor_frame, anchor_frame + 50) for key in defender_keys},
        "unit_start": unit_start,
        "unit_end": unit_end,
        "relative_end": relative_end,
        "ball": ball,
    }


def _draw_pitch(ax) -> None:
    ax.add_patch(Rectangle((0, 0), PITCH_LENGTH_M, PITCH_WIDTH_M, fill=False, edgecolor="#98A2B3", lw=.9))
    ax.axvline(PITCH_LENGTH_M / 2, color="#D0D5DD", lw=.7)
    ax.add_patch(plt.Circle((PITCH_LENGTH_M / 2, PITCH_WIDTH_M / 2), 9.15, fill=False, color="#D0D5DD", lw=.7))
    for x, sign in [(0.0, 1.0), (PITCH_LENGTH_M, -1.0)]:
        ax.add_patch(Rectangle((x if sign > 0 else x - 16.5, (PITCH_WIDTH_M - 40.32) / 2), 16.5, 40.32, fill=False, edgecolor="#D0D5DD", lw=.7))
        ax.add_patch(Rectangle((x if sign > 0 else x - 5.5, (PITCH_WIDTH_M - 18.32) / 2), 5.5, 18.32, fill=False, edgecolor="#D0D5DD", lw=.7))
    ax.set(xlim=(-1, PITCH_LENGTH_M + 1), ylim=(-1, PITCH_WIDTH_M + 1), aspect="equal")
    ax.axis("off")


def _rank_colour(rank: int) -> str:
    return NEAR if rank <= 3 else (MIDDLE if rank <= 7 else FAR)


def panel_a(axes: list[Any]) -> dict[str, Any]:
    """Three real-pitch frames explaining the already-governed measurement."""
    geometry = heldout_game2_geometry()
    selected = geometry["selected"]
    focal = geometry["attacker_key"]
    defenders = geometry["defender_keys"]
    ranks = geometry["rank_by_key"]
    a1, a2, a3 = axes
    for ax in axes:
        _draw_pitch(ax)

    # A1: the deterministic attacker-only exposure selection and anchor geometry.
    for key, point in geometry["attackers_at_anchor"].items():
        if key != focal:
            a1.scatter(*point, s=18, color=ORANGE, alpha=.22, zorder=2)
    for key in defenders:
        rank = ranks[key]
        a1.scatter(*geometry["defender_start"][key], s=42 if rank <= 3 else 22,
                   color=_rank_colour(rank), alpha=1.0 if rank <= 3 else .45, zorder=3)
        if rank <= 3:
            a1.text(*(geometry["defender_start"][key] + np.array([1.2, 1.1])), f"D{rank}", fontsize=7.2, color=NEAR, weight="bold")
    a1.plot(geometry["attacker_path"][:, 0], geometry["attacker_path"][:, 1], color=ORANGE, lw=2.2, zorder=4)
    a1.annotate("", xy=geometry["attacker_path"][-1], xytext=geometry["attacker_path"][-8],
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=2.2))
    a1.scatter(*geometry["attacker_path"][0], s=20, facecolors="white", edgecolors=ORANGE, linewidths=.9, zorder=5)
    a1.scatter(*geometry["attacker_path"][-1], s=52, color=ORANGE, zorder=5)
    if geometry["ball"] is not None:
        a1.scatter(*geometry["ball"], s=26, facecolors="white", edgecolors="#344054", linewidths=1.1, zorder=6)
    # `display` orients the selected attacker's preceding x movement left to right.
    a1.annotate("attacking direction", xy=(.94, .94), xytext=(.59, .94), xycoords="axes fraction",
                textcoords="axes fraction", ha="left", va="center", fontsize=6.9, color="#344054",
                arrowprops=dict(arrowstyle="->", color="#344054", lw=1.1))
    a1.text(.02, .03, "orange: focal attacker   green: D1–D3   blue-grey: D4–D7", transform=a1.transAxes, fontsize=6.8, color=GREY)
    a1.set_title("A1  Exposure: preceding attacker movement", loc="left", fontsize=10.2, weight="bold")

    # A2: actual absolute post-anchor defender paths and the all-defender unit shift.
    for key in defenders:
        rank = ranks[key]
        path = geometry["defender_paths"][key]
        a2.plot(path[:, 0], path[:, 1], color=_rank_colour(rank), alpha=.95 if rank <= 3 else .4,
                lw=1.7 if rank <= 3 else .85, zorder=2)
        a2.scatter(*path[0], s=28 if rank <= 3 else 14, facecolors="white", edgecolors=_rank_colour(rank), linewidths=.8, zorder=3)
        if rank <= 3:
            a2.text(*(path[-1] + np.array([1.15, 1.0])), f"D{rank}", fontsize=7.2, color=NEAR, weight="bold")
    a2.annotate("", xy=geometry["unit_end"], xytext=geometry["unit_start"],
                arrowprops=dict(arrowstyle="->", color="#344054", lw=2.1, linestyle="--"))
    a2.scatter(*geometry["unit_end"], marker="X", color="#344054", s=36, zorder=6)
    a2.text(*(geometry["unit_end"] + np.array([1.3, 1.4])), "unit shift:\ngoalward + lateral", fontsize=6.8, color="#344054")
    a2.set_title("A2  Next 2 s: absolute defender movement", loc="left", fontsize=10.2, weight="bold")

    # A3: exact focal-relative vector construction, using each defender's leave-one-out unit shift.
    for key in defenders:
        rank = ranks[key]
        start, end = geometry["defender_start"][key], geometry["relative_end"][key]
        emph = rank <= 3 or rank in {4, 5}
        a3.scatter(*start, s=24 if emph else 10, facecolors="white", edgecolors=_rank_colour(rank), linewidths=.7, alpha=1 if emph else .25, zorder=3)
        if emph:
            a3.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", color=_rank_colour(rank), lw=2.0 if rank <= 3 else 1.2, alpha=.95 if rank <= 3 else .65))
        if rank <= 3:
            a3.text(*(end + np.array([1.1, 1.0])), f"D{rank}", fontsize=7.2, color=NEAR, weight="bold")
    a3.text(.02, .03, "arrow = defender movement − leave-one-out defensive-unit shift", transform=a3.transAxes, fontsize=6.7, color=GREY)
    a3.set_title("A3  Same movement relative to the defensive unit", loc="left", fontsize=10.2, weight="bold")
    return geometry


def metrica_items() -> list[dict]:
    game1 = row("outputs/spatial_defensive_response_footprint_game1_v1/regional_contrasts.csv", estimand="Delta_NM")
    game2 = row("outputs/spatial_defensive_response_footprint_game2_final_v1/game2_regional.csv", estimand="Delta_NM")
    pooled = row("outputs/spatial_defensive_response_footprint_game2_final_v1/pooled_regional.csv", estimand="Delta_NM")
    return [
        interval_item("Metrica Game 1  development", "Metrica", game1, NAVY),
        interval_item("Metrica Game 2  heldout", "Metrica", game2, NAVY),
        interval_item("Metrica pooled", "Metrica", pooled, NAVY, marker="D"),
    ]


def idsse_items() -> list[dict]:
    table = pd.read_csv(ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/coefficient_intervals.csv")
    selected = table.loc[(table["family"] == "primary") & (table["estimand"] == "near_minus_middle")]
    order = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9", "POOLED"]
    items = []
    for match in order:
        matched = selected.loc[selected["match_id"] == match]
        if len(matched) != 1:
            raise ValueError(f"Expected one IDSSE primary row for {match}")
        label = "IDSSE pooled" if match == "POOLED" else f"IDSSE {match}"
        items.append(interval_item(label, "IDSSE", matched.iloc[0].to_dict(), TEAL, marker="D" if match == "POOLED" else "o"))
    return items


def panel_b(ax) -> None:
    metrica = metrica_items()
    idsse = idsse_items()
    rows = metrica[:2] + idsse[:-1] + [metrica[2], idsse[-1]]
    y = np.arange(len(rows))[::-1]
    ax.axvline(0, color="#98A2B3", lw=.9, zorder=0)
    for yi, item in zip(y, rows):
        ax.plot([item["low"], item["high"]], [yi, yi], color=item["colour"], lw=1.9, solid_capstyle="round")
        ax.scatter(item["estimate"], yi, color=item["colour"], marker=item["marker"], s=38 if item["marker"] == "o" else 47, zorder=3)
    ax.axhline(8.5, color=LIGHT_GREY, lw=.8)
    ax.axhline(1.5, color=LIGHT_GREY, lw=.8)
    ax.set_yticks(y, [item["label"] for item in rows], fontsize=8.2)
    ax.set_xlabel("Near − middle coefficient (m defender-relative path / m preceding attacker path)", fontsize=8.4)
    ax.set_xlim(-.01, .18)
    ax.set_title("B  The localized association replicates across matches", loc="left", fontsize=11.5, weight="bold")
    ax.text(.01, .94, "Circles: individual matches   ◆: within-environment pooled estimate",
            transform=ax.transAxes, fontsize=7.3, color=GREY, va="top")
    ax.text(.01, -.18, "Metrica intervals: 97.5%; IDSSE intervals: 95%. Pools are shown separately, not as a nine-match meta-analysis.",
            transform=ax.transAxes, fontsize=7.0, color=GREY, va="top")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#EAECF0", lw=.8)


def temporal_rows() -> list[dict]:
    metrica_primary = row("outputs/spatial_defensive_response_footprint_game2_final_v1/pooled_regional.csv", estimand="Delta_NM")
    metrica_reverse = row("outputs/spatial_defensive_response_footprint_game2_final_v1/pooled_placebo.csv", estimand="Delta_NM")
    metrica_excess = row("outputs/spatial_defensive_response_footprint_game2_final_v1/pooled_primary_placebo_paired.csv", estimand="primary_minus_placebo_Delta_NM")
    idsse = pd.read_csv(ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/coefficient_intervals.csv")

    def idsse_row(analysis: str, estimand: str) -> dict:
        matched = idsse.loc[(idsse["match_id"] == "POOLED") & (idsse["family"] == analysis) & (idsse["estimand"] == estimand)]
        if len(matched) != 1:
            raise ValueError(f"Expected one IDSSE {analysis}/{estimand} pooled row")
        return matched.iloc[0].to_dict()

    return [
        interval_item("Forward primary", "Metrica", metrica_primary, NAVY),
        interval_item("Reverse-time comparison", "Metrica", metrica_reverse, GREY),
        interval_item("Paired forward − reverse", "Metrica", metrica_excess, ORANGE),
        interval_item("Forward primary", "IDSSE", idsse_row("primary", "near_minus_middle"), TEAL),
        interval_item("Reverse-time comparison", "IDSSE", idsse_row("placebo", "near_minus_middle"), GREY),
        interval_item("Paired forward − reverse", "IDSSE", idsse_row("paired_primary_minus_placebo", "near_minus_middle"), ORANGE),
    ]


def panel_c(ax) -> None:
    rows = temporal_rows()
    y = np.array([5, 4, 3, 1.5, .5, -.5])
    ax.axvline(0, color="#98A2B3", lw=.9, zorder=0)
    for yi, item in zip(y, rows):
        ax.plot([item["low"], item["high"]], [yi, yi], color=item["colour"], lw=2.1, solid_capstyle="round")
        ax.scatter(item["estimate"], yi, color=item["colour"], s=40, zorder=3)
        ax.text(item["high"] + .002, yi, f"{item['estimate']:.3f}", fontsize=7.4, va="center", color=item["colour"])
    ax.axhline(2.25, color=LIGHT_GREY, lw=.8)
    ax.set_yticks(y, ["Metrica: " + item["label"] for item in rows[:3]] + ["IDSSE: " + item["label"] for item in rows[3:]], fontsize=7.8)
    ax.set_xlim(-.014, .085)
    ax.set_ylim(-1.1, 5.9)
    ax.set_xlabel("Near − middle association (m/m)", fontsize=8.4)
    ax.set_title("C  Forward association exceeds reverse time", loc="left", fontsize=11.5, weight="bold")
    ax.text(.01, -.18, "Reverse-time structure remains positive. The evidence is paired forward − reverse excess, not a reverse-time null.",
            transform=ax.transAxes, fontsize=7.0, color=GREY, va="top")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#EAECF0", lw=.8)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(19.5, 11.1))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.02, 1.08], hspace=.57, wspace=.38)
    pitch_grid = grid[0, :].subgridspec(1, 3, wspace=.10)
    geometry = panel_a([fig.add_subplot(pitch_grid[0, index]) for index in range(3)])
    panel_b(fig.add_subplot(grid[1, 0]))
    panel_c(fig.add_subplot(grid[1, 1]))
    fig.suptitle("Time-ordered localized defensive reorganization", x=.13, y=.992,
                 ha="left", fontsize=14.2, weight="bold")
    fig.text(.13, .958,
             f"Panel A: deterministic heldout Metrica Game 2 anchor at {float(geometry['selected']['time_period_s']):.2f} s "
             "(earliest eligible anchor at or above the upper quartile of preceding attacker path; selection uses attacker movement only).",
             fontsize=7.7, color=GREY, va="top")
    fig.text(.13, .030, "Replicated: localized, time-ordered defensive reorganization.   Not established: causation, tactical meaning, opportunity, or value.",
             fontsize=8.7, color="#344054")
    fig.subplots_adjust(left=.13, right=.98, bottom=.15, top=.90)
    for suffix, kwargs in (("svg", {"metadata": {"Date": None}}), ("png", {"dpi": 240}), ("pdf", {"metadata": {"CreationDate": None, "ModDate": None}})):
        fig.savefig(OUT / f"temporal_footprint_flagship.{suffix}", facecolor="white", **kwargs)
    plt.close(fig)
    # Avoid harmless trailing SVG whitespace producing noisy repository checks.
    svg = OUT / "temporal_footprint_flagship.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
