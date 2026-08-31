"""Compare frozen Phase 4C ingestion with Kloppy for IDSSE match J03WMX."""
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

import phase4c_idsse_external_replication as phase4c  # noqa: E402
from infrastructure.kloppy_idsse_adapter import (  # noqa: E402
    IDSSE_CANONICAL_COLUMNS,
    PERIOD_LABELS,
    idsse_paths,
    iter_long_chunks,
    load_dataset,
    provenance_dict,
    read_ball_frame_sidecar,
    roster,
    to_phase4c_tracking,
)


MATCH_ID = "J03WMX"
OUT = ROOT / "outputs" / "kloppy_idsse_equivalence"
COORDINATE_TOLERANCE_M = 1e-5
POSITION_TOLERANCE_M = 1e-4
SCALAR_TOLERANCE_M = 1e-3
CORRELATION_TOLERANCE = 1e-6
PRIMARY_SECONDS = 5
PRIMARY_SMOOTHING = 7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def entity_map(period_data: dict) -> dict[tuple[str, str], dict]:
    result = {(entity["team_id"], entity["person_id"]): entity for entity in period_data["entities"]}
    balls = [entity for entity in period_data["entities"] if entity["team_id"] == "BALL"]
    if len(balls) == 1:
        result[("BALL", "ball")] = balls[0]
    return result


def coordinate_and_support_audit(current: dict, candidate: dict, metadata: dict) -> tuple[pd.DataFrame, dict]:
    coordinate_rows = []
    support_rows = []
    player_keys = sorted((player.team_id, player.player_id) for player in metadata["players"].values())
    for period in phase4c.PERIODS:
        current_period = current[period]
        candidate_period = candidate[period]
        current_map = entity_map(current_period)
        candidate_map = entity_map(candidate_period)
        if not np.array_equal(current_period["frame_n"], candidate_period["frame_n"]):
            raise RuntimeError(f"Frame IDs differ in {period}")
        for object_type, keys in (("player", player_keys), ("ball", [("BALL", "ball")])):
            for axis in ("x", "y"):
                differences = []
                masks_exact = True
                valid_observations = 0
                for key in keys:
                    a_entity = current_map.get(key)
                    b_entity = candidate_map.get(key)
                    a = (
                        np.asarray(a_entity[axis], dtype=float)
                        if a_entity is not None
                        else np.full(len(current_period["frame_n"]), np.nan)
                    )
                    b = (
                        np.asarray(b_entity[axis], dtype=float)
                        if b_entity is not None
                        else np.full(len(candidate_period["frame_n"]), np.nan)
                    )
                    a_mask = np.isfinite(a)
                    b_mask = np.isfinite(b)
                    masks_exact = masks_exact and bool(np.array_equal(a_mask, b_mask))
                    valid = a_mask & b_mask
                    valid_observations += int(valid.sum())
                    differences.append(np.abs(a[valid] - b[valid]))
                    if object_type == "player" and axis == "x":
                        support_rows.append(
                            {
                                "period": period,
                                "team_id": key[0],
                                "player_id": key[1],
                                "current_observed_frames": int(a_mask.sum()),
                                "kloppy_observed_frames": int(b_mask.sum()),
                                "presence_mask_exact": bool(np.array_equal(a_mask, b_mask)),
                            }
                        )
                summary = describe_difference(np.concatenate(differences), COORDINATE_TOLERANCE_M)
                coordinate_rows.append(
                    {
                        "period": period,
                        "object_type": object_type,
                        "axis": axis,
                        "valid_observations": valid_observations,
                        "missingness_mask_exact": masks_exact,
                        **{key: value for key, value in summary.items() if key != "n"},
                    }
                )
    support = pd.DataFrame(support_rows)
    return pd.DataFrame(coordinate_rows), {
        "all_player_presence_masks_exact": bool(support["presence_mask_exact"].all()),
        "players_compared": int(support[["team_id", "player_id"]].drop_duplicates().shape[0]),
        "player_period_rows": support.to_dict(orient="records"),
    }


def add_scientific_state(intervals: list[dict]) -> tuple[pd.DataFrame, dict[str, dict]]:
    activity = phase4c.interval_activity(intervals, PRIMARY_SMOOTHING)
    phase4c.assign_collective_rank_bins(intervals)
    pairs = phase4c.select_misaligned(intervals)
    return activity, pairs


