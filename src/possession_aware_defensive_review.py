"""Possession-context gating for analyst-facing defensive review.

The raw relational-reorganization score is not changed here.  This module adds
only a conservative, event-derived context layer for Metrica review workflows.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_match_review import (
    REFERENCE_MOMENT_COLUMNS,
    PooledScoreReference,
    ReferenceMomentSpec,
    _clusters,
    _leading_scores,
    _one_second_changes,
)
from defensive_reorganization_replay import DefensiveReorganizationScores


AMBIGUOUS = "ambiguous"
DEAD_BALL = "dead_ball_or_restart"
IN_POSSESSION = "in_possession"
OUT_OF_POSSESSION = "out_of_possession"

POSSESSION_CONTEXT_COLUMNS = (
    "match_id", "period", "frame_id_provider", "time_match_s", "team_key",
    "possession_team_key", "possession_state", "state_start_time_s",
    "continuous_state_seconds", "possession_state_run_id",
    "nearest_possession_change_offset_s", "restart_event",
    "defensive_review_eligible",
)

CONTEXT_MOMENT_COLUMNS = REFERENCE_MOMENT_COLUMNS + (
    "possession_state", "possession_team_key",
    "continuous_out_of_possession_s", "defensive_review_eligible",
    "nearest_possession_change_offset_s", "context_classification",
)


@dataclass(frozen=True)
class DefensiveReviewEligibilitySpec:
    continuous_out_of_possession_seconds: float = 2.0
    transition_radius_seconds: float = 2.0

    def __post_init__(self) -> None:
        values = (self.continuous_out_of_possession_seconds, self.transition_radius_seconds)
        if not np.isfinite(values).all() or min(values) <= 0:
            raise ValueError("possession-context durations must be finite and positive")


@dataclass(frozen=True)
class PossessionAwareReviewResult:
    possession_timelines: Mapping[str, pd.DataFrame]
    moments: pd.DataFrame
    selected_moments: pd.DataFrame
    transition_moments: pd.DataFrame
    historical_selection_audit: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "possession_timelines",
            MappingProxyType({key: value.copy(deep=True) for key, value in self.possession_timelines.items()}),
        )
        for name in ("moments", "selected_moments", "transition_moments", "historical_selection_audit"):
            object.__setattr__(self, name, getattr(self, name).copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _whole_frame(values: pd.Series, label: str) -> np.ndarray:
    parsed = pd.to_numeric(values, errors="raise").to_numpy(float)
    if not np.isfinite(parsed).all() or not np.equal(parsed, np.floor(parsed)).all():
        raise ValueError(f"{label} must contain finite integer provider frames")
    return parsed.astype(np.int64)


def _normalize_native_frames(native_frames: pd.DataFrame, source_fps: float) -> pd.DataFrame:
    required = {"match_id", "period", "frame_id_provider", "time_match_s"}
    missing = required - set(native_frames.columns)
    if missing:
        raise ValueError(f"missing native-frame columns: {sorted(missing)}")
    frames = native_frames.loc[:, sorted(required)].copy(deep=True)
    frames["frame_int"] = _whole_frame(frames["frame_id_provider"], "frame_id_provider")
    frames["period"] = _whole_frame(frames["period"], "period")
    frames["time_match_s"] = pd.to_numeric(frames["time_match_s"], errors="raise")
    if not np.isfinite(frames["time_match_s"].to_numpy(float)).all():
        raise ValueError("native-frame times must be finite")
    grouped = frames.groupby(["match_id", "period", "frame_int"], sort=False)["time_match_s"]
    if grouped.nunique().gt(1).any():
        raise ValueError("provider frame maps to changing native times")
    frames = frames.drop_duplicates(["match_id", "period", "frame_int"]).sort_values(
        ["match_id", "period", "frame_int"], kind="mergesort"
    ).reset_index(drop=True)
    cadence = 1.0 / float(source_fps)
    for (_, period), group in frames.groupby(["match_id", "period"], sort=False):
        frame_diff = np.diff(group["frame_int"].to_numpy(np.int64))
        time_diff = np.diff(group["time_match_s"].to_numpy(float))
        adjacent = frame_diff == 1
        if adjacent.any() and not np.allclose(time_diff[adjacent], cadence, atol=1e-7, rtol=0):
            raise ValueError(f"native clock mismatch in period {period}")
    return frames


def _normalize_events(
    events: pd.DataFrame, *, block_required_malformed: bool = True
) -> pd.DataFrame:
    required = {
        "Team", "Type", "Subtype", "Period", "Start Frame", "Start Time [s]",
        "End Frame", "End Time [s]",
    }
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"missing Metrica event columns: {sorted(missing)}")
    q = events.copy(deep=True).reset_index(names="provider_event_index")
    q["Type"] = q["Type"].astype(str).str.strip().str.upper()
    q["Subtype"] = q["Subtype"].fillna("").astype(str).str.strip().str.upper()
    q["Team"] = q["Team"].astype(str).str.strip()
    if not q["Team"].isin(["Home", "Away"]).all():
        raise ValueError("events contain unsupported team identity")
    q["team_key"] = "metrica:" + q["Team"]
    q["Period"] = _whole_frame(q["Period"], "Period")
    q["start_frame"] = _whole_frame(q["Start Frame"], "Start Frame")
    q["start_time"] = pd.to_numeric(q["Start Time [s]"], errors="raise")
    if not np.isfinite(q["start_time"].to_numpy(float)).all():
        raise ValueError("event start times must be finite")
    if np.any(np.diff(q["Period"].to_numpy(np.int64)) < 0):
        raise ValueError("event periods must remain in provider order")
    for period, group in q.groupby("Period", sort=False):
        if (
            np.any(np.diff(group["start_frame"].to_numpy(np.int64)) < 0)
            or np.any(np.diff(group["start_time"].to_numpy(float)) < 0)
        ):
            raise ValueError(f"event starts are disordered in period {period}")

    q["endpoint_required"] = q["Type"].eq("SHOT") & q["Subtype"].str.contains(
        "GOAL|OUT", regex=True
    )
    raw_end_frame = pd.to_numeric(q["End Frame"], errors="coerce").to_numpy(float)
    raw_end_time = pd.to_numeric(q["End Time [s]"], errors="coerce").to_numpy(float)
    end_frame_finite = np.isfinite(raw_end_frame)
    end_frame_whole = end_frame_finite & np.equal(raw_end_frame, np.floor(raw_end_frame))
    end_time_finite = np.isfinite(raw_end_time)
    end_frame_ordered = end_frame_whole & (raw_end_frame >= q["start_frame"].to_numpy(float))
    end_time_ordered = end_time_finite & (raw_end_time >= q["start_time"].to_numpy(float))
    malformed_end = ~(end_frame_ordered & end_time_ordered)
    endpoint_required = q["endpoint_required"].to_numpy(bool)
    endpoint_qc = {
        "total_event_count": int(len(q)),
        "endpoint_required_count": int(endpoint_required.sum()),
        "malformed_unused_end_count": int((malformed_end & ~endpoint_required).sum()),
        "malformed_required_end_count": int((malformed_end & endpoint_required).sum()),
        "tolerated_unused_end_count": int((malformed_end & ~endpoint_required).sum()),
        "blocked_required_end_count": int((malformed_end & endpoint_required).sum()),
    }
    if block_required_malformed and endpoint_qc["blocked_required_end_count"]:
        raise ValueError("required Metrica event endpoint is malformed")
    q["end_frame"] = np.where(end_frame_whole, raw_end_frame, np.nan)
    q["end_time"] = np.where(end_time_finite, raw_end_time, np.nan)
    q["end_metadata_malformed"] = malformed_end
    establishing = q["Type"].isin({"PASS", "RECOVERY", "SET PIECE", "SHOT"})
    conflicts = q.loc[establishing].groupby(["Period", "start_frame"])["team_key"].nunique()
    if conflicts.gt(1).any():
        raise ValueError("conflicting possession teams share one provider frame")
    normalized = q.sort_values(
        ["Period", "start_frame", "start_time", "provider_event_index"], kind="mergesort"
    ).reset_index(drop=True)
    normalized.attrs["event_endpoint_qc"] = endpoint_qc
    return normalized


def metrica_event_endpoint_qc(events: pd.DataFrame) -> Mapping[str, int]:
    """Return aggregate endpoint QC under the frozen event-type-specific rule."""
    normalized = _normalize_events(events, block_required_malformed=False)
    return MappingProxyType(dict(normalized.attrs["event_endpoint_qc"]))


def build_metrica_possession_context(
    events: pd.DataFrame,
    native_frames: pd.DataFrame,
    *,
    match_id: str,
    team_keys: tuple[str, str] = ("metrica:Home", "metrica:Away"),
    source_fps: float = 25.0,
    spec: DefensiveReviewEligibilitySpec = DefensiveReviewEligibilitySpec(),
) -> pd.DataFrame:
    """Build conservative evaluated-team possession states on native frames."""
    if set(team_keys) != {"metrica:Home", "metrica:Away"} or len(team_keys) != 2:
        raise ValueError("Metrica context requires exactly Home and Away team keys")
    if not np.isfinite(source_fps) or source_fps <= 0:
        raise ValueError("source_fps must be finite and positive")
    buffer_frames = int(round(spec.continuous_out_of_possession_seconds * source_fps))
    if not np.isclose(buffer_frames / source_fps, spec.continuous_out_of_possession_seconds):
        raise ValueError("eligibility buffer must map to whole native increments")
    frames = _normalize_native_frames(native_frames, source_fps)
    if set(frames["match_id"].astype(str)) != {str(match_id)}:
        raise ValueError("native frames do not match the requested match")
    q = _normalize_events(events)
    endpoint_qc = dict(q.attrs["event_endpoint_qc"])
    if not set(q["Period"]).issubset(set(frames["period"])):
        raise ValueError("event period is absent from native frames")

    establishing_types = {"PASS", "RECOVERY", "SET PIECE", "SHOT"}
    absolute_rows: list[dict[str, object]] = []
    transition_times: dict[int, list[float]] = {}
    for period, period_frames in frames.groupby("period", sort=True):
        period_events = q.loc[q["Period"].eq(period)].copy()
        frame_ids = set(period_frames["frame_int"].tolist())
        native_time_by_frame = period_frames.set_index("frame_int")["time_match_s"]
        missing_start = set(period_events["start_frame"]) - frame_ids
        if missing_start:
            raise ValueError("event start frame cannot be reconciled to native tracking")
        event_start_time = period_events["start_frame"].map(native_time_by_frame).to_numpy(float)
        if not np.allclose(
            event_start_time,
            period_events["start_time"].to_numpy(float),
            atol=1e-7,
            rtol=0,
        ):
            raise ValueError("event start time cannot be reconciled to native tracking")
        required_endpoints = period_events.loc[period_events["endpoint_required"]]
        required_end_frames = required_endpoints["end_frame"].astype(np.int64)
        missing_end = set(required_end_frames) - frame_ids
        if missing_end:
            raise ValueError("required event end frame cannot be reconciled to native tracking")
        required_end_time = required_end_frames.map(native_time_by_frame).to_numpy(float)
        if not np.allclose(
            required_end_time,
            required_endpoints["end_time"].to_numpy(float),
            atol=1e-7,
            rtol=0,
        ):
            raise ValueError("required event end time cannot be reconciled to native tracking")
        starts = {int(key): group for key, group in period_events.groupby("start_frame", sort=False)}
        end_dead = period_events.loc[
            period_events["Type"].eq("SHOT")
            & period_events["Subtype"].str.contains("GOAL|OUT", regex=True)
        ].groupby("end_frame", sort=False)
        end_dead_frames = {int(key) for key, _ in end_dead}
        phase = AMBIGUOUS
        owner: str | None = None
        pending_owner: str | None = None
        state_start_time = float(period_frames["time_match_s"].iloc[0])
        state_run = 0
        last_evidence_owner: str | None = None
        changes: list[float] = []
        for frame in period_frames.itertuples(index=False):
            frame_id = int(frame.frame_int)
            time_s = float(frame.time_match_s)
            if pending_owner is not None:
                phase, owner = "active", pending_owner
                pending_owner = None
                state_start_time = time_s
                state_run += 1
            at = starts.get(frame_id, pd.DataFrame())
            types = set(at["Type"]) if not at.empty else set()
            subtypes = set(at["Subtype"]) if not at.empty else set()
            establishing = at.loc[at["Type"].isin(establishing_types)] if not at.empty else at
            establishing_owners = tuple(sorted(establishing["team_key"].unique())) if not at.empty else ()
            if len(establishing_owners) > 1:
                raise ValueError("conflicting possession evidence at a native frame")
            evidence_owner = establishing_owners[0] if establishing_owners else None
            restart = "SET PIECE" in types
            starts_dead = bool(
                types.intersection({"BALL OUT", "FAULT RECEIVED", "CARD"})
                or any("FORCED-END HALF" in value for value in subtypes)
                or frame_id in end_dead_frames
            )
            if starts_dead:
                if phase != "dead" or owner is not None:
                    state_run += 1
                phase, owner, pending_owner = "dead", None, None
                state_start_time = time_s
            if restart:
                if evidence_owner is None:
                    raise ValueError("restart lacks one possession team")
                if phase != "dead" or owner is not None:
                    state_run += 1
                phase, owner, pending_owner = "dead", None, evidence_owner
                state_start_time = time_s
                last_evidence_owner = evidence_owner
            elif evidence_owner is not None and not starts_dead:
                resolving_dead = phase == "dead"
                evidence_type = str(establishing["Type"].iloc[0])
                changed = last_evidence_owner is not None and evidence_owner != last_evidence_owner
                if resolving_dead:
                    phase, owner, pending_owner = "dead", None, evidence_owner
                    state_start_time = time_s
                    restart = True
                else:
                    if phase != "active" or owner != evidence_owner:
                        state_run += 1
                        state_start_time = time_s
                    phase, owner = "active", evidence_owner
                    if changed and evidence_type in {"PASS", "RECOVERY", "SHOT"}:
                        changes.append(time_s)
                last_evidence_owner = evidence_owner
            elif "BALL LOST" in types and not starts_dead:
                if phase != AMBIGUOUS or owner is not None:
                    state_run += 1
                phase, owner = AMBIGUOUS, None
                state_start_time = time_s

            absolute_rows.append(
                {
                    "match_id": str(match_id), "period": int(period),
                    "frame_id_provider": frame.frame_id_provider,
                    "frame_int": frame_id, "time_match_s": time_s,
                    "phase": phase, "possession_team_key": owner,
                    "state_start_time_s": state_start_time,
                    "continuous_state_seconds": max(0.0, time_s - state_start_time),
                    "state_run_id": f"p{int(period)}::state{state_run}",
                    "restart_event": bool(restart or phase == "dead"),
                }
            )
        transition_times[int(period)] = sorted(set(changes))

    absolute = pd.DataFrame(absolute_rows)
    expanded: list[pd.DataFrame] = []
    for team in team_keys:
        table = absolute.copy()
        table["team_key"] = team
        table["possession_state"] = np.select(
            [
                table["phase"].eq("dead"),
                table["phase"].eq(AMBIGUOUS),
                table["possession_team_key"].eq(team),
                table["possession_team_key"].notna(),
            ],
            [DEAD_BALL, AMBIGUOUS, IN_POSSESSION, OUT_OF_POSSESSION],
            default=AMBIGUOUS,
        )
        offsets = np.full(len(table), np.nan)
        for period, indexes in table.groupby("period", sort=False).groups.items():
            changes = np.asarray(transition_times.get(int(period), ()), dtype=float)
            if not len(changes):
                continue
            times = table.loc[indexes, "time_match_s"].to_numpy(float)
            insertion = np.searchsorted(changes, times)
            for local, (index, pos) in enumerate(zip(indexes, insertion, strict=True)):
                candidates = []
                if pos > 0:
                    candidates.append(changes[pos - 1])
                if pos < len(changes):
                    candidates.append(changes[pos])
                nearest = min(candidates, key=lambda value: (abs(times[local] - value), value))
                offsets[table.index.get_loc(index)] = times[local] - nearest
        table["nearest_possession_change_offset_s"] = offsets
        table["possession_state_run_id"] = table["state_run_id"]
        table["defensive_review_eligible"] = (
            table["possession_state"].eq(OUT_OF_POSSESSION)
            & table["continuous_state_seconds"].ge(
                spec.continuous_out_of_possession_seconds - 1e-9
            )
        )
        expanded.append(table.loc[:, POSSESSION_CONTEXT_COLUMNS])
    result = pd.concat(expanded, ignore_index=True).sort_values(
        ["match_id", "team_key", "period", "time_match_s", "frame_id_provider"],
        kind="mergesort",
    ).reset_index(drop=True)
    result.attrs["event_endpoint_qc"] = endpoint_qc
    return result


def _context_clusters(candidates: pd.DataFrame, cadence: float, *, transition: bool = False):
    if candidates.empty:
        return []
    q = candidates.sort_values(
        ["match_id", "team_key", "period", "run_id", "time_match_s"], kind="mergesort"
    ).reset_index(drop=True)
    cuts = [0]
    for index in range(1, len(q)):
        previous, current = q.iloc[index - 1], q.iloc[index]
        same = (
            str(current.run_id) == str(previous.run_id)
            and str(current.possession_state_run_id) == str(previous.possession_state_run_id)
            and np.isclose(current.time_match_s - previous.time_match_s, cadence, atol=1e-7, rtol=0)
        )
        if transition:
            same = same and np.isclose(
                current.transition_anchor_time_s, previous.transition_anchor_time_s,
                atol=1e-7, rtol=0,
            )
        if not same:
            cuts.append(index)
    cuts.append(len(q))
    return [q.iloc[start:end].copy() for start, end in zip(cuts[:-1], cuts[1:], strict=True)]


def _moment_row(
    cluster: pd.DataFrame,
    *,
    moment_type: str,
    score_package: DefensiveReorganizationScores,
    runs: Mapping[str, Mapping[str, object]],
    leading_players: int,
    render_context_seconds: float,
) -> dict[str, object]:
    if moment_type == "high":
        peak = cluster.sort_values(["mean_trailing_relative_path_m", "time_match_s"], ascending=[False, True], kind="mergesort").iloc[0]
    elif moment_type == "low":
        peak = cluster.sort_values(["mean_trailing_relative_path_m", "time_match_s"], ascending=[True, True], kind="mergesort").iloc[0]
    else:
        peak = cluster.sort_values(["one_second_change_m", "time_match_s"], ascending=[False, True], kind="mergesort").iloc[0]
    run = runs[str(peak.run_id)]
    render_eligible = (
        float(peak.time_match_s) - float(run["start_time_s"]) >= render_context_seconds
        and float(run["end_time_s"]) - float(peak.time_match_s) >= render_context_seconds
    )
    memberships = moment_type
    if moment_type == "transition_reorganization":
        kinds = []
        if bool(peak.high_qualifies):
            kinds.append("high")
        if bool(peak.rapid_qualifies):
            kinds.append("rapid_increase")
        memberships = "|".join(["transition_reorganization", *kinds])
    return {
        "moment_type": moment_type,
        "match_id": str(peak.match_id), "period": int(peak.period),
        "team_key": str(peak.team_key), "run_id": str(peak.run_id),
        "start_time_s": float(cluster.time_match_s.iloc[0]),
        "end_time_s": float(cluster.time_match_s.iloc[-1]),
        "peak_time_s": float(peak.time_match_s),
        "duration_s": float(len(cluster) / float(score_package.metadata["source_fps"])),
        "team_score_m": float(peak.mean_trailing_relative_path_m),
        "reference_percentile": float(peak.reference_percentile),
        "before_score_m": np.nan if not np.isfinite(peak.before_score_m) else float(peak.before_score_m),
        "one_second_change_m": np.nan if not np.isfinite(peak.one_second_change_m) else float(peak.one_second_change_m),
        "before_reference_percentile": np.nan if not np.isfinite(peak.before_reference_percentile) else float(peak.before_reference_percentile),
        "leading_player_scores_m": _leading_scores(
            score_package, match_id=str(peak.match_id), period=int(peak.period),
            team_key=str(peak.team_key), frame_id_provider=peak.frame_id_provider,
            count=leading_players,
        ),
        "render_eligible": bool(render_eligible), "selected_for_case_study": False,
        "category_memberships": memberships,
        "possession_state": str(peak.possession_state),
        "possession_team_key": peak.possession_team_key,
        "continuous_out_of_possession_s": (
            float(peak.continuous_state_seconds)
            if peak.possession_state == OUT_OF_POSSESSION else np.nan
        ),
        "defensive_review_eligible": bool(peak.defensive_review_eligible),
        "nearest_possession_change_offset_s": (
            np.nan if not np.isfinite(peak.nearest_possession_change_offset_s)
            else float(peak.nearest_possession_change_offset_s)
        ),
        "context_classification": (
            "defensive_review" if bool(peak.defensive_review_eligible)
            else "possession_transition"
        ),
    }


def find_defensive_review_windows(
    scores_by_team: Mapping[str, DefensiveReorganizationScores],
    reference: PooledScoreReference,
    possession_context: pd.DataFrame,
    *,
    moment_spec: ReferenceMomentSpec = ReferenceMomentSpec(),
    eligibility_spec: DefensiveReviewEligibilitySpec = DefensiveReviewEligibilitySpec(),
    historical_selected: pd.DataFrame | None = None,
) -> PossessionAwareReviewResult:
    """Apply frozen thresholds only to possession-eligible defensive frames."""
    if tuple(possession_context.columns) != POSSESSION_CONTEXT_COLUMNS:
        raise ValueError("unexpected possession-context schema")
    cadence = 1.0 / reference.source_fps
    minimum_frames = int(round(moment_spec.minimum_high_low_seconds * reference.source_fps))
    rows: list[dict[str, object]] = []
    transition_rows: list[dict[str, object]] = []
    timelines: dict[str, pd.DataFrame] = {}
    for team_key, scores in sorted(scores_by_team.items()):
        timeline = _one_second_changes(scores, reference.source_fps)
        timeline["reference_percentile"] = reference.team_percentile(timeline["mean_trailing_relative_path_m"].to_numpy(float))
        before = np.isfinite(timeline["before_score_m"])
        timeline["before_reference_percentile"] = np.nan
        timeline.loc[before, "before_reference_percentile"] = reference.team_percentile(timeline.loc[before, "before_score_m"].to_numpy(float))
        context = possession_context.loc[possession_context["team_key"].eq(team_key)]
        keys = ["match_id", "period", "frame_id_provider", "time_match_s", "team_key"]
        timeline = timeline.merge(context, on=keys, how="left", validate="one_to_one")
        if timeline["possession_state"].isna().any():
            raise RuntimeError("supported score frame lacks possession context")
        offset = int(round(reference.source_fps))
        timeline["before_defensive_eligible"] = timeline.groupby("run_id", sort=False)["defensive_review_eligible"].shift(offset, fill_value=False).astype(bool)
        timeline["before_state_run_id"] = timeline.groupby("run_id", sort=False)["possession_state_run_id"].shift(offset)
        timeline["high_qualifies"] = timeline["mean_trailing_relative_path_m"].ge(reference.high_threshold_m)
        timeline["low_qualifies"] = timeline["mean_trailing_relative_path_m"].le(reference.low_threshold_m)
        timeline["rapid_qualifies"] = timeline["one_second_change_m"].ge(reference.rapid_threshold_m)
        timelines[team_key] = timeline.copy()
        runs = {str(run["match_id"]) + f"::p{int(run['period'])}::run{int(run['run_index'])}": run for run in scores.metadata.get("stable_runs", ())}
        definitions = (
            ("high", timeline.high_qualifies & timeline.defensive_review_eligible),
            ("low", timeline.low_qualifies & timeline.defensive_review_eligible),
            (
                "rapid_increase",
                timeline.rapid_qualifies & timeline.defensive_review_eligible
                & timeline.before_defensive_eligible
                & timeline.possession_state_run_id.eq(timeline.before_state_run_id),
            ),
        )
        for kind, mask in definitions:
            for cluster in _context_clusters(timeline.loc[mask], cadence):
                if kind in {"high", "low"} and len(cluster) < minimum_frames:
                    continue
                rows.append(_moment_row(cluster, moment_type=kind, score_package=scores, runs=runs, leading_players=moment_spec.leading_players, render_context_seconds=moment_spec.render_context_seconds))

        near_transition = timeline["nearest_possession_change_offset_s"].abs().le(eligibility_spec.transition_radius_seconds + 1e-9)
        transition_mask = near_transition & (timeline.high_qualifies | timeline.rapid_qualifies)
        transition = timeline.loc[transition_mask].copy()
        transition["transition_anchor_time_s"] = transition["time_match_s"] - transition["nearest_possession_change_offset_s"]
        for cluster in _context_clusters(transition, cadence, transition=True):
            transition_rows.append(_moment_row(cluster, moment_type="transition_reorganization", score_package=scores, runs=runs, leading_players=moment_spec.leading_players, render_context_seconds=moment_spec.render_context_seconds))

    audit = pd.DataFrame(rows, columns=CONTEXT_MOMENT_COLUMNS)
    transitions = pd.DataFrame(transition_rows, columns=CONTEXT_MOMENT_COLUMNS)
    selected_indices: list[int] = []
    if not audit.empty:
        for kind in ("high", "low", "rapid_increase"):
            subset = audit.loc[audit.moment_type.eq(kind) & audit.render_eligible]
            order = "one_second_change_m" if kind == "rapid_increase" else "team_score_m"
            subset = subset.sort_values(
                [order, "match_id", "team_key", "period", "peak_time_s"],
                ascending=[kind == "low", True, True, True, True], kind="mergesort",
            ).head(moment_spec.selection_per_category)
            selected_indices.extend(subset.index.tolist())
        audit.loc[selected_indices, "selected_for_case_study"] = True
    selected = audit.loc[selected_indices].copy() if selected_indices else audit.head(0).copy()
    for index, row in selected.iterrows():
        memberships = selected.loc[
            selected.match_id.eq(row.match_id) & selected.team_key.eq(row.team_key)
            & selected.period.eq(row.period) & selected.start_time_s.le(row.end_time_s)
            & selected.end_time_s.ge(row.start_time_s), "moment_type"
        ].drop_duplicates().sort_values().tolist()
        selected.at[index, "category_memberships"] = "|".join(memberships)
        audit.at[index, "category_memberships"] = "|".join(memberships)
    selected = selected.sort_values(["moment_type", "team_key", "period", "peak_time_s"], kind="mergesort").reset_index(drop=True)

    historical_rows = []
    if historical_selected is not None:
        for row in historical_selected.itertuples(index=False):
            timeline = timelines[str(row.team_key)]
            point = timeline.loc[
                timeline["period"].eq(int(row.period))
                & np.isclose(timeline["time_match_s"], float(row.peak_time_s), atol=1e-7, rtol=0)
            ]
            if len(point) != 1:
                raise RuntimeError("historical selection does not map to one score frame")
            point = point.iloc[0]
            if bool(point.defensive_review_eligible):
                classification = "still_defensively_eligible"
            elif point.possession_state == DEAD_BALL:
                classification = "restart_or_dead_ball"
            elif point.possession_state == IN_POSSESSION:
                classification = "evaluated_team_in_possession"
            elif point.possession_state == AMBIGUOUS:
                classification = "ambiguous"
            else:
                classification = "transition_context"
            historical_rows.append({
                "moment_type": str(row.moment_type), "team_key": str(row.team_key),
                "period": int(row.period), "peak_time_s": float(row.peak_time_s),
                "possession_state": str(point.possession_state),
                "continuous_out_of_possession_s": (
                    float(point.continuous_state_seconds) if point.possession_state == OUT_OF_POSSESSION else np.nan
                ),
                "nearest_possession_change_offset_s": (
                    np.nan if not np.isfinite(point.nearest_possession_change_offset_s) else float(point.nearest_possession_change_offset_s)
                ),
                "classification": classification,
            })
    historical = pd.DataFrame(historical_rows)
    return PossessionAwareReviewResult(
        timelines, audit.reset_index(drop=True), selected, transitions.reset_index(drop=True), historical,
        {
            "raw_measurement": "team_relational_reorganization",
            "source_fps": reference.source_fps,
            "continuous_out_of_possession_seconds": eligibility_spec.continuous_out_of_possession_seconds,
            "transition_radius_seconds": eligibility_spec.transition_radius_seconds,
            "thresholds_unchanged": True,
            "raw_scores_unchanged": True,
        },
    )


def possession_state_summary(context: pd.DataFrame) -> pd.DataFrame:
    """Return aggregate-only state coverage for publication."""
    required = set(POSSESSION_CONTEXT_COLUMNS)
    if set(context.columns) != required:
        raise ValueError("unexpected possession-context schema")
    return (
        context.groupby(["team_key", "period", "possession_state"], sort=True)
        .agg(
            frame_count=("frame_id_provider", "size"),
            eligible_frame_count=("defensive_review_eligible", "sum"),
        )
        .reset_index()
    )
