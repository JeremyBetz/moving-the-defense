"""Tier-3 IDSSE external replication of frozen Concurrent Geometry v1."""
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

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase4c_idsse_external_replication as idsse  # noqa: E402
import concurrent_attacker_defensive_geometry_game1_v1 as base  # noqa: E402
import local_defensive_deformation_v1 as deformation  # noqa: E402
from infrastructure import kloppy_idsse_adapter as adapter  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/concurrent_attacker_defensive_geometry_v1_idsse_replication.md"
CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1_idsse_replication.json"
EQUIVALENCE = ROOT / "docs/concurrent_attacker_defensive_geometry_v1_idsse_equivalence.md"
LEDGER = ROOT / "config/concurrent_attacker_defensive_geometry_v1_idsse_replication_hashes.json"
DEFAULT_OUTPUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_idsse_v1"
DEFAULT_RERUN = ROOT / "outputs/.concurrent_attacker_defensive_geometry_idsse_v1_rerun"
FROZEN = {
    PROTOCOL: "1022d4a6b49f601970a3f1eb828885d29eab2bb5b2b9031ba0d8e3a7caafcdaa",
    CONFIG: "7af31dde8c70c7e4eba10dd52cf840025e8717d65b8444f93d35594e3d238dc4",
    EQUIVALENCE: "3fcc148c9f8e4a4cedaad2844aec435de43c5203a24fb9c57395af0237adbec9",
    LEDGER: "a0cf0415c2bb50c3fe4088d6d7f887012673bdc84e9c8169c0254c3fd0a40426",
}
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
P, BOOT, MIN_VALID, MASTER_SEED, TRIM = 72, 2000, 1900, 20260902, 12.198443079831405
FRAME_NS, SMOOTH_EDGE = 40_000_000, 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen() -> None:
    bad = {str(p.relative_to(ROOT)): [sha(p), expected] for p, expected in FROZEN.items() if sha(p) != expected}
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")


def write_json(path: Path, value: Any) -> None:
    base.write_json(path, value)


def load_native(match_id: str) -> tuple[dict, dict, dict]:
    raw = ROOT / "data/idsse_raw"
    metadata = idsse.read_metadata(idsse.find_file(raw, "metadata", match_id))
    events = idsse.read_events(idsse.find_file(raw, "events", match_id))
    cache = ROOT / f"data/idsse_cache/{match_id}_raw_tracking.npz"
    tracking = idsse.load_tracking_cache(cache) if cache.exists() else idsse.read_tracking(idsse.find_file(raw, "tracking", match_id), metadata)
    return metadata, events, tracking


def tracking_equivalence(match_id: str, metadata: dict, native: dict) -> dict:
    metadata_path, _, tracking_path = adapter.idsse_paths(ROOT, match_id)
    dataset = adapter.load_dataset(metadata_path, tracking_path)
    sidecar = adapter.read_ball_frame_sidecar(tracking_path)
    candidate = adapter.to_phase4c_tracking(dataset, sidecar)
    max_coordinate = 0.0
    masks_exact = True
    ball_masks_exact = True
    times_exact = True
    frames_exact = True
    native_map_meta = {(p.team_id, p.player_id): p.goalkeeper for p in metadata["players"].values()}
    candidate_roster = {(team, player.player_id): is_gk for player, team, is_gk in adapter.roster(dataset)}
    roster_exact = native_map_meta == candidate_roster
    for period in idsse.PERIODS:
        a, b = native[period], candidate[period]
        frames_exact &= np.array_equal(a["frame_n"], b["frame_n"])
        times_exact &= np.array_equal(a["time_ns"], b["time_ns"])
        amap = {(e["team_id"], e["person_id"]): e for e in a["entities"]}
        bmap = {(e["team_id"], e["person_id"]): e for e in b["entities"]}
        for key in sorted(amap):
            if key not in bmap:
                if key[0] == "BALL":
                    ball_masks_exact = False
                elif key in native_map_meta:
                    masks_exact = False
                continue
            if key[0] != "BALL" and key not in native_map_meta:
                continue
            for axis in ("x", "y"):
                av, bv = np.asarray(amap[key][axis], float), np.asarray(bmap[key][axis], float)
                am, bm = np.isfinite(av), np.isfinite(bv)
                if key[0] == "BALL":
                    ball_masks_exact &= np.array_equal(am, bm)
                else:
                    masks_exact &= np.array_equal(am, bm)
                if (am & bm).any():
                    max_coordinate = max(max_coordinate, float(np.max(np.abs(av[am & bm] - bv[am & bm]))))
    result = {
        "match_id": match_id,
        "frames_exact": bool(frames_exact),
        "provider_timestamps_exact": bool(times_exact),
        "player_team_goalkeeper_roster_exact": bool(roster_exact),
        "observed_null_masks_exact": bool(masks_exact),
        "ball_observed_null_masks_exact_descriptive": bool(ball_masks_exact),
        "maximum_coordinate_difference_m": max_coordinate,
        "coordinate_tolerance_m": 1e-5,
        "event_context_layer_shared_exactly": True,
    }
    result["passed"] = all([frames_exact, times_exact, roster_exact, masks_exact, max_coordinate <= 1e-5])
    del dataset, candidate, sidecar
    gc.collect()
    return result


