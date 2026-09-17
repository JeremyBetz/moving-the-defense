import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import skillcorner_additional_directional_support_preflight_v1 as audit


class Source:
    pass


def source(timestamp="0:00.0"):
    item = Source()
    item.match_id = 1874553
    item.meta = {"id": item.match_id, "status": "played", "pitch_length": 105, "pitch_width": 68,
                 "home_team": {"id": 1}, "away_team": {"id": 2},
                 "home_team_side": ["left_to_right", "right_to_left"],
                 "players": [{"id": i, "team_id": 1 if i <= 11 else 2,
                              "player_role": {"id": 0 if i in (1, 12) else 1},
                              "playing_time": {"total": {"start_frame": 0, "end_frame": 1}}}
                             for i in range(1, 23)]}
    players = [{"player_id": i, "x": float(i), "y": float(i), "is_detected": True} for i in range(1, 23)]
    item.rows = {0: {"frame": 0, "period": 1, "timestamp": timestamp, "player_data": players,
                     "ball_data": {"x": 0.0, "y": 0.0, "is_detected": True}, "possession": {"group": "home team"}},
                 10: {"frame": 10, "period": 2, "timestamp": "45:00.0", "player_data": copy.deepcopy(players),
                      "ball_data": {"x": 0.0, "y": 0.0, "is_detected": True}, "possession": {"group": "away team"}}}
    item.period_frames = {1: [0], 2: [10]}
    item.player_team = {i: 1 if i <= 11 else 2 for i in range(1, 23)}
    item.phase_coverage = {0, 10}
    item.provider_equivalence = lambda: {"pass": True}
    return item


def test_population_partition_is_exact():
    config = json.loads(audit.CONFIG.read_text())
    population = config["existing_formal_matches"] + config["previously_excluded_matches"] + config["candidate_matches"]
    assert len(population) == len(set(population)) == 20
    assert len(config["candidate_matches"]) == 10


def test_finite_native_clock_passes():
    assert audit.audit_source(source())["clock_valid"] is True


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_native_clock_fails(value):
    with pytest.raises(audit.AuditError, match="nonfinite"):
        audit.audit_source(source(f"0:{value}"))


def test_clock_mismatch_fails():
    with pytest.raises((audit.AuditError, ValueError), match="clock|timestamp"):
        audit.audit_source(source("0:00.1"))


def test_missing_detection_flag_fails():
    item = source(); del item.rows[0]["player_data"][0]["is_detected"]
    with pytest.raises(audit.AuditError, match="detection"):
        audit.audit_source(item)


def test_absent_ball_coordinate_does_not_require_detection_status():
    item = source()
    item.rows[0]["ball_data"] = {"x": None, "y": None, "is_detected": None}
    assert audit.audit_source(item)["ball_support"] is True


def test_no_outcome_vocabulary_or_execution_dependency():
    text = Path(audit.__file__).read_text()
    for forbidden in ("construct_row(", "construct_match(", "fit_equal_match_ols(", "bootstrap("):
        assert forbidden not in text
