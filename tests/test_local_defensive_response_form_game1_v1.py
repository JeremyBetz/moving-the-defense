from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import local_defensive_response_form_game1_v1 as execution  # noqa: E402


class ResponseFormGame1ExecutionTest(unittest.TestCase):
    def test_frozen_hashes_and_governance(self):
        self.assertTrue(all(execution.sha256(path) == expected for path, expected in execution.HASHES.items()))
        self.assertEqual((execution.BOOTSTRAPS, execution.MIN_VALID, execution.CHILD_INDEX), (2000, 1900, 6))
        self.assertEqual(execution.REGIONS, {"near": [1, 2, 3], "middle": [4, 5, 6, 7], "far": [8, 9, 10]})

    def test_region_identity(self):
        result = execution.regions(np.arange(1, 11, dtype=float))
        self.assertAlmostEqual(result["near"], 2.0)
        self.assertAlmostEqual(result["middle"], 5.5)
        self.assertAlmostEqual(result["far"], 9.0)
        self.assertAlmostEqual(result["near_minus_middle"], -3.5)

    def test_design_and_rank_fit_fixture(self):
        rows = []
        for rank in range(1, 11):
            for i in range(12):
                x = float(i)
                baseline = float(i * i / 30)
                centroid = float(np.sin(i))
                rows.append({
                    "distance_rank": rank,
                    "x": x,
                    "baseline": baseline,
                    "prior_centroid_path_m": centroid,
                    "y": 1 + rank / 100 + 0.4 * x + 0.2 * baseline - 0.1 * centroid,
                })
        import pandas as pd
        beta = execution.fit_ranks(pd.DataFrame(rows), "y", "x", "baseline")
        np.testing.assert_allclose(beta, np.repeat(0.4, 10), atol=1e-12)


if __name__ == "__main__":
    unittest.main()
