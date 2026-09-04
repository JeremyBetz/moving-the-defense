import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_departure_v1_design import (  # noqa: E402
    attacking_frame,
    ball_nearest_attacker,
    classify_application_foundation,
    drd,
    family_is_stable,
    leave_one_match_out,
    localized_response,
    macro_mae,
    select_alpha,
)


def test_target_retains_near_and_middle_components():
    near, middle, response = localized_response(np.arange(1.0, 11.0))
    assert near == pytest.approx(2.0)
    assert middle == pytest.approx(5.5)
    assert response == pytest.approx(-3.5)


def test_target_requires_complete_rank_vector():
    with pytest.raises(ValueError):
        localized_response(np.arange(9.0))


def test_ball_nearest_proxy_is_threshold_free_and_tie_deterministic():
    positions = {f"A{i:02d}": (float(i), 0.0) for i in range(10)}
    positions["A00"] = (-1.0, 0.0)
    positions["A01"] = (1.0, 0.0)
    assert ball_nearest_attacker(positions, (0.0, 0.0)) == "A00"


def test_ball_nearest_proxy_requires_complete_attacking_outfield_set():
    with pytest.raises(ValueError):
        ball_nearest_attacker({"A": (0.0, 0.0)}, (0.0, 0.0))


def test_attacking_frame_preserves_distance_and_makes_goalward_positive():
    points = np.asarray([[3.0, -2.0], [1.0, 4.0]])
    transformed = attacking_frame(points, attack_sign_x=-1, focal_start_y=-2.0)
    assert np.linalg.norm(points[0] - points[1]) == pytest.approx(
        np.linalg.norm(transformed[0] - transformed[1])
    )
    movement = attacking_frame([[2.0, -2.0], [1.0, -2.0]], -1, -2.0)
    assert movement[1, 0] - movement[0, 0] > 0.0
    assert movement[0, 1] >= 0.0


def test_macro_mae_gives_matches_equal_weight():
    assert macro_mae({"large": [1.0] * 100, "small": [3.0]}) == pytest.approx(2.0)


def test_leave_one_match_out_never_splits_or_leaks_a_match():
    folds = leave_one_match_out(["M3", "M1", "M2"])
    assert [test for _, test in folds] == ["M1", "M2", "M3"]
    assert all(test not in train and len(train) == 2 for train, test in folds)


def test_alpha_tie_uses_largest_value_within_frozen_tolerance():
    scores = {0.01: 1.0, 0.1: 0.9000000, 1.0: 0.9000005, 10.0: 0.91}
    assert select_alpha(scores) == 1.0


def test_context_family_stability_requires_both_frozen_conditions():
    full = {f"M{i}": 0.98 for i in range(7)}
    ablated = {f"M{i}": 1.00 for i in range(7)}
    assert family_is_stable(full, ablated)
    only_four = {f"M{i}": (1.02 if i < 4 else 0.97) for i in range(7)}
    assert not family_is_stable(full, only_four)


def test_supported_status_requires_all_four_gates():
    e0 = {f"M{i}": 1.0 for i in range(7)}
    e1 = {f"M{i}": (0.96 if i < 6 else 1.0) for i in range(7)}
    assert classify_application_foundation(e0, e1, stable_family_count=1) == "SUPPORTED"
    assert classify_application_foundation(e0, e1, stable_family_count=0) == "MIXED"


def test_exact_ten_percent_worsening_prevents_supported_status():
    e0 = {f"M{i}": 1.0 for i in range(7)}
    e1 = {f"M{i}": 0.90 for i in range(7)}
    e1["M6"] = 1.10
    assert classify_application_foundation(e0, e1, stable_family_count=1) == "MIXED"


def test_status_tree_preserves_not_supported_and_invalid():
    e0 = {f"M{i}": 1.0 for i in range(7)}
    worse = {f"M{i}": 1.01 for i in range(7)}
    assert classify_application_foundation(e0, worse, stable_family_count=0) == "NOT SUPPORTED"
    assert classify_application_foundation(e0, e0, stable_family_count=0, valid=False) == "INVALID"


def test_drd_is_observed_minus_out_of_fold_prediction():
    np.testing.assert_allclose(drd([2.0, 1.0], [1.5, 1.25]), [0.5, -0.25])
