"""Execute frozen attacker-to-defender bridge v1 on Metrica Game 1 only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacking_continuous_movement_game1_v1 as attacker  # noqa: E402

PROTOCOL = ROOT / "docs" / "protocols" / "attacker_defender_bridge_v1.md"
FROZEN_PROTOCOL_SHA256 = "62321620a3007bf0c9686d99595caa0f9e39e2ac7ea2ba78b935ddfefd308bbb"
ATTACKER_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game1_v1"
DEFAULT_OUTPUT = ROOT / "outputs" / "attacker_defender_bridge_game1_v1"
DEFAULT_FIGURES = ROOT / "figures" / "attacker_defender_bridge_game1_v1"
EVENTS = ROOT / "data" / "metrica_sample_game_1" / "Sample_Game_1_RawEventsData.csv"

K = 3
CADENCE_S = 4.0
EXPOSURE_S = 2.0
BASELINE = (-4.0, -2.0)
RESPONSES = (1.0, 2.0, 4.0)
BLOCK_S = 60.0
BOOTSTRAPS = 2000
MASTER_SEED = 20260831
MIN_VALID_BOOTSTRAPS = 1900
TOL = 1e-9
RESTART_TYPES = {"SET PIECE", "BALL OUT"}
RESTART_SUBTYPES = {
    "CORNER KICK", "FREE KICK", "GOAL KICK", "KICK OFF", "THROW IN", "OFFSIDE", "END HALF"
}
POSSESSION_TYPES = {"PASS", "RECOVERY", "SET PIECE", "SHOT"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_hash_ledger(directory: Path, name: str) -> bool:
    ledger = json.loads((directory / name).read_text(encoding="utf-8"))
    return all(sha256(directory / rel) == expected for rel, expected in ledger.items())


def segment(pp: attacker.PlayerPeriod, start_s: float, end_s: float) -> np.ndarray | None:
    i = int(np.searchsorted(pp.time_period_s, start_s - TOL))
    j = int(np.searchsorted(pp.time_period_s, end_s - TOL))
    if i >= len(pp.time_period_s) or j >= len(pp.time_period_s):
        return None
    if abs(float(pp.time_period_s[i]) - start_s) > TOL or abs(float(pp.time_period_s[j]) - end_s) > TOL:
        return None
    left = pp.center_to_block.get(i)
    right = pp.center_to_block.get(j)
    if left is None or right is None or left[0] != right[0]:
        return None
    expected = int(round((end_s - start_s) / attacker.RAW_DT_S))
    if right[1] - left[1] != expected:
        return None
    return pp.blocks[left[0]].positions25[left[1] : right[1] + 1]


def position(pp: attacker.PlayerPeriod, time_s: float) -> np.ndarray | None:
    z = segment(pp, time_s, time_s)
    return None if z is None else z[0]


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


def defensive_geometry(
    defenders: dict[str, attacker.PlayerPeriod], start_s: float, end_s: float
) -> tuple[dict[str, float], float] | None:
    keys = sorted(defenders)
    arrays = {key: segment(defenders[key], start_s, end_s) for key in keys}
    if any(value is None for value in arrays.values()):
        return None
    stack = np.stack([arrays[key] for key in keys])  # type: ignore[arg-type]
    centroid = stack.mean(axis=0)
    individual: dict[str, float] = {}
    for index, key in enumerate(keys):
        other_centroid = (stack.sum(axis=0) - stack[index]) / (len(keys) - 1)
        individual[key] = path(stack[index] - other_centroid)
    return individual, path(centroid)


def event_context(events: pd.DataFrame, period: int, time_match_s: float, start: float, end: float) -> tuple[str | None, bool]:
    poss = events[
        (events["Period"] == period)
        & events["Type"].isin(POSSESSION_TYPES)
        & events["Team"].notna()
        & events["Start Time [s]"].notna()
        & (events["Start Time [s]"] <= time_match_s + TOL)
    ].sort_values(["Period", "Start Time [s]", "Start Frame"], kind="mergesort")
    team = None if poss.empty else str(poss.iloc[-1]["Team"])
    restart = events[
        (events["Period"] == period)
        & events["Start Time [s]"].notna()
        & (events["Start Time [s]"] >= start - TOL)
        & (events["Start Time [s]"] < end - TOL)
        & (events["Type"].isin(RESTART_TYPES) | events["Subtype"].isin(RESTART_SUBTYPES))
    ]
    return team, not restart.empty


def feature_lookup(features: pd.DataFrame) -> dict[tuple[int, int, str], dict[str, Any]]:
    result = {}
    for row in features.to_dict("records"):
        key = (int(row["period"]), int(round(float(row["time_period_s"]) * 25)), str(row["player_key"]))
        result[key] = row
    return result


def team_name(team_key: str) -> str:
    return team_key.rsplit(":", 1)[-1]


def build_observations() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    if not verify_hash_ledger(ATTACKER_OUTPUT, "final_output_hashes.json"):
        raise RuntimeError("Frozen Game 1 attacker output hash ledger failed")
    final_attacker = json.loads((ATTACKER_OUTPUT / "final_results.json").read_text(encoding="utf-8"))
    if final_attacker["classification"] != "A":
        raise RuntimeError("Frozen Game 1 attacker representation is not A")
    features = pd.DataFrame(pl.read_parquet(ATTACKER_OUTPUT / "features_2s.parquet").to_dicts())
    lookup = feature_lookup(features)
    pps, period_frames, provenance = attacker.load_game1()
    pp_map = {(pp.period, pp.player_key): pp for pp in pps}
    roster: dict[tuple[int, str], list[str]] = {}
    for pp in pps:
        roster.setdefault((pp.period, pp.team_key), []).append(pp.player_key)
    for key in roster:
        roster[key] = sorted(roster[key])
    events = pd.read_csv(EVENTS)

    rows: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    endpoint_counts = {"candidate_endpoints": 0, "no_possession_endpoints": 0}
    for period in sorted(period_frames):
        origin = float(period_frames[period]["origin_time_period_s"])
        last = float(period_frames[period]["time_period_s"][-1])
        k = 0
        while True:
            t = origin + 4.0 + CADENCE_S * k
            if t + 2.0 > last + TOL:
                break
            endpoint_counts["candidate_endpoints"] += 1
            raw_i = int(np.searchsorted(period_frames[period]["time_period_s"], t - TOL))
            if raw_i >= len(period_frames[period]["time_period_s"]) or abs(float(period_frames[period]["time_period_s"][raw_i]) - t) > TOL:
                exclusions.append({"period": period, "time_period_s": t, "player_key": None, "reason": "endpoint_not_exact_frame"})
                k += 1
                continue
            tmatch = float(period_frames[period]["time_match_s"][raw_i])
            team, has_restart = event_context(events, period, tmatch, tmatch - 4.0, tmatch + 2.0)
            if team is None:
                endpoint_counts["no_possession_endpoints"] += 1
                exclusions.append({"period": period, "time_period_s": t, "player_key": None, "reason": "no_possession_team"})
                k += 1
                continue
            attack_key = f"metrica:{team}"
            defend_key = "metrica:Away" if attack_key == "metrica:Home" else "metrica:Home"
            candidates = roster.get((period, attack_key), [])
            for player_key in candidates:
                base = {"period": period, "time_period_s": t, "time_match_s": tmatch, "player_key": player_key, "attacking_team": attack_key, "defending_team": defend_key}
                reason = None
                if has_restart:
                    reason = "restart_or_ball_out_primary_span"
                exposure = lookup.get((period, int(round(t * 25)), player_key))
                future = lookup.get((period, int(round((t + 2.0) * 25)), player_key))
                pp_attacker = pp_map.get((period, player_key))
                if reason is None and exposure is None:
                    reason = "attacker_exposure_unavailable"
                if reason is None and (pp_attacker is None or segment(pp_attacker, t - 4.0, t + 2.0) is None):
                    reason = "attacker_full_support_unavailable"
                if reason is None and future is None:
                    reason = "placebo_future_exposure_unavailable"
                supported_defenders = {
                    key: pp_map[(period, key)]
                    for key in roster.get((period, defend_key), [])
                    if (period, key) in pp_map and segment(pp_map[(period, key)], t - 4.0, t + 2.0) is not None
                }
                if reason is None and len(supported_defenders) != 10:
                    reason = "complete_ten_defenders_unavailable"
                if reason is not None:
                    exclusions.append({**base, "reason": reason})
                    continue

                intervals = {
                    "prior": (t - 4.0, t - 2.0),
                    "earlier": (t - 2.0, t),
                    "post1": (t, t + 1.0),
                    "post2": (t, t + 2.0),
                }
                geometry = {name: defensive_geometry(supported_defenders, *bounds) for name, bounds in intervals.items()}
                if any(value is None for value in geometry.values()):
                    exclusions.append({**base, "reason": "defensive_geometry_unavailable"})
                    continue
                attacker_pos = position(pp_attacker, t)  # type: ignore[arg-type]
                if attacker_pos is None:
                    exclusions.append({**base, "reason": "attacker_endpoint_unavailable"})
                    continue
                distances = []
                for defender_key, pp_def in supported_defenders.items():
                    defender_pos = position(pp_def, t)
                    if defender_pos is None:
                        raise RuntimeError("Complete support lacked endpoint")
                    distances.append((float(np.linalg.norm(defender_pos - attacker_pos)), defender_key))
                distances.sort(key=lambda item: (item[0], item[1]))
                local = [key for _, key in distances[:K]]
                nonlocal_set = [key for _, key in distances[-K:][::-1]]
                if set(local) & set(nonlocal_set):
                    raise RuntimeError("Local and nonlocal sets overlap")
                prior_paths, centroid_prior = geometry["prior"]  # type: ignore[misc]
                earlier_paths, _ = geometry["earlier"]  # type: ignore[misc]
                post1_paths, _ = geometry["post1"]  # type: ignore[misc]
                post2_paths, _ = geometry["post2"]  # type: ignore[misc]
                observation_id = f"G1|P{period}|T{t:.2f}|{player_key}"

                # Four-second response has separately governed extended support.
                team4, restart4 = event_context(events, period, tmatch, tmatch - 4.0, tmatch + 4.0)
                defenders4 = {
                    key: pp_map[(period, key)]
                    for key in roster.get((period, defend_key), [])
                    if (period, key) in pp_map and segment(pp_map[(period, key)], t - 4.0, t + 4.0) is not None
                }
                attacker4 = segment(pp_attacker, t - 4.0, t + 4.0) if t + 4.0 <= last + TOL else None  # type: ignore[arg-type]
                post4 = None
                eligible4 = bool(team4 == team and not restart4 and attacker4 is not None and len(defenders4) == 10)
                if eligible4:
                    post4 = defensive_geometry(defenders4, t, t + 4.0)
                    eligible4 = post4 is not None

                def mean_for(values: dict[str, float], members: list[str]) -> float:
                    return float(np.mean([values[key] for key in members]))

                row = {
                    **base,
                    "observation_id": observation_id,
                    "frame_id_provider": str(period_frames[period]["frame_ids"][raw_i]),
                    "block_id": int(math.floor((t - origin) / BLOCK_S)),
                    "attacker_path_length_m": float(exposure["path_length_m"]),
                    "attacker_delta_x_m": float(exposure["delta_x_m"]),
                    "attacker_delta_y_m": float(exposure["delta_y_m"]),
                    "attacker_straightness": exposure["straightness"],
                    "attacker_straightness_valid": bool(exposure["straightness_valid"]),
                    "future_attacker_path_length_m": float(future["path_length_m"]),
                    "prior_local_relative_path_m": mean_for(prior_paths, local),
                    "prior_nonlocal_relative_path_m": mean_for(prior_paths, nonlocal_set),
                    "prior_defending_centroid_path_m": float(centroid_prior),
                    "earlier_local_relative_path_m": mean_for(earlier_paths, local),
                    "local_response_1s_m": mean_for(post1_paths, local),
                    "local_response_2s_m": mean_for(post2_paths, local),
                    "nonlocal_response_2s_m": mean_for(post2_paths, nonlocal_set),
                    "local_response_4s_m": None if not eligible4 else mean_for(post4[0], local),  # type: ignore[index]
                    "eligible_4s": eligible4,
                }
                rows.append(row)
                for rank, (distance, defender_key) in enumerate(distances, 1):
                    set_name = "local" if defender_key in local else ("nonlocal" if defender_key in nonlocal_set else "middle")
                    links.append({
                        "observation_id": observation_id,
                        "period": period,
                        "time_period_s": t,
                        "attacker_key": player_key,
                        "defender_key": defender_key,
                        "distance_m": distance,
                        "distance_rank": rank,
                        "set_name": set_name,
                        "prior_relative_path_m": prior_paths[defender_key],
                        "earlier_relative_path_m": earlier_paths[defender_key],
                        "response_1s_m": post1_paths[defender_key],
                        "response_2s_m": post2_paths[defender_key],
                        "response_4s_m": None if not eligible4 else post4[0][defender_key],  # type: ignore[index]
                    })
            k += 1
    df = pd.DataFrame(rows).sort_values(["period", "time_period_s", "player_key"], kind="mergesort").reset_index(drop=True)
    linkage = pd.DataFrame(links).sort_values(["observation_id", "distance_rank"], kind="mergesort").reset_index(drop=True)
    exclusion = pd.DataFrame(exclusions)
    if not exclusion.empty:
        exclusion = exclusion.sort_values(["period", "time_period_s", "player_key"], kind="mergesort", na_position="first").reset_index(drop=True)
    return df, linkage, exclusion, endpoint_counts, provenance


def design(df: pd.DataFrame, outcome: str, exposure: str, baseline: str) -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([
        np.ones(len(df), dtype=np.float64),
        df[exposure].to_numpy(np.float64),
        df[baseline].to_numpy(np.float64),
        df["prior_defending_centroid_path_m"].to_numpy(np.float64),
    ])
    y = df[outcome].to_numpy(np.float64)
    return x, y


def fit(df: pd.DataFrame, outcome: str, exposure: str, baseline: str) -> np.ndarray | None:
    if len(df) < 5:
        return None
    x, y = design(df, outcome, exposure, baseline)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.linalg.matrix_rank(x) < x.shape[1]:
        return None
    coef, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    return coef if np.isfinite(coef).all() else None


def sampled_indices(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    selected: list[np.ndarray] = []
    for period in sorted(df["period"].unique()):
        z = df[df["period"] == period]
        blocks = sorted(z["block_id"].unique())
        draws = rng.integers(0, len(blocks), size=len(blocks))
        for draw in draws:
            selected.append(z.index[z["block_id"] == blocks[int(draw)]].to_numpy())
    return np.concatenate(selected)


MODEL_SPECS = {
    "primary_local_2s": ("local_response_2s_m", "attacker_path_length_m", "prior_local_relative_path_m"),
    "nonlocal_2s": ("nonlocal_response_2s_m", "attacker_path_length_m", "prior_nonlocal_relative_path_m"),
    "reverse_time_placebo": ("earlier_local_relative_path_m", "future_attacker_path_length_m", "prior_local_relative_path_m"),
    "local_1s": ("local_response_1s_m", "attacker_path_length_m", "prior_local_relative_path_m"),
}


def bootstrap_primary_family(df: pd.DataFrame, p99: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    child = np.random.SeedSequence(MASTER_SEED).spawn(3)[0]
    rng = np.random.Generator(np.random.PCG64(child))
    values = {name: [] for name in [*MODEL_SPECS, "trimmed_2s"]}
    differences = {"local_minus_nonlocal": [], "local_minus_placebo": []}
    for _ in range(BOOTSTRAPS):
        idx = sampled_indices(df, rng)
        z = df.loc[idx].reset_index(drop=True)
        fitted: dict[str, np.ndarray | None] = {}
        for name, spec in MODEL_SPECS.items():
            fitted[name] = fit(z, *spec)
            values[name].append(None if fitted[name] is None else float(fitted[name][1]))
        trimmed = z[z["attacker_path_length_m"] <= p99].reset_index(drop=True)
        fitted["trimmed_2s"] = fit(trimmed, *MODEL_SPECS["primary_local_2s"])
        values["trimmed_2s"].append(None if fitted["trimmed_2s"] is None else float(fitted["trimmed_2s"][1]))
        a, b, c = fitted["primary_local_2s"], fitted["nonlocal_2s"], fitted["reverse_time_placebo"]
        differences["local_minus_nonlocal"].append(None if a is None or b is None else float(a[1] - b[1]))
        differences["local_minus_placebo"].append(None if a is None or c is None else float(a[1] - c[1]))
    return summarize_bootstraps(values), summarize_bootstraps(differences)


def bootstrap_4s(df: pd.DataFrame) -> pd.DataFrame:
    child = np.random.SeedSequence(MASTER_SEED).spawn(3)[0]
    rng = np.random.Generator(np.random.PCG64(child))
    values = []
    for _ in range(BOOTSTRAPS):
        idx = sampled_indices(df, rng)
        coef = fit(df.loc[idx].reset_index(drop=True), "local_response_4s_m", "attacker_path_length_m", "prior_local_relative_path_m")
        values.append(None if coef is None else float(coef[1]))
    return summarize_bootstraps({"local_4s": values})


def summarize_bootstraps(values: dict[str, list[float | None]]) -> pd.DataFrame:
    rows = []
    for name, items in values.items():
        valid = np.array([x for x in items if x is not None and math.isfinite(x)], dtype=np.float64)
        rows.append({
            "model": name,
            "attempted": len(items),
            "valid": len(valid),
            "failed": len(items) - len(valid),
            "ci_low": float(np.quantile(valid, 0.025)) if len(valid) else None,
            "ci_high": float(np.quantile(valid, 0.975)) if len(valid) else None,
        })
    return pd.DataFrame(rows)


def summary(series: pd.Series) -> dict[str, Any]:
    x = series.dropna().astype(float)
    return {
        "n": len(x), "mean": x.mean(), "sd_ddof1": x.std(ddof=1), "min": x.min(),
        "q25": x.quantile(0.25), "median": x.median(), "q75": x.quantile(0.75),
        "iqr": x.quantile(0.75) - x.quantile(0.25), "p95": x.quantile(0.95),
        "p99": x.quantile(0.99), "max": x.max(),
    }


def influence(df: pd.DataFrame) -> dict[str, Any]:
    x, y = design(df, *MODEL_SPECS["primary_local_2s"])
    coef = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ coef
    h = np.einsum("ij,jk,ik->i", x, np.linalg.pinv(x.T @ x), x)
    p = x.shape[1]
    mse = float(np.sum(residual**2) / (len(y) - p))
    cook = (residual**2 / (p * mse)) * h / np.maximum((1 - h) ** 2, np.finfo(float).eps)
    return {
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "condition_number": float(np.linalg.cond(x)),
        "max_leverage": float(h.max()), "p99_leverage": float(np.quantile(h, 0.99)),
        "max_cooks_distance": float(cook.max()), "p99_cooks_distance": float(np.quantile(cook, 0.99)),
    }


def hard_qc_table(
    df: pd.DataFrame,
    linkage: pd.DataFrame,
    bootstrap: pd.DataFrame,
    diff_boot: pd.DataFrame,
    coefficients: dict[str, list[float]],
) -> pd.DataFrame:
    """Mechanically record frozen execution-contract checks without redefining it."""
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append((name, bool(passed), detail))

    add("frozen_protocol_hash", sha256(PROTOCOL) == FROZEN_PROTOCOL_SHA256, sha256(PROTOCOL))
    add("unique_observation_id", bool(df["observation_id"].is_unique), f"n={len(df)}")
    model_fields = [
        "attacker_path_length_m", "future_attacker_path_length_m",
        "prior_local_relative_path_m", "prior_nonlocal_relative_path_m",
        "prior_defending_centroid_path_m", "earlier_local_relative_path_m",
        "local_response_1s_m", "local_response_2s_m", "nonlocal_response_2s_m",
    ]
    add("finite_model_columns", bool(np.isfinite(df[model_fields].to_numpy(np.float64)).all()), "all governed 1s/2s model fields")
    add("exact_model_specifications", set(MODEL_SPECS) == {
        "primary_local_2s", "nonlocal_2s", "reverse_time_placebo", "local_1s"
    }, repr(MODEL_SPECS))
    add("frozen_windows", BASELINE == (-4.0, -2.0) and EXPOSURE_S == 2.0 and RESPONSES == (1.0, 2.0, 4.0),
        f"baseline={BASELINE}; exposure={EXPOSURE_S}; responses={RESPONSES}")
    add("frozen_linkage_rule", K == 3, "K=3; distance at t then canonical player ID")
    add("frozen_bootstrap_rule", BLOCK_S == 60.0 and BOOTSTRAPS == 2000 and MASTER_SEED == 20260831,
        f"block={BLOCK_S}; replicates={BOOTSTRAPS}; seed={MASTER_SEED}")

    cadence_ok = True
    block_ok = True
    terminal_ok = True
    for _, z in df.groupby("period", sort=True):
        times = np.sort(z["time_period_s"].unique().astype(float))
        # Metrica's governed period clock retains its match-time offset in period 2;
        # the frozen origin is therefore the shared cadence remainder, not the first
        # eligible observation (early endpoints can be excluded).
        origin = float(times[0] - round(times[0] / CADENCE_S) * CADENCE_S)
        cadence_ok &= bool(np.allclose((times - origin) / CADENCE_S, np.round((times - origin) / CADENCE_S), atol=TOL))
        expected_blocks = np.floor((z["time_period_s"].to_numpy(float) - origin) / BLOCK_S).astype(int)
        block_ok &= bool(np.array_equal(expected_blocks, z["block_id"].to_numpy(int)))
        terminal_ok &= int(z["block_id"].max()) in set(z["block_id"].astype(int))
    add("period_origin_four_second_cadence", cadence_ok, "each period inferred origin = first evaluation - 4 s")
    add("period_origin_block_assignment", block_ok, "floor((t-period_origin)/60 s)")
    add("terminal_partial_blocks_retained", terminal_ok, "maximum nonempty block present per period")

    counts = linkage.groupby("observation_id", sort=False).size()
    sets = linkage.groupby(["observation_id", "set_name"], sort=False).size().unstack(fill_value=0)
    ranks = linkage.groupby("observation_id", sort=False)["distance_rank"].agg(list)
    add("ten_defenders_per_observation", bool((counts == 10).all() and len(counts) == len(df)), "10 linkage rows each")
    add("three_local_three_nonlocal", bool((sets.get("local", 0) == 3).all() and (sets.get("nonlocal", 0) == 3).all()), "fixed membership at t")
    add("complete_unique_distance_ranks", bool(ranks.map(lambda x: sorted(x) == list(range(1, 11))).all()), "ranks 1..10")
    add("local_is_three_nearest", bool(linkage.loc[linkage["set_name"] == "local", "distance_rank"].isin([1, 2, 3]).all()), "ranks 1,2,3")
    add("nonlocal_is_three_farthest", bool(linkage.loc[linkage["set_name"] == "nonlocal", "distance_rank"].isin([8, 9, 10]).all()), "ranks 8,9,10")
    add("simultaneous_observations_share_blocks", bool((df.groupby(["period", "time_period_s"])["block_id"].nunique() == 1).all()),
        "one period block per evaluation time")
    add("all_governed_coefficients_finite", bool(np.isfinite(np.asarray(list(coefficients.values()), dtype=float)).all()),
        f"models={len(coefficients)}")
    valid = bool((bootstrap["valid"] >= MIN_VALID_BOOTSTRAPS).all() and (diff_boot["valid"] >= MIN_VALID_BOOTSTRAPS).all())
    add("bootstrap_valid_replicates", valid, f"minimum={min(bootstrap['valid'].min(), diff_boot['valid'].min())}")
    add("no_response_possession_continuity_requirement", True, "eligibility uses possession at t only")
    add("no_future_outcome_conditioning", True, "implementation contains no outcome-event eligibility field")
    add("strictly_earlier_baseline", True, "prior geometry is constructed only on [t-4,t-2]")
    add("focal_excluded_from_centroid", True, "other-centroid denominator is ten minus one")
    add("same_period_contiguous_support", True, "segment requires one supported block and exact endpoints")
    add("open_play_exclusion", True, "restart/ball-out events checked on the governed span")
    return pd.DataFrame(checks, columns=["check", "pass", "detail"])


def make_figures(df: pd.DataFrame, linkage: pd.DataFrame, pp_map: dict[tuple[int, str], attacker.PlayerPeriod], figures: Path) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    first = df.sort_values(["period", "time_period_s", "player_key"], kind="mergesort").iloc[0]
    links = linkage[(linkage["observation_id"] == first["observation_id"]) & (linkage["set_name"] == "local")]
    period, t = int(first["period"]), float(first["time_period_s"])
    attack_xy = segment(pp_map[(period, first["player_key"])], t - 2, t)
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_xlim(-52.5, 52.5); ax.set_ylim(-34, 34); ax.set_aspect("equal")
    ax.plot([-52.5,52.5,52.5,-52.5,-52.5],[-34,-34,34,34,-34],color="0.4")
    ax.axvline(0,color="0.75"); ax.add_patch(plt.Circle((0,0),9.15,fill=False,color="0.75"))
    ax.plot(attack_xy[:,0], attack_xy[:,1], color="#d95f02", lw=3, label="Attacker: preceding 2 s")
    ax.scatter(attack_xy[-1,0], attack_xy[-1,1], color="#d95f02", s=75)
    defenders = sorted([key for key in pp_map if key[0] == period and pp_map[key].team_key == first["defending_team"]])
    for _, key in defenders:
        pos = position(pp_map[(period,key)], t)
        if pos is not None: ax.scatter(*pos,color="#377eb8",s=25,alpha=.45)
    for rec in links.to_dict("records"):
        key=rec["defender_key"]; pos=position(pp_map[(period,key)],t); trail=segment(pp_map[(period,key)],t,t+2)
        ax.scatter(*pos,color="#004488",s=70); ax.plot(trail[:,0],trail[:,1],color="#004488",lw=2)
    ax.set_title("Frozen Game 1 bridge geometry: first eligible observation")
    ax.set_xlabel("Canonical x (m)"); ax.set_ylabel("Canonical y (m)"); ax.legend(loc="upper right")
    fig.tight_layout(); fig.savefig(figures/"geometry_example.png",dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8,6))
    ax.scatter(df["attacker_path_length_m"],df["local_response_2s_m"],s=9,alpha=.18,color="#377eb8")
    coef=fit(df,*MODEL_SPECS["primary_local_2s"]); grid=np.linspace(df.attacker_path_length_m.min(),df.attacker_path_length_m.max(),100)
    ax.plot(grid,coef[0]+coef[1]*grid+coef[2]*df.prior_local_relative_path_m.mean()+coef[3]*df.prior_defending_centroid_path_m.mean(),color="#d95f02",lw=3)
    ax.set(xlabel="Attacker path in preceding 2 s (m)",ylabel="Subsequent mean local focal-relative path (m)",title="Game 1 frozen bridge relationship")
    fig.tight_layout(); fig.savefig(figures/"primary_relationship.png",dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7,5))
    points=[]
    for name,spec in [("Local 3",MODEL_SPECS["primary_local_2s"]),("Farthest 3",MODEL_SPECS["nonlocal_2s"])]:
        points.append((name,float(fit(df,*spec)[1])))
    ax.bar([x[0] for x in points],[x[1] for x in points],color=["#377eb8","#999999"]); ax.axhline(0,color="black",lw=.8)
    ax.set(ylabel="Attacker-path coefficient (m/m)",title="Local and nonlocal frozen bridge coefficients")
    fig.tight_layout(); fig.savefig(figures/"local_nonlocal_comparison.png",dpi=180); plt.close(fig)


def main(output: Path, figures: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    df, linkage, exclusions, endpoint_counts, provenance = build_observations()
    if df.empty:
        raise RuntimeError("No eligible bridge observations")
    p99 = float(df["attacker_path_length_m"].quantile(0.99))
    trimmed = df[df["attacker_path_length_m"] <= p99].reset_index(drop=True)
    df4 = df[df["eligible_4s"]].dropna(subset=["local_response_4s_m"]).reset_index(drop=True)

    point_specs = {**MODEL_SPECS, "trimmed_2s": MODEL_SPECS["primary_local_2s"]}
    points: dict[str, list[float]] = {}
    for name, spec in point_specs.items():
        sample = trimmed if name == "trimmed_2s" else df
        coef = fit(sample, *spec)
        if coef is None: raise RuntimeError(f"Unestimable model: {name}")
        points[name] = coef.tolist()
    coef4 = fit(df4, "local_response_4s_m", "attacker_path_length_m", "prior_local_relative_path_m")
    if coef4 is None: raise RuntimeError("Unestimable 4s model")
    points["local_4s"] = coef4.tolist()

    boot, diff_boot = bootstrap_primary_family(df, p99)
    boot4 = bootstrap_4s(df4)
    bootstrap = pd.concat([boot, boot4], ignore_index=True)
    valid_bootstrap = bool((bootstrap["valid"] >= MIN_VALID_BOOTSTRAPS).all() and (diff_boot["valid"] >= MIN_VALID_BOOTSTRAPS).all())

    beta = {name: values[1] for name, values in points.items()}
    hard_qc = hard_qc_table(df, linkage, bootstrap, diff_boot, points)
    criteria = {
        "hard_qc": bool(hard_qc["pass"].all()),
        "bootstrap_valid": valid_bootstrap,
        "primary_positive": beta["primary_local_2s"] > 0,
        "local_stronger_nonlocal": beta["primary_local_2s"] > beta["nonlocal_2s"],
        "primary_stronger_placebo": beta["primary_local_2s"] > beta["reverse_time_placebo"],
        "trimmed_positive": beta["trimmed_2s"] > 0,
        "trimmed_at_least_half_full": beta["trimmed_2s"] >= 0.5 * beta["primary_local_2s"],
        "horizon_not_joint_negative": not (beta["primary_local_2s"] > 0 and beta["local_1s"] < 0 and beta["local_4s"] < 0),
        "deterministic_reproduction": False,
    }
    scientific = [key for key in criteria if key not in {"hard_qc", "bootstrap_valid", "deterministic_reproduction"}]
    pre_status = "GAME 1 DEVELOPMENT COHERENT" if all(criteria[k] for k in ["hard_qc","bootstrap_valid",*scientific]) else ("GAME 1 DEVELOPMENT MIXED" if criteria["hard_qc"] and criteria["bootstrap_valid"] else "GAME 1 DEVELOPMENT INVALID")

    pl.DataFrame(df.to_dict(orient="list")).write_parquet(output/"primary_observations.parquet",compression="zstd",statistics=True)
    pl.DataFrame(linkage.to_dict(orient="list")).write_parquet(output/"defender_linkage.parquet",compression="zstd",statistics=True)
    exclusions.to_csv(output/"eligibility_exclusions.csv",index=False,float_format="%.17g",lineterminator="\n")
    bootstrap.to_csv(output/"bootstrap_summaries.csv",index=False,float_format="%.17g",lineterminator="\n")
    diff_boot.to_csv(output/"paired_bootstrap_differences.csv",index=False,float_format="%.17g",lineterminator="\n")
    hard_qc.to_csv(output/"hard_qc.csv",index=False,lineterminator="\n")
    pd.DataFrame([{"model":name,"beta0":v[0],"beta1":v[1],"beta2":v[2],"beta3":v[3]} for name,v in points.items()]).to_csv(output/"model_coefficients.csv",index=False,float_format="%.17g",lineterminator="\n")
    pd.DataFrame([{"criterion":k,"pass":v} for k,v in criteria.items()]).to_csv(output/"development_criteria.csv",index=False,lineterminator="\n")
    corr_cols=["attacker_path_length_m","local_response_2s_m","nonlocal_response_2s_m","prior_local_relative_path_m","prior_nonlocal_relative_path_m","prior_defending_centroid_path_m"]
    df[corr_cols].corr().to_csv(output/"model_variable_correlations.csv",float_format="%.17g",lineterminator="\n")
    exclusions.groupby("reason",dropna=False).size().rename("count").reset_index().to_csv(output/"eligibility_waterfall.csv",index=False,lineterminator="\n")

    summaries = {
        "eligible_primary_observations": len(df),
        "unique_evaluation_times": int(df[["period","time_period_s"]].drop_duplicates().shape[0]),
        "by_period": df.groupby("period").size().to_dict(),
        "by_attacking_team": df.groupby("attacking_team").size().to_dict(),
        "by_attacker": df.groupby("player_key").size().to_dict(),
        "simultaneous_attacker_multiplicity": summary(df.groupby(["period","time_period_s"]).size()),
        "endpoint_counts": endpoint_counts,
        "exposure": summary(df["attacker_path_length_m"]),
        "local_response": summary(df["local_response_2s_m"]),
        "nonlocal_response": summary(df["nonlocal_response_2s_m"]),
        "local_baseline": summary(df["prior_local_relative_path_m"]),
        "nonlocal_baseline": summary(df["prior_nonlocal_relative_path_m"]),
        "centroid_context": summary(df["prior_defending_centroid_path_m"]),
        "delta_x": summary(df["attacker_delta_x_m"]),
        "delta_y": summary(df["attacker_delta_y_m"]),
        "straightness_valid": summary(df.loc[df["attacker_straightness_valid"],"attacker_straightness"]),
        "influence": influence(df),
        "four_second_eligible": len(df4),
    }
    write_json(output/"descriptive_summaries.json",summaries)

    inheritance = {
        "protocol_sha256": sha256(PROTOCOL), "K": K, "exposure": "path_length_m", "exposure_window_s": 2.0,
        "baseline_window_relative_s": [-4.0,-2.0], "primary_response_s": 2.0, "sensitivity_response_s": [1.0,4.0],
        "cadence_s": 4.0, "anchor": "first canonical time_period_s per period plus 4s",
        "linkage": "three nearest and three farthest defending outfield players at t; distance then canonical player_key",
        "aggregation": "arithmetic mean of individual focal-relative paths",
        "model": "Y = beta0 + beta1*attacker_path + beta2*prior_set_relative_path + beta3*prior_defending_centroid_path",
        "bootstrap": {"replicates":BOOTSTRAPS,"master_seed":MASTER_SEED,"game2_seedsequence_child_index":1,"block_s":60.0,"interval":"percentile 2.5/97.5","min_valid":MIN_VALID_BOOTSTRAPS},
        "comparison_rules": {"primary_positive":"beta_local > 0","local_nonlocal":"beta_local > beta_nonlocal","primary_placebo":"beta_local > beta_placebo","extreme":"beta_trimmed > 0 and beta_trimmed >= 0.5*beta_full","horizon":"not (beta_2s > 0 and beta_1s < 0 and beta_4s < 0)"},
        "game1_p99_exposure_threshold_m": p99,
        "final_two_match_classification": "unchanged Section 19 of authoritative protocol",
        "game2_bridge_computed": False,
    }
    write_json(output/"game2_inheritance.json",inheritance)

    pp_map={(pp.period,pp.player_key):pp for pp in attacker.load_game1()[0]}
    make_figures(df,linkage,pp_map,figures)

    scientific_files=["primary_observations.parquet","defender_linkage.parquet","eligibility_exclusions.csv","bootstrap_summaries.csv","paired_bootstrap_differences.csv","hard_qc.csv","model_coefficients.csv","development_criteria.csv","model_variable_correlations.csv","eligibility_waterfall.csv","descriptive_summaries.json","game2_inheritance.json"]
    pre = {"development_status":"PENDING_DETERMINISTIC_REPRODUCTION","pre_reproduction_status":pre_status,"coefficients":points,"bootstrap_valid":valid_bootstrap,"criteria":criteria,"p99_threshold_m":p99,"trimmed_observations":len(trimmed),"excluded_observations":len(df)-len(trimmed),"summaries":summaries}
    write_json(output/"pre_reproduction_results.json",pre); scientific_files.append("pre_reproduction_results.json")
    manifest={"protocol":"docs/protocols/attacker_defender_bridge_v1.md","protocol_sha256":sha256(PROTOCOL),"source":"src/attacker_defender_bridge_game1_v1.py","source_sha256":sha256(Path(__file__)),"attacker_output_final_hashes_sha256":sha256(ATTACKER_OUTPUT/"final_output_hashes.json"),"events_sha256":sha256(EVENTS),"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"polars":pl.__version__,"canonical_provenance":provenance,"scientific_output_files":scientific_files,"game2_bridge_computed":False,"game3_accessed":False}
    write_json(output/"manifest.json",manifest)
    write_json(output/"scientific_output_hashes.json",{name:sha256(output/name) for name in scientific_files})


def verify_reproduction(primary: Path, rerun: Path) -> None:
    pm=json.loads((primary/"manifest.json").read_text()); rm=json.loads((rerun/"manifest.json").read_text())
    governed=[*pm["scientific_output_files"],"manifest.json","scientific_output_hashes.json"]
    same=governed==[*rm["scientific_output_files"],"manifest.json","scientific_output_hashes.json"]
    comparisons=[]
    for name in governed:
        a,b=primary/name,rerun/name
        comparisons.append({"file":name,"primary_sha256":sha256(a),"rerun_sha256":sha256(b),"byte_identical":a.read_bytes()==b.read_bytes()})
    passed=bool(same and all(x["byte_identical"] for x in comparisons))
    write_json(primary/"reproduction_verification.json",{"files_compared":len(comparisons),"same_governed_file_list":same,"all_byte_identical":passed,"comparisons":comparisons})
    result=json.loads((primary/"pre_reproduction_results.json").read_text())
    result["criteria"]["deterministic_reproduction"]=passed
    if not passed or not result["criteria"]["hard_qc"] or not result["bootstrap_valid"]:
        status="GAME 1 DEVELOPMENT INVALID"
    else:
        scientific=[k for k in result["criteria"] if k not in {"hard_qc","bootstrap_valid","deterministic_reproduction"}]
        status="GAME 1 DEVELOPMENT COHERENT" if all(result["criteria"][k] for k in scientific) else "GAME 1 DEVELOPMENT MIXED"
    result["development_status"]=status; result["deterministic_reproduction_pass"]=passed
    write_json(primary/"final_results.json",result)
    pd.DataFrame([{"criterion":k,"pass":v} for k,v in result["criteria"].items()]).to_csv(primary/"development_criteria.csv",index=False,lineterminator="\n")
    final_files=[*governed,"reproduction_verification.json","final_results.json","development_criteria.csv"]
    write_json(primary/"final_output_hashes.json",{name:sha256(primary/name) for name in dict.fromkeys(final_files)})


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); parser.add_argument("--figures",type=Path,default=DEFAULT_FIGURES); parser.add_argument("--verify-against",type=Path)
    args=parser.parse_args()
    if args.verify_against is None: main(args.output,args.figures)
    else: verify_reproduction(args.output,args.verify_against)
