"""Bounded, structural Metrica Game 2 loader for the tracking replay prototype."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tracking_animation import TrackingClipSpec


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrica_sample_game_2"
SOURCE_FPS = 25.0

DEMO_SPEC = TrackingClipSpec(
    match_id="metrica_sample_game_2",
    period=1,
    anchor_time_s=2336.04,
    start_time_s=2332.04,
    end_time_s=2338.04,
    focal_player_key="metrica:Home:1",
    attacking_team_key="metrica:Home",
    defending_team_key="metrica:Away",
    defender_ranks={
        "metrica:Away:22": 1,
        "metrica:Away:24": 2,
        "metrica:Away:18": 3,
        "metrica:Away:20": 4,
        "metrica:Away:17": 5,
        "metrica:Away:23": 6,
        "metrica:Away:16": 7,
        "metrica:Away:19": 8,
        "metrica:Away:21": 9,
        "metrica:Away:15": 10,
    },
)


def _bounded_rows(path: Path, spec: TrackingClipSpec) -> pd.DataFrame:
    retained: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, skiprows=2, chunksize=10_000):
        q = chunk.loc[
            (chunk["Period"] == spec.period)
            & chunk["Time [s]"].between(spec.start_time_s, spec.end_time_s)
        ]
        if not q.empty:
            retained.append(q)
        if float(chunk["Time [s]"].iloc[-1]) > spec.end_time_s:
            break
    if not retained:
        raise RuntimeError(f"Requested bounded tracking interval is unavailable: {path}")
    return pd.concat(retained, ignore_index=True).sort_values("Frame", kind="mergesort")


def _normalized_team(rows: pd.DataFrame, team: str, spec: TrackingClipSpec) -> list[dict]:
    records: list[dict] = []
    columns = list(rows.columns)
    for index, column in enumerate(columns[:-1]):
        if not str(column).startswith("Player"):
            continue
        number = str(column).replace("Player", "").strip()
        for frame, time_s, x, y in zip(
            rows["Frame"], rows["Time [s]"], rows.iloc[:, index], rows.iloc[:, index + 1], strict=True
        ):
            valid = bool(np.isfinite(x) and np.isfinite(y))
            records.append({
                "match_id": spec.match_id,
                "period": int(spec.period),
                "frame_id_provider": str(int(frame)),
                "time_match_s": float(time_s),
                "entity_type": "player",
                "team_key": f"metrica:{team}",
                "player_key": f"metrica:{team}:{number}",
                "x_m": float(x) * 105.0 - 52.5 if valid else np.nan,
                "y_m": float(y) * 68.0 - 34.0 if valid else np.nan,
                "coordinate_valid": valid,
                "pitch_length_m": 105.0,
                "pitch_width_m": 68.0,
            })
    return records


def load_demo_tracking(
    root: Path = ROOT,
    spec: TrackingClipSpec = DEMO_SPEC,
) -> pd.DataFrame:
    """Load only the approved six-second interval; return coordinates in memory."""
    data = root / "data" / "metrica_sample_game_2"
    home = _bounded_rows(data / "Sample_Game_2_RawTrackingData_Home_Team.csv", spec)
    away = _bounded_rows(data / "Sample_Game_2_RawTrackingData_Away_Team.csv", spec)
    if not home[["Period", "Frame", "Time [s]"]].reset_index(drop=True).equals(
        away[["Period", "Frame", "Time [s]"]].reset_index(drop=True)
    ):
        raise RuntimeError("Home and away bounded frame grids differ")
    records = [*_normalized_team(home, "Home", spec), *_normalized_team(away, "Away", spec)]
    ball_index = list(home.columns).index("Ball")
    for frame, time_s, x, y in zip(
        home["Frame"], home["Time [s]"], home.iloc[:, ball_index], home.iloc[:, ball_index + 1], strict=True
    ):
        valid = bool(np.isfinite(x) and np.isfinite(y))
        records.append({
            "match_id": spec.match_id,
            "period": int(spec.period),
            "frame_id_provider": str(int(frame)),
            "time_match_s": float(time_s),
            "entity_type": "ball",
            "team_key": pd.NA,
            "player_key": pd.NA,
            "x_m": float(x) * 105.0 - 52.5 if valid else np.nan,
            "y_m": float(y) * 68.0 - 34.0 if valid else np.nan,
            "coordinate_valid": valid,
            "pitch_length_m": 105.0,
            "pitch_width_m": 68.0,
        })
    return pd.DataFrame.from_records(records)
