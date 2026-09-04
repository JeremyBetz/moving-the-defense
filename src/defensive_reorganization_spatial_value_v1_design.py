"""Outcome-free algebra for Defensive Reorganization Spatial Form v1.

The module contains only fixed design-matrix and decision-rule mechanics.  It
does not load tracking, response outcomes, DRD values, or provider files.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np


MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
BASE_COLUMNS = (
    "attacker_path_exposure_m",
    "attacker_path_prior_m",
    "attacker_minus_unit_goalward_m",
    "attacker_ball_distance_start_m",
    "defending_unit_width_m",
    "defending_unit_depth_m",
    "ball_minus_unit_goalward_m",
    "attacker_goalward_displacement_m",
    "attacker_outward_displacement_m",
)


def equal_match_weights(match_ids: Sequence[str]) -> np.ndarray:
    """Return row weights giving each represented match total weight one."""
    labels = np.asarray([str(value) for value in match_ids], dtype=object)
    if labels.ndim != 1 or len(labels) == 0:
        raise ValueError("a nonempty match vector is required")
    names, counts = np.unique(labels, return_counts=True)
    lookup = dict(zip(names.tolist(), counts.tolist(), strict=True))
    return np.asarray([1.0 / lookup[name] for name in labels], dtype=float)


def matrix(continuous: Sequence[Sequence[float]], match_ids: Sequence[str]) -> tuple[np.ndarray, tuple[str, ...]]:
    """Build raw-unit OLS columns: global intercept, match effects, covariates."""
    z = np.asarray(continuous, dtype=float)
    labels = np.asarray([str(value) for value in match_ids], dtype=object)
    if z.ndim != 2 or len(z) != len(labels) or len(z) == 0 or not np.isfinite(z).all():
        raise ValueError("finite aligned continuous and match rows are required")
    names = tuple(sorted(set(labels.tolist())))
    indicators = np.column_stack([(labels == name).astype(float) for name in names[1:]]) if len(names) > 1 else np.empty((len(z), 0))
    return np.column_stack([np.ones(len(z)), indicators, z]), names


def fit_equal_match_ols(outcome: Sequence[float], continuous: Sequence[Sequence[float]], match_ids: Sequence[str]) -> tuple[np.ndarray, int, tuple[str, ...]]:
    """Fit the frozen equal-match-weighted raw-unit OLS and require full rank."""
    y = np.asarray(outcome, dtype=float)
    x, names = matrix(continuous, match_ids)
    if y.ndim != 1 or len(y) != len(x) or not np.isfinite(y).all():
        raise ValueError("finite aligned outcome is required")
    weighted = x * np.sqrt(equal_match_weights(match_ids))[:, None]
    wy = y * np.sqrt(equal_match_weights(match_ids))
    rank = int(np.linalg.matrix_rank(weighted))
    if rank != weighted.shape[1]:
        raise ValueError(f"design is not full rank: {rank} of {weighted.shape[1]}")
    beta, _, _, _ = np.linalg.lstsq(weighted, wy, rcond=None)
    return beta, rank, names


def primary_contrast(beta: Sequence[float]) -> float:
    """Return beta_outward minus beta_goalward from the final two columns."""
    values = np.asarray(beta, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values[-2:]).all():
        raise ValueError("a finite coefficient vector is required")
    return float(values[-1] - values[-2])


def strict_interval_excludes_zero(low: float, high: float) -> bool:
    if not np.isfinite([low, high]).all() or low > high:
        raise ValueError("a finite ordered interval is required")
    return bool(low > 0.0 or high < 0.0)


def same_strict_sign(value: float, reference: float) -> bool:
    return bool(np.isfinite([value, reference]).all() and ((value > 0.0 and reference > 0.0) or (value < 0.0 and reference < 0.0)))


def classify_primary(estimate: float, low: float, high: float, match_estimates: Sequence[float], lomo_estimates: Sequence[float], trim_estimate: float, valid: bool = True) -> tuple[str, dict[str, object]]:
    """Apply the frozen exhaustive Spatial Form v1 primary status tree."""
    if len(match_estimates) != 7 or len(lomo_estimates) != 7:
        raise ValueError("seven match and seven leave-one-match-out estimates are required")
    if not valid:
        return "SPATIAL FORM INVALID", {"valid": False}
    direction_matches = int(sum(same_strict_sign(value, estimate) for value in match_estimates)) if estimate else 0
    direction_lomo = int(sum(same_strict_sign(value, estimate) for value in lomo_estimates)) if estimate else 0
    ratio = abs(float(trim_estimate) / float(estimate)) if estimate else np.nan
    gates = {
        "primary_95_percent_interval_excludes_zero": strict_interval_excludes_zero(low, high),
        "at_least_6_of_7_match_estimates_same_sign": direction_matches >= 6,
        "all_7_leave_one_match_out_estimates_same_sign": direction_lomo == 7,
        "trim_same_strict_sign_and_50_to_150_percent_magnitude": bool(same_strict_sign(trim_estimate, estimate) and 0.5 <= ratio <= 1.5),
    }
    if all(gates.values()):
        status = "SPATIAL FORM SUPPORTED"
    elif gates["primary_95_percent_interval_excludes_zero"] or (direction_matches >= 6 and direction_lomo == 7) or (all(list(gates.values())[:3]) and not gates["trim_same_strict_sign_and_50_to_150_percent_magnitude"]):
        status = "SPATIAL FORM MIXED"
    else:
        status = "SPATIAL FORM NOT SUPPORTED"
    return status, {"valid": True, "gates": gates, "same_sign_match_count": direction_matches, "same_sign_lomo_count": direction_lomo, "trimmed_to_full_absolute_ratio": ratio}


def classify_secondary(static_macro_mae: float, dynamic_macro_mae: float, static_by_match: Mapping[str, float], dynamic_by_match: Mapping[str, float], low: float, high: float) -> tuple[str, dict[str, object]]:
    """Apply the fixed 1% / 5-of-7 / paired-interval representation rule."""
    relative = 100.0 * (static_macro_mae - dynamic_macro_mae) / static_macro_mae
    dynamic_improved = int(sum(dynamic_by_match[name] < static_by_match[name] for name in MATCHES))
    static_improved = int(sum(static_by_match[name] < dynamic_by_match[name] for name in MATCHES))
    if relative >= 1.0 and dynamic_improved >= 5 and low > 0.0:
        status = "DYNAMIC PREFERRED"
    elif -relative >= 1.0 and static_improved >= 5 and high < 0.0:
        status = "STATIC PREFERRED"
    else:
        status = "NO CLEAR REPRESENTATIONAL ADVANTAGE"
    return status, {"static_minus_dynamic_macro_mae_m": static_macro_mae - dynamic_macro_mae, "relative_dynamic_improvement_percent": relative, "dynamic_improved_matches": dynamic_improved, "static_improved_matches": static_improved, "paired_interval_strictly_above_zero": bool(low > 0.0), "paired_interval_strictly_below_zero": bool(high < 0.0)}