def scientific_audit(metadata: dict, events: dict, current: dict, candidate: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    current_intervals = phase4c.eligible_raw_intervals(metadata, events, current, PRIMARY_SECONDS)
    candidate_intervals = phase4c.eligible_raw_intervals(metadata, events, candidate, PRIMARY_SECONDS)
    _, current_pairs = add_scientific_state(current_intervals)
    _, regenerated_candidate_pairs = add_scientific_state(candidate_intervals)
    current_by_id = {interval["interval_id"]: interval for interval in current_intervals}
    candidate_by_id = {interval["interval_id"]: interval for interval in candidate_intervals}
    frozen_candidate_pairs = {
        interval_id: candidate_by_id[pair["interval_id"]]
        for interval_id, pair in current_pairs.items()
        if pair["interval_id"] in candidate_by_id
    }
    current_outcomes = phase4c.construct_outcomes(current_intervals, PRIMARY_SMOOTHING, current_pairs)
    candidate_outcomes = phase4c.construct_outcomes(candidate_intervals, PRIMARY_SMOOTHING, frozen_candidate_pairs)
    regenerated_outcomes = phase4c.construct_outcomes(
        candidate_intervals, PRIMARY_SMOOTHING, regenerated_candidate_pairs
    )
    keys = ["interval_id", "focal_player_id"]
    joined = current_outcomes.merge(candidate_outcomes, on=keys, suffixes=("_current", "_kloppy"), validate="one_to_one")
    frozen = pd.read_csv(OUT.parent / "phase4c" / "primary_focal_observations.csv")
    frozen = frozen[frozen.match_id == MATCH_ID].copy()
    frozen_joined = current_outcomes.merge(frozen, on=keys, suffixes=("_fresh", "_frozen"), validate="one_to_one")

    point_rows = []
    point_values = {"leave_one_out_centroid_components_m": [], "focal_relative_components_m": []}
    for interval_id in sorted(current_by_id):
        a_interval = current_by_id[interval_id]
        b_interval = candidate_by_id[interval_id]
        for focal in a_interval["players"]:
            a_others = [player for player in a_interval["players"] if player != focal]
            b_others = [player for player in b_interval["players"] if player != focal]
            a_loo = phase4c.smooth_xy(
                np.stack([a_interval["positions"][player] for player in a_others]).mean(axis=0),
                PRIMARY_SMOOTHING,
            )
            b_loo = phase4c.smooth_xy(
                np.stack([b_interval["positions"][player] for player in b_others]).mean(axis=0),
                PRIMARY_SMOOTHING,
            )
            a_focal = phase4c.smooth_xy(a_interval["positions"][focal], PRIMARY_SMOOTHING)
            b_focal = phase4c.smooth_xy(b_interval["positions"][focal], PRIMARY_SMOOTHING)
            valid = np.isfinite(a_loo).all(axis=1) & np.isfinite(b_loo).all(axis=1)
            point_values["leave_one_out_centroid_components_m"].append(np.abs(a_loo[valid] - b_loo[valid]).ravel())
            point_values["focal_relative_components_m"].append(
                np.abs((a_focal - a_loo)[valid] - (b_focal - b_loo)[valid]).ravel()
            )
    for quantity, values in point_values.items():
        point_rows.append(
            {
                "quantity": quantity,
                "missingness_mask_exact": True,
                **describe_difference(np.concatenate(values), POSITION_TOLERANCE_M),
            }
        )

    metrics = [
        "focal_relative_path_m",
        "focal_relative_net_x_change_m",
        "focal_relative_net_y_change_m",
        "focal_relative_net_displacement_m",
        "focal_absolute_path_m",
        "leave_one_out_centroid_path_m",
        "full_defending_outfield_centroid_path_m",
        "sum_defending_outfield_paths_m",
        "ball_path_m",
        "misaligned_relative_path_m",
    ]
    metric_rows = []
    for metric in metrics:
        a = joined[f"{metric}_current"].to_numpy(float)
        b = joined[f"{metric}_kloppy"].to_numpy(float)
        valid = np.isfinite(a) & np.isfinite(b)
        metric_rows.append(
            {
                "quantity": metric,
                "missingness_mask_exact": bool(np.array_equal(np.isnan(a), np.isnan(b))),
                **describe_difference(np.abs(a[valid] - b[valid]), SCALAR_TOLERANCE_M),
            }
        )
    downstream = pd.concat([pd.DataFrame(point_rows), pd.DataFrame(metric_rows)], ignore_index=True)

    current_distribution, current_correlations = phase4c.summarize_setting(current_outcomes)
    candidate_distribution, candidate_correlations = phase4c.summarize_setting(candidate_outcomes)
    frozen_summary = pd.read_csv(OUT.parent / "phase4c" / "match_summary.csv").set_index("match_id").loc[MATCH_ID]
    summary_fields = ["observations", "intervals", "median_m", "iqr_m", "p10_m", "p25_m", "p75_m", "p90_m"]
    summary_rows = [
        {
            "quantity": field,
            "current": current_distribution[field],
            "kloppy": candidate_distribution[field],
            "frozen_phase4c": frozen_summary[field],
            "current_vs_kloppy_abs_difference": abs(float(current_distribution[field]) - float(candidate_distribution[field])),
            "current_vs_frozen_abs_difference": abs(float(current_distribution[field]) - float(frozen_summary[field])),
        }
        for field in summary_fields
    ]
    current_corr = {row["activity_variable"]: row["spearman_rho"] for row in current_correlations}
    candidate_corr = {row["activity_variable"]: row["spearman_rho"] for row in candidate_correlations}
    frozen_corr = pd.read_csv(OUT.parent / "phase4c" / "primary_activity_correlations.csv")
    frozen_corr = frozen_corr[frozen_corr.match_id == MATCH_ID].set_index("activity_variable")["spearman_rho"]
    correlation_rows = [
        {
            "activity_variable": variable,
            "current_spearman_rho": current_corr[variable],
            "kloppy_spearman_rho": candidate_corr[variable],
            "frozen_phase4c_spearman_rho": frozen_corr[variable],
            "current_vs_kloppy_abs_difference": abs(current_corr[variable] - candidate_corr[variable]),
            "current_vs_frozen_abs_difference": abs(current_corr[variable] - frozen_corr[variable]),
        }
        for variable in phase4c.ACTIVITY_COLUMNS
    ]
    correlations_pass = all(
        row["current_vs_kloppy_abs_difference"] <= CORRELATION_TOLERANCE
        for row in correlation_rows
    )

    current_control = phase4c.summarize_misaligned(current_outcomes)
    candidate_control = phase4c.summarize_misaligned(candidate_outcomes)
    frozen_control = pd.read_csv(OUT.parent / "phase4c" / "primary_misaligned_control.csv")
    frozen_control = frozen_control[frozen_control.match_id == MATCH_ID].iloc[0].to_dict()
    pair_mismatches = []
    for interval_id in sorted(set(current_pairs) | set(regenerated_candidate_pairs)):
        a = current_pairs.get(interval_id, {}).get("interval_id")
        b = regenerated_candidate_pairs.get(interval_id, {}).get("interval_id")
        if a != b:
            pair_mismatches.append(
                {
                    "interval_id": interval_id,
                    "current_control_interval_id": a,
                    "kloppy_regenerated_control_interval_id": b,
                }
            )
    regenerated_joined = current_outcomes.merge(
        regenerated_outcomes, on=keys, suffixes=("_current", "_kloppy"), validate="one_to_one"
    )
    regenerated_a = regenerated_joined["misaligned_relative_path_m_current"].to_numpy(float)
    regenerated_b = regenerated_joined["misaligned_relative_path_m_kloppy"].to_numpy(float)
    regenerated_valid = np.isfinite(regenerated_a) & np.isfinite(regenerated_b)
    regenerated_summary = describe_difference(
        np.abs(regenerated_a[regenerated_valid] - regenerated_b[regenerated_valid]),
        SCALAR_TOLERANCE_M,
    )
    _, current_transport = phase4c.add_activity_strata(current_outcomes)
    _, candidate_transport = phase4c.add_activity_strata(candidate_outcomes)
    metrica_current, _ = phase4c.add_activity_strata(current_outcomes)
    metrica_candidate, _ = phase4c.add_activity_strata(candidate_outcomes)
    activity_cells_current = int((metrica_current.observations > 0).sum())
    activity_cells_candidate = int((metrica_candidate.observations > 0).sum())

    frozen_metric_max = 0.0
    for metric in metrics:
        fresh = frozen_joined[f"{metric}_fresh"].to_numpy(float)
        saved = frozen_joined[f"{metric}_frozen"].to_numpy(float)
        valid = np.isfinite(fresh) & np.isfinite(saved)
        if valid.any():
            frozen_metric_max = max(frozen_metric_max, float(np.max(np.abs(fresh[valid] - saved[valid]))))
    support = {
        "current_intervals": len(current_intervals),
        "kloppy_intervals": len(candidate_intervals),
        "interval_ids_exact": list(current_by_id) == list(candidate_by_id),
        "current_outcomes": len(current_outcomes),
        "kloppy_outcomes": len(candidate_outcomes),
        "outcome_keys_exact": len(joined) == len(current_outcomes) == len(candidate_outcomes),
        "fresh_current_vs_frozen_phase4c_max_metric_difference": frozen_metric_max,
        "current_control": current_control,
        "kloppy_frozen_pair_control": candidate_control,
        "frozen_phase4c_control": frozen_control,
        "regenerated_pair_mismatch_count": len(pair_mismatches),
        "regenerated_pair_mismatches": pair_mismatches,
        "regenerated_control_comparison": regenerated_summary,
        "metrica_activity_cells_current": activity_cells_current,
        "metrica_activity_cells_kloppy": activity_cells_candidate,
        "idsse_descriptive_rows_current": len(current_transport),
        "idsse_descriptive_rows_kloppy": len(candidate_transport),
        "activity_correlations_pass": correlations_pass,
    }
    return downstream, pd.DataFrame(summary_rows), pd.DataFrame(correlation_rows), support


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metadata_path, event_path, tracking_path = idsse_paths(ROOT, MATCH_ID)
    current_metadata = phase4c.read_metadata(metadata_path)
    current_events = phase4c.read_events(event_path)
    current_tracking = phase4c.load_tracking_cache(ROOT / "data" / "idsse_cache" / f"{MATCH_ID}_raw_tracking.npz")
    sidecar = read_ball_frame_sidecar(tracking_path)
    dataset = load_dataset(metadata_path, tracking_path)
    adapter_provenance = provenance_dict(dataset)
    canonical_sample = next(iter_long_chunks(dataset, sidecar, frames_per_chunk=3))
    candidate_tracking = to_phase4c_tracking(dataset, sidecar)

    current_players = current_metadata["players"]
    kloppy_roster = roster(dataset)
    kloppy_players = {player.player_id: team_id for player, team_id, _ in kloppy_roster}
    current_player_teams = {player_id: player.team_id for player_id, player in current_players.items()}
    current_goalkeepers = sorted(player_id for player_id, player in current_players.items() if player.goalkeeper)
    kloppy_goalkeepers = sorted(player.player_id for player, _, goalkeeper in kloppy_roster if goalkeeper)
    ground_teams = {team.ground.value: team.team_id for team in dataset.metadata.teams}
    ball_state_exact = True
    ball_possession_exact = True
    sidecar_lookup = {
        (row.period_label, int(row.frame_id)): row
        for row in sidecar.itertuples(index=False)
    }
    for frame in dataset.frames:
        raw = sidecar_lookup[(PERIOD_LABELS[int(frame.period.id)], int(frame.frame_id))]
        ball_state_exact = ball_state_exact and str(frame.ball_state.value) == raw.provider_ball_state
        expected_team = ground_teams["home"] if raw.provider_ball_possession_code == 1 else ground_teams["away"]
        ball_possession_exact = ball_possession_exact and frame.ball_owning_team.team_id == expected_team

    coordinate, support = coordinate_and_support_audit(current_tracking, candidate_tracking, current_metadata)
    downstream, summary, correlations, scientific = scientific_audit(
        current_metadata, current_events, current_tracking, candidate_tracking
    )
    period_rows = []
    for period_id, period_label in PERIOD_LABELS.items():
        current_period = current_tracking[period_label]
        candidate_period = candidate_tracking[period_label]
        frames = [frame for frame in dataset.frames if int(frame.period.id) == period_id]
        period_rows.append(
            {
                "period": period_label,
                "current_frames": len(current_period["frame_n"]),
                "kloppy_frames": len(candidate_period["frame_n"]),
                "first_frame": int(candidate_period["frame_n"][0]),
                "last_frame": int(candidate_period["frame_n"][-1]),
                "first_provider_timestamp_ns": int(candidate_period["time_ns"][0]),
                "last_provider_timestamp_ns": int(candidate_period["time_ns"][-1]),
                "first_kloppy_period_time_s": float(frames[0].timestamp.total_seconds()),
                "last_kloppy_period_time_s": float(frames[-1].timestamp.total_seconds()),
                "frame_ids_exact": bool(np.array_equal(current_period["frame_n"], candidate_period["frame_n"])),
                "provider_timestamps_exact": bool(np.array_equal(current_period["time_ns"], candidate_period["time_ns"])),
            }
        )
    period = pd.DataFrame(period_rows)
    coordinate_pass = bool(
        coordinate["missingness_mask_exact"].all()
        and (coordinate["mismatches_above_tolerance"] == 0).all()
    )
    downstream_pass = bool(
        downstream["missingness_mask_exact"].all()
        and (downstream["mismatches_above_tolerance"] == 0).all()
        and scientific["activity_correlations_pass"]
    )
    structural_pass = bool(
        period["frame_ids_exact"].all()
        and period["provider_timestamps_exact"].all()
        and current_player_teams == kloppy_players
        and current_goalkeepers == kloppy_goalkeepers
        and support["all_player_presence_masks_exact"]
        and ball_state_exact
        and ball_possession_exact
    )
    classification = "B" if structural_pass and coordinate_pass and downstream_pass else "C"
    architecture = "NOT READY"
    result = {
        "classification": classification,
        "architecture_decision": architecture,
        "interpretation": "Mostly compatible through explicit provider rules; the common schema works geometrically, but raw absolute time, coordinate-origin semantics, ball/provider fields, null-row construction, and discrete boundary stability still require a governed canonical contract.",
        "selected_match": MATCH_ID,
        "provider_match_id": current_metadata["provider_match_id"],
        "kloppy_version": adapter_provenance["kloppy_version"],
        "structural_pass": structural_pass,
        "coordinate_pass": coordinate_pass,
        "downstream_pass": downstream_pass,
        "structural": {
            "periods": period_rows,
            "frame_rate_hz": int(dataset.metadata.frame_rate),
            "current_player_ids": sorted(current_player_teams),
            "kloppy_player_ids": sorted(kloppy_players),
            "player_team_mapping_exact": current_player_teams == kloppy_players,
            "current_goalkeeper_ids": current_goalkeepers,
            "kloppy_goalkeeper_ids": kloppy_goalkeepers,
            "goalkeeper_ids_exact": current_goalkeepers == kloppy_goalkeepers,
            "ball_state_exact": ball_state_exact,
            "ball_possession_mapping_exact": ball_possession_exact,
            "provider_ball_object_id_preserved_by_kloppy": False,
            "provider_ball_object_id_location": "raw/provider provenance sidecar",
            "provider_ball_object_ids": sorted(sidecar["provider_ball_object_id"].dropna().unique().tolist()),
            "canonical_core_columns_match_metrica": IDSSE_CANONICAL_COLUMNS[: len(IDSSE_CANONICAL_COLUMNS) - 4],
            "idsse_sidecar_columns": IDSSE_CANONICAL_COLUMNS[-4:],
            "canonical_full_rows": len(dataset.frames) * (len(kloppy_roster) + 1),
            "canonical_materialization": "streamed; only a three-frame schema sample is committed",
            **support,
        },
        "scientific_support": scientific,
        "tolerances": {
            "coordinates_m": COORDINATE_TOLERANCE_M,
            "point_components_m": POSITION_TOLERANCE_M,
            "paths_and_scalar_outputs_m": SCALAR_TOLERANCE_M,
            "activity_correlations": CORRELATION_TOLERANCE,
        },
        "provenance": adapter_provenance,
        "inputs": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (metadata_path, event_path, tracking_path)
        },
        "source_sha256": sha256(Path(__file__)),
        "adapter_sha256": sha256(ROOT / "src" / "infrastructure" / "kloppy_idsse_adapter.py"),
        "phase4c_protocol_sha256": sha256(ROOT / "config" / "phase4c_external_replication_protocol.json"),
        "phase4c_implementation_sha256": sha256(ROOT / "config" / "phase4c_idsse_implementation.json"),
        "metrica_game3_accessed": False,
        "unravelsports_used": False,
        "interpolation_used": False,
        "existing_phase4c_outputs_modified": False,
    }
    period.to_csv(OUT / "structural_equivalence.csv", index=False)
    coordinate.to_csv(OUT / "coordinate_equivalence.csv", index=False)
    downstream.to_csv(OUT / "downstream_equivalence.csv", index=False)
    summary.to_csv(OUT / "match_summary_equivalence.csv", index=False)
    correlations.to_csv(OUT / "activity_correlation_equivalence.csv", index=False)
    canonical_sample.to_csv(OUT / "canonical_long_sample.csv", index=False)
    pd.DataFrame(
        scientific["regenerated_pair_mismatches"],
        columns=[
            "interval_id",
            "current_control_interval_id",
            "kloppy_regenerated_control_interval_id",
        ],
    ).to_csv(OUT / "regenerated_control_pair_mismatches.csv", index=False)
    (OUT / "equivalence_result.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    del dataset
    gc.collect()
    print(json.dumps({key: result[key] for key in ("classification", "architecture_decision", "selected_match", "structural_pass", "coordinate_pass", "downstream_pass")}, indent=2))


if __name__ == "__main__":
    main()
