from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.game1_event_ordering_compatibility_audit import (
    CLASSIFICATION,
    classify,
    dependency_rows,
    summarize_events,
    write_json,
)


def _events(*, required_endpoint_bad: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Team": ["Home", "Away", "Home"],
            "Type": ["SET PIECE", "PASS", "SHOT"],
            "Subtype": ["KICK OFF", "", "ON TARGET-GOAL"],
            "Period": [1, 1, 1],
            "Start Frame": [1, 2, 3],
            "Start Time [s]": [0.04, 0.08, 0.12],
            "End Frame": [0, 2, 2 if required_endpoint_bad else 4],
            "End Time [s]": [0.0, 0.08, 0.08 if required_endpoint_bad else 0.16],
        }
    )


def _reconciliation(ok: bool = True) -> dict[str, object]:
    return {"all_reconciled_starts_exact": ok}


def test_summary_counts_and_linear_negative_quantiles() -> None:
    summary = summarize_events(_events())
    anomaly = summary["end_time_before_start_time"]
    assert summary["total_event_count"] == 3
    assert anomaly["count"] == 1
    assert anomaly["rate"] == pytest.approx(1 / 3)
    assert anomaly["by_type"] == {"SET PIECE": 1}
    assert anomaly["by_subtype"] == {"KICK OFF": 1}
    assert set(anomaly["negative_duration_distribution"].values()) == {-0.04}
    assert summary["end_frame_before_start_frame"] == {
        "count": 1,
        "same_record_set_as_time_anomalies": True,
    }


def test_unused_malformed_endpoint_yields_event_specific_classification() -> None:
    assessment = classify(summarize_events(_events()), _reconciliation())
    assert assessment["classification"] == CLASSIFICATION
    assert assessment["start_integrity_passed"] is True
    assert assessment["required_endpoint_integrity_passed"] is True


@pytest.mark.parametrize("start_ok,required_bad", [(False, False), (True, True)])
def test_start_or_required_endpoint_failure_strictly_blocks(
    start_ok: bool, required_bad: bool
) -> None:
    assessment = classify(
        summarize_events(_events(required_endpoint_bad=required_bad)),
        _reconciliation(start_ok),
    )
    assert assessment["classification"] == "C. STRICT BLOCK REQUIRED"


def test_dependency_matrix_records_only_one_end_frame_consumer() -> None:
    rows = dependency_rows()
    consumers = [row for row in rows if row["needs_end_frame"]]
    assert [row["operation"] for row in consumers] == ["SHOT GOAL/OUT dead-ball opening"]
    assert not any(row["needs_end_time"] for row in rows)


def test_nonfinite_and_nonwhole_start_values_fail_closed() -> None:
    events = _events()
    events.loc[1, "Start Time [s]"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        summarize_events(events)
    events = _events()
    events["Start Frame"] = events["Start Frame"].astype(float)
    events.loc[1, "Start Frame"] = 1.5
    with pytest.raises(ValueError, match="whole"):
        summarize_events(events)


def test_aggregate_serialization_rejects_raw_or_nonfinite_content(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="prohibited"):
        write_json(tmp_path / "bad.json", {"offending_rows": []})
    with pytest.raises(ValueError, match="nonfinite"):
        write_json(tmp_path / "bad.json", {"value": float("inf")})


def test_json_serialization_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    payload = {"z": [2, 1], "a": {"count": 3}}
    write_json(first, payload)
    write_json(second, json.loads(json.dumps(payload)))
    assert first.read_bytes() == second.read_bytes()
