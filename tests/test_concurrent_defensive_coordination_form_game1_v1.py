import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/concurrent_defensive_coordination_form_game1_v1"


def test_governed_result_and_frozen_classification():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 1 COORDINATION FORM DEVELOPMENT COHERENT"
    assert result["sample"]["eligible_observations"] == 8261
    assert result["sample"]["rows"] == 82610
    assert result["sample"]["unique_anchor_times"] == 849
    assert result["paired_valid_bootstraps"] == 2000
    assert result["primary"]["primary_D2_D3_minus_D4_D7"] > 0
    assert min(result["primary_contrast_ci95"]) > 0
    assert result["sensitivity"]["primary_D2_D3_minus_D4_D7"] > 0
    assert all(result["hard_qc"].values())


def test_governed_hash_ledger():
    ledger = json.loads((OUT / "governed_hashes.json").read_text(encoding="utf-8"))
    assert len(ledger) == 8
    for name, expected in ledger.items():
        assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == expected


def test_independent_reproduction_record():
    qc = json.loads((OUT / "reproduction_qc.json").read_text(encoding="utf-8"))
    assert qc["status"] == "PASS"
    assert qc["independent_rerun"] is True
    assert qc["governed_files_byte_identical"] == qc["governed_files_total"] == 8
    assert qc["governed_hash_ledger_byte_identical"] is True
