from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_coverage_v2_invalid_history_and_closed_v3_result_coexist():
    v2 = json.loads(
        (ROOT / "outputs/defensive_coverage_redistribution_game1_v2/model_results.json")
        .read_text(encoding="utf-8")
    )
    v3 = json.loads(
        (ROOT / "outputs/defensive_coverage_redistribution_game1_v3/model_results.json")
        .read_text(encoding="utf-8")
    )
    assert v2["classification"] == "INVALID"
    assert v2["invalid_reason"] == "frozen design rank failure 11/12"
    assert not {"primary", "bootstrap", "controls"}.intersection(v2)
    assert v3["classification"] == "MIXED"
    assert v3["hard_qc"]["valid"] is True
