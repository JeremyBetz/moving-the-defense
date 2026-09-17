from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import skillcorner_additional_directional_replication_v1 as module


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _criteria(positive: int = 10, all_lomo: bool = True) -> dict[str, object]:
    return {
        "valid_execution": True,
        "positive_matches": positive,
        "valid_matches": 10,
        "positive_match_percent": 10.0 * positive,
        "minimum_positive_matches_required": 7,
        "trimmed_to_full_absolute_ratio": 1.0,
        "quality_to_full_absolute_ratio": 1.0,
        "gates": {
            "at_least_8_valid_matches": True,
            "pooled_contrast_strictly_positive": True,
            "bootstrap_95_percent_interval_strictly_positive": True,
            "at_least_70_percent_match_contrasts_positive": positive >= 7,
            "all_leave_one_match_out_contrasts_positive": all_lomo,
            "trim_positive_and_50_to_150_percent_magnitude": True,
            "quality_full_rank_positive_and_50_to_150_percent_magnitude": True,
        },
    }


def _synthetic_builder(directory: Path, *, classification: str = "ADDITIONAL SKILLCORNER DIRECTIONAL REPLICATION SUPPORTED") -> None:
    directory.mkdir(parents=True)
    per_match = []
    lomo = []
    samples = []
    equivalence = []
    for match in module.FORMAL_MATCHES:
        per_match.append({"match_id": match, "eligible_rows": 20, "eligible_anchors": 10, "model_rank": 10, "beta_goalward_m_per_m": 0.01, "beta_outward_m_per_m": 0.03, "outward_minus_goalward_m_per_m": 0.02, "positive_contrast": True})
        lomo.append({"heldout_match_id": match, "training_rows": 180, "model_rank": 18, "outward_minus_goalward_m_per_m": 0.02})
        samples.append({"match_id": match, "candidate_anchors": 12, "retained_anchors": 10, "retained_rows": 20, "period_1_anchors": 5, "period_2_anchors": 5, "majority_detected_rows": 15})
        equivalence.append({"match_id": match, "pass": True})
    primary = {"classification": classification, "beta_goalward_m_per_m": 0.01, "beta_outward_m_per_m": 0.03, "outward_minus_goalward_m_per_m": 0.02, "five_m_translation_m": 0.1, "ci_low": 0.01, "ci_high": 0.03, "valid_bootstrap_replicates": 2000}
    trim = {"rows_retained": 180, "retained_proportion": 0.9, "beta_goalward_m_per_m": 0.01, "beta_outward_m_per_m": 0.03, "outward_minus_goalward_m_per_m": 0.02, "model_rank": 19}
    quality = {"rows": 150, "anchors": 80, "matches": 10, "full_rank": True, "model_rank": 19, "beta_goalward_m_per_m": 0.01, "beta_outward_m_per_m": 0.03, "outward_minus_goalward_m_per_m": 0.02}
    tables = {
        "primary_contrast.csv": [primary], "per_match_coefficients.csv": per_match,
        "leave_one_match_out.csv": lomo, "trim_sensitivity.csv": [trim],
        "quality_sensitivity.csv": [quality], "sample_summary.csv": samples,
        "provider_equivalence.csv": equivalence,
    }
    for name, rows in tables.items():
        _write_csv(directory / name, module.CSV_SCHEMAS[name], rows)
    criteria = _criteria()
    result = {
        "classification": classification,
        "sample": {"rows": 200, "anchors": 100, "matches": 10, "match_ids": list(module.FORMAL_MATCHES)},
        "primary": {key: primary[key] for key in ("beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "five_m_translation_m")},
        "bootstrap": {"replicates_requested": 2000, "valid_replicates": 2000, "seed": 20260905, "block_seconds": 60.0, "ci_low": 0.01, "ci_high": 0.03},
        "trim": trim, "quality_sensitivity": quality, "classification_criteria": criteria,
    }
    module.write_json(directory / "result.json", result)
    module.write_json(directory / "hard_qc.json", {"status": "PASSED", "checks": {key: True for key in module.HARD_QC_KEYS}})
    module.write_json(directory / "classification_criteria.json", criteria)
    module.write_json(directory / "manifest.json", {
        "status": "PENDING_AUTHORITATIVE_VALIDATION", "authorization_reference": "synthetic-approval",
        "protocol_sha256": "a" * 64, "configuration_sha256": "b" * 64,
        "freeze_ledger_sha256": "c" * 64, "implementation_sha256": "d" * 64,
        "tests_sha256": "e" * 64, "source_commit": module.SOURCE_COMMIT,
        "source_tree": module.SOURCE_TREE, "formal_matches": list(module.FORMAL_MATCHES),
        "bootstrap_seed": 20260905, "bootstrap_replicates": 2000,
        "classification": classification, "preflight_lineage": {"manifest_sha256": "f" * 64, "source_ledger_sha256": "0" * 64},
        "publication_policy": "compact_aggregate_outputs_only",
    })
    (directory / "result_report.md").write_text("# Synthetic aggregate result\n", encoding="utf-8")


def test_frozen_population_is_exact_and_disjoint() -> None:
    assert len(module.FORMAL_MATCHES) == len(set(module.FORMAL_MATCHES)) == 10
    assert not set(module.FORMAL_MATCHES) & set(module.ORIGINAL_MATCHES)
    assert module.EXCLUDED_MATCH not in module.FORMAL_MATCHES


def test_configuration_freezes_seed_population_and_no_result_exclusion() -> None:
    config = json.loads(module.CONFIG.read_text())
    assert config["population"]["formal_matches"] == list(module.FORMAL_MATCHES)
    assert config["population"]["post_response_removal"] is False
    assert config["inference"] == {"replicates": 2000, "minimum_valid": 1900, "generator": "PCG64", "seed": 20260905, "block_seconds": 60.0, "strata": "match_period", "preserve_simultaneous_anchor_rows": True, "interval": "two_sided_95_percentile"}


def test_preflight_lineage_recovers_exact_candidate_population() -> None:
    result = module.verify_preflight_lineage()
    assert set(result) == {"manifest_sha256", "source_ledger_sha256"}


def test_classification_branches_are_inherited_without_new_thresholds() -> None:
    per_match = pd.DataFrame({"positive_contrast": [True] * 10})
    lomo = pd.DataFrame({"outward_minus_goalward_m_per_m": [0.1] * 10})
    trim = {"outward_minus_goalward_m_per_m": 0.1}
    quality = {"full_rank": True, "outward_minus_goalward_m_per_m": 0.1}
    status, _ = module.classify(0.1, {"ci_low": 0.01}, per_match, lomo, trim, quality)
    assert status.endswith("SUPPORTED")
    status, _ = module.classify(0.1, {"ci_low": -0.01}, per_match, lomo, trim, quality)
    assert status.endswith("MIXED")
    status, _ = module.classify(-0.1, {"ci_low": -0.2}, per_match, lomo, {"outward_minus_goalward_m_per_m": -0.1}, {"full_rank": True, "outward_minus_goalward_m_per_m": -0.1})
    assert status.endswith("NOT SUPPORTED")
    status, _ = module.classify(0.1, {"ci_low": 0.01}, per_match, lomo, trim, quality, valid=False)
    assert status.endswith("INVALID")


def test_inherited_fit_uses_equal_total_match_weight_not_row_pooling() -> None:
    rng = np.random.default_rng(41)
    rows = []
    nuisance_beta = np.linspace(0.1, 0.8, 8)
    for match, size, slope in (("a", 15, 4.0), ("b", 80, -1.0)):
        continuous = rng.normal(size=(size, 9))
        outcome = continuous[:, :8] @ nuisance_beta + slope * continuous[:, 8]
        for values, y in zip(continuous, outcome, strict=True):
            row = dict(zip(module.inherited.BASE, values, strict=True))
            row.update(match_id=match, Y_m=y)
            rows.append(row)
    frame = pd.DataFrame(rows)
    beta, _, _ = module.inherited.fit(frame)
    match = frame.match_id.to_numpy()
    names = sorted(set(match))
    match_effects = np.column_stack([(match == key).astype(float) for key in names[1:]])
    matrix = np.column_stack([np.ones(len(frame)), match_effects, frame.loc[:, module.inherited.BASE].to_numpy(float)])
    weights = np.array([1.0 / sum(match == key) for key in match])
    oracle = np.linalg.lstsq(matrix * np.sqrt(weights)[:, None], frame.Y_m.to_numpy() * np.sqrt(weights), rcond=None)[0]
    row_pooled = np.linalg.lstsq(matrix, frame.Y_m.to_numpy(), rcond=None)[0]
    assert beta == pytest.approx(oracle)
    assert beta[-1] != pytest.approx(row_pooled[-1])


def test_output_schemas_are_aggregate_only(tmp_path: Path) -> None:
    package = tmp_path / "package"
    _synthetic_builder(package)
    assert module.validate_package(package)["files_validated"] == len(module.GOVERNED_FILES)
    prohibited = {"observation_id", "timestamp", "x_m", "y_m", "player_id", "team_id", "Y_m", "residual"}
    for schema in module.CSV_SCHEMAS.values():
        assert not prohibited & set(schema)


def test_structural_validation_rejects_substitution(tmp_path: Path) -> None:
    package = tmp_path / "package"
    _synthetic_builder(package)
    rows = list(csv.DictReader((package / "per_match_coefficients.csv").open()))
    rows[0]["match_id"] = str(module.EXCLUDED_MATCH)
    _write_csv(package / "per_match_coefficients.csv", module.CSV_SCHEMAS["per_match_coefficients.csv"], rows)
    with pytest.raises(RuntimeError, match="identity mismatch"):
        module.validate_package(package)


def test_structural_validation_rejects_nonfinite_and_unexpected_column(tmp_path: Path) -> None:
    package = tmp_path / "package"
    _synthetic_builder(package)
    path = package / "primary_contrast.csv"
    rows = list(csv.DictReader(path.open()))
    rows[0]["ci_low"] = "NaN"
    _write_csv(path, module.CSV_SCHEMAS[path.name], rows)
    with pytest.raises(RuntimeError, match="nonfinite"):
        module.validate_package(package)
    _synthetic_builder(tmp_path / "second")
    path = tmp_path / "second" / "primary_contrast.csv"
    text = path.read_text().replace("\n", ",observation_id\n", 1)
    path.write_text(text)
    with pytest.raises(RuntimeError, match="schema mismatch"):
        module.validate_package(tmp_path / "second")


def test_structural_validation_rejects_nested_reconstructive_json(tmp_path: Path) -> None:
    package = tmp_path / "package"
    _synthetic_builder(package)
    result = json.loads((package / "result.json").read_text())
    result["sample"]["observation_id"] = "forbidden"
    module.write_json(package / "result.json", result)
    with pytest.raises(RuntimeError, match="reconstructive JSON field"):
        module.validate_package(package)


def test_authorization_reference_is_required_before_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(module, "verify_hash_ledger", lambda: pytest.fail("gate proceeded"))
    with pytest.raises(RuntimeError, match="authorization"):
        module.run(tmp_path, tmp_path, " ")


def test_clean_committed_gate_rejects_worktree_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "read_json", lambda path: {"files": {"src/example.py": "a" * 64}})
    class Completed:
        def __init__(self, stdout: str = "", returncode: int = 0):
            self.stdout, self.returncode = stdout, returncode
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kwargs: Completed(" M src/example.py\n") if command[1] == "status" else Completed())
    with pytest.raises(RuntimeError, match="clean committed worktree"):
        module.require_clean_committed_freeze()


