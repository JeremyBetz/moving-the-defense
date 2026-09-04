import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_context_v1_design import (  # noqa: E402
    classify_context_study,
    context_gate,
    equal_match_weights,
    fit_equal_match_fixed_effect_ols,
    interval_excludes_zero,
)


PRIMARY = ("attacker_minus_unit_goalward_m", "attacker_ball_distance_start_m")


def summary(estimate=0.02, interval=(0.01, 0.03), match_signs=7, lomo_signs=7, trimmed=0.018):
    return {
        "estimate": estimate,
        "ci_low": interval[0],
        "ci_high": interval[1],
        "per_match_estimates": [0.01] * match_signs + [-0.01] * (7 - match_signs),
        "leave_one_match_out_estimates": [0.01] * lomo_signs + [-0.01] * (7 - lomo_signs),
        "trimmed_estimate": trimmed,
    }


def test_equal_match_weights_do_not_let_large_match_dominate():
    weights = equal_match_weights(["large"] * 100 + ["small"])
    assert weights[:100].sum() == pytest.approx(1.0)
    assert weights[100:].sum() == pytest.approx(1.0)


def test_raw_unit_fixed_effect_ols_recovers_context_coefficients():
    matches = np.repeat(["M1", "M2"], 8)
    x = np.arange(16.0)
    d = np.tile([-2.0, -1.0, 1.0, 2.0], 4)
    design = np.column_stack([x, d])
    match_shift = np.where(matches == "M2", 4.0, 0.0)
    y = 1.5 + match_shift + 0.2 * x - 0.7 * d
    coefficients, names, rank = fit_equal_match_fixed_effect_ols(y, design, matches)
    assert names == ("intercept", "match[M2]")
    assert rank == 4
    np.testing.assert_allclose(coefficients[-2:], [0.2, -0.7], atol=1e-12)


def test_rank_defect_fails_closed():
    with pytest.raises(ValueError, match="not full rank"):
        fit_equal_match_fixed_effect_ols([1.0, 2.0, 3.0], [[1.0, 1.0]] * 3, ["M"] * 3)


def test_interval_touching_zero_does_not_exclude_zero():
    assert interval_excludes_zero(0.001, 0.01)
    assert not interval_excludes_zero(0.0, 0.01)


def test_context_gate_requires_all_four_conditions():
    assert context_gate(summary())["passed"]
    assert not context_gate(summary(match_signs=5))["passed"]
    assert not context_gate(summary(lomo_signs=6))["passed"]
    assert not context_gate(summary(trimmed=0.031))["passed"]


def test_exhaustive_status_tree():
    supported = {name: summary() for name in PRIMARY}
    assert classify_context_study(supported) == "SUPPORTED"
    mixed = {name: summary(interval=(-0.01, 0.03), match_signs=6, lomo_signs=6) for name in PRIMARY}
    assert classify_context_study(mixed) == "MIXED"
    unsupported = {name: summary(interval=(-0.01, 0.03), match_signs=4, lomo_signs=4) for name in PRIMARY}
    assert classify_context_study(unsupported) == "NOT SUPPORTED"
    assert classify_context_study(supported, valid=False) == "INVALID"
