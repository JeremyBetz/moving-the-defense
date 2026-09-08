"""Render a presentation-only view of the closed IDSSE response-map aggregates.

This renderer intentionally reads only compact, already-published grid summaries.
It neither loads the protected registry nor reconstructs the response outcome.
The governed response-map figures remain separate, hash-pinned artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import Pitch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
GOVERNED_OUTPUT = ROOT / "outputs/localized_reorganization_response_map_v1"
GOVERNED_FIGURE = ROOT / "figures/localized_reorganization_response_map_v1"
AGGREGATE = GOVERNED_OUTPUT / "aggregate_response_grid.csv"
SUMMARY = GOVERNED_OUTPUT / "surface_summary.csv"
FINAL_HASHES = GOVERNED_OUTPUT / "final_hashes.json"
OUTPUT_BASE = ROOT / "figures/presentation/localized_reorganization_response_map_readme"

PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
HALF_LENGTH_M = PITCH_LENGTH_M / 2
HALF_WIDTH_M = PITCH_WIDTH_M / 2
CIRCLE_RADIUS_M = 9.15
PENALTY_DEPTH_M = 16.5
PENALTY_WIDTH_M = 40.32
GOAL_AREA_DEPTH_M = 5.5
GOAL_AREA_WIDTH_M = 18.32
PENALTY_SPOT_M = 11.0
DISPLAY_LIMIT_M = 0.55
VALID_CELLS = {5.0: 6373, 7.5: 6979, 10.0: 7132}
PANEL_ORDER = (7.5, 5.0, 10.0)


class PresentationMapError(RuntimeError):
    """Raised when the closed aggregate package cannot be presented faithfully."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered_to_pitch(x_m: np.ndarray | float, y_m: np.ndarray | float) -> tuple[np.ndarray | float, np.ndarray | float]:
    """Map stored centred metres to Matplotlib's 0--105 by 0--68 pitch frame."""
    return np.asarray(x_m) + HALF_LENGTH_M, np.asarray(y_m) + HALF_WIDTH_M


def pitch_landmarks() -> dict[str, tuple[float, ...]]:
    """Exact IFAB-metre landmarks in the plotting coordinate system."""
    penalty_y = (PITCH_WIDTH_M - PENALTY_WIDTH_M) / 2
    goal_area_y = (PITCH_WIDTH_M - GOAL_AREA_WIDTH_M) / 2
    return {
        "halfway_line": (HALF_LENGTH_M,),
        "centre": (HALF_LENGTH_M, HALF_WIDTH_M),
        "centre_circle_radius": (CIRCLE_RADIUS_M,),
        "left_penalty_area": (0.0, penalty_y, PENALTY_DEPTH_M, PENALTY_WIDTH_M),
        "right_penalty_area": (PITCH_LENGTH_M - PENALTY_DEPTH_M, penalty_y, PENALTY_DEPTH_M, PENALTY_WIDTH_M),
        "left_goal_area": (0.0, goal_area_y, GOAL_AREA_DEPTH_M, GOAL_AREA_WIDTH_M),
        "right_goal_area": (PITCH_LENGTH_M - GOAL_AREA_DEPTH_M, goal_area_y, GOAL_AREA_DEPTH_M, GOAL_AREA_WIDTH_M),
        "left_penalty_spot": (PENALTY_SPOT_M, HALF_WIDTH_M),
        "right_penalty_spot": (PITCH_LENGTH_M - PENALTY_SPOT_M, HALF_WIDTH_M),
    }


def pitch_model() -> Pitch:
    """Return mplsoccer's full regulation custom pitch in plotting metres."""
    return Pitch(
        pitch_type="custom", pitch_length=PITCH_LENGTH_M, pitch_width=PITCH_WIDTH_M,
        pitch_color="none", line_color="#263238", line_alpha=0.9, linewidth=0.85,
        line_zorder=5, goal_type="box", goal_alpha=0.9, axis=True, label=False, tick=True,
        pad_left=1.8, pad_right=1.8, pad_bottom=0.8, pad_top=0.8,
    )