def test_inherited_block_bootstrap_is_deterministic_and_groups_complete_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(8)
    rows = []
    for match in map(str, module.FORMAL_MATCHES):
        for period in (1, 2):
            for block in (0, 1):
                for anchor in range(12):
                    values = rng.normal(size=9)
                    row = dict(zip(module.inherited.BASE, values, strict=True))
                    row.update(match_id=match, period=period, block_id=block, anchor_frame=anchor, Y_m=float(values @ np.linspace(0.1, 0.9, 9)))
                    rows.append(row)
    frame = pd.DataFrame(rows)
    _x, _y, groups, strata = module.inherited.block_statistics(frame, tuple(map(str, module.FORMAL_MATCHES)))
    assert len(groups) == 40
    assert all(len(indices) == 12 for indices in groups.values())
    assert all(len(keys) == 2 for keys in strata.values())
    monkeypatch.setattr(module.inherited, "BOOTSTRAP_REPLICATES", 12)
    monkeypatch.setattr(module.inherited, "MINIMUM_BOOTSTRAP_VALID", 10)
    first = module.inherited.bootstrap(frame, tuple(map(str, module.FORMAL_MATCHES)))
    second = module.inherited.bootstrap(frame, tuple(map(str, module.FORMAL_MATCHES)))
    assert first == second
    assert first["seed"] == 20260905


