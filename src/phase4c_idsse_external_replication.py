"""Frozen Phase 4C IDSSE external replication.

The ``mapping`` stage performs provider mapping and support checks only.  It
does not construct focal-relative coordinates or outcomes.  The ``execute``
stage is intentionally unavailable until the mapping audit has passed and the
implementation has been frozen in the repository documentation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config" / "phase4c_external_replication_protocol.json"
IMPLEMENTATION_PATH = ROOT / "config" / "phase4c_idsse_implementation.json"
FIGURE_DIR = ROOT / "figures" / "phase4c"


MATCH_IDS = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
PERIODS = ("firstHalf", "secondHalf")
RESTART_TAGS = {
    "KickOff",
    "ThrowIn",
    "GoalKick",
    "FreeKick",
    "CornerKick",
    "Penalty",
    "RefereeBall",
    "Offside",
    "FinalWhistle",
}
BALL_ACTION_TAGS = {"Play", "OtherBallAction", "ShotAtGoal", "BallClaiming"}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def iso_ns(value: datetime) -> int:
    return int(round(value.timestamp() * 1_000_000_000))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_file(raw_dir: Path, kind: str, match_id: str) -> Path:
    markers = {
        "metadata": "matchinformation",
        "events": "events_raw",
        "tracking": "positions_raw_observed",
    }
    paths = list(raw_dir.glob(f"*{markers[kind]}*{match_id}.xml"))
    if len(paths) != 1:
        raise RuntimeError(f"Expected one {kind} file for {match_id}, found {len(paths)}")
    return paths[0]


@dataclass(frozen=True)
class Player:
    player_id: str
    team_id: str
    position: str
    goalkeeper: bool


def read_metadata(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    general = next(node for node in root.iter() if local(node.tag) == "General")
    environment = next(node for node in root.iter() if local(node.tag) == "Environment")
    team_by_player: dict[str, str] = {}
    players: dict[str, Player] = {}
    for team in (node for node in root.iter() if local(node.tag) == "Team"):
        team_id = team.attrib["TeamId"]
        for node in team.iter():
            if local(node.tag) != "Player":
                continue
            player_id = node.attrib["PersonId"]
            position = node.attrib.get("PlayingPosition", "")
            players[player_id] = Player(player_id, team_id, position, position == "TW")
            team_by_player[player_id] = team_id
    return {
        "match_id": general.attrib["MatchId"].removeprefix("DFL-MAT-"),
        "provider_match_id": general.attrib["MatchId"],
        "home_team_id": general.attrib["HomeTeamId"],
        "away_team_id": general.attrib["GuestTeamId"],
        "home_team_name": general.attrib["HomeTeamName"],
        "away_team_name": general.attrib["GuestTeamName"],
        "pitch_x_m": float(environment.attrib["PitchX"]),
        "pitch_y_m": float(environment.attrib["PitchY"]),
        "players": players,
        "team_by_player": team_by_player,
    }


def infer_event_team(tag: str, attributes: dict[str, str]) -> str | None:
    if tag == "TacklingGame":
        changed = attributes.get("PossessionChange", "false").lower() == "true"
        return attributes.get("WinnerTeam" if changed else "LoserTeam")
    if tag == "Foul":
        return None
    return attributes.get("Team")


def read_events(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    kickoffs: dict[str, datetime] = {}
    substitution_rows: list[dict[str, Any]] = []
    restart_counts: Counter[str] = Counter()
    for _, element in ET.iterparse(path, events=("end",)):
        if local(element.tag) != "Event":
            continue
        timestamp = parse_time(element.attrib["EventTime"])
        children = list(element)
        for child in children:
            tag = local(child.tag)
            attrs = dict(child.attrib)
            if tag == "KickOff" and attrs.get("GameSection") in PERIODS:
                kickoffs[attrs["GameSection"]] = timestamp
            if tag == "Substitution":
                substitution_rows.append({"timestamp": timestamp.isoformat(), **attrs})
            if tag in RESTART_TAGS:
                restart_counts[tag] += 1

            team = infer_event_team(tag, attrs)
            open_state: bool | None = None
            state_event = False
            if tag in RESTART_TAGS:
                open_state = False
                state_event = True
            elif tag == "Play":
                open_state = attrs.get("FromOpenPlay", "false").lower() == "true"
                state_event = True
            elif tag in BALL_ACTION_TAGS or tag == "TacklingGame":
                state_event = team is not None
            if state_event:
                rows.append(
                    {
                        "time_ns": iso_ns(timestamp),
                        "event_id": element.attrib.get("EventId", ""),
                        "tag": tag,
                        "team_id": team,
                        "open_state": open_state,
                    }
                )
        element.clear()
    if set(kickoffs) != set(PERIODS):
        raise RuntimeError(f"Missing period kickoff(s) in {path.name}: {kickoffs}")
    rows.sort(key=lambda row: (row["time_ns"], row["event_id"], row["tag"]))
    return {
        "state_events": rows,
        "kickoffs": kickoffs,
        "substitutions": substitution_rows,
        "restart_counts": dict(restart_counts),
    }


def read_tracking(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Read raw provider coordinates without constructing relational outcomes."""
    blocks: dict[str, list[dict[str, Any]]] = {period: [] for period in PERIODS}
    pitch_sizes: set[tuple[float, float]] = set()
    context = ET.iterparse(path, events=("start", "end"))
    current: dict[str, Any] | None = None
    frame_n: list[int] = []
    frame_t: list[int] = []
    frame_x: list[float] = []
    frame_y: list[float] = []
    frame_m: list[int] = []
    for event, element in context:
        tag = local(element.tag)
        if event == "start" and tag == "PitchSize":
            pitch_sizes.add((float(element.attrib["X"]), float(element.attrib["Y"])))
        elif event == "start" and tag == "FrameSet":
            current = dict(element.attrib)
            frame_n, frame_t, frame_x, frame_y, frame_m = [], [], [], [], []
        elif event == "end" and tag == "Frame" and current is not None:
            frame_n.append(int(element.attrib["N"]))
            frame_t.append(iso_ns(parse_time(element.attrib["T"])))
            frame_x.append(float(element.attrib["X"]))
            frame_y.append(float(element.attrib["Y"]))
            frame_m.append(int(element.attrib.get("M", "1")))
            element.clear()
        elif event == "end" and tag == "FrameSet" and current is not None:
            period = current["GameSection"]
            if period in blocks:
                blocks[period].append(
                    {
                        **current,
                        "n": np.asarray(frame_n, dtype=np.int32),
                        "t": np.asarray(frame_t, dtype=np.int64),
                        "x": np.asarray(frame_x, dtype=np.float32),
                        "y": np.asarray(frame_y, dtype=np.float32),
                        "m": np.asarray(frame_m, dtype=np.int8),
                    }
                )
            current = None
            element.clear()

    expected_pitch = (metadata["pitch_x_m"], metadata["pitch_y_m"])
    if pitch_sizes != {expected_pitch}:
        raise RuntimeError(f"Pitch metadata disagreement in {path.name}: {pitch_sizes} vs {expected_pitch}")

    result: dict[str, Any] = {"pitch_sizes": sorted(pitch_sizes)}
    for period, period_blocks in blocks.items():
        if not period_blocks:
            raise RuntimeError(f"No {period} tracking in {path.name}")
        all_n = np.unique(np.concatenate([block["n"] for block in period_blocks]))
        all_n.sort()
        index = {int(n): i for i, n in enumerate(all_n)}
        time_ns = np.full(len(all_n), -1, dtype=np.int64)
        entities: list[dict[str, Any]] = []
        for block in period_blocks:
            idx = np.fromiter((index[int(n)] for n in block["n"]), dtype=np.int64, count=len(block["n"]))
            populated = time_ns[idx] >= 0
            if populated.any() and not np.array_equal(time_ns[idx][populated], block["t"][populated]):
                raise RuntimeError(f"Timestamp disagreement at shared frames in {path.name} {period}")
            time_ns[idx] = block["t"]
            x = np.full(len(all_n), np.nan, dtype=np.float32)
            y = np.full(len(all_n), np.nan, dtype=np.float32)
            valid = np.zeros(len(all_n), dtype=bool)
            x[idx], y[idx] = block["x"], block["y"]
            # Provider ``M`` is the match-minute field (it advances from 1 onward),
            # not a measurement-quality flag. Presence plus finite X/Y defines a
            # usable raw observation; absent frames remain NaN/False.
            valid[idx] = np.isfinite(block["x"]) & np.isfinite(block["y"])
            entities.append(
                {
                    "team_id": block["TeamId"],
                    "person_id": block["PersonId"],
                    "x": x,
                    "y": y,
                    "valid": valid,
                }
            )
        if (time_ns < 0).any():
            raise RuntimeError(f"Frames without timestamps in {path.name} {period}")
        result[period] = {"frame_n": all_n, "time_ns": time_ns, "entities": entities}
    return result


