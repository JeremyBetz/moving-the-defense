"""Execute the frozen rapid-change-first Game 2 defensive review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    align_events_to_reference,
    render_reorganization_window,
)
from possession_aware_defensive_review import (
    DefensiveReviewEligibilitySpec,
    build_metrica_possession_context,
    find_defensive_review_windows,
)
from rapid_change_defensive_review import (
    RapidReviewPrioritySpec,
    find_rapid_reorganization_windows,
)
from run_full_match_application_case_study import _reference_and_game2, load_frozen_config
from run_metrica_game2_application import load_ball, load_shots, metrica_sample_preset


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "rapid_change_first_defensive_review_v1.json"
DEFAULT_OUTPUT = Path("/tmp/moving_the_defense_rapid_change_review")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rapid_config(path: Path = CONFIG) -> dict[str, object]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN_BEFORE_RAPID_CANDIDATE_INSPECTION":
        raise RuntimeError("rapid-change review configuration is not frozen")
    checks = {
        config["measurement"]["production_scorer_path"]: config["measurement"]["production_scorer_sha256"],
        config["source"]["event_path"]: config["source"]["event_sha256"],
        config["source"]["reference_config_path"]: config["source"]["reference_config_sha256"],
        config["historical_packages"]["v1_manifest_path"]: config["historical_packages"]["v1_manifest_sha256"],
        config["historical_packages"]["v2_manifest_path"]: config["historical_packages"]["v2_manifest_sha256"],
        **config["frozen_dependencies_sha256"],
    }
    for relative, expected in checks.items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"frozen rapid-review dependency hash mismatch: {relative}")
    if config["measurement"]["rapid_threshold_m"] != 0.6251746256690309:
        raise RuntimeError("frozen rapid threshold changed")
    return config


def normalize_event_context(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"Period", "Start Time [s]", "Type", "Subtype"}
    if not required.issubset(raw.columns):
        raise ValueError(f"event source lacks context columns: {sorted(required - set(raw.columns))}")
    q = raw.loc[:, ["Period", "Start Time [s]", "Type", "Subtype"]].copy()
    q.columns = ["period", "event_time_s", "event_type", "event_subtype"]
    q["period"] = pd.to_numeric(q["period"], errors="raise").astype(int)
    q["event_time_s"] = pd.to_numeric(q["event_time_s"], errors="raise")
    if not np.isfinite(q["event_time_s"].to_numpy(float)).all():
        raise ValueError("event context times must be finite")
    q["event_type"] = q["event_type"].fillna("").astype(str).str.strip().str.upper()
    q["event_subtype"] = q["event_subtype"].fillna("").astype(str).str.strip().str.upper()
    return q.sort_values(
        ["period", "event_time_s", "event_type", "event_subtype"], kind="mergesort"
    ).reset_index(drop=True)


def json_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def plot_rapid_timeline(review, rapid, events: pd.DataFrame, threshold: float, path: Path) -> Path:
    figure, axes = plt.subplots(2, 1, figsize=(12, 6), constrained_layout=True, sharey=True)
    colors = {"metrica:Home": "#2563a7", "metrica:Away": "#d17a22"}
    public_keys = {
        (str(row.team_key), int(row.period), float(row.peak_time_s))
        for row in rapid.public_examples.itertuples(index=False)
    }
    for axis, team in zip(axes, sorted(review.possession_timelines), strict=True):
        timeline = review.possession_timelines[team].copy()
        eligible = (
            timeline["defensive_review_eligible"]
            & timeline["before_defensive_eligible"]
            & timeline["possession_state_run_id"].eq(timeline["before_state_run_id"])
        )
        for period, group in timeline.groupby("period", sort=True):
            values = group["one_second_change_m"].where(eligible.loc[group.index])
            axis.plot(group.time_match_s / 60, values, color=colors[team], linewidth=.65)
        axis.axhline(threshold, color="#991b1b", linestyle="--", linewidth=1, label="Frozen P95 increase")
        team_review = rapid.review_set.loc[rapid.review_set.team_key.eq(team)]
        for row in team_review.itertuples(index=False):
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            axis.scatter(
                row.peak_time_s / 60, row.one_second_change_m,
                marker="*" if key in public_keys else "o",
                s=70 if key in public_keys else 28,
                facecolor="#111111" if key in public_keys else "white",
                edgecolor="#111111", zorder=5,
            )
        attacking = "metrica:Away" if team == "metrica:Home" else "metrica:Home"
        for event in events.loc[events.attacking_team_key.eq(attacking)].itertuples(index=False):
            axis.axvline(
                event.event_time_s / 60, color="#6b7280",
                linewidth=.4 if event.event_type == "SHOT" else 1.1,
                alpha=.25 if event.event_type == "SHOT" else .65,
            )
        axis.set_title(f"{team.split(':')[-1]} defending · eligible opponent-possession frames")
        axis.set_ylabel("One-second change (m)")
        axis.grid(alpha=.16)
    axes[0].legend(loc="upper right", fontsize=8, frameon=False)
    axes[-1].set_xlabel("Match time (minutes; provider clock)")
    figure.suptitle("Metrica Sample Game 2: rapid-change-first defensive review")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return path


def _render_row(
    row: pd.Series,
    *,
    combined: pd.DataFrame,
    scores_by_team,
    output_dir: Path,
    stem: str,
) -> dict[str, Path]:
    render_row = row.copy()
    render_row["category_memberships"] = "|".join(
        [str(row.get("moment_type", "rapid_change")).replace("_", " "),
         str(row.get("rapid_context", "context unavailable")).replace("_", " "),
         str(row.get("contribution_pattern", "")).replace("_", " ")]
    ).strip("|")
    render_row["context_classification"] = "defensive_review"
    return render_reorganization_window(
        combined, scores_by_team[str(row.team_key)], render_row,
        output_dir, stem=stem, context_seconds=5.0, render_gif=True,
    )


def execute(output_dir: Path = DEFAULT_OUTPUT, *, render_media: bool = True) -> dict[str, object]:
    config = load_rapid_config()
    case_config = load_frozen_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    reference, analysis, tracking_by_team = _reference_and_game2(case_config)
    if reference.rapid_threshold_m != config["measurement"]["rapid_threshold_m"]:
        raise RuntimeError("calculated rapid threshold differs from the freeze")
    preset = metrica_sample_preset(2)
    raw_events = pd.read_csv(preset.data_dir / preset.events_file)
    normalized_events = normalize_event_context(raw_events)
    combined_players = pd.concat(tracking_by_team.values(), ignore_index=True)
    eligibility = DefensiveReviewEligibilitySpec(
        continuous_out_of_possession_seconds=2.0, transition_radius_seconds=2.0
    )
    context = build_metrica_possession_context(
        raw_events, combined_players, match_id=preset.match_id,
        source_fps=25.0, spec=eligibility,
    )
    possession_review = find_defensive_review_windows(
        analysis.scores_by_team, reference, context,
        moment_spec=ReferenceMomentSpec(
            minimum_high_low_seconds=1.0, change_seconds=1.0,
            selection_per_category=2, render_context_seconds=5.0,
        ),
        eligibility_spec=eligibility,
        historical_selected=analysis.selected_moments,
    )
    priority_spec = RapidReviewPrioritySpec()
    rapid = find_rapid_reorganization_windows(
        possession_review, analysis.scores_by_team,
        events=normalized_events, spec=priority_spec,
    )
    if len(rapid.review_set) > 6 or rapid.review_set["rapid_context"].isin({"restart_adjacent", "ambiguous_context"}).any():
        raise RuntimeError("rapid review set violates frozen context selection")

    shots = load_shots(preset.data_dir / preset.events_file, match_id=preset.match_id)
    aligned = align_events_to_reference(
        shots, analysis, reference,
        defending_team_by_attacking_team={"metrica:Home": "metrica:Away", "metrica:Away": "metrica:Home"},
    )
    if not aligned.alignment_status.eq("matched").all():
        raise RuntimeError("event alignment changed")

    public_dir = output_dir / "public"
    review_dir = output_dir / "review_media"
    decrease_dir = output_dir / "decrease_media"
    public_dir.mkdir(parents=True, exist_ok=True)
    timeline = plot_rapid_timeline(
        possession_review, rapid, aligned, reference.rapid_threshold_m,
        public_dir / "rapid_change_timeline.png",
    )
    rapid.classified_increases.to_csv(output_dir / "classified_rapid_increases.csv", index=False)
    rapid.review_set.to_csv(output_dir / "top_six_rapid_review.csv", index=False)
    rapid.decrease_diagnostics.to_csv(output_dir / "top_three_rapid_decreases.csv", index=False)

    review_media: list[dict[str, object]] = []
    decrease_media: list[dict[str, object]] = []
    public_media: list[dict[str, object]] = []
    if render_media:
        combined = pd.concat([
            *tracking_by_team.values(),
            load_ball(preset.data_dir / preset.team_files["metrica:Home"], match_id=preset.match_id),
        ], ignore_index=True)
        public_keys = {
            (str(row.team_key), int(row.period), float(row.peak_time_s)): row
            for row in rapid.public_examples.itertuples(index=False)
        }
        for row in rapid.review_set.itertuples(index=False):
            series = pd.Series(row._asdict())
            stem = f"rapid_increase_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            paths = _render_row(
                series, combined=combined, scores_by_team=analysis.scores_by_team,
                output_dir=review_dir, stem=stem,
            )
            item = {"review_rank": int(row.review_rank), "stem": stem, **{key: str(value) for key, value in paths.items()}}
            review_media.append(item)
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            if key in public_keys:
                copied = {}
                for kind, source in paths.items():
                    destination = public_dir / Path(source).name
                    shutil.copyfile(source, destination)
                    copied[kind] = str(destination)
                public_media.append({
                    "public_rank": int(public_keys[key].public_rank),
                    "selection_reason": str(public_keys[key].public_selection_reason),
                    "stem": stem, **copied,
                })
        for index, row in rapid.decrease_diagnostics.iterrows():
            render_row = row.copy()
            render_row["moment_type"] = "rapid_decrease"
            render_row["team_score_m"] = float(row.after_score_m)
            render_row["reference_percentile"] = float(row.after_reference_percentile)
            render_row["defensive_review_eligible"] = True
            render_row["category_memberships"] = f"rapid decrease|{row.rapid_context.replace('_', ' ')}"
            stem = f"rapid_decrease_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            paths = _render_row(
                render_row, combined=combined, scores_by_team=analysis.scores_by_team,
                output_dir=decrease_dir, stem=stem,
            )
            decrease_media.append({"decrease_rank": index + 1, "stem": stem, **{key: str(value) for key, value in paths.items()}})

    governed = [timeline]
    for item in public_media:
        governed.extend(Path(item[key]) for key in ("diagnostic_png", "gif"))
    result = {
        "status": "RAPID_CHANGE_FIRST_REVIEW_COMPLETE",
        "match_id": preset.match_id,
        "question": "When did the defensive unit begin reorganizing much more strongly than one second earlier?",
        "rapid_threshold_m": reference.rapid_threshold_m,
        "restart_adjacency_seconds": 5.0,
        "top_six": json_records(rapid.review_set),
        "public_examples": json_records(rapid.public_examples),
        "rapid_decreases": json_records(rapid.decrease_diagnostics),
        "review_media": review_media,
        "public_media": public_media,
        "decrease_media": decrease_media,
        "historical_high_low_unchanged": True,
        "event_alignment_unchanged": True,
        "claim_boundary": "descriptive retrieval only; no causal, predictive, tactical, quality, danger, effectiveness, or value interpretation",
    }
    (output_dir / "rapid_review_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    manifest = {
        "artifact_id": "rapid_change_defensive_review_v1",
        "status": result["status"],
        "created": "2026-09-27",
        "case_study_match": "Metrica Sample Game 2",
        "protocol": "docs/protocols/rapid_change_first_defensive_review_v1.md",
        "question": result["question"],
        "measurement": "one-second change in team relational reorganization, raw metres",
        "rapid_threshold_m": result["rapid_threshold_m"],
        "restart_adjacency_seconds": result["restart_adjacency_seconds"],
        "top_six": result["top_six"],
        "public_examples": result["public_examples"],
        "files_sha256": {path.name: sha256(path) for path in governed},
        "historical_manifest_sha256": {
            "v1": config["historical_packages"]["v1_manifest_sha256"],
            "v2": config["historical_packages"]["v2_manifest_sha256"],
        },
        "qc": {
            "raw_scores_unchanged": True,
            "rapid_threshold_unchanged": True,
            "possession_rules_unchanged": True,
            "event_alignment_unchanged": True,
            "all_six_public": False,
            "rapid_decreases_public": False,
            "player_identities_public": False,
            "historical_v1_v2_modified": False,
        },
    }
    (public_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
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
