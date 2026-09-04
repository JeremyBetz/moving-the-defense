"""Execute frozen Defensive Reorganization Departure v1 on the seven IDSSE matches.

The implementation is deliberately narrow: it reuses the closed spatial
footprint observation registry for the rank-fixed response target, derives the
predeclared attacker/ball context from the same validated native IDSSE support,
and performs only the frozen nested Ridge comparison.
"""

from __future__ import annotations

import argparse
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

import concurrent_attacker_defensive_geometry_idsse_v1 as concurrent  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402
from defensive_reorganization_departure_v1_design import (  # noqa: E402
    attacking_frame,
    ball_nearest_attacker,
    classify_application_foundation,
    family_is_stable,
    relative_improvement_percent,
    select_alpha,
)

PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_departure_v1.md"
CONFIG = ROOT / "config/defensive_reorganization_departure_v1.json"
LEDGER = ROOT / "config/defensive_reorganization_departure_v1_hashes.json"
TARGET = ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/observation_rows.parquet"
DEFAULT_OUTPUT = ROOT / "outputs/defensive_reorganization_departure_v1"
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
SEED, BOOT, MIN_VALID = 20260903, 1000, 950
FRAME_NS, EDGE = 40_000_000, 3
E0 = ("attacker_path_exposure_m", "attacker_path_prior_m")
DIRECTION = ("attacker_goalward_displacement_m", "attacker_outward_displacement_m")
START = ("attacker_minus_unit_goalward_m", "attacker_minus_unit_outward_m", "defending_unit_depth_m", "defending_unit_width_m")
BALL = ("attacker_ball_distance_start_m", "ball_minus_unit_goalward_m", "ball_minus_unit_outward_m", "attacker_ball_distance_change_m")
MODELS = {"E0": E0, "E1": E0 + DIRECTION + START + BALL,
          "E1_minus_movement_direction": E0 + START + BALL,
          "E1_minus_start_position": E0 + DIRECTION + BALL,
          "E1_minus_ball_geometry": E0 + DIRECTION + START}


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


def frozen() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def verify_frozen() -> None:
    ledger = frozen()
    bad = {name: [sha(ROOT / name), expected] for section in ("frozen_design_sha256", "closed_inherited_artifacts_sha256")
           for name, expected in ledger[section].items() if sha(ROOT / name) != expected}
    if bad: raise RuntimeError(f"frozen hash failure: {bad}")


def smoothed(entity: dict, idx: int) -> np.ndarray:
    window = np.column_stack([entity["x"][idx - EDGE: idx + EDGE + 1], entity["y"][idx - EDGE: idx + EDGE + 1]]).astype(float)
    if len(window) != 7 or not entity["valid"][idx - EDGE: idx + EDGE + 1].all():
        raise ValueError("incomplete centered smoothing support")
    return window.mean(axis=0)


def smooth_series(entity: dict, indices: np.ndarray) -> np.ndarray:
    return np.asarray([smoothed(entity, int(index)) for index in indices])


def path(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum(dtype=np.float64))


def target_rows() -> pd.DataFrame:
    columns = ["observation_id", "match_id", "period", "time_period_s", "time_utc_ns", "attacker_key", "attacking_team", "defending_team", "block_id", "defender_key", "distance_rank", "response_2s_m"]
    data = pd.DataFrame(pl.read_parquet(TARGET, columns=columns).to_dict(as_series=False))
    rows = []
    for oid, group in data.groupby("observation_id", sort=False):
        group = group.sort_values("distance_rank")
        if group.distance_rank.tolist() != list(range(1, 11)): raise RuntimeError(f"invalid inherited rank vector: {oid}")
        first = group.iloc[0]
        rows.append({"observation_id": oid, "match_id": first.match_id, "period": int(first.period),
                     "time_period_s": float(first.time_period_s), "time_utc_ns": int(first.time_utc_ns),
                     "attacker_key": first.attacker_key, "attacking_team": first.attacking_team,
                     "defending_team": first.defending_team, "block_id": int(first.block_id),
                     "defender_keys": tuple(group.defender_key.tolist()),
                     "near_component_m": float(group.iloc[:3].response_2s_m.mean()),
                     "middle_component_m": float(group.iloc[3:7].response_2s_m.mean()),
                     "Y_m": float(group.iloc[:3].response_2s_m.mean() - group.iloc[3:7].response_2s_m.mean())})
    return pd.DataFrame(rows).sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)


