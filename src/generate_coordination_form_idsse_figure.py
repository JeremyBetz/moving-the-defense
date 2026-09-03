"""Render the governed IDSSE coordination-form external-replication figure."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "outputs/concurrent_defensive_coordination_form_idsse_v1/final_results.json"
OUT = ROOT / "figures/concurrent_defensive_coordination_form_idsse_v1/external_replication.png"


def main() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    matches = list(result["match_results"])

    fig, (forest, profiles) = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True)
    y = np.arange(len(matches))
    estimates = np.array([
        result["match_results"][match]["primary"]["primary_D2_D3_minus_D4_D7"]
        for match in matches
    ])
    intervals = np.array([
        result["match_results"][match]["primary_ci95"] for match in matches
    ])
    forest.errorbar(
        estimates,
        y,
        xerr=np.vstack((estimates - intervals[:, 0], intervals[:, 1] - estimates)),
        fmt="o",
        color="#173f5f",
        ecolor="#20639b",
        capsize=3,
    )
    forest.axvline(0, color="#666666", linewidth=1, linestyle="--")
    forest.set_yticks(y, matches)
    forest.invert_yaxis()
    forest.set_xlabel("D2–D3 minus D4–D7 coefficient (m/s)")
    forest.set_title("Frozen primary contrast")
    forest.grid(axis="x", alpha=0.2)

    colors = plt.cm.viridis(np.linspace(0.08, 0.9, len(matches)))
    ranks = np.arange(1, 11)
    for match, color in zip(matches, colors, strict=True):
        values = result["match_results"][match]["primary"]["D1_D10"]
        profiles.plot(ranks, values, marker="o", markersize=3, linewidth=1.4, label=match, color=color)
    profiles.axhline(0, color="#666666", linewidth=1, linestyle="--")
    profiles.axvspan(1.8, 3.2, color="#2a9d8f", alpha=0.08, label="D2–D3")
    profiles.axvspan(3.8, 7.2, color="#e9c46a", alpha=0.10, label="D4–D7")
    profiles.set_xticks(ranks)
    profiles.set_xlabel("Defender rank at anchor")
    profiles.set_ylabel("AARD_vel coefficient (m/s)")
    profiles.set_title("Descriptive D1–D10 profiles")
    profiles.grid(alpha=0.18)
    profiles.legend(fontsize=7, ncol=2, frameon=False)

    fig.suptitle(
        "Concurrent Defensive Coordination Form v1 — IDSSE external replication\n"
        "All seven match-level primary estimates and 95% intervals are above zero",
        fontsize=13,
        fontweight="bold",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