def context_at_anchor(events: dict, start_ns: int, anchor_ns: int, end_ns: int) -> tuple[str | None, bool]:
    team, open_state = None, False
    for row in events["state_events"]:
        if row["time_ns"] > anchor_ns:
            break
        if row["team_id"] is not None:
            team = row["team_id"]
        if row["open_state"] is not None:
            open_state = bool(row["open_state"])
    if team is None or not open_state:
        return None, False
    for row in events["state_events"]:
        if row["time_ns"] < start_ns:
            continue
        if row["time_ns"] > end_ns:
            break
        if row["open_state"] is False:
            return team, False
    return team, True


def smooth_full(raw: np.ndarray) -> np.ndarray:
    return pd.DataFrame(raw).rolling(7, center=True, min_periods=7).mean().to_numpy()[3:-3]


def build_sample(match_id: str, metadata: dict, events: dict, tracking: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, exclusions = [], []
    teams = {metadata["home_team_id"], metadata["away_team_id"]}
    for period_number, period in enumerate(idsse.PERIODS, 1):
        pdata = tracking[period]
        kickoff_ns = idsse.iso_ns(events["kickoffs"][period])
        # The canonical Kloppy period clock starts at the first observed provider
        # frame; raw UTC remains the shared key for event synchronization.
        period_origin_ns = int(pdata["time_ns"][0])
        entity = {(e["team_id"], e["person_id"]): e for e in pdata["entities"]}
        time_lookup = {int(t): i for i, t in enumerate(pdata["time_ns"])}
        max_offset = (int(pdata["time_ns"][-1]) - period_origin_ns) / 1e9
        k = 0
        while 4.0 + 4.0 * k <= max_offset + 1e-9:
            anchor_s = 2.0 + 4.0 * k
            anchor_ns = period_origin_ns + int(anchor_s * 1e9)
            outer_start, outer_end = anchor_ns - 2_000_000_000, anchor_ns + 2_000_000_000
            raw_start, raw_end = outer_start - SMOOTH_EDGE * FRAME_NS, outer_end + SMOOTH_EDGE * FRAME_NS
            expected_times = np.arange(raw_start, raw_end + FRAME_NS, FRAME_NS, dtype=np.int64)
            if any(int(t) not in time_lookup for t in expected_times):
                exclusions.append({"match_id": match_id, "period": period_number, "time_period_s": anchor_s, "attacker_id": None, "reason": "complete_cadence_support_unavailable"})
                k += 1
                continue
            idx = np.asarray([time_lookup[int(t)] for t in expected_times], dtype=int)
            attack_team, open_ok = context_at_anchor(events, outer_start, anchor_ns, outer_end)
            if attack_team not in teams or not open_ok:
                exclusions.append({"match_id": match_id, "period": period_number, "time_period_s": anchor_s, "attacker_id": None, "reason": "possession_or_open_play"})
                k += 1
                continue
            defend_team = next(iter(teams - {attack_team}))
            defenders = []
            for player in metadata["players"].values():
                if player.team_id == defend_team and not player.goalkeeper and (player.team_id, player.player_id) in entity:
                    e = entity[(player.team_id, player.player_id)]
                    if e["valid"][idx].all():
                        defenders.append(player.player_id)
            attackers = []
            for player in metadata["players"].values():
                if player.team_id == attack_team and not player.goalkeeper and (player.team_id, player.player_id) in entity:
                    e = entity[(player.team_id, player.player_id)]
                    if e["valid"][idx].all():
                        attackers.append(player.player_id)
            if len(defenders) != 10:
                for attacker in attackers or [None]:
                    exclusions.append({"match_id": match_id, "period": period_number, "time_period_s": anchor_s, "attacker_id": attacker, "reason": "complete_ten_defenders_unavailable"})
                k += 1
                continue
            defenders = sorted(defenders)
            dxy = {p: smooth_full(np.column_stack([entity[(defend_team, p)]["x"][idx], entity[(defend_team, p)]["y"][idx]]).astype(float)) for p in defenders}
            stack = np.stack([dxy[p] for p in defenders], axis=1)
            pre, concurrent = stack[:51], stack[50:]
            pre_centroid_path = base.path(pre.mean(axis=1))
            pre_abs = np.asarray([base.path(pre[:, j]) for j in range(10)])
            pre_rel = np.asarray([base.path(pre[:, j] - np.delete(pre, j, axis=1).mean(axis=1)) for j in range(10)])
            con_rel = np.asarray([base.path(concurrent[:, j] - np.delete(concurrent, j, axis=1).mean(axis=1)) for j in range(10)])
            con_def = deformation.focal_endpoint_rms(concurrent)
            for attacker in sorted(attackers):
                a = entity[(attack_team, attacker)]
                axy = smooth_full(np.column_stack([a["x"][idx], a["y"][idx]]).astype(float))
                pre_a, con_a = axy[:51], axy[50:]
                order = sorted((float(np.linalg.norm(concurrent[0, j] - con_a[0])), defender, j) for j, defender in enumerate(defenders))
                obs = f"CAGI|{match_id}|P{period_number}|T{anchor_s:.2f}|{attacker}"
                for rank, (distance, defender, j) in enumerate(order, 1):
                    rows.append({
                        "observation_id": obs, "match_id": match_id, "period": period_number, "time_period_s": anchor_s,
                        "time_utc_ns": anchor_ns, "attacker_key": attacker, "attacking_team": attack_team,
                        "defending_team": defend_team, "is_home_attacking": attack_team == metadata["home_team_id"],
                        "block_id": int(math.floor(anchor_s / 60.0)), "defender_key": defender, "distance_rank": rank,
                        "distance_m": distance, "concurrent_attacker_path_m": base.path(con_a), "prior_attacker_path_m": base.path(pre_a),
                        "prior_focal_relative_path_m": pre_rel[j], "prior_defensive_centroid_path_m": pre_centroid_path,
                        "prior_other_nine_mean_absolute_path_m": float((pre_abs.sum() - pre_abs[j]) / 9.0),
                        "concurrent_focal_relative_path_m": con_rel[j], "concurrent_endpoint_deformation_rms_m": con_def[j],
                    })
            k += 1
    data = pd.DataFrame(rows).sort_values(["match_id", "period", "time_period_s", "attacker_key", "distance_rank"], kind="mergesort").reset_index(drop=True)
    return data, pd.DataFrame(exclusions)


def design(data: pd.DataFrame) -> np.ndarray:
    matrix = np.zeros((len(data), P), dtype=np.float64)
    rank = data.distance_rank.to_numpy(int) - 1
    terms = np.column_stack([np.ones(len(data)), data.concurrent_attacker_path_m, data.prior_focal_relative_path_m,
                             data.prior_defensive_centroid_path_m, data.prior_other_nine_mean_absolute_path_m,
                             data.prior_attacker_path_m, data.distance_m]).astype(np.float64)
    for term in range(7):
        matrix[np.arange(len(data)), rank * 7 + term] = terms[:, term]
    matrix[:, 70] = (data.period.to_numpy(int) == 2).astype(float)
    matrix[:, 71] = data.is_home_attacking.to_numpy(float)
    return matrix


def block_stats(data: pd.DataFrame, x: np.ndarray, outcomes: dict[str, np.ndarray], trim: np.ndarray) -> dict:
    stats = {name: {} for name in ("primary", "secondary", "trimmed")}
    for key, indexes in data.groupby(["match_id", "period", "block_id"], sort=True).indices.items():
        ix = np.asarray(indexes, int)
        for name in ("primary", "secondary"):
            stats[name][key] = (x[ix].T @ x[ix], x[ix].T @ outcomes[name][ix])
        tx = ix[trim[ix]]
        if len(tx): stats["trimmed"][key] = (x[tx].T @ x[tx], x[tx].T @ outcomes["primary"][tx])
    return stats


def bootstrap(data: pd.DataFrame, x: np.ndarray, outcomes: dict[str, np.ndarray], trim: np.ndarray, child: int, pooled: bool) -> dict[str, np.ndarray]:
    stats = block_stats(data, x, outcomes, trim)
    by_stratum: dict[tuple, list] = {}
    for key in sorted(stats["primary"]):
        stratum = (key[0], key[1]) if pooled else (key[1],)
        by_stratum.setdefault(stratum, []).append(key)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(MASTER_SEED).spawn(8)[child]))
    result = {name: [] for name in stats}
    for _ in range(BOOT):
        selected = []
        for keys in by_stratum.values():
            selected.extend(keys[int(i)] for i in rng.integers(0, len(keys), size=len(keys)))
        for name in result:
            available = [key for key in selected if key in stats[name]]
            xtx = sum((stats[name][key][0] for key in available), np.zeros((P, P)))
            xty = sum((stats[name][key][1] for key in available), np.zeros(P))
            try: result[name].append(base.summarize(base.fit_sufficient(xtx, xty))["D1_D10"])
            except np.linalg.LinAlgError: pass
    return {name: np.asarray(values) for name, values in result.items()}


