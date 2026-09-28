from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ball_alignment_reorganization_review import (
    TrajectoryIntegritySpec,
    audit_native_trajectory_integrity,
    classify_ballward,
    reference_ballward_thresholds,
    select_ball_alignment_review,
    summarize_ball_alignment_increments,
)
from defensive_reorganization_replay import (
    PLAYER_SCORE_COLUMNS,
    TEAM_SCORE_COLUMNS,
    DefensiveReorganizationScores,
    SUPPORTED,
)


def fake_scores(peak: float = 10.0) -> DefensiveReorganizationScores:
    players = pd.DataFrame([
        {
            "match_id": "m", "period": 1, "frame_id_provider": "10",
            "time_match_s": peak, "team_key": "t", "player_key": f"p{i}",
            "trailing_relative_path_m": 1.0, "support_status": SUPPORTED,
        }
        for i in range(10)
    ], columns=PLAYER_SCORE_COLUMNS)
    teams = pd.DataFrame([{
        "match_id": "m", "period": 1, "frame_id_provider": "10",
        "time_match_s": peak, "team_key": "t",
        "mean_trailing_relative_path_m": 1.0,
        "supported_defender_count": 10, "support_status": SUPPORTED,
    }], columns=TEAM_SCORE_COLUMNS)
    return DefensiveReorganizationScores(players, teams, {"source_fps": 1.0})


def tracking_fixture(*, swap: bool = False, jump: bool = False, close_crossing: bool = False) -> pd.DataFrame:
    rows = []
    for frame, time_s in enumerate(np.arange(4.0, 14.0), start=4):
        for player in range(10):
            x = float(player * 5)
            if close_crossing and player in (0, 1):
                x = (0.0 if player == 0 else .2) if time_s < 8 else (.2 if player == 0 else 0.0)
            if swap and player in (0, 1):
                x = (0.0 if player == 0 else 40.0) if time_s < 8 else (40.0 if player == 0 else 0.0)
            if jump and player == 0 and time_s >= 8:
                x += 20.0
            rows.append({
                "match_id": "m", "period": 1, "frame_id_provider": str(frame),
                "time_match_s": time_s, "entity_type": "player", "team_key": "t",
                "player_key": f"p{player}", "x_m": x, "y_m": float(player),
                "coordinate_valid": True, "pitch_length_m": 105.0, "pitch_width_m": 68.0,
            })
    return pd.DataFrame(rows)


def test_normal_sprint_and_legitimate_close_crossing_are_clean():
    spec = TrajectoryIntegritySpec(source_fps=1.0)
    normal = audit_native_trajectory_integrity(
        tracking_fixture(), fake_scores(), match_id="m", period=1,
        team_key="t", peak_time_s=10.0, spec=spec,
    )
    crossing = audit_native_trajectory_integrity(
        tracking_fixture(close_crossing=True), fake_scores(), match_id="m", period=1,
        team_key="t", peak_time_s=10.0, spec=spec,
    )
    assert normal.clean and crossing.clean
    assert crossing.identity_swap_suspicion_count == 0


def test_impossible_jump_and_swap_signature_fail_without_repair():
    spec = TrajectoryIntegritySpec(source_fps=1.0)
    jump_source = tracking_fixture(jump=True)
    swap_source = tracking_fixture(swap=True)
    original = swap_source.copy(deep=True)
    jump = audit_native_trajectory_integrity(
        jump_source, fake_scores(), match_id="m", period=1,
        team_key="t", peak_time_s=10.0, spec=spec,
    )
    swap = audit_native_trajectory_integrity(
        swap_source, fake_scores(), match_id="m", period=1,
        team_key="t", peak_time_s=10.0, spec=spec,
    )
    assert jump.impossible_speed_count >= 1 and not jump.clean
    assert swap.identity_swap_suspicion_count == 1 and not swap.clean
    assert swap.swap_pairs == (("p0", "p1"),)
    pd.testing.assert_frame_equal(swap_source, original)


@pytest.mark.parametrize(
    "delta,expected_a,expected_b",
    [
        ([1.0, 0.0], 1.0, 1.0),
        ([-1.0, 0.0], -1.0, 0.0),
        ([0.0, 1.0], 0.0, 0.0),
    ],
)
def test_exact_toward_away_and_perpendicular_alignment(delta, expected_a, expected_b):
    result = summarize_ball_alignment_increments(
        np.asarray(delta, dtype=float).reshape(1, 1, 2),
        np.zeros((1, 1, 2)),
        np.asarray([[10.0, 0.0]]),
    )
    assert result.player_alignment.iloc[0].signed_alignment == pytest.approx(expected_a)
    assert result.player_alignment.iloc[0].ballward_projection_share == pytest.approx(expected_b)


