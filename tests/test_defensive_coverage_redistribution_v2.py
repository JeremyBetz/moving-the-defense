import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_coverage_redistribution_v2 import (  # noqa: E402
    ball_nearest_reference_index,
    defensive_response_contrast,
    fixed_elsewhere_cost_change,
    fixed_elsewhere_coverage,
    focal_relative_path_lengths,
    full_ten_coverage,
    rank_focal_relative_paths,
    rotate_internal_defender_motion,
    v1_demeaned_complement,
)


def base_scene():
    attackers = np.array(
        [
            [0.0, 0.0],
            [10.0, -18.0], [10.0, -9.0], [10.0, 0.0],
            [10.0, 9.0], [10.0, 18.0],
            [25.0, -18.0], [25.0, -9.0], [25.0, 9.0], [25.0, 18.0],
        ],
        dtype=np.float64,
    )
    defenders = attackers + np.array([[-1.0, 0.0]])
    ball = np.array([0.2, 0.1])
    return attackers, defenders, ball


def two_frame(start, end):
    return np.stack([np.asarray(start), np.asarray(end)])


def test_rejected_v1_demeaning_is_exact_focal_complement():
    delta = np.linspace(-0.4, 1.4, 10)
    demeaned, complement = v1_demeaned_complement(delta)
    np.testing.assert_allclose(demeaned, complement, atol=1e-15)


def test_reference_is_start_defined_and_label_invariant_when_unique():
    attackers, _, ball = base_scene()
    assert ball_nearest_reference_index(attackers, ball) == 0
    permutation = np.array([4, 7, 1, 9, 0, 2, 6, 8, 5, 3])
    permuted_index = ball_nearest_reference_index(attackers[permutation], ball)
    assert int(permutation[permuted_index]) == 0


def test_reference_tie_is_rejected_without_player_id_tiebreak():
    attackers, _, _ = base_scene()
    attackers[0] = [-1.0, 0.0]
    attackers[1] = [1.0, 0.0]
    with pytest.raises(ValueError):
        ball_nearest_reference_index(attackers, np.array([0.0, 0.0]))


def test_reference_and_fixed_elsewhere_cost_are_rigid_transform_invariant():
    attackers, defenders, ball = base_scene()
    angle = 0.83
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )
    reflection = np.array([[-1.0, 0.0], [0.0, 1.0]])
    transform = rotation @ reflection
    shift = np.array([14.0, -6.0])
    transformed_attackers = attackers @ transform.T + shift
    transformed_defenders = defenders @ transform.T + shift
    transformed_ball = ball @ transform.T + shift
    assert ball_nearest_reference_index(transformed_attackers, transformed_ball) == 0
    original = fixed_elsewhere_coverage(attackers, defenders, 0).mean_distance_m
    transformed = fixed_elsewhere_coverage(
        transformed_attackers, transformed_defenders, 0
    ).mean_distance_m
    assert transformed == pytest.approx(original, abs=1e-12)


def test_complete_fixed_sets_are_required():
    attackers, defenders, _ = base_scene()
    with pytest.raises(ValueError):
        fixed_elsewhere_coverage(attackers[:9], defenders, 0)
    with pytest.raises(ValueError):
        fixed_elsewhere_coverage(attackers, defenders[:9], 0)


def test_case_1_perfect_compensation_is_neutral():
    attackers, defenders, _ = base_scene()
    end_defenders = defenders.copy()
    # Defender 1 joins the reference; the formerly spare reference defender
    # exactly replaces defender 1 for the fixed elsewhere set.
    end_defenders[1] = np.array([0.0, 0.0])
    end_defenders[0] = defenders[1]
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    assert change == pytest.approx(0.0, abs=1e-12)


def test_case_2_no_compensation_worsens_elsewhere_geometry():
    attackers, defenders, _ = base_scene()
    end_defenders = defenders.copy()
    end_defenders[1] = np.array([0.0, 0.0])
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    assert change > 0.5


def test_case_3_shared_rigid_translation_is_neutral():
    attackers, defenders, _ = base_scene()
    shift = np.array([8.0, -5.0])
    change = fixed_elsewhere_cost_change(
        attackers, attackers + shift, defenders, defenders + shift, 0
    )
    assert change == pytest.approx(0.0, abs=1e-12)
    paths = rank_focal_relative_paths(two_frame(defenders, defenders + shift), attackers[0])
    assert defensive_response_contrast(paths) == pytest.approx(0.0, abs=1e-12)


def test_defense_only_translation_changes_cost_without_local_response():
    attackers, defenders, _ = base_scene()
    shift = np.array([3.0, -2.0])
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, defenders + shift, 0
    )
    paths = rank_focal_relative_paths(two_frame(defenders, defenders + shift), attackers[0])
    assert abs(change) > 0.0
    assert defensive_response_contrast(paths) == pytest.approx(0.0, abs=1e-12)


