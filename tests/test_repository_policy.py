"""Synthetic tests for bounded paper-firewall and artifact-publication checks."""
from __future__ import annotations

import hashlib
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
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "config" / "repository_policy.json").write_text(json.dumps(_policy()), encoding="utf-8")
    return tmp_path


def _blocking(findings: list[policy.Finding]) -> list[policy.Finding]:
    return [finding for finding in findings if finding.blocking]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _sha(text: str = "fixture") -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _exception(path: str, *, status: str = "A", source_path: str | None = None, overrides: list[str] | None = None, kind: str = "publication_artifact") -> dict:
    item = {
        "path": path,
        "change_status": status,
        "exception_type": kind,
        "purpose": "bounded synthetic test",
        "rationale": "reviewed exact exception",
        "approval_reference": "test-approval",
        "sha256": _sha(),
        "overrides": overrides or ["reconstructive_name"],
    }
    if source_path is not None:
        item["source_path"] = source_path
    return item


def test_current_paper_import_graph_has_no_blocking_findings():
    assert _blocking(policy.audit_current_paper(ROOT)) == []


def test_import_graph_traverses_direct_and_nested_relative_imports(tmp_path):
    root = _tree(tmp_path, {
        "src/pkg/paper.py": "from . import helper\n",
        "src/pkg/helper.py": "from .nested import x\n",
        "src/pkg/nested.py": "import protected_module\n",
    })
    findings = policy.audit_current_paper(root, _policy("src/pkg/paper.py"))
    assert _blocking(findings) == [policy.Finding("protected_module", "src/pkg/nested.py", "protected_module")]


def test_import_graph_traverses_from_relative_module_and_parent_import(tmp_path):
    root = _tree(tmp_path, {
        "src/pkg/nested/paper.py": "from ..helper import x\n",
        "src/pkg/helper.py": "import protected_module\n",
    })
    findings = policy.audit_current_paper(root, _policy("src/pkg/nested/paper.py"))
    assert _blocking(findings) == [policy.Finding("protected_module", "src/pkg/helper.py", "protected_module")]


def test_missing_configured_entrypoint_fails_closed(tmp_path):
    root = _tree(tmp_path, {})
    assert policy.audit_current_paper(root, _policy("src/missing.py")) == [
        policy.Finding("missing_entrypoint", "src/missing.py", "configured current-paper entry point does not exist")
    ]


def test_static_reader_forms_and_local_aliases_block_protected_paths(tmp_path):
    cases = {
        "concat": "from pathlib import Path\nPath('data/' + 'metrica_sample_game_3/raw.csv').read_text()\n",
        "fstring": "from pathlib import Path\nPath(f\"data/{'metrica_sample_game_3'}/raw.csv\").read_text()\n",
        "receiver": "from pathlib import Path\nPath('data/metrica_sample_game_3/raw.csv').open('rb')\n",
        "keyword": "import pandas as pd\npd.read_csv(filepath_or_buffer='data/metrica_sample_game_3/raw.csv')\n",
        "local": "import pandas as pd\ndef f():\n    base = 'data/metrica_sample_game_3'\n    path = base + '/raw.csv'\n    pd.read_csv(path)\n",
    }
    for name, source in cases.items():
        root = _tree(tmp_path / name, {"src/paper.py": source})
        assert _blocking(policy.audit_current_paper(root, _policy())) == [
            policy.Finding("protected_read_path", "src/paper.py", "data/metrica_sample_game_3/raw.csv")
        ]


def test_known_skillcorner_loader_checks_both_provider_paths(tmp_path):
    root = _tree(tmp_path, {
        "src/paper.py": "from kloppy import skillcorner\nskillcorner.load('safe.json', 'data/metrica_sample_game_3/raw.csv')\n"
    })
    assert _blocking(policy.audit_current_paper(root, _policy())) == [
        policy.Finding("protected_read_path", "src/paper.py", "data/metrica_sample_game_3/raw.csv")
    ]


def test_json_load_is_not_misclassified_as_a_path_reader(tmp_path):
    root = _tree(tmp_path, {"src/paper.py": "import json\njson.load(handle)\n"})
    assert policy.audit_current_paper(root, _policy()) == []


def test_dynamic_and_control_flow_paths_remain_visible_nonblocking_warnings(tmp_path):
    root = _tree(tmp_path, {
        "src/paper.py": "import pandas as pd\ndef f(name):\n    if name:\n        path = 'data/metrica_sample_game_3/raw.csv'\n    pd.read_csv(path)\n"
    })
    findings = policy.audit_current_paper(root, _policy())
    assert _blocking(findings) == []
    assert len(findings) == 1 and findings[0].kind == "unresolved_read_path"
    assert findings[0].sites == (policy.ReadSite(5, "pandas.read_csv", "path", "path is not statically resolved"),)


