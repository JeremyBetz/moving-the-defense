"""Outcome-blind audit of start-distance defender-rank composition.

The runner projects only IDs, start ranks/distances, and strictly prior fields
from the closed concurrent-geometry ledgers. It never selects a concurrent
response, coverage outcome, or future-geometry column.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
from scipy.optimize import minimize
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import attacking_continuous_movement_game1_v1 as metrica1  # noqa: E402
import attacking_continuous_movement_game2_v1 as metrica2  # noqa: E402
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import concurrent_attacker_defensive_geometry_idsse_v1 as idsse  # noqa: E402


CONFIG = ROOT / "config/defender_rank_composition_audit.json"
DEFAULT_OUTPUT = ROOT / "outputs/defender_rank_composition_audit"
DT = 0.04
GEOMETRY_TOLERANCE_M = 1e-6

COMMON_COLUMNS = (
    "observation_id",
    "period",
    "time_period_s",
    "attacker_key",
    "attacking_team",
    "defending_team",
    "block_id",
    "defender_key",
    "distance_rank",
    "distance_m",
    "prior_attacker_path_m",
    "prior_focal_relative_path_m",
    "prior_defensive_centroid_path_m",
    "prior_other_nine_mean_absolute_path_m",
)
IDSSE_EXTRA_COLUMNS = ("match_id", "time_utc_ns")
FORBIDDEN_TOKENS = (
    "concurrent_attacker_path",
    "concurrent_focal_relative",
    "concurrent_endpoint_deformation",
    "primary_aard",
    "parallel_m",
    "orthogonal_m",
    "radial_m",
    "coverage",
    "future",
)

SUMMARY_VARIABLES = (
    "attacker_defender_start_distance_m",
    "defender_fixed_x_m",
    "defender_fixed_y_m",
    "defender_own_goal_depth_m",
    "defender_goalward_offset_from_centroid_m",
    "defender_lateral_offset_from_centroid_m",
    "defender_abs_lateral_offset_from_centroid_m",
    "defender_centroid_distance_m",
    "ball_defender_distance_m",
    "prior_absolute_path_m",
    "prior_focal_relative_path_m",
    "prior_terminal_speed_mps",
    "prior_defensive_centroid_path_m",
    "prior_other_nine_mean_absolute_path_m",
    "prior_attacker_path_m",
    "local_two_neighbor_mean_distance_m",
    "unit_depth_span_m",
    "unit_width_span_m",
    "attacker_goalward_offset_from_centroid_m",
    "attacker_abs_lateral_offset_from_centroid_m",
    "ball_goalward_offset_from_centroid_m",
    "ball_abs_lateral_offset_from_centroid_m",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        x = float(value)
        return x if math.isfinite(x) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.12g", lineterminator="\n")


def verify_frozen(config: dict[str, Any]) -> dict[str, Any]:
    mismatches = {}
    for relative, expected in config["frozen_input_hashes"].items():
        path = ROOT / relative
        actual = sha256(path)
        if actual != expected:
            mismatches[relative] = {"expected": expected, "actual": actual}
    if mismatches:
        raise RuntimeError(f"frozen input hash mismatch: {mismatches}")
    if (ROOT / "outputs/defensive_coverage_redistribution_game1_v3").exists():
        raise RuntimeError("v3 empirical coverage output exists")
    return {
        "frozen_input_hashes_match": True,
        "coverage_v3_output_absent": True,
        "game3_not_accessed": True,
    }


def _polars_to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({name: frame[name].to_numpy() for name in frame.columns})


def load_rank_ledger(path: Path, match_id: str | None = None) -> pd.DataFrame:
    schema = pl.scan_parquet(path).collect_schema()
    selected = list(COMMON_COLUMNS)
    if "match_id" in schema:
        selected += list(IDSSE_EXTRA_COLUMNS)
    if any(any(token in name for token in FORBIDDEN_TOKENS) for name in selected):
        raise RuntimeError("forbidden response column entered the safe projection")
    frame = pl.scan_parquet(path).select(selected).collect()
    data = _polars_to_pandas(frame)
    if match_id is not None:
        data["match_id"] = match_id
    data = data.rename(
        columns={"distance_m": "attacker_defender_start_distance_m"}
    )
    required = set(range(1, 11))
    vectors = data.groupby("observation_id", sort=False).distance_rank.agg(
        lambda x: set(map(int, x))
    )
    if len(data) != 10 * len(vectors) or not vectors.map(lambda x: x == required).all():
        raise RuntimeError(f"rank ledger is not complete D1-D10: {path}")
    return data.sort_values(
        ["match_id", "period", "time_period_s", "attacker_key", "distance_rank"],
        kind="mergesort",
    ).reset_index(drop=True)


def path_length(values: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(values, axis=0), axis=1).sum(dtype=np.float64))


def _centered_seven(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(values).all(axis=1)
    if len(values) != 7 or not valid.all():
        return np.full(2, np.nan)
    return values.mean(axis=0, dtype=np.float64)


def metrica_ball_and_goal_sign(game_number: int) -> tuple[dict, dict, dict]:
    adapter = metrica1.metrica
    if game_number == 1:
        home, away = adapter.game1_paths(ROOT)
        match_id = "metrica:sample-game-1"
    else:
        home, away = adapter.game_paths(ROOT, game_number)
        match_id = f"metrica:sample-game-{game_number}"
    frame_index = adapter.read_provider_frame_index(home)
    dataset = adapter.load_dataset(home, away)
    pieces = []
    for chunk in adapter.iter_canonical_polars_chunks(
        dataset, frame_index, match_id=match_id, frames_per_chunk=2500
    ):
        pieces.append(
            chunk.filter(
                (pl.col("entity_type") == "ball") | pl.col("is_goalkeeper")
            ).select(
                [
                    "period",
                    "time_period_s",
                    "entity_type",
                    "team_key",
                    "x_m",
                    "y_m",
                    "coordinate_valid",
                    "support_state",
                ]
            )
        )
    q = _polars_to_pandas(pl.concat(pieces))
    q["valid"] = (
        q.coordinate_valid.fillna(False).astype(bool)
        & q.support_state.eq("observed")
        & np.isfinite(q[["x_m", "y_m"]].to_numpy(float)).all(axis=1)
    )
    balls = {}
    for period, group in q.loc[q.entity_type == "ball"].groupby("period", sort=True):
        group = group.sort_values("time_period_s", kind="mergesort").reset_index(drop=True)
        xy = group[["x_m", "y_m"]].to_numpy(float)
        valid = group.valid.to_numpy(bool)
        for i in range(3, len(group) - 3):
            point = _centered_seven(xy[i - 3 : i + 4], valid[i - 3 : i + 4])
            balls[(int(period), round(float(group.time_period_s.iloc[i]), 2))] = point
    goal_sign, sign_support_end = {}, {}
    keepers = q.loc[q.entity_type == "player"]
    for (period, team), group in keepers.groupby(["period", "team_key"], sort=True):
        group = group.loc[group.valid]
        opening = float(group.time_period_s.min())
        values = group.loc[group.time_period_s <= opening + 2.0, "x_m"].to_numpy(float)
        if len(values) == 0:
            raise RuntimeError(f"goalkeeper orientation unavailable: G{game_number} P{period} {team}")
        median_x = float(np.median(values))
        if abs(median_x) < 1.0:
            raise RuntimeError(f"ambiguous goalkeeper orientation: G{game_number} P{period} {team}")
        goal_sign[(int(period), str(team))] = 1.0 if median_x > 0 else -1.0
        sign_support_end[(int(period), str(team))] = opening + 2.0
    return balls, goal_sign, sign_support_end


def feature_rows_for_observation(
    group: pd.DataFrame,
    defender_prior: np.ndarray,
    attacker_prior: np.ndarray,
    ball_start: np.ndarray,
    goal_sign: float,
    provider: str,
) -> list[dict[str, Any]]:
    group = group.sort_values("distance_rank", kind="mergesort").reset_index(drop=True)
    if defender_prior.shape[0] != 10 or defender_prior.shape[2] != 2:
        raise RuntimeError("defender prior geometry must be 10 by time by xy")
    d0 = defender_prior[:, -1, :]
    a0 = attacker_prior[-1]
    centroid = d0.mean(axis=0, dtype=np.float64)
    distances = np.linalg.norm(d0 - a0, axis=1)
    if np.max(
        np.abs(distances - group.attacker_defender_start_distance_m.to_numpy(float))
    ) > GEOMETRY_TOLERANCE_M:
        raise RuntimeError(f"start distance/rank reconstruction differs: {group.observation_id.iloc[0]}")
    if np.any(np.diff(distances) < -GEOMETRY_TOLERANCE_M):
        raise RuntimeError(f"reconstructed start distances violate rank order: {group.observation_id.iloc[0]}")
    pair = np.linalg.norm(d0[:, None, :] - d0[None, :, :], axis=2)
    pair[np.eye(10, dtype=bool)] = np.inf
    local_two = np.sort(pair, axis=1)[:, :2].mean(axis=1)
    prior_absolute = np.asarray([path_length(xy) for xy in defender_prior])
    prior_relative = np.asarray([
        path_length(
            defender_prior[j]
            - np.delete(defender_prior, j, axis=0).mean(axis=0, dtype=np.float64)
        )
        for j in range(10)
    ])
    prior_centroid = path_length(defender_prior.mean(axis=0, dtype=np.float64))
    prior_other_nine = (prior_absolute.sum(dtype=np.float64) - prior_absolute) / 9.0
    if np.max(
        np.abs(prior_relative - group.prior_focal_relative_path_m.to_numpy(float))
    ) > 1e-6:
        raise RuntimeError(f"prior relative path reconstruction differs: {group.observation_id.iloc[0]}")
    if abs(prior_centroid - float(group.prior_defensive_centroid_path_m.iloc[0])) > 1e-6:
        raise RuntimeError(f"prior centroid path reconstruction differs: {group.observation_id.iloc[0]}")
    if np.max(
        np.abs(prior_other_nine - group.prior_other_nine_mean_absolute_path_m.to_numpy(float))
    ) > 1e-6:
        raise RuntimeError(f"prior absolute-path identity differs: {group.observation_id.iloc[0]}")
    terminal_speed = np.linalg.norm(
        defender_prior[:, -1, :] - defender_prior[:, -2, :], axis=1
    ) / DT
    prior_attacker = path_length(attacker_prior)
    ball_valid = np.isfinite(ball_start).all()
    common = {
        "provider": provider,
        "match_id": str(group.match_id.iloc[0]),
        "observation_id": str(group.observation_id.iloc[0]),
        "period": int(group.period.iloc[0]),
        "time_period_s": float(group.time_period_s.iloc[0]),
        "attacker_key": str(group.attacker_key.iloc[0]),
        "attacking_team": str(group.attacking_team.iloc[0]),
        "defending_team": str(group.defending_team.iloc[0]),
        "unit_depth_span_m": float(np.ptp(d0[:, 0])),
        "unit_width_span_m": float(np.ptp(d0[:, 1])),
        "attacker_goalward_offset_from_centroid_m": float(goal_sign * (a0[0] - centroid[0])),
        "attacker_abs_lateral_offset_from_centroid_m": float(abs(a0[1] - centroid[1])),
        "ball_goalward_offset_from_centroid_m": (
            float(goal_sign * (ball_start[0] - centroid[0])) if ball_valid else np.nan
        ),
        "ball_abs_lateral_offset_from_centroid_m": (
            float(abs(ball_start[1] - centroid[1])) if ball_valid else np.nan
        ),
        "prior_attacker_path_m": prior_attacker,
    }
    if abs(prior_attacker - float(group.prior_attacker_path_m.iloc[0])) > 1e-6:
        raise RuntimeError(f"prior attacker path differs: {group.observation_id.iloc[0]}")
    rows = []
    for j, source in group.iterrows():
        lateral = float(d0[j, 1] - centroid[1])
        row = {
            **common,
            "defender_key": str(source.defender_key),
            "distance_rank": int(source.distance_rank),
            "rank_group": (
                "near" if int(source.distance_rank) <= 3 else
                "middle" if int(source.distance_rank) <= 7 else "far"
            ),
            "attacker_defender_start_distance_m": float(source.attacker_defender_start_distance_m),
            "defender_fixed_x_m": float(d0[j, 0]),
            "defender_fixed_y_m": float(d0[j, 1]),
            "defender_own_goal_depth_m": float(52.5 - goal_sign * d0[j, 0]),
            "defender_goalward_offset_from_centroid_m": float(goal_sign * (d0[j, 0] - centroid[0])),
            "defender_lateral_offset_from_centroid_m": lateral,
            "defender_abs_lateral_offset_from_centroid_m": abs(lateral),
            "defender_centroid_distance_m": float(np.linalg.norm(d0[j] - centroid)),
            "ball_defender_distance_m": (
                float(np.linalg.norm(d0[j] - ball_start)) if ball_valid else np.nan
            ),
            "prior_absolute_path_m": float(prior_absolute[j]),
            "prior_focal_relative_path_m": float(source.prior_focal_relative_path_m),
            "prior_terminal_speed_mps": float(terminal_speed[j]),
            "prior_defensive_centroid_path_m": float(source.prior_defensive_centroid_path_m),
            "prior_other_nine_mean_absolute_path_m": float(source.prior_other_nine_mean_absolute_path_m),
            "local_two_neighbor_mean_distance_m": float(local_two[j]),
        }
        rows.append(row)
    return rows


def extract_metrica(
    data: pd.DataFrame, game_number: int
) -> tuple[pd.DataFrame, dict, dict]:
    if game_number == 1:
        players, _frames, provenance = metrica1.load_game1()
    else:
        players, _frames, provenance, _support = metrica2.load_game2_from_frozen_support()
    lookup = {(int(p.period), str(p.player_key)): p for p in players}
    balls, signs, sign_support_end = metrica_ball_and_goal_sign(game_number)
    for (period, team), end_time in sign_support_end.items():
        anchors = data.loc[
            (data.period == period) & (data.defending_team.astype(str) == team),
            "time_period_s",
        ]
        if not anchors.empty and float(anchors.min()) + 1e-9 < end_time:
            raise RuntimeError(
                f"goalward-sign support is future to an audited anchor: "
                f"G{game_number} P{period} {team}"
            )
    rows = []
    for _obs, group in data.groupby("observation_id", sort=False):
        first = group.iloc[0]
        period, t = int(first.period), float(first.time_period_s)
        ordered = group.sort_values("distance_rank", kind="mergesort")
        defender_prior = []
        for key in ordered.defender_key.astype(str):
            segment = bridge.segment(lookup[(period, key)], t - 2.0, t)
            if segment is None:
                raise RuntimeError(f"closed Metrica defender support unavailable: {first.observation_id} {key}")
            defender_prior.append(segment)
        attacker_prior = bridge.segment(lookup[(period, str(first.attacker_key))], t - 2.0, t)
        if attacker_prior is None:
            raise RuntimeError(f"closed Metrica attacker support unavailable: {first.observation_id}")
        ball = balls.get((period, round(t, 2)), np.full(2, np.nan))
        rows.extend(
            feature_rows_for_observation(
                group,
                np.stack(defender_prior),
                attacker_prior,
                ball,
                signs[(period, str(first.defending_team))],
                "Metrica",
            )
        )
    frame = pd.DataFrame(rows)
    sample = {
        "match_id": str(data.match_id.iloc[0]),
        "rank_rows": int(len(data)),
        "observations": int(data.observation_id.nunique()),
        "ball_available_rows": int(frame.ball_defender_distance_m.notna().sum()),
    }
    input_record = {
        "match_id": str(data.match_id.iloc[0]),
        "provider": "Metrica",
        "source_files": provenance["source_files"],
        "coordinate_contract": provenance["canonical_coordinate_system"],
        "goalward_sign_support": "first 2.0 seconds of supported goalkeeper tracking in each period",
        "goalward_sign_support_precedes_every_anchor": True,
    }
    return frame, sample, input_record


def _idsse_smoothed_prior(entity: dict, indexes: np.ndarray) -> np.ndarray:
    raw = np.column_stack([entity["x"][indexes], entity["y"][indexes]]).astype(float)
    if not np.asarray(entity["valid"], bool)[indexes].all() or not np.isfinite(raw).all():
        raise RuntimeError("closed IDSSE prior support unavailable")
    result = idsse.smooth_full(raw)
    if result.shape != (51, 2):
        raise RuntimeError(f"unexpected IDSSE prior shape: {result.shape}")
    return result


def load_idsse_tracking_only(match_id: str) -> tuple[dict, dict, dict]:
    """Load metadata and tracking without opening the provider event file."""
    raw = ROOT / "data/idsse_raw"
    metadata_path = idsse.idsse.find_file(raw, "metadata", match_id)
    metadata = idsse.idsse.read_metadata(metadata_path)
    cache = ROOT / f"data/idsse_cache/{match_id}_raw_tracking.npz"
    if cache.exists():
        tracking_path = cache
        tracking = idsse.idsse.load_tracking_cache(cache)
        source_kind = "governed native tracking cache"
    else:
        tracking_path = idsse.idsse.find_file(raw, "tracking", match_id)
        tracking = idsse.idsse.read_tracking(tracking_path, metadata)
        source_kind = "provider raw tracking XML"
    provenance = {
        "match_id": match_id,
        "provider": "IDSSE/Sportec",
        "source_files": [
            {
                "role": "provider metadata XML",
                "path": str(metadata_path.relative_to(ROOT)),
                "sha256": sha256(metadata_path),
            },
            {
                "role": source_kind,
                "path": str(tracking_path.relative_to(ROOT)),
                "sha256": sha256(tracking_path),
            },
        ],
        "event_file_opened": False,
        "coordinate_contract": "metres, pitch centre origin, +x right, +y top, fixed pitch frame",
        "goalward_sign_support": "first 2.0 seconds of supported goalkeeper tracking in each period",
        "goalward_sign_support_precedes_every_anchor": True,
    }
    return metadata, tracking, provenance


def extract_idsse_match(
    data: pd.DataFrame, match_id: str
) -> tuple[pd.DataFrame, dict, dict]:
    metadata, native, provenance = load_idsse_tracking_only(match_id)
    rows = []
    periods = list(idsse.idsse.PERIODS)
    for period_number, period_name in enumerate(periods, 1):
        subset = data.loc[data.period == period_number]
        if subset.empty:
            continue
        pdata = native[period_name]
        entities = {(e["team_id"], e["person_id"]): e for e in pdata["entities"]}
        time_lookup = {int(t): i for i, t in enumerate(pdata["time_ns"])}
        signs = {}
        period_time_ns = np.asarray(pdata["time_ns"], dtype=np.int64)
        for team in (metadata["home_team_id"], metadata["away_team_id"]):
            keepers = [
                p.player_id for p in metadata["players"].values()
                if p.team_id == team and p.goalkeeper
            ]
            keeper_entities = []
            for keeper in keepers:
                entity = entities.get((team, keeper))
                if entity is not None:
                    keeper_entities.append(entity)
            valid_times = [
                period_time_ns[np.asarray(entity["valid"], bool)]
                for entity in keeper_entities
                if np.asarray(entity["valid"], bool).any()
            ]
            if not valid_times:
                raise RuntimeError(
                    f"IDSSE goalkeeper orientation unavailable: {match_id} {period_name} {team}"
                )
            opening_ns = min(int(times.min()) for times in valid_times)
            if opening_ns + 2_000_000_000 > int(subset.time_utc_ns.min()):
                raise RuntimeError(
                    f"goalward-sign support is future to an audited anchor: "
                    f"{match_id} {period_name} {team}"
                )
            values = []
            for entity in keeper_entities:
                valid = np.asarray(entity["valid"], bool)
                opening_support = valid & (period_time_ns <= opening_ns + 2_000_000_000)
                values.extend(np.asarray(entity["x"], float)[opening_support].tolist())
            if not values or abs(float(np.median(values))) < 1.0:
                raise RuntimeError(f"IDSSE goalkeeper orientation unavailable: {match_id} {period_name} {team}")
            signs[team] = 1.0 if float(np.median(values)) > 0 else -1.0
        for _obs, group in subset.groupby("observation_id", sort=False):
            first = group.iloc[0]
            anchor_ns = int(first.time_utc_ns)
            times = np.arange(
                anchor_ns - 2_000_000_000 - 3 * idsse.FRAME_NS,
                anchor_ns + 3 * idsse.FRAME_NS + idsse.FRAME_NS,
                idsse.FRAME_NS,
                dtype=np.int64,
            )
            try:
                indexes = np.asarray([time_lookup[int(t)] for t in times], dtype=int)
            except KeyError as error:
                raise RuntimeError(f"closed IDSSE cadence unavailable: {first.observation_id}") from error
            ordered = group.sort_values("distance_rank", kind="mergesort")
            defender_prior = [
                _idsse_smoothed_prior(entities[(str(first.defending_team), str(key))], indexes)
                for key in ordered.defender_key.astype(str)
            ]
            attacker_prior = _idsse_smoothed_prior(
                entities[(str(first.attacking_team), str(first.attacker_key))], indexes
            )
            ball_entity = next(e for e in pdata["entities"] if e["team_id"] == "BALL")
            center = time_lookup[anchor_ns]
            ball_indexes = np.arange(center - 3, center + 4, dtype=int)
            ball = _centered_seven(
                np.column_stack([
                    ball_entity["x"][ball_indexes], ball_entity["y"][ball_indexes]
                ]),
                np.asarray(ball_entity["valid"], bool)[ball_indexes],
            )
            rows.extend(
                feature_rows_for_observation(
                    group,
                    np.stack(defender_prior),
                    attacker_prior,
                    ball,
                    signs[str(first.defending_team)],
                    "IDSSE",
                )
            )
    frame = pd.DataFrame(rows)
    sample = {
        "match_id": match_id,
        "rank_rows": int(len(data)),
        "observations": int(data.observation_id.nunique()),
        "ball_available_rows": int(frame.ball_defender_distance_m.notna().sum()),
    }
    return frame, sample, provenance


def summaries(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    group_rows = []
    for (match, variable, rank_group), values in (
        data.melt(
            id_vars=["match_id", "rank_group"],
            value_vars=list(SUMMARY_VARIABLES),
            var_name="variable",
            value_name="value",
        ).groupby(["match_id", "variable", "rank_group"], sort=True)
    ):
        x = values.value.to_numpy(float)
        x = x[np.isfinite(x)]
        group_rows.append({
            "match_id": match,
            "variable": variable,
            "rank_group": rank_group,
            "n": len(x),
            "median": np.median(x) if len(x) else np.nan,
            "q1": np.quantile(x, 0.25) if len(x) else np.nan,
            "q3": np.quantile(x, 0.75) if len(x) else np.nan,
            "mean": np.mean(x) if len(x) else np.nan,
            "sd": np.std(x, ddof=1) if len(x) > 1 else np.nan,
        })
    group_summary = pd.DataFrame(group_rows)
    effects = []
    for (match, variable), group in group_summary.groupby(["match_id", "variable"], sort=True):
        lookup = group.set_index("rank_group")
        near, middle = lookup.loc["near"], lookup.loc["middle"]
        denom_n = near.n + middle.n - 2
        pooled_sd = math.sqrt(
            ((near.n - 1) * near.sd**2 + (middle.n - 1) * middle.sd**2) / denom_n
        ) if denom_n > 0 and np.isfinite([near.sd, middle.sd]).all() else np.nan
        effects.append({
            "match_id": match,
            "variable": variable,
            "near_median": near["median"],
            "near_q1": near.q1,
            "near_q3": near.q3,
            "middle_median": middle["median"],
            "middle_q1": middle.q1,
            "middle_q3": middle.q3,
            "standardized_difference": (
                (near["mean"] - middle["mean"]) / pooled_sd
                if pooled_sd > 0 else np.nan
            ),
        })
    effect_frame = pd.DataFrame(effects)
    cross = []
    for variable, group in effect_frame.groupby("variable", sort=True):
        x = group.standardized_difference.to_numpy(float)
        x = x[np.isfinite(x)]
        cross.append({
            "variable": variable,
            "matches": len(x),
            "median_match_standardized_difference": np.median(x),
            "q1_match_standardized_difference": np.quantile(x, 0.25),
            "q3_match_standardized_difference": np.quantile(x, 0.75),
            "positive_matches": int((x > 0).sum()),
            "negative_matches": int((x < 0).sum()),
            "same_sign_matches": int(max((x > 0).sum(), (x < 0).sum())),
        })
    cross_frame = pd.DataFrame(cross)
    rank_rows = []
    for (match, variable, rank), values in (
        data.melt(
            id_vars=["match_id", "distance_rank"],
            value_vars=list(SUMMARY_VARIABLES),
            var_name="variable",
            value_name="value",
        ).groupby(["match_id", "variable", "distance_rank"], sort=True)
    ):
        x = values.value.to_numpy(float)
        x = x[np.isfinite(x)]
        rank_rows.append({
            "match_id": match,
            "variable": variable,
            "distance_rank": int(rank),
            "n": len(x),
            "median": np.median(x) if len(x) else np.nan,
            "q1": np.quantile(x, 0.25) if len(x) else np.nan,
            "q3": np.quantile(x, 0.75) if len(x) else np.nan,
        })
    return group_summary, effect_frame.merge(cross_frame, on="variable"), pd.DataFrame(rank_rows)


def _weighted_standardize(x: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.average(x, axis=0, weights=weights)
    variance = np.average((x - mean) ** 2, axis=0, weights=weights)
    sd = np.sqrt(variance)
    if np.any(sd <= 1e-12):
        raise RuntimeError("constant primary classifier feature")
    return mean, sd


def _fit_logistic(x: np.ndarray, y: np.ndarray, weights: np.ndarray, l2: float) -> np.ndarray:
    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        z = x @ beta
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
        loss = float(np.sum(weights * (np.logaddexp(0.0, z) - y * z)))
        loss += 0.5 * l2 * float(beta[1:] @ beta[1:])
        grad = x.T @ (weights * (p - y))
        grad[1:] += l2 * beta[1:]
        return loss, grad

    start = np.zeros(x.shape[1], dtype=float)
    result = minimize(
        objective,
        start,
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 500, "ftol": 1e-12, "gtol": 1e-8},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"logistic fit failed: {result.message}")
    return np.asarray(result.x, float)


def _auc(y: np.ndarray, score: np.ndarray) -> float:
    n1, n0 = int(y.sum()), int(len(y) - y.sum())
    ranks = rankdata(score, method="average")
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def rank_predictability(data: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = config["rank_predictability"]["features"]
    frame = data.loc[data.rank_group.isin(["near", "middle"])].copy()
    if "attacker_defender_start_distance_m" in features:
        raise RuntimeError("defining attacker distance entered the classifier")
    complete = np.isfinite(frame[features].to_numpy(float)).all(axis=1)
    frame = frame.loc[complete].reset_index(drop=True)
    matches = sorted(frame.match_id.unique())
    fold_rows, coefficient_rows = [], []
    for heldout in matches:
        test = frame.match_id.eq(heldout).to_numpy()
        train = ~test
        train_matches = sorted(frame.loc[train, "match_id"].unique())
        weights = np.zeros(train.sum(), dtype=float)
        train_ids = frame.loc[train, "match_id"].to_numpy(str)
        for match in train_matches:
            mask = train_ids == match
            weights[mask] = 1.0 / (len(train_matches) * int(mask.sum()))
        x_train_raw = frame.loc[train, features].to_numpy(float)
        x_test_raw = frame.loc[test, features].to_numpy(float)
        mean, sd = _weighted_standardize(x_train_raw, weights)
        x_train = np.column_stack([np.ones(train.sum()), (x_train_raw - mean) / sd])
        x_test = np.column_stack([np.ones(test.sum()), (x_test_raw - mean) / sd])
        y_train = frame.loc[train, "rank_group"].eq("near").to_numpy(int)
        y_test = frame.loc[test, "rank_group"].eq("near").to_numpy(int)
        beta = _fit_logistic(x_train, y_train, weights, l2=1e-6)
        probability = 1.0 / (1.0 + np.exp(-np.clip(x_test @ beta, -35.0, 35.0)))
        predicted = probability >= 0.5
        tpr = predicted[y_test == 1].mean()
        tnr = (~predicted[y_test == 0]).mean()
        fold_rows.append({
            "heldout_match": heldout,
            "train_rows": int(train.sum()),
            "test_rows": int(test.sum()),
            "test_near_rows": int(y_test.sum()),
            "auc": _auc(y_test, probability),
            "balanced_accuracy_at_0_5": float((tpr + tnr) / 2.0),
        })
        for name, value in zip(["intercept", *features], beta):
            coefficient_rows.append({
                "heldout_match": heldout,
                "feature": name,
                "standardized_coefficient": value,
            })
    return pd.DataFrame(fold_rows), pd.DataFrame(coefficient_rows)


def conditioning_map(cross: pd.DataFrame, config: dict) -> pd.DataFrame:
    reference = config["core_conditioning_reference"]
    status = {}
    for label, variables in reference.items():
        normalized = label.replace("_conditioned", "").replace("not_", "not ")
        for variable in variables:
            status[variable] = normalized
    rows = []
    for row in cross.drop_duplicates("variable").itertuples(index=False):
        adjustment = status[row.variable]
        strong = (
            abs(float(row.median_match_standardized_difference)) >= 0.5
            and int(row.same_sign_matches) >= 7
        )
        if adjustment == "fully":
            severity = "MINOR" if strong else "MINOR"
            action = "Existing rank-specific linear control; retain as QC."
        elif adjustment == "partially":
            severity = "MAJOR" if strong else (
                "MODERATE" if abs(float(row.median_match_standardized_difference)) >= 0.2 and int(row.same_sign_matches) >= 6 else "MINOR"
            )
            action = "Prospective sensitivity if imbalance is strong/stable."
        else:
            severity = "MAJOR" if strong else (
                "MODERATE" if abs(float(row.median_match_standardized_difference)) >= 0.2 and int(row.same_sign_matches) >= 6 else "MINOR"
            )
            action = "Prospective sensitivity if MAJOR; otherwise limitation/QC."
        rows.append({
            "baseline_difference": row.variable,
            "median_match_standardized_difference": row.median_match_standardized_difference,
            "same_sign_matches": row.same_sign_matches,
            "strong_by_rank": bool(strong),
            "existing_core_adjustment": adjustment,
            "could_plausibly_confound": (
                "only through residual nonlinearity/effect modification" if adjustment == "fully"
                else "yes if associated with attacker movement and response or if it modifies the slope"
            ),
            "severity": severity,
            "recommended_action": action,
        })
    return pd.DataFrame(rows)


def classify(
    cross: pd.DataFrame,
    folds: pd.DataFrame,
    conditioning: pd.DataFrame,
) -> dict[str, Any]:
    median_auc = float(folds.auc.median())
    strong_auc = median_auc >= 0.70 and int((folds.auc >= 0.65).sum()) >= 7
    major_variables = conditioning.loc[conditioning.severity == "MAJOR", "baseline_difference"].tolist()
    moderate_variables = conditioning.loc[conditioning.severity == "MODERATE", "baseline_difference"].tolist()
    if strong_auc or major_variables:
        severity = "MAJOR"
        verdict = "TARGETED CORE SENSITIVITY REQUIRED BEFORE DOWNSTREAM USE"
        v3 = "V3 SHOULD WAIT FOR A PROSPECTIVE CORE SENSITIVITY"
    elif median_auc >= 0.60 or moderate_variables:
        severity = "MODERATE"
        verdict = "CORE RANK LOCALIZATION USABLE WITH MODERATE LIMITATION"
        v3 = "V3 MAY PROCEED WITH A PAPER LIMITATION / NONCLASSIFYING QC"
    else:
        severity = "MINOR"
        verdict = "CORE RANK LOCALIZATION ADEQUATELY ROBUST FOR DOWNSTREAM USE"
        v3 = "V3 MAY PROCEED; RANK-COMPOSITION THREAT IS ADEQUATELY MANAGED"
    return {
        "severity": severity,
        "verdict": verdict,
        "v3_decision": v3,
        "median_heldout_auc": median_auc,
        "heldout_auc_at_least_0_65": int((folds.auc >= 0.65).sum()),
        "strong_predictability_rule": bool(strong_auc),
        "major_variables": major_variables,
        "moderate_variables": moderate_variables,
        "interpretive_guard": (
            "Rank composition can threaten a rank-specific attacker-path slope only if the baseline feature also covaries with attacker movement and response or modifies that slope; balance alone is not proof of confounding."
        ),
    }


def execute(output: Path) -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    firewall = verify_frozen(config)
    output.mkdir(parents=True, exist_ok=True)

    game1 = load_rank_ledger(
        ROOT / config["data"]["rank_sources"]["metrica_game_1"],
        "metrica_game_1",
    )
    game2 = load_rank_ledger(
        ROOT / config["data"]["rank_sources"]["metrica_game_2"],
        "metrica_game_2",
    )
    external = load_rank_ledger(ROOT / config["data"]["rank_sources"]["idsse"])
    frames, sample, input_records = [], [], []
    for ledger, game_number in ((game1, 1), (game2, 2)):
        frame, record, input_record = extract_metrica(ledger, game_number)
        frames.append(frame)
        sample.append(record)
        input_records.append(input_record)
    for match_id in config["data"]["matches"][2:]:
        subset = external.loc[external.match_id == match_id].reset_index(drop=True)
        frame, record, input_record = extract_idsse_match(subset, match_id)
        frames.append(frame)
        sample.append(record)
        input_records.append(input_record)
    data = pd.concat(frames, ignore_index=True).sort_values(
        ["match_id", "period", "time_period_s", "attacker_key", "distance_rank"],
        kind="mergesort",
    ).reset_index(drop=True)

    group_summary, effects, rank_summary = summaries(data)
    folds, coefficients = rank_predictability(data, config)
    conditioning = conditioning_map(effects, config)
    decision = classify(effects, folds, conditioning)
    cross_columns = [
        "variable",
        "matches",
        "median_match_standardized_difference",
        "q1_match_standardized_difference",
        "q3_match_standardized_difference",
        "positive_matches",
        "negative_matches",
        "same_sign_matches",
    ]
    cross_effects = effects[cross_columns].drop_duplicates("variable").sort_values(
        "variable", kind="mergesort"
    )

    input_provenance = {
        "status": "OUTCOME_BLIND_RECONSTRUCTION_INPUTS_BOUND",
        "matches": input_records,
        "frozen_reconstruction_dependencies": {
            relative: expected
            for relative, expected in config["frozen_input_hashes"].items()
            if relative.startswith("src/")
            or relative.startswith(
                "outputs/attacking_continuous_movement_game2_stage_a/"
            )
        },
        "provider_event_files_opened_for_reconstruction": False,
        "protected_response_or_coverage_inputs": [],
        "game3_inputs": [],
    }
    write_json(output / "input_provenance.json", input_provenance)
    write_csv(pd.DataFrame(sample), output / "sample_counts.csv")
    write_csv(group_summary, output / "rank_group_summaries.csv")
    write_csv(effects, output / "near_middle_effects.csv")
    write_csv(cross_effects, output / "cross_match_effects.csv")
    write_csv(rank_summary, output / "rank_D1_D10_summaries.csv")
    write_csv(folds, output / "rank_predictability_folds.csv")
    write_csv(coefficients, output / "rank_predictability_coefficients.csv")
    write_csv(conditioning, output / "conditioning_coverage.csv")
    result = {
        "status": "OUTCOME_BLIND_RANK_COMPOSITION_AUDIT_COMPLETE",
        "starting_commit": config["starting_commit"],
        "config_sha256": sha256(CONFIG),
        "sample": sample,
        "rows": int(len(data)),
        "attacker_anchor_observations": int(data.observation_id.nunique()),
        "matches": int(data.match_id.nunique()),
        "composition": {
            "largest_nondefining_cross_match_effects": (
                cross_effects.loc[
                    cross_effects.variable != "attacker_defender_start_distance_m"
                ]
                .assign(
                    absolute_effect=lambda x: x.median_match_standardized_difference.abs()
                )
                .sort_values("absolute_effect", ascending=False, kind="mergesort")
                .head(5)
                .drop(columns="absolute_effect")
                .to_dict("records")
            )
        },
        "classifier": {
            "features": config["rank_predictability"]["features"],
            "folds": folds.to_dict("records"),
            "median_auc": float(folds.auc.median()),
            "auc_range": [float(folds.auc.min()), float(folds.auc.max())],
            "median_balanced_accuracy": float(folds.balanced_accuracy_at_0_5.median()),
            "complete_rows": int(folds.test_rows.sum()),
        },
        "decision": decision,
        "firewall": {
            **firewall,
            "rank_ledger_columns_selected": list(COMMON_COLUMNS) + list(IDSSE_EXTRA_COLUMNS),
            "concurrent_response_columns_selected": [],
            "coverage_outcomes_selected": [],
            "start_distance_and_prior_geometry_reconstructed_within_1e_6_m": True,
            "game2_or_idsse_coverage_outcomes_inspected": False,
            "game3_accessed": False,
        },
    }
    write_json(output / "audit_results.json", result)
    governed = [
        "sample_counts.csv",
        "input_provenance.json",
        "rank_group_summaries.csv",
        "near_middle_effects.csv",
        "cross_match_effects.csv",
        "rank_D1_D10_summaries.csv",
        "rank_predictability_folds.csv",
        "rank_predictability_coefficients.csv",
        "conditioning_coverage.csv",
        "audit_results.json",
    ]
    write_json(
        output / "governed_hashes.json",
        {name: sha256(output / name) for name in governed},
    )
    return result


def reproduce(output: Path) -> None:
    rerun = output.parent / f".{output.name}_rerun"
    if rerun.exists():
        shutil.rmtree(rerun)
    execute(rerun)
    expected = json.loads((output / "governed_hashes.json").read_text(encoding="utf-8"))
    actual = {name: sha256(rerun / name) for name in expected}
    report = {
        "all_governed_outputs_byte_identical": expected == actual,
        "governed_outputs": len(expected),
        "expected": expected,
        "actual": actual,
    }
    shutil.rmtree(rerun)
    write_json(output / "reproduction.json", report)
    if not report["all_governed_outputs_byte_identical"]:
        raise RuntimeError("outcome-blind audit did not reproduce deterministically")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    if args.reproduce:
        reproduce(args.output)
    else:
        execute(args.output)


if __name__ == "__main__":
    main()
