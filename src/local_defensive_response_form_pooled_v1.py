"""Synthetic-only pooled mechanics for Local Defensive Response Form v1."""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

RANKS = tuple(range(1, 11))
REGIONS = {"near": (1, 2, 3), "middle": (4, 5, 6, 7), "far": (8, 9, 10)}


def pooled_design(
    exposure: Iterable[float],
    prior_parallel: Iterable[float],
    prior_centroid_path: Iterable[float],
    rank: Iterable[int],
    game2_indicator: Iterable[float],
) -> np.ndarray:
    """Return 10 rank-specific four-term blocks plus one common Game 2 effect."""
    x = np.asarray(tuple(exposure), dtype=np.float64)
    q = np.asarray(tuple(prior_parallel), dtype=np.float64)
    c = np.asarray(tuple(prior_centroid_path), dtype=np.float64)
    r = np.asarray(tuple(rank), dtype=np.int64)
    g = np.asarray(tuple(game2_indicator), dtype=np.float64)
    if not (x.shape == q.shape == c.shape == r.shape == g.shape):
        raise ValueError("All pooled-design inputs must have the same one-dimensional shape")
    if not np.isfinite(np.column_stack([x, q, c, g])).all():
        raise ValueError("Pooled-design inputs must be finite")
    if not np.isin(r, RANKS).all() or not np.isin(g, (0.0, 1.0)).all():
        raise ValueError("Ranks must be D1-D10 and match indicator must be binary")
    design = np.zeros((len(x), 41), dtype=np.float64)
    for k in RANKS:
        mask = r == k
        offset = 4 * (k - 1)
        design[mask, offset:offset + 4] = np.column_stack([
            np.ones(mask.sum()), x[mask], q[mask], c[mask]
        ])
    design[:, 40] = g
    return design


def exposure_coefficients(coefficients: Iterable[float]) -> np.ndarray:
    values = np.asarray(tuple(coefficients), dtype=np.float64)
    if values.shape != (41,):
        raise ValueError("Expected the frozen 41-coefficient pooled model")
    return values[np.arange(1, 40, 4)]


def regional_contrasts(beta: Iterable[float]) -> dict[str, float]:
    values = np.asarray(tuple(beta), dtype=np.float64)
    if values.shape != (10,):
        raise ValueError("Expected D1-D10 coefficients")
    near = float(values[:3].mean())
    middle = float(values[3:7].mean())
    far = float(values[7:].mean())
    return {
        "near": near,
        "middle": middle,
        "far": far,
        "near_minus_middle": near - middle,
        "middle_minus_far": middle - far,
    }


def common_sample_ids(rows: pd.DataFrame) -> list[str]:
    """Return anchors with both axes/supports valid and one complete D1-D10 vector."""
    required = {
        "observation_id", "distance_rank", "primary_axis_valid", "control_axis_valid",
        "primary_support_valid", "control_support_valid",
    }
    if not required.issubset(rows.columns):
        raise ValueError(f"Missing common-sample columns: {sorted(required - set(rows.columns))}")
    result = []
    for observation_id, group in rows.groupby("observation_id", sort=True):
        complete = (
            len(group) == 10
            and sorted(group["distance_rank"].astype(int)) == list(RANKS)
            and group[["primary_axis_valid", "control_axis_valid",
                       "primary_support_valid", "control_support_valid"]].all().all()
        )
        if complete:
            result.append(str(observation_id))
    return result


def sample_pooled_anchor_indices(anchors: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Resample 60-second blocks independently within each match-period stratum."""
    required = {"game", "period", "block_id"}
    if not required.issubset(anchors.columns):
        raise ValueError(f"Missing pooled-bootstrap columns: {sorted(required - set(anchors.columns))}")
    selected = []
    for game in sorted(anchors["game"].unique()):
        game_rows = anchors[anchors["game"] == game]
        for period in sorted(game_rows["period"].unique()):
            group = game_rows[game_rows["period"] == period]
            blocks = sorted(group["block_id"].unique())
            draws = rng.integers(0, len(blocks), size=len(blocks))
            for draw in draws:
                selected.append(group.index[group["block_id"] == blocks[int(draw)]].to_numpy())
    return np.concatenate(selected) if selected else np.empty(0, dtype=np.int64)


def paired_excess(primary_beta: Iterable[float], control_beta: Iterable[float]) -> float:
    primary = regional_contrasts(primary_beta)["near_minus_middle"]
    control = regional_contrasts(control_beta)["near_minus_middle"]
    return primary - control
