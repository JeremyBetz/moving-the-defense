from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1_idsse_replication.json"
LEDGER = ROOT / "config/concurrent_attacker_defensive_geometry_v1_idsse_replication_hashes.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def classify(valid: bool, pooled: float, lower: float, positive_matches: int, trimmed: float, retained: float) -> str:
    if not valid:
        return "INVALID"
    if pooled <= 0 or positive_matches <= 3:
        return "NOT_SUPPORTED"
    if lower > 0 and positive_matches >= 5 and trimmed > 0 and retained >= 0.5:
        return "SUPPORTED"
    return "MIXED"


class IDSSEConcurrentGeometryGovernanceTest(unittest.TestCase):
    def test_frozen_artifact_hashes_match(self) -> None:
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        for name, expected in {
            **ledger["frozen_replication_artifacts_sha256"],
            **ledger["closed_and_inherited_artifacts_sha256"],
        }.items():
            self.assertEqual(digest(ROOT / name), expected)

    def test_construct_and_model_are_inherited_unchanged(self) -> None:
        config = load_config()
        self.assertEqual(config["primary_estimand"], "mean_D1_D3_concurrent_attacker_path_beta_minus_mean_D4_D7_beta")
        self.assertEqual(config["inheritance"]["model"], "unchanged_72_column_float64_stacked_rank_specific_OLS")
        self.assertEqual(config["pooled"]["model"], "same_unweighted_72_column_stacked_model")
        self.assertFalse(config["pooled"]["match_indicators"])
        self.assertFalse(config["pooled"]["match_interactions"])

    def test_all_seven_matches_are_governed_and_equivalence_is_mandatory(self) -> None:
        config = load_config()
        self.assertEqual(config["matches"], ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9"])
        self.assertTrue(config["equivalence_gate"]["required_for_every_match_before_outcomes"])
        self.assertEqual(config["equivalence_gate"]["failure_policy"], "IDSSE_EXTERNAL_REPLICATION_INVALID_no_match_dropped")
        self.assertEqual(config["adapter"]["interpolation"], "none")

    def test_status_logic_is_exhaustive_and_key_boundaries_are_fixed(self) -> None:
        self.assertEqual(classify(False, 1, 1, 7, 1, 1), "INVALID")
        self.assertEqual(classify(True, 0, -1, 7, 1, 1), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 3, 1, 1), "NOT_SUPPORTED")
        self.assertEqual(classify(True, 1, 0.1, 5, 1, 0.5), "SUPPORTED")
        self.assertEqual(classify(True, 1, 0, 7, 1, 1), "MIXED")
        self.assertEqual(classify(True, 1, 0.1, 4, 1, 1), "MIXED")
        self.assertEqual(classify(True, 1, 0.1, 7, -0.1, 1), "MIXED")

    def test_bootstrap_and_secondary_role_are_frozen(self) -> None:
        config = load_config()
        bootstrap = config["bootstrap"]
        self.assertEqual((bootstrap["replicates"], bootstrap["minimum_valid"], bootstrap["block_seconds"]), (2000, 1900, 60))
        self.assertEqual(set(bootstrap["match_child_indices"].values()), set(range(7)))
        self.assertEqual(bootstrap["pooled_child_index"], 7)
        self.assertEqual(config["secondary_deformation"]["classification_effect"], "none")

    def test_any_empirical_result_is_post_freeze_and_governed(self) -> None:
        output = ROOT / "outputs/concurrent_attacker_defensive_geometry_idsse_v1"
        if not output.exists():
            return
        manifest = json.loads((output / "execution_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["starting_commit"], "887e1adcd37aa9f53ce0a101dc94f08d3680c7d5")
        self.assertTrue(manifest["results_observed_after_freeze"])
        self.assertTrue(manifest["game3_untouched"])


if __name__ == "__main__":
    unittest.main()
