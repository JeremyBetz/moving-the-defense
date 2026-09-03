import sys
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_coverage_redistribution_v1 import (  # noqa: E402
    coverage_cost_change,
    defensive_response_contrast,
    minimum_distinct_defender_coverage,
    synthetic_fixture,
    within_anchor_demean,
)


def test_minimum_matching_requires_complete_outfield_sets():
    with pytest.raises(ValueError):
        minimum_distinct_defender_coverage(np.zeros((8, 2)), np.zeros((10, 2)))
    with pytest.raises(ValueError):
        minimum_distinct_defender_coverage(np.zeros((9, 2)), np.zeros((9, 2)))


def test_matching_cost_is_rigid_transform_invariant():
    rng = np.random.default_rng(20260905)
    attackers = rng.normal(size=(9, 2))
    defenders = rng.normal(size=(10, 2))
    angle = 0.73
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    translation = np.array([22.0, -9.0])
    original = minimum_distinct_defender_coverage(attackers, defenders).mean_distance_m
    transformed = minimum_distinct_defender_coverage(
        attackers @ rotation.T + translation, defenders @ rotation.T + translation
    ).mean_distance_m
    assert transformed == pytest.approx(original, abs=1e-12)


def test_scalar_matching_cost_is_player_order_invariant():
    rng = np.random.default_rng(20260906)
    attackers = rng.normal(size=(9, 2))
    defenders = rng.normal(size=(10, 2))
    original = minimum_distinct_defender_coverage(attackers, defenders).mean_distance_m
    permuted = minimum_distinct_defender_coverage(
        attackers[rng.permutation(9)], defenders[rng.permutation(10)]
    ).mean_distance_m
    assert permuted == pytest.approx(original, abs=1e-12)


def test_shared_translation_has_zero_coverage_change():
    rng = np.random.default_rng(11)
    attackers = rng.normal(size=(9, 2))
    defenders = rng.normal(size=(10, 2))
    shift = np.array([7.0, -3.0])
    assert coverage_cost_change(attackers, attackers + shift, defenders, defenders + shift) == pytest.approx(0.0)


def test_response_contrast_is_exact_group_difference():
    paths = np.arange(1.0, 11.0)
    assert defensive_response_contrast(paths) == pytest.approx(2.0 - 5.5)


def test_within_anchor_demeaning_preserves_focal_variation():
    values = np.array([[1.0, 2.0], [3.0, 6.0], [2.0, 5.0], [8.0, 9.0]])
    anchors = np.array([1, 1, 2, 2])
    result = within_anchor_demean(values, anchors)
    np.testing.assert_allclose(result[:2].mean(axis=0), 0.0)
    np.testing.assert_allclose(result[2:].mean(axis=0), 0.0)
    assert np.linalg.matrix_rank(result) > 0


def test_synthetic_six_column_design_remains_identified_after_demeaning():
    rng = np.random.default_rng(20260907)
    anchors = np.repeat(np.arange(20), 10)
    columns = rng.normal(size=(200, 6))
    transformed = within_anchor_demean(columns, anchors)
    assert np.linalg.matrix_rank(transformed) == 6


def test_frozen_protocol_and_configuration_hashes_match_ledger():
    ledger = json.loads((ROOT / "config" / "defensive_coverage_redistribution_v1_hashes.json").read_text())
    for relative, expected in ledger["frozen_design_sha256"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected


def test_case_1_local_tracking_with_perfect_compensation():
    case = synthetic_fixture("perfect_compensation")
    assert case["response_contrast_m"] > 1.0
    assert case["coverage_change_m"] == pytest.approx(0.0, abs=1e-12)


def test_case_2_local_tracking_without_compensation():
    case = synthetic_fixture("coverage_loss")
    assert case["response_contrast_m"] > 1.0
    assert case["coverage_change_m"] > 0.0


def test_case_3_collective_translation_is_neutral():
    case = synthetic_fixture("collective_translation")
    assert abs(case["response_contrast_m"]) < 1e-12
    assert abs(case["coverage_change_m"]) < 1e-12


def test_case_4_independent_attacker_motion_changes_coverage_without_response():
    case = synthetic_fixture("independent_other_attacker")
    assert abs(case["response_contrast_m"]) < 1e-12
    assert case["coverage_change_m"] > 0.0


def test_case_5_ignored_focal_movement_is_neutral():
    case = synthetic_fixture("focal_ignored")
    assert abs(case["response_contrast_m"]) < 1e-12
    assert abs(case["coverage_change_m"]) < 1e-12


def test_case_6_multi_defender_collapse_weakens_other_coverage():
    case = synthetic_fixture("multi_defender_collapse")
    assert case["response_contrast_m"] > 1.0
    assert case["coverage_change_m"] > synthetic_fixture("coverage_loss")["coverage_change_m"]
