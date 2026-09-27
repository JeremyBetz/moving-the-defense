from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_application import score_stable_runs
from defensive_reorganization_replay import (
    SUPPORTED,
    DefensiveReorganizationScores,
)
from full_match_application_case_study import (
    PooledScoreReference,
    ReferenceMatchAnalysis,
    ReferenceMomentSpec,
    analyze_match_with_reference,
    align_events_to_reference,
    build_pooled_reference,
    classify_shot_on_target,
    empirical_reference_percentile,
    export_application_tables,
    find_reorganization_windows,
    normalize_case_study_events,
    render_reorganization_window,
    summarize_event_context,
    _one_second_changes,
)


def score_package(
    values: list[float],
    *,
    team: str = "D",
    match: str = "m",
    fps: float = 10.0,
    start_time: float = 0.0,
) -> DefensiveReorganizationScores:
    rows, players = [], []
    for index, value in enumerate(values):
        time_s = start_time + index / fps
        frame = str(index)
        rows.append(
            {
                "match_id": match,
                "period": 1,
                "frame_id_provider": frame,
                "time_match_s": time_s,
                "team_key": team,
                "mean_trailing_relative_path_m": value,
                "supported_defender_count": 10,
                "support_status": SUPPORTED,
            }
        )
        for player in range(10):
            players.append(
                {
                    "match_id": match,
                    "period": 1,
                    "frame_id_provider": frame,
                    "time_match_s": time_s,
                    "team_key": team,
                    "player_key": f"{team}{player}",
                    "trailing_relative_path_m": value + player / 100,
                    "support_status": SUPPORTED,
                }
            )
    return DefensiveReorganizationScores(
        pd.DataFrame(players),
        pd.DataFrame(rows),
        {
            "source_fps": fps,
            "stable_runs": [
                {
                    "match_id": match,
                    "period": 1,
                    "run_index": 1,
                    "start_time_s": start_time,
                    "end_time_s": start_time + (len(values) - 1) / fps,
                    "native_frame_count": len(values),
                    "supported_frame_count": len(values),
                }
            ],
        },
    )


