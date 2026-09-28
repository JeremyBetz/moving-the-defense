"""Rapid-change-first retrieval over possession-aware defensive review results."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_replay import DefensiveReorganizationScores, SUPPORTED
from possession_aware_defensive_review import (
    DEAD_BALL,
    OUT_OF_POSSESSION,
    PossessionAwareReviewResult,
)


@dataclass(frozen=True)
class RapidReviewPrioritySpec:
    restart_adjacency_seconds: float = 5.0
    transition_radius_seconds: float = 2.0
    review_limit: int = 6
    public_limit: int = 3
    localized_top_three_share: float = 0.60
    broad_minimum_at_or_above_team_delta: int = 5
    decrease_review_limit: int = 3
    render_context_seconds: float = 5.0

    def __post_init__(self) -> None:
        finite = (
            self.restart_adjacency_seconds,
            self.transition_radius_seconds,
            self.localized_top_three_share,
            self.render_context_seconds,
        )
        if not np.isfinite(finite).all() or min(finite) < 0:
            raise ValueError("rapid-review numeric settings must be finite and nonnegative")
        if not 0 < self.localized_top_three_share <= 1:
            raise ValueError("localized top-three share must be in (0, 1]")
        if self.review_limit != 6 or self.public_limit != 3 or self.decrease_review_limit != 3:
            raise ValueError("rapid-review limits differ from the frozen protocol")
        if self.broad_minimum_at_or_above_team_delta != 5:
            raise ValueError("broad-unit contributor count differs from the frozen protocol")


@dataclass(frozen=True)
class RapidReviewResult:
    classified_increases: pd.DataFrame
    review_set: pd.DataFrame
    public_examples: pd.DataFrame
    decrease_diagnostics: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        for field in (
            "classified_increases",
            "review_set",
            "public_examples",
            "decrease_diagnostics",
        ):
            object.__setattr__(self, field, getattr(self, field).copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _restart_boundaries(timeline: pd.DataFrame) -> dict[int, np.ndarray]:
    boundaries: dict[int, np.ndarray] = {}
    for period, group in timeline.groupby("period", sort=True):
        q = group.sort_values("time_match_s", kind="mergesort")
        dead = q["possession_state"].eq(DEAD_BALL).to_numpy(bool)
        changed = np.r_[False, dead[1:] != dead[:-1]]
        boundaries[int(period)] = q.loc[changed, "time_match_s"].to_numpy(float)
    return boundaries


def _nearest_offset(time_s: float, candidates: np.ndarray) -> float:
    if candidates.size == 0:
        return np.nan
    offsets = float(time_s) - candidates
    order = np.lexsort((candidates, np.abs(offsets)))
    return float(offsets[order[0]])


def _event_context(
    period: int,
    time_s: float,
    events: pd.DataFrame | None,
) -> tuple[str | None, str | None, float]:
    if events is None or events.empty:
        return None, None, np.nan
    required = {"period", "event_time_s", "event_type", "event_subtype"}
    if not required.issubset(events.columns):
        raise ValueError(f"normalized events lack columns: {sorted(required - set(events.columns))}")
    q = events.loc[events["period"].eq(period)].copy()
    if q.empty:
        return None, None, np.nan
    q["event_time_s"] = pd.to_numeric(q["event_time_s"], errors="raise")
    if not np.isfinite(q["event_time_s"].to_numpy(float)).all():
        raise ValueError("event times must be finite")
    q["offset"] = float(time_s) - q["event_time_s"]
    q = q.sort_values(["offset"], key=lambda s: s.abs(), kind="mergesort")
    closest_abs = abs(float(q.iloc[0]["offset"]))
    q = q.loc[np.isclose(q["offset"].abs(), closest_abs, atol=1e-9, rtol=0)]
    row = q.sort_values(["event_time_s", "event_type", "event_subtype"], kind="mergesort").iloc[0]
    return str(row.event_type), str(row.event_subtype), float(row.offset)


def _player_deltas(
    scores: DefensiveReorganizationScores,
    *,
    match_id: str,
    period: int,
    team_key: str,
    peak_time_s: float,
    change_seconds: float,
    team_delta: float,
    spec: RapidReviewPrioritySpec,
) -> dict[str, object]:
    players = scores.player_scores
    base = (
        players["match_id"].astype(str).eq(match_id)
        & players["period"].eq(period)
        & players["team_key"].astype(str).eq(team_key)
    )
    current = players.loc[base & np.isclose(players["time_match_s"], peak_time_s, atol=1e-7, rtol=0)]
    before = players.loc[
        base
        & np.isclose(
            players["time_match_s"], peak_time_s - change_seconds, atol=1e-7, rtol=0
        )
    ]
    if len(current) != 10 or len(before) != 10:
        raise RuntimeError("rapid contribution window does not contain ten defenders")
    if not current["support_status"].eq(SUPPORTED).all() or not before["support_status"].eq(SUPPORTED).all():
        raise RuntimeError("rapid contribution window is unsupported")
    current_values = current.set_index("player_key")["trailing_relative_path_m"].sort_index()
    before_values = before.set_index("player_key")["trailing_relative_path_m"].sort_index()
    if not current_values.index.equals(before_values.index):
        raise RuntimeError("defender identity changes across the rapid interval")
    delta = current_values.to_numpy(float) - before_values.to_numpy(float)
    if not np.isfinite(delta).all() or not np.isclose(delta.mean(), team_delta, atol=1e-8, rtol=0):
        raise RuntimeError("player changes do not reconcile to the team change")
    positive = np.maximum(delta, 0.0)
    total_positive = float(positive.sum())
    if total_positive <= 0:
        raise RuntimeError("positive rapid episode lacks positive player contributions")
    descending = np.sort(positive)[::-1]
    top_three_share = float(descending[:3].sum() / total_positive)
    at_or_above = int(np.count_nonzero(delta >= team_delta - 1e-12))
    if top_three_share >= spec.localized_top_three_share - 1e-12:
        pattern = "localized"
    elif at_or_above >= spec.broad_minimum_at_or_above_team_delta:
        pattern = "broad_unit"
    else:
        pattern = "mixed"
    return {
        "top_positive_changes_m": tuple(round(float(value), 10) for value in descending[:3]),
        "top_three_positive_share": top_three_share,
        "players_at_or_above_team_delta": at_or_above,
        "positive_contributor_count": int(np.count_nonzero(positive > 0)),
        "contribution_pattern": pattern,
    }


def _render_supported(
    scores: DefensiveReorganizationScores,
    run_id: str,
    peak_time_s: float,
    context_seconds: float,
) -> bool:
    runs = {
        f"{run['match_id']}::p{int(run['period'])}::run{int(run['run_index'])}": run
        for run in scores.metadata.get("stable_runs", ())
    }
    if run_id not in runs:
        raise RuntimeError("rapid episode references an unknown stable run")
    run = runs[run_id]
    return (
        peak_time_s - float(run["start_time_s"]) >= context_seconds
        and float(run["end_time_s"]) - peak_time_s >= context_seconds
    )


def _classify_row(
    row: pd.Series,
    *,
    scores: DefensiveReorganizationScores,
    timeline: pd.DataFrame,
    boundaries: dict[int, np.ndarray],
    events: pd.DataFrame | None,
    spec: RapidReviewPrioritySpec,
) -> dict[str, object]:
    period = int(row.period)
    peak = float(row.peak_time_s)
    point = timeline.loc[
        timeline["period"].eq(period)
        & np.isclose(timeline["time_match_s"], peak, atol=1e-7, rtol=0)
    ]
    if len(point) != 1:
        raise RuntimeError("rapid episode does not map to one possession timeline frame")
    point = point.iloc[0]
    if not np.isclose(
        float(point.one_second_change_m), float(row.one_second_change_m), atol=1e-10, rtol=0
    ):
        raise RuntimeError("rapid episode delta differs from the unchanged score timeline")
    endpoints_eligible = (
        bool(point.defensive_review_eligible)
        and bool(point.before_defensive_eligible)
        and str(point.possession_state_run_id) == str(point.before_state_run_id)
    )
    restart_offset = _nearest_offset(peak, boundaries.get(period, np.array([], dtype=float)))
    transition_offset = float(row.nearest_possession_change_offset_s)
    ambiguous = (
        not bool(row.defensive_review_eligible)
        or not endpoints_eligible
        or str(row.possession_state) != OUT_OF_POSSESSION
        or not np.isfinite(float(row.one_second_change_m))
    )
    restart_adjacent = np.isfinite(restart_offset) and abs(restart_offset) <= spec.restart_adjacency_seconds + 1e-9
    transition = np.isfinite(transition_offset) and abs(transition_offset) <= spec.transition_radius_seconds + 1e-9
    if ambiguous:
        context = "ambiguous_context"
    elif restart_adjacent:
        context = "restart_adjacent"
    elif transition:
        context = "transition"
    else:
        context = "open_play"
    event_type, event_subtype, event_offset = _event_context(period, peak, events)
    contribution = _player_deltas(
        scores,
        match_id=str(row.match_id),
        period=period,
        team_key=str(row.team_key),
        peak_time_s=peak,
        change_seconds=1.0,
        team_delta=float(row.one_second_change_m),
        spec=spec,
    )
    return {
        **row.to_dict(),
        "after_score_m": float(row.team_score_m),
        "after_reference_percentile": float(row.reference_percentile),
        "nearest_restart_boundary_offset_s": restart_offset,
        "nearest_event_type": event_type,
        "nearest_event_subtype": event_subtype,
        "nearest_event_offset_s": event_offset,
        "rapid_context": context,
        **contribution,
    }


def _negative_episodes(
    review: PossessionAwareReviewResult,
    scores_by_team: Mapping[str, DefensiveReorganizationScores],
    events: pd.DataFrame | None,
    spec: RapidReviewPrioritySpec,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for team_key, timeline in sorted(review.possession_timelines.items()):
        q = timeline.sort_values(["period", "run_id", "time_match_s"], kind="mergesort").copy()
        mask = (
            q["one_second_change_m"].lt(0)
            & q["defensive_review_eligible"]
            & q["before_defensive_eligible"]
            & q["possession_state_run_id"].eq(q["before_state_run_id"])
        )
        candidates = q.loc[mask].copy()
        if candidates.empty:
            continue
        cadence = 1.0 / float(review.metadata["source_fps"])
        cuts = (
            candidates["period"].ne(candidates["period"].shift())
            | candidates["run_id"].ne(candidates["run_id"].shift())
            | candidates["possession_state_run_id"].ne(candidates["possession_state_run_id"].shift())
            | ~np.isclose(candidates["time_match_s"].diff(), cadence, atol=1e-7, rtol=0)
        ).cumsum()
        boundaries = _restart_boundaries(q)
        for _, cluster in candidates.groupby(cuts, sort=False):
            peak = cluster.sort_values(
                ["one_second_change_m", "time_match_s"], kind="mergesort"
            ).iloc[0]
            score_package = scores_by_team[team_key]
            if not _render_supported(score_package, str(peak.run_id), float(peak.time_match_s), spec.render_context_seconds):
                continue
            restart_offset = _nearest_offset(float(peak.time_match_s), boundaries.get(int(peak.period), np.array([], dtype=float)))
            if np.isfinite(restart_offset) and abs(restart_offset) <= spec.restart_adjacency_seconds + 1e-9:
                continue
            event_type, event_subtype, event_offset = _event_context(int(peak.period), float(peak.time_match_s), events)
            rows.append({
                "match_id": str(peak.match_id), "team_key": str(team_key),
                "period": int(peak.period), "run_id": str(peak.run_id),
                "peak_time_s": float(peak.time_match_s),
                "before_score_m": float(peak.before_score_m),
                "after_score_m": float(peak.mean_trailing_relative_path_m),
                "one_second_change_m": float(peak.one_second_change_m),
                "before_reference_percentile": float(peak.before_reference_percentile),
                "after_reference_percentile": float(peak.reference_percentile),
                "continuous_out_of_possession_s": float(peak.continuous_state_seconds),
                "rapid_context": (
                    "transition" if abs(float(peak.nearest_possession_change_offset_s)) <= spec.transition_radius_seconds + 1e-9
                    else "open_play"
                ),
                "nearest_restart_boundary_offset_s": restart_offset,
                "nearest_event_type": event_type,
                "nearest_event_subtype": event_subtype,
                "nearest_event_offset_s": event_offset,
            })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        ["one_second_change_m", "period", "peak_time_s", "team_key"],
        kind="mergesort",
    ).head(spec.decrease_review_limit).reset_index(drop=True)


def _select_public(review_set: pd.DataFrame, spec: RapidReviewPrioritySpec) -> pd.DataFrame:
    if review_set.empty:
        return review_set.copy()
    selected = [review_set.index[0]]
    first = review_set.loc[selected[0]]
    for index, row in review_set.iloc[1:].iterrows():
        if row.rapid_context != first.rapid_context or row.contribution_pattern != first.contribution_pattern:
            selected.append(index)
            break
    if len(selected) >= 2 and len(selected) < spec.public_limit:
        contexts = set(review_set.loc[selected, "rapid_context"])
        patterns = set(review_set.loc[selected, "contribution_pattern"])
        for index, row in review_set.iterrows():
            if index in selected:
                continue
            if row.rapid_context not in contexts and row.contribution_pattern not in patterns:
                selected.append(index)
                break
    result = review_set.loc[selected].copy()
    reasons = ["rank_1"]
    if len(result) >= 2:
        reasons.append("first_new_context_or_contribution_pattern")
    if len(result) >= 3:
        reasons.append("first_both_context_and_contribution_pattern_new")
    result["public_selection_reason"] = reasons
    result["public_rank"] = np.arange(1, len(result) + 1)
    return result.reset_index(drop=True)


def find_rapid_reorganization_windows(
    possession_review: PossessionAwareReviewResult,
    scores_by_team: Mapping[str, DefensiveReorganizationScores],
    *,
    events: pd.DataFrame | None = None,
    spec: RapidReviewPrioritySpec = RapidReviewPrioritySpec(),
) -> RapidReviewResult:
    """Prioritize frozen rapid-change episodes without altering raw retrieval."""
    rapid = possession_review.moments.loc[
        possession_review.moments["moment_type"].eq("rapid_increase")
    ].copy()
    classified: list[dict[str, object]] = []
    for row in rapid.itertuples(index=False):
        series = pd.Series(row._asdict())
        team_key = str(series.team_key)
        if team_key not in scores_by_team or team_key not in possession_review.possession_timelines:
            raise ValueError("rapid episode lacks its team score/context package")
        classified.append(_classify_row(
            series,
            scores=scores_by_team[team_key],
            timeline=possession_review.possession_timelines[team_key],
            boundaries=_restart_boundaries(possession_review.possession_timelines[team_key]),
            events=events,
            spec=spec,
        ))
    all_increases = pd.DataFrame(classified)
    if all_increases.empty:
        review_set = all_increases.copy()
    else:
        allowed = (
            all_increases["defensive_review_eligible"].astype(bool)
            & all_increases["render_eligible"].astype(bool)
            & all_increases["rapid_context"].isin({"open_play", "transition"})
        )
        review_set = all_increases.loc[allowed].sort_values(
            ["one_second_change_m", "period", "peak_time_s", "team_key"],
            ascending=[False, True, True, True], kind="mergesort",
        ).head(spec.review_limit).reset_index(drop=True)
        review_set["review_rank"] = np.arange(1, len(review_set) + 1)
    public = _select_public(review_set, spec)
    decreases = _negative_episodes(possession_review, scores_by_team, events, spec)
    return RapidReviewResult(
        all_increases.reset_index(drop=True), review_set, public, decreases,
        {
            "raw_measurement": possession_review.metadata["raw_measurement"],
            "source_fps": possession_review.metadata["source_fps"],
            "rapid_threshold_m": 0.6251746256690309,
            "continuous_out_of_possession_seconds": possession_review.metadata["continuous_out_of_possession_seconds"],
            "restart_adjacency_seconds": spec.restart_adjacency_seconds,
            "transition_radius_seconds": spec.transition_radius_seconds,
            "raw_scores_unchanged": True,
            "high_low_unchanged": True,
        },
    )
