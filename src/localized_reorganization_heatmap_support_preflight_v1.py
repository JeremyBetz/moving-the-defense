"""Response-blind IDSSE spatial-support preflight for a future descriptive map.

The implementation intentionally selects only registry identity/support fields.
It never selects or constructs footprint response fields, and never serializes
attacker-anchor coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import concurrent_attacker_defensive_geometry_idsse_v1 as concurrent  # noqa: E402
import defensive_reorganization_departure_v1 as departure  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/localized_reorganization_heatmap_support_preflight_v1.md"
CONFIG = ROOT / "config/localized_reorganization_heatmap_support_preflight_v1.json"
REGISTRY = ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/observation_rows.parquet"
DEFAULT_OUTPUT = ROOT / "outputs/localized_reorganization_heatmap_support_preflight_v1"
DEFAULT_REPORT = ROOT / "docs/results/localized_reorganization_heatmap_support_preflight_v1.md"
DEFAULT_FIGURE = ROOT / "figures/localized_reorganization_heatmap_support_preflight_v1/support_frontier.png"
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
EDGE, FRAME_NS = 3, 40_000_000


@dataclass(frozen=True)
class PreparedMatch:
    match_id: str
    coordinates: np.ndarray
    time_keys: np.ndarray
    block_keys: np.ndarray


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def grid_points(cfg: dict[str, Any]) -> np.ndarray:
    x, y = cfg["grid"]["x_centres_m"], cfg["grid"]["y_centres_m"]
    xx = np.arange(x["start"], x["stop"] + x["step"] / 2, x["step"], dtype=float)
    yy = np.arange(y["start"], y["stop"] + y["step"] / 2, y["step"], dtype=float)
    gx, gy = np.meshgrid(xx, yy, indexing="xy")
    return np.column_stack([gx.ravel(), gy.ravel()])


def _registry(cfg: dict[str, Any]) -> pd.DataFrame:
    """Read permitted ID/support fields only; response columns are never selected."""
    if not REGISTRY.is_file():
        raise RuntimeError(f"missing local governed footprint registry: {REGISTRY}")
    columns = cfg["source_population"]["permitted_registry_columns"]
    available = set(pl.read_parquet_schema(REGISTRY).names())
    forbidden = set(cfg["source_population"]["forbidden_columns"])
    if not forbidden.issubset(available):
        raise RuntimeError("expected response-blind firewall schema is unavailable")
    # Keep the repository's no-PyArrow conversion convention used by governed
    # IDSSE scripts; only the allowlisted fields above are materialized.
    data = pd.DataFrame(pl.read_parquet(REGISTRY, columns=columns).to_dict(as_series=False))
    if set(data.columns) != set(columns):
        raise RuntimeError("registry selected an unpermitted column")
    if set(data.match_id.unique()) != set(MATCHES):
        raise RuntimeError("governed footprint match registry differs from the seven authorized matches")
    ranks = data.groupby("observation_id", sort=False)["distance_rank"].agg(list)
    if not ranks.map(lambda value: sorted(value) == list(range(1, 11))).all():
        raise RuntimeError("governed observation registry lacks complete D1-D10 vectors")
    base = data.loc[data.distance_rank == 1].copy()
    if base.observation_id.duplicated().any() or len(base) * 10 != len(data):
        raise RuntimeError("governed observation identity collapse is not exact")
    expected = base.apply(lambda row: f"TSFI|{row.match_id}|P{int(row.period)}|T{float(row.time_period_s):.2f}|{row.attacker_key}", axis=1)
    if not (expected == base.observation_id).all():
        raise RuntimeError("governed observation IDs do not match their authorized identity fields")
    return base.sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)


def _smoothed_at(entity: dict[str, Any], index: int) -> np.ndarray:
    window = np.column_stack([entity["x"][index - EDGE:index + EDGE + 1], entity["y"][index - EDGE:index + EDGE + 1]]).astype(float)
    if len(window) != 7 or not entity["valid"][index - EDGE:index + EDGE + 1].all():
        raise RuntimeError("incomplete seven-frame attacker start support")
    return window.mean(axis=0)


def prepare_match(match_id: str, rows: pd.DataFrame) -> PreparedMatch:
    """Reconstruct only in-memory t-2 attacker coordinates for one match."""
    metadata, _events, tracking = concurrent.load_native(match_id)
    signs = departure.period_signs(metadata, tracking)
    period_maps = {}
    for period_number, period_name in enumerate(idsse.PERIODS, 1):
        pdata = tracking[period_name]
        period_maps[period_number] = (
            {int(time): index for index, time in enumerate(pdata["time_ns"])},
            {(item["team_id"], item["person_id"]): item for item in pdata["entities"]},
        )
    values: list[tuple[float, float]] = []
    for row in rows.itertuples(index=False):
        lookup, entities = period_maps[int(row.period)]
        start_ns = int(row.time_utc_ns) - 2_000_000_000
        if start_ns not in lookup:
            raise RuntimeError("authorized anchor is absent from native t-2 support")
        entity = entities.get((row.attacking_team, row.attacker_key))
        if entity is None:
            raise RuntimeError("authorized attacker is absent from native roster")
        xy = _smoothed_at(entity, lookup[start_ns])
        values.append((float(signs[(int(row.period), row.attacking_team)]) * float(xy[0]), float(xy[1])))
    coordinates = np.asarray(values, dtype=float)
    if not np.isfinite(coordinates).all():
        raise RuntimeError("reconstructed attacker start coordinates are nonfinite")
    time_keys = np.asarray([f"P{int(row.period)}|{int(row.time_utc_ns)}" for row in rows.itertuples(index=False)], dtype=object)
    block_keys = np.asarray(
        [f"P{int(row.period)}|B{int(row.block_id)}" for row in rows.itertuples(index=False)],
        dtype=object,
    )
    return PreparedMatch(match_id, coordinates, time_keys, block_keys)


def _kish(weights: np.ndarray) -> float:
    total = float(weights.sum())
    return 0.0 if total == 0.0 else total * total / float(np.square(weights).sum())


def _edge_flags(x: float, y: float) -> tuple[bool, bool, bool, bool]:
    """Flag 1 m grid cells intersecting named pitch-boundary line segments."""
    half = 0.5
    intersects = lambda centre, lo, hi: centre + half >= lo and centre - half <= hi
    touchline = intersects(y, -34.0, -34.0) or intersects(y, 34.0, 34.0)
    goal_line = intersects(x, -52.5, -52.5) or intersects(x, 52.5, 52.5)
    centre_line = intersects(x, 0.0, 0.0)

    # A 105 x 68 m pitch has penalty-area front lines 16.5 m from each goal
    # line (x=+/-36.0) and side lines at y=+/-20.16.  Do not flag their
    # infinite extensions: the cell rectangle must meet an actual line segment.
    front = (
        (intersects(x, -36.0, -36.0) or intersects(x, 36.0, 36.0))
        and intersects(y, -20.16, 20.16)
    )
    side = (
        (intersects(y, -20.16, -20.16) or intersects(y, 20.16, 20.16))
        and (intersects(x, -52.5, -36.0) or intersects(x, 36.0, 52.5))
    )
    return touchline, goal_line, centre_line, front or side


def _support_metrics(grid_tree: cKDTree, points: np.ndarray, item: PreparedMatch, h: float, truncate: float) -> dict[str, np.ndarray]:
    """Vectorized aggregate support for one match/bandwidth; no rows persist."""
    edge = grid_tree.sparse_distance_matrix(cKDTree(item.coordinates), max_distance=truncate * h, output_type="coo_matrix")
    row, col, distance = edge.row, edge.col, edge.data
    n = len(points); raw = np.bincount(row, minlength=n).astype(np.int32)
    nearest = np.full(n, np.inf); np.minimum.at(nearest, row, distance)
    weights = np.exp(-0.5 * np.square(distance / h))
    mass = np.bincount(row, weights=weights, minlength=n); mass2 = np.bincount(row, weights=np.square(weights), minlength=n)
    kish = np.divide(np.square(mass), mass2, out=np.zeros(n), where=mass2 > 0)
    _, time_code = np.unique(item.time_keys, return_inverse=True)
    unique_pairs = np.unique(row.astype(np.int64) * len(time_code) + time_code[col])
    unique = np.bincount((unique_pairs // len(time_code)).astype(int), minlength=n).astype(np.int32)
    _, block_code = np.unique(item.block_keys, return_inverse=True)
    block_base = len(block_code)
    unique_blocks = np.unique(row.astype(np.int64) * block_base + block_code[col])
    blocks = np.bincount((unique_blocks // block_base).astype(int), minlength=n).astype(np.int32)
    return {"raw": raw, "unique": unique, "blocks": blocks, "nearest": nearest, "mass": mass, "kish": kish}


def aggregate_support(matches: list[PreparedMatch], cfg: dict[str, Any]) -> pd.DataFrame:
    """Aggregate kernel support. Coordinates never leave this function's memory."""
    points = grid_points(cfg); bands = cfg["kernel"]["bandwidths_m"]; truncate = float(cfg["kernel"]["truncate_at_bandwidths"])
    profiles = cfg["support_profiles"]
    grid_tree = cKDTree(points)
    rows: list[dict[str, Any]] = []
    match_coverage: list[dict[str, Any]] = []
    for h in bands:
        by_match: dict[str, dict[str, np.ndarray]] = {}
        for item in matches:
            by_match[item.match_id] = _support_metrics(grid_tree, points, item, h, truncate)
        raw = np.stack([by_match[m.match_id]["raw"] for m in matches]); unique = np.stack([by_match[m.match_id]["unique"] for m in matches]); blocks = np.stack([by_match[m.match_id]["blocks"] for m in matches])
        nearest = np.stack([by_match[m.match_id]["nearest"] for m in matches]); mass = np.stack([by_match[m.match_id]["mass"] for m in matches]); kish = np.stack([by_match[m.match_id]["kish"] for m in matches])
        for profile_name, profile in profiles.items():
            per_match_passing = ((nearest <= h * float(profile["maximum_nearest_observation_distance_bandwidths"])) & (blocks >= int(profile["minimum_distinct_60_second_blocks_per_match"])) & (kish >= float(profile["minimum_kish_row_weight_concentration_count_per_match"])))
            required_matches = int(profile["matches_required"])
            if required_matches != len(matches):
                raise RuntimeError("configured match requirement does not match the governed seven-match population")
            passing = per_match_passing.sum(axis=0) == required_matches
            match_coverage.extend(
                {"bandwidth_m": float(h), "profile": profile_name, "support_fraction": float(per_match_passing[index].mean())}
                for index in range(len(matches))
            )
            for i, (x, y) in enumerate(points):
                touch, goal, centre, penalty = _edge_flags(float(x), float(y))
                finite_nearest = nearest[:, i][np.isfinite(nearest[:, i])]
                rows.append({"grid_x_m": float(x), "grid_y_m": float(y), "bandwidth_m": float(h), "profile": profile_name,
                             "support_pass": bool(passing[i]), "matches_supported": int(np.sum(raw[:, i] > 0)),
                             "raw_anchor_count": int(raw[:, i].sum()), "unique_time_anchor_count": int(unique[:, i].sum()),
                             "minimum_match_raw_anchor_count": int(raw[:, i].min()), "maximum_match_raw_anchor_count": int(raw[:, i].max()),
                             "minimum_match_unique_time_anchor_count": int(unique[:, i].min()), "maximum_match_unique_time_anchor_count": int(unique[:, i].max()),
                             "minimum_match_block_count": int(blocks[:, i].min()), "maximum_match_block_count": int(blocks[:, i].max()),
                             "maximum_nearest_distance_m": None if len(finite_nearest) == 0 else float(finite_nearest.max()), "mean_nearest_distance_m": None if len(finite_nearest) == 0 else float(finite_nearest.mean()),
                             "minimum_match_kernel_mass": float(mass[:, i].min()), "maximum_match_kernel_mass": float(mass[:, i].max()), "combined_kernel_mass": float(mass[:, i].sum()),
                             "minimum_match_kish_row_weight_concentration_count": float(kish[:, i].min()), "maximum_match_kish_row_weight_concentration_count": float(kish[:, i].max()), "combined_kish_row_weight_concentration_count": float(kish[:, i].sum()),
                             "kernel_mass_balance_min_over_mean": float(mass[:, i].min() / mass[:, i].mean()) if mass[:, i].mean() > 0 else 0.0,
                             "edge_touchline": touch, "edge_goal_line": goal, "edge_centre_line": centre, "edge_penalty_area_boundary": penalty})
    grid = pd.DataFrame(rows)
    # Kept only in memory for the aggregate minimum/maximum range in the
    # summary; match identifiers are never serialized.
    grid.attrs["per_match_support_coverage"] = pd.DataFrame(match_coverage)
    return grid


