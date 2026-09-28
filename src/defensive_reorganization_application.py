"""Application helpers for replay scoring, moment discovery, and export.

The functions here organize the committed retrospective score for analyst use.
They do not modify its construction or create an inferential response.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Literal
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_replay import (
    SUPPORTED,
    DefensiveReorganizationScores,
    DefenderRelativePathSpec,
    score_trailing_defender_relative_path,
)
from defensive_reorganization_replay_visualization import (
    DEFAULT_SCORE_VMAX_M,
    animate_defensive_reorganization,
    plot_defensive_reorganization_diagnostic,
)
from tracking_animation import TrackingClipSpec, export_animation


MOMENT_COLUMNS = (
    "moment_type",
    "match_id",
    "period",
    "team_key",
    "start_time_s",
    "end_time_s",
    "peak_time_s",
    "duration_s",
    "team_score_m",
    "within_match_percentile",
    "positive_change_m",
    "leading_player_contributors",
    "seconds_from_run_start",
    "seconds_to_run_end",
    "boundary_flag",
    "interior_eligible",
    "selected_for_clip",
)

EVENT_SUMMARY_BASE_COLUMNS = (
    "event_id",
    "match_id",
    "period",
    "event_time_s",
    "event_type",
    "team_key",
    "defending_team_key",
    "score_at_event_m",
    "within_match_percentile",
)

EVENT_WINDOW_COLUMNS = (
    "event_id", "match_id", "period", "event_time_s", "event_type",
    "event_detail", "event_x_m", "event_y_m", "attacking_team_key", "defending_team_key",
    "pre_score_m", "anchor_score_m", "post_score_m", "maximum_score_m",
    "post_minus_pre_change_m", "time_to_peak_s", "leading_player_contributors",
    "support_status", "suitability_status", "suitability_reason", "rank_by",
    "rank_value", "rank",
)


@dataclass(frozen=True)
class EventWindowQuery:
    """Provider-neutral request for event-anchored analyst review windows."""

    defending_team_key: str
    event_types: tuple[str, ...] = ()
    explicit_timestamps: tuple[tuple[int, float], ...] = ()
    attacking_team_key: str | None = None
    pre_seconds: float = 3.0
    post_seconds: float = 3.0
    rank_by: Literal[
        "anchor_score", "maximum_score", "post_minus_pre_change", "time_to_peak"
    ] = "maximum_score"
    limit: int = 3
    require_suitable: bool = True
    leading_players: int = 3

    def __post_init__(self) -> None:
        if not str(self.defending_team_key):
            raise ValueError("defending_team_key is required")
        if not self.event_types and not self.explicit_timestamps:
            raise ValueError("event_types and/or explicit_timestamps are required")
        normalized = tuple(str(value).strip().upper() for value in self.event_types)
        if any(not value for value in normalized):
            raise ValueError("event_types cannot contain blanks")
        object.__setattr__(self, "event_types", normalized)
        for period, time_s in self.explicit_timestamps:
            if int(period) < 1 or not np.isfinite(float(time_s)):
                raise ValueError("explicit timestamps require positive periods and finite times")
        if (
            not np.isfinite([self.pre_seconds, self.post_seconds]).all()
            or self.pre_seconds <= 0
            or self.post_seconds <= 0
        ):
            raise ValueError("pre_seconds and post_seconds must be finite and positive")
        if self.limit < 1 or self.leading_players < 1:
            raise ValueError("limit and leading_players must be positive")
        if self.rank_by not in {
            "anchor_score", "maximum_score", "post_minus_pre_change", "time_to_peak"
        }:
            raise ValueError("rank_by is not supported")


@dataclass(frozen=True)
class EventWindowResult:
    windows: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "windows", self.windows.copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class MomentDiscoverySpec:
    top_n_per_type: int = 3
    tail_fraction: float = 0.05
    adjacency_seconds: float = 1.0
    leading_players: int = 3
    interior_guard_seconds: float = 6.0

    def __post_init__(self) -> None:
        if self.top_n_per_type < 1 or self.leading_players < 1:
            raise ValueError("moment counts must be positive")
        if not 0 < self.tail_fraction < 0.5:
            raise ValueError("tail_fraction must lie between 0 and 0.5")
        if not np.isfinite(self.adjacency_seconds) or self.adjacency_seconds < 0:
            raise ValueError("adjacency_seconds must be finite and nonnegative")
        if not np.isfinite(self.interior_guard_seconds) or self.interior_guard_seconds < 0:
            raise ValueError("interior_guard_seconds must be finite and nonnegative")


@dataclass(frozen=True)
class MatchApplicationConfig:
    """Deterministic defaults for the low-decision notebook workflow."""

    source_fps: float
    smoothing_frames: int
    window_seconds: float = 2.0
    interior_guard_seconds: float = 6.0
    adjacency_seconds: float = 1.0
    tail_fraction: float = 0.05
    category_quota: int = 2
    leading_players: int = 3
    event_lookbacks_seconds: tuple[float, ...] = (2.0, 5.0, 10.0)
    clip_context_seconds: float = 3.0
    frame_step: int = 2
    playback_fps: float = 12.5
    score_vmax_m: float = DEFAULT_SCORE_VMAX_M
    export_formats: tuple[str, ...] = ("csv", "parquet")

    def __post_init__(self) -> None:
        # Reuse the scientific-spec validation for cadence/window/smoothing.
        DefenderRelativePathSpec(
            defending_team_key="validation",
            source_fps=self.source_fps,
            window_seconds=self.window_seconds,
            smoothing_frames=self.smoothing_frames,
        )
        MomentDiscoverySpec(
            top_n_per_type=self.category_quota,
            tail_fraction=self.tail_fraction,
            adjacency_seconds=self.adjacency_seconds,
            leading_players=self.leading_players,
            interior_guard_seconds=self.interior_guard_seconds,
        )
        if self.interior_guard_seconds < self.window_seconds + self.clip_context_seconds:
            raise ValueError(
                "interior guard must cover the trailing window plus pre-clip context"
            )
        if self.frame_step < 1 or self.playback_fps <= 0:
            raise ValueError("frame_step and playback_fps must be positive")
        if not self.event_lookbacks_seconds:
            raise ValueError("event lookbacks cannot be empty")


@dataclass(frozen=True)
class MatchApplicationResult:
    scores_by_team: Mapping[str, DefensiveReorganizationScores]
    moment_audit: pd.DataFrame
    selected_moments: pd.DataFrame
    event_summary: pd.DataFrame
    distributions: pd.DataFrame
    metadata: Mapping[str, object]
    artifacts: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scores_by_team", MappingProxyType(dict(self.scores_by_team)))
        object.__setattr__(self, "moment_audit", self.moment_audit.copy(deep=True))
        object.__setattr__(self, "selected_moments", self.selected_moments.copy(deep=True))
        object.__setattr__(self, "event_summary", self.event_summary.copy(deep=True))
        object.__setattr__(self, "distributions", self.distributions.copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        object.__setattr__(self, "artifacts", MappingProxyType(dict(self.artifacts)))


def score_match(
    tracking: pd.DataFrame,
    *,
    defending_team_key: str,
    source_fps: float,
    smoothing_frames: int,
    window_seconds: float = 2.0,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
) -> DefensiveReorganizationScores:
    """Score normalized tracking and optionally return a bounded time range.

    The complete input is scored before filtering, so a requested range may use
    valid history/smoother support present outside its displayed boundaries.
    """
    scores = score_trailing_defender_relative_path(
        tracking,
        DefenderRelativePathSpec(
            defending_team_key=defending_team_key,
            source_fps=source_fps,
            window_seconds=window_seconds,
            smoothing_frames=smoothing_frames,
        ),
    )
    if start_time_s is None and end_time_s is None:
        return scores
    start = -np.inf if start_time_s is None else float(start_time_s)
    end = np.inf if end_time_s is None else float(end_time_s)
    if np.isnan([start, end]).any() or start > end:
        raise ValueError("time range must satisfy start_time_s <= end_time_s")
    players = scores.player_scores.loc[
        scores.player_scores["time_match_s"].between(start, end)
    ].reset_index(drop=True)
    teams = scores.team_scores.loc[
        scores.team_scores["time_match_s"].between(start, end)
    ].reset_index(drop=True)
    return DefensiveReorganizationScores(
        player_scores=players,
        team_scores=teams,
        metadata={
            **scores.metadata,
            "requested_start_time_s": None if start_time_s is None else start,
            "requested_end_time_s": None if end_time_s is None else end,
        },
    )


def score_stable_runs(
    tracking: pd.DataFrame,
    *,
    defending_team_key: str,
    source_fps: float,
    smoothing_frames: int,
    window_seconds: float = 2.0,
    excluded_player_keys: Iterable[str] = (),
) -> DefensiveReorganizationScores:
    """Score maximal regular-cadence runs with ten stable finite defenders.

    This application wrapper handles substitutions and missing-coordinate
    boundaries by splitting support; it never bridges or interpolates them.
    """
    q = tracking.copy(deep=True)
    excluded = {str(key) for key in excluded_player_keys}
    defenders = q.loc[
        q["entity_type"].eq("player")
        & q["team_key"].eq(defending_team_key)
        & ~q["player_key"].astype(str).isin(excluded)
    ].copy()
    if defenders.empty:
        raise ValueError("defending team has no candidate outfield tracking")
    players_out: list[pd.DataFrame] = []
    teams_out: list[pd.DataFrame] = []
    run_records: list[dict[str, object]] = []
    cadence = 1.0 / float(source_fps)
    minimum_frames = int(round(window_seconds * source_fps)) + smoothing_frames

    for (match_id, period), group in defenders.groupby(["match_id", "period"], sort=True):
        frames = (
            group[["frame_id_provider", "time_match_s"]]
            .drop_duplicates()
            .sort_values(["time_match_s", "frame_id_provider"], kind="mergesort")
            .reset_index(drop=True)
        )
        valid = group.loc[
            group["coordinate_valid"].astype(bool)
            & np.isfinite(group["x_m"].to_numpy(float))
            & np.isfinite(group["y_m"].to_numpy(float))
        ]
        active_map = valid.groupby("frame_id_provider", sort=False)["player_key"].agg(
            lambda values: tuple(sorted(values.astype(str).unique()))
        )
        frames["active_keys"] = frames["frame_id_provider"].map(active_map).map(
            lambda keys: keys if isinstance(keys, tuple) and len(keys) == 10 else ()
        )

        start = 0
        run_index = 0
        for index in range(1, len(frames) + 1):
            boundary = index == len(frames)
            if not boundary:
                same_roster = frames.iloc[index]["active_keys"] == frames.iloc[index - 1]["active_keys"]
                regular = np.isclose(
                    float(frames.iloc[index]["time_match_s"])
                    - float(frames.iloc[index - 1]["time_match_s"]),
                    cadence,
                    atol=1e-7,
                    rtol=0,
                )
                boundary = not (same_roster and regular)
            if not boundary:
                continue
            candidate = frames.iloc[start:index]
            keys = candidate.iloc[0]["active_keys"] if len(candidate) else ()
            if len(keys) == 10 and len(candidate) >= minimum_frames:
                run_index += 1
                run_id = f"{match_id}::p{period}::run{run_index}"
                run_frame_ids = set(candidate["frame_id_provider"])
                run = group.loc[
                    group["frame_id_provider"].isin(run_frame_ids)
                    & group["player_key"].astype(str).isin(keys)
                ].copy()
                run["match_id"] = run_id
                scored = score_match(
                    run,
                    defending_team_key=defending_team_key,
                    source_fps=source_fps,
                    smoothing_frames=smoothing_frames,
                    window_seconds=window_seconds,
                )
                player = scored.player_scores.copy()
                team = scored.team_scores.copy()
                player["match_id"] = match_id
                team["match_id"] = match_id
                players_out.append(player)
                teams_out.append(team)
                run_records.append(
                    {
                        "match_id": str(match_id),
                        "period": int(period),
                        "run_index": run_index,
                        "start_time_s": float(candidate["time_match_s"].iloc[0]),
                        "end_time_s": float(candidate["time_match_s"].iloc[-1]),
                        "native_frame_count": int(len(candidate)),
                        "supported_frame_count": int(team["support_status"].eq(SUPPORTED).sum()),
                    }
                )
            start = index
    if not players_out:
        raise ValueError("no stable ten-defender run has sufficient score support")
    return DefensiveReorganizationScores(
        pd.concat(players_out, ignore_index=True),
        pd.concat(teams_out, ignore_index=True),
        {
            "source_fps": float(source_fps),
            "window_seconds": float(window_seconds),
            "smoothing_frames": int(smoothing_frames),
            "defending_team_key": defending_team_key,
            "support_unit": "maximal_regular_cadence_stable_ten_outfielder_run",
            "stable_runs": run_records,
        },
    )


def export_scores(
    scores: DefensiveReorganizationScores,
    output_dir: str | Path,
    *,
    formats: Iterable[str] = ("csv", "parquet"),
) -> dict[str, Path]:
    """Export player/team score timelines in explicit requested formats."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    requested = tuple(dict.fromkeys(str(item).lower() for item in formats))
    if not requested or not set(requested) <= {"csv", "parquet"}:
        raise ValueError("formats must be a nonempty subset of csv and parquet")
    written: dict[str, Path] = {}
    for name, frame in (
        ("player_scores", scores.player_scores),
        ("team_scores", scores.team_scores),
    ):
        for suffix in requested:
            path = destination / f"{name}.{suffix}"
            if suffix == "csv":
                frame.to_csv(path, index=False, lineterminator="\n")
            else:
                try:
                    frame.to_parquet(path, index=False)
                except ImportError:
                    # The repository runtime includes Polars but intentionally
                    # does not require pandas' optional PyArrow engine.
                    import polars as pl

                    pl.from_pandas(frame).write_parquet(path)
            written[f"{name}_{suffix}"] = path
    metadata = destination / "score_metadata.json"
    metadata.write_text(
        json.dumps(dict(scores.metadata), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    written["metadata_json"] = metadata
    return written


def _cluster(masked: pd.DataFrame, adjacency_seconds: float) -> list[pd.DataFrame]:
    if masked.empty:
        return []
    groups = []
    start = 0
    times = masked["time_match_s"].to_numpy(float)
    periods = masked["period"].to_numpy()
    for index in range(1, len(masked)):
        if periods[index] != periods[index - 1] or times[index] - times[index - 1] > adjacency_seconds:
            groups.append(masked.iloc[start:index])
            start = index
    groups.append(masked.iloc[start:])
    return groups


def discover_moments(
    scores: DefensiveReorganizationScores,
    spec: MomentDiscoverySpec = MomentDiscoverySpec(),
    *,
    audit: bool = False,
) -> pd.DataFrame:
    """Find high, low, and rapid-positive-change passages without duplication."""
    team = scores.team_scores.loc[
        scores.team_scores["support_status"].eq(SUPPORTED)
        & np.isfinite(scores.team_scores["mean_trailing_relative_path_m"])
    ].copy()
    if team.empty:
        return pd.DataFrame(columns=MOMENT_COLUMNS)
    team = team.sort_values(
        ["match_id", "team_key", "period", "time_match_s"], kind="mergesort"
    ).reset_index(drop=True)
    team["within_match_percentile"] = team.groupby(
        ["match_id", "team_key"], sort=False
    )["mean_trailing_relative_path_m"].rank(method="average", pct=True)
    team["positive_change_m"] = team.groupby(
        ["match_id", "team_key", "period"], sort=False
    )["mean_trailing_relative_path_m"].diff()

    players = scores.player_scores.loc[
        scores.player_scores["support_status"].eq(SUPPORTED)
    ].copy()
    runs = list(scores.metadata.get("stable_runs", []))
    passages: list[dict[str, object]] = []
    for (match_id, team_key), group in team.groupby(["match_id", "team_key"], sort=True):
        high_cut = group["mean_trailing_relative_path_m"].quantile(1 - spec.tail_fraction)
        low_cut = group["mean_trailing_relative_path_m"].quantile(spec.tail_fraction)
        finite_changes = group["positive_change_m"].dropna()
        change_cut = finite_changes.quantile(1 - spec.tail_fraction) if len(finite_changes) else np.inf
        definitions = (
            ("high", group.loc[group["mean_trailing_relative_path_m"] >= high_cut], "max"),
            ("low", group.loc[group["mean_trailing_relative_path_m"] <= low_cut], "min"),
            ("rapid_increase", group.loc[group["positive_change_m"] >= change_cut], "change"),
        )
        for moment_type, candidates, criterion in definitions:
            rows = []
            for cluster in _cluster(candidates, spec.adjacency_seconds):
                if criterion == "max":
                    peak = cluster.loc[cluster["mean_trailing_relative_path_m"].idxmax()]
                elif criterion == "min":
                    peak = cluster.loc[cluster["mean_trailing_relative_path_m"].idxmin()]
                else:
                    peak = cluster.loc[cluster["positive_change_m"].idxmax()]
                at_peak = players.loc[
                    players["match_id"].eq(match_id)
                    & players["team_key"].eq(team_key)
                    & players["period"].eq(peak["period"])
                    & players["frame_id_provider"].eq(peak["frame_id_provider"])
                ].nlargest(spec.leading_players, "trailing_relative_path_m")
                matching_runs = [
                    run
                    for run in runs
                    if str(run.get("match_id")) == str(match_id)
                    and int(run.get("period")) == int(peak["period"])
                    and float(run.get("start_time_s")) <= float(peak["time_match_s"])
                    <= float(run.get("end_time_s"))
                ]
                if matching_runs:
                    run = matching_runs[0]
                    from_start = float(peak["time_match_s"] - float(run["start_time_s"]))
                    to_end = float(float(run["end_time_s"]) - peak["time_match_s"])
                else:
                    period_group = group.loc[group["period"].eq(peak["period"])]
                    from_start = float(
                        peak["time_match_s"] - period_group["time_match_s"].min()
                    )
                    to_end = float(
                        period_group["time_match_s"].max() - peak["time_match_s"]
                    )
                boundary = min(from_start, to_end) < spec.interior_guard_seconds
                rows.append(
                    {
                        "moment_type": moment_type,
                        "match_id": match_id,
                        "period": peak["period"],
                        "team_key": team_key,
                        "start_time_s": float(cluster["time_match_s"].iloc[0]),
                        "end_time_s": float(cluster["time_match_s"].iloc[-1]),
                        "peak_time_s": float(peak["time_match_s"]),
                        "duration_s": float(
                            cluster["time_match_s"].iloc[-1] - cluster["time_match_s"].iloc[0]
                        ),
                        "team_score_m": float(peak["mean_trailing_relative_path_m"]),
                        "within_match_percentile": float(peak["within_match_percentile"]),
                        "positive_change_m": (
                            None
                            if not np.isfinite(float(peak["positive_change_m"]))
                            else float(peak["positive_change_m"])
                        ),
                        "leading_player_contributors": json.dumps(
                            [
                                {
                                    "player_key": str(row.player_key),
                                    "score_m": float(row.trailing_relative_path_m),
                                }
                                for row in at_peak.itertuples(index=False)
                            ],
                            separators=(",", ":"),
                        ),
                        "seconds_from_run_start": from_start,
                        "seconds_to_run_end": to_end,
                        "boundary_flag": bool(boundary),
                        "interior_eligible": bool(not boundary),
                        "selected_for_clip": False,
                    }
                )
            order = "positive_change_m" if criterion == "change" else "team_score_m"
            reverse = criterion != "min"
            rows = sorted(
                rows,
                key=lambda row: -np.inf if row[order] is None else float(row[order]),
                reverse=reverse,
            )
            selected = 0
            for row in rows:
                if row["interior_eligible"] and selected < spec.top_n_per_type:
                    row["selected_for_clip"] = True
                    selected += 1
            passages.extend(rows)
    result = pd.DataFrame(passages, columns=MOMENT_COLUMNS)
    if audit:
        return result
    return result.loc[result["selected_for_clip"]].reset_index(drop=True)


def align_events(
    events: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    *,
    defending_team_key: str,
    lookbacks_seconds: Iterable[float] = (2.0, 5.0, 10.0),
) -> pd.DataFrame:
    """Join descriptive event times to the preceding supported team timeline."""
    required = {"event_id", "match_id", "period", "event_time_s", "event_type", "team_key"}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"missing event columns: {sorted(missing)}")
    lookbacks = tuple(float(value) for value in lookbacks_seconds)
    if not lookbacks or any(not np.isfinite(value) or value <= 0 for value in lookbacks):
        raise ValueError("lookbacks must be finite and positive")
    if len(set(lookbacks)) != len(lookbacks):
        raise ValueError("lookbacks must be unique")
    team = scores.team_scores.loc[
        scores.team_scores["team_key"].eq(defending_team_key)
        & scores.team_scores["support_status"].eq(SUPPORTED)
        & np.isfinite(scores.team_scores["mean_trailing_relative_path_m"])
    ].copy()
    team["within_match_percentile"] = team.groupby(
        ["match_id", "team_key"], sort=False
    )["mean_trailing_relative_path_m"].rank(method="average", pct=True)
    rows: list[dict[str, object]] = []
    for event in events.sort_values(
        ["match_id", "period", "event_time_s", "event_id"], kind="mergesort"
    ).itertuples(index=False):
        timeline = team.loc[
            team["match_id"].eq(event.match_id)
            & team["period"].eq(event.period)
            & (team["time_match_s"] <= float(event.event_time_s))
        ].sort_values("time_match_s")
        base = {
            "event_id": event.event_id,
            "match_id": event.match_id,
            "period": event.period,
            "event_time_s": float(event.event_time_s),
            "event_type": str(event.event_type),
            "team_key": event.team_key,
            "defending_team_key": defending_team_key,
            "score_at_event_m": np.nan,
            "within_match_percentile": np.nan,
        }
        if not timeline.empty:
            current = timeline.iloc[-1]
            base["score_at_event_m"] = float(current["mean_trailing_relative_path_m"])
            base["within_match_percentile"] = float(current["within_match_percentile"])
        for seconds in lookbacks:
            label = f"previous_{seconds:g}s"
            window = timeline.loc[
                timeline["time_match_s"] >= float(event.event_time_s) - seconds
            ]
            base[f"{label}_mean_m"] = (
                np.nan if window.empty else float(window["mean_trailing_relative_path_m"].mean())
            )
            base[f"{label}_peak_m"] = (
                np.nan if window.empty else float(window["mean_trailing_relative_path_m"].max())
            )
            before = timeline.loc[
                timeline["time_match_s"] <= float(event.event_time_s) - seconds
            ]
            base[f"{label}_change_m"] = (
                np.nan
                if timeline.empty or before.empty
                else float(
                    timeline.iloc[-1]["mean_trailing_relative_path_m"]
                    - before.iloc[-1]["mean_trailing_relative_path_m"]
                )
            )
        rows.append(base)
    return pd.DataFrame(rows)


def query_event_windows(
    events: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    query: EventWindowQuery,
) -> EventWindowResult:
    """Rank event-anchored windows using already-computed replay scores.

    Event labels narrow review candidates; they do not classify tactics or
    infer possession, intent, success, or causation.
    """
    required = {"event_id", "match_id", "period", "event_time_s", "event_type", "team_key"}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"missing event columns: {sorted(missing)}")
    candidates = events.copy(deep=True)
    candidates["event_type"] = candidates["event_type"].astype(str).str.upper()
    if query.explicit_timestamps:
        match_ids = scores.team_scores["match_id"].dropna().astype(str).unique()
        if len(match_ids) != 1:
            raise ValueError("explicit timestamps require exactly one event match_id")
        additions = []
        for index, (period, time_s) in enumerate(query.explicit_timestamps, start=1):
            exists = candidates["period"].eq(int(period)) & np.isclose(
                candidates["event_time_s"].astype(float), float(time_s), atol=1e-7, rtol=0
            )
            if not exists.any():
                additions.append(
                    {
                        "event_id": f"explicit-p{int(period)}-{float(time_s):.6f}-{index}",
                        "match_id": match_ids[0], "period": int(period),
                        "event_time_s": float(time_s), "event_type": "EXPLICIT_TIMESTAMP",
                        "team_key": query.attacking_team_key or "unspecified",
                        "event_detail": "analyst-supplied timestamp",
                    }
                )
        if additions:
            candidates = pd.concat([candidates, pd.DataFrame(additions)], ignore_index=True)
    masks = []
    if query.event_types:
        masks.append(candidates["event_type"].isin(query.event_types))
    if query.explicit_timestamps:
        timestamp_mask = pd.Series(False, index=candidates.index)
        for period, time_s in query.explicit_timestamps:
            timestamp_mask |= candidates["period"].eq(int(period)) & np.isclose(
                candidates["event_time_s"].astype(float), float(time_s), atol=1e-7, rtol=0
            )
        masks.append(timestamp_mask)
    keep = masks[0]
    for mask in masks[1:]:
        keep |= mask
    candidates = candidates.loc[keep]
    if query.attacking_team_key is not None:
        candidates = candidates.loc[candidates["team_key"].eq(query.attacking_team_key)]

    team = scores.team_scores.loc[
        scores.team_scores["team_key"].eq(query.defending_team_key)
        & scores.team_scores["support_status"].eq(SUPPORTED)
        & np.isfinite(scores.team_scores["mean_trailing_relative_path_m"])
    ].copy()
    players = scores.player_scores.loc[
        scores.player_scores["team_key"].eq(query.defending_team_key)
        & scores.player_scores["support_status"].eq(SUPPORTED)
        & np.isfinite(scores.player_scores["trailing_relative_path_m"])
    ].copy()
    rows: list[dict[str, object]] = []
    ordered = candidates.sort_values(
        ["match_id", "period", "event_time_s", "event_id"], kind="mergesort"
    )
    for event in ordered.itertuples(index=False):
        event_time = float(event.event_time_s)
        raw_event_x = getattr(event, "event_x_m", np.nan)
        raw_event_y = getattr(event, "event_y_m", np.nan)
        timeline = team.loc[
            team["match_id"].eq(event.match_id)
            & team["period"].eq(event.period)
            & team["time_match_s"].between(
                event_time - query.pre_seconds, event_time + query.post_seconds
            )
        ].sort_values("time_match_s", kind="mergesort")
        anchor = timeline.loc[timeline["time_match_s"] <= event_time]
        cadence = 1.0 / float(scores.metadata["source_fps"])
        complete = (
            not timeline.empty
            and not anchor.empty
            and float(timeline.iloc[0]["time_match_s"])
            <= event_time - query.pre_seconds + cadence / 2 + 1e-7
            and float(timeline.iloc[-1]["time_match_s"])
            >= event_time + query.post_seconds - cadence / 2 - 1e-7
        )
        suitability = bool(getattr(event, "visual_suitable", True))
        reason = str(getattr(event, "visual_suitability_reason", ""))
        row: dict[str, object] = {
            "event_id": str(event.event_id), "match_id": str(event.match_id),
            "period": int(event.period), "event_time_s": event_time,
            "event_type": str(event.event_type),
            "event_detail": str(getattr(event, "event_detail", "")),
            "event_x_m": np.nan if pd.isna(raw_event_x) else float(raw_event_x),
            "event_y_m": np.nan if pd.isna(raw_event_y) else float(raw_event_y),
            "attacking_team_key": str(event.team_key),
            "defending_team_key": query.defending_team_key,
            "pre_score_m": np.nan, "anchor_score_m": np.nan, "post_score_m": np.nan,
            "maximum_score_m": np.nan, "post_minus_pre_change_m": np.nan,
            "time_to_peak_s": np.nan, "leading_player_contributors": "",
            "support_status": "supported" if complete else "unsupported",
            "suitability_status": "suitable" if suitability else "unsuitable",
            "suitability_reason": reason,
            "rank_by": query.rank_by, "rank_value": np.nan, "rank": pd.NA,
        }
        if complete:
            pre_value = float(timeline.iloc[0]["mean_trailing_relative_path_m"])
            anchor_value = float(anchor.iloc[-1]["mean_trailing_relative_path_m"])
            post_value = float(timeline.iloc[-1]["mean_trailing_relative_path_m"])
            peak_index = timeline["mean_trailing_relative_path_m"].astype(float).idxmax()
            peak = timeline.loc[peak_index]
            peak_time = float(peak["time_match_s"])
            at_peak = players.loc[
                players["match_id"].eq(event.match_id)
                & players["period"].eq(event.period)
                & np.isclose(players["time_match_s"], peak_time, atol=1e-7, rtol=0)
            ].sort_values(
                ["trailing_relative_path_m", "player_key"],
                ascending=[False, True], kind="mergesort"
            )
            leaders = at_peak.head(query.leading_players)["player_key"].astype(str).tolist()
            row.update(
                pre_score_m=pre_value, anchor_score_m=anchor_value,
                post_score_m=post_value,
                maximum_score_m=float(peak["mean_trailing_relative_path_m"]),
                post_minus_pre_change_m=post_value - pre_value,
                time_to_peak_s=peak_time - event_time,
                leading_player_contributors="|".join(leaders),
            )
            rank_columns = {
                "anchor_score": "anchor_score_m", "maximum_score": "maximum_score_m",
                "post_minus_pre_change": "post_minus_pre_change_m",
                "time_to_peak": "time_to_peak_s",
            }
            row["rank_value"] = row[rank_columns[query.rank_by]]
        rows.append(row)
    frame = pd.DataFrame(rows, columns=EVENT_WINDOW_COLUMNS)
    eligible = frame.loc[frame.support_status.eq("supported")]
    if query.require_suitable:
        eligible = eligible.loc[eligible.suitability_status.eq("suitable")]
    ascending = query.rank_by == "time_to_peak"
    eligible = eligible.sort_values(
        ["rank_value", "event_time_s", "event_id"],
        ascending=[ascending, True, True], kind="mergesort"
    ).head(query.limit).copy()
    eligible["rank"] = np.arange(1, len(eligible) + 1)
    no_result_reasons = []
    if candidates.empty:
        no_result_reasons.append("no matching events")
    elif eligible.empty:
        if frame.support_status.ne("supported").all():
            no_result_reasons.append("no matching event has complete score support")
        elif query.require_suitable:
            no_result_reasons.append("no supported matching event passed suitability checks")
    return EventWindowResult(
        eligible.reset_index(drop=True),
        {
            "question": "What defensive reorganization happened around the requested events?",
            "candidate_count": int(len(candidates)), "result_count": int(len(eligible)),
            "rank_by": query.rank_by, "no_result_reasons": tuple(no_result_reasons),
            "claim_boundary": (
                "event-anchored retrospective geometry for human review; event labels do not "
                "classify tactics, intent, quality, cause, success, or value"
            ),
        },
    )