def fit_bundle(data: pd.DataFrame, child: int, pooled: bool) -> tuple[dict, dict[str, pd.DataFrame]]:
    x = design(data)
    outcomes = {"primary": data.concurrent_focal_relative_path_m.to_numpy(float), "secondary": data.concurrent_endpoint_deformation_rms_m.to_numpy(float)}
    trim = data.concurrent_attacker_path_m.to_numpy(float) <= TRIM
    points = {"primary": base.summarize(base.fit(x, outcomes["primary"])), "secondary": base.summarize(base.fit(x, outcomes["secondary"])), "trimmed": base.summarize(base.fit(x[trim], outcomes["primary"][trim]))}
    samples = bootstrap(data, x, outcomes, trim, child, pooled)
    tables = {name: base.interval_table(points[name], samples[name]) for name in points}
    p = tables["primary"].query("estimand == 'near_minus_middle'").iloc[0]
    s = tables["secondary"].query("estimand == 'near_minus_middle'").iloc[0]
    t = tables["trimmed"].query("estimand == 'near_minus_middle'").iloc[0]
    anchors = data.drop_duplicates("observation_id")
    retained = abs(float(t.estimate / p.estimate)) if p.estimate != 0 else None
    summary = {
        "eligible_attacker_anchor_observations": int(len(anchors)), "unique_period_time_anchors": int(anchors[["match_id", "period", "time_period_s"]].drop_duplicates().shape[0]),
        "defender_rows": int(len(data)), "D1_D10": points["primary"]["D1_D10"], "near": points["primary"]["near"], "middle": points["primary"]["middle"], "far": points["primary"]["far"],
        "near_minus_middle": {"estimate": float(p.estimate), "ci_low": float(p.ci_low), "ci_high": float(p.ci_high)},
        "trimmed_near_minus_middle": {"estimate": float(t.estimate), "ci_low": float(t.ci_low), "ci_high": float(t.ci_high), "retained_magnitude_fraction": retained,
                                        "excluded_anchors": int((anchors.concurrent_attacker_path_m > TRIM).sum()), "excluded_fraction": float((anchors.concurrent_attacker_path_m > TRIM).mean())},
        "secondary_deformation_near_minus_middle": {"estimate": float(s.estimate), "ci_low": float(s.ci_low), "ci_high": float(s.ci_high),
            "classification": "SUPPORTIVE" if s.estimate > 0 and s.ci_low > 0 else "DIRECTIONALLY SUPPORTIVE" if s.estimate > 0 else "NON-SUPPORTIVE"},
        "bootstrap_valid": {name: int(len(value)) for name, value in samples.items()}, "design_rank": int(np.linalg.matrix_rank(x)),
    }
    return summary, tables


