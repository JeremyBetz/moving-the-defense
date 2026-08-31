from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from attacking_continuous_movement_game1_v1 import (  # noqa: E402
    cumulative_path,
    geometry,
    run_fixtures,
    smooth_positions,
)


class ContinuousAttackingMovementV1Test(unittest.TestCase):
    def test_zero_path_is_null_not_zero_or_one(self):
        positions = np.ones((51, 2), dtype=np.float64)
        result = geometry(positions, cumulative_path(positions), 0, 50)
        self.assertEqual(result["delta_x_m"], 0.0)
        self.assertEqual(result["delta_y_m"], 0.0)
        self.assertEqual(result["path_length_m"], 0.0)
        self.assertIsNone(result["straightness"])
        self.assertFalse(result["straightness_valid"])

    def test_positive_path_zero_displacement_is_valid_zero(self):
        x = np.r_[np.linspace(0, 1, 26), np.linspace(0.96, 0, 25)]
        positions = np.column_stack([x, np.zeros(len(x))])
        result = geometry(positions, cumulative_path(positions), 0, 50)
        self.assertGreater(result["path_length_m"], 0)
        self.assertEqual(result["displacement_m"], 0.0)
        self.assertEqual(result["straightness"], 0.0)
        self.assertTrue(result["straightness_valid"])

    def test_centered_seven_frame_mean_has_exact_edges(self):
        raw = np.column_stack([2 * np.arange(20) + 1, -np.arange(20) + 3]).astype(float)
        smoothed = smooth_positions(raw)
        self.assertEqual(len(smoothed), 14)
        np.testing.assert_allclose(smoothed, raw[3:-3], atol=1e-12, rtol=0)

    def test_all_frozen_fixtures_and_invariances(self):
        fixtures, invariance = run_fixtures()
        self.assertTrue(fixtures["pass"].all())
        self.assertTrue(invariance["pass"].all())


if __name__ == "__main__":
    unittest.main()
