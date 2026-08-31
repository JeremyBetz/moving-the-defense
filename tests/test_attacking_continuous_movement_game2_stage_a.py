from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from attacking_continuous_movement_game2_stage_a import (  # noqa: E402
    exact_duplicate_runs,
    hard_jump_invalid_mask,
    true_runs,
)


class Game2StageASupportTest(unittest.TestCase):
    def test_single_hard_link_invalidates_only_endpoints(self):
        actual = hard_jump_invalid_mask(np.array([4]), 9)
        expected = np.zeros(9, dtype=bool)
        expected[3:5] = True
        np.testing.assert_array_equal(actual, expected)

    def test_two_hard_links_in_one_observed_run_invalidate_bounded_segment(self):
        actual = hard_jump_invalid_mask(np.array([3, 7]), 10)
        expected = np.zeros(10, dtype=bool)
        expected[2:8] = True
        np.testing.assert_array_equal(actual, expected)

    def test_hard_links_do_not_bound_across_support_break(self):
        base = np.ones(10, dtype=bool)
        base[5] = False
        continuity = np.ones(10, dtype=bool)
        continuity[5] = False
        continuity[6] = False
        actual = hard_jump_invalid_mask(np.array([3, 8]), 10, base, continuity)
        expected = np.zeros(10, dtype=bool)
        expected[2:4] = True
        expected[7:9] = True
        np.testing.assert_array_equal(actual, expected)

    def test_exact_duplicate_requires_consecutive_support(self):
        common = {
            "base_valid": np.ones(8, dtype=bool),
            "continuity": np.r_[False, np.ones(7, dtype=bool)],
            "x_m": np.arange(8, dtype=float),
            "y_m": np.zeros(8, dtype=float),
        }
        other = {name: value.copy() for name, value in common.items()}
        other["continuity"][4] = False
        self.assertEqual(exact_duplicate_runs(common, other), [(0, 3), (4, 7)])

    def test_true_runs_split_on_incoming_discontinuity(self):
        mask = np.array([True, True, True, True])
        continuity = np.array([False, True, False, True])
        self.assertEqual(true_runs(mask, continuity), [(0, 1), (2, 3)])


if __name__ == "__main__":
    unittest.main()