def save_tracking_cache(cache_path: Path, tracking: dict[str, Any]) -> None:
    arrays: dict[str, np.ndarray] = {}
    manifest: dict[str, Any] = {"pitch_sizes": tracking["pitch_sizes"], "periods": {}}
    for period in PERIODS:
        data = tracking[period]
        arrays[f"{period}_frame_n"] = data["frame_n"]
        arrays[f"{period}_time_ns"] = data["time_ns"]
        period_manifest = []
        for i, entity in enumerate(data["entities"]):
            arrays[f"{period}_{i}_x"] = entity["x"]
            arrays[f"{period}_{i}_y"] = entity["y"]
            arrays[f"{period}_{i}_valid"] = entity["valid"]
            period_manifest.append({"team_id": entity["team_id"], "person_id": entity["person_id"]})
        manifest["periods"][period] = period_manifest
    arrays["manifest"] = np.asarray(json.dumps(manifest))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, **arrays)


def load_tracking_cache(cache_path: Path) -> dict[str, Any]:
    with np.load(cache_path, allow_pickle=False) as payload:
        manifest = json.loads(str(payload["manifest"]))
        result: dict[str, Any] = {"pitch_sizes": manifest["pitch_sizes"]}
        for period in PERIODS:
            entities = []
            for i, entity in enumerate(manifest["periods"][period]):
                x = payload[f"{period}_{i}_x"].copy()
                y = payload[f"{period}_{i}_y"].copy()
                entities.append(
                    {
                        **entity,
                        "x": x,
                        "y": y,
                        "valid": np.isfinite(x) & np.isfinite(y),
                    }
                )
            result[period] = {
                "frame_n": payload[f"{period}_frame_n"].copy(),
                "time_ns": payload[f"{period}_time_ns"].copy(),
                "entities": entities,
            }
    return result


def event_state_at_intervals(
    state_events: list[dict[str, Any]], starts_ns: np.ndarray, ends_ns: np.ndarray
) -> tuple[list[str | None], np.ndarray]:
    """Carry the latest event-defined possession/open-play state through time."""
    event_times = np.asarray([row["time_ns"] for row in state_events], dtype=np.int64)
    teams: list[str | None] = []
    valid_open = np.zeros(len(starts_ns), dtype=bool)
    current_team: str | None = None
    current_open = False
    cursor = 0
    for i, (start, end) in enumerate(zip(starts_ns, ends_ns, strict=True)):
        while cursor < len(state_events) and event_times[cursor] <= start:
            row = state_events[cursor]
            if row["team_id"] is not None:
                current_team = row["team_id"]
            if row["open_state"] is not None:
                current_open = bool(row["open_state"])
            cursor += 1
        team = current_team
        open_state = current_open
        j = cursor
        stable = team is not None and open_state
        while j < len(state_events) and event_times[j] < end:
            row = state_events[j]
            next_team = row["team_id"] if row["team_id"] is not None else team
            next_open = row["open_state"] if row["open_state"] is not None else open_state
            if next_team != team or not next_open:
                stable = False
            team, open_state = next_team, bool(next_open)
            j += 1
        teams.append(current_team if stable else None)
        valid_open[i] = stable
        while cursor < j:
            row = state_events[cursor]
            if row["team_id"] is not None:
                current_team = row["team_id"]
            if row["open_state"] is not None:
                current_open = bool(row["open_state"])
            cursor += 1
    return teams, valid_open


