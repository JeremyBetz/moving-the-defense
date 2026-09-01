from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import local_defensive_deformation_game2_v1 as execution  # noqa: E402


class LocalDefensiveDeformationGame2ExecutionTest(unittest.TestCase):
    def test_frozen_hashes_and_child_stream(self):
        self.assertTrue(all(execution.g1.sha(path) == expected for path, expected in execution.HASHES.items()))
        self.assertEqual(execution.CHILD, 7)

    def test_closed_result_is_unclassified_and_not_pooled(self):
        result = json.loads(
            (ROOT / "outputs/local_defensive_deformation_game2_v1/final_results.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result["status"], "GAME 2 HELDOUT REPLICATION — STANDALONE UNCLASSIFIED")
        self.assertTrue(result["hard_qc"]["pooled_not_executed"])
        self.assertFalse(result["replication_conditions"]["paired_excess_positive"])

    def test_reproduction_record(self):
        reproduction = json.loads(
            (ROOT / "outputs/local_defensive_deformation_game2_v1/reproduction.json").read_text(encoding="utf-8")
        )
        self.assertEqual(reproduction["governed_outputs_compared"], 13)
        self.assertTrue(reproduction["byte_identical"])


if __name__ == "__main__":
    unittest.main()
