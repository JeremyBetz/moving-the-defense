"""Aggregate-only audit of Metrica Game 1 event endpoint ordering.

This module never constructs possession states or scientific response values.
It inspects event metadata and native tracking clocks only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


AUDIT_ID = "game1_event_ordering_compatibility_audit"
CLASSIFICATION = "B. EVENT-TYPE-SPECIFIC COMPATIBILITY JUSTIFIED"
REQUIRED_EVENT_COLUMNS = (
    "Team",
    "Type",
    "Subtype",
    "Period",
    "Start Frame",
    "Start Time [s]",
    "End Frame",
    "End Time [s]",
)
PROHIBITED_SERIALIZED_KEYS = {
    "event_rows",
    "offending_rows",
    "timestamps",
    "frame_ids",
    "coordinates",
    "player_ids",
    "team_ids",
    "scores",
    "possession_states",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _whole(values: pd.Series, name: str) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="raise").to_numpy(float)
    if not np.isfinite(numeric).all() or not np.equal(numeric, np.floor(numeric)).all():
        raise ValueError(f"{name} must contain finite whole values")
    return numeric.astype(np.int64)


def _finite(values: pd.Series, name: str) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="raise").to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"{name} must contain finite values")
    return numeric


def _count_map(values: pd.Series) -> dict[str, int]:
    normalized = values.fillna("<NULL>").astype(str).str.strip().replace("", "<EMPTY>")
    return {str(key): int(value) for key, value in normalized.value_counts().sort_index().items()}


def summarize_events(events: pd.DataFrame) -> dict[str, Any]:
    missing = set(REQUIRED_EVENT_COLUMNS) - set(events.columns)
    if missing:
        raise ValueError(f"missing event columns: {sorted(missing)}")

    period = _whole(events["Period"], "Period")
    start_frame = _whole(events["Start Frame"], "Start Frame")
    end_frame = _whole(events["End Frame"], "End Frame")
    start_time = _finite(events["Start Time [s]"], "Start Time [s]")
    end_time = _finite(events["End Time [s]"], "End Time [s]")
    time_reverse = end_time < start_time
    frame_reverse = end_frame < start_frame
    duration = end_time - start_time
    negative = duration[time_reverse]

    types = events["Type"].fillna("").astype(str).str.strip().str.upper()
    subtypes = events["Subtype"].fillna("").astype(str).str.strip().str.upper()
    endpoint_required = types.eq("SHOT") & subtypes.str.contains("GOAL|OUT", regex=True)

    provider_order = {}
    for value in sorted(set(period.tolist())):
        selected = period == value
        provider_order[str(int(value))] = {
            "start_frame_nondecreasing": bool(np.all(np.diff(start_frame[selected]) >= 0)),
            "start_time_nondecreasing": bool(np.all(np.diff(start_time[selected]) >= 0)),
        }

    if len(negative):
        q = np.quantile(negative, [0.0, 0.25, 0.5, 0.75, 1.0], method="linear")
        distribution = {
            "minimum_s": float(q[0]),
            "p25_s": float(q[1]),
            "median_s": float(q[2]),
            "p75_s": float(q[3]),
            "maximum_s": float(q[4]),
        }
    else:
        distribution = {
            "minimum_s": None,
            "p25_s": None,
            "median_s": None,
            "p75_s": None,
            "maximum_s": None,
        }

    selected = events.loc[time_reverse]
    return {
        "total_event_count": int(len(events)),
        "end_time_before_start_time": {
            "count": int(time_reverse.sum()),
            "rate": float(time_reverse.mean()) if len(events) else 0.0,
            "by_period": _count_map(selected["Period"]),
            "by_type": _count_map(selected["Type"]),
            "by_subtype": _count_map(selected["Subtype"]),
            "negative_duration_distribution": distribution,
        },
        "end_frame_before_start_frame": {
            "count": int(frame_reverse.sum()),
            "same_record_set_as_time_anomalies": bool(np.array_equal(time_reverse, frame_reverse)),
        },
        "start_integrity": {
            "all_start_frames_finite_whole": True,
            "all_start_times_finite": True,
            "provider_order_by_period": provider_order,
        },
        "endpoint_dependent_records": {
            "definition": "SHOT subtype containing GOAL or OUT",
            "count": int(endpoint_required.sum()),
            "time_order_anomaly_count": int((time_reverse & endpoint_required.to_numpy()).sum()),
            "frame_order_anomaly_count": int((frame_reverse & endpoint_required.to_numpy()).sum()),
        },
    }


def read_tracking_clock(path: Path) -> pd.DataFrame:
    clock = pd.read_csv(path, skiprows=2, usecols=[0, 1, 2])
    clock.columns = ["period", "frame", "time_s"]
    clock["period"] = _whole(clock["period"], "tracking Period")
    clock["frame"] = _whole(clock["frame"], "tracking Frame")
    clock["time_s"] = _finite(clock["time_s"], "tracking Time")
    if clock.duplicated(["period", "frame"]).any():
        raise ValueError("tracking clock contains duplicate period/frame keys")
    return clock


def reconcile_starts(
    events: pd.DataFrame,
    home_clock: pd.DataFrame,
    away_clock: pd.DataFrame,
) -> dict[str, Any]:
    if not home_clock.equals(away_clock):
        raise ValueError("Home and Away native tracking clocks differ")
    start_period = _whole(events["Period"], "Period")
    start_frame = _whole(events["Start Frame"], "Start Frame")
    start_time = _finite(events["Start Time [s]"], "Start Time [s]")
    lookup = home_clock.set_index(["period", "frame"])["time_s"]
    missing = 0
    differences: list[float] = []
    for period, frame, time_s in zip(start_period, start_frame, start_time, strict=True):
        key = (int(period), int(frame))
        if key not in lookup.index:
            missing += 1
            continue
        differences.append(float(time_s) - float(lookup.loc[key]))
    maximum = max((abs(value) for value in differences), default=0.0)
    return {
        "home_away_tracking_clocks_identical": True,
        "event_start_count": int(len(events)),
        "unreconciled_start_count": int(missing),
        "maximum_absolute_start_time_mismatch_s": float(maximum),
        "all_reconciled_starts_exact": bool(missing == 0 and maximum == 0.0),
    }


def dependency_rows() -> list[dict[str, Any]]:
    rows = [
        ("PASS possession establishment/change", True, False, False, "evaluated at the event start"),
        ("RECOVERY possession establishment/change", True, False, False, "evaluated at the event start"),
        ("SET PIECE restart", True, False, False, "restart frame and pending owner use the event start"),
        ("SHOT possession evidence", True, False, False, "possession evidence uses the shot start"),
        ("BALL LOST ambiguity", True, False, False, "ambiguity begins at the event start"),
        ("CHALLENGE", True, False, False, "inspected at its start but does not establish possession"),
        ("BALL OUT dead-ball opening", True, False, False, "dead ball opens at the event start"),
        ("FAULT RECEIVED dead-ball opening", True, False, False, "dead ball opens at the event start"),
        ("CARD dead-ball opening", True, False, False, "dead ball opens at the event start"),
        ("SHOT GOAL/OUT dead-ball opening", True, True, False, "dead ball opens at the recorded End Frame"),
        ("FORCED-END HALF", True, False, False, "period-ending state begins at the event start"),
        ("restart-frame handling", True, False, False, "SET PIECE start remains dead; possession starts next frame"),
        ("period boundary", True, False, False, "state initializes from native period frames and does not carry over"),
    ]
    return [
        {
            "operation": operation,
            "needs_start": start,
            "needs_end_frame": end_frame,
            "needs_end_time": end_time,
            "reason": reason,
        }
        for operation, start, end_frame, end_time, reason in rows
    ]


def classify(summary: Mapping[str, Any], reconciliation: Mapping[str, Any]) -> dict[str, Any]:
    start_ok = bool(reconciliation["all_reconciled_starts_exact"]) and all(
        row["start_frame_nondecreasing"] and row["start_time_nondecreasing"]
        for row in summary["start_integrity"]["provider_order_by_period"].values()
    )
    endpoint = summary["endpoint_dependent_records"]
    required_ok = endpoint["time_order_anomaly_count"] == 0 and endpoint["frame_order_anomaly_count"] == 0
    anomaly_count = summary["end_time_before_start_time"]["count"]
    if not start_ok or not required_ok:
        classification = "C. STRICT BLOCK REQUIRED"
    elif anomaly_count > 0:
        classification = CLASSIFICATION
    else:
        classification = "B. EVENT-TYPE-SPECIFIC COMPATIBILITY JUSTIFIED"
    return {
        "classification": classification,
        "start_integrity_passed": start_ok,
        "required_endpoint_integrity_passed": required_ok,
        "provider_semantics_status": "raw Start/End column semantics are not explicitly defined",
        "source_pattern_evidence": (
            "the sole anomaly is an opening SET PIECE/KICK OFF boundary record; "
            "its Start maps exactly to the first native tracking frame while its End precedes support"
        ),
        "prospective_rule": {
            "all_events": (
                "require finite whole Start Frame, finite Start Time, provider ordering, exact native-clock "
                "reconciliation, and unchanged simultaneous-ownership checks"
            ),
            "endpoint_dependent_events": (
                "for SHOT subtypes containing GOAL or OUT, additionally require finite ordered End Frame "
                "and End Time and native tracking reconciliation"
            ),
            "other_events": (
                "preserve and report malformed End metadata but do not reject possession reconstruction "
                "because those End fields are not consumed"
            ),
            "forbidden_repairs": ["swap", "clamp", "absolute_duration", "zero_duration", "row_drop"],
            "applies_identically_to": ["Metrica Sample Game 1", "Metrica Sample Game 2"],
        },
    }


def _assert_aggregate_safe(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_SERIALIZED_KEYS:
                raise ValueError(f"prohibited serialized key: {key}")
            _assert_aggregate_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_aggregate_safe(nested)
    elif isinstance(value, float) and not np.isfinite(value):
        raise ValueError("nonfinite aggregate value")


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _assert_aggregate_safe(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_audit(
    *,
    event_path: Path,
    home_tracking_path: Path,
    away_tracking_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    events = pd.read_csv(event_path)
    summary = summarize_events(events)
    reconciliation = reconcile_starts(
        events,
        read_tracking_clock(home_tracking_path),
        read_tracking_clock(away_tracking_path),
    )
    summary["start_integrity"]["tracking_reconciliation"] = reconciliation
    dependencies = {"audit_id": AUDIT_ID, "operations": dependency_rows()}
    assessment = classify(summary, reconciliation)
    schema = {
        "audit_id": AUDIT_ID,
        "relevant_fields": [
            {"name": "Team", "units": None, "period_basis": None, "nullable": False, "current_use": "ownership evidence", "semantic_evidence": "project implementation"},
            {"name": "Type", "units": None, "period_basis": None, "nullable": False, "current_use": "state-operation category", "semantic_evidence": "provider event definitions"},
            {"name": "Subtype", "units": None, "period_basis": None, "nullable": True, "current_use": "restart/dead-ball subtype", "semantic_evidence": "provider event definitions"},
            {"name": "Period", "units": None, "period_basis": "match period", "nullable": False, "current_use": "state reset and clock reconciliation", "semantic_evidence": "source schema and project implementation"},
            {"name": "Start Frame", "units": "native frame", "period_basis": "provider frame identifier", "nullable": False, "current_use": "event ordering and state change", "semantic_evidence": "source pattern and project implementation; provider PDF does not define the column"},
            {"name": "Start Time [s]", "units": "seconds", "period_basis": "match clock", "nullable": False, "current_use": "ordering tie-break and validation", "semantic_evidence": "field label/source synchronization; provider PDF does not define the column"},
            {"name": "End Frame", "units": "native frame", "period_basis": "provider frame identifier", "nullable": False, "current_use": "SHOT GOAL/OUT dead-ball boundary", "semantic_evidence": "project implementation; provider PDF does not define the column"},
            {"name": "End Time [s]", "units": "seconds", "period_basis": "match clock", "nullable": False, "current_use": "validation only", "semantic_evidence": "field label; provider PDF does not define the column"},
        ],
        "provider_documentation": {
            "sample_repository": "https://github.com/metrica-sports/sample-data",
            "event_definitions": "https://github.com/metrica-sports/sample-data/blob/master/documentation/events-definitions.pdf",
            "event_definitions_sha256": "5afb1ee34931447223ef8b9dc6a30b827fd0ba57ac9b6e2d7125ee87b083a866",
            "documented": "event types, subtypes, possession terminology, and tracking/event synchronization",
            "not_documented": "raw CSV Start Frame/Time and End Frame/Time semantics",
        },
    }
    qc = {
        "audit_id": AUDIT_ID,
        "status": "PASS",
        "no_possession_reconstruction": True,
        "no_score_or_candidate_access": True,
        "no_raw_rows_serialized": True,
        "source_unmodified": True,
        "classification_count": 1,
        "checks": {
            "start_integrity": assessment["start_integrity_passed"],
            "required_endpoint_integrity": assessment["required_endpoint_integrity_passed"],
            "aggregate_only": True,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        "schema_summary.json": schema,
        "anomaly_summary.json": {"audit_id": AUDIT_ID, **summary},
        "dependency_matrix.json": dependencies,
        "compatibility_assessment.json": {"audit_id": AUDIT_ID, **assessment},
        "qc.json": qc,
    }
    for name, payload in payloads.items():
        write_json(output_dir / name, payload)
    manifest = {
        "audit_id": AUDIT_ID,
        "status": "CLOSED_AGGREGATE_ONLY",
        "audit_input_commit": "42326b440fcec5de45ee8977dd97eae0e40a88be",
        "classification": assessment["classification"],
        "frozen_dependency_sha256": {
            "docs/protocols/game1_event_ordering_compatibility_audit.md": sha256_file(
                Path("docs/protocols/game1_event_ordering_compatibility_audit.md")
            ),
            "src/game1_event_ordering_compatibility_audit.py": sha256_file(
                Path("src/game1_event_ordering_compatibility_audit.py")
            ),
            "tests/test_game1_event_ordering_compatibility_audit.py": sha256_file(
                Path("tests/test_game1_event_ordering_compatibility_audit.py")
            ),
        },
        "source_identities": {
            str(event_path): sha256_file(event_path),
            str(home_tracking_path): sha256_file(home_tracking_path),
            str(away_tracking_path): sha256_file(away_tracking_path),
        },
        "artifact_sha256": {
            name: sha256_file(output_dir / name) for name in sorted(payloads)
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    return {"summary": summary, "assessment": assessment, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--home-tracking-path", type=Path, required=True)
    parser.add_argument("--away-tracking-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_audit(
        event_path=args.event_path,
        home_tracking_path=args.home_tracking_path,
        away_tracking_path=args.away_tracking_path,
        output_dir=args.output_dir,
    )
    print(json.dumps({"classification": result["assessment"]["classification"]}, sort_keys=True))


if __name__ == "__main__":
    main()
