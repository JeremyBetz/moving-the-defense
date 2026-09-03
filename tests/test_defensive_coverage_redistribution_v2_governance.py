import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "config" / "defensive_coverage_redistribution_v2_hashes.json"


def test_rejected_v1_and_frozen_v2_hashes_match_ledger():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    governed = {
        **ledger["rejected_v1_sha256"],
        **ledger["frozen_design_sha256"],
        **ledger["design_support_sha256"],
    }
    for relative, expected in governed.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_no_empirical_coverage_output_exists_at_freeze():
    output_root = ROOT / "outputs"
    names = [
        "defensive_coverage_redistribution_v1",
        "defensive_coverage_redistribution_v2",
    ]
    assert not any((output_root / name).exists() for name in names)
