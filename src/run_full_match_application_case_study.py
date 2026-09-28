"""Execute the frozen public-Metrica full-match application case study."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from defensive_reorganization_application import score_stable_runs
from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    align_events_to_reference,
    analyze_match_with_reference,
    build_pooled_reference,
    render_reorganization_window,
    summarize_event_context,
)
from run_metrica_game2_application import (
    GOALKEEPERS,
    load_ball,
    load_normalized_team,
    load_shots,
    metrica_sample_preset,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "full_match_application_case_study_v1.json"
DEFAULT_OUTPUT = Path("/tmp/moving_the_defense_full_match_case_study")
TIMELINE_Y_HEADROOM_FRACTION = 0.05
PUBLIC_GIF_CATEGORIES = frozenset({"high", "low"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_config(path: Path = CONFIG) -> dict[str, object]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN_BEFORE_EVENT_ALIGNED_EXECUTION":
        raise RuntimeError("case-study configuration is not frozen")
    if config["case_study"]["game"] != 2:
        raise RuntimeError("case-study match differs from the frozen Game 2")
    for relative, expected in config["inputs_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"frozen input hash mismatch: {relative}")
    scorer = ROOT / config["measurement"]["scorer_path"]
    if sha256(scorer) != config["measurement"]["scorer_sha256"]:
        raise RuntimeError("production scorer hash mismatch")
    return config


def _reference_and_game2(config: dict[str, object]):
    population = {}
    game2_tracking = {}
    for game in (1, 2):
        preset = metrica_sample_preset(game)
        for team_key, filename in sorted(preset.team_files.items()):
            tracking = load_normalized_team(
                preset.data_dir / filename, team_key, match_id=preset.match_id
            )
            scores = score_stable_runs(
                tracking,
                defending_team_key=team_key,
                source_fps=25,
                smoothing_frames=7,
                window_seconds=2,
                excluded_player_keys=(GOALKEEPERS[team_key],),
            )
            population[f"game{game}:{team_key}"] = scores
            if game == 2:
                game2_tracking[team_key] = tracking
    reference = build_pooled_reference(
        population,
        source_fps=25,
        metadata={
            "games": (1, 2),
            "teams": ("metrica:Home", "metrica:Away"),
            "source_hashes": dict(config["inputs_sha256"]),
        },
    )
    if reference.metadata["stable_run_count"] != config["reference_population"]["stable_run_count"]:
        raise RuntimeError("reference stable-run count differs from the frozen population")
    combined = pd.concat(game2_tracking.values(), ignore_index=True)
    analysis = analyze_match_with_reference(
        combined,
        defending_team_keys=("metrica:Home", "metrica:Away"),
        reference=reference,
        smoothing_frames=7,
        excluded_player_keys={
            team: (GOALKEEPERS[team],) for team in game2_tracking
        },
        moment_spec=ReferenceMomentSpec(
            minimum_high_low_seconds=1,
            change_seconds=1,
            selection_per_category=2,
            render_context_seconds=5,
        ),
    )
    return reference, analysis, game2_tracking


def timeline_shared_y_range(analysis) -> tuple[float, float]:
    """Return one deterministic raw-metre range for both timeline panels."""
    supported_values = np.concatenate(
        [
            scores.team_scores.loc[
                scores.team_scores.support_status.eq("supported"),
                "mean_trailing_relative_path_m",
            ].to_numpy(float)
            for scores in analysis.scores_by_team.values()
        ]
    )
    if not len(supported_values) or not np.isfinite(supported_values).all():
        raise RuntimeError("timeline requires finite supported team scores")
    return (
        0.0,
        float(supported_values.max()) * (1.0 + TIMELINE_Y_HEADROOM_FRACTION),
    )


def plot_full_match_timeline(
    analysis,
    events: pd.DataFrame,
    path: Path,
) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=False, constrained_layout=True)
    colors = {"metrica:Home": "#2563a7", "metrica:Away": "#d17a22"}
    shared_y_range = timeline_shared_y_range(analysis)
    for axis, (team, scores) in zip(axes, sorted(analysis.scores_by_team.items()), strict=True):
        q = scores.team_scores.loc[scores.team_scores.support_status.eq("supported")]
        for period, group in q.groupby("period", sort=True):
            axis.plot(group.time_match_s / 60, group.mean_trailing_relative_path_m,
                      color=colors[team], linewidth=.7, label=f"Period {period}")
        selected = analysis.selected_moments.loc[analysis.selected_moments.team_key.eq(team)]
        marker = {"high": "^", "low": "v", "rapid_increase": "D"}
        for row in selected.itertuples(index=False):
            axis.scatter(row.peak_time_s / 60, row.team_score_m, marker=marker[row.moment_type],
                         s=35, color="#111111", zorder=4)
        attacking = "metrica:Away" if team == "metrica:Home" else "metrica:Home"
        for event in events.loc[events.attacking_team_key.eq(attacking)].itertuples(index=False):
            axis.axvline(event.event_time_s / 60, color="#6b7280",
                        linewidth=.45 if event.event_type == "SHOT" else 1.2,
                        alpha=.35 if event.event_type == "SHOT" else .8)
        axis.set_title(f"{team.split(':')[-1]} defending")
        axis.set_ylabel("Mean trailing path (m)")
        axis.set_ylim(shared_y_range)
        axis.grid(alpha=.16)
    axes[0].legend(
        handles=[
            Line2D([0], [0], color="#6b7280", linewidth=.5, alpha=.5, label="Shot"),
            Line2D([0], [0], color="#6b7280", linewidth=1.5, alpha=.9, label="Goal"),
            Line2D([0], [0], marker="^", color="none", markerfacecolor="#111111",
                   markeredgecolor="#111111", label="Selected high", markersize=6),
            Line2D([0], [0], marker="v", color="none", markerfacecolor="#111111",
                   markeredgecolor="#111111", label="Selected low", markersize=6),
            Line2D([0], [0], marker="D", color="none", markerfacecolor="#111111",
                   markeredgecolor="#111111", label="Selected rapid increase", markersize=5),
        ],
        loc="upper right",
        ncol=5,
        fontsize=7,
        frameon=False,
    )
    axes[-1].set_xlabel("Match time (minutes; provider clock)")
    fig.suptitle("Metrica Sample Game 2: full-match defensive reorganization scan")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def execute(output_dir: Path = DEFAULT_OUTPUT, *, render_media: bool = True) -> dict[str, object]:
    config = load_frozen_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    reference, analysis, tracking_by_team = _reference_and_game2(config)
    preset = metrica_sample_preset(2)
    shots = load_shots(preset.data_dir / preset.events_file, match_id=preset.match_id)
    aligned = align_events_to_reference(
        shots,
        analysis,
        reference,
        defending_team_by_attacking_team={
            "metrica:Home": "metrica:Away",
            "metrica:Away": "metrica:Home",
        },
    )
    if not aligned.alignment_status.eq("matched").all():
        raise RuntimeError("Game 2 event synchronization is incomplete; case study stopped")
    event_summary = summarize_event_context(aligned)
    analysis.distributions.to_csv(output_dir / "full_match_summary.csv", index=False)
    analysis.selected_moments.to_csv(output_dir / "selected_moments.csv", index=False)
    aligned.to_csv(output_dir / "event_context.csv", index=False)
    event_summary.to_csv(output_dir / "event_group_summary.csv", index=False)
    timeline = plot_full_match_timeline(analysis, aligned, output_dir / "full_match_timeline.png")

    media: list[dict[str, object]] = []
    if render_media:
        combined = pd.concat(
            [
                *tracking_by_team.values(),
                load_ball(
                    preset.data_dir / preset.team_files["metrica:Home"],
                    match_id=preset.match_id,
                ),
            ],
            ignore_index=True,
        )
        first_by_category = {
            category: group.iloc[0].name
            for category, group in analysis.selected_moments.groupby("moment_type", sort=False)
        }
        rendered_intervals: dict[tuple[str, int, float], Path] = {}
        for index, row in analysis.selected_moments.iterrows():
            category = str(row.moment_type)
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            want_gif = (
                category in PUBLIC_GIF_CATEGORIES
                and index == first_by_category[category]
            )
            stem = f"{category}_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            if want_gif and key in rendered_intervals:
                paths = {"diagnostic_png": render_reorganization_window(
                    combined, analysis.scores_by_team[str(row.team_key)], row,
                    output_dir / "media", stem=stem, render_gif=False,
                )["diagnostic_png"], "gif": rendered_intervals[key]}
            else:
                paths = render_reorganization_window(
                    combined,
                    analysis.scores_by_team[str(row.team_key)],
                    row,
                    output_dir / "media",
                    stem=stem,
                    context_seconds=5,
                    render_gif=want_gif,
                )
                if want_gif:
                    rendered_intervals[key] = paths["gif"]
            media.append(
                {
                    "category": category,
                    "memberships": row.category_memberships,
                    "team": row.team_key,
                    "period": int(row.period),
                    "peak_time_s": float(row.peak_time_s),
                    **{name: str(path) for name, path in paths.items()},
                }
            )
    result = {
        "status": "DESCRIPTIVE_APPLICATION_COMPLETE",
        "match_id": preset.match_id,
        "reference": {
            "player_score_count": reference.metadata["player_score_count"],
            "team_score_count": reference.metadata["team_score_count"],
            "one_second_change_count": reference.metadata["one_second_change_count"],
            "stable_run_count": reference.metadata["stable_run_count"],
            "low_threshold_m": reference.low_threshold_m,
            "high_threshold_m": reference.high_threshold_m,
            "rapid_one_second_threshold_m": reference.rapid_threshold_m,
        },
        "events": {
            "shot_count": int(len(aligned)),
            "goal_count": int(aligned.event_type.eq("GOAL").sum()),
            "shot_on_target_count": int(aligned.shot_on_target.sum()),
            "matched_count": int(aligned.alignment_status.eq("matched").sum()),
        },
        "selected_moment_count": int(len(analysis.selected_moments)),
        "timeline": str(timeline),
        "media": media,
        "claim_boundary": (
            "retrospective descriptive geometry only; no causal, predictive, tactical, "
            "quality, effectiveness, or value interpretation"
        ),
    }
    (output_dir / "case_study_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-media", action="store_true")
    args = parser.parse_args()
    print(json.dumps(execute(args.output_dir, render_media=not args.no_media), indent=2))


if __name__ == "__main__":
    main()
