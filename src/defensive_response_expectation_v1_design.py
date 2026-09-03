"""Outcome-free design helpers for Defensive Response Expectation v1."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def local_response_contrast(rank_values: Sequence[float]) -> float:
    """Return mean(D2,D3) - mean(D4,D5,D6,D7) for one complete rank vector."""
    values = np.asarray(rank_values, dtype=float)
    if values.shape != (10,) or not np.isfinite(values).all():
        raise ValueError("one finite D1-D10 vector is required")
    return float(values[1:3].mean() - values[3:7].mean())


def contiguous_block_folds(blocks: Sequence[tuple[int, int]], folds: int = 5) -> np.ndarray:
    """Assign ordered (period, 60-second-block) keys to contiguous near-equal folds."""
    ordered = list(blocks)
    if ordered != sorted(ordered) or len(set(ordered)) != len(ordered):
        raise ValueError("blocks must be unique and sorted")
    if folds < 2 or len(ordered) < folds:
        raise ValueError("insufficient blocks")
    return np.minimum(np.arange(len(ordered)) * folds // len(ordered), folds - 1)


def treatment_columns(labels: Sequence[str]) -> np.ndarray:
    """Deterministic full-rank treatment coding with lexical reference level."""
    values = np.asarray(labels, dtype=str)
    levels = sorted(set(values))
    return np.column_stack([values == level for level in levels[1:]]).astype(float)


def synthetic_design_ranks() -> dict[str, int]:
    """Verify the frozen nested design idea without reading empirical outcomes."""
    rng = np.random.default_rng(20260903)
    n = 400
    match = np.array([f"M{i % 7}" for i in range(n)])
    period_two = np.array([(i // 70) % 2 for i in range(n)])
    side_two = np.array([i % 2 for i in range(n)])
    movement = rng.normal(size=(n, 2))
    context = rng.normal(size=(n, 10))
    match_columns = treatment_columns(match)
    match_levels = sorted(set(match))
    period_columns = np.column_stack(
        [(match == level) & (period_two == 1) for level in match_levels]
    ).astype(float)
    side_columns = np.column_stack(
        [(match == level) & (side_two == 1) for level in match_levels]
    ).astype(float)
    e0 = np.column_stack([np.ones(n), movement, match_columns, period_columns])
    e1 = np.column_stack([e0, context])
    e2a = np.column_stack([e1, side_columns])
    e2b = np.column_stack([e2a, side_columns * movement[:, [0]]])
    ranks = {name: int(np.linalg.matrix_rank(value)) for name, value in {
        "E0": e0, "E1": e1, "E2a": e2a, "E2b": e2b
    }.items()}
    widths = {name: value.shape[1] for name, value in {
        "E0": e0, "E1": e1, "E2a": e2a, "E2b": e2b
    }.items()}
    if ranks != widths:
        raise AssertionError((ranks, widths))
    return ranks
