from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import local_defensive_response_form_pooled_v1 as pooled  # noqa: E402


class ResponseFormPooledMechanicsTest(unittest.TestCase):
    def test_design_matrix_and_match_indicator(self):
        rank = np.repeat(np.arange(1, 11), 2)
        game = np.tile([0.0, 1.0], 10)
        design = pooled.pooled_design(np.ones(20), np.full(20, 2.0), np.full(20, 3.0), rank, game)
        self.assertEqual(design.shape, (20, 41))
        np.testing.assert_array_equal(design[:, -1], game)
        self.assertEqual(int(np.count_nonzero(design[0, :-1])), 4)
        self.assertEqual(int(np.count_nonzero(design[2, :-1])), 4)
        self.assertFalse(np.array_equal(np.flatnonzero(design[0, :-1]), np.flatnonzero(design[2, :-1])))

    def test_observation_weighting_has_no_balance_weights(self):
        rank = [1] * 5 + [1] * 2
        design = pooled.pooled_design(range(7), np.zeros(7), np.zeros(7), rank, [0] * 5 + [1] * 2)
        self.assertEqual(design.shape[0], 7)
        np.testing.assert_array_equal(design[:, 40], [0, 0, 0, 0, 0, 1, 1])

    def test_common_sample_requires_same_complete_units(self):
        rows = []
        for oid in ["keep", "bad_control", "incomplete"]:
            stop = 9 if oid == "incomplete" else 10
            for rank in range(1, stop + 1):
                rows.append({
                    "observation_id": oid,
                    "distance_rank": rank,
                    "primary_axis_valid": True,
                    "control_axis_valid": not (oid == "bad_control" and rank == 4),
                    "primary_support_valid": True,
                    "control_support_valid": True,
                })
        self.assertEqual(pooled.common_sample_ids(pd.DataFrame(rows)), ["keep"])

    def test_regional_and_paired_reconstruction(self):
        primary = np.arange(1, 11, dtype=float)
        control = primary - np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        self.assertAlmostEqual(pooled.regional_contrasts(primary)["near_minus_middle"], -3.5)
        self.assertAlmostEqual(pooled.paired_excess(primary, control), 1.0)

    def test_block_bootstrap_deterministic_and_match_stratified(self):
        anchors = pd.DataFrame({
            "game": ["G1"] * 5 + ["G2"] * 3,
            "period": [1, 1, 1, 2, 2, 1, 1, 2],
            "block_id": [0, 0, 1, 0, 1, 0, 1, 0],
        })
        a = pooled.sample_pooled_anchor_indices(anchors, np.random.default_rng(42))
        b = pooled.sample_pooled_anchor_indices(anchors, np.random.default_rng(42))
        np.testing.assert_array_equal(a, b)
        sampled = anchors.loc[a]
        self.assertEqual(set(sampled["game"]), {"G1", "G2"})
        self.assertEqual(set(zip(sampled["game"], sampled["period"])), {("G1", 1), ("G1", 2), ("G2", 1), ("G2", 2)})


if __name__ == "__main__":
    unittest.main()
