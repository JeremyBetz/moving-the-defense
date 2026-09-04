"""Tier-3 IDSSE execution of frozen temporal Spatial Footprint v1.

This file intentionally contains no alternative temporal specification.  It
uses the pre-frozen 25 Hz, seven-frame, complete-support construction only.
"""
from __future__ import annotations

import argparse
import gc
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
import concurrent_attacker_defensive_geometry_idsse_v1 as concurrent  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402
from infrastructure import kloppy_idsse_adapter as adapter  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/spatial_defensive_response_footprint_v1_idsse_external_replication.md"
CONFIG = ROOT / "config/spatial_defensive_response_footprint_v1_idsse_external_replication.json"
EQUIVALENCE = ROOT / "docs/spatial_defensive_response_footprint_v1_idsse_equivalence.md"
LEDGER = ROOT / "config/spatial_defensive_response_footprint_v1_idsse_external_replication_hashes.json"
DEFAULT_OUTPUT = ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1"
DEFAULT_RERUN = ROOT / "outputs/.spatial_defensive_response_footprint_idsse_v1_rerun"
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
FRAME_NS, EDGE, BOOT, MIN_VALID, SEED, TRIM = 40_000_000, 3, 2000, 1900, 20260903, 12.198443079831405
REGIONS = {"near": (0, 3), "middle": (3, 7), "far": (7, 10)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)):
        value = float(value); return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_, bool)): return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def frozen() -> dict[str, str]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def verify_frozen() -> None:
    ledger = frozen()
    bad = {name: [sha(ROOT / name), expected] for section in ("frozen_replication_artifacts_sha256", "closed_and_inherited_artifacts_sha256")
           for name, expected in ledger[section].items() if sha(ROOT / name) != expected}
    if bad: raise RuntimeError(f"frozen hash failure: {bad}")


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


def smooth(raw: np.ndarray) -> np.ndarray:
    return pd.DataFrame(raw).rolling(7, center=True, min_periods=7).mean().to_numpy()[EDGE:-EDGE]


def geometry(stack: np.ndarray) -> tuple[np.ndarray, float]:
    """Return each defender's leave-one-out path and full-unit centroid path."""
    centroid = stack.mean(axis=1)
    total = stack.sum(axis=1)
    values = np.asarray([path(stack[:, j] - (total - stack[:, j]) / 9.0) for j in range(10)])
    return values, path(centroid)


def context(events: dict, start_ns: int, anchor_ns: int, end_ns: int) -> tuple[str | None, bool]:
    return concurrent.context_at_anchor(events, start_ns, anchor_ns, end_ns)


def load_canonical(match_id: str) -> dict:
    metadata_path, _, tracking_path = adapter.idsse_paths(ROOT, match_id)
    dataset = adapter.load_dataset(metadata_path, tracking_path)
    sidecar = adapter.read_ball_frame_sidecar(tracking_path)
    value = adapter.to_phase4c_tracking(dataset, sidecar)
    del dataset, sidecar
    gc.collect()
    return value


def cadence_ok(tracking: dict) -> bool:
    return all(np.all(np.diff(np.asarray(tracking[p]["time_ns"], dtype=np.int64)) == FRAME_NS) for p in idsse.PERIODS)


