"""Pure geometry helpers for frozen Defensive Coverage Redistribution v1.

This module contains no provider loading and cannot execute the empirical study.
The rectangular matching is a geometric coverage-capacity representation, not an
inferred marking assignment.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True)
class CoverageMatch:
    """Minimum-cost injective attacker-to-defender geometric matching."""

    mean_distance_m: float
    attacker_indices: np.ndarray
    defender_indices: np.ndarray
    matched_distances_m: np.ndarray


def minimum_distinct_defender_coverage(
    other_attacker_xy: np.ndarray, defender_xy: np.ndarray
) -> CoverageMatch:
    """Return the minimum mean distance matching nine attackers to distinct defenders.

    Exactly nine non-focal attacking outfield players and ten defending outfield
    players are required. One defender is therefore unused. Matching identities
    are descriptive only; the scalar minimum cost is the governed quantity.
    """
    attackers = np.asarray(other_attacker_xy, dtype=np.float64)
    defenders = np.asarray(defender_xy, dtype=np.float64)
    if attackers.shape != (9, 2) or defenders.shape != (10, 2):
        raise ValueError("v1 requires nine other attackers and ten outfield defenders")
    if not np.isfinite(attackers).all() or not np.isfinite(defenders).all():
        raise ValueError("v1 does not interpolate or accept missing endpoint geometry")

    cost = np.linalg.norm(attackers[:, None, :] - defenders[None, :, :], axis=2)
    attacker_indices, defender_indices = linear_sum_assignment(cost)
    distances = cost[attacker_indices, defender_indices]
    return CoverageMatch(
        mean_distance_m=float(distances.mean()),
        attacker_indices=attacker_indices.astype(np.int64),
        defender_indices=defender_indices.astype(np.int64),
        matched_distances_m=distances.astype(np.float64),
    )


def coverage_cost_change(
    attacker_start_xy: np.ndarray,
    attacker_end_xy: np.ndarray,
    defender_start_xy: np.ndarray,
    defender_end_xy: np.ndarray,
) -> float:
    """End minus start mean distinct-defender matching distance, in metres."""
    start = minimum_distinct_defender_coverage(attacker_start_xy, defender_start_xy)
    end = minimum_distinct_defender_coverage(attacker_end_xy, defender_end_xy)
    return float(end.mean_distance_m - start.mean_distance_m)


def defensive_response_contrast(focal_relative_paths_m: np.ndarray) -> float:
    """Observed D1-D3 minus D4-D7 focal-relative path contrast, in metres."""
    paths = np.asarray(focal_relative_paths_m, dtype=np.float64)
    if paths.shape != (10,) or not np.isfinite(paths).all():
        raise ValueError("v1 requires one finite start-ranked D1-D10 path vector")
    return float(paths[:3].mean() - paths[3:7].mean())


def endpoint_focal_relative_paths(
    defender_start_xy: np.ndarray,
    defender_end_xy: np.ndarray,
    focal_start_xy: np.ndarray,
) -> np.ndarray:
    """Synthetic two-frame focal-relative paths, returned in start-distance rank order."""
    start = np.asarray(defender_start_xy, dtype=np.float64)
    end = np.asarray(defender_end_xy, dtype=np.float64)
    focal = np.asarray(focal_start_xy, dtype=np.float64)
    if start.shape != (10, 2) or end.shape != (10, 2) or focal.shape != (2,):
        raise ValueError("expected ten defender endpoints and one focal start position")
    total_start = start.sum(axis=0)
    total_end = end.sum(axis=0)
    loo_start = (total_start - start) / 9.0
    loo_end = (total_end - end) / 9.0
    paths = np.linalg.norm((end - loo_end) - (start - loo_start), axis=1)
    order = np.lexsort((np.arange(10), np.linalg.norm(start - focal, axis=1)))
    return paths[order]


def within_anchor_demean(values: np.ndarray, anchor_ids: np.ndarray) -> np.ndarray:
    """Demean every model column within simultaneous-focal anchor groups."""
    matrix = np.asarray(values, dtype=np.float64)
    groups = np.asarray(anchor_ids)
    one_dimensional = matrix.ndim == 1
    if one_dimensional:
        matrix = matrix[:, None]
    if matrix.ndim != 2 or len(groups) != len(matrix):
        raise ValueError("values and anchor_ids must have compatible row counts")
    result = np.empty_like(matrix)
    for key in np.unique(groups):
        mask = groups == key
        if int(mask.sum()) < 2:
            raise ValueError("within-anchor identification requires at least two focal attackers")
        result[mask] = matrix[mask] - matrix[mask].mean(axis=0)
    return result[:, 0] if one_dimensional else result


def synthetic_fixture(name: str) -> dict[str, np.ndarray | float | str]:
    """Return one of six frozen, outcome-free football geometry fixtures."""
    attackers = np.array(
        [
            [20.0, 10.0], [20.0, 20.0], [20.0, 30.0],
            [35.0, 10.0], [35.0, 20.0], [35.0, 30.0],
            [50.0, 10.0], [50.0, 20.0], [50.0, 30.0],
        ],
        dtype=np.float64,
    )
    focal_start = np.array([18.0, 10.0], dtype=np.float64)
    focal_end = np.array([10.0, 5.0], dtype=np.float64)
    defenders = np.vstack([attackers, np.array([[17.0, 14.0]])])
    end_attackers = attackers.copy()
    end_defenders = defenders.copy()

    if name == "perfect_compensation":
        end_defenders[0] = focal_end
        end_defenders[9] = attackers[0]
    elif name == "coverage_loss":
        end_defenders[0] = focal_end
    elif name == "collective_translation":
        shift = np.array([8.0, -5.0])
        end_attackers += shift
        end_defenders += shift
        focal_end = focal_start + shift
    elif name == "independent_other_attacker":
        end_attackers[8] += np.array([0.0, 8.0])
        focal_end = focal_start.copy()
    elif name == "focal_ignored":
        pass
    elif name == "multi_defender_collapse":
        end_defenders[[0, 9, 1]] = np.array([[10.0, 5.0], [10.5, 5.3], [11.0, 5.6]])
    else:
        raise KeyError(name)

    relative_paths = endpoint_focal_relative_paths(defenders, end_defenders, focal_start)
    return {
        "name": name,
        "focal_start_xy": focal_start,
        "focal_end_xy": focal_end,
        "attacker_start_xy": attackers,
        "attacker_end_xy": end_attackers,
        "defender_start_xy": defenders,
        "defender_end_xy": end_defenders,
        "response_contrast_m": defensive_response_contrast(relative_paths),
        "coverage_change_m": coverage_cost_change(
            attackers, end_attackers, defenders, end_defenders
        ),
    }
