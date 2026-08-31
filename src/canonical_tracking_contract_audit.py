"""Cross-provider audit of the governed canonical Polars tracking contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import polars as pl


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import phase4b_focal_departure_validation as phase4b  # noqa: E402
import phase4c_idsse_external_replication as phase4c  # noqa: E402
from infrastructure.canonical_tracking import (  # noqa: E402
    CANONICAL_SCHEMA,
    CONTRACT_VERSION,
    canonical_schema_dict,
    validate_chunk,
)
from infrastructure import kloppy_idsse_adapter as idsse  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402


OUT = ROOT / "outputs" / "canonical_tracking_contract"
METRICA_INTERVAL_ID = "G1_P1_590.00_5s"
METRICA_FOCAL = "2"
POSITION_TOLERANCE_M = 1e-4
PATH_TOLERANCE_M = 1e-3
REQUIRED_PROVENANCE = {
    "contract_version",
    "adapter_version",
    "provider",
    "provider_match_id",
    "canonical_match_id",
    "kloppy_version",
    "source_files",
    "source_coordinate_system",
    "canonical_coordinate_system",
    "coordinate_transform",
    "pitch_m",
    "provider_raw_timestamp_available",
    "provider_frame_id_available",
    "time_period_rule",
    "time_match_rule",
    "team_id_map_provider_to_canonical",
    "player_id_map_provider_to_canonical",
    "goalkeeper_source",
    "ball_object_id_provider",
    "ball_state_available",
    "possession_team_available",
    "support_rule",
    "orientation_metadata",
    "coordinates_attacking_direction_normalized",
    "interpolation_used",
    "transformation_log",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_chunks(chunks, expected_rows_per_frame: int, selected_frames: set[tuple[int, str]]) -> tuple[dict, pl.DataFrame, pl.DataFrame]:
    rows = 0
    frames = 0
    last_match_time = float("-inf")
    last_period_times: dict[int, float] = {}
    selected = []
    sample = None
    support_states: set[str] = set()
    coordinate_outside_pitch = 0
    ball_rows = 0
    ball_present = 0
    selected_keys = [f"{period}:{frame_id}" for period, frame_id in selected_frames]
    for chunk in chunks:
        validate_chunk(chunk)
        if sample is None:
            sample = chunk.head(expected_rows_per_frame * 3)
        frame_table = chunk.select(
            ["period", "frame_id_provider", "time_period_s", "time_match_s"]
        ).unique(maintain_order=True)
        counts = chunk.group_by(["period", "frame_id_provider"]).len()
        if counts.filter(pl.col("len") != expected_rows_per_frame).height:
            raise ValueError("Canonical frame does not contain every roster entity plus ball")
        for period, frame_id, time_period, time_match in frame_table.iter_rows():
            period = int(period)
            if float(time_match) <= last_match_time:
                raise ValueError("time_match_s is not strictly increasing")
            if period in last_period_times and float(time_period) <= last_period_times[period]:
                raise ValueError("time_period_s is not strictly increasing within period")
            last_match_time = float(time_match)
            last_period_times[period] = float(time_period)
        wanted = chunk.filter(
            pl.concat_str([pl.col("period").cast(pl.String), pl.col("frame_id_provider")], separator=":")
            .is_in(selected_keys)
        )
        if wanted.height:
            selected.append(wanted)
        support_states.update(chunk.get_column("support_state").unique().to_list())
        coordinate_outside_pitch += chunk.filter(
            pl.col("coordinate_valid")
            & (
                (pl.col("x_m").abs() > pl.col("pitch_length_m") / 2)
                | (pl.col("y_m").abs() > pl.col("pitch_width_m") / 2)
            )
        ).height
        balls = chunk.filter(pl.col("entity_type") == "ball")
        ball_rows += balls.height
        ball_present += balls.filter(pl.col("coordinate_valid")).height
        rows += chunk.height
        frames += frame_table.height
    if sample is None:
        raise ValueError("No canonical chunks emitted")
    selected_table = pl.concat(selected) if selected else pl.DataFrame(schema=CANONICAL_SCHEMA)
    return (
        {
            "rows": rows,
            "frames": frames,
            "rows_per_frame": expected_rows_per_frame,
            "last_match_time_s": last_match_time,
            "support_states": sorted(support_states),
            "coordinate_rows_outside_nominal_pitch": coordinate_outside_pitch,
            "ball_rows": ball_rows,
            "ball_coordinate_valid_rows": ball_present,
            "schema_exact": sample.schema == CANONICAL_SCHEMA,
        },
        sample,
        selected_table,
    )


def selected_positions(
    table: pl.DataFrame,
    period: int,
    frame_ids: list[int],
    player_keys: list[str],
    historical_metrica_axes: bool,
) -> dict[str, np.ndarray]:
    order = {str(frame): index for index, frame in enumerate(frame_ids)}
    result = {}
    for key in player_keys:
        rows = table.filter(
            (pl.col("period") == period)
            & (pl.col("player_key") == key)
            & pl.col("frame_id_provider").is_in(list(order))
        ).select(["frame_id_provider", "x_m", "y_m"])
        if rows.height != len(frame_ids):
            raise ValueError(f"Incomplete canonical selection for {key}")
        values = sorted(rows.iter_rows(), key=lambda row: order[row[0]])
        xy = np.asarray([[row[1], row[2]] for row in values], dtype=float)
        if historical_metrica_axes:
            xy[:, 0] += 52.5
            xy[:, 1] = 34.0 - xy[:, 1]
        result[key] = xy
    return result


def compare_selected_geometry(
    provider: str,
    current_interval: dict,
    control_interval: dict,
    canonical_table: pl.DataFrame,
    period: int,
    frame_ids: list[int],
    control_frame_ids: list[int],
    focal_provider_id: str,
    provider_player_ids: list[str],
    canonical_keys: dict[str, str],
    historical_metrica_axes: bool,
) -> list[dict]:
    all_frames = frame_ids + control_frame_ids
    positions = selected_positions(
        canonical_table,
        period,
        all_frames,
        [canonical_keys[player] for player in provider_player_ids],
        historical_metrica_axes,
    )
    n = len(frame_ids)
    canonical_primary = {
        player: positions[canonical_keys[player]][:n] for player in provider_player_ids
    }
    canonical_control = {
        player: positions[canonical_keys[player]][n:] for player in provider_player_ids
    }
    others = [player for player in provider_player_ids if player != focal_provider_id]
    current_loo = phase4c.smooth_xy(
        np.stack([current_interval["positions"][player] for player in others]).mean(axis=0), 7
    )
    canonical_loo = phase4c.smooth_xy(
        np.stack([canonical_primary[player] for player in others]).mean(axis=0), 7
    )
    current_focal = phase4c.smooth_xy(current_interval["positions"][focal_provider_id], 7)
    canonical_focal = phase4c.smooth_xy(canonical_primary[focal_provider_id], 7)
    current_relative = current_focal - current_loo
    canonical_relative = canonical_focal - canonical_loo
    current_control_loo = phase4c.smooth_xy(
        np.stack([control_interval["positions"][player] for player in others]).mean(axis=0), 7
    )
    canonical_control_loo = phase4c.smooth_xy(
        np.stack([canonical_control[player] for player in others]).mean(axis=0), 7
    )
    return [
        {
            "provider": provider,
            "quantity": "leave_one_out_centroid_components_m",
            "max_absolute_difference": float(np.nanmax(np.abs(current_loo - canonical_loo))),
            "tolerance": POSITION_TOLERANCE_M,
        },
        {
            "provider": provider,
            "quantity": "focal_relative_components_m",
            "max_absolute_difference": float(np.nanmax(np.abs(current_relative - canonical_relative))),
            "tolerance": POSITION_TOLERANCE_M,
        },
        {
            "provider": provider,
            "quantity": "focal_relative_path_m",
            "max_absolute_difference": abs(phase4c.path_length(current_relative) - phase4c.path_length(canonical_relative)),
            "tolerance": PATH_TOLERANCE_M,
        },
        {
            "provider": provider,
            "quantity": "frozen_misaligned_control_path_m",
            "max_absolute_difference": abs(
                phase4c.path_length(current_focal - current_control_loo)
                - phase4c.path_length(canonical_focal - canonical_control_loo)
            ),
            "tolerance": PATH_TOLERANCE_M,
        },
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Historical Metrica selections are resolved before canonical construction.
    metrica_current = phase4b.load_match(1)
    cfg = json.loads((ROOT / "config" / "phase4a_focal_departure_validation_protocol.json").read_text())
    _, metrica_intervals, _ = phase4b.build_intervals(metrica_current, cfg, seconds=5.0, smoothing=7)
    metrica_by_id = {interval["interval_id"]: interval for interval in metrica_intervals}
    metrica_pairs = phase4b.misaligned_pairs(metrica_intervals, cfg)
    metrica_interval = metrica_by_id[METRICA_INTERVAL_ID]
    metrica_control = metrica_pairs[METRICA_INTERVAL_ID]
    metrica_frame_ids = metrica_current["tracking"].loc[
        (metrica_current["tracking"]["Period"] == 1)
        & (metrica_current["tracking"]["Time [s]"] >= 590)
        & (metrica_current["tracking"]["Time [s]"] < 595),
        "Frame",
    ].astype(int).tolist()
    metrica_control_frame_ids = metrica_current["tracking"].loc[
        (metrica_current["tracking"]["Period"] == 1)
        & (metrica_current["tracking"]["Time [s]"] >= metrica_control["start_s"])
        & (metrica_current["tracking"]["Time [s]"] < metrica_control["start_s"] + 5),
        "Frame",
    ].astype(int).tolist()
    metrica_selected_frames = {(1, str(frame)) for frame in metrica_frame_ids + metrica_control_frame_ids}

    home_path, away_path = metrica.game1_paths(ROOT)
    metrica_index = metrica.read_provider_frame_index(home_path)
    metrica_dataset = metrica.load_dataset(home_path, away_path)
    metrica_provenance = metrica.canonical_provenance(metrica_dataset, home_path, away_path)
    metrica_summary, metrica_sample, metrica_selected = audit_chunks(
        metrica.iter_canonical_polars_chunks(metrica_dataset, metrica_index, frames_per_chunk=1000),
        expected_rows_per_frame=29,
        selected_frames=metrica_selected_frames,
    )
    metrica_keys = {
        player: metrica.canonical_player_key("Home", player) for player in metrica_interval["players"]
    }
    downstream_rows = compare_selected_geometry(
        "metrica",
        metrica_interval,
        metrica_control,
        metrica_selected,
        1,
        metrica_frame_ids,
        metrica_control_frame_ids,
        METRICA_FOCAL,
        metrica_interval["players"],
        metrica_keys,
        True,
    )

    # Historical IDSSE selections are likewise fixed from Phase 4C first.
    metadata_path, event_path, tracking_path = idsse.idsse_paths(ROOT, "J03WMX")
    idsse_metadata = phase4c.read_metadata(metadata_path)
    idsse_events = phase4c.read_events(event_path)
    idsse_current = phase4c.load_tracking_cache(ROOT / "data" / "idsse_cache" / "J03WMX_raw_tracking.npz")
    idsse_intervals = phase4c.eligible_raw_intervals(idsse_metadata, idsse_events, idsse_current, 5)
    phase4c.interval_activity(idsse_intervals, 7)
    phase4c.assign_collective_rank_bins(idsse_intervals)
    idsse_pairs = phase4c.select_misaligned(idsse_intervals)
    idsse_interval = idsse_intervals[0]
    idsse_control = idsse_pairs[idsse_interval["interval_id"]]
    idsse_period = idsse_interval["period"]
    idsse_period_number = 1 if idsse_period == "firstHalf" else 2
    period_data = idsse_current[idsse_period]
    idsse_idx = np.flatnonzero(
        (period_data["time_ns"] >= idsse_interval["start_ns"])
        & (period_data["time_ns"] < idsse_interval["start_ns"] + 5_000_000_000)
    )
    idsse_control_idx = np.flatnonzero(
        (period_data["time_ns"] >= idsse_control["start_ns"])
        & (period_data["time_ns"] < idsse_control["start_ns"] + 5_000_000_000)
    )
    idsse_frame_ids = period_data["frame_n"][idsse_idx].astype(int).tolist()
    idsse_control_frame_ids = period_data["frame_n"][idsse_control_idx].astype(int).tolist()
    idsse_selected_frames = {
        (idsse_period_number, str(frame)) for frame in idsse_frame_ids + idsse_control_frame_ids
    }
    idsse_sidecar = idsse.read_ball_frame_sidecar(tracking_path)
    idsse_dataset = idsse.load_dataset(metadata_path, tracking_path)
    idsse_provenance = idsse.canonical_provenance(
        idsse_dataset, idsse_sidecar, metadata_path, event_path, tracking_path
    )
    idsse_summary, idsse_sample, idsse_selected = audit_chunks(
        idsse.iter_canonical_polars_chunks(idsse_dataset, idsse_sidecar, frames_per_chunk=1000),
        expected_rows_per_frame=41,
        selected_frames=idsse_selected_frames,
    )
    idsse_keys = {player: idsse.canonical_player_key(player) for player in idsse_interval["players"]}
    idsse_focal = idsse_interval["players"][0]
    downstream_rows.extend(
        compare_selected_geometry(
            "idsse",
            idsse_interval,
            idsse_control,
            idsse_selected,
            idsse_period_number,
            idsse_frame_ids,
            idsse_control_frame_ids,
            idsse_focal,
            idsse_interval["players"],
            idsse_keys,
            False,
        )
    )

    for provenance in (metrica_provenance, idsse_provenance):
        missing = REQUIRED_PROVENANCE - set(provenance)
        if missing:
            raise ValueError(f"Incomplete provenance for {provenance.get('provider')}: {sorted(missing)}")
        if provenance["contract_version"] != CONTRACT_VERSION:
            raise ValueError("Contract version mismatch")
    downstream = pd.DataFrame(downstream_rows)
    downstream["pass"] = downstream["max_absolute_difference"] <= downstream["tolerance"]
    provider_summary = pd.DataFrame(
        [
            {"provider": "metrica", **metrica_summary},
            {"provider": "idsse_sportec", **idsse_summary},
        ]
    )
    architecture_ready = bool(
        provider_summary["schema_exact"].all()
        and downstream["pass"].all()
        and not metrica_provenance["interpolation_used"]
        and not idsse_provenance["interpolation_used"]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "architecture_decision": "READY" if architecture_ready else "NOT READY",
        "scope": ["Metrica Sample Game 1", "IDSSE/Sportec J03WMX"],
        "canonical_schema": canonical_schema_dict(),
        "provider_summaries": provider_summary.to_dict(orient="records"),
        "downstream_pass": bool(downstream["pass"].all()),
        "provenance_complete": True,
        "support_semantics_explicit": True,
        "time_semantics_resolved": True,
        "coordinate_semantics_resolved": True,
        "historical_pipelines_migrated": False,
        "metrica_game3_accessed": False,
        "unravelsports_used": False,
        "source_sha256": sha256(Path(__file__)),
        "canonical_module_sha256": sha256(ROOT / "src" / "infrastructure" / "canonical_tracking.py"),
    }
    metrica_sample.write_parquet(OUT / "metrica_canonical_sample.parquet")
    idsse_sample.write_parquet(OUT / "idsse_canonical_sample.parquet")
    provider_summary.to_csv(OUT / "provider_contract_summary.csv", index=False)
    downstream.to_csv(OUT / "downstream_equivalence.csv", index=False)
    (OUT / "canonical_schema.json").write_text(json.dumps(canonical_schema_dict(), indent=2) + "\n")
    (OUT / "metrica_provenance.json").write_text(json.dumps(metrica_provenance, indent=2) + "\n")
    (OUT / "idsse_provenance.json").write_text(json.dumps(idsse_provenance, indent=2) + "\n")
    (OUT / "contract_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"architecture_decision": result["architecture_decision"], "downstream_pass": result["downstream_pass"]}, indent=2))


if __name__ == "__main__":
    main()
