from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_idsse_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IDSSEConcurrentGeometryResultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))

    def test_frozen_status_and_sign_pattern(self) -> None:
        self.assertEqual(self.result["status"], "IDSSE EXTERNAL REPLICATION SUPPORTED")
        self.assertEqual(self.result["positive_match_estimates"], 7)
        self.assertGreater(self.result["pooled"]["near_minus_middle"]["ci_low"], 0)
        self.assertGreaterEqual(self.result["pooled"]["trimmed_near_minus_middle"]["retained_magnitude_fraction"], 0.5)

    def test_all_match_models_and_bootstraps_are_valid(self) -> None:
        self.assertEqual(set(self.result["match_results"]), {"J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9"})
        for match in self.result["match_results"].values():
            self.assertEqual(match["design_rank"], 72)
            self.assertGreater(match["near_minus_middle"]["estimate"], 0)
            self.assertGreaterEqual(min(match["bootstrap_valid"].values()), 1900)

    def test_hard_qc_and_equivalence_pass(self) -> None:
        self.assertTrue(all(self.result["hard_qc"].values()))
        self.assertTrue(all(row["passed"] for row in self.result["provider_equivalence"]))

    def test_reproduction_and_hash_ledgers(self) -> None:
        reproduction = json.loads((OUT / "reproduction.json").read_text(encoding="utf-8"))
        self.assertTrue(reproduction["all_governed_outputs_byte_identical"])
        self.assertEqual(reproduction["files_compared"], 6)
        hashes = json.loads((OUT / "final_hashes.json").read_text(encoding="utf-8"))
        for name, expected in hashes.items():
            self.assertEqual(sha(OUT / name), expected)


if __name__ == "__main__":
    unittest.main()
