from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import research_execution_governance as governance  # noqa: E402


class ExecutionGovernanceTest(unittest.TestCase):
    def test_current_checkpoint(self):
        result = governance.verify_checkpoint()
        self.assertTrue(result["pass"])
        self.assertEqual(result["scientific_state"], "FINAL RESPONSE FORM B")

    def test_checkpoint_detects_hash_and_forbidden_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "artifact.txt").write_text("fixed\n", encoding="utf-8")
            expected = hashlib.sha256(b"fixed\n").hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "required_sha256": {"artifact.txt": expected},
                "forbidden_output_globs": ["outputs/*game2*"],
            }), encoding="utf-8")
            self.assertTrue(governance.verify_checkpoint(manifest, root)["pass"])
            (root / "outputs").mkdir()
            (root / "outputs/result_game2.json").write_text("{}", encoding="utf-8")
            self.assertFalse(governance.verify_checkpoint(manifest, root)["pass"])
            (root / "artifact.txt").write_text("changed\n", encoding="utf-8")
            self.assertFalse(governance.verify_checkpoint(manifest, root)["pass"])

    def test_hash_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact = root / "a.json"
            artifact.write_text("{}\n", encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            ledger = root / "ledger.json"
            ledger.write_text(json.dumps({"a.json": digest}), encoding="utf-8")
            self.assertTrue(governance.verify_hash_ledger(root, ledger)["pass"])
            artifact.write_text("{\"changed\": true}\n", encoding="utf-8")
            self.assertFalse(governance.verify_hash_ledger(root, ledger)["pass"])


if __name__ == "__main__":
    unittest.main()
