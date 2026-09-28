"""Execute the frozen trajectory-integrity and ball-alignment application review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ball_alignment_reorganization_review import (
    TrajectoryIntegritySpec,
    audit_native_trajectory_integrity,
    classify_ballward,
    compute_ball_alignment_at_time,
    reference_ballward_thresholds,
    select_ball_alignment_review,
)
from defensive_reorganization_application import score_stable_runs
from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    analyze_match_with_reference,
    build_pooled_reference,
    render_reorganization_window,
)
from possession_aware_defensive_review import (
    DefensiveReviewEligibilitySpec,
    build_metrica_possession_context,
    find_defensive_review_windows,
)
from rapid_change_defensive_review import find_rapid_reorganization_windows
from run_full_match_application_case_study import load_frozen_config
from run_metrica_game2_application import (
    GOALKEEPERS,
    load_ball,
    load_normalized_team,
    metrica_sample_preset,
)
from run_rapid_change_defensive_review import normalize_event_context


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "ball_alignment_reorganization_review_v1.json"
DEFAULT_OUTPUT = Path("/tmp/moving_the_defense_ball_alignment_review")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path = CONFIG) -> dict[str, object]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN_BEFORE_BALL_ALIGNMENT_OR_REPLACEMENT_CANDIDATE_INSPECTION":
        raise RuntimeError("ball-alignment review is not frozen")
    for relative, expected in config["source"]["tracking_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"tracking source hash mismatch: {relative}")
    for relative, expected in config["source"]["event_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"event source hash mismatch: {relative}")
    for relative, expected in config["frozen_dependencies_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"frozen dependency hash mismatch: {relative}")
    scorer = ROOT / "src" / "defensive_reorganization_replay.py"
    if sha256(scorer) != config["measurement"]["production_scorer_sha256"]:
        raise RuntimeError("production scorer hash mismatch")
    for package in config["historical_packages"].values():
        if not isinstance(package, dict):
            continue
        manifest = ROOT / package["manifest"]
        if sha256(manifest) != package["manifest_sha256"]:
            raise RuntimeError(f"historical manifest changed: {manifest}")
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for name, expected in payload["files_sha256"].items():
            if sha256(manifest.parent / name) != expected:
                raise RuntimeError(f"historical media changed: {manifest.parent / name}")
    return config


def _load_population():
    case_config = load_frozen_config()
    population = {}
    tracking_by_game: dict[int, dict[str, pd.DataFrame]] = {}
    ball_by_game: dict[int, pd.DataFrame] = {}
    events_by_game: dict[int, pd.DataFrame] = {}
    for game in (1, 2):
        preset = metrica_sample_preset(game)
        tracking_by_game[game] = {}
        for team_key, filename in sorted(preset.team_files.items()):
            tracking = load_normalized_team(
                preset.data_dir / filename, team_key, match_id=preset.match_id
            )
            tracking_by_game[game][team_key] = tracking
            population[f"game{game}:{team_key}"] = score_stable_runs(
                tracking,
                defending_team_key=team_key,
                source_fps=25.0,
                smoothing_frames=7,
                window_seconds=2.0,
                excluded_player_keys=(GOALKEEPERS[team_key],),
            )
        ball_by_game[game] = load_ball(
            preset.data_dir / preset.team_files["metrica:Home"], match_id=preset.match_id
        )
        events_by_game[game] = pd.read_csv(preset.data_dir / preset.events_file)
    reference = build_pooled_reference(
        population,
        source_fps=25.0,
        metadata={"games": (1, 2), "stable_run_count": 18},
    )
    if reference.metadata["stable_run_count"] != case_config["reference_population"]["stable_run_count"]:
        raise RuntimeError("stable-run population changed")
    return reference, tracking_by_game, ball_by_game, events_by_game


def _game_review(game, reference, tracking_by_team, raw_events):
    preset = metrica_sample_preset(game)
    combined = pd.concat(tracking_by_team.values(), ignore_index=True)
    analysis = analyze_match_with_reference(
        combined,
        defending_team_keys=("metrica:Home", "metrica:Away"),
        reference=reference,
        smoothing_frames=7,
        excluded_player_keys={team: (GOALKEEPERS[team],) for team in tracking_by_team},
        moment_spec=ReferenceMomentSpec(
            minimum_high_low_seconds=1.0,
            change_seconds=1.0,
            selection_per_category=2,
            render_context_seconds=5.0,
        ),
    )
    eligibility = DefensiveReviewEligibilitySpec(
        continuous_out_of_possession_seconds=2.0, transition_radius_seconds=2.0
    )
    context = build_metrica_possession_context(
        raw_events,
        combined,
        match_id=preset.match_id,
        source_fps=25.0,
        spec=eligibility,
    )
    possession = find_defensive_review_windows(
        analysis.scores_by_team,
        reference,
        context,
        moment_spec=ReferenceMomentSpec(
            minimum_high_low_seconds=1.0,
            change_seconds=1.0,
            selection_per_category=2,
            render_context_seconds=5.0,
        ),
        eligibility_spec=eligibility,
        historical_selected=analysis.selected_moments,
    )
    rapid = find_rapid_reorganization_windows(
        possession,
        analysis.scores_by_team,
        events=normalize_event_context(raw_events),
    )
    return analysis, possession, rapid


def _alignment_row(
    row: pd.Series,
    *,
    tracking_by_team,
    ball,
    scores_by_team,
    integrity: bool,
    spec: TrajectoryIntegritySpec,
) -> dict[str, object]:
    team = str(row.team_key)
    match_id = str(row.match_id)
    period = int(row.period)
    peak = float(row.peak_time_s)
    alignment = compute_ball_alignment_at_time(
        tracking_by_team[team], ball, scores_by_team[team],
        match_id=match_id, period=period, team_key=team, time_s=peak, spec=spec,
    )
    audit = (
        audit_native_trajectory_integrity(
            tracking_by_team[team], scores_by_team[team], match_id=match_id,
            period=period, team_key=team, peak_time_s=peak, spec=spec,
        )
        if integrity
        else None
    )
    if alignment.player_alignment.empty:
        top_paths: tuple[float, ...] = ()
        top_shares: tuple[float, ...] = ()
    else:
        paths = np.sort(alignment.player_alignment.raw_path_m.to_numpy(float))[::-1]
        top_paths = tuple(round(float(value), 10) for value in paths[:3])
        top_shares = tuple(round(float(value / paths.sum()), 10) for value in paths[:3])
    return {
        **row.to_dict(),
        "trajectory_integrity_status": (
            "not_evaluated_for_reference" if audit is None else audit.status
        ),
        "impossible_speed_count": 0 if audit is None else audit.impossible_speed_count,
        "identity_swap_suspicion_count": 0 if audit is None else audit.identity_swap_suspicion_count,
        "missing_duplicate_invalid_count": 0 if audit is None else audit.missing_duplicate_invalid_count,
        "maximum_native_speed_mps": np.nan if audit is None else audit.maximum_native_speed_mps,
        "ball_alignment_support_status": alignment.support_status,
        "team_ballward_projection_share": alignment.team_ballward_projection_share,
        "team_signed_ball_alignment": alignment.team_signed_alignment,
        "team_raw_path_sum_m": alignment.team_raw_path_sum_m,
        "top_three_player_raw_paths_m": top_paths,
        "top_three_player_raw_path_shares": top_shares,
    }


def _public_record(row: pd.Series) -> dict[str, object]:
    allowed = (
        "period", "team_key", "peak_time_s", "one_second_change_m", "before_score_m",
        "after_score_m", "team_score_m", "reference_percentile",
        "continuous_out_of_possession_s", "rapid_context", "trajectory_integrity_status",
        "impossible_speed_count", "identity_swap_suspicion_count",
        "team_ballward_projection_share", "team_signed_ball_alignment",
        "ballward_stratum", "top_three_player_raw_paths_m",
        "top_three_player_raw_path_shares", "contribution_pattern",
        "public_selection_reason", "public_rank", "overall_rank", "stratum_rank",
    )
    record = {}
    for key in allowed:
        if key in row.index:
            value = row[key]
            if isinstance(value, tuple):
                value = list(value)
            if isinstance(value, (np.integer, np.floating)):
                value = value.item()
            if isinstance(value, float) and not np.isfinite(value):
                value = None
            record[key] = value
    return record


def _plot_comparison(candidates: pd.DataFrame, p25: float, p75: float, path: Path) -> Path:
    fig, axis = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    clean = candidates.loc[
        candidates.trajectory_integrity_status.eq("trajectory_integrity_clean")
        & candidates.ball_alignment_support_status.eq("supported")
    ]
    failed = candidates.loc[candidates.trajectory_integrity_status.ne("trajectory_integrity_clean")]
    axis.scatter(
        clean.team_ballward_projection_share,
        clean.one_second_change_m,
        c=np.where(clean.team_key.eq("metrica:Home"), "#2563a7", "#d17a22"),
        s=24, alpha=.72, label="Integrity-clean rapid episode",
    )
    if not failed.empty:
        axis.scatter(
            failed.team_ballward_projection_share, failed.one_second_change_m,
            marker="x", color="#991b1b", s=42, label="Trajectory-integrity failed",
        )
    axis.axvline(p25, color="#4b5563", linestyle="--", linewidth=1, label="Reference P25/P75")
    axis.axvline(p75, color="#4b5563", linestyle="--", linewidth=1)
    axis.set_xlabel("Team ballward projection share")
    axis.set_ylabel("One-second increase in raw team reorganization (m)")
    axis.set_title("Game 2 rapid reorganization: trajectory integrity and ball alignment")
    axis.grid(alpha=.18)
    axis.legend(frameon=False, fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def _render_row(row, combined, scores_by_team, destination, stem, *, gif=True):
    render = row.copy()
    render["category_memberships"] = (
        f"{str(row.ballward_stratum).replace('_', ' ')} rapid"
        f"|ballward share {float(row.team_ballward_projection_share):.2f}"
        f"|signed alignment {float(row.team_signed_ball_alignment):+.2f}"
        "|integrity clean"
    )
    render["context_classification"] = "defensive_review"
    render["team_score_m"] = float(row.get("after_score_m", row.team_score_m))
    return render_reorganization_window(
        combined, scores_by_team[str(row.team_key)], render, destination,
        stem=stem, context_seconds=5.0, render_gif=gif,
    )


def execute(output_dir: Path = DEFAULT_OUTPUT, *, render_media: bool = True) -> dict[str, object]:
    config = load_config()
    spec = TrajectoryIntegritySpec()
    reference, tracking_by_game, ball_by_game, events_by_game = _load_population()
    analyses, possessions, rapids = {}, {}, {}
    reference_rows = []
    for game in (1, 2):
        analysis, possession, rapid = _game_review(
            game, reference, tracking_by_game[game], events_by_game[game]
        )
        analyses[game], possessions[game], rapids[game] = analysis, possession, rapid
        rapid_moments = possession.moments.loc[
            possession.moments.moment_type.eq("rapid_increase")
        ].reset_index(drop=True)
        for _, row in rapid_moments.iterrows():
            reference_rows.append(_alignment_row(
                row, tracking_by_team=tracking_by_game[game], ball=ball_by_game[game],
                scores_by_team=analysis.scores_by_team, integrity=False, spec=spec,
            ))
    reference_frame = pd.DataFrame(reference_rows)
    supported_reference = reference_frame.loc[
        reference_frame.ball_alignment_support_status.eq("supported")
    ]
    b_thresholds = reference_ballward_thresholds(
        supported_reference.team_ballward_projection_share.to_numpy(float)
    )
    signed_values = supported_reference.team_signed_ball_alignment.to_numpy(float)
    reference_summary = {
        "eligible_rapid_episode_count": int(len(reference_frame)),
        "supported_alignment_count": int(len(supported_reference)),
        "ballward_share": {
            **b_thresholds,
            "minimum": float(supported_reference.team_ballward_projection_share.min()),
            "maximum": float(supported_reference.team_ballward_projection_share.max()),
        },
        "signed_alignment": {
            "p25": float(np.quantile(signed_values, .25, method="linear")),
            "p50": float(np.quantile(signed_values, .50, method="linear")),
            "p75": float(np.quantile(signed_values, .75, method="linear")),
            "minimum": float(signed_values.min()),
            "maximum": float(signed_values.max()),
        },
    }

    game2_rows = []
    for _, row in rapids[2].classified_increases.iterrows():
        game2_rows.append(_alignment_row(
            row, tracking_by_team=tracking_by_game[2], ball=ball_by_game[2],
            scores_by_team=analyses[2].scores_by_team, integrity=True, spec=spec,
        ))
    annotated = pd.DataFrame(game2_rows)
    annotated["ballward_stratum"] = [
        classify_ballward(float(value), p25=b_thresholds["p25"], p75=b_thresholds["p75"])
        if np.isfinite(float(value)) else "unsupported"
        for value in annotated.team_ballward_projection_share
    ]
    overall, low, high, public = select_ball_alignment_review(
        annotated, p25=b_thresholds["p25"], p75=b_thresholds["p75"]
    )

    v3 = json.loads((ROOT / config["historical_packages"]["v3"]["manifest"]).read_text(encoding="utf-8"))
    old_rows = []
    for old in v3["top_six"]:
        q = annotated.loc[
            annotated.team_key.eq(old["team_key"])
            & annotated.period.eq(old["period"])
            & np.isclose(annotated.peak_time_s, old["peak_time_s"], atol=1e-7, rtol=0)
        ]
        if len(q) != 1:
            raise RuntimeError("historical rapid episode did not reconcile")
        record = q.iloc[0].copy()
        record["historical_review_rank"] = old["review_rank"]
        old_rows.append(record)
    historical = pd.DataFrame(old_rows).sort_values("historical_review_rank", kind="mergesort")

    output_dir.mkdir(parents=True, exist_ok=True)
    local_dir, public_dir = output_dir / "review_media", output_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    comparison = _plot_comparison(
        annotated, b_thresholds["p25"], b_thresholds["p75"],
        public_dir / "ball_alignment_comparison.png",
    )
    combined = pd.concat([
        *tracking_by_game[2].values(), ball_by_game[2]
    ], ignore_index=True)
    local_render_keys = []
    for frame in (overall.head(3), low.head(2), high.head(2)):
        for _, row in frame.iterrows():
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            if key in local_render_keys:
                continue
            local_render_keys.append(key)
            stem = f"review_{str(row.ballward_stratum)}_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            if render_media:
                _render_row(row, combined, analyses[2].scores_by_team, local_dir, stem)

    public_media = []
    contrast = public.loc[public.public_selection_reason.isin(["top_low_ballward", "top_high_ballward"])].copy()
    for _, row in contrast.iterrows():
        stem = f"{str(row.ballward_stratum)}_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
        if render_media:
            paths = _render_row(row, combined, analyses[2].scores_by_team, local_dir, stem)
            copied = {}
            for kind, source in paths.items():
                destination = public_dir / Path(source).name
                shutil.copyfile(source, destination)
                copied[kind] = destination
            public_media.append((row, copied))

    governed = [comparison]
    for _, paths in public_media:
        governed.extend(paths.values())
    manifest = {
        "artifact_id": "ball_alignment_reorganization_review_v1",
        "status": "BALL_ALIGNMENT_REVIEW_COMPLETE",
        "created": "2026-09-28",
        "protocol": "docs/protocols/ball_alignment_reorganization_review_v1.md",
        "question": "When rapid relational reorganization begins, how strongly is it directed toward the ball?",
        "rapid_threshold_m": config["measurement"]["rapid_threshold_m"],
        "trajectory_maximum_speed_mps": config["trajectory_integrity"]["maximum_plausible_native_speed_mps"],
        "reference_summary": reference_summary,
        "historical_six_audit": [_public_record(row) | {"historical_review_rank": int(row.historical_review_rank)} for _, row in historical.iterrows()],
        "top_overall": [_public_record(row) for _, row in overall.head(6).iterrows()],
        "top_low_ballward": [_public_record(row) for _, row in low.head(6).iterrows()],
        "top_high_ballward": [_public_record(row) for _, row in high.head(6).iterrows()],
        "selected_public_contrast": [_public_record(row) for _, row in contrast.iterrows()],
        "files_sha256": {path.name: sha256(path) for path in sorted(governed)},
        "historical_manifest_sha256": {
            label: package["manifest_sha256"]
            for label, package in config["historical_packages"].items()
            if isinstance(package, dict)
        },
        "qc": {
            "raw_scores_unchanged": True,
            "rapid_threshold_unchanged": True,
            "possession_rules_unchanged": True,
            "historical_packages_unchanged": True,
            "identity_repair": False,
            "player_identities_public": False,
            "raw_rows_or_coordinates_public": False,
        },
        "claim_boundary": "descriptive retrieval context only; no causal, predictive, tactical, quality, effectiveness, or value interpretation",
    }
    manifest_path = public_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    local = {
        "reference_summary": reference_summary,
        "historical_six_audit": historical.replace({np.nan: None}).to_dict(orient="records"),
        "public_examples": public.replace({np.nan: None}).to_dict(orient="records"),
        "manifest": str(manifest_path),
    }
    (output_dir / "review_summary.json").write_text(
        json.dumps(local, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return local


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-media", action="store_true")
    args = parser.parse_args()
    result = execute(args.output_dir, render_media=not args.no_media)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