def verify_closed_package() -> dict[str, str]:
    """Verify only the aggregate inputs and governed figures used for provenance."""
    ledger = json.loads(FINAL_HASHES.read_text(encoding="utf-8"))["artifacts_sha256"]
    paths = {
        "aggregate_response_grid.csv": AGGREGATE,
        "surface_summary.csv": SUMMARY,
        "figures/response_map.png": GOVERNED_FIGURE / "response_map.png",
        "figures/response_map.svg": GOVERNED_FIGURE / "response_map.svg",
    }
    actual = {name: sha256(path) for name, path in paths.items()}
    mismatch = {name: (actual[name], ledger[name]) for name in paths if actual[name] != ledger[name]}
    if mismatch:
        raise PresentationMapError(f"closed response package hash mismatch: {mismatch}")
    return actual


def load_aggregate_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read compact grid aggregates only; no anchor-level or protected data are used."""
    aggregate = pd.read_csv(AGGREGATE)
    summary = pd.read_csv(SUMMARY)
    expected = {"grid_x_m", "grid_y_m", "bandwidth_m", "support_profile", "support_valid", "equal_match_local_mean_m"}
    if set(aggregate.columns) != expected:
        raise PresentationMapError(f"unexpected aggregate schema: {list(aggregate.columns)}")
    if set(summary.bandwidth_m.astype(float)) != set(VALID_CELLS):
        raise PresentationMapError("summary does not contain exactly the frozen bandwidths")
    return aggregate, summary


def validate_display_inputs(aggregate: pd.DataFrame, summary: pd.DataFrame) -> dict[float, dict[str, float]]:
    """Confirm mask identity and exact values before using the fixed presentation scale."""
    statistics: dict[float, dict[str, float]] = {}
    for bandwidth, expected_count in VALID_CELLS.items():
        group = aggregate[(aggregate.bandwidth_m == bandwidth) & aggregate.support_valid].copy()
        values = group.equal_match_local_mean_m
        if len(group) != expected_count:
            raise PresentationMapError(f"h={bandwidth:g} has {len(group)} valid cells, expected {expected_count}")
        if values.isna().any() or not np.isfinite(values.to_numpy(float)).all():
            raise PresentationMapError(f"h={bandwidth:g} has missing/nonfinite supported aggregate values")
        if (values.abs() > DISPLAY_LIMIT_M).any():
            offending = values.loc[values.abs() > DISPLAY_LIMIT_M].iloc[0]
            raise PresentationMapError(f"h={bandwidth:g} value {offending:.12g} exceeds fixed ±{DISPLAY_LIMIT_M:g} m display scale")
        row = summary.loc[summary.bandwidth_m == bandwidth]
        if len(row) != 1 or int(row.iloc[0].support_valid_cell_count) != expected_count:
            raise PresentationMapError(f"h={bandwidth:g} summary disagrees with frozen valid-cell count")
        statistics[bandwidth] = {
            "minimum_m": float(values.min()), "maximum_m": float(values.max()),
            "median_m": float(values.median()), "mean_m": float(values.mean()),
            "saturation_count": int((values.abs() >= DISPLAY_LIMIT_M).sum()),
        }
    return statistics


def presentation_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("localized_reorganization", ["#2166ac", "#67a9cf", "#f7f7f7", "#ef8a62", "#b2182b"])


def _normalize_svg_whitespace(path: Path) -> None:
    """Keep the new, non-governed SVG compatible with Git whitespace checks."""
    path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


def _draw_pitch(ax: plt.Axes) -> None:
    """Draw mplsoccer's full regulation pitch over the 0--105 by 0--68 heatmap."""
    pitch_model().draw(ax=ax)


