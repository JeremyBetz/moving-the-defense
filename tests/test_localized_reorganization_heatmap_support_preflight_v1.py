"""Synthetic and provider-gated checks for the response-blind support preflight."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import localized_reorganization_heatmap_support_preflight_v1 as support  # noqa: E402


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


@pytest.mark.provider_data
def test_real_idsse_registry_and_coordinate_preparation_are_response_blind():
    """One local provider gate: no response field is selected or serialized."""
    cfg = support.config()
    registry = support._registry(cfg)
    rows = registry[registry.match_id == support.MATCHES[0]].head(1).reset_index(drop=True)
    prepared = support.prepare_match(support.MATCHES[0], rows)
    assert prepared.coordinates.shape == (1, 2)
    assert np.isfinite(prepared.coordinates).all()