def period_interval_candidates(period_data: dict[str, Any], kickoff: datetime, seconds: int = 5) -> list[np.ndarray]:
    time_ns = period_data["time_ns"]
    kickoff_ns = iso_ns(kickoff)
    first_offset = max(0.0, (int(time_ns[0]) - kickoff_ns) / 1e9)
    grid = math.ceil(first_offset / seconds) * seconds
    final_offset = (int(time_ns[-1]) - kickoff_ns) / 1e9
    candidates: list[np.ndarray] = []
    while grid + seconds <= final_offset + 1e-9:
        start_ns = kickoff_ns + int(grid * 1e9)
        end_ns = start_ns + int(seconds * 1e9)
        idx = np.flatnonzero((time_ns >= start_ns) & (time_ns < end_ns))
        if len(idx) == seconds * 25 and np.all(np.diff(time_ns[idx]) == 40_000_000):
            candidates.append(idx)
        grid += seconds
    return candidates


def support_for_match(metadata: dict[str, Any], events: dict[str, Any], tracking: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    interval_rows: list[dict[str, Any]] = []
    teams = {metadata["home_team_id"], metadata["away_team_id"]}
    for period in PERIODS:
        data = tracking[period]
        candidates = period_interval_candidates(data, events["kickoffs"][period], 5)
        starts = np.asarray([data["time_ns"][idx[0]] for idx in candidates], dtype=np.int64)
        # Eligibility is evaluated over the exact half-open grid, not first/last frame timestamps.
        grid_start = np.asarray(
            [iso_ns(events["kickoffs"][period]) + int(round(((int(s) - iso_ns(events["kickoffs"][period])) / 1e9 // 5) * 5e9)) for s in starts],
            dtype=np.int64,
        )
        # The expression above can round down after a small timestamp offset; derive grid from the first frame.
        grid_start = np.asarray([int(s - ((int(s) - iso_ns(events["kickoffs"][period])) % 5_000_000_000)) for s in starts], dtype=np.int64)
        # If the first observed frame follows the grid boundary, the modulo expression is the boundary.
        ends = grid_start + 5_000_000_000
        possession, open_valid = event_state_at_intervals(events["state_events"], grid_start, ends)
        entity_by_key = {(e["team_id"], e["person_id"]): e for e in data["entities"]}
        ball_entities = [e for e in data["entities"] if e["team_id"] == "BALL"]
        if len(ball_entities) != 1:
            raise RuntimeError(f"Expected one ball entity in {metadata['match_id']} {period}")
        ball = ball_entities[0]
        for sequence, (idx, start_ns, end_ns, attacking_team, state_ok) in enumerate(
            zip(candidates, grid_start, ends, possession, open_valid, strict=True)
        ):
            reason = None
            if not state_ok or attacking_team not in teams:
                reason = "possession_or_open_play"
            elif not ball["valid"][idx].all():
                reason = "incomplete_ball"
            defending_team = next(iter(teams - {attacking_team})) if attacking_team in teams else None
            complete: list[str] = []
            if defending_team:
                for player in metadata["players"].values():
                    if player.team_id != defending_team or player.goalkeeper:
                        continue
                    entity = entity_by_key.get((defending_team, player.player_id))
                    if entity is not None and entity["valid"][idx].all():
                        complete.append(player.player_id)
            if reason is None and len(complete) < 9:
                reason = "fewer_than_9_complete_defending_outfield"
            interval_rows.append(
                {
                    "match_id": metadata["match_id"],
                    "period": period,
                    "sequence": sequence,
                    "start_time_utc": datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc).isoformat(),
                    "end_time_utc": datetime.fromtimestamp(end_ns / 1e9, tz=timezone.utc).isoformat(),
                    "attacking_team_id": attacking_team,
                    "defending_team_id": defending_team,
                    "complete_defending_outfield_count": len(complete),
                    "complete_focal_ids": "|".join(sorted(complete)),
                    "eligible": reason is None,
                    "exclusion_reason": reason,
                }
            )
    intervals = pd.DataFrame(interval_rows)
    eligible = intervals[intervals["eligible"]].copy()
    team_counts = eligible.groupby("defending_team_id").size().to_dict()
    focal_counts: Counter[str] = Counter()
    for value in eligible["complete_focal_ids"]:
        focal_counts.update(value.split("|") if value else [])
    focal_25 = sum(value >= 25 for value in focal_counts.values())
    expected_teams = [metadata["home_team_id"], metadata["away_team_id"]]
    summary = {
        "match_id": metadata["match_id"],
        "eligible_intervals": int(len(eligible)),
        "defending_team_interval_counts": {team: int(team_counts.get(team, 0)) for team in expected_teams},
        "focal_defenders_with_at_least_25": int(focal_25),
        "focal_interval_counts": dict(sorted(focal_counts.items())),
        "exclusion_counts": {str(k): int(v) for k, v in intervals["exclusion_reason"].fillna("eligible").value_counts().items()},
    }
    summary["usable"] = (
        summary["eligible_intervals"] >= 100
        and all(value >= 40 for value in summary["defending_team_interval_counts"].values())
        and summary["focal_defenders_with_at_least_25"] >= 8
    )
    return intervals, summary


def mapping_stage(raw_dir: Path, cache_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    checksums: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    interval_tables: list[pd.DataFrame] = []
    schema: dict[str, Any] = {}
    for match_id in MATCH_IDS:
        files = {kind: find_file(raw_dir, kind, match_id) for kind in ("metadata", "events", "tracking")}
        for kind, path in files.items():
            checksums.append({"match_id": match_id, "kind": kind, "file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
        metadata = read_metadata(files["metadata"])
        events = read_events(files["events"])
        cache_path = cache_dir / f"{match_id}_raw_tracking.npz"
        if cache_path.exists():
            tracking = load_tracking_cache(cache_path)
        else:
            tracking = read_tracking(files["tracking"], metadata)
            save_tracking_cache(cache_path, tracking)
        intervals, summary = support_for_match(metadata, events, tracking)
        summaries.append(summary)
        interval_tables.append(intervals)
        schema[match_id] = {
            "provider_match_id": metadata["provider_match_id"],
            "teams": {
                metadata["home_team_id"]: metadata["home_team_name"],
                metadata["away_team_id"]: metadata["away_team_name"],
            },
            "pitch_m": [metadata["pitch_x_m"], metadata["pitch_y_m"]],
            "goalkeepers": sorted(player.player_id for player in metadata["players"].values() if player.goalkeeper),
            "kickoffs_utc": {key: value.isoformat() for key, value in events["kickoffs"].items()},
            "substitutions": events["substitutions"],
            "restart_counts": events["restart_counts"],
            "period_tracking": {
                period: {
                    "frames": int(len(tracking[period]["frame_n"])),
                    "first_frame": int(tracking[period]["frame_n"][0]),
                    "last_frame": int(tracking[period]["frame_n"][-1]),
                    "first_time_utc": datetime.fromtimestamp(int(tracking[period]["time_ns"][0]) / 1e9, tz=timezone.utc).isoformat(),
                    "last_time_utc": datetime.fromtimestamp(int(tracking[period]["time_ns"][-1]) / 1e9, tz=timezone.utc).isoformat(),
                    "entities": len(tracking[period]["entities"]),
                }
                for period in PERIODS
            },
        }
        print(json.dumps(summary, sort_keys=True))
    pd.DataFrame(checksums).to_csv(output_dir / "input_checksums.csv", index=False)
    pd.DataFrame(summaries).to_json(output_dir / "mapping_support_summary.json", orient="records", indent=2)
    pd.concat(interval_tables, ignore_index=True).to_csv(output_dir / "mapping_interval_support.csv", index=False)
    (output_dir / "provider_schema_audit.json").write_text(json.dumps(schema, indent=2) + "\n")
    usable = sum(bool(row["usable"]) for row in summaries)
    (output_dir / "mapping_gate.json").write_text(
        json.dumps(
            {
                "stage": "outcome_blind_mapping_and_support",
                "focal_relative_outcomes_constructed": False,
                "usable_matches": usable,
                "behavioral_execution_authorized_by_support": usable >= 5,
            },
            indent=2,
        )
        + "\n"
    )


def smooth_xy(values: np.ndarray, frames: int) -> np.ndarray:
    return pd.DataFrame(values).rolling(frames, center=True, min_periods=frames).mean().to_numpy()


def path_length(values: np.ndarray) -> float:
    valid = np.isfinite(values).all(axis=1)
    data = values[valid]
    if len(data) < 2:
        return float("nan")
    return float(np.linalg.norm(np.diff(data, axis=0), axis=1).sum())


def spearman(x: pd.Series | np.ndarray, y: pd.Series | np.ndarray) -> float:
    a = pd.Series(x).rank(method="average").to_numpy(float)
    b = pd.Series(y).rank(method="average").to_numpy(float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def eligible_raw_intervals(
    metadata: dict[str, Any], events: dict[str, Any], tracking: dict[str, Any], seconds: int
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    teams = {metadata["home_team_id"], metadata["away_team_id"]}
    for period in PERIODS:
        data = tracking[period]
        candidates = period_interval_candidates(data, events["kickoffs"][period], seconds)
        kickoff_ns = iso_ns(events["kickoffs"][period])
        first_times = np.asarray([data["time_ns"][idx[0]] for idx in candidates], dtype=np.int64)
        grid_starts = np.asarray(
            [int(value - ((int(value) - kickoff_ns) % int(seconds * 1e9))) for value in first_times],
            dtype=np.int64,
        )
        grid_ends = grid_starts + int(seconds * 1e9)
        possession, state_ok = event_state_at_intervals(events["state_events"], grid_starts, grid_ends)
        entity_by_key = {(entity["team_id"], entity["person_id"]): entity for entity in data["entities"]}
        balls = [entity for entity in data["entities"] if entity["team_id"] == "BALL"]
        if len(balls) != 1:
            raise RuntimeError(f"Expected one ball in {metadata['match_id']} {period}")
        ball = balls[0]
        for sequence, (idx, start_ns, attacking_team, open_ok) in enumerate(
            zip(candidates, grid_starts, possession, state_ok, strict=True)
        ):
            if not open_ok or attacking_team not in teams or not ball["valid"][idx].all():
                continue
            defending_team = next(iter(teams - {attacking_team}))
            complete = []
            for player in metadata["players"].values():
                if player.team_id != defending_team or player.goalkeeper:
                    continue
                entity = entity_by_key.get((defending_team, player.player_id))
                if entity is not None and entity["valid"][idx].all():
                    complete.append(player.player_id)
            if len(complete) < 9:
                continue
            interval_id = f"{metadata['match_id']}_{period}_{start_ns}_{seconds}s"
            rows.append(
                {
                    "interval_id": interval_id,
                    "match_id": metadata["match_id"],
                    "period": period,
                    "sequence": sequence,
                    "start_ns": int(start_ns),
                    "start_s": (int(start_ns) - kickoff_ns) / 1e9 + (0 if period == "firstHalf" else 2700),
                    "seconds": seconds,
                    "attacking_team_id": attacking_team,
                    "defending_team_id": defending_team,
                    "players": sorted(complete),
                    "positions": {
                        player_id: np.column_stack(
                            [entity_by_key[(defending_team, player_id)]["x"][idx], entity_by_key[(defending_team, player_id)]["y"][idx]]
                        ).astype(float)
                        for player_id in complete
                    },
                    "ball": np.column_stack([ball["x"][idx], ball["y"][idx]]).astype(float),
                }
            )
    return rows


def interval_activity(intervals: list[dict[str, Any]], smoothing: int) -> pd.DataFrame:
    records = []
    for interval in intervals:
        smoothed = {player: smooth_xy(position, smoothing) for player, position in interval["positions"].items()}
        stack = np.stack([interval["positions"][player] for player in interval["players"]])
        full_centroid = smooth_xy(stack.mean(axis=0), smoothing)
        focal_paths = {player: path_length(smoothed[player]) for player in interval["players"]}
        interval["smoothed"] = smoothed
        interval["full_centroid_smoothed"] = full_centroid
        interval["activity"] = {
            "full_defending_outfield_centroid_path_m": path_length(full_centroid),
            "sum_defending_outfield_paths_m": float(sum(focal_paths.values())),
            "ball_path_m": path_length(smooth_xy(interval["ball"], smoothing)),
        }
        interval["focal_absolute"] = focal_paths
        records.append(
            {
                "interval_id": interval["interval_id"],
                "match_id": interval["match_id"],
                "period": interval["period"],
                "start_s": interval["start_s"],
                "defending_team_id": interval["defending_team_id"],
                **interval["activity"],
            }
        )
    return pd.DataFrame(records)


def assign_collective_rank_bins(intervals: list[dict[str, Any]]) -> None:
    ordered = sorted(
        intervals,
        key=lambda item: (
            item["activity"]["full_defending_outfield_centroid_path_m"],
            item["period"],
            item["start_s"],
            item["interval_id"],
        ),
    )
    n = len(ordered)
    for rank, interval in enumerate(ordered):
        interval["collective_rank_bin"] = min(2, math.floor(3 * rank / n))


def select_misaligned(intervals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for interval in intervals:
        candidates = [
            other
            for other in intervals
            if other["period"] == interval["period"]
            and other["defending_team_id"] == interval["defending_team_id"]
            and other["collective_rank_bin"] == interval["collective_rank_bin"]
            and 10 <= abs(other["start_s"] - interval["start_s"]) <= 120
            and abs(other["start_s"] - interval["start_s"]) >= max(interval["seconds"], other["seconds"])
        ]
        if candidates:
            selected[interval["interval_id"]] = min(
                candidates,
                key=lambda other: (
                    abs(other["start_s"] - interval["start_s"]),
                    other["start_s"],
                    other["interval_id"],
                ),
            )
    return selected


def construct_outcomes(
    intervals: list[dict[str, Any]], smoothing: int, misaligned: dict[str, dict[str, Any]]
) -> pd.DataFrame:
    rows = []
    for interval in intervals:
        candidate = misaligned.get(interval["interval_id"])
        for focal in interval["players"]:
            other_players = [player for player in interval["players"] if player != focal]
            loo = smooth_xy(np.stack([interval["positions"][player] for player in other_players]).mean(axis=0), smoothing)
            focal_xy = interval["smoothed"][focal]
            relative = focal_xy - loo
            valid = relative[np.isfinite(relative).all(axis=1)]
            row = {
                "match_id": interval["match_id"],
                "interval_id": interval["interval_id"],
                "period": interval["period"],
                "start_s": interval["start_s"],
                "seconds": interval["seconds"],
                "smoothing_frames": smoothing,
                "attacking_team_id": interval["attacking_team_id"],
                "defending_team_id": interval["defending_team_id"],
                "focal_player_id": focal,
                "focal_relative_path_m": path_length(relative),
                "focal_relative_net_x_change_m": float(valid[-1, 0] - valid[0, 0]),
                "focal_relative_net_y_change_m": float(valid[-1, 1] - valid[0, 1]),
                "focal_relative_net_displacement_m": float(np.linalg.norm(valid[-1] - valid[0])),
                "focal_absolute_path_m": interval["focal_absolute"][focal],
                "leave_one_out_centroid_path_m": path_length(loo),
                **interval["activity"],
                "collective_rank_bin": interval["collective_rank_bin"],
            }
            if candidate is not None:
                candidate_others = [player for player in candidate["players"] if player != focal]
                candidate_loo = smooth_xy(
                    np.stack([candidate["positions"][player] for player in candidate_others]).mean(axis=0), smoothing
                )
                row["misaligned_interval_id"] = candidate["interval_id"]
                row["misaligned_relative_path_m"] = path_length(focal_xy - candidate_loo)
            rows.append(row)
    return pd.DataFrame(rows)


ACTIVITY_COLUMNS = (
    "focal_absolute_path_m",
    "full_defending_outfield_centroid_path_m",
    "sum_defending_outfield_paths_m",
    "ball_path_m",
)


def summarize_setting(outcomes: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values = outcomes["focal_relative_path_m"]
    q = values.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    distribution = {
        "observations": int(len(outcomes)),
        "intervals": int(outcomes["interval_id"].nunique()),
        "finite": bool(np.isfinite(values).all()),
        "nonnegative": bool((values >= 0).all()),
        "p10_m": float(q.loc[0.1]),
        "p25_m": float(q.loc[0.25]),
        "median_m": float(q.loc[0.5]),
        "p75_m": float(q.loc[0.75]),
        "p90_m": float(q.loc[0.9]),
        "iqr_m": float(q.loc[0.75] - q.loc[0.25]),
        "numerical_zero_fraction": float((values <= 1e-8).mean()),
    }
    correlations = [
        {
            "activity_variable": column,
            "spearman_rho": spearman(outcomes["focal_relative_path_m"], outcomes[column]),
        }
        for column in ACTIVITY_COLUMNS
    ]
    return distribution, correlations


def summarize_misaligned(outcomes: pd.DataFrame) -> dict[str, Any]:
    supported = outcomes.dropna(subset=["misaligned_relative_path_m"]).copy()
    differences = supported["misaligned_relative_path_m"] - supported["focal_relative_path_m"]
    support = supported["interval_id"].nunique() / outcomes["interval_id"].nunique()
    median = float(differences.median()) if len(differences) else float("nan")
    fraction_positive = float((differences > 0).mean()) if len(differences) else float("nan")
    fraction_nonnegative = float((differences >= 0).mean()) if len(differences) else float("nan")
    passed = support >= 0.70 and median > 0 and fraction_positive > 0.50
    contradiction = support >= 0.70 and median < 0 and fraction_positive < 0.50
    return {
        "eligible_interval_support_fraction": float(support),
        "supported_intervals": int(supported["interval_id"].nunique()),
        "paired_focal_observations": int(len(supported)),
        "paired_median_difference_m": median,
        "fraction_misaligned_greater": fraction_positive,
        "fraction_misaligned_nonnegative": fraction_nonnegative,
        "pass": bool(passed),
        "material_contradiction": bool(contradiction),
        "classification": "pass" if passed else ("material_contradiction" if contradiction else "inconclusive"),
    }


def common_translation_control(translation: np.ndarray) -> list[dict[str, Any]]:
    """Apply one observed collective trajectory to fixed relative positions."""
    translation = np.asarray(translation, dtype=float)
    fixed = np.asarray([[i * 2.3, (-1) ** i * (i + 1)] for i in range(9)], dtype=float)
    positions = translation[None, :, :] + fixed[:, None, :]
    results = []
    for smoothing in (5, 7, 9):
        maximum = 0.0
        for focal in range(len(fixed)):
            focal_xy = smooth_xy(positions[focal], smoothing)
            loo = smooth_xy(positions[np.arange(len(fixed)) != focal].mean(axis=0), smoothing)
            maximum = max(maximum, path_length(focal_xy - loo))
        results.append({"smoothing_frames": smoothing, "maximum_focal_relative_path_m": maximum, "pass": maximum <= 1e-8})
    return results


def cluster_bootstrap(
    outcomes: pd.DataFrame, match_seed: int, resamples: int = 10000
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(match_seed)
    interval_ids = outcomes["interval_id"].unique()
    groups = {key: outcomes.index[outcomes["interval_id"] == key].to_numpy() for key in interval_ids}
    metrics = {"median_m": np.empty(resamples)}
    for column in ACTIVITY_COLUMNS:
        metrics[f"rho__{column}"] = np.empty(resamples)
    for i in range(resamples):
        sampled = rng.choice(interval_ids, len(interval_ids), replace=True)
        indices = np.concatenate([groups[key] for key in sampled])
        sample = outcomes.loc[indices]
        metrics["median_m"][i] = sample["focal_relative_path_m"].median()
        for column in ACTIVITY_COLUMNS:
            metrics[f"rho__{column}"][i] = spearman(sample["focal_relative_path_m"], sample[column])
    rows = []
    for metric, values in metrics.items():
        low, high = np.nanquantile(values, [0.025, 0.975])
        rows.append({"metric": metric, "bootstrap_low": float(low), "bootstrap_high": float(high), "resamples": resamples})
    return rows


def classify_results(
    match_rows: list[dict[str, Any]], common_translation_pass: bool
) -> dict[str, Any]:
    usable = len(match_rows)
    if usable < 5:
        return {"category": "P", "label": "portability-inconclusive", "reason": "fewer than five usable matches"}
    core_count = sum(row["core_replicating"] for row in match_rows)
    contradictions = sum(row["misaligned_material_contradiction"] for row in match_rows)
    sensitivity_failures = sum(not row["sensitivity_pass"] for row in match_rows)
    reversal_sets = {
        variable: {row["match_id"] for row in match_rows if row[f"rho__{variable}"] <= -0.10}
        for variable in ACTIVITY_COLUMNS
    }
    same_variable_three = any(len(matches) >= 3 for matches in reversal_sets.values())
    multi_variable_matches = sum(
        sum(row[f"rho__{variable}"] <= -0.10 for variable in ACTIVITY_COLUMNS) >= 2 for row in match_rows
    )
    c_reasons = []
    if not common_translation_pass:
        c_reasons.append("common translation failed")
    if core_count <= 3:
        c_reasons.append("three or fewer core-replicating matches")
    if same_variable_three:
        c_reasons.append("same activity relationship materially reversed in at least three matches")
    if multi_variable_matches >= 2:
        c_reasons.append("at least two activity relationships reversed within each of at least two matches")
    if contradictions >= 3:
        c_reasons.append("at least three material misaligned-control contradictions")
    if sensitivity_failures >= 3:
        c_reasons.append("at least three sensitivity-failing matches")
    if c_reasons:
        return {"category": "C", "label": "behavioral external-replication failure", "reasons": c_reasons}
    repeated_reversal = any(len(matches) >= 2 for matches in reversal_sets.values()) or any(
        sum(row[f"rho__{variable}"] <= -0.10 for variable in ACTIVITY_COLUMNS) >= 2 for row in match_rows
    )
    a_pass = (
        usable >= 6
        and core_count >= 6
        and common_translation_pass
        and sum(row["misaligned_pass"] for row in match_rows) >= 6
        and contradictions == 0
        and not repeated_reversal
    )
    if a_pass:
        return {"category": "A", "label": "strong external replication", "reasons": []}
    return {"category": "B", "label": "mixed / partial external replication", "reasons": ["one or more A requirements not met"]}


def add_activity_strata(outcomes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    protocol_a = json.loads((ROOT / "config" / "phase4a_focal_departure_validation_protocol.json").read_text())
    cuts = protocol_a["activity_conditioning"]["cuts_m"]
    data = outcomes.copy()
    for column in ACTIVITY_COLUMNS:
        thresholds = cuts[column]
        data[f"metrica_bin__{column}"] = np.where(
            data[column] < thresholds[0], "low", np.where(data[column] <= thresholds[1], "middle", "high")
        )
        data[f"idsse_tercile__{column}"] = data.groupby("match_id")[column].transform(
            lambda values: pd.qcut(values.rank(method="first"), 3, labels=["low", "middle", "high"])
        )
    transport = (
        data.groupby(
            ["match_id", "metrica_bin__focal_absolute_path_m", "metrica_bin__full_defending_outfield_centroid_path_m"],
            observed=False,
        )["focal_relative_path_m"]
        .agg(observations="size", median_m="median")
        .reset_index()
    )
    descriptive = (
        data.groupby(
            ["match_id", "idsse_tercile__focal_absolute_path_m", "idsse_tercile__full_defending_outfield_centroid_path_m"],
            observed=False,
        )["focal_relative_path_m"]
        .agg(observations="size", median_m="median")
        .reset_index()
    )
    return transport, descriptive


def create_figures(
    primary: pd.DataFrame,
    match_summary: pd.DataFrame,
    correlations: pd.DataFrame,
    controls: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> None:
    import matplotlib.pyplot as plt

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    matches = sorted(primary["match_id"].unique())
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True)
    for ax, match in zip(axes.flat, matches, strict=False):
        ax.hist(primary.loc[primary.match_id == match, "focal_relative_path_m"], bins=35, color="#35618f", alpha=0.85)
        ax.axvline(match_summary.set_index("match_id").loc[match, "median_m"], color="#b33c2e", lw=1.5)
        ax.set_title(match)
        ax.set_xlabel("focal-relative path [m]")
    axes.flat[-1].axis("off")
    fig.suptitle("Phase 4C primary focal-relative path distributions")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "phase4c_distributions.png", dpi=180)
    plt.close(fig)

    pivot = correlations.pivot(index="match_id", columns="activity_variable", values="spearman_rho").loc[matches]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    image = ax.imshow(pivot.to_numpy(), vmin=-1, vmax=1, cmap="RdBu_r", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), [value.replace("_path_m", "").replace("_", " ") for value in pivot.columns], rotation=25, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Spearman rho")
    ax.set_title("Separate primary activity relationships by match")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "phase4c_activity_relationships.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(controls.match_id, controls.paired_median_difference_m, color="#5b8f55")
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set(title="Misaligned minus contemporaneous", ylabel="paired median difference [m]")
    axes[1].bar(sensitivity.match_id, sensitivity.consistent_settings, color="#8064a2")
    axes[1].axhline(8, color="black", ls="--", lw=0.8)
    axes[1].set(title="Frozen sensitivity consistency", ylabel="consistent settings (of 9)", ylim=(0, 9.5))
    for ax in axes:
        ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "phase4c_controls_and_sensitivity.png", dpi=180)
    plt.close(fig)


def execute_stage(raw_dir: Path, cache_dir: Path, output_dir: Path) -> None:
    frozen_protocol_hash = sha256(PROTOCOL_PATH)
    frozen_implementation = json.loads(IMPLEMENTATION_PATH.read_text())
    if frozen_implementation["outcome_blind_support_gate"]["passed"] is not True:
        raise RuntimeError("Outcome-blind support gate is not frozen as passed")
    output_dir.mkdir(parents=True, exist_ok=True)
    primary_frames: list[pd.DataFrame] = []
    setting_summaries: list[dict[str, Any]] = []
    setting_correlations: list[dict[str, Any]] = []
    setting_controls: list[dict[str, Any]] = []
    primary_intervals_by_match: dict[str, list[dict[str, Any]]] = {}
    for match_index, match_id in enumerate(MATCH_IDS):
        metadata = read_metadata(find_file(raw_dir, "metadata", match_id))
        events = read_events(find_file(raw_dir, "events", match_id))
        tracking = load_tracking_cache(cache_dir / f"{match_id}_raw_tracking.npz")
        for seconds in (4, 5, 6):
            intervals = eligible_raw_intervals(metadata, events, tracking, seconds)
            for smoothing in (5, 7, 9):
                interval_activity(intervals, smoothing)
                assign_collective_rank_bins(intervals)
                misaligned = select_misaligned(intervals)
                outcomes = construct_outcomes(intervals, smoothing, misaligned)
                distribution, correlations = summarize_setting(outcomes)
                control = summarize_misaligned(outcomes)
                base = {"match_id": match_id, "seconds": seconds, "smoothing_frames": smoothing, **distribution}
                setting_summaries.append(base)
                setting_correlations.extend({"match_id": match_id, "seconds": seconds, "smoothing_frames": smoothing, **row} for row in correlations)
                setting_controls.append({"match_id": match_id, "seconds": seconds, "smoothing_frames": smoothing, **control})
                if seconds == 5 and smoothing == 7:
                    primary_frames.append(outcomes)
                    primary_intervals_by_match[match_id] = intervals
    primary = pd.concat(primary_frames, ignore_index=True)
    summaries = pd.DataFrame(setting_summaries)
    correlations = pd.DataFrame(setting_correlations)
    controls = pd.DataFrame(setting_controls)

    match_rows = []
    sensitivity_rows = []
    for match_id in MATCH_IDS:
        match_settings = summaries[summaries.match_id == match_id]
        match_corr = correlations[correlations.match_id == match_id]
        match_controls = controls[controls.match_id == match_id]
        consistency = []
        any_reversal = []
        any_contradiction = []
        for _, setting in match_settings.iterrows():
            key = (setting.seconds, setting.smoothing_frames)
            corr = match_corr[(match_corr.seconds == key[0]) & (match_corr.smoothing_frames == key[1])]
            control = match_controls[(match_controls.seconds == key[0]) & (match_controls.smoothing_frames == key[1])].iloc[0]
            reversal = bool((corr.spearman_rho <= -0.10).any())
            consistent = (
                bool(setting.finite)
                and bool(setting.nonnegative)
                and setting.median_m > 1e-8
                and setting.iqr_m > 1e-8
                and not reversal
                and control.eligible_interval_support_fraction >= 0.70
                and control.paired_median_difference_m >= 0
                and control.fraction_misaligned_nonnegative >= 0.50
            )
            consistency.append(consistent)
            any_reversal.append(reversal)
            any_contradiction.append(bool(control.material_contradiction))
        primary_summary = match_settings[(match_settings.seconds == 5) & (match_settings.smoothing_frames == 7)].iloc[0]
        primary_corr = match_corr[(match_corr.seconds == 5) & (match_corr.smoothing_frames == 7)]
        primary_control = match_controls[(match_controls.seconds == 5) & (match_controls.smoothing_frames == 7)].iloc[0]
        rho_map = dict(zip(primary_corr.activity_variable, primary_corr.spearman_rho, strict=True))
        distribution_pass = bool(primary_summary.finite and primary_summary.nonnegative and primary_summary.median_m > 1e-8 and primary_summary.iqr_m > 1e-8)
        activity_pass = rho_map["focal_absolute_path_m"] > 0 and all(value > -0.10 for value in rho_map.values())
        primary_pass = distribution_pass and activity_pass and bool(primary_control["pass"])
        sensitivity_pass = primary_pass and sum(consistency) >= 8 and not any(any_reversal) and not any(any_contradiction)
        sensitivity_rows.append(
            {
                "match_id": match_id,
                "consistent_settings": int(sum(consistency)),
                "any_material_activity_reversal": bool(any(any_reversal)),
                "any_material_control_contradiction": bool(any(any_contradiction)),
                "primary_setting_pass": bool(primary_pass),
                "sensitivity_pass": bool(sensitivity_pass),
            }
        )
        row = {
            "match_id": match_id,
            **{key: primary_summary[key] for key in ["observations", "intervals", "median_m", "iqr_m", "p10_m", "p25_m", "p75_m", "p90_m", "numerical_zero_fraction", "finite", "nonnegative"]},
            **{f"rho__{key}": float(value) for key, value in rho_map.items()},
            "misaligned_pass": bool(primary_control["pass"]),
            "misaligned_material_contradiction": bool(primary_control.material_contradiction),
            "sensitivity_pass": bool(sensitivity_pass),
        }
        row["core_replicating"] = bool(distribution_pass and activity_pass and row["misaligned_pass"] and sensitivity_pass)
        match_rows.append(row)

    first_interval = primary_intervals_by_match[MATCH_IDS[0]][0]
    observed_translation = np.stack([first_interval["positions"][player] for player in first_interval["players"]]).mean(axis=0)
    common = common_translation_control(observed_translation)
    common_pass = all(row["pass"] for row in common)
    classification = classify_results(match_rows, common_pass)
    classification.update(
        {
            "usable_matches": 7,
            "core_replicating_matches": int(sum(row["core_replicating"] for row in match_rows)),
            "common_translation_pass": common_pass,
            "protocol_sha256_before_execution": frozen_protocol_hash,
        }
    )

    bootstrap_rows = []
    for match_id in MATCH_IDS:
        match_outcomes = primary[primary.match_id == match_id].reset_index(drop=True)
        for row in cluster_bootstrap(match_outcomes, 20260830, 10000):
            bootstrap_rows.append({"match_id": match_id, **row})

    transport, descriptive = add_activity_strata(primary)
    team_summary = (
        primary.groupby(["match_id", "defending_team_id"])["focal_relative_path_m"]
        .agg(observations="size", median_m="median", q25_m=lambda x: x.quantile(0.25), q75_m=lambda x: x.quantile(0.75))
        .reset_index()
    )
    team_summary["iqr_m"] = team_summary.q75_m - team_summary.q25_m
    player_summary = (
        primary.groupby(["match_id", "defending_team_id", "focal_player_id"])["focal_relative_path_m"]
        .agg(observations="size", median_m="median", q25_m=lambda x: x.quantile(0.25), q75_m=lambda x: x.quantile(0.75))
        .reset_index()
    )
    player_summary["iqr_m"] = player_summary.q75_m - player_summary.q25_m

    primary.to_csv(output_dir / "primary_focal_observations.csv", index=False)
    pd.DataFrame(match_rows).to_csv(output_dir / "match_summary.csv", index=False)
    correlations[correlations.seconds.eq(5) & correlations.smoothing_frames.eq(7)].to_csv(output_dir / "primary_activity_correlations.csv", index=False)
    controls[controls.seconds.eq(5) & controls.smoothing_frames.eq(7)].to_csv(output_dir / "primary_misaligned_control.csv", index=False)
    summaries.to_csv(output_dir / "sensitivity_distribution_settings.csv", index=False)
    correlations.to_csv(output_dir / "sensitivity_activity_settings.csv", index=False)
    controls.to_csv(output_dir / "sensitivity_control_settings.csv", index=False)
    pd.DataFrame(sensitivity_rows).to_csv(output_dir / "sensitivity_match_results.csv", index=False)
    pd.DataFrame(common).to_csv(output_dir / "common_translation_control.csv", index=False)
    pd.DataFrame(bootstrap_rows).to_csv(output_dir / "bootstrap_uncertainty.csv", index=False)
    transport.to_csv(output_dir / "metrica_activity_cut_transport.csv", index=False)
    descriptive.to_csv(output_dir / "idsse_activity_terciles_descriptive.csv", index=False)
    team_summary.to_csv(output_dir / "defending_team_summary.csv", index=False)
    player_summary.to_csv(output_dir / "focal_player_summary.csv", index=False)
    (output_dir / "classification.json").write_text(json.dumps(classification, indent=2) + "\n")
    (output_dir / "execution_manifest.json").write_text(
        json.dumps(
            {
                "protocol_sha256_before_execution": frozen_protocol_hash,
                "implementation_sha256": sha256(IMPLEMENTATION_PATH),
                "bootstrap_seed_base": 20260830,
                "bootstrap_match_seed_rule": "seed 20260830 restarted independently for each match",
                "bootstrap_resamples_per_match": 10000,
                "raw_data_directory_ignored": True,
            },
            indent=2,
        )
        + "\n"
    )
    create_figures(
        primary,
        pd.DataFrame(match_rows),
        correlations[correlations.seconds.eq(5) & correlations.smoothing_frames.eq(7)],
        controls[controls.seconds.eq(5) & controls.smoothing_frames.eq(7)],
        pd.DataFrame(sensitivity_rows),
    )
    print(json.dumps(classification, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("mapping", "execute"), required=True)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/idsse_raw"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/idsse_cache"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/phase4c"))
    args = parser.parse_args()
    if args.stage == "mapping":
        mapping_stage(args.raw_dir, args.cache_dir, args.output_dir)
    else:
        execute_stage(args.raw_dir, args.cache_dir, args.output_dir)


if __name__ == "__main__":
    main()
