"""Pure estimability governance for Defensive Coverage Redistribution v3.

This module does not load match data or calculate coverage outcomes. It only
resolves the prospectively designated nuisance columns before model fitting.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


FROZEN_CONSTANT_NUISANCE_COLUMNS = ("period_2_indicator",)


class DesignEstimabilityError(RuntimeError):
    """Raised when the frozen scientific design remains non-estimable."""


@dataclass(frozen=True)
class ResolvedDesign:
    """The deterministic active design after constant-nuisance handling."""

    matrix: np.ndarray
    nominal_columns: tuple[str, ...]
    active_columns: tuple[str, ...]
    omitted_constant_nuisance_columns: tuple[str, ...]
    rank: int


def resolve_design(
    matrix: np.ndarray,
    column_names: tuple[str, ...],
    *,
    nuisance_columns: tuple[str, ...],
) -> ResolvedDesign:
    """Omit only predesignated nuisance columns constant in the full sample.

    Constancy is exact after the frozen binary/categorical construction. The
    decision is made once on the complete eligible primary sample, not inside
    bootstrap, null, comparator, or robustness replicates. No other column is
    eligible for omission, and any remaining exact rank deficiency is fatal.
    """
    x = np.asarray(matrix, dtype=np.float64)
    names = tuple(column_names)
    nuisance = tuple(nuisance_columns)
    if x.ndim != 2 or x.shape[1] != len(names):
        raise ValueError("matrix width must equal the number of column names")
    if x.shape[0] == 0:
        raise ValueError("the complete eligible primary sample must not be empty")
    if len(set(names)) != len(names):
        raise ValueError("column names must be unique")
    if nuisance != FROZEN_CONSTANT_NUISANCE_COLUMNS:
        raise ValueError(
            "v3 permits only its frozen period_2_indicator nuisance designation"
        )
    if not set(nuisance).issubset(names):
        raise ValueError("the frozen designated nuisance column must exist")
    if not np.isfinite(x).all():
        raise DesignEstimabilityError("the frozen design contains non-finite values")
    if "intercept" not in names or not np.all(x[:, names.index("intercept")] == 1.0):
        raise ValueError("v3 requires its retained all-one intercept column")
    for name in nuisance:
        values = x[:, names.index(name)]
        if not np.all((values == 0.0) | (values == 1.0)):
            raise DesignEstimabilityError(
                f"designated nuisance column is not a frozen binary dummy: {name}"
            )

    omitted = tuple(
        name
        for name in names
        if name in nuisance and np.all(x[:, names.index(name)] == x[0, names.index(name)])
    )
    active = tuple(name for name in names if name not in omitted)
    indices = [names.index(name) for name in active]
    reduced = x[:, indices]
    # Match the frozen estimator's exact rank convention rather than using a
    # separate matrix-rank tolerance.
    _, _, rank, _ = np.linalg.lstsq(
        reduced, np.zeros(reduced.shape[0], dtype=np.float64), rcond=None
    )
    rank = int(rank)
    if rank != reduced.shape[1]:
        raise DesignEstimabilityError(
            f"remaining frozen design is rank deficient: {rank}/{reduced.shape[1]}"
        )
    return ResolvedDesign(
        matrix=reduced,
        nominal_columns=names,
        active_columns=active,
        omitted_constant_nuisance_columns=omitted,
        rank=rank,
    )


def apply_resolved_plan(
    matrix: np.ndarray,
    column_names: tuple[str, ...],
    *,
    plan: ResolvedDesign,
) -> np.ndarray:
    """Apply one complete-sample column plan without rechecking constancy.

    Bootstrap, null, comparator, trim, and descriptive families must use this
    operation rather than resolve their own active columns.
    """
    x = np.asarray(matrix, dtype=np.float64)
    names = tuple(column_names)
    if names != plan.nominal_columns:
        raise ValueError("column names/order must match the frozen complete-sample plan")
    if x.ndim != 2 or x.shape[1] != len(names):
        raise ValueError("matrix width must equal the frozen nominal column count")
    if not np.isfinite(x).all():
        raise DesignEstimabilityError("the planned design contains non-finite values")
    indices = [names.index(name) for name in plan.active_columns]
    return x[:, indices]
