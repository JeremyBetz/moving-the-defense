"""Tests for bounded static paper-firewall and changed-artifact checks."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import repository_policy as policy  # noqa: E402


def _policy(entrypoint: str = "src/paper.py") -> dict:
    return {
        "current_paper_entrypoints": [entrypoint],
        "protected_module_prefixes": ["protected_module"],
        "protected_path_prefixes": ["data/metrica_sample_game_3/"],
        "protected_path_substrings": [],
        "artifact_policy": {
            "allowed_data_paths": ["data/.gitkeep"],
            "max_changed_file_bytes": 10 * 1024 * 1024,
            "raw_filename_substrings": ["RawTrackingData", "RawEventsData", "raw_tracking"],
            "reconstructive_name_substrings": ["observation_rows", "eligibility_ledger", "heldout_predictions", "prediction_rows", "residual_rows", "player_rows"],
            "exceptions": [],
        },
    }


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for relative, content in files.items():
        path = tmp_path / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding="utf-8")
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "config" / "repository_policy.json").write_text(json.dumps(_policy()), encoding="utf-8")
    return tmp_path


def _blocking(findings: list[policy.Finding]) -> list[policy.Finding]:
    return [finding for finding in findings if finding.blocking]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_current_paper_import_graph_has_no_blocking_findings():
    assert _blocking(policy.audit_current_paper(ROOT)) == []


def test_current_paper_import_graph_rejects_transitive_protected_module(tmp_path):
    root = _tree(tmp_path, {"src/paper.py": "import helper\n", "src/helper.py": "import protected_module.submodule\n"})
    assert _blocking(policy.audit_current_paper(root, _policy())) == [policy.Finding("protected_module", "src/helper.py", "protected_module.submodule")]


def test_current_paper_import_graph_traverses_relative_import_forms(tmp_path):
    root = _tree(tmp_path, {
        "src/pkg/paper.py": "from . import helper\n",
        "src/pkg/helper.py": "from .nested import x\n",
        "src/pkg/nested.py": "import protected_module\n",
    })
    findings = policy.audit_current_paper(root, _policy("src/pkg/paper.py"))
    assert _blocking(findings) == [policy.Finding("protected_module", "src/pkg/nested.py", "protected_module")]


def test_current_paper_import_graph_traverses_from_relative_module_import(tmp_path):
    root = _tree(tmp_path, {
        "src/pkg/paper.py": "from .helper import x\n",
        "src/pkg/helper.py": "import protected_module\n",
    })
    findings = policy.audit_current_paper(root, _policy("src/pkg/paper.py"))
    assert _blocking(findings) == [policy.Finding("protected_module", "src/pkg/helper.py", "protected_module")]


def test_current_paper_import_graph_traverses_nested_relative_import(tmp_path):
    root = _tree(tmp_path, {
        "src/pkg/nested/paper.py": "from .. import helper\n",
        "src/pkg/helper.py": "import protected_module\n",
    })
    findings = policy.audit_current_paper(root, _policy("src/pkg/nested/paper.py"))
    assert _blocking(findings) == [policy.Finding("protected_module", "src/pkg/helper.py", "protected_module")]


def test_current_paper_missing_configured_entrypoint_fails_closed(tmp_path):
    root = _tree(tmp_path, {})
    findings = policy.audit_current_paper(root, _policy("src/missing.py"))
    assert findings == [policy.Finding("missing_entrypoint", "src/missing.py", "configured current-paper entry point does not exist")]


def test_current_paper_path_guard_resolves_path_expression_forms(tmp_path):
    cases = {
        "concat": "from pathlib import Path\nPath('data/' + 'metrica_sample_game_3/raw.csv').read_text()\n",
        "fstring": "from pathlib import Path\nPath(f\"data/{'metrica_sample_game_3'}/raw.csv\").read_text()\n",
        "slash": "from pathlib import Path\nROOT = Path('.')\nPath(ROOT / 'data' / 'metrica_sample_game_3' / 'raw.csv').read_text()\n",
        "path_open": "from pathlib import Path\nPath('data/metrica_sample_game_3/raw.csv').open('rb')\n",
        "keyword_reader": "import pandas as pd\npd.read_csv(filepath_or_buffer='data/metrica_sample_game_3/raw.csv')\n",
    }
    for name, source in cases.items():
        root = _tree(tmp_path / name, {"src/paper.py": source})
        assert _blocking(policy.audit_current_paper(root, _policy())) == [policy.Finding("protected_read_path", "src/paper.py", "data/metrica_sample_game_3/raw.csv")]


def test_current_paper_dynamic_read_path_is_visible_nonblocking_warning(tmp_path):
    root = _tree(tmp_path, {"src/paper.py": "from pathlib import Path\nname = input()\nPath('data' / name).read_text()\n"})
    findings = policy.audit_current_paper(root, _policy())
    assert _blocking(findings) == []
    assert findings == [policy.Finding("unresolved_read_path", "src/paper.py", "Path('data' / name)", blocking=False)]


def test_current_paper_guard_ignores_prose_and_negative_metadata(tmp_path):
    root = _tree(tmp_path, {"src/paper.py": "'''data/metrica_sample_game_3/raw.csv'''\nMETA = {'game3_accessed': False}\ndef f(): return META\n"})
    assert policy.audit_current_paper(root, _policy()) == []


def test_artifact_guard_rejects_raw_to_safe_rename_and_copy():
    changes = [
        policy.Change("R", "docs/safe.csv", old_path="data/Sample_Game_1_RawTrackingData.csv", size=1),
        policy.Change("C", "docs/copied.csv", old_path="docs/Sample_Game_1_RawTrackingData.csv", size=1),
    ]
    findings = policy.audit_changes(changes, _policy())
    assert {finding.path for finding in findings if finding.kind == "raw_provider_filename"} == {
        "data/Sample_Game_1_RawTrackingData.csv", "docs/Sample_Game_1_RawTrackingData.csv"
    }
    assert any(finding.kind == "data_path" and finding.path == "data/Sample_Game_1_RawTrackingData.csv" for finding in findings)


def test_artifact_guard_rejects_changed_provider_row_artifacts():
    findings = policy.audit_changes([policy.Change("M", "outputs/current/match_observation_rows.parquet", size=3)], _policy())
    assert findings == [policy.Finding("reconstructive_row_artifact", "outputs/current/match_observation_rows.parquet", "matches configured row-artifact marker")]


def test_artifact_guard_rejects_copied_file_over_ten_mib():
    findings = policy.audit_changes([policy.Change("C", "docs/copied.bin", old_path="docs/source.bin", size=10 * 1024 * 1024 + 1)], _policy())
    assert findings == [policy.Finding("large_changed_file", "docs/copied.bin", f"{10 * 1024 * 1024 + 1} bytes exceeds configured limit")]


def test_artifact_guard_does_not_scan_unchanged_historical_artifacts():
    assert policy.audit_changes([], _policy()) == []


def test_artifact_guard_allows_compact_ordinary_outputs():
    assert policy.audit_changes([policy.Change("A", "outputs/current/summary.json", size=512)], _policy()) == []


def test_artifact_exception_requires_exact_path_reason_and_approval_reference():
    rules = _policy()
    rules["artifact_policy"]["exceptions"] = [{"path": "outputs/current/observation_rows.parquet", "reason": "reviewed compact exception", "approval_reference": "issue-42"}]
    allowed = policy.Change("A", "outputs/current/observation_rows.parquet", size=5)
    other = policy.Change("A", "outputs/current/other_observation_rows.parquet", size=5)
    assert policy.audit_changes([allowed], rules) == []
    assert policy.audit_changes([other], rules)[0].kind == "reconstructive_row_artifact"
    incomplete = _policy(); incomplete["artifact_policy"]["exceptions"] = [{"path": allowed.path, "reason": "missing approval"}]
    assert policy.audit_changes([allowed], incomplete)[0].kind == "reconstructive_row_artifact"


def test_artifact_guard_rejects_external_symlink(tmp_path):
    findings = policy.audit_changes([policy.Change("A", "docs/link", size=1, symlink_target="/private/outside")], _policy(), tmp_path)
    assert findings == [policy.Finding("external_symlink", "docs/link", "/private/outside")]


def test_worktree_changes_lists_untracked_nested_files(tmp_path):
    _git(tmp_path, "init")
    nested = tmp_path / "untracked" / "nested" / "sample.csv"; nested.parent.mkdir(parents=True); nested.write_text("x", encoding="utf-8")
    assert [change.path for change in policy._worktree_changes(tmp_path)] == ["untracked/nested/sample.csv"]


def test_git_change_parser_handles_added_modified_renamed_and_copied_files(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Synthetic Test")
    (tmp_path / "modified.txt").write_text("before\n", encoding="utf-8")
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "Sample_Game_1_RawTrackingData.csv").write_text("synthetic raw marker\n" * 50, encoding="utf-8")
    (tmp_path / "copy_source.txt").write_text("synthetic copied marker\n" * 50, encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "base")
    (tmp_path / "modified.txt").write_text("after\n", encoding="utf-8")
    (tmp_path / "added.txt").write_text("added\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    _git(tmp_path, "mv", "raw/Sample_Game_1_RawTrackingData.csv", "docs/safe.csv")
    shutil.copyfile(tmp_path / "copy_source.txt", tmp_path / "copied.txt")
    (tmp_path / "docs" / "external-link").symlink_to("/private/outside")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "changes")
    changes = policy._git_changes(tmp_path, "HEAD~", "HEAD")
    assert {change.status for change in changes} == {"A", "M", "R", "C"}
    assert any(change.status == "R" and change.old_path == "raw/Sample_Game_1_RawTrackingData.csv" and change.path == "docs/safe.csv" for change in changes)
    assert any(change.status == "C" and change.old_path == "copy_source.txt" and change.path == "copied.txt" for change in changes)
    symlink = next(change for change in changes if change.path == "docs/external-link")
    assert symlink.symlink_target == "/private/outside"
    assert policy.audit_changes([symlink], _policy(), tmp_path) == [policy.Finding("external_symlink", "docs/external-link", "/private/outside")]