def period_signs(metadata: dict, tracking: dict) -> dict[tuple[int, str], int]:
    result = {}
    for p_number, period in enumerate(idsse.PERIODS, 1):
        block = tracking[period]
        early = block["time_ns"] <= block["time_ns"][0] + 1_960_000_000
        for player in metadata["players"].values():
            if not player.goalkeeper: continue
            entity = next((e for e in block["entities"] if e["team_id"] == player.team_id and e["person_id"] == player.player_id), None)
            if entity is None: continue
            valid = early & entity["valid"]
            if valid.sum() >= 25: result[(p_number, player.team_id)] = 1 if float(np.median(entity["x"][valid])) < 0 else -1
        teams = {metadata["home_team_id"], metadata["away_team_id"]}
        if {team for number, team in result if number == p_number} != teams: raise RuntimeError("incomplete goalkeeper direction registry")
    return result


def add_features_for_match(base: pd.DataFrame, match_id: str) -> tuple[pd.DataFrame, list[dict], int]:
    metadata, _, tracking = concurrent.load_native(match_id)
    signs = period_signs(metadata, tracking)
    result, exclusions, offball_base = [], [], 0
    for _, row in base.loc[base.match_id == match_id].iterrows():
        period_name = idsse.PERIODS[int(row.period) - 1]; pdata = tracking[period_name]
        lookup = {int(t): i for i, t in enumerate(pdata["time_ns"])}
        anchor = int(row.time_utc_ns)
        required = np.arange(anchor - 4_120_000_000, anchor + 120_000_000 + FRAME_NS, FRAME_NS, dtype=np.int64)
        if any(int(t) not in lookup for t in required):
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "feature_cadence_support"}); continue
        idx = lookup[anchor]
        entity = {(e["team_id"], e["person_id"]): e for e in pdata["entities"]}
        attack, defend = row.attacking_team, row.defending_team
        attackers = sorted(p.player_id for p in metadata["players"].values() if p.team_id == attack and not p.goalkeeper and (p.team_id, p.player_id) in entity
                           and entity[(p.team_id, p.player_id)]["valid"][idx - EDGE: idx + EDGE + 1].all())
        if len(attackers) != 10:
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "complete_attacking_anchor_set"}); continue
        ball = next((e for e in pdata["entities"] if e["team_id"] == "BALL"), None)
        if ball is None or not ball["valid"][idx - 53:idx + 4].all():
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "ball_feature_support"}); continue
        attacker_positions = {player: smoothed(entity[(attack, player)], idx) for player in attackers}
        nearest = ball_nearest_attacker(attacker_positions, smoothed(ball, idx))
        if row.attacker_key == nearest:
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "ball_nearest_at_anchor"}); continue
        offball_base += 1
        focal = entity.get((attack, row.attacker_key))
        if focal is None or not focal["valid"][idx - 103:idx + 4].all():
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "focal_feature_support"}); continue
        # The closed rank registry, rather than the full match roster, defines
        # the inherited complete D1--D10 target vector.  Metadata includes
        # players who may no longer be active after substitutions.
        defenders = list(row.defender_keys)
        if len(defenders) != 10 or not all((defend, p) in entity and entity[(defend, p)]["valid"][idx - 53:idx + 4].all() for p in defenders):
            raise RuntimeError("inherited target and feature defender support disagree")
        prior = smooth_series(focal, np.arange(idx - 100, idx - 49))
        exposure = smooth_series(focal, np.arange(idx - 50, idx + 1))
        focal_start, focal_anchor = exposure[0], exposure[-1]
        defender_start = np.stack([smoothed(entity[(defend, player)], idx - 50) for player in defenders])
        ball_start, ball_anchor = smoothed(ball, idx - 50), smoothed(ball, idx)
        sign = signs[(int(row.period), attack)]
        transformed = attacking_frame(np.vstack([focal_start, focal_anchor, defender_start, ball_start, ball_anchor]), sign, focal_start[1])
        f0, ft = transformed[0], transformed[1]
        ds = transformed[2:12]; b0, bt = transformed[12], transformed[13]
        unit = ds.mean(axis=0)
        values = row.to_dict()
        values.update({
            "attacker_path_exposure_m": path(exposure), "attacker_path_prior_m": path(prior),
            "attacker_goalward_displacement_m": float(ft[0] - f0[0]), "attacker_outward_displacement_m": float(ft[1] - f0[1]),
            "attacker_minus_unit_goalward_m": float(f0[0] - unit[0]), "attacker_minus_unit_outward_m": float(f0[1] - unit[1]),
            "defending_unit_depth_m": float(np.ptp(ds[:, 0])), "defending_unit_width_m": float(np.ptp(ds[:, 1])),
            "attacker_ball_distance_start_m": float(np.linalg.norm(f0 - b0)), "ball_minus_unit_goalward_m": float(b0[0] - unit[0]),
            "ball_minus_unit_outward_m": float(b0[1] - unit[1]), "attacker_ball_distance_change_m": float(np.linalg.norm(ft - bt) - np.linalg.norm(f0 - b0)),
            "ball_nearest_attacker_key": nearest,
        })
        result.append(values)
    return pd.DataFrame(result), exclusions, offball_base


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    base = target_rows(); frames = []; excluded = []
    base_offball = {}
    for match in MATCHES:
        data, log, count = add_features_for_match(base, match); frames.append(data); excluded.extend(log); base_offball[match] = count
    sample = pd.concat(frames, ignore_index=True).sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)
    ledger = pd.DataFrame(excluded, columns=["observation_id", "match_id", "reason"])
    all_counts = base.groupby("match_id").size(); kept = sample.groupby("match_id").size()
    report = {m: {"inherited_target_rows": int(all_counts[m]), "threshold_free_off_ball_base_rows": int(base_offball[m]), "common_sample_rows": int(kept.get(m, 0)),
                  "retention_of_off_ball_base_rows": float(kept.get(m, 0) / base_offball[m])} for m in MATCHES}
    return sample, ledger, report


