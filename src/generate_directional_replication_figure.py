"""Render manuscript Figure 2 from closed aggregate directional results only.

The figure deliberately reads compact, publication-safe coefficients and
intervals. It never opens provider tracking, row-level observations, or any
other empirical-analysis artifact.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "figures" / "sloan"
IDSSE_POOLED = ROOT / "outputs" / "defensive_reorganization_spatial_value_v1" / "primary_contrast.csv"
IDSSE_MATCHES = ROOT / "outputs" / "defensive_reorganization_spatial_value_v1" / "per_match_primary.csv"
SKILLCORNER_POOLED = ROOT / "outputs" / "defensive_reorganization_spatial_form_v1_skillcorner_external" / "primary_contrast.csv"
SKILLCORNER_MATCHES = ROOT / "outputs" / "defensive_reorganization_spatial_form_v1_skillcorner_external" / "per_match_coefficients.csv"

IDSSE_EXPECTED = (0.056855865053930386, 0.051357502908698824, 0.062430030351618114)
SKILLCORNER_EXPECTED = (0.04888315393173942, 0.042940468423309466, 0.05470717099579395)

IDSSE_COLOUR = "#1F5A82"
SKILLCORNER_COLOUR = "#9A4F2B"
GREY = "#667085"
LIGHT_GREY = "#D0D5DD"
matplotlib.rcParams["svg.hashsalt"] = "moving-the-defense-directional-replication-v1"


def read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"Expected one compact result row in {path}, found {len(rows)}")
    return rows[0]


def read_many(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No compact match-level rows found in {path}")
    return rows


def checked_pooled(
    path: Path, expected: tuple[float, float, float], estimate_column: str
) -> tuple[float, float, float]:
    row = read_one(path)
    values = tuple(float(row[key]) for key in (estimate_column, "ci_low", "ci_high"))
    if not np.allclose(values, expected, rtol=0.0, atol=1e-12):
        raise ValueError(f"Closed aggregate result in {path} did not match the recorded Figure 2 value")
    return values


def checked_matches(path: Path, expected_count: int) -> list[float]:
    rows = read_many(path)
    values = [float(row["outward_minus_goalward_m_per_m"]) for row in rows]
    if len(values) != expected_count:
        raise ValueError(f"Expected {expected_count} compact match-level contrasts in {path}, found {len(values)}")
    if not all(value > 0.0 for value in values):
        raise ValueError(f"A closed match-level contrast in {path} was not positive")
    return values


def render() -> None:
    idsse = checked_pooled(IDSSE_POOLED, IDSSE_EXPECTED, "estimate")
    skillcorner = checked_pooled(SKILLCORNER_POOLED, SKILLCORNER_EXPECTED, "outward_minus_goalward_m_per_m")
    idsse_matches = checked_matches(IDSSE_MATCHES, 7)
    skillcorner_matches = checked_matches(SKILLCORNER_MATCHES, 9)

    figure, (pooled_axis, match_axis) = plt.subplots(
        1, 2, figsize=(7, 5), gridspec_kw={"width_ratios": [1, 1.05]}
    )
    figure.subplots_adjust(left=0.15, right=0.98, bottom=0.27, top=0.78, wspace=0.65)

    sources = [
        ("IDSSE\n(7 matches)", *idsse, IDSSE_COLOUR, "o"),
        ("SkillCorner\n(9 matches)", *skillcorner, SKILLCORNER_COLOUR, "s"),
    ]
    for y, (label, estimate, low, high, colour, marker) in zip([1, 0], sources, strict=True):
        pooled_axis.plot([low, high], [y, y], color=colour, linewidth=3.0, solid_capstyle="round")
        pooled_axis.scatter(estimate, y, color=colour, marker=marker, s=72, zorder=3)
        pooled_axis.text(
            estimate, y + 0.16, f"{estimate:.3f}",
            ha="center", va="bottom", fontsize=9, color=colour, weight="bold"
        )
    pooled_axis.axvline(0, color="#344054", linewidth=1.0, zorder=0)
    pooled_axis.set_xlim(-0.004, 0.078)
    pooled_axis.set_ylim(-0.55, 1.55)
    pooled_axis.set_yticks([1, 0], [item[0] for item in sources], fontsize=9)
    pooled_axis.set_xlabel("Outward minus goalward\nassociation (m/m)", fontsize=9)
    pooled_axis.set_title("A  Separate provider estimates", loc="left", fontweight="bold", fontsize=10, pad=12)
    pooled_axis.grid(axis="x", color="#EAECF0", linewidth=0.9)
    pooled_axis.spines[["top", "right", "left"]].set_visible(False)
    pooled_axis.tick_params(axis="y", length=0)
    pooled_axis.tick_params(axis="x", labelsize=9)
    figure.text(.05, .09, "Modeled 5 m comparison:\nIDSSE ≈28 cm · SkillCorner ≈24 cm\n"
                "Difference in near–middle defender-relative path", fontsize=8,
                color="#344054", va="center", linespacing=1.5)

    match_values = [("IDSSE", idsse_matches, IDSSE_COLOUR, "o"), ("SkillCorner", skillcorner_matches, SKILLCORNER_COLOUR, "s")]
    y = 0
    ticks: list[int] = []
    labels: list[str] = []
    for provider, values, colour, marker in match_values:
        positions = np.arange(y, y + len(values))
        match_axis.scatter(values, positions, color=colour, marker=marker, s=42, zorder=3, label=provider)
        ticks.extend(positions.tolist())
        labels.extend([f"{provider} {index}" for index in range(1, len(values) + 1)])
        y += len(values)
    match_axis.axhline(6.5, color=LIGHT_GREY, linewidth=1.0)
    match_axis.axvline(0, color="#344054", linewidth=1.0, zorder=0)
    match_axis.set_xlim(-0.004, 0.078)
    match_axis.set_yticks(ticks, labels, fontsize=8)
    match_axis.invert_yaxis()
    match_axis.set_xlabel("Outward minus goalward\nassociation (m/m)", fontsize=9)
    match_axis.set_title("B  Individual matches", loc="left", fontweight="bold", fontsize=10, pad=12)
    match_axis.grid(axis="x", color="#EAECF0", linewidth=0.9)
    match_axis.spines[["top", "right", "left"]].set_visible(False)
    match_axis.tick_params(axis="y", length=0)
    match_axis.tick_params(axis="x", labelsize=9)
    match_axis.text(.006, 3, "7/7\npositive", fontsize=8, color=IDSSE_COLOUR, ha="left", va="center")
    match_axis.text(.006, 11, "9/9\npositive", fontsize=8, color=SKILLCORNER_COLOUR, ha="left", va="center")

    figure.suptitle(
        "Directional difference replicates across tracking environments",
        x=0.04, y=0.97, ha="left", fontsize=12, fontweight="bold"
    )
    figure.text(
        0.04, 0.90,
        "Outward: away from the pitch centreline · Goalward: toward goal",
        fontsize=9, color="#344054"
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for suffix, options in (
        ("svg", {"metadata": {"Date": None}}),
        ("png", {"dpi": 240, "metadata": {"Software": "Moving the Defense"}}),
        ("pdf", {"metadata": {"CreationDate": None, "ModDate": None}}),
    ):
        figure.savefig(OUTPUT / f"directional_replication.{suffix}", facecolor="white", **options)
    plt.close(figure)
    svg = OUTPUT / "directional_replication.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    render()