def validate_support_grid(grid: pd.DataFrame, cfg: dict[str, Any]) -> None:
    expected = cfg["publication"]["support_grid_schema"]
    if list(grid.columns) != expected:
        raise RuntimeError("aggregate support-grid schema differs from its allowlist")
    bad = [column for column in grid.columns if any(token in column.lower() for token in cfg["publication"]["forbidden_field_tokens"])]
    if bad:
        raise RuntimeError(f"aggregate support grid contains forbidden row-level fields: {bad}")
    expected_rows = len(grid_points(cfg)) * len(cfg["kernel"]["bandwidths_m"]) * len(cfg["support_profiles"])
    if len(grid) != expected_rows or grid.duplicated(["grid_x_m", "grid_y_m", "bandwidth_m", "profile"]).any():
        raise RuntimeError("aggregate support-grid cardinality is not deterministic")


def period_block_correction_audit(matches: list[PreparedMatch], grid: pd.DataFrame, cfg: dict[str, Any]) -> int:
    """Count support-pass cells changed by correcting the historical block collision."""
    legacy_matches = [
        replace(item, block_keys=np.asarray([key.split("|", 1)[1] for key in item.block_keys], dtype=object))
        for item in matches
    ]
    legacy = aggregate_support(legacy_matches, cfg)
    keys = ["grid_x_m", "grid_y_m", "bandwidth_m", "profile"]
    corrected_values = grid[keys + ["support_pass"]].copy()
    legacy_values = legacy[keys + ["support_pass"]].copy()
    # Per-match coverage remains an in-memory DataFrame attribute on the full
    # grids. Remove it from merge inputs: pandas requires equality-comparable
    # attrs when concatenating merge columns.
    corrected_values.attrs = {}
    legacy_values.attrs = {}
    merged = corrected_values.merge(legacy_values, on=keys, validate="one_to_one", suffixes=("_corrected", "_legacy"))
    return int((merged.support_pass_corrected != merged.support_pass_legacy).sum())


