"""Bounded UnravelSports interoperability audit for governed tracking data."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
import polars as pl
from unravel.soccer import KloppyPolarsDataset


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure import kloppy_idsse_adapter as idsse  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402
from infrastructure.unravelsports_compat import (  # noqa: E402
    canonical_to_unravel_reference_view,
)


OUT = ROOT / "outputs" / "unravelsports_interoperability"
FRAME_LIMIT = 250
POSITION_TOLERANCE_M = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _provider_view(
    canonical: pl.DataFrame,
    player_map: dict[str, str],
) -> pl.DataFrame:
    reverse = {canonical_key: provider for provider, canonical_key in player_map.items()}
    return (
        canonical.with_columns(
            pl.col("player_key")
            .replace_strict(reverse, default=None)
            .alias("provider_id")
        )
        .with_columns(
            pl.when(pl.col("entity_type") == "ball")
            .then(pl.lit("ball"))
            .otherwise(pl.col("provider_id"))
            .alias("provider_id")
        )
        .select(
            pl.col("period").cast(pl.Int64).alias("period_id"),
            pl.col("frame_id_provider").cast(pl.Int64).alias("frame_id"),
            "provider_id",
            "entity_type",
            "x_m",
            "y_m",
            "coordinate_valid",
            "support_state",
        )
    )


def _load_unravel(dataset, smoothing: bool) -> tuple[KloppyPolarsDataset, list[str]]:
    caught: list[str] = []
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        converted = KloppyPolarsDataset(
            dataset,
            orient_ball_owning=False,
            add_smoothing=smoothing,
        )
    caught.extend(str(record.message) for record in records)
    return converted, caught


def _interop_summary(
    provider: str,
    canonical: pl.DataFrame,
    provenance: dict,
    unravel: KloppyPolarsDataset,
    warnings_seen: list[str],
    axis_sign_to_canonical: tuple[int, int],
) -> tuple[dict, pl.DataFrame]:
    current = _provider_view(canonical, provenance["player_id_map_provider_to_canonical"])
    other = unravel.data.select(
        pl.col("period_id").cast(pl.Int64),
        pl.col("frame_id").cast(pl.Int64),
        pl.col("id").cast(pl.String).alias("provider_id"),
        pl.col("x").alias("unravel_x_m"),
        pl.col("y").alias("unravel_y_m"),
        "team_id",
        "position_name",
        "ball_state",
        "ball_owning_team_id",
    )
    shared = current.join(other, on=["period_id", "frame_id", "provider_id"], how="inner")
    valid_shared = shared.filter(pl.col("coordinate_valid"))
    raw_dx = (valid_shared["x_m"] - valid_shared["unravel_x_m"]).abs()
    raw_dy = (valid_shared["y_m"] - valid_shared["unravel_y_m"]).abs()
    aligned_dx = (valid_shared["x_m"] - axis_sign_to_canonical[0] * valid_shared["unravel_x_m"]).abs()
    aligned_dy = (valid_shared["y_m"] - axis_sign_to_canonical[1] * valid_shared["unravel_y_m"]).abs()
    raw_max_coordinate_difference = max(float(raw_dx.max() or 0), float(raw_dy.max() or 0))
    aligned_max_coordinate_difference = max(float(aligned_dx.max() or 0), float(aligned_dy.max() or 0))
    canonical_frames = current.select(["period_id", "frame_id"]).unique().height
    unravel_frames = other.select(["period_id", "frame_id"]).unique().height
    result = {
        "provider": provider,
        "frames_requested": FRAME_LIMIT,
        "canonical_frames": canonical_frames,
        "unravelsports_frames": unravel_frames,
        "canonical_rows": current.height,
        "canonical_coordinate_valid_rows": current.filter(pl.col("coordinate_valid")).height,
        "unravelsports_rows": other.height,
        "shared_rows": shared.height,
        "unravelsports_null_xy_rows": other.filter(pl.col("unravel_x_m").is_null() | pl.col("unravel_y_m").is_null()).height,
        "raw_max_shared_coordinate_difference_m": raw_max_coordinate_difference,
        "axis_sign_to_canonical_x": axis_sign_to_canonical[0],
        "axis_sign_to_canonical_y": axis_sign_to_canonical[1],
        "aligned_max_shared_coordinate_difference_m": aligned_max_coordinate_difference,
        "coordinate_tolerance_m": POSITION_TOLERANCE_M,
        "shared_coordinates_pass_after_explicit_axis_mapping": aligned_max_coordinate_difference <= POSITION_TOLERANCE_M,
        "unravelsports_schema": {name: str(dtype) for name, dtype in unravel.data.schema.items()},
        "unravelsports_orientation": str(unravel.settings.orientation.value),
        "warnings": sorted(set(warnings_seen)),
        "possession_inferred": not provenance["possession_team_available"],
        "row_membership_equivalent": current.height == other.height,
        "support_semantics_preserved": False,
        "provenance_sidecar_preserved": False,
    }
    return result, shared


def _project_kinematics(canonical: pl.DataFrame, player_map: dict[str, str]) -> pd.DataFrame:
    reverse = {canonical_key: provider for provider, canonical_key in player_map.items()}
    selected = canonical.filter((pl.col("entity_type") == "player") & pl.col("coordinate_valid"))
    selected = (
        selected
        .with_columns(pl.col("player_key").replace_strict(reverse).alias("provider_id"))
        .select("period", "frame_id_provider", "time_period_s", "provider_id", "x_m", "y_m")
    )
    data = pd.DataFrame(selected.rows(), columns=selected.columns)
    rows = []
    for (period, player), group in data.groupby(["period", "provider_id"], sort=False):
        group = group.sort_values("time_period_s").copy()
        group["sx"] = group["x_m"].rolling(7, center=True, min_periods=7).mean()
        group["sy"] = group["y_m"].rolling(7, center=True, min_periods=7).mean()
        dt = group["time_period_s"].diff()
        group["project_vx"] = group["sx"].diff() / dt
        group["project_vy"] = group["sy"].diff() / dt
        rows.append(group[["period", "frame_id_provider", "provider_id", "project_vx", "project_vy"]])
    return pd.concat(rows, ignore_index=True)


def _kinematics_summary(
    provider: str,
    canonical: pl.DataFrame,
    provenance: dict,
    unravel: KloppyPolarsDataset,
    axis_sign_to_canonical: tuple[int, int],
) -> dict:
    project = _project_kinematics(canonical, provenance["player_id_map_provider_to_canonical"])
    other_selected = (
        unravel.data.filter(pl.col("team_id") != "ball")
        .select("period_id", "frame_id", "id", "vx", "vy", "v")
    )
    other = pd.DataFrame(other_selected.rows(), columns=other_selected.columns).rename(
        columns={"period_id": "period", "frame_id": "frame_id_provider", "id": "provider_id", "vx": "unravel_vx", "vy": "unravel_vy", "v": "unravel_speed"}
    )
    project["frame_id_provider"] = project["frame_id_provider"].astype(int)
    joined = project.merge(other, on=["period", "frame_id_provider", "provider_id"], how="inner").dropna()
    joined["unravel_vx"] *= axis_sign_to_canonical[0]
    joined["unravel_vy"] *= axis_sign_to_canonical[1]
    component_error = np.concatenate(
        [
            (joined["project_vx"] - joined["unravel_vx"]).to_numpy(),
            (joined["project_vy"] - joined["unravel_vy"]).to_numpy(),
        ]
    )
    project_speed = np.hypot(joined["project_vx"], joined["project_vy"])
    return {
        "provider": provider,
        "shared_finite_player_rows": int(len(joined)),
        "component_mae_mps": float(np.mean(np.abs(component_error))),
        "component_max_absolute_difference_mps": float(np.max(np.abs(component_error))),
        "speed_correlation": float(np.corrcoef(project_speed, joined["unravel_speed"])[0, 1]),
        "unravelsports_speed_at_cap_rows": int((joined["unravel_speed"] >= 12.0).sum()),
        "project_rule": "centered 7-frame rolling mean of position, then backward first difference / observed dt",
        "unravelsports_rule": "backward first difference of position, Savitzky-Golay velocity smoothing (window 7, polyorder 1), then acceleration; scalar speed/acceleration capped",
        "exact_substitute": False,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    m_home, m_away = metrica.game1_paths(ROOT)
    m_index = metrica.read_provider_frame_index(m_home)
    m_dataset = metrica.load_dataset(m_home, m_away, limit=FRAME_LIMIT)
    m_canonical = pl.concat(
        metrica.iter_canonical_polars_chunks(m_dataset, m_index, frames_per_chunk=FRAME_LIMIT)
    )
    m_provenance = metrica.canonical_provenance(m_dataset, m_home, m_away)
    m_unravel_raw, m_warnings = _load_unravel(m_dataset, smoothing=False)
    m_axis_sign = (1, -1)
    m_interop, _ = _interop_summary("metrica", m_canonical, m_provenance, m_unravel_raw, m_warnings, m_axis_sign)
    m_unravel_smooth, _ = _load_unravel(m_dataset, smoothing=True)
    m_kinematics = _kinematics_summary("metrica", m_canonical, m_provenance, m_unravel_smooth, m_axis_sign)

    i_meta, i_event, i_tracking = idsse.idsse_paths(ROOT, "J03WMX")
    i_sidecar = idsse.read_ball_frame_sidecar(i_tracking)
    i_dataset = idsse.load_dataset(i_meta, i_tracking, limit=FRAME_LIMIT)
    i_canonical = pl.concat(
        idsse.iter_canonical_polars_chunks(i_dataset, i_sidecar, frames_per_chunk=FRAME_LIMIT)
    )
    i_provenance = idsse.canonical_provenance(i_dataset, i_sidecar, i_meta, i_event, i_tracking)
    i_unravel_raw, i_warnings = _load_unravel(i_dataset, smoothing=False)
    i_axis_sign = (-1, -1)
    i_interop, _ = _interop_summary("idsse_sportec", i_canonical, i_provenance, i_unravel_raw, i_warnings, i_axis_sign)
    i_unravel_smooth, _ = _load_unravel(i_dataset, smoothing=True)
    i_kinematics = _kinematics_summary("idsse_sportec", i_canonical, i_provenance, i_unravel_smooth, i_axis_sign)

    compatibility_samples = pl.concat(
        [
            canonical_to_unravel_reference_view(m_canonical).head(87),
            canonical_to_unravel_reference_view(i_canonical).head(123),
        ],
        how="vertical_relaxed",
    )
    interop = pd.DataFrame([m_interop, i_interop])
    kinematics = pd.DataFrame([m_kinematics, i_kinematics])
    components = {
        "kloppy_polars_tooling": "REFERENCE ONLY",
        "canonical_compatibility_view": "INTEGRATE",
        "kinematics": "REFERENCE ONLY",
        "pressing_intensity": "DEFER",
        "efpi": "DEFER",
        "graph_tooling": "DO NOT USE",
    }
    result = {
        "classification": "B",
        "decision": "useful interoperability/reference layer, but no governed pipeline integration",
        "unravelsports_version": importlib.metadata.version("unravelsports"),
        "kloppy_version": importlib.metadata.version("kloppy"),
        "polars_version": importlib.metadata.version("polars"),
        "scipy_version": importlib.metadata.version("scipy"),
        "frame_limit_per_provider": FRAME_LIMIT,
        "shared_coordinates_pass_after_explicit_axis_mapping": bool(interop["shared_coordinates_pass_after_explicit_axis_mapping"].all()),
        "row_membership_equivalent": bool(interop["row_membership_equivalent"].all()),
        "support_semantics_preserved": False,
        "kinematics_exact_substitute": False,
        "canonical_contract_replaced": False,
        "governed_measurement_replaced": False,
        "game3_accessed": False,
        "historical_pipeline_migrated": False,
        "source_sha256": sha256(Path(__file__)),
    }
    manifest = {
        **result,
        "license": "MPL-2.0",
        "python_compatibility": ">=3.11; tested on 3.13.15",
        "declared_dependencies": importlib.metadata.requires("unravelsports"),
        "source_inputs": {
            "metrica": m_provenance["source_files"],
            "idsse_sportec": i_provenance["source_files"],
        },
        "component_classification": components,
    }

    interop.to_csv(OUT / "provider_interoperability.csv", index=False)
    kinematics.to_csv(OUT / "kinematics_comparison.csv", index=False)
    compatibility_samples.write_parquet(OUT / "canonical_compatibility_sample.parquet")
    (OUT / "component_classification.json").write_text(json.dumps(components, indent=2) + "\n")
    (OUT / "audit_result.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
