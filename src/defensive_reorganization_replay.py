"""Provider-light scoring for retrospective defensive-reorganization replay.

The score in this module is a trailing visualization analogue of the frozen
forward response quantity.  It is accumulated defender-relative path in metres,
not an instantaneous, causal, tactical, or value measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping

import numpy as np
import pandas as pd


REQUIRED_TRACKING_COLUMNS = (
    "match_id",
    "period",
    "frame_id_provider",
    "time_match_s",
    "entity_type",
    "team_key",
    "player_key",
    "x_m",
    "y_m",
    "coordinate_valid",
    "pitch_length_m",
    "pitch_width_m",
)


PLAYER_SCORE_COLUMNS = (
    "match_id",
    "period",
    "frame_id_provider",
    "time_match_s",
    "team_key",
    "player_key",
    "trailing_relative_path_m",
    "support_status",
)

TEAM_SCORE_COLUMNS = (
    "match_id",
    "period",
    "frame_id_provider",
    "time_match_s",
    "team_key",
    "mean_trailing_relative_path_m",
    "supported_defender_count",
    "support_status",
)

SUPPORTED = "supported"
INSUFFICIENT_HISTORY = "insufficient_history"
INSUFFICIENT_FUTURE = "insufficient_future_smoother_support"
MISSING_COORDINATES = "missing_coordinate_support"


@dataclass(frozen=True)
class DefenderRelativePathSpec:
    """Frozen computation settings for one defending team."""

    defending_team_key: str
    source_fps: float
    window_seconds: float = 2.0
    smoothing_frames: int = 7
    smoothing_method: Literal["centered_mean"] = "centered_mean"

    def __post_init__(self) -> None:
        if not self.defending_team_key:
            raise ValueError("defending_team_key must be nonempty")
        if not np.isfinite(self.source_fps) or self.source_fps <= 0:
            raise ValueError("source_fps must be finite and positive")
        if not np.isfinite(self.window_seconds) or self.window_seconds <= 0:
            raise ValueError("window_seconds must be finite and positive")
        increments = self.window_seconds * self.source_fps
        if not np.isclose(increments, round(increments), atol=1e-10, rtol=0):
            raise ValueError("window_seconds * source_fps must be an integer")
        if self.smoothing_frames < 1 or self.smoothing_frames % 2 != 1:
            raise ValueError("smoothing_frames must be a positive odd integer")
        if self.smoothing_method != "centered_mean":
            raise ValueError("only centered_mean smoothing is supported")


@dataclass(frozen=True)
class DefensiveReorganizationScores:
    """Tidy scores plus deterministic metadata read-only at the top level."""

    player_scores: pd.DataFrame
    team_scores: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        if tuple(self.player_scores.columns) != PLAYER_SCORE_COLUMNS:
            raise ValueError("unexpected player-score schema")
        if tuple(self.team_scores.columns) != TEAM_SCORE_COLUMNS:
            raise ValueError("unexpected team-score schema")
        object.__setattr__(self, "player_scores", self.player_scores.copy(deep=True))
        object.__setattr__(self, "team_scores", self.team_scores.copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class DisplayNormalization:
    """Visual-only fixed-scale values; raw scientific scores remain unchanged."""

    normalized: np.ndarray
    clipped_m: np.ndarray
    saturation_count: int
    missing_count: int
    vmin_m: float
    vmax_m: float


def defender_relative_path_lengths(defender_trajectory_xy: np.ndarray) -> np.ndarray:
    """Return accumulated leave-one-out-relative path for ten defenders.

    Parameters
    ----------
    defender_trajectory_xy:
        Finite array with shape ``[frames, 10, 2]``. Coordinates must already
        be expressed in canonical metres and smoothed under the selected
        provider convention.
    """
    trajectory = np.asarray(defender_trajectory_xy, dtype=np.float64)
    if trajectory.ndim != 3 or trajectory.shape[1:] != (10, 2):
        raise ValueError("expected [frames, 10 defenders, xy]")
    if len(trajectory) < 2 or not np.isfinite(trajectory).all():
        raise ValueError("at least two complete finite defender frames are required")
    total = trajectory.sum(axis=1, keepdims=True)
    leave_one_out = (total - trajectory) / 9.0
    relative = trajectory - leave_one_out
    return np.linalg.norm(np.diff(relative, axis=0), axis=2).sum(axis=0)


def normalize_scores_for_display(
    values,
    *,
    vmin_m: float = 0.0,
    vmax_m: float = 4.0,
) -> DisplayNormalization:
    """Map raw metre scores to a fixed visual scale without changing them."""
    lower, upper = float(vmin_m), float(vmax_m)
    if not np.isfinite([lower, upper]).all() or not lower < upper:
        raise ValueError("display scale requires finite vmin_m < vmax_m")
    raw = np.asarray(values, dtype=np.float64)
    finite = np.isfinite(raw)
    clipped = np.full(raw.shape, np.nan, dtype=np.float64)
    normalized = np.full(raw.shape, np.nan, dtype=np.float64)
    clipped[finite] = np.clip(raw[finite], lower, upper)
    normalized[finite] = (clipped[finite] - lower) / (upper - lower)
    return DisplayNormalization(
        normalized=normalized,
        clipped_m=clipped,
        saturation_count=int(np.count_nonzero(finite & (raw > upper))),
        missing_count=int(np.count_nonzero(~finite)),
        vmin_m=lower,
        vmax_m=upper,
    )


def _validate_tracking(tracking: pd.DataFrame, spec: DefenderRelativePathSpec) -> pd.DataFrame:
    missing = set(REQUIRED_TRACKING_COLUMNS) - set(tracking.columns)
    if missing:
        raise ValueError(f"Missing normalized tracking columns: {sorted(missing)}")
    q = tracking.loc[:, list(REQUIRED_TRACKING_COLUMNS)].copy(deep=True)
    if q.empty:
        raise ValueError("tracking is empty")
    for column in ("match_id", "period", "frame_id_provider", "entity_type"):
        if q[column].isna().any():
            raise ValueError(f"normalized tracking contains null {column}")
    if not set(q["entity_type"].dropna().unique()) <= {"player", "ball"}:
        raise ValueError("entity_type must be player or ball")
    player_rows = q["entity_type"].eq("player")
    for column in ("player_key", "team_key"):
        if q.loc[player_rows, column].isna().any():
            raise ValueError(f"normalized player rows contain null {column}")
    if not np.allclose(q["pitch_length_m"].astype(float), 105.0) or not np.allclose(
        q["pitch_width_m"].astype(float), 68.0
    ):
        raise ValueError("Tracking must use a constant 105 x 68 m pitch")
    q["_entity_key"] = np.where(
        q["entity_type"].eq("ball"), "__ball__", q["player_key"].astype(str)
    )
    if q.duplicated(["match_id", "period", "frame_id_provider", "_entity_key"]).any():
        raise ValueError("Duplicate frame/entity rows")
    players = q.loc[q["entity_type"].eq("player")]
    identities = players.groupby(["match_id", "player_key"], dropna=False)["team_key"].nunique(
        dropna=False
    )
    if (identities != 1).any():
        raise ValueError("Player/team identity changes within a match")
    defenders = players.loc[players["team_key"].eq(spec.defending_team_key)]
    if defenders.empty:
        raise ValueError("defending team is absent")
    for (_, _), group in defenders.groupby(["match_id", "period"], sort=False):
        if group["player_key"].nunique(dropna=False) != 10:
            raise ValueError("each match-period must contain exactly ten stable defenders")
    q = q.sort_values(
        ["match_id", "period", "time_match_s", "frame_id_provider", "entity_type", "team_key", "player_key"],
        kind="mergesort",
        na_position="last",
    ).reset_index(drop=True)
    return q


def _score_group(
    group: pd.DataFrame,
    spec: DefenderRelativePathSpec,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    frame_identity = group[["frame_id_provider", "time_match_s"]].drop_duplicates()
    if frame_identity.groupby("frame_id_provider")["time_match_s"].nunique().gt(1).any():
        raise ValueError("one provider frame maps to multiple timestamps")
    frames = frame_identity.sort_values(
        ["time_match_s", "frame_id_provider"], kind="mergesort"
    ).reset_index(drop=True)
    if len(frames) < 2 or not np.isfinite(frames["time_match_s"].to_numpy(float)).all():
        raise ValueError("at least two finite frame timestamps are required")
    expected = 1.0 / spec.source_fps
    if not np.allclose(
        np.diff(frames["time_match_s"].to_numpy(float)), expected, atol=1e-7, rtol=0
    ):
        raise ValueError("Native frame cadence is irregular")
    canonical_frame_ids = frames["frame_id_provider"].map(str)
    if canonical_frame_ids.duplicated().any():
        raise ValueError("distinct frame_id_provider values collide after canonicalization")

    defenders = group.loc[
        group["entity_type"].eq("player") & group["team_key"].eq(spec.defending_team_key)
    ]
    player_keys = tuple(sorted(defenders["player_key"].astype(str).unique()))
    if len(player_keys) != 10:
        raise ValueError("each match-period must contain exactly ten stable defenders")
    frame_lookup = {value: index for index, value in enumerate(frames["frame_id_provider"])}
    player_lookup = {value: index for index, value in enumerate(player_keys)}
    raw = np.full((len(frames), 10, 2), np.nan, dtype=np.float64)
    present = np.zeros((len(frames), 10), dtype=bool)
    for row in defenders.itertuples(index=False):
        frame_index = frame_lookup[row.frame_id_provider]
        player_index = player_lookup[str(row.player_key)]
        if not isinstance(row.coordinate_valid, (bool, np.bool_)):
            raise ValueError("coordinate_valid must be Boolean")
        xy = np.asarray([row.x_m, row.y_m], dtype=np.float64)
        if bool(row.coordinate_valid) and not np.isfinite(xy).all():
            raise ValueError("coordinates marked valid must be finite")
        if bool(row.coordinate_valid):
            raw[frame_index, player_index] = xy
            present[frame_index, player_index] = True

    match_value = group["match_id"].iloc[0]
    period_value = group["period"].iloc[0]
    window_steps = int(round(spec.window_seconds * spec.source_fps))
    half = spec.smoothing_frames // 2
    player_rows: list[dict[str, object]] = []
    team_rows: list[dict[str, object]] = []
    for index, frame in frames.iterrows():
        raw_start = index - window_steps - half
        raw_end = index + half
        if raw_start < 0:
            status = INSUFFICIENT_HISTORY
            paths = None
        elif raw_end >= len(frames):
            status = INSUFFICIENT_FUTURE
            paths = None
        elif not present[raw_start : raw_end + 1].all():
            status = MISSING_COORDINATES
            paths = None
        else:
            smoothed = np.stack(
                [
                    raw[position - half : position + half + 1].mean(axis=0)
                    for position in range(index - window_steps, index + 1)
                ],
                axis=0,
            )
            paths = defender_relative_path_lengths(smoothed)
            status = SUPPORTED
        for player_index, player_key in enumerate(player_keys):
            player_rows.append(
                {
                    "match_id": match_value,
                    "period": period_value,
                    "frame_id_provider": frame["frame_id_provider"],
                    "time_match_s": float(frame["time_match_s"]),
                    "team_key": spec.defending_team_key,
                    "player_key": player_key,
                    "trailing_relative_path_m": (
                        np.nan if paths is None else float(paths[player_index])
                    ),
                    "support_status": status,
                }
            )
        team_rows.append(
            {
                "match_id": match_value,
                "period": period_value,
                "frame_id_provider": frame["frame_id_provider"],
                "time_match_s": float(frame["time_match_s"]),
                "team_key": spec.defending_team_key,
                "mean_trailing_relative_path_m": (
                    np.nan if paths is None else float(paths.mean())
                ),
                "supported_defender_count": 0 if paths is None else 10,
                "support_status": status,
            }
        )
    return player_rows, team_rows


def score_trailing_defender_relative_path(
    tracking: pd.DataFrame,
    spec: DefenderRelativePathSpec,
) -> DefensiveReorganizationScores:
    """Compute the trailing-window analogue at every native frame.

    The function never infers possession, ranks, marking, or outcomes.  Complete
    ten-defender support is all-or-none at each score time.
    """
    q = _validate_tracking(tracking, spec)
    player_rows: list[dict[str, object]] = []
    team_rows: list[dict[str, object]] = []
    for _, group in q.groupby(["match_id", "period"], sort=True):
        players, teams = _score_group(group, spec)
        player_rows.extend(players)
        team_rows.extend(teams)
    player_scores = pd.DataFrame(player_rows, columns=PLAYER_SCORE_COLUMNS)
    team_scores = pd.DataFrame(team_rows, columns=TEAM_SCORE_COLUMNS)
    status_counts = {
        str(key): int(value)
        for key, value in team_scores["support_status"].value_counts().sort_index().items()
    }
    metadata = {
        "metric": "trailing_defender_relative_path",
        "label": f"Trailing {spec.window_seconds:g} s defender-relative path — a visualization-derived trailing analogue of the frozen response measure",
        "units": "metres",
        "timing": "trailing_window_ending_at_displayed_frame",
        "inferential_response": False,
        "window_seconds": float(spec.window_seconds),
        "window_increments": int(round(spec.window_seconds * spec.source_fps)),
        "source_fps": float(spec.source_fps),
        "smoothing_frames": int(spec.smoothing_frames),
        "smoothing_method": spec.smoothing_method,
        "smoother_future_support_seconds": float((spec.smoothing_frames // 2) / spec.source_fps),
        "required_defenders": 10,
        "reference": "leave_one_out_centroid_of_other_nine_defenders",
        "normalization": "none_raw_metres",
        "input_frame_count": int(len(team_scores)),
        "supported_frame_count": int(team_scores["support_status"].eq(SUPPORTED).sum()),
        "support_status_counts": status_counts,
    }
    return DefensiveReorganizationScores(player_scores, team_scores, metadata)
