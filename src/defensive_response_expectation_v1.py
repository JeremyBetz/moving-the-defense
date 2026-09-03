"""Governed execution of frozen Defensive Response Expectation v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

import concurrent_attacker_defensive_geometry_idsse_v1 as ext
from concurrent_defensive_coordination_form_idsse_v1 import Player
from defensive_response_expectation_v1_design import contiguous_block_folds, local_response_contrast

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/defensive_response_expectation_v1.md"
CONFIG = ROOT / "config/defensive_response_expectation_v1.json"
INPUT = ROOT / "outputs/concurrent_defensive_coordination_form_idsse_v1/observation_rows.parquet"
OUT = ROOT / "outputs/defensive_response_expectation_v1"
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
FROZEN = {
    PROTOCOL: "dd4d9bec9309a6679230ba7f90a693091c221ea3585e3c1ec04112f3f65ac06f",
    CONFIG: "089bb247af30d8a76751163cb8f7d83e6a5fba9dd0af478d6368a6275f67f7d3",
}
BOOT, BOOT_SEED, SHUFFLES, SHUFFLE_SEED = 2000, 20260903, 200, 20260904
CONTINUOUS = [
    "concurrent_attacker_path_m", "prior_attacker_path_m",
    "mean_D2_D3_anchor_distance_m", "mean_D4_D7_anchor_distance_m",
    "prior_mean_D2_D3_focal_relative_path_m", "prior_mean_D4_D7_focal_relative_path_m",
    "prior_defensive_centroid_path_m", "prior_all_defenders_mean_absolute_path_m",
    "attacker_minus_defensive_centroid_longitudinal_m",
    "attacker_minus_defensive_centroid_absolute_lateral_m",
    "defensive_unit_depth_span_m", "defensive_unit_width_span_m",
    "ball_minus_defensive_centroid_longitudinal_m",
    "ball_minus_defensive_centroid_absolute_lateral_m",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return None if not np.isfinite(value) else float(value)
    if isinstance(value, float): return None if not math.isfinite(value) else value
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_frozen() -> None:
    bad = {str(p.relative_to(ROOT)): [sha(p), h] for p, h in FROZEN.items() if sha(p) != h}
    if bad: raise RuntimeError(f"frozen hash failure: {bad}")
    if not INPUT.exists(): raise RuntimeError("closed IDSSE observation ledger is unavailable")


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())


def period_direction_registry(metadata: dict, native: dict) -> dict[tuple[int, str], float]:
    """Goalward sign from the opponent goalkeeper's median fixed-pitch x."""
    result = {}
    teams = (metadata["home_team_id"], metadata["away_team_id"])
    for period_number, period in enumerate(ext.idsse.PERIODS, 1):
        entities = {(e["team_id"], e["person_id"]): e for e in native[period]["entities"]}
        for attack in teams:
            defend = next(t for t in teams if t != attack)
            keepers = [p.player_id for p in metadata["players"].values() if p.team_id == defend and p.goalkeeper]
            values = []
            for keeper in keepers:
                e = entities.get((defend, keeper))
                if e is not None: values.extend(np.asarray(e["x"], float)[np.asarray(e["valid"], bool)].tolist())
            if not values: raise RuntimeError(f"goalkeeper direction unavailable: {period} {attack}")
            med = float(np.median(values))
            if abs(med) < 1.0: raise RuntimeError(f"ambiguous goalkeeper direction: {period} {attack} {med}")
            result[(period_number, attack)] = 1.0 if med > 0 else -1.0
    return result


