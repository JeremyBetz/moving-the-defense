import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from src.concurrent_defensive_coordination_form_v1 import (
    butterworth_padlen,
    continuous_valid_blocks,
    window_has_physical_edge_support,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/concurrent_defensive_coordination_form_v1.json"
PROTOCOL = ROOT / "docs/protocols/concurrent_defensive_coordination_form_v1.md"
LEDGER = ROOT / "config/concurrent_defensive_coordination_form_v1_hashes.json"


class GovernanceTests(unittest.TestCase):
    def test_frozen_config_matches_measurement(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cfg["status"], "FROZEN_RESULTS_UNOBSERVED")
        self.assertEqual(cfg["preprocessing"]["primary"]["cutoff_hz"], 1.0)
        self.assertEqual(cfg["preprocessing"]["required_sensitivity"]["cutoff_hz"], 1.5)
        self.assertEqual(cfg["support"]["edge_margin_s"], 2.0)
        self.assertEqual(cfg["estimands"]["primary"], "mean_beta_D2_D3_minus_mean_beta_D4_D7")
        self.assertFalse(cfg["classification"]["D1_can_change_status"])
        self.assertEqual(cfg["model"]["columns"], 10 * 7 + 2)

    def test_filter_padding_is_below_two_second_margin(self):
        for hz in (10.0, 25.0):
            for cutoff in (1.0, 1.5):
                padlen = butterworth_padlen(hz, cutoff)
                self.assertEqual(padlen, 15)
                self.assertGreaterEqual(2.0 * hz, padlen)

    def test_native_blocks_split_invalid_frame_and_time_gaps(self):
        frame = np.array([1, 2, 3, 4, 6, 7, 8, 9, 10])
        time = np.array([0, .1, .2, .3, .5, .6, .7, .9, 1.0])
        valid = np.array([1, 1, 0, 1, 1, 1, 1, 1, 1], dtype=bool)
        self.assertEqual(
            continuous_valid_blocks(frame, time, valid, .1),
            [(0, 1), (3, 3), (4, 6), (7, 8)],
        )

    def test_two_second_window_plus_margin_requires_t_minus4_to_t_plus4(self):
        self.assertFalse(window_has_physical_edge_support(0, 10, 2))
        self.assertTrue(window_has_physical_edge_support(0, 10, 4))
        self.assertTrue(window_has_physical_edge_support(0, 10, 6))
        self.assertFalse(window_has_physical_edge_support(0, 10, 8))

    def test_hash_ledger(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        for relative, expected in ledger["frozen_artifacts_sha256"].items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected)
        self.assertFalse(ledger["protected_outcomes_observed"])


if __name__ == "__main__":
    unittest.main()
