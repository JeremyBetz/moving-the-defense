"""Execute frozen Phase 5A contextual-expectation feasibility protocol v1.0.

The preflight stage constructs only eligibility, feature completeness, temporal
support, and leakage audits. The execute stage constructs the frozen target and
runs the fixed B0--B4 nested match-heldout pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phase4c_idsse_external_replication import (
    MATCH_IDS,
    PERIODS,
    eligible_raw_intervals,
    find_file,
    load_tracking_cache,
    read_events,
    read_metadata,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_MD = ROOT / "docs" / "phase5a_contextual_expectation_protocol.md"
PROTOCOL_JSON = ROOT / "config" / "phase5a_contextual_expectation_protocol.json"
PHASE4_SOURCE = ROOT / "src" / "phase4c_idsse_external_replication.py"
PHASE4_PROTOCOL = ROOT / "docs" / "phase4c_external_replication_protocol.md"
PHASE4_CONFIG = ROOT / "config" / "phase4c_external_replication_protocol.json"
OUTPUT_DIR = ROOT / "outputs" / "phase5a"
FIGURE_DIR = ROOT / "figures" / "phase5a"
ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
LEVELS = ("B0", "B1", "B2", "B3", "B4")
FEATURES = {
    "B1": [
        "focal_recent_absolute_path_m", "focal_recent_relative_path_m",
        "focal_terminal_vx_mps", "focal_terminal_vy_mps",
        "focal_relative_terminal_vx_mps", "focal_relative_terminal_vy_mps",
    ],
    "B2": [
        "focal_recent_absolute_path_m", "focal_recent_relative_path_m",
        "focal_terminal_vx_mps", "focal_terminal_vy_mps",
        "focal_relative_terminal_vx_mps", "focal_relative_terminal_vy_mps",
        "loo_centroid_recent_path_m", "loo_centroid_terminal_vx_mps",
        "loo_centroid_terminal_vy_mps", "other_defenders_recent_mean_path_m",
    ],
    "B3": [
        "focal_recent_absolute_path_m", "focal_recent_relative_path_m",
        "focal_terminal_vx_mps", "focal_terminal_vy_mps",
        "focal_relative_terminal_vx_mps", "focal_relative_terminal_vy_mps",
        "loo_centroid_recent_path_m", "loo_centroid_terminal_vx_mps",
        "loo_centroid_terminal_vy_mps", "other_defenders_recent_mean_path_m",
        "ball_x_m", "ball_y_m", "ball_terminal_vx_mps", "ball_terminal_vy_mps",
        "ball_recent_path_m", "focal_minus_ball_x_m", "focal_minus_ball_y_m",
        "focal_ball_distance_m",
    ],
    "B4": [
        "focal_recent_absolute_path_m", "focal_recent_relative_path_m",
        "focal_terminal_vx_mps", "focal_terminal_vy_mps",
        "focal_relative_terminal_vx_mps", "focal_relative_terminal_vy_mps",
        "loo_centroid_recent_path_m", "loo_centroid_terminal_vx_mps",
        "loo_centroid_terminal_vy_mps", "other_defenders_recent_mean_path_m",
        "ball_x_m", "ball_y_m", "ball_terminal_vx_mps", "ball_terminal_vy_mps",
        "ball_recent_path_m", "focal_minus_ball_x_m", "focal_minus_ball_y_m",
        "focal_ball_distance_m", "focal_own_goal_depth_m", "focal_y_m",
        "focal_own_goal_distance_m", "focal_lateral_distance_m",
        "ball_lateral_distance_m",
    ],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def trailing_mean(values: np.ndarray, frames: int = 7) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) < frames or not np.isfinite(values).all():
        return np.empty((0, values.shape[1]), dtype=float)
    sums = np.cumsum(values, axis=0)
    sums[frames:] -= sums[:-frames]
    return sums[frames - 1 :] / frames


def centered_mean(values: np.ndarray, frames: int = 7) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) < frames or not np.isfinite(values).all():
        return np.empty((0, values.shape[1]), dtype=float)
    sums = np.cumsum(values, axis=0)
    sums[frames:] -= sums[:-frames]
    return sums[frames - 1 :] / frames


def path_length(values: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(values, axis=0), axis=1).sum())


def terminal_velocity(values: np.ndarray) -> np.ndarray:
    return (values[-1] - values[-2]) / 0.04


def rank_average(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(float)


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    valid = np.isfinite(x) & np.isfinite(y)
    if valid.sum() < 3:
        return float("nan")
    a, b = rank_average(x[valid]), rank_average(y[valid])
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def standardized_xy(values: np.ndarray, sigma: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return np.column_stack([sigma * values[:, 0] + 52.5, sigma * values[:, 1] + 34.0])


def period_orientation(metadata: dict[str, Any], tracking: dict[str, Any], period: str) -> dict[str, tuple[int, str, float]]:
    data = tracking[period]
    keep = data["time_ns"] <= data["time_ns"][0] + 1_960_000_000
    goalkeeper_rows = []
    for player in metadata["players"].values():
        if not player.goalkeeper:
            continue
        entity = next((e for e in data["entities"] if e["team_id"] == player.team_id and e["person_id"] == player.player_id), None)
        if entity is None:
            continue
        valid = keep & entity["valid"]
        if valid.sum() >= 25:
            goalkeeper_rows.append((player.team_id, player.player_id, float(np.median(entity["x"][valid]))))
    by_team: dict[str, tuple[int, str, float]] = {}
    for team_id, player_id, median_x in goalkeeper_rows:
        sigma = 1 if median_x < 0 else -1
        by_team[team_id] = (sigma, player_id, median_x)
    expected = {metadata["home_team_id"], metadata["away_team_id"]}
    if set(by_team) != expected:
        raise RuntimeError(f"Incomplete goalkeeper orientation in {metadata['match_id']} {period}: {by_team}")
    if len({value[0] for value in by_team.values()}) != 2:
        raise RuntimeError(f"Goalkeepers do not identify opposing orientations: {metadata['match_id']} {period}")
    return by_team


def match_inputs(raw_dir: Path, cache_dir: Path, match_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    metadata = read_metadata(find_file(raw_dir, "metadata", match_id))
    events = read_events(find_file(raw_dir, "events", match_id))
    tracking = load_tracking_cache(cache_dir / f"{match_id}_raw_tracking.npz")
    return metadata, events, tracking


def prepare_rows(raw_dir: Path, cache_dir: Path, history_frames: int, include_target: bool) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    interval_audit: list[dict[str, Any]] = []
    orientation_audit: list[dict[str, Any]] = []
    for match_id in MATCH_IDS:
        metadata, events, tracking = match_inputs(raw_dir, cache_dir, match_id)
        orientations = {period: period_orientation(metadata, tracking, period) for period in PERIODS}
        for period in PERIODS:
            for team, (sigma, goalkeeper, median_x) in orientations[period].items():
                orientation_audit.append({"match_id": match_id, "period": period, "team_id": team, "sigma": sigma, "goalkeeper_id": goalkeeper, "opening_median_x_m": median_x})
        intervals = eligible_raw_intervals(metadata, events, tracking, 5)
        interval_by_period = {period: tracking[period] for period in PERIODS}
        for interval in intervals:
            data = interval_by_period[interval["period"]]
            start_idx = int(np.searchsorted(data["time_ns"], interval["start_ns"]))
            target_idx = np.arange(start_idx, start_idx + 125)
            cutoff_idx = start_idx - 1
            history_idx = np.arange(cutoff_idx - history_frames + 1, cutoff_idx + 1)
            target_times = data["time_ns"][target_idx] if target_idx[-1] < len(data["time_ns"]) else np.array([], dtype=np.int64)
            history_times = data["time_ns"][history_idx] if history_idx[0] >= 0 else np.array([], dtype=np.int64)
            time_ok = (
                len(target_times) == 125 and np.all(np.diff(target_times) == 40_000_000)
                and len(history_times) == history_frames and np.all(np.diff(history_times) == 40_000_000)
                and int(history_times[-1]) < int(target_times[0])
            )
            entity_by_key = {(e["team_id"], e["person_id"]): e for e in data["entities"]}
            ball = next(e for e in data["entities"] if e["team_id"] == "BALL")
            defending_team = interval["defending_team_id"]
            sigma = orientations[interval["period"]][defending_team][0]
            history_complete_players = []
            if time_ok:
                for player in metadata["players"].values():
                    if player.team_id != defending_team or player.goalkeeper:
                        continue
                    entity = entity_by_key.get((defending_team, player.player_id))
                    if entity is not None and entity["valid"][history_idx].all() and entity["valid"][cutoff_idx]:
                        history_complete_players.append(player.player_id)
            ball_history_complete = bool(time_ok and ball["valid"][history_idx].all())
            phase4_focals = interval["players"]
            primary_complete = []
            common_complete = []
            for focal in phase4_focals:
                focal_history_ok = focal in history_complete_players
                other_history = sorted(player for player in history_complete_players if player != focal)
                history_ok = bool(time_ok and focal_history_ok and len(other_history) >= 8)
                if history_ok:
                    primary_complete.append(focal)
                b4_ok = history_ok and ball_history_complete
                if b4_ok:
                    common_complete.append(focal)
                base = {
                    "match_id": match_id, "interval_id": interval["interval_id"], "period": interval["period"],
                    "sequence": interval["sequence"], "start_ns": interval["start_ns"], "start_s": interval["start_s"],
                    "attacking_team_id": interval["attacking_team_id"], "defending_team_id": defending_team,
                    "focal_player_id": focal, "history_frames": history_frames,
                    "prediction_cutoff_ns": int(history_times[-1]) if len(history_times) else -1,
                    "feature_max_raw_time_ns": int(history_times[-1]) if len(history_times) else -1,
                    "target_min_raw_support_ns": int(target_times[0]) if len(target_times) else -1,
                    "target_max_raw_support_ns": int(target_times[-1]) if len(target_times) else -1,
                    "target_raw_frames": len(target_times), "target_smoothed_positions": 119, "target_path_increments": 118,
                    "history_raw_frames": len(history_times), "history_smoothed_positions": max(0, len(history_times) - 6),
                    "history_path_increments": max(0, len(history_times) - 7), "history_reference_count": len(other_history),
                    "target_reference_count": len(phase4_focals) - 1, "history_target_membership_equal": set(other_history) == (set(phase4_focals) - {focal}),
                    "history_complete": history_ok, "ball_history_complete": ball_history_complete, "B4_complete": b4_ok,
                }
                if not b4_ok:
                    rows.append(base)
                    continue
                focal_entity = entity_by_key[(defending_team, focal)]
                raw_focal_hist = standardized_xy(np.column_stack([focal_entity["x"][history_idx], focal_entity["y"][history_idx]]), sigma)
                raw_other_hist = [standardized_xy(np.column_stack([entity_by_key[(defending_team, p)]["x"][history_idx], entity_by_key[(defending_team, p)]["y"][history_idx]]), sigma) for p in other_history]
                raw_centroid_hist = np.mean(np.stack(raw_other_hist), axis=0)
                raw_ball_hist = standardized_xy(np.column_stack([ball["x"][history_idx], ball["y"][history_idx]]), sigma)
                focal_sm, centroid_sm, ball_sm = trailing_mean(raw_focal_hist), trailing_mean(raw_centroid_hist), trailing_mean(raw_ball_hist)
                other_sm = [trailing_mean(value) for value in raw_other_hist]
                relative_sm = focal_sm - centroid_sm
                focal_now, ball_now = raw_focal_hist[-1], raw_ball_hist[-1]
                delta = focal_now - ball_now
                features = {
                    "focal_recent_absolute_path_m": path_length(focal_sm),
                    "focal_recent_relative_path_m": path_length(relative_sm),
                    "focal_terminal_vx_mps": terminal_velocity(focal_sm)[0], "focal_terminal_vy_mps": terminal_velocity(focal_sm)[1],
                    "focal_relative_terminal_vx_mps": terminal_velocity(relative_sm)[0], "focal_relative_terminal_vy_mps": terminal_velocity(relative_sm)[1],
                    "loo_centroid_recent_path_m": path_length(centroid_sm),
                    "loo_centroid_terminal_vx_mps": terminal_velocity(centroid_sm)[0], "loo_centroid_terminal_vy_mps": terminal_velocity(centroid_sm)[1],
                    "other_defenders_recent_mean_path_m": float(np.mean([path_length(value) for value in other_sm])),
                    "ball_x_m": ball_now[0], "ball_y_m": ball_now[1],
                    "ball_terminal_vx_mps": terminal_velocity(ball_sm)[0], "ball_terminal_vy_mps": terminal_velocity(ball_sm)[1],
                    "ball_recent_path_m": path_length(ball_sm),
                    "focal_minus_ball_x_m": delta[0], "focal_minus_ball_y_m": delta[1], "focal_ball_distance_m": float(np.linalg.norm(delta)),
                    "focal_own_goal_depth_m": focal_now[0], "focal_y_m": focal_now[1],
                    "focal_own_goal_distance_m": float(np.hypot(focal_now[0], focal_now[1] - 34.0)),
                    "focal_lateral_distance_m": abs(focal_now[1] - 34.0), "ball_lateral_distance_m": abs(ball_now[1] - 34.0),
                }
                if include_target:
                    raw_focal_target = standardized_xy(np.column_stack([focal_entity["x"][target_idx], focal_entity["y"][target_idx]]), sigma)
                    target_others = [p for p in phase4_focals if p != focal]
                    raw_target_centroid = np.mean(np.stack([standardized_xy(np.column_stack([entity_by_key[(defending_team, p)]["x"][target_idx], entity_by_key[(defending_team, p)]["y"][target_idx]]), sigma) for p in target_others]), axis=0)
                    focal_target_sm = centered_mean(raw_focal_target)
                    centroid_target_sm = centered_mean(raw_target_centroid)
                    if len(focal_target_sm) != 119 or len(centroid_target_sm) != 119:
                        raise RuntimeError("Frozen target smoothing count failed")
                    base["focal_relative_path_m"] = path_length(focal_target_sm - centroid_target_sm)
                rows.append({**base, **features})
            interval_audit.append({
                "match_id": match_id, "interval_id": interval["interval_id"], "period": interval["period"],
                "defending_team_id": defending_team, "phase4_eligible_focal_observations": len(phase4_focals),
                "history_complete_focal_observations": len(primary_complete), "ball_history_complete_focal_observations": len(common_complete),
                "B4_complete_focal_observations": len(common_complete), "final_common_comparison_observations": len(common_complete),
            })
    return pd.DataFrame(rows), pd.DataFrame(interval_audit), pd.DataFrame(orientation_audit)


def attrition_table(intervals: pd.DataFrame) -> pd.DataFrame:
    base = intervals.groupby(["match_id", "defending_team_id"], as_index=False).sum(numeric_only=True)
    columns = ["phase4_eligible_focal_observations", "history_complete_focal_observations", "ball_history_complete_focal_observations", "B4_complete_focal_observations", "final_common_comparison_observations"]
    base["B4_retention_percentage"] = 100 * base["B4_complete_focal_observations"] / base["phase4_eligible_focal_observations"]
    by_match = base.groupby("match_id", as_index=False)[columns].sum(); by_match.insert(1, "defending_team_id", "ALL")
    overall = pd.DataFrame([{**{"match_id": "ALL", "defending_team_id": "ALL"}, **{column: int(base[column].sum()) for column in columns}}])
    overall["B4_retention_percentage"] = 100 * overall["B4_complete_focal_observations"] / overall["phase4_eligible_focal_observations"]
    by_match["B4_retention_percentage"] = 100 * by_match["B4_complete_focal_observations"] / by_match["phase4_eligible_focal_observations"]
    return pd.concat([base, by_match, overall], ignore_index=True)


def leakage_audit(rows: pd.DataFrame, history_frames: int) -> dict[str, Any]:
    common = rows[rows["B4_complete"]].copy()
    expected_smoothed = history_frames - 6
    expected_increments = history_frames - 7
    checks = {
        "observations": int(len(common)),
        "feature_at_or_before_cutoff": bool((common["feature_max_raw_time_ns"] <= common["prediction_cutoff_ns"]).all()),
        "cutoff_before_target_raw_support": bool((common["prediction_cutoff_ns"] < common["target_min_raw_support_ns"]).all()),
        "one_frame_gap": bool(((common["target_min_raw_support_ns"] - common["prediction_cutoff_ns"]) == 40_000_000).all()),
        "target_125_119_118": bool(((common["target_raw_frames"] == 125) & (common["target_smoothed_positions"] == 119) & (common["target_path_increments"] == 118)).all()),
        "history_counts": bool(((common["history_raw_frames"] == history_frames) & (common["history_smoothed_positions"] == expected_smoothed) & (common["history_path_increments"] == expected_increments)).all()),
        "minimum_reference_count": bool((common["history_reference_count"] >= 8).all()),
        "target_and_history_membership_stored_separately": True,
        "future_eligibility_predictor": False,
        "future_substitution_membership": False,
        "centered_predictor_smoothing": False,
        "interpolation": False,
        "identity_predictors": False,
    }
    checks["passed"] = bool(all(value for key, value in checks.items() if key not in {"observations", "future_eligibility_predictor", "future_substitution_membership", "centered_predictor_smoothing", "interpolation", "identity_predictors"}) and not any(checks[key] for key in ["future_eligibility_predictor", "future_substitution_membership", "centered_predictor_smoothing", "interpolation", "identity_predictors"]))
    return checks


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> dict[str, Any]:
    means = x.mean(axis=0)
    sds = x.std(axis=0, ddof=0)
    keep = sds > 0
    z = (x[:, keep] - means[keep]) / sds[keep]
    y_mean = float(y.mean())
    matrix = z.T @ z + alpha * np.eye(z.shape[1])
    rhs = z.T @ (y - y_mean)
    try:
        coef = np.linalg.solve(matrix, rhs)
        solver = "solve"
    except np.linalg.LinAlgError:
        coef = np.linalg.pinv(matrix) @ rhs
        solver = "pseudoinverse"
    return {"means": means, "sds": sds, "keep": keep, "coef": coef, "intercept": y_mean, "solver": solver}


def predict_ridge(model: dict[str, Any], x: np.ndarray) -> np.ndarray:
    z = (x[:, model["keep"]] - model["means"][model["keep"]]) / model["sds"][model["keep"]]
    return model["intercept"] + z @ model["coef"]


def metrics(y: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = y - prediction
    denominator = np.sum((y - y.mean()) ** 2)
    return {
        "MAE": float(np.mean(np.abs(error))), "median_absolute_error": float(np.median(np.abs(error))),
        "RMSE": float(np.sqrt(np.mean(error**2))), "R2": float(1 - np.sum(error**2) / denominator) if denominator > 0 else float("nan"),
    }


def choose_alpha(train: pd.DataFrame, features: list[str]) -> tuple[float, pd.DataFrame, dict[float, np.ndarray]]:
    records = []
    predictions: dict[float, list[pd.DataFrame]] = {alpha: [] for alpha in ALPHAS}
    matches = sorted(train["match_id"].unique())
    for heldout in matches:
        inner_train, inner_test = train[train.match_id != heldout], train[train.match_id == heldout]
        x_train, y_train = inner_train[features].to_numpy(float), inner_train["focal_relative_path_m"].to_numpy(float)
        x_test, y_test = inner_test[features].to_numpy(float), inner_test["focal_relative_path_m"].to_numpy(float)
        for alpha in ALPHAS:
            model = fit_ridge(x_train, y_train, alpha)
            pred = predict_ridge(model, x_test)
            records.append({"inner_heldout_match": heldout, "alpha": alpha, "MAE": metrics(y_test, pred)["MAE"], "constant_features_removed": int((~model["keep"]).sum()), "solver": model["solver"]})
            predictions[alpha].append(pd.DataFrame({"row_index": inner_test.index, "prediction": pred}))
    table = pd.DataFrame(records)
    medians = table.groupby("alpha")["MAE"].median()
    minimum = medians.min()
    selected = float(max(alpha for alpha, value in medians.items() if value <= minimum + 1e-6))
    selected_predictions = pd.concat(predictions[selected]).sort_values("row_index")
    return selected, table, {selected: selected_predictions.to_numpy()}


def execute_models(data: pd.DataFrame, history_label: str) -> dict[str, pd.DataFrame | dict[str, Any]]:
    evaluations, inner_records, predictions, calibration = [], [], [], []
    alpha_records = []
    for outer_match in sorted(data["match_id"].unique()):
        train, test = data[data.match_id != outer_match], data[data.match_id == outer_match]
        y_train, y_test = train["focal_relative_path_m"].to_numpy(float), test["focal_relative_path_m"].to_numpy(float)
        b0_prediction = np.full(len(test), np.median(y_train))
        evaluations.append({"history": history_label, "outer_heldout_match": outer_match, "model": "B0", "alpha": np.nan, "n": len(test), **metrics(y_test, b0_prediction)})
        identifiers = test[["interval_id", "defending_team_id", "focal_player_id"]].reset_index(drop=True)
        predictions.append(pd.concat([identifiers, pd.DataFrame({"row_index": test.index, "history": history_label, "outer_heldout_match": outer_match, "model": "B0", "observed": y_test, "predicted": b0_prediction})], axis=1))
        for level in ("B1", "B2", "B3", "B4"):
            features = FEATURES[level]
            alpha, inner, selected_prediction_array = choose_alpha(train, features)
            inner.insert(0, "history", history_label); inner.insert(1, "outer_heldout_match", outer_match); inner.insert(2, "model", level)
            inner_records.append(inner)
            model = fit_ridge(train[features].to_numpy(float), y_train, alpha)
            pred = predict_ridge(model, test[features].to_numpy(float))
            evaluations.append({"history": history_label, "outer_heldout_match": outer_match, "model": level, "alpha": alpha, "n": len(test), **metrics(y_test, pred)})
            alpha_records.append({"history": history_label, "outer_heldout_match": outer_match, "model": level, "selected_alpha": alpha, "outer_constant_features_removed": int((~model["keep"]).sum()), "outer_solver": model["solver"]})
            predictions.append(pd.concat([identifiers.copy(), pd.DataFrame({"row_index": test.index, "history": history_label, "outer_heldout_match": outer_match, "model": level, "observed": y_test, "predicted": pred})], axis=1))
            selected_oof = pd.DataFrame(selected_prediction_array[alpha], columns=["row_index", "prediction"]).sort_values("row_index")
            edges = np.quantile(selected_oof["prediction"], [0, .2, .4, .6, .8, 1], method="linear")
            edges = np.unique(edges)
            if len(edges) < 2:
                bin_ids = np.zeros(len(test), dtype=int)
            else:
                bin_ids = np.clip(np.searchsorted(edges[1:-1], pred, side="right"), 0, len(edges) - 2)
            for bin_id in sorted(np.unique(bin_ids)):
                keep = bin_ids == bin_id
                calibration.append({"history": history_label, "outer_heldout_match": outer_match, "model": level, "bin": int(bin_id) + 1, "realized_bins": max(1, len(edges) - 1), "lower_edge": float(edges[bin_id]) if len(edges) > 1 else float(edges[0]), "upper_edge": float(edges[bin_id + 1]) if len(edges) > 1 else float(edges[0]), "n": int(keep.sum()), "predicted_mean": float(pred[keep].mean()), "predicted_median": float(np.median(pred[keep])), "observed_mean": float(y_test[keep].mean()), "observed_median": float(np.median(y_test[keep]))})
            slope, intercept = np.polyfit(pred, y_test, 1) if np.std(pred) > 0 else (np.nan, np.nan)
            calibration.append({"history": history_label, "outer_heldout_match": outer_match, "model": level, "bin": "ALL", "realized_bins": max(1, len(edges) - 1), "lower_edge": np.nan, "upper_edge": np.nan, "n": len(test), "predicted_mean": float(pred.mean()), "predicted_median": float(np.median(pred)), "observed_mean": float(y_test.mean()), "observed_median": float(np.median(y_test)), "calibration_slope": float(slope), "calibration_intercept": float(intercept)})
    return {"evaluation": pd.DataFrame(evaluations), "inner": pd.concat(inner_records, ignore_index=True), "alphas": pd.DataFrame(alpha_records), "predictions": pd.concat(predictions, ignore_index=True), "calibration": pd.DataFrame(calibration)}


def model_summaries(evaluation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    pivot = evaluation.pivot(index="outer_heldout_match", columns="model", values="MAE")
    summaries = []
    for level in LEVELS:
        values = pivot[level]
        relative = (pivot["B0"] - values) / pivot["B0"]
        summaries.append({"model": level, "median_MAE": float(values.median()), "MAE_min": float(values.min()), "MAE_max": float(values.max()), "MAE_IQR": float(values.quantile(.75) - values.quantile(.25)), "median_relative_improvement_vs_B0": float(relative.median()), "matches_improved_vs_B0": int((values < pivot.B0).sum()), "matches_worsened_10pct_or_more_vs_B0": int((values >= 1.10 * pivot.B0).sum())})
    adjacent = []
    for prior, current in zip(LEVELS[:-1], LEVELS[1:]):
        relative = (pivot[prior] - pivot[current]) / pivot[prior]
        adjacent.append({"prior": prior, "current": current, "median_relative_MAE_improvement": float(relative.median()), "matches_improved": int((pivot[current] < pivot[prior]).sum()), "matches_worsened_10pct_or_more": int((pivot[current] >= 1.10 * pivot[prior]).sum()), "materiality_pass": bool(relative.median() >= .03 and (pivot[current] < pivot[prior]).sum() >= 5 and (pivot[current] >= 1.10 * pivot[prior]).sum() <= 1)})
    summary = pd.DataFrame(summaries)
    adjacent_table = pd.DataFrame(adjacent)
    simple = summary[summary.model != "B0"]
    minimum = simple.median_MAE.min()
    best = next(level for level in ("B1", "B2", "B3", "B4") if float(simple.loc[simple.model == level, "median_MAE"].iloc[0]) <= minimum + 1e-6)
    a_models = simple[(simple.median_relative_improvement_vs_B0 >= .10) & (simple.matches_improved_vs_B0 >= 6) & (simple.matches_worsened_10pct_or_more_vs_B0 <= 1)]
    c = bool((simple.median_relative_improvement_vs_B0 < .03).all() and (simple.matches_improved_vs_B0 < 4).all())
    category = "A" if len(a_models) else ("C" if c else "B")
    classification = {"category": category, "best_simple_model": best, "A_qualifying_models": a_models.model.tolist(), "classification_precedence": ["A", "C", "B"]}
    return summary, adjacent_table, classification


def adjacent_by_match(evaluation: pd.DataFrame) -> pd.DataFrame:
    pivot = evaluation.pivot(index="outer_heldout_match", columns="model", values="MAE")
    rows = []
    for prior, current in zip(LEVELS[:-1], LEVELS[1:]):
        for match in pivot.index:
            rows.append({"prior": prior, "current": current, "outer_heldout_match": match, "prior_MAE": float(pivot.loc[match, prior]), "current_MAE": float(pivot.loc[match, current]), "absolute_MAE_change": float(pivot.loc[match, current] - pivot.loc[match, prior]), "relative_MAE_improvement": float((pivot.loc[match, prior] - pivot.loc[match, current]) / pivot.loc[match, prior])})
    return pd.DataFrame(rows)


def residual_diagnostics(data: pd.DataFrame, predictions: pd.DataFrame, best: str, history: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred = predictions[(predictions.history == history) & (predictions.model == best)].set_index("row_index")
    joined = data.join(pred[["predicted"]], how="inner")
    joined["residual"] = joined.focal_relative_path_m - joined.predicted
    variables = ["focal_recent_absolute_path_m", "loo_centroid_recent_path_m", "other_defenders_recent_mean_path_m", "ball_recent_path_m", "focal_own_goal_depth_m", "focal_lateral_distance_m", "predicted"]
    correlations = []
    for variable in variables:
        correlations.append({"scope": "overall", "group": "ALL", "variable": variable, "spearman_rho": spearman(joined.residual.to_numpy(float), joined[variable].to_numpy(float)), "n": len(joined)})
        for match, group in joined.groupby("match_id"):
            correlations.append({"scope": "match", "group": match, "variable": variable, "spearman_rho": spearman(group.residual.to_numpy(float), group[variable].to_numpy(float)), "n": len(group)})
    distributions = []
    for scope, column in [("match", "match_id"), ("defending_team", "defending_team_id"), ("player", "focal_player_id")]:
        for group_name, group in joined.groupby(column):
            distributions.append({"scope": scope, "group": group_name, "n": len(group), "mean_residual": float(group.residual.mean()), "median_residual": float(group.residual.median()), "residual_sd": float(group.residual.std(ddof=0)), "mean_absolute_residual": float(group.residual.abs().mean())})
    return pd.DataFrame(correlations), pd.DataFrame(distributions)


def figures(evaluation: pd.DataFrame, adjacent: pd.DataFrame, predictions: pd.DataFrame, classification: dict[str, Any], sensitivity_summary: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    primary = evaluation[evaluation.history == "2s"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for match, group in primary.groupby("outer_heldout_match"):
        ordered = group.set_index("model").loc[list(LEVELS)]
        ax.plot(LEVELS, ordered.MAE, marker="o", alpha=.65, label=match)
    ax.set(ylabel="Held-out MAE (m)", xlabel="Frozen ladder level", title="Phase 5A held-out MAE by match")
    ax.legend(ncol=4, fontsize=7); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIGURE_DIR / "heldout_mae_by_match.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = ["#2f6b8a" if value else "#999999" for value in adjacent.materiality_pass]
    ax.bar([f"{a}→{b}" for a,b in zip(adjacent.prior, adjacent.current)], 100*adjacent.median_relative_MAE_improvement, color=colors)
    ax.axhline(3, color="black", linestyle="--", linewidth=1); ax.set(ylabel="Median relative MAE improvement (%)", title="Adjacent ladder increments"); fig.tight_layout(); fig.savefig(FIGURE_DIR / "adjacent_improvement.png", dpi=180); plt.close(fig)
    best = classification["best_simple_model"]
    chosen = predictions[(predictions.history == "2s") & (predictions.model == best)]
    fig, ax = plt.subplots(figsize=(6, 6))
    for match, group in chosen.groupby("outer_heldout_match"):
        ax.scatter(group.predicted, group.observed, s=6, alpha=.25, label=match)
    lo=min(chosen.predicted.min(),chosen.observed.min()); hi=max(chosen.predicted.max(),chosen.observed.max()); ax.plot([lo,hi],[lo,hi],color="black",linewidth=1)
    ax.set(xlabel="Held-out predicted path (m)", ylabel="Observed path (m)", title=f"Observed vs predicted: {best}"); ax.legend(ncol=2,fontsize=6); fig.tight_layout(); fig.savefig(FIGURE_DIR / "observed_vs_predicted_best.png",dpi=180); plt.close(fig)
    chosen = chosen.copy(); chosen["residual"] = chosen.observed - chosen.predicted
    fig, ax = plt.subplots(figsize=(10, 5))
    groups = [group.residual.to_numpy() for _, group in chosen.groupby("outer_heldout_match")]
    labels = [match for match, _ in chosen.groupby("outer_heldout_match")]
    ax.boxplot(groups, tick_labels=labels, showfliers=False); ax.axhline(0, color="black", linewidth=1)
    ax.set(ylabel="Contextual departure residual (m)", title=f"Held-out residual distributions: {best}"); ax.tick_params(axis="x", rotation=35); fig.tight_layout(); fig.savefig(FIGURE_DIR / "residuals_by_match.png",dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sens=sensitivity_summary.set_index("model"); ax.plot(sens.index,sens["2s_median_MAE"],marker="o",label="2 s"); ax.plot(sens.index,sens["1s_median_MAE"],marker="o",label="1 s")
    ax.set(ylabel="Median match-heldout MAE (m)",title="Frozen history sensitivity"); ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIGURE_DIR / "history_sensitivity.png",dpi=180); plt.close(fig)


def manifest(stage: str) -> dict[str, Any]:
    return {
        "stage": stage, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": "d675c8cdd8a0bc16b7e3887d4303c4012a3c1791",
        "protocol_md_sha256": sha256(PROTOCOL_MD), "protocol_json_sha256": sha256(PROTOCOL_JSON),
        "phase4_source_sha256": sha256(PHASE4_SOURCE), "phase4_protocol_sha256": sha256(PHASE4_PROTOCOL), "phase4_config_sha256": sha256(PHASE4_CONFIG),
        "implementation_sha256": sha256(Path(__file__)),
        "clarifications": {"scaling_sd_ddof": 0, "ridge_solver": "numpy solve with deterministic pseudoinverse fallback", "ridge_objective": "sum_squared_error_plus_alpha_times_squared_coefficient_norm"},
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "model_fit": stage == "executed", "metrica_game3_accessed": False,
    }


def preflight(raw_dir: Path, cache_dir: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows, intervals, orientation = prepare_rows(raw_dir, cache_dir, 50, include_target=False)
    attrition = attrition_table(intervals)
    leakage = leakage_audit(rows, 50)
    if not leakage["passed"] or set(rows.loc[rows.B4_complete, "match_id"].unique()) != set(MATCH_IDS):
        raise RuntimeError(f"Preflight failed: {leakage}")
    common_by_match = rows[rows.B4_complete].groupby("match_id").size()
    if (common_by_match < 100).any():
        raise RuntimeError(f"Unexpectedly insufficient common sample: {common_by_match.to_dict()}")
    attrition.to_csv(OUTPUT_DIR / "preflight_attrition.csv", index=False)
    orientation.to_csv(OUTPUT_DIR / "orientation_audit.csv", index=False)
    (OUTPUT_DIR / "preflight_leakage_audit.json").write_text(json.dumps(leakage, indent=2) + "\n")
    (OUTPUT_DIR / "execution_manifest.json").write_text(json.dumps(manifest("preflight_passed_no_target_or_model"), indent=2) + "\n")
    print(json.dumps({"preflight": "passed", "common_by_match": common_by_match.to_dict(), "leakage": leakage}, indent=2))


def execute(raw_dir: Path, cache_dir: Path) -> None:
    if not (OUTPUT_DIR / "preflight_leakage_audit.json").exists():
        raise RuntimeError("Run preflight before execute")
    preflight_audit = json.loads((OUTPUT_DIR / "preflight_leakage_audit.json").read_text())
    if not preflight_audit.get("passed"):
        raise RuntimeError("Preflight did not pass")
    datasets, interval_tables, audits = {}, {}, {}
    for frames, label in ((50, "2s"), (25, "1s")):
        rows, intervals, _ = prepare_rows(raw_dir, cache_dir, frames, include_target=True)
        common = rows[rows.B4_complete].copy().reset_index(drop=True)
        if not np.isfinite(common[[*FEATURES["B4"], "focal_relative_path_m"]].to_numpy(float)).all():
            raise RuntimeError(f"Nonfinite common data: {label}")
        audit = leakage_audit(common, frames)
        if not audit["passed"]:
            raise RuntimeError(f"Leakage audit failed: {label}: {audit}")
        datasets[label], interval_tables[label], audits[label] = common, intervals, audit
    phase4 = pd.read_csv(ROOT / "outputs" / "phase4c" / "primary_focal_observations.csv", usecols=["match_id", "interval_id", "focal_player_id", "focal_relative_path_m"])
    reproduced = datasets["2s"][["match_id", "interval_id", "focal_player_id", "focal_relative_path_m"]].merge(phase4, on=["match_id", "interval_id", "focal_player_id"], suffixes=("_phase5a", "_phase4c"), validate="one_to_one")
    reproduction = {"phase5a_common_observations": len(datasets["2s"]), "matched_phase4c_observations": len(reproduced), "maximum_absolute_target_difference_m": float(np.max(np.abs(reproduced.focal_relative_path_m_phase5a - reproduced.focal_relative_path_m_phase4c))), "passed": bool(len(reproduced) == len(datasets["2s"]) and np.max(np.abs(reproduced.focal_relative_path_m_phase5a - reproduced.focal_relative_path_m_phase4c)) <= 1e-9)}
    if not reproduction["passed"]:
        raise RuntimeError(f"Phase 4 target reproduction failed: {reproduction}")
    (OUTPUT_DIR / "target_reproduction_audit.json").write_text(json.dumps(reproduction, indent=2) + "\n")
    results = {label: execute_models(data, label) for label, data in datasets.items()}
    summaries, adjacents, classifications = {}, {}, {}
    for label in ("2s", "1s"):
        summaries[label], adjacents[label], classifications[label] = model_summaries(results[label]["evaluation"])
    best = classifications["2s"]["best_simple_model"]
    residual_corr, residual_dist = residual_diagnostics(datasets["2s"], results["2s"]["predictions"], best, "2s")
    evaluation = pd.concat([results[x]["evaluation"] for x in ("2s", "1s")], ignore_index=True)
    predictions = pd.concat([results[x]["predictions"] for x in ("2s", "1s")], ignore_index=True)
    alphas = pd.concat([results[x]["alphas"] for x in ("2s", "1s")], ignore_index=True)
    inner = pd.concat([results[x]["inner"] for x in ("2s", "1s")], ignore_index=True)
    calibration = pd.concat([results[x]["calibration"] for x in ("2s", "1s")], ignore_index=True)
    summary = summaries["2s"].merge(summaries["1s"], on="model", suffixes=("_2s", "_1s"))
    sensitivity = pd.DataFrame({"model": summary.model, "2s_median_MAE": summary.median_MAE_2s, "1s_median_MAE": summary.median_MAE_1s})
    evaluation.to_csv(OUTPUT_DIR / "heldout_model_metrics.csv", index=False)
    summaries["2s"].to_csv(OUTPUT_DIR / "primary_model_summary.csv", index=False)
    summaries["1s"].to_csv(OUTPUT_DIR / "sensitivity_model_summary.csv", index=False)
    adjacents["2s"].to_csv(OUTPUT_DIR / "primary_adjacent_materiality.csv", index=False)
    adjacents["1s"].to_csv(OUTPUT_DIR / "sensitivity_adjacent_materiality.csv", index=False)
    adjacent_by_match(results["2s"]["evaluation"]).to_csv(OUTPUT_DIR / "primary_adjacent_by_match.csv", index=False)
    adjacent_by_match(results["1s"]["evaluation"]).to_csv(OUTPUT_DIR / "sensitivity_adjacent_by_match.csv", index=False)
    alphas.to_csv(OUTPUT_DIR / "selected_alphas.csv", index=False)
    inner.to_csv(OUTPUT_DIR / "inner_cv_metrics.csv", index=False)
    calibration.to_csv(OUTPUT_DIR / "calibration.csv", index=False)
    predictions.to_csv(OUTPUT_DIR / "heldout_predictions.csv", index=False)
    residual_corr.to_csv(OUTPUT_DIR / "residual_correlations.csv", index=False)
    residual_dist.to_csv(OUTPUT_DIR / "residual_group_distributions.csv", index=False)
    sensitivity.to_csv(OUTPUT_DIR / "history_sensitivity.csv", index=False)
    attrition_table(interval_tables["2s"]).to_csv(OUTPUT_DIR / "primary_attrition.csv", index=False)
    attrition_table(interval_tables["1s"]).to_csv(OUTPUT_DIR / "sensitivity_attrition.csv", index=False)
    pd.DataFrame([audits["2s"], audits["1s"]], index=["2s", "1s"]).reset_index(names="history").to_csv(OUTPUT_DIR / "leakage_audit.csv", index=False)
    result = {"primary": classifications["2s"], "sensitivity": classifications["1s"], "maximum_claim_if_A": "Future focal-relative path contains reproducibly predictable structure from pre-interval observable context.", "nonclaims_preserved": True}
    (OUTPUT_DIR / "classification.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUTPUT_DIR / "execution_manifest.json").write_text(json.dumps(manifest("executed"), indent=2) + "\n")
    figures(evaluation, adjacents["2s"], predictions, classifications["2s"], sensitivity)
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("preflight", "execute"))
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "idsse_raw")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data" / "idsse_cache")
    args = parser.parse_args()
    preflight(args.raw_dir, args.cache_dir) if args.stage == "preflight" else execute(args.raw_dir, args.cache_dir)


if __name__ == "__main__":
    main()
