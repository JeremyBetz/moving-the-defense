import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/concurrent_defensive_coordination_form_game2_v1"
PROTOCOL = ROOT / "docs/protocols/concurrent_defensive_coordination_form_v1.md"
CONFIG = ROOT / "config/concurrent_defensive_coordination_form_v1.json"
CLARIFICATION = ROOT / "docs/protocols/concurrent_defensive_coordination_form_v1_game2_replication.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_and_prospective_hashes():
    assert digest(PROTOCOL) == "3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032"
    assert digest(CONFIG) == "d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3"
    assert digest(CLARIFICATION) == "b5cec238d04649217a39549587ebfb292278829fb8c9c434ff5ef40b8a2786e9"


def test_result_and_mixed_classification_reproduce():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 2 COORDINATION FORM REPLICATION MIXED"
    assert result["sample"]["eligible_observations"] == 1143
    assert result["sample"]["rows"] == 11430
    assert result["sample"]["unique_anchor_times"] == 123
    assert result["paired_valid_bootstraps"] == 2000
    criteria = result["replication_criteria"]
    assert criteria["valid_execution_and_qc"]
    assert criteria["primary_1hz_positive"]
    assert not criteria["primary_95_percent_interval_strictly_above_zero"]
    assert criteria["sensitivity_1_5hz_positive"]
    assert all(result["hard_qc"].values())


def test_governed_hashes_and_independent_reproduction():
    ledger = json.loads((OUT / "governed_hashes.json").read_text(encoding="utf-8"))
    assert len(ledger) == 8
    for name, expected in ledger.items():
        assert digest(OUT / name) == expected
    reproduction = json.loads((OUT / "reproduction_qc.json").read_text(encoding="utf-8"))
    assert reproduction["status"] == "PASS"
    assert reproduction["all_governed_outputs_byte_identical"]
    assert reproduction["files_compared"] == 8
