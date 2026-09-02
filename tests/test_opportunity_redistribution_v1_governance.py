import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/opportunity_redistribution_v1.json"
LEDGER = ROOT / "config/opportunity_redistribution_v1_hashes.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_design_and_closed_inputs_match_ledger():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    for group in ("frozen_design_sha256", "closed_concurrent_geometry_sha256"):
        assert all(sha(ROOT / name) == expected for name, expected in ledger[group].items())


def test_primary_construct_and_model_are_single_and_explicit():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["opportunity"]["outcome"] == "mean_local_change_in_nearest_defender_separation_minus_mean_remote_change"
    assert config["defensive_predictor"] == "mean_D1_D3_concurrent_focal_relative_path_minus_mean_D4_D7"
    assert config["model"]["primary_estimand"] == "beta_D_column_2"
    assert len(config["model"]["columns_in_order"]) == 6
    assert config["model"]["solver"] == "numpy.linalg.lstsq_rcond_none"


def test_frozen_development_firewall_and_current_heldout_boundaries():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert config["data"]["game2"] == "heldout_unobserved_requires_separate_addendum"
    assert config["data"]["game3"] == "reserved_untouched"
    assert config["data"]["idsse"] == "not_executed"
    assert ledger["firewall"]["opportunity_metric_selected_from_results"] is False
    assert ledger["firewall"]["game1_opportunity_result"] == "not_created_or_inspected"
    result = ROOT / "outputs/opportunity_redistribution_game1_v1/final_results.json"
    metadata = json.loads((ROOT / "outputs/opportunity_redistribution_game1_v1/execution_metadata.json").read_text(encoding="utf-8"))
    assert result.exists()
    assert metadata["results_observed_only_after_design_freeze"] is True
    assert not (ROOT / "outputs/opportunity_redistribution_game2_v1").exists()


def test_status_and_robustness_rules_are_frozen():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["classification"]["evaluation_order"] == ["INVALID", "NEGATIVE", "COHERENT", "MIXED"]
    assert len(config["classification"]["coherent"]) == 6
    assert config["robustness"]["extreme_focal_attacker_path_threshold_m"] == 12.198443079831405
    assert config["bootstrap"]["replicates"] == 2000
    assert config["bootstrap"]["game2_reserved_child_index"] == 1
