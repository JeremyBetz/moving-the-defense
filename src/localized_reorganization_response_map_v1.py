"""Frozen, fail-closed implementation for the IDSSE descriptive response map.

Importing this module and running ``--verify-freeze`` are response-blind.  The
protected registry is reachable only through ``--execute-response`` after a
future explicit human authorization has been supplied at the command line.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import localized_reorganization_heatmap_support_preflight_v1 as support  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/localized_reorganization_response_map_v1.md"
CONFIG = ROOT / "config/localized_reorganization_response_map_v1.json"
HASH_LEDGER = ROOT / "config/localized_reorganization_response_map_v1_hashes.json"
REGISTRY = ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/observation_rows.parquet"
DEFAULT_OUTPUT = ROOT / "outputs/localized_reorganization_response_map_v1"
DEFAULT_FIGURE = ROOT / "figures/localized_reorganization_response_map_v1/response_map"


class ResponseMapInvalid(RuntimeError):
    """A frozen response-map validity rule failed."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _atomic_write_json(path: Path, value: Any) -> None:
    """Publish one closure marker only after its content has been validated."""
    temporary = path.with_name(f".{path.name}.tmp")
    if path.exists() or temporary.exists():
        raise ResponseMapInvalid(f"refusing to replace an existing closure marker: {path}")
    try:
        _write_json(temporary, value)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_csv(frame: pd.DataFrame, path: Path, columns: list[str]) -> None:
    if list(frame.columns) != columns:
        raise ResponseMapInvalid(f"output schema differs for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def expected_match_order(cfg: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in cfg["matches"])


def authorized_response_columns(cfg: dict[str, Any]) -> tuple[str, ...]:
    columns = tuple(cfg["protected_source"]["authorized_response_columns"])
    expected = ("observation_id", "distance_rank", "response_2s_m")
    if columns != expected or any("*" in value for value in columns):
        raise ResponseMapInvalid("response loader columns are not the exact frozen allowlist")
    return columns


def validate_response_request(columns: Iterable[str], cfg: dict[str, Any]) -> None:
    requested = tuple(columns)
    authorized = authorized_response_columns(cfg)
    if requested != authorized:
        raise ResponseMapInvalid("response loader requested an unauthorized or reordered field")
    prohibited = set(cfg["protected_source"]["prohibited_outcome_columns"])
    if prohibited.intersection(requested):
        raise ResponseMapInvalid("response loader requested a prohibited outcome field")


def construct_anchor_y(
    response_rows: pd.DataFrame,
    expected_observation_ids: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Construct the sole frozen D1--D3 minus D4--D7 anchor outcome."""
    expected_columns = ["observation_id", "distance_rank", "response_2s_m"]
    if list(response_rows.columns) != expected_columns:
        raise ResponseMapInvalid("response rows do not have the exact authorized schema")
    data = response_rows.copy()
    data["distance_rank"] = pd.to_numeric(data["distance_rank"], errors="raise")
    if not data["distance_rank"].isin(range(1, 8)).all():
        raise ResponseMapInvalid("response rows include a rank outside the frozen D1-D7 outcome")
    data["response_2s_m"] = pd.to_numeric(data["response_2s_m"], errors="raise")
    if not np.isfinite(data["response_2s_m"].to_numpy(float)).all():
        raise ResponseMapInvalid("required response field contains missing or nonfinite values")
    if data.duplicated(["observation_id", "distance_rank"]).any():
        raise ResponseMapInvalid("governed rank is duplicated within an observation")
    rank_sets = data.groupby("observation_id", sort=False)["distance_rank"].agg(lambda q: tuple(sorted(q)))
    if not rank_sets.map(lambda ranks: ranks == tuple(range(1, 8))).all():
        raise ResponseMapInvalid("governed response vector lacks one or more required D1-D7 ranks")
    if expected_observation_ids is not None and set(rank_sets.index) != set(expected_observation_ids):
        raise ResponseMapInvalid("response observations do not exactly join the governed support population")
    near = data[data.distance_rank <= 3].groupby("observation_id", sort=True).response_2s_m.mean()
    middle = data[data.distance_rank >= 4].groupby("observation_id", sort=True).response_2s_m.mean()
    outcome = (near - middle).rename("y_m").reset_index()
    if not np.isfinite(outcome.y_m.to_numpy(float)).all():
        raise ResponseMapInvalid("constructed anchor outcome is nonfinite")
    return outcome.sort_values("observation_id", kind="mergesort").reset_index(drop=True)


def gaussian_weights(distances_m: np.ndarray, bandwidth_m: float, truncate_at_bandwidths: float) -> np.ndarray:
    distances = np.asarray(distances_m, dtype=float)
    if bandwidth_m <= 0 or truncate_at_bandwidths <= 0:
        raise ResponseMapInvalid("kernel bandwidth and cutoff must be positive")
    values = np.zeros_like(distances, dtype=float)
    keep = distances <= truncate_at_bandwidths * bandwidth_m
    values[keep] = np.exp(-0.5 * np.square(distances[keep] / bandwidth_m))
    return values


def one_match_local_mean(
    coordinates: np.ndarray,
    values: np.ndarray,
    grid: np.ndarray,
    bandwidth_m: float,
    truncate_at_bandwidths: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a local mean and denominator at every supplied legal grid cell."""
    xy = np.asarray(coordinates, dtype=float)
    y = np.asarray(values, dtype=float)
    cells = np.asarray(grid, dtype=float)
    if len(xy) != len(y) or xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all() or not np.isfinite(y).all():
        raise ResponseMapInvalid("nonfinite or mismatched coordinate/outcome input")
    edges = cKDTree(cells).sparse_distance_matrix(
        cKDTree(xy), max_distance=truncate_at_bandwidths * bandwidth_m, output_type="coo_matrix"
    )
    weights = gaussian_weights(edges.data, bandwidth_m, truncate_at_bandwidths)
    denominator = np.bincount(edges.row, weights=weights, minlength=len(cells)).astype(float)
    numerator = np.bincount(edges.row, weights=weights * y[edges.col], minlength=len(cells)).astype(float)
    means = np.divide(numerator, denominator, out=np.full(len(cells), np.nan), where=denominator > 0)
    return means, denominator


def equal_match_surface(
    by_match: dict[str, tuple[np.ndarray, np.ndarray]],
    grid: np.ndarray,
    bandwidth_m: float,
    truncate_at_bandwidths: float,
    matches: Iterable[str],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Compute equal-match, never row-pooled, local means."""
    ordered = tuple(matches)
    if set(by_match) != set(ordered):
        raise ResponseMapInvalid("match set differs from the frozen seven-match population")
    means: list[np.ndarray] = []
    denominators: dict[str, np.ndarray] = {}
    for match_id in ordered:
        mean, denominator = one_match_local_mean(*by_match[match_id], grid, bandwidth_m, truncate_at_bandwidths)
        means.append(mean)
        denominators[match_id] = denominator
    stacked = np.stack(means)
    return stacked.mean(axis=0), denominators


def weighted_inverse_ecdf_limit(anchor_outcomes: pd.DataFrame, matches: Iterable[str]) -> float:
    """Equal-match weighted inverse empirical CDF of absolute anchor outcomes."""
    required = ["match_id", "observation_id", "y_m"]
    if list(anchor_outcomes.columns) != required:
        raise ResponseMapInvalid("color-scale input schema differs from the frozen anchor outcome schema")
    ordered_matches = tuple(matches)
    if set(anchor_outcomes.match_id) != set(ordered_matches):
        raise ResponseMapInvalid("color-scale match population differs from the frozen population")
    rows: list[tuple[float, str, float]] = []
    for match_id in ordered_matches:
        group = anchor_outcomes[anchor_outcomes.match_id == match_id]
        if len(group) == 0 or not np.isfinite(group.y_m.to_numpy(float)).all() or group.observation_id.duplicated().any():
            raise ResponseMapInvalid("color-scale input is incomplete or nonfinite")
        weight = 1.0 / (len(ordered_matches) * len(group))
        rows.extend((abs(float(row.y_m)), str(row.observation_id), weight) for row in group.itertuples(index=False))
    rows.sort(key=lambda row: (row[0], row[1]))
    cumulative = 0.0
    for value, _observation_id, weight in rows:
        cumulative += weight
        if cumulative >= 0.95:
            return float(value)
    raise ResponseMapInvalid("weighted color-scale CDF did not reach 0.95")


def scale_state(limit: float, surfaces: Iterable[np.ndarray]) -> str:
    values = np.concatenate([np.asarray(surface, dtype=float)[np.isfinite(surface)] for surface in surfaces])
    if not math.isfinite(limit) or limit < 0:
        return "INVALID"
    if limit == 0.0:
        return "VALID_BUT_UNINFORMATIVE" if np.all(values == 0.0) else "INVALID"
    return "VALID"


def saturation_counts(surface: np.ndarray, limit: float) -> tuple[int, int]:
    values = np.asarray(surface, dtype=float)
    return int((values < -limit).sum()), int((values > limit).sum())


def saturation_extension(negative_count: int, positive_count: int) -> str:
    """Return Matplotlib's shared-colorbar extension from actual clipping."""
    if negative_count < 0 or positive_count < 0:
        raise ResponseMapInvalid("saturation counts must be nonnegative")
    if negative_count and positive_count:
        return "both"
    if negative_count:
        return "min"
    if positive_count:
        return "max"
    return "neither"


def _destination_error(path: Path) -> ResponseMapInvalid:
    return ResponseMapInvalid(
        f"refusing to overwrite existing authoritative destination: {path}; "
        "use a clean/disposable environment or an explicitly isolated reproduction destination"
    )


def require_clean_destinations(output: Path, figure_base: Path) -> None:
    """Fail closed before any protected access when an authoritative target exists."""
    if output.exists():
        raise _destination_error(output)
    for suffix in (".png", ".svg"):
        target = figure_base.with_suffix(suffix)
        if target.exists():
            raise _destination_error(target)


def _artifact_paths(output: Path, figure_base: Path, cfg: dict[str, Any]) -> dict[str, Path]:
    names = cfg["closure"]["deterministic_machine_readable_files"]
    result = {name: output / name for name in names}
    result.update({f"figures/response_map{suffix}": figure_base.with_suffix(suffix) for suffix in (".png", ".svg")})
    return result


def _artifact_hashes(output: Path, figure_base: Path, cfg: dict[str, Any]) -> dict[str, str]:
    paths = _artifact_paths(output, figure_base, cfg)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ResponseMapInvalid(f"run is missing deterministic artifacts: {missing}")
    return {name: sha(path) for name, path in paths.items()}


def compare_deterministic_artifacts(
    primary_output: Path,
    primary_figure: Path,
    rerun_output: Path,
    rerun_figure: Path,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Compare the deterministic scientific package byte-for-byte."""
    primary = _artifact_paths(primary_output, primary_figure, cfg)
    rerun = _artifact_paths(rerun_output, rerun_figure, cfg)
    differences = [name for name in primary if primary[name].read_bytes() != rerun[name].read_bytes()]
    figure_names = {"figures/response_map.png", "figures/response_map.svg"}
    return {
        "machine_readable_byte_identical": not any(name not in figure_names for name in differences),
        "figure_byte_identical": not any(name in figure_names for name in differences),
        "differing_artifacts": differences,
    }


def validate_aggregate_schema(frame: pd.DataFrame, cfg: dict[str, Any], key: str) -> None:
    expected = cfg["outputs"][key]
    if list(frame.columns) != expected:
        raise ResponseMapInvalid("aggregate output schema differs from the frozen allowlist")
    forbidden = cfg["outputs"]["forbidden_field_tokens"]
    bad = [column for column in frame.columns if any(token in column.lower() for token in forbidden)]
    if bad:
        raise ResponseMapInvalid(f"aggregate output contains forbidden field tokens: {bad}")


def select_frozen_masks(support_grid: pd.DataFrame, cfg: dict[str, Any]) -> dict[float, pd.DataFrame]:
    required = {"grid_x_m", "grid_y_m", "bandwidth_m", "profile", "support_pass"}
    if not required.issubset(support_grid.columns):
        raise ResponseMapInvalid("support grid lacks the frozen mask fields")
    profile = cfg["support"]["source_profile"]
    bands = [float(cfg["kernel"]["bandwidths_m"]["primary"]), *map(float, cfg["kernel"]["bandwidths_m"]["sensitivity"])]
    masks: dict[float, pd.DataFrame] = {}
    for bandwidth in bands:
        mask = support_grid[(support_grid.bandwidth_m == bandwidth) & (support_grid.profile == profile)].copy()
        mask = mask.sort_values(["grid_y_m", "grid_x_m"], kind="mergesort").reset_index(drop=True)
        if len(mask) != int(cfg["grid"]["legal_cells"]):
            raise ResponseMapInvalid("saved support mask does not cover the legal grid")
        expected_count = int(cfg["support"]["valid_cells_by_bandwidth"][f"{bandwidth:.1f}"])
        if int(mask.support_pass.sum()) != expected_count:
            raise ResponseMapInvalid("saved support mask valid-cell count differs from the frozen value")
        masks[bandwidth] = mask
    common = np.logical_and.reduce([masks[bandwidth].support_pass.to_numpy(bool) for bandwidth in bands])
    if int(common.sum()) != int(cfg["support"]["common_intersection_cells"]):
        raise ResponseMapInvalid("saved support-mask intersection differs from the frozen value")
    return masks


def assemble_aggregate_grid(
    masks: dict[float, pd.DataFrame], surfaces: dict[float, np.ndarray], cfg: dict[str, Any]
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    profile = cfg["support"]["source_profile"]
    for bandwidth, mask in masks.items():
        values = np.asarray(surfaces[bandwidth], dtype=float)
        valid = mask.support_pass.to_numpy(bool)
        if len(values) != len(mask) or not np.isfinite(values[valid]).all() or np.isfinite(values[~valid]).any():
            raise ResponseMapInvalid("surface does not respect the frozen support mask")
        rows.append(pd.DataFrame({
            "grid_x_m": mask.grid_x_m.to_numpy(float),
            "grid_y_m": mask.grid_y_m.to_numpy(float),
            "bandwidth_m": float(bandwidth),
            "support_profile": profile,
            "support_valid": valid,
            "equal_match_local_mean_m": np.where(valid, values, np.nan),
        }))
    frame = pd.concat(rows, ignore_index=True).sort_values(["bandwidth_m", "grid_y_m", "grid_x_m"], kind="mergesort").reset_index(drop=True)
    validate_aggregate_schema(frame, cfg, "aggregate_response_grid_schema")
    return frame


def summarize_surfaces(
    aggregate: pd.DataFrame, denominators: dict[float, dict[str, np.ndarray]], limit: float, cfg: dict[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for bandwidth, group in aggregate.groupby("bandwidth_m", sort=True):
        valid = group.support_valid.to_numpy(bool)
        values = group.equal_match_local_mean_m.to_numpy(float)[valid]
        low, high = saturation_counts(values, limit)
        rows.append({
            "bandwidth_m": float(bandwidth),
            "legal_grid_cell_count": int(len(group)),
            "support_valid_cell_count": int(valid.sum()),
            "support_fraction": float(valid.mean()),
            "surface_min_m": float(values.min()),
            "surface_median_m": float(np.median(values)),
            "surface_max_m": float(values.max()),
            "area_weighted_mean_m": float(values.mean()),
            "positive_cell_fraction": float((values > 0).mean()),
            "negative_cell_fraction": float((values < 0).mean()),
            "zero_cell_fraction": float((values == 0).mean()),
            "saturated_low_cell_count": low,
            "saturated_high_cell_count": high,
            "all_match_denominators_finite": bool(all(np.isfinite(v).all() and (v > 0).all() for v in denominators[float(bandwidth)].values())),
        })
    frame = pd.DataFrame(rows).sort_values("bandwidth_m", kind="mergesort").reset_index(drop=True)
    validate_aggregate_schema(frame, cfg, "surface_summary_schema")
    return frame


def render_response_map(aggregate: pd.DataFrame, limit: float, cfg: dict[str, Any], output_base: Path) -> dict[str, int | str]:
    """Render only aggregate response-grid values on the frozen three panels."""
    bands = [float(value) for value in cfg["figure"]["panel_order_bandwidth_m"]]
    if scale_state(limit, [aggregate.equal_match_local_mean_m.to_numpy(float)]) == "INVALID":
        raise ResponseMapInvalid("degenerate shared color scale is invalid")
    cmap = plt.get_cmap("RdBu_r").with_extremes(bad="#d9d9d9")
    with matplotlib.rc_context({"svg.hashsalt": "moving-the-defense-response-map-v1"}):
        fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True)
        image = None
        negative_total = positive_total = 0
        for label, bandwidth, axis in zip(("A", "B", "C"), bands, axes, strict=True):
            group = aggregate[aggregate.bandwidth_m == bandwidth].sort_values(["grid_y_m", "grid_x_m"], kind="mergesort")
            x = np.sort(group.grid_x_m.unique()); y = np.sort(group.grid_y_m.unique())
            values = group.equal_match_local_mean_m.to_numpy(float).reshape(len(y), len(x))
            negative, positive = saturation_counts(values[np.isfinite(values)], limit)
            negative_total += negative; positive_total += positive
            if limit == 0.0:
                values = np.ma.masked_invalid(values)
                image = axis.pcolormesh(x, y, values * 0.0, shading="nearest", cmap="Greys", vmin=-1, vmax=1)
                title = f"{label}. h={bandwidth:g} m — neutral (L=0)"
            else:
                image = axis.pcolormesh(x, y, values, shading="nearest", cmap=cmap, vmin=-limit, vmax=limit)
                title = f"{label}. h={bandwidth:g} m" + (" — primary" if bandwidth == 7.5 else " — sensitivity")
                title += f" — saturation −{negative}/+{positive}"
            axis.add_patch(plt.Rectangle((-52.5, -34), 105, 68, fill=False, color="#222222", lw=1.1))
            axis.axvline(0, color="#555555", lw=0.6)
            axis.set(xlim=(-52.5, 52.5), ylim=(-34, 34), aspect="equal", title=title,
                     xlabel="Deeper ← longitudinal position (m) → Goalward",
                     ylabel="Provider physical lateral position (m)")
        extension = saturation_extension(negative_total, positive_total) if limit > 0 else "neither"
        colorbar = fig.colorbar(image, ax=axes, shrink=0.78, pad=0.02, extend=extension)
        colorbar.set_label("Equal-match local mean near-minus-middle response (m)")
        fig.text(0.5, 0.01, f"Display saturation across panels: negative={negative_total}, positive={positive_total}", ha="center", fontsize=8)
        output_base.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_base.with_suffix(".png"), dpi=180, metadata={"Software": "Moving the Defense"})
        fig.savefig(output_base.with_suffix(".svg"), metadata={"Date": None, "Creator": "Moving the Defense"})
        plt.close(fig)
    return {"negative_saturation_count": negative_total, "positive_saturation_count": positive_total, "colorbar_extension": extension}


def verify_freeze(cfg: dict[str, Any], ledger_path: Path = HASH_LEDGER) -> dict[str, str]:
    """Verify code/docs/support hashes without touching the protected registry."""
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    expected = ledger["frozen_artifacts_sha256"]
    mismatches = {path: (sha(ROOT / path), digest) for path, digest in expected.items() if sha(ROOT / path) != digest}
    if mismatches:
        raise ResponseMapInvalid(f"frozen artifact hash mismatch: {mismatches}")
    protected = ledger["protected_registry_identity"]
    if protected["path"] != cfg["protected_source"]["registry_path"] or protected["sha256"] != cfg["protected_source"]["registry_sha256"]:
        raise ResponseMapInvalid("protected registry identity differs from the frozen configuration")
    return expected


def _load_authorized_response_rows(cfg: dict[str, Any]) -> pd.DataFrame:
    """The only production function permitted to materialize response values."""
    columns = authorized_response_columns(cfg)
    validate_response_request(columns, cfg)
    if not REGISTRY.is_file():
        raise ResponseMapInvalid("protected governed registry is unavailable")
    frame = pl.scan_parquet(REGISTRY).filter(pl.col("distance_rank").is_between(1, 7)).select(list(columns)).collect()
    return pd.DataFrame(frame.to_dict(as_series=False))[list(columns)]


def _load_execution_inputs(cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[float, pd.DataFrame]]:
    """Load frozen support keys and the one authorized response field after approval."""
    support_rows = support._registry(support.config())
    response_rows = _load_authorized_response_rows(cfg)
    anchor_y = construct_anchor_y(response_rows, support_rows.observation_id)
    coordinates: list[pd.DataFrame] = []
    for match_id in expected_match_order(cfg):
        rows = support_rows[support_rows.match_id == match_id].reset_index(drop=True)
        prepared = support.prepare_match(match_id, rows)
        if len(rows) != len(prepared.coordinates):
            raise ResponseMapInvalid("coordinate reconstruction does not exactly preserve support-row identity")
        coordinates.append(pd.DataFrame({"observation_id": rows.observation_id, "match_id": match_id,
                                         "x_plot_m": prepared.coordinates[:, 0], "y_plot_m": prepared.coordinates[:, 1]}))
    anchors = pd.concat(coordinates, ignore_index=True).merge(anchor_y, on="observation_id", how="inner", validate="one_to_one")
    if len(anchors) != len(support_rows) or anchors.observation_id.duplicated().any():
        raise ResponseMapInvalid("response and coordinate populations do not join exactly")
    grid = pd.DataFrame(pl.read_parquet(cfg["support"]["source_grid_path"], columns=["grid_x_m", "grid_y_m", "bandwidth_m", "profile", "support_pass"]).to_dict(as_series=False))
    return anchors.sort_values(["match_id", "observation_id"], kind="mergesort").reset_index(drop=True), select_frozen_masks(grid, cfg)


def _validate_anchor_population(anchors: pd.DataFrame, cfg: dict[str, Any]) -> None:
    required = {"match_id", "observation_id", "x_plot_m", "y_plot_m", "y_m"}
    if not required.issubset(anchors.columns) or anchors.observation_id.duplicated().any():
        raise ResponseMapInvalid("response execution anchor population is incomplete or duplicated")
    if set(anchors.match_id) != set(expected_match_order(cfg)):
        raise ResponseMapInvalid("response execution anchor matches differ from the frozen population")
    if not np.isfinite(anchors[["x_plot_m", "y_plot_m", "y_m"]].to_numpy(float)).all():
        raise ResponseMapInvalid("response execution anchors contain nonfinite values")


def run_from_inputs(
    anchors: pd.DataFrame,
    masks: dict[float, pd.DataFrame],
    output: Path,
    figure_base: Path,
    authorization_reference: str,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Create one isolated, pre-closure run from already-authorized inputs."""
    require_clean_destinations(output, figure_base)
    _validate_anchor_population(anchors, cfg)
    by_match = {
        match_id: (group[["x_plot_m", "y_plot_m"]].to_numpy(float), group.y_m.to_numpy(float))
        for match_id, group in anchors.groupby("match_id", sort=True)
    }
    limit = weighted_inverse_ecdf_limit(anchors[["match_id", "observation_id", "y_m"]], expected_match_order(cfg))
    surfaces: dict[float, np.ndarray] = {}
    denominators: dict[float, dict[str, np.ndarray]] = {}
    for bandwidth, mask in masks.items():
        valid = mask.support_pass.to_numpy(bool)
        grid = mask.loc[valid, ["grid_x_m", "grid_y_m"]].to_numpy(float)
        means, denoms = equal_match_surface(
            by_match, grid, bandwidth, float(cfg["kernel"]["truncate_at_bandwidths"]), expected_match_order(cfg)
        )
        full = np.full(len(mask), np.nan)
        full[valid] = means
        if any((~np.isfinite(value)).any() or (value <= 0).any() for value in denoms.values()):
            raise ResponseMapInvalid("a displayed cell lacks a finite positive denominator in a required match")
        surfaces[bandwidth] = full
        denominators[bandwidth] = denoms
    state = scale_state(limit, surfaces.values())
    if state == "INVALID":
        raise ResponseMapInvalid("frozen shared color-scale rule is invalid")
    aggregate = assemble_aggregate_grid(masks, surfaces, cfg)
    summary = summarize_surfaces(aggregate, denominators, limit, cfg)
    counts = anchors.groupby("match_id", sort=True).size().rename("eligible_anchor_count").reset_index()
    counts["complete_response_anchor_count"] = counts.eligible_anchor_count
    counts["missing_required_response_anchor_count"] = 0
    counts["identity_join_pass"] = True
    validate_aggregate_schema(counts, cfg, "sample_counts_schema")

    output.mkdir(parents=True, exist_ok=False)
    _write_csv(aggregate, output / "aggregate_response_grid.csv", cfg["outputs"]["aggregate_response_grid_schema"])
    _write_csv(counts, output / "sample_counts.csv", cfg["outputs"]["sample_counts_schema"])
    _write_csv(summary, output / "surface_summary.csv", cfg["outputs"]["surface_summary_schema"])
    saturation = render_response_map(aggregate, limit, cfg, figure_base)
    manifest = {
        "status": cfg["statuses"]["preclosure"],
        "authorization_reference": authorization_reference,
        "color_limit_m": limit,
        "color_scale_state": state,
        "response_registry_sha256": cfg["protected_source"]["registry_sha256"],
        "support_grid_path": cfg["support"]["source_grid_path"],
        "matches": list(expected_match_order(cfg)),
        "anchor_coordinates_serialized": False,
        "row_level_y_serialized": False,
        "per_match_surfaces_serialized": False,
        "closure_state": "PENDING_INDEPENDENT_REPRODUCTION",
    }
    _write_json(output / "manifest.json", manifest)
    _write_json(output / "hard_qc.json", {
        "exact_identity_join": True,
        "all_required_responses_finite": True,
        "all_match_denominators_finite": True,
        "frozen_masks_used": True,
        "response_field_exact": True,
        "coordinate_clipping_applied": False,
        "saturation": saturation,
    })
    governed = cfg["closure"]["governed_hash_files"]
    _write_json(output / "governed_hashes.json", {name: sha(output / name) for name in governed})
    return {"manifest": manifest, "artifact_hashes": _artifact_hashes(output, figure_base, cfg)}


def _final_artifact_paths(output: Path, figure_base: Path, cfg: dict[str, Any]) -> dict[str, Path]:
    result = {name: output / name for name in cfg["closure"]["final_output_files"]}
    result.update({f"figures/response_map{suffix}": figure_base.with_suffix(suffix) for suffix in (".png", ".svg")})
    return result


def validate_final_hashes(output: Path, figure_base: Path, cfg: dict[str, Any]) -> dict[str, str]:
    recorded = json.loads((output / "final_hashes.json").read_text(encoding="utf-8"))
    return validate_final_hash_content(recorded, output, figure_base, cfg)


def validate_final_hash_content(
    recorded: dict[str, Any], output: Path, figure_base: Path, cfg: dict[str, Any]
) -> dict[str, str]:
    """Validate a final-ledger candidate against actual authoritative paths."""
    expected_paths = _final_artifact_paths(output, figure_base, cfg)
    if (
        recorded.get("closure_status") != cfg["statuses"]["valid"]
        or recorded.get("self_hash_excluded") is not True
        or set(recorded.get("artifacts_sha256", {})) != set(expected_paths)
    ):
        raise ResponseMapInvalid("final hash ledger has an unexpected artifact set")
    actual = {name: sha(path) for name, path in expected_paths.items()}
    if recorded["artifacts_sha256"] != actual:
        raise ResponseMapInvalid("final hash ledger does not match the closed package")
    return actual


def publish_final_hashes(output: Path, figure_base: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    """Validate actual authoritative artifacts, then atomically publish final authority."""
    final_path = output / "final_hashes.json"
    ledger = {
        "closure_status": cfg["statuses"]["valid"],
        "artifacts_sha256": {name: sha(path) for name, path in _final_artifact_paths(output, figure_base, cfg).items()},
        "self_hash_excluded": True,
    }
    validate_final_hash_content(ledger, output, figure_base, cfg)
    _atomic_write_json(final_path, ledger)
    return ledger


def finalize_closure(
    primary_output: Path,
    primary_figure: Path,
    rerun_output: Path,
    rerun_figure: Path,
    authorization_reference: str,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Close a staging run only after byte-identical independent reproduction."""
    comparison = compare_deterministic_artifacts(primary_output, primary_figure, rerun_output, rerun_figure, cfg)
    if not comparison["machine_readable_byte_identical"] or not comparison["figure_byte_identical"]:
        raise ResponseMapInvalid(f"deterministic reproduction failed: {comparison['differing_artifacts']}")
    reproduction = {
        "closure_status": "DETERMINISTIC_REPRODUCTION_PASSED",
        "authorization_reference": authorization_reference,
        "frozen_artifacts_sha256": json.loads(HASH_LEDGER.read_text(encoding="utf-8"))["frozen_artifacts_sha256"],
        "protected_registry_expected_sha256": cfg["protected_source"]["registry_sha256"],
        "primary_staging": {
            "artifact_scope": "isolated_preclosure_primary_staging",
            "artifacts_sha256": _artifact_hashes(primary_output, primary_figure, cfg),
        },
        "reproduction_staging": {
            "artifact_scope": "isolated_preclosure_independent_rerun",
            "artifacts_sha256": _artifact_hashes(rerun_output, rerun_figure, cfg),
        },
        "comparison": comparison,
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }
    _write_json(primary_output / "reproduction.json", reproduction)
    manifest = json.loads((primary_output / "manifest.json").read_text(encoding="utf-8"))
    # A promoted manifest is deliberately non-final.  The separately published
    # final ledger below is the only authoritative valid-status marker.
    manifest["closure_state"] = "PENDING_FINAL_HASH_VALIDATION"
    _write_json(primary_output / "manifest.json", manifest)
    return manifest


def _promote_authoritative_package(staging_output: Path, staging_figure: Path, output: Path, figure_base: Path) -> None:
    require_clean_destinations(output, figure_base)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure_base.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg"):
        os.replace(staging_figure.with_suffix(suffix), figure_base.with_suffix(suffix))
    # The finalized manifest is inside ``staging_output``.  Move its directory
    # only after both authoritative figures exist, so a promotion failure can
    # never expose an authoritative valid-status output package prematurely.
    os.replace(staging_output, output)


def execute_response(output: Path, figure_base: Path, authorization_reference: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Future-only, two-run closure; never invoke during the pre-access freeze."""
    if not authorization_reference.strip():
        raise ResponseMapInvalid("--execute-response requires a nonempty authorization reference")
    require_clean_destinations(output, figure_base)
    verify_freeze(cfg)
    if sha(REGISTRY) != cfg["protected_source"]["registry_sha256"]:
        raise ResponseMapInvalid("protected response registry hash mismatch")
    with tempfile.TemporaryDirectory(prefix="localized-response-map-") as temporary_root:
        root = Path(temporary_root)
        primary_output, primary_figure = root / "primary" / "outputs", root / "primary" / "figures" / "response_map"
        rerun_output, rerun_figure = root / "rerun" / "outputs", root / "rerun" / "figures" / "response_map"
        primary_anchors, primary_masks = _load_execution_inputs(cfg)
        run_from_inputs(primary_anchors, primary_masks, primary_output, primary_figure, authorization_reference, cfg)
        rerun_anchors, rerun_masks = _load_execution_inputs(cfg)
        run_from_inputs(rerun_anchors, rerun_masks, rerun_output, rerun_figure, authorization_reference, cfg)
        manifest = finalize_closure(primary_output, primary_figure, rerun_output, rerun_figure, authorization_reference, cfg)
        _promote_authoritative_package(primary_output, primary_figure, output, figure_base)
        publish_final_hashes(output, figure_base, cfg)
        validate_final_hashes(output, figure_base, cfg)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-freeze", action="store_true", help="verify frozen non-response artifacts only")
    parser.add_argument("--execute-response", action="store_true", help="future authorized response execution only")
    parser.add_argument("--authorization-reference", default="")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure-base", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args(argv); cfg = load_config()
    if args.verify_freeze and args.execute_response:
        parser.error("choose either --verify-freeze or --execute-response")
    if args.verify_freeze:
        print(json.dumps({"verified_frozen_artifacts": verify_freeze(cfg)}, sort_keys=True)); return 0
    if args.execute_response:
        print(json.dumps(execute_response(args.output, args.figure_base, args.authorization_reference, cfg), sort_keys=True)); return 0
    parser.error("response access is disabled by default; use --verify-freeze or a later authorized --execute-response")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
