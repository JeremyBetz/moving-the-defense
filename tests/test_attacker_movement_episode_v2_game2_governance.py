import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "attacker_movement_episode_v2_game2_replication.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_game1_and_support_hashes_match() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    paths = {
        "protocol_sha256": ROOT / "docs/protocols/attacker_movement_episode_v2.md",
        "configuration_sha256": ROOT / "config/attacker_movement_episode_v2.json",
        "game1_result_sha256": ROOT / "outputs/attacker_movement_episode_v2_game1/results.json",
        "game1_ledger_sha256": ROOT / "outputs/attacker_movement_episode_v2_game1/hashes.json",
    }
    for key, path in paths.items():
        assert sha256(path) == cfg["inheritance"][key]
    support_paths = {
        "valid_support_segments_sha256": ROOT / "outputs/attacking_continuous_movement_game2_stage_a/valid_support_segments.csv",
        "trajectory_validity_registry_sha256": ROOT / "outputs/attacking_continuous_movement_game2_stage_a/trajectory_validity_registry.csv",
        "stage_a_result_sha256": ROOT / "outputs/attacking_continuous_movement_game2_stage_a/stage_a_result.json",
        "stage_a_governed_hashes_sha256": ROOT / "outputs/attacking_continuous_movement_game2_stage_a/governed_output_hashes.json",
    }
    for key, path in support_paths.items():
        assert sha256(path) == cfg["support"][key]


def test_replication_rules_are_prospective_and_immutable() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["status"] == "frozen_before_game2_v2_execution"
    assert cfg["replication_gates"] == {
        "fragmentation_relative_reduction_pct_min": 20.0,
        "merging_direction_pct_max": 3.97,
        "lower_speed_coverage_share_min": 0.368955525083439,
        "objective_audit_checks_required": True,
        "deterministic_reproduction_required": True,
        "no_post_result_tuning_required": True,
    }
    assert not any(cfg["firewall"].values())
    assert cfg["support"]["interpolation"] is False


def test_governance_records_pre_result_freeze() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    protocol = (ROOT / "docs/protocols/attacker_movement_episode_v2_game2_replication.md").read_text(encoding="utf-8")
    assert cfg["starting_commit"] == "35e22081c2697be2b3773986c7745815bf2ce317"
    assert "No Game 2 v2 result existed or had been inspected" in protocol


def test_closed_result_matches_frozen_decision_tree() -> None:
    result = json.loads((ROOT / "outputs/attacker_movement_episode_v2_game2/results.json").read_text(encoding="utf-8"))
    reproduction = json.loads((ROOT / "outputs/attacker_movement_episode_v2_game2/reproduction_verification.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 2 ATTACKER EPISODE v2 REPLICATION MIXED"
    assert result["gates"]["fragmentation_relative_reduction"] is True
    assert result["gates"]["merging_direction"] is True
    assert result["gates"]["lower_speed_coverage"] is True
    assert result["gates"]["objective_audit"] is False
    assert reproduction["all_governed_outputs_byte_identical"] is True