def test_mixed_zero_missing_and_path_weighted_team_alignment():
    mixed = summarize_ball_alignment_increments(
        np.asarray([[[1.0, 0.0]], [[-1.0, 0.0]]]),
        np.zeros((2, 1, 2)),
        np.asarray([[10.0, 0.0], [10.0, 0.0]]),
    )
    assert mixed.team_signed_alignment == pytest.approx(0.0)
    assert mixed.team_ballward_projection_share == pytest.approx(.5)
    weighted = summarize_ball_alignment_increments(
        np.asarray([[[3.0, 0.0], [-1.0, 0.0]]]),
        np.zeros((1, 2, 2)),
        np.asarray([[10.0, 0.0]]),
    )
    assert weighted.team_signed_alignment == pytest.approx(.5)
    assert weighted.team_ballward_projection_share == pytest.approx(.75)
    zero = summarize_ball_alignment_increments(
        np.zeros((1, 1, 2)), np.zeros((1, 1, 2)), np.asarray([[10.0, 0.0]])
    )
    assert zero.support_status == "zero_path"
    assert np.isnan(zero.player_alignment.iloc[0].signed_alignment)
    missing = summarize_ball_alignment_increments(
        np.ones((1, 1, 2)), np.zeros((1, 1, 2)), np.asarray([[np.nan, 0.0]])
    )
    assert missing.support_status == "unsupported"


def annotated_candidates() -> pd.DataFrame:
    return pd.DataFrame([
        {"one_second_change_m": 2.0, "period": 1, "peak_time_s": 10.0, "team_key": "A",
         "trajectory_integrity_status": "trajectory_integrity_failed", "ball_alignment_support_status": "supported",
         "team_ballward_projection_share": .1, "rapid_context": "open_play", "render_eligible": True},
        {"one_second_change_m": 1.9, "period": 1, "peak_time_s": 11.0, "team_key": "A",
         "trajectory_integrity_status": "trajectory_integrity_clean", "ball_alignment_support_status": "supported",
         "team_ballward_projection_share": .2, "rapid_context": "open_play", "render_eligible": True},
        {"one_second_change_m": 1.8, "period": 1, "peak_time_s": 12.0, "team_key": "B",
         "trajectory_integrity_status": "trajectory_integrity_clean", "ball_alignment_support_status": "supported",
         "team_ballward_projection_share": .8, "rapid_context": "transition", "render_eligible": True},
        {"one_second_change_m": 1.7, "period": 1, "peak_time_s": 13.0, "team_key": "B",
         "trajectory_integrity_status": "trajectory_integrity_clean", "ball_alignment_support_status": "supported",
         "team_ballward_projection_share": .5, "rapid_context": "restart_adjacent", "render_eligible": True},
    ])


def test_integrity_gate_strata_rankings_and_no_manual_substitution():
    source = annotated_candidates()
    original = source.copy(deep=True)
    overall, low, high, public = select_ball_alignment_review(source, p25=.2, p75=.8)
    assert overall.one_second_change_m.tolist() == [1.9, 1.8]
    assert low.iloc[0].peak_time_s == 11.0
    assert high.iloc[0].peak_time_s == 12.0
    assert public.public_selection_reason.tolist() == ["top_low_ballward", "top_high_ballward"]
    assert source.iloc[0].one_second_change_m == 2.0  # failed raw result remains intact
    pd.testing.assert_frame_equal(source, original)


def test_reference_quantiles_and_closed_stratum_boundaries():
    thresholds = reference_ballward_thresholds([0.0, .25, .5, .75, 1.0])
    assert thresholds == {"count": 5, "p25": .25, "p50": .5, "p75": .75}
    assert classify_ballward(.25, p25=.25, p75=.75) == "low_ballward"
    assert classify_ballward(.75, p25=.25, p75=.75) == "high_ballward"
    assert classify_ballward(.5, p25=.25, p75=.75) == "mid_ballward"


def test_frozen_production_dependencies_and_threshold_are_unchanged():
    expected = {
        "src/defensive_reorganization_replay.py": "6b5f33de5a034ae4000270e847ebcefe0164b1df1d21d4f3a7ed8adf9bd24a8a",
        "src/possession_aware_defensive_review.py": "1a2ca8e08b5c62660f2bb97a1c8f1d54caebc0707a3cdea2b16a65639d49f231",
        "src/rapid_change_defensive_review.py": "86108989513ddd0ff6411c29268503f48baa3523025c62edef355cdcdae8d08b",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
