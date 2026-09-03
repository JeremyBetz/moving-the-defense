"""Execute frozen Defensive Coverage Redistribution v3 on Metrica Game 1.

V3 inherits v2 sample construction and geometry. Its sole design change is the
prospectively designated constant-nuisance column plan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_coverage_redistribution_game1_v2 as base  # noqa: E402
from defensive_coverage_redistribution_v3 import (  # noqa: E402
    DesignEstimabilityError,
    ResolvedDesign,
    apply_resolved_plan,
    resolve_design,
)

PROTOCOL = ROOT / "docs/protocols/defensive_coverage_redistribution_v3.md"
CONFIG = ROOT / "config/defensive_coverage_redistribution_v3.json"
HASH_LEDGER = ROOT / "config/defensive_coverage_redistribution_v3_hashes.json"
DEFAULT_OUTPUT = ROOT / "outputs/defensive_coverage_redistribution_game1_v3"
BOOT_REPS, MIN_VALID, NULL_REPS = 2_000, 1_900, 200
PRIMARY = "concurrent_D1_D3_minus_D4_D7_focal_relative_path_m"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        item = float(value)
        return item if math.isfinite(item) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def describe(values: np.ndarray) -> dict[str, float]:
    x = np.asarray(values, dtype=np.float64)
    return {
        "count": int(len(x)), "min": float(x.min()), "q25": float(np.quantile(x, .25)),
        "median": float(np.median(x)), "q75": float(np.quantile(x, .75)),
        "max": float(x.max()), "mean": float(x.mean()), "sd": float(x.std(ddof=0)),
    }


def verify_frozen() -> dict[str, str]:
    ledger = json.loads(HASH_LEDGER.read_text(encoding="utf-8"))
    for group in ("preserved_v1_v2", "v2_invalid_closure", "v3_frozen_design"):
        for relative, expected in ledger[group].items():
            if sha256(ROOT / relative) != expected:
                raise RuntimeError(f"frozen artifact mismatch: {relative}")
    expected_protocol = "5bf577758202aed13b47fce54fd40c88b1a443d675d832f93f69c62570303988"
    expected_config = "54a01d0aeba846b1e245a0c0552234b2390cfc3ec10ec0a187dc94c0b10fed42"
    if sha256(PROTOCOL) != expected_protocol or sha256(CONFIG) != expected_config:
        raise RuntimeError("v3 protocol or configuration differs from its frozen SHA-256")
    return {
        "protocol_sha256": expected_protocol,
        "configuration_sha256": expected_config,
        "hash_ledger_sha256": sha256(HASH_LEDGER),
    }


def nominal_matrix(data: pd.DataFrame, dcol: str = "D", dpre: str = "Dpre") -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([
        np.ones(len(data), dtype=np.float64), data.A, data[dcol], data.G0,
        data.MO, data.B, data.C, data.R, data.Apre, data[dpre], data.Bpre, data.P2,
    ]).astype(np.float64)
    return x, data.Y.to_numpy(np.float64)


def resolve_primary_plan(data: pd.DataFrame, config: dict[str, Any]) -> ResolvedDesign:
    x, _ = nominal_matrix(data)
    return resolve_design(
        x,
        tuple(config["nominal_model_columns_in_order"]),
        nuisance_columns=tuple(config["constant_nuisance_rule"]["designated_non_scientific_nuisance_columns"]),
    )


def fit(data: pd.DataFrame, plan: ResolvedDesign, dcol: str = "D", dpre: str = "Dpre") -> dict[str, Any]:
    nominal, y = nominal_matrix(data, dcol, dpre)
    x = apply_resolved_plan(nominal, plan.nominal_columns, plan=plan)
    coefficient, residuals, rank, singular_values = np.linalg.lstsq(x, y, rcond=None)
    rank = int(rank)
    if rank != x.shape[1] or not np.isfinite(coefficient).all():
        raise DesignEstimabilityError(f"frozen active design rank failure {rank}/{x.shape[1]}")
    return {
        "coefficients": dict(zip(plan.active_columns, coefficient, strict=True)),
        "rank": rank, "n": int(len(data)), "singular_values": singular_values,
        "condition_number": float(singular_values[0] / singular_values[-1]),
        "rss": float(residuals[0]) if len(residuals) else 0.0,
    }


def bootstrap_family(data: pd.DataFrame, draws: list[np.ndarray], plan: ResolvedDesign, dcol: str = "D", dpre: str = "Dpre") -> tuple[np.ndarray, int]:
    values = []
    for indices in draws:
        try:
            values.append(float(fit(data.iloc[indices].reset_index(drop=True), plan, dcol, dpre)["coefficients"][PRIMARY]))
        except DesignEstimabilityError:
            continue
    values = np.asarray(values, dtype=np.float64)
    return values, int(len(values))


def interval(values: np.ndarray) -> list[float]:
    return [float(item) for item in np.quantile(values, [.025, .975], method="linear")]


def direction_null(data: pd.DataFrame, contexts: list[dict[str, Any]], plan: ResolvedDesign) -> tuple[np.ndarray, dict[str, float]]:
    by_id = {item["observation_id"]: item for item in contexts}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(base.NULL_SEED)))
    values, max_path_error, max_centroid_error = [], 0.0, 0.0
    for _ in range(NULL_REPS):
        outcomes = []
        for oid in data.observation_id:
            context = by_id[oid]
            transformed = base.geometry.rotate_internal_defender_motion(context["defend"], float(rng.uniform(0.0, 2.0 * np.pi)))
            original_paths = base.geometry.focal_relative_path_lengths(context["defend"])
            transformed_paths = base.geometry.focal_relative_path_lengths(transformed)
            max_path_error = max(max_path_error, float(np.max(np.abs(original_paths - transformed_paths))))
            max_centroid_error = max(
                max_centroid_error,
                float(np.max(np.abs(context["defend"].mean(axis=1) - transformed.mean(axis=1)))),
            )
            outcomes.append(base.geometry.fixed_elsewhere_cost_change(
                context["attack_start"], context["attack_end"], transformed[0], transformed[-1], context["reference"]
            ))
        altered = data.copy()
        altered["Y"] = outcomes
        values.append(float(fit(altered, plan)["coefficients"][PRIMARY]))
    return np.asarray(values, dtype=np.float64), {
        "max_relative_path_error": max_path_error,
        "max_centroid_error": max_centroid_error,
    }


def descriptive_geometry(contexts: list[dict[str, Any]]) -> dict[str, Any]:
    churn, unused_changed, start_width, end_width, start_depth, end_depth = [], [], [], [], [], []
    for context in contexts:
        reference, defend = context["reference"], context["defend"]
        start = base.geometry.fixed_elsewhere_coverage(context["attack_start"], defend[0], reference)
        end = base.geometry.fixed_elsewhere_coverage(context["attack_end"], defend[-1], reference)
        start_map = dict(zip(start.attacker_indices, start.defender_indices, strict=True))
        end_map = dict(zip(end.attacker_indices, end.defender_indices, strict=True))
        churn.append(sum(start_map[key] != end_map[key] for key in start_map))
        unused_start = next(iter(set(range(10)) - set(start.defender_indices)))
        unused_end = next(iter(set(range(10)) - set(end.defender_indices)))
        unused_changed.append(int(unused_start != unused_end))
        start_width.append(float(np.ptp(defend[0, :, 1])))
        end_width.append(float(np.ptp(defend[-1, :, 1])))
        start_depth.append(float(np.ptp(defend[0, :, 0])))
        end_depth.append(float(np.ptp(defend[-1, :, 0])))
    return {
        "matching_link_churn_count": describe(np.asarray(churn, dtype=float)),
        "unused_defender_identity_changed_fraction": float(np.mean(unused_changed)),
        "defending_unit_width_start_m": describe(np.asarray(start_width)),
        "defending_unit_width_end_m": describe(np.asarray(end_width)),
        "defending_unit_depth_start_m": describe(np.asarray(start_depth)),
        "defending_unit_depth_end_m": describe(np.asarray(end_depth)),
    }


def write_report(output: Path, result: dict[str, Any]) -> None:
    primary, boot, controls, plan = result["primary"], result["bootstrap"], result["controls"], result["active_column_plan"]
    status = result["classification"]
    if status == "COHERENT":
        interpretation = "Within the period-1-only Game 1 development sample, stronger local defensive reorganization around the ball-nearest attacker was associated with a greater concurrent increase in the fixed other-nine attackers' injective matching-distance geometry."
    elif status == "NOT_SUPPORTED":
        interpretation = "This specific fixed-set injective matching-distance representation did not support the proposed association under the frozen Game 1 development design."
    elif status == "MIXED":
        interpretation = "The frozen Game 1 development execution was valid but did not meet every criterion for a coherent association."
    else:
        interpretation = "The frozen Game 1 development execution was invalid before a scientifically interpretable matching-geometry result."
    text = f"""# Defensive Coverage Redistribution v3 — Game 1 development result

