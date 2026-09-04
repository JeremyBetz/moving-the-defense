"""Outcome-blind SkillCorner compatibility helpers for Spatial Form v1.

This module contains provider/time/coordinate/support rules only.  It does not
construct the localized defensive-reorganization target or fit any model.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable, Mapping, Sequence

import numpy as np


NATIVE_HZ = 10
CANONICAL_PITCH_LENGTH_M = 105.0
CANONICAL_PITCH_WIDTH_M = 68.0
SMOOTHER_FRAMES = 3
SMOOTHER_EDGE_FRAMES = 1
MAX_IDENTITY_STEP_M = 1.5
QUALITY_DETECTED_FRACTION = 0.5


def timestamp_seconds(timestamp: str, period: int) -> float:
    """Return period-relative seconds from the provider match-clock string."""
    parts = [float(value) for value in timestamp.split(":")]
    if len(parts) == 2:
        total = 60.0 * parts[0] + parts[1]
    elif len(parts) == 3:
        total = 3600.0 * parts[0] + 60.0 * parts[1] + parts[2]
    else:
        raise ValueError("unsupported SkillCorner timestamp")
    if period == 1:
        return total
    if period == 2:
        return total - 45.0 * 60.0
    raise ValueError("Spatial Form external v1 supports periods 1 and 2 only")


def canonical_xy(
    x_m: float,
    y_m: float,
    pitch_length_m: float,
    pitch_width_m: float,
) -> np.ndarray:
    """Scale centred native metres to the governed centred 105 x 68 m pitch."""
    if pitch_length_m <= 0.0 or pitch_width_m <= 0.0:
        raise ValueError("pitch dimensions must be positive")
    return np.asarray(
        [
            float(x_m) * CANONICAL_PITCH_LENGTH_M / float(pitch_length_m),
            float(y_m) * CANONICAL_PITCH_WIDTH_M / float(pitch_width_m),
        ],
        dtype=np.float64,
    )


def goalward_sign(home_team_side: Sequence[str], period: int, is_home: bool) -> int:
    """Map the provider's period-specific home direction to a team sign."""
    if period not in (1, 2) or len(home_team_side) < period:
        raise ValueError("missing period-specific home-team direction")
    side = home_team_side[period - 1]
    if side not in {"left_to_right", "right_to_left"}:
        raise ValueError("unsupported SkillCorner direction label")
    home_sign = 1 if side == "left_to_right" else -1
    return home_sign if is_home else -home_sign


def attacking_frame(
    points_xy: np.ndarray,
    attack_sign: int,
    focal_start_y_m: float,
) -> np.ndarray:
    """Apply the unchanged goalward and start-side normalization."""
    if attack_sign not in (-1, 1):
        raise ValueError("attack_sign must be -1 or 1")
    values = np.asarray(points_xy, dtype=np.float64).copy()
    values[:, 0] *= attack_sign
    if focal_start_y_m < 0.0:
        values[:, 1] *= -1.0
    return values


def active_outfield_player_ids(metadata: Mapping, frame_id: int, team_id: int) -> tuple[int, ...]:
    """Use provider playing intervals and role metadata, never coordinate presence."""
    active: list[int] = []
    for player in metadata["players"]:
        if int(player["team_id"]) != int(team_id):
            continue
        if int(player["player_role"]["id"]) == 0:
            continue
        playing = player.get("playing_time")
        if not playing or not playing.get("total"):
            continue
        total = playing["total"]
        if int(total["start_frame"]) <= int(frame_id) <= int(total["end_frame"]):
            active.append(int(player["id"]))
    return tuple(sorted(active))


def anchor_frames(period_start_frame: int, period_end_frame: int) -> tuple[int, ...]:
    """Period origin + 4 + 4k seconds with complete primary/smoother support."""
    first = int(period_start_frame) + 4 * NATIVE_HZ
    last = int(period_end_frame) - 2 * NATIVE_HZ - SMOOTHER_EDGE_FRAMES
    return tuple(range(first, last + 1, 4 * NATIVE_HZ))


def required_frame_ids(anchor_frame: int) -> tuple[int, ...]:
    """Raw frames required by [t-4,t+2] and the centred three-frame smoother."""
    return tuple(
        range(
            int(anchor_frame) - 4 * NATIVE_HZ - SMOOTHER_EDGE_FRAMES,
            int(anchor_frame) + 2 * NATIVE_HZ + SMOOTHER_EDGE_FRAMES + 1,
        )
    )


def detected_fraction(flags: Iterable[bool]) -> float:
    values = tuple(flags)
    if not values or not all(isinstance(value, (bool, np.bool_)) for value in values):
        raise ValueError("detected status must be a nonempty Boolean sequence")
    return float(np.mean(values))


def stricter_quality_pass(
    focal_flags: Iterable[bool],
    ball_flags: Iterable[bool],
    defender_flag_sequences: Iterable[Iterable[bool]],
) -> bool:
    defenders = tuple(tuple(flags) for flags in defender_flag_sequences)
    return (
        detected_fraction(focal_flags) >= QUALITY_DETECTED_FRACTION
        and detected_fraction(ball_flags) >= QUALITY_DETECTED_FRACTION
        and len(defenders) == 7
        and all(detected_fraction(flags) >= QUALITY_DETECTED_FRACTION for flags in defenders)
    )


def identity_step_is_valid(point_a: Sequence[float], point_b: Sequence[float]) -> bool:
    """Fail closed when an adjacent native 0.1 s player step exceeds 1.5 m."""
    a = np.asarray(point_a, dtype=np.float64)
    b = np.asarray(point_b, dtype=np.float64)
    return bool(
        np.isfinite(a).all()
        and np.isfinite(b).all()
        and np.linalg.norm(b - a) <= MAX_IDENTITY_STEP_M
    )
