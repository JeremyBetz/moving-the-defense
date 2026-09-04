"""Outcome-blind active-roster support helpers for prospective DRD v2.

These functions contain no response outcome, model, prediction, or retrieval
logic.  They distinguish a complete current on-pitch attacking set from the
v1 assumption that the set must always contain exactly ten outfield players.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

import numpy as np


def active_outfield_at_anchor(
    starting_outfield: Iterable[str],
    roster_events: Sequence[Mapping[str, object]],
    anchor_ns: int,
) -> tuple[str, ...]:
    """Apply substitutions and confirmed player dismissals through an anchor.

    Events use ``kind`` equal to ``substitution`` or ``dismissal``. A
    substitution requires ``player_out`` and ``player_in``; a dismissal
    requires ``player``. Events after the anchor are ignored.
    """
    active = {str(player) for player in starting_outfield}
    if len(active) != 10:
        raise ValueError("exactly ten starting outfield players are required")
    ordered = sorted(roster_events, key=lambda event: (int(event["time_ns"]), str(event.get("event_id", ""))))
    for event in ordered:
        if int(event["time_ns"]) > int(anchor_ns):
            break
        kind = str(event["kind"])
        if kind == "substitution":
            player_out, player_in = str(event["player_out"]), str(event["player_in"])
            if player_out not in active or player_in in active:
                raise ValueError("ambiguous substitution registry")
            active.remove(player_out); active.add(player_in)
        elif kind == "dismissal":
            player = str(event["player"])
            if player not in active:
                raise ValueError("ambiguous dismissal registry")
            active.remove(player)
        else:
            raise ValueError(f"unsupported roster event kind: {kind}")
    if not 2 <= len(active) <= 10:
        raise ValueError("at least two and no more than ten active outfield players are required")
    return tuple(sorted(active))


def active_set_support_is_complete(
    active_outfield: Sequence[str],
    complete_tracking_outfield: Sequence[str],
) -> bool:
    """Require exact agreement between event-defined and tracking-complete sets."""
    active = tuple(sorted(str(player) for player in active_outfield))
    complete = tuple(sorted(str(player) for player in complete_tracking_outfield))
    return bool(len(active) == len(set(active)) and active == complete)


def active_ball_nearest_attacker(
    active_positions: Mapping[str, Sequence[float]],
    ball_position: Sequence[float],
) -> str:
    """Return ball-nearest active attacker with the frozen lexical tie-break."""
    if not 2 <= len(active_positions) <= 10:
        raise ValueError("a complete active attacking outfield set is required")
    ball = np.asarray(ball_position, dtype=float)
    if ball.shape != (2,) or not np.isfinite(ball).all():
        raise ValueError("finite two-dimensional ball position is required")
    ranked = []
    for player, position in active_positions.items():
        xy = np.asarray(position, dtype=float)
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError("every active player position must be finite")
        ranked.append((float(np.linalg.norm(xy - ball)), str(player)))
    return min(ranked, key=lambda item: (item[0], item[1]))[1]
