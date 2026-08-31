"""Execute frozen continuous attacker-movement v1 on held-out Metrica Game 2."""
from __future__ import annotations

import argparse
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
import attacking_continuous_movement_game1_v1 as frozen  # noqa: E402
from infrastructure import canonical_tracking  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402


PROTOCOL = ROOT / "docs" / "protocols" / "attacking_continuous_movement_v1.md"
HELDOUT_PROTOCOL = ROOT / "docs" / "protocols" / "attacking_continuous_movement_game2_heldout_v1.md"
STAGE_A = ROOT / "outputs" / "attacking_continuous_movement_game2_stage_a"
STAGE_A_RESULT = ROOT / "docs" / "results" / "attacking_continuous_movement_game2_stage_a.md"
DEFAULT_OUTPUT = ROOT / "outputs" / "attacking_continuous_movement_game2_v1"
MATCH_ID = "metrica:sample-game-2"
WINDOWS = frozen.WINDOWS
GRID_S = frozen.GRID_S
RAW_DT_S = frozen.RAW_DT_S
TIME_TOL = frozen.TIME_TOL
GEOM_TOL = frozen.GEOM_TOL


def sha256(path: Path) -> str:
    return frozen.sha256(path)


def write_json(path: Path, value: Any) -> None:
    frozen.write_json(path, value)


def verify_stage_a() -> dict[str, Any]:
    hashes = json.loads((STAGE_A / "governed_output_hashes.json").read_text(encoding="utf-8"))
    mismatches = [name for name, expected in hashes.items() if sha256(STAGE_A / name) != expected]
    reproduction = json.loads((STAGE_A / "reproduction_verification.json").read_text(encoding="utf-8"))
    result = json.loads((STAGE_A / "stage_a_result.json").read_text(encoding="utf-8"))
    registry = pd.read_csv(STAGE_A / "trajectory_validity_registry.csv")
    segments = pd.read_csv(STAGE_A / "valid_support_segments.csv")
    exact = (
        result["stage_a_classification"] == "READY"
        and not mismatches
        and reproduction["all_governed_outputs_byte_identical"]
        and result["raw_support"]["canonical_outfield_rows"] == 3_387_744
        and result["raw_support"]["universal_invalid_rows"] == 564_620
        and result["raw_support"]["hard_jump_invalid_rows_before_overlap"] == 726_886
        and result["raw_support"]["sustained_duplicate_invalid_rows_before_overlap"] == 6_419
        and result["raw_support"]["overlap_hard_and_duplicate_rows"] == 3_209
        and result["raw_support"]["final_valid_rows"] == 2_093_028
        and result["valid_support_segments"] == 134
        and len(registry) == 138
        and len(segments) == 134
        and int(segments["frame_count"].sum()) == 2_093_028
    )
    if not exact:
        raise RuntimeError(f"Frozen Stage-A support integrity failed; mismatches={mismatches}")
    return {
        "classification": "READY",
        "governed_hash_files": len(hashes),
        "governed_hashes_valid": not mismatches,
        "independent_reproduction_valid": bool(reproduction["all_governed_outputs_byte_identical"]),
        "registry_sha256": sha256(STAGE_A / "trajectory_validity_registry.csv"),
        "support_segments_sha256": sha256(STAGE_A / "valid_support_segments.csv"),
        "valid_raw_rows": 2_093_028,
        "support_segments": 134,
    }


