"""Governed provider-agnostic tracking contract for new analyses.

The logical table is long and complete. Implementations may emit consecutive
Polars chunks, but every chunk has the identical explicit schema below.
Historical loaders and scientific measurements remain authoritative for their
committed analyses.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import polars as pl


CONTRACT_VERSION = "1.0.0"
ADAPTER_VERSION = "1.0.0"
ENTITY_TYPES = {"player", "ball"}
SUPPORT_STATES = {
    "observed",
    "provider_coordinate_missing",
    "provider_entity_absent",
    "inactive_off_pitch",
    "ball_absent",
    "not_observed_unspecified",
}
BALL_STATES = {"alive", "dead", "unknown"}

CANONICAL_SCHEMA = pl.Schema(
    {
        "match_id": pl.String,
        "period": pl.UInt8,
        "frame_id_provider": pl.String,
        "time_period_s": pl.Float64,
        "time_match_s": pl.Float64,
        "entity_type": pl.String,
        "team_key": pl.String,
        "player_key": pl.String,
        "is_goalkeeper": pl.Boolean,
        "x_m": pl.Float64,
        "y_m": pl.Float64,
        "z_m": pl.Float64,
        "is_present": pl.Boolean,
        "coordinate_valid": pl.Boolean,
        "support_state": pl.String,
        "ball_state": pl.String,
        "possession_team_key": pl.String,
        "pitch_length_m": pl.Float64,
        "pitch_width_m": pl.Float64,
    }
)


def canonical_frame(rows: list[dict[str, Any]]) -> pl.DataFrame:
    """Construct one schema-stable Polars chunk."""
    return pl.DataFrame(rows, schema=CANONICAL_SCHEMA)


def validate_chunk(table: pl.DataFrame) -> dict[str, Any]:
    """Validate schema and provider-independent row invariants."""
    if table.schema != CANONICAL_SCHEMA:
        raise ValueError(f"Canonical schema mismatch: {table.schema}")
    if table.is_empty():
        raise ValueError("Canonical chunks may not be empty")
    entity_values = set(table.get_column("entity_type").unique().to_list())
    if not entity_values <= ENTITY_TYPES:
        raise ValueError(f"Unexpected entity types: {entity_values - ENTITY_TYPES}")
    support_values = set(table.get_column("support_state").unique().to_list())
    if not support_values <= SUPPORT_STATES:
        raise ValueError(f"Unexpected support states: {support_values - SUPPORT_STATES}")
    ball_values = set(table.get_column("ball_state").drop_nulls().unique().to_list())
    if not ball_values <= BALL_STATES:
        raise ValueError(f"Unexpected ball states: {ball_values - BALL_STATES}")
    invalid_presence = table.filter(~pl.col("is_present") & pl.col("coordinate_valid")).height
    invalid_coordinates = table.filter(
        pl.col("coordinate_valid")
        & (pl.col("x_m").is_null() | pl.col("y_m").is_null())
    ).height
    invalid_player_keys = table.filter(
        (pl.col("entity_type") == "player")
        & (pl.col("team_key").is_null() | pl.col("player_key").is_null())
    ).height
    invalid_ball_keys = table.filter(
        (pl.col("entity_type") == "ball") & pl.col("player_key").is_not_null()
    ).height
    invalid_ball_fields = table.filter(
        (pl.col("entity_type") == "player")
        & (pl.col("ball_state").is_not_null() | pl.col("possession_team_key").is_not_null())
    ).height
    if any((invalid_presence, invalid_coordinates, invalid_player_keys, invalid_ball_keys, invalid_ball_fields)):
        raise ValueError("Canonical row invariants failed")
    if table.get_column("period").min() < 1:
        raise ValueError("Period numbers must be positive")
    if table.filter(pl.col("time_period_s") < 0).height:
        raise ValueError("Period-relative time must be nonnegative")
    if table.filter(pl.col("time_match_s") < 0).height:
        raise ValueError("Match-global time must be nonnegative")
    return {
        "rows": table.height,
        "frames": table.select(["period", "frame_id_provider"]).unique().height,
        "entity_types": sorted(entity_values),
        "support_states": sorted(support_values),
    }


def validate_sequence(chunks: Iterable[pl.DataFrame]) -> dict[str, Any]:
    """Validate cross-chunk clock and identity invariants."""
    rows = 0
    frames = 0
    last_frame_key: tuple[int, str] | None = None
    last_match_time = float("-inf")
    seen_frames: set[tuple[int, str]] = set()
    schema = None
    for chunk in chunks:
        summary = validate_chunk(chunk)
        rows += summary["rows"]
        frame_table = (
            chunk.select(["period", "frame_id_provider", "time_period_s", "time_match_s"])
            .unique(maintain_order=True)
        )
        frames += frame_table.height
        for period, frame_id, time_period, time_match in frame_table.iter_rows():
            key = (int(period), str(frame_id))
            if key in seen_frames:
                raise ValueError(f"Frame appears in more than one chunk: {key}")
            seen_frames.add(key)
            if float(time_match) <= last_match_time:
                raise ValueError(f"Match-global time is not strictly increasing at {key}")
            last_match_time = float(time_match)
            last_frame_key = key
        schema = chunk.schema
    if rows == 0:
        raise ValueError("Canonical sequence contains no rows")
    return {
        "contract_version": CONTRACT_VERSION,
        "rows": rows,
        "frames": frames,
        "last_frame_key": list(last_frame_key) if last_frame_key else None,
        "last_match_time_s": last_match_time,
        "schema": {name: str(dtype) for name, dtype in schema.items()} if schema else {},
    }


def canonical_schema_dict() -> dict[str, str]:
    return {name: str(dtype) for name, dtype in CANONICAL_SCHEMA.items()}
