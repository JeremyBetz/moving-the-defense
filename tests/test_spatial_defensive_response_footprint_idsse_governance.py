from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/spatial_defensive_response_footprint_v1_idsse_external_replication.json"
LEDGER = ROOT / "config/spatial_defensive_response_footprint_v1_idsse_external_replication_hashes.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def classify(valid: bool, primary: float, primary_lower: float, primary_positive_matches: int,
             paired: float, paired_lower: float, paired_positive_matches: int,
             trimmed: float, retained: float, horizons_reverse: bool) -> str:
    if not valid:
        return "INVALID"
    if primary <= 0 or primary_positive_matches <= 3 or paired <= 0 or paired_positive_matches <= 3:
        return "NOT_SUPPORTED"
    if (primary_lower > 0 and primary_positive_matches >= 5 and paired_lower > 0
            and paired_positive_matches >= 5 and trimmed > 0 and retained >= 0.5
            and not horizons_reverse):
        return "SUPPORTED"
    return "MIXED"


class IDSSETemporalFootprintGovernanceTest(unittest.TestCase):
    def test_frozen_artifact_hashes_match(self) -> None:
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        for name, expected in {
            **ledger["frozen_replication_artifacts_sha256"],
            **ledger["closed_and_inherited_artifacts_sha256"],
        }.items():
            self.assertEqual(digest(ROOT / name), expected)

    def test_closed_time_order_rank_groups_and_adapter_are_fixed(self) -> None:
        config = load_config()
        self.assertEqual(config["timing"]["prior_context_seconds"], [-4.0, -2.0])
        self.assertEqual(config["timing"]["attacker_exposure_seconds"], [-2.0, 0.0])
        self.assertEqual(config["timing"]["primary_response_seconds"], [0.0, 2.0])
        self.assertEqual(config["support_and_ranks"]["regions"], {"near": [1, 2, 3], "middle": [4, 5, 6, 7], "far_descriptive": [8, 9, 10]})
        self.assertEqual(config["adapter"]["required_native_frame_rate_hz"], 25)
        self.assertEqual(config["adapter"]["interpolation"], "none")

    def test_all_matches_equivalence_and_grouped_bootstrap_are_governed(self) -> None:
        config = load_config()
        self.assertEqual(config["matches"], ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9"])
        self.assertTrue(config["equivalence_gate"]["required_for_every_match_before_outcomes"])
        self.assertEqual(config["equivalence_gate"]["failure_policy"], "IDSSE_TEMPORAL_FOOTPRINT_EXTERNAL_REPLICATION_INVALID_no_match_dropped")
        bootstrap = config["bootstrap"]
        self.assertEqual((bootstrap["replicates"], bootstrap["minimum_valid"], bootstrap["block_seconds"]), (2000, 1900, 60.0))
        self.assertEqual(set(bootstrap["match_child_indices"].values()), set(range(7)))
        self.assertEqual(bootstrap["pooled_child_index"], 7)

    def test_status_logic_is_exhaustive_and_requires_temporal_excess(self) -> None:
        self.assertEqual(classify(False, 1, 1, 7, 1, 1, 7, 1, 1, False), "INVALID")
        self.assertEqual(classify(True, 0, -1, 7, 1, 1, 7, 1, 1, False), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 3, 1, 1, 7, 1, 1, False), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 7, 0, -1, 7, 1, 1, False), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 7, 1, 0.1, 3, 1, 1, False), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 5, 1, 0.1, 5, 1, 0.5, False), "SUPPORTED")
        self.assertEqual(classify(True, 1, 0, 7, 1, 0.1, 7, 1, 1, False), "MIXED")
        self.assertEqual(classify(True, 1, 0.1, 7, 1, 0, 7, 1, 1, False), "MIXED")
        self.assertEqual(classify(True, 1, 0.1, 7, 1, 0.1, 7, 1, 1, True), "MIXED")

    def test_provider_derived_row_outputs_remain_ignored(self) -> None:
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("outputs/spatial_defensive_response_footprint_idsse_v1/observation_rows.parquet", ignored)
        self.assertIn("outputs/spatial_defensive_response_footprint_idsse_v1/_stage/", ignored)


if __name__ == "__main__":
    unittest.main()
