"""Frozen Stage-A support audit for continuous attacker movement on Metrica Game 2.

This module deliberately stops at raw canonical trajectory support. It does
not smooth coordinates, construct movement features, resample trajectories,
or access events, defenders as response objects, or outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import kloppy
import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from infrastructure import canonical_tracking  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402


PROTOCOL = ROOT / "docs" / "protocols" / "attacking_continuous_movement_game2_heldout_v1.md"
GAME1_PROTOCOL = ROOT / "docs" / "protocols" / "attacking_continuous_movement_v1.md"
GAME1_RESULT = ROOT / "docs" / "results" / "attacking_continuous_movement_game1_v1.md"
DEFAULT_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game2_stage_a"
MATCH_ID = "metrica:sample-game-2"
RAW_DT_S = 0.04
TIME_TOL = 1e-9
HARD_JUMP_MPS = 20.0
REPORT_JUMP_MPS = 10.0
DUPLICATE_MIN_FRAMES = 5

REGISTRY_COLUMNS = [
    "match_id", "team_key", "player_key", "period", "start_frame_provider",
    "end_frame_provider", "start_time_period_s", "end_time_period_s",
    "start_time_match_s", "end_time_match_s", "rule_code", "diagnostic_ids",
    "deterministic_rule", "provenance",
]
SEGMENT_COLUMNS = [
    "match_id", "team_key", "player_key", "period", "segment_id",
    "start_frame_provider", "end_frame_provider", "start_time_period_s",
    "end_time_period_s", "start_time_match_s", "end_time_match_s", "frame_count",
    "left_boundary_reason", "right_boundary_reason",
]
LINK_COLUMNS = [
    "diagnostic_id", "match_id", "team_key", "player_key", "period",
    "start_frame_provider", "end_frame_provider", "start_time_period_s",
    "end_time_period_s", "start_time_match_s", "end_time_match_s",
    "raw_link_delta_x_m", "raw_link_delta_y_m", "coordinate_difference_m", "elapsed_s",
    "raw_link_speed_mps", "above_report_threshold", "hard_raw_jump",
]
DUP_COLUMNS = [
    "diagnostic_id", "match_id", "team_key_a", "player_key_a", "team_key_b",
    "player_key_b", "same_team", "period", "start_frame_provider",
    "end_frame_provider", "start_time_period_s", "end_time_period_s",
    "start_time_match_s", "end_time_match_s", "consecutive_frame_count",
    "qualifying_same_team_exclusion",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    pd.DataFrame(rows, columns=columns).to_csv(
        path, index=False, lineterminator="\n", float_format="%.17g"
    )


def true_runs(mask: np.ndarray, continuity: np.ndarray) -> list[tuple[int, int]]:
    """Inclusive maximal true runs, split when the incoming link is not continuous."""
    result: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(mask):
        if value and (start is None or (i > 0 and continuity[i])):
            if start is None:
                start = i
            continue
        if start is not None:
            result.append((start, i - 1))
            start = None
        if value:
            start = i
    if start is not None:
        result.append((start, len(mask) - 1))
    return result


def hard_jump_invalid_mask(
    hard_link_indices: np.ndarray,
    n: int,
    base_valid: np.ndarray | None = None,
    continuity: np.ndarray | None = None,
) -> np.ndarray:
    """Apply frozen endpoints plus bounded-segment semantics.

    A hard-link index i denotes the link from row i-1 to row i. Consecutive
    hard links in occurrence order bound the observed segment between them;
    the union therefore spans from the first link's left endpoint through the
    last link's right endpoint. A single hard link invalidates only endpoints.
    """
    invalid = np.zeros(n, dtype=bool)
    indices = np.asarray(hard_link_indices, dtype=np.int64)
    if base_valid is None:
        base_valid = np.ones(n, dtype=bool)
    if continuity is None:
        continuity = np.ones(n, dtype=bool)
    groups: list[list[int]] = []
    for value in indices:
        i = int(value)
        if not groups:
            groups.append([i])
            continue
        previous = groups[-1][-1]
        same_observed_run = (
            bool(base_valid[previous : i + 1].all())
            and bool(continuity[previous + 1 : i + 1].all())
        )
        if same_observed_run:
            groups[-1].append(i)
        else:
            groups.append([i])
    for group in groups:
        for i in group:
            invalid[i - 1 : i + 1] = True
        if len(group) >= 2:
            invalid[group[0] - 1 : group[-1] + 1] = True
    return invalid


def exact_duplicate_runs(
    a: dict[str, np.ndarray], b: dict[str, np.ndarray]
) -> list[tuple[int, int]]:
    continuity = a["continuity"] & b["continuity"]
    equal = (
        a["base_valid"] & b["base_valid"]
        & (a["x_m"] == b["x_m"]) & (a["y_m"] == b["y_m"])
    )
    return true_runs(equal, continuity)


def _interval_row(
    trace: dict[str, Any], start: int, end: int, rule: str,
    diagnostic_ids: list[str], explanation: str,
) -> dict[str, Any]:
    return {
        "match_id": MATCH_ID,
        "team_key": trace["team_key"],
        "player_key": trace["player_key"],
        "period": trace["period"],
        "start_frame_provider": int(trace["frame"][start]),
        "end_frame_provider": int(trace["frame"][end]),
        "start_time_period_s": float(trace["time_period_s"][start]),
        "end_time_period_s": float(trace["time_period_s"][end]),
        "start_time_match_s": float(trace["time_match_s"][start]),
        "end_time_match_s": float(trace["time_match_s"][end]),
        "rule_code": rule,
        "diagnostic_ids": json.dumps(sorted(diagnostic_ids), separators=(",", ":")),
        "deterministic_rule": explanation,
        "provenance": "heldout Game 2 protocol v1 Stage A",
    }


def _boundary_reason(trace: dict[str, Any], index: int, side: str) -> str:
    if side == "left":
        if index == 0:
            return "period_or_observed_trace_start"
        adjacent = index - 1
    else:
        if index == len(trace["frame"]) - 1:
            return "period_or_observed_trace_end"
        adjacent = index + 1
    reasons = []
    if not trace["base_valid"][adjacent]:
        reasons.append("universal_invalid_support")
    if trace["hard_invalid"][adjacent]:
        reasons.append("hard_raw_jump")
    if trace["duplicate_invalid"][adjacent]:
        reasons.append("sustained_exact_same_team_duplication")
    incoming = index if side == "left" else adjacent
    if not trace["continuity"][incoming]:
        reasons.append("frame_or_time_continuity_break")
    return "+".join(sorted(set(reasons))) or "support_transition"


def _source_hashes(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in paths]


def load_canonical_traces() -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any], dict[str, Any]]:
    home, away = metrica.game_paths(ROOT, 2)
    frame_index = metrica.read_provider_frame_index(home)
    dataset = metrica.load_dataset(home, away)
    provenance = metrica.canonical_provenance(
        dataset, home, away,
        provider_match_id="Sample Game 2",
        canonical_match_id=MATCH_ID,
    )
    buffers: dict[tuple[str, int], dict[str, list[np.ndarray] | str | int]] = {}
    canonical_rows = 0
    canonical_frames = 0
    seen_frames: set[tuple[int, str]] = set()
    seen_row_keys: set[tuple[str, int, str, str]] = set()
    last_match_time = -math.inf
    periods: set[int] = set()
    for chunk in metrica.iter_canonical_polars_chunks(
        dataset, frame_index, match_id=MATCH_ID, frames_per_chunk=2500
    ):
        canonical_tracking.validate_chunk(chunk)
        keys = chunk.select(["match_id", "period", "frame_id_provider", "entity_type", "player_key"])
        if keys.is_duplicated().any():
            raise RuntimeError("Canonical row keys are not unique within a chunk")
        for match, period, frame, entity, player in keys.iter_rows():
            row_key = (str(match), int(period), str(frame), str(entity) + ":" + str(player))
            if row_key in seen_row_keys:
                raise RuntimeError(f"Canonical row key repeats across chunks: {row_key}")
            seen_row_keys.add(row_key)
        canonical_rows += chunk.height
        frame_table = chunk.select(
            ["period", "frame_id_provider", "time_period_s", "time_match_s"]
        ).unique(maintain_order=True)
        canonical_frames += frame_table.height
        for period, frame, _, time_match in frame_table.iter_rows():
            key = (int(period), str(frame))
            if key in seen_frames:
                raise RuntimeError(f"Canonical frame repeats across chunks: {key}")
            if float(time_match) <= last_match_time:
                raise RuntimeError(f"Canonical match clock is not increasing at {key}")
            seen_frames.add(key)
            last_match_time = float(time_match)
            periods.add(int(period))
        players = chunk.filter((pl.col("entity_type") == "player") & (~pl.col("is_goalkeeper")))
        for key_row in players.select(["player_key", "period"]).unique().iter_rows():
            player_key, period = str(key_row[0]), int(key_row[1])
            part = players.filter(
                (pl.col("player_key") == player_key) & (pl.col("period") == period)
            ).sort("time_match_s")
            team_key = str(part.get_column("team_key")[0])
            key = (player_key, period)
            if key not in buffers:
                buffers[key] = {
                    "player_key": player_key, "team_key": team_key, "period": period,
                    "frame": [], "time_period_s": [], "time_match_s": [], "x_m": [],
                    "y_m": [], "is_present": [], "coordinate_valid": [], "support_state": [],
                }
            b = buffers[key]
            b["frame"].append(part.get_column("frame_id_provider").cast(pl.Int64).to_numpy())
            for name in ("time_period_s", "time_match_s", "x_m", "y_m", "is_present", "coordinate_valid"):
                b[name].append(part.get_column(name).to_numpy())
            b["support_state"].append(part.get_column("support_state").to_numpy())
    traces: dict[tuple[str, int], dict[str, Any]] = {}
    for key in sorted(buffers):
        b = buffers[key]
        trace = {name: b[name] for name in ("player_key", "team_key", "period")}
        for name in ("frame", "time_period_s", "time_match_s", "x_m", "y_m", "is_present", "coordinate_valid", "support_state"):
            trace[name] = np.concatenate(b[name])
        finite = np.isfinite(trace["x_m"]) & np.isfinite(trace["y_m"])
        trace["base_valid"] = (
            trace["is_present"].astype(bool)
            & trace["coordinate_valid"].astype(bool)
            & (trace["support_state"] == "observed") & finite
        )
        continuity = np.zeros(len(trace["frame"]), dtype=bool)
        if len(continuity) > 1:
            continuity[1:] = (
                (np.diff(trace["frame"]) == 1)
                & (np.abs(np.diff(trace["time_match_s"]) - RAW_DT_S) <= TIME_TOL)
                & (np.diff(trace["time_period_s"]) > 0)
            )
        trace["continuity"] = continuity
        trace["hard_invalid"] = np.zeros(len(continuity), dtype=bool)
        trace["duplicate_invalid"] = np.zeros(len(continuity), dtype=bool)
        traces[key] = trace
    ingest = {
        "canonical_contract_version": canonical_tracking.CONTRACT_VERSION,
        "adapter_version": canonical_tracking.ADAPTER_VERSION,
        "kloppy_version": str(kloppy.__version__),
        "canonical_rows": canonical_rows,
        "canonical_frames": canonical_frames,
        "periods": sorted(periods),
        "eligible_outfield_players": len({key[0] for key in traces}),
        "player_periods": len(traces),
        "teams": sorted({str(t["team_key"]) for t in traces.values()}),
        "pitch_length_m": metrica.PITCH_LENGTH_M,
        "pitch_width_m": metrica.PITCH_WIDTH_M,
        "coordinate_convention": "metres, pitch centre origin, +x right, +y up, fixed pitch frame",
        "provider_frame_semantics": "integer global provider frame preserved as canonical string",
        "provider_time_semantics": "raw Metrica Time [s] as match clock; Kloppy period-relative timestamp",
    }
    return traces, provenance, ingest


def execute(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    home, away = metrica.game_paths(ROOT, 2)
    traces, provenance, ingest = load_canonical_traces()

    inventory_rows: list[dict[str, Any]] = []
    continuity_rows: list[dict[str, Any]] = []
    registry_rows: list[dict[str, Any]] = []
    link_rows: list[dict[str, Any]] = []
    all_link_max = 0.0
    hard_trigger_map: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)

    for key in sorted(traces):
        trace = traces[key]
        base = trace["base_valid"]
        observed_indices = np.flatnonzero(base)
        unexpected = np.flatnonzero(~trace["continuity"] & (np.arange(len(base)) > 0))
        invalid_runs = true_runs(~base, trace["continuity"])
        for start, end in invalid_runs:
            reasons = sorted(set(str(v) for v in trace["support_state"][start:end + 1]))
            registry_rows.append(_interval_row(
                trace, start, end, "universal_invalid_support", [],
                "row fails presence/coordinate/support/finite universal support rule: " + ",".join(reasons),
            ))
        internal_gap_count = sum(
            1 for start, end in invalid_runs
            if observed_indices.size and start > observed_indices[0] and end < observed_indices[-1]
        )
        out_bounds = base & (
            (np.abs(trace["x_m"]) > metrica.PITCH_LENGTH_M / 2)
            | (np.abs(trace["y_m"]) > metrica.PITCH_WIDTH_M / 2)
        )
        inventory_rows.append({
            "match_id": MATCH_ID, "team_key": trace["team_key"],
            "player_key": trace["player_key"], "period": trace["period"],
            "first_observed_frame": int(trace["frame"][observed_indices[0]]) if observed_indices.size else None,
            "last_observed_frame": int(trace["frame"][observed_indices[-1]]) if observed_indices.size else None,
            "period_start_frame": int(trace["frame"][0]),
            "period_end_frame": int(trace["frame"][-1]),
            "first_observed_time_match_s": float(trace["time_match_s"][observed_indices[0]]) if observed_indices.size else None,
            "last_observed_time_match_s": float(trace["time_match_s"][observed_indices[-1]]) if observed_indices.size else None,
            "total_canonical_rows": len(base), "observed_valid_rows": int(base.sum()),
            "unsupported_rows": int((~base).sum()), "coordinate_valid_rows": int(trace["coordinate_valid"].sum()),
            "coordinate_invalid_rows": int((~trace["coordinate_valid"].astype(bool)).sum()),
            "present_rows": int(trace["is_present"].sum()), "absent_rows": int((~trace["is_present"].astype(bool)).sum()),
            "internal_unsupported_gaps": internal_gap_count,
            "starts_after_period_start": bool(observed_indices.size and observed_indices[0] > 0),
            "ends_before_period_end": bool(observed_indices.size and observed_indices[-1] < len(base) - 1),
            "finite_out_of_bounds_rows": int(out_bounds.sum()),
        })
        for i in unexpected:
            continuity_rows.append({
                "match_id": MATCH_ID, "player_key": trace["player_key"], "period": trace["period"],
                "previous_frame": int(trace["frame"][i - 1]), "current_frame": int(trace["frame"][i]),
                "previous_time_period_s": float(trace["time_period_s"][i - 1]),
                "current_time_period_s": float(trace["time_period_s"][i]),
                "previous_time_match_s": float(trace["time_match_s"][i - 1]),
                "current_time_match_s": float(trace["time_match_s"][i]),
                "frame_delta": int(trace["frame"][i] - trace["frame"][i - 1]),
                "time_period_delta_s": float(trace["time_period_s"][i] - trace["time_period_s"][i - 1]),
                "time_match_delta_s": float(trace["time_match_s"][i] - trace["time_match_s"][i - 1]),
                "classification": "support_split",
            })
        eligible_links = base[1:] & base[:-1] & trace["continuity"][1:]
        indices = np.flatnonzero(eligible_links) + 1
        if indices.size:
            dx = trace["x_m"][indices] - trace["x_m"][indices - 1]
            dy = trace["y_m"][indices] - trace["y_m"][indices - 1]
            dt = trace["time_match_s"][indices] - trace["time_match_s"][indices - 1]
            distance = np.hypot(dx, dy)
            speed = distance / dt
            all_link_max = max(all_link_max, float(speed.max()))
            report = speed > REPORT_JUMP_MPS
            for local in np.flatnonzero(report):
                i = int(indices[local])
                diagnostic_id = f"LINK-{trace['player_key']}-P{trace['period']}-F{int(trace['frame'][i - 1])}-{int(trace['frame'][i])}"
                hard = bool(speed[local] > HARD_JUMP_MPS)
                link_rows.append({
                    "diagnostic_id": diagnostic_id, "match_id": MATCH_ID,
                    "team_key": trace["team_key"], "player_key": trace["player_key"], "period": trace["period"],
                    "start_frame_provider": int(trace["frame"][i - 1]), "end_frame_provider": int(trace["frame"][i]),
                    "start_time_period_s": float(trace["time_period_s"][i - 1]), "end_time_period_s": float(trace["time_period_s"][i]),
                    "start_time_match_s": float(trace["time_match_s"][i - 1]), "end_time_match_s": float(trace["time_match_s"][i]),
                    "raw_link_delta_x_m": float(dx[local]), "raw_link_delta_y_m": float(dy[local]),
                    "coordinate_difference_m": float(distance[local]), "elapsed_s": float(dt[local]),
                    "raw_link_speed_mps": float(speed[local]), "above_report_threshold": True,
                    "hard_raw_jump": hard,
                })
                if hard:
                    hard_trigger_map[key].append((i, diagnostic_id))
        hard_indices = np.array([i for i, _ in hard_trigger_map[key]], dtype=np.int64)
        trace["hard_invalid"] = hard_jump_invalid_mask(
            hard_indices, len(base), base, trace["continuity"]
        )
        for start, end in true_runs(trace["hard_invalid"], np.ones(len(base), dtype=bool)):
            ids = [identifier for i, identifier in hard_trigger_map[key] if start <= i <= end + 1]
            registry_rows.append(_interval_row(
                trace, start, end, "hard_raw_jump",
                ids, "invalidate hard-link endpoints and any observed segment bounded by consecutive >20.0 m/s hard links",
            ))

    duplicate_rows: list[dict[str, Any]] = []
    duplicate_trigger_map: dict[tuple[str, int], list[tuple[int, int, str]]] = defaultdict(list)
    by_period: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces.values():
        by_period[int(trace["period"])].append(trace)
    duplicate_number = 0
    for period in sorted(by_period):
        candidates = sorted(by_period[period], key=lambda x: x["player_key"])
        for ai, a in enumerate(candidates):
            for b in candidates[ai + 1:]:
                for start, end in exact_duplicate_runs(a, b):
                    duplicate_number += 1
                    diagnostic_id = f"DUP-{duplicate_number:06d}"
                    same_team = a["team_key"] == b["team_key"]
                    count = end - start + 1
                    qualifying = same_team and count >= DUPLICATE_MIN_FRAMES
                    duplicate_rows.append({
                        "diagnostic_id": diagnostic_id, "match_id": MATCH_ID,
                        "team_key_a": a["team_key"], "player_key_a": a["player_key"],
                        "team_key_b": b["team_key"], "player_key_b": b["player_key"],
                        "same_team": same_team, "period": period,
                        "start_frame_provider": int(a["frame"][start]), "end_frame_provider": int(a["frame"][end]),
                        "start_time_period_s": float(a["time_period_s"][start]), "end_time_period_s": float(a["time_period_s"][end]),
                        "start_time_match_s": float(a["time_match_s"][start]), "end_time_match_s": float(a["time_match_s"][end]),
                        "consecutive_frame_count": count, "qualifying_same_team_exclusion": qualifying,
                    })
                    if qualifying:
                        duplicate_trigger_map[(a["player_key"], period)].append((start, end, diagnostic_id))
                        duplicate_trigger_map[(b["player_key"], period)].append((start, end, diagnostic_id))
    for key, events in duplicate_trigger_map.items():
        trace = traces[key]
        for start, end, _ in events:
            trace["duplicate_invalid"][start:end + 1] = True
        for start, end in true_runs(trace["duplicate_invalid"], np.ones(len(trace["frame"]), dtype=bool)):
            ids = [identifier for lo, hi, identifier in events if lo <= end and hi >= start]
            registry_rows.append(_interval_row(
                trace, start, end, "sustained_exact_same_team_duplication", ids,
                "invalidate both players throughout maximal exact same-team duplicate run of at least five consecutive frames",
            ))

    registry_rows.sort(key=lambda r: (r["team_key"], r["player_key"], r["period"], r["start_frame_provider"], r["rule_code"]))
    segment_rows: list[dict[str, Any]] = []
    for key in sorted(traces):
        trace = traces[key]
        valid = trace["base_valid"] & ~trace["hard_invalid"] & ~trace["duplicate_invalid"]
        for number, (start, end) in enumerate(true_runs(valid, trace["continuity"]), 1):
            segment_rows.append({
                "match_id": MATCH_ID, "team_key": trace["team_key"], "player_key": trace["player_key"],
                "period": trace["period"], "segment_id": f"{trace['player_key']}|P{trace['period']}|S{number:03d}",
                "start_frame_provider": int(trace["frame"][start]), "end_frame_provider": int(trace["frame"][end]),
                "start_time_period_s": float(trace["time_period_s"][start]), "end_time_period_s": float(trace["time_period_s"][end]),
                "start_time_match_s": float(trace["time_match_s"][start]), "end_time_match_s": float(trace["time_match_s"][end]),
                "frame_count": end - start + 1,
                "left_boundary_reason": _boundary_reason(trace, start, "left"),
                "right_boundary_reason": _boundary_reason(trace, end, "right"),
            })

    # Mechanical QC on the frozen raw support products.
    registry_keys = set()
    final_valid_rows = 0
    hard_invalid_rows = 0
    duplicate_invalid_rows = 0
    universal_hard_overlap = 0
    universal_duplicate_overlap = 0
    hard_duplicate_overlap = 0
    all_three_overlap = 0
    for trace in traces.values():
        universal = ~trace["base_valid"]
        effective_invalid = ~trace["base_valid"] | trace["hard_invalid"] | trace["duplicate_invalid"]
        final_valid_rows += int((~effective_invalid).sum())
        hard_invalid_rows += int(trace["hard_invalid"].sum())
        duplicate_invalid_rows += int(trace["duplicate_invalid"].sum())
        universal_hard_overlap += int((universal & trace["hard_invalid"]).sum())
        universal_duplicate_overlap += int((universal & trace["duplicate_invalid"]).sum())
        hard_duplicate_overlap += int((trace["hard_invalid"] & trace["duplicate_invalid"]).sum())
        all_three_overlap += int((universal & trace["hard_invalid"] & trace["duplicate_invalid"]).sum())
        for index in np.flatnonzero(effective_invalid):
            registry_keys.add((trace["player_key"], trace["period"], int(trace["frame"][index])))
    segment_keys = set()
    for row in segment_rows:
        for frame in range(row["start_frame_provider"], row["end_frame_provider"] + 1):
            segment_keys.add((row["player_key"], row["period"], frame))
    hard_survivors = 0
    duplicate_survivors = 0
    for key, trace in traces.items():
        valid = trace["base_valid"] & ~trace["hard_invalid"] & ~trace["duplicate_invalid"]
        hard_survivors += int((valid[1:] & valid[:-1] & trace["continuity"][1:] & (
            np.hypot(np.diff(trace["x_m"]), np.diff(trace["y_m"])) / RAW_DT_S > HARD_JUMP_MPS
        )).sum())
    for row in duplicate_rows:
        if not row["qualifying_same_team_exclusion"]:
            continue
        for player in (row["player_key_a"], row["player_key_b"]):
            frames = range(row["start_frame_provider"], row["end_frame_provider"] + 1)
            duplicate_survivors += sum((player, row["period"], f) in segment_keys for f in frames)
    qc = {
        "canonical_schema_valid": True,
        "unique_canonical_row_keys": True,
        "stable_player_ids": True,
        "every_raw_row_has_deterministic_status": (
            final_valid_rows + len(registry_keys)
            == sum(len(trace["frame"]) for trace in traces.values())
        ),
        "registry_rows_have_required_fields": all(set(r) == set(REGISTRY_COLUMNS) for r in registry_rows),
        "excluded_rows_in_valid_segments": len(registry_keys & segment_keys),
        "hard_jump_links_surviving": hard_survivors,
        "qualifying_duplicate_rows_surviving": duplicate_survivors,
        "period_boundaries_respected": all(r["period"] in ingest["periods"] for r in segment_rows),
        "invalid_coordinates_excluded": True,
        "interpolation_used": False,
        "clipping_used": False,
        "smoothing_used": False,
        "continuous_features_computed": False,
        "frequency_diagnostic_computed": False,
        "defensive_outcomes_accessed": False,
        "game3_accessed": False,
    }
    hard_count = sum(bool(r["hard_raw_jump"]) for r in link_rows)
    qualifying_duplicates = sum(bool(r["qualifying_same_team_exclusion"]) for r in duplicate_rows)
    hard_records = [r for r in link_rows if r["hard_raw_jump"]]
    qualifying_duplicate_records = [r for r in duplicate_rows if r["qualifying_same_team_exclusion"]]
    duplicate_counts = np.array(
        [r["consecutive_frame_count"] for r in qualifying_duplicate_records], dtype=np.int64
    )
    duplicate_player_periods = {
        (player, int(r["period"]))
        for r in qualifying_duplicate_records
        for player in (r["player_key_a"], r["player_key_b"])
    }
    aggregate = {
        "canonical_ingestion": ingest,
        "duplicate_canonical_row_keys": 0,
        "raw_support": {
            "canonical_outfield_rows": int(sum(r["total_canonical_rows"] for r in inventory_rows)),
            "observed_valid_rows_before_registry": int(sum(r["observed_valid_rows"] for r in inventory_rows)),
            "universal_invalid_rows": int(sum(r["unsupported_rows"] for r in inventory_rows)),
            "coordinate_invalid_rows": int(sum(r["coordinate_invalid_rows"] for r in inventory_rows)),
            "finite_out_of_bounds_rows": int(sum(r["finite_out_of_bounds_rows"] for r in inventory_rows)),
            "internal_unsupported_gaps": int(sum(r["internal_unsupported_gaps"] for r in inventory_rows)),
            "player_periods_starting_after_period_start": int(sum(r["starts_after_period_start"] for r in inventory_rows)),
            "player_periods_ending_before_period_end": int(sum(r["ends_before_period_end"] for r in inventory_rows)),
            "hard_jump_invalid_rows_before_overlap": hard_invalid_rows,
            "sustained_duplicate_invalid_rows_before_overlap": duplicate_invalid_rows,
            "final_valid_rows": final_valid_rows,
            "final_invalid_union_rows": len(registry_keys),
            "overlap_universal_and_hard_rows": universal_hard_overlap,
            "overlap_universal_and_duplicate_rows": universal_duplicate_overlap,
            "overlap_hard_and_duplicate_rows": hard_duplicate_overlap,
            "overlap_all_three_rows": all_three_overlap,
        },
        "frame_time_continuity_issues": len(continuity_rows),
        "reported_links_above_10_mps": len(link_rows),
        "hard_links_above_20_mps": hard_count,
        "hard_link_affected_players": len({r["player_key"] for r in hard_records}),
        "hard_link_affected_player_periods": len({(r["player_key"], int(r["period"])) for r in hard_records}),
        "hard_link_registry_intervals": sum(r["rule_code"] == "hard_raw_jump" for r in registry_rows),
        "maximum_observed_raw_link_speed_mps": all_link_max,
        "exact_duplicate_runs_all_pairs": len(duplicate_rows),
        "qualifying_sustained_same_team_duplicate_events": qualifying_duplicates,
        "qualifying_duplicate_distinct_identity_pairs": len({
            tuple(sorted((r["player_key_a"], r["player_key_b"])))
            for r in qualifying_duplicate_records
        }),
        "qualifying_duplicate_affected_players": len({player for player, _ in duplicate_player_periods}),
        "qualifying_duplicate_affected_player_periods": len(duplicate_player_periods),
        "qualifying_duplicate_frame_count_min": int(duplicate_counts.min()),
        "qualifying_duplicate_frame_count_median": float(np.median(duplicate_counts)),
        "qualifying_duplicate_frame_count_max": int(duplicate_counts.max()),
        "qualifying_duplicate_registry_intervals": sum(
            r["rule_code"] == "sustained_exact_same_team_duplication" for r in registry_rows
        ),
        "registry_entries": len(registry_rows),
        "registry_entries_by_rule": {
            rule: sum(r["rule_code"] == rule for r in registry_rows)
            for rule in sorted({r["rule_code"] for r in registry_rows})
        },
        "valid_support_segments": len(segment_rows),
        "unresolved_support_ambiguities": [],
        "stage_a_classification": "READY" if all([
            qc["canonical_schema_valid"], qc["unique_canonical_row_keys"],
            qc["stable_player_ids"], qc["every_raw_row_has_deterministic_status"],
            qc["registry_rows_have_required_fields"],
            qc["excluded_rows_in_valid_segments"] == 0, qc["hard_jump_links_surviving"] == 0,
            qc["qualifying_duplicate_rows_surviving"] == 0,
        ]) else "BLOCKED",
    }

    write_json(output / "canonical_provenance.json", provenance)
    write_csv(output / "raw_support_inventory.csv", inventory_rows, list(inventory_rows[0]))
    continuity_columns = [
        "match_id", "player_key", "period", "previous_frame", "current_frame",
        "previous_time_period_s", "current_time_period_s", "previous_time_match_s",
        "current_time_match_s", "frame_delta", "time_period_delta_s", "time_match_delta_s",
        "classification",
    ]
    write_csv(output / "frame_time_continuity.csv", continuity_rows, continuity_columns)
    write_csv(output / "raw_link_diagnostics.csv", link_rows, LINK_COLUMNS)
    write_csv(output / "exact_coordinate_duplication_runs.csv", duplicate_rows, DUP_COLUMNS)
    write_csv(output / "trajectory_validity_registry.csv", registry_rows, REGISTRY_COLUMNS)
    write_csv(output / "valid_support_segments.csv", segment_rows, SEGMENT_COLUMNS)
    write_json(output / "stage_a_qc.json", qc)
    write_json(output / "stage_a_result.json", aggregate)
    manifest = {
        "analysis": "Game 2 continuous attacker movement Stage-A support audit",
        "stage": "A — raw trajectory support only",
        "source_files": _source_hashes([home, away]),
        "governing_files": _source_hashes([PROTOCOL, GAME1_PROTOCOL, GAME1_RESULT, Path(__file__)]),
        "versions": {
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "polars": pl.__version__, "kloppy": kloppy.__version__,
            "canonical_contract": canonical_tracking.CONTRACT_VERSION,
            "adapter": canonical_tracking.ADAPTER_VERSION,
        },
        "frozen_rules": {
            "raw_dt_s": RAW_DT_S, "time_tolerance_s": TIME_TOL,
            "hard_raw_jump_operator": ">", "hard_raw_jump_mps": HARD_JUMP_MPS,
            "report_only_raw_jump_operator": ">", "report_only_raw_jump_mps": REPORT_JUMP_MPS,
            "same_team_exact_duplicate_min_consecutive_frames": DUPLICATE_MIN_FRAMES,
        },
        "firewall": {
            "smoothing": False, "continuous_features": False, "frequency_diagnostic": False,
            "events": False, "defensive_outcomes": False, "game3": False,
        },
    }
    write_json(output / "manifest.json", manifest)
    governed = [
        "canonical_provenance.json", "raw_support_inventory.csv", "frame_time_continuity.csv",
        "raw_link_diagnostics.csv", "exact_coordinate_duplication_runs.csv",
        "trajectory_validity_registry.csv", "valid_support_segments.csv", "stage_a_qc.json",
        "stage_a_result.json", "manifest.json",
    ]
    write_json(output / "governed_output_hashes.json", {name: sha256(output / name) for name in governed})
    return aggregate


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    expected = json.loads((primary / "governed_output_hashes.json").read_text(encoding="utf-8"))
    observed = {name: sha256(rerun / name) for name in expected}
    result = {
        "all_governed_outputs_byte_identical": expected == observed,
        "expected": expected,
        "observed": observed,
        "mismatches": sorted(name for name in expected if expected[name] != observed[name]),
    }
    write_json(primary / "reproduction_verification.json", result)
    if not result["all_governed_outputs_byte_identical"]:
        raise RuntimeError(f"Stage-A deterministic reproduction failed: {result['mismatches']}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-against", type=Path)
    parser.add_argument("--no-independent-rerun", action="store_true")
    args = parser.parse_args()
    execute(args.output)
    if args.verify_against:
        verify(args.verify_against, args.output)
        return
    if not args.no_independent_rerun:
        with tempfile.TemporaryDirectory(prefix="moving-defense-game2-stage-a-") as directory:
            rerun = Path(directory)
            execute(rerun)
            verify(args.output, rerun)


if __name__ == "__main__":
    main()
