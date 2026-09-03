"""Generate public-facing README visuals from closed governed results only."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/figures/readme"
GREEN = "#176B55"
BLUE = "#235789"
ORANGE = "#F28E2B"
RED = "#C44536"
GREY = "#667085"
matplotlib.rcParams["svg.hashsalt"] = "moving-the-defense-readme-v1"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(fig, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / name
    fig.savefig(target, bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)
    # Matplotlib emits harmless trailing spaces inside SVG path data. Strip
    # them so repository whitespace checks remain clean and deterministic.
    target.write_text("\n".join(line.rstrip() for line in target.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


def pitch(ax):
    ax.set_facecolor("#F5FAF7")
    ax.add_patch(Rectangle((0, 0), 105, 68, fill=False, color=GREEN, lw=1.4))
    ax.plot([52.5, 52.5], [0, 68], color=GREEN, lw=1)
    ax.add_patch(Circle((52.5, 34), 9.15, fill=False, color=GREEN, lw=1))
    ax.add_patch(Rectangle((0, 13.84), 16.5, 40.32, fill=False, color=GREEN, lw=1))
    ax.add_patch(Rectangle((88.5, 13.84), 16.5, 40.32, fill=False, color=GREEN, lw=1))
    ax.add_patch(Arc((0, 34), 18.3, 18.3, theta1=-53, theta2=53, color=GREEN, lw=1))
    ax.add_patch(Arc((105, 34), 18.3, 18.3, theta1=127, theta2=233, color=GREEN, lw=1))
    ax.set(xlim=(-3, 108), ylim=(-3, 71), aspect="equal")
    ax.axis("off")


def schematic():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1))
    base = np.array([[55, 20], [58, 29], [58, 39], [55, 48]], float)
    shift = np.array([9, 2])
    attacker0, attacker1 = np.array([43, 34]), np.array([53, 30])
    for ax, depart, title in zip(axes, [False, True], ["A collective defensive shift", "Movement within the unit"]):
        pitch(ax)
        final = base + shift
        if depart:
            final[1] += np.array([-5, -6])
        for start, end in zip(base, final):
            ax.annotate("", end, start, arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
        ax.scatter(base[:, 0], base[:, 1], s=55, facecolors="white", edgecolors=BLUE, zorder=3)
        ax.scatter(final[:, 0], final[:, 1], s=65, color=BLUE, zorder=4)
        ax.annotate("", attacker1, attacker0, arrowprops=dict(arrowstyle="->", color=ORANGE, lw=2.5))
        ax.scatter(*attacker1, s=80, color=ORANGE, zorder=4)
        c0, c1 = base.mean(axis=0), final.mean(axis=0)
        ax.plot([c0[0], c1[0]], [c0[1], c1[1]], color=GREY, lw=2, ls="--")
        ax.scatter(*c1, marker="x", s=70, color=GREY, zorder=5)
        if depart:
            ax.annotate("extra movement relative\nto the defensive unit", xy=final[1], xytext=(74, 13),
                        arrowprops=dict(arrowstyle="->", color=RED), color=RED, fontsize=9, ha="center")
        ax.set_title(title, fontsize=13, weight="bold")
    fig.suptitle("Ordinary displacement mixes the unit's shift with local reorganization", fontsize=15, weight="bold")
    fig.text(.5, .01, "Synthetic illustration — not a match result", ha="center", color=GREY, fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .93))
    save(fig, "measurement_schematic.svg")


def forest():
    def metrica_row(game: int):
        table = pd.read_csv(ROOT / f"outputs/concurrent_attacker_defensive_geometry_game{game}_v1/primary_coefficients.csv")
        row = table.loc[table.estimand == "near_minus_middle"].iloc[0]
        return {"estimate": row.estimate, "ci_low": row.ci_low, "ci_high": row.ci_high}
    g1, g2 = metrica_row(1), metrica_row(2)
    idsse = load("outputs/concurrent_attacker_defensive_geometry_idsse_v1/final_results.json")
    labels = ["Metrica Game 1", "Metrica Game 2"] + list(idsse["match_results"]) + ["IDSSE pooled"]
    values = [g1, g2] + [idsse["match_results"][k]["near_minus_middle"] for k in idsse["match_results"]] + [idsse["pooled"]["near_minus_middle"]]
    est = np.array([v["estimate"] for v in values]); lo = np.array([v["ci_low"] for v in values]); hi = np.array([v["ci_high"] for v in values])
    y = np.arange(len(labels))[::-1]
    colors = [BLUE, BLUE] + [GREEN] * 7 + [ORANGE]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    ax.axvline(0, color="#98A2B3", lw=1)
    for yi, e, l, h, c in zip(y, est, lo, hi, colors):
        ax.plot([l, h], [yi, yi], color=c, lw=2)
        ax.scatter(e, yi, color=c, s=42, zorder=3)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Near-minus-middle attacker-path coefficient (m/m)")
    ax.set_title("Localized concurrent defensive geometry reproduced across matches", loc="left", weight="bold")
    ax.text(.99, -.16, "IDSSE pooled is the governed seven-match pooled result, not a nine-match meta-analysis.",
            transform=ax.transAxes, ha="right", color=GREY, fontsize=8.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#E4E7EC", lw=.8)
    fig.tight_layout()
    save(fig, "concurrent_geometry_replication.svg")


def rank_profile():
    pooled = load("outputs/concurrent_attacker_defensive_geometry_idsse_v1/final_results.json")["pooled"]
    values = pooled["D1_D10"]
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    for a, b, c, label in [(1, 3, "#DCEFE8", "near D1–D3"), (4, 7, "#E9EEF5", "middle D4–D7"), (8, 10, "#FFF0DF", "far D8–D10")]:
        ax.axvspan(a-.45, b+.45, color=c, label=label)
    ax.plot(range(1, 11), values, color=BLUE, marker="o", lw=2.2)
    ax.set(xticks=range(1, 11), xlabel="Defender proximity rank", ylabel="Attacker-path coefficient (m/m)")
    ax.set_title("IDSSE pooled rank profile is localized but non-monotonic", loc="left", weight="bold")
    ax.legend(frameon=False, ncol=3, fontsize=8.5, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E4E7EC", lw=.8)
    fig.tight_layout()
    save(fig, "idsse_pooled_rank_profile.svg")


def directional():
    g1 = load("outputs/concurrent_defensive_coordination_form_game1_v1/final_results.json")
    g2 = load("outputs/concurrent_defensive_coordination_form_game2_v1/final_results.json")
    x = np.arange(1, 11)
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    ax.axhline(0, color="#98A2B3", lw=1)
    ax.plot(x, g1["primary"]["D1_D10"], marker="o", lw=2, color=GREEN, label="Game 1 — coherent")
    ax.plot(x, g2["primary"]["D1_D10"], marker="o", lw=2, color=ORANGE, label="Game 2 — mixed")
    ax.set(xticks=x, xlabel="Defender proximity rank", ylabel="Attacker-aligned relative velocity coefficient")
    ax.set_title("Directional form: similar group contrast, different rank shape", loc="left", weight="bold")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E4E7EC", lw=.8)
    fig.text(.5, .01, "Game 1: 0.04045 [0.02366, 0.05538]   •   Game 2: 0.04587 [-0.01056, 0.09260]",
             ha="center", color=GREY, fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, 1))
    save(fig, "coordination_form_game1_game2.svg")


if __name__ == "__main__":
    schematic(); forest(); rank_profile(); directional()