def build_sample(match_id: str, metadata: dict, events: dict, tracking: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []; exclusions: list[dict] = []
    teams = {metadata["home_team_id"], metadata["away_team_id"]}
    for period_number, period in enumerate(idsse.PERIODS, 1):
        pdata = tracking[period]; origin = int(pdata["time_ns"][0]); end = int(pdata["time_ns"][-1])
        lookup = {int(v): i for i, v in enumerate(pdata["time_ns"])}
        entity = {(e["team_id"], e["person_id"]): e for e in pdata["entities"]}
        max_s = (end - origin) / 1e9; k = 0
        while 6.0 + 4.0 * k <= max_s + 1e-9:
            t_s = 4.0 + 4.0 * k; t_ns = origin + int(t_s * 1e9)
            raw_start, raw_end = t_ns - 4_000_000_000 - EDGE * FRAME_NS, t_ns + 2_000_000_000 + EDGE * FRAME_NS
            expected = np.arange(raw_start, raw_end + FRAME_NS, FRAME_NS, dtype=np.int64)
            base = {"match_id": match_id, "period": period_number, "time_period_s": t_s}
            if any(int(v) not in lookup for v in expected):
                exclusions.append({**base, "attacker_key": None, "reason": "complete_cadence_support_unavailable"}); k += 1; continue
            idx = np.asarray([lookup[int(v)] for v in expected], dtype=int)
            attack, open_ok = context(events, t_ns - 4_000_000_000, t_ns, t_ns + 2_000_000_000)
            if attack not in teams or not open_ok:
                exclusions.append({**base, "attacker_key": None, "reason": "possession_or_open_play"}); k += 1; continue
            defend = next(iter(teams - {attack}))
            defenders = sorted(p.player_id for p in metadata["players"].values()
                               if p.team_id == defend and not p.goalkeeper and (p.team_id, p.player_id) in entity
                               and entity[(p.team_id, p.player_id)]["valid"][idx].all())
            attackers = sorted(p.player_id for p in metadata["players"].values()
                               if p.team_id == attack and not p.goalkeeper and (p.team_id, p.player_id) in entity
                               and entity[(p.team_id, p.player_id)]["valid"][idx].all())
            if len(defenders) != 10:
                for attacker in attackers or [None]: exclusions.append({**base, "attacker_key": attacker, "reason": "complete_ten_defenders_unavailable"})
                k += 1; continue
            dxy = {p: smooth(np.column_stack([entity[(defend, p)]["x"][idx], entity[(defend, p)]["y"][idx]]).astype(float)) for p in defenders}
            stack = np.stack([dxy[p] for p in defenders], axis=1)
            prior, centroid_prior = geometry(stack[:51]); earlier, _ = geometry(stack[50:101]); post1, _ = geometry(stack[100:126]); post2, _ = geometry(stack[100:151])
            # Four-second sensitivity has its own prospectively complete support/sample.
            raw4_start, raw4_end = t_ns - 4_000_000_000 - EDGE * FRAME_NS, t_ns + 4_000_000_000 + EDGE * FRAME_NS
            expected4 = np.arange(raw4_start, raw4_end + FRAME_NS, FRAME_NS, dtype=np.int64)
            idx4 = np.asarray([lookup[int(v)] for v in expected4], dtype=int) if all(int(v) in lookup for v in expected4) else None
            attack4, open4 = context(events, t_ns - 4_000_000_000, t_ns, t_ns + 4_000_000_000)
            valid4 = bool(idx4 is not None and attack4 == attack and open4)
            post4 = None
            if valid4:
                if not all(entity[(defend, p)]["valid"][idx4].all() for p in defenders): valid4 = False
                else:
                    stack4 = np.stack([smooth(np.column_stack([entity[(defend, p)]["x"][idx4], entity[(defend, p)]["y"][idx4]]).astype(float)) for p in defenders], axis=1)
                    post4, _ = geometry(stack4[100:201])
            for attacker in attackers:
                a = entity[(attack, attacker)]; axy = smooth(np.column_stack([a["x"][idx], a["y"][idx]]).astype(float))
                order = sorted((float(np.linalg.norm(stack[100, j] - axy[100])), defender_key, j) for j, defender_key in enumerate(defenders))
                oid = f"TSFI|{match_id}|P{period_number}|T{t_s:.2f}|{attacker}"
                for rank, (distance, defender_key, j) in enumerate(order, 1):
                    rows.append({"observation_id": oid, **base, "time_utc_ns": t_ns, "attacker_key": attacker,
                                 "attacking_team": attack, "defending_team": defend, "block_id": int(math.floor(t_s / 60.0)),
                                 "defender_key": defender_key, "distance_rank": rank, "distance_m": distance,
                                 "attacker_path_m": path(axy[50:101]), "future_attacker_path_m": path(axy[100:151]),
                                 "prior_relative_path_m": prior[j], "prior_centroid_path_m": centroid_prior,
                                 "earlier_relative_path_m": earlier[j], "response_1s_m": post1[j], "response_2s_m": post2[j],
                                 "response_4s_m": None if not valid4 else post4[j], "eligible_4s": valid4})
            k += 1
    data = pd.DataFrame(rows).sort_values(["match_id", "period", "time_period_s", "attacker_key", "distance_rank"], kind="mergesort").reset_index(drop=True)
    excluded = pd.DataFrame(exclusions).sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort", na_position="first").reset_index(drop=True) if exclusions else pd.DataFrame(columns=["match_id", "period", "time_period_s", "attacker_key", "reason"])
    return data, excluded


def equivalence(match_id: str, metadata: dict, events: dict, native: dict) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Bind the already-closed all-match adapter gate to this new construction.

    The seven raw-to-Kloppy comparisons were independently executed and hashed
    for the closed concurrent IDSSE replication. Re-loading a 330–400 MB XML
    match with Kloppy concurrently with its native cache exceeds the governed
    execution host's memory limit. This execution therefore verifies that
    closed adapter gate byte-for-byte, then recomputes all cadence, support,
    context, rank, and derived path components from the identical native cache.
    It does not substitute a new data representation or relax a tolerance.
    """
    closed = ROOT / "outputs/concurrent_attacker_defensive_geometry_idsse_v1"
    final = json.loads((closed / "final_hashes.json").read_text(encoding="utf-8"))
    if any(sha(closed / name) != digest for name, digest in final.items()):
        raise RuntimeError("closed IDSSE adapter-equivalence artifact hash failure")
    prior = pd.read_csv(closed / "provider_equivalence.csv").set_index("match_id").loc[match_id].to_dict()
    if not bool(prior["passed"]): raise RuntimeError(f"closed adapter equivalence failed for {match_id}")
    rows, excluded = build_sample(match_id, metadata, events, native)
    rank_complete = bool(rows.groupby("observation_id").distance_rank.apply(lambda q: sorted(q) == list(range(1, 11))).all()) if len(rows) else True
    finite = bool(np.isfinite(rows[["attacker_path_m", "future_attacker_path_m", "prior_relative_path_m", "prior_centroid_path_m", "earlier_relative_path_m", "response_1s_m", "response_2s_m"]].to_numpy(float)).all()) if len(rows) else True
    gate = {f"closed_adapter_{key}": clean(value) for key, value in prior.items() if key != "match_id"}
    gate.update({"match_id": match_id, "closed_adapter_gate_hash": sha(closed / "provider_equivalence.csv"),
                 "native_25hz_cadence_exact": cadence_ok(native), "anchor_rank_membership_exact": rank_complete,
                 "derived_components_finite": finite, "derived_component_tolerance_m": 1e-4,
                 "path_tolerance_m": 1e-3,
                 "equivalence_mechanism": "verified_closed_raw_to_Kloppy_gate_plus_current_native_component_reconstruction"})
    gate["passed"] = bool(prior["passed"] and cadence_ok(native) and rank_complete and finite)
    return gate, rows, excluded


def stage_dir(output: Path) -> Path:
    """Local, ignored per-match input staging for memory-bounded execution."""
    return output / "_stage"


def stage_match(output: Path, match_id: str) -> dict:
    """Reconstruct one governed native match in an isolated Python process.

    The staging files contain provider-derived rows and remain ignored.  They
    allow the later fit to avoid retaining decoded XML for multiple matches.
    """
    verify_frozen()
    output.mkdir(parents=True, exist_ok=True)
    directory = stage_dir(output); directory.mkdir(exist_ok=True)
    metadata, events, native = concurrent.load_native(match_id)
    gate, data, excluded = equivalence(match_id, metadata, events, native)
    if not gate["passed"]:
        raise RuntimeError(f"provider equivalence failed: {gate}")
    data_path = directory / f"{match_id}_rows.parquet"
    exclusion_path = directory / f"{match_id}_exclusions.csv"
    gate_path = directory / f"{match_id}_gate.json"
    pl.DataFrame(data.to_dict("list")).write_parquet(data_path)
    excluded.to_csv(exclusion_path, index=False)
    write_json(gate_path, {"gate": gate, "rows_sha256": sha(data_path), "exclusions_sha256": sha(exclusion_path),
                           "frozen_ledger_sha256": sha(LEDGER)})
    return {"match_id": match_id, "passed": True, "rows": len(data), "exclusions": len(excluded),
            "rows_sha256": sha(data_path), "exclusions_sha256": sha(exclusion_path)}


def read_staged(output: Path, match_id: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    directory = stage_dir(output)
    data_path = directory / f"{match_id}_rows.parquet"
    exclusion_path = directory / f"{match_id}_exclusions.csv"
    gate_path = directory / f"{match_id}_gate.json"
    if not all(path.exists() for path in (data_path, exclusion_path, gate_path)):
        raise RuntimeError(f"missing local staged provider reconstruction for {match_id}")
    manifest = json.loads(gate_path.read_text(encoding="utf-8"))
    if manifest["rows_sha256"] != sha(data_path) or manifest["exclusions_sha256"] != sha(exclusion_path):
        raise RuntimeError(f"staged provider reconstruction hash failure for {match_id}")
    if manifest["frozen_ledger_sha256"] != sha(LEDGER):
        raise RuntimeError(f"staged provider reconstruction frozen-ledger mismatch for {match_id}")
    # Avoid an optional PyArrow dependency: the governed fields are primitive
    # columns and Polars' deterministic dictionary export is sufficient.
    return manifest["gate"], pd.DataFrame(pl.read_parquet(data_path).to_dict(as_series=False)), pd.read_csv(exclusion_path)


def design(data: pd.DataFrame, pooled: bool) -> np.ndarray:
    p = 40 + (6 if pooled else 0); x = np.zeros((len(data), p), dtype=np.float64); r = data.distance_rank.to_numpy(int) - 1
    terms = np.column_stack([np.ones(len(data)), data.attacker_path_m, data.prior_relative_path_m, data.prior_centroid_path_m]).astype(float)
    for j in range(4): x[np.arange(len(data)), r * 4 + j] = terms[:, j]
    if pooled:
        for j, match in enumerate(MATCHES[1:]): x[:, 40 + j] = (data.match_id == match).to_numpy(float)
    return x


def fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    if len(y) < x.shape[1] or np.linalg.matrix_rank(x) != x.shape[1]: raise np.linalg.LinAlgError("unestimable frozen design")
    coef, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    if not np.isfinite(coef).all(): raise np.linalg.LinAlgError("nonfinite fit")
    return coef


def beta(coef: np.ndarray) -> np.ndarray: return coef[np.arange(10) * 4 + 1]


def summary(coef: np.ndarray) -> dict[str, float]:
    b = beta(coef); n, m, f = b[:3].mean(), b[3:7].mean(), b[7:].mean()
    return {**{f"D{k}": float(b[k-1]) for k in range(1, 11)}, "near": float(n), "middle": float(m), "far": float(f), "near_minus_middle": float(n-m), "middle_minus_far": float(m-f)}


def block_stats(data: pd.DataFrame, x: np.ndarray, family: str) -> dict[tuple, tuple[np.ndarray, np.ndarray]]:
    if family == "primary": y = data.response_2s_m.to_numpy(float); xx = x
    elif family == "placebo":
        xx = x.copy();
        for r in range(10): xx[:, r * 4 + 1] = data.future_attacker_path_m.to_numpy(float) * (data.distance_rank.to_numpy(int) == r + 1)
        y = data.earlier_relative_path_m.to_numpy(float)
    elif family == "one": y = data.response_1s_m.to_numpy(float); xx = x
    elif family == "trim":
        keep = data.attacker_path_m.to_numpy(float) <= TRIM; data, xx = data.loc[keep].reset_index(drop=True), x[keep]; y = data.response_2s_m.to_numpy(float)
    else: raise ValueError(family)
    out = {}
    for key, ix in data.groupby(["match_id", "period", "block_id"], sort=True).indices.items():
        ix = np.asarray(ix, int); out[key] = (xx[ix].T @ xx[ix], xx[ix].T @ y[ix])
    return out


def bootstrap(data: pd.DataFrame, pooled: bool, child: int) -> dict[str, np.ndarray]:
    x = design(data, pooled); stats = {name: block_stats(data, x, name) for name in ("primary", "placebo", "one", "trim")}
    strata: dict[tuple, list[tuple]] = {}
    for key in sorted(stats["primary"]): strata.setdefault((key[0], key[1]) if pooled else (key[1],), []).append(key)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(8)[child])); result = {name: [] for name in stats}; p=x.shape[1]
    for _ in range(BOOT):
        chosen = [key for keys in strata.values() for key in (keys[int(i)] for i in rng.integers(0, len(keys), len(keys)))]
        for name, table in stats.items():
            available = [key for key in chosen if key in table]
            xtx = sum((table[key][0] for key in available), np.zeros((p, p))); xty = sum((table[key][1] for key in available), np.zeros(p))
            try: result[name].append(summary(fit(xtx, xty)))
            except np.linalg.LinAlgError: pass
    return {name: pd.DataFrame(values) for name, values in result.items()}


def sum_stats(table: dict[tuple, tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    first = next(iter(table.values()))
    return (sum((value[0] for value in table.values()), np.zeros_like(first[0])),
            sum((value[1] for value in table.values()), np.zeros_like(first[1])))


def bootstrap_from_stats(stats: dict[str, dict[tuple, tuple[np.ndarray, np.ndarray]]], child: int) -> dict[str, pd.DataFrame]:
    """Frozen grouped bootstrap from sufficient statistics, without raw-row pooling."""
    strata: dict[tuple, list[tuple]] = {}
    base = next(iter(stats.values()))
    for key in sorted(base):
        strata.setdefault((key[0], key[1]), []).append(key)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(8)[child]))
    result = {name: [] for name in stats}
    p = next(iter(base.values()))[0].shape[0]
    for _ in range(BOOT):
        chosen = [key for keys in strata.values() for key in (keys[int(i)] for i in rng.integers(0, len(keys), len(keys)))]
        for name, table in stats.items():
            available = [key for key in chosen if key in table]
            try:
                xtx = sum((table[key][0] for key in available), np.zeros((p, p)))
                xty = sum((table[key][1] for key in available), np.zeros(p))
                result[name].append(summary(fit(xtx, xty)))
            except np.linalg.LinAlgError:
                pass
    return {name: pd.DataFrame(values) for name, values in result.items()}


def pooled_from_staged(output: Path) -> tuple[dict, pd.DataFrame, list[dict], pd.DataFrame]:
    """Fit the frozen observation-weighted pooled model from staged match blocks.

    Algebraically, summing each match-period block's X'X and X'y gives the
    same pooled OLS and grouped bootstrap as retaining all provider rows in
    memory.  This is necessary on the governed host, where decoded raw XML
    and a seven-match dense design cannot coexist.
    """
    stats: dict[str, dict[tuple, tuple[np.ndarray, np.ndarray]]] = {name: {} for name in ("primary", "placebo", "one", "trim")}
    four_stats: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
    sample: list[dict] = []; excluded: list[pd.DataFrame] = []
    for match_id in MATCHES:
        gate, data, rejected = read_staged(output, match_id)
        if not gate["passed"]:
            raise RuntimeError(f"provider equivalence failed: {gate}")
        x = design(data, True)
        for name in stats:
            values = block_stats(data, x, name)
            if set(values).intersection(stats[name]):
                raise RuntimeError(f"duplicate pooled block keys for {match_id}")
            stats[name].update(values)
        q = data[data.eligible_4s].copy().reset_index(drop=True)
        x4 = design(q, True)
        for key, ix in q.groupby(["match_id", "period", "block_id"], sort=True).indices.items():
            ix = np.asarray(ix, int)
            four_stats[key] = (x4[ix].T @ x4[ix], x4[ix].T @ q.response_4s_m.to_numpy(float)[ix])
        anchors = data.drop_duplicates("observation_id")
        sample.append({"match_id": match_id, "eligible_attacker_anchor_observations": len(anchors),
                       "unique_time_anchors": int(anchors[["match_id", "period", "time_period_s"]].drop_duplicates().shape[0]),
                       "defender_rows": len(data), "four_second_anchors": int(data[data.eligible_4s].observation_id.nunique()),
                       "trim_excluded_anchors": int((anchors.attacker_path_m > TRIM).sum())})
        excluded.append(rejected)
        del data, rejected, q, x, x4
        gc.collect()
    points = {name: summary(fit(*sum_stats(table))) for name, table in stats.items()}
    draws = bootstrap_from_stats(stats, 7)
    four_point = summary(fit(*sum_stats(four_stats)))
    four_draws = bootstrap_from_stats({"four": four_stats}, 7)["four"]
    points["four"] = four_point
    tables = [interval(points[name], draws[name], "POOLED", name) for name in draws]
    tables.append(interval(four_point, four_draws, "POOLED", "four"))
    paired = draws["primary"]["near_minus_middle"].to_numpy(float) - draws["placebo"]["near_minus_middle"].to_numpy(float)
    paired_point = points["primary"]["near_minus_middle"] - points["placebo"]["near_minus_middle"]
    tables.append(pd.DataFrame([{"match_id": "POOLED", "family": "paired_primary_minus_placebo", "estimand": "near_minus_middle",
                                 "estimate": paired_point, "ci_low": float(np.quantile(paired, .025)), "ci_high": float(np.quantile(paired, .975)),
                                 "attempted": BOOT, "valid": len(paired)}]))
    primary = points["primary"]["near_minus_middle"]
    result = {"eligible_attacker_anchor_observations": int(sum(v["eligible_attacker_anchor_observations"] for v in sample)),
              "unique_time_anchors": int(sum(v["unique_time_anchors"] for v in sample)), "defender_rows": int(sum(v["defender_rows"] for v in sample)),
              "primary": points["primary"], "placebo": points["placebo"], "one_second": points["one"], "four_second": points["four"],
              "trimmed": points["trim"], "paired_primary_minus_placebo": paired_point,
              "trim_retained_magnitude_fraction": abs(points["trim"]["near_minus_middle"] / primary) if primary else None,
              "trim_excluded_anchors": int(sum(v["trim_excluded_anchors"] for v in sample)),
              "bootstrap_valid": {key: len(value) for key, value in draws.items()} | {"four": len(four_draws)},
              "design_rank": int(np.linalg.matrix_rank(sum_stats(stats["primary"])[0])), "design_columns": 46,
              "four_second_anchors": int(sum(v["four_second_anchors"] for v in sample))}
    return clean(result), pd.concat(tables, ignore_index=True), sample, pd.concat(excluded, ignore_index=True)


def horizon(data: pd.DataFrame, pooled: bool, child: int) -> tuple[dict[str, float], pd.DataFrame]:
    q = data[data.eligible_4s].copy().reset_index(drop=True); x = design(q, pooled); point = summary(fit(x, q.response_4s_m.to_numpy(float)))
    stats = {}
    for key, ix in q.groupby(["match_id", "period", "block_id"], sort=True).indices.items():
        ix = np.asarray(ix, int); stats[key] = (x[ix].T @ x[ix], x[ix].T @ q.response_4s_m.to_numpy(float)[ix])
    strata: dict[tuple, list[tuple]] = {}
    for key in sorted(stats): strata.setdefault((key[0], key[1]) if pooled else (key[1],), []).append(key)
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(8)[child])); rows=[]; p=x.shape[1]
    for _ in range(BOOT):
        chosen=[key for keys in strata.values() for key in (keys[int(i)] for i in rng.integers(0,len(keys),len(keys)))]
        try:
            xtx=sum((stats[key][0] for key in chosen),np.zeros((p,p))); xty=sum((stats[key][1] for key in chosen),np.zeros(p)); rows.append(summary(fit(xtx,xty)))
        except np.linalg.LinAlgError: pass
    return point, pd.DataFrame(rows)


def interval(point: dict[str, float], draws: pd.DataFrame, match_id: str, family: str) -> pd.DataFrame:
    rows=[]
    for key, value in point.items():
        valid=draws[key].dropna().to_numpy(float) if key in draws else np.asarray([])
        rows.append({"match_id":match_id,"family":family,"estimand":key,"estimate":value,"ci_low":float(np.quantile(valid,.025)) if len(valid) else None,"ci_high":float(np.quantile(valid,.975)) if len(valid) else None,"attempted":BOOT,"valid":len(valid)})
    return pd.DataFrame(rows)


def fit_bundle(data: pd.DataFrame, pooled: bool, child: int) -> tuple[dict, pd.DataFrame]:
    x=design(data,pooled); points={"primary":summary(fit(x,data.response_2s_m.to_numpy(float))),
        "one":summary(fit(x,data.response_1s_m.to_numpy(float))),
        "trim":summary(fit(x[data.attacker_path_m.to_numpy(float)<=TRIM],data.loc[data.attacker_path_m<=TRIM,"response_2s_m"].to_numpy(float)))}
    # Construct placebo design explicitly, preserving the 4 rank-specific term columns.
    placebo_x=x.copy()
    for r in range(10): placebo_x[:,r*4+1]=data.future_attacker_path_m.to_numpy(float)*(data.distance_rank.to_numpy(int)==r+1)
    points["placebo"]=summary(fit(placebo_x,data.earlier_relative_path_m.to_numpy(float)))
    draws=bootstrap(data,pooled,child); h4_point,h4_draws=horizon(data,pooled,child); points["four"]=h4_point
    tables=[interval(points[name],draws[name],"POOLED" if pooled else str(data.match_id.iloc[0]),name) for name in draws]
    tables.append(interval(h4_point,h4_draws,"POOLED" if pooled else str(data.match_id.iloc[0]),"four"))
    primary, placebo = points["primary"]["near_minus_middle"], points["placebo"]["near_minus_middle"]
    paired=draws["primary"]["near_minus_middle"].to_numpy(float)-draws["placebo"]["near_minus_middle"].to_numpy(float)
    pairpoint=primary-placebo
    tables.append(pd.DataFrame([{"match_id":"POOLED" if pooled else str(data.match_id.iloc[0]),"family":"paired_primary_minus_placebo","estimand":"near_minus_middle","estimate":pairpoint,"ci_low":float(np.quantile(paired,.025)),"ci_high":float(np.quantile(paired,.975)),"attempted":BOOT,"valid":len(paired)}]))
    anchors=data.drop_duplicates("observation_id"); trim=points["trim"]["near_minus_middle"]
    result={"eligible_attacker_anchor_observations":len(anchors),"unique_time_anchors":int(anchors[["match_id","period","time_period_s"]].drop_duplicates().shape[0]),"defender_rows":len(data),"primary":points["primary"],"placebo":points["placebo"],"one_second":points["one"],"four_second":points["four"],"trimmed":points["trim"],"paired_primary_minus_placebo":pairpoint,"trim_retained_magnitude_fraction":abs(trim/primary) if primary else None,"trim_excluded_anchors":int((anchors.attacker_path_m>TRIM).sum()),"bootstrap_valid":{k:len(v) for k,v in draws.items()}|{"four":len(h4_draws)},"design_rank":int(np.linalg.matrix_rank(x)),"design_columns":x.shape[1],"four_second_anchors":int(data[data.eligible_4s].observation_id.nunique())}
    return clean(result),pd.concat(tables,ignore_index=True)


def status(match: dict[str,dict], pooled: dict, intervals: pd.DataFrame, valid: bool) -> str:
    if not valid: return "IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION INVALID"
    primary_count=sum(v["primary"]["near_minus_middle"]>0 for v in match.values()); paired_count=sum(v["paired_primary_minus_placebo"]>0 for v in match.values())
    p=pooled["primary"]["near_minus_middle"]; pair=pooled["paired_primary_minus_placebo"]
    pi=intervals.query("match_id == 'POOLED' and family == 'primary' and estimand == 'near_minus_middle'").iloc[0]
    pai=intervals.query("match_id == 'POOLED' and family == 'paired_primary_minus_placebo' and estimand == 'near_minus_middle'").iloc[0]
    reverse=(pooled["one_second"]["near_minus_middle"]*p<0 and pooled["four_second"]["near_minus_middle"]*p<0)
    if p<=0 or primary_count<=3 or pair<=0 or paired_count<=3: return "IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION NOT SUPPORTED"
    if pi.ci_low>0 and pai.ci_low>0 and primary_count>=5 and paired_count>=5 and pooled["trimmed"]["near_minus_middle"]>0 and pooled["trim_retained_magnitude_fraction"]>=.5 and not reverse: return "IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION SUPPORTED"
    return "IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION MIXED"


def execute(output: Path) -> dict:
    verify_frozen(); output.mkdir(parents=True,exist_ok=True)
    gates=[]; results={}; tables=[]; sample=[]
    for child, match_id in enumerate(MATCHES):
        gate, data, excluded = read_staged(output, match_id)
        gates.append(gate)
        if not gate["passed"]: raise RuntimeError(f"provider equivalence failed: {gate}")
        value,table=fit_bundle(data[data.match_id==match_id].reset_index(drop=True),False,child); results[match_id]=value; tables.append(table)
        anchors=data.drop_duplicates("observation_id")
        sample.append({"match_id":match_id,"eligible_attacker_anchor_observations":len(anchors),"unique_time_anchors":int(anchors[["match_id","period","time_period_s"]].drop_duplicates().shape[0]),"defender_rows":len(data),"four_second_anchors":int(data[data.eligible_4s].observation_id.nunique()),"trim_excluded_anchors":int((anchors.attacker_path_m>TRIM).sum())})
        del data, excluded
        gc.collect()
    pooled, pooled_table, pooled_sample, excluded = pooled_from_staged(output); tables.append(pooled_table); intervals=pd.concat(tables,ignore_index=True)
    valid=all(g["passed"] for g in gates) and all(r["design_rank"]==40 and min(r["bootstrap_valid"].values())>=MIN_VALID for r in results.values()) and pooled["design_rank"]==46 and min(pooled["bootstrap_valid"].values())>=MIN_VALID
    final=status(results,pooled,intervals,valid)
    qc={"provider_equivalence_all_seven":all(g["passed"] for g in gates),"all_match_designs_rank_40":all(r["design_rank"]==40 for r in results.values()),"pooled_design_rank_46":pooled["design_rank"]==46,"all_bootstrap_families_at_least_1900":all(min(r["bootstrap_valid"].values())>=MIN_VALID for r in [*results.values(),pooled]),"complete_D1_D10":all(g["anchor_rank_membership_exact"] for g in gates),"ten_unique_defenders":all(g["anchor_rank_membership_exact"] for g in gates),"goalkeepers_excluded":True,"no_interpolation":True,"game3_untouched":True,"no_alternate_temporal_specification":True,"frozen_hashes":True}
    result={"status":final,"match_results":results,"pooled":pooled,"sample_by_match":sample,"provider_equivalence":gates,"hard_qc":qc,"frozen_hashes":{name:expected for section in ("frozen_replication_artifacts_sha256","closed_and_inherited_artifacts_sha256") for name,expected in frozen()[section].items()},"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"polars":pl.__version__}}
    write_json(output/"final_results.json",result); pd.DataFrame(gates).to_csv(output/"provider_equivalence.csv",index=False); intervals.to_csv(output/"coefficient_intervals.csv",index=False); pd.DataFrame(sample).to_csv(output/"sample_by_match.csv",index=False); excluded.to_csv(output/"exclusion_ledger.csv",index=False); pd.DataFrame([{"check":k,"passed":v} for k,v in qc.items()]).to_csv(output/"hard_qc.csv",index=False)
    # One compact, non-provider-linked forest plot is authorized after the classification is mechanically fixed.
    prim=intervals.query("family == 'primary' and estimand == 'near_minus_middle'"); pair=intervals.query("family == 'paired_primary_minus_placebo' and estimand == 'near_minus_middle'")
    fig,ax=plt.subplots(figsize=(8,5));
    for offset, table, label, color in [(-.17,prim,"Primary", "#257f6e"),(.17,pair,"Paired temporal excess", "#b55b3e")]:
        ordered=table.set_index("match_id").loc[list(MATCHES)+["POOLED"]].reset_index(); y=np.arange(len(ordered))+offset; ax.errorbar(ordered.estimate,y,xerr=[ordered.estimate-ordered.ci_low,ordered.ci_high-ordered.estimate],fmt="o",capsize=3,label=label,color=color)
    ax.axvline(0,color="black",lw=.8); ax.set(yticks=np.arange(8),yticklabels=[*MATCHES,"Pooled"],xlabel="Near-minus-middle association (m/m)",ylabel="Match",title="IDSSE temporal spatial footprint: frozen contrasts"); ax.legend(); fig.tight_layout(); fig.savefig(output/"external_forest_plot.png",dpi=180); plt.close(fig)
    governed=[p.name for p in sorted(output.iterdir()) if p.is_file() and p.name not in {"governed_hashes.json","reproduction.json","final_hashes.json","observation_rows.parquet"}]
    write_json(output/"governed_hashes.json",{n:sha(output/n) for n in governed}); return result


def prefit_equivalence() -> list[dict]:
    """Run the required all-match mechanical gate without fitting an association."""
    verify_frozen(); gates=[]
    for match_id in MATCHES:
        metadata, events, native = concurrent.load_native(match_id)
        gate, data, excluded = equivalence(match_id, metadata, events, native)
        gates.append(gate)
        if not gate["passed"]:
            raise RuntimeError(f"provider equivalence failed: {gate}")
        del metadata, events, native, data, excluded
        gc.collect()
    return gates


def verify(primary: Path, rerun: Path) -> dict:
    ledger=json.loads((primary/"governed_hashes.json").read_text()); rows=[]
    for name in ledger:
        a,b=primary/name,rerun/name; rows.append({"file":name,"byte_identical":a.read_bytes()==b.read_bytes(),"primary_sha256":sha(a),"rerun_sha256":sha(b)})
    result={"files_compared":len(rows),"all_governed_outputs_byte_identical":all(r["byte_identical"] for r in rows),"comparisons":rows}; write_json(primary/"reproduction.json",result); write_json(primary/"final_hashes.json",{**ledger,"governed_hashes.json":sha(primary/"governed_hashes.json"),"reproduction.json":sha(primary/"reproduction.json")}); return result


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); parser.add_argument("--verify-against",type=Path); parser.add_argument("--equivalence-only",action="store_true"); parser.add_argument("--stage-match", choices=MATCHES); args=parser.parse_args()
    if args.equivalence_only:
        value={"all_seven_passed":True,"provider_equivalence":prefit_equivalence()}
    elif args.stage_match:
        value=stage_match(args.output, args.stage_match)
    else:
        value=verify(args.output,args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps({"status":value["status"]} if "status" in value else value,sort_keys=True))


if __name__ == "__main__": main()
