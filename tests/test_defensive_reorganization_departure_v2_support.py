import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_departure_v2_support import (  # noqa: E402
    active_ball_nearest_attacker,
    active_outfield_at_anchor,
    active_set_support_is_complete,
)


STARTERS = tuple(f"A{i:02d}" for i in range(10))


def test_substitution_preserves_ten_player_active_set():
    events = [{"kind": "substitution", "time_ns": 100, "event_id": "1", "player_out": "A09", "player_in": "A10"}]
    active = active_outfield_at_anchor(STARTERS, events, 100)
    assert len(active) == 10 and "A09" not in active and "A10" in active


def test_confirmed_dismissal_produces_complete_nine_player_set():
    events = [{"kind": "dismissal", "time_ns": 100, "event_id": "1", "player": "A09"}]
    active = active_outfield_at_anchor(STARTERS, events, 100)
    assert len(active) == 9 and "A09" not in active


def test_future_dismissal_does_not_change_pre_anchor_set():
    events = [{"kind": "dismissal", "time_ns": 101, "event_id": "1", "player": "A09"}]
    assert active_outfield_at_anchor(STARTERS, events, 100) == STARTERS


def test_ambiguous_roster_event_fails_closed():
    with pytest.raises(ValueError):
        active_outfield_at_anchor(STARTERS, [{"kind": "dismissal", "time_ns": 1, "player": "BENCH"}], 1)


def test_tracking_support_must_equal_complete_active_set():
    active = STARTERS[:-1]
    assert active_set_support_is_complete(active, active)
    assert not active_set_support_is_complete(active, active[:-1])
    assert not active_set_support_is_complete(active, (*active, "BENCH"))


def test_ball_nearest_uses_every_active_player_and_lexical_tie_break():
    positions = {player: (float(index + 2), 0.0) for index, player in enumerate(STARTERS[:-1])}
    positions["A00"], positions["A01"] = (-1.0, 0.0), (1.0, 0.0)
    assert active_ball_nearest_attacker(positions, (0.0, 0.0)) == "A00"


def test_ball_nearest_rejects_set_without_an_off_ball_candidate():
    with pytest.raises(ValueError):
        active_ball_nearest_attacker({"A0": (0.0, 0.0)}, (0.0, 0.0))