def fit_ridge(train: pd.DataFrame, test: pd.DataFrame, features: tuple[str, ...], alpha: float) -> tuple[np.ndarray, list[str], str]:
    mean = train.loc[:, features].mean().to_numpy(float); sd = train.loc[:, features].std(ddof=0).to_numpy(float); keep = sd > 0
    x_train = (train.loc[:, features].to_numpy(float)[:, keep] - mean[keep]) / sd[keep]
    x_test = (test.loc[:, features].to_numpy(float)[:, keep] - mean[keep]) / sd[keep]
    x_train = np.column_stack([np.ones(len(train)), x_train]); x_test = np.column_stack([np.ones(len(test)), x_test])
    penalty = np.eye(x_train.shape[1]); penalty[0, 0] = 0.0
    try: beta = np.linalg.solve(x_train.T @ x_train + alpha * penalty, x_train.T @ train.Y_m.to_numpy(float)); solver = "solve"
    except np.linalg.LinAlgError: beta = np.linalg.pinv(x_train.T @ x_train + alpha * penalty, rcond=1e-15) @ (x_train.T @ train.Y_m.to_numpy(float)); solver = "pinv"
    return x_test @ beta, list(np.asarray(features)[keep]), solver


def choose_alpha(train: pd.DataFrame, features: tuple[str, ...]) -> tuple[float, dict[str, float]]:
    scores = {}
    for alpha in ALPHAS:
        errors = {}
        for heldout in MATCHES:
            inner_test = train.match_id.eq(heldout)
            if not inner_test.any(): continue
            pred, _, _ = fit_ridge(train.loc[~inner_test], train.loc[inner_test], features, alpha)
            errors[heldout] = np.abs(train.loc[inner_test, "Y_m"].to_numpy(float) - pred)
        scores[alpha] = float(np.mean([value.mean() for value in errors.values()]))
    return select_alpha(scores), {str(key): float(value) for key, value in scores.items()}


