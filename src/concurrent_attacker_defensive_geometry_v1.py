"""Pure geometry and sampling helpers for the frozen concurrent-geometry v1 design.

This module contains no match loader or empirical execution entry point.
"""

from __future__ import annotations

import numpy as np


def leave_one_out_relative_positions(focal_xy: np.ndarray, others_xy: np.ndarray) -> np.ndarray:
    focal = np.asarray(focal_xy, dtype=np.float64)
    others = np.asarray(others_xy, dtype=np.float64)
    if focal.ndim != 2 or focal.shape[1] != 2 or others.shape != (len(focal), 9, 2):
        raise ValueError("expected focal (n,2) and nine other outfield defenders (n,9,2)")
    if not (np.isfinite(focal).all() and np.isfinite(others).all()):
        raise ValueError("complete finite support is required; interpolation is prohibited")
    return focal - others.mean(axis=1)


def focal_relative_path(focal_xy: np.ndarray, others_xy: np.ndarray) -> float:
    relative = leave_one_out_relative_positions(focal_xy, others_xy)
    return float(np.linalg.norm(np.diff(relative, axis=0), axis=1).sum())


def endpoint_deformation(focal_xy: np.ndarray, others_xy: np.ndarray) -> float:
    focal = np.asarray(focal_xy, dtype=np.float64)
    others = np.asarray(others_xy, dtype=np.float64)
    if focal.shape != (2, 2) or others.shape != (2, 9, 2):
        raise ValueError("expected two endpoints for focal and nine teammates")
    distances = np.linalg.norm(others - focal[:, None, :], axis=2)
    return float(np.sqrt(np.mean(np.diff(distances, axis=0)[0] ** 2)))


def rank_defenders(attacker_xy: np.ndarray, defender_ids: list[str], defender_xy: np.ndarray) -> list[str]:
    attacker = np.asarray(attacker_xy, dtype=np.float64)
    defenders = np.asarray(defender_xy, dtype=np.float64)
    if attacker.shape != (2,) or defenders.shape != (10, 2) or len(defender_ids) != 10:
        raise ValueError("one attacker and exactly ten defending outfield players are required")
    if len(set(defender_ids)) != 10:
        raise ValueError("defender identities must be unique")
    distances = np.linalg.norm(defenders - attacker, axis=1)
    order = sorted(range(10), key=lambda i: (float(distances[i]), str(defender_ids[i])))
    return [str(defender_ids[i]) for i in order]


def period_grid_anchors(period_start_s: float, period_end_s: float, *, history_s: float = 2.0,
                        window_s: float = 2.0, cadence_s: float = 4.0) -> np.ndarray:
    """Return period-origin anchors with complete [t-history, t+window] support."""
    if min(history_s, window_s, cadence_s) <= 0 or cadence_s < history_s + window_s:
        raise ValueError("positive, non-overlapping period-grid spans are required")
    first = period_start_s + history_s
    if first + window_s > period_end_s:
        return np.array([], dtype=np.float64)
    count = int(np.floor((period_end_s - window_s - first) / cadence_s)) + 1
    return first + cadence_s * np.arange(count, dtype=np.float64)
