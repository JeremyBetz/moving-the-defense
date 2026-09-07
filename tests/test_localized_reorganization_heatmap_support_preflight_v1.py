"""Synthetic and provider-gated checks for the response-blind support preflight."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import localized_reorganization_heatmap_support_preflight_v1 as support  # noqa: E402


OUTPUT = ROOT / "outputs/localized_reorganization_heatmap_support_preflight_v1"
REPORT = ROOT / "docs/results/localized_reorganization_heatmap_support_preflight_v1.md"
FIGURES = ROOT / "figures/localized_reorganization_heatmap_support_preflight_v1"


def _small_config() -> dict:
    cfg = copy.deepcopy(support.config())
    cfg["grid"] = {"x_centres_m": {"start": 0.0, "stop": 1.0, "step": 1.0}, "y_centres_m": {"start": 0.0, "stop": 0.0, "step": 1.0}}
    cfg["kernel"]["bandwidths_m"] = [2.5]
    return cfg


def _matches() -> list[support.PreparedMatch]:
    coordinates = np.zeros((32, 2), dtype=float)
    time_keys = np.asarray([f"P1|{index}" for index in range(32)], dtype=object)
    block_keys = np.asarray([f"P1|B{index % 4}" for index in range(32)], dtype=object)
    return [support.PreparedMatch(match, coordinates.copy(), time_keys.copy(), block_keys.copy()) for match in support.MATCHES]


def test_goalward_orientation_preserves_physical_lateral_coordinate(monkeypatch):
    period = support.idsse.PERIODS[0]
    times = np.arange(0, 5_000_000_000, support.FRAME_NS, dtype=np.int64)
    entity = {"team_id": "attack", "person_id": "a1", "x": np.full(len(times), 5.0), "y": np.full(len(times), 6.0), "valid": np.ones(len(times), dtype=bool)}
    tracking = {name: {"time_ns": times, "entities": [entity]} for name in support.idsse.PERIODS}
    monkeypatch.setattr(support.concurrent, "load_native", lambda match: ({}, {}, tracking))
    monkeypatch.setattr(support.departure, "period_signs", lambda metadata, native: {(1, "attack"): -1})
    rows = pd.DataFrame([{ "period": 1, "time_utc_ns": 3_000_000_000, "attacking_team": "attack", "attacker_key": "a1", "block_id": 0 }])
    prepared = support.prepare_match("J03WMX", rows)
    assert np.array_equal(prepared.coordinates, np.asarray([[-5.0, 6.0]]))


def test_prepare_match_extracts_centered_smoothed_position_at_t_minus_2(monkeypatch):
    """The focal coordinate must come from the governed centred t-2 window."""
    times = np.arange(0, 10_000_000_000, support.FRAME_NS, dtype=np.int64)
    frame = np.arange(len(times), dtype=float)
    entity = {
        "team_id": "attack",
        "person_id": "a1",
        "x": 2.0 + 0.1 * frame,
        "y": -4.0 + 0.05 * frame,
        "valid": np.ones(len(times), dtype=bool),
    }
    tracking = {
        name: {"time_ns": times, "entities": [entity]}
        for name in support.idsse.PERIODS
    }
    monkeypatch.setattr(support.concurrent, "load_native", lambda match: ({}, {}, tracking))
    monkeypatch.setattr(
        support.departure,
        "period_signs",
        lambda metadata, native: {(1, "attack"): -1},
    )
    anchor_ns = 6_000_000_000
    rows = pd.DataFrame(
        [{
            "period": 1,
            "time_utc_ns": anchor_ns,
            "attacking_team": "attack",
            "attacker_key": "a1",
            "block_id": 0,
        }]
    )

    prepared = support.prepare_match("J03WMX", rows)

    # For a linear trajectory, a centred seven-frame mean equals the centre
    # value. Derive that value analytically, without production slicing.
    start_index = int((anchor_ns - 2_000_000_000) // support.FRAME_NS)
    expected_start = np.asarray(
        [-(2.0 + 0.1 * start_index), -4.0 + 0.05 * start_index]
    )
    wrong_anchor_index = int(anchor_ns // support.FRAME_NS)
    wrong_anchor = np.asarray(
        [-(2.0 + 0.1 * wrong_anchor_index), -4.0 + 0.05 * wrong_anchor_index]
    )
    assert not np.array_equal(expected_start, wrong_anchor)
    assert np.allclose(prepared.coordinates[0], expected_start)


def test_native_out_of_pitch_anchor_is_not_clipped_before_kernel_support(monkeypatch):
    """A finite native coordinate outside the pitch remains a kernel input."""
    times = np.arange(0, 5_000_000_000, support.FRAME_NS, dtype=np.int64)
    entity = {
        "team_id": "attack",
        "person_id": "a1",
        "x": np.full(len(times), 54.0),
        "y": np.full(len(times), 0.5),
        "valid": np.ones(len(times), dtype=bool),
    }
    tracking = {
        name: {"time_ns": times, "entities": [entity]}
        for name in support.idsse.PERIODS
    }
    monkeypatch.setattr(support.concurrent, "load_native", lambda match: ({}, {}, tracking))
    monkeypatch.setattr(
        support.departure,
        "period_signs",
        lambda metadata, native: {(1, "attack"): 1},
    )
    rows = pd.DataFrame(
        [{
            "period": 1,
            "time_utc_ns": 3_000_000_000,
            "attacking_team": "attack",
            "attacker_key": "a1",
            "block_id": 0,
        }]
    )

    prepared = support.prepare_match("J03WMX", rows)
    assert np.array_equal(prepared.coordinates, np.asarray([[54.0, 0.5]]))
    assert prepared.coordinates[0, 0] > 52.5

    legal_grid = support.grid_points(support.config())
    point = np.asarray([[52.0, 0.5]])
    assert np.any(np.all(legal_grid == point[0], axis=1))
    metrics = support._support_metrics(
        support.cKDTree(point), point, prepared, h=2.5, truncate=2.0
    )
    expected_native_weight = np.exp(-0.5 * np.square(2.0 / 2.5))
    assert int(metrics["raw"][0]) == 1
    assert float(metrics["mass"][0]) == pytest.approx(expected_native_weight)


def test_grid_aggregation_profile_logic_and_determinism():
    cfg = _small_config()
    first = support.aggregate_support(_matches(), cfg)
    second = support.aggregate_support(_matches(), cfg)
    pd.testing.assert_frame_equal(first, second)
    support.validate_support_grid(first, cfg)
    at_origin = first[(first.grid_x_m == 0.0) & (first.grid_y_m == 0.0)].set_index("profile")
    assert bool(at_origin.loc["basic", "support_pass"])
    assert bool(at_origin.loc["conservative", "support_pass"])
    assert int(at_origin.loc["basic", "matches_supported"]) == 7
    assert int(at_origin.loc["basic", "minimum_match_block_count"]) == 4
    assert float(at_origin.loc["basic", "minimum_match_kish_row_weight_concentration_count"]) == pytest.approx(32.0)
    assert not any("effective_count" in column for column in first.columns)
    summary = support.summarize(first, cfg).set_index("profile")
    assert float(summary.loc["basic", "minimum_match_support_fraction"]) == pytest.approx(1.0)
    assert float(summary.loc["basic", "maximum_match_support_fraction"]) == pytest.approx(1.0)
    assert support.period_block_correction_audit(_matches(), first, cfg) == 0


def test_period_aware_temporal_block_keys_do_not_collapse_identical_half_blocks():
    points = np.asarray([[0.0, 0.0]])
    item = support.PreparedMatch(
        "J03WMX",
        np.asarray([[0.0, 0.0], [0.0, 0.0]]),
        np.asarray(["P1|100", "P2|100"], dtype=object),
        np.asarray(["P1|B3", "P2|B3"], dtype=object),
    )
    metrics = support._support_metrics(support.cKDTree(points), points, item, h=2.5, truncate=2.0)
    assert int(metrics["blocks"][0]) == 2


def test_penalty_boundary_flags_only_actual_penalty_area_segments():
    # Front line and its finite lateral extent.
    assert support._edge_flags(36.0, 0.0)[3]
    assert not support._edge_flags(36.0, 25.0)[3]
    # Side line and its finite longitudinal extent.
    assert support._edge_flags(45.0, 20.16)[3]
    assert not support._edge_flags(0.0, 20.16)[3]
    # The opposite goal's front/side segments use the same physical geometry.
    assert support._edge_flags(-36.0, -10.0)[3]
    assert support._edge_flags(-45.0, -20.16)[3]


def test_aggregate_schema_rejects_row_level_or_response_column():
    cfg = _small_config(); grid = support.aggregate_support(_matches(), cfg)
    support.validate_support_grid(grid, cfg)
    bad = grid.assign(response_2s_m=1.0)
    with pytest.raises(RuntimeError, match="schema differs"):
        support.validate_support_grid(bad, cfg)


def test_closed_preflight_package_is_compact_aggregate_only_and_provenanced():
    """Lock the committed support-only package without reading provider rows."""
    expected_files = {
        OUTPUT / "support_grid.parquet",
        OUTPUT / "support_profile_summary.csv",
        OUTPUT / "manifest.json",
        OUTPUT / "hard_qc.json",
        OUTPUT / "hashes.json",
        REPORT,
        FIGURES / "support_frontier.png",
        FIGURES / "support_mask.png",
    }
    assert all(path.is_file() for path in expected_files)

    cfg = support.config()
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    hashes = json.loads((OUTPUT / "hashes.json").read_text(encoding="utf-8"))
    hard_qc = json.loads((OUTPUT / "hard_qc.json").read_text(encoding="utf-8"))
    for name, expected in hashes.items():
        assert support.sha(OUTPUT / name) == expected
    assert manifest["protocol_sha256"] == support.sha(support.PROTOCOL)
    assert manifest["configuration_sha256"] == support.sha(support.CONFIG)
    assert manifest["source_sha256"] == support.sha(Path(support.__file__))
    assert manifest["support_grid_sha256"] == hashes["support_grid.parquet"]
    assert manifest["support_profile_summary_sha256"] == hashes["support_profile_summary.csv"]
    assert manifest["support_frontier_figure_sha256"] == support.sha(FIGURES / "support_frontier.png")
    assert manifest["support_mask_figure_sha256"] == support.sha(FIGURES / "support_mask.png")

    schema = pl.read_parquet_schema(OUTPUT / "support_grid.parquet")
    assert list(schema) == cfg["publication"]["support_grid_schema"]
    forbidden = cfg["publication"]["forbidden_field_tokens"]
    assert not [column for column in schema if any(token in column.lower() for token in forbidden)]
    compact = pl.read_parquet(
        OUTPUT / "support_grid.parquet",
        columns=["grid_x_m", "grid_y_m", "bandwidth_m", "profile"],
    )
    assert compact.height == (
        len(support.grid_points(cfg))
        * len(cfg["kernel"]["bandwidths_m"])
        * len(cfg["support_profiles"])
    ) == 85_680
    assert compact.unique().height == compact.height

    future = cfg["future_response_map_stage"]
    assert manifest["matches"] == list(support.MATCHES)
    assert cfg["source_population"]["matches"] == list(support.MATCHES)
    assert all(
        profile["matches_required"] == len(support.MATCHES)
        for profile in cfg["support_profiles"].values()
    )
    assert future["matches_required"] == len(support.MATCHES)
    assert manifest["recommendation"]["bandwidth_m"] == 7.5
    assert manifest["recommendation"]["profile"] == "conservative"
    assert future["bandwidths_m"] == {
        "primary": 7.5,
        "sensitivity": [5.0, 10.0],
        "instability_rule": "accept_absent_weak_or_unstable_pattern_without_changing_smoother",
    }
    assert future["support"]["primary_profile"] == "conservative"
    assert future["support"]["all_seven_matches_must_pass_local_mask"] is True
    assert manifest["response_fields_selected"] is False
    assert manifest["anchor_coordinates_serialized"] is False
    assert manifest["response_surface_rendered"] is False
    assert all(hard_qc[key] is False for key in ("response_fields_selected", "anchor_coordinates_serialized", "coordinate_clipping_applied"))
    assert hard_qc["aggregate_schema_allowlist"] is True
    assert hard_qc["seven_matches_exact"] is True

    report = REPORT.read_text(encoding="utf-8")
    for key in ("protocol_sha256", "configuration_sha256", "source_sha256", "support_grid_sha256"):
        assert manifest[key] in report


@pytest.mark.provider_data
def test_real_idsse_registry_and_coordinate_preparation_are_response_blind():
    """One local provider gate: no response field is selected or serialized."""
    cfg = support.config()
    registry = support._registry(cfg)
    rows = registry[registry.match_id == support.MATCHES[0]].head(1).reset_index(drop=True)
    prepared = support.prepare_match(support.MATCHES[0], rows)
    assert prepared.coordinates.shape == (1, 2)
    assert np.isfinite(prepared.coordinates).all()