def test_dynamic_protected_prefix_fails_closed(tmp_path):
    root = _tree(tmp_path, {
        "src/paper.py": "from pathlib import Path\ndef f(name):\n    Path('data/metrica_sample_game_3' / name).read_text()\n"
    })
    findings = _blocking(policy.audit_current_paper(root, _policy()))
    assert findings == [policy.Finding("protected_read_path", "src/paper.py", "data/metrica_sample_game_3 [dynamic suffix]")]


def test_unresolved_warnings_are_grouped_by_file_and_function(tmp_path):
    root = _tree(tmp_path, {
        "src/paper.py": "import pandas as pd\ndef f(a, b):\n    pd.read_csv(a)\n    pd.read_csv(b)\n"
    })
    findings = policy.audit_current_paper(root, _policy())
    assert len(findings) == 1
    assert findings[0].detail == "f: 2 path expression(s) not statically resolved"
    assert [site.expression for site in findings[0].sites] == ["a", "b"]


def test_guard_ignores_prose_and_negative_metadata(tmp_path):
    root = _tree(tmp_path, {"src/paper.py": "'''data/metrica_sample_game_3/raw.csv'''\nMETA = {'game3_accessed': False}\ndef f(): return META\n"})
    assert policy.audit_current_paper(root, _policy()) == []


def test_artifact_guard_checks_both_sides_of_rename_and_copy():
    changes = [
        policy.Change("R", "docs/safe.csv", old_path="data/Sample_Game_1_RawTrackingData.csv", size=1, sha256=_sha()),
        policy.Change("C", "docs/copied.csv", old_path="docs/Sample_Game_1_RawTrackingData.csv", size=1, sha256=_sha()),
    ]
    findings = policy.audit_changes(changes, _policy())
    assert {finding.path for finding in findings if finding.kind == "raw_provider_filename"} == {
        "data/Sample_Game_1_RawTrackingData.csv", "docs/Sample_Game_1_RawTrackingData.csv"
    }
    assert any(finding.kind == "data_path" for finding in findings)


def test_artifact_guard_blocks_reconstructive_and_opaque_artifacts_by_default():
    findings = policy.audit_changes([
        policy.Change("M", "outputs/current/match_observation_rows.parquet", size=3, sha256=_sha()),
        policy.Change("A", "outputs/current/bundle.zip", size=3, sha256=_sha()),
        policy.Change("A", "notebooks/result.ipynb", size=3, sha256=_sha()),
    ], _policy())
    assert {finding.kind for finding in findings} == {"reconstructive_row_artifact", "opaque_container", "notebook_embedded_output"}


def test_publication_artifact_may_override_exact_opaque_or_notebook_capability():
    rules = _policy()
    opaque = "outputs/current/reviewed.zip"
    notebook = "notebooks/reviewed.ipynb"
    rules["artifact_policy"]["exceptions"] = [
        _exception(opaque, overrides=["opaque_container"]),
        _exception(notebook, overrides=["notebook_embedded_output"]),
    ]
    assert policy.audit_changes([
        policy.Change("A", opaque, size=5, sha256=_sha()),
        policy.Change("A", notebook, size=5, sha256=_sha()),
    ], rules) == []


def test_synthetic_fixture_cannot_override_opaque_or_notebook_capability():
    rules = _policy()
    opaque = "tests/fixtures/reviewed.zip"
    notebook = "tests/fixtures/reviewed.ipynb"
    rules["artifact_policy"]["exceptions"] = [
        _exception(opaque, kind="synthetic_fixture", overrides=["opaque_container"]),
        _exception(notebook, kind="synthetic_fixture", overrides=["notebook_embedded_output"]),
    ]
    findings = policy.audit_changes([
        policy.Change("A", opaque, size=5, sha256=_sha()),
        policy.Change("A", notebook, size=5, sha256=_sha()),
    ], rules)
    assert {finding.kind for finding in findings} == {
        "invalid_exception", "opaque_container", "notebook_embedded_output"
    }


def test_artifact_exception_is_exact_hash_bound_and_capability_specific():
    rules = _policy()
    path = "outputs/current/observation_rows.parquet"
    rules["artifact_policy"]["exceptions"] = [_exception(path)]
    allowed = policy.Change("A", path, size=5, sha256=_sha())
    wrong_hash = policy.Change("A", path, size=5, sha256=_sha("other"))
    assert policy.audit_changes([allowed], rules) == []
    assert policy.audit_changes([wrong_hash], rules)[0].kind == "reconstructive_row_artifact"


