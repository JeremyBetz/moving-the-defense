from __future__ import annotations

import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/spatial_defensive_response_footprint_v1.md"
CONFIG = ROOT / "config/spatial_defensive_response_footprint_v1.json"
CLARIFICATION = ROOT / "docs/protocols/spatial_defensive_response_footprint_v1_execution_clarification.md"
CLARIFICATION_SHA256 = "60678b0f90128c5905ed2535a81aab37b562fe8a6b8aa6a9c9ff1f7642dcf37e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SpatialFootprintExecutionGovernanceTest(unittest.TestCase):
    def test_frozen_scientific_artifacts_unchanged(self):
        self.assertEqual(sha256(PROTOCOL), "649c40c551d880f5204f6ccca7e37cf219660c4a5fdea590e0b73b6377534458")
        self.assertEqual(sha256(CONFIG), "b784b3839146a424acd427a0f1d99959f3ef547039743d30ce90e39f9e557c9c")

    def test_game2_has_no_standalone_classification(self):
        self.assertEqual(sha256(CLARIFICATION), CLARIFICATION_SHA256)
        text = CLARIFICATION.read_text(encoding="utf-8")
        self.assertIn("no Game 2-only coherent/mixed/invalid status may be invented", text)
        self.assertIn("Do not give Game 2 a standalone coherent/mixed/invalid scientific classification", text)

    def test_final_classification_requires_game2_and_pooled_sequence(self):
        text = CLARIFICATION.read_text(encoding="utf-8")
        self.assertIn("After Game 2 is closed, execute the already-authorized pooled footprint analysis", text)
        self.assertIn("Only then assign `FINAL FOOTPRINT A`, `FINAL FOOTPRINT B`, or `FINAL FOOTPRINT C`", text)


if __name__ == "__main__":
    unittest.main()
