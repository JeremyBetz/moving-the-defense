"""Thin JSON boundary for the retrospective defender-relative replay score.

This module deliberately provides an in-process/CLI API rather than a hosted
service.  It accepts the repository's normalized tracking contract, delegates
all measurement logic to :mod:`defensive_reorganization_replay`, and returns
only the scorer's documented player/team tables and metadata.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_replay import (
    PLAYER_SCORE_COLUMNS,
    TEAM_SCORE_COLUMNS,
    DefenderRelativePathSpec,
    score_trailing_defender_relative_path,
)


API_SCHEMA_VERSION = "1.0"
REQUIRED_REQUEST_KEYS = frozenset({"schema_version", "spec", "tracking"})
OPTIONAL_REQUEST_KEYS = frozenset({"time_range"})
SPEC_KEYS = frozenset(
    {
        "defending_team_key",
        "source_fps",
        "window_seconds",
        "smoothing_frames",
        "smoothing_method",
    }
)


class ReplayAPIError(ValueError):
    """Raised when a request violates the public replay API contract."""


def _finite_json(value: Any) -> Any:
    """Convert pandas/NumPy values to strict JSON-compatible values."""
    if value is pd.NA or value is None:
        return None
    if isinstance(value, Mapping):
        return {str(key): _finite_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite_json(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {column: _finite_json(row[column]) for column in frame.columns}
        for row in frame.to_dict(orient="records")
    ]


def score_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Score one normalized-tracking request and return a JSON-ready response.

    The function performs no provider loading, interpolation, tactical
    inference, outcome discovery, or display normalization.
    """
    if not isinstance(payload, Mapping):
        raise ReplayAPIError("request must be a JSON object")
    missing_request = REQUIRED_REQUEST_KEYS - set(payload)
    unknown_request = set(payload) - REQUIRED_REQUEST_KEYS - OPTIONAL_REQUEST_KEYS
    if missing_request or unknown_request:
        raise ReplayAPIError(
            f"request keys are invalid; missing={sorted(missing_request)}, "
            f"unknown={sorted(unknown_request)}"
        )
    if payload["schema_version"] != API_SCHEMA_VERSION:
        raise ReplayAPIError(f"schema_version must equal {API_SCHEMA_VERSION}")

    spec_payload = payload["spec"]
    if not isinstance(spec_payload, Mapping):
        raise ReplayAPIError("spec must be a JSON object")
    unknown_spec = set(spec_payload) - SPEC_KEYS
    if unknown_spec:
        raise ReplayAPIError(f"unsupported spec keys: {sorted(unknown_spec)}")
    required_spec = {"defending_team_key", "source_fps"}
    missing_spec = required_spec - set(spec_payload)
    if missing_spec:
        raise ReplayAPIError(f"missing spec keys: {sorted(missing_spec)}")

    tracking_payload = payload["tracking"]
    if not isinstance(tracking_payload, list) or not tracking_payload:
        raise ReplayAPIError("tracking must be a nonempty JSON array of rows")
    if not all(isinstance(row, Mapping) for row in tracking_payload):
        raise ReplayAPIError("every tracking row must be a JSON object")

    try:
        spec = DefenderRelativePathSpec(**dict(spec_payload))
        scores = score_trailing_defender_relative_path(
            pd.DataFrame.from_records(tracking_payload), spec
        )
    except (TypeError, ValueError) as exc:
        raise ReplayAPIError(str(exc)) from exc

    players = scores.player_scores
    teams = scores.team_scores
    time_range = payload.get("time_range")
    if time_range is not None:
        if (
            not isinstance(time_range, Mapping)
            or set(time_range) != {"start_time_s", "end_time_s"}
        ):
            raise ReplayAPIError("time_range must contain exactly start_time_s and end_time_s")
        try:
            start = float(time_range["start_time_s"])
            end = float(time_range["end_time_s"])
        except (TypeError, ValueError) as exc:
            raise ReplayAPIError("time_range values must be numeric") from exc
        if not np.isfinite([start, end]).all() or start > end:
            raise ReplayAPIError("time_range must be finite with start_time_s <= end_time_s")
        players = players.loc[players["time_match_s"].between(start, end)].reset_index(drop=True)
        teams = teams.loc[teams["time_match_s"].between(start, end)].reset_index(drop=True)

    return {
        "schema_version": API_SCHEMA_VERSION,
        "measurement": "trailing_defender_relative_path",
        "units": "metres",
        "interpretation": (
            "retrospective accumulated movement relative to the other nine "
            "defenders; not a causal, tactical, quality, or value measure"
        ),
        "player_score_columns": list(PLAYER_SCORE_COLUMNS),
        "team_score_columns": list(TEAM_SCORE_COLUMNS),
        "player_scores": _records(players),
        "team_scores": _records(teams),
        "metadata": _finite_json(
            {**scores.metadata, "requested_time_range": dict(time_range) if time_range else None}
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score normalized tracking with the retrospective replay metric."
    )
    parser.add_argument("request", type=Path, help="JSON request path, or '-' for stdin")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if str(args.request) == "-" else args.request.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
        response = score_request(payload)
    except (OSError, json.JSONDecodeError, ReplayAPIError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(response, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
