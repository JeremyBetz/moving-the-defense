from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1_game2_replication.json"
LEDGER = ROOT / "config/concurrent_attacker_defensive_geometry_v1_game2_replication_hashes.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_replication_and_inherited_hashes_match():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    for name, expected in {**ledger["frozen_replication_artifacts_sha256"], **ledger["closed_and_inherited_artifacts_sha256"]}.items():
        assert digest(ROOT / name) == expected


def test_only_original_primary_estimand_classifies():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["primary_estimand"] == "mean_D1_D3_concurrent_attacker_path_beta_minus_mean_D4_D7_beta"
    assert "D1_specific_gate" in config["prohibitions"]
    assert "near_far_gate" in config["prohibitions"]
    assert "monotonicity_gate" in config["prohibitions"]
    assert config["descriptive_only"][:4] == [
        "D1_is_largest", "near_elevation_concentrated_at_D1", "far_exceeds_middle", "monotonic_rank_shape"
    ]


def test_status_logic_is_complete_and_null_is_not_invalid():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    classification = config["classification"]
    assert classification["evaluation_order"] == ["INVALID", "NOT_SUPPORTED", "SUPPORTED", "MIXED"]
    assert classification["not_supported"] == "valid_execution_and_primary_near_minus_middle_point_estimate_nonpositive"
    assert len(classification["statuses"]) == len(set(classification["statuses"])) == 4


def test_heldout_bootstrap_and_closure_are_tier3():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["bootstrap"] == {
        "block_seconds": 60,
        "child_index": 1,
        "grouping": "complete_D1_D10_vector_and_all_simultaneous_attackers",
        "interval_percent": 95.0,
        "master_seed": 20260831,
        "minimum_valid": 1900,
        "replicates": 2000,
        "spawn_count": 2,
        "terminal_partial_blocks": "retained",
    }
    assert config["closure"]["tier"] == 3
    assert config["closure"]["independent_complete_reproduction"] is True
    assert config["closure"]["pooled_analysis"] == "prohibited"


def test_no_game2_result_exists_at_freeze():
    assert not (ROOT / "outputs/concurrent_attacker_defensive_geometry_game2_v1").exists()