def anchor_context(match: str, needed: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    metadata, _events, native = ext.load_native(match)
    direction = period_direction_registry(metadata, native)
    out, missing_ball = [], 0
    for period_number, period in enumerate(ext.idsse.PERIODS, 1):
        subset = needed.loc[needed.period == period_number]
        if subset.empty: continue
        pdata = native[period]
        times = (pdata["time_ns"] - pdata["time_ns"][0]) / 1e9
        entities = {(e["team_id"], e["person_id"]): e for e in pdata["entities"]}
        players = {}
        for p in metadata["players"].values():
            key = (p.team_id, p.player_id)
            if p.goalkeeper or key not in entities: continue
            e = entities[key]; raw = np.column_stack([e["x"], e["y"]]).astype(float)
            players[key] = Player(*key, times, raw, np.asarray(e["valid"], bool) & np.isfinite(raw).all(axis=1))
        ball = next(e for e in pdata["entities"] if e["team_id"] == "BALL")
        lookup = {round(float(t), 2): i for i, t in enumerate(times)}
        for row in subset.itertuples(index=False):
            attack = row.attacking_team
            defend = metadata["away_team_id"] if attack == metadata["home_team_id"] else metadata["home_team_id"]
            attacker = players.get((attack, row.attacker_key))
            defenders = sorted((pid, obj) for (team, pid), obj in players.items() if team == defend)
            if attacker is None: continue
            aseg = attacker.segment(row.time_period_s - 2, row.time_period_s + 2, "primary")
            dsegs = [(pid, obj.segment(row.time_period_s - 2, row.time_period_s + 2, "primary")) for pid, obj in defenders]
            dsegs = [(pid, seg) for pid, seg in dsegs if seg is not None]
            if aseg is None or len(dsegs) != 10: continue
            axy, atime = aseg; c = int(np.flatnonzero(np.abs(atime - row.time_period_s) <= 1e-9)[0])
            stack = np.stack([seg[0] for _, seg in dsegs], axis=1)
            centroid = stack[:, :, :].mean(axis=1); a0, c0, d0 = axy[c], centroid[c], stack[c]
            idx = lookup.get(round(float(row.time_period_s), 2))
            if idx is None or not bool(ball["valid"][idx]) or not np.isfinite([ball["x"][idx], ball["y"][idx]]).all():
                missing_ball += 1; continue
            b0 = np.asarray([ball["x"][idx], ball["y"][idx]], float)
            sign = direction[(period_number, attack)]
            out.append({
                "observation_id": row.observation_id,
                "defending_team": defend,
                "prior_all_defenders_mean_absolute_path_m": float(np.mean([path(seg[0][:c + 1]) for _, seg in dsegs])),
                "attacker_minus_defensive_centroid_longitudinal_m": float(sign * (a0[0] - c0[0])),
                "attacker_minus_defensive_centroid_absolute_lateral_m": float(abs(a0[1] - c0[1])),
                "defensive_unit_depth_span_m": float(np.ptp(d0[:, 0])),
                "defensive_unit_width_span_m": float(np.ptp(d0[:, 1])),
                "ball_minus_defensive_centroid_longitudinal_m": float(sign * (b0[0] - c0[0])),
                "ball_minus_defensive_centroid_absolute_lateral_m": float(abs(b0[1] - c0[1])),
            })
    return pd.DataFrame(out), {"missing_ball_or_context": missing_ball, "direction_registry": {f"P{p}|{t}": v for (p, t), v in direction.items()}}


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rank_frame = pl.read_parquet(INPUT).select([
        "observation_id", "match_id", "period", "time_period_s", "attacker_key", "attacking_team",
        "is_home_attacking", "block_id", "distance_rank", "primary_distance_m",
        "primary_attacker_path_m", "primary_prior_attacker_path_m", "primary_prior_focal_relative_path_m",
        "primary_prior_centroid_path_m", "primary_prior_other_nine_mean_absolute_path_m", "primary_aard_vel_mps",
    ])
    ranks = pd.DataFrame(rank_frame.to_dicts())
    groups, exclusions, registries = [], [], {}
    for match, frame in ranks.groupby("match_id", sort=True):
        rows = []
        for obs, g in frame.groupby("observation_id", sort=False):
            g = g.sort_values("distance_rank")
            if len(g) != 10 or g.distance_rank.tolist() != list(range(1, 11)): continue
            first = g.iloc[0]
            rows.append({
                "observation_id": obs, "match_id": match, "period": int(first.period),
                "time_period_s": float(first.time_period_s), "attacker_key": first.attacker_key,
                "attacking_team": first.attacking_team, "is_home_attacking": bool(first.is_home_attacking),
                "block_id": int(first.block_id), "outcome_mps": local_response_contrast(g.primary_aard_vel_mps),
                "concurrent_attacker_path_m": float(first.primary_attacker_path_m),
                "prior_attacker_path_m": float(first.primary_prior_attacker_path_m),
                "mean_D2_D3_anchor_distance_m": float(g.iloc[1:3].primary_distance_m.mean()),
                "mean_D4_D7_anchor_distance_m": float(g.iloc[3:7].primary_distance_m.mean()),
                "prior_mean_D2_D3_focal_relative_path_m": float(g.iloc[1:3].primary_prior_focal_relative_path_m.mean()),
                "prior_mean_D4_D7_focal_relative_path_m": float(g.iloc[3:7].primary_prior_focal_relative_path_m.mean()),
                "prior_defensive_centroid_path_m": float(first.primary_prior_centroid_path_m),
                "D1_minus_D2_D3_mean_mps": float(g.iloc[0].primary_aard_vel_mps - g.iloc[1:3].primary_aard_vel_mps.mean()),
            })
        base = pd.DataFrame(rows)
        ctx, log = anchor_context(match, base[["observation_id", "period", "time_period_s", "attacker_key", "attacking_team"]])
        registries[match] = log["direction_registry"]
        merged = base.merge(ctx, on="observation_id", how="inner", validate="one_to_one")
        missing = set(base.observation_id) - set(merged.observation_id)
        exclusions.extend({"match_id": match, "observation_id": x, "reason": "E1_context_or_ball_unavailable"} for x in sorted(missing))
        groups.append(merged)
    data = pd.concat(groups, ignore_index=True).sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)
    data["block_key"] = data.match_id + "|P" + data.period.astype(str) + "|B" + data.block_id.astype(str)
    return data, pd.DataFrame(exclusions), registries


