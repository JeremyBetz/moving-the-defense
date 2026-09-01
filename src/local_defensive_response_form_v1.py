"""Synthetic-only geometry for frozen local defensive response form v1.

This module defines vector identities and ranking behavior. It contains no
provider loader, match-data path, model fitting, or empirical execution entrypoint.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
VECTOR_NORM_EPSILON_M = 64 * np.finfo(np.float64).eps * math.hypot(
    PITCH_LENGTH_M, PITCH_WIDTH_M
)


@dataclass(frozen=True)
class ResponseForm:
    focal_relative_delta: np.ndarray
    attacker_axis_valid: bool
    radial_axis_valid: bool
    parallel_m: float | None
    orthogonal_m: float | None
    radial_m: float | None
    alignment_cosine: float | None
    defender_displacement_m: float
    centroid_displacement_m: float
    focal_relative_displacement_m: float


def _vector(value: Iterable[float]) -> np.ndarray:
    result = np.asarray(tuple(value), dtype=np.float64)
    if result.shape != (2,) or not np.isfinite(result).all():
        raise ValueError("Expected one finite two-dimensional vector")
    return result


def _unit(value: np.ndarray) -> tuple[np.ndarray | None, float]:
    norm = float(np.linalg.norm(value))
    if norm <= VECTOR_NORM_EPSILON_M:
        return None, norm
    return value / norm, norm


def decompose_response(
    attacker_displacement: Iterable[float],
    defender_displacement: Iterable[float],
    centroid_displacement: Iterable[float],
    attacker_at_response_start: Iterable[float],
    defender_at_response_start: Iterable[float],
) -> ResponseForm:
    """Return the frozen endpoint-vector decomposition in canonical metres."""
    attacker_delta = _vector(attacker_displacement)
    defender_delta = _vector(defender_displacement)
    centroid_delta = _vector(centroid_displacement)
    attacker_start = _vector(attacker_at_response_start)
    defender_start = _vector(defender_at_response_start)

    focal_delta = defender_delta - centroid_delta
    attacker_axis, _ = _unit(attacker_delta)
    radial_axis, _ = _unit(attacker_start - defender_start)
    focal_norm = float(np.linalg.norm(focal_delta))

    parallel = orthogonal = cosine = None
    if attacker_axis is not None:
        parallel = float(np.dot(focal_delta, attacker_axis))
        left_normal = np.array([-attacker_axis[1], attacker_axis[0]])
        orthogonal = float(np.dot(focal_delta, left_normal))
        if focal_norm > VECTOR_NORM_EPSILON_M:
            cosine = parallel / focal_norm

    radial = None if radial_axis is None else float(np.dot(focal_delta, radial_axis))
    return ResponseForm(
        focal_relative_delta=focal_delta,
        attacker_axis_valid=attacker_axis is not None,
        radial_axis_valid=radial_axis is not None,
        parallel_m=parallel,
        orthogonal_m=orthogonal,
        radial_m=radial,
        alignment_cosine=cosine,
        defender_displacement_m=float(np.linalg.norm(defender_delta)),
        centroid_displacement_m=float(np.linalg.norm(centroid_delta)),
        focal_relative_displacement_m=focal_norm,
    )


def rank_defenders(
    attacker_position: Iterable[float],
    defenders: Iterable[tuple[str, Iterable[float]]],
) -> list[tuple[int, str, float]]:
    """Rank by exact Euclidean distance then canonical player key."""
    attacker = _vector(attacker_position)
    rows = [(float(np.linalg.norm(_vector(position) - attacker)), key) for key, position in defenders]
    rows.sort(key=lambda row: (row[0], row[1]))
    return [(rank, key, distance) for rank, (distance, key) in enumerate(rows, start=1)]
