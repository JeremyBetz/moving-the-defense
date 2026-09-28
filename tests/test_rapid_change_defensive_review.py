from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_replay import (
    PLAYER_SCORE_COLUMNS,
    TEAM_SCORE_COLUMNS,
    SUPPORTED,
    DefensiveReorganizationScores,
)
from possession_aware_defensive_review import (
    CONTEXT_MOMENT_COLUMNS,
    POSSESSION_CONTEXT_COLUMNS,
    PossessionAwareReviewResult,
)
from rapid_change_defensive_review import (
    RapidReviewPrioritySpec,
    find_rapid_reorganization_windows,
)


LOCALIZED = np.array([7, 1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=float)
BROAD = np.ones(10, dtype=float)
MIXED = np.array([1.6, 1.6, 1.5, 1.5, .9, .9, .8, .7, .5, 0], dtype=float)


def fixture(
    patterns: list[np.ndarray],
    *,
    peaks: list[int] | None = None,
    transition_index: int | None = None,
    dead_frames: tuple[int, ...] = (),
) -> tuple[PossessionAwareReviewResult, dict[str, DefensiveReorganizationScores]]:
    peaks = peaks or [10 + index * 5 for index in range(len(patterns))]
    frame_count = max(51, max(peaks) + 7)
    team = "metrica:Home"
    player_rows, team_rows = [], []
    values = np.ones((frame_count, 10), dtype=float)
    for peak, pattern in zip(peaks, patterns, strict=True):
        values[peak] = values[peak - 1] + pattern
    for frame in range(frame_count):
        common = {
            "match_id": "m", "period": 1, "frame_id_provider": frame,
            "time_match_s": float(frame), "team_key": team,
            "support_status": SUPPORTED,
        }
        team_rows.append({
            **common, "mean_trailing_relative_path_m": float(values[frame].mean()),
            "supported_defender_count": 10,
        })
        for player in range(10):
            player_rows.append({
                **common, "player_key": f"p{player}",
                "trailing_relative_path_m": float(values[frame, player]),
            })
    scores = DefensiveReorganizationScores(
        pd.DataFrame(player_rows, columns=PLAYER_SCORE_COLUMNS),
        pd.DataFrame(team_rows, columns=TEAM_SCORE_COLUMNS),
        {"source_fps": 1.0, "stable_runs": [{
            "match_id": "m", "period": 1, "run_index": 1,
            "start_time_s": 0.0, "end_time_s": float(frame_count - 1),
            "native_frame_count": frame_count, "supported_frame_count": frame_count,
        }]},
    )
    context_rows = []
    state_run = 1
    previous_dead = False
    for frame in range(frame_count):
        dead = frame in dead_frames
        if dead != previous_dead:
            state_run += 1
        previous_dead = dead
        context_rows.append({
            "match_id": "m", "period": 1, "frame_id_provider": frame,
            "time_match_s": float(frame), "team_key": team,
            "possession_team_key": None if dead else "metrica:Away",
            "possession_state": "dead_ball_or_restart" if dead else "out_of_possession",
            "state_start_time_s": 0.0, "continuous_state_seconds": float(frame),
            "possession_state_run_id": f"state{state_run}",
            "defensive_review_eligible": not dead,
            "nearest_possession_change_offset_s": np.nan,
            "restart_event": dead,
        })
    timeline = pd.DataFrame(context_rows, columns=POSSESSION_CONTEXT_COLUMNS)
    timeline["run_id"] = "m::p1::run1"
    timeline["mean_trailing_relative_path_m"] = values.mean(axis=1)
    timeline["reference_percentile"] = .5
    timeline["before_score_m"] = timeline["mean_trailing_relative_path_m"].shift(1)
    timeline["one_second_change_m"] = timeline["mean_trailing_relative_path_m"].diff()
    timeline["before_reference_percentile"] = .4
    timeline["before_defensive_eligible"] = timeline["defensive_review_eligible"].shift(1, fill_value=False)
    timeline["before_state_run_id"] = timeline["possession_state_run_id"].shift(1)
    moment_rows = []
    for index, (peak, pattern) in enumerate(zip(peaks, patterns, strict=True)):
        delta = float(pattern.mean())
        transition_offset = 1.0 if transition_index == index else 20.0
        moment_rows.append({
            "moment_type": "rapid_increase", "match_id": "m", "period": 1,
            "team_key": team, "run_id": "m::p1::run1",
            "start_time_s": float(peak), "end_time_s": float(peak),
            "peak_time_s": float(peak), "duration_s": 1.0,
            "team_score_m": float(values[peak].mean()), "reference_percentile": .8,
            "before_score_m": float(values[peak - 1].mean()),
            "one_second_change_m": delta, "before_reference_percentile": .4,
            "leading_player_scores_m": "[]", "render_eligible": True,
            "selected_for_case_study": False, "category_memberships": "rapid_increase",
            "possession_state": "out_of_possession", "possession_team_key": "metrica:Away",
            "continuous_out_of_possession_s": float(peak),
            "defensive_review_eligible": True,
            "nearest_possession_change_offset_s": transition_offset,
            "context_classification": "defensive_review",
        })
    moments = pd.DataFrame(moment_rows, columns=CONTEXT_MOMENT_COLUMNS)
    review = PossessionAwareReviewResult(
        {team: timeline}, moments, moments.head(0), moments.head(0), pd.DataFrame(),
        {"raw_measurement": "team_relational_reorganization", "source_fps": 1.0,
         "continuous_out_of_possession_seconds": 2.0},
    )
    return review, {team: scores}


def test_top_six_ranking_patterns_and_public_diversity_are_deterministic():
    patterns = [
        LOCALIZED * 1.5, LOCALIZED * 1.4, BROAD * 1.3,
        MIXED * 1.2, BROAD * 1.1, LOCALIZED, MIXED * .9,
    ]
    review, scores = fixture(patterns, transition_index=3)
    original_moments = review.moments.copy(deep=True)
    result = find_rapid_reorganization_windows(review, scores)
    assert result.review_set.review_rank.tolist() == [1, 2, 3, 4, 5, 6]
    assert result.review_set.one_second_change_m.is_monotonic_decreasing
    assert result.review_set.contribution_pattern.tolist()[:4] == [
        "localized", "localized", "broad_unit", "mixed"
    ]
    assert result.public_examples.review_rank.tolist() == [1, 3, 4]
    assert result.public_examples.public_selection_reason.tolist() == [
        "rank_1", "first_new_context_or_contribution_pattern",
        "first_both_context_and_contribution_pattern_new",
    ]
    pd.testing.assert_frame_equal(review.moments, original_moments)
    assert result.metadata["rapid_threshold_m"] == 0.6251746256690309
    assert result.metadata["raw_scores_unchanged"] is True
    assert result.metadata["high_low_unchanged"] is True


def test_restart_adjacency_is_closed_at_exactly_five_seconds():
    review, scores = fixture([LOCALIZED], peaks=[11], dead_frames=(4, 5))
    result = find_rapid_reorganization_windows(review, scores)
    row = result.classified_increases.iloc[0]
    assert row.nearest_restart_boundary_offset_s == pytest.approx(5.0)
    assert row.rapid_context == "restart_adjacent"
    assert result.review_set.empty


def test_transition_is_allowed_and_event_ties_choose_earlier():
    review, scores = fixture([BROAD], transition_index=0)
    events = pd.DataFrame([
        {"period": 1, "event_time_s": 9.0, "event_type": "PASS", "event_subtype": "A"},
        {"period": 1, "event_time_s": 11.0, "event_type": "RECOVERY", "event_subtype": "B"},
    ])
    result = find_rapid_reorganization_windows(review, scores, events=events)
    row = result.review_set.iloc[0]
    assert row.rapid_context == "transition"
    assert row.nearest_event_type == "PASS"
    assert row.nearest_event_offset_s == pytest.approx(1.0)


def test_localized_boundary_is_inclusive_and_both_endpoints_are_rechecked():
    exact_sixty = np.array([2, 2, 2, 1, 1, 1, 1, 0, 0, 0], dtype=float)
    review, scores = fixture([exact_sixty])
    result = find_rapid_reorganization_windows(review, scores)
    assert result.review_set.iloc[0].top_three_positive_share == pytest.approx(.60)
    assert result.review_set.iloc[0].contribution_pattern == "localized"

    timeline = review.possession_timelines["metrica:Home"].copy()
    timeline.loc[timeline.time_match_s.eq(10), "before_defensive_eligible"] = False
    invalid = PossessionAwareReviewResult(
        {"metrica:Home": timeline}, review.moments, review.selected_moments,
        review.transition_moments, review.historical_selection_audit, review.metadata,
    )
    failed_closed = find_rapid_reorganization_windows(invalid, scores)
    assert failed_closed.classified_increases.iloc[0].rapid_context == "ambiguous_context"
    assert failed_closed.review_set.empty


def test_decreases_are_secondary_ranked_and_not_public():
    review, scores = fixture([LOCALIZED], peaks=[40])
    timeline = review.possession_timelines["metrica:Home"].copy()
    timeline.loc[timeline.time_match_s.eq(12), "one_second_change_m"] = -1.0
    timeline.loc[timeline.time_match_s.eq(22), "one_second_change_m"] = -2.0
    timeline.loc[timeline.time_match_s.eq(32), "one_second_change_m"] = -1.5
    amended = PossessionAwareReviewResult(
        {"metrica:Home": timeline}, review.moments, review.selected_moments,
        review.transition_moments, review.historical_selection_audit, review.metadata,
    )
    result = find_rapid_reorganization_windows(amended, scores)
    assert result.decrease_diagnostics.one_second_change_m.tolist() == [-2.0, -1.5, -1.0]
    assert "public_selection_reason" not in result.decrease_diagnostics.columns


def test_spec_rejects_post_freeze_limit_or_contribution_changes():
    with pytest.raises(ValueError, match="limits differ"):
        RapidReviewPrioritySpec(review_limit=5)
    with pytest.raises(ValueError, match="contributor count differs"):
        RapidReviewPrioritySpec(broad_minimum_at_or_above_team_delta=4)


def test_input_order_and_score_packages_are_unchanged():
    review, scores = fixture([LOCALIZED * 1.2, BROAD, MIXED * .8])
    original_players = scores["metrica:Home"].player_scores.copy(deep=True)
    first = find_rapid_reorganization_windows(review, scores)
    shuffled_review = PossessionAwareReviewResult(
        review.possession_timelines,
        review.moments.sample(frac=1, random_state=9),
        review.selected_moments,
        review.transition_moments,
        review.historical_selection_audit,
        review.metadata,
    )
    second = find_rapid_reorganization_windows(shuffled_review, scores)
    pd.testing.assert_frame_equal(first.review_set, second.review_set)
    pd.testing.assert_frame_equal(first.public_examples, second.public_examples)
    pd.testing.assert_frame_equal(scores["metrica:Home"].player_scores, original_players)