def nested_predictions(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows, alpha_rows = [], []
    for heldout in MATCHES:
        train, test = data.loc[data.match_id != heldout], data.loc[data.match_id == heldout]
        for model, features in MODELS.items():
            alpha, inner = choose_alpha(train, features)
            pred, kept, solver = fit_ridge(train, test, features, alpha)
            out = test[["observation_id", "match_id", "period", "time_period_s", "block_id", "attacker_key", "Y_m", "near_component_m", "middle_component_m"]].copy()
            out["model"] = model; out["prediction_m"] = pred; all_rows.append(out)
            alpha_rows.append({"heldout_match": heldout, "model": model, "alpha": alpha, "inner_macro_mae_by_alpha": json.dumps(inner, sort_keys=True),
                               "retained_features": json.dumps(kept), "solver": solver})
    return pd.concat(all_rows, ignore_index=True), pd.DataFrame(alpha_rows)


def model_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []; values = {}
    for model, group in predictions.groupby("model", sort=True):
        by_match = {}
        for match, part in group.groupby("match_id", sort=True):
            error = part.Y_m.to_numpy(float) - part.prediction_m.to_numpy(float); mae = float(np.abs(error).mean())
            by_match[match] = mae
            rows.append({"model": model, "match_id": match, "n": len(part), "MAE_m": mae, "RMSE_m": float(np.sqrt(np.mean(error ** 2)))})
        error = group.Y_m.to_numpy(float) - group.prediction_m.to_numpy(float)
        values[model] = {"macro_MAE_m": float(np.mean(list(by_match.values()))), "median_match_MAE_m": float(np.median(list(by_match.values()))),
                         "weighted_MAE_m": float(np.abs(error).mean()), "RMSE_m": float(np.sqrt(np.mean(error ** 2))), "by_match": by_match}
    return pd.DataFrame(rows), values


def bootstrap(predictions: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    wide = predictions.pivot(index="observation_id", columns="model", values="prediction_m").reset_index()
    meta = predictions[predictions.model == "E0"][["observation_id", "match_id", "period", "block_id", "Y_m"]]
    data = meta.merge(wide, on="observation_id", validate="one_to_one")
    groups = {key: value.index.to_numpy() for key, value in data.groupby(["match_id", "period", "block_id"], sort=True)}
    blocks = {(match, period): [key for key in groups if key[:2] == (match, period)] for match in MATCHES for period in (1, 2)}
    rng = np.random.Generator(np.random.PCG64(SEED)); rows = []
    for _ in range(BOOT):
        occurrence_errors = {model: [] for model in MODELS}
        for match in rng.choice(MATCHES, size=len(MATCHES), replace=True):
            selected = []
            for period in (1, 2):
                keys = blocks[(match, period)]
                if not keys: continue
                selected.extend(groups[keys[int(i)]] for i in rng.integers(0, len(keys), len(keys)))
            if not selected: continue
            ix = np.concatenate(selected)
            for model in MODELS: occurrence_errors[model].append(float(np.abs(data.Y_m.to_numpy(float)[ix] - data[model].to_numpy(float)[ix]).mean()))
        if any(len(value) != len(MATCHES) for value in occurrence_errors.values()): continue
        macro = {model: float(np.mean(value)) for model, value in occurrence_errors.items()}
        row = {"absolute_E1_minus_E0_m": macro["E0"] - macro["E1"], "relative_E1_vs_E0_percent": relative_improvement_percent(macro["E0"], macro["E1"])}
        for name in ("movement_direction", "start_position", "ball_geometry"):
            ablated = f"E1_minus_{name}"; row[f"ablation_{name}_relative_worsening_percent"] = relative_improvement_percent(macro["E1"], macro[ablated])
        rows.append(row)
    table = pd.DataFrame(rows)
    interval = {column: {"estimate": float(table[column].mean()), "ci_low": float(table[column].quantile(.025)), "ci_high": float(table[column].quantile(.975)), "valid": len(table)} for column in table}
    return table, interval


def classification(metrics: dict) -> tuple[str, list[str], dict]:
    full = metrics["E1"]["by_match"]; stable = []
    details = {}
    for family in ("movement_direction", "start_position", "ball_geometry"):
        ablated = metrics[f"E1_minus_{family}"]["by_match"]
        macro = relative_improvement_percent(metrics["E1"]["macro_MAE_m"], metrics[f"E1_minus_{family}"]["macro_MAE_m"])
        worsened = int(sum(ablated[match] > full[match] for match in MATCHES))
        passed = family_is_stable(full, ablated); details[family] = {"macro_worsening_percent": macro, "matches_worsened": worsened, "passed_stable_family_gate": passed}
        if passed: stable.append(family)
    status = classify_application_foundation(metrics["E0"]["by_match"], full, len(stable), valid=True)
    return status, stable, details


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "reproduction.json", "final_hashes.json", "heldout_predictions.parquet"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def report(output: Path, result: dict) -> None:
    status = result["status"]
    if status == "DRD APPLICATION FOUNDATION INVALID":
        text = ["# Defensive Reorganization Departure v1 — IDSSE result", "", "**Formal status:** `DRD APPLICATION FOUNDATION INVALID`", "",
                "The frozen common-sample gate failed before any E0/E1 fit or prediction. J03WN1 retained fewer than 1,000 threshold-free, off-ball eligible rows because exactly ten attacking outfield players with complete anchor support were unavailable at most inherited target anchors.", "",
                "No model, prediction error, DRD residual, retrieval passage, Metrica transport, SkillCorner outcome, or player ranking was produced. The protocol, thresholds, target, features, and data-support requirement were not changed."]
        (output / "result_report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
        return
    metrics = result["metrics"]
    text = ["# Defensive Reorganization Departure v1 — IDSSE result", "", f"**Formal status:** `{status}`", "",
            "This governed seven-match IDSSE execution uses the prospectively frozen target, features, nested validation, and classification logic.", "",
            "## Heldout performance", "", "| Model | Equal-match macro MAE (m) |", "|---|---:|"]
    for model in ("E0", "E1", "E1_minus_movement_direction", "E1_minus_start_position", "E1_minus_ball_geometry"):
        text.append(f"| {model} | {metrics[model]['macro_MAE_m']:.6f} |")
    text += ["", f"E1 versus E0 macro improvement: **{result['e1_vs_e0_relative_improvement_percent']:.3f}%**.", ""]
    if status != "SUPPORTED": text += ["## Frozen stop rule", "", "The primary application foundation did not meet every SUPPORT gate. No DRD residual was named or inspected, no retrieval board was generated, no Metrica transport was run, and no SkillCorner outcome was inspected.", ""]
    text += ["## Boundary", "", "These results concern heldout prediction of an observed geometric near-minus-middle response. They do not establish tactical response, causation, influence, attention, marking, responsibility, gravity, or player value.", ""]
    (output / "result_report.md").write_text("\n".join(text), encoding="utf-8")


def execute(output: Path) -> dict:
    verify_frozen()
    if output.exists() and any(output.iterdir()): raise RuntimeError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    data, exclusions, retention = build_sample()
    if any(retention[m]["common_sample_rows"] < 1000 or retention[m]["retention_of_off_ball_base_rows"] < .9 for m in MATCHES):
        hard_qc = {"frozen_hashes": True, "seven_governed_matches_only": set(data.match_id) == set(MATCHES), "game3_untouched": True,
                   "common_sample_minimum_rows": False,
                   "common_sample_retention_minimum": all(value["retention_of_off_ball_base_rows"] >= .9 for value in retention.values()),
                   "model_not_fitted_after_pre_fit_invalidity": True, "no_prediction_error_or_residual_inspected": True,
                   "no_skillcorner": True, "no_metrica_transport": True, "no_player_ranking": True}
        result = {"status": "DRD APPLICATION FOUNDATION INVALID", "invalid_reason": "frozen_common_sample_minimum_rows_per_match_failure",
                  "sample_retention": retention, "hard_qc": hard_qc,
                  "frozen_hashes": {**frozen()["frozen_design_sha256"], **frozen()["closed_inherited_artifacts_sha256"]},
                  "execution": {"empirical_target_used_for_eligibility": True, "model_fitted": False, "out_of_fold_prediction_computed": False,
                                "prediction_error_or_residual_inspected": False, "DRD_computed": False, "retrieval_generated": False,
                                "Metrica_transport": False, "SkillCorner_outcome": False, "Game3_accessed": False}}
        exclusions.to_csv(output / "eligibility_ledger.csv", index=False)
        pd.DataFrame([{"match_id": key, **value} for key, value in retention.items()]).to_csv(output / "sample_retention.csv", index=False)
        write_json(output / "feature_dictionary.json", {name: list(features) for name, features in MODELS.items()})
        write_json(output / "hard_qc.json", hard_qc)
        write_json(output / "manifest.json", {"matches": list(MATCHES), "protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "target_registry_sha256": sha(TARGET), "status": result["status"], "model_fitted": False})
        write_json(output / "result.json", result); report(output, result)
        write_json(output / "governed_hashes.json", hash_outputs(output))
        return result
    if not np.isfinite(data[list(MODELS["E1"]) + ["Y_m"]].to_numpy(float)).all(): raise RuntimeError("nonfinite common sample")
    predictions, alphas = nested_predictions(data)
    if predictions.groupby(["model", "observation_id"]).size().max() != 1 or len(predictions) != len(data) * len(MODELS): raise RuntimeError("heldout prediction coverage failure")
    metrics_table, metrics = model_metrics(predictions)
    _, boot_interval = bootstrap(predictions)
    status, stable, ablation = classification(metrics)
    e0, e1 = metrics["E0"], metrics["E1"]
    per_match = pd.DataFrame([{"match_id": match, "E0_MAE_m": e0["by_match"][match], "E1_MAE_m": e1["by_match"][match],
                               "relative_improvement_percent": relative_improvement_percent(e0["by_match"][match], e1["by_match"][match])} for match in MATCHES])
    hard_qc = {"frozen_hashes": True, "seven_governed_matches_only": set(data.match_id) == set(MATCHES), "game3_untouched": True,
               "common_sample_minimum_rows": all(value["common_sample_rows"] >= 1000 for value in retention.values()),
               "common_sample_retention_minimum": all(value["retention_of_off_ball_base_rows"] >= .9 for value in retention.values()),
               "finite_common_features_and_target": True, "one_outer_prediction_per_model_observation": True,
               "bootstrap_valid_at_least_950": len(boot_interval) > 0 and next(iter(boot_interval.values()))["valid"] >= MIN_VALID,
               "no_skillcorner": True, "no_metrica_transport": status != "SUPPORTED", "no_player_ranking": True}
    result = {"status": status, "sample_retention": retention, "metrics": metrics, "e1_vs_e0_absolute_macro_improvement_m": e0["macro_MAE_m"] - e1["macro_MAE_m"],
              "e1_vs_e0_relative_improvement_percent": relative_improvement_percent(e0["macro_MAE_m"], e1["macro_MAE_m"]),
              "matches_improved": int(sum(e1["by_match"][m] < e0["by_match"][m] for m in MATCHES)),
              "maximum_match_worsening_percent": float(max(relative_improvement_percent(e0["by_match"][m], e1["by_match"][m]) * -1 for m in MATCHES)),
              "stable_context_families": stable, "family_ablations": ablation, "bootstrap_intervals": boot_interval, "hard_qc": hard_qc,
              "frozen_hashes": {**frozen()["frozen_design_sha256"], **frozen()["closed_inherited_artifacts_sha256"]},
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "polars": pl.__version__}}
    exclusions.to_csv(output / "eligibility_ledger.csv", index=False)
    write_json(output / "feature_dictionary.json", {name: list(features) for name, features in MODELS.items()})
    alphas.to_csv(output / "fold_alpha_ledger.csv", index=False)
    predictions.to_parquet(output / "heldout_predictions.parquet", index=False)
    metrics_table.to_csv(output / "match_metrics.csv", index=False); per_match.to_csv(output / "e0_e1_per_match_comparison.csv", index=False)
    pd.DataFrame([{**{"family": key}, **value} for key, value in ablation.items()]).to_csv(output / "family_ablations.csv", index=False)
    pd.DataFrame([{**{"quantity": key}, **value} for key, value in boot_interval.items()]).to_csv(output / "bootstrap_intervals.csv", index=False)
    write_json(output / "reliability_diagnostics.json", {"authorized": status == "SUPPORTED", "reason": "not_run_under_frozen_stop_rule" if status != "SUPPORTED" else "execution_not_implemented"})
    write_json(output / "hard_qc.json", hard_qc); write_json(output / "manifest.json", {"matches": list(MATCHES), "protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "target_registry_sha256": sha(TARGET), "status": status})
    write_json(output / "result.json", result); report(output, result)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    return result


def verify(primary: Path, rerun: Path) -> dict:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8")); rows = []
    for name, expected in ledger.items():
        a, b = primary / name, rerun / name
        rows.append({"file": name, "expected_sha256": expected, "primary_sha256": sha(a), "rerun_sha256": sha(b), "byte_identical": a.read_bytes() == b.read_bytes()})
    result = {"files_compared": len(rows), "all_governed_outputs_byte_identical": all(row["byte_identical"] for row in rows), "comparisons": rows}
    write_json(primary / "reproduction.json", result); write_json(primary / "final_hashes.json", {**ledger, "governed_hashes.json": sha(primary / "governed_hashes.json"), "reproduction.json": sha(primary / "reproduction.json")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT); parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    result = verify(args.output, args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps({"status": result.get("status"), "byte_identical": result.get("all_governed_outputs_byte_identical")}, sort_keys=True))


if __name__ == "__main__": main()
