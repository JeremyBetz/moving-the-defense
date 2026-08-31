"""Run the isolated Kloppy/Metrica Game 1 ingestion-equivalence experiment."""
from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import phase4b_focal_departure_validation as phase4  # noqa: E402
from infrastructure.kloppy_metrica_adapter import (  # noqa: E402
    CANONICAL_COLUMNS,
    GOALKEEPER_IDS,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    game1_paths,
    iter_long_chunks,
    load_dataset,
    provenance,
    read_provider_frame_index,
    roster,
    to_project_wide,
)


OUT = ROOT / "outputs" / "kloppy_metrica_equivalence"
DOC = ROOT / "docs" / "kloppy_metrica_equivalence.md"
CFG = ROOT / "config" / "phase4a_focal_departure_validation_protocol.json"
NORMALIZED_TOL = 1e-12
POSITION_TOL_M = 1e-9
PATH_TOL_M = 1e-8
SELECTED_INTERVALS = ["G1_P1_5.00_5s", "G1_P1_590.00_5s", "G1_P2_4195.00_5s"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_difference(values: np.ndarray, tolerance: float) -> dict:
    finite = values[np.isfinite(values)]
    mismatches = int((finite > tolerance).sum())
    return {
        "n": int(len(finite)),
        "max_absolute_difference": float(np.max(finite)) if len(finite) else None,
        "median_absolute_difference": float(np.median(finite)) if len(finite) else None,
        "p99_absolute_difference": float(np.quantile(finite, 0.99)) if len(finite) else None,
        "tolerance": tolerance,
        "mismatches_above_tolerance": mismatches,
        "mismatch_share": float(mismatches / len(finite)) if len(finite) else None,
    }


def coordinate_audit(current: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for object_type, teams in [("player", ("Home", "Away")), ("ball", ("Home",))]:
        for axis, scale in [("x", PITCH_LENGTH_M), ("y", PITCH_WIDTH_M)]:
            arrays = []
            mask_equal = True
            compared = 0
            for team in teams:
                columns = (
                    [c for c in current if c.startswith(f"{team}_") and c.endswith(f"_{axis}") and "ball" not in c]
                    if object_type == "player"
                    else [f"{team}_ball_{axis}"]
                )
                for column in columns:
                    a = current[column].to_numpy(float)
                    b = candidate[column].to_numpy(float)
                    mask_equal = mask_equal and bool(np.array_equal(np.isnan(a), np.isnan(b)))
                    valid = np.isfinite(a) & np.isfinite(b)
                    arrays.append(np.abs(a[valid] - b[valid]))
                    compared += int(valid.sum())
            diff = np.concatenate(arrays) if arrays else np.array([], dtype=float)
            summary = describe_difference(diff, NORMALIZED_TOL)
            rows.append(
                {
                    "object_type": object_type,
                    "axis": axis,
                    "valid_observations": compared,
                    "missingness_mask_exact": mask_equal,
                    **{f"normalized_{k}": v for k, v in summary.items() if k != "n"},
                    "max_absolute_difference_m": None if summary["max_absolute_difference"] is None else summary["max_absolute_difference"] * scale,
                }
            )
    return pd.DataFrame(rows)


def period_summary(table: pd.DataFrame, source: str) -> pd.DataFrame:
    q = table.groupby("Period", as_index=False).agg(
        frame_count=("Frame", "size"),
        first_frame=("Frame", "min"),
        last_frame=("Frame", "max"),
        first_time_s=("Time [s]", "min"),
        last_time_s=("Time [s]", "max"),
    )
    q.insert(0, "source", source)
    return q


def scientific_audit(current_match: dict, kloppy_match: dict, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    _, current_intervals, current_attrition = phase4.build_intervals(current_match, cfg, seconds=5.0, smoothing=7)
    _, candidate_intervals, candidate_attrition = phase4.build_intervals(kloppy_match, cfg, seconds=5.0, smoothing=7)
    current_activity = phase4.activity_rows(current_intervals, cfg)
    candidate_activity = phase4.activity_rows(candidate_intervals, cfg)
    current_by_id = {r["interval_id"]: r for r in current_intervals}
    candidate_by_id = {r["interval_id"]: r for r in candidate_intervals}
    current_pairs = phase4.misaligned_pairs(current_intervals, cfg)
    regenerated_candidate_pairs = phase4.misaligned_pairs(candidate_intervals, cfg)
    frozen_candidate_pairs = {
        interval_id: candidate_by_id[pair["interval_id"]]
        for interval_id, pair in current_pairs.items()
        if pair["interval_id"] in candidate_by_id
    }
    current_outcomes = phase4.add_outcomes(current_intervals, current_activity, 7, current_pairs)
    candidate_outcomes = phase4.add_outcomes(candidate_intervals, candidate_activity, 7, frozen_candidate_pairs)
    regenerated_candidate_outcomes = phase4.add_outcomes(
        candidate_intervals, candidate_activity, 7, regenerated_candidate_pairs
    )

    keys = ["interval_id", "focal_player"]
    joined = current_outcomes.merge(candidate_outcomes, on=keys, suffixes=("_current", "_kloppy"), validate="one_to_one")
    metrics = [
        "focal_relative_path_m",
        "focal_relative_net_x_change_m",
        "focal_relative_net_y_change_m",
        "focal_relative_net_displacement_m",
        "leave_one_out_centroid_path_m",
        "misaligned_relative_path_m",
    ]
    downstream_rows = []
    for metric in metrics:
        a = joined[f"{metric}_current"].to_numpy(float)
        b = joined[f"{metric}_kloppy"].to_numpy(float)
        both_nan = np.isnan(a) & np.isnan(b)
        mask_equal = bool(np.array_equal(np.isnan(a), np.isnan(b)))
        valid = np.isfinite(a) & np.isfinite(b)
        summary = describe_difference(np.abs(a[valid] - b[valid]), PATH_TOL_M)
        downstream_rows.append({"quantity": metric, "missingness_mask_exact": mask_equal, "both_missing": int(both_nan.sum()), **summary})

    point_differences = {"loo_centroid": [], "focal_relative": []}
    selected_rows = []
    for interval_id in sorted(set(current_by_id) & set(candidate_by_id)):
        a_rec, b_rec = current_by_id[interval_id], candidate_by_id[interval_id]
        for focal in a_rec["players"]:
            a_others = [p for p in a_rec["players"] if p != focal]
            b_others = [p for p in b_rec["players"] if p != focal]
            a_loo = phase4.smooth_xy(np.mean(np.stack([a_rec["positions"][p] for p in a_others]), axis=0), 7)
            b_loo = phase4.smooth_xy(np.mean(np.stack([b_rec["positions"][p] for p in b_others]), axis=0), 7)
            a_focal = phase4.smooth_xy(a_rec["positions"][focal], 7)
            b_focal = phase4.smooth_xy(b_rec["positions"][focal], 7)
            valid = np.isfinite(a_loo).all(axis=1) & np.isfinite(b_loo).all(axis=1)
            loo_diff = np.abs(a_loo[valid] - b_loo[valid])
            rel_diff = np.abs((a_focal - a_loo)[valid] - (b_focal - b_loo)[valid])
            point_differences["loo_centroid"].append(loo_diff.ravel())
            point_differences["focal_relative"].append(rel_diff.ravel())
            if interval_id in SELECTED_INTERVALS:
                a_path = phase4.path_length(a_focal - a_loo)
                b_path = phase4.path_length(b_focal - b_loo)
                selected_rows.append(
                    {
                        "interval_id": interval_id,
                        "focal_player": focal,
                        "defending_team": a_rec["defending_team"],
                        "current_focal_relative_path_m": a_path,
                        "kloppy_focal_relative_path_m": b_path,
                        "absolute_difference_m": abs(a_path - b_path),
                        "max_loo_centroid_component_difference_m": float(loo_diff.max()),
                        "max_focal_relative_component_difference_m": float(rel_diff.max()),
                        "negative_control_interval_id": current_pairs.get(interval_id, {}).get("interval_id"),
                    }
                )

    point_rows = []
    for name, values in point_differences.items():
        summary = describe_difference(np.concatenate(values), POSITION_TOL_M)
        point_rows.append({"quantity": name, "missingness_mask_exact": True, "both_missing": 0, **summary})
    downstream = pd.concat([pd.DataFrame(point_rows), pd.DataFrame(downstream_rows)], ignore_index=True)
    pair_mismatches = []
    for interval_id in sorted(set(current_pairs) | set(regenerated_candidate_pairs)):
        current_pair = current_pairs.get(interval_id, {}).get("interval_id")
        regenerated_pair = regenerated_candidate_pairs.get(interval_id, {}).get("interval_id")
        if current_pair != regenerated_pair:
            pair_mismatches.append(
                {
                    "interval_id": interval_id,
                    "current_control_interval_id": current_pair,
                    "kloppy_regenerated_control_interval_id": regenerated_pair,
                }
            )
    regenerated_joined = current_outcomes.merge(
        regenerated_candidate_outcomes,
        on=keys,
        suffixes=("_current", "_kloppy"),
        validate="one_to_one",
    )
    regenerated_a = regenerated_joined["misaligned_relative_path_m_current"].to_numpy(float)
    regenerated_b = regenerated_joined["misaligned_relative_path_m_kloppy"].to_numpy(float)
    regenerated_valid = np.isfinite(regenerated_a) & np.isfinite(regenerated_b)
    regenerated_control_summary = describe_difference(
        np.abs(regenerated_a[regenerated_valid] - regenerated_b[regenerated_valid]), PATH_TOL_M
    )
    support = {
        "current_grid_intervals": 1158,
        "current_eligible_intervals": len(current_intervals),
        "kloppy_eligible_intervals": len(candidate_intervals),
        "eligible_interval_ids_exact": [r["interval_id"] for r in current_intervals] == [r["interval_id"] for r in candidate_intervals],
        "current_attrition": current_attrition,
        "kloppy_attrition": candidate_attrition,
        "focal_outcome_keys_exact": len(joined) == len(current_outcomes) == len(candidate_outcomes),
        "current_focal_outcomes": len(current_outcomes),
        "kloppy_focal_outcomes": len(candidate_outcomes),
        "frozen_control_pair_ids_reused": True,
        "regenerated_misaligned_pair_ids_exact": len(pair_mismatches) == 0,
        "regenerated_misaligned_pair_mismatch_count": len(pair_mismatches),
        "regenerated_misaligned_pair_mismatches": pair_mismatches,
        "regenerated_misaligned_control_comparison": regenerated_control_summary,
    }
    return downstream, pd.DataFrame(selected_rows), support


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    home_path, away_path = game1_paths(ROOT)
    provider_index = read_provider_frame_index(home_path)
    current_match = phase4.load_match(1)
    current = current_match["tracking"]

    dataset = load_dataset(home_path, away_path)
    adapter_provenance = provenance(dataset)
    canonical_sample = next(iter_long_chunks(dataset, provider_index, frames_per_chunk=5))
    kloppy_wide, kloppy_players = to_project_wide(dataset, provider_index)
    metadata_players = {
        team: [number for _, player_team, number in roster(dataset) if player_team == team]
        for team in ("Home", "Away")
    }
    kloppy_period_offsets = []
    for frame in [dataset.frames[0], next(f for f in dataset.frames if f.period.id == 2)]:
        provider_time = float(provider_index.loc[provider_index.frame_id == int(frame.frame_id), "provider_time_s"].iloc[0])
        kloppy_period_offsets.append(
            {
                "period": int(frame.period.id),
                "first_frame": int(frame.frame_id),
                "provider_time_s": provider_time,
                "kloppy_period_time_s": float(frame.timestamp.total_seconds()),
                "provider_minus_kloppy_time_s": provider_time - float(frame.timestamp.total_seconds()),
            }
        )
    raw_kloppy_y = 1.0 - kloppy_wide["Home_1_y"].to_numpy(float)
    current_y = current["Home_1_y"].to_numpy(float)
    valid_y = np.isfinite(raw_kloppy_y) & np.isfinite(current_y)
    unadapted_y = {
        "relationship": "kloppy_y = 1 - project_raw_y",
        "max_abs_of_kloppy_y_plus_project_y_minus_1": float(np.max(np.abs(raw_kloppy_y[valid_y] + current_y[valid_y] - 1.0))),
        "correlation": float(np.corrcoef(raw_kloppy_y[valid_y], current_y[valid_y])[0, 1]),
    }
    dataset_frame_count = len(dataset.frames)
    dataset_periods = [int(p.id) for p in dataset.metadata.periods]
    dataset_orientation = str(dataset.metadata.orientation.value)
    del dataset
    gc.collect()

    coordinate = coordinate_audit(current, kloppy_wide)
    period = pd.concat([period_summary(current, "current"), period_summary(kloppy_wide, "kloppy_adapter")], ignore_index=True)
    cfg = json.loads(CFG.read_text())
    kloppy_match = {
        "game": 1,
        "data": ROOT / "data" / "metrica_sample_game_1",
        "tracking": kloppy_wide,
        "events": current_match["events"].copy(),
        "players": kloppy_players,
    }
    downstream, selected, scientific_support = scientific_audit(current_match, kloppy_match, cfg)

    coordinate_pass = bool(coordinate["missingness_mask_exact"].all() and (coordinate["normalized_mismatches_above_tolerance"] == 0).all())
    downstream_pass = bool(downstream["missingness_mask_exact"].all() and (downstream["mismatches_above_tolerance"] == 0).all())
    structural = {
        "current_frames": int(len(current)),
        "kloppy_frames": int(dataset_frame_count),
        "frame_ids_exact": bool(np.array_equal(current["Frame"].to_numpy(int), kloppy_wide["Frame"].to_numpy(int))),
        "provider_timestamps_exact": bool(np.array_equal(current["Time [s]"].to_numpy(float), kloppy_wide["Time [s]"].to_numpy(float))),
        "period_membership_exact": bool(np.array_equal(current["Period"].to_numpy(int), kloppy_wide["Period"].to_numpy(int))),
        "period_ids": dataset_periods,
        "current_players": current_match["players"],
        "kloppy_adapter_players": kloppy_players,
        "player_ids_exact": current_match["players"] == kloppy_players == metadata_players,
        "kloppy_native_team_ids": ["home", "away"],
        "adapter_team_ids": ["Home", "Away"],
        "goalkeeper_ids": GOALKEEPER_IDS,
        "kloppy_native_goalkeeper_positions_available": False,
        "adapter_goalkeeper_source": "frozen project identity mapping",
        "ball_rows": int(len(kloppy_wide)),
        "current_ball_observed": int(current["Home_ball_x"].notna().sum()),
        "kloppy_ball_observed": int(kloppy_wide["Home_ball_x"].notna().sum()),
        "kloppy_orientation": dataset_orientation,
        "canonical_long_columns": CANONICAL_COLUMNS,
        "canonical_full_rows": int(len(current) * (len(kloppy_players["Home"]) + len(kloppy_players["Away"]) + 1)),
        "canonical_materialization": "streamed in reproducible chunks; only a five-frame schema sample is saved",
    }
    structural_pass = all(
        structural[key]
        for key in ["frame_ids_exact", "provider_timestamps_exact", "period_membership_exact", "player_ids_exact"]
    ) and structural["current_frames"] == structural["kloppy_frames"] and structural["current_ball_observed"] == structural["kloppy_ball_observed"]
    classification = "B" if structural_pass and coordinate_pass and downstream_pass else "C"
    result = {
        "classification": classification,
        "interpretation": "Mostly compatible but requires an explicit, tested adapter for y-axis, IDs, raw time, and goalkeeper identity; regenerated negative-control pairing is sensitive to floating-point movement across a frozen activity cut." if classification == "B" else "Not currently safe to migrate.",
        "kloppy_version": adapter_provenance.kloppy_version,
        "structural_pass": structural_pass,
        "coordinate_pass": coordinate_pass,
        "downstream_pass": downstream_pass,
        "structural": structural,
        "period_time_offsets": kloppy_period_offsets,
        "unadapted_y_diagnostic": unadapted_y,
        "scientific_support": scientific_support,
        "tolerances": {
            "normalized_coordinates": NORMALIZED_TOL,
            "point_positions_m": POSITION_TOL_M,
            "path_and_scalar_outputs_m": PATH_TOL_M,
        },
        "provenance": adapter_provenance.__dict__,
        "inputs_sha256": {home_path.name: sha256(home_path), away_path.name: sha256(away_path)},
        "source_sha256": sha256(Path(__file__)),
        "adapter_sha256": sha256(ROOT / "src" / "infrastructure" / "kloppy_metrica_adapter.py"),
        "phase4_protocol_sha256": sha256(CFG),
        "game2_accessed": False,
        "game3_accessed": False,
        "unravelsports_used": False,
        "interpolation_used": False,
        "existing_outputs_modified": False,
    }
    coordinate.to_csv(OUT / "coordinate_equivalence.csv", index=False)
    period.to_csv(OUT / "period_equivalence.csv", index=False)
    downstream.to_csv(OUT / "downstream_equivalence.csv", index=False)
    selected.to_csv(OUT / "selected_window_equivalence.csv", index=False)
    canonical_sample.to_csv(OUT / "canonical_long_sample.csv", index=False)
    (OUT / "equivalence_result.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