def render_selected_passage(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    clip_spec: TrackingClipSpec,
    output_dir: str | Path,
    *,
    stem: str,
    selected_time_s: float | None = None,
    frame_step: int = 2,
    playback_fps: float = 12.5,
    score_vmax_m: float = DEFAULT_SCORE_VMAX_M,
    show_focal_highlight: bool = False,
    diagnostic_anchor_label: str | None = None,
    coach_facing: bool = False,
    context_note: str | None = None,
) -> dict[str, Path]:
    """Render one caller-selected window using the existing visualization."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    figure = plot_defensive_reorganization_diagnostic(
        tracking,
        scores,
        clip_spec,
        selected_time_s=selected_time_s,
        score_vmax_m=score_vmax_m,
        show_focal_highlight=show_focal_highlight,
    )
    if diagnostic_anchor_label is not None and figure.axes:
        figure.axes[0].set_xlabel(diagnostic_anchor_label)
    png = destination / f"{stem}_diagnostic.png"
    figure.savefig(png, dpi=160, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(figure)
    bundle = animate_defensive_reorganization(
        tracking,
        scores,
        clip_spec,
        frame_step=frame_step,
        playback_fps=playback_fps,
        score_vmax_m=score_vmax_m,
        show_focal_highlight=show_focal_highlight,
        coach_facing=coach_facing,
        show_team_meter=not coach_facing,
        context_note=context_note,
    )
    gif = export_animation(bundle, destination / f"{stem}.gif")
    plt.close(bundle.figure)
    return {"diagnostic_png": png, "gif": gif}


def _select_global_moments(
    audit: pd.DataFrame, quota: int, *, exclusion_seconds: float
) -> pd.DataFrame:
    """Select distinct public moments with a fixed cross-category priority.

    High, rapid-increase, then low candidates are considered in that order.
    Within the same match and period, a later category cannot reuse an episode
    whose peak lies within ``exclusion_seconds`` of an already selected peak.
    """
    if not np.isfinite(exclusion_seconds) or exclusion_seconds < 0:
        raise ValueError("exclusion_seconds must be finite and nonnegative")
    groups = []
    eligible = audit.loc[audit["interior_eligible"]]
    for moment_type in ("high", "rapid_increase", "low"):
        group = eligible.loc[eligible["moment_type"].eq(moment_type)]
        if group.empty:
            continue
        column = "positive_change_m" if moment_type == "rapid_increase" else "team_score_m"
        ascending = moment_type == "low"
        ranked = group.sort_values(column, ascending=ascending, kind="mergesort")
        chosen_rows = []
        for row in ranked.itertuples(index=False):
            conflicts = any(
                int(row.period) == int(selected.period)
                and str(row.match_id) == str(selected.match_id)
                and abs(float(row.peak_time_s) - float(selected.peak_time_s))
                <= exclusion_seconds
                for chosen in groups
                for selected in chosen.itertuples(index=False)
            )
            if conflicts:
                continue
            chosen_rows.append(row)
            if len(chosen_rows) == quota:
                break
        if chosen_rows:
            groups.append(pd.DataFrame(chosen_rows, columns=ranked.columns))
    if not groups:
        return pd.DataFrame(columns=MOMENT_COLUMNS)
    selected = pd.concat(groups, ignore_index=True)
    selected["selected_for_clip"] = True
    return selected.sort_values(
        ["moment_type", "team_key", "peak_time_s"], kind="mergesort"
    ).reset_index(drop=True)


def analyze_match(
    tracking: pd.DataFrame,
    *,
    defending_team_keys: Iterable[str],
    config: MatchApplicationConfig,
    events: pd.DataFrame | None = None,
    excluded_player_keys: Mapping[str, Iterable[str]] | None = None,
    output_dir: str | Path | None = None,
    render_selected: bool = False,
) -> MatchApplicationResult:
    """Run the deterministic notebook-oriented application pipeline in one call.

    The caller supplies normalized tracking and optional normalized events. The
    function scores stable support runs, audits/selects moments, aligns events,
    exports tables when requested, and can render the selected clip set.
    """
    teams = tuple(dict.fromkeys(str(team) for team in defending_team_keys))
    if len(teams) != 2:
        raise ValueError("the default match application requires exactly two team keys")
    match_ids = tracking["match_id"].dropna().astype(str).unique()
    if len(match_ids) != 1:
        raise ValueError("the default match application requires exactly one match")
    excluded = excluded_player_keys or {}
    score_by_team: dict[str, DefensiveReorganizationScores] = {}
    audits = []
    distributions = []
    artifacts: dict[str, str] = {}
    destination = None if output_dir is None else Path(output_dir)
    if destination is not None:
        destination.mkdir(parents=True, exist_ok=True)

    moment_spec = MomentDiscoverySpec(
        top_n_per_type=config.category_quota,
        tail_fraction=config.tail_fraction,
        adjacency_seconds=config.adjacency_seconds,
        leading_players=config.leading_players,
        interior_guard_seconds=config.interior_guard_seconds,
    )
    for team in teams:
        scores = score_stable_runs(
            tracking,
            defending_team_key=team,
            source_fps=config.source_fps,
            smoothing_frames=config.smoothing_frames,
            window_seconds=config.window_seconds,
            excluded_player_keys=excluded.get(team, ()),
        )
        score_by_team[team] = scores
        audit = discover_moments(scores, moment_spec, audit=True)
        audits.append(audit)
        supported = scores.team_scores.loc[scores.team_scores.support_status.eq(SUPPORTED)]
        values = supported.mean_trailing_relative_path_m.to_numpy(float)
        quantiles = np.quantile(values, [0, .05, .25, .5, .75, .95, 1])
        distributions.append(
            {
                "match_id": supported.match_id.iloc[0],
                "defending_team_key": team,
                "stable_runs": len(scores.metadata["stable_runs"]),
                "supported_frames": len(values),
                **dict(
                    zip(
                        ("min_m", "p05_m", "p25_m", "median_m", "p75_m", "p95_m", "max_m"),
                        map(float, quantiles),
                        strict=True,
                    )
                ),
            }
        )
        if destination is not None:
            exported = export_scores(
                scores,
                destination / team.replace(":", "_"),
                formats=config.export_formats,
            )
            artifacts.update(
                {f"{team}:{name}": str(path) for name, path in exported.items()}
            )

    audit = pd.concat(audits, ignore_index=True)
    audit["selected_for_clip"] = False
    selected = _select_global_moments(
        audit,
        config.category_quota,
        exclusion_seconds=2 * config.clip_context_seconds,
    )
    if not selected.empty:
        keys = set(
            zip(
                selected.moment_type,
                selected.team_key,
                selected.period,
                selected.peak_time_s,
            )
        )
        audit["selected_for_clip"] = [
            (row.moment_type, row.team_key, row.period, row.peak_time_s) in keys
            for row in audit.itertuples(index=False)
        ]

    event_tables = []
    if events is not None:
        for defending in teams:
            attacking = next(team for team in teams if team != defending)
            relevant = events.loc[events["team_key"].eq(attacking)]
            event_tables.append(
                align_events(
                    relevant,
                    score_by_team[defending],
                    defending_team_key=defending,
                    lookbacks_seconds=config.event_lookbacks_seconds,
                )
            )
    event_summary = (
        pd.concat(event_tables, ignore_index=True)
        if event_tables
        else pd.DataFrame(columns=EVENT_SUMMARY_BASE_COLUMNS)
    )
    distribution_frame = pd.DataFrame(distributions)

    if render_selected:
        if destination is None:
            raise ValueError("render_selected requires output_dir")
        for index, row in enumerate(selected.itertuples(index=False), start=1):
            defending = str(row.team_key)
            attacking = next(team for team in teams if team != defending)
            peak = float(row.peak_time_s)
            start = peak - config.clip_context_seconds
            end = peak + config.clip_context_seconds
            scores = score_by_team[defending]
            at_peak = scores.player_scores.loc[
                scores.player_scores["period"].eq(row.period)
                & np.isclose(
                    scores.player_scores["time_match_s"], peak, atol=1e-7, rtol=0
                )
            ]
            defender_keys = set(at_peak.player_key.astype(str))
            clip_tracking = tracking.loc[
                tracking["period"].eq(row.period)
                & tracking["time_match_s"].between(start, end)
                & ~(
                    tracking["team_key"].eq(defending)
                    & ~tracking["player_key"].astype(str).isin(defender_keys)
                )
            ].copy()
            frame_count = clip_tracking[["frame_id_provider", "time_match_s"]].drop_duplicates().shape[0]
            focal = []
            for key, group in clip_tracking.loc[
                clip_tracking["entity_type"].eq("player")
                & clip_tracking["team_key"].eq(attacking)
            ].groupby("player_key", sort=True):
                valid = group["coordinate_valid"].astype(bool) & np.isfinite(
                    group[["x_m", "y_m"]]
                ).all(axis=1)
                if len(group) == frame_count and valid.all():
                    focal.append(str(key))
            if len(defender_keys) != 10 or not focal:
                raise ValueError("selected clip lacks complete player support")
            clip_spec = TrackingClipSpec(
                match_id=str(row.match_id),
                period=int(row.period),
                anchor_time_s=peak,
                start_time_s=start,
                end_time_s=end,
                focal_player_key=focal[0],
                attacking_team_key=attacking,
                defending_team_key=defending,
                defender_ranks=None,
            )
            clip_scores = DefensiveReorganizationScores(
                scores.player_scores.loc[
                    scores.player_scores["period"].eq(row.period)
                    & scores.player_scores["time_match_s"].between(start, end)
                    & scores.player_scores["player_key"].astype(str).isin(defender_keys)
                ].reset_index(drop=True),
                scores.team_scores.loc[
                    scores.team_scores["period"].eq(row.period)
                    & scores.team_scores["time_match_s"].between(start, end)
                ].reset_index(drop=True),
                {**scores.metadata, "source_fps": config.source_fps},
            )
            stem = f"{index:02d}_{row.moment_type}_{defending.replace(':', '_')}_{peak:.2f}"
            paths = render_selected_passage(
                clip_tracking,
                clip_scores,
                clip_spec,
                destination / "selected_clips",
                stem=stem,
                selected_time_s=peak,
                frame_step=config.frame_step,
                playback_fps=config.playback_fps,
                score_vmax_m=config.score_vmax_m,
                show_focal_highlight=False,
            )
            artifacts.update(
                {f"clip_{index}:{name}": str(path) for name, path in paths.items()}
            )

    if destination is not None:
        tables = {
            "moment_audit_csv": ("moment_audit.csv", audit),
            "selected_moments_csv": ("selected_moments.csv", selected),
            "event_summary_csv": ("event_summary.csv", event_summary),
            "distributions_csv": ("team_score_distributions.csv", distribution_frame),
        }
        for name, (filename, frame) in tables.items():
            path = destination / filename
            frame.to_csv(path, index=False, lineterminator="\n")
            artifacts[name] = str(path)

    metadata = {
        "status": "EXPLORATORY_APPLICATION_COMPLETE",
        "match_id": str(match_ids[0]),
        "teams": teams,
        "source_fps": config.source_fps,
        "smoothing_frames": config.smoothing_frames,
        "window_seconds": config.window_seconds,
        "interior_guard_seconds": config.interior_guard_seconds,
        "adjacency_seconds": config.adjacency_seconds,
        "tail_fraction": config.tail_fraction,
        "category_quota": config.category_quota,
        "event_lookbacks_seconds": config.event_lookbacks_seconds,
        "clip_context_seconds": config.clip_context_seconds,
        "score_vmax_m": config.score_vmax_m,
        "boundary_candidate_count": int(audit.boundary_flag.sum()),
        "selected_moment_count": int(len(selected)),
        "selection_policy": {
            "support_segmentation": (
                "maximal regular-cadence runs with exactly ten stable finite outfield identities"
            ),
            "boundary_guard": "symmetric distance from stable-run boundaries",
            "clustering": "adjacent threshold-qualified frames grouped before ranking",
            "categories": ("high", "low", "rapid_increase"),
            "selection_scope": "global across the two defending-team timelines",
            "event_alignment": "descriptive defending-team score at and before supplied events",
            "rendering": "optional six-second context clips centered on selected peaks",
        },
        "claim_boundary": (
            "descriptive retrospective geometry only; not causal, predictive, tactical, or validated utility"
        ),
    }
    if destination is not None:
        metadata_path = destination / "application_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        artifacts["application_metadata_json"] = str(metadata_path)
    return MatchApplicationResult(
        score_by_team,
        audit,
        selected,
        event_summary,
        distribution_frame,
        metadata,
        artifacts,
    )
