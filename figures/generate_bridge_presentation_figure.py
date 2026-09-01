"""Render a documentation figure from frozen bridge outputs without refitting."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
GAME1 = ROOT / "outputs" / "attacker_defender_bridge_game1_v1"
GAME2 = ROOT / "outputs" / "attacker_defender_bridge_game2_v1"
OUTPUT = ROOT / "figures" / "bridge" / "bridge_replication_and_controls.png"


def rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["model"]: row for row in csv.DictReader(handle)}


def estimate(table: dict[str, dict[str, str]], model: str) -> float:
    return float(table[model]["beta1"])


def interval(table: dict[str, dict[str, str]], model: str) -> tuple[float, float]:
    row = table[model]
    return float(row["ci_low"]), float(row["ci_high"])


g1_coef = rows(GAME1 / "model_coefficients.csv")
g1_ci = rows(GAME1 / "bootstrap_summaries.csv")
g2_coef = rows(GAME2 / "game2_model_coefficients.csv")
g2_ci = rows(GAME2 / "game2_bootstrap_summaries.csv")
pooled_coef = rows(GAME2 / "pooled_model_coefficients.csv")
pooled_ci = rows(GAME2 / "pooled_bootstrap_summaries.csv")
paired_ci = rows(GAME2 / "pooled_paired_bootstrap_differences.csv")
final_results = json.loads((GAME2 / "final_results.json").read_text(encoding="utf-8"))

primary = [
    ("Game 1", estimate(g1_coef, "primary_local_2s"), interval(g1_ci, "primary_local_2s")),
    ("Game 2", estimate(g2_coef, "primary_local_2s"), interval(g2_ci, "primary_local_2s")),
    ("Pooled", estimate(pooled_coef, "primary_local_2s"), interval(pooled_ci, "primary_local_2s")),
]
controls = [
    ("Local − nonlocal", float(final_results["pooled_differences"]["local_minus_nonlocal"]), interval(paired_ci, "local_minus_nonlocal")),
    ("Primary − reverse-time", float(final_results["pooled_differences"]["local_minus_placebo"]), interval(paired_ci, "local_minus_placebo")),
]

plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold"})
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
colors = ["#4C78A8", "#F58518", "#2E8B57"]

for ax, data, title, xlabel in [
    (axes[0], primary, "Primary association replicated", "Additional local defender-relative path per metre of attacker path"),
    (axes[1], controls, "Frozen controls remained lower", "Paired coefficient difference"),
]:
    labels = [item[0] for item in data]
    values = [item[1] for item in data]
    lows = [item[1] - item[2][0] for item in data]
    highs = [item[2][1] - item[1] for item in data]
    ypos = list(range(len(data)))[::-1]
    for i, (y, value, low, high) in enumerate(zip(ypos, values, lows, highs)):
        ax.errorbar(value, y, xerr=[[low], [high]], fmt="o", color=colors[i], markersize=8, capsize=4, linewidth=2)
        ax.text(value, y + 0.22, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    ax.axvline(0, color="#555555", linewidth=1, linestyle="--")
    ax.set_yticks(ypos, labels)
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.22)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

fig.suptitle("Attacker movement and subsequent local defensive movement", fontsize=15, fontweight="bold")
fig.text(0.5, -0.02, "Frozen two-match observational bridge; points are saved coefficients/contrasts and bars are 95% 60-second block-bootstrap intervals.", ha="center", fontsize=9, color="#444444")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
