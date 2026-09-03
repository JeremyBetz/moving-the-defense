"""Governance checks for the outcome-blind defender-rank composition audit.

These tests inspect schemas, configuration, compact outcome-blind audit outputs,
and hashes only.  They never load a real concurrent-response or coverage value.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import polars as pl
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defender_rank_composition_audit as audit  # noqa: E402


CONFIG = ROOT / "config/defender_rank_composition_audit.json"
OUTPUT = ROOT / "outputs/defender_rank_composition_audit"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_ledger_fixture() -> pl.DataFrame:
    rows = []
    for rank in range(1, 11):
        row = {
            "observation_id": "safe-projection-fixture",
            "period": 1,
            "time_period_s": 10.0,
            "attacker_key": "A1",
            "attacking_team": "attack",
            "defending_team": "defend",
            "block_id": 0,
            "defender_key": f"D{rank:02d}",
            "distance_rank": rank,
            "distance_m": float(rank),
            "prior_attacker_path_m": 1.0,
            "prior_focal_relative_path_m": 2.0,
            "prior_defensive_centroid_path_m": 3.0,
            "prior_other_nine_mean_absolute_path_m": 4.0,
            "match_id": "fixture_match",
            "time_utc_ns": 1_000_000_000,
        }
        for forbidden in _json(CONFIG)["data"]["forbidden_columns"]:
            row[forbidden] = 999.0
        rows.append(row)
    return pl.DataFrame(rows)


def test_rank_ledger_projection_excludes_every_forbidden_outcome(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger_with_poison_columns.parquet"
    _safe_ledger_fixture().write_parquet(source)

    projected = audit.load_rank_ledger(source)
    expected = [
        "attacker_defender_start_distance_m" if name == "distance_m" else name
        for name in (*audit.COMMON_COLUMNS, *audit.IDSSE_EXTRA_COLUMNS)
    ]
    assert projected.columns.tolist() == expected
    assert len(projected) == 10
    assert projected.distance_rank.tolist() == list(range(1, 11))

    config = _json(CONFIG)
    assert not set(config["data"]["forbidden_columns"]).intersection(projected)
    assert not any(
        token in column
        for column in projected
        for token in audit.FORBIDDEN_TOKENS
    )
    assert "attacker_defender_start_distance_m" not in config["rank_predictability"][
        "features"
    ]
    assert config["rank_predictability"][
        "scalar_euclidean_attacker_defender_distance_excluded"
    ] is True


def test_projection_guard_rejects_a_forbidden_selected_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ledger.parquet"
    _safe_ledger_fixture().write_parquet(source)
    monkeypatch.setattr(
        audit,
        "COMMON_COLUMNS",
        (*audit.COMMON_COLUMNS, "concurrent_focal_relative_path_m"),
    )
    with pytest.raises(RuntimeError, match="forbidden response column"):
        audit.load_rank_ledger(source)


def test_configured_source_projection_is_ids_prior_and_rank_only() -> None:
    config = _json(CONFIG)
    configured = {
        name.removesuffix("_if_present")
        for name in config["data"]["rank_source_projection_only"]
    }
    implemented = set(audit.COMMON_COLUMNS) | set(audit.IDSSE_EXTRA_COLUMNS)
    assert configured == implemented
    assert set(config["rank_predictability"]["features"]).issubset(
        set(config["summary_variables"])
    )
    assert not any(
        token in column
        for column in implemented | set(config["rank_predictability"]["features"])
        for token in audit.FORBIDDEN_TOKENS
    )


def test_generated_sample_counts_and_output_shapes_are_exact() -> None:
    config = _json(CONFIG)
    result = _json(OUTPUT / "audit_results.json")
    sample = pd.read_csv(OUTPUT / "sample_counts.csv")

    assert result["status"] == "OUTCOME_BLIND_RANK_COMPOSITION_AUDIT_COMPLETE"
    assert result["starting_commit"] == config["starting_commit"]
    assert result["config_sha256"] == _sha256(CONFIG)
    assert result["matches"] == 9
    assert result["rows"] == 835_130
    assert result["attacker_anchor_observations"] == 83_513
    assert result["rows"] == 10 * result["attacker_anchor_observations"]

    assert sample.match_id.tolist() == config["data"]["matches"]
    assert len(sample) == result["matches"]
    assert int(sample.rank_rows.sum()) == result["rows"]
    assert int(sample.observations.sum()) == result["attacker_anchor_observations"]
    assert (sample.rank_rows == 10 * sample.observations).all()
    assert result["sample"] == sample.to_dict("records")

    matches = len(config["data"]["matches"])
    variables = len(config["summary_variables"])
    features = len(config["rank_predictability"]["features"])
    assert len(pd.read_csv(OUTPUT / "rank_group_summaries.csv")) == matches * variables * 3
    assert len(pd.read_csv(OUTPUT / "near_middle_effects.csv")) == matches * variables
    assert len(pd.read_csv(OUTPUT / "cross_match_effects.csv")) == variables
    assert len(pd.read_csv(OUTPUT / "rank_D1_D10_summaries.csv")) == matches * variables * 10
    folds = pd.read_csv(OUTPUT / "rank_predictability_folds.csv")
    assert len(folds) == matches
    assert sorted(folds.heldout_match) == sorted(config["data"]["matches"])
    assert len(pd.read_csv(OUTPUT / "rank_predictability_coefficients.csv")) == matches * (
        features + 1
    )
    assert len(pd.read_csv(OUTPUT / "conditioning_coverage.csv")) == variables
    assert result["classifier"]["complete_rows"] == int(folds.test_rows.sum())

    provenance = _json(OUTPUT / "input_provenance.json")
    assert provenance["status"] == "OUTCOME_BLIND_RECONSTRUCTION_INPUTS_BOUND"
    assert len(provenance["matches"]) == matches
    assert provenance["provider_event_files_opened_for_reconstruction"] is False
    assert provenance["protected_response_or_coverage_inputs"] == []
    assert provenance["game3_inputs"] == []
    for match in provenance["matches"]:
        assert match["source_files"]
        assert match["goalward_sign_support_precedes_every_anchor"] is True
        if match["provider"] == "IDSSE/Sportec":
            assert match["event_file_opened"] is False
        for source in match["source_files"]:
            path = ROOT / source["path"]
            assert path.exists()
            assert _sha256(path) == source["sha256"]


def test_generated_verdict_and_firewalls_are_exact() -> None:
    config = _json(CONFIG)
    rules = config["severity_rules"]
    assert "large_stable_unresolved_nondefining_composition" in rules
    assert "large_stable_unadjusted_composition" not in rules
    assert "attacker_defender_start_distance_m" in rules[
        "large_stable_unresolved_nondefining_composition"
    ]
    assert "do not alone trigger severity" in rules["fully_conditioned_rule"]

    result = _json(OUTPUT / "audit_results.json")
    decision = result["decision"]
    assert decision["severity"] == "MODERATE"
    assert decision["verdict"] == "CORE RANK LOCALIZATION USABLE WITH MODERATE LIMITATION"
    assert decision["v3_decision"] == (
        "V3 MAY PROCEED WITH A PAPER LIMITATION / NONCLASSIFYING QC"
    )
    assert decision["strong_predictability_rule"] is False
    assert decision["major_variables"] == []
    assert decision["moderate_variables"] == [
        "defender_goalward_offset_from_centroid_m"
    ]

    firewall = result["firewall"]
    assert firewall["frozen_input_hashes_match"] is True
    assert firewall["coverage_v3_output_absent"] is True
    assert firewall["concurrent_response_columns_selected"] == []
    assert firewall["coverage_outcomes_selected"] == []
    assert firewall["game2_or_idsse_coverage_outcomes_inspected"] is False
    assert firewall["game3_accessed"] is False
    assert firewall["game3_not_accessed"] is True
    assert firewall["start_distance_and_prior_geometry_reconstructed_within_1e_6_m"] is True
    assert firewall["rank_ledger_columns_selected"] == [
        *audit.COMMON_COLUMNS,
        *audit.IDSSE_EXTRA_COLUMNS,
    ]


def test_all_frozen_inputs_and_generated_outputs_match_their_hashes() -> None:
    config = _json(CONFIG)
    assert config["status"] == (
        "FROZEN_FOR_AUTHORITATIVE_RERUN_AFTER_PRECLOSURE_OUTCOME_BLIND_INTEGRITY_CORRECTION"
    )
    for relative, expected in config["frozen_input_hashes"].items():
        assert _sha256(ROOT / relative) == expected, relative

    governed = _json(OUTPUT / "governed_hashes.json")
    assert len(governed) == 10
    for name, expected in governed.items():
        assert _sha256(OUTPUT / name) == expected, name
    reproduction = _json(OUTPUT / "reproduction.json")
    assert reproduction["all_governed_outputs_byte_identical"] is True
    assert reproduction["governed_outputs"] == 10
    assert reproduction["expected"] == reproduction["actual"] == governed


def test_rank_audit_records_the_preexecution_v3_firewall() -> None:
    config = _json(CONFIG)
    assert config["firewall"]["coverage_v3_execution"] == "prohibited"
