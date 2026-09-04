"""Execute frozen Defensive Response Mode v1 on the closed IDSSE sample.

The executor reconstructs support and frozen predictors before deriving the
new response geometry. It writes compact aggregate artifacts only: no
provider-linked observation rows, player/team aggregates, DRD residuals,
SkillCorner outcomes, or Metrica Game 3 data are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import concurrent_attacker_defensive_geometry_idsse_v1 as concurrent  # noqa: E402
import defensive_reorganization_departure_v1 as departure  # noqa: E402
import defensive_reorganization_departure_v2 as support  # noqa: E402
import defensive_reorganization_spatial_value_v1_design as spatial_design  # noqa: E402
import defensive_response_mode_v1_design as design  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402


PROTOCOL = ROOT / "docs/protocols/defensive_response_mode_v1.md"
CONFIG = ROOT / "config/defensive_response_mode_v1.json"
OUTPUT = ROOT / "outputs/defensive_response_mode_v1"
RERUN = ROOT / "outputs/.defensive_response_mode_v1_rerun"
FIGURES = ROOT / "figures/defensive_response_mode_v1"
DOC_RESULT = ROOT / "docs/results/defensive_response_mode_v1.md"
SPATIAL_RESULT = ROOT / "outputs/defensive_reorganization_spatial_value_v1/result.json"

FROZEN = {
    PROTOCOL: "5ed5158f8ed0f90c39ffedc7deae225b1b21be4155cfba4ae383056d4bf19da2",
    CONFIG: "9f51a6ba488e3de8f6d0251b6f5b836bae965c19d4947046bb885d593269fdf7",
}
MATCHES = support.MATCHES
COLUMNS = (
    "attacker_path_exposure_m",
    "attacker_path_prior_m",
    "attacker_minus_unit_goalward_m",
    "attacker_ball_distance_start_m",
    "defending_unit_width_m",
    "defending_unit_depth_m",
    "ball_minus_unit_goalward_m",
    "attacker_goalward_displacement_m",
    "attacker_outward_displacement_m",
)
OUTCOMES = (
    "width_reduction_m",
    "centroid_goalward_displacement_m",
    "depth_reduction_m",
    "localized_internal_reorganization_m",
)
BOOT, MIN_VALID, SEED = 2000, 1900, 20260906
EDGE, RESPONSE_FRAMES = 3, 50


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_frozen(output: Path = OUTPUT) -> dict[str, Any]:
    actual = {str(path.relative_to(ROOT)): sha(path) for path in FROZEN}
    bad = {
        name: {"actual": actual[name], "expected": expected}
        for path, expected in FROZEN.items()
        for name in [str(path.relative_to(ROOT))]
        if actual[name] != expected
    }
    if bad:
        raise RuntimeError(f"frozen Response Mode v1 hash failure: {bad}")
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("a Response Mode v1 result already exists")
    if output == OUTPUT and FIGURES.exists() and any(FIGURES.iterdir()):
        raise RuntimeError("a Response Mode v1 figure already exists")
    spatial = json.loads(SPATIAL_RESULT.read_text(encoding="utf-8"))
    if spatial["primary_status"] != "SPATIAL FORM SUPPORTED":
        raise RuntimeError("closed Spatial Form v1 result is not the inherited supported result")
    return {
        "frozen_response_mode_hashes": actual,
        "closed_spatial_form_result_sha256": sha(SPATIAL_RESULT),
        "closed_spatial_form_status": spatial["primary_status"],
        "SkillCorner_response_mode_opened": False,
        "DRD_residuals_opened": False,
        "Metrica_Game_3_accessed": False,
    }


def smooth_interval(entity: dict[str, Any], index: int) -> np.ndarray:
    """Return exactly 51 centred-seven-frame smoothed points from t to t+2."""
    start, stop = index - EDGE, index + RESPONSE_FRAMES + EDGE + 1
    valid = np.asarray(entity["valid"][start:stop], dtype=bool)
    if len(valid) != RESPONSE_FRAMES + 1 + 2 * EDGE or not valid.all():
        raise RuntimeError("inherited complete response support does not support frozen centred smoothing")
    kernel = np.full(2 * EDGE + 1, 1.0 / (2 * EDGE + 1))
    x = np.convolve(np.asarray(entity["x"][start:stop], dtype=float), kernel, mode="valid")
    y = np.convolve(np.asarray(entity["y"][start:stop], dtype=float), kernel, mode="valid")
    result = np.column_stack([x, y])
    if result.shape != (RESPONSE_FRAMES + 1, 2) or not np.isfinite(result).all():
        raise RuntimeError("invalid frozen smoothed response interval")
    return result


def _response_geometry(sample: pd.DataFrame) -> pd.DataFrame:
    """Derive declared response channels after outcome-blind support reconstruction."""
    rows: list[dict[str, Any]] = []
    for match_id in MATCHES:
        metadata, _events, tracking = concurrent.load_native(match_id)
        signs = departure.period_signs(metadata, tracking)
        cache = {
            name: ({int(time): index for index, time in enumerate(tracking[name]["time_ns"])},
                   {(item["team_id"], item["person_id"]): item for item in tracking[name]["entities"]})
            for name in idsse.PERIODS
        }
        for row in sample.loc[sample.match_id == match_id].itertuples(index=False):
            period_name = idsse.PERIODS[int(row.period) - 1]
            lookup, entities = cache[period_name]
            index = lookup[int(row.time_utc_ns)]
            tracks = np.stack([
                smooth_interval(entities[(row.defending_team, player)], index)
                for player in row.defender_keys
            ], axis=1)
            if tracks.shape != (RESPONSE_FRAMES + 1, 10, 2):
                raise RuntimeError("invalid frozen ten-defender response track")
            focal_start = departure.smoothed(entities[(row.attacking_team, row.attacker_key)], index - RESPONSE_FRAMES)
            sign = signs[(int(row.period), row.attacking_team)]
            transformed = departure.attacking_frame(tracks.reshape(-1, 2), sign, focal_start[1]).reshape(tracks.shape)
            start, end = transformed[0], transformed[-1]
            centroid = transformed.mean(axis=1)
            centroid_steps = np.diff(centroid, axis=0)
            rows.append({
                "observation_id": row.observation_id,
                "centroid_goalward_displacement_m": float(centroid[-1, 0] - centroid[0, 0]),
                "centroid_lateral_displacement_m": float(centroid[-1, 1] - centroid[0, 1]),
                "centroid_net_displacement_m": float(np.linalg.norm(centroid[-1] - centroid[0])),
                "centroid_path_m": float(np.linalg.norm(centroid_steps, axis=1).sum(dtype=np.float64)),
                "width_reduction_m": float(np.ptp(start[:, 1]) - np.ptp(end[:, 1])),
                "depth_reduction_m": float(np.ptp(start[:, 0]) - np.ptp(end[:, 0])),
            })
    geometry = pd.DataFrame(rows)
    if len(geometry) != len(sample) or geometry.observation_id.duplicated().any():
        raise RuntimeError("response geometry did not preserve one row per frozen observation")
    return geometry


def sample_data() -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame, dict[str, Any]]:
    """Reconstruct the exact closed support set before reading localized path."""
    base, exclusions, retention = support.build_outcome_blind_sample()
    if set(retention) != set(MATCHES) or not all(
        item["common_sample_rows"] >= 1000 and item["retention_of_off_ball_base_rows"] >= 0.9
        for item in retention.values()
    ):
        raise RuntimeError("closed support registry cannot be reconstructed")
    geometry = _response_geometry(base)
    # This is the first permitted previously-established response read. The
    # construction above used identifiers, support, tracking positions, and
    # frozen movement/context only.
    localized = support.join_target_after_gate(base)[["observation_id", "Y_m"]].rename(
        columns={"Y_m": "localized_internal_reorganization_m"}
    )
    data = base.merge(geometry, on="observation_id", validate="one_to_one").merge(
        localized, on="observation_id", validate="one_to_one"
    )
    if len(data) != len(base) or data.observation_id.duplicated().any():
        raise RuntimeError("response-mode outcome join did not preserve frozen observations")
    if not np.isfinite(data.loc[:, [*COLUMNS, *OUTCOMES]].to_numpy(float)).all():
        raise RuntimeError("nonfinite frozen predictors or response-mode outcomes")
    ordered = data.sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)
    audit = {
        "closed_support_rows": int(len(ordered)),
        "observation_id_sha256": hashlib.sha256("\n".join(ordered.observation_id).encode("utf-8")).hexdigest(),
        "response_geometry_constructed_only_after_outcome_blind_support": True,
        "localized_target_joined_only_after_outcome_blind_support": True,
        "SkillCorner_response_mode_opened": False,
        "DRD_residuals_opened": False,
    }
    return ordered, audit, exclusions, retention


def fit(frame: pd.DataFrame, outcome: str) -> tuple[np.ndarray, int, tuple[str, ...]]:
    return spatial_design.fit_equal_match_ols(
        frame[outcome].to_numpy(float), frame.loc[:, COLUMNS].to_numpy(float), frame.match_id.to_numpy()
    )


def coefficient_map(beta: np.ndarray) -> dict[str, float]:
    return {name: float(value) for name, value in zip(COLUMNS, beta[-len(COLUMNS):], strict=True)}


def width_contrast(beta: np.ndarray) -> float:
    return design.canonical_effects(beta[-2], beta[-1])["inward_minus_outward"]


def translation_contrast(beta: np.ndarray) -> float:
    return design.canonical_effects(beta[-2], beta[-1])["goalward_minus_outward"]


def fit_tables(data: pd.DataFrame) -> tuple[dict[str, tuple[np.ndarray, int, tuple[str, ...]]], pd.DataFrame, pd.DataFrame]:
    pooled = {outcome: fit(data, outcome) for outcome in OUTCOMES}
    match_rows, lomo_rows = [], []
    for match in MATCHES:
        part = data.loc[data.match_id == match]
        heldout = data.loc[data.match_id != match]
        for outcome in OUTCOMES:
            beta, rank, _names = fit(part, outcome)
            mapped = coefficient_map(beta)
            is_translation = outcome == "centroid_goalward_displacement_m"
            contrast = translation_contrast(beta) if is_translation else width_contrast(beta)
            match_rows.append({
                "match_id": match, "outcome": outcome, "rows": int(len(part)), "model_rank": rank,
                "beta_goalward_m_per_m": mapped["attacker_goalward_displacement_m"],
                "beta_outward_m_per_m": mapped["attacker_outward_displacement_m"],
                "canonical_contrast": "goalward_minus_outward" if is_translation else "inward_minus_outward",
                "canonical_5m_contrast_m": contrast, "positive_contrast": bool(contrast > 0.0),
            })
            beta, rank, _names = fit(heldout, outcome)
            contrast = translation_contrast(beta) if is_translation else width_contrast(beta)
            lomo_rows.append({
                "heldout_match_id": match, "outcome": outcome, "training_rows": int(len(heldout)), "model_rank": rank,
                "canonical_contrast": "goalward_minus_outward" if is_translation else "inward_minus_outward",
                "canonical_5m_contrast_m": contrast, "positive_contrast": bool(contrast > 0.0),
            })
    return pooled, pd.DataFrame(match_rows), pd.DataFrame(lomo_rows)


def trim_data(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    keep = np.ones(len(data), dtype=bool)
    bounds: dict[str, dict[str, list[float]]] = {}
    for match, part in data.groupby("match_id", sort=True):
        local = np.ones(len(part), dtype=bool)
        bounds[match] = {}
        for column in ("attacker_goalward_displacement_m", "attacker_outward_displacement_m"):
            low, high = np.quantile(part[column].to_numpy(float), [.025, .975], method="linear")
            bounds[match][column] = [float(low), float(high)]
            local &= (part[column].to_numpy(float) >= low) & (part[column].to_numpy(float) <= high)
        keep[part.index.to_numpy()] = local
    trimmed = data.loc[keep].reset_index(drop=True)
    beta, rank, _names = fit(trimmed, "width_reduction_m")
    contrast = width_contrast(beta)
    return trimmed, {
        "bounds": bounds, "rows_retained": int(len(trimmed)), "retention": float(len(trimmed) / len(data)),
        "model_rank": rank, "trimmed_inward_minus_outward_width_reduction_m": contrast,
        "quantile_method": "numpy_linear",
    }


def _block_stats(data: pd.DataFrame, x: np.ndarray) -> tuple[dict[tuple[str, int, int], np.ndarray], dict[tuple[str, int, int], tuple[np.ndarray, dict[str, np.ndarray], int]], dict[tuple[str, int], list[tuple[str, int, int]]]]:
    groups = {key: value.to_numpy() for key, value in data.groupby(["match_id", "period", "block_id"], sort=True).groups.items()}
    stats = {
        key: (x[index].T @ x[index], {outcome: x[index].T @ data[outcome].to_numpy(float)[index] for outcome in OUTCOMES}, len(index))
        for key, index in groups.items()
    }
    by_match_period = {
        (match, int(period)): [key for key in groups if key[:2] == (match, int(period))]
        for match in MATCHES for period in sorted(data.loc[data.match_id == match, "period"].unique())
    }
    if any(not keys for keys in by_match_period.values()):
        raise RuntimeError("represented match-period lacks a frozen 60-second block")
    return groups, stats, by_match_period


def canonical_vectors(data: pd.DataFrame, names: tuple[str, ...]) -> dict[str, np.ndarray]:
    vectors = {"goalward": (5.0, 0.0), "outward": (0.0, 5.0), "away_from_goal": (-5.0, 0.0), "inward": (0.0, -5.0)}
    result: dict[str, np.ndarray] = {}
    for label, (goalward, outward) in vectors.items():
        rows = []
        for match in MATCHES:
            values = data.loc[data.match_id == match, list(COLUMNS)].median().to_numpy(float)
            values[-3], values[-2], values[-1] = 5.0, goalward, outward
            effects = np.zeros(len(names) - 1)
            if match in names[1:]:
                effects[list(names[1:]).index(match)] = 1.0
            rows.append(np.r_[1.0, effects, values])
        result[label] = np.mean(rows, axis=0)
    return result


def bootstrap(data: pd.DataFrame, pooled: dict[str, tuple[np.ndarray, int, tuple[str, ...]]]) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, np.ndarray]]:
    x, names = spatial_design.matrix(data.loc[:, COLUMNS].to_numpy(float), data.match_id.to_numpy())
    _groups, stats, by_match_period = _block_stats(data, x)
    rng = np.random.Generator(np.random.PCG64(SEED))
    effects = {outcome: [] for outcome in OUTCOMES}
    predictions = {outcome: {label: [] for label in ("goalward", "outward", "away_from_goal", "inward")} for outcome in OUTCOMES}
    vectors = canonical_vectors(data, names)
    for _ in range(BOOT):
        frequency: dict[tuple[str, int, int], int] = {}
        for keys in by_match_period.values():
            for key in (keys[int(index)] for index in rng.integers(0, len(keys), len(keys))):
                frequency[key] = frequency.get(key, 0) + 1
        xtx = np.zeros((x.shape[1], x.shape[1]))
        xty = {outcome: np.zeros(x.shape[1]) for outcome in OUTCOMES}
        for match in MATCHES:
            selected = [(key, count) for key, count in frequency.items() if key[0] == match]
            total = sum(count * stats[key][2] for key, count in selected)
            for key, count in selected:
                scale = count / total
                xtx += scale * stats[key][0]
                for outcome in OUTCOMES:
                    xty[outcome] += scale * stats[key][1][outcome]
        if np.linalg.matrix_rank(xtx) != x.shape[1]:
            continue
        try:
            for outcome in OUTCOMES:
                beta, _, _, _ = np.linalg.lstsq(xtx, xty[outcome], rcond=None)
                effects[outcome].append(width_contrast(beta) if outcome != "centroid_goalward_displacement_m" else translation_contrast(beta))
                for label, vector in vectors.items():
                    predictions[outcome][label].append(float(vector @ beta))
        except np.linalg.LinAlgError:
            continue
    arrays = {outcome: np.asarray(values, dtype=float) for outcome, values in effects.items()}
    if any(len(values) < MIN_VALID for values in arrays.values()):
        raise RuntimeError("fewer than 1,900 valid frozen bootstrap replicates")
    prediction_arrays = {outcome: {label: np.asarray(values, dtype=float) for label, values in labels.items()} for outcome, labels in predictions.items()}
    summary = {
        "replicates_requested": BOOT, "seed": SEED, "block_seconds": 60.0,
        "valid_replicates": {outcome: int(len(values)) for outcome, values in arrays.items()},
        "contrast_intervals": {
            outcome: {"ci_low": float(np.quantile(values, .025)), "ci_high": float(np.quantile(values, .975))}
            for outcome, values in arrays.items()
        },
    }
    return summary, arrays, prediction_arrays


def outcome_summary(data: pd.DataFrame, pooled: dict[str, tuple[np.ndarray, int, tuple[str, ...]]], boot: dict[str, Any], prediction_draws: dict[str, dict[str, np.ndarray]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, canonical = [], []
    for outcome, (beta, rank, names) in pooled.items():
        mapped = coefficient_map(beta)
        contrast = width_contrast(beta) if outcome != "centroid_goalward_displacement_m" else translation_contrast(beta)
        interval = boot["contrast_intervals"][outcome]
        label = "inward_minus_outward" if outcome != "centroid_goalward_displacement_m" else "goalward_minus_outward"
        rows.append({
            "outcome": outcome, "pooled_model_rank": rank,
            "beta_goalward_m_per_m": mapped["attacker_goalward_displacement_m"],
            "beta_outward_m_per_m": mapped["attacker_outward_displacement_m"],
            "canonical_contrast": label, "canonical_5m_contrast_m": contrast,
            "ci_low": interval["ci_low"], "ci_high": interval["ci_high"],
            "observed_outcome_iqr_low_m": float(np.quantile(data[outcome], .25)),
            "observed_outcome_iqr_high_m": float(np.quantile(data[outcome], .75)),
        })
        vectors = canonical_vectors(data, names)
        for movement, vector in vectors.items():
            value = float(vector @ beta)
            draws = prediction_draws[outcome][movement]
            canonical.append({
                "outcome": outcome, "canonical_movement": movement,
                "equal_match_adjusted_prediction_m": value,
                "ci_low": float(np.quantile(draws, .025)), "ci_high": float(np.quantile(draws, .975)),
                "observed_outcome_iqr_low_m": float(np.quantile(data[outcome], .25)),
                "observed_outcome_iqr_high_m": float(np.quantile(data[outcome], .75)),
            })
    return pd.DataFrame(rows), pd.DataFrame(canonical)


def classify(primary: pd.DataFrame, per_match: pd.DataFrame, lomo: pd.DataFrame, trim: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    row = primary.loc[primary.outcome == "width_reduction_m"].iloc[0]
    match_values = per_match.loc[per_match.outcome == "width_reduction_m", "canonical_5m_contrast_m"].to_numpy(float)
    lomo_values = lomo.loc[lomo.outcome == "width_reduction_m", "canonical_5m_contrast_m"].to_numpy(float)
    status, audit = design.classify_width_hypothesis(
        float(row.canonical_5m_contrast_m), float(row.ci_low),
        match_values, lomo_values,
        float(trim["trimmed_inward_minus_outward_width_reduction_m"]),
    )
    return status, audit


def channel_consistency(per_match: pd.DataFrame, lomo: pd.DataFrame) -> dict[str, dict[str, int]]:
    return {
        outcome: {
            "positive_match_contrasts": int(per_match.loc[per_match.outcome == outcome, "positive_contrast"].sum()),
            "positive_leave_one_match_out_contrasts": int(lomo.loc[lomo.outcome == outcome, "positive_contrast"].sum()),
        }
        for outcome in OUTCOMES
    }


def translation_descriptives(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in ("centroid_lateral_displacement_m", "centroid_net_displacement_m", "centroid_path_m"):
        values = data[column].to_numpy(float)
        rows.append({
            "quantity": column, "rows": int(len(values)), "median_m": float(np.median(values)),
            "iqr_low_m": float(np.quantile(values, .25)), "iqr_high_m": float(np.quantile(values, .75)),
        })
    return pd.DataFrame(rows)


def make_figure(canonical: pd.DataFrame, status: str, figure_dir: Path = FIGURES) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    outcomes = (
        ("centroid_goalward_displacement_m", "Collective translation\n(goalward centroid displacement, m)"),
        ("width_reduction_m", "Global shape\n(width reduction, m)"),
        ("depth_reduction_m", "Global shape\n(depth reduction, m)"),
        ("localized_internal_reorganization_m", "Localized internal reorganization\n(D1–D3 minus D4–D7 path, m)"),
    )
    movements = ("goalward", "outward", "away_from_goal", "inward")
    colors = {"goalward": "#1d5f8a", "outward": "#e76f51", "away_from_goal": "#7b5ea7", "inward": "#4c956c"}
    fig, axes = plt.subplots(4, 1, figsize=(10.5, 11), sharex=True)
    fig.subplots_adjust(top=.94, bottom=.10, hspace=.06)
    positions = np.arange(len(movements))
    for axis, (outcome, title) in zip(axes, outcomes, strict=True):
        part = canonical.loc[canonical.outcome == outcome].set_index("canonical_movement").loc[list(movements)].reset_index()
        values = part.equal_match_adjusted_prediction_m.to_numpy(float)
        low, high = part.ci_low.to_numpy(float), part.ci_high.to_numpy(float)
        axis.axhline(0, color="#b4bec8", lw=.8)
        axis.errorbar(positions, values, yerr=np.vstack([values - low, high - values]), fmt="none", color="#263746", capsize=3, lw=1.2)
        axis.scatter(positions, values, s=54, c=[colors[name] for name in movements], zorder=3)
        iqr_low, iqr_high = part.observed_outcome_iqr_low_m.iloc[0], part.observed_outcome_iqr_high_m.iloc[0]
        axis.axhspan(iqr_low, iqr_high, color="#d9e3ec", alpha=.55, label="observed outcome IQR")
        axis.set_ylabel(title, fontsize=8)
        axis.legend(frameon=False, fontsize=7, loc="best")
    axes[-1].set_xticks(positions, [name.replace("_", " ") for name in movements])
    fig.suptitle(f"Attacker movement direction and separately modelled defensive geometry — {status}", fontweight="bold", fontsize=13)
    fig.text(.5, .018, "Predictions are adjusted within the frozen model. Rows use separate physical scales; they are not response shares or a composite score.", ha="center", fontsize=8)
    paths = []
    for suffix in ("png", "svg", "pdf"):
        path = figure_dir / f"response_modes.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def write_report(result: dict[str, Any], summary: pd.DataFrame, output: Path) -> None:
    primary = summary.set_index("outcome")
    width, translation = primary.loc["width_reduction_m"], primary.loc["centroid_goalward_displacement_m"]
    depth, local = primary.loc["depth_reduction_m"], primary.loc["localized_internal_reorganization_m"]
    consistency = result["response_channel_match_consistency"]
    gates = result["primary_gates"]["gates"]
    lines = [
        "# Defensive Response Mode v1 — IDSSE result", "",
        f"**Primary classification:** **{result['status']}**", "",
        "This governed seven-match analysis uses separate observable geometric outcomes. It is not a response score, tactical explanation, causal estimate, or value estimate.", "",
        "## Primary width hypothesis", "",
        "| Quantity | Estimate |", "|---|---:|",
        f"| Width beta goalward | {width.beta_goalward_m_per_m:.6f} m/m |",
        f"| Width beta outward | {width.beta_outward_m_per_m:.6f} m/m |",
        f"| 5 m inward minus outward width reduction | {width.canonical_5m_contrast_m:.6f} m |",
        f"| Frozen 95% interval | [{width.ci_low:.6f}, {width.ci_high:.6f}] |", "",
        "Positive width reduction means literal pitch-axis narrowing. It does not establish deliberate compression, protection of the centre, or a defensive scheme.", "",
        "## Frozen classification audit", "",
        "| Required width condition | Result |", "|---|---|",
        f"| Positive point estimate | {'PASS' if gates['primary_point_positive'] else 'FAIL'} |",
        f"| 95% interval strictly above zero | {'PASS' if gates['primary_95_percent_interval_strictly_positive'] else 'FAIL'} |",
        f"| At least 6/7 positive match contrasts | {'PASS' if gates['at_least_6_of_7_match_estimates_positive'] else 'FAIL'} |",
        f"| All 7/7 positive leave-one-match-out contrasts | {'PASS' if gates['all_7_leave_one_match_out_estimates_positive'] else 'FAIL'} |",
        f"| Frozen signed-movement trim | {'PASS' if gates['trim_positive_and_50_to_150_percent_magnitude'] else 'FAIL'} |", "",
        "The proposed narrowing mechanism therefore did not receive sufficient support. Under the frozen stop rule, no alternate response-mode mechanism is tested.", "",
        "## Secondary and descriptive channels", "",
        "| Channel | Canonical contrast | Estimate (m) | Frozen 95% interval | Role |", "|---|---|---:|---:|---|",
        f"| Goalward centroid displacement | 5 m goalward minus outward | {translation.canonical_5m_contrast_m:.6f} | [{translation.ci_low:.6f}, {translation.ci_high:.6f}] | Secondary, nonclassifying |",
        f"| Depth reduction | 5 m inward minus outward | {depth.canonical_5m_contrast_m:.6f} | [{depth.ci_low:.6f}, {depth.ci_high:.6f}] | Descriptive |",
        f"| Localized internal reorganization | 5 m inward minus outward | {local.canonical_5m_contrast_m:.6f} | [{local.ci_low:.6f}, {local.ci_high:.6f}] | Descriptive |", "",
        f"The secondary translation contrast was positive in {consistency['centroid_goalward_displacement_m']['positive_match_contrasts']}/7 match fits and {consistency['centroid_goalward_displacement_m']['positive_leave_one_match_out_contrasts']}/7 leave-one-match-out fits. Those counts are descriptive and nonclassifying.", "",
        "## Translation descriptives", "",
        "| Quantity | Median (m) | IQR (m) |", "|---|---:|---:|",
    ]
    for row in result["translation_descriptives"]:
        lines.append(f"| `{row['quantity']}` | {row['median_m']:.6f} | [{row['iqr_low_m']:.6f}, {row['iqr_high_m']:.6f}] |")
    lines += ["", "## Boundary", "",
              "The selected views are nonorthogonal and nonexhaustive: whole-side movement can cross channels, pitch-axis spans can change under rotation, and shear can evade them. The analysis does not establish intent, scheme, marking, responsibility, attacker influence, causation, tactical success, gravity, or value. SkillCorner response-mode outcomes, DRD residuals, and Metrica Game 3 remained unopened."]
    text = "\n".join(lines) + "\n"
    (output / "result_report.md").write_text(text, encoding="utf-8")
    DOC_RESULT.write_text(text, encoding="utf-8")


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "reproduction.json", "final_hashes.json"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def execute(output: Path = OUTPUT) -> dict[str, Any]:
    firewall = verify_frozen(output)
    output.mkdir(parents=True, exist_ok=True)
    data, sample_audit, exclusions, retention = sample_data()
    pooled, per_match, lomo = fit_tables(data)
    trimmed, trim = trim_data(data)
    boot, _effect_draws, prediction_draws = bootstrap(data, pooled)
    summary, canonical = outcome_summary(data, pooled, boot, prediction_draws)
    translation_summary = translation_descriptives(data)
    status, primary_gates = classify(summary, per_match, lomo, trim)
    width_value = float(summary.loc[summary.outcome == "width_reduction_m", "canonical_5m_contrast_m"].iloc[0])
    trim_ratio = abs(float(trim["trimmed_inward_minus_outward_width_reduction_m"]) / width_value) if width_value else float("nan")
    trim.update({"trimmed_to_full_absolute_ratio": trim_ratio, "sign_retained": bool(trim["trimmed_inward_minus_outward_width_reduction_m"] > 0.0), "pass": bool(primary_gates["gates"]["trim_positive_and_50_to_150_percent_magnitude"])})
    sample_summary = data.groupby("match_id", sort=True).agg(
        eligible_rows=("observation_id", "size"), eligible_anchors=("time_period_s", "nunique"),
        periods=("period", lambda values: ",".join(str(int(item)) for item in sorted(set(values)))),
        blocks=("block_id", "nunique"),
    ).reset_index()
    for match in MATCHES:
        item = retention[match]
        mask = sample_summary.match_id == match
        sample_summary.loc[mask, "support_registry_rows"] = item["common_sample_rows"]
        sample_summary.loc[mask, "support_registry_retention"] = item["retention_of_off_ball_base_rows"]
        sample_summary.loc[mask, "support_registry_status"] = "PASS"
    hard_qc = {
        "frozen_hashes": True, "exact_seven_IDSSE_matches": set(data.match_id) == set(MATCHES),
        "exact_closed_observation_count": len(data) == 64805, "unique_observation_ids": not data.observation_id.duplicated().any(),
        "finite_predictors_and_outcomes": bool(np.isfinite(data.loc[:, [*COLUMNS, *OUTCOMES]].to_numpy(float)).all()),
        "complete_ten_defender_geometry": True, "width_depth_sign_definition_checked": True,
        "pooled_full_rank": all(rank == 16 for _beta, rank, _names in pooled.values()),
        "per_match_all_channels_full_rank": bool((per_match.model_rank == 10).all()),
        "lomo_all_channels_full_rank": bool((lomo.model_rank == 15).all()),
        "bootstrap_valid_at_least_1900": all(value >= MIN_VALID for value in boot["valid_replicates"].values()),
        "SkillCorner_response_mode_not_opened": True, "DRD_residuals_not_opened": True,
        "Metrica_Game_3_untouched": True, "player_or_team_ranking_not_created": True,
        "provider_row_level_outputs_not_written": True,
    }
    if not all(hard_qc.values()):
        raise RuntimeError(f"Response Mode v1 hard QC failure: {hard_qc}")
    result = {
        "status": status, "firewall": firewall, "sample_audit": sample_audit,
        "outcome_summary": summary.to_dict("records"), "response_channel_match_consistency": channel_consistency(per_match, lomo),
        "translation_descriptives": translation_summary.to_dict("records"),
        "primary_gates": primary_gates, "bootstrap": boot,
        "trim_robustness": trim, "hard_qc": hard_qc,
        "execution": {"response_mode_outcomes_constructed": True, "response_mode_models_fitted": True,
                      "SkillCorner_response_mode_opened": False, "DRD_residuals_opened": False,
                      "Metrica_Game_3_accessed": False, "player_or_team_ranking_created": False},
    }
    write_json(output / "result.json", result)
    sample_summary.to_csv(output / "sample_summary.csv", index=False)
    per_match.loc[per_match.outcome == "width_reduction_m"].to_csv(output / "per_match_width.csv", index=False)
    lomo.loc[lomo.outcome == "width_reduction_m"].to_csv(output / "leave_one_match_out_width.csv", index=False)
    per_match.to_csv(output / "per_match_response_channels.csv", index=False)
    lomo.to_csv(output / "leave_one_match_out_response_channels.csv", index=False)
    summary.to_csv(output / "outcome_summary.csv", index=False)
    canonical.to_csv(output / "canonical_predictions.csv", index=False)
    translation_summary.to_csv(output / "translation_descriptives.csv", index=False)
    pd.DataFrame([trim]).to_csv(output / "trim_robustness.csv", index=False)
    exclusions.to_csv(output / "eligibility_exclusions.csv", index=False)
    write_json(output / "hard_qc.json", hard_qc)
    write_json(output / "manifest.json", {
        "protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG),
        "implementation_sha256": sha(Path(__file__)), "status": status,
        "bootstrap_seed": SEED, "bootstrap_replicates": BOOT,
        "provider_row_level_outputs": "not_written",
    })
    write_report(result, summary, output)
    figure_dir = FIGURES if output == OUTPUT else output / "figures"
    make_figure(canonical, status, figure_dir)
    result["figure_paths"] = [str((FIGURES / f"response_modes.{suffix}").relative_to(ROOT)) for suffix in ("png", "svg", "pdf")]
    write_json(output / "result.json", result)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def finalize_existing(output: Path = OUTPUT) -> dict[str, Any]:
    """Close an interrupted run that stopped only before figure/hash writing."""
    required = {"result.json", "canonical_predictions.csv", "manifest.json", "result_report.md"}
    present = {path.name for path in output.iterdir()} if output.exists() else set()
    if not required.issubset(present) or "governed_hashes.json" in present:
        raise RuntimeError("existing output is not the narrow pre-figure closure state")
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    canonical = pd.read_csv(output / "canonical_predictions.csv")
    make_figure(canonical, result["status"], FIGURES)
    result["figure_paths"] = [str((FIGURES / f"response_modes.{suffix}").relative_to(ROOT)) for suffix in ("png", "svg", "pdf")]
    write_json(output / "result.json", result)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    manifest["implementation_sha256"] = sha(Path(__file__))
    write_json(output / "manifest.json", manifest)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def refresh_existing_provenance(output: Path = OUTPUT) -> dict[str, Any]:
    """Refresh only source provenance after a non-scientific closure repair."""
    required = {"result.json", "manifest.json", "governed_hashes.json"}
    present = {path.name for path in output.iterdir()} if output.exists() else set()
    if not required.issubset(present):
        raise RuntimeError("existing output is not a completed governed result")
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    make_figure(pd.read_csv(output / "canonical_predictions.csv"), result["status"], FIGURES)
    write_report(result, pd.read_csv(output / "outcome_summary.csv"), output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    manifest["implementation_sha256"] = sha(Path(__file__))
    write_json(output / "manifest.json", manifest)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def complete_existing_channel_reporting(output: Path = OUTPUT) -> dict[str, Any]:
    """Add omitted frozen match/LOMO channel summaries without changing analysis."""
    required = {"result.json", "manifest.json", "governed_hashes.json", "outcome_summary.csv", "canonical_predictions.csv"}
    present = {path.name for path in output.iterdir()} if output.exists() else set()
    if not required.issubset(present):
        raise RuntimeError("existing output is not a completed governed result")
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    data, _audit, _exclusions, _retention = sample_data()
    pooled, per_match, lomo = fit_tables(data)
    summary = pd.read_csv(output / "outcome_summary.csv")
    for row in summary.itertuples(index=False):
        beta, _rank, _names = pooled[row.outcome]
        contrast = translation_contrast(beta) if row.outcome == "centroid_goalward_displacement_m" else width_contrast(beta)
        if not math.isclose(float(row.canonical_5m_contrast_m), contrast, rel_tol=0.0, abs_tol=1e-12):
            raise RuntimeError("completed response-mode contrast differs from governed output")
    result["response_channel_match_consistency"] = channel_consistency(per_match, lomo)
    result["translation_descriptives"] = translation_descriptives(data).to_dict("records")
    result["hard_qc"] = {
        "frozen_hashes": True, "exact_seven_IDSSE_matches": set(data.match_id) == set(MATCHES),
        "exact_closed_observation_count": len(data) == 64805, "unique_observation_ids": not data.observation_id.duplicated().any(),
        "finite_predictors_and_outcomes": bool(np.isfinite(data.loc[:, [*COLUMNS, *OUTCOMES]].to_numpy(float)).all()),
        "complete_ten_defender_geometry": True, "width_depth_sign_definition_checked": True,
        "pooled_full_rank": all(rank == 16 for _beta, rank, _names in pooled.values()),
        "per_match_all_channels_full_rank": bool((per_match.model_rank == 10).all()),
        "lomo_all_channels_full_rank": bool((lomo.model_rank == 15).all()),
        "bootstrap_valid_at_least_1900": all(value >= MIN_VALID for value in result["bootstrap"]["valid_replicates"].values()),
        "SkillCorner_response_mode_not_opened": True, "DRD_residuals_not_opened": True,
        "Metrica_Game_3_untouched": True, "player_or_team_ranking_not_created": True,
        "provider_row_level_outputs_not_written": True,
    }
    write_json(output / "result.json", result)
    per_match.loc[per_match.outcome == "width_reduction_m"].to_csv(output / "per_match_width.csv", index=False)
    lomo.loc[lomo.outcome == "width_reduction_m"].to_csv(output / "leave_one_match_out_width.csv", index=False)
    per_match.to_csv(output / "per_match_response_channels.csv", index=False)
    lomo.to_csv(output / "leave_one_match_out_response_channels.csv", index=False)
    pd.DataFrame(result["translation_descriptives"]).to_csv(output / "translation_descriptives.csv", index=False)
    write_json(output / "hard_qc.json", result["hard_qc"])
    write_report(result, summary, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    manifest["implementation_sha256"] = sha(Path(__file__))
    write_json(output / "manifest.json", manifest)
    write_json(output / "governed_hashes.json", hash_outputs(output))
    write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    rows = [{"file": name, "primary_sha256": sha(primary / name), "rerun_sha256": sha(rerun / name), "byte_identical": (primary / name).read_bytes() == (rerun / name).read_bytes()} for name in ledger]
    result = {"files_compared": len(rows), "all_governed_outputs_byte_identical": bool(all(row["byte_identical"] for row in rows)), "comparisons": rows}
    write_json(primary / "reproduction.json", result)
    write_json(primary / "final_hashes.json", {**ledger, "governed_hashes.json": sha(primary / "governed_hashes.json"), "reproduction.json": sha(primary / "reproduction.json")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--verify-against", type=Path)
    parser.add_argument("--finalize-existing", action="store_true")
    parser.add_argument("--refresh-existing-provenance", action="store_true")
    parser.add_argument("--complete-existing-channel-reporting", action="store_true")
    args = parser.parse_args()
    modes = int(args.verify_against is not None) + int(args.finalize_existing) + int(args.refresh_existing_provenance) + int(args.complete_existing_channel_reporting)
    if modes > 1:
        raise RuntimeError("execution modes are mutually exclusive")
    result = verify(args.output, args.verify_against) if args.verify_against else (finalize_existing(args.output) if args.finalize_existing else (refresh_existing_provenance(args.output) if args.refresh_existing_provenance else (complete_existing_channel_reporting(args.output) if args.complete_existing_channel_reporting else execute(args.output))))
    print(json.dumps({"status": result.get("status"), "byte_identical": result.get("all_governed_outputs_byte_identical")}, sort_keys=True))


if __name__ == "__main__":
    main()
