"""Pure-geometry helpers for prospective Defensive Coverage Redistribution v2.

This module cannot load match data or execute the governed study.  V2 uses one
start-defined reference attacker per anchor and one fixed nine-attacker set, so
it contains no repeated focal perspectives and no within-anchor demeaning.
Optimized links remain geometric assignments, not inferred marking.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True)
class CoverageMatch:
    """Minimum-cost injective geometric matching for a fixed attacker set."""

    mean_distance_m: float
    attacker_indices: np.ndarray
    defender_indices: np.ndarray
    matched_distances_m: np.ndarray


def ball_nearest_reference_index(
    attacker_xy: np.ndarray,
    ball_xy: np.ndarray,
    *,
    tie_tolerance_m: float = 1e-9,
) -> int:
    """Select the unique attacker nearest the observed ball at the anchor.

    Exact/numerical ties are rejected rather than resolved with player identity,
    preserving player-label invariance of the selected physical unit.
    """
    attackers = np.asarray(attacker_xy, dtype=np.float64)
    ball = np.asarray(ball_xy, dtype=np.float64)
    if attackers.shape != (10, 2) or ball.shape != (2,):
        raise ValueError("v2 requires ten attacking outfield players and one ball point")
    if not np.isfinite(attackers).all() or not np.isfinite(ball).all():
        raise ValueError("v2 does not interpolate or accept missing anchor geometry")
    distances = np.linalg.norm(attackers - ball, axis=1)
    order = np.argsort(distances, kind="stable")
    if distances[order[1]] - distances[order[0]] <= float(tie_tolerance_m):
        raise ValueError("ball-nearest reference is not unique within the frozen tolerance")
    return int(order[0])


def fixed_elsewhere_coverage(
    attacker_xy: np.ndarray,
    defender_xy: np.ndarray,
    reference_attacker_index: int,
) -> CoverageMatch:
    """Match the fixed nine non-reference attackers to ten distinct defenders."""
    attackers = np.asarray(attacker_xy, dtype=np.float64)
    defenders = np.asarray(defender_xy, dtype=np.float64)
    reference = int(reference_attacker_index)
    if attackers.shape != (10, 2) or defenders.shape != (10, 2):
        raise ValueError("v2 requires complete ten-attacker and ten-defender endpoint sets")
    if not 0 <= reference < 10:
        raise ValueError("reference attacker index must be in [0, 9]")
    if not np.isfinite(attackers).all() or not np.isfinite(defenders).all():
        raise ValueError("v2 does not interpolate or accept missing endpoint geometry")

    retained = np.flatnonzero(np.arange(10) != reference)
    cost = np.linalg.norm(
        attackers[retained, None, :] - defenders[None, :, :], axis=2
    )
    rows, defender_indices = linear_sum_assignment(cost)
    distances = cost[rows, defender_indices]
    return CoverageMatch(
        mean_distance_m=float(distances.mean()),
        attacker_indices=retained[rows].astype(np.int64),
        defender_indices=defender_indices.astype(np.int64),
        matched_distances_m=distances.astype(np.float64),
    )


def fixed_elsewhere_cost_change(
    attacker_start_xy: np.ndarray,
    attacker_end_xy: np.ndarray,
    defender_start_xy: np.ndarray,
    defender_end_xy: np.ndarray,
    reference_attacker_index: int,
) -> float:
    """Return end-minus-start cost for one fixed nine-attacker set."""
    start = fixed_elsewhere_coverage(
        attacker_start_xy, defender_start_xy, reference_attacker_index
    )
    end = fixed_elsewhere_coverage(
        attacker_end_xy, defender_end_xy, reference_attacker_index
    )
    return float(end.mean_distance_m - start.mean_distance_m)


def full_ten_coverage(attacker_xy: np.ndarray, defender_xy: np.ndarray) -> CoverageMatch:
    """Descriptive full ten-to-ten minimum mean matching distance."""
    attackers = np.asarray(attacker_xy, dtype=np.float64)
    defenders = np.asarray(defender_xy, dtype=np.float64)
    if attackers.shape != (10, 2) or defenders.shape != (10, 2):
        raise ValueError("full matching requires ten attackers and ten defenders")
    if not np.isfinite(attackers).all() or not np.isfinite(defenders).all():
        raise ValueError("full matching requires finite endpoint geometry")
    cost = np.linalg.norm(attackers[:, None, :] - defenders[None, :, :], axis=2)
    rows, columns = linear_sum_assignment(cost)
    distances = cost[rows, columns]
    return CoverageMatch(
        mean_distance_m=float(distances.mean()),
        attacker_indices=rows.astype(np.int64),
        defender_indices=columns.astype(np.int64),
        matched_distances_m=distances.astype(np.float64),
    )


def defensive_response_contrast(focal_relative_paths_m: np.ndarray) -> float:
    """Return the inherited D1-D3 minus D4-D7 focal-relative path contrast."""
    paths = np.asarray(focal_relative_paths_m, dtype=np.float64)
    if paths.shape != (10,) or not np.isfinite(paths).all():
        raise ValueError("v2 requires one finite start-ranked D1-D10 path vector")
    return float(paths[:3].mean() - paths[3:7].mean())


def focal_relative_path_lengths(defender_trajectory_xy: np.ndarray) -> np.ndarray:
    """Compute leave-one-out defender-relative path length for every defender."""
    trajectory = np.asarray(defender_trajectory_xy, dtype=np.float64)
    if trajectory.ndim != 3 or trajectory.shape[1:] != (10, 2):
        raise ValueError("expected [frames, 10 defenders, xy]")
    if len(trajectory) < 2 or not np.isfinite(trajectory).all():
        raise ValueError("at least two complete defender frames are required")
    total = trajectory.sum(axis=1, keepdims=True)
    leave_one_out = (total - trajectory) / 9.0
    relative = trajectory - leave_one_out
    return np.linalg.norm(np.diff(relative, axis=0), axis=2).sum(axis=0)


def rank_focal_relative_paths(
    defender_trajectory_xy: np.ndarray, focal_start_xy: np.ndarray
) -> np.ndarray:
    """Return focal-relative paths in start-distance rank order."""
    trajectory = np.asarray(defender_trajectory_xy, dtype=np.float64)
    focal = np.asarray(focal_start_xy, dtype=np.float64)
    if focal.shape != (2,):
        raise ValueError("expected one focal start point")
    paths = focal_relative_path_lengths(trajectory)
    order = np.lexsort(
        (np.arange(10), np.linalg.norm(trajectory[0] - focal, axis=1))
    )
    return paths[order]


def rotate_internal_defender_motion(
    defender_trajectory_xy: np.ndarray, angle_radians: float
) -> np.ndarray:
    """Rotate internal defender motion while preserving centroid and path magnitudes.

    The start formation and observed centroid trajectory are fixed.  A common
    orthogonal rotation is applied to every defender's centred displacement from
    its own start-centred position.  This preserves each leave-one-out-relative
    path exactly while breaking its direction relative to attacker positions.
    """
    trajectory = np.asarray(defender_trajectory_xy, dtype=np.float64)
    if trajectory.ndim != 3 or trajectory.shape[1:] != (10, 2):
        raise ValueError("expected [frames, 10 defenders, xy]")
    if len(trajectory) < 2 or not np.isfinite(trajectory).all():
        raise ValueError("at least two complete defender frames are required")
    angle = float(angle_radians)
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float64,
    )
    centroid = trajectory.mean(axis=1, keepdims=True)
    centred = trajectory - centroid
    start_centred = centred[[0]]
    internal_change = centred - start_centred
    rotated_change = internal_change @ rotation.T
    return centroid + start_centred + rotated_change


def v1_demeaned_complement(delta_costs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expose the rejected v1 leave-one-out/demeaning algebra on toy costs."""
    delta = np.asarray(delta_costs, dtype=np.float64)
    if delta.shape != (10,) or not np.isfinite(delta).all():
        raise ValueError("expected ten finite per-attacker cost changes")
    leave_one_out = np.array(
        [np.delete(delta, focal).mean() for focal in range(10)], dtype=np.float64
    )
    demeaned = leave_one_out - leave_one_out.mean()
    complement = -(delta - delta.mean()) / 9.0
    return demeaned, complement