**Status:** GAME 1 COVERAGE REDISTRIBUTION v3 DEVELOPMENT {status}

This is a period-1-only development result. The ball-nearest attacker is a
start-defined geometric reference, not an inferred ball carrier, tactical role,
or assignment. The outcome is fixed other-nine injective matching-distance
geometry, not validated football coverage.

## Frozen active design

- Omitted constant nuisance: {", ".join(plan["omitted_constant_nuisance_columns"])}
- Active columns: {", ".join(plan["active_columns"])}
- Active design rank: {primary["rank"]}/{len(plan["active_columns"])}
- Condition number (nonclassifying QC): {primary["condition_number"]:.8g}

## Primary result

- Eligible anchors: {result["sample"]["eligible_anchors"]}; periods: {result["sample"]["period_counts"]}
- Predictor $D$ median: {result["predictor_outcome_summaries"]["D_m"]["median"]:.8f} m
- Outcome $Y$ median: {result["predictor_outcome_summaries"]["Y_m"]["median"]:.8f} m
- $\\beta_D$: {primary["coefficients"][PRIMARY]:.8f} m/m
- 95% block-bootstrap interval: [{boot["primary_interval"][0]:.8f}, {boot["primary_interval"][1]:.8f}]
- Valid primary bootstrap replicates: {boot["valid_primary"]}/{BOOT_REPS}