def _surface(axis: plt.Axes, aggregate: pd.DataFrame, bandwidth: float, label: str, primary: bool) -> matplotlib.collections.QuadMesh:
    group = aggregate.loc[aggregate.bandwidth_m == bandwidth].sort_values(["grid_y_m", "grid_x_m"], kind="mergesort")
    x = np.sort(group.grid_x_m.unique()); y = np.sort(group.grid_y_m.unique())
    values = group.equal_match_local_mean_m.to_numpy(float).reshape(len(y), len(x))
    values = np.ma.masked_where(~group.support_valid.to_numpy(bool).reshape(len(y), len(x)), values)
    px, py = centered_to_pitch(x, y)
    image = axis.pcolormesh(px, py, values, shading="nearest", cmap=presentation_colormap().with_extremes(bad="#c9cdd1"),
                            vmin=-DISPLAY_LIMIT_M, vmax=DISPLAY_LIMIT_M, zorder=1)
    _draw_pitch(axis)
    axis.set_title(f"{label} — h = {bandwidth:g} m", loc="left", fontsize=11.5 if primary else 10.2, weight="bold", pad=7)
    axis.tick_params(labelsize=8, colors="#263238")
    return image


def render_presentation_map(aggregate: pd.DataFrame, output_base: Path = OUTPUT_BASE) -> None:
    """Render the fixed-scale presentation figure from closed compact aggregates."""
    with matplotlib.rc_context({"svg.hashsalt": "moving-the-defense-presentation-response-map-v1", "font.family": "DejaVu Sans"}):
        fig = plt.figure(figsize=(15.0, 7.6))
        # Explicit margins reserve independent space for the shared scale and
        # presentation note; constrained layout otherwise lets those compete.
        layout = fig.add_gridspec(2, 2, width_ratios=(1.72, 1.0), height_ratios=(1, 1),
                                 left=0.065, right=0.985, top=0.895, bottom=0.245,
                                 wspace=0.13, hspace=0.16)
        primary = fig.add_subplot(layout[:, 0])
        small_top = fig.add_subplot(layout[0, 1])
        small_bottom = fig.add_subplot(layout[1, 1])
        image = _surface(primary, aggregate, 7.5, "Primary", True)
        _surface(small_top, aggregate, 5.0, "Sensitivity", False)
        _surface(small_bottom, aggregate, 10.0, "Sensitivity", False)
        primary.set_xlabel("Deeper  ←  Starting longitudinal position  →  Goalward", fontsize=9.5, labelpad=5)
        primary.set_ylabel("Physical lateral starting position (m)", fontsize=9.5, labelpad=5)
        small_top.set_xticklabels([])
        small_top.set_yticklabels([])
        small_bottom.set_xlabel("Deeper  ←  Goalward", fontsize=8.5, labelpad=3)
        small_bottom.set_yticklabels([])
        colorbar = fig.colorbar(image, cax=fig.add_axes((0.15, 0.105, 0.70, 0.028)), orientation="horizontal",
                                ticks=[-0.55, -0.275, 0.0, 0.275, 0.55])
        colorbar.set_label("Localized near-minus-middle response (m)", fontsize=10, labelpad=3)
        colorbar.ax.tick_params(labelsize=8.5)
        fig.suptitle("Localized defensive reorganization by attacker starting location", fontsize=16, weight="bold", x=0.46)
        fig.text(0.46, 0.935, "IDSSE seven-match sample · primary h=7.5 m with predeclared bandwidth sensitivities", ha="center", fontsize=9.5, color="#46515a")
        fig.text(0.5, 0.022, "Presentation display scale: ±0.55 m. Underlying aggregate estimates and support masks are unchanged.", ha="center", fontsize=8.2, color="#46515a")
        output_base.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_base.with_suffix(".png"), dpi=190, metadata={"Software": "Moving the Defense", "Creation Time": None})
        fig.savefig(output_base.with_suffix(".svg"), metadata={"Date": None, "Creator": "Moving the Defense"})
        plt.close(fig)
    _normalize_svg_whitespace(output_base.with_suffix(".svg"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-base", type=Path, default=OUTPUT_BASE)
    args = parser.parse_args(argv)
    verify_closed_package()
    aggregate, summary = load_aggregate_inputs()
    stats = validate_display_inputs(aggregate, summary)
    render_presentation_map(aggregate, args.output_base)
    print(json.dumps({"output_base": str(args.output_base), "display_limit_m": DISPLAY_LIMIT_M, "statistics": stats}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
