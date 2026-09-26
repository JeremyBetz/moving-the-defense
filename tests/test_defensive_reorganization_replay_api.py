from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_replay import PLAYER_SCORE_COLUMNS, TEAM_SCORE_COLUMNS
from defensive_reorganization_replay_api import (
    API_SCHEMA_VERSION,
    ReplayAPIError,
    main,
    score_request,
)


def tracking_rows(frames: int = 25) -> list[dict]:
    rows = []
    for frame in range(frames):
        for player in range(10):
            rows.append(
                {
                    "match_id": "synthetic",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": frame / 10,
                    "entity_type": "player",
                    "team_key": "D",
                    "player_key": f"D{player}",
                    "x_m": float(player + (frame / 10 if player == 0 else 0)),
                    "y_m": float(player),
                    "coordinate_valid": True,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                    "response_2s_m": 999.0,
                }
            )
        rows.append(
            {
                "match_id": "synthetic",
                "period": 1,
                "frame_id_provider": str(frame),
                "time_match_s": frame / 10,
                "entity_type": "ball",
                "team_key": None,
                "player_key": None,
                "x_m": 0.0,
                "y_m": 0.0,
                "coordinate_valid": True,
                "pitch_length_m": 105.0,
                "pitch_width_m": 68.0,
                "response_2s_m": 999.0,
            }
        )
    return rows


def request() -> dict:
    return {
        "schema_version": API_SCHEMA_VERSION,
        "spec": {
            "defending_team_key": "D",
            "source_fps": 10.0,
            "window_seconds": 1.0,
            "smoothing_frames": 3,
            "smoothing_method": "centered_mean",
        },
        "tracking": tracking_rows(),
    }


def test_api_delegates_to_frozen_score_and_exposes_only_allowlisted_outputs():
    response = score_request(request())
    assert response["schema_version"] == API_SCHEMA_VERSION
    assert response["units"] == "metres"
    assert response["player_score_columns"] == list(PLAYER_SCORE_COLUMNS)
    assert response["team_score_columns"] == list(TEAM_SCORE_COLUMNS)
    assert len(response["player_scores"]) == 250
    assert len(response["team_scores"]) == 25
    assert "response_2s_m" not in json.dumps(response)
    supported = [row for row in response["player_scores"] if row["support_status"] == "supported"]
    assert supported
    assert max(row["trailing_relative_path_m"] for row in supported) == pytest.approx(1.0)


def test_api_is_deterministic_under_tracking_row_shuffle():
    first = request()
    shuffled = request()
    shuffled["tracking"] = pd.DataFrame(shuffled["tracking"]).sample(frac=1, random_state=7).to_dict("records")
    assert score_request(first) == score_request(shuffled)


def test_optional_time_range_filters_outputs_after_full_support_scoring():
    payload = request()
    payload["time_range"] = {"start_time_s": 1.1, "end_time_s": 1.3}
    response = score_request(payload)
    assert {row["time_match_s"] for row in response["team_scores"]} == {1.1, 1.2, 1.3}
    assert len(response["player_scores"]) == 30
    assert all(row["support_status"] == "supported" for row in response["player_scores"])


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda p: p.update(extra=True), "request keys"),
        (lambda p: p.__setitem__("schema_version", "2.0"), "schema_version"),
        (lambda p: p["spec"].update(outcome="Y"), "unsupported spec"),
        (lambda p: p.__setitem__("tracking", []), "nonempty"),
    ],
)
def test_api_fails_closed_on_contract_changes(mutation, message):
    payload = request()
    mutation(payload)
    with pytest.raises(ReplayAPIError, match=message):
        score_request(payload)


def test_missing_support_serializes_as_json_null():
    response = score_request(request())
    assert response["player_scores"][0]["trailing_relative_path_m"] is None
    assert response["team_scores"][0]["mean_trailing_relative_path_m"] is None
    json.dumps(response, allow_nan=False)


def test_cli_writes_strict_json(tmp_path):
    request_path = tmp_path / "request.json"
    output_path = tmp_path / "response.json"
    request_path.write_text(json.dumps(request()), encoding="utf-8")
    assert main([str(request_path), "--output", str(output_path)]) == 0
    response = json.loads(output_path.read_text(encoding="utf-8"))
    assert response["measurement"] == "trailing_defender_relative_path"