def test_source_gate_rejects_substitution_before_response_construction(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    for match in (*module.FORMAL_MATCHES[1:], module.EXCLUDED_MATCH):
        (data / f"{match}_match.json").write_text("{}")
    class Completed:
        def __init__(self, value: str): self.stdout, self.returncode = value + "\n", 0
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kwargs: Completed(module.SOURCE_COMMIT if command[-1] == "HEAD" else module.SOURCE_TREE))
    with pytest.raises(RuntimeError, match="missing one or more frozen"):
        module.verify_sources(data, tmp_path)


def test_isolated_reproduction_and_final_authority_are_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "final"
    result = module.close_execution(output, "synthetic-approval", _synthetic_builder)
    assert result["status"] == "FINAL_PACKAGE_VALID"
    assert module.validate_final_authority(output)["status"] == "FINAL_PACKAGE_VALID"
    assert json.loads((output / "reproduction.json").read_text())["status"] == "STAGING_REPRODUCTION_PASSED"


def test_output_directory_is_promoted_before_final_marker(tmp_path: Path) -> None:
    output = tmp_path / "final"
    destinations: list[Path] = []
    def recording_replace(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        destinations.append(Path(destination))
        os.replace(source, destination)
    module.close_execution(output, "synthetic-approval", _synthetic_builder, replace=recording_replace)
    assert destinations[-2:] == [output, output / module.FINAL_MARKER]


def test_byte_difference_fails_without_final_authority(tmp_path: Path) -> None:
    output = tmp_path / "final"
    calls = 0
    def differing_builder(directory: Path) -> None:
        nonlocal calls
        _synthetic_builder(directory)
        calls += 1
        if calls == 2:
            (directory / "result_report.md").write_text("different\n")
    with pytest.raises(RuntimeError, match="reproduction differs"):
        module.close_execution(output, "synthetic-approval", differing_builder)
    assert not (output / module.FINAL_MARKER).exists()


def test_final_validation_failure_removes_valid_marker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "final"
    original = module.validate_final_authority
    monkeypatch.setattr(module, "validate_final_authority", lambda directory: (_ for _ in ()).throw(RuntimeError("forced final failure")))
    with pytest.raises(RuntimeError, match="forced final failure"):
        module.close_execution(output, "synthetic-approval", _synthetic_builder)
    assert not (output / module.FINAL_MARKER).exists()
    monkeypatch.setattr(module, "validate_final_authority", original)


def test_existing_authoritative_destination_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "final"
    output.mkdir()
    with pytest.raises(RuntimeError, match="already exists"):
        module.close_execution(output, "synthetic-approval", _synthetic_builder)


def test_cli_has_separate_response_blind_and_execution_modes() -> None:
    source = Path(module.__file__).read_text()
    assert 'add_parser("preflight")' in source
    assert 'add_parser("run")' in source
    assert 'add_parser("publication-check")' in source
    assert "construct_match" not in source.split("def preflight", 1)[1].split("def run", 1)[0]
