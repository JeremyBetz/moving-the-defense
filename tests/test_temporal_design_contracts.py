"""Synthetic production-path contracts for frozen temporal constructions."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacker_defender_bridge_game1_v1 as bridge
import attacking_continuous_movement_game1_v1 as movement
import spatial_defensive_response_footprint_idsse_v1 as idsse_footprint


def _player(key: str, team: str, coefficient: float, times: np.ndarray, *, split: bool = False) -> movement.PlayerPeriod:
    positions = np.column_stack([coefficient * times**2, np.full(len(times), float(coefficient))])
    cumulative = movement.cumulative_path(positions)
    block = movement.SmoothBlock(
        block_id=f"{key}:0", player_key=key, team_key=team, period=1,
        raw_start_index=0, raw_end_index=len(times) - 1, center_indices=np.arange(len(times)),
        times_period_s=times, positions25=positions, cumulative25=cumulative,
        positions10=np.empty((0, 2)), cumulative10=np.empty(0), ticks10=np.empty(0, dtype=int), tick10_to_index={},
    )
    center_to_block = {index: (0, index) for index in range(len(times))}
    if split:
        for index in range(len(times) // 2, len(times)):
            center_to_block[index] = (1, index - len(times) // 2)
        second = movement.SmoothBlock(
            block_id=f"{key}:1", player_key=key, team_key=team, period=1,
            raw_start_index=len(times) // 2, raw_end_index=len(times) - 1,
            center_indices=np.arange(len(times) // 2, len(times)), times_period_s=times[len(times) // 2:],
            positions25=positions[len(times) // 2:], cumulative25=movement.cumulative_path(positions[len(times) // 2:]),
            positions10=np.empty((0, 2)), cumulative10=np.empty(0), ticks10=np.empty(0, dtype=int), tick10_to_index={},
        )
        blocks = [block, second]
    else:
        blocks = [block]
    return movement.PlayerPeriod(
        player_key=key, team_key=team, player_number=key.rsplit(":", 1)[-1], period=1,
        frame_ids=np.arange(len(times)), time_period_s=times, time_match_s=times,
        raw_xy=positions, raw_valid_base=np.ones(len(times), dtype=bool), registry_invalid=np.zeros(len(times), dtype=bool),
        continuity_links=np.ones(len(times), dtype=bool), blocks=blocks, center_to_block=center_to_block,
    )


def _quadratic_path(coefficient: float, start: float, end: float) -> float:
    return abs(coefficient) * (end**2 - start**2)


def _metrica_fixture(monkeypatch, tmp_path: Path):
    times = np.arange(0.0, 6.0 + movement.RAW_DT_S / 2, movement.RAW_DT_S)
    attacker_key, attack_team, defend_team = "metrica:Home:1", "metrica:Home", "metrica:Away"
    pps = [_player(attacker_key, attack_team, 1.0, times)]
    pps.extend(_player(f"metrica:Away:{number}", defend_team, float(number), times) for number in range(1, 11))
    period_frames = {1: {"origin_time_period_s": 0.0, "time_period_s": times, "time_match_s": times, "frame_ids": np.arange(len(times))}}
    features = pl.DataFrame([
        {"period": 1, "time_period_s": 4.0, "player_key": attacker_key, "path_length_m": 11.0, "delta_x_m": 1.0, "delta_y_m": 2.0, "straightness": 0.5, "straightness_valid": True},
        {"period": 1, "time_period_s": 6.0, "player_key": attacker_key, "path_length_m": 29.0, "delta_x_m": 3.0, "delta_y_m": 4.0, "straightness": 0.6, "straightness_valid": True},
    ])
    output = tmp_path / "attacker"; output.mkdir()
    (output / "final_results.json").write_text(json.dumps({"classification": "A"}), encoding="utf-8")
    events = pd.DataFrame([{"Period": 1, "Type": "PASS", "Team": "Home", "Start Time [s]": 0.0, "Start Frame": 0, "Subtype": ""}])
    monkeypatch.setattr(bridge, "ATTACKER_OUTPUT", output)
    monkeypatch.setattr(bridge, "verify_hash_ledger", lambda *_: True)
    monkeypatch.setattr(bridge.attacker, "load_game1", lambda: (pps, period_frames, {"synthetic": True}))
    monkeypatch.setattr(bridge.pl, "read_parquet", lambda _: features)
    monkeypatch.setattr(bridge.pd, "read_csv", lambda _: events)
    return attacker_key


def test_metrica_segment_requires_exact_inclusive_same_block_support():
    times = np.arange(0.0, 4.0 + movement.RAW_DT_S / 2, movement.RAW_DT_S)
    exact = _player("metrica:Home:1", "metrica:Home", 1.0, times)
    left = bridge.segment(exact, 0.0, 2.0)
    right = bridge.segment(exact, 2.0, 4.0)
    assert left is not None and right is not None
    assert len(left) == 51 and len(right) == 51
    assert np.array_equal(left[-1], right[0])
    assert bridge.segment(exact, 0.0, 2.01) is None
    missing = _player("metrica:Home:2", "metrica:Home", 1.0, np.delete(times, 50))
    assert bridge.segment(missing, 0.0, 2.0) is None
    split = _player("metrica:Home:3", "metrica:Home", 1.0, times, split=True)
    assert bridge.segment(split, 1.0, 3.0) is None


def test_metrica_build_observations_uses_exact_chronological_windows(monkeypatch, tmp_path):
    _metrica_fixture(monkeypatch, tmp_path)
    data, linkage, excluded, counts, _ = bridge.build_observations()
    assert counts == {"candidate_endpoints": 1, "no_possession_endpoints": 0}
    assert excluded.empty and len(data) == 1 and len(linkage) == 10
    assert sorted(linkage.distance_rank) == list(range(1, 11))
    coefficient = {f"metrica:Away:{number}": float(number) for number in range(1, 11)}
    mean = np.mean(list(coefficient.values()))
    for row in linkage.itertuples(index=False):
        relative = abs(coefficient[row.defender_key] - (10 * mean - coefficient[row.defender_key]) / 9.0)
        assert np.isclose(row.prior_relative_path_m, _quadratic_path(relative, 0.0, 2.0))
        assert np.isclose(row.earlier_relative_path_m, _quadratic_path(relative, 2.0, 4.0))
        assert np.isclose(row.response_1s_m, _quadratic_path(relative, 4.0, 5.0))
        assert np.isclose(row.response_2s_m, _quadratic_path(relative, 4.0, 6.0))
    row = data.iloc[0]
    assert row.attacker_path_length_m == 11.0
    assert row.future_attacker_path_length_m == 29.0


def test_metrica_reverse_time_model_uses_future_attacker_path_and_pre_anchor_defense(monkeypatch, tmp_path):
    _metrica_fixture(monkeypatch, tmp_path)
    data, _, _, _, _ = bridge.build_observations()
    outcome, exposure, baseline = bridge.MODEL_SPECS["reverse_time_placebo"]
    x, y = bridge.design(data, outcome, exposure, baseline)
    row = data.iloc[0]
    assert y[0] == row.earlier_local_relative_path_m
    assert x[0, 1] == row.future_attacker_path_length_m == 29.0
    assert x[0, 2] == row.prior_local_relative_path_m
    assert y[0] != row.local_response_2s_m
    assert x[0, 1] != row.attacker_path_length_m


def _idsse_fixture():
    period = idsse_footprint.idsse.PERIODS[0]
    other_period = idsse_footprint.idsse.PERIODS[1]
    time_ns = np.arange(0, 10_120_000_000 + idsse_footprint.FRAME_NS, idsse_footprint.FRAME_NS, dtype=np.int64)
    seconds = time_ns / 1e9
    players = {"A1": SimpleNamespace(team_id="A", player_id="A1", goalkeeper=False)}
    players.update({f"D{number}": SimpleNamespace(team_id="B", player_id=f"D{number}", goalkeeper=False) for number in range(1, 11)})
    entities = []
    for key, player in players.items():
        coefficient = 1.0 if key == "A1" else float(key[1:])
        # Constant offsets make D10 nearest at t=8 while D1 becomes nearest
        # later; they cancel from all movement-path differences.
        anchor_delta = 0.0 if key == "D10" else float(key[1:]) if key != "A1" else 0.0
        offset = 0.0 if key == "A1" else anchor_delta - (coefficient - 1.0) * 64.0
        entities.append({"team_id": player.team_id, "person_id": key, "valid": np.ones(len(time_ns), dtype=bool), "x": coefficient * seconds**2 + offset, "y": np.zeros(len(time_ns))})
    empty = {"time_ns": np.asarray([0], dtype=np.int64), "entities": []}
    tracking = {period: {"time_ns": time_ns, "entities": entities}, other_period: empty}
    metadata = {"home_team_id": "A", "away_team_id": "B", "players": players}
    events = {"state_events": [{"time_ns": 0, "team_id": "A", "open_state": True}]}
    return metadata, events, tracking


def _fixture_order(tracking: dict, time_s: float) -> list[str]:
    period = idsse_footprint.idsse.PERIODS[0]
    pdata = tracking[period]
    index = int(np.flatnonzero(pdata["time_ns"] == int(time_s * 1e9))[0])
    entities = {(entity["team_id"], entity["person_id"]): entity for entity in pdata["entities"]}
    attacker = np.array([entities[("A", "A1")]["x"][index], entities[("A", "A1")]["y"][index]])
    return [key for _, key in sorted(
        (float(np.linalg.norm(np.array([entities[("B", f"D{number}")]["x"][index], entities[("B", f"D{number}")]["y"][index]]) - attacker)), f"D{number}")
        for number in range(1, 11)
    )]


def test_idsse_build_sample_uses_exact_prior_exposure_and_response_windows():
    metadata, events, tracking = _idsse_fixture()
    anchor_order = _fixture_order(tracking, 8.0)
    future_order = _fixture_order(tracking, 10.0)
    data, excluded = idsse_footprint.build_sample("SYN", metadata, events, tracking)
    assert len(data) == 10
    assert set(data.distance_rank) == set(range(1, 11))
    assert anchor_order == ["D10", *[f"D{number}" for number in range(1, 10)]]
    assert anchor_order != future_order
    assert data.sort_values("distance_rank").defender_key.tolist() == anchor_order
    assert excluded.to_dict("records") == [{"match_id": "SYN", "period": 1, "time_period_s": 4.0, "attacker_key": None, "reason": "complete_cadence_support_unavailable"}]
    coefficient = {f"D{number}": float(number) for number in range(1, 11)}
    mean = np.mean(list(coefficient.values()))
    for row in data.itertuples(index=False):
        relative = abs(coefficient[row.defender_key] - (10 * mean - coefficient[row.defender_key]) / 9.0)
        assert np.isclose(row.attacker_path_m, _quadratic_path(1.0, 6.0, 8.0))
        assert np.isclose(row.future_attacker_path_m, _quadratic_path(1.0, 8.0, 10.0))
        assert np.isclose(row.prior_relative_path_m, _quadratic_path(relative, 4.0, 6.0))
        assert np.isclose(row.earlier_relative_path_m, _quadratic_path(relative, 6.0, 8.0))
        assert np.isclose(row.response_1s_m, _quadratic_path(relative, 8.0, 9.0))
        assert np.isclose(row.response_2s_m, _quadratic_path(relative, 8.0, 10.0))


def test_idsse_placebo_stats_use_future_exposure_and_pre_anchor_outcome():
    data, _ = idsse_footprint.build_sample("SYN", *_idsse_fixture())
    # Deliberately break the quadratic proportionality so each placebo term has
    # a distinct sentinel from its forward-time counterpart.
    data = data.copy()
    data["future_attacker_path_m"] += 1.0
    data["earlier_relative_path_m"] += 1.0
    data["response_2s_m"] += 1.0
    primary_x = idsse_footprint.design(data, pooled=False)
    placebo = idsse_footprint.block_stats(data, primary_x, "placebo")
    _, (xtx, xty) = next(iter(placebo.items()))
    expected_x = primary_x.copy()
    for rank in range(10):
        expected_x[:, rank * 4 + 1] = data.future_attacker_path_m.to_numpy(float) * (data.distance_rank.to_numpy(int) == rank + 1)
    expected_y = data.earlier_relative_path_m.to_numpy(float)
    assert np.allclose(xtx, expected_x.T @ expected_x)
    assert np.allclose(xty, expected_x.T @ expected_y)
    for rank in range(10):
        row = data[data.distance_rank == rank + 1].iloc[0]
        exposure_column = rank * 4 + 1
        assert np.isclose(xtx[exposure_column, exposure_column], row.future_attacker_path_m**2)
        assert np.isclose(xty[exposure_column], row.future_attacker_path_m * row.earlier_relative_path_m)
        assert not np.isclose(xty[exposure_column], row.attacker_path_m * row.response_2s_m)