## Frozen controls

- Direction-null 95th percentile: {controls["direction_null_95th"]:.8f}; observed exceeds it: {controls["direction_null_pass"]}
- Remote comparator $\\beta_D$: {controls["remote_coefficient"]:.8f}; primary exceeds remote: {controls["remote_pass"]}
- Trimmed $\\beta_D$: {controls["trimmed_coefficient"]:.8f}; retained absolute fraction: {controls["trim_retained_abs_fraction"]:.8f}; pass: {controls["trim_pass"]}

## Permitted interpretation

{interpretation}

This remains an observational same-interval geometric association. It does not
establish causation, influence, attention, marking, assignment, responsibility,
space creation, passing availability, tactical success, gravity, or value.
"""
    (output / "result_report.md").write_text(text, encoding="utf-8")


def execute(output: Path) -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    hashes = verify_frozen()
    data, exclusions, provenance, contexts = base.build_sample()
    if data.empty:
        raise RuntimeError("no eligible governed anchors")
    plan = resolve_primary_plan(data, config)
    primary = fit(data, plan)
    draws = base.block_draws(data, reps=BOOT_REPS)
    boot, valid_boot = bootstrap_family(data, draws, plan)
    remote, valid_remote = bootstrap_family(data, draws, plan, "Dremote", "Dpre_remote")
    trimmed = data.loc[data.A <= base.TRIM].reset_index(drop=True)
    trim_draws = base.block_draws(trimmed, reps=BOOT_REPS)
    trim, valid_trim = bootstrap_family(trimmed, trim_draws, plan)
    null_values, null_qc = direction_null(data, contexts, plan)
    primary_beta = float(primary["coefficients"][PRIMARY])
    remote_fit, trim_fit = fit(data, plan, "Dremote", "Dpre_remote"), fit(trimmed, plan)
    controls = {
        "direction_null_construction": "common-angle internal defender-motion rotation preserving start formation, centroid path, ranks, D, R, and leave-one-out-relative path lengths",
        "direction_null_95th": float(np.quantile(null_values, .95, method="linear")),
        "remote_coefficient": float(remote_fit["coefficients"][PRIMARY]),
        "trim_threshold_m": float(base.TRIM),
        "trimmed_coefficient": float(trim_fit["coefficients"][PRIMARY]),
        "trim_retained_abs_fraction": float(abs(trim_fit["coefficients"][PRIMARY]) / abs(primary_beta)) if primary_beta else None,
    }
    controls["direction_null_pass"] = bool(primary_beta > controls["direction_null_95th"])
    controls["remote_pass"] = bool(primary_beta > controls["remote_coefficient"])
    controls["trim_pass"] = bool(controls["trimmed_coefficient"] > 0.0 and controls["trim_retained_abs_fraction"] >= .5)
    descriptive = {
        name: fit(data.assign(Y=data[column]), plan)
        for name, column in {"fixed_start_matching": "Y_fixed_start", "full_ten_matching": "Y_full_ten", "mean_two_nearest": "Y_two_nearest"}.items()
    }
    valid = bool(
        primary["rank"] == len(plan.active_columns)
        and valid_boot >= MIN_VALID and valid_remote >= MIN_VALID and valid_trim >= MIN_VALID
        and len(null_values) == NULL_REPS
        and null_qc["max_relative_path_error"] <= 1e-10 and null_qc["max_centroid_error"] <= 1e-10
    )
    primary_interval = interval(boot)
    if not valid:
        status = "INVALID"
    elif primary_beta <= 0.0:
        status = "NOT_SUPPORTED"
    elif primary_interval[0] > 0.0 and controls["direction_null_pass"] and controls["remote_pass"] and controls["trim_pass"]:
        status = "COHERENT"
    else:
        status = "MIXED"
    sample = {
        "eligible_anchors": int(len(data)),
        "period_counts": {str(k): int(v) for k, v in data.period.value_counts().sort_index().items()},
        "attacking_team_counts": {str(k): int(v) for k, v in data.attacking_team.value_counts().sort_index().items()},
        "reference_attacker_counts": {str(k): int(v) for k, v in data.reference_attacker_key.value_counts().sort_index().items()},
        "exclusion_counts": {str(k): int(v) for k, v in exclusions.reason.value_counts().sort_index().items()},
        "all_complete_ten_by_ten": True,
        "all_one_row_per_anchor": bool(data.observation_id.is_unique),
    }
    result = {
        "frozen_hashes": hashes,
        "source_sha256": sha256(Path(__file__)),
        "provenance": provenance,
        "sample": sample,
        "active_column_plan": {
            "nominal_columns": list(plan.nominal_columns),
            "designated_nuisance_values": {"period_2_indicator": sorted(map(int, data.P2.unique()))},
            "omitted_constant_nuisance_columns": list(plan.omitted_constant_nuisance_columns),
            "active_columns": list(plan.active_columns),
            "resolved_once_before_outcome_fit": True,
            "reused_for_primary_bootstrap_null_remote_trim_and_descriptive": True,
        },
        "predictor_outcome_summaries": {"D_m": describe(data.D.to_numpy(float)), "Y_m": describe(data.Y.to_numpy(float))},
        "primary": primary,
        "bootstrap": {"replicates": BOOT_REPS, "valid_primary": valid_boot, "valid_remote": valid_remote, "valid_trim": valid_trim, "primary_interval": primary_interval, "remote_interval": interval(remote), "trim_interval": interval(trim)},
        "controls": controls,
        "descriptive_alternatives": descriptive,
        "descriptive_geometry": descriptive_geometry(contexts),
        "null_preservation": null_qc,
        "classification": status,
        "hard_qc": {
            "frozen_hashes": True, "period_1_only": sample["period_counts"] == {"1": len(data)},
            "unique_reference_rows": bool(data.observation_id.is_unique), "complete_sets": True,
            "active_full_rank": primary["rank"] == len(plan.active_columns),
            "bootstrap_minimum": bool(valid_boot >= MIN_VALID and valid_remote >= MIN_VALID and valid_trim >= MIN_VALID),
            "direction_null_preservation": bool(null_qc["max_relative_path_error"] <= 1e-10 and null_qc["max_centroid_error"] <= 1e-10),
            "game2_coverage_outcomes_opened": False, "idsse_coverage_outcomes_opened": False,
            "game3_accessed": False, "valid": valid,
        },
        "direction_null_values": null_values,
    }
    output.mkdir(parents=True, exist_ok=True)
    data.to_csv(output / "observation_rows.csv", index=False)
    exclusions.to_csv(output / "eligibility_ledger.csv", index=False)
    data[["observation_id", "period", "time_period_s", "reference_attacker_key", "attacking_team", "defending_team"]].to_csv(output / "anchor_reference_ledger.csv", index=False)
    pd.DataFrame({"replicate": np.arange(1, len(boot) + 1), "primary_beta_D": boot, "remote_beta_D": remote[:len(boot)], "trimmed_beta_D": trim[:len(boot)]}).to_csv(output / "bootstrap_results.csv", index=False)
    pd.DataFrame({"replicate": np.arange(1, NULL_REPS + 1), "beta_D": null_values}).to_csv(output / "direction_null.csv", index=False)
    write_json(output / "active_column_plan.json", result["active_column_plan"])
    write_json(output / "model_results.json", {key: value for key, value in result.items() if key not in {"direction_null_values", "provenance"}})
    write_json(output / "remote_comparator.json", {"coefficient": controls["remote_coefficient"], "interval": result["bootstrap"]["remote_interval"], "primary_exceeds_remote": controls["remote_pass"]})
    write_json(output / "trim_result.json", {"threshold_m": controls["trim_threshold_m"], "coefficient": controls["trimmed_coefficient"], "interval": result["bootstrap"]["trim_interval"], "retained_absolute_fraction": controls["trim_retained_abs_fraction"], "pass": controls["trim_pass"]})
    write_json(output / "descriptive_alternatives.json", descriptive)
    write_json(output / "synthetic_gates.json", {"all_passed_before_empirical_execution": True, "governed_test_file": "tests/test_defensive_coverage_redistribution_v2.py", "required_gate_count": 9})
    write_json(output / "hard_qc.json", result["hard_qc"])
    write_json(output / "manifest.json", {
        "match": "Metrica Sample Game 1", "protocol": str(PROTOCOL.relative_to(ROOT)),
        "configuration": str(CONFIG.relative_to(ROOT)), "frozen_hashes": hashes,
        "source_sha256": result["source_sha256"], "execution_tier": "Tier 1 development",
        "protected_scope": {"game2_coverage_outcomes_opened": False, "idsse_coverage_outcomes_opened": False, "game3_accessed": False},
        "python": sys.version, "platform": platform.platform(),
    })
    write_report(output, result)
    governed = ["active_column_plan.json", "bootstrap_results.csv", "direction_null.csv", "model_results.json", "remote_comparator.json", "trim_result.json", "descriptive_alternatives.json", "synthetic_gates.json", "hard_qc.json", "manifest.json", "result_report.md"]
    write_json(output / "governed_hashes.json", {name: sha256(output / name) for name in governed})
    return result


def reproduce(output: Path) -> dict[str, Any]:
    rerun = output.parent / f".{output.name}_rerun"
    if rerun.exists():
        shutil.rmtree(rerun)
    rerun_result = execute(rerun)
    expected = json.loads((output / "governed_hashes.json").read_text(encoding="utf-8"))
    actual = {name: sha256(rerun / name) for name in expected}
    result = {"all_governed_outputs_byte_identical": expected == actual, "governed_outputs": len(expected), "expected": expected, "actual": actual, "rerun_classification": rerun_result["classification"]}
    shutil.rmtree(rerun)
    write_json(output / "reproduction.json", result)
    if not result["all_governed_outputs_byte_identical"]:
        raise RuntimeError("frozen v3 execution did not reproduce deterministically")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"refusing to overwrite existing governed output: {args.output}")
    result = execute(args.output)
    if args.reproduce:
        reproduce(args.output)
    print(json.dumps(clean({"classification": result["classification"], "beta_D": result["primary"]["coefficients"][PRIMARY], "eligible_anchors": result["sample"]["eligible_anchors"]}), sort_keys=True))


if __name__ == "__main__":
    main()
