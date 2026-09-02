import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/opportunity_redistribution_game1_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_inputs_and_closed_result_hashes():
    expected = {
        "docs/protocols/opportunity_redistribution_v1.md": "15825647a23c4cfcb24317e773d07a8c17cbb5d705b8c7eafd07493f728625fa",
        "config/opportunity_redistribution_v1.json": "45c418a9b52565298da184f32250dab190df2e62030d4f42fde7408c3523e431",
        "config/opportunity_redistribution_v1_hashes.json": "aa5cba169e330bcea2b280b269e0bd075af7c0eca3e6f7eac879317587259c49",
        "outputs/opportunity_redistribution_game1_v1/final_results.json": "215cea1c83efb5d542c9ffc8a0c59c227a07b695c118b97cc05bbf14dc340656",
    }
    assert all(sha(ROOT / name) == digest for name, digest in expected.items())
    ledger = json.loads((OUT / "result_hashes.json").read_text(encoding="utf-8"))
    assert all(sha(OUT / name) == digest for name, digest in ledger.items())


def test_negative_status_sample_and_period2_diagnosis():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT NEGATIVE"
    assert result["sample"]["eligible_focal_attacker_observations"] == 5750
    assert result["sample"]["period_counts"] == {"1": 5750}
    diagnosis = result["sample"]["period2_support_diagnosis"]
    assert diagnosis["classification"] == "PERIOD-2 EXCLUSION CORRECT UNDER FROZEN RULES"
    assert diagnosis["maximum_supported_outfield_players_per_team"] == 9


def test_primary_coefficient_and_robustness_reconstruct():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    primary = pd.read_csv(OUT / "primary_coefficients.csv").set_index("predictor")
    assert primary.loc["D", "estimate"] < 0
    assert abs(primary.loc["D", "estimate"] - result["coefficients"]["primary"][1]["estimate"]) < 1e-15
    assert result["robustness_positive_signs"] == {"fixed_start": True, "three_nearest": False, "trimmed": False}
    assert all(rank == 6 for rank in result["design_rank"].values())
    assert all(item["valid"] == item["attempted"] == 2000 for item in result["bootstrap"].values())


def test_hard_qc_and_reproduction_pass():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    reproduction = json.loads((OUT / "reproduction_qc.json").read_text(encoding="utf-8"))
    assert all(result["hard_qc"].values())
    assert reproduction["all_pass"]
    assert reproduction["byte_identical"] == reproduction["governed_outputs"] == 9
