import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_response_expectation_v1_design import (  # noqa: E402
    contiguous_block_folds,
    local_response_contrast,
    synthetic_design_ranks,
    treatment_columns,
)


def test_local_response_contrast_is_exact_group_difference():
    ranks = np.arange(1.0, 11.0)
    assert local_response_contrast(ranks) == pytest.approx(2.5 - 5.5)


def test_local_response_contrast_requires_complete_vector():
    with pytest.raises(ValueError):
        local_response_contrast(np.arange(9.0))


def test_contiguous_fold_assignment_is_deterministic_and_ordered():
    blocks = [(1, value) for value in range(11)]
    assigned = contiguous_block_folds(blocks)
    assert assigned.tolist() == [0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4]


def test_treatment_coding_uses_lexical_reference():
    encoded = treatment_columns(["b", "a", "c"])
    np.testing.assert_array_equal(encoded, [[1, 0], [0, 0], [0, 1]])


def test_nested_synthetic_designs_are_full_rank():
    ranks = synthetic_design_ranks()
    assert ranks["E0"] < ranks["E1"] < ranks["E2a"] < ranks["E2b"]
