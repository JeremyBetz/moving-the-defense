from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from attacking_continuous_movement_game2_v1 import (  # noqa: E402
    GRID_S,
    MATCH_ID,
    WINDOWS,
    verify_stage_a,
)


class Game2ContinuousMovementV1Test(unittest.TestCase):
    def test_frozen_representation_constants(self):
        self.assertEqual(MATCH_ID, "metrica:sample-game-2")
        self.assertEqual(WINDOWS, (1.0, 2.0, 4.0))
        self.assertEqual(GRID_S, 0.20)

    def test_frozen_stage_a_artifacts_validate(self):
        result = verify_stage_a()
        self.assertEqual(result["classification"], "READY")
        self.assertTrue(result["governed_hashes_valid"])
        self.assertTrue(result["independent_reproduction_valid"])
        self.assertEqual(result["valid_raw_rows"], 2_093_028)
        self.assertEqual(result["support_segments"], 134)


if __name__ == "__main__":
    unittest.main()
