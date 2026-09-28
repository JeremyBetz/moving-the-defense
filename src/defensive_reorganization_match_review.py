"""Reference-calibrated defensive-reorganization match-review helpers.

This module is an analyst-facing wrapper around the committed retrospective
scorer.  Raw metres remain authoritative; empirical reference percentiles are
descriptive context only.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_application import render_selected_passage, score_stable_runs
from defensive_reorganization_replay import SUPPORTED, DefensiveReorganizationScores
from defensive_reorganization_replay_visualization import (
    DEFAULT_SCORE_VMAX_M,
    plot_defensive_reorganization_diagnostic,
)
from tracking_animation import TrackingClipSpec


REFERENCE_MOMENT_COLUMNS = (
    "moment_type",
    "match_id",
    "period",
    "team_key",
    "run_id",
    "start_time_s",
    "end_time_s",
    "peak_time_s",
    "duration_s",
    "team_score_m",
    "reference_percentile",
    "before_score_m",
    "one_second_change_m",
    "before_reference_percentile",
    "leading_player_scores_m",
    "render_eligible",
    "selected_for_case_study",
    "category_memberships",
)

EVENT_CONTEXT_COLUMNS = (
    "event_id",
    "match_id",
    "period",
    "event_time_s",
    "event_type",
    "event_detail",
    "attacking_team_key",
    "defending_team_key",
    "shot_on_target",
    "alignment_status",
    "matched_time_s",
    "alignment_error_s",
    "score_at_event_m",
    "reference_percentile_at_event",
    "previous_2s_mean_m",
    "previous_2s_max_m",
    "previous_2s_max_reference_percentile",
    "previous_5s_mean_m",
    "previous_5s_max_m",
    "previous_5s_max_reference_percentile",
    "previous_10s_mean_m",
    "previous_10s_max_m",
    "previous_10s_max_reference_percentile",
    "change_1s_m",
    "change_2s_m",
    "leading_player_scores_m",
)


@dataclass(frozen=True)
class PooledScoreReference:
    """Sorted raw reference distributions used only for descriptive context."""

    player_scores_m: np.ndarray
    team_scores_m: np.ndarray
    one_second_changes_m: np.ndarray
    source_fps: float
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        arrays = {}
        for name in ("player_scores_m", "team_scores_m", "one_second_changes_m"):
            values = np.sort(np.asarray(getattr(self, name), dtype=float).copy())
            if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
                raise ValueError(f"{name} must be a nonempty finite one-dimensional array")
            values.setflags(write=False)
            arrays[name] = values
        if not np.isfinite(self.source_fps) or self.source_fps <= 0:
            raise ValueError("source_fps must be finite and positive")
        for name, values in arrays.items():
            object.__setattr__(self, name, values)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @staticmethod
    def _percentile(values: np.ndarray | float, reference: np.ndarray) -> np.ndarray:
        raw = np.asarray(values, dtype=float)
        if not np.isfinite(raw).all():
            raise ValueError("percentile inputs must be finite")
        return np.searchsorted(reference, raw, side="right") / float(reference.size)

    def player_percentile(self, values: np.ndarray | float) -> np.ndarray:
        return self._percentile(values, self.player_scores_m)

    def team_percentile(self, values: np.ndarray | float) -> np.ndarray:
        return self._percentile(values, self.team_scores_m)

    @property
    def high_threshold_m(self) -> float:
        return float(np.quantile(self.team_scores_m, 0.95, method="linear"))

    @property
    def low_threshold_m(self) -> float:
        return float(np.quantile(self.team_scores_m, 0.05, method="linear"))

    @property
    def rapid_threshold_m(self) -> float:
        return float(np.quantile(self.one_second_changes_m, 0.95, method="linear"))


@dataclass(frozen=True)
class ReferenceMomentSpec:
    minimum_high_low_seconds: float = 1.0
    change_seconds: float = 1.0
    selection_per_category: int = 2
    render_context_seconds: float = 5.0
    leading_players: int = 3

    def __post_init__(self) -> None:
        finite = (
            self.minimum_high_low_seconds,
            self.change_seconds,
            self.render_context_seconds,
        )
        if not np.isfinite(finite).all() or min(finite) <= 0:
            raise ValueError("moment durations must be finite and positive")
        if self.selection_per_category < 1 or self.leading_players < 1:
            raise ValueError("selection and contribution counts must be positive")


@dataclass(frozen=True)
class ReferenceMatchAnalysis:
    scores_by_team: Mapping[str, DefensiveReorganizationScores]
    player_timelines: Mapping[str, pd.DataFrame]
    team_timelines: Mapping[str, pd.DataFrame]
    moments: pd.DataFrame
    selected_moments: pd.DataFrame
    distributions: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scores_by_team", MappingProxyType(dict(self.scores_by_team)))
        object.__setattr__(
            self,
            "player_timelines",
            MappingProxyType({key: value.copy(deep=True) for key, value in self.player_timelines.items()}),
        )
        object.__setattr__(
            self,
            "team_timelines",
            MappingProxyType({key: value.copy(deep=True) for key, value in self.team_timelines.items()}),
        )
        object.__setattr__(self, "moments", self.moments.copy(deep=True))
        object.__setattr__(self, "selected_moments", self.selected_moments.copy(deep=True))
        object.__setattr__(self, "distributions", self.distributions.copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def empirical_reference_percentile(
    values: np.ndarray | Iterable[float] | float,
    sorted_reference: np.ndarray | Iterable[float],
) -> np.ndarray:
    """Return the frozen right-sided empirical-CDF reference percentile."""
    reference = np.asarray(sorted_reference, dtype=float)
    raw = np.asarray(values, dtype=float)
    if reference.ndim != 1 or reference.size == 0 or not np.isfinite(reference).all():
        raise ValueError("reference must be a nonempty finite one-dimensional array")
    if np.any(reference[1:] < reference[:-1]):
        raise ValueError("reference must be sorted")
    if not np.isfinite(raw).all():
        raise ValueError("values must be finite")
    return np.searchsorted(reference, raw, side="right") / float(reference.size)


def format_reference_percentile(value: float) -> str:
    """Format reference context without implying rounded empirical endpoints."""
    percentile = float(value)
    if not np.isfinite(percentile) or not 0.0 <= percentile <= 1.0:
        raise ValueError("reference percentile must be finite and in [0, 1]")
    if percentile >= 0.999:
        return ">P99.9"
    if percentile <= 0.001:
        return "<P0.1"
    return f"P{100 * percentile:.1f}"


def _supported_team_with_runs(scores: DefensiveReorganizationScores) -> pd.DataFrame:
    team = scores.team_scores.loc[
        scores.team_scores["support_status"].eq(SUPPORTED)
        & np.isfinite(scores.team_scores["mean_trailing_relative_path_m"])
    ].copy()
    team = team.sort_values(
        ["match_id", "team_key", "period", "time_match_s", "frame_id_provider"],
        kind="mergesort",
    ).reset_index(drop=True)
    team["run_id"] = ""
    runs = list(scores.metadata.get("stable_runs", ()))
    for run in runs:
        mask = (
            team["match_id"].astype(str).eq(str(run["match_id"]))
            & team["period"].eq(int(run["period"]))
            & team["time_match_s"].between(
                float(run["start_time_s"]), float(run["end_time_s"])
            )
        )
        run_id = f"{run['match_id']}::p{int(run['period'])}::run{int(run['run_index'])}"
        if (team.loc[mask, "run_id"] != "").any():
            raise RuntimeError("stable-run metadata overlap")
        team.loc[mask, "run_id"] = run_id
    if team.empty or team["run_id"].eq("").any():
        raise RuntimeError("supported team frame is not bound to one stable run")
    return team


def _one_second_changes(
    scores: DefensiveReorganizationScores, source_fps: float
) -> pd.DataFrame:
    offset = int(round(float(source_fps)))
    if not np.isclose(offset / float(source_fps), 1.0, atol=1e-12, rtol=0):
        raise ValueError("source cadence must represent exactly one second in whole frames")
    cadence = 1.0 / float(source_fps)
    parts = []
    for run_id, group in _supported_team_with_runs(scores).groupby("run_id", sort=True):
        q = group.sort_values(["time_match_s", "frame_id_provider"], kind="mergesort").copy()
        times = q["time_match_s"].to_numpy(float)
        if len(times) > 1 and not np.allclose(np.diff(times), cadence, atol=1e-7, rtol=0):
            raise RuntimeError(f"supported run is not regular at {source_fps:g} Hz: {run_id}")
        q["before_score_m"] = q["mean_trailing_relative_path_m"].shift(offset)
        q["before_time_s"] = q["time_match_s"].shift(offset)
        q["one_second_change_m"] = (
            q["mean_trailing_relative_path_m"] - q["before_score_m"]
        )
        complete = np.isclose(
            q["time_match_s"] - q["before_time_s"], 1.0, atol=1e-7, rtol=0
        )
        q.loc[~complete, ["before_score_m", "one_second_change_m"]] = np.nan
        parts.append(q)
    return pd.concat(parts, ignore_index=True)


def build_pooled_reference(
    scores_by_population: Mapping[str, DefensiveReorganizationScores],
    *,
    source_fps: float,
    metadata: Mapping[str, object] | None = None,
) -> PooledScoreReference:
    """Build separate pooled raw player/team/change references in memory."""
    if not scores_by_population:
        raise ValueError("at least one population score package is required")
    player_values: list[np.ndarray] = []
    team_values: list[np.ndarray] = []
    changes: list[np.ndarray] = []
    stable_runs = 0
    for label, scores in sorted(scores_by_population.items()):
        if not np.isclose(float(scores.metadata["source_fps"]), source_fps):
            raise ValueError(f"source cadence mismatch for {label}")
        players = scores.player_scores.loc[
            scores.player_scores["support_status"].eq(SUPPORTED),
            "trailing_relative_path_m",
        ].to_numpy(float)
        teams = _supported_team_with_runs(scores)["mean_trailing_relative_path_m"].to_numpy(float)
        delta = _one_second_changes(scores, source_fps)["one_second_change_m"].dropna().to_numpy(float)
        if not np.isfinite(players).all() or not np.isfinite(teams).all() or not np.isfinite(delta).all():
            raise RuntimeError(f"nonfinite supported reference value for {label}")
        player_values.append(players)
        team_values.append(teams)
        changes.append(delta)
        stable_runs += len(scores.metadata.get("stable_runs", ()))
    return PooledScoreReference(
        np.concatenate(player_values),
        np.concatenate(team_values),
        np.concatenate(changes),
        float(source_fps),
        {
            **dict(metadata or {}),
            "population_labels": tuple(sorted(scores_by_population)),
            "stable_run_count": stable_runs,
            "player_score_count": int(sum(map(len, player_values))),
            "team_score_count": int(sum(map(len, team_values))),
            "one_second_change_count": int(sum(map(len, changes))),
            "percentile_semantics": "right_sided_empirical_cdf_reference_context",
        },
    )


def _reference_timelines(
    scores: DefensiveReorganizationScores, reference: PooledScoreReference
) -> tuple[pd.DataFrame, pd.DataFrame]:
    players = scores.player_scores.copy()
    teams = scores.team_scores.copy()
    player_mask = players["support_status"].eq(SUPPORTED) & np.isfinite(
        players["trailing_relative_path_m"]
    )
    team_mask = teams["support_status"].eq(SUPPORTED) & np.isfinite(
        teams["mean_trailing_relative_path_m"]
    )
    players["reference_percentile"] = np.nan
    teams["reference_percentile"] = np.nan
    players.loc[player_mask, "reference_percentile"] = reference.player_percentile(
        players.loc[player_mask, "trailing_relative_path_m"].to_numpy(float)
    )
    teams.loc[team_mask, "reference_percentile"] = reference.team_percentile(
        teams.loc[team_mask, "mean_trailing_relative_path_m"].to_numpy(float)
    )
    return players, teams


def _clusters(candidates: pd.DataFrame, cadence: float) -> list[pd.DataFrame]:
    if candidates.empty:
        return []
    q = candidates.sort_values(
        ["match_id", "team_key", "period", "run_id", "time_match_s"], kind="mergesort"
    ).reset_index(drop=True)
    cuts = [0]
    for index in range(1, len(q)):
        previous, current = q.iloc[index - 1], q.iloc[index]
        continuous = (
            str(current.run_id) == str(previous.run_id)
            and np.isclose(
                float(current.time_match_s) - float(previous.time_match_s),
                cadence,
                atol=1e-7,
                rtol=0,
            )
        )
        if not continuous:
            cuts.append(index)
    cuts.append(len(q))
    return [q.iloc[start:end].copy() for start, end in zip(cuts[:-1], cuts[1:], strict=True)]


def _leading_scores(
    scores: DefensiveReorganizationScores,
    *,
    match_id: str,
    period: int,
    team_key: str,
    frame_id_provider: object,
    count: int,
) -> str:
    q = scores.player_scores.loc[
        scores.player_scores["match_id"].astype(str).eq(str(match_id))
        & scores.player_scores["period"].eq(period)
        & scores.player_scores["team_key"].eq(team_key)
        & scores.player_scores["frame_id_provider"].astype(str).eq(str(frame_id_provider))
        & scores.player_scores["support_status"].eq(SUPPORTED)
    ].sort_values(
        ["trailing_relative_path_m", "player_key"],
        ascending=[False, True],
        kind="mergesort",
    )
    return json.dumps(
        [round(float(value), 6) for value in q["trailing_relative_path_m"].head(count)],
        separators=(",", ":"),
    )


def find_reorganization_windows(
    scores_by_team: Mapping[str, DefensiveReorganizationScores],
    reference: PooledScoreReference,
    spec: ReferenceMomentSpec = ReferenceMomentSpec(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Discover frozen high, low, and one-second-increase episodes."""
    cadence = 1.0 / reference.source_fps
    minimum_frames = int(round(spec.minimum_high_low_seconds * reference.source_fps))
    if not np.isclose(minimum_frames / reference.source_fps, spec.minimum_high_low_seconds):
        raise ValueError("minimum duration must map to whole native frames")
    rows: list[dict[str, object]] = []
    for team_key, scores in sorted(scores_by_team.items()):
        timeline = _one_second_changes(scores, reference.source_fps)
        timeline["reference_percentile"] = reference.team_percentile(
            timeline["mean_trailing_relative_path_m"].to_numpy(float)
        )
        before_mask = np.isfinite(timeline["before_score_m"])
        timeline["before_reference_percentile"] = np.nan
        timeline.loc[before_mask, "before_reference_percentile"] = reference.team_percentile(
            timeline.loc[before_mask, "before_score_m"].to_numpy(float)
        )
        definitions = (
            ("high", timeline["mean_trailing_relative_path_m"] >= reference.high_threshold_m),
            ("low", timeline["mean_trailing_relative_path_m"] <= reference.low_threshold_m),
            ("rapid_increase", timeline["one_second_change_m"] >= reference.rapid_threshold_m),
        )
        runs = {str(run["match_id"]) + f"::p{int(run['period'])}::run{int(run['run_index'])}": run
                for run in scores.metadata.get("stable_runs", ())}
        for moment_type, mask in definitions:
            for cluster in _clusters(timeline.loc[mask], cadence):
                if moment_type in {"high", "low"} and len(cluster) < minimum_frames:
                    continue
                if moment_type == "high":
                    peak = cluster.sort_values(
                        ["mean_trailing_relative_path_m", "time_match_s"],
                        ascending=[False, True], kind="mergesort"
                    ).iloc[0]
                elif moment_type == "low":
                    peak = cluster.sort_values(
                        ["mean_trailing_relative_path_m", "time_match_s"],
                        ascending=[True, True], kind="mergesort"
                    ).iloc[0]
                else:
                    peak = cluster.sort_values(
                        ["one_second_change_m", "time_match_s"],
                        ascending=[False, True], kind="mergesort"
                    ).iloc[0]
                run = runs[str(peak.run_id)]
                render_eligible = (
                    float(peak.time_match_s) - float(run["start_time_s"])
                    >= spec.render_context_seconds
                    and float(run["end_time_s"]) - float(peak.time_match_s)
                    >= spec.render_context_seconds
                )
                rows.append(
                    {
                        "moment_type": moment_type,
                        "match_id": str(peak.match_id),
                        "period": int(peak.period),
                        "team_key": team_key,
                        "run_id": str(peak.run_id),
                        "start_time_s": float(cluster.time_match_s.iloc[0]),
                        "end_time_s": float(cluster.time_match_s.iloc[-1]),
                        "peak_time_s": float(peak.time_match_s),
                        "duration_s": float(len(cluster) / reference.source_fps),
                        "team_score_m": float(peak.mean_trailing_relative_path_m),
                        "reference_percentile": float(peak.reference_percentile),
                        "before_score_m": (
                            np.nan if not np.isfinite(peak.before_score_m) else float(peak.before_score_m)
                        ),
                        "one_second_change_m": (
                            np.nan if not np.isfinite(peak.one_second_change_m)
                            else float(peak.one_second_change_m)
                        ),
                        "before_reference_percentile": (
                            np.nan if not np.isfinite(peak.before_reference_percentile)
                            else float(peak.before_reference_percentile)
                        ),
                        "leading_player_scores_m": _leading_scores(
                            scores,
                            match_id=str(peak.match_id),
                            period=int(peak.period),
                            team_key=team_key,
                            frame_id_provider=peak.frame_id_provider,
                            count=spec.leading_players,
                        ),
                        "render_eligible": bool(render_eligible),
                        "selected_for_case_study": False,
                        "category_memberships": moment_type,
                    }
                )
    audit = pd.DataFrame(rows, columns=REFERENCE_MOMENT_COLUMNS)
    if audit.empty:
        return audit, audit.copy()
    selected_indices: list[int] = []
    for moment_type in ("high", "low", "rapid_increase"):
        q = audit.loc[
            audit["moment_type"].eq(moment_type) & audit["render_eligible"]
        ].copy()
        order = "one_second_change_m" if moment_type == "rapid_increase" else "team_score_m"
        q = q.sort_values(
            [order, "match_id", "team_key", "period", "peak_time_s"],
            ascending=[moment_type == "low", True, True, True, True],
            kind="mergesort",
        ).head(spec.selection_per_category)
        selected_indices.extend(q.index.tolist())
    audit.loc[selected_indices, "selected_for_case_study"] = True
    selected = audit.loc[selected_indices].copy()
    for index, row in selected.iterrows():
        memberships = selected.loc[
            selected["match_id"].eq(row.match_id)
            & selected["team_key"].eq(row.team_key)
            & selected["period"].eq(row.period)
            & (selected["start_time_s"] <= row.end_time_s)
            & (selected["end_time_s"] >= row.start_time_s),
            "moment_type",
        ].drop_duplicates().sort_values().tolist()
        selected.at[index, "category_memberships"] = "|".join(memberships)
        audit.at[index, "category_memberships"] = "|".join(memberships)
    selected = selected.sort_values(
        ["moment_type", "match_id", "team_key", "period", "peak_time_s"],
        kind="mergesort",
    ).reset_index(drop=True)
    return audit.reset_index(drop=True), selected


