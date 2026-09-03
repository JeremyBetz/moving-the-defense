import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "config/defensive_coverage_redistribution_v3_hashes.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v3_hash_ledger_and_frozen_lineage():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    for group in ("preserved_v1_v2", "v2_invalid_closure", "v3_frozen_design"):
        for relative, expected in ledger[group].items():
            assert _sha(ROOT / relative) == expected, relative


def test_v3_allows_only_period_indicator_as_constant_nuisance():
    config = json.loads(
        (ROOT / "config/defensive_coverage_redistribution_v3.json").read_text(
            encoding="utf-8"
        )
    )
    rule = config["constant_nuisance_rule"]
    assert rule["designated_non_scientific_nuisance_columns"] == [
        "period_2_indicator"
    ]
    assert rule["decision_sample"] == "complete realized eligible primary sample"
    assert rule["reuse_active_columns_everywhere"] is True
    assert rule["remaining_estimator_rank_deficiency"] == "INVALID"
    assert "primary predictor" in rule["never_omit"]
    assert "scientific covariate" in rule["never_omit"]


def test_v2_invalid_closure_exists_without_protected_results_and_v3_is_unexecuted():
    v2 = json.loads(
        (ROOT / "outputs/defensive_coverage_redistribution_game1_v2/model_results.json")
        .read_text(encoding="utf-8")
    )
    assert v2["classification"] == "INVALID"
    assert v2["invalid_reason"] == "frozen design rank failure 11/12"
    assert not {"primary", "bootstrap", "controls"}.intersection(v2)
    assert not (ROOT / "outputs/defensive_coverage_redistribution_game1_v3").exists()
