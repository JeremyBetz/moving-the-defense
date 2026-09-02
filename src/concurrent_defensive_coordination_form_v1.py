"""Outcome-blind geometry for the draft Concurrent Defensive Coordination Form v1.

This module contains measurement primitives and preprocessing helpers only.  It
has no match loader, defender-rank model, bootstrap, or empirical execution
entrypoint.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfiltfilt


EPSILON_M = 64 * np.finfo(np.float64).eps * np.hypot(105.0, 68.0)


@dataclass(frozen=True)
class CoordinationForm:
    attacker_path_m: float
    relative_aligned_m: float | None
    absolute_aligned_m: float | None
    relative_cross_m: float | None


def _trajectory(value: np.ndarray) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 2 or len(result) < 2:
        raise ValueError("Expected at least two two-dimensional positions")
    if not np.isfinite(result).all():
        raise ValueError("Trajectory must be finite; interpolation is prohibited")
    return result


def leave_one_out_relative(
    focal_xy: np.ndarray, other_defenders_xy: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return focal-minus-other-outfield centroid and the centroid itself."""
    focal = _trajectory(focal_xy)
    others = np.asarray(other_defenders_xy, dtype=np.float64)
    if others.ndim != 3 or others.shape[0] != len(focal) or others.shape[2] != 2:
        raise ValueError("Other defenders must have shape (time, players, 2)")
    if others.shape[1] != 9 or not np.isfinite(others).all():
        raise ValueError("Exactly nine finite other outfield defenders are required")
    centroid = others.mean(axis=1, dtype=np.float64)
    return focal - centroid, centroid


def _path_weighted_components(
    attacker: np.ndarray, response: np.ndarray
) -> tuple[float, float | None, float | None]:
    da = np.diff(attacker, axis=0)
    dr = np.diff(response, axis=0)
    step = np.linalg.norm(da, axis=1)
    denominator = float(step.sum(dtype=np.float64))
    if denominator <= EPSILON_M:
        return denominator, None, None
    aligned = float(np.einsum("ij,ij->i", dr, da).sum(dtype=np.float64) / denominator)
    # |cross(dr, da)| / |da| is the absolute response component normal to
    # each local attacker step; summing cross products applies attacker-path
    # weighting without constructing an unstable angle.
    cross = np.abs(dr[:, 0] * da[:, 1] - dr[:, 1] * da[:, 0])
    perpendicular = float(cross.sum(dtype=np.float64) / denominator)
    return denominator, aligned, perpendicular


def coordination_form(
    attacker_xy: np.ndarray,
    focal_xy: np.ndarray,
    other_defenders_xy: np.ndarray,
) -> CoordinationForm:
    """Compute path-weighted concurrent geometry in metres.

    Stationary attacker steps add zero to numerator and denominator.  A whole
    interval with numerical-zero attacker path has undefined aligned/cross
    quantities rather than an imputed zero.
    """
    attacker = _trajectory(attacker_xy)
    focal = _trajectory(focal_xy)
    if len(attacker) != len(focal):
        raise ValueError("Trajectories must share exact temporal support")
    relative, _ = leave_one_out_relative(focal, other_defenders_xy)
    rel = _path_weighted_components(attacker, relative)
    absolute = _path_weighted_components(attacker, focal)
    if rel[1] is None:
        return CoordinationForm(rel[0], None, None, None)
    return CoordinationForm(rel[0], rel[1], absolute[1], rel[2])


def centered_rolling_mean(xy: np.ndarray, frames: int = 7) -> np.ndarray:
    """Historical comparison: complete-support centred arithmetic mean."""
    values = _trajectory(xy)
    if frames < 1 or frames % 2 == 0 or len(values) < frames:
        raise ValueError("frames must be odd, positive, and supported")
    return np.lib.stride_tricks.sliding_window_view(values, frames, axis=0).mean(axis=2)


def zero_phase_butterworth(
    xy: np.ndarray, sample_hz: float, cutoff_hz: float, order: int = 4
) -> np.ndarray:
    """Low-pass a complete continuous trajectory with a zero-phase Butterworth.

    Filtering is performed on the full supported block before window extraction.
    SciPy's deterministic odd-reflection padding is retained.  Blocks too short
    for ``sosfiltfilt`` are invalid; they are never padded with fabricated data.
    """
    values = _trajectory(xy)
    if not (sample_hz > 0 and 0 < cutoff_hz < sample_hz / 2 and order > 0):
        raise ValueError("Invalid sample rate, cutoff, or order")
    sos = butter(order, cutoff_hz, btype="lowpass", fs=sample_hz, output="sos")
    return sosfiltfilt(sos, values, axis=0, padtype="odd")
