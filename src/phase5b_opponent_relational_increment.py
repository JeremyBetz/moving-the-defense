"""Execute frozen Phase 5B opponent-relational predictive-increment protocol v1.0."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import phase5a_contextual_expectation_feasibility as p5a
from phase4c_idsse_external_replication import MATCH_IDS, PERIODS


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_MD = ROOT / "docs" / "phase5b_opponent_relational_increment_protocol.md"
PROTOCOL_JSON = ROOT / "config" / "phase5b_opponent_relational_increment_protocol.json"
PHASE5A_SOURCE = ROOT / "src" / "phase5a_contextual_expectation_feasibility.py"
PHASE5A_PROTOCOL = ROOT / "docs" / "phase5a_contextual_expectation_protocol.md"
PHASE5A_CONFIG = ROOT / "config" / "phase5a_contextual_expectation_protocol.json"
PHASE4_SOURCE = ROOT / "src" / "phase4c_idsse_external_replication.py"
PHASE4_PROTOCOL = ROOT / "docs" / "phase4c_external_replication_protocol.md"
PHASE4_CONFIG = ROOT / "config" / "phase4c_external_replication_protocol.json"
OUTPUT_DIR = ROOT / "outputs" / "phase5b"
FIGURE_DIR = ROOT / "figures" / "phase5b"
FROZEN_COMMIT = "3051187230ab936a145b7257dbd768640800b417"
PROJECTION_TOLERANCE_M = 1e-9

B4 = list(p5a.FEATURES["B4"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometry_names(ranks: list[int], span_prefix: str | None) -> list[str]:
    names = []
    for rank in ranks:
        names += [f"focal_minus_A{rank}_x_m", f"focal_minus_A{rank}_y_m", f"focal_A{rank}_distance_m", f"A{rank}_ball_distance_m"]
    if span_prefix:
        names += [f"{span_prefix}_x_span_m", f"{span_prefix}_y_span_m"]
    return names


def motion_names(ranks: list[int]) -> list[str]:
    names = []
    for rank in ranks:
        names += [f"A{rank}_recent_absolute_path_m", f"A{rank}_terminal_vx_mps", f"A{rank}_terminal_vy_mps"]
    return names


def relational_names(ranks: list[int]) -> list[str]:
    names = []
    for rank in ranks:
        names += [f"focal_A{rank}_distance_change_m", f"focal_A{rank}_relative_path_m", f"focal_approach_toward_A{rank}_mps", f"A{rank}_approach_toward_focal_mps"]
    return names


G13, M13, R13 = geometry_names([1, 2, 3], "selected_attackers"), motion_names([1, 2, 3]), relational_names([1, 2, 3])
G1, M1, R1 = geometry_names([1], None), motion_names([1]), relational_names([1])
G46, M46, R46 = geometry_names([4, 5, 6], "nonlocal_attackers"), motion_names([4, 5, 6]), relational_names([4, 5, 6])

PRIMARY_FEATURES = {"B4": B4, "B5": B4 + G13, "B6": B4 + G13 + M13, "B7": B4 + G13 + M13 + R13}
K1_FEATURES = {"B4": B4, "K1_B5": B4 + G1, "K1_B6": B4 + G1 + M1, "K1_B7": B4 + G1 + M1 + R1}
CONTROL_FEATURES = {
    "B4": B4,
    "LOCAL_B5": B4 + G13, "LOCAL_B6": B4 + G13 + M13, "LOCAL_B7": B4 + G13 + M13 + R13,
    "NONLOCAL_B5": B4 + G46, "NONLOCAL_B6": B4 + G46 + M46, "NONLOCAL_B7": B4 + G46 + M46 + R46,
}


def selected_features(
    ranks: list[int], selected: list[tuple[str, np.ndarray, dict[str, Any]]],
    focal_raw: np.ndarray, focal_sm: np.ndarray, ball_raw: np.ndarray,
    history_idx: np.ndarray, sigma: int, span_prefix: str | None,
) -> tuple[dict[str, float], bool, bool, int]:
    """Return cutoff geometry, history features, B7 completeness, and near-zero count."""
    features: dict[str, float] = {}
    history_complete = True
    relational_complete = True
    near_zero = 0
    cutoff_positions = []
    for rank, (_, attacker_now, entity) in zip(ranks, selected):
        delta = focal_raw - attacker_now
        cutoff_positions.append(attacker_now)
        features[f"focal_minus_A{rank}_x_m"] = float(delta[0])
        features[f"focal_minus_A{rank}_y_m"] = float(delta[1])
        features[f"focal_A{rank}_distance_m"] = float(np.linalg.norm(delta))
        features[f"A{rank}_ball_distance_m"] = float(np.linalg.norm(attacker_now - ball_raw))
        if not entity["valid"][history_idx].all():
            history_complete = False
            continue
        raw = p5a.standardized_xy(np.column_stack([entity["x"][history_idx], entity["y"][history_idx]]), sigma)
        sm = p5a.trailing_mean(raw)
        if len(sm) != len(focal_sm):
            history_complete = False
            continue
        velocity = p5a.terminal_velocity(sm)
        features[f"A{rank}_recent_absolute_path_m"] = p5a.path_length(sm)
        features[f"A{rank}_terminal_vx_mps"] = float(velocity[0])
        features[f"A{rank}_terminal_vy_mps"] = float(velocity[1])
        relative = sm - focal_sm
        distances = np.linalg.norm(relative, axis=1)
        features[f"focal_A{rank}_distance_change_m"] = float(distances[-1] - distances[0])
        features[f"focal_A{rank}_relative_path_m"] = p5a.path_length(relative)
        terminal_distance = float(distances[-1])
        if terminal_distance <= PROJECTION_TOLERANCE_M:
            near_zero += 1
            relational_complete = False
            continue
        unit_focal_to_attacker = relative[-1] / terminal_distance
        focal_velocity = p5a.terminal_velocity(focal_sm)
        features[f"focal_approach_toward_A{rank}_mps"] = float(focal_velocity @ unit_focal_to_attacker)
        features[f"A{rank}_approach_toward_focal_mps"] = float(velocity @ (-unit_focal_to_attacker))
    if span_prefix:
        positions = np.stack(cutoff_positions)
        features[f"{span_prefix}_x_span_m"] = float(positions[:, 0].max() - positions[:, 0].min())
        features[f"{span_prefix}_y_span_m"] = float(positions[:, 1].max() - positions[:, 1].min())
    return features, history_complete, relational_complete, near_zero


def enrich_rows(raw_dir: Path, cache_dir: Path, history_frames: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    base, _, _ = p5a.prepare_rows(raw_dir, cache_dir, history_frames, include_target=True)
    base = base[base["B4_complete"]].copy().reset_index(drop=True)
    extra_rows: dict[int, dict[str, Any]] = {}
    for match_id, match_group in base.groupby("match_id"):
        metadata, _, tracking = p5a.match_inputs(raw_dir, cache_dir, match_id)
        orientations = {period: p5a.period_orientation(metadata, tracking, period) for period in PERIODS}
        for row_index, row in match_group.iterrows():
            data = tracking[row["period"]]
            cutoff_ns = int(row["prediction_cutoff_ns"])
            cutoff_idx = int(np.searchsorted(data["time_ns"], cutoff_ns))
            if cutoff_idx >= len(data["time_ns"]) or int(data["time_ns"][cutoff_idx]) != cutoff_ns:
                raise RuntimeError(f"No exact cutoff frame: {match_id} {row['interval_id']} {cutoff_ns}")
            history_idx = np.arange(cutoff_idx - history_frames + 1, cutoff_idx + 1)
            if history_idx[0] < 0 or not np.all(np.diff(data["time_ns"][history_idx]) == 40_000_000):
                raise RuntimeError("Frozen history support failed")
            entity_by_key = {(e["team_id"], e["person_id"]): e for e in data["entities"]}
            defending_team = row["defending_team_id"]
            attacking_team = row["attacking_team_id"]
            sigma = orientations[row["period"]][defending_team][0]
            focal_entity = entity_by_key[(defending_team, row["focal_player_id"])]
            focal_raw_hist = p5a.standardized_xy(np.column_stack([focal_entity["x"][history_idx], focal_entity["y"][history_idx]]), sigma)
            focal_sm = p5a.trailing_mean(focal_raw_hist)
            focal_now = focal_raw_hist[-1]
            ball = next(e for e in data["entities"] if e["team_id"] == "BALL")
            ball_now = p5a.standardized_xy(np.array([[ball["x"][cutoff_idx], ball["y"][cutoff_idx]]]), sigma)[0]
            candidates = []
            for player in metadata["players"].values():
                if player.team_id != attacking_team or player.goalkeeper:
                    continue
                entity = entity_by_key.get((attacking_team, player.player_id))
                if entity is None or not entity["valid"][cutoff_idx]:
                    continue
                now = p5a.standardized_xy(np.array([[entity["x"][cutoff_idx], entity["y"][cutoff_idx]]]), sigma)[0]
                candidates.append((player.player_id, now, entity, float(np.linalg.norm(now - focal_now))))
            candidates.sort(key=lambda item: (item[3], str(item[0])))
            out: dict[str, Any] = {
                "K3_selectable": len(candidates) >= 3,
                "K6_selectable": len(candidates) >= 6,
                "selected_ids_fixed": True,
                "selection_time_ns": cutoff_ns,
                "opponent_feature_max_raw_time_ns": cutoff_ns,
                "near_zero_projection_pairs": 0,
            }
            if candidates:
                ball_ranked = sorted(candidates, key=lambda item: (float(np.linalg.norm(item[1] - ball_now)), str(item[0])))
                proxy_id = ball_ranked[0][0]
                selected_ids = [item[0] for item in candidates[:3]]
                out["ball_nearest_attacking_player_id"] = proxy_id
                out["ball_nearest_distance_m"] = float(np.linalg.norm(ball_ranked[0][1] - ball_now))
                out["ball_nearest_selected_category"] = f"A{selected_ids.index(proxy_id)+1}" if proxy_id in selected_ids else "outside_A1_A3"
            if len(candidates) >= 3:
                local = [(item[0], item[1], item[2]) for item in candidates[:3]]
                out.update({f"A{i}_player_id": value[0] for i, value in enumerate(local, 1)})
                feats, hist_ok, rel_ok, zero = selected_features([1, 2, 3], local, focal_now, focal_sm, ball_now, history_idx, sigma, "selected_attackers")
                out.update(feats)
                out["A1_A3_history_complete"] = hist_ok
                out["B5_complete"] = bool(np.isfinite([out.get(name, np.nan) for name in G13]).all())
                out["B6_complete"] = bool(hist_ok and np.isfinite([out.get(name, np.nan) for name in M13]).all())
                out["B7_complete"] = bool(out["B6_complete"] and rel_ok and np.isfinite([out.get(name, np.nan) for name in R13]).all())
                out["near_zero_projection_pairs"] += zero
                out["mean_A1_A3_recent_absolute_path_m"] = float(np.mean([out.get(f"A{i}_recent_absolute_path_m", np.nan) for i in (1, 2, 3)]))
            else:
                out.update({"A1_A3_history_complete": False, "B5_complete": False, "B6_complete": False, "B7_complete": False})
            if len(candidates) >= 6:
                nonlocal_players = [(item[0], item[1], item[2]) for item in candidates[3:6]]
                out.update({f"A{i}_player_id": value[0] for i, value in zip((4, 5, 6), nonlocal_players)})
                feats, hist_ok, rel_ok, zero = selected_features([4, 5, 6], nonlocal_players, focal_now, focal_sm, ball_now, history_idx, sigma, "nonlocal_attackers")
                out.update(feats)
                out["A4_A6_history_complete"] = hist_ok
                out["nonlocal_B7_complete"] = bool(hist_ok and rel_ok and np.isfinite([out.get(name, np.nan) for name in G46 + M46 + R46]).all())
                out["near_zero_projection_pairs"] += zero
            else:
                out.update({"A4_A6_history_complete": False, "nonlocal_B7_complete": False})
            out["control_complete"] = bool(out["B7_complete"] and out["nonlocal_B7_complete"])
            extra_rows[row_index] = out
    extra = pd.DataFrame.from_dict(extra_rows, orient="index").sort_index()
    enriched = pd.concat([base, extra], axis=1)
    common = enriched[enriched["B7_complete"]].copy().reset_index(drop=True)
    return enriched, common


def attrition_table(enriched: pd.DataFrame) -> pd.DataFrame:
    data = enriched.copy()
    data["phase5a_B4_complete"] = 1
    for source, target in [
        ("K3_selectable", "K3_selectable"), ("A1_A3_history_complete", "A1_A3_history_complete"),
        ("B5_complete", "B5_only_computable"), ("B6_complete", "B6_only_computable"),
        ("B7_complete", "B7_complete"), ("B7_complete", "final_primary_sample"),
        ("K6_selectable", "K6_selectable"), ("control_complete", "final_locality_control_sample"),
    ]:
        data[target] = data[source].fillna(False).astype(int)
    columns = ["phase5a_B4_complete", "K3_selectable", "A1_A3_history_complete", "B5_only_computable", "B6_only_computable", "B7_complete", "final_primary_sample", "K6_selectable", "final_locality_control_sample"]
    team = data.groupby(["match_id", "defending_team_id"], as_index=False)[columns].sum()
    match = data.groupby("match_id", as_index=False)[columns].sum(); match.insert(1, "defending_team_id", "ALL")
    overall = pd.DataFrame([{**{"match_id": "ALL", "defending_team_id": "ALL"}, **{c: int(data[c].sum()) for c in columns}}])
    return pd.concat([team, match, overall], ignore_index=True)


def run_models(data: pd.DataFrame, feature_map: dict[str, list[str]], analysis: str) -> dict[str, pd.DataFrame]:
    evaluation, inner_records, alpha_records, predictions, calibration = [], [], [], [], []
    for outer_match in sorted(data["match_id"].unique()):
        train, test = data[data.match_id != outer_match], data[data.match_id == outer_match]
        y_train, y_test = train["focal_relative_path_m"].to_numpy(float), test["focal_relative_path_m"].to_numpy(float)
        identifiers = test[["match_id", "interval_id", "defending_team_id", "focal_player_id"]].reset_index(drop=True)
        for level, features in feature_map.items():
            alpha, inner, selected_oof = p5a.choose_alpha(train, features)
            inner.insert(0, "analysis", analysis); inner.insert(1, "outer_heldout_match", outer_match); inner.insert(2, "model", level)
            inner_records.append(inner)
            model = p5a.fit_ridge(train[features].to_numpy(float), y_train, alpha)
            pred = p5a.predict_ridge(model, test[features].to_numpy(float))
            evaluation.append({"analysis": analysis, "outer_heldout_match": outer_match, "model": level, "alpha": alpha, "n": len(test), **p5a.metrics(y_test, pred)})
            alpha_records.append({"analysis": analysis, "outer_heldout_match": outer_match, "model": level, "selected_alpha": alpha, "outer_constant_features_removed": int((~model["keep"]).sum()), "outer_solver": model["solver"]})
            predictions.append(pd.concat([identifiers.copy(), pd.DataFrame({"row_index": test.index, "analysis": analysis, "outer_heldout_match": outer_match, "model": level, "observed": y_test, "predicted": pred, "residual": y_test - pred})], axis=1))
            oof = pd.DataFrame(selected_oof[alpha], columns=["row_index", "prediction"]).sort_values("row_index")
            edges = np.unique(np.quantile(oof["prediction"], [0, .2, .4, .6, .8, 1], method="linear"))
            bin_ids = np.zeros(len(test), dtype=int) if len(edges) < 2 else np.clip(np.searchsorted(edges[1:-1], pred, side="right"), 0, len(edges)-2)
            for bin_id in sorted(np.unique(bin_ids)):
                keep = bin_ids == bin_id
                calibration.append({"analysis": analysis, "outer_heldout_match": outer_match, "model": level, "bin": int(bin_id)+1, "realized_bins": max(1, len(edges)-1), "lower_edge": float(edges[bin_id]) if len(edges)>1 else float(edges[0]), "upper_edge": float(edges[bin_id+1]) if len(edges)>1 else float(edges[0]), "n": int(keep.sum()), "predicted_mean": float(pred[keep].mean()), "predicted_median": float(np.median(pred[keep])), "observed_mean": float(y_test[keep].mean()), "observed_median": float(np.median(y_test[keep]))})
            slope, intercept = np.polyfit(pred, y_test, 1) if np.std(pred) > 0 else (np.nan, np.nan)
            calibration.append({"analysis": analysis, "outer_heldout_match": outer_match, "model": level, "bin": "ALL", "realized_bins": max(1, len(edges)-1), "lower_edge": np.nan, "upper_edge": np.nan, "n": len(test), "predicted_mean": float(pred.mean()), "predicted_median": float(np.median(pred)), "observed_mean": float(y_test.mean()), "observed_median": float(np.median(y_test)), "calibration_slope": float(slope), "calibration_intercept": float(intercept), "mean_residual": float(np.mean(y_test-pred))})
    return {"evaluation": pd.DataFrame(evaluation), "inner": pd.concat(inner_records, ignore_index=True), "alphas": pd.DataFrame(alpha_records), "predictions": pd.concat(predictions, ignore_index=True), "calibration": pd.DataFrame(calibration)}


def summarize_primary(evaluation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    pivot = evaluation.pivot(index="outer_heldout_match", columns="model", values="MAE")
    rows = []
    for level in ("B4", "B5", "B6", "B7"):
        values = pivot[level]
        rel = (pivot.B4 - values) / pivot.B4
        rows.append({"model": level, "median_MAE": float(values.median()), "MAE_min": float(values.min()), "MAE_max": float(values.max()), "MAE_IQR": float(values.quantile(.75)-values.quantile(.25)), "median_relative_improvement_vs_B4": float(rel.median()), "matches_improved_vs_B4": int((values < pivot.B4).sum()), "matches_worsened_10pct_or_more_vs_B4": int((values >= 1.10*pivot.B4).sum())})
    summary = pd.DataFrame(rows)
    adjacent_rows, by_match = [], []
    for prior, current in (("B4", "B5"), ("B5", "B6"), ("B6", "B7")):
        rel = (pivot[prior]-pivot[current])/pivot[prior]
        passed = bool(rel.median() >= .03 and (pivot[current] < pivot[prior]).sum() >= 5 and (pivot[current] >= 1.10*pivot[prior]).sum() <= 1)
        adjacent_rows.append({"prior": prior, "current": current, "median_relative_MAE_improvement": float(rel.median()), "matches_improved": int((pivot[current] < pivot[prior]).sum()), "matches_worsened_10pct_or_more": int((pivot[current] >= 1.10*pivot[prior]).sum()), "materiality_pass": passed})
        for match in pivot.index:
            by_match.append({"prior": prior, "current": current, "outer_heldout_match": match, "prior_MAE": float(pivot.loc[match, prior]), "current_MAE": float(pivot.loc[match, current]), "relative_MAE_improvement": float(rel.loc[match])})
    opponent = summary[summary.model.isin(["B5", "B6", "B7"])]
    minimum = opponent.median_MAE.min()
    best = next(level for level in ("B5", "B6", "B7") if float(opponent.loc[opponent.model == level, "median_MAE"].iloc[0]) <= minimum + 1e-6)
    qualifying = opponent[(opponent.median_relative_improvement_vs_B4 >= .05) & (opponent.matches_improved_vs_B4 >= 6) & (opponent.matches_worsened_10pct_or_more_vs_B4 <= 1)]
    c = bool((opponent.median_relative_improvement_vs_B4 < .02).all() and (opponent.matches_improved_vs_B4 < 4).all())
    category = "A" if len(qualifying) else ("C" if c else "B")
    classification = {"category": category, "label": {"A":"OPPONENT_RELATIONAL_PREDICTIVE_INCREMENT_SUPPORTED", "B":"MIXED_PARTIAL", "C":"NO_PRACTICALLY_USEFUL_OPPONENT_INCREMENT"}[category], "best_opponent_model": best, "A_qualifying_models": qualifying.model.tolist(), "classification_precedence": ["A", "C", "B"], "mechanically_verified": True}
    return summary, pd.DataFrame(adjacent_rows), pd.DataFrame(by_match), classification


def summarize_sensitivity(evaluation: pd.DataFrame, models: list[str]) -> pd.DataFrame:
    pivot = evaluation.pivot(index="outer_heldout_match", columns="model", values="MAE")
    rows=[]
    for level in models:
        values=pivot[level]; rel=(pivot.B4-values)/pivot.B4
        rows.append({"model":level,"median_MAE":float(values.median()),"MAE_min":float(values.min()),"MAE_max":float(values.max()),"MAE_IQR":float(values.quantile(.75)-values.quantile(.25)),"median_relative_improvement_vs_B4":float(rel.median()),"matches_improved_vs_B4":int((values<pivot.B4).sum()),"matches_worsened_10pct_or_more_vs_B4":int((values>=1.10*pivot.B4).sum())})
    return pd.DataFrame(rows)


def residual_diagnostics(data: pd.DataFrame, predictions: pd.DataFrame, best: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred = predictions[predictions.model == best].set_index("row_index")
    joined = data.join(pred[["predicted", "residual"]], how="inner")
    variables = [
        ("B4_prediction_magnitude", "predicted"), ("focal_recent_absolute_path", "focal_recent_absolute_path_m"),
        ("focal_recent_relative_path", "focal_recent_relative_path_m"), ("A1_distance", "focal_A1_distance_m"),
        ("A2_distance", "focal_A2_distance_m"), ("A3_distance", "focal_A3_distance_m"),
        ("mean_A1_A3_attacker_history_path", "mean_A1_A3_recent_absolute_path_m"),
        ("A3_distance_as_local_configuration_scale", "focal_A3_distance_m"),
        ("selected_x_span", "selected_attackers_x_span_m"), ("selected_y_span", "selected_attackers_y_span_m"),
        ("ball_activity", "ball_recent_path_m"), ("focal_depth", "focal_own_goal_depth_m"),
        ("focal_lateral_position", "focal_y_m"),
    ]
    correlations=[]
    for label, column in variables:
        correlations.append({"scope":"overall","group":"ALL","diagnostic":label,"source_column":column,"spearman_rho":p5a.spearman(joined.residual.to_numpy(float),joined[column].to_numpy(float)),"n":len(joined)})
        for match, group in joined.groupby("match_id"):
            correlations.append({"scope":"match","group":match,"diagnostic":label,"source_column":column,"spearman_rho":p5a.spearman(group.residual.to_numpy(float),group[column].to_numpy(float)),"n":len(group)})
    distributions=[]
    for scope,column in [("match","match_id"),("defending_team","defending_team_id"),("focal_player","focal_player_id")]:
        for name,group in joined.groupby(column):
            distributions.append({"scope":scope,"group":name,"n":len(group),"mean_residual":float(group.residual.mean()),"median_residual":float(group.residual.median()),"residual_sd":float(group.residual.std(ddof=0)),"mean_absolute_residual":float(group.residual.abs().mean())})
    return pd.DataFrame(correlations),pd.DataFrame(distributions)


def make_figures(primary: dict[str,pd.DataFrame], summary: pd.DataFrame, adjacent: pd.DataFrame, calibration: pd.DataFrame, residual_groups: pd.DataFrame, k1_eval: pd.DataFrame, control_eval: pd.DataFrame, best: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    eval_=primary["evaluation"]
    fig,ax=plt.subplots(figsize=(10,5.5))
    for match,group in eval_.groupby("outer_heldout_match"):
        ordered=group.set_index("model").loc[["B4","B5","B6","B7"]]
        ax.plot(["B4","B5","B6","B7"],ordered.MAE,marker="o",alpha=.7,label=match)
    ax.set(xlabel="Frozen ladder level",ylabel="Held-out MAE (m)",title="Phase 5B held-out MAE by match"); ax.grid(alpha=.2); ax.legend(ncol=4,fontsize=7); fig.tight_layout(); fig.savefig(FIGURE_DIR/"heldout_mae_by_match.png",dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.8)); labels=[f"{a}→{b}" for a,b in zip(adjacent.prior,adjacent.current)]
    ax.bar(labels,100*adjacent.median_relative_MAE_improvement,color=["#2f6b8a" if x else "#999999" for x in adjacent.materiality_pass]); ax.axhline(3,color="black",ls="--",lw=1); ax.set(ylabel="Median MAE improvement (%)",title="Frozen adjacent opponent-information increments"); fig.tight_layout(); fig.savefig(FIGURE_DIR/"adjacent_improvements.png",dpi=180); plt.close(fig)
    cal=calibration[(calibration.model==best)&(calibration.bin.astype(str)!="ALL")]
    fig,ax=plt.subplots(figsize=(7,6))
    for match,g in cal.groupby("outer_heldout_match"): ax.plot(g.predicted_mean,g.observed_mean,marker="o",alpha=.7,label=match)
    lo=min(cal.predicted_mean.min(),cal.observed_mean.min()); hi=max(cal.predicted_mean.max(),cal.observed_mean.max()); ax.plot([lo,hi],[lo,hi],color="black",lw=1); ax.set(xlabel="Predicted bin mean (m)",ylabel="Observed bin mean (m)",title=f"Held-out calibration: {best}"); ax.legend(ncol=2,fontsize=6); fig.tight_layout(); fig.savefig(FIGURE_DIR/"best_model_calibration.png",dpi=180); plt.close(fig)
    matches=residual_groups[residual_groups.scope=="match"]
    fig,ax=plt.subplots(figsize=(10,5)); ax.bar(matches.group.astype(str),matches.mean_residual,yerr=matches.residual_sd,color="#5b8aa8",alpha=.8); ax.axhline(0,color="black",lw=1); ax.tick_params(axis="x",rotation=35); ax.set(ylabel="Mean residual ± SD (m)",title=f"Residual distributions by held-out match: {best}"); fig.tight_layout(); fig.savefig(FIGURE_DIR/"best_model_residuals.png",dpi=180); plt.close(fig)
    p=eval_.pivot(index="outer_heldout_match",columns="model",values="MAE"); k=k1_eval.pivot(index="outer_heldout_match",columns="model",values="MAE")
    fig,ax=plt.subplots(figsize=(10,5)); x=np.arange(len(p)); ax.plot(x,p.B7,marker="o",label="K=3 B7"); ax.plot(x,k.K1_B7,marker="o",label="K=1 B7"); ax.set_xticks(x,p.index,rotation=35); ax.set(ylabel="Held-out MAE (m)",title="K=3 versus K=1 representation sensitivity"); ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIGURE_DIR/"k3_vs_k1.png",dpi=180); plt.close(fig)
    c=control_eval.pivot(index="outer_heldout_match",columns="model",values="MAE"); fig,ax=plt.subplots(figsize=(10,5)); x=np.arange(len(c)); ax.plot(x,c.LOCAL_B7,marker="o",label="Local A1–A3 B7"); ax.plot(x,c.NONLOCAL_B7,marker="o",label="Nonlocal A4–A6 B7"); ax.set_xticks(x,c.index,rotation=35); ax.set(ylabel="Held-out MAE (m)",title="Nonlocal-opponent locality control"); ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIGURE_DIR/"local_vs_nonlocal.png",dpi=180); plt.close(fig)


def manifest(stage: str) -> dict[str, Any]:
    paths={
        "phase5b_protocol_md":PROTOCOL_MD,"phase5b_protocol_json":PROTOCOL_JSON,
        "phase5a_source":PHASE5A_SOURCE,"phase5a_protocol_md":PHASE5A_PROTOCOL,"phase5a_protocol_json":PHASE5A_CONFIG,
        "phase4_source":PHASE4_SOURCE,"phase4_protocol_md":PHASE4_PROTOCOL,"phase4_protocol_json":PHASE4_CONFIG,
    }
    return {"stage":stage,"timestamp_utc":datetime.now(timezone.utc).isoformat(),"frozen_commit":FROZEN_COMMIT,"hashes_sha256":{name:sha256(path) for name,path in paths.items()},"implementation_sha256":sha256(Path(__file__)),"clarifications":{"exact_tie_break":"distance_then_provider_player_id_lexical","attacking_outfield_on_pitch":"provider non-goalkeeper with valid exact-cutoff tracking coordinate","projection_tolerance_m":PROJECTION_TOLERANCE_M,"ridge_solver":"Phase 5A NumPy solve with deterministic pseudoinverse fallback","scaling_sd_ddof":0},"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"pandas":pd.__version__,"model_fit":stage=="executed","metrica_game3_accessed":False}


def preflight(raw_dir: Path, cache_dir: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    enriched,common=enrich_rows(raw_dir,cache_dir,50)
    checks={
        "matches_exact":sorted(common.match_id.unique())==sorted(MATCH_IDS),"B5_count":len(G13)==14,"B6_count":len(M13)==9,"B7_count":len(R13)==12,
        "K1_counts":[len(G1),len(M1),len(R1)]==[4,3,4],"feature_times_at_or_before_cutoff":bool((common.opponent_feature_max_raw_time_ns<=common.prediction_cutoff_ns).all()),
        "selection_at_cutoff":bool((common.selection_time_ns==common.prediction_cutoff_ns).all()),"selected_ids_fixed":bool(common.selected_ids_fixed.all()),"dynamic_reranking":False,
        "primary_all_finite":bool(np.isfinite(common[B4+G13+M13+R13+["focal_relative_path_m"]].to_numpy(float)).all()),"projection_tolerance_m":PROJECTION_TOLERANCE_M,
        "near_zero_pairs":int(enriched.near_zero_projection_pairs.fillna(0).sum()),"primary_observations":len(common),"model_fit":False,"metrica_game3_accessed":False,
    }
    positive_checks = ["matches_exact", "B5_count", "B6_count", "B7_count", "K1_counts", "feature_times_at_or_before_cutoff", "selection_at_cutoff", "selected_ids_fixed", "primary_all_finite"]
    checks["passed"]=bool(all(checks[key] for key in positive_checks) and not checks["dynamic_reranking"] and not checks["model_fit"] and not checks["metrica_game3_accessed"])
    if not checks["passed"]: raise RuntimeError(checks)
    attrition_table(enriched).to_csv(OUTPUT_DIR/"preflight_attrition.csv",index=False)
    (OUTPUT_DIR/"preflight_qc.json").write_text(json.dumps(checks,indent=2)+"\n")
    (OUTPUT_DIR/"execution_manifest.json").write_text(json.dumps(manifest("preflight_passed_no_model"),indent=2)+"\n")
    print(json.dumps(checks,indent=2))


def execute(raw_dir: Path, cache_dir: Path) -> None:
    preflight_path=OUTPUT_DIR/"preflight_qc.json"
    if not preflight_path.exists() or not json.loads(preflight_path.read_text()).get("passed"): raise RuntimeError("Passing preflight required")
    enriched,common=enrich_rows(raw_dir,cache_dir,50)
    attrition=attrition_table(enriched)
    # Frozen target reproduction.
    phase4=pd.read_csv(ROOT/"outputs"/"phase4c"/"primary_focal_observations.csv",usecols=["match_id","interval_id","focal_player_id","focal_relative_path_m"])
    reproduced=common[["match_id","interval_id","focal_player_id","focal_relative_path_m"]].merge(phase4,on=["match_id","interval_id","focal_player_id"],suffixes=("_phase5b","_phase4c"),validate="one_to_one")
    max_diff=float(np.max(np.abs(reproduced.focal_relative_path_m_phase5b-reproduced.focal_relative_path_m_phase4c)))
    target_audit={"phase5b_primary_observations":len(common),"matched_phase4c_observations":len(reproduced),"maximum_absolute_target_difference_m":max_diff,"passed":bool(len(reproduced)==len(common) and max_diff<=1e-9)}
    if not target_audit["passed"]: raise RuntimeError(target_audit)
    primary=run_models(common,PRIMARY_FEATURES,"primary_K3_2s")
    summary,adjacent,adjacent_match,classification=summarize_primary(primary["evaluation"])
    best=classification["best_opponent_model"]
    residual_corr,residual_groups=residual_diagnostics(common,primary["predictions"],best)
    k1=run_models(common,K1_FEATURES,"K1_same_primary_sample")
    k1_summary=summarize_sensitivity(k1["evaluation"],["B4","K1_B5","K1_B6","K1_B7"])
    control_data=enriched[enriched.control_complete].copy().reset_index(drop=True)
    if set(control_data.match_id.unique()) != set(MATCH_IDS): raise RuntimeError("Locality control missing a match")
    control=run_models(control_data,CONTROL_FEATURES,"locality_control")
    control_summary=summarize_sensitivity(control["evaluation"],["B4","LOCAL_B5","LOCAL_B6","LOCAL_B7","NONLOCAL_B5","NONLOCAL_B6","NONLOCAL_B7"])
    cp=control["evaluation"].pivot(index="outer_heldout_match",columns="model",values="MAE")
    locality=[]
    for level in (5,6,7):
        local,nonlocal_=f"LOCAL_B{level}",f"NONLOCAL_B{level}"
        for match in cp.index:
            locality.append({"level":f"B{level}","outer_heldout_match":match,"local_MAE":float(cp.loc[match,local]),"nonlocal_MAE":float(cp.loc[match,nonlocal_]),"local_minus_nonlocal_MAE":float(cp.loc[match,local]-cp.loc[match,nonlocal_]),"local_relative_improvement_vs_nonlocal":float((cp.loc[match,nonlocal_]-cp.loc[match,local])/cp.loc[match,nonlocal_])})
    locality=pd.DataFrame(locality)
    ball=common.groupby(["match_id","ball_nearest_selected_category"]).size().reset_index(name="n")
    ball["proportion_within_match"]=ball.n/ball.groupby("match_id").n.transform("sum")
    overall=common.groupby("ball_nearest_selected_category").size().reset_index(name="n"); overall.insert(0,"match_id","ALL"); overall["proportion_within_match"]=overall.n/overall.n.sum(); ball=pd.concat([ball,overall],ignore_index=True)
    # Frozen one-second history sensitivity, independently complete K3 sample; K1 would use its corresponding K3 rows.
    enriched1,common1=enrich_rows(raw_dir,cache_dir,25)
    history1=run_models(common1,PRIMARY_FEATURES,"K3_1s_history_sensitivity")
    history1_summary,history1_adjacent,_,history1_classification=summarize_primary(history1["evaluation"])
    # Outputs.
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    attrition.to_csv(OUTPUT_DIR/"sample_attrition.csv",index=False)
    common[["match_id","interval_id","period","start_ns","prediction_cutoff_ns","defending_team_id","attacking_team_id","focal_player_id","A1_player_id","A2_player_id","A3_player_id"]].to_csv(OUTPUT_DIR/"primary_common_sample_keys.csv",index=False)
    primary["evaluation"].to_csv(OUTPUT_DIR/"primary_heldout_metrics.csv",index=False); summary.to_csv(OUTPUT_DIR/"primary_model_summary.csv",index=False)
    primary["alphas"].to_csv(OUTPUT_DIR/"selected_alphas.csv",index=False); primary["inner"].to_csv(OUTPUT_DIR/"inner_cv_metrics.csv",index=False); primary["predictions"].to_csv(OUTPUT_DIR/"heldout_predictions.csv",index=False)
    adjacent.to_csv(OUTPUT_DIR/"adjacent_materiality.csv",index=False); adjacent_match.to_csv(OUTPUT_DIR/"adjacent_by_match.csv",index=False)
    primary["calibration"][primary["calibration"].model==best].to_csv(OUTPUT_DIR/"best_model_calibration.csv",index=False)
    residual_corr.to_csv(OUTPUT_DIR/"residual_correlations.csv",index=False); residual_groups.to_csv(OUTPUT_DIR/"residual_group_distributions.csv",index=False)
    k1["evaluation"].to_csv(OUTPUT_DIR/"k1_heldout_metrics.csv",index=False); k1_summary.to_csv(OUTPUT_DIR/"k1_model_summary.csv",index=False); k1["alphas"].to_csv(OUTPUT_DIR/"k1_selected_alphas.csv",index=False)
    control["evaluation"].to_csv(OUTPUT_DIR/"locality_control_heldout_metrics.csv",index=False); control_summary.to_csv(OUTPUT_DIR/"locality_control_summary.csv",index=False); locality.to_csv(OUTPUT_DIR/"locality_control_comparison.csv",index=False); control["alphas"].to_csv(OUTPUT_DIR/"locality_control_selected_alphas.csv",index=False)
    ball.to_csv(OUTPUT_DIR/"ball_nearest_diagnostic.csv",index=False)
    history1["evaluation"].to_csv(OUTPUT_DIR/"one_second_history_heldout_metrics.csv",index=False); history1_summary.to_csv(OUTPUT_DIR/"one_second_history_summary.csv",index=False); history1_adjacent.to_csv(OUTPUT_DIR/"one_second_history_adjacent.csv",index=False); history1["alphas"].to_csv(OUTPUT_DIR/"one_second_history_selected_alphas.csv",index=False)
    (OUTPUT_DIR/"target_reproduction_audit.json").write_text(json.dumps(target_audit,indent=2)+"\n")
    result={"classification":classification,"one_second_history_classification":history1_classification,"maximum_claim_if_A":"Prospectively specified opponent-relative information adds reproducible held-out predictive information about future focal-relative movement beyond the tested non-opponent contextual baseline.","inference_rung":"opponent_information_association","nonclaims_preserved":True}
    (OUTPUT_DIR/"classification.json").write_text(json.dumps(result,indent=2)+"\n")
    qc={"protocol_feature_counts":{"B5":len(G13),"B6":len(M13),"B7":len(R13),"K1":[len(G1),len(M1),len(R1)]},"cutoff_firewall":bool((common.opponent_feature_max_raw_time_ns<=common.prediction_cutoff_ns).all()),"selection_at_c":bool((common.selection_time_ns==common.prediction_cutoff_ns).all()),"selected_ids_fixed":bool(common.selected_ids_fixed.all()),"reranking":False,"zero_distance_rule_applied_pairs":int(enriched.near_zero_projection_pairs.fillna(0).sum()),"common_sample_identical_B4_B7":bool(primary["evaluation"].groupby("outer_heldout_match").n.nunique().max()==1),"B4_refit_on_phase5b_sample":True,"outer_folds":int(primary["evaluation"].outer_heldout_match.nunique()),"inner_training_match_folds":6,"training_only_preprocessing":True,"classification_mechanically_reproduced":True,"K1_same_sample":bool(len(common)==sum(k1["evaluation"].query("model=='B4'").n)),"locality_control_affects_classification":False,"target_reproduction":target_audit,"all_actual_solvers":sorted(set(pd.concat([primary["alphas"],k1["alphas"],control["alphas"],history1["alphas"]]).outer_solver)),"metrica_game3_accessed":False}
    qc["passed"]=bool(qc["cutoff_firewall"] and qc["selection_at_c"] and qc["selected_ids_fixed"] and not qc["reranking"] and qc["common_sample_identical_B4_B7"] and qc["outer_folds"]==7 and qc["K1_same_sample"] and target_audit["passed"] and not qc["metrica_game3_accessed"])
    (OUTPUT_DIR/"qc_results.json").write_text(json.dumps(qc,indent=2)+"\n")
    (OUTPUT_DIR/"execution_manifest.json").write_text(json.dumps(manifest("executed"),indent=2)+"\n")
    make_figures(primary,summary,adjacent,primary["calibration"],residual_groups,k1["evaluation"],control["evaluation"],best)
    print(json.dumps(result,indent=2))


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("stage",choices=("preflight","execute")); parser.add_argument("--raw-dir",type=Path,default=ROOT/"data"/"idsse_raw"); parser.add_argument("--cache-dir",type=Path,default=ROOT/"data"/"idsse_cache"); args=parser.parse_args()
    preflight(args.raw_dir,args.cache_dir) if args.stage=="preflight" else execute(args.raw_dir,args.cache_dir)


if __name__=="__main__": main()