def _distribution_rows(
    scores_by_team: Mapping[str, DefensiveReorganizationScores],
    moments: pd.DataFrame,
    reference: PooledScoreReference,
) -> pd.DataFrame:
    rows = []
    for team_key, scores in sorted(scores_by_team.items()):
        team = _supported_team_with_runs(scores)
        values = team["mean_trailing_relative_path_m"].to_numpy(float)
        percentiles = reference.team_percentile(values)
        row: dict[str, object] = {
            "match_id": str(team.match_id.iloc[0]),
            "defending_team_key": team_key,
            "stable_runs": int(team.run_id.nunique()),
            "supported_frames": int(len(team)),
            "supported_duration_s": float(len(team) / reference.source_fps),
            "mean_m": float(values.mean()),
            "reference_percentile_mean": float(percentiles.mean()),
            "reference_percentile_min": float(percentiles.min()),
            "reference_percentile_max": float(percentiles.max()),
        }
        for label, quantile in (("median_m", .5), ("p75_m", .75), ("p90_m", .9),
                                ("p95_m", .95), ("p99_m", .99), ("max_m", 1.0)):
            row[label] = float(np.quantile(values, quantile, method="linear"))
        for kind in ("high", "low", "rapid_increase"):
            episodes = moments.loc[
                moments["team_key"].eq(team_key) & moments["moment_type"].eq(kind)
            ]
            row[f"{kind}_episode_count"] = int(len(episodes))
            row[f"{kind}_episode_duration_s"] = float(episodes.duration_s.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def analyze_match_with_reference(
    tracking: pd.DataFrame,
    *,
    defending_team_keys: Iterable[str],
    reference: PooledScoreReference,
    smoothing_frames: int,
    window_seconds: float = 2.0,
    excluded_player_keys: Mapping[str, Iterable[str]] | None = None,
    moment_spec: ReferenceMomentSpec = ReferenceMomentSpec(),
) -> ReferenceMatchAnalysis:
    """Score one normalized match and apply the frozen pooled-reference rules."""
    original = tracking.copy(deep=True)
    teams = tuple(dict.fromkeys(str(team) for team in defending_team_keys))
    if not teams:
        raise ValueError("at least one defending team is required")
    excluded = excluded_player_keys or {}
    scores_by_team = {
        team: score_stable_runs(
                tracking,
                defending_team_key=team,
                source_fps=reference.source_fps,
                smoothing_frames=smoothing_frames,
                window_seconds=window_seconds,
                excluded_player_keys=excluded.get(team, ()),
            )
        for team in teams
    }
    reference_timelines = {
        team: _reference_timelines(scores, reference)
        for team, scores in scores_by_team.items()
    }
    pd.testing.assert_frame_equal(tracking, original)
    audit, selected = find_reorganization_windows(scores_by_team, reference, moment_spec)
    distributions = _distribution_rows(scores_by_team, audit, reference)
    return ReferenceMatchAnalysis(
        scores_by_team,
        {team: tables[0] for team, tables in reference_timelines.items()},
        {team: tables[1] for team, tables in reference_timelines.items()},
        audit,
        selected,
        distributions,
        {
            "reference_context_only": True,
            "raw_units": "metres",
            "high_threshold_m": reference.high_threshold_m,
            "low_threshold_m": reference.low_threshold_m,
            "rapid_one_second_threshold_m": reference.rapid_threshold_m,
            "source_fps": reference.source_fps,
            "reference_metadata": dict(reference.metadata),
        },
    )


def export_application_tables(
    analysis: ReferenceMatchAnalysis,
    output_dir: str | Path,
    *,
    formats: Iterable[str] = ("csv",),
) -> dict[str, Path]:
    """Write detailed analyst tables to a caller-controlled local directory."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    requested = tuple(dict.fromkeys(str(value).lower() for value in formats))
    if not requested or not set(requested) <= {"csv", "parquet"}:
        raise ValueError("formats must be a nonempty subset of csv and parquet")
    tables: dict[str, pd.DataFrame] = {
        "moments": analysis.moments,
        "selected_moments": analysis.selected_moments,
        "distributions": analysis.distributions,
    }
    for team, scores in analysis.scores_by_team.items():
        stem = team.replace(":", "_")
        tables[f"{stem}_player_scores"] = analysis.player_timelines[team]
        tables[f"{stem}_team_scores"] = analysis.team_timelines[team]
    written: dict[str, Path] = {}
    for name, frame in tables.items():
        for suffix in requested:
            path = destination / f"{name}.{suffix}"
            if suffix == "csv":
                frame.to_csv(path, index=False, lineterminator="\n")
            else:
                try:
                    frame.to_parquet(path, index=False)
                except ImportError:
                    import polars as pl

                    pl.from_pandas(frame).write_parquet(path)
            written[f"{name}_{suffix}"] = path
    return written


def classify_shot_on_target(event_detail: object) -> bool:
    """Apply the frozen Metrica subtype rule without inferring event semantics."""
    detail = "" if pd.isna(event_detail) else str(event_detail).upper()
    if "BLOCK" in detail or "OFF TARGET" in detail:
        return False
    return any(token in detail for token in ("GOAL", "ON TARGET", "SAVED"))


def normalize_case_study_events(events: pd.DataFrame) -> pd.DataFrame:
    """Validate normalized Metrica shots and add the frozen on-target flag."""
    required = {
        "event_id", "match_id", "period", "event_time_s", "event_type",
        "event_detail", "team_key",
    }
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"missing event columns: {sorted(missing)}")
    q = events.copy(deep=True)
    q["event_type"] = q["event_type"].astype(str).str.upper()
    if not q["event_type"].isin(["SHOT", "GOAL"]).all():
        raise ValueError("case-study events must contain only shots and goals")
    if not np.isfinite(q["event_time_s"].to_numpy(float)).all():
        raise ValueError("event times must be finite")
    if q["event_id"].astype(str).duplicated().any():
        raise ValueError("event IDs must be unique")
    q["shot_on_target"] = q["event_detail"].map(classify_shot_on_target)
    goal_mask = q["event_type"].eq("GOAL")
    if not q.loc[goal_mask, "shot_on_target"].all():
        raise RuntimeError("a goal did not satisfy the frozen shot-on-target subtype rule")
    return q.sort_values(
        ["match_id", "period", "event_time_s", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def _complete_preceding_window(
    run: pd.DataFrame,
    *,
    current_time_s: float,
    seconds: float,
    source_fps: float,
) -> pd.DataFrame | None:
    increments = int(round(seconds * source_fps))
    if not np.isclose(increments / source_fps, seconds, atol=1e-12, rtol=0):
        raise ValueError("event lookback must map to whole native frames")
    q = run.loc[run["time_match_s"].between(current_time_s - seconds, current_time_s)]
    q = q.sort_values(["time_match_s", "frame_id_provider"], kind="mergesort")
    if len(q) != increments + 1:
        return None
    times = q["time_match_s"].to_numpy(float)
    if (
        not np.isclose(times[0], current_time_s - seconds, atol=1e-7, rtol=0)
        or not np.isclose(times[-1], current_time_s, atol=1e-7, rtol=0)
        or not np.allclose(np.diff(times), 1.0 / source_fps, atol=1e-7, rtol=0)
    ):
        return None
    return q


def align_events_to_reference(
    events: pd.DataFrame,
    analysis: ReferenceMatchAnalysis,
    reference: PooledScoreReference,
    *,
    defending_team_by_attacking_team: Mapping[str, str],
    lookbacks_seconds: Iterable[float] = (2.0, 5.0, 10.0),
    change_seconds: Iterable[float] = (1.0, 2.0),
    half_frame_tolerance_s: float | None = None,
    leading_players: int = 3,
) -> pd.DataFrame:
    """Align public events to exact supported frames and summarize prior context."""
    q = normalize_case_study_events(events)
    lookbacks = tuple(float(value) for value in lookbacks_seconds)
    changes = tuple(float(value) for value in change_seconds)
    if lookbacks != (2.0, 5.0, 10.0) or changes != (1.0, 2.0):
        raise ValueError("case-study event windows differ from the frozen configuration")
    tolerance = (
        .5 / reference.source_fps + 1e-7
        if half_frame_tolerance_s is None
        else float(half_frame_tolerance_s)
    )
    expected = .5 / reference.source_fps + 1e-7
    if not np.isclose(tolerance, expected, atol=1e-12, rtol=0):
        raise ValueError("event tolerance differs from the frozen half-frame rule")
    rows: list[dict[str, object]] = []
    for event in q.itertuples(index=False):
        attacking = str(event.team_key)
        if attacking not in defending_team_by_attacking_team:
            raise ValueError(f"no defending-team mapping for {attacking}")
        defending = str(defending_team_by_attacking_team[attacking])
        if defending not in analysis.scores_by_team:
            raise ValueError(f"no scores for defending team {defending}")
        scores = analysis.scores_by_team[defending]
        timeline = _supported_team_with_runs(scores)
        timeline = timeline.loc[
            timeline["match_id"].astype(str).eq(str(event.match_id))
            & timeline["period"].eq(int(event.period))
        ].copy()
        base: dict[str, object] = {
            "event_id": str(event.event_id),
            "match_id": str(event.match_id),
            "period": int(event.period),
            "event_time_s": float(event.event_time_s),
            "event_type": str(event.event_type),
            "event_detail": str(event.event_detail),
            "attacking_team_key": attacking,
            "defending_team_key": defending,
            "shot_on_target": bool(event.shot_on_target),
            "alignment_status": "unmatched",
            "matched_time_s": np.nan,
            "alignment_error_s": np.nan,
            "score_at_event_m": np.nan,
            "reference_percentile_at_event": np.nan,
            "change_1s_m": np.nan,
            "change_2s_m": np.nan,
            "leading_player_scores_m": "[]",
        }
        for seconds in lookbacks:
            label = f"previous_{seconds:g}s"
            base[f"{label}_mean_m"] = np.nan
            base[f"{label}_max_m"] = np.nan
            base[f"{label}_max_reference_percentile"] = np.nan
        if timeline.empty:
            rows.append(base)
            continue
        timeline["distance"] = np.abs(
            timeline["time_match_s"].to_numpy(float) - float(event.event_time_s)
        )
        nearest = timeline.sort_values(
            ["distance", "time_match_s", "frame_id_provider"], kind="mergesort"
        ).iloc[0]
        if float(nearest.distance) > tolerance:
            rows.append(base)
            continue
        run = timeline.loc[timeline["run_id"].eq(nearest.run_id)].drop(columns="distance")
        current_time = float(nearest.time_match_s)
        current_score = float(nearest.mean_trailing_relative_path_m)
        base.update(
            alignment_status="matched",
            matched_time_s=current_time,
            alignment_error_s=float(current_time - float(event.event_time_s)),
            score_at_event_m=current_score,
            reference_percentile_at_event=float(reference.team_percentile(current_score)),
            leading_player_scores_m=_leading_scores(
                scores,
                match_id=str(event.match_id),
                period=int(event.period),
                team_key=defending,
                frame_id_provider=nearest.frame_id_provider,
                count=leading_players,
            ),
        )
        for seconds in lookbacks:
            label = f"previous_{seconds:g}s"
            window = _complete_preceding_window(
                run,
                current_time_s=current_time,
                seconds=seconds,
                source_fps=reference.source_fps,
            )
            if window is None:
                continue
            values = window["mean_trailing_relative_path_m"].to_numpy(float)
            base[f"{label}_mean_m"] = float(values.mean())
            base[f"{label}_max_m"] = float(values.max())
            base[f"{label}_max_reference_percentile"] = float(
                reference.team_percentile(values).max()
            )
        for seconds in changes:
            window = _complete_preceding_window(
                run,
                current_time_s=current_time,
                seconds=seconds,
                source_fps=reference.source_fps,
            )
            if window is not None:
                base[f"change_{seconds:g}s_m"] = float(
                    current_score - float(window.mean_trailing_relative_path_m.iloc[0])
                )
        rows.append(base)
    return pd.DataFrame(rows, columns=EVENT_CONTEXT_COLUMNS)


def summarize_event_context(events: pd.DataFrame) -> pd.DataFrame:
    """Return compact descriptive counts without population-level inference."""
    if tuple(events.columns) != EVENT_CONTEXT_COLUMNS:
        raise ValueError("unexpected event-context schema")
    rows = []
    definitions = (
        ("all_shots", pd.Series(True, index=events.index)),
        ("goals", events["event_type"].eq("GOAL")),
        ("shots_on_target", events["shot_on_target"].astype(bool)),
    )
    for label, mask in definitions:
        q = events.loc[mask]
        matched = q.loc[q["alignment_status"].eq("matched")]
        rows.append(
            {
                "event_group": label,
                "event_count": int(len(q)),
                "matched_count": int(len(matched)),
                "mean_score_at_event_m": (
                    np.nan if matched.empty else float(matched["score_at_event_m"].mean())
                ),
                "median_reference_percentile_at_event": (
                    np.nan
                    if matched.empty
                    else float(matched["reference_percentile_at_event"].median())
                ),
            }
        )
    return pd.DataFrame(rows)


def render_reorganization_window(
    tracking: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    moment: pd.Series | Mapping[str, object],
    output_dir: str | Path,
    *,
    stem: str,
    context_seconds: float = 5.0,
    render_gif: bool = False,
    frame_step: int = 2,
    playback_fps: float = 12.5,
    score_vmax_m: float = DEFAULT_SCORE_VMAX_M,
) -> dict[str, Path]:
    """Render one deterministic supported interval around a selected moment."""
    row = dict(moment)
    required = {"match_id", "period", "team_key", "peak_time_s"}
    missing = required - set(row)
    if missing:
        raise ValueError(f"moment is missing fields: {sorted(missing)}")
    if not np.isfinite(context_seconds) or context_seconds <= 0:
        raise ValueError("context_seconds must be finite and positive")
    match_id = str(row["match_id"])
    period = int(row["period"])
    defending = str(row["team_key"])
    teams = sorted(
        tracking.loc[tracking["entity_type"].eq("player"), "team_key"]
        .dropna().astype(str).unique().tolist()
    )
    opponents = [team for team in teams if team != defending]
    if len(opponents) != 1:
        raise ValueError("rendering requires exactly two player teams")
    attacking = opponents[0]
    peak = float(row["peak_time_s"])
    start, end = peak - context_seconds, peak + context_seconds
    at_peak = scores.player_scores.loc[
        scores.player_scores["period"].eq(period)
        & np.isclose(scores.player_scores["time_match_s"], peak, atol=1e-7, rtol=0)
        & scores.player_scores["support_status"].eq(SUPPORTED)
    ]
    defender_keys = set(at_peak["player_key"].astype(str))
    if len(defender_keys) != 10:
        raise RuntimeError("selected peak lacks exactly ten supported defenders")
    clip = tracking.loc[
        tracking["match_id"].astype(str).eq(match_id)
        & tracking["period"].eq(period)
        & tracking["time_match_s"].between(start, end)
        & ~(
            tracking["team_key"].eq(defending)
            & ~tracking["player_key"].astype(str).isin(defender_keys)
        )
    ].copy()
    frames = clip[["frame_id_provider", "time_match_s"]].drop_duplicates()
    expected = int(round(2 * context_seconds * float(scores.metadata["source_fps"]))) + 1
    if len(frames) != expected:
        raise RuntimeError("selected window lacks complete native rendering support")
    focal_candidates = []
    for key, group in clip.loc[
        clip["entity_type"].eq("player") & clip["team_key"].eq(attacking)
    ].groupby("player_key", sort=True):
        valid = group["coordinate_valid"].astype(bool) & np.isfinite(
            group[["x_m", "y_m"]]
        ).all(axis=1)
        if len(group) == expected and valid.all():
            focal_candidates.append(str(key))
    if not focal_candidates:
        raise RuntimeError("selected window lacks a complete neutral attacking reference")
    clip_spec = TrackingClipSpec(
        match_id=match_id,
        period=period,
        anchor_time_s=peak,
        start_time_s=start,
        end_time_s=end,
        focal_player_key=focal_candidates[0],
        attacking_team_key=attacking,
        defending_team_key=defending,
        defender_ranks=None,
    )
    clip_scores = DefensiveReorganizationScores(
        scores.player_scores.loc[
            scores.player_scores["period"].eq(period)
            & scores.player_scores["time_match_s"].between(start, end)
            & scores.player_scores["player_key"].astype(str).isin(defender_keys)
        ].reset_index(drop=True),
        scores.team_scores.loc[
            scores.team_scores["period"].eq(period)
            & scores.team_scores["time_match_s"].between(start, end)
        ].reset_index(drop=True),
        dict(scores.metadata),
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    png = destination / f"{stem}_diagnostic.png"
    import matplotlib.pyplot as plt
    paths: dict[str, Path] = {"diagnostic_png": png}
    if render_gif:
        rendered = render_selected_passage(
            clip,
            clip_scores,
            clip_spec,
            destination,
            stem=stem,
            selected_time_s=peak,
            frame_step=frame_step,
            playback_fps=playback_fps,
            score_vmax_m=score_vmax_m,
            show_focal_highlight=False,
        )
        paths["gif"] = Path(rendered["gif"])
    # Draw last so the committed static diagnostic always retains the explicit
    # case-study category, raw team score, and reference context.
    figure = plot_defensive_reorganization_diagnostic(
        clip,
        clip_scores,
        clip_spec,
        selected_time_s=peak,
        score_vmax_m=score_vmax_m,
        show_focal_highlight=False,
        technical=True,
    )
    if figure.axes:
        figure.axes[0].set_xlabel("Time relative to selected moment (s)")
    category = str(row.get("category_memberships", row.get("moment_type", "selected")))
    percentile = row.get("reference_percentile", np.nan)
    figure.suptitle(
        f"{category.replace('|', ' + ')} · raw team mean {float(row.get('team_score_m', np.nan)):.2f} m"
        + (
            ""
            if not np.isfinite(float(percentile))
            else f" · reference {format_reference_percentile(float(percentile))}"
        ),
        fontsize=10,
    )
    figure.savefig(png, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return paths
