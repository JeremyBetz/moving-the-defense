"""Experimental Kloppy adapter for Metrica Sample Game 1.

The adapter restores the raw Metrica coordinate convention used by the
validated Moving the Defense pipelines. Kloppy 3.19.0 flips Metrica's y-axis
while loading CSV tracking data; project_y = 1 - kloppy_y reverses that
normalization explicitly. No interpolation, possession inference, kinematic
derivation, or scientific measurement is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import kloppy
from kloppy import metrica
import numpy as np
import pandas as pd


PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
FRAME_RATE_HZ = 25
GOALKEEPER_IDS = {"Home": "11", "Away": "25"}

CANONICAL_COLUMNS = [
    "period",
    "frame_id",
    "provider_time_s",
    "kloppy_period_time_s",
    "object_type",
    "team_id",
    "player_id",
    "kloppy_player_id",
    "is_goalkeeper",
    "observed",
    "x_norm",
    "y_norm",
    "x_m",
    "y_m",
]


@dataclass(frozen=True)
class AdapterProvenance:
    provider: str
    kloppy_version: str
    frame_rate_hz: int
    source_coordinate_system: str
    kloppy_coordinate_system: str
    kloppy_orientation: str
    project_pitch_length_m: float
    project_pitch_width_m: float
    y_adapter_rule: str
    goalkeeper_source: str
    possession_inferred: bool
    interpolation_used: bool


def game1_paths(root: Path) -> tuple[Path, Path]:
    data = root / "data" / "metrica_sample_game_1"
    return (
        data / "Sample_Game_1_RawTrackingData_Home_Team.csv",
        data / "Sample_Game_1_RawTrackingData_Away_Team.csv",
    )


def read_provider_frame_index(home_path: Path) -> pd.DataFrame:
    """Read only the provider's structural frame/time sidecar.

    Kloppy retains frame IDs and period-relative time but not Metrica's global
    `Time [s]` column as a separate raw field. Reading the first three columns
    preserves that provider value without duplicating coordinate parsing.
    """
    index = pd.read_csv(
        home_path,
        skiprows=3,
        header=None,
        usecols=[0, 1, 2],
        names=["period", "frame_id", "provider_time_s"],
    )
    return index.astype({"period": "int64", "frame_id": "int64", "provider_time_s": "float64"})


def load_dataset(home_path: Path, away_path: Path, limit: int | None = None):
    """Load local CSVs through Kloppy in its explicit Metrica coordinate system."""
    with home_path.open("rb") as home_data, away_path.open("rb") as away_data:
        return metrica.load_tracking_csv(
            home_data=home_data,
            away_data=away_data,
            limit=limit,
            coordinates="metrica",
        )


def team_name(kloppy_team_id: str) -> str:
    mapping = {"home": "Home", "away": "Away"}
    if kloppy_team_id not in mapping:
        raise ValueError(f"Unexpected Kloppy Metrica team ID: {kloppy_team_id}")
    return mapping[kloppy_team_id]


def player_number(player) -> str:
    if player.jersey_no is None:
        raise ValueError(f"Player {player.player_id} lacks a Metrica jersey number")
    return str(int(player.jersey_no))


def project_coordinates(point) -> tuple[float, float]:
    """Convert a Kloppy Metrica point back to project raw-normalized axes."""
    if point is None:
        return np.nan, np.nan
    return float(point.x), float(1.0 - point.y)


def provenance(dataset) -> AdapterProvenance:
    return AdapterProvenance(
        provider=str(dataset.metadata.provider.value),
        kloppy_version=str(kloppy.__version__),
        frame_rate_hz=int(dataset.metadata.frame_rate),
        source_coordinate_system="Metrica normalized: x left-to-right, y top-to-bottom",
        kloppy_coordinate_system=dataset.metadata.coordinate_system.__class__.__name__,
        kloppy_orientation=str(dataset.metadata.orientation.value),
        project_pitch_length_m=PITCH_LENGTH_M,
        project_pitch_width_m=PITCH_WIDTH_M,
        y_adapter_rule="project_y_norm = 1 - kloppy_y_norm",
        goalkeeper_source="Moving the Defense frozen Metrica identity mapping",
        possession_inferred=False,
        interpolation_used=False,
    )


def roster(dataset) -> list[tuple[object, str, str]]:
    rows = []
    for team in dataset.metadata.teams:
        project_team = team_name(team.team_id)
        for player in team.players:
            rows.append((player, project_team, player_number(player)))
    return rows


def _provider_index_lookup(provider_index: pd.DataFrame) -> dict[int, tuple[int, float]]:
    if provider_index["frame_id"].duplicated().any():
        raise ValueError("Provider frame index contains duplicate frame IDs")
    return {
        int(row.frame_id): (int(row.period), float(row.provider_time_s))
        for row in provider_index.itertuples(index=False)
    }


def iter_long_chunks(
    dataset,
    provider_index: pd.DataFrame,
    frames_per_chunk: int = 1000,
) -> Iterator[pd.DataFrame]:
    """Yield canonical long rows, including explicit missing player/ball rows."""
    lookup = _provider_index_lookup(provider_index)
    players = roster(dataset)
    rows: list[dict] = []
    for frame_count, frame in enumerate(dataset.frames, start=1):
        source_period, provider_time_s = lookup[int(frame.frame_id)]
        if int(frame.period.id) != source_period:
            raise ValueError(f"Period mismatch at frame {frame.frame_id}")
        common = {
            "period": source_period,
            "frame_id": int(frame.frame_id),
            "provider_time_s": provider_time_s,
            "kloppy_period_time_s": float(frame.timestamp.total_seconds()),
        }
        for player, project_team, number in players:
            point = frame.players_coordinates.get(player)
            x_norm, y_norm = project_coordinates(point)
            rows.append(
                {
                    **common,
                    "object_type": "player",
                    "team_id": project_team,
                    "player_id": number,
                    "kloppy_player_id": player.player_id,
                    "is_goalkeeper": number == GOALKEEPER_IDS[project_team],
                    "observed": point is not None,
                    "x_norm": x_norm,
                    "y_norm": y_norm,
                    "x_m": x_norm * PITCH_LENGTH_M,
                    "y_m": y_norm * PITCH_WIDTH_M,
                }
            )
        ball_x, ball_y = project_coordinates(frame.ball_coordinates)
        rows.append(
            {
                **common,
                "object_type": "ball",
                "team_id": pd.NA,
                "player_id": pd.NA,
                "kloppy_player_id": pd.NA,
                "is_goalkeeper": False,
                "observed": frame.ball_coordinates is not None,
                "x_norm": ball_x,
                "y_norm": ball_y,
                "x_m": ball_x * PITCH_LENGTH_M,
                "y_m": ball_y * PITCH_WIDTH_M,
            }
        )
        if frame_count % frames_per_chunk == 0:
            yield pd.DataFrame(rows, columns=CANONICAL_COLUMNS)
            rows = []
    if rows:
        yield pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def to_long_dataframe(dataset, provider_index: pd.DataFrame) -> pd.DataFrame:
    """Materialize the canonical table; intended for bounded tests and samples."""
    chunks = list(iter_long_chunks(dataset, provider_index))
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=CANONICAL_COLUMNS)


def to_project_wide(dataset, provider_index: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Create a compatibility view for existing project-owned measurements."""
    lookup = _provider_index_lookup(provider_index)
    players = roster(dataset)
    ids = {
        team: [number for _, player_team, number in players if player_team == team]
        for team in ("Home", "Away")
    }
    rows: list[dict] = []
    for frame in dataset.frames:
        source_period, provider_time_s = lookup[int(frame.frame_id)]
        row: dict[str, float | int] = {
            "Period": source_period,
            "Frame": int(frame.frame_id),
            "Time [s]": provider_time_s,
        }
        for player, project_team, number in players:
            x_norm, y_norm = project_coordinates(frame.players_coordinates.get(player))
            row[f"{project_team}_{number}_x"] = x_norm
            row[f"{project_team}_{number}_y"] = y_norm
        ball_x, ball_y = project_coordinates(frame.ball_coordinates)
        for project_team in ("Home", "Away"):
            row[f"{project_team}_ball_x"] = ball_x
            row[f"{project_team}_ball_y"] = ball_y
        rows.append(row)
    return pd.DataFrame(rows), ids
