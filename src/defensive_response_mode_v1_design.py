"""Outcome-free geometry and decision rules for Defensive Response Mode v1.

This module contains synthetic geometry only. It does not load IDSSE,
SkillCorner, Metrica, DRD, or empirical response outcomes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np


NEAR = (0, 1, 2)
MIDDLE = (3, 4, 5, 6)


def _points(value: Sequence[Sequence[float]], *, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (10, 2) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite 10 by 2 defender coordinates")
    return array


def fixed_distance_order(start: Sequence[Sequence[float]], attacker: Sequence[float]) -> np.ndarray:
    """Return start-fixed D1--D10 indices using index as the synthetic tie key."""
    defenders = _points(start, name="start")
    focal = np.asarray(attacker, dtype=np.float64)
    if focal.shape != (2,) or not np.isfinite(focal).all():
        raise ValueError("attacker must be a finite x/y point")
    distance = np.linalg.norm(defenders - focal, axis=1)
    return np.lexsort((np.arange(10), distance))


def leave_one_out_relative(track: Sequence[Sequence[Sequence[float]]]) -> np.ndarray:
    """Return each defender relative to the other nine at every time point."""
    array = np.asarray(track, dtype=np.float64)
    if array.ndim != 3 or array.shape[1:] != (10, 2) or not np.isfinite(array).all():
        raise ValueError("track must have shape time by 10 by 2 with finite values")
    total = array.sum(axis=1, keepdims=True)
    return array - (total - array) / 9.0


def localized_relative_path(track: Sequence[Sequence[Sequence[float]]], order: Sequence[int]) -> float:
    """Compute the frozen mean D1--D3 minus mean D4--D7 relative path."""
    relative = leave_one_out_relative(track)
    path = np.linalg.norm(np.diff(relative, axis=0), axis=2).sum(axis=0)
    ranks = np.asarray(order, dtype=int)
    if ranks.shape != (10,) or sorted(ranks.tolist()) != list(range(10)):
        raise ValueError("order must be a permutation of ten defender indices")
    return float(path[ranks[list(NEAR)]].mean() - path[ranks[list(MIDDLE)]].mean())


def mean_pairwise_distance(points: Sequence[Sequence[float]]) -> float:
    defenders = _points(points, name="points")
    distance = np.linalg.norm(defenders[:, None, :] - defenders[None, :, :], axis=2)
    return float(distance[np.triu_indices(10, 1)].mean())


def response_channels(
    track: Sequence[Sequence[Sequence[float]]],
    attacker: Sequence[float],
) -> dict[str, float]:
    """Describe separate translation, pitch-axis shape, and localized channels."""
    array = np.asarray(track, dtype=np.float64)
    if array.ndim != 3 or array.shape[1:] != (10, 2) or len(array) < 2 or not np.isfinite(array).all():
        raise ValueError("track must have at least two finite 10 by 2 frames")
    start, end = array[0], array[-1]
    order = fixed_distance_order(start, attacker)
    centroid = array.mean(axis=1)
    centroid_steps = np.diff(centroid, axis=0)
    centroid_net = centroid[-1] - centroid[0]
    start_depth, end_depth = np.ptp(start[:, 0]), np.ptp(end[:, 0])
    start_width, end_width = np.ptp(start[:, 1]), np.ptp(end[:, 1])
    pairwise_start = mean_pairwise_distance(start)
    pairwise_end = mean_pairwise_distance(end)
    return {
        "centroid_goalward_displacement_m": float(centroid_net[0]),
        "centroid_outward_displacement_m": float(centroid_net[1]),
        "centroid_net_displacement_m": float(np.linalg.norm(centroid_net)),
        "centroid_path_m": float(np.linalg.norm(centroid_steps, axis=1).sum()),
        "width_reduction_m": float(start_width - end_width),
        "depth_reduction_m": float(start_depth - end_depth),
        "mean_pairwise_distance_change_m": float(pairwise_end - pairwise_start),
        "localized_internal_reorganization_m": localized_relative_path(array, order),
    }


def canonical_effects(
    beta_goalward: float,
    beta_outward: float,
    distance_m: float = 5.0,
) -> dict[str, float]:
    """Translate one outcome's signed coefficients into frozen direction contrasts."""
    values = np.asarray([beta_goalward, beta_outward, distance_m], dtype=np.float64)
    if not np.isfinite(values).all() or distance_m <= 0:
        raise ValueError("finite coefficients and positive distance are required")
    return {
        "inward_minus_outward": float(-2.0 * distance_m * beta_outward),
        "goalward_minus_outward": float(distance_m * (beta_goalward - beta_outward)),
    }


def classify_width_hypothesis(
    estimate: float,
    ci_low: float,
    match_estimates: Sequence[float],
    lomo_estimates: Sequence[float],
    trim_estimate: float,
    *,
    valid: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Apply the prospective v1 status tree to inward-minus-outward narrowing."""
    matches = np.asarray(match_estimates, dtype=np.float64)
    lomo = np.asarray(lomo_estimates, dtype=np.float64)
    if matches.shape != (7,) or lomo.shape != (7,) or not np.isfinite(np.r_[matches, lomo, estimate, ci_low, trim_estimate]).all():
        raise ValueError("seven finite match and LOMO estimates plus finite summaries are required")
    ratio = abs(trim_estimate / estimate) if estimate else np.nan
    gates = {
        "primary_point_positive": bool(estimate > 0.0),
        "primary_95_percent_interval_strictly_positive": bool(ci_low > 0.0),
        "at_least_6_of_7_match_estimates_positive": bool((matches > 0.0).sum() >= 6),
        "all_7_leave_one_match_out_estimates_positive": bool((lomo > 0.0).all()),
        "trim_positive_and_50_to_150_percent_magnitude": bool(trim_estimate > 0.0 and 0.5 <= ratio <= 1.5),
    }
    if not valid:
        status = "RESPONSE MODE INVALID"
    elif all(gates.values()):
        status = "RESPONSE MODE WIDTH HYPOTHESIS SUPPORTED"
    elif estimate > 0.0:
        status = "RESPONSE MODE WIDTH HYPOTHESIS MIXED"
    else:
        status = "RESPONSE MODE WIDTH HYPOTHESIS NOT SUPPORTED"
    return status, {"valid": valid, "gates": gates, "trimmed_to_full_absolute_ratio": ratio}
