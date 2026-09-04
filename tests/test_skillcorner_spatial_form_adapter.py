import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.skillcorner_spatial_form_adapter import (
    active_outfield_player_ids,
    anchor_frames,
    attacking_frame,
    canonical_xy,
    goalward_sign,
    identity_step_is_valid,
    required_frame_ids,
    stricter_quality_pass,
    timestamp_seconds,
)


def _player(pid, team, role, start, end):
    return {
        "id": pid,
        "team_id": team,
        "player_role": {"id": role},
        "playing_time": {"total": {"start_frame": start, "end_frame": end}},
    }


def test_native_time_and_physical_windows_are_exact():
    assert timestamp_seconds("00:00:04.00", 1) == 4.0
    assert timestamp_seconds("00:45:04.00", 2) == 4.0
    assert anchor_frames(10, 100) == (50,)
    required = required_frame_ids(50)
    assert required[0] == 9
    assert required[-1] == 71
    assert len(required) == 63


def test_canonical_coordinate_scaling_is_center_preserving():
    assert np.array_equal(canonical_xy(0.0, 0.0, 104.0, 68.0), [0.0, 0.0])
    assert np.allclose(canonical_xy(52.0, 34.0, 104.0, 68.0), [52.5, 34.0])


def test_goalward_and_outward_rules_are_start_fixed():
    sides = ["right_to_left", "left_to_right"]
    assert goalward_sign(sides, 1, True) == -1
    assert goalward_sign(sides, 1, False) == 1
    points = np.asarray([[10.0, -5.0], [8.0, -8.0]])
    transformed = attacking_frame(points, -1, focal_start_y_m=-5.0)
    assert np.array_equal(transformed, [[-10.0, 5.0], [-8.0, 8.0]])
    assert transformed[1, 1] - transformed[0, 1] == 3.0


def test_active_roster_uses_playing_intervals_and_excludes_goalkeeper():
    metadata = {"players": [
        _player(1, 10, 0, 0, 100),
        _player(2, 10, 4, 0, 49),
        _player(3, 10, 4, 50, 100),
        _player(4, 11, 4, 0, 100),
    ]}
    assert active_outfield_player_ids(metadata, 49, 10) == (2,)
    assert active_outfield_player_ids(metadata, 50, 10) == (3,)


def test_quality_and_identity_rules_fail_closed_at_exact_boundaries():
    majority = [True, True, False, False]
    assert stricter_quality_pass(majority, majority, [majority] * 7)
    assert not stricter_quality_pass([True, False, False], majority, [majority] * 7)
    assert identity_step_is_valid([0.0, 0.0], [1.5, 0.0])
    assert not identity_step_is_valid([0.0, 0.0], [1.5000001, 0.0])
