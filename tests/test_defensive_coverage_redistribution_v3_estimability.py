import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_coverage_redistribution_v3 import (
    DesignEstimabilityError,
    apply_resolved_plan,
    resolve_design,
)


def test_constant_zero_period_nuisance_is_omitted_without_changing_scientific_fit():
    d = np.array([-2.0, -0.5, 0.4, 1.2, 2.1])
    covariate = np.array([0.2, 1.1, -0.3, 1.9, 0.7])
    base = np.column_stack([np.ones(5), d, covariate])
    y = 1.7 + 0.8 * d - 0.3 * covariate
    expanded = np.column_stack([base, np.zeros(5)])
    assert np.linalg.matrix_rank(expanded) == 3

    resolved = resolve_design(
        expanded,
        ("intercept", "D", "scientific_covariate", "period_2_indicator"),
        nuisance_columns=("period_2_indicator",),
    )
    expected = np.linalg.lstsq(base, y, rcond=None)[0]
    actual = np.linalg.lstsq(resolved.matrix, y, rcond=None)[0]
    assert resolved.omitted_constant_nuisance_columns == ("period_2_indicator",)
    assert resolved.active_columns == ("intercept", "D", "scientific_covariate")
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
    np.testing.assert_allclose(resolved.matrix @ actual, base @ expected, rtol=0, atol=1e-14)
    np.testing.assert_allclose(y - resolved.matrix @ actual, y - base @ expected, rtol=0, atol=1e-14)


def test_constant_one_nuisance_collinear_with_intercept_is_omitted():
    d = np.array([-1.0, 0.0, 1.0, 2.0])
    x = np.column_stack([np.ones(4), d, np.ones(4)])
    resolved = resolve_design(
        x,
        ("intercept", "D", "period_2_indicator"),
        nuisance_columns=("period_2_indicator",),
    )
    assert resolved.active_columns == ("intercept", "D")
    assert resolved.rank == 2


def test_varying_nuisance_is_retained():
    x = np.array(
        [[1.0, -2.0, 0.0], [1.0, -0.5, 1.0], [1.0, 0.7, 0.0], [1.0, 1.4, 1.0]]
    )
    resolved = resolve_design(
        x,
        ("intercept", "D", "period_2_indicator"),
        nuisance_columns=("period_2_indicator",),
    )
    assert resolved.active_columns == ("intercept", "D", "period_2_indicator")
    assert resolved.omitted_constant_nuisance_columns == ()


def test_constant_scientific_predictor_is_not_omitted():
    x = np.column_stack([np.ones(4), np.ones(4), np.zeros(4)])
    with pytest.raises(DesignEstimabilityError, match="rank deficient"):
        resolve_design(
            x,
            ("intercept", "D", "period_2_indicator"),
            nuisance_columns=("period_2_indicator",),
        )


def test_varying_exactly_collinear_scientific_predictor_is_not_dropped():
    d = np.array([-1.0, 0.0, 1.0, 2.0])
    x = np.column_stack([np.ones(4), d, 2.0 * d, np.array([0.0, 1.0, 0.0, 1.0])])
    with pytest.raises(DesignEstimabilityError, match="rank deficient"):
        resolve_design(
            x,
            ("intercept", "D", "scientific_covariate", "period_2_indicator"),
            nuisance_columns=("period_2_indicator",),
        )


def test_near_collinearity_does_not_trigger_column_omission():
    d = np.array([-1.0, 0.0, 1.0, 2.0, 3.0])
    almost_d = d + np.array([0.0, 1e-8, -1e-8, 2e-8, -2e-8])
    x = np.column_stack([np.ones(5), d, almost_d, np.array([0.0, 1.0, 0.0, 1.0, 0.0])])
    resolved = resolve_design(
        x,
        ("intercept", "D", "scientific_covariate", "period_2_indicator"),
        nuisance_columns=("period_2_indicator",),
    )
    assert resolved.active_columns == (
        "intercept", "D", "scientific_covariate", "period_2_indicator"
    )


def test_designated_nuisance_must_be_a_frozen_binary_dummy():
    x = np.array([[1.0, -1.0, 0.5], [1.0, 0.0, 0.5], [1.0, 2.0, 0.5]])
    with pytest.raises(DesignEstimabilityError, match="not a frozen binary dummy"):
        resolve_design(
            x,
            ("intercept", "D", "period_2_indicator"),
            nuisance_columns=("period_2_indicator",),
        )


@pytest.mark.parametrize("prohibited", [("intercept",), ("D",)])
def test_scientific_or_structural_columns_cannot_be_designated_as_nuisance(prohibited):
    x = np.column_stack([np.ones(4), np.array([0.0, 1.0, 0.0, 1.0]), np.zeros(4)])
    with pytest.raises(ValueError, match="only its frozen period_2_indicator"):
        resolve_design(
            x,
            ("intercept", "D", "period_2_indicator"),
            nuisance_columns=prohibited,
        )


def test_complete_sample_plan_is_reused_without_subset_reselection():
    complete = np.array(
        [[1.0, -2.0, 0.0], [1.0, -0.5, 1.0], [1.0, 0.7, 0.0], [1.0, 1.4, 1.0]]
    )
    names = ("intercept", "D", "period_2_indicator")
    plan = resolve_design(
        complete,
        names,
        nuisance_columns=("period_2_indicator",),
    )
    subset_where_period_is_constant = complete[[0, 2]]
    applied = apply_resolved_plan(
        subset_where_period_is_constant,
        names,
        plan=plan,
    )
    assert plan.omitted_constant_nuisance_columns == ()
    assert applied.shape == (2, 3)
    np.testing.assert_array_equal(applied, subset_where_period_is_constant)
