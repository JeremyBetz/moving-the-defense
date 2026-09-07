"""Synthetic pre-response contracts for the frozen IDSSE response-map v1."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import localized_reorganization_response_map_v1 as response_map  # noqa: E402


def _cfg() -> dict:
    return copy.deepcopy(response_map.load_config())


def _response_rows(values: list[float] | None = None) -> pd.DataFrame:
    values = values or [3.0, 6.0, 9.0, 4.0, 8.0, 12.0, 16.0]
    return pd.DataFrame({
        "observation_id": ["a"] * 7,
        "distance_rank": list(range(1, 8)),
        "response_2s_m": values,
    })


def _small_cfg() -> dict:
    cfg = _cfg()
    cfg["grid"]["legal_cells"] = 2
    cfg["support"]["valid_cells_by_bandwidth"] = {"5.0": 1, "7.5": 1, "10.0": 1}
    cfg["support"]["common_intersection_cells"] = 1
    return cfg


def _small_masks() -> dict[float, pd.DataFrame]:
    return {
        h: pd.DataFrame({
            "grid_x_m": [0.0, 1.0], "grid_y_m": [0.0, 0.0], "bandwidth_m": [h, h],
            "profile": ["conservative", "conservative"], "support_pass": [True, False],
        })
        for h in (5.0, 7.5, 10.0)
    }


def test_exact_authorized_response_request_rejects_alternatives_and_wildcards():
    cfg = _cfg()
    assert response_map.authorized_response_columns(cfg) == ("observation_id", "distance_rank", "response_2s_m")
    response_map.validate_response_request(("observation_id", "distance_rank", "response_2s_m"), cfg)
    with pytest.raises(response_map.ResponseMapInvalid, match="unauthorized"):
        response_map.validate_response_request(("observation_id", "distance_rank", "response_1s_m"), cfg)
    with pytest.raises(response_map.ResponseMapInvalid, match="unauthorized"):
        response_map.validate_response_request(("*",), cfg)


def test_y_oracle_is_exact_near_minus_middle_rank_mean():
    outcome = response_map.construct_anchor_y(_response_rows(), expected_observation_ids=["a"])
    assert outcome.to_dict("records") == [{"observation_id": "a", "y_m": pytest.approx(6.0 - 10.0)}]


@pytest.mark.parametrize("mutator", [
    lambda frame: frame.assign(response_2s_m=[3, 6, np.nan, 4, 8, 12, 16]),
    lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True),
    lambda frame: frame.iloc[:-1].copy(),
])
def test_missing_nonfinite_or_duplicate_required_rank_fails_closed(mutator):
    with pytest.raises(response_map.ResponseMapInvalid):
        response_map.construct_anchor_y(mutator(_response_rows()), expected_observation_ids=["a"])


def test_incomplete_identity_join_fails_closed():
    with pytest.raises(response_map.ResponseMapInvalid, match="join"):
        response_map.construct_anchor_y(_response_rows(), expected_observation_ids=["a", "b"])


def test_gaussian_oracle_and_hard_truncation():
    weights = response_map.gaussian_weights(np.asarray([0.0, 2.0, 4.0, 4.01]), 2.0, 2.0)
    assert weights[0] == pytest.approx(1.0)
    assert weights[1] == pytest.approx(np.exp(-0.5))
    assert weights[2] == pytest.approx(np.exp(-2.0))
    assert weights[3] == 0.0


def test_equal_match_surface_is_not_row_pooled_when_sample_sizes_differ():
    grid = np.asarray([[0.0, 0.0]])
    many_zero = (np.zeros((100, 2)), np.zeros(100))
    one_ten = (np.zeros((1, 2)), np.asarray([10.0]))
    surface, denominators = response_map.equal_match_surface(
        {"m1": many_zero, "m2": one_ten}, grid, 5.0, 2.0, ("m1", "m2")
    )
    assert surface[0] == pytest.approx(5.0)
    assert surface[0] != pytest.approx(10.0 / 101.0)
    assert all(value[0] > 0 for value in denominators.values())


def test_saved_masks_route_each_bandwidth_and_lock_common_intersection():
    cfg = _small_cfg()
    grid = pd.concat(list(_small_masks().values()), ignore_index=True)
    selected = response_map.select_frozen_masks(grid, cfg)
    assert set(selected) == {5.0, 7.5, 10.0}
    assert all(int(mask.support_pass.sum()) == 1 for mask in selected.values())
    broken = grid.copy(); broken.loc[(broken.bandwidth_m == 7.5) & (broken.grid_x_m == 0), "support_pass"] = False
    with pytest.raises(response_map.ResponseMapInvalid, match="valid-cell count"):
        response_map.select_frozen_masks(broken, cfg)


def test_native_out_of_pitch_coordinate_contributes_without_clipping():
    mean, denominator = response_map.one_match_local_mean(
        np.asarray([[54.0, 0.0]]), np.asarray([8.0]), np.asarray([[52.0, 0.0]]), 2.5, 2.0
    )
    assert denominator[0] == pytest.approx(np.exp(-0.5 * (2.0 / 2.5) ** 2))
    assert mean[0] == pytest.approx(8.0)


def test_weighted_inverse_ecdf_uses_equal_match_anchor_weight_and_no_interpolation():
    values = pd.DataFrame({
        "match_id": ["m1", "m1", "m1", "m2"],
        "observation_id": ["a", "b", "c", "d"],
        "y_m": [0.0, 1.0, 2.0, 100.0],
    })
    # m1 contributes 1/2 in total and m2 contributes 1/2 despite its one row.
    assert response_map.weighted_inverse_ecdf_limit(values, ("m1", "m2")) == 100.0


def test_weighted_inverse_ecdf_uses_observed_tied_value_without_interpolation():
    values = pd.DataFrame({
        "match_id": ["m1", "m1", "m2", "m2"],
        "observation_id": ["a", "b", "c", "d"],
        "y_m": [1.0, -2.0, 2.0, -2.0],
    })
    # The 0.95 crossing is the tied observed magnitude 2.0, never an
    # interpolated value between observations.
    assert response_map.weighted_inverse_ecdf_limit(values, ("m1", "m2")) == 2.0


def test_degenerate_scale_and_saturation_rules():
    assert response_map.scale_state(0.0, [np.asarray([0.0, 0.0])]) == "VALID_BUT_UNINFORMATIVE"
    assert response_map.scale_state(0.0, [np.asarray([0.0, 0.1])]) == "INVALID"
    assert response_map.saturation_counts(np.asarray([-2.0, -1.0, 0.0, 1.0, 2.0]), 1.0) == (1, 1)


def test_compact_aggregate_schema_and_synthetic_csv_svg_png_are_deterministic(tmp_path):
    cfg = _small_cfg(); masks = _small_masks()
    surfaces = {h: np.asarray([float(h), np.nan]) for h in masks}
    aggregate = response_map.assemble_aggregate_grid(masks, surfaces, cfg)
    assert list(aggregate.columns) == cfg["outputs"]["aggregate_response_grid_schema"]
    assert aggregate.support_valid.sum() == 3
    assert aggregate.equal_match_local_mean_m.notna().sum() == 3
    with pytest.raises(response_map.ResponseMapInvalid):
        response_map.validate_aggregate_schema(aggregate.assign(observation_id="forbidden"), cfg, "aggregate_response_grid_schema")

    first_csv, second_csv = tmp_path / "one.csv", tmp_path / "two.csv"
    response_map._write_csv(aggregate, first_csv, cfg["outputs"]["aggregate_response_grid_schema"])
    response_map._write_csv(aggregate, second_csv, cfg["outputs"]["aggregate_response_grid_schema"])
    assert first_csv.read_bytes() == second_csv.read_bytes()

    first_json, second_json = tmp_path / "one.json", tmp_path / "two.json"
    response_map._write_json(first_json, {"z": [2, 1], "a": "stable"})
    response_map._write_json(second_json, {"z": [2, 1], "a": "stable"})
    assert first_json.read_bytes() == second_json.read_bytes()

    first, second = tmp_path / "first" / "response_map", tmp_path / "second" / "response_map"
    response_map.render_response_map(aggregate, 10.0, cfg, first)
    response_map.render_response_map(aggregate, 10.0, cfg, second)
    for suffix in (".png", ".svg"):
        assert first.with_suffix(suffix).read_bytes() == second.with_suffix(suffix).read_bytes()


def test_source_default_path_requires_explicit_future_execution_gate():
    source = Path(response_map.__file__).read_text(encoding="utf-8")
    assert "--execute-response" in source
    assert "response access is disabled by default" in source
    assert "authorization_reference" in source


def test_config_freezes_nonbinary_status_and_no_response_access():
    cfg = _cfg()
    assert cfg["statuses"]["valid"] == "DESCRIPTIVE RESPONSE MAP EXECUTED — QC PASSED"
    assert cfg["statuses"]["invalid"] == "DESCRIPTIVE RESPONSE MAP INVALID"
    assert cfg["publication"]["row_level_y_serialized"] is False
    assert cfg["publication"]["per_match_surfaces_serialized"] is False
    assert json.loads(json.dumps(cfg))["protected_source"]["registry_sha256"] == "3c8a50cfa07f034b4428e280ecc6fcf7df423ed4dacad86b0862ba1e7d6716d2"
