"""Build the Sloan-facing temporal-footprint figure from closed compact results.

Panel A is deliberately synthetic: it explains the measurement without opening
provider tracking rows or choosing a match passage. Panels B and C read only
committed governed compact result tables; this script never fits a model or
calculates a new scientific quantity.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures" / "sloan"

NAVY = "#1F5A82"
TEAL = "#0B746A"
ORANGE = "#D97706"
GREY = "#667085"
LIGHT_GREY = "#D0D5DD"
PALE_GREEN = "#F2F8F5"
NEAR = "#176B55"
MIDDLE = "#6B7C93"
FAR = "#B8C2CC"
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


def panel_a(ax) -> None:
    """Synthetic measurement sketch—no real passage or provider data."""
    start = np.array(
        [
            [5.1, 1.7], [5.5, 2.8], [5.4, 4.1], [5.7, 5.3],
            [7.0, 1.4], [7.2, 2.5], [7.1, 3.8], [7.6, 5.0],
            [8.6, 1.8], [8.8, 4.0],
        ],
        dtype=float,
    )
    unit_shift = np.array([.85, .24])
    end = start + unit_shift
    # One near defender additionally departs from the common shift.
    end[1] += np.array([-.55, -1.05])
    colours = [NEAR] * 3 + [MIDDLE] * 4 + [FAR] * 3
    ax.add_patch(Ellipse((7.25, 3.45), 4.6, 5.6, facecolor=PALE_GREEN, edgecolor="#B8D7CA", lw=1.0, ls="--", zorder=0))
    ax.text(7.25, 6.55, "defensive unit", ha="center", color="#315E50", fontsize=8.7, weight="bold")
    for s, e, colour in zip(start, end, colours):
        ax.annotate("", xy=e, xytext=s, arrowprops=dict(arrowstyle="->", color=colour, lw=1.8, alpha=.9))
        ax.scatter(*s, s=30, facecolors="white", edgecolors=colour, linewidths=1.3, zorder=3)
        ax.scatter(*e, s=34, color=colour, zorder=4)

    centroid_start = start.mean(axis=0)
    centroid_end = (start + unit_shift).mean(axis=0)
    ax.annotate("", xy=centroid_end, xytext=centroid_start,
                arrowprops=dict(arrowstyle="->", color="#344054", lw=2.1, linestyle="--"))
    ax.scatter(*centroid_end, marker="X", color="#344054", s=42, zorder=6)
    ax.text(centroid_end[0] - .2, centroid_end[1] + .57, "shared\ndefensive-unit shift", fontsize=8.0, color="#344054", ha="center")

    attacker_start, attacker_end = np.array([.9, 4.7]), np.array([3.15, 3.65])
    ax.annotate("", xy=attacker_end, xytext=attacker_start,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=2.4))
    ax.scatter(*attacker_end, color=ORANGE, s=47, zorder=6)
    ax.text(.35, 5.37, "preceding\nattacker path", color=ORANGE, fontsize=8.5, ha="left")

    focal_start, focal_end = start[1], end[1]
    baseline = focal_start + unit_shift
    ax.plot([baseline[0], focal_end[0]], [baseline[1], focal_end[1]], color=ORANGE, lw=2.6, zorder=5)
    ax.annotate("extra defender-relative\nmovement", xy=focal_end, xytext=(1.0, 1.05), color=ORANGE,
                fontsize=8.2, ha="left", arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.15))
    ax.text(.35, .30, "Near D1–D3", color=NEAR, fontsize=8.3, weight="bold")
    ax.text(3.15, .30, "Middle D4–D7", color=MIDDLE, fontsize=8.3, weight="bold")
    ax.text(6.45, .30, "Far D8–D10", color=GREY, fontsize=8.3, weight="bold")
    ax.set(xlim=(0, 10.4), ylim=(0, 7.0))
    ax.axis("off")
    ax.set_title("A  Measure movement within the defensive unit", loc="left", fontsize=11.5, weight="bold")
    ax.text(.0, -.06, "Synthetic schematic: absolute defender paths = shared shift + relative movement.",
            transform=ax.transAxes, fontsize=7.4, color=GREY, va="top")


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
    ax.set_title("B  The time-ordered footprint replicates across matches", loc="left", fontsize=11.5, weight="bold")
    ax.text(.01, .94, "Circles: individual matches   ◆: governed within-environment pooled estimate",
            transform=ax.transAxes, fontsize=7.3, color=GREY, va="top")
    ax.text(.01, -.22, "Metrica intervals: frozen 97.5%; IDSSE intervals: frozen 95%. Pools are shown separately, not as a nine-match meta-analysis.",
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
    ax.text(.01, -.25, "Reverse-time structure remains positive. The evidence is paired forward − reverse excess, not a reverse-time null.",
            transform=ax.transAxes, fontsize=7.0, color=GREY, va="top")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#EAECF0", lw=.8)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(19.5, 7.6))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.22, 1.17, 1.16], wspace=.65)
    panel_a(fig.add_subplot(grid[0, 0]))
    panel_b(fig.add_subplot(grid[0, 1]))
    panel_c(fig.add_subplot(grid[0, 2]))
    fig.suptitle("Moving the Defense: a replicated temporal footprint of localized defensive movement", x=.022,
                 ha="left", fontsize=16, weight="bold")
    fig.text(.022, .022, "Replicated: localized time-ordered defensive footprint.   Not established: causation, tactical meaning, opportunity, or value.",
             fontsize=8.7, color="#344054")
    fig.subplots_adjust(left=.03, right=.985, bottom=.16, top=.88, wspace=.65)
    for suffix, kwargs in (("svg", {"metadata": {"Date": None}}), ("png", {"dpi": 240}), ("pdf", {"metadata": {"CreationDate": None, "ModDate": None}})):
        fig.savefig(OUT / f"temporal_footprint_flagship.{suffix}", facecolor="white", **kwargs)
    plt.close(fig)
    # Avoid harmless trailing SVG whitespace producing noisy repository checks.
    svg = OUT / "temporal_footprint_flagship.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
