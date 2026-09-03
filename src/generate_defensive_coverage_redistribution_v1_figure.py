"""Generate the frozen synthetic explanation for Defensive Coverage Redistribution v1."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_coverage_redistribution_v1 import (  # noqa: E402
    minimum_distinct_defender_coverage,
    synthetic_fixture,
)


def draw_pitch(ax: plt.Axes) -> None:
    ax.add_patch(Rectangle((0, 0), 105, 68, fill=False, color="#5b6470", lw=1.0))
    ax.plot([52.5, 52.5], [0, 68], color="#c8cdd3", lw=0.7)
    ax.add_patch(plt.Circle((52.5, 34), 9.15, fill=False, color="#c8cdd3", lw=0.7))
    ax.add_patch(Rectangle((0, 13.84), 16.5, 40.32, fill=False, color="#c8cdd3", lw=0.7))
    ax.add_patch(Arc((11, 34), 18.3, 18.3, theta1=310, theta2=50, color="#c8cdd3", lw=0.7))
    ax.set(xlim=(-2, 58), ylim=(0, 40), aspect="equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_state(ax: plt.Axes, case: dict, endpoint: str, title: str) -> None:
    draw_pitch(ax)
    attackers = np.asarray(case[f"attacker_{endpoint}_xy"])
    defenders = np.asarray(case[f"defender_{endpoint}_xy"])
    focal = np.asarray(case[f"focal_{endpoint}_xy"])
    match = minimum_distinct_defender_coverage(attackers, defenders)
    for ai, di in zip(match.attacker_indices, match.defender_indices, strict=True):
        ax.plot(
            [attackers[ai, 0], defenders[di, 0]],
            [attackers[ai, 1], defenders[di, 1]],
            color="#aeb6bf",
            lw=0.7,
            alpha=0.8,
            zorder=1,
        )
    ax.scatter(defenders[:, 0], defenders[:, 1], s=58, c="#2474b5", marker="s", label="Outfield defender", zorder=3)
    ax.scatter(attackers[:, 0], attackers[:, 1], s=34, c="#ed8b2c", marker="o", label="Other attacker", zorder=4)
    ax.scatter([focal[0]], [focal[1]], s=90, c="#c0392b", marker="*", label="Focal attacker", zorder=5)
    ax.set_title(title, fontsize=10, loc="left", weight="bold")
    ax.text(
        0.01,
        0.02,
        f"Mean distinct-defender distance: {match.mean_distance_m:.2f} m",
        transform=ax.transAxes,
        fontsize=8,
        color="#333333",
    )


def main() -> None:
    output = ROOT / "figures" / "defensive_coverage_redistribution_v1" / "synthetic_compensation_vs_loss.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    cases = [
        (synthetic_fixture("perfect_compensation"), "A  Defender follows; teammate compensates"),
        (synthetic_fixture("coverage_loss"), "B  Defender follows; no compensation"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.2))
    for row, (case, label) in enumerate(cases):
        draw_state(axes[row, 0], case, "start", f"{label} — start")
        draw_state(axes[row, 1], case, "end", f"{label} — end")
        focal_start = np.asarray(case["focal_start_xy"])
        focal_end = np.asarray(case["focal_end_xy"])
        axes[row, 1].annotate(
            "focal movement",
            xy=focal_end,
            xytext=focal_start,
            arrowprops={"arrowstyle": "->", "color": "#c0392b", "lw": 1.6},
            fontsize=8,
            color="#8e2d22",
        )
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=3, frameon=False, fontsize=9)
    fig.suptitle(
        "Synthetic coverage redistribution: the same local response can preserve or weaken coverage elsewhere",
        fontsize=13,
        weight="bold",
    )
    fig.text(
        0.5,
        0.012,
        "Grey links are minimum-cost geometric pairings, not inferred marking assignments. Synthetic design figure; no match outcome.",
        ha="center",
        fontsize=8.5,
        color="#4d5560",
    )
    fig.subplots_adjust(left=0.04, right=0.99, top=0.90, bottom=0.12, wspace=0.08, hspace=0.18)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
