"""Execute the frozen SkillCorner Spatial Form v1 external replication.

Only compact aggregate outputs are written. Native SkillCorner JSONL remains
authoritative for frame-level tracking-status support; Kloppy is used for the
required per-match provider-equivalence gate. No DRD value is read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from kloppy import skillcorner

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_reorganization_spatial_value_v1_design as design  # noqa: E402
from infrastructure.skillcorner_spatial_form_adapter import (  # noqa: E402
    CANONICAL_PITCH_LENGTH_M,
    CANONICAL_PITCH_WIDTH_M,
    SMOOTHER_EDGE_FRAMES,
    active_outfield_player_ids,
    anchor_frames,
    attacking_frame,
    canonical_xy,
    detected_fraction,
    goalward_sign,
    identity_step_is_valid,
    required_frame_ids,
    stricter_quality_pass,
    timestamp_seconds,
)


PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_spatial_form_v1_skillcorner_external.md"
CONFIG = ROOT / "config/defensive_reorganization_spatial_form_v1_skillcorner_external.json"
LEDGER = ROOT / "config/defensive_reorganization_spatial_form_v1_skillcorner_external_hashes.json"
RECONCILIATION = ROOT / "docs/protocols/defensive_reorganization_spatial_form_v1_skillcorner_external_preexecution_support_reconciliation.md"
PARENT_PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_spatial_value_v1.md"
PARENT_CONFIG = ROOT / "config/defensive_reorganization_spatial_value_v1.json"
OUTPUT = ROOT / "outputs/defensive_reorganization_spatial_form_v1_skillcorner_external"
DOC_RESULT = ROOT / "docs/results/defensive_reorganization_spatial_form_v1_skillcorner_external.md"

FROZEN = {
    PROTOCOL: "9d863157e9bf938b4e13d216f73c5b56057d9c59f34a86b47dac20a4d9d9f80e",
    CONFIG: "7b1537235dd6966b9ade55a091c3688635e8cdf586673f45fa0b5aa64d50a79e",
    LEDGER: "b24b0ffda4a96052851100c28254799cf7099f76b225aabb3597d8bb555f2f73",
    RECONCILIATION: "db3dcdf533f687f875c252a2d17aebe55a4f3bfe5c29726d33a259056fc1bf84",
    PARENT_PROTOCOL: "d394519c7839ad20aba3806b2bbae5bf7b71bdb33a77a70eeb0b6d0c8af08e25",
    PARENT_CONFIG: "2d8d7abac9738ccb8a4765c657f6865ab445cf390e41ed8063b05a111d62e5df",
}

FORMAL_MATCHES = (
    1886347,
    1899585,
    1925299,
    1996435,
    2006229,
    2011166,
    2013725,
    2015213,
    2017461,
)
EXCLUDED_MATCH = 1953632
BASE = design.BASE_COLUMNS
BOOTSTRAP_REPLICATES = 2000
MINIMUM_BOOTSTRAP_VALID = 1900
BOOTSTRAP_SEED = 20260905
BLOCK_SECONDS = 60.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_frozen(output: Path) -> dict[str, Any]:
    actual = {str(path.relative_to(ROOT)): sha(path) for path in FROZEN}
    failures = {
        str(path.relative_to(ROOT)): {"actual": actual[str(path.relative_to(ROOT))], "expected": expected}
        for path, expected in FROZEN.items()
        if actual[str(path.relative_to(ROOT))] != expected
    }
    if failures:
        raise RuntimeError(f"frozen SkillCorner Spatial Form hash failure: {failures}")
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("a SkillCorner Spatial Form result already exists")
    if DOC_RESULT.exists():
        raise RuntimeError("a SkillCorner Spatial Form report already exists")
    return {
        "frozen_hashes_verified": actual,
        "excluded_match": EXCLUDED_MATCH,
        "excluded_match_reason": "provider_top_level_status_not_started_conflicts_with_complete_two_period_files",
        "SkillCorner_response_target_preexisting": False,
        "SkillCorner_coefficient_preexisting": False,
        "SkillCorner_classification_preexisting": False,
        "DRD_residuals_read": False,
        "Metrica_Game_3_accessed": False,
    }


class MatchSource:
    """Native SkillCorner input plus outcome-blind roster/support helpers."""

    def __init__(self, match_id: int, data_dir: Path):
        self.match_id = int(match_id)
        self.data_dir = data_dir
        self.meta_path = data_dir / f"{match_id}_match.json"
        self.tracking_path = data_dir / f"{match_id}_tracking_extrapolated.jsonl"
        self.phase_path = data_dir / f"{match_id}_phases_of_play.csv"
        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        self.rows: dict[int, dict[str, Any]] = {}
        self.period_frames: dict[int, list[int]] = {1: [], 2: []}
        with self.tracking_path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                period = row.get("period")
                if period in (1, 2):
                    frame = int(row["frame"])
                    self.rows[frame] = row
                    self.period_frames[int(period)].append(frame)
        for period, frames in self.period_frames.items():
            if not frames or any(next_frame - frame != 1 for frame, next_frame in zip(frames, frames[1:], strict=False)):
                raise RuntimeError(f"match {match_id} period {period} lacks contiguous native frames")
        self.period_start = {period: frames[0] for period, frames in self.period_frames.items()}
        self.period_end = {period: frames[-1] for period, frames in self.period_frames.items()}
        self.home_team_id = int(self.meta["home_team"]["id"])
        self.away_team_id = int(self.meta["away_team"]["id"])
        self.team_ids = (self.home_team_id, self.away_team_id)
        self.player_team = {int(player["id"]): int(player["team_id"]) for player in self.meta["players"] if player.get("team_id") is not None}
        self.goalkeepers = {
            int(player["id"])
            for player in self.meta["players"]
            if player.get("team_id") is not None and int(player["player_role"]["id"]) == 0
        }
        self.support_cache: dict[int, bool] = {}
        self.phase_coverage = self._phase_coverage()
        self._verify_native_clock()

    def _phase_coverage(self) -> set[int]:
        coverage: set[int] = set()
        with self.phase_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                coverage.update(range(int(row["frame_start"]), int(row["frame_end"]) + 1))
        return coverage

    def _verify_native_clock(self) -> None:
        for period, frames in self.period_frames.items():
            start = self.period_start[period]
            for frame in frames:
                expected = (frame - start) / 10.0
                actual = timestamp_seconds(self.rows[frame]["timestamp"], period)
                if abs(actual - expected) > 1e-9:
                    raise RuntimeError(f"match {self.match_id} native clock disagreement at frame {frame}")

    def is_home(self, team_id: int) -> bool:
        if int(team_id) == self.home_team_id:
            return True
        if int(team_id) == self.away_team_id:
            return False
        raise RuntimeError(f"unknown team {team_id} in match {self.match_id}")

    def active_outfield(self, frame: int, team_id: int) -> tuple[int, ...]:
        return active_outfield_player_ids(self.meta, frame, team_id)

    def _player_record(self, frame: int, player_id: int) -> dict[str, Any]:
        for record in self.rows[frame]["player_data"]:
            if int(record["player_id"]) == int(player_id):
                return record
        raise KeyError(f"player {player_id} absent from frame {frame}")

    def raw_xy(self, frame: int, player_id: int) -> np.ndarray:
        record = self._player_record(frame, player_id)
        values = np.asarray([record.get("x"), record.get("y")], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("invalid player coordinate")
        return values

    def detected(self, frame: int, player_id: int) -> bool:
        value = self._player_record(frame, player_id).get("is_detected")
        if not isinstance(value, bool):
            raise ValueError("missing non-Boolean player status")
        return value

    def ball_xy(self, frame: int) -> np.ndarray:
        record = self.rows[frame]["ball_data"]
        values = np.asarray([record.get("x"), record.get("y")], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("invalid ball coordinate")
        return values

    def ball_detected(self, frame: int) -> bool:
        value = self.rows[frame]["ball_data"].get("is_detected")
        if not isinstance(value, bool):
            raise ValueError("missing non-Boolean ball status")
        return value

    def canonical_player(self, frame: int, player_id: int) -> np.ndarray:
        xy = self.raw_xy(frame, player_id)
        return canonical_xy(xy[0], xy[1], self.meta["pitch_length"], self.meta["pitch_width"])

    def canonical_ball(self, frame: int) -> np.ndarray:
        xy = self.ball_xy(frame)
        return canonical_xy(xy[0], xy[1], self.meta["pitch_length"], self.meta["pitch_width"])

    def smooth_player(self, frame: int, player_id: int) -> np.ndarray:
        return np.mean([self.canonical_player(index, player_id) for index in (frame - 1, frame, frame + 1)], axis=0)

    def smooth_ball(self, frame: int) -> np.ndarray:
        return np.mean([self.canonical_ball(index) for index in (frame - 1, frame, frame + 1)], axis=0)

    def frame_support_valid(self, frame: int) -> bool:
        if frame in self.support_cache:
            return self.support_cache[frame]
        row = self.rows.get(frame)
        if row is None or row.get("period") not in (1, 2):
            self.support_cache[frame] = False
            return False
        seen: dict[int, set[int]] = {team: set() for team in self.team_ids}
        for record in row["player_data"]:
            player = int(record["player_id"])
            team = self.player_team.get(player)
            values = np.asarray([record.get("x"), record.get("y")], dtype=float)
            if team not in seen or not np.isfinite(values).all() or not isinstance(record.get("is_detected"), bool):
                self.support_cache[frame] = False
                return False
            if player not in self.goalkeepers:
                seen[team].add(player)
        valid = True
        for team in self.team_ids:
            expected = set(self.active_outfield(frame, team))
            valid &= len(expected) == 10 and seen[team] == expected
        self.support_cache[frame] = bool(valid)
        return bool(valid)

    def period_for_frame(self, frame: int) -> int:
        period = self.rows[frame]["period"]
        if period not in (1, 2):
            raise RuntimeError("missing period")
        return int(period)

    def anchor_support_reason(self, anchor: int) -> str | None:
        required = required_frame_ids(anchor)
        if any(frame not in self.rows for frame in required):
            return "cadence_or_period"
        period = self.period_for_frame(anchor)
        if any(self.period_for_frame(frame) != period for frame in required):
            return "cadence_or_period"
        if any(not self.frame_support_valid(frame) for frame in required):
            return "complete_player_support"
        ball_frames = range(anchor - 41, anchor + 2)
        try:
            if any(not np.isfinite(self.ball_xy(frame)).all() or not isinstance(self.rows[frame]["ball_data"].get("is_detected"), bool) for frame in ball_frames):
                return "ball_support"
        except (KeyError, ValueError):
            return "ball_support"
        if any(frame not in self.phase_coverage for frame in range(anchor - 40, anchor + 21)):
            return "not_continuously_ball_in_play"
        if self.rows[anchor]["possession"].get("group") not in {"home team", "away team"}:
            return "possession_at_anchor"
        return None

    def attacking_team(self, anchor: int) -> int:
        group = self.rows[anchor]["possession"]["group"]
        if group == "home team":
            return self.home_team_id
        if group == "away team":
            return self.away_team_id
        raise RuntimeError("missing anchor possession group")

    def provider_equivalence(self) -> dict[str, Any]:
        dataset = skillcorner.load(
            self.meta_path,
            self.tracking_path,
            coordinates="skillcorner",
            include_empty_frames=True,
            data_version="V3",
        )
        kloppy_frames = {(int(frame.frame_id), int(frame.period.id)): frame for frame in dataset.records}
        native_keys = {(frame, int(row["period"])) for frame, row in self.rows.items()}
        if native_keys != set(kloppy_frames):
            raise RuntimeError(f"match {self.match_id} native/Kloppy frame identity disagreement")
        player_sets_exact = True
        possession_exact = True
        coordinate_null_masks_exact = True
        max_time = 0.0
        max_player_coordinate = 0.0
        max_ball_coordinate = 0.0
        for frame_id, period in sorted(native_keys):
            native = self.rows[frame_id]
            parsed = kloppy_frames[(frame_id, period)]
            max_time = max(max_time, abs(parsed.timestamp.total_seconds() - timestamp_seconds(native["timestamp"], period)))
            native_players = {int(item["player_id"]): item for item in native["player_data"]}
            kloppy_players = {int(player.player_id): data for player, data in parsed.players_data.items()}
            player_sets_exact &= set(native_players) == set(kloppy_players)
            for player_id in native_players:
                raw = np.asarray([native_players[player_id].get("x"), native_players[player_id].get("y")], float)
                parsed_xy = kloppy_players[player_id].coordinates
                native_present = bool(np.isfinite(raw).all())
                parsed_present = parsed_xy is not None
                coordinate_null_masks_exact &= native_present == parsed_present
                if not native_present and not parsed_present:
                    continue
                if not native_present or not parsed_present:
                    raise RuntimeError(f"match {self.match_id} native/Kloppy player coordinate null disagreement")
                max_player_coordinate = max(max_player_coordinate, float(np.max(np.abs(raw - [parsed_xy.x, parsed_xy.y]))))
            native_ball = np.asarray([native["ball_data"].get("x"), native["ball_data"].get("y")], float)
            parsed_ball = parsed.ball_coordinates
            native_ball_present = bool(np.isfinite(native_ball).all())
            parsed_ball_present = parsed_ball is not None
            coordinate_null_masks_exact &= native_ball_present == parsed_ball_present
            if not native_ball_present and not parsed_ball_present:
                continue
            if not native_ball_present or not parsed_ball_present:
                raise RuntimeError(f"match {self.match_id} native/Kloppy ball coordinate null disagreement")
            max_ball_coordinate = max(max_ball_coordinate, float(np.max(np.abs(native_ball - [parsed_ball.x, parsed_ball.y]))))
            native_group = native["possession"].get("group")
            parsed_team = parsed.ball_owning_team.team_id if parsed.ball_owning_team else None
            expected_team = self.home_team_id if native_group == "home team" else self.away_team_id if native_group == "away team" else None
            possession_exact &= parsed_team == expected_team
        native_goalkeepers = set(self.goalkeepers)
        kloppy_goalkeepers = {
            int(player.player_id)
            for team in dataset.metadata.teams
            for player in team.players
            if str(player.starting_position) == "Goalkeeper"
        }
        team_ids = {int(team.team_id) for team in dataset.metadata.teams}
        exact = (
            player_sets_exact
            and possession_exact
            and coordinate_null_masks_exact
            and team_ids == set(self.team_ids)
            and native_goalkeepers == kloppy_goalkeepers
            and max_time <= 1e-9
            and max_player_coordinate <= 1e-12
            and max_ball_coordinate <= 1e-12
            and float(dataset.metadata.pitch_dimensions.pitch_length) == float(self.meta["pitch_length"])
            and float(dataset.metadata.pitch_dimensions.pitch_width) == float(self.meta["pitch_width"])
        )
        return {
            "match_id": self.match_id,
            "frames_compared": len(native_keys),
            "player_sets_exact": player_sets_exact,
            "team_ids_exact": team_ids == set(self.team_ids),
            "goalkeeper_ids_exact": native_goalkeepers == kloppy_goalkeepers,
            "possession_team_exact": possession_exact,
            "coordinate_null_masks_exact": coordinate_null_masks_exact,
            "max_period_time_difference_s": max_time,
            "max_player_coordinate_difference_m": max_player_coordinate,
            "max_ball_coordinate_difference_m": max_ball_coordinate,
            "pitch_dimensions_exact": float(dataset.metadata.pitch_dimensions.pitch_length) == float(self.meta["pitch_length"]) and float(dataset.metadata.pitch_dimensions.pitch_width) == float(self.meta["pitch_width"]),
            "Kloppy_drops_native_is_detected": True,
            "pass": exact,
        }


def path_length(points: Iterable[np.ndarray]) -> float:
    array = np.asarray(list(points), float)
    return float(np.linalg.norm(np.diff(array, axis=0), axis=1).sum())


def sorted_rank_ids(source: MatchSource, anchor: int, focal_id: int, defender_ids: tuple[int, ...], attack_sign: int, focal_start_y: float) -> tuple[int, ...]:
    focal = attacking_frame(source.smooth_player(anchor, focal_id)[None, :], attack_sign, focal_start_y)[0]
    defenders = attacking_frame(np.stack([source.smooth_player(anchor, player) for player in defender_ids]), attack_sign, focal_start_y)
    distances = np.linalg.norm(defenders - focal, axis=1)
    order = np.lexsort((np.asarray(defender_ids, int), distances))
    return tuple(int(defender_ids[index]) for index in order)


def continuity_valid(source: MatchSource, focal_id: int, rank_ids: tuple[int, ...], anchor: int) -> bool:
    try:
        focal_points = [source.raw_xy(frame, focal_id) for frame in range(anchor - 41, anchor + 2)]
        if any(not identity_step_is_valid(left, right) for left, right in zip(focal_points, focal_points[1:], strict=False)):
            return False
        for defender in rank_ids[:7]:
            points = [source.raw_xy(frame, defender) for frame in range(anchor - 1, anchor + 22)]
            if any(not identity_step_is_valid(left, right) for left, right in zip(points, points[1:], strict=False)):
                return False
    except (KeyError, ValueError):
        return False
    return True


def quality_valid(source: MatchSource, focal_id: int, rank_ids: tuple[int, ...], anchor: int) -> bool:
    focal = [source.detected(frame, focal_id) for frame in range(anchor - 41, anchor + 2)]
    ball = [source.ball_detected(frame) for frame in range(anchor - 41, anchor + 2)]
    defenders = [[source.detected(frame, defender) for frame in range(anchor - 1, anchor + 22)] for defender in rank_ids[:7]]
    return stricter_quality_pass(focal, ball, defenders)


def construct_row(source: MatchSource, anchor: int, focal_id: int) -> dict[str, Any]:
    period = source.period_for_frame(anchor)
    attacking_team = source.attacking_team(anchor)
    defending_team = source.away_team_id if attacking_team == source.home_team_id else source.home_team_id
    attackers = source.active_outfield(anchor, attacking_team)
    defenders = source.active_outfield(anchor, defending_team)
    if focal_id not in attackers or len(attackers) != 10 or len(defenders) != 10:
        raise RuntimeError("invalid active outfield set at supported anchor")
    attack_sign = goalward_sign(source.meta["home_team_side"], period, source.is_home(attacking_team))
    focal_start_raw = source.smooth_player(anchor - 20, focal_id)
    focal_start_y = float(focal_start_raw[1])
    rank_ids = sorted_rank_ids(source, anchor, focal_id, defenders, attack_sign, focal_start_y)
    if not continuity_valid(source, focal_id, rank_ids, anchor):
        raise ValueError("identity_gate")
    transform = lambda values: attacking_frame(np.asarray(values, float), attack_sign, focal_start_y)
    focal_prior = transform([source.smooth_player(frame, focal_id) for frame in range(anchor - 40, anchor - 19)])
    focal_exposure = transform([source.smooth_player(frame, focal_id) for frame in range(anchor - 20, anchor + 1)])
    focal_start = focal_exposure[0]
    focal_anchor = focal_exposure[-1]
    defender_start = transform([source.smooth_player(anchor - 20, player) for player in defenders])
    ball_start = transform(source.smooth_ball(anchor - 20)[None, :])[0]
    relative = []
    for frame in range(anchor, anchor + 21):
        positions = transform([source.smooth_player(frame, player) for player in rank_ids])
        relative.append((10.0 * positions - positions.sum(axis=0)) / 9.0)
    paths = np.linalg.norm(np.diff(np.asarray(relative), axis=0), axis=2).sum(axis=0)
    if not np.isfinite(paths).all():
        raise RuntimeError("nonfinite defender-relative path")
    width = float(np.ptp(defender_start[:, 1]))
    depth = float(np.ptp(defender_start[:, 0]))
    if width <= 0.0 or depth <= 0.0:
        raise RuntimeError("nonpositive defending-unit geometry")
    time_period_s = (anchor - source.period_start[period]) / 10.0
    return {
        "observation_id": f"{source.match_id}:{period}:{anchor}:{focal_id}",
        "match_id": str(source.match_id),
        "period": period,
        "anchor_frame": anchor,
        "anchor_time_period_s": time_period_s,
        "block_id": int(time_period_s // BLOCK_SECONDS),
        "Y_m": float(paths[:3].mean() - paths[3:7].mean()),
        "attacker_path_exposure_m": path_length(focal_exposure),
        "attacker_path_prior_m": path_length(focal_prior),
        "attacker_minus_unit_goalward_m": float(focal_start[0] - defender_start[:, 0].mean()),
        "attacker_ball_distance_start_m": float(np.linalg.norm(focal_start - ball_start)),
        "defending_unit_width_m": width,
        "defending_unit_depth_m": depth,
        "ball_minus_unit_goalward_m": float(ball_start[0] - defender_start[:, 0].mean()),
        "attacker_goalward_displacement_m": float(focal_anchor[0] - focal_start[0]),
        "attacker_outward_displacement_m": float(focal_anchor[1] - focal_start[1]),
        "quality_pass": quality_valid(source, focal_id, rank_ids, anchor),
        "focal_detected_fraction": detected_fraction(source.detected(frame, focal_id) for frame in range(anchor - 41, anchor + 2)),
        "ball_detected_fraction": detected_fraction(source.ball_detected(frame) for frame in range(anchor - 41, anchor + 2)),
        "minimum_D1_D7_detected_fraction": float(min(detected_fraction(source.detected(frame, defender) for frame in range(anchor - 1, anchor + 22)) for defender in rank_ids[:7])),
    }


def support_match(source: MatchSource) -> dict[str, Any]:
    """Evaluate only frozen provider/support/identity conditions, not Y."""
    exclusions: Counter[str] = Counter()
    candidate_anchors = 0
    retained_anchors: set[int] = set()
    retained_rows = 0
    majority_rows = 0
    focal_detection, ball_detection, defender_detection = [], [], []
    for period in (1, 2):
        for anchor in anchor_frames(source.period_start[period], source.period_end[period]):
            candidate_anchors += 1
            reason = source.anchor_support_reason(anchor)
            if reason:
                exclusions[reason] += 1
                continue
            attacking_team = source.attacking_team(anchor)
            defending_team = source.away_team_id if attacking_team == source.home_team_id else source.home_team_id
            attackers = source.active_outfield(anchor, attacking_team)
            defenders = source.active_outfield(anchor, defending_team)
            ball = source.smooth_ball(anchor)
            nearest = min(attackers, key=lambda player: (float(np.linalg.norm(source.smooth_player(anchor, player) - ball)), int(player)))
            attack_sign = goalward_sign(source.meta["home_team_side"], period, source.is_home(attacking_team))
            for focal in attackers:
                if focal == nearest:
                    continue
                start_y = float(source.smooth_player(anchor - 20, focal)[1])
                ranks = sorted_rank_ids(source, anchor, focal, defenders, attack_sign, start_y)
                if not continuity_valid(source, focal, ranks, anchor):
                    exclusions["identity_gate_row"] += 1
                    continue
                retained_anchors.add(anchor)
                retained_rows += 1
                focal_fraction = detected_fraction(source.detected(frame, focal) for frame in range(anchor - 41, anchor + 2))
                ball_fraction = detected_fraction(source.ball_detected(frame) for frame in range(anchor - 41, anchor + 2))
                defender_fraction = min(detected_fraction(source.detected(frame, defender) for frame in range(anchor - 1, anchor + 22)) for defender in ranks[:7])
                focal_detection.append(focal_fraction)
                ball_detection.append(ball_fraction)
                defender_detection.append(defender_fraction)
                if stricter_quality_pass(
                    [source.detected(frame, focal) for frame in range(anchor - 41, anchor + 2)],
                    [source.ball_detected(frame) for frame in range(anchor - 41, anchor + 2)],
                    [[source.detected(frame, defender) for frame in range(anchor - 1, anchor + 22)] for defender in ranks[:7]],
                ):
                    majority_rows += 1
    return {
        "match_id": source.match_id,
        "candidate_anchors": candidate_anchors,
        "retained_anchors": len(retained_anchors),
        "retained_rows": retained_rows,
        "mean_focal_detected_fraction": float(np.mean(focal_detection)) if focal_detection else math.nan,
        "mean_ball_detected_fraction": float(np.mean(ball_detection)) if ball_detection else math.nan,
        "mean_minimum_D1_D7_detected_fraction": float(np.mean(defender_detection)) if defender_detection else math.nan,
        "majority_detected_rows": majority_rows,
        "exclusions": dict(sorted(exclusions.items())),
    }


def construct_match(source: MatchSource) -> tuple[pd.DataFrame, dict[str, Any]]:
    exclusions: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    candidate_anchors = 0
    for period in (1, 2):
        for anchor in anchor_frames(source.period_start[period], source.period_end[period]):
            candidate_anchors += 1
            reason = source.anchor_support_reason(anchor)
            if reason:
                exclusions[reason] += 1
                continue
            attacking_team = source.attacking_team(anchor)
            attackers = source.active_outfield(anchor, attacking_team)
            ball = source.smooth_ball(anchor)
            nearest = min(attackers, key=lambda player: (float(np.linalg.norm(source.smooth_player(anchor, player) - ball)), int(player)))
            for focal in attackers:
                if focal == nearest:
                    continue
                try:
                    rows.append(construct_row(source, anchor, focal))
                except ValueError as error:
                    if str(error) != "identity_gate":
                        raise
                    exclusions["identity_gate_row"] += 1
    data = pd.DataFrame(rows)
    if data.empty:
        raise RuntimeError(f"match {source.match_id} retained no rows")
    if data.observation_id.duplicated().any() or not np.isfinite(data.loc[:, ["Y_m", *BASE]].to_numpy(float)).all():
        raise RuntimeError(f"match {source.match_id} has invalid constructed rows")
    anchors = int(data.anchor_frame.nunique())
    summary = {
        "match_id": source.match_id,
        "candidate_anchors": candidate_anchors,
        "retained_anchors": anchors,
        "retained_rows": int(len(data)),
        "period_1_anchors": int(data.loc[data.period == 1, "anchor_frame"].nunique()),
        "period_2_anchors": int(data.loc[data.period == 2, "anchor_frame"].nunique()),
        "mean_focal_detected_fraction": float(data.focal_detected_fraction.mean()),
        "mean_ball_detected_fraction": float(data.ball_detected_fraction.mean()),
        "mean_minimum_D1_D7_detected_fraction": float(data.minimum_D1_D7_detected_fraction.mean()),
        "majority_detected_rows": int(data.quality_pass.sum()),
        "majority_detected_anchors": int(data.loc[data.quality_pass, "anchor_frame"].nunique()),
        "exclusions": dict(sorted(exclusions.items())),
    }
    return data.sort_values(["period", "anchor_frame", "observation_id"], kind="mergesort").reset_index(drop=True), summary


def fit(frame: pd.DataFrame) -> tuple[np.ndarray, int, tuple[str, ...]]:
    return design.fit_equal_match_ols(frame.Y_m.to_numpy(float), frame.loc[:, BASE].to_numpy(float), frame.match_id.to_numpy())


def continuous_map(beta: np.ndarray) -> dict[str, float]:
    return {name: float(value) for name, value in zip(BASE, beta[-len(BASE):], strict=True)}


def primary_fit_table(data: pd.DataFrame, matches: tuple[str, ...]) -> tuple[dict[str, float], int, pd.DataFrame, pd.DataFrame]:
    beta, rank, _ = fit(data)
    per_match, lomo = [], []
    for match in matches:
        local = data.loc[data.match_id == match]
        local_beta, local_rank, _ = fit(local)
        local_map = continuous_map(local_beta)
        per_match.append({
            "match_id": match,
            "eligible_rows": int(len(local)),
            "eligible_anchors": int(local.anchor_frame.nunique()),
            "model_rank": local_rank,
            "beta_goalward_m_per_m": local_map["attacker_goalward_displacement_m"],
            "beta_outward_m_per_m": local_map["attacker_outward_displacement_m"],
            "outward_minus_goalward_m_per_m": local_map["attacker_outward_displacement_m"] - local_map["attacker_goalward_displacement_m"],
            "positive_contrast": bool(local_map["attacker_outward_displacement_m"] - local_map["attacker_goalward_displacement_m"] > 0.0),
        })
        leave = data.loc[data.match_id != match]
        leave_beta, leave_rank, _ = fit(leave)
        leave_map = continuous_map(leave_beta)
        lomo.append({
            "heldout_match_id": match,
            "training_rows": int(len(leave)),
            "model_rank": leave_rank,
            "outward_minus_goalward_m_per_m": leave_map["attacker_outward_displacement_m"] - leave_map["attacker_goalward_displacement_m"],
        })
    return continuous_map(beta), rank, pd.DataFrame(per_match), pd.DataFrame(lomo)


def trim_fit(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    keep = np.ones(len(data), dtype=bool)
    bounds: dict[str, dict[str, list[float]]] = {}
    for match, part in data.groupby("match_id", sort=True):
        local = np.ones(len(part), dtype=bool)
        bounds[match] = {}
        for column in ("attacker_goalward_displacement_m", "attacker_outward_displacement_m"):
            low, high = np.quantile(part[column].to_numpy(float), [0.025, 0.975], method="linear")
            bounds[match][column] = [float(low), float(high)]
            local &= (part[column].to_numpy(float) >= low) & (part[column].to_numpy(float) <= high)
        keep[part.index.to_numpy()] = local
    trimmed = data.loc[keep].reset_index(drop=True)
    beta, rank, _ = fit(trimmed)
    mapping = continuous_map(beta)
    return trimmed, {
        "rows_retained": int(len(trimmed)),
        "retained_proportion": float(len(trimmed) / len(data)),
        "beta_goalward_m_per_m": mapping["attacker_goalward_displacement_m"],
        "beta_outward_m_per_m": mapping["attacker_outward_displacement_m"],
        "outward_minus_goalward_m_per_m": mapping["attacker_outward_displacement_m"] - mapping["attacker_goalward_displacement_m"],
        "model_rank": rank,
        "bounds": bounds,
    }


def block_statistics(data: pd.DataFrame, matches: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray, dict[tuple[str, int, int], np.ndarray], dict[tuple[str, int], list[tuple[str, int, int]]]]:
    x, _names = design.matrix(data.loc[:, BASE].to_numpy(float), data.match_id.to_numpy())
    y = data.Y_m.to_numpy(float)
    groups = {key: value.to_numpy() for key, value in data.groupby(["match_id", "period", "block_id"], sort=True).groups.items()}
    strata = {
        (match, period): [key for key in groups if key[:2] == (match, period)]
        for match in matches
        for period in sorted(data.loc[data.match_id == match, "period"].unique())
    }
    if any(not values for values in strata.values()):
        raise RuntimeError("represented match-period lacks a frozen 60-second block")
    return x, y, groups, strata


def bootstrap(data: pd.DataFrame, matches: tuple[str, ...]) -> dict[str, Any]:
    x, y, groups, strata = block_statistics(data, matches)
    sufficient = {key: (x[index].T @ x[index], x[index].T @ y[index], len(index)) for key, index in groups.items()}
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    contrasts: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        frequencies: Counter[tuple[str, int, int]] = Counter()
        for keys in strata.values():
            frequencies.update(keys[int(choice)] for choice in rng.integers(0, len(keys), len(keys)))
        xtx = np.zeros((x.shape[1], x.shape[1]), dtype=float)
        xty = np.zeros(x.shape[1], dtype=float)
        for match in matches:
            selected = [(key, count) for key, count in frequencies.items() if key[0] == match]
            total = sum(count * sufficient[key][2] for key, count in selected)
            if total == 0:
                raise RuntimeError("empty bootstrap match draw")
            for key, count in selected:
                weight = count / total
                xtx += weight * sufficient[key][0]
                xty += weight * sufficient[key][1]
        if np.linalg.matrix_rank(xtx) != x.shape[1]:
            continue
        beta, _, _, _ = np.linalg.lstsq(xtx, xty, rcond=None)
        contrasts.append(float(beta[-1] - beta[-2]))
    array = np.asarray(contrasts, float)
    if len(array) < MINIMUM_BOOTSTRAP_VALID:
        raise RuntimeError("fewer than 1,900 valid frozen bootstrap replicates")
    return {
        "replicates_requested": BOOTSTRAP_REPLICATES,
        "valid_replicates": int(len(array)),
        "seed": BOOTSTRAP_SEED,
        "block_seconds": BLOCK_SECONDS,
        "ci_low": float(np.quantile(array, 0.025)),
        "ci_high": float(np.quantile(array, 0.975)),
    }


def classification(
    valid: bool,
    matches: tuple[str, ...],
    contrast: float,
    bootstrap_summary: dict[str, Any],
    per_match: pd.DataFrame,
    lomo: pd.DataFrame,
    trim: dict[str, Any],
    quality: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    minimum_positive = math.ceil(0.70 * len(matches))
    positive_matches = int(per_match.positive_contrast.sum())
    trim_ratio = abs(trim["outward_minus_goalward_m_per_m"] / contrast) if contrast else math.nan
    quality_ratio = abs(quality["outward_minus_goalward_m_per_m"] / contrast) if contrast else math.nan
    gates = {
        "at_least_8_valid_matches": len(matches) >= 8,
        "pooled_contrast_strictly_positive": contrast > 0.0,
        "bootstrap_95_percent_interval_strictly_positive": bootstrap_summary["ci_low"] > 0.0,
        "at_least_70_percent_match_contrasts_positive": positive_matches >= minimum_positive,
        "all_leave_one_match_out_contrasts_positive": bool((lomo.outward_minus_goalward_m_per_m > 0.0).all()),
        "trim_positive_and_50_to_150_percent_magnitude": bool(trim["outward_minus_goalward_m_per_m"] > 0.0 and 0.5 <= trim_ratio <= 1.5),
        "quality_full_rank_positive_and_50_to_150_percent_magnitude": bool(quality["full_rank"] and quality["outward_minus_goalward_m_per_m"] > 0.0 and 0.5 <= quality_ratio <= 1.5),
    }
    if not valid:
        status = "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION INVALID"
    elif all(gates.values()):
        status = "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION SUPPORTED"
    elif contrast > 0.0:
        status = "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION MIXED"
    else:
        status = "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION NOT SUPPORTED"
    return status, {
        "valid_execution": valid,
        "positive_matches": positive_matches,
        "valid_matches": len(matches),
        "positive_match_percent": 100.0 * positive_matches / len(matches),
        "minimum_positive_matches_required": minimum_positive,
        "trimmed_to_full_absolute_ratio": trim_ratio,
        "quality_to_full_absolute_ratio": quality_ratio,
        "gates": gates,
    }


def write_report(result: dict[str, Any], output: Path) -> None:
    primary, boot, quality = result["primary"], result["bootstrap"], result["quality_sensitivity"]
    lines = [
        "# Defensive Reorganization Spatial Form v1 — SkillCorner external replication",
        "",
        f"**External classification:** **{result['classification']}**",
        "",
        "This prospectively governed third-environment study uses SkillCorner Open Data only. It tests the predeclared outward-minus-goalward contrast on subsequent near-minus-middle defender-relative path. It is observational geometry, not a tactical, causal, or value result.",
        "",
        "## Primary result",
        "",
        "| Quantity | Estimate |",
        "|---|---:|",
        f"| Goalward coefficient | {primary['beta_goalward_m_per_m']:.6f} m/m |",
        f"| Outward coefficient | {primary['beta_outward_m_per_m']:.6f} m/m |",
        f"| Outward minus goalward | {primary['outward_minus_goalward_m_per_m']:.6f} m/m |",
        f"| Frozen 95% interval | [{boot['ci_low']:.6f}, {boot['ci_high']:.6f}] |",
        f"| 5 m outward versus goalward translation | {primary['five_m_translation_m']:.6f} m |",
        "",
        "The 5 m translation is a model-predicted difference in subsequent near-minus-middle defender-relative reorganization between straight 5 m outward and straight 5 m goalward displacement under equal frozen path magnitude and starting context. It is not value.",
        "",
        "## Support and robustness",
        "",
        f"The primary sample retained {result['sample']['rows']:,} rows across {result['sample']['anchors']:,} anchors and {result['sample']['valid_matches']} valid matches. The frozen joint trim retained {result['trim']['rows_retained']:,} rows ({100.0 * result['trim']['retained_proportion']:.2f}%). The majority-directly-detected sensitivity retained {quality['rows']:,} rows across {quality['anchors']:,} anchors; its contrast was {quality['outward_minus_goalward_m_per_m']:.6f} m/m.",
        "",
        "## Boundary",
        "",
        "The result does not establish attacker influence or causation, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, space creation, tactical success, player quality, gravity, or attacking value. No DRD residual, Metrica Game 3 datum, player/team ranking, alternate spatial representation, or cross-provider pooled meta-analysis was created.",
    ]
    text = "\n".join(lines) + "\n"
    (output / "result_report.md").write_text(text, encoding="utf-8")
    DOC_RESULT.parent.mkdir(parents=True, exist_ok=True)
    DOC_RESULT.write_text(text, encoding="utf-8")


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "reproduction.json", "final_hashes.json"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def execute(data_dir: Path, output: Path = OUTPUT, preflight_only: bool = False) -> dict[str, Any]:
    firewall = verify_frozen(output) if not preflight_only else {"frozen_hashes_verified": {str(path.relative_to(ROOT)): sha(path) for path in FROZEN}}
    provider_rows, support_rows, samples = [], [], []
    invalid: dict[str, str] = {}
    for match_id in FORMAL_MATCHES:
        try:
            source = MatchSource(match_id, data_dir)
            equivalence = source.provider_equivalence()
            provider_rows.append(equivalence)
            if not equivalence["pass"]:
                invalid[str(match_id)] = "native_Kloppy_equivalence_failure"
                continue
            support_summary = support_match(source)
            if preflight_only:
                support_rows.append(support_summary)
                continue
            sample, summary = construct_match(source)
            for key in ("retained_anchors", "retained_rows", "majority_detected_rows"):
                if summary[key] != support_summary[key]:
                    raise RuntimeError(f"match {match_id} pre-outcome support disagrees with outcome construction for {key}")
            support_rows.append(summary)
            samples.append(sample)
        except Exception as error:
            invalid[str(match_id)] = f"provider_or_support_failure:{type(error).__name__}:{error}"
    valid_matches = tuple(str(row["match_id"]) for row in support_rows if str(row["match_id"]) not in invalid)
    preflight = {
        "firewall": firewall,
        "formal_matches": list(FORMAL_MATCHES),
        "prospectively_excluded_match": {str(EXCLUDED_MATCH): "provider_top_level_status_not_started_conflicts_with_complete_two_period_files"},
        "provider_equivalence": provider_rows,
        "support": support_rows,
        "invalid_matches": invalid,
        "valid_matches": list(valid_matches),
        "minimum_valid_matches": 8,
    }
    if preflight_only:
        return preflight
    if len(valid_matches) < 8:
        raise RuntimeError(f"fewer than eight valid SkillCorner matches: {preflight}")
    data = pd.concat(samples, ignore_index=True).sort_values(["match_id", "period", "anchor_frame", "observation_id"], kind="mergesort").reset_index(drop=True)
    if set(data.match_id) != set(valid_matches) or data.observation_id.duplicated().any():
        raise RuntimeError("invalid final SkillCorner observation set")
    pooled, pooled_rank, per_match, lomo = primary_fit_table(data, valid_matches)
    contrast = pooled["attacker_outward_displacement_m"] - pooled["attacker_goalward_displacement_m"]
    primary = {
        "beta_goalward_m_per_m": pooled["attacker_goalward_displacement_m"],
        "beta_outward_m_per_m": pooled["attacker_outward_displacement_m"],
        "outward_minus_goalward_m_per_m": contrast,
        "five_m_translation_m": 5.0 * contrast,
        "pooled_model_rank": pooled_rank,
    }
    bootstrap_summary = bootstrap(data, valid_matches)
    _trimmed, trim = trim_fit(data)
    quality_data = data.loc[data.quality_pass].reset_index(drop=True)
    if quality_data.empty:
        quality = {"rows": 0, "anchors": 0, "matches": 0, "full_rank": False, "outward_minus_goalward_m_per_m": math.nan, "beta_goalward_m_per_m": math.nan, "beta_outward_m_per_m": math.nan}
    else:
        quality_beta, quality_rank, _ = fit(quality_data)
        quality_map = continuous_map(quality_beta)
        quality = {
            "rows": int(len(quality_data)),
            "anchors": int(quality_data.anchor_frame.nunique()),
            "matches": int(quality_data.match_id.nunique()),
            "full_rank": quality_rank == len(BASE) + quality_data.match_id.nunique(),
            "model_rank": quality_rank,
            "beta_goalward_m_per_m": quality_map["attacker_goalward_displacement_m"],
            "beta_outward_m_per_m": quality_map["attacker_outward_displacement_m"],
            "outward_minus_goalward_m_per_m": quality_map["attacker_outward_displacement_m"] - quality_map["attacker_goalward_displacement_m"],
        }
    hard_qc = {
        "frozen_hashes": True,
        "exact_formal_match_set_only": set(valid_matches).issubset({str(item) for item in FORMAL_MATCHES}),
        "at_least_eight_valid_matches": len(valid_matches) >= 8,
        "provider_equivalence_every_valid_match": all(row["pass"] for row in provider_rows),
        "unique_observation_ids": not data.observation_id.duplicated().any(),
        "finite_target_and_model_columns": bool(np.isfinite(data.loc[:, ["Y_m", *BASE]].to_numpy(float)).all()),
        "complete_anchor_vectors": bool((data.groupby(["match_id", "period", "anchor_frame"]).size() == 9).all()),
        "pooled_full_rank": pooled_rank == len(BASE) + len(valid_matches),
        "per_match_full_rank": bool((per_match.model_rank == len(BASE) + 1).all()),
        "lomo_full_rank": bool((lomo.model_rank == len(BASE) + len(valid_matches) - 1).all()),
        "bootstrap_valid_at_least_1900": bootstrap_summary["valid_replicates"] >= MINIMUM_BOOTSTRAP_VALID,
        "no_interpolation": True,
        "no_row_level_provider_outputs_written": True,
        "DRD_residual_not_read": True,
        "Metrica_Game_3_untouched": True,
        "player_team_rankings_not_created": True,
        "alternate_spatial_representation_not_tested": True,
        "cross_provider_meta_analysis_not_created": True,
    }
    valid_execution = all(hard_qc.values())
    status, criteria = classification(valid_execution, valid_matches, contrast, bootstrap_summary, per_match, lomo, trim, quality)
    output.mkdir(parents=True, exist_ok=True)
    sample_summary = pd.DataFrame(support_rows)
    sample_summary["exclusions_json"] = sample_summary.exclusions.map(lambda value: json.dumps(value, sort_keys=True))
    sample_summary = sample_summary.drop(columns="exclusions")
    write_json(output / "result.json", {
        "classification": status,
        "firewall": firewall,
        "sample": {"rows": int(len(data)), "anchors": int(data.anchor_frame.nunique()), "valid_matches": len(valid_matches), "match_ids": list(valid_matches)},
        "primary": primary,
        "bootstrap": bootstrap_summary,
        "trim": trim,
        "quality_sensitivity": quality,
        "classification_criteria": criteria,
        "hard_qc": hard_qc,
        "execution": {"DRD_residuals_read": False, "Metrica_Game_3_accessed": False, "cross_provider_pooled_meta_analysis": False, "alternate_spatial_representation": False},
    })
    sample_summary.to_csv(output / "sample_summary.csv", index=False)
    pd.DataFrame(provider_rows).to_csv(output / "provider_equivalence.csv", index=False)
    pd.DataFrame([{"match_id": key, "reason": value} for key, value in sorted(invalid.items())]).to_csv(output / "invalid_matches.csv", index=False)
    per_match.to_csv(output / "per_match_coefficients.csv", index=False)
    lomo.to_csv(output / "leave_one_match_out.csv", index=False)
    pd.DataFrame([{"column": key, "estimate_m_per_m": value} for key, value in pooled.items()]).to_csv(output / "pooled_coefficients.csv", index=False)
    pd.DataFrame([{**primary, "ci_low": bootstrap_summary["ci_low"], "ci_high": bootstrap_summary["ci_high"], "valid_bootstrap_replicates": bootstrap_summary["valid_replicates"]}]).to_csv(output / "primary_contrast.csv", index=False)
    pd.DataFrame([{key: value for key, value in trim.items() if key != "bounds"}]).to_csv(output / "trim_robustness.csv", index=False)
    pd.DataFrame([quality]).to_csv(output / "quality_sensitivity.csv", index=False)
    write_json(output / "classification_criteria.json", criteria)
    write_json(output / "hard_qc.json", hard_qc)
    write_json(output / "manifest.json", {
        "protocol_sha256": sha(PROTOCOL),
        "configuration_sha256": sha(CONFIG),
        "freeze_ledger_sha256": sha(LEDGER),
        "preexecution_support_reconciliation_sha256": sha(RECONCILIATION),
        "implementation_sha256": sha(Path(__file__)),
        "data_repository_commit": "c1e17a0cc3e07e1774b52d929c1a0b85115143fc",
        "formal_matches": list(FORMAL_MATCHES),
        "prospective_match_exclusion": EXCLUDED_MATCH,
        "kloppy_version": "3.19.0",
        "classification": status,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "publication_policy": "compact_aggregate_outputs_only",
    })
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    write_report(result, output)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    comparisons = []
    for name in ledger:
        left, right = primary / name, rerun / name
        comparisons.append({"file": name, "primary_sha256": sha(left), "rerun_sha256": sha(right), "byte_identical": left.read_bytes() == right.read_bytes()})
    result = {"files_compared": len(comparisons), "all_governed_outputs_byte_identical": bool(all(row["byte_identical"] for row in comparisons)), "comparisons": comparisons}
    write_json(primary / "reproduction.json", result)
    write_json(primary / "final_hashes.json", {**ledger, "governed_hashes.json": sha(primary / "governed_hashes.json"), "reproduction.json": sha(primary / "reproduction.json")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.verify_against:
        result = verify(args.output, args.verify_against)
    else:
        result = execute(args.data_dir, args.output, args.preflight_only)
    print(json.dumps(clean(result), sort_keys=True))


if __name__ == "__main__":
    main()
