"""Outcome-free design helpers for Defensive Reorganization Context v1.

The module encodes the prospective equal-match weighting, interpretable linear
estimator, and exhaustive context-study decision tree. It does not load
tracking data, inspect the response target, fit an empirical match, calculate
DRD, or select examples.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np


def equal_match_weights(match_ids: Sequence[str]) -> np.ndarray:
    """Give every represented match equal total weight."""
    labels = np.asarray([str(match) for match in match_ids], dtype=object)
    if labels.ndim != 1 or len(labels) == 0:
        raise ValueError("a nonempty one-dimensional match vector is required")
    unique, counts = np.unique(labels, return_counts=True)
    count_by_match = dict(zip(unique.tolist(), counts.tolist(), strict=True))
    return np.asarray([1.0 / count_by_match[label] for label in labels], dtype=float)


def fit_equal_match_fixed_effect_ols(
    outcome_m: Sequence[float],
    continuous_design: Sequence[Sequence[float]],
    match_ids: Sequence[str],
) -> tuple[np.ndarray, tuple[str, ...], int]:
    """Fit raw-unit OLS with equal match weights and match intercepts.

    The first returned coefficient is the global intercept, followed by
    lexical match indicators excluding the first match, then the supplied
    continuous columns in their original order.
    """
    y = np.asarray(outcome_m, dtype=float)
    z = np.asarray(continuous_design, dtype=float)
    labels = np.asarray([str(match) for match in match_ids], dtype=object)
    if z.ndim != 2 or y.ndim != 1 or labels.ndim != 1 or len(y) != len(z) or len(y) != len(labels):
        raise ValueError("aligned outcome, design, and match rows are required")
    if len(y) == 0 or not np.isfinite(y).all() or not np.isfinite(z).all():
        raise ValueError("finite nonempty outcome and design values are required")
    matches = tuple(sorted(set(labels.tolist())))
    if len(matches) < 1:
        raise ValueError("at least one match is required")
    indicators = np.column_stack([(labels == match).astype(float) for match in matches[1:]]) if len(matches) > 1 else np.empty((len(y), 0))
    design = np.column_stack([np.ones(len(y)), indicators, z])
    weights = equal_match_weights(labels)
    weighted_design = design * np.sqrt(weights)[:, None]
    weighted_outcome = y * np.sqrt(weights)
    rank = int(np.linalg.matrix_rank(weighted_design))
    if rank != design.shape[1]:
        raise ValueError(f"design is not full rank: {rank} of {design.shape[1]}")
    coefficients, _, _, _ = np.linalg.lstsq(weighted_design, weighted_outcome, rcond=None)
    names = ("intercept", *(f"match[{match}]" for match in matches[1:]))
    return coefficients, names, rank


def interval_excludes_zero(ci_low: float, ci_high: float) -> bool:
    """Apply the frozen strict two-sided interval boundary."""
    if not np.isfinite([ci_low, ci_high]).all() or ci_low > ci_high:
        raise ValueError("a finite ordered interval is required")
    return bool(ci_low > 0.0 or ci_high < 0.0)


def same_strict_sign(value: float, reference: float) -> bool:
    """Return true only when two finite nonzero values share a sign."""
    if not np.isfinite([value, reference]).all():
        raise ValueError("finite values are required")
    return bool((value > 0.0 and reference > 0.0) or (value < 0.0 and reference < 0.0))


def context_gate(summary: Mapping[str, object]) -> dict[str, object]:
    """Evaluate one primary context against the frozen four-part support gate."""
    estimate = float(summary["estimate"])
    ci_low = float(summary["ci_low"])
    ci_high = float(summary["ci_high"])
    per_match = np.asarray(summary["per_match_estimates"], dtype=float)
    leave_one_out = np.asarray(summary["leave_one_match_out_estimates"], dtype=float)
    trimmed = float(summary["trimmed_estimate"])
    if per_match.shape != (7,) or leave_one_out.shape != (7,):
        raise ValueError("exactly seven match and seven leave-one-match-out estimates are required")
    if estimate == 0.0 or not np.isfinite([estimate, trimmed]).all():
        ratio = np.nan
    else:
        ratio = abs(trimmed / estimate)
    match_count = int(sum(same_strict_sign(value, estimate) for value in per_match)) if estimate != 0.0 else 0
    lomo_count = int(sum(same_strict_sign(value, estimate) for value in leave_one_out)) if estimate != 0.0 else 0
    checks = {
        "familywise_interval_excludes_zero": interval_excludes_zero(ci_low, ci_high),
        "match_direction_at_least_6_of_7": match_count >= 6,
        "leave_one_match_out_direction_7_of_7": lomo_count == 7,
        "central_support_trim_same_sign_and_50_to_150_percent": bool(
            estimate != 0.0 and same_strict_sign(trimmed, estimate) and 0.5 <= ratio <= 1.5
        ),
    }
    return {
        "passed": all(checks.values()),
        "suggestive": bool(checks["familywise_interval_excludes_zero"] or checks["match_direction_at_least_6_of_7"]),
        "checks": checks,
        "same_sign_matches": match_count,
        "same_sign_leave_one_match_out": lomo_count,
        "trimmed_to_primary_absolute_ratio": ratio,
    }


def classify_context_study(
    summaries: Mapping[str, Mapping[str, object]],
    valid: bool = True,
) -> str:
    """Return the exhaustive SUPPORTED/MIXED/NOT SUPPORTED/INVALID status."""
    if not valid:
        return "INVALID"
    if set(summaries) != {
        "attacker_minus_unit_goalward_m",
        "attacker_ball_distance_start_m",
    }:
        raise ValueError("the two frozen primary contexts are required")
    results = [context_gate(summary) for summary in summaries.values()]
    if any(result["passed"] for result in results):
        return "SUPPORTED"
    if any(result["suggestive"] for result in results):
        return "MIXED"
    return "NOT SUPPORTED"
