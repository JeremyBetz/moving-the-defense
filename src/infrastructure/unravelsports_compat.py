"""Non-governed compatibility views for UnravelSports interoperability.

The governed canonical table remains authoritative. This module only exposes
column names familiar to UnravelSports; it does not construct an
``KloppyPolarsDataset`` or infer possession, roles, support, or kinematics.
"""
from __future__ import annotations

import polars as pl

from infrastructure.canonical_tracking import CANONICAL_SCHEMA, validate_chunk


UNRAVEL_REFERENCE_COLUMNS = [
    "period_id",
    "timestamp",
    "frame_id",
    "ball_state",
    "id",
    "x",
    "y",
    "z",
    "team_id",
    "position_name",
    "game_id",
    "ball_owning_team_id",
]


def canonical_to_unravel_reference_view(table: pl.DataFrame) -> pl.DataFrame:
    """Return a loss-aware Unravel-shaped view without changing row membership.

    Canonical identifiers stay namespaced, unsupported entities stay as null rows,
    and provider possession remains null when unavailable. The view intentionally
    omits velocity, acceleration, ball-carrier, and inferred-role columns.
    """
    if table.schema != CANONICAL_SCHEMA:
        raise ValueError("Expected canonical tracking schema")
    validate_chunk(table)
    return table.select(
        pl.col("period").cast(pl.Int64).alias("period_id"),
        pl.duration(microseconds=(pl.col("time_period_s") * 1_000_000).round().cast(pl.Int64)).alias("timestamp"),
        pl.col("frame_id_provider").alias("frame_id"),
        pl.when(pl.col("entity_type") == "ball").then(pl.col("ball_state")).otherwise(None).alias("ball_state"),
        pl.when(pl.col("entity_type") == "ball").then(pl.lit("ball")).otherwise(pl.col("player_key")).alias("id"),
        pl.col("x_m").alias("x"),
        pl.col("y_m").alias("y"),
        pl.col("z_m").alias("z"),
        pl.when(pl.col("entity_type") == "ball").then(pl.lit("ball")).otherwise(pl.col("team_key")).alias("team_id"),
        pl.when(pl.col("is_goalkeeper")).then(pl.lit("GK")).otherwise(None).alias("position_name"),
        pl.col("match_id").alias("game_id"),
        pl.col("possession_team_key").alias("ball_owning_team_id"),
    )
