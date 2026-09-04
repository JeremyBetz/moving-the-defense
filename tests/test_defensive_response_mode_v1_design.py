from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_response_mode_v1_design as mode  # noqa: E402


START = np.array([
    [-12.0, -18.0], [-12.0, -6.0], [-12.0, 6.0], [-12.0, 18.0],
    [0.0, -14.0], [0.0, -4.0], [0.0, 4.0], [0.0, 14.0],
    [12.0, -8.0], [12.0, 8.0],
])
ATTACKER = np.array([-16.0, -20.0])


def channels(end: np.ndarray) -> dict[str, float]:
    return mode.response_channels(np.stack([START, end]), ATTACKER)


def test_pure_translation_only_moves_collective_channel():
    result = channels(START + np.array([7.0, -3.0]))
    assert math.isclose(result["centroid_net_displacement_m"], math.hypot(7.0, 3.0))
    assert abs(result["width_reduction_m"]) < 1e-12
    assert abs(result["depth_reduction_m"]) < 1e-12
    assert abs(result["localized_internal_reorganization_m"]) < 1e-12


def test_pure_axis_compressions_change_shape_without_translation():
    center = START.mean(axis=0)
    narrowing = START.copy()
    narrowing[:, 1] = center[1] + 0.75 * (START[:, 1] - center[1])
    depth = START.copy()
    depth[:, 0] = center[0] + 0.75 * (START[:, 0] - center[0])
    width_result, depth_result = channels(narrowing), channels(depth)
    assert width_result["width_reduction_m"] > 0.0
    assert abs(width_result["centroid_net_displacement_m"]) < 1e-12
    assert depth_result["depth_reduction_m"] > 0.0
    assert abs(depth_result["centroid_net_displacement_m"]) < 1e-12


def test_local_outward_adjustment_is_localized_not_pure_translation():
    order = mode.fixed_distance_order(START, ATTACKER)
    end = START.copy()
    end[order[:2], 1] -= 4.0
    result = channels(end)
    assert result["localized_internal_reorganization_m"] > 0.0
    assert result["centroid_net_displacement_m"] < 1.0


def test_whole_side_shift_combines_translation_and_axis_shape_change():
    end = START.copy()
    end[end[:, 1] < 0.0, 1] -= 4.0
    result = channels(end)
    assert result["centroid_net_displacement_m"] > 0.0
    assert result["width_reduction_m"] < 0.0
    assert abs(result["localized_internal_reorganization_m"]) < 1e-12


def test_rotation_preserves_pairwise_shape_but_not_axis_spans_or_local_path():
    theta = np.deg2rad(20.0)
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    center = START.mean(axis=0)
    end = (START - center) @ rotation.T + center
    result = channels(end)
    assert abs(result["centroid_net_displacement_m"]) < 1e-12
    assert abs(result["mean_pairwise_distance_change_m"]) < 1e-12
    assert abs(result["width_reduction_m"]) > 0.0 or abs(result["depth_reduction_m"]) > 0.0
    assert abs(result["localized_internal_reorganization_m"]) > 0.0


def test_shear_is_not_uniquely_identified_by_three_channels():
    center = START.mean(axis=0)
    end = START.copy()
    end[:, 1] += 0.25 * (START[:, 0] - center[0])
    result = channels(end)
    assert abs(result["centroid_net_displacement_m"]) < 1e-12
    assert abs(result["mean_pairwise_distance_change_m"]) > 0.0
    assert abs(result["width_reduction_m"]) < 1e-12
    assert abs(result["depth_reduction_m"]) < 1e-12
    assert abs(result["localized_internal_reorganization_m"]) < 1e-12


def test_canonical_effect_translations_are_exact():
    result = mode.canonical_effects(beta_goalward=0.2, beta_outward=-0.1)
    assert math.isclose(result["inward_minus_outward"], 1.0)
    assert math.isclose(result["goalward_minus_outward"], 1.5)


def test_primary_classification_requires_all_support_gates():
    values = [0.2] * 7
    status, audit = mode.classify_width_hypothesis(0.2, 0.05, values, values, 0.19)
    assert status == "RESPONSE MODE WIDTH HYPOTHESIS SUPPORTED"
    assert all(audit["gates"].values())
    values[0] = -0.1
    status, _ = mode.classify_width_hypothesis(0.2, -0.01, values, [0.2] * 7, 0.19)
    assert status == "RESPONSE MODE WIDTH HYPOTHESIS MIXED"
    status, _ = mode.classify_width_hypothesis(-0.1, -0.2, [-0.1] * 7, [-0.1] * 7, -0.1)
    assert status == "RESPONSE MODE WIDTH HYPOTHESIS NOT SUPPORTED"
