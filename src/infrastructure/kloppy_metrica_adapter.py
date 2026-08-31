"""Experimental Kloppy adapter for Metrica Sample Game 1.

The adapter restores the raw Metrica coordinate convention used by the
validated Moving the Defense pipelines. Kloppy 3.19.0 flips Metrica's y-axis
while loading CSV tracking data; project_y = 1 - kloppy_y reverses that
normalization explicitly. No interpolation, possession inference, kinematic
derivation, or scientific measurement is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterator

import kloppy
from kloppy import metrica
import numpy as np
import pandas as pd

from infrastructure.canonical_tracking import (
    ADAPTER_VERSION,
    CONTRACT_VERSION,
    canonical_frame,
)


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_team_key(team_id: str) -> str:
    return f"metrica:{team_id}"


def canonical_player_key(team_id: str, player_id: str) -> str:
    return f"metrica:{team_id}:{player_id}"


def iter_canonical_polars_chunks(
    dataset,
    provider_index: pd.DataFrame,
    match_id: str = "metrica:sample-game-1",
    frames_per_chunk: int = 1000,
):
    """Yield governed canonical chunks in a fixed centred pitch frame."""
    lookup = _provider_index_lookup(provider_index)
    players = roster(dataset)
    rows: list[dict] = []
    for frame_count, frame in enumerate(dataset.frames, start=1):
        period, provider_time_s = lookup[int(frame.frame_id)]
        common = {
            "match_id": match_id,
            "period": period,
            "frame_id_provider": str(int(frame.frame_id)),
            "time_period_s": float(frame.timestamp.total_seconds()),
            "time_match_s": provider_time_s,
            "pitch_length_m": PITCH_LENGTH_M,
            "pitch_width_m": PITCH_WIDTH_M,
        }
        for player, team_id, number in players:
            point = frame.players_coordinates.get(player)
            valid = point is not None and np.isfinite(point.x) and np.isfinite(point.y)
            rows.append(
                {
                    **common,
                    "entity_type": "player",
                    "team_key": canonical_team_key(team_id),
                    "player_key": canonical_player_key(team_id, number),
                    "is_goalkeeper": number == GOALKEEPER_IDS[team_id],
                    "x_m": float(point.x * PITCH_LENGTH_M - PITCH_LENGTH_M / 2) if valid else None,
                    "y_m": float(point.y * PITCH_WIDTH_M - PITCH_WIDTH_M / 2) if valid else None,
                    "z_m": None,
                    "is_present": point is not None,
                    "coordinate_valid": bool(valid),
                    "support_state": "observed" if valid else "not_observed_unspecified",
                    "ball_state": None,
                    "possession_team_key": None,
                }
            )
        ball = frame.ball_coordinates
        ball_valid = ball is not None and np.isfinite(ball.x) and np.isfinite(ball.y)
        ball_state = str(frame.ball_state.value) if frame.ball_state is not None else "unknown"
        possession = (
            canonical_team_key(team_name(frame.ball_owning_team.team_id))
            if frame.ball_owning_team is not None
            else None
        )
        rows.append(
            {
                **common,
                "entity_type": "ball",
                "team_key": None,
                "player_key": None,
                "is_goalkeeper": False,
                "x_m": float(ball.x * PITCH_LENGTH_M - PITCH_LENGTH_M / 2) if ball_valid else None,
                "y_m": float(ball.y * PITCH_WIDTH_M - PITCH_WIDTH_M / 2) if ball_valid else None,
                "z_m": None,
                "is_present": ball is not None,
                "coordinate_valid": bool(ball_valid),
                "support_state": "observed" if ball_valid else "ball_absent",
                "ball_state": ball_state if ball_valid else "unknown",
                "possession_team_key": possession,
            }
        )
        if frame_count % frames_per_chunk == 0:
            yield canonical_frame(rows)
            rows = []
    if rows:
        yield canonical_frame(rows)


def canonical_provenance(dataset, home_path: Path, away_path: Path) -> dict:
    """Return the governed provenance sidecar for canonical Metrica output."""
    team_map = {
        team.team_id: canonical_team_key(team_name(team.team_id))
        for team in dataset.metadata.teams
    }
    player_map = {
        player.player_id: canonical_player_key(team_id, number)
        for player, team_id, number in roster(dataset)
    }
    return {
        "contract_version": CONTRACT_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "provider": "metrica",
        "provider_match_id": "Sample Game 1",
        "canonical_match_id": "metrica:sample-game-1",
        "kloppy_version": str(kloppy.__version__),
        "source_files": [
            {"path": str(path.relative_to(path.parents[2])), "sha256": _sha256(path)}
            for path in (home_path, away_path)
        ],
        "source_coordinate_system": "normalized x left-to-right, y top-to-bottom",
        "canonical_coordinate_system": "metres, pitch centre origin, +x right, +y top, fixed pitch frame",
        "coordinate_transform": [
            "Kloppy 3.19.0 parses Metrica y bottom-to-top",
            "x_m = kloppy_x * 105 - 52.5",
            "y_m = kloppy_y * 68 - 34",
        ],
        "pitch_m": [PITCH_LENGTH_M, PITCH_WIDTH_M],
        "provider_raw_timestamp_available": False,
        "provider_frame_id_available": True,
        "time_period_rule": "Kloppy period-relative timestamp",
        "time_match_rule": "raw Metrica Time [s] preserved from provider frame-index sidecar",
        "team_id_map_provider_to_canonical": team_map,
        "player_id_map_provider_to_canonical": player_map,
        "goalkeeper_source": "frozen project metadata: Home 11, Away 25",
        "ball_object_id_provider": None,
        "ball_state_available": False,
        "possession_team_available": False,
        "support_rule": "Kloppy coordinate-object presence; unavailable reason retained as not_observed_unspecified",
        "orientation_metadata": str(dataset.metadata.orientation.value),
        "coordinates_attacking_direction_normalized": False,
        "interpolation_used": False,
        "transformation_log": ["load via Kloppy", "canonical fixed-pitch coordinate transform", "explicit roster null rows"],
    }