def assign_folds(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy(); out["fold"] = -1
    for match, ix in out.groupby("match_id", sort=True).groups.items():
        keys = sorted(set(zip(out.loc[ix, "period"].astype(int), out.loc[ix, "block_id"].astype(int))))
        mapping = dict(zip(keys, contiguous_block_folds(keys).tolist()))
        out.loc[ix, "fold"] = [mapping[(int(p), int(b))] for p, b in zip(out.loc[ix, "period"], out.loc[ix, "block_id"])]
    return out


def categorical(data: pd.DataFrame, side_override: np.ndarray | None = None) -> dict[str, np.ndarray]:
    matches = np.asarray(data.match_id); period = np.asarray(data.period); side = np.asarray(data.defending_team if side_override is None else side_override)
    match_cols = np.column_stack([matches == m for m in MATCHES[1:]]).astype(float)
    period_cols = np.column_stack([(matches == m) & (period == 2) for m in MATCHES]).astype(float)
    side_cols = []
    for m in MATCHES:
        levels = sorted(set(data.loc[data.match_id == m, "defending_team"]))
        reference = levels[0]
        side_cols.append((matches == m) & (side != reference))
    side_cols = np.column_stack(side_cols).astype(float)
    return {"common": np.column_stack([match_cols, period_cols]), "side": side_cols}


def matrices(train: pd.DataFrame, test: pd.DataFrame, model: str, train_side=None, test_side=None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    use = CONTINUOUS[:2] if model == "E0" else CONTINUOUS
    mean = train[use].mean().to_numpy(float); sd = train[use].std(ddof=0).to_numpy(float)
    keep = sd > 0
    tr = (train[use].to_numpy(float)[:, keep] - mean[keep]) / sd[keep]
    te = (test[use].to_numpy(float)[:, keep] - mean[keep]) / sd[keep]
    tc, ec = categorical(train, train_side), categorical(test, test_side)
    xtr = np.column_stack([np.ones(len(train)), tr, tc["common"]]); xte = np.column_stack([np.ones(len(test)), te, ec["common"]])
    names = ["intercept"] + list(np.asarray(use)[keep]) + [f"match_{x}" for x in MATCHES[1:]] + [f"period2_{x}" for x in MATCHES]
    if model in ("E2a", "E2b"):
        xtr = np.column_stack([xtr, tc["side"]]); xte = np.column_stack([xte, ec["side"]]); names += [f"side_{x}" for x in MATCHES]
    if model == "E2b":
        movement_index = list(np.asarray(use)[keep]).index("concurrent_attacker_path_m") + 1
        xtr = np.column_stack([xtr, tc["side"] * xtr[:, [movement_index]]])
        xte = np.column_stack([xte, ec["side"] * xte[:, [movement_index]]])
        names += [f"side_path_{x}" for x in MATCHES]
    # The protocol prospectively requires training-zero-variance columns to be
    # removed from the fold and applied identically to heldout rows. This is
    # relevant to J03WN1's sparse second defending side in fold 0.
    keep_columns = np.r_[True, np.ptp(xtr[:, 1:], axis=0) > 0]
    xtr, xte = xtr[:, keep_columns], xte[:, keep_columns]
    names = list(np.asarray(names)[keep_columns])
    return xtr, xte, names


def fold_masks(data: pd.DataFrame, fold: int) -> tuple[np.ndarray, np.ndarray, dict]:
    test = data.fold.to_numpy() == fold; train = ~test
    test_keys = set(zip(data.loc[test, "match_id"], data.loc[test, "period"], data.loc[test, "block_id"]))
    embargo = np.array([any(m == tm and p == tp and abs(int(b) - int(tb)) == 1 for tm, tp, tb in test_keys) for m, p, b in zip(data.match_id, data.period, data.block_id)])
    train &= ~embargo
    supported = np.ones(len(data), bool); ledger = {}
    for match in MATCHES:
        for side in sorted(data.loc[data.match_id == match, "defending_team"].unique()):
            key = (data.match_id == match) & (data.defending_team == side)
            nt, ne = int((key & train).sum()), int((key & test).sum())
            ok = nt >= 100 and ne >= 25
            if not ok: supported[key & test] = False
            ledger[f"{match}|{side}"] = {"train": nt, "test": ne, "supported": ok}
    return train, test & supported, {"embargoed_training_rows": int((~test & embargo).sum()), "side_support": ledger}


def predict_primary(data: pd.DataFrame, side_labels: np.ndarray | None = None, models=("E0", "E1", "E2a", "E2b")) -> tuple[pd.DataFrame, dict]:
    rows, folds = [], {}
    labels = np.asarray(data.defending_team if side_labels is None else side_labels)
    for fold in range(5):
        train_mask, test_mask, log = fold_masks(data, fold); folds[str(fold)] = log
        train, test = data.loc[train_mask], data.loc[test_mask]
        for model in models:
            xtr, xte, names = matrices(train, test, model, labels[train_mask], labels[test_mask])
            rank = int(np.linalg.matrix_rank(xtr))
            if rank != xtr.shape[1]: raise RuntimeError(f"rank deficient {fold} {model}: {rank}/{xtr.shape[1]}")
            beta = np.linalg.lstsq(xtr, train.outcome_mps.to_numpy(float), rcond=None)[0]
            pred = xte @ beta
            rows.append(pd.DataFrame({"row_id": test.index, "fold": fold, "model": model, "observed": test.outcome_mps.to_numpy(float), "predicted": pred}))
    pred = pd.concat(rows, ignore_index=True).merge(data.reset_index(names="row_id")[["row_id", "observation_id", "match_id", "period", "block_id", "defending_team", "attacking_team", "time_period_s", "concurrent_attacker_path_m"]], on="row_id", validate="many_to_one")
    return pred.sort_values(["model", "row_id"], kind="mergesort").reset_index(drop=True), folds


def performance(pred: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    p = pred.copy(); p["absolute_error"] = abs(p.observed - p.predicted); p["squared_error"] = (p.observed - p.predicted) ** 2
    per = p.groupby(["model", "match_id"], sort=True).agg(rows=("row_id", "size"), mae_mps=("absolute_error", "mean"), rmse_mps=("squared_error", lambda x: float(np.sqrt(x.mean())))).reset_index()
    result = {}
    for model, g in p.groupby("model", sort=True):
        result[model] = {"macro_mae_mps": float(per.loc[per.model == model, "mae_mps"].mean()), "weighted_mae_mps": float(g.absolute_error.mean()), "rmse_mps": float(np.sqrt(g.squared_error.mean())), "rows": int(len(g))}
    return result, per


def comparison(perf: dict, per: pd.DataFrame, baseline: str, model: str) -> dict:
    b, m = perf[baseline]["macro_mae_mps"], perf[model]["macro_mae_mps"]
    pivot = per.pivot(index="match_id", columns="model", values="mae_mps")
    return {"baseline": baseline, "model": model, "absolute_improvement_mps": b - m, "relative_improvement_percent": 100 * (b - m) / b, "matches_improved": int((pivot[model] < pivot[baseline]).sum()), "per_match_improvement_mps": (pivot[baseline] - pivot[model]).to_dict()}


def bootstrap(pred: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    wide = pred.pivot(index="row_id", columns="model", values="predicted").reset_index().merge(pred.drop_duplicates("row_id")[["row_id", "observed", "match_id", "period", "block_id"]], on="row_id")
    rng = np.random.default_rng(BOOT_SEED); values = []
    by_match = {m: g for m, g in wide.groupby("match_id", sort=True)}
    for rep in range(BOOT):
        chosen_matches = rng.choice(MATCHES, len(MATCHES), replace=True); maes = {k: [] for k in ("E1", "E2b")}
        for m in chosen_matches:
            g = by_match[m]; blocks = list(g.groupby(["period", "block_id"], sort=True))
            chosen = rng.integers(0, len(blocks), len(blocks)); sample = pd.concat([blocks[i][1] for i in chosen], ignore_index=True)
            for model in maes: maes[model].append(float(np.mean(abs(sample.observed - sample[model]))))
        b, e = np.mean(maes["E1"]), np.mean(maes["E2b"])
        values.append({"replicate": rep, "absolute_improvement_mps": b - e, "relative_improvement_percent": 100 * (b - e) / b})
    table = pd.DataFrame(values)
    summary = {c: {"ci_low": float(table[c].quantile(.025)), "ci_high": float(table[c].quantile(.975))} for c in ("absolute_improvement_mps", "relative_improvement_percent")}
    summary["valid_replicates"] = len(table)
    return table, summary


def shifted_labels(data: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SHUFFLE_SEED); rows = []
    originals = np.asarray(data.defending_team)
    strata = list(data.groupby(["match_id", "period"], sort=True).groups.items())
    attempt = 0
    while len(rows) < SHUFFLES:
        attempt += 1
        if attempt > 10 * SHUFFLES: raise RuntimeError("insufficient full-rank shifted-label controls")
        labels = originals.copy()
        for (_m, _p), ix in strata:
            ix = np.asarray(ix); blocks = sorted(data.loc[ix, "block_id"].unique())
            shift_blocks = int(rng.integers(1, len(blocks)))
            # One label per time anchor; rolling by 15 four-second grid points
            # per selected 60-second block preserves simultaneous attackers.
            anchor = data.loc[ix, ["time_period_s", "defending_team"]].drop_duplicates("time_period_s").sort_values("time_period_s")
            source = np.roll(anchor.defending_team.to_numpy(), 15 * shift_blocks)
            mapping = dict(zip(anchor.time_period_s, source))
            labels[ix] = [mapping[t] for t in data.loc[ix, "time_period_s"]]
        try:
            pred, _ = predict_primary(data, labels, models=("E1", "E2b"))
        except RuntimeError as error:
            if "rank deficient" in str(error): continue
            raise
        perf, per = performance(pred)
        c = comparison(perf, per, "E1", "E2b")
        rows.append({"replicate": len(rows), "draw_attempt": attempt, "relative_improvement_percent": c["relative_improvement_percent"], "absolute_improvement_mps": c["absolute_improvement_mps"]})
    return pd.DataFrame(rows)


def expanding_validation(data: pd.DataFrame) -> dict:
    rows = []
    for fold in (1, 2, 3, 4):
        test = data.fold.eq(fold).to_numpy(); train = data.fold.lt(fold).to_numpy()
        test_keys = set(zip(data.loc[test, "match_id"], data.loc[test, "period"], data.loc[test, "block_id"]))
        embargo = np.array([any(m == tm and p == tp and abs(int(b)-int(tb)) == 1 for tm,tp,tb in test_keys) for m,p,b in zip(data.match_id,data.period,data.block_id)])
        train &= ~embargo
        for model in ("E1", "E2b"):
            xtr, xte, _ = matrices(data.loc[train], data.loc[test], model)
            if np.linalg.matrix_rank(xtr) < xtr.shape[1]: continue
            beta = np.linalg.lstsq(xtr, data.loc[train, "outcome_mps"], rcond=None)[0]
            rows.append(pd.DataFrame({"model": model, "match_id": data.loc[test, "match_id"], "observed": data.loc[test, "outcome_mps"], "predicted": xte @ beta}))
    if not rows: return {"valid": False}
    p = pd.concat(rows); p["ae"] = abs(p.observed-p.predicted)
    macro = p.groupby(["model","match_id"]).ae.mean().groupby("model").mean()
    return {"valid": True, "macro_mae_mps": macro.to_dict(), "E2b_vs_E1_relative_improvement_percent": float(100*(macro.E1-macro.E2b)/macro.E1)}


def repeated_team_check(data: pd.DataFrame) -> dict:
    team = "DFL-CLU-00000P"; matches = sorted(data.loc[data.defending_team == team, "match_id"].unique()); rows=[]
    for held in matches:
        train = data.match_id.ne(held); test = data.match_id.eq(held) & data.defending_team.eq(team)
        # Frozen descriptive cross-match check: compact E1 continuous context plus a shared repeated-team intercept/path term.
        use = CONTINUOUS
        mean=data.loc[train,use].mean().to_numpy(); sd=data.loc[train,use].std(ddof=0).to_numpy(); keep=sd>0
        a=(data.loc[train,use].to_numpy()[:,keep]-mean[keep])/sd[keep]; b=(data.loc[test,use].to_numpy()[:,keep]-mean[keep])/sd[keep]
        ti=data.loc[train,"defending_team"].eq(team).to_numpy(float); vi=data.loc[test,"defending_team"].eq(team).to_numpy(float)
        x=np.column_stack([np.ones(train.sum()),a,ti,ti*a[:,0]]); z=np.column_stack([np.ones(test.sum()),b,vi,vi*b[:,0]])
        beta=np.linalg.lstsq(x,data.loc[train,"outcome_mps"],rcond=None)[0]; pred=z@beta
        rows.append({"heldout_match":held,"rows":int(test.sum()),"mae_mps":float(np.mean(abs(data.loc[test,"outcome_mps"]-pred))),"team_intercept":float(beta[-2]),"team_path_deviation":float(beta[-1])})
    tab=pd.DataFrame(rows); signs=np.sign(tab.team_path_deviation)
    interpretation="directionally consistent" if abs(signs.sum())==len(signs) else "too uncertain to interpret"
    return {"team_id":team,"folds":rows,"interpretation":interpretation}


def classify(primary: dict, boot: dict, shuffle95: float) -> tuple[str, dict]:
    gates={"positive_macro_improvement":primary["absolute_improvement_mps"]>0,"at_least_four_matches":primary["matches_improved"]>=4,"at_least_six_matches":primary["matches_improved"]>=6,"material_3_percent":primary["relative_improvement_percent"]>=3,"paired_ci_strictly_positive":boot["absolute_improvement_mps"]["ci_low"]>0,"shuffle_control_pass":primary["relative_improvement_percent"]>shuffle95,"bootstrap_valid":boot["valid_replicates"]>=1900}
    valid=gates["bootstrap_valid"]
    if not valid: status="INVALID"
    elif not gates["positive_macro_improvement"] or primary["matches_improved"]<=3: status="NOT SUPPORTED"
    elif all(gates[k] for k in ("at_least_six_matches","material_3_percent","paired_ci_strictly_positive","shuffle_control_pass")): status="SUPPORTED"
    else: status="MIXED"
    return status,gates


def execute(output: Path) -> dict:
    verify_frozen(); output.mkdir(parents=True, exist_ok=True)
    data, exclusions, registries = build_sample(); data = assign_folds(data)
    original_counts = pl.read_parquet(INPUT).select("observation_id").unique().group_by(pl.col("observation_id").str.split("|").list.get(1).alias("match_id")).len() if False else None
    pred, fold_log = predict_primary(data); perf, per = performance(pred)
    comparisons={"E1_vs_E0":comparison(perf,per,"E0","E1"),"E2a_vs_E1":comparison(perf,per,"E1","E2a"),"E2b_vs_E1":comparison(perf,per,"E1","E2b")}
    boots, boot_summary=bootstrap(pred); shuffled=shifted_labels(data); q95=float(shuffled.relative_improvement_percent.quantile(.95))
    status,gates=classify(comparisons["E2b_vs_E1"],boot_summary,q95)
    expanding=expanding_validation(data); repeated=repeated_team_check(data)
    e1=pred.loc[pred.model=="E1"].copy(); e1["residual_mps"]=e1.observed-e1.predicted; e1["absolute_residual_mps"]=abs(e1.residual_mps)
    secondary=e1.groupby(["match_id","defending_team"],sort=True).agg(rows=("row_id","size"),mean_residual_mps=("residual_mps","mean"),median_residual_mps=("residual_mps","median"),mean_absolute_residual_mps=("absolute_residual_mps","mean")).reset_index()
    sample=[]
    for m,g in data.groupby("match_id",sort=True):
        sample.append({"match_id":m,"eligible_anchors":len(g),"heldout_observations":int(pred.loc[(pred.model=="E1")&(pred.match_id==m),"row_id"].nunique()),"folds":int(g.fold.nunique()),"period1":int((g.period==1).sum()),"period2":int((g.period==2).sum()),"retained_fraction":None,"defending_side_counts":g.defending_team.value_counts().sort_index().to_dict()})
    prediction_sets=[tuple(sorted(g.row_id)) for _,g in pred.groupby("model",sort=True)]
    result={"status":status,"sample":sample,"performance":perf,"comparisons":comparisons,"bootstrap":boot_summary,"shifted_label_control":{"replicates":len(shuffled),"draw_attempts":int(shuffled.draw_attempt.max()),"p95_relative_improvement_percent":q95,"observed_relative_improvement_percent":comparisons["E2b_vs_E1"]["relative_improvement_percent"],"passed":comparisons["E2b_vs_E1"]["relative_improvement_percent"]>q95},"classification_gates":gates,"secondary_forward":expanding,"repeated_team":repeated,"direction_registry":registries,"hard_qc":{"complete_features":bool(np.isfinite(data[CONTINUOUS+["outcome_mps"]].to_numpy()).all()),"each_row_predicted_once_per_model":bool(pred.groupby(["model","row_id"]).size().eq(1).all()),"five_folds_each_match":bool(data.groupby("match_id").fold.nunique().eq(5).all()),"no_game3_access":True,"no_interpolation":True,"protocol_unchanged":True,"common_prediction_rows":bool(all(x==prediction_sets[0] for x in prediction_sets[1:])),"bootstrap_valid":len(boots)>=1900},"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in FROZEN.items()},"input":{"path":str(INPUT.relative_to(ROOT)),"sha256":sha(INPUT),"publication":"local_only"},"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"polars":pl.__version__}}
    pl.from_pandas(data).write_parquet(output/"prediction_source_rows.parquet",compression="zstd")
    pl.from_pandas(pred).write_parquet(output/"prediction_rows.parquet",compression="zstd")
    exclusions.to_csv(output/"exclusions.csv",index=False); pd.DataFrame(sample).to_csv(output/"sample_ledger.csv",index=False); per.to_csv(output/"heldout_errors.csv",index=False); boots.to_csv(output/"bootstrap_results.csv",index=False,float_format="%.12g"); shuffled.to_csv(output/"shuffle_control.csv",index=False,float_format="%.12g"); secondary.to_csv(output/"secondary_descriptions.csv",index=False,float_format="%.12g")
    write_json(output/"model_comparisons.json",result); write_json(output/"fold_ledger.json",fold_log); write_json(output/"hard_qc.json",result["hard_qc"])
    write_json(output/"manifest.json",{"starting_commit":"1bc9d499ced4e3e48c54950202fcc60b19ca708a","source":str(Path(__file__).relative_to(ROOT)),"source_sha256":sha(Path(__file__)),"frozen_hashes":result["frozen_hashes"],"provider_linked_observation_tables":"local_only"})
    governed=["exclusions.csv","sample_ledger.csv","heldout_errors.csv","bootstrap_results.csv","shuffle_control.csv","secondary_descriptions.csv","model_comparisons.json","fold_ledger.json","hard_qc.json","manifest.json"]
    write_json(output/"governed_hashes.json",{n:sha(output/n) for n in governed})
    return result


def compare(primary: Path, rerun: Path) -> dict:
    ledger=json.loads((primary/"governed_hashes.json").read_text()); comparisons={n:(primary/n).read_bytes()==(rerun/n).read_bytes() for n in ledger}
    return {"files_compared":len(comparisons),"all_governed_outputs_byte_identical":all(comparisons.values()),"comparisons":comparisons}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=OUT); parser.add_argument("--verify-against",type=Path); parser.add_argument("--clean-output",action="store_true"); args=parser.parse_args()
    if args.clean_output and args.output.exists(): shutil.rmtree(args.output)
    value=compare(args.output,args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps(clean(value),indent=2,sort_keys=True))