def normalized_tracking(frames: int = 81, fps: float = 10.0) -> pd.DataFrame:
    records = []
    for frame in range(frames):
        for player in range(10):
            records.append(
                {
                    "match_id": "m",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": frame / fps,
                    "entity_type": "player",
                    "team_key": "D",
                    "player_key": f"D{player}",
                    "x_m": float(player + .05 * frame * (player + 1)),
                    "y_m": float(player),
                    "coordinate_valid": True,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
    return pd.DataFrame(records)


def test_empirical_reference_percentile_is_right_sided_and_validates_boundaries():
    reference = np.array([0.0, 1.0, 1.0, 3.0])
    assert empirical_reference_percentile([-.1, 0, 1, 2, 3, 4], reference).tolist() == [
        0.0, .25, .75, .75, 1.0, 1.0
    ]
    with pytest.raises(ValueError, match="sorted"):
        empirical_reference_percentile([1], [1, 0])
    with pytest.raises(ValueError, match="finite"):
        empirical_reference_percentile([np.nan], reference)


def test_pooled_reference_keeps_player_team_and_one_second_distributions_separate():
    scores = score_package([float(value) for value in range(21)])
    reference = build_pooled_reference({"population": scores}, source_fps=10)
    assert len(reference.player_scores_m) == 210
    assert len(reference.team_scores_m) == 21
    assert len(reference.one_second_changes_m) == 11
    assert np.all(reference.one_second_changes_m == 10)
    assert reference.player_percentile(1.05) != reference.team_percentile(1.05)
    assert reference.metadata["stable_run_count"] == 1
    with pytest.raises(ValueError):
        reference.team_scores_m[0] = 99


def test_one_second_change_uses_exact_same_run_offset_and_never_frame_diff():
    scores = score_package([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 16], fps=10)
    changes = _one_second_changes(scores, 10)
    assert changes.one_second_change_m.iloc[:10].isna().all()
    assert changes.one_second_change_m.iloc[10] == pytest.approx(15)
    assert changes.one_second_change_m.iloc[11] == pytest.approx(15)


def test_reference_moments_cluster_require_duration_and_preserve_overlap():
    values = [1.0] * 100
    values[20:32] = [9.0] * 12
    values[60:72] = [.1] * 12
    scores = score_package(values, fps=10)
    # P95 high=8, P05 low=.2, rapid P95=.5 makes the jump into high qualify.
    reference = PooledScoreReference(
        np.linspace(0, 10, 101), np.linspace(0, 8.4, 101), np.linspace(-1, .5, 101), 10, {}
    )
    audit, selected = find_reorganization_windows(
        {"D": scores},
        reference,
        ReferenceMomentSpec(render_context_seconds=1, selection_per_category=2),
    )
    assert set(audit.moment_type) == {"high", "low", "rapid_increase"}
    assert audit.loc[audit.moment_type.eq("high"), "duration_s"].item() == pytest.approx(1.2)
    assert audit.loc[audit.moment_type.eq("low"), "duration_s"].item() == pytest.approx(1.2)
    assert selected.selected_for_case_study.all()
    high = selected.loc[selected.moment_type.eq("high")].iloc[0]
    rapid = selected.loc[selected.moment_type.eq("rapid_increase")].iloc[0]
    assert high.peak_time_s == pytest.approx(rapid.peak_time_s)
    assert high.category_memberships == "high|rapid_increase"
    assert rapid.category_memberships == "high|rapid_increase"


def test_subsecond_high_or_low_runs_do_not_become_episodes():
    values = [5.0] * 50
    values[20:25] = [10.0] * 5
    values[30:35] = [0.0] * 5
    scores = score_package(values, fps=10)
    reference = PooledScoreReference(
        np.linspace(0, 10, 101), np.linspace(0, 10, 101), np.linspace(-10, 10, 101), 10, {}
    )
    audit, _ = find_reorganization_windows(
        {"D": scores}, reference, ReferenceMomentSpec(render_context_seconds=.5)
    )
    assert not audit.moment_type.isin(["high", "low"]).any()


def test_analysis_matches_direct_scorer_and_does_not_mutate_input():
    tracking = normalized_tracking()
    original = tracking.copy(deep=True)
    direct = score_stable_runs(
        tracking,
        defending_team_key="D",
        source_fps=10,
        smoothing_frames=3,
        window_seconds=2,
    )
    reference = build_pooled_reference({"reference": direct}, source_fps=10)
    analysis = analyze_match_with_reference(
        tracking.sample(frac=1, random_state=4),
        defending_team_keys=("D",),
        reference=reference,
        smoothing_frames=3,
        moment_spec=ReferenceMomentSpec(render_context_seconds=.5),
    )
    observed = analysis.scores_by_team["D"].team_scores
    pd.testing.assert_frame_equal(observed.reset_index(drop=True), direct.team_scores.reset_index(drop=True))
    assert "reference_percentile" in analysis.team_timelines["D"]
    assert "reference_percentile" in analysis.player_timelines["D"]
    pd.testing.assert_frame_equal(tracking, original)
    assert analysis.metadata["raw_units"] == "metres"
    assert bool(analysis.metadata["reference_context_only"])


def test_export_is_explicit_and_writes_only_requested_local_formats(tmp_path: Path):
    scores = score_package([float(value) for value in range(30)])
    reference = build_pooled_reference({"reference": scores}, source_fps=10)
    analysis = analyze_match_with_reference(
        normalized_tracking(),
        defending_team_keys=("D",),
        reference=reference,
        smoothing_frames=3,
        moment_spec=ReferenceMomentSpec(render_context_seconds=.5),
    )
    written = export_application_tables(analysis, tmp_path, formats=("csv",))
    assert written
    assert all(path.suffix == ".csv" and path.exists() for path in written.values())
    with pytest.raises(ValueError, match="subset"):
        export_application_tables(analysis, tmp_path, formats=("json",))


def event_analysis_fixture() -> tuple[ReferenceMatchAnalysis, PooledScoreReference]:
    values = [float(index) for index in range(121)]
    scores = score_package(values, fps=10)
    reference = build_pooled_reference({"reference": scores}, source_fps=10)
    player, team = scores.player_scores.copy(), scores.team_scores.copy()
    player["reference_percentile"] = reference.player_percentile(
        player.trailing_relative_path_m.to_numpy(float)
    )
    team["reference_percentile"] = reference.team_percentile(
        team.mean_trailing_relative_path_m.to_numpy(float)
    )
    analysis = ReferenceMatchAnalysis(
        {"D": scores}, {"D": player}, {"D": team},
        pd.DataFrame(columns=[]), pd.DataFrame(columns=[]), pd.DataFrame(columns=[]),
        {"source_fps": 10},
    )
    return analysis, reference


def normalized_events(times: list[float], details: list[str] | None = None) -> pd.DataFrame:
    details = details or ["ON TARGET-SAVED"] * len(times)
    return pd.DataFrame(
        {
            "event_id": [f"e{index}" for index in range(len(times))],
            "match_id": ["m"] * len(times),
            "period": [1] * len(times),
            "event_time_s": times,
            "event_type": ["SHOT"] * len(times),
            "event_detail": details,
            "team_key": ["A"] * len(times),
        }
    )


def test_shot_on_target_rule_uses_only_frozen_subtype_tokens():
    assert classify_shot_on_target("ON TARGET-SAVED")
    assert classify_shot_on_target("HEAD-ON TARGET-GOAL")
    assert classify_shot_on_target("SAVED")
    assert not classify_shot_on_target("BLOCKED")
    assert not classify_shot_on_target("HEAD-OFF TARGET-OUT")
    normalized = normalize_case_study_events(
        normalized_events([1.0], ["ON TARGET-GOAL"]).assign(event_type="GOAL")
    )
    assert bool(normalized.shot_on_target.item())


def test_event_alignment_exact_nearest_tie_and_outside_tolerance():
    analysis, reference = event_analysis_fixture()
    events = normalized_events([6.0, 6.04, 6.05, 6.051])
    aligned = align_events_to_reference(
        events,
        analysis,
        reference,
        defending_team_by_attacking_team={"A": "D"},
        half_frame_tolerance_s=.0500001,
    )
    # A custom tolerance is prohibited, so repeat at the fixture's 10 Hz half-frame value.
    assert aligned.alignment_status.tolist() == ["matched"] * 4


def test_event_alignment_rejects_outside_half_frame_and_period_mismatch():
    analysis, reference = event_analysis_fixture()
    events = normalized_events([12.06])
    aligned = align_events_to_reference(
        events, analysis, reference, defending_team_by_attacking_team={"A": "D"}
    )
    assert aligned.alignment_status.tolist() == ["unmatched"]
    wrong_period = normalized_events([6.0]).assign(period=2)
    result = align_events_to_reference(
        wrong_period, analysis, reference, defending_team_by_attacking_team={"A": "D"}
    )
    assert result.alignment_status.tolist() == ["unmatched"]


def test_event_features_use_complete_preceding_windows_without_future_leakage():
    analysis, reference = event_analysis_fixture()
    aligned = align_events_to_reference(
        normalized_events([10.0]),
        analysis,
        reference,
        defending_team_by_attacking_team={"A": "D"},
    ).iloc[0]
    assert aligned.score_at_event_m == pytest.approx(100)
    assert aligned.previous_2s_mean_m == pytest.approx(np.mean(np.arange(80, 101)))
    assert aligned.previous_2s_max_m == pytest.approx(100)
    assert aligned.change_1s_m == pytest.approx(10)
    assert aligned.change_2s_m == pytest.approx(20)
    assert aligned.previous_10s_mean_m == pytest.approx(np.mean(np.arange(0, 101)))
    assert aligned.leading_player_scores_m.startswith("[")


def test_incomplete_event_windows_remain_missing_and_summary_is_descriptive():
    analysis, reference = event_analysis_fixture()
    aligned = align_events_to_reference(
        normalized_events([1.0, 10.0], ["OFF TARGET-OUT", "ON TARGET-GOAL"]).assign(
            event_type=["SHOT", "GOAL"]
        ),
        analysis,
        reference,
        defending_team_by_attacking_team={"A": "D"},
    )
    assert np.isnan(aligned.iloc[0].previous_2s_mean_m)
    summary = summarize_event_context(aligned)
    assert summary.set_index("event_group").loc["all_shots", "event_count"] == 2
    assert summary.set_index("event_group").loc["goals", "event_count"] == 1
    assert summary.set_index("event_group").loc["shots_on_target", "event_count"] == 1


def test_arbitrary_window_renderer_keeps_fixed_scale_and_static_only(tmp_path, monkeypatch):
    scores = score_package([1.0] * 121, fps=10)
    defending = normalized_tracking(frames=121)
    attacking = defending.copy()
    attacking["team_key"] = "A"
    attacking["player_key"] = attacking["player_key"].str.replace("D", "A", regex=False)
    ball = defending.loc[defending.player_key.eq("D0")].copy()
    ball["entity_type"] = "ball"
    ball["team_key"] = pd.NA
    ball["player_key"] = pd.NA
    combined = pd.concat([defending, attacking, ball], ignore_index=True)
    captured = {}

    def fake_plot(*args, **kwargs):
        captured.update(kwargs)
        return plt.figure()

    import full_match_application_case_study as module

    monkeypatch.setattr(module, "plot_defensive_reorganization_diagnostic", fake_plot)
    paths = render_reorganization_window(
        combined,
        scores,
        {
            "match_id": "m", "period": 1, "team_key": "D", "peak_time_s": 6.0,
            "moment_type": "high", "category_memberships": "high",
            "team_score_m": 1.0, "reference_percentile": .5,
        },
        tmp_path,
        stem="window",
        context_seconds=1,
        render_gif=False,
    )
    assert set(paths) == {"diagnostic_png"}
    assert paths["diagnostic_png"].exists()
    assert captured["score_vmax_m"] == pytest.approx(6.25)
    assert captured["show_focal_highlight"] is False