def summarize(grid: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    match_coverage = grid.attrs.get("per_match_support_coverage")
    if not isinstance(match_coverage, pd.DataFrame):
        raise RuntimeError("in-memory per-match support coverage is unavailable")
    result = []
    for (h, profile), group in grid.groupby(["bandwidth_m", "profile"], sort=True):
        support = group[group.support_pass]
        coverage_by_match = match_coverage[(match_coverage.bandwidth_m == h) & (match_coverage.profile == profile)].support_fraction
        if len(coverage_by_match) != len(MATCHES):
            raise RuntimeError("per-match coverage summary is incomplete")
        def coverage(mask: pd.Series) -> float: return float(mask.mean()) if len(mask) else 0.0
        result.append({"bandwidth_m": float(h), "profile": profile, "grid_cells": int(len(group)), "support_cells": int(len(support)), "common_support_fraction": coverage(group.support_pass),
                       "minimum_match_support_fraction": float(coverage_by_match.min()), "maximum_match_support_fraction": float(coverage_by_match.max()),
                       "mean_raw_anchor_count_supported": float(support.raw_anchor_count.mean()) if len(support) else 0.0,
                       "mean_unique_time_anchor_count_supported": float(support.unique_time_anchor_count.mean()) if len(support) else 0.0,
                       "minimum_match_blocks_supported": int(support.minimum_match_block_count.min()) if len(support) else 0,
                       "maximum_nearest_distance_supported_m": float(support.maximum_nearest_distance_m.max()) if len(support) else None,
                       "minimum_match_kish_row_weight_concentration_supported": float(support.minimum_match_kish_row_weight_concentration_count.min()) if len(support) else 0.0,
                       "mean_kernel_mass_balance_supported": float(support.kernel_mass_balance_min_over_mean.mean()) if len(support) else 0.0,
                       "touchline_coverage": coverage(group.loc[group.edge_touchline, "support_pass"]), "goal_line_coverage": coverage(group.loc[group.edge_goal_line, "support_pass"]),
                       "centre_line_coverage": coverage(group.loc[group.edge_centre_line, "support_pass"]), "penalty_boundary_coverage": coverage(group.loc[group.edge_penalty_area_boundary, "support_pass"])})
    return pd.DataFrame(result).sort_values(["profile", "bandwidth_m"], kind="mergesort").reset_index(drop=True)


def recommendation(summary: pd.DataFrame, cfg: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Record a reviewed human recommendation; never select a bandwidth automatically."""
    rec = dict(cfg["human_recommendation"])
    selected = summary[(summary.bandwidth_m == float(rec["bandwidth_m"])) & (summary.profile == rec["profile"])]
    if len(selected) != 1:
        raise RuntimeError("human support recommendation is absent from the prospectively bounded alternatives")
    rec["common_support_fraction"] = float(selected.iloc[0].common_support_fraction)
    rec["recommended"] = True
    return rec, (
        "Response-blind human selection: Conservative h=7.5 m balances locality with seven-match support in the "
        "reviewed bounded frontier. It was not selected by a prospectively frozen automatic rule. Human approval "
        "freezes it for the future descriptive response-map stage; this execution remains support-only."
    )


def render(summary: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for profile, group in summary.groupby("profile", sort=True):
        ax.plot(group.bandwidth_m, group.common_support_fraction, marker="o", label=profile.title())
    ax.set(xlabel="Gaussian bandwidth (m)", ylabel="Seven-match common-support fraction", title="Response-blind IDSSE spatial support frontier")
    ax.set_ylim(bottom=0); ax.legend(title="Support profile"); fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


def render_mask(grid: pd.DataFrame, rec: dict[str, Any], path: Path) -> None:
    """Render only the response-blind support mask for the recommendation."""
    if not rec.get("recommended"):
        return
    chosen = grid[(grid.bandwidth_m == rec["bandwidth_m"]) & (grid.profile == rec["profile"])].sort_values(["grid_y_m", "grid_x_m"], kind="mergesort")
    x = np.sort(chosen.grid_x_m.unique()); y = np.sort(chosen.grid_y_m.unique())
    mask = chosen.support_pass.to_numpy(bool).reshape(len(y), len(x))
    fig, ax = plt.subplots(figsize=(9, 5.8))
    image = ax.imshow(mask, origin="lower", extent=[x.min() - .5, x.max() + .5, y.min() - .5, y.max() + .5], interpolation="nearest", cmap="Blues", vmin=0, vmax=1, aspect="equal")
    ax.add_patch(plt.Rectangle((-52.5, -34), 105, 68, fill=False, color="black", lw=1.2))
    ax.axvline(0, color="black", lw=.8)
    ax.set(xlim=(-52.5, 52.5), ylim=(-34, 34), xlabel="Deeper ←   longitudinal position (m)   → Goalward", ylabel="Provider physical lateral position (m)", title=f"Response-blind support mask for human recommendation: {rec['profile']} h={rec['bandwidth_m']:g} m")
    colorbar = fig.colorbar(image, ax=ax, fraction=.035, pad=.02, ticks=[0, 1]); colorbar.ax.set_yticklabels(["masked", "supported"])
    fig.tight_layout(); path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, dpi=180); plt.close(fig)


def report(summary: pd.DataFrame, rec: dict[str, Any], note: str, manifest: dict[str, Any], path: Path) -> None:
    lines = ["# Localized Reorganization Heatmap — Support Preflight v1", "", "**Status:** response-blind support characterization; no response surface or response field was read.", "", "## Bounded alternatives", "", "| Profile | h (m) | Cells | Coverage | Match coverage range | Mean raw / unique anchors | Min blocks / Kish row-weight concentration | Max nearest (m) | Mass balance | Edge: touch / goal / centre / penalty |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary.itertuples(index=False):
        nearest = "—" if row.maximum_nearest_distance_supported_m is None else f"{row.maximum_nearest_distance_supported_m:.2f}"
        lines.append(f"| {row.profile} | {row.bandwidth_m:g} | {row.support_cells} | {row.common_support_fraction:.3%} | {row.minimum_match_support_fraction:.3%}–{row.maximum_match_support_fraction:.3%} | {row.mean_raw_anchor_count_supported:.1f} / {row.mean_unique_time_anchor_count_supported:.1f} | {row.minimum_match_blocks_supported} / {row.minimum_match_kish_row_weight_concentration_supported:.2f} | {nearest} | {row.mean_kernel_mass_balance_supported:.3f} | {row.touchline_coverage:.3%} / {row.goal_line_coverage:.3%} / {row.centre_line_coverage:.3%} / {row.penalty_boundary_coverage:.3%} |")
    outside = int(manifest["provider_native_anchor_count_outside_nominal_pitch"])
    total = int(manifest["observation_count"])
    corrected = int(manifest["period_aware_block_correction_support_pass_cells_changed"])
    correction = "did not change any candidate support-pass cell or mask" if corrected == 0 else f"changed {corrected} candidate support-pass cells"
    lines += ["", "## Support-only recommendation", "", note, "", json.dumps(rec, indent=2, sort_keys=True), "", "## Boundary", "", f"This report used only governed observation identity/support fields and in-memory `t-2 s` attacker coordinates. It did not read or construct a response, a near-minus-middle outcome, a coefficient, or a response-colored surface. The future response-map specification is frozen separately and still has not been executed. Native coordinates were retained without clipping or exclusion: {outside:,} of {total:,} anchors ({outside / total:.3%}) lay outside the nominal pitch rectangle, while kernels were evaluated only at legal-pitch grid cells.", "", f"Correcting period-aware 60-second block identity {correction}; it corrects reported temporal-block counts without changing the underlying eligible anchor population.", "", "Kish row-weight concentration counts describe local kernel-weight concentration, not independent observations; simultaneous attackers can increase them. Unique-time-anchor and period-aware 60-second-block counts provide separate temporal-support diagnostics.", "", "## Provenance", "", f"- protocol SHA-256: `{manifest['protocol_sha256']}`", f"- configuration SHA-256: `{manifest['configuration_sha256']}`", f"- source SHA-256: `{manifest['source_sha256']}`", f"- support-grid SHA-256: `{manifest['support_grid_sha256']}`"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(output: Path = DEFAULT_OUTPUT, report_path: Path = DEFAULT_REPORT, figure_path: Path = DEFAULT_FIGURE) -> dict[str, Any]:
    cfg = config(); registry = _registry(cfg)
    prepared = [prepare_match(match, registry[registry.match_id == match].reset_index(drop=True)) for match in MATCHES]
    grid = aggregate_support(prepared, cfg); validate_support_grid(grid, cfg)
    block_correction_changed_cells = period_block_correction_audit(prepared, grid, cfg)
    output.mkdir(parents=True, exist_ok=True)
    grid_path = output / "support_grid.parquet"; pl.DataFrame(grid).write_parquet(grid_path, compression="zstd", statistics=True)
    if grid_path.stat().st_size > int(cfg["publication"]["maximum_support_grid_bytes"]):
        raise RuntimeError("aggregate support grid exceeds the public size boundary")
    summary = summarize(grid, cfg); summary_path = output / "support_profile_summary.csv"; summary.to_csv(summary_path, index=False)
    rec, note = recommendation(summary, cfg); render(summary, figure_path); mask_path = figure_path.with_name("support_mask.png"); render_mask(grid, rec, mask_path)
    all_coordinates = np.vstack([item.coordinates for item in prepared])
    outside_pitch = int(((np.abs(all_coordinates[:, 0]) > 52.5) | (np.abs(all_coordinates[:, 1]) > 34.0)).sum())
    manifest = {"status": "RESPONSE_BLIND_SUPPORT_PREFLIGHT_COMPLETE", "matches": list(MATCHES), "observation_count": int(len(registry)), "provider_native_coordinates_finite": True, "provider_native_anchor_count_outside_nominal_pitch": outside_pitch, "coordinate_clipping_applied": False, "protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "source_sha256": sha(Path(__file__)), "support_grid_sha256": sha(grid_path), "support_profile_summary_sha256": sha(summary_path), "support_frontier_figure_sha256": sha(figure_path), "support_mask_figure_sha256": sha(mask_path), "response_fields_selected": False, "anchor_coordinates_serialized": False, "response_surface_rendered": False, "future_response_map_mask_frozen": True, "temporal_block_identity": "period_x_60_second_block", "period_aware_block_correction_support_pass_cells_changed": block_correction_changed_cells, "recommendation": rec}
    write_json(output / "manifest.json", manifest); report(summary, rec, note, manifest, report_path)
    write_json(output / "hard_qc.json", {"aggregate_schema_allowlist": True, "response_fields_selected": False, "anchor_coordinates_serialized": False, "seven_matches_exact": {item.match_id for item in prepared} == set(MATCHES), "provider_native_coordinates_finite": True, "coordinate_clipping_applied": False, "period_aware_temporal_blocks": True, "period_aware_block_correction_support_pass_cells_changed": block_correction_changed_cells, "support_grid_under_10_mib": True})
    write_json(output / "hashes.json", {name: sha(output / name) for name in ("support_grid.parquet", "support_profile_summary.csv", "manifest.json", "hard_qc.json")})
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args(); execute(args.output, args.report, args.figure); return 0


if __name__ == "__main__":
    raise SystemExit(main())