def load_game2_from_frozen_support() -> tuple[list[frozen.PlayerPeriod], dict[int, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    stage_a = verify_stage_a()
    segment_table = pd.read_csv(STAGE_A / "valid_support_segments.csv")
    home, away = metrica.game_paths(ROOT, 2)
    frame_index = metrica.read_provider_frame_index(home)
    dataset = metrica.load_dataset(home, away)
    traces: dict[str, list[pd.DataFrame]] = {}
    metadata: dict[str, str] = {}
    for chunk in metrica.iter_canonical_polars_chunks(
        dataset, frame_index, match_id=MATCH_ID, frames_per_chunk=2500
    ):
        canonical_tracking.validate_chunk(chunk)
        players = chunk.filter((pl.col("entity_type") == "player") & (~pl.col("is_goalkeeper")))
        q = pd.DataFrame(players.to_dicts())
        for key, group in q.groupby("player_key", sort=False):
            traces.setdefault(str(key), []).append(
                group[[
                    "team_key", "period", "frame_id_provider", "time_period_s", "time_match_s",
                    "x_m", "y_m", "is_present", "coordinate_valid", "support_state",
                ]]
            )
            metadata[str(key)] = str(group["team_key"].iloc[0])

    player_periods: list[frozen.PlayerPeriod] = []
    period_frames: dict[int, dict[str, Any]] = {}
    consumed_segment_ids: list[str] = []
    consumed_raw_rows = 0
    for player_key in sorted(traces):
        trace = pd.concat(traces[player_key], ignore_index=True)
        team_key = metadata[player_key]
        player_number = player_key.rsplit(":", 1)[1]
        for period_value, group in trace.groupby("period", sort=True):
            period = int(period_value)
            group = group.sort_values("time_match_s", kind="mergesort").reset_index(drop=True)
            frames = group["frame_id_provider"].astype(int).to_numpy()
            tperiod = group["time_period_s"].to_numpy(np.float64)
            tmatch = group["time_match_s"].to_numpy(np.float64)
            raw_xy = group[["x_m", "y_m"]].to_numpy(np.float64)
            base = (
                group["is_present"].fillna(False).to_numpy(bool)
                & group["coordinate_valid"].fillna(False).to_numpy(bool)
                & group["support_state"].eq("observed").to_numpy(bool)
                & np.isfinite(raw_xy).all(axis=1)
            )
            links = np.zeros(len(group), dtype=bool)
            if len(group) > 1:
                links[1:] = (
                    (np.diff(frames) == 1)
                    & (np.abs(np.diff(tmatch) - RAW_DT_S) <= TIME_TOL)
                    & (np.diff(tperiod) > 0)
                )
            if period not in period_frames:
                period_frames[period] = {
                    "origin_time_period_s": float(tperiod[0]),
                    "frame_ids": frames.copy(),
                    "time_period_s": tperiod.copy(),
                    "time_match_s": tmatch.copy(),
                }
            else:
                ref = period_frames[period]
                if not (
                    np.array_equal(ref["frame_ids"], frames)
                    and np.allclose(ref["time_period_s"], tperiod, atol=TIME_TOL, rtol=0)
                    and np.allclose(ref["time_match_s"], tmatch, atol=TIME_TOL, rtol=0)
                ):
                    raise RuntimeError("Canonical player-period grids differ")

            frozen_segments = segment_table[
                (segment_table["player_key"] == player_key)
                & (segment_table["period"] == period)
            ].sort_values("start_frame_provider", kind="mergesort")
            segment_valid = np.zeros(len(frames), dtype=bool)
            segment_bounds: list[tuple[int, int, str]] = []
            frame_lookup = {int(frame): i for i, frame in enumerate(frames)}
            for row in frozen_segments.itertuples(index=False):
                start = frame_lookup.get(int(row.start_frame_provider))
                end = frame_lookup.get(int(row.end_frame_provider))
                if start is None or end is None or end < start:
                    raise RuntimeError(f"Frozen segment bounds unavailable: {row.segment_id}")
                if end - start + 1 != int(row.frame_count):
                    raise RuntimeError(f"Frozen segment frame count differs: {row.segment_id}")
                if not base[start : end + 1].all() or (end > start and not links[start + 1 : end + 1].all()):
                    raise RuntimeError(f"Frozen segment cannot be consumed as valid raw support: {row.segment_id}")
                if not (
                    abs(float(tperiod[start]) - float(row.start_time_period_s)) <= TIME_TOL
                    and abs(float(tperiod[end]) - float(row.end_time_period_s)) <= TIME_TOL
                    and abs(float(tmatch[start]) - float(row.start_time_match_s)) <= TIME_TOL
                    and abs(float(tmatch[end]) - float(row.end_time_match_s)) <= TIME_TOL
                ):
                    raise RuntimeError(f"Frozen segment clocks differ: {row.segment_id}")
                if segment_valid[start : end + 1].any():
                    raise RuntimeError(f"Frozen segments overlap: {row.segment_id}")
                segment_valid[start : end + 1] = True
                segment_bounds.append((start, end, str(row.segment_id)))
                consumed_segment_ids.append(str(row.segment_id))
                consumed_raw_rows += int(row.frame_count)

            pp = frozen.PlayerPeriod(
                player_key=player_key,
                team_key=team_key,
                player_number=player_number,
                period=period,
                frame_ids=frames,
                time_period_s=tperiod,
                time_match_s=tmatch,
                raw_xy=raw_xy,
                raw_valid_base=base,
                registry_invalid=base & ~segment_valid,
                continuity_links=links,
                blocks=[],
                center_to_block={},
            )
            origin = period_frames[period]["origin_time_period_s"]
            for start, end, segment_id in segment_bounds:
                block = frozen._build_block(pp, start, end, len(pp.blocks) + 1, origin)
                if block is None:
                    continue
                block.block_id = segment_id
                block_index = len(pp.blocks)
                pp.blocks.append(block)
                for local, center in enumerate(block.center_indices):
                    pp.center_to_block[int(center)] = (block_index, local)
            player_periods.append(pp)

    if consumed_raw_rows != 2_093_028 or len(consumed_segment_ids) != 134:
        raise RuntimeError("Frozen Stage-A support was not consumed completely")
    if consumed_segment_ids != segment_table["segment_id"].tolist():
        # Compare identities exactly while permitting deterministic loader ordering.
        if sorted(consumed_segment_ids) != sorted(segment_table["segment_id"].tolist()):
            raise RuntimeError("Frozen Stage-A segment identities differ")
    provenance = metrica.canonical_provenance(
        dataset, home, away,
        provider_match_id="Sample Game 2",
        canonical_match_id=MATCH_ID,
    )
    support_consumption = {
        **stage_a,
        "consumed_segment_id_count": len(consumed_segment_ids),
        "consumed_raw_row_count": consumed_raw_rows,
        "no_support_rediscovery": True,
        "no_registry_revision": True,
    }
    return player_periods, period_frames, provenance, support_consumption


def exclusion_reason(pp: frozen.PlayerPeriod, start: int, end: int) -> str:
    if start < 0:
        return "window_before_period_start"
    if start - 3 < 0 or end + 3 >= len(pp.frame_ids):
        return "smoothing_edge"
    required = slice(start - 3, end + 4)
    if pp.registry_invalid[required].any():
        return "frozen_stage_a_registry_or_segment_boundary"
    if not pp.raw_valid_base[required].all():
        return "raw_support_invalid"
    if not pp.continuity_links[start - 2 : end + 4].all():
        return "continuity_break"
    return "smoothed_window_not_contiguous"


def calculate_window(
    player_periods: list[frozen.PlayerPeriod],
    period_frames: dict[int, dict[str, Any]],
    window_s: float,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    steps25 = int(round(window_s / RAW_DT_S))
    ticks10 = int(round(window_s / 0.1))
    base_columns = {
        "observation_id": [], "match_id": [], "period": [], "frame_id_provider": [],
        "player_key": [], "team_key": [], "window_s": [], "time_period_s": [],
        "time_match_s": [], "support_segment_id": [],
    }
    support = base_columns | {"eligible": [], "exclusion_reason": []}
    features = {key: [] for key in base_columns} | {
        "delta_x_m": [], "delta_y_m": [], "displacement_m": [], "path_length_m": [],
        "straightness": [], "straightness_valid": [],
    }
    comparisons = {key: [] for key in base_columns} | {
        "matched_10hz": [], "delta_x_m_25hz": [], "delta_x_m_10hz": [],
        "delta_y_m_25hz": [], "delta_y_m_10hz": [], "path_length_m_25hz": [],
        "path_length_m_10hz": [], "straightness_25hz": [], "straightness_10hz": [],
        "straightness_valid_25hz": [], "straightness_valid_10hz": [],
    }
    for pp in player_periods:
        origin = float(period_frames[pp.period]["origin_time_period_s"])
        for end in range(0, len(pp.frame_ids), 5):
            start = end - steps25
            lookup_start = pp.center_to_block.get(start)
            lookup_end = pp.center_to_block.get(end)
            eligible = bool(
                start >= 0 and lookup_start is not None and lookup_end is not None
                and lookup_start[0] == lookup_end[0]
                and lookup_end[1] - lookup_start[1] == steps25
                and abs((pp.time_period_s[end] - pp.time_period_s[start]) - window_s) <= TIME_TOL
                and abs((pp.time_period_s[end] - origin) / GRID_S - round((pp.time_period_s[end] - origin) / GRID_S)) <= TIME_TOL
            )
            segment_id = pp.blocks[lookup_end[0]].block_id if eligible else None
            obs_id = f"{MATCH_ID}|{pp.period}|{pp.frame_ids[end]}|{pp.player_key}|{int(window_s*1000)}"
            row = {
                "observation_id": obs_id, "match_id": MATCH_ID, "period": pp.period,
                "frame_id_provider": str(pp.frame_ids[end]), "player_key": pp.player_key,
                "team_key": pp.team_key, "window_s": window_s,
                "time_period_s": float(pp.time_period_s[end]), "time_match_s": float(pp.time_match_s[end]),
                "support_segment_id": segment_id,
            }
            for key, value in row.items():
                support[key].append(value)
            support["eligible"].append(eligible)
            support["exclusion_reason"].append("eligible" if eligible else exclusion_reason(pp, start, end))
            if not eligible:
                continue
            block = pp.blocks[lookup_start[0]]
            g25 = frozen.geometry(block.positions25, block.cumulative25, lookup_start[1], lookup_end[1])
            for key, value in row.items():
                features[key].append(value)
                comparisons[key].append(value)
            for key, value in g25.items():
                features[key].append(value)
            start_tick = int(round((float(pp.time_period_s[start]) - origin) / 0.1))
            end_tick = start_tick + ticks10
            i10 = block.tick10_to_index.get(start_tick)
            j10 = block.tick10_to_index.get(end_tick)
            matched = bool(i10 is not None and j10 is not None and j10 - i10 == ticks10)
            comparisons["matched_10hz"].append(matched)
            g10 = frozen.geometry(block.positions10, block.cumulative10, i10, j10) if matched else None
            for feature in ("delta_x_m", "delta_y_m", "path_length_m", "straightness"):
                comparisons[f"{feature}_25hz"].append(g25[feature])
                comparisons[f"{feature}_10hz"].append(None if g10 is None else g10[feature])
            comparisons["straightness_valid_25hz"].append(g25["straightness_valid"])
            comparisons["straightness_valid_10hz"].append(None if g10 is None else g10["straightness_valid"])
    return pl.DataFrame(support), pl.DataFrame(features), pl.DataFrame(comparisons)


def mathematical_qc(features: pl.DataFrame, window_s: float) -> list[dict[str, Any]]:
    dx = features["delta_x_m"].to_numpy()
    dy = features["delta_y_m"].to_numpy()
    displacement = features["displacement_m"].to_numpy()
    path = features["path_length_m"].to_numpy()
    valid = features["straightness_valid"].to_numpy()
    straight = features["straightness"].to_numpy()
    straight_filled = np.array([np.nan if value is None else float(value) for value in straight])
    checks = {
        "duplicate_observation_ids": features.height - features["observation_id"].n_unique(),
        "null_support_segment_ids": features["support_segment_id"].null_count(),
        "nonfinite_scientific_values": int(sum(np.count_nonzero(~np.isfinite(v)) for v in (dx, dy, displacement, path)) + np.count_nonzero(valid & ~np.isfinite(straight_filled))),
        "negative_path": int(np.count_nonzero(path < 0.0)),
        "negative_displacement": int(np.count_nonzero(displacement < 0.0)),
        "path_below_displacement": int(np.count_nonzero(path + GEOM_TOL < displacement)),
        "valid_straightness_outside_unit_interval": int(np.count_nonzero(valid & ((straight_filled < -GEOM_TOL) | (straight_filled > 1.0 + GEOM_TOL)))),
        "straightness_null_validity_mismatch": int(np.count_nonzero(valid == np.isnan(straight_filled))),
        "zero_path_nonzero_displacement": int(np.count_nonzero((path == 0.0) & (displacement != 0.0))),
        "zero_path_valid_straightness": int(np.count_nonzero((path == 0.0) & valid)),
        "positive_path_invalid_straightness": int(np.count_nonzero((path > 0.0) & ~valid)),
        "positive_path_zero_displacement_nonzero_straightness": int(np.count_nonzero((path > 0.0) & (displacement == 0.0) & (straight_filled != 0.0))),
    }
    return [{"window_s": window_s, "check": name, "violation_count": int(value), "pass": int(value) == 0} for name, value in checks.items()]


def descriptive_comparison(game2: dict[str, Any]) -> pl.DataFrame:
    game1 = json.loads(
        (ROOT / "outputs" / "attacking_continuous_movement_game1_v1" / "final_results.json").read_text(encoding="utf-8")
    )
    rows = []
    for window in WINDOWS:
        key = f"{int(window)}s"
        for feature in ("delta_x_m", "delta_y_m", "displacement_m", "path_length_m", "straightness_valid"):
            for statistic in ("min", "q25", "median", "q75", "max"):
                rows.append({
                    "window_s": window, "feature": feature, "statistic": statistic,
                    "game1_value": game1["summaries"][key][feature][statistic],
                    "game2_value": game2[key][feature][statistic],
                    "validation_gate": False,
                })
        for statistic in ("zero_path_rate", "invalid_straightness_rate"):
            rows.append({
                "window_s": window, "feature": statistic, "statistic": "rate",
                "game1_value": game1["summaries"][key][statistic],
                "game2_value": game2[key][statistic], "validation_gate": False,
            })
    return pl.DataFrame(rows)


def execute(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fixtures, invariance = frozen.run_fixtures()
    player_periods, period_frames, provenance, support_consumption = load_game2_from_frozen_support()
    distributions: list[pl.DataFrame] = []
    frequency_rows: list[dict[str, Any]] = []
    exclusion_tables: list[pl.DataFrame] = []
    math_rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    eligibility: dict[str, Any] = {}
    scientific_files: list[str] = []
    hard_checks: dict[str, bool] = {
        "stage_a_support_consumed": support_consumption["consumed_raw_row_count"] == 2_093_028,
        "stage_a_segments_consumed": support_consumption["consumed_segment_id_count"] == 134,
        "fixtures": bool(fixtures["pass"].all()), "invariance": bool(invariance["pass"].all()),
        "primary_interpolation": False, "clipping": False, "epsilon_denominator": False,
        "low_speed_threshold": False, "period_crossing": False,
    }
    for window in WINDOWS:
        support, features, comparison = calculate_window(player_periods, period_frames, window)
        suffix = f"{int(window)}s"
        paths = {
            "support": output / f"evaluation_support_{suffix}.parquet",
            "features": output / f"features_{suffix}.parquet",
            "comparison": output / f"frequency_comparison_{suffix}.parquet",
        }
        support.write_parquet(paths["support"], compression="zstd", statistics=True)
        features.write_parquet(paths["features"], compression="zstd", statistics=True)
        comparison.write_parquet(paths["comparison"], compression="zstd", statistics=True)
        scientific_files.extend(path.name for path in paths.values())
        summaries[suffix] = frozen.feature_summary(features, window)
        distributions.append(frozen.distribution_rows(features))
        rows, eligibility_result = frozen.frequency_metrics(comparison, window)
        frequency_rows.extend(rows)
        eligibility[suffix] = eligibility_result
        math_rows.extend(mathematical_qc(features, window))
        exclusion_tables.append(
            support.group_by(["window_s", "eligible", "exclusion_reason"]).len().sort(["window_s", "eligible", "exclusion_reason"])
        )
        hard_checks[f"unique_support_ids_{suffix}"] = support["observation_id"].n_unique() == support.height
        hard_checks[f"unique_feature_ids_{suffix}"] = features["observation_id"].n_unique() == features.height
        hard_checks[f"eligible_identity_match_{suffix}"] = support.filter(pl.col("eligible"))["observation_id"].to_list() == features["observation_id"].to_list()
        hard_checks[f"all_features_link_to_frozen_segment_{suffix}"] = features["support_segment_id"].null_count() == 0

    distribution_table = pl.concat(distributions, how="vertical")
    frequency_table = pl.DataFrame(frequency_rows)
    exclusion_table = pl.concat(exclusion_tables, how="vertical")
    math_table = pl.DataFrame(math_rows)
    comparison_table = descriptive_comparison(summaries)
    for name, table in (
        ("distribution_diagnostics.csv", distribution_table),
        ("frequency_metrics.csv", frequency_table),
        ("exclusion_summary.csv", exclusion_table),
        ("mathematical_qc.csv", math_table),
        ("game1_game2_descriptive_comparison.csv", comparison_table),
        ("fixtures.csv", fixtures), ("invariance_results.csv", invariance),
    ):
        table.write_csv(output / name, float_scientific=False)
        scientific_files.append(name)

    hard_checks["all_mathematical_qc"] = bool(math_table["pass"].all())
    frequency_pass = bool(frequency_table["pass"].all())
    hard_qc = bool(
        all(value for key, value in hard_checks.items() if key not in {
            "primary_interpolation", "clipping", "epsilon_denominator", "low_speed_threshold", "period_crossing"
        })
        and not any(hard_checks[key] for key in (
            "primary_interpolation", "clipping", "epsilon_denominator", "low_speed_threshold", "period_crossing"
        ))
    )
    candidate = "A_candidate" if hard_qc and frequency_pass else ("B_candidate" if hard_qc else "C")
    results = {
        "classification": "PENDING_DETERMINISTIC_REPRODUCTION",
        "pre_reproduction_classification": candidate,
        "feature_set": ["delta_x_m", "delta_y_m", "path_length_m", "straightness", "straightness_valid"],
        "windows_s": list(WINDOWS), "evaluation_grid_s": GRID_S,
        "eligible_outfield_players": len({pp.player_key for pp in player_periods}),
        "eligible_player_periods_available": len(player_periods),
        "stage_a_support": support_consumption, "summaries": summaries,
        "eligibility_frequency": eligibility, "hard_checks": hard_checks,
        "hard_qc_pre_reproduction_pass": hard_qc,
        "frequency_all_gates_pass": frequency_pass,
        "frequency_gate_pass_count": int(frequency_table["pass"].sum()),
        "frequency_gate_total": frequency_table.height,
        "bridge_protocol_authorized": False,
    }
    write_json(output / "pre_reproduction_results.json", results)
    scientific_files.append("pre_reproduction_results.json")
    manifest = {
        "protocol": str(PROTOCOL.relative_to(ROOT)), "protocol_sha256": sha256(PROTOCOL),
        "heldout_protocol": str(HELDOUT_PROTOCOL.relative_to(ROOT)), "heldout_protocol_sha256": sha256(HELDOUT_PROTOCOL),
        "stage_a_result": str(STAGE_A_RESULT.relative_to(ROOT)), "stage_a_result_sha256": sha256(STAGE_A_RESULT),
        "stage_a_registry_sha256": support_consumption["registry_sha256"],
        "stage_a_support_segments_sha256": support_consumption["support_segments_sha256"],
        "frozen_game1_source": str(Path(frozen.__file__).relative_to(ROOT)),
        "frozen_game1_source_sha256": sha256(Path(frozen.__file__)),
        "source": str(Path(__file__).relative_to(ROOT)), "source_sha256": sha256(Path(__file__)),
        "canonical_contract_sha256": sha256(ROOT / "docs" / "canonical_tracking_contract.md"),
        "canonical_module_sha256": sha256(ROOT / "src" / "infrastructure" / "canonical_tracking.py"),
        "metrica_adapter_sha256": sha256(ROOT / "src" / "infrastructure" / "kloppy_metrica_adapter.py"),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "polars": pl.__version__, "canonical_provenance": provenance,
        "scientific_output_files": scientific_files,
        "support_discovery_performed": False, "support_registry_revised": False,
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "scientific_output_hashes.json", {name: sha256(output / name) for name in scientific_files})


def verify_reproduction(primary: Path, rerun: Path) -> None:
    primary_manifest = json.loads((primary / "manifest.json").read_text(encoding="utf-8"))
    rerun_manifest = json.loads((rerun / "manifest.json").read_text(encoding="utf-8"))
    governed = [*primary_manifest["scientific_output_files"], "manifest.json", "scientific_output_hashes.json"]
    same_list = governed == [*rerun_manifest["scientific_output_files"], "manifest.json", "scientific_output_hashes.json"]
    comparisons = []
    for name in governed:
        left, right = primary / name, rerun / name
        comparisons.append({
            "file": name, "primary_sha256": sha256(left) if left.exists() else None,
            "rerun_sha256": sha256(right) if right.exists() else None,
            "byte_identical": bool(left.exists() and right.exists() and left.read_bytes() == right.read_bytes()),
        })
    passed = bool(same_list and all(row["byte_identical"] for row in comparisons))
    write_json(primary / "reproduction_verification.json", {
        "files_compared": len(comparisons), "same_governed_file_list": same_list,
        "all_byte_identical": passed, "comparisons": comparisons,
    })
    base = json.loads((primary / "pre_reproduction_results.json").read_text(encoding="utf-8"))
    hard = bool(base["hard_qc_pre_reproduction_pass"] and passed)
    classification = "A" if hard and base["frequency_all_gates_pass"] else ("B" if hard else "C")
    final = {
        **base, "classification": classification, "deterministic_reproduction_pass": passed,
        "hard_qc_pass": hard, "bridge_protocol_authorized": classification == "A",
    }
    write_json(primary / "final_results.json", final)
    write_json(primary / "final_output_hashes.json", {
        name: sha256(primary / name)
        for name in [*governed, "reproduction_verification.json", "final_results.json"]
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.verify_against is None:
        execute(args.output)
    else:
        verify_reproduction(args.output, args.verify_against)