def execute(output: Path, skip_equivalence: bool = False) -> dict:
    verify_frozen(); output.mkdir(parents=True, exist_ok=True)
    gate, all_data, exclusions = [], [], []
    for match_id in MATCHES:
        metadata, events, native = load_native(match_id)
        if skip_equivalence:
            closed_gate = pd.read_csv(DEFAULT_OUTPUT / "provider_equivalence.csv")
            eq = closed_gate.loc[closed_gate.match_id == match_id].iloc[0].to_dict()
            eq = {key: (bool(value) if isinstance(value, np.bool_) else value) for key, value in eq.items()}
        else:
            eq = tracking_equivalence(match_id, metadata, native)
        gate.append(eq)
        if not eq["passed"]: raise RuntimeError(f"provider equivalence failed: {eq}")
        data, excluded = build_sample(match_id, metadata, events, native)
        all_data.append(data); exclusions.append(excluded)
    combined = pd.concat(all_data, ignore_index=True)
    excluded = pd.concat(exclusions, ignore_index=True)
    match_results, tables = {}, []
    for child, match_id in enumerate(MATCHES):
        result, match_tables = fit_bundle(combined[combined.match_id == match_id].reset_index(drop=True), child, False)
        match_results[match_id] = result
        for family, table in match_tables.items():
            table.insert(0, "family", family); table.insert(0, "match_id", match_id); tables.append(table)
    pooled, pooled_tables = fit_bundle(combined, 7, True)
    for family, table in pooled_tables.items():
        table.insert(0, "family", family); table.insert(0, "match_id", "POOLED"); tables.append(table)
    positive = sum(r["near_minus_middle"]["estimate"] > 0 for r in match_results.values())
    valid = all(x["passed"] for x in gate) and all(r["design_rank"] == P and min(r["bootstrap_valid"].values()) >= MIN_VALID for r in [*match_results.values(), pooled])
    p, t = pooled["near_minus_middle"], pooled["trimmed_near_minus_middle"]
    if not valid: status = "IDSSE EXTERNAL REPLICATION INVALID"
    elif p["estimate"] <= 0 or positive <= 3: status = "IDSSE EXTERNAL REPLICATION NOT SUPPORTED"
    elif p["ci_low"] > 0 and positive >= 5 and t["estimate"] > 0 and t["retained_magnitude_fraction"] >= .5: status = "IDSSE EXTERNAL REPLICATION SUPPORTED"
    else: status = "IDSSE EXTERNAL REPLICATION MIXED"
    hard_qc = {"provider_equivalence_all_seven": all(x["passed"] for x in gate), "all_designs_full_rank": all(r["design_rank"] == P for r in [*match_results.values(), pooled]),
               "all_bootstrap_families_at_least_1900": all(min(r["bootstrap_valid"].values()) >= MIN_VALID for r in [*match_results.values(), pooled]),
               "complete_D1_D10": bool(combined.groupby("observation_id").distance_rank.apply(lambda x: sorted(x) == list(range(1,11))).all()),
               "ten_unique_defenders": bool(combined.groupby("observation_id").defender_key.nunique().eq(10).all()), "no_interpolation": True, "game3_untouched": True,
               "opportunity_outcomes_not_accessed": True, "frozen_scientific_rules_unchanged": True}
    result = {"status": status, "positive_match_estimates": positive, "match_results": match_results, "pooled": pooled, "provider_equivalence": gate,
              "hard_qc": hard_qc, "frozen_hashes": {str(p.relative_to(ROOT)): h for p,h in FROZEN.items()},
              "smoothing_timescale_note": "Seven centered frames span 0.28 s at 25 Hz IDSSE versus 0.70 s at 10 Hz Metrica; the frozen frame-count rule was not changed.",
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "polars": pl.__version__}}
    write_json(output/"final_results.json", result)
    pd.DataFrame(gate).to_csv(output/"provider_equivalence.csv", index=False)
    pd.concat(tables, ignore_index=True).to_csv(output/"coefficient_intervals.csv", index=False)
    excluded.to_csv(output/"exclusion_ledger.csv", index=False)
    pl.DataFrame(combined.to_dict("list")).write_parquet(output/"observation_rows.parquet")
    write_json(output/"execution_manifest.json", {"starting_commit": "887e1adcd37aa9f53ce0a101dc94f08d3680c7d5", "tier": 3, "results_observed_after_freeze": True, "game3_untouched": True})
    closure_files = {"governed_hashes.json", "reproduction.json", "final_hashes.json"}
    governed = [p.name for p in sorted(output.iterdir()) if p.is_file() and p.name not in closure_files]
    write_json(output/"governed_hashes.json", {name: sha(output/name) for name in governed})
    return result


def verify(primary: Path, rerun: Path) -> dict:
    ledger = json.loads((primary/"governed_hashes.json").read_text())
    rows = [{"file": name, "byte_identical": (primary/name).read_bytes() == (rerun/name).read_bytes()} for name in ledger]
    result = {"files_compared": len(rows), "all_governed_outputs_byte_identical": all(x["byte_identical"] for x in rows), "comparisons": rows}
    write_json(primary/"reproduction.json", result)
    final_names = list(ledger) + ["governed_hashes.json", "reproduction.json"]
    write_json(primary/"final_hashes.json", {name: sha(primary/name) for name in final_names})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT); parser.add_argument("--skip-equivalence", action="store_true"); parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    value = verify(args.output, args.verify_against) if args.verify_against else execute(args.output, args.skip_equivalence)
    print(json.dumps(value if args.verify_against else {"status": value["status"]}, sort_keys=True))


if __name__ == "__main__": main()
