"""Execute the frozen possession-aware Metrica Game 2 review rescan."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    align_events_to_reference,
    render_reorganization_window,
    summarize_event_context,
)
from possession_aware_defensive_review import (
    DefensiveReviewEligibilitySpec,
    build_metrica_possession_context,
    find_defensive_review_windows,
    possession_state_summary,
)
from run_full_match_application_case_study import (
    _reference_and_game2,
    load_frozen_config,
    timeline_shared_y_range,
)
from run_metrica_game2_application import load_ball, load_shots, metrica_sample_preset


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "possession_aware_defensive_review_v1.json"
DEFAULT_OUTPUT = Path("/tmp/moving_the_defense_possession_aware_review")
PUBLIC_GIF_CATEGORIES = frozenset({"high", "low", "rapid_increase"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_possession_config(path: Path = CONFIG) -> dict[str, object]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN_BEFORE_POSSESSION_AWARE_GAME2_RESCAN":
        raise RuntimeError("possession-aware review configuration is not frozen")
    event_path = ROOT / config["source"]["event_path"]
    if sha256(event_path) != config["source"]["event_sha256"]:
        raise RuntimeError("Game 2 event source hash mismatch")
    scorer = ROOT / config["measurement"]["production_scorer_path"]
    if sha256(scorer) != config["measurement"]["production_scorer_sha256"]:
        raise RuntimeError("production scorer hash mismatch")
    if config["eligibility"]["continuous_out_of_possession_native_increments"] != 50:
        raise RuntimeError("frozen two-second eligibility buffer changed")
    return config


def plot_possession_aware_timeline(analysis, review, events: pd.DataFrame, path: Path) -> Path:
    """Plot unchanged raw timelines with possession-gated review selections."""
    figure, axes = plt.subplots(2, 1, figsize=(12, 6), constrained_layout=True)
    colors = {"metrica:Home": "#2563a7", "metrica:Away": "#d17a22"}
    marker = {"high": "^", "low": "v", "rapid_increase": "D"}
    limits = timeline_shared_y_range(analysis)
    for axis, team in zip(axes, sorted(analysis.scores_by_team), strict=True):
        timeline = review.possession_timelines[team]
        for period, group in timeline.groupby("period", sort=True):
            axis.plot(
                group.time_match_s / 60, group.mean_trailing_relative_path_m,
                color=colors[team], linewidth=.7, label=f"Period {period}",
            )
        selected = review.selected_moments.loc[review.selected_moments.team_key.eq(team)]
        for row in selected.itertuples(index=False):
            axis.scatter(
                row.peak_time_s / 60, row.team_score_m, marker=marker[row.moment_type],
                s=35, color="#111111", zorder=4,
            )
        attacking = "metrica:Away" if team == "metrica:Home" else "metrica:Home"
        for event in events.loc[events.attacking_team_key.eq(attacking)].itertuples(index=False):
            axis.axvline(
                event.event_time_s / 60, color="#6b7280",
                linewidth=.45 if event.event_type == "SHOT" else 1.2,
                alpha=.35 if event.event_type == "SHOT" else .8,
            )
        axis.set_title(f"{team.split(':')[-1]} review · opponent possession only")
        axis.set_ylabel("Team relational reorganization (m)")
        axis.set_ylim(limits)
        axis.grid(alpha=.16)
    axes[0].legend(
        handles=[
            Line2D([0], [0], color="#6b7280", linewidth=.5, alpha=.5, label="Shot"),
            Line2D([0], [0], color="#6b7280", linewidth=1.5, alpha=.9, label="Goal"),
            Line2D([0], [0], marker="^", color="none", markerfacecolor="#111111", label="Defensive high", markersize=6),
            Line2D([0], [0], marker="v", color="none", markerfacecolor="#111111", label="Defensive low", markersize=6),
            Line2D([0], [0], marker="D", color="none", markerfacecolor="#111111", label="Defensive rapid increase", markersize=5),
        ],
        loc="upper right", ncol=5, fontsize=7, frameon=False,
    )
    axes[-1].set_xlabel("Match time (minutes; provider clock)")
    figure.suptitle("Metrica Sample Game 2: possession-aware defensive review")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return path


def _json_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    clean = frame.replace({np.nan: None})
    return json.loads(clean.to_json(orient="records"))


def execute(output_dir: Path = DEFAULT_OUTPUT, *, render_media: bool = True) -> dict[str, object]:
    possession_config = load_possession_config()
    case_config = load_frozen_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    reference, analysis, tracking_by_team = _reference_and_game2(case_config)
    preset = metrica_sample_preset(2)
    combined_players = pd.concat(tracking_by_team.values(), ignore_index=True)
    raw_events = pd.read_csv(preset.data_dir / preset.events_file)
    context = build_metrica_possession_context(
        raw_events, combined_players, match_id=preset.match_id,
        source_fps=float(possession_config["source"]["source_fps"]),
        spec=DefensiveReviewEligibilitySpec(
            continuous_out_of_possession_seconds=float(possession_config["eligibility"]["continuous_out_of_possession_seconds"]),
            transition_radius_seconds=float(possession_config["eligibility"]["transition_radius_seconds"]),
        ),
    )
    review = find_defensive_review_windows(
        analysis.scores_by_team, reference, context,
        moment_spec=ReferenceMomentSpec(
            minimum_high_low_seconds=1.0, change_seconds=1.0,
            selection_per_category=2, render_context_seconds=5.0,
        ),
        historical_selected=analysis.selected_moments,
    )
    if not all(
        group.defensive_review_eligible.any()
        for _, group in context.groupby(["team_key", "period"], sort=True)
    ):
        raise RuntimeError("two-second defensive eligibility is unsupported in a team-period")

    shots = load_shots(preset.data_dir / preset.events_file, match_id=preset.match_id)
    aligned = align_events_to_reference(
        shots, analysis, reference,
        defending_team_by_attacking_team={"metrica:Home": "metrica:Away", "metrica:Away": "metrica:Home"},
    )
    if not aligned.alignment_status.eq("matched").all():
        raise RuntimeError("Game 2 event synchronization changed")
    event_summary = summarize_event_context(aligned)
    state_summary = possession_state_summary(context)
    state_summary.to_csv(output_dir / "possession_state_summary.csv", index=False)
    review.moments.to_csv(output_dir / "defensive_moments.csv", index=False)
    review.selected_moments.to_csv(output_dir / "selected_defensive_moments.csv", index=False)
    review.transition_moments.to_csv(output_dir / "transition_moments.csv", index=False)
    review.historical_selection_audit.to_csv(output_dir / "historical_selection_audit.csv", index=False)
    analysis.distributions.to_csv(output_dir / "raw_full_match_summary.csv", index=False)
    aligned.to_csv(output_dir / "event_context.csv", index=False)
    event_summary.to_csv(output_dir / "event_group_summary.csv", index=False)
    timeline = plot_possession_aware_timeline(
        analysis, review, aligned, output_dir / "possession_aware_timeline.png"
    )

    media: list[dict[str, object]] = []
    if render_media:
        combined = pd.concat([
            *tracking_by_team.values(),
            load_ball(preset.data_dir / preset.team_files["metrica:Home"], match_id=preset.match_id),
        ], ignore_index=True)
        first_by_category = {
            category: group.index[0]
            for category, group in review.selected_moments.groupby("moment_type", sort=False)
        }
        rendered_intervals: dict[tuple[str, int, float], Path] = {}
        for index, row in review.selected_moments.iterrows():
            category = str(row.moment_type)
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            want_gif = category in PUBLIC_GIF_CATEGORIES and index == first_by_category[category]
            stem = f"defensive_{category}_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            if want_gif and key in rendered_intervals:
                diagnostic = render_reorganization_window(
                    combined, analysis.scores_by_team[str(row.team_key)], row,
                    output_dir / "media", stem=stem, render_gif=False,
                )["diagnostic_png"]
                paths = {"diagnostic_png": diagnostic, "gif": rendered_intervals[key]}
            else:
                paths = render_reorganization_window(
                    combined, analysis.scores_by_team[str(row.team_key)], row,
                    output_dir / "media", stem=stem, context_seconds=5,
                    render_gif=want_gif,
                )
                if want_gif:
                    rendered_intervals[key] = paths["gif"]
            media.append({
                "category": category, "memberships": row.category_memberships,
                "team": row.team_key, "period": int(row.period),
                "peak_time_s": float(row.peak_time_s),
                "continuous_out_of_possession_s": float(row.continuous_out_of_possession_s),
                **{name: str(path) for name, path in paths.items()},
            })

    selection_counts = {
        kind: int(review.selected_moments.moment_type.eq(kind).sum())
        for kind in ("high", "low", "rapid_increase")
    }
    result = {
        "status": "POSSESSION_AWARE_DEFENSIVE_REVIEW_COMPLETE",
        "match_id": preset.match_id,
        "measurement": "team relational reorganization",
        "possession_source": "conservative Metrica event-derived context",
        "defensive_review_buffer_seconds": 2.0,
        "transition_radius_seconds": 2.0,
        "thresholds_m": {
            "high_p95": reference.high_threshold_m,
            "low_p05": reference.low_threshold_m,
            "rapid_one_second_p95": reference.rapid_threshold_m,
        },
        "selection_counts": selection_counts,
        "selected_moments": _json_records(review.selected_moments),
        "transition_episode_count": int(len(review.transition_moments)),
        "historical_selection_audit": _json_records(review.historical_selection_audit),
        "state_summary": _json_records(state_summary),
        "event_counts_unchanged": {
            "shots": int(len(aligned)), "goals": int(aligned.event_type.eq("GOAL").sum()),
            "shots_on_target": int(aligned.shot_on_target.sum()),
            "matched": int(aligned.alignment_status.eq("matched").sum()),
        },
        "timeline": str(timeline), "media": media,
        "raw_scores_unchanged": True,
        "reference_percentiles_unchanged": True,
        "event_alignment_unchanged": True,
        "claim_boundary": "event-derived review context only; no provider-ground-truth, causal, predictive, tactical, quality, effectiveness, or value interpretation",
    }
    (output_dir / "possession_aware_review_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    governed_files = [timeline]
    for item in media:
        governed_files.extend(Path(item[name]) for name in ("diagnostic_png", "gif") if name in item)
    manifest = {
        "artifact_id": "possession_aware_defensive_review_v1",
        "status": "POSSESSION_AWARE_DEFENSIVE_REVIEW_COMPLETE",
        "created": "2026-09-27",
        "case_study_match": "Metrica Sample Game 2",
        "protocol": "docs/protocols/possession_aware_defensive_review_v1.md",
        "source_event_sha256": possession_config["source"]["event_sha256"],
        "production_scorer_sha256": possession_config["measurement"]["production_scorer_sha256"],
        "measurement": "team relational reorganization in raw metres",
        "possession_source": "conservative event-derived context; not provider ground truth",
        "defensive_review_buffer_seconds": 2.0,
        "transition_radius_seconds": 2.0,
        "display_scale_m": [0.0, 6.25],
        "thresholds_m": result["thresholds_m"],
        "selection_counts": selection_counts,
        "selected_moments": result["selected_moments"],
        "historical_selection_audit": result["historical_selection_audit"],
        "transition_episode_count": result["transition_episode_count"],
        "state_summary": result["state_summary"],
        "event_counts_unchanged": result["event_counts_unchanged"],
        "files_sha256": {path.name: sha256(path) for path in governed_files},
        "qc": {
            "raw_scores_unchanged": True,
            "reference_percentiles_unchanged": True,
            "event_alignment_unchanged": True,
            "both_teams_and_periods_have_eligible_support": True,
            "historical_v1_package_modified": False,
            "native_state_rows_published": False,
            "tactical_or_causal_claim_created": False,
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
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
