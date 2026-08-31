"""Experimental Kloppy adapter for one IDSSE/Sportec tracking match.

Sportec coordinates are retained in the provider's centred 105 x 68 metre
system because that is the validated Phase 4C representation. Absolute UTC
timestamps are restored from a raw ball-frame sidecar because Kloppy 3.19.0
exposes a frame-derived period-relative clock. No interpolation, tactical
inference, smoothing, or scientific measurement is performed here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
import xml.etree.ElementTree as ET

import kloppy
from kloppy import sportec
from kloppy.domain import PositionType
import numpy as np
import pandas as pd

from infrastructure.kloppy_metrica_adapter import CANONICAL_COLUMNS


PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
FRAME_RATE_HZ = 25
PERIOD_LABELS = {1: "firstHalf", 2: "secondHalf"}
IDSSE_CANONICAL_COLUMNS = CANONICAL_COLUMNS + [
    "provider_timestamp_ns",
    "period_label",
    "ball_state",
    "ball_owning_team_id",
]


@dataclass(frozen=True)
class IDSSEProvenance:
    provider: str
    provider_format: str
    provider_match_id: str
    kloppy_version: str
    frame_rate_hz: int
    coordinate_system: str
    orientation: str
    pitch_length_m: float
    pitch_width_m: float
    timestamp_rule: str
    goalkeeper_rule: str
    interpolation_used: bool
    tactical_fields_inferred: bool


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_timestamp_ns(value: str) -> int:
    parsed = datetime.fromisoformat(value).astimezone(timezone.utc)
    return int(round(parsed.timestamp() * 1_000_000_000))


def idsse_paths(root: Path, match_id: str) -> tuple[Path, Path, Path]:
    raw = root / "data" / "idsse_raw"
    patterns = (
        f"*matchinformation*{match_id}.xml",
        f"*events_raw*{match_id}.xml",
        f"*positions_raw_observed*{match_id}.xml",
    )
    found = []
    for pattern in patterns:
        candidates = list(raw.glob(pattern))
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one IDSSE file for {pattern}, found {len(candidates)}")
        found.append(candidates[0])
    return tuple(found)  # type: ignore[return-value]


def load_dataset(metadata_path: Path, tracking_path: Path, limit: int | None = None):
    """Load Sportec tracking in its native centred-metre coordinate system."""
    with metadata_path.open("rb") as metadata, tracking_path.open("rb") as tracking:
        return sportec.load_tracking(
            meta_data=metadata,
            raw_data=tracking,
            limit=limit,
            coordinates="sportec",
            only_alive=False,
        )


def read_ball_frame_sidecar(tracking_path: Path) -> pd.DataFrame:
    """Read raw absolute time and provider ball-state fields without coordinates."""
    rows: list[dict] = []
    current_period: str | None = None
    current_ball_object_id: str | None = None
    in_ball = False
    for event, element in ET.iterparse(tracking_path, events=("start", "end")):
        tag = local(element.tag)
        if event == "start" and tag == "FrameSet":
            in_ball = element.attrib.get("TeamId") == "BALL"
            current_period = element.attrib.get("GameSection") if in_ball else None
            current_ball_object_id = element.attrib.get("PersonId") if in_ball else None
        elif event == "end" and tag == "Frame":
            if in_ball and current_period is not None:
                rows.append(
                    {
                        "period_label": current_period,
                        "frame_id": int(element.attrib["N"]),
                        "provider_timestamp_ns": parse_timestamp_ns(element.attrib["T"]),
                        "provider_ball_state": "alive" if int(element.attrib.get("BallStatus", "0")) == 1 else "dead",
                        "provider_ball_possession_code": int(element.attrib.get("BallPossession", "0")),
                        "provider_ball_object_id": current_ball_object_id,
                    }
                )
            element.clear()
        elif event == "end" and tag == "FrameSet":
            in_ball = False
            current_period = None
            current_ball_object_id = None
            element.clear()
    result = pd.DataFrame(rows)
    if result[["period_label", "frame_id"]].duplicated().any():
        raise ValueError("IDSSE ball sidecar contains duplicate period/frame keys")
    return result


def roster(dataset) -> list[tuple[object, str, bool]]:
    result = []
    for team in dataset.metadata.teams:
        for player in team.players:
            result.append(
                (
                    player,
                    team.team_id,
                    player.starting_position == PositionType.Goalkeeper,
                )
            )
    return result


def provenance(dataset) -> IDSSEProvenance:
    dimensions = dataset.metadata.pitch_dimensions
    return IDSSEProvenance(
        provider=str(dataset.metadata.provider.value),
        provider_format="DFL/Sportec XML (match information + raw observed positions)",
        provider_match_id=str(dataset.metadata.game_id),
        kloppy_version=str(kloppy.__version__),
        frame_rate_hz=int(dataset.metadata.frame_rate),
        coordinate_system=dataset.metadata.coordinate_system.__class__.__name__,
        orientation=str(dataset.metadata.orientation.value),
        pitch_length_m=float(dimensions.pitch_length),
        pitch_width_m=float(dimensions.pitch_width),
        timestamp_rule="raw UTC nanoseconds from provider ball-frame sidecar; Kloppy time retained separately",
        goalkeeper_rule="Kloppy starting_position == Goalkeeper, checked against frozen provider metadata",
        interpolation_used=False,
        tactical_fields_inferred=False,
    )


def _sidecar_lookup(sidecar: pd.DataFrame) -> dict[tuple[str, int], dict]:
    return {
        (row.period_label, int(row.frame_id)): row._asdict()
        for row in sidecar.itertuples(index=False)
    }


def iter_long_chunks(dataset, sidecar: pd.DataFrame, frames_per_chunk: int = 1000) -> Iterator[pd.DataFrame]:
    """Yield the shared canonical core plus explicit IDSSE provenance fields."""
    lookup = _sidecar_lookup(sidecar)
    players = roster(dataset)
    rows: list[dict] = []
    for frame_count, frame in enumerate(dataset.frames, start=1):
        period = int(frame.period.id)
        period_label = PERIOD_LABELS[period]
        raw = lookup[(period_label, int(frame.frame_id))]
        common = {
            "period": period,
            "frame_id": int(frame.frame_id),
            "provider_time_s": raw["provider_timestamp_ns"] / 1e9,
            "kloppy_period_time_s": float(frame.timestamp.total_seconds()),
            "provider_timestamp_ns": int(raw["provider_timestamp_ns"]),
            "period_label": period_label,
            "ball_state": str(frame.ball_state.value),
            "ball_owning_team_id": frame.ball_owning_team.team_id if frame.ball_owning_team else pd.NA,
        }
        for player, team_id, is_goalkeeper in players:
            point = frame.players_coordinates.get(player)
            x_m = float(point.x) if point is not None else np.nan
            y_m = float(point.y) if point is not None else np.nan
            rows.append(
                {
                    **common,
                    "object_type": "player",
                    "team_id": team_id,
                    "player_id": player.player_id,
                    "kloppy_player_id": player.player_id,
                    "is_goalkeeper": is_goalkeeper,
                    "observed": point is not None,
                    "x_norm": (x_m + PITCH_LENGTH_M / 2) / PITCH_LENGTH_M,
                    "y_norm": (y_m + PITCH_WIDTH_M / 2) / PITCH_WIDTH_M,
                    "x_m": x_m,
                    "y_m": y_m,
                }
            )
        ball = frame.ball_coordinates
        ball_x = float(ball.x) if ball is not None else np.nan
        ball_y = float(ball.y) if ball is not None else np.nan
        rows.append(
            {
                **common,
                "object_type": "ball",
                "team_id": pd.NA,
                "player_id": pd.NA,
                "kloppy_player_id": pd.NA,
                "is_goalkeeper": False,
                "observed": ball is not None,
                "x_norm": (ball_x + PITCH_LENGTH_M / 2) / PITCH_LENGTH_M,
                "y_norm": (ball_y + PITCH_WIDTH_M / 2) / PITCH_WIDTH_M,
                "x_m": ball_x,
                "y_m": ball_y,
            }
        )
        if frame_count % frames_per_chunk == 0:
            yield pd.DataFrame(rows, columns=IDSSE_CANONICAL_COLUMNS)
            rows = []
    if rows:
        yield pd.DataFrame(rows, columns=IDSSE_CANONICAL_COLUMNS)


def to_phase4c_tracking(dataset, sidecar: pd.DataFrame) -> dict:
    """Build a Phase 4C-compatible view for independent scientific comparison."""
    lookup = _sidecar_lookup(sidecar)
    players = roster(dataset)
    result: dict = {"pitch_sizes": [[PITCH_LENGTH_M, PITCH_WIDTH_M]]}
    for period_id, period_label in PERIOD_LABELS.items():
        frames = [frame for frame in dataset.frames if int(frame.period.id) == period_id]
        frame_ids = np.asarray([int(frame.frame_id) for frame in frames], dtype=np.int32)
        time_ns = np.asarray(
            [int(lookup[(period_label, int(frame.frame_id))]["provider_timestamp_ns"]) for frame in frames],
            dtype=np.int64,
        )
        entities = []
        for player, team_id, _ in players:
            x = np.full(len(frames), np.nan, dtype=float)
            y = np.full(len(frames), np.nan, dtype=float)
            for index, frame in enumerate(frames):
                point = frame.players_coordinates.get(player)
                if point is not None:
                    x[index], y[index] = float(point.x), float(point.y)
            entities.append(
                {
                    "team_id": team_id,
                    "person_id": player.player_id,
                    "x": x,
                    "y": y,
                    "valid": np.isfinite(x) & np.isfinite(y),
                }
            )
        ball_x = np.asarray([float(frame.ball_coordinates.x) for frame in frames], dtype=float)
        ball_y = np.asarray([float(frame.ball_coordinates.y) for frame in frames], dtype=float)
        entities.append(
            {
                "team_id": "BALL",
                "person_id": "ball",
                "x": ball_x,
                "y": ball_y,
                "valid": np.isfinite(ball_x) & np.isfinite(ball_y),
            }
        )
        result[period_label] = {"frame_n": frame_ids, "time_ns": time_ns, "entities": entities}
    return result


def provenance_dict(dataset) -> dict:
    return asdict(provenance(dataset))
