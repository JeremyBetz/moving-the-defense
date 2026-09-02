"""Pure geometry helpers for frozen Opportunity Redistribution v1; no data execution."""
from __future__ import annotations

import numpy as np


def rank_other_attackers(focal_xy: np.ndarray, keys: list[str], xy: np.ndarray) -> np.ndarray:
    """Return start-time recipient indices ordered by focal distance then canonical ID."""
    if xy.shape != (9, 2) or len(keys) != 9:
        raise ValueError("v1 requires exactly nine non-focal attacking outfield players")
    distance = np.linalg.norm(xy - np.asarray(focal_xy, dtype=np.float64), axis=1)
    return np.asarray(sorted(range(9), key=lambda i: (float(distance[i]), str(keys[i]))), dtype=int)


def nearest_defender_separation(recipient_xy: np.ndarray, defender_xy: np.ndarray) -> np.ndarray:
    """Nearest-defender distance for each recipient without assignment semantics."""
    r, d = np.asarray(recipient_xy, dtype=np.float64), np.asarray(defender_xy, dtype=np.float64)
    if r.shape != (9, 2) or d.shape != (10, 2):
        raise ValueError("v1 requires nine recipients and ten defending outfield players")
    return np.linalg.norm(r[:, None, :] - d[None, :, :], axis=2).min(axis=1)


def opportunity_contrast(start_sep: np.ndarray, end_sep: np.ndarray, order: np.ndarray) -> float:
    """Local-minus-remote change in nearest-defender separation."""
    change = np.asarray(end_sep, dtype=np.float64) - np.asarray(start_sep, dtype=np.float64)
    return float(change[order[:3]].mean() - change[order[6:9]].mean())


def defensive_contrast(focal_relative_paths: np.ndarray) -> float:
    """D1-D3 mean minus D4-D7 mean for a start-ranked ten-defender vector."""
    value = np.asarray(focal_relative_paths, dtype=np.float64)
    if value.shape != (10,):
        raise ValueError("v1 requires a complete D1-D10 vector")
    return float(value[:3].mean() - value[3:7].mean())


def within_anchor_demean(values: np.ndarray, anchor_ids: np.ndarray) -> np.ndarray:
    """Demean columns within complete simultaneous-focal anchor groups."""
    x = np.asarray(values, dtype=np.float64)
    ids = np.asarray(anchor_ids)
    if x.ndim == 1:
        x = x[:, None]
    out = np.empty_like(x)
    for key in np.unique(ids):
        mask = ids == key
        if mask.sum() < 2:
            raise ValueError("within-anchor identification requires at least two focal attackers")
        out[mask] = x[mask] - x[mask].mean(axis=0)
    return out