def test_balanced_independent_defender_motion_changes_cost_without_local_response():
    attackers, defenders, _ = base_scene()
    angles = np.linspace(0.0, 2.0 * np.pi, 10, endpoint=False)
    end_defenders = defenders + np.column_stack([np.cos(angles), np.sin(angles)])
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    paths = rank_focal_relative_paths(two_frame(defenders, end_defenders), attackers[0])
    assert abs(change) > 0.0
    assert defensive_response_contrast(paths) == pytest.approx(0.0, abs=1e-12)


def test_rigid_defensive_rotation_exposes_need_for_direction_null():
    attackers, defenders, _ = base_scene()
    angle = 0.25
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )
    centroid = defenders.mean(axis=0)
    end_defenders = (defenders - centroid) @ rotation.T + centroid
    trajectory = two_frame(defenders, end_defenders)
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    contrast = defensive_response_contrast(
        rank_focal_relative_paths(trajectory, attackers[0])
    )
    nulled = rotate_internal_defender_motion(trajectory, 1.11)
    null_contrast = defensive_response_contrast(
        rank_focal_relative_paths(nulled, attackers[0])
    )
    assert abs(change) > 0.0
    assert abs(contrast) > 0.0
    assert null_contrast == pytest.approx(contrast, abs=1e-12)


def test_case_4_uniform_expansion_changes_cost_but_not_symmetric_local_contrast():
    angles = np.linspace(0.0, 2.0 * np.pi, 10, endpoint=False)
    defenders = np.column_stack([10.0 * np.cos(angles), 10.0 * np.sin(angles)])
    attackers = defenders.copy()
    attackers[0] = [0.0, 0.0]
    end_defenders = 1.2 * defenders
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    paths = rank_focal_relative_paths(two_frame(defenders, end_defenders), attackers[0])
    assert change > 0.0
    assert defensive_response_contrast(paths) == pytest.approx(0.0, abs=1e-12)


def test_case_5_independent_other_attacker_motion_changes_outcome_without_response():
    attackers, defenders, _ = base_scene()
    end_attackers = attackers.copy()
    end_attackers[9] += np.array([0.0, 8.0])
    change = fixed_elsewhere_cost_change(
        attackers, end_attackers, defenders, defenders, 0
    )
    paths = rank_focal_relative_paths(two_frame(defenders, defenders), attackers[0])
    assert change > 0.0
    assert defensive_response_contrast(paths) == pytest.approx(0.0, abs=1e-12)


def test_case_6_smooth_defender_swap_preserves_scalar_geometry():
    attackers, defenders, _ = base_scene()
    end_defenders = defenders.copy()
    end_defenders[[2, 3]] = end_defenders[[3, 2]]
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    assert change == pytest.approx(0.0, abs=1e-12)


def test_case_7_near_tie_switch_has_no_large_scalar_jump():
    attackers, defenders, _ = base_scene()
    attackers[1] = [10.0, -1.0]
    attackers[2] = [10.0, 1.0]
    defenders[1] = [9.0, -1e-8]
    defenders[2] = [9.0, 1e-8]
    end_defenders = defenders.copy()
    end_defenders[1, 1] *= -1.0
    end_defenders[2, 1] *= -1.0
    change = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    assert abs(change) < 1e-7


def test_case_8_reference_relationship_change_does_not_change_elsewhere_cost():
    attackers, defenders, _ = base_scene()
    end_defenders = defenders.copy()
    end_defenders[0] = np.array([0.0, 0.0])
    elsewhere = fixed_elsewhere_cost_change(
        attackers, attackers, defenders, end_defenders, 0
    )
    full_start = full_ten_coverage(attackers, defenders).mean_distance_m
    full_end = full_ten_coverage(attackers, end_defenders).mean_distance_m
    assert elsewhere == pytest.approx(0.0, abs=1e-12)
    assert full_end != pytest.approx(full_start, abs=1e-12)


def test_internal_direction_null_preserves_centroid_and_relative_path_lengths():
    rng = np.random.default_rng(20260909)
    start = rng.normal(size=(10, 2))
    increments = rng.normal(scale=0.25, size=(20, 10, 2))
    trajectory = np.concatenate([start[None], start[None] + np.cumsum(increments, axis=0)])
    transformed = rotate_internal_defender_motion(trajectory, 1.17)
    np.testing.assert_allclose(
        transformed.mean(axis=1), trajectory.mean(axis=1), atol=1e-12
    )
    np.testing.assert_allclose(transformed[0], trajectory[0], atol=1e-12)
    np.testing.assert_allclose(
        focal_relative_path_lengths(transformed),
        focal_relative_path_lengths(trajectory),
        atol=1e-11,
    )


def test_full_ten_matching_is_rigid_transform_and_order_invariant():
    attackers, defenders, _ = base_scene()
    angle = 0.73
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )
    shift = np.array([11.0, -4.0])
    original = full_ten_coverage(attackers, defenders).mean_distance_m
    transformed = full_ten_coverage(
        attackers @ rotation.T + shift, defenders @ rotation.T + shift
    ).mean_distance_m
    permuted = full_ten_coverage(attackers[::-1], defenders[[3, 1, 9, 0, 8, 2, 7, 4, 6, 5]]).mean_distance_m
    assert transformed == pytest.approx(original, abs=1e-12)
    assert permuted == pytest.approx(original, abs=1e-12)
