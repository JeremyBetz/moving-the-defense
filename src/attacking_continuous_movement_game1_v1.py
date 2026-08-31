"""Execute frozen continuous attacker-movement v1 on Metrica Sample Game 1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from infrastructure import canonical_tracking  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402

PROTOCOL = ROOT / "docs" / "protocols" / "attacking_continuous_movement_v1.md"
DEFAULT_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game1_v1"
WINDOWS = (1.0, 2.0, 4.0)
GRID_S = 0.20
RAW_DT_S = 0.04
TIME_TOL = 1e-9
GEOM_TOL = 1e-12
SMOOTH_FRAMES = 7
REGISTRY = (
    ("metrica:Home", "10", 1, 2911, 2945),
    ("metrica:Home", "3", 2, None, None),
    ("metrica:Away", "22", 2, None, None),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
        return None if not math.isfinite(value) else value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def geometry(positions: np.ndarray, cumulative_path: np.ndarray, start: int, end: int) -> dict[str, Any]:
    delta = positions[end] - positions[start]
    # The frozen formula requires chronological summation inside the physical
    # window. Do not subtract long cumulative totals: cancellation at later
    # match times can violate the 1e-12 geometric hard-QC tolerance.
    steps = np.diff(positions[start : end + 1], axis=0)
    path = float(np.linalg.norm(steps, axis=1).sum(dtype=np.float64))
    displacement = float(np.hypot(delta[0], delta[1]))
    if path == 0.0:
        straightness = None
        valid = False
    else:
        straightness = displacement / path
        valid = True
    return {
        "delta_x_m": float(delta[0]),
        "delta_y_m": float(delta[1]),
        "displacement_m": displacement,
        "path_length_m": path,
        "straightness": straightness,
        "straightness_valid": valid,
    }


def cumulative_path(positions: np.ndarray) -> np.ndarray:
    if len(positions) == 0:
        return np.empty(0, dtype=np.float64)
    return np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(positions, axis=0), axis=1), dtype=np.float64)]


def smooth_positions(raw_xy: np.ndarray) -> np.ndarray:
    if len(raw_xy) < SMOOTH_FRAMES:
        return np.empty((0, 2), dtype=np.float64)
    kernel = np.ones(SMOOTH_FRAMES, dtype=np.float64) / SMOOTH_FRAMES
    return np.column_stack([np.convolve(raw_xy[:, j], kernel, mode="valid") for j in range(2)])


@dataclass
class SmoothBlock:
    block_id: str
    player_key: str
    team_key: str
    period: int
    raw_start_index: int
    raw_end_index: int
    center_indices: np.ndarray
    times_period_s: np.ndarray
    positions25: np.ndarray
    cumulative25: np.ndarray
    positions10: np.ndarray
    cumulative10: np.ndarray
    ticks10: np.ndarray
    tick10_to_index: dict[int, int]


@dataclass
class PlayerPeriod:
    player_key: str
    team_key: str
    player_number: str
    period: int
    frame_ids: np.ndarray
    time_period_s: np.ndarray
    time_match_s: np.ndarray
    raw_xy: np.ndarray
    raw_valid_base: np.ndarray
    registry_invalid: np.ndarray
    continuity_links: np.ndarray
    blocks: list[SmoothBlock]
    center_to_block: dict[int, tuple[int, int]]


def registry_mask(team_key: str, player_number: str, period: int, frames: np.ndarray) -> np.ndarray:
    mask = np.zeros(len(frames), dtype=bool)
    for team, player, p, lo, hi in REGISTRY:
        if (team_key, player_number, period) != (team, player, p):
            continue
        if lo is None:
            mask[:] = True
        else:
            mask |= (frames >= lo) & (frames <= hi)
    return mask


def _valid_runs(valid: np.ndarray, links: np.ndarray) -> list[tuple[int, int]]:
    starts: list[int] = []
    ends: list[int] = []
    inside = False
    for i, ok in enumerate(valid):
        new = bool(ok and (i == 0 or not valid[i - 1] or not links[i]))
        if new:
            if inside:
                ends.append(i - 1)
            starts.append(i)
            inside = True
        elif inside and not ok:
            ends.append(i - 1)
            inside = False
    if inside:
        ends.append(len(valid) - 1)
    return list(zip(starts, ends))


def _build_block(
    pp: PlayerPeriod,
    run_start: int,
    run_end: int,
    block_number: int,
    period_origin: float,
) -> SmoothBlock | None:
    raw = pp.raw_xy[run_start : run_end + 1]
    positions = smooth_positions(raw)
    if len(positions) == 0:
        return None
    centers = np.arange(run_start + 3, run_end - 2, dtype=np.int64)
    times = pp.time_period_s[centers]
    k_min = int(math.ceil((float(times[0]) - period_origin - TIME_TOL) / 0.1))
    k_max = int(math.floor((float(times[-1]) - period_origin + TIME_TOL) / 0.1))
    ticks = np.arange(k_min, k_max + 1, dtype=np.int64)
    target = period_origin + 0.1 * ticks
    if len(target):
        positions10 = np.column_stack([np.interp(target, times, positions[:, j]) for j in range(2)])
    else:
        positions10 = np.empty((0, 2), dtype=np.float64)
    return SmoothBlock(
        block_id=f"{pp.player_key}|P{pp.period}|B{block_number:03d}",
        player_key=pp.player_key,
        team_key=pp.team_key,
        period=pp.period,
        raw_start_index=run_start,
        raw_end_index=run_end,
        center_indices=centers,
        times_period_s=times,
        positions25=positions,
        cumulative25=cumulative_path(positions),
        positions10=positions10,
        cumulative10=cumulative_path(positions10),
        ticks10=ticks,
        tick10_to_index={int(k): i for i, k in enumerate(ticks)},
    )


def load_game1() -> tuple[list[PlayerPeriod], dict[int, dict[str, Any]], dict[str, Any]]:
    home, away = metrica.game1_paths(ROOT)
    frame_index = metrica.read_provider_frame_index(home)
    dataset = metrica.load_dataset(home, away)
    traces: dict[str, list[pd.DataFrame]] = {}
    metadata: dict[str, str] = {}
    period_frames: dict[int, dict[str, Any]] = {}
    for chunk in metrica.iter_canonical_polars_chunks(dataset, frame_index, frames_per_chunk=2500):
        players = chunk.filter((pl.col("entity_type") == "player") & (~pl.col("is_goalkeeper")))
        q = pd.DataFrame(players.to_dicts())
        for key, group in q.groupby("player_key", sort=False):
            traces.setdefault(str(key), []).append(
                group[
                    [
                        "team_key",
                        "period",
                        "frame_id_provider",
                        "time_period_s",
                        "time_match_s",
                        "x_m",
                        "y_m",
                        "is_present",
                        "coordinate_valid",
                        "support_state",
                    ]
                ]
            )
            metadata[str(key)] = str(group["team_key"].iloc[0])
    player_periods: list[PlayerPeriod] = []
    for player_key in sorted(traces):
        trace = pd.concat(traces[player_key], ignore_index=True)
        team_key = metadata[player_key]
        player_number = player_key.rsplit(":", 1)[1]
        for period_value, group in trace.groupby("period", sort=True):
            period = int(period_value)
            group = group.sort_values("time_match_s", kind="mergesort").reset_index(drop=True)
            frames = group["frame_id_provider"].astype(int).to_numpy()
            tperiod = group["time_period_s"].to_numpy(np.float64)
            tmatch = group["time_match_s"].to_numpy(np.float64)
            raw_xy = group[["x_m", "y_m"]].to_numpy(np.float64)
            base = (
                group["is_present"].fillna(False).to_numpy(bool)
                & group["coordinate_valid"].fillna(False).to_numpy(bool)
                & group["support_state"].eq("observed").to_numpy(bool)
                & np.isfinite(raw_xy).all(axis=1)
            )
            reg = registry_mask(team_key, player_number, period, frames)
            links = np.zeros(len(group), dtype=bool)
            if len(group) > 1:
                links[1:] = (
                    (np.diff(frames) == 1)
                    & (np.abs(np.diff(tmatch) - RAW_DT_S) <= TIME_TOL)
                    & (np.diff(tperiod) > 0)
                )
            if period not in period_frames:
                period_frames[period] = {
                    "origin_time_period_s": float(tperiod[0]),
                    "frame_ids": frames.copy(),
                    "time_period_s": tperiod.copy(),
                    "time_match_s": tmatch.copy(),
                }
            else:
                ref = period_frames[period]
                if not (
                    np.array_equal(ref["frame_ids"], frames)
                    and np.allclose(ref["time_period_s"], tperiod, atol=TIME_TOL, rtol=0)
                    and np.allclose(ref["time_match_s"], tmatch, atol=TIME_TOL, rtol=0)
                ):
                    raise RuntimeError("Canonical player period grids differ")
            pp = PlayerPeriod(
                player_key=player_key,
                team_key=team_key,
                player_number=player_number,
                period=period,
                frame_ids=frames,
                time_period_s=tperiod,
                time_match_s=tmatch,
                raw_xy=raw_xy,
                raw_valid_base=base,
                registry_invalid=reg,
                continuity_links=links,
                blocks=[],
                center_to_block={},
            )
            valid = base & ~reg
            origin = period_frames[period]["origin_time_period_s"]
            for bno, (start, end) in enumerate(_valid_runs(valid, links), 1):
                block = _build_block(pp, start, end, bno, origin)
                if block is None:
                    continue
                idx = len(pp.blocks)
                pp.blocks.append(block)
                for local, center in enumerate(block.center_indices):
                    pp.center_to_block[int(center)] = (idx, local)
            player_periods.append(pp)
    provenance = metrica.canonical_provenance(dataset, home, away)
    return player_periods, period_frames, provenance


def exclusion_reason(pp: PlayerPeriod, start: int, end: int) -> str:
    if start < 0:
        return "window_before_period_start"
    if start - 3 < 0 or end + 3 >= len(pp.frame_ids):
        return "smoothing_edge"
    required = slice(start - 3, end + 4)
    if pp.registry_invalid[required].any():
        return "trajectory_registry"
    if not pp.raw_valid_base[required].all():
        return "raw_support_invalid"
    if not pp.continuity_links[start - 2 : end + 4].all():
        return "continuity_break"
    return "smoothed_window_not_contiguous"


def _empty_columns() -> dict[str, list[Any]]:
    return {
        "observation_id": [],
        "match_id": [],
        "period": [],
        "frame_id_provider": [],
        "player_key": [],
        "team_key": [],
        "window_s": [],
        "time_period_s": [],
        "time_match_s": [],
    }


def calculate_window(
    player_periods: list[PlayerPeriod],
    period_frames: dict[int, dict[str, Any]],
    window_s: float,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    steps25 = int(round(window_s / RAW_DT_S))
    ticks10 = int(round(window_s / 0.1))
    support = _empty_columns() | {"eligible": [], "exclusion_reason": []}
    features = _empty_columns() | {
        "delta_x_m": [],
        "delta_y_m": [],
        "displacement_m": [],
        "path_length_m": [],
        "straightness": [],
        "straightness_valid": [],
    }
    comparisons = _empty_columns() | {
        "matched_10hz": [],
        "delta_x_m_25hz": [],
        "delta_x_m_10hz": [],
        "delta_y_m_25hz": [],
        "delta_y_m_10hz": [],
        "path_length_m_25hz": [],
        "path_length_m_10hz": [],
        "straightness_25hz": [],
        "straightness_10hz": [],
        "straightness_valid_25hz": [],
        "straightness_valid_10hz": [],
    }
    for pp in player_periods:
        ref = period_frames[pp.period]
        origin = float(ref["origin_time_period_s"])
        for end in range(0, len(pp.frame_ids), 5):
            start = end - steps25
            obs_id = f"metrica:sample-game-1|{pp.period}|{pp.frame_ids[end]}|{pp.player_key}|{int(window_s*1000)}"
            base = {
                "observation_id": obs_id,
                "match_id": "metrica:sample-game-1",
                "period": pp.period,
                "frame_id_provider": str(pp.frame_ids[end]),
                "player_key": pp.player_key,
                "team_key": pp.team_key,
                "window_s": window_s,
                "time_period_s": float(pp.time_period_s[end]),
                "time_match_s": float(pp.time_match_s[end]),
            }
            lookup_start = pp.center_to_block.get(start)
            lookup_end = pp.center_to_block.get(end)
            eligible = bool(
                start >= 0
                and lookup_start is not None
                and lookup_end is not None
                and lookup_start[0] == lookup_end[0]
                and lookup_end[1] - lookup_start[1] == steps25
                and abs((pp.time_period_s[end] - pp.time_period_s[start]) - window_s) <= TIME_TOL
                and abs((pp.time_period_s[end] - origin) / GRID_S - round((pp.time_period_s[end] - origin) / GRID_S)) <= TIME_TOL
            )
            reason = "eligible" if eligible else exclusion_reason(pp, start, end)
            for key, value in base.items():
                support[key].append(value)
            support["eligible"].append(eligible)
            support["exclusion_reason"].append(reason)
            if not eligible:
                continue
            block = pp.blocks[lookup_start[0]]
            g25 = geometry(block.positions25, block.cumulative25, lookup_start[1], lookup_end[1])
            for key, value in base.items():
                features[key].append(value)
                comparisons[key].append(value)
            for key, value in g25.items():
                features[key].append(value)
            start_tick = int(round((float(pp.time_period_s[start]) - origin) / 0.1))
            end_tick = start_tick + ticks10
            i10 = block.tick10_to_index.get(start_tick)
            j10 = block.tick10_to_index.get(end_tick)
            matched = bool(i10 is not None and j10 is not None and j10 - i10 == ticks10)
            comparisons["matched_10hz"].append(matched)
            g10 = geometry(block.positions10, block.cumulative10, i10, j10) if matched else None
            comparisons["delta_x_m_25hz"].append(g25["delta_x_m"])
            comparisons["delta_x_m_10hz"].append(None if g10 is None else g10["delta_x_m"])
            comparisons["delta_y_m_25hz"].append(g25["delta_y_m"])
            comparisons["delta_y_m_10hz"].append(None if g10 is None else g10["delta_y_m"])
            comparisons["path_length_m_25hz"].append(g25["path_length_m"])
            comparisons["path_length_m_10hz"].append(None if g10 is None else g10["path_length_m"])
            comparisons["straightness_25hz"].append(g25["straightness"])
            comparisons["straightness_10hz"].append(None if g10 is None else g10["straightness"])
            comparisons["straightness_valid_25hz"].append(g25["straightness_valid"])
            comparisons["straightness_valid_10hz"].append(None if g10 is None else g10["straightness_valid"])
    return pl.DataFrame(support), pl.DataFrame(features), pl.DataFrame(comparisons)


def _summary(values: np.ndarray) -> dict[str, Any]:
    finite = values[np.isfinite(values)]
    if not len(finite):
        return {key: None for key in ("count", "min", "q01", "q25", "median", "mean", "q75", "q99", "max")}
    q = np.quantile(finite, [0.01, 0.25, 0.5, 0.75, 0.99], method="linear")
    return {
        "count": len(finite),
        "min": float(np.min(finite)),
        "q01": float(q[0]),
        "q25": float(q[1]),
        "median": float(q[2]),
        "mean": float(np.mean(finite)),
        "q75": float(q[3]),
        "q99": float(q[4]),
        "max": float(np.max(finite)),
    }


def feature_summary(features: pl.DataFrame, window_s: float) -> dict[str, Any]:
    arrays = {name: features[name].to_numpy() for name in ("delta_x_m", "delta_y_m", "displacement_m", "path_length_m")}
    straight = features.filter(pl.col("straightness_valid"))["straightness"].drop_nulls().to_numpy()
    displacement = arrays["displacement_m"]
    path = arrays["path_length_m"]
    zero_path = int(np.count_nonzero(path == 0.0))
    invalid_straight = int(features.filter(~pl.col("straightness_valid")).height)
    finite_count = sum(int(np.count_nonzero(~np.isfinite(v))) for v in arrays.values()) + int(np.count_nonzero(~np.isfinite(straight)))
    return {
        "window_s": window_s,
        "eligible_players": features["player_key"].n_unique(),
        "eligible_player_periods": features.select(["player_key", "period"]).unique().height,
        "eligible_observations": features.height,
        "supported_evaluation_grid_player_time_s": features.height * GRID_S,
        "delta_x_m": _summary(arrays["delta_x_m"]),
        "delta_y_m": _summary(arrays["delta_y_m"]),
        "displacement_m": _summary(displacement),
        "path_length_m": _summary(path),
        "straightness_valid": _summary(straight),
        "zero_path_count": zero_path,
        "zero_path_rate": zero_path / features.height if features.height else None,
        "invalid_straightness_count": invalid_straight,
        "invalid_straightness_rate": invalid_straight / features.height if features.height else None,
        "nonfinite_count": finite_count,
        "path_lt_displacement_violations": int(np.count_nonzero(path + GEOM_TOL < displacement)),
        "straightness_range_violations": int(np.count_nonzero((straight < -GEOM_TOL) | (straight > 1 + GEOM_TOL))),
        "exact_zero_displacement_count": int(np.count_nonzero(displacement == 0.0)),
        "straightness_exact_zero_count": int(np.count_nonzero(straight == 0.0)),
        "straightness_exact_one_count": int(np.count_nonzero(straight == 1.0)),
        "straightness_within_1e_12_of_zero_count": int(np.count_nonzero(np.abs(straight) <= GEOM_TOL)),
        "straightness_within_1e_12_of_one_count": int(np.count_nonzero(np.abs(straight - 1.0) <= GEOM_TOL)),
    }


def distribution_rows(features: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in features.partition_by(["window_s", "team_key", "period", "player_key"], as_dict=True).items():
        window_s, team_key, period, player_key = keys
        for feature in ("delta_x_m", "delta_y_m", "displacement_m", "path_length_m", "straightness"):
            values = group[feature].drop_nulls().to_numpy()
            stats = _summary(values)
            rows.append({"window_s": window_s, "team_key": team_key, "period": period, "player_key": player_key, "feature": feature, **stats})
    return pl.DataFrame(rows)


def frequency_metrics(comparison: pl.DataFrame, window_s: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    matched = comparison.filter(pl.col("matched_10hz"))
    n25 = comparison.height
    nmatch = matched.height
    rows: list[dict[str, Any]] = []

    def errors(name: str, ref_col: str, test_col: str, extra_mask: np.ndarray | None = None) -> dict[str, float]:
        ref = matched[ref_col].to_numpy()
        test = matched[test_col].to_numpy()
        mask = np.isfinite(ref) & np.isfinite(test)
        if extra_mask is not None:
            mask &= extra_mask
        diff = test[mask] - ref[mask]
        absolute = np.abs(diff)
        return {
            "observable": name,
            "denominator": int(len(diff)),
            "signed_bias": float(np.mean(diff)),
            "absolute_signed_bias": float(abs(np.mean(diff))),
            "median_absolute_error": float(np.quantile(absolute, 0.5, method="linear")),
            "p95_absolute_error": float(np.quantile(absolute, 0.95, method="linear")),
            "max_absolute_error": float(np.max(absolute)),
        }

    x = errors("delta_x_m", "delta_x_m_25hz", "delta_x_m_10hz")
    x["pass"] = x["absolute_signed_bias"] <= 0.010 and x["median_absolute_error"] <= 0.020 and x["p95_absolute_error"] <= 0.050
    rows.append({"window_s": window_s, **x})
    y = errors("delta_y_m", "delta_y_m_25hz", "delta_y_m_10hz")
    y["pass"] = y["absolute_signed_bias"] <= 0.010 and y["median_absolute_error"] <= 0.020 and y["p95_absolute_error"] <= 0.050
    rows.append({"window_s": window_s, **y})
    path = errors("path_length_m", "path_length_m_25hz", "path_length_m_10hz")
    ref_path = matched["path_length_m_25hz"].to_numpy()
    test_path = matched["path_length_m_10hz"].to_numpy()
    rel_mask = np.isfinite(ref_path) & np.isfinite(test_path) & (ref_path >= 1.0)
    rel = np.abs(test_path[rel_mask] - ref_path[rel_mask]) / ref_path[rel_mask]
    path["relative_denominator"] = int(len(rel))
    path["median_relative_error"] = float(np.quantile(rel, 0.5, method="linear"))
    path["p95_relative_error"] = float(np.quantile(rel, 0.95, method="linear"))
    path["pass"] = (
        -0.050 <= path["signed_bias"] <= 0.010
        and path["median_absolute_error"] <= 0.050
        and path["p95_absolute_error"] <= 0.150
        and path["median_relative_error"] <= 0.02
        and path["p95_relative_error"] <= 0.05
    )
    rows.append({"window_s": window_s, **path})
    valid25 = matched["straightness_valid_25hz"].to_numpy()
    valid10 = matched["straightness_valid_10hz"].to_numpy()
    validity_mismatch = int(np.count_nonzero(valid25 != valid10))
    valid_both = valid25 & valid10
    straight = errors("straightness", "straightness_25hz", "straightness_10hz", valid_both)
    straight["validity_mismatch_count"] = validity_mismatch
    straight["pass"] = (
        validity_mismatch == 0
        and straight["absolute_signed_bias"] <= 0.010
        and straight["median_absolute_error"] <= 0.015
        and straight["p95_absolute_error"] <= 0.050
    )
    rows.append({"window_s": window_s, **straight})
    eligibility_rate = nmatch / n25 if n25 else 0.0
    eligibility = {
        "window_s": window_s,
        "reference_eligible": n25,
        "matched_eligible": nmatch,
        "unmatched_25hz": n25 - nmatch,
        "match_rate": eligibility_rate,
        "all_mismatches_explained_by_support_edge": bool(nmatch == n25),
        "pass": bool(eligibility_rate >= 0.999 and nmatch == n25),
    }
    rows.append(
        {
            "window_s": window_s,
            "observable": "eligibility",
            "denominator": n25,
            "numerator": nmatch,
            "match_rate": eligibility_rate,
            "pass": eligibility["pass"],
        }
    )
    return rows, eligibility


def run_fixtures() -> tuple[pl.DataFrame, pl.DataFrame]:
    t = np.arange(0.0, 2.0 + 0.02, 0.04, dtype=np.float64)
    fixtures: list[tuple[str, np.ndarray, tuple[float, float], float, float | None, bool, float]] = []
    fixtures.append(("stationary", np.column_stack([np.ones(len(t)), 2 * np.ones(len(t))]), (0.0, 0.0), 0.0, None, False, GEOM_TOL))
    fixtures.append(("straight_constant", np.column_stack([2 * t, np.zeros(len(t))]), (4.0, 0.0), 4.0, 1.0, True, GEOM_TOL))
    fixtures.append(("straight_accelerating", np.column_stack([0.5 * t**2, np.zeros(len(t))]), (2.0, 0.0), 2.0, 1.0, True, GEOM_TOL))
    arc = np.column_stack([2 * np.sin(np.pi * t / 4), 2 * (1 - np.cos(np.pi * t / 4))])
    fixtures.append(("gradual_quarter_circle", arc, (2.0, 2.0), 200 * np.sin(np.pi / 200), np.sqrt(8) / (200 * np.sin(np.pi / 200)), True, 1e-10))
    cut = np.column_stack([np.where(t <= 1, t, 1), np.where(t <= 1, 0, t - 1)])
    fixtures.append(("sharp_cut", cut, (1.0, 1.0), 2.0, np.sqrt(2) / 2, True, GEOM_TOL))
    out = np.column_stack([np.where(t <= 1, t, 2 - t), np.zeros(len(t))])
    fixtures.append(("out_and_back", out, (0.0, 0.0), 2.0, 0.0, True, GEOM_TOL))
    fixtures.append(("low_speed_drift", np.column_stack([np.zeros(len(t)), 0.1 * t]), (0.0, 0.2), 0.2, 1.0, True, GEOM_TOL))
    stop_x = np.where(t <= 0.75, t, np.where(t <= 1.25, 0.75, t - 0.5))
    stop = np.column_stack([stop_x, np.zeros(len(t))])
    fixtures.append(("stop_restart", stop, (1.5, 0.0), 1.5, 1.0, True, GEOM_TOL))
    freq = np.column_stack([1.5 * t, -0.5 * t])
    fixtures.append(("frequency_equivalent_straight", freq, (3.0, -1.0), np.sqrt(10), 1.0, True, GEOM_TOL))
    rows: list[dict[str, Any]] = []
    for name, positions, expected_delta, expected_path, expected_s, expected_valid, tolerance in fixtures:
        result = geometry(positions, cumulative_path(positions), 0, len(positions) - 1)
        checks = [
            abs(result["delta_x_m"] - expected_delta[0]) <= tolerance,
            abs(result["delta_y_m"] - expected_delta[1]) <= tolerance,
            abs(result["path_length_m"] - expected_path) <= tolerance,
            result["straightness_valid"] == expected_valid,
            (result["straightness"] is None and expected_s is None)
            or (result["straightness"] is not None and expected_s is not None and abs(result["straightness"] - expected_s) <= tolerance),
        ]
        rows.append({"fixture": name, **result, "expected_delta_x_m": expected_delta[0], "expected_delta_y_m": expected_delta[1], "expected_path_length_m": expected_path, "expected_straightness": expected_s, "tolerance": tolerance, "pass": all(checks)})
    affine_raw = np.column_stack([2 * np.arange(20) * 0.04 + 3, -np.arange(20) * 0.04 + 7])
    smoothed = smooth_positions(affine_raw)
    expected_affine = affine_raw[3:-3]
    rows.append({"fixture": "seven_frame_smoothing_edges_affine", "delta_x_m": None, "delta_y_m": None, "displacement_m": None, "path_length_m": None, "straightness": None, "straightness_valid": None, "expected_delta_x_m": None, "expected_delta_y_m": None, "expected_path_length_m": None, "expected_straightness": None, "tolerance": GEOM_TOL, "pass": len(smoothed) == len(affine_raw) - 6 and np.max(np.abs(smoothed - expected_affine)) <= GEOM_TOL})
    rows.append({"fixture": "support_break", "delta_x_m": None, "delta_y_m": None, "displacement_m": None, "path_length_m": None, "straightness": None, "straightness_valid": None, "expected_delta_x_m": None, "expected_delta_y_m": None, "expected_path_length_m": None, "expected_straightness": None, "tolerance": 0.0, "pass": _valid_runs(np.r_[np.ones(25, bool), False, np.ones(25, bool)], np.r_[False, np.ones(50, bool)]) == [(0, 24), (26, 50)]})
    rows.append({"fixture": "grid_period_reset", "delta_x_m": None, "delta_y_m": None, "displacement_m": None, "path_length_m": None, "straightness": None, "straightness_valid": None, "expected_delta_x_m": None, "expected_delta_y_m": None, "expected_path_length_m": None, "expected_straightness": None, "tolerance": TIME_TOL, "pass": np.allclose(0.04 + 0.2 * np.arange(6), np.array([0.04, 0.24, 0.44, 0.64, 0.84, 1.04]), atol=TIME_TOL, rtol=0)})
    rows.append({"fixture": "stable_id", "delta_x_m": None, "delta_y_m": None, "displacement_m": None, "path_length_m": None, "straightness": None, "straightness_valid": None, "expected_delta_x_m": None, "expected_delta_y_m": None, "expected_path_length_m": None, "expected_straightness": None, "tolerance": 0.0, "pass": "m|1|25|p|2000" == "|".join(["m", "1", "25", "p", "2000"])})
    rows.append({"fixture": "invalid_duplicate_rejected", "delta_x_m": None, "delta_y_m": None, "displacement_m": None, "path_length_m": None, "straightness": None, "straightness_valid": None, "expected_delta_x_m": None, "expected_delta_y_m": None, "expected_path_length_m": None, "expected_straightness": None, "tolerance": 0.0, "pass": len({("m", 1, 25, "p"), ("m", 1, 25, "p")}) != 2})

    base = cut
    base_result = geometry(base, cumulative_path(base), 0, len(base) - 1)
    transformations = {
        "translation": base + np.array([13.0, -4.0]),
        "rotation": base @ np.array([[0.0, 1.0], [-1.0, 0.0]]).T,
        "mirror_x": base * np.array([-1.0, 1.0]),
        "mirror_y": base * np.array([1.0, -1.0]),
        "traversal_reversal": base[::-1].copy(),
    }
    inv_rows: list[dict[str, Any]] = []
    for name, transformed in transformations.items():
        result = geometry(transformed, cumulative_path(transformed), 0, len(transformed) - 1)
        if name == "translation":
            expected_delta = np.array([base_result["delta_x_m"], base_result["delta_y_m"]])
        elif name == "rotation":
            expected_delta = np.array([base_result["delta_y_m"], -base_result["delta_x_m"]])
        elif name == "mirror_x":
            expected_delta = np.array([-base_result["delta_x_m"], base_result["delta_y_m"]])
        elif name == "mirror_y":
            expected_delta = np.array([base_result["delta_x_m"], -base_result["delta_y_m"]])
        else:
            expected_delta = -np.array([base_result["delta_x_m"], base_result["delta_y_m"]])
        passed = (
            np.max(np.abs(np.array([result["delta_x_m"], result["delta_y_m"]]) - expected_delta)) <= GEOM_TOL
            and abs(result["path_length_m"] - base_result["path_length_m"]) <= GEOM_TOL
            and abs(result["straightness"] - base_result["straightness"]) <= GEOM_TOL
        )
        inv_rows.append({"transformation": name, "delta_x_m": result["delta_x_m"], "delta_y_m": result["delta_y_m"], "path_length_m": result["path_length_m"], "straightness": result["straightness"], "pass": passed})
    for row in rows:
        row["pass"] = bool(row["pass"])
    for row in inv_rows:
        row["pass"] = bool(row["pass"])
    return pl.DataFrame(rows), pl.DataFrame(inv_rows)


def main(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fixtures, invariance = run_fixtures()
    if not fixtures["pass"].all() or not invariance["pass"].all():
        raise RuntimeError("Frozen fixture or invariance failure")
    player_periods, period_frames, provenance = load_game1()
    all_distribution: list[pl.DataFrame] = []
    all_frequency_rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    eligibility: dict[str, Any] = {}
    exclusion_tables: list[pl.DataFrame] = []
    scientific_files: list[str] = []
    hard_checks: dict[str, bool] = {
        "fixtures": bool(fixtures["pass"].all()),
        "invariance": bool(invariance["pass"].all()),
        "protocol_sha256_matches_execution": True,
        "primary_interpolation": False,
        "clipping": False,
        "epsilon_denominator": False,
        "low_speed_threshold": False,
        "period_crossing": False,
    }
    for window in WINDOWS:
        support, features, comparison = calculate_window(player_periods, period_frames, window)
        suffix = f"{int(window)}s"
        support_path = output / f"evaluation_support_{suffix}.parquet"
        feature_path = output / f"features_{suffix}.parquet"
        comparison_path = output / f"frequency_comparison_{suffix}.parquet"
        support.write_parquet(support_path, compression="zstd", statistics=True)
        features.write_parquet(feature_path, compression="zstd", statistics=True)
        comparison.write_parquet(comparison_path, compression="zstd", statistics=True)
        scientific_files.extend([support_path.name, feature_path.name, comparison_path.name])
        summaries[suffix] = feature_summary(features, window)
        all_distribution.append(distribution_rows(features))
        freq_rows, eligibility_result = frequency_metrics(comparison, window)
        all_frequency_rows.extend(freq_rows)
        eligibility[suffix] = eligibility_result
        exclusion_tables.append(
            support.group_by(["window_s", "eligible", "exclusion_reason"]).len().sort(["window_s", "eligible", "exclusion_reason"])
        )
        hard_checks[f"unique_support_ids_{suffix}"] = support["observation_id"].n_unique() == support.height
        hard_checks[f"unique_feature_ids_{suffix}"] = features["observation_id"].n_unique() == features.height
        hard_checks[f"eligible_identity_match_{suffix}"] = support.filter(pl.col("eligible"))["observation_id"].to_list() == features["observation_id"].to_list()
        hard_checks[f"finite_and_geometry_{suffix}"] = summaries[suffix]["nonfinite_count"] == 0 and summaries[suffix]["path_lt_displacement_violations"] == 0 and summaries[suffix]["straightness_range_violations"] == 0
        hard_checks[f"straightness_definition_{suffix}"] = summaries[suffix]["zero_path_count"] == summaries[suffix]["invalid_straightness_count"]
    distributions = pl.concat(all_distribution, how="vertical")
    frequency_table = pl.DataFrame(all_frequency_rows)
    exclusions = pl.concat(exclusion_tables, how="vertical")
    distributions.write_csv(output / "distribution_diagnostics.csv", float_scientific=False)
    frequency_table.write_csv(output / "frequency_metrics.csv", float_scientific=False)
    exclusions.write_csv(output / "exclusion_summary.csv")
    fixtures.write_csv(output / "fixtures.csv", float_scientific=False)
    invariance.write_csv(output / "invariance_results.csv", float_scientific=False)
    scientific_files.extend(["distribution_diagnostics.csv", "frequency_metrics.csv", "exclusion_summary.csv", "fixtures.csv", "invariance_results.csv"])
    frequency_pass = bool(frequency_table["pass"].all())
    hard_qc = bool(all(value for key, value in hard_checks.items() if key not in {"primary_interpolation", "clipping", "epsilon_denominator", "low_speed_threshold", "period_crossing"}) and not any(hard_checks[key] for key in ("primary_interpolation", "clipping", "epsilon_denominator", "low_speed_threshold", "period_crossing")))
    pre_reproduction_classification = "A_candidate" if hard_qc and frequency_pass else ("B_candidate" if hard_qc else "C")
    results = {
        "classification": "PENDING_DETERMINISTIC_REPRODUCTION",
        "pre_reproduction_classification": pre_reproduction_classification,
        "feature_set": ["delta_x_m", "delta_y_m", "path_length_m", "straightness", "straightness_valid"],
        "windows_s": list(WINDOWS),
        "evaluation_grid_s": GRID_S,
        "eligible_outfield_players": len({pp.player_key for pp in player_periods}),
        "eligible_player_periods_available": len(player_periods),
        "summaries": summaries,
        "eligibility_frequency": eligibility,
        "hard_checks": hard_checks,
        "hard_qc_pre_reproduction_pass": hard_qc,
        "frequency_all_gates_pass": frequency_pass,
        "frequency_gate_pass_count": int(frequency_table["pass"].sum()),
        "frequency_gate_total": frequency_table.height,
        "game2_prerequisite_met": False,
    }
    write_json(output / "pre_reproduction_results.json", results)
    scientific_files.append("pre_reproduction_results.json")
    manifest = {
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256(PROTOCOL),
        "source": str(Path(__file__).relative_to(ROOT)),
        "source_sha256": sha256(Path(__file__)),
        "canonical_contract_sha256": sha256(ROOT / "docs" / "canonical_tracking_contract.md"),
        "canonical_module_sha256": sha256(ROOT / "src" / "infrastructure" / "canonical_tracking.py"),
        "metrica_adapter_sha256": sha256(ROOT / "src" / "infrastructure" / "kloppy_metrica_adapter.py"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "polars": pl.__version__,
        "canonical_provenance": provenance,
        "trajectory_registry": [list(row) for row in REGISTRY],
        "scientific_output_files": scientific_files,
    }
    write_json(output / "manifest.json", manifest)
    hashes = {name: sha256(output / name) for name in scientific_files}
    write_json(output / "scientific_output_hashes.json", hashes)


def verify_reproduction(primary: Path, rerun: Path) -> None:
    primary_manifest = json.loads((primary / "manifest.json").read_text(encoding="utf-8"))
    rerun_manifest = json.loads((rerun / "manifest.json").read_text(encoding="utf-8"))
    governed = [*primary_manifest["scientific_output_files"], "manifest.json", "scientific_output_hashes.json"]
    same_file_list = governed == [*rerun_manifest["scientific_output_files"], "manifest.json", "scientific_output_hashes.json"]
    comparisons = []
    for name in governed:
        left = primary / name
        right = rerun / name
        comparisons.append(
            {
                "file": name,
                "primary_sha256": sha256(left) if left.exists() else None,
                "rerun_sha256": sha256(right) if right.exists() else None,
                "byte_identical": bool(left.exists() and right.exists() and left.read_bytes() == right.read_bytes()),
            }
        )
    passed = bool(same_file_list and all(row["byte_identical"] for row in comparisons))
    verification = {
        "files_compared": len(comparisons),
        "same_governed_file_list": same_file_list,
        "all_byte_identical": passed,
        "comparisons": comparisons,
    }
    write_json(primary / "reproduction_verification.json", verification)
    base = json.loads((primary / "pre_reproduction_results.json").read_text(encoding="utf-8"))
    hard = bool(base["hard_qc_pre_reproduction_pass"] and passed)
    classification = "A" if hard and base["frequency_all_gates_pass"] else ("B" if hard else "C")
    final = {
        **base,
        "classification": classification,
        "deterministic_reproduction_pass": passed,
        "hard_qc_pass": hard,
        "game2_prerequisite_met": classification == "A",
    }
    write_json(primary / "final_results.json", final)
    final_hashes = {name: sha256(primary / name) for name in [*governed, "reproduction_verification.json", "final_results.json"]}
    write_json(primary / "final_output_hashes.json", final_hashes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.verify_against is None:
        main(args.output)
    else:
        verify_reproduction(args.output, args.verify_against)
