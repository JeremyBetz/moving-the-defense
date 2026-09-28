"""Trajectory-integrity and ball-alignment context for rapid review.

This module is an application diagnostic.  It does not alter the production
defender-relative path scorer, possession reconstruction, or rapid threshold.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from defensive_reorganization_replay import DefensiveReorganizationScores, SUPPORTED


@dataclass(frozen=True)
class TrajectoryIntegritySpec:
    source_fps: float = 25.0
    maximum_plausible_speed_mps: float = 15.0
    swap_cross_displacement_ratio_maximum: float = 0.25
    score_window_seconds: float = 2.0
    rapid_change_seconds: float = 1.0
    smoothing_frames: int = 7

    def __post_init__(self) -> None:
        values = (
            self.source_fps,
            self.maximum_plausible_speed_mps,
            self.swap_cross_displacement_ratio_maximum,
            self.score_window_seconds,
            self.rapid_change_seconds,
        )
        if not np.isfinite(values).all() or min(values) <= 0:
            raise ValueError("trajectory-integrity settings must be finite and positive")
        if self.maximum_plausible_speed_mps != 15.0:
            raise ValueError("native-speed threshold differs from the freeze")
        if self.swap_cross_displacement_ratio_maximum != 0.25:
            raise ValueError("swap ratio differs from the freeze")
        if self.smoothing_frames != 7 or self.smoothing_frames % 2 != 1:
            raise ValueError("smoothing window differs from the freeze")

    @property
    def half_smoother_seconds(self) -> float:
        return (self.smoothing_frames // 2) / self.source_fps

    def rapid_raw_support(self, peak_time_s: float) -> tuple[float, float]:
        return (
            float(peak_time_s)
            - self.rapid_change_seconds
            - self.score_window_seconds
            - self.half_smoother_seconds,
            float(peak_time_s) + self.half_smoother_seconds,
        )


@dataclass(frozen=True)
class TrajectoryIntegrityAudit:
    status: str
    impossible_speed_count: int
    identity_swap_suspicion_count: int
    missing_duplicate_invalid_count: int
    maximum_native_speed_mps: float
    support_start_time_s: float
    support_end_time_s: float
    swap_pairs: tuple[tuple[str, str], ...] = ()

    @property
    def clean(self) -> bool:
        return self.status == "trajectory_integrity_clean"


@dataclass(frozen=True)
class BallAlignmentSummary:
    player_alignment: pd.DataFrame
    team_signed_alignment: float
    team_ballward_projection_share: float
    team_raw_path_sum_m: float
    support_status: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_alignment", self.player_alignment.copy(deep=True))


@dataclass(frozen=True)
class BallAlignmentReviewResult:
    reference_summary: Mapping[str, object]
    historical_audit: pd.DataFrame
    overall_ranking: pd.DataFrame
    low_ballward_ranking: pd.DataFrame
    high_ballward_ranking: pd.DataFrame
    public_examples: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        for field in (
            "historical_audit",
            "overall_ranking",
            "low_ballward_ranking",
            "high_ballward_ranking",
            "public_examples",
        ):
            object.__setattr__(self, field, getattr(self, field).copy(deep=True))
        object.__setattr__(self, "reference_summary", MappingProxyType(dict(self.reference_summary)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _score_player_keys(
    scores: DefensiveReorganizationScores,
    *,
    match_id: str,
    period: int,
    team_key: str,
    time_s: float,
) -> tuple[str, ...]:
    q = scores.player_scores.loc[
        scores.player_scores["match_id"].astype(str).eq(str(match_id))
        & scores.player_scores["period"].eq(int(period))
        & scores.player_scores["team_key"].astype(str).eq(str(team_key))
        & np.isclose(scores.player_scores["time_match_s"], time_s, atol=1e-7, rtol=0)
        & scores.player_scores["support_status"].eq(SUPPORTED)
    ]
    keys = tuple(sorted(q["player_key"].astype(str)))
    if len(keys) != 10:
        raise RuntimeError("candidate score lacks exactly ten supported defenders")
    return keys


def _raw_player_cube(
    tracking: pd.DataFrame,
    *,
    match_id: str,
    period: int,
    team_key: str,
    player_keys: Sequence[str],
    start_time_s: float,
    end_time_s: float,
    source_fps: float,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], int]:
    keys = tuple(sorted(map(str, player_keys)))
    q = tracking.loc[
        tracking["match_id"].astype(str).eq(str(match_id))
        & tracking["period"].eq(int(period))
        & tracking["entity_type"].eq("player")
        & tracking["team_key"].astype(str).eq(str(team_key))
        & tracking["player_key"].astype(str).isin(keys)
        & tracking["time_match_s"].between(start_time_s - 1e-7, end_time_s + 1e-7)
    ].copy()
    duplicate_count = int(q.duplicated(["frame_id_provider", "player_key"], keep=False).sum())
    frame_table = (
        q[["frame_id_provider", "time_match_s"]]
        .drop_duplicates()
        .sort_values(["time_match_s", "frame_id_provider"], kind="mergesort")
        .reset_index(drop=True)
    )
    expected_frames = int(round((end_time_s - start_time_s) * source_fps)) + 1
    invalid_count = duplicate_count
    if len(frame_table) != expected_frames:
        invalid_count += abs(expected_frames - len(frame_table)) * len(keys)
    times = frame_table["time_match_s"].to_numpy(float)
    if len(times) and (
        not np.isclose(times[0], start_time_s, atol=1e-7, rtol=0)
        or not np.isclose(times[-1], end_time_s, atol=1e-7, rtol=0)
        or not np.allclose(np.diff(times), 1.0 / source_fps, atol=1e-7, rtol=0)
    ):
        invalid_count += 1
    cube = np.full((len(frame_table), len(keys), 2), np.nan, dtype=float)
    frame_lookup = {value: index for index, value in enumerate(frame_table.frame_id_provider)}
    key_lookup = {value: index for index, value in enumerate(keys)}
    for row in q.itertuples(index=False):
        if row.frame_id_provider not in frame_lookup or str(row.player_key) not in key_lookup:
            continue
        i, j = frame_lookup[row.frame_id_provider], key_lookup[str(row.player_key)]
        xy = np.asarray([row.x_m, row.y_m], dtype=float)
        valid = bool(row.coordinate_valid) and np.isfinite(xy).all()
        if valid and np.isnan(cube[i, j]).all():
            cube[i, j] = xy
        elif not valid:
            invalid_count += 1
    invalid_count += int(np.isnan(cube).any(axis=2).sum())
    return times, cube, keys, invalid_count


def audit_native_trajectory_integrity(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    *,
    match_id: str,
    period: int,
    team_key: str,
    peak_time_s: float,
    spec: TrajectoryIntegritySpec = TrajectoryIntegritySpec(),
) -> TrajectoryIntegrityAudit:
    """Audit the complete raw support for both one-second score endpoints."""
    keys = _score_player_keys(
        scores, match_id=match_id, period=period, team_key=team_key, time_s=peak_time_s
    )
    start, end = spec.rapid_raw_support(peak_time_s)
    times, cube, keys, invalid_count = _raw_player_cube(
        tracking,
        match_id=match_id,
        period=period,
        team_key=team_key,
        player_keys=keys,
        start_time_s=start,
        end_time_s=end,
        source_fps=spec.source_fps,
    )
    if invalid_count or len(times) < 2:
        return TrajectoryIntegrityAudit(
            "trajectory_integrity_failed", 0, 0, int(invalid_count), np.nan, start, end
        )
    displacement = np.linalg.norm(np.diff(cube, axis=0), axis=2)
    speed = displacement * spec.source_fps
    impossible = speed > spec.maximum_plausible_speed_mps
    swap_pairs: set[tuple[str, str]] = set()
    for frame in range(len(cube) - 1):
        impossible_players = np.flatnonzero(impossible[frame])
        for left_position, left in enumerate(impossible_players):
            for right in impossible_players[left_position + 1 :]:
                cross_left = np.linalg.norm(cube[frame + 1, right] - cube[frame, left])
                cross_right = np.linalg.norm(cube[frame + 1, left] - cube[frame, right])
                own_total = displacement[frame, left] + displacement[frame, right]
                cross_total = cross_left + cross_right
                plausible = (
                    cross_left * spec.source_fps <= spec.maximum_plausible_speed_mps
                    and cross_right * spec.source_fps <= spec.maximum_plausible_speed_mps
                )
                if plausible and cross_total <= spec.swap_cross_displacement_ratio_maximum * own_total + 1e-12:
                    swap_pairs.add((keys[left], keys[right]))
    impossible_count = int(impossible.sum())
    swap_count = len(swap_pairs)
    status = (
        "trajectory_integrity_clean"
        if impossible_count == 0 and swap_count == 0 and invalid_count == 0
        else "trajectory_integrity_failed"
    )
    return TrajectoryIntegrityAudit(
        status,
        impossible_count,
        swap_count,
        int(invalid_count),
        float(speed.max(initial=0.0)),
        start,
        end,
        tuple(sorted(swap_pairs)),
    )


def _centered_mean(values: np.ndarray, frames: int) -> np.ndarray:
    return np.stack(
        [values[index : index + frames].mean(axis=0) for index in range(len(values) - frames + 1)],
        axis=0,
    )


def summarize_ball_alignment_increments(
    defender_relative_increments: np.ndarray,
    player_midpoints: np.ndarray,
    ball_midpoints: np.ndarray,
    *,
    player_keys: Sequence[str] | None = None,
) -> BallAlignmentSummary:
    """Summarize already-aligned increments with independent geometric inputs."""
    delta = np.asarray(defender_relative_increments, dtype=float)
    players = np.asarray(player_midpoints, dtype=float)
    ball = np.asarray(ball_midpoints, dtype=float)
    if delta.ndim != 3 or delta.shape[-1] != 2 or players.shape != delta.shape:
        raise ValueError("increments and player midpoints must have shape [increments, players, 2]")
    if ball.shape != (len(delta), 2):
        raise ValueError("ball midpoints must have shape [increments, 2]")
    if not np.isfinite(delta).all() or not np.isfinite(players).all() or not np.isfinite(ball).all():
        return BallAlignmentSummary(pd.DataFrame(), np.nan, np.nan, np.nan, "unsupported")
    keys = tuple(map(str, player_keys or tuple(f"p{index}" for index in range(delta.shape[1]))))
    if len(keys) != delta.shape[1] or len(set(keys)) != len(keys):
        raise ValueError("player keys must be unique and match the increment width")
    magnitude = np.linalg.norm(delta, axis=2)
    toward_ball = ball[:, None, :] - players
    distance = np.linalg.norm(toward_ball, axis=2)
    if not np.isfinite(distance).all() or np.any(distance <= 0):
        return BallAlignmentSummary(pd.DataFrame(), np.nan, np.nan, np.nan, "unsupported")
    unit = toward_ball / distance[:, :, None]
    projection = np.sum(delta * unit, axis=2)
    perpendicular = np.sqrt(np.maximum(magnitude**2 - projection**2, 0.0))
    raw_path = magnitude.sum(axis=0)
    positive = np.maximum(projection, 0.0).sum(axis=0)
    negative = np.maximum(-projection, 0.0).sum(axis=0)
    signed = projection.sum(axis=0)
    lateral = perpendicular.sum(axis=0)
    status = np.where(raw_path > 0, "supported", "zero_path")
    rows = pd.DataFrame(
        {
            "player_key": keys,
            "raw_path_m": raw_path,
            "signed_alignment": np.divide(signed, raw_path, out=np.full(len(keys), np.nan), where=raw_path > 0),
            "ballward_projection_share": np.divide(positive, raw_path, out=np.full(len(keys), np.nan), where=raw_path > 0),
            "awayward_projection_share": np.divide(negative, raw_path, out=np.full(len(keys), np.nan), where=raw_path > 0),
            "lateral_alignment_index": np.divide(lateral, raw_path, out=np.full(len(keys), np.nan), where=raw_path > 0),
            "support_status": status,
        }
    )
    total_path = float(raw_path.sum())
    complete = bool(np.all(raw_path > 0) and np.isfinite(rows.drop(columns=["player_key", "support_status"]).to_numpy(float)).all())
    return BallAlignmentSummary(
        rows,
        float(signed.sum() / total_path) if total_path > 0 else np.nan,
        float(positive.sum() / total_path) if total_path > 0 else np.nan,
        total_path,
        "supported" if complete else "zero_path",
    )


def compute_ball_alignment_at_time(
    tracking: pd.DataFrame,
    ball_tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    *,
    match_id: str,
    period: int,
    team_key: str,
    time_s: float,
    spec: TrajectoryIntegritySpec = TrajectoryIntegritySpec(),
) -> BallAlignmentSummary:
    """Compute path-weighted ball alignment over the exact trailing score window."""
    keys = _score_player_keys(
        scores, match_id=match_id, period=period, team_key=team_key, time_s=time_s
    )
    half = spec.half_smoother_seconds
    start, end = time_s - spec.score_window_seconds - half, time_s + half
    times, raw, keys, invalid_count = _raw_player_cube(
        tracking,
        match_id=match_id,
        period=period,
        team_key=team_key,
        player_keys=keys,
        start_time_s=start,
        end_time_s=end,
        source_fps=spec.source_fps,
    )
    ball = ball_tracking.loc[
        ball_tracking["match_id"].astype(str).eq(str(match_id))
        & ball_tracking["period"].eq(int(period))
        & ball_tracking["entity_type"].eq("ball")
        & ball_tracking["time_match_s"].between(start - 1e-7, end + 1e-7)
    ].sort_values(["time_match_s", "frame_id_provider"], kind="mergesort")
    if (
        invalid_count
        or len(ball) != len(times)
        or ball.duplicated(["frame_id_provider"]).any()
        or not ball["coordinate_valid"].astype(bool).all()
        or not np.isfinite(ball[["x_m", "y_m"]].to_numpy(float)).all()
        or not np.allclose(ball["time_match_s"].to_numpy(float), times, atol=1e-7, rtol=0)
    ):
        return BallAlignmentSummary(
            pd.DataFrame(), np.nan, np.nan, np.nan, "unsupported"
        )
    smooth_players = _centered_mean(raw, spec.smoothing_frames)
    smooth_ball = _centered_mean(ball[["x_m", "y_m"]].to_numpy(float), spec.smoothing_frames)
    expected_centers = int(round(spec.score_window_seconds * spec.source_fps)) + 1
    if len(smooth_players) != expected_centers:
        raise RuntimeError("alignment smoother support differs from the score interval")
    total = smooth_players.sum(axis=1, keepdims=True)
    relative = (10.0 * smooth_players - total) / 9.0
    delta = np.diff(relative, axis=0)
    player_mid = (smooth_players[1:] + smooth_players[:-1]) / 2.0
    ball_mid = (smooth_ball[1:] + smooth_ball[:-1]) / 2.0
    summary = summarize_ball_alignment_increments(
        delta, player_mid, ball_mid, player_keys=keys
    )
    if summary.support_status == "unsupported":
        return summary
    raw_path = summary.player_alignment["raw_path_m"].to_numpy(float)
    stored = (
        scores.player_scores.loc[
            scores.player_scores["match_id"].astype(str).eq(str(match_id))
            & scores.player_scores["period"].eq(int(period))
            & scores.player_scores["team_key"].astype(str).eq(str(team_key))
            & np.isclose(scores.player_scores["time_match_s"], time_s, atol=1e-7, rtol=0)
        ]
        .set_index("player_key")["trailing_relative_path_m"]
        .reindex(keys)
        .to_numpy(float)
    )
    if not np.allclose(raw_path, stored, atol=1e-10, rtol=1e-10):
        raise RuntimeError("ball-alignment path does not reproduce the production score")
    return summary


def reference_ballward_thresholds(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError("ballward reference must be nonempty and finite")
    return {
        "count": int(array.size),
        "p25": float(np.quantile(array, 0.25, method="linear")),
        "p50": float(np.quantile(array, 0.50, method="linear")),
        "p75": float(np.quantile(array, 0.75, method="linear")),
    }


def classify_ballward(value: float, *, p25: float, p75: float) -> str:
    if not np.isfinite(value) or not np.isfinite([p25, p75]).all() or p25 > p75:
        raise ValueError("ballward value and thresholds must be ordered and finite")
    if value <= p25:
        return "low_ballward"
    if value >= p75:
        return "high_ballward"
    return "mid_ballward"


def select_ball_alignment_review(
    annotated: pd.DataFrame,
    *,
    p25: float,
    p75: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return deterministic overall/low/high rankings and the contrast set."""
    q = annotated.copy(deep=True)
    required = {
        "one_second_change_m", "period", "peak_time_s", "team_key",
        "trajectory_integrity_status", "ball_alignment_support_status",
        "team_ballward_projection_share", "rapid_context", "render_eligible",
    }
    if not required.issubset(q.columns):
        raise ValueError(f"annotated rapid candidates lack: {sorted(required - set(q.columns))}")
    q["ballward_stratum"] = [
        classify_ballward(float(value), p25=p25, p75=p75)
        if np.isfinite(float(value)) else "unsupported"
        for value in q["team_ballward_projection_share"]
    ]
    eligible = q.loc[
        q["trajectory_integrity_status"].eq("trajectory_integrity_clean")
        & q["ball_alignment_support_status"].eq("supported")
        & q["render_eligible"].astype(bool)
        & ~q["rapid_context"].isin(["ambiguous_context", "restart_adjacent"])
    ].sort_values(
        ["one_second_change_m", "period", "peak_time_s", "team_key"],
        ascending=[False, True, True, True], kind="mergesort",
    ).reset_index(drop=True)
    eligible["overall_rank"] = np.arange(1, len(eligible) + 1)
    low = eligible.loc[eligible.ballward_stratum.eq("low_ballward")].reset_index(drop=True)
    high = eligible.loc[eligible.ballward_stratum.eq("high_ballward")].reset_index(drop=True)
    low["stratum_rank"] = np.arange(1, len(low) + 1)
    high["stratum_rank"] = np.arange(1, len(high) + 1)
    selected: list[pd.Series] = []
    reasons: list[str] = []
    if not low.empty:
        selected.append(low.iloc[0]); reasons.append("top_low_ballward")
    if not high.empty:
        key = (str(high.iloc[0].team_key), int(high.iloc[0].period), float(high.iloc[0].peak_time_s))
        existing = {(str(row.team_key), int(row.period), float(row.peak_time_s)) for row in selected}
        if key not in existing:
            selected.append(high.iloc[0]); reasons.append("top_high_ballward")
    if not eligible.empty:
        row = eligible.iloc[0]
        key = (str(row.team_key), int(row.period), float(row.peak_time_s))
        existing = {(str(item.team_key), int(item.period), float(item.peak_time_s)) for item in selected}
        if key not in existing:
            selected.append(row); reasons.append("distinct_top_overall")
    public = pd.DataFrame(selected).reset_index(drop=True) if selected else eligible.head(0)
    if not public.empty:
        public["public_selection_reason"] = reasons
        public["public_rank"] = np.arange(1, len(public) + 1)
    return eligible, low, high, public