def test_exception_cannot_bypass_raw_data_or_symlink_rules(tmp_path):
    rules = _policy()
    raw = "data/Sample_Game_1_RawTrackingData.csv"
    rules["artifact_policy"]["exceptions"] = [_exception(raw, overrides=["provider_like_filename"])]
    findings = policy.audit_changes([
        policy.Change("A", raw, size=3, sha256=_sha()),
        policy.Change("A", "docs/link", size=1, symlink_target="/private/outside", sha256=_sha()),
    ], rules, tmp_path)
    assert {finding.kind for finding in findings} >= {"data_path", "raw_provider_filename", "external_symlink"}


def test_synthetic_fixture_may_use_an_exact_provider_like_name_only(tmp_path):
    rules = _policy()
    path = "tests/fixtures/Sample_Game_1_RawTrackingData.csv"
    rules["artifact_policy"]["exceptions"] = [_exception(path, kind="synthetic_fixture", overrides=["provider_like_filename"])]
    assert policy.audit_changes([policy.Change("A", path, size=3, sha256=_sha())], rules, tmp_path) == []


def test_invalid_exception_schema_fails_closed():
    rules = _policy()
    rules["artifact_policy"]["exceptions"] = [{"path": "outputs/current/observation_rows.parquet"}]
    findings = policy.audit_changes([], rules)
    assert findings == [policy.Finding("invalid_exception", "outputs/current/observation_rows.parquet", "exception schema is incomplete or has unsupported authority")]


def test_synthetic_fixture_exception_cannot_allow_large_or_nonfixture_path():
    rules = _policy()
    rules["artifact_policy"]["exceptions"] = [
        _exception("tests/fixtures/observation_rows.csv", kind="synthetic_fixture"),
        _exception("tests/fixtures/large_observation_rows.csv", kind="synthetic_fixture", overrides=["reconstructive_name", "large_file"]),
    ]
    findings = policy.audit_changes([
        policy.Change("A", "tests/fixtures/observation_rows.csv", size=5, sha256=_sha()),
        policy.Change("A", "tests/fixtures/large_observation_rows.csv", size=10 * 1024 * 1024 + 1, sha256=_sha()),
    ], rules)
    assert {finding.kind for finding in findings} == {"invalid_exception", "large_changed_file"}


def test_rename_exception_requires_source_status_and_target_hash():
    rules = _policy()
    rules["artifact_policy"]["exceptions"] = [
        _exception("outputs/current/observation_rows.parquet", status="R", source_path="outputs/old/observation_rows.parquet")
    ]
    change = policy.Change("R", "outputs/current/observation_rows.parquet", old_path="outputs/old/observation_rows.parquet", size=3, sha256=_sha())
    assert policy.audit_changes([change], rules)[0].kind == "reconstructive_row_artifact"


def test_artifact_guard_allows_compact_ordinary_outputs_and_ignores_history():
    assert policy.audit_changes([policy.Change("A", "outputs/current/summary.json", size=512, sha256=_sha())], _policy()) == []
    assert policy.audit_changes([], _policy()) == []


def test_artifact_guard_warns_for_small_unknown_binary():
    findings = policy.audit_changes([policy.Change("A", "docs/payload.bin", size=2, sha256=_sha())], _policy())
    assert findings == [policy.Finding("unknown_binary_artifact", "docs/payload.bin", "small binary artifact was not content-classified", blocking=False)]


def test_internal_and_external_worktree_symlinks_are_classified(tmp_path):
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    internal = policy.Change("A", "docs/link", size=1, symlink_target="../safe.txt", sha256=_sha())
    external = policy.Change("A", "docs/link", size=1, symlink_target="/private/outside", sha256=_sha())
    assert policy.audit_changes([internal], _policy(), tmp_path) == []
    assert policy.audit_changes([external], _policy(), tmp_path) == [policy.Finding("external_symlink", "docs/link", "/private/outside")]


def test_worktree_changes_lists_untracked_nested_files(tmp_path):
    _git(tmp_path, "init")
    nested = tmp_path / "untracked" / "nested" / "sample.csv"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")
    assert [change.path for change in policy._worktree_changes(tmp_path)] == ["untracked/nested/sample.csv"]


def test_git_change_parser_handles_added_modified_renamed_copied_and_symlink_files(tmp_path):
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
