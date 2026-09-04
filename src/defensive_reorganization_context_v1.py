"""Execute frozen Defensive Reorganization Context v1 on seven IDSSE matches.

This script uses the established active-roster/off-ball constructor and the
observed near-minus-middle geometric target.  It neither reads DRD predictions
or residuals nor creates a row-level result artifact.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import defensive_reorganization_context_v1_design as design
import defensive_reorganization_departure_v1 as v1
import defensive_reorganization_departure_v2 as v2


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_context_v1.md"
CONFIG = ROOT / "config/defensive_reorganization_context_v1.json"
LEDGER = ROOT / "config/defensive_reorganization_context_v1_hashes.json"
OUTPUT = ROOT / "outputs/defensive_reorganization_context_v1"
FIGURES = ROOT / "figures/defensive_reorganization_context_v1"
DOC_RESULT = ROOT / "docs/results/defensive_reorganization_context_v1.md"

CONTEXTS = ("attacker_minus_unit_goalward_m", "attacker_ball_distance_start_m")
COLUMNS = (
    "attacker_path_exposure_m",
    "attacker_path_prior_m",
    "attacker_minus_unit_goalward_m",
    "attacker_ball_distance_start_m",
    "defending_unit_depth_m",
    "ball_minus_unit_goalward_m",
)
MATCHES = tuple(v1.MATCHES)
BOOT = 2000
MIN_VALID = 1900
SEED = 20260904


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen() -> dict[str, Any]:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    bad = {}
    for section in ("frozen_context_v1_sha256", "preserved_DRD_v2_sha256"):
        for name, expected in ledger[section].items():
            actual = sha(ROOT / name)
            if actual != expected:
                bad[name] = {"actual": actual, "expected": expected}
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")
    if (OUTPUT.exists() and any(OUTPUT.iterdir())) or (FIGURES.exists() and any(FIGURES.iterdir())):
        raise RuntimeError("refusing to overwrite an existing context v1 result")
    return ledger


def sample_data() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """Construct the frozen v2 common sample before reading Y.

    The v2 constructor uses tracking support, event-defined active rosters, and
    ball-nearest eligibility only. It does not read any v2 prediction ledger.
    """
    support_sample, _exclusions, retention = v2.build_outcome_blind_sample()
    expected = set(MATCHES)
    if set(retention) != expected:
        raise RuntimeError("seven-match support registry mismatch")
    if not all(
        value["common_sample_rows"] >= 1000
        and value["retention_of_off_ball_base_rows"] >= 0.9
        for value in retention.values()
    ):
        raise RuntimeError("inherited v2 common-sample gate failed")
    data = v2.join_target_after_gate(support_sample)
    if len(data) != len(support_sample) or data.observation_id.duplicated().any():
        raise RuntimeError("context target join does not preserve one row per inherited observation")
    if not np.isfinite(data[["Y_m", "near_component_m", "middle_component_m", *COLUMNS]].to_numpy(float)).all():
        raise RuntimeError("nonfinite target or frozen model column")
    if set(data.match_id) != expected:
        raise RuntimeError("context target does not retain the frozen match set")
    audit = {
        "common_sample_observation_ids_reconstructed_from_frozen_v2_rules": int(len(data)),
        "v2_prediction_or_residual_ledger_read": False,
        "target_join_after_support_gate": True,
    }
    return data.sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True), retention, audit


def fit(frame: pd.DataFrame) -> tuple[np.ndarray, int]:
    coefficients, _match_names, rank = design.fit_equal_match_fixed_effect_ols(
        frame.Y_m.to_numpy(float), frame.loc[:, COLUMNS].to_numpy(float), frame.match_id.to_numpy()
    )
    return coefficients[-len(COLUMNS):], rank


def coefficient_map(coefficients: np.ndarray) -> dict[str, float]:
    return {name: float(value) for name, value in zip(COLUMNS, coefficients, strict=True)}


def per_match_fits(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for match in MATCHES:
        part = data.loc[data.match_id == match]
        coefficients, rank = fit(part)
        mapped = coefficient_map(coefficients)
        for context in CONTEXTS:
            rows.append({"match_id": match, "context": context, "estimate_m_per_m": mapped[context],
                         "sign": int(np.sign(mapped[context])), "rows": int(len(part)), "model_rank": rank})
    return pd.DataFrame(rows)


def leave_one_match_out_fits(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for heldout in MATCHES:
        part = data.loc[data.match_id != heldout]
        coefficients, rank = fit(part)
        mapped = coefficient_map(coefficients)
        for context in CONTEXTS:
            rows.append({"heldout_match_id": heldout, "context": context, "estimate_m_per_m": mapped[context],
                         "sign": int(np.sign(mapped[context])), "rows": int(len(part)), "model_rank": rank})
    return pd.DataFrame(rows)


def _block_groups(data: pd.DataFrame) -> tuple[dict[tuple[str, int, int], np.ndarray], dict[tuple[str, int], list[tuple[str, int, int]]]]:
    groups = {key: value.index.to_numpy() for key, value in data.groupby(["match_id", "period", "block_id"], sort=True)}
    by_match_period = {(match, period): [key for key in groups if key[:2] == (match, period)] for match in MATCHES for period in (1, 2)}
    if any(not by_match_period[(match, period)] for match in MATCHES for period in set(data.loc[data.match_id == match, "period"])):
        raise RuntimeError("a represented match-period has no frozen 60-second block")
    return groups, by_match_period


def bootstrap(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    groups, by_match_period = _block_groups(data)
    rng = np.random.Generator(np.random.PCG64(SEED))
    draws = []
    for _ in range(BOOT):
        selected = []
        for match in MATCHES:
            for period in sorted(set(data.loc[data.match_id == match, "period"])):
                keys = by_match_period[(match, int(period))]
                selected.extend(groups[keys[int(i)]] for i in rng.integers(0, len(keys), len(keys)))
        index = np.concatenate(selected)
        try:
            coefficients, _rank = fit(data.iloc[index].reset_index(drop=True))
        except (np.linalg.LinAlgError, ValueError):
            continue
        mapped = coefficient_map(coefficients)
        draws.append({context: mapped[context] for context in CONTEXTS})
    table = pd.DataFrame(draws)
    if len(table) < MIN_VALID:
        raise RuntimeError(f"only {len(table)} valid bootstrap replicates; {MIN_VALID} required")
    intervals = {
        context: {
            "estimate": float(table[context].mean()),
            "ci_low": float(table[context].quantile(0.0125)),
            "ci_high": float(table[context].quantile(0.9875)),
            "valid": int(len(table)),
        }
        for context in CONTEXTS
    }
    return table, intervals


def trim_fit(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    keep = np.ones(len(data), dtype=bool)
    bounds: dict[str, dict[str, list[float]]] = {}
    for match, part in data.groupby("match_id", sort=True):
        bounds[match] = {}
        local = np.ones(len(part), dtype=bool)
        for context in CONTEXTS:
            low, high = np.quantile(part[context].to_numpy(float), [0.025, 0.975], method="linear")
            bounds[match][context] = [float(low), float(high)]
            local &= (part[context].to_numpy(float) >= low) & (part[context].to_numpy(float) <= high)
        keep[part.index.to_numpy()] = local
    trimmed = data.loc[keep].reset_index(drop=True)
    coefficients, rank = fit(trimmed)
    return trimmed, {"bounds": bounds, "coefficients": coefficient_map(coefficients), "model_rank": rank,
                     "rows_retained": int(len(trimmed)), "retention": float(len(trimmed) / len(data)),
                     "quantile_method": "numpy_linear"}


def sample_summary(data: pd.DataFrame, retention: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for match in MATCHES:
        part = data.loc[data.match_id == match]
        item = retention[match]
        row = {
            "match_id": match,
            "eligible_rows": int(len(part)),
            "unique_anchors": int(part[["period", "time_period_s"]].drop_duplicates().shape[0]),
            "periods": ",".join(str(int(value)) for value in sorted(part.period.unique())),
            "occupied_60_second_blocks": int(item["occupied_60_second_blocks"]),
        }
        for context in CONTEXTS:
            values = part[context].to_numpy(float)
            row[f"{context}_min_m"] = float(values.min())
            row[f"{context}_p10_m"] = float(np.quantile(values, .1, method="linear"))
            row[f"{context}_p90_m"] = float(np.quantile(values, .9, method="linear"))
            row[f"{context}_max_m"] = float(values.max())
        rows.append(row)
    return pd.DataFrame(rows)


def effect_sizes(data: pd.DataFrame, pooled: dict[str, float]) -> pd.DataFrame:
    rows = []
    for context in CONTEXTS:
        values = data[context].to_numpy(float)
        p10, p90 = np.quantile(values, [.1, .9], method="linear")
        coefficient = pooled[context]
        rows.append({"context": context, "coefficient_m_per_m": coefficient,
                     "change_in_Y_per_10_m": 10.0 * coefficient,
                     "predictor_p10_m": float(p10), "predictor_p90_m": float(p90),
                     "predictor_p10_to_p90_span_m": float(p90 - p10),
                     "change_in_Y_across_p10_to_p90_m": float(coefficient * (p90 - p10))})
    return pd.DataFrame(rows)


def classify(pooled: dict[str, float], intervals: dict[str, dict[str, float]], match_table: pd.DataFrame,
             lomo_table: pd.DataFrame, trim: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    summaries = {}
    for context in CONTEXTS:
        interval = intervals[context]
        summaries[context] = {
            "estimate": pooled[context], "ci_low": interval["ci_low"], "ci_high": interval["ci_high"],
            "per_match_estimates": match_table.loc[match_table.context == context, "estimate_m_per_m"].tolist(),
            "leave_one_match_out_estimates": lomo_table.loc[lomo_table.context == context, "estimate_m_per_m"].tolist(),
            "trimmed_estimate": trim["coefficients"][context],
        }
    gate = {context: design.context_gate(summary) for context, summary in summaries.items()}
    return design.classify_context_study(summaries, valid=True), gate


def _draw_pitch(ax: plt.Axes, label: str) -> None:
    ax.set_xlim(-52.5, 52.5); ax.set_ylim(-34, 34); ax.set_aspect("equal")
    ax.add_patch(plt.Rectangle((-52.5, -34), 105, 68, fill=False, color="#273043", lw=1.4))
    ax.axvline(0, color="#b7c1d1", lw=.8); ax.plot(0, 0, "o", ms=2, color="#b7c1d1")
    defender_x = [-7, -3, 2, 6, -5, 0, 5, 9, -1, 3]
    defender_y = [-17, -6, 4, 17, -12, -1, 10, -18, 15, 22]
    ax.scatter(defender_x, defender_y, s=38, color="#2a6fbb", label="defensive unit", zorder=3)
    ax.scatter([20], [0], s=58, color="#e76f51", marker="*", label="attacker", zorder=4)
    ax.scatter([3], [-10], s=34, color="#f4b942", edgecolor="#805f00", label="ball", zorder=4)
    ax.scatter([np.mean(defender_x)], [np.mean(defender_y)], s=45, color="#173b63", marker="x", label="unit centroid", zorder=5)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(label, fontsize=9, loc="left")


def make_figure(data: pd.DataFrame, pooled: dict[str, float], intervals: dict[str, dict[str, float]],
                per_match: pd.DataFrame, status: str) -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(14, 7), constrained_layout=True)
    outer = fig.add_gridspec(1, 2, wspace=.08)
    labels = {
        "attacker_minus_unit_goalward_m": ("H1: attacker goalward of unit", "Attacker start relative to defensive-unit centroid"),
        "attacker_ball_distance_start_m": ("H2: attacker–ball distance", "Attacker start relative to ball"),
    }
    for col, context in enumerate(CONTEXTS):
        sub = outer[col].subgridspec(2, 2, height_ratios=[1.0, 1.35], width_ratios=[1.0, 1.4])
        schematic = fig.add_subplot(sub[0, 0]); _draw_pitch(schematic, labels[context][1])
        if context == "attacker_minus_unit_goalward_m":
            schematic.annotate("goalward offset", xy=(20, 0), xytext=(6, 25), arrowprops={"arrowstyle": "->", "color": "#c44e52"}, color="#8d2b30", fontsize=8)
        else:
            schematic.plot([3, 20], [-10, 0], "--", color="#8d2b30", lw=1.2)
            schematic.text(9, -7, "distance", color="#8d2b30", fontsize=8)
        curve = fig.add_subplot(sub[:, 1])
        values = data[context].to_numpy(float); p10, p90, reference = np.quantile(values, [.1, .9, .5], method="linear")
        grid = np.linspace(p10, p90, 100); beta = pooled[context]; low = intervals[context]["ci_low"]; high = intervals[context]["ci_high"]
        curve.axhline(0, color="#9aa5b5", lw=.8)
        curve.fill_between(grid, low * (grid - reference), high * (grid - reference), color="#8ecae6", alpha=.35, label="97.5% coefficient interval")
        curve.plot(grid, beta * (grid - reference), color="#1d5f8a", lw=2.3, label="pooled adjusted association")
        matches = per_match.loc[per_match.context == context].sort_values("match_id")
        for _, row in matches.iterrows():
            curve.plot([reference, p90], [0, row.estimate_m_per_m * (p90 - reference)], color="#e76f51", alpha=.38, lw=.9)
        curve.scatter(np.repeat(p90, len(matches)), matches.estimate_m_per_m.to_numpy(float) * (p90-reference), color="#e76f51", s=18, zorder=3, label="seven match slopes")
        curve.set_xlabel(f"{labels[context][1]} (m)")
        curve.set_ylabel("Adjusted change in localized reorganization (m)")
        curve.set_title(labels[context][0], loc="left", fontweight="bold")
        curve.legend(fontsize=7, frameon=False, loc="best")
        curve.text(.01, .01, f"Status at serialization: {status.replace('DEFENSIVE REORGANIZATION CONTEXT v1 ', '')}\nObservational association; not cause, recommendation, or value.", transform=curve.transAxes, fontsize=7, va="bottom")
    fig.suptitle("Starting spatial context and subsequent localized defensive reorganization", fontsize=14, fontweight="bold")
    paths = []
    for suffix in ("png", "svg", "pdf"):
        path = FIGURES / f"context_relationships.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_reports(output: Path, result: dict[str, Any]) -> None:
    status = result["status"]
    pooled = result["pooled_coefficients"]
    intervals = result["bootstrap_intervals"]
    gates = result["context_gates"]
    lines = [
        "# Defensive Reorganization Context v1 — IDSSE result", "",
        f"**Formal status:** **{status}**", "",
        "This governed descriptive study uses observed near-minus-middle defender-relative path, not DRD or residuals. Its two pre-movement contexts are attacker goalward position relative to the defensive unit and attacker–ball distance.", "",
        "## Pooled associations", "",
        "| Context | Estimate (m/m) | 97.5% interval | Individual support gate |", "|---|---:|---:|---|",
    ]
    for context in CONTEXTS:
        item = intervals[context]; gate = gates[context]
        lines.append(f"| `{context}` | {pooled[context]:.6f} | [{item['ci_low']:.6f}, {item['ci_high']:.6f}] | {'PASS' if gate['passed'] else 'FAIL'} |")
    lines += ["", "## Boundary", "", "The result is observational. It does not establish why defenders moved, tactical response, causal influence, marking, assignment, responsibility, player quality, gravity, or value.", "", "No DRD residual, passage retrieval, SkillCorner outcome, Game 3 data, or player ranking was inspected or created."]
    text = "\n".join(lines) + "\n"
    (output / "result_report.md").write_text(text, encoding="utf-8")
    DOC_RESULT.write_text(text, encoding="utf-8")


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "final_hashes.json"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def execute() -> dict[str, Any]:
    ledger = verify_frozen()
    OUTPUT.mkdir(parents=True); FIGURES.mkdir(parents=True)
    data, retention, support_audit = sample_data()
    pooled_values, pooled_rank = fit(data); pooled = coefficient_map(pooled_values)
    per_match = per_match_fits(data); lomo = leave_one_match_out_fits(data)
    _draws, intervals = bootstrap(data)
    trimmed, trim = trim_fit(data)
    status_short, gates = classify(pooled, intervals, per_match, lomo, trim)
    status = f"DEFENSIVE REORGANIZATION CONTEXT v1 {status_short}"
    samples = sample_summary(data, retention); effects = effect_sizes(data, pooled)
    hard_qc = {
        "frozen_hashes": True,
        "seven_exact_matches": set(data.match_id) == set(MATCHES),
        "v2_common_sample_reconstructed_before_target_join": True,
        "minimum_rows_and_retention_per_match": True,
        "one_row_per_observation": not data.observation_id.duplicated().any(),
        "finite_target_and_model_columns": True,
        "pooled_full_rank": pooled_rank == 13,
        "per_match_full_rank": bool((per_match.model_rank == 7).all()),
        "leave_one_match_out_full_rank": bool((lomo.model_rank == 12).all()),
        "bootstrap_valid_at_least_1900": all(item["valid"] >= MIN_VALID for item in intervals.values()),
        "DRD_residual_not_read": True,
        "SkillCorner_not_opened": True,
        "Game3_untouched": True,
        "player_ranking_not_created": True,
        "compact_outputs_only": True,
    }
    if not all(hard_qc.values()):
        raise RuntimeError(f"hard QC failure: {hard_qc}")
    result = {
        "status": status,
        "support_audit": support_audit,
        "sample_retention": retention,
        "pooled_coefficients": pooled,
        "pooled_model_rank": pooled_rank,
        "bootstrap_intervals": intervals,
        "context_gates": gates,
        "trim_robustness": trim,
        "hard_qc": hard_qc,
        "execution": {
            "context_model_fitted": True,
            "context_effect_inspected": True,
            "DRD_residual_inspected": False,
            "retrieval_generated": False,
            "SkillCorner_opened": False,
            "Metrica_Game_3_accessed": False,
            "player_ranking_created": False,
        },
    }
    # Classification is saved before visualization by the frozen protocol.
    write_json(OUTPUT / "result.json", result)
    samples.to_csv(OUTPUT / "sample_summary.csv", index=False)
    per_match.to_csv(OUTPUT / "per_match_coefficients.csv", index=False)
    lomo.to_csv(OUTPUT / "leave_one_match_out_coefficients.csv", index=False)
    pd.DataFrame([{"column": name, "estimate_m_per_m": value} for name, value in pooled.items()]).to_csv(OUTPUT / "pooled_coefficients.csv", index=False)
    pd.DataFrame([{"context": name, **value} for name, value in intervals.items()]).to_csv(OUTPUT / "bootstrap_intervals.csv", index=False)
    pd.DataFrame([{"context": name, "full_estimate_m_per_m": pooled[name], "trimmed_estimate_m_per_m": trim["coefficients"][name],
                   "same_strict_sign": gates[name]["checks"]["central_support_trim_same_sign_and_50_to_150_percent"],
                   "absolute_ratio": gates[name]["trimmed_to_primary_absolute_ratio"], "trimmed_rows": trim["rows_retained"], "trimmed_retention": trim["retention"]}
                  for name in CONTEXTS]).to_csv(OUTPUT / "trim_robustness.csv", index=False)
    effects.to_csv(OUTPUT / "effect_sizes.csv", index=False)
    write_json(OUTPUT / "hard_qc.json", hard_qc)
    manifest = {
        "protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG),
        "hash_ledger_sha256": sha(LEDGER), "implementation_sha256": sha(Path(__file__)),
        "status": status, "bootstrap_seed": SEED, "bootstrap_replicates": BOOT,
        "provider_row_level_outputs": "not_written",
    }
    write_json(OUTPUT / "manifest.json", manifest)
    write_reports(OUTPUT, result)
    figure_paths = make_figure(data, pooled, intervals, per_match, status)
    result["figure_paths"] = [str(path.relative_to(ROOT)) for path in figure_paths]
    write_json(OUTPUT / "result.json", result)
    write_json(OUTPUT / "governed_hashes.json", hash_outputs(OUTPUT))
    write_json(OUTPUT / "final_hashes.json", {**json.loads((OUTPUT / "governed_hashes.json").read_text()),
                                                "governed_hashes.json": sha(OUTPUT / "governed_hashes.json")})
    return result


if __name__ == "__main__":
    final = execute()
    print(json.dumps({"status": final["status"], "hard_qc": final["hard_qc"]}, sort_keys=True))
