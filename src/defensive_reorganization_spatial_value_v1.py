"""Execute the frozen Defensive Reorganization Spatial Form v1 study.

Only compact aggregate outputs are written.  The source reconstructs the
closed Context v1 observation set before reading its observed response target;
it does not read DRD predictions/residuals, SkillCorner, or Game 3.
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
import defensive_reorganization_context_v1 as context  # noqa: E402
import defensive_reorganization_departure_v1 as v1  # noqa: E402
import defensive_reorganization_departure_v2 as v2  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402
import defensive_reorganization_spatial_value_v1_design as design  # noqa: E402


PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_spatial_value_v1.md"
CONFIG = ROOT / "config/defensive_reorganization_spatial_value_v1.json"
OUTPUT = ROOT / "outputs/defensive_reorganization_spatial_value_v1"
RERUN = ROOT / "outputs/.defensive_reorganization_spatial_value_v1_rerun"
FIGURES = ROOT / "figures/defensive_reorganization_spatial_value_v1"
DOC_RESULT = ROOT / "docs/results/defensive_reorganization_spatial_value_v1.md"
MATCHES = design.MATCHES
FROZEN = {
    PROTOCOL: "d394519c7839ad20aba3806b2bbae5bf7b71bdb33a77a70eeb0b6d0c8af08e25",
    CONFIG: "2d8d7abac9738ccb8a4765c657f6865ab445cf390e41ed8063b05a111d62e5df",
}
BASE = design.BASE_COLUMNS
STATIC = BASE + ("half_space", "wide")
DYNAMIC = BASE + ("attacker_unit_lateral_position", "attacker_beyond_same_side_edge_m")
BOOT, MIN_VALID, SEED = 2000, 1900, 20260905


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
    bad = {name: {"actual": actual[name], "expected": expected} for path, expected in FROZEN.items() if actual[str(path.relative_to(ROOT))] != expected for name in [str(path.relative_to(ROOT))]}
    if bad:
        raise RuntimeError(f"frozen Spatial Form v1 hash failure: {bad}")
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("a Spatial Form v1 result already exists")
    closed_context = json.loads((ROOT / "outputs/defensive_reorganization_context_v1/result.json").read_text(encoding="utf-8"))
    drd = json.loads((ROOT / "outputs/defensive_reorganization_departure_v2/result.json").read_text(encoding="utf-8"))
    if closed_context["status"] != "DEFENSIVE REORGANIZATION CONTEXT v1 SUPPORTED":
        raise RuntimeError("closed Context v1 status differs from the frozen inherited state")
    if drd["status"] != "DRD APPLICATION FOUNDATION MIXED":
        raise RuntimeError("closed DRD v2 status differs from the frozen inherited state")
    return {"spatial_form_frozen_hashes": actual, "context_v1_status": closed_context["status"], "drd_v2_status": drd["status"], "DRD_residuals_read": False, "SkillCorner_opened": False, "Metrica_Game_3_accessed": False}


def _spatial_geometry(sample: pd.DataFrame) -> pd.DataFrame:
    """Add only frozen start-frame spatial columns after outcome-blind support gates."""
    additions: list[dict[str, Any]] = []
    for match_id in MATCHES:
        metadata, _events, tracking = concurrent.load_native(match_id)
        signs = v1.period_signs(metadata, tracking)
        by_period = {}
        for period_name in idsse.PERIODS:
            pdata = tracking[period_name]
            by_period[period_name] = ({int(t): index for index, t in enumerate(pdata["time_ns"])}, {(entity["team_id"], entity["person_id"]): entity for entity in pdata["entities"]})
        for row in sample.loc[sample.match_id == match_id].itertuples(index=False):
            period_name = idsse.PERIODS[int(row.period) - 1]
            lookup, entities = by_period[period_name]
            index = lookup[int(row.time_utc_ns)]
            defender_start = np.stack([v1.smoothed(entities[(row.defending_team, player)], index - 50) for player in row.defender_keys])
            focal_start = v1.smoothed(entities[(row.attacking_team, row.attacker_key)], index - 50)
            transformed = v1.attacking_frame(np.vstack([focal_start, defender_start]), signs[(int(row.period), row.attacking_team)], focal_start[1])
            f0, defenders = transformed[0], transformed[1:]
            width = float(np.ptp(defenders[:, 1]))
            if not np.isfinite(width) or width <= 0.0:
                raise RuntimeError("nonpositive frozen defending-unit width")
            additions.append({"observation_id": row.observation_id,
                              "static_abs_lateral_start_m": float(abs(f0[1])),
                              "half_space": float(abs(f0[1]) > 9.15 and abs(f0[1]) <= 20.16),
                              "wide": float(abs(f0[1]) > 20.16),
                              "attacker_unit_lateral_position": float((f0[1] - defenders[:, 1].mean()) / (width / 2.0)),
                              "attacker_beyond_same_side_edge_m": float(max(0.0, f0[1] - defenders[:, 1].max()))})
    extra = pd.DataFrame(additions)
    return sample.merge(extra, on="observation_id", validate="one_to_one").sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)


def sample_data() -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    support, exclusions, retention = v2.build_outcome_blind_sample()
    if set(retention) != set(MATCHES) or not all(item["common_sample_rows"] >= 1000 and item["retention_of_off_ball_base_rows"] >= .9 for item in retention.values()):
        raise RuntimeError("closed Context v1 support registry cannot be reconstructed")
    spatial = _spatial_geometry(support)
    # This is the first permitted response read.  The Context v1 set was made
    # by the identical frozen support constructor; IDs are fingerprinted below.
    data = v2.join_target_after_gate(spatial)
    if len(data) != len(support) or data.observation_id.duplicated().any() or not np.isfinite(data.loc[:, ["Y_m", *DYNAMIC, *STATIC]].to_numpy(float)).all():
        raise RuntimeError("invalid post-gate Spatial Form v1 sample")
    ordered = data.sort_values(["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort").reset_index(drop=True)
    fingerprint = hashlib.sha256("\n".join(ordered.observation_id.tolist()).encode("utf-8")).hexdigest()
    audit = {"context_v1_observation_set_reconstructed_by_frozen_v2_support": True,
             "observation_id_count": int(len(ordered)), "observation_id_sha256": fingerprint,
             "target_read_only_after_outcome_blind_support_and_spatial_geometry": True,
             "DRD_residuals_read": False}
    return ordered, audit, exclusions


def fit(frame: pd.DataFrame, columns: tuple[str, ...] = BASE) -> tuple[np.ndarray, int, tuple[str, ...]]:
    return design.fit_equal_match_ols(frame.Y_m.to_numpy(float), frame.loc[:, columns].to_numpy(float), frame.match_id.to_numpy())


def continuous_map(beta: np.ndarray, columns: tuple[str, ...]) -> dict[str, float]:
    return {name: float(value) for name, value in zip(columns, beta[-len(columns):], strict=True)}


def primary_fits(data: pd.DataFrame) -> tuple[dict[str, float], int, pd.DataFrame, pd.DataFrame]:
    beta, rank, _ = fit(data)
    pooled = continuous_map(beta, BASE)
    per_match, lomo = [], []
    for match in MATCHES:
        local_beta, local_rank, _ = fit(data.loc[data.match_id == match])
        local = continuous_map(local_beta, BASE)
        per_match.append({"match_id": match, "rows": int((data.match_id == match).sum()), "model_rank": local_rank,
                          "beta_goalward_m_per_m": local["attacker_goalward_displacement_m"], "beta_outward_m_per_m": local["attacker_outward_displacement_m"],
                          "outward_minus_goalward_m_per_m": local["attacker_outward_displacement_m"] - local["attacker_goalward_displacement_m"]})
        lomo_beta, lomo_rank, _ = fit(data.loc[data.match_id != match])
        local_lomo = continuous_map(lomo_beta, BASE)
        lomo.append({"heldout_match_id": match, "training_rows": int((data.match_id != match).sum()), "model_rank": lomo_rank,
                     "outward_minus_goalward_m_per_m": local_lomo["attacker_outward_displacement_m"] - local_lomo["attacker_goalward_displacement_m"]})
    return pooled, rank, pd.DataFrame(per_match), pd.DataFrame(lomo)


def trim_data(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    keep = np.ones(len(data), dtype=bool); bounds: dict[str, dict[str, list[float]]] = {}
    for match, part in data.groupby("match_id", sort=True):
        local = np.ones(len(part), dtype=bool); bounds[match] = {}
        for column in ("attacker_goalward_displacement_m", "attacker_outward_displacement_m"):
            low, high = np.quantile(part[column].to_numpy(float), [.025, .975], method="linear")
            bounds[match][column] = [float(low), float(high)]
            local &= (part[column].to_numpy(float) >= low) & (part[column].to_numpy(float) <= high)
        keep[part.index.to_numpy()] = local
    trimmed = data.loc[keep].reset_index(drop=True)
    beta, rank, _ = fit(trimmed)
    return trimmed, {"bounds": bounds, "rows_retained": int(len(trimmed)), "retention": float(len(trimmed) / len(data)), "model_rank": rank,
                     "outward_minus_goalward_m_per_m": design.primary_contrast(beta), "quantile_method": "numpy_linear"}


def block_indices(data: pd.DataFrame) -> dict[tuple[str, int, int], np.ndarray]:
    result = {key: value.to_numpy() for key, value in data.groupby(["match_id", "period", "block_id"], sort=True).groups.items()}
    if not result:
        raise RuntimeError("no frozen match-period blocks")
    return result


def _bootstrap_draw_indexes(data: pd.DataFrame, rng: np.random.Generator) -> list[np.ndarray]:
    groups = block_indices(data); choices: list[np.ndarray] = []
    for match in MATCHES:
        for period in sorted(data.loc[data.match_id == match, "period"].unique()):
            keys = [key for key in groups if key[:2] == (match, int(period))]
            if not keys:
                raise RuntimeError("represented match-period lacks 60-second blocks")
            choices.append(np.concatenate([groups[keys[int(item)]] for item in rng.integers(0, len(keys), len(keys))]))
    return choices


def lomo_predictions(data: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    """Fixed seven-fold outer prediction ledger.

    The frozen fixed-effect OLS uses the global intercept plus training-match
    indicators.  The unseen match has no indicator and therefore receives the
    common intercept; both representations use this identical predeclared
    coding and their paired absolute errors are compared only to each other.
    """
    rows = []
    for heldout in MATCHES:
        train, test = data.loc[data.match_id != heldout], data.loc[data.match_id == heldout]
        beta, rank, names = fit(train, columns)
        # ``matrix`` on the test set must use training names so that the unseen
        # group is represented by the common intercept (all effects zero).
        z = test.loc[:, columns].to_numpy(float)
        effects = np.zeros((len(test), len(names) - 1), dtype=float)
        x = np.column_stack([np.ones(len(test)), effects, z])
        prediction = x @ beta
        out = test[["observation_id", "match_id", "period", "block_id", "time_period_s", "Y_m"]].copy()
        out["heldout_match_id"] = heldout; out["prediction_m"] = prediction; out["absolute_error_m"] = np.abs(out.Y_m.to_numpy(float) - prediction)
        out["train_rank"] = rank; out["train_columns"] = len(beta); rows.append(out)
    return pd.concat(rows, ignore_index=True)


def secondary(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    static, dynamic = lomo_predictions(data, STATIC), lomo_predictions(data, DYNAMIC)
    merged = static.merge(dynamic, on=["observation_id", "match_id", "period", "block_id", "time_period_s", "Y_m", "heldout_match_id"], suffixes=("_static", "_dynamic"), validate="one_to_one")
    rows, s_by, d_by = [], {}, {}
    for match in MATCHES:
        part = merged.loc[merged.match_id == match]
        s_by[match] = float(part.absolute_error_m_static.mean()); d_by[match] = float(part.absolute_error_m_dynamic.mean())
        rows.append({"match_id": match, "rows": int(len(part)), "static_MAE_m": s_by[match], "dynamic_MAE_m": d_by[match], "static_minus_dynamic_MAE_m": s_by[match] - d_by[match],
                     "static_train_rank": int(part.train_rank_static.iloc[0]), "dynamic_train_rank": int(part.train_rank_dynamic.iloc[0]),
                     "static_columns": int(part.train_columns_static.iloc[0]), "dynamic_columns": int(part.train_columns_dynamic.iloc[0])})
    summary = {"static_macro_MAE_m": float(np.mean(list(s_by.values()))), "dynamic_macro_MAE_m": float(np.mean(list(d_by.values()))),
               "static_weighted_MAE_m": float(merged.absolute_error_m_static.mean()), "dynamic_weighted_MAE_m": float(merged.absolute_error_m_dynamic.mean()),
               "static_by_match": s_by, "dynamic_by_match": d_by,
               "heldout_unseen_match_intercept": "common_global_intercept_with_unseen_match_effect_zero"}
    return merged, {"per_match": pd.DataFrame(rows), "summary": summary}


def bootstrap(data: pd.DataFrame, errors: pd.DataFrame) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(SEED)); contrasts, error_differences = [], []
    groups = block_indices(data)
    data_strata = {(match, int(period)): [key for key in groups if key[:2] == (match, int(period))]
                   for match in MATCHES for period in sorted(data.loc[data.match_id == match, "period"].unique())}
    x, _names = design.matrix(data.loc[:, BASE].to_numpy(float), data.match_id.to_numpy())
    y = data.Y_m.to_numpy(float)
    sufficient = {key: (x[index].T @ x[index], x[index].T @ y[index], len(index)) for key, index in groups.items()}
    error_stats = {(match, int(period), int(block)): (float((group.absolute_error_m_static - group.absolute_error_m_dynamic).sum()), int(len(group)))
                   for (match, period, block), group in errors.groupby(["match_id", "period", "block_id"], sort=True)}
    for _ in range(BOOT):
        selected_keys = []
        for (match, period), keys in data_strata.items():
            if not keys:
                raise RuntimeError("represented match-period lacks 60-second blocks")
            selected_keys.extend(keys[int(item)] for item in rng.integers(0, len(keys), len(keys)))
        frequency: dict[tuple[str, int, int], int] = {}
        for key in selected_keys:
            frequency[key] = frequency.get(key, 0) + 1
        try:
            xtx = np.zeros((x.shape[1], x.shape[1])); xty = np.zeros(x.shape[1])
            for match in MATCHES:
                selected = [(key, count) for key, count in frequency.items() if key[0] == match]
                total = sum(count * sufficient[key][2] for key, count in selected)
                for key, count in selected:
                    scale = count / total
                    xtx += scale * sufficient[key][0]; xty += scale * sufficient[key][1]
            if np.linalg.matrix_rank(xtx) != x.shape[1]:
                continue
            beta, _, _, _ = np.linalg.lstsq(xtx, xty, rcond=None)
            contrasts.append(design.primary_contrast(beta))
        except (np.linalg.LinAlgError, ValueError):
            continue
        # The identical primary block draw is applied to the fixed paired
        # absolute-error ledger without refitting either secondary model.
        values = []
        for match in MATCHES:
            selected = [key for key in selected_keys if key[0] == match]
            total_error, total_rows = sum(error_stats[key][0] for key in selected), sum(error_stats[key][1] for key in selected)
            values.append((match, total_error / total_rows))
        error_differences.append(float(np.mean([value for _match, value in values])))
    contrast_array, error_array = np.asarray(contrasts, float), np.asarray(error_differences, float)
    if len(contrast_array) < MIN_VALID or len(error_array) < MIN_VALID:
        raise RuntimeError("fewer than 1,900 valid frozen bootstrap replicates")
    return {"replicates_requested": BOOT, "valid_primary": int(len(contrast_array)), "valid_secondary": int(len(error_array)),
            "primary_ci_low": float(np.quantile(contrast_array, .025)), "primary_ci_high": float(np.quantile(contrast_array, .975)),
            "secondary_ci_low": float(np.quantile(error_array, .025)), "secondary_ci_high": float(np.quantile(error_array, .975)), "seed": SEED}, contrast_array, error_array


def canonical(data: pd.DataFrame, beta: np.ndarray, names: tuple[str, ...]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    vectors = {"goalward": (5.0, 0.0), "outward": (0.0, 5.0), "away_from_goal": (-5.0, 0.0), "inward": (0.0, -5.0)}
    for label, (goalward, outward) in vectors.items():
        predictions = []
        for match in MATCHES:
            values = data.loc[data.match_id == match, list(BASE)].median().to_numpy(float)
            values[-3] = 5.0; values[-2] = goalward; values[-1] = outward
            effect = np.zeros(len(names) - 1); effect[list(names).index(match) - 1] = 1.0 if match in names[1:] else 0.0
            predictions.append(float(np.r_[1.0, effect, values] @ beta))
        rows.append({"canonical_movement": label, "goalward_displacement_m": goalward, "outward_displacement_m": outward, "exposure_path_m": 5.0,
                     "equal_match_adjusted_predicted_Y_m": float(np.mean(predictions))})
    y = data.Y_m.to_numpy(float)
    support = {column: {"p10": float(np.quantile(data[column], .1)), "p90": float(np.quantile(data[column], .9)), "min": float(data[column].min()), "max": float(data[column].max())} for column in ("attacker_goalward_displacement_m", "attacker_outward_displacement_m", "attacker_path_exposure_m", "attacker_path_prior_m")}
    return pd.DataFrame(rows), {"Y_IQR_m": [float(np.quantile(y, .25)), float(np.quantile(y, .75))], "predictor_support": support}


def figure(data: pd.DataFrame, canonical_table: pd.DataFrame, per_match: pd.DataFrame, status: str, secondary_status: str) -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    pitch, forest = axes
    pitch.set(xlim=(-52.5, 52.5), ylim=(-34, 34), aspect="equal", xticks=[], yticks=[])
    pitch.add_patch(plt.Rectangle((-52.5, -34), 105, 68, fill=False, color="#243447", lw=1.2)); pitch.axvline(0, color="#c0c8d0", lw=.7)
    defenders = np.array([[-8, -16], [-4, -8], [1, 0], [5, 11], [-6, 18], [0, -2], [6, -13], [10, 17], [-1, 7], [3, 23]])
    pitch.scatter(defenders[:, 0], defenders[:, 1], color="#2864a0", s=42, label="defending outfield unit")
    step = max(1, len(data) // 3500)
    starts = data.iloc[::step]
    pitch.scatter(starts.attacker_minus_unit_goalward_m, starts.attacker_minus_unit_outward_m, color="#90a4b8", alpha=.10, s=5, label="observed start support")
    origin = np.array([float(data.attacker_minus_unit_goalward_m.median()), float(data.attacker_minus_unit_outward_m.median())])
    pitch.scatter(*origin, color="#e76f51", marker="*", s=130, label="median focal start")
    colors = {"goalward": "#1d5f8a", "outward": "#e76f51", "away_from_goal": "#7b5ea7", "inward": "#4c956c"}
    mapping = {"goalward": (5, 0), "outward": (0, 5), "away_from_goal": (-5, 0), "inward": (0, -5)}
    for row in canonical_table.itertuples(index=False):
        dx, dy = mapping[row.canonical_movement]
        pitch.arrow(*origin, dx, dy, width=.11, head_width=1.0, length_includes_head=True, color=colors[row.canonical_movement])
        offset_x, offset_y = {"goalward": (1.3, 1.5), "outward": (2.0, 1.0), "away_from_goal": (-1.3, 1.5), "inward": (2.0, -1.8)}[row.canonical_movement]
        pitch.text(origin[0] + dx * 1.18 + offset_x, origin[1] + dy * 1.18 + offset_y, f"{row.canonical_movement.replace('_', ' ')}\n{row.equal_match_adjusted_predicted_Y_m:.3f} m", color=colors[row.canonical_movement], fontsize=8, ha="center")
    pitch.set_title("Canonical movement geometry (5 m; adjusted predictions)", loc="left", fontweight="bold")
    pitch.legend(loc="lower left", frameon=False, fontsize=8)
    forest.axvline(0, color="#9ba7b5", lw=.8)
    ordered = per_match.sort_values("match_id")
    forest.scatter(ordered.outward_minus_goalward_m_per_m, np.arange(7), color="#e76f51", s=35, label="match contrast")
    forest.set(yticks=np.arange(7), yticklabels=ordered.match_id, xlabel="Outward minus goalward coefficient (m/m)", title="Seven observed match contrasts")
    forest.invert_yaxis(); forest.legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle(f"Spatial form of localized defensive reorganization — {status}; {secondary_status}", fontweight="bold")
    paths = []
    for suffix in ("png", "svg", "pdf"):
        path = FIGURES / f"spatial_form.{suffix}"; fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight"); paths.append(path)
    plt.close(fig)
    return paths


def write_report(result: dict[str, Any], output: Path) -> None:
    p, b, s = result["primary"], result["bootstrap"], result["secondary"]
    lines = ["# Defensive Reorganization Spatial Form v1 — IDSSE result", "", f"**Primary classification:** **{result['primary_status']}**", "", f"**Secondary classification:** **{result['secondary_status']}**", "",
             "This governed seven-match study tests the fixed outward-minus-goalward coefficient contrast on observed near-minus-middle defender-relative path. It is observational geometry, not a tactical or value result.", "",
             "## Primary contrast", "", "| Quantity | Estimate |", "|---|---:|",
             f"| Goalward coefficient | {p['beta_goalward_m_per_m']:.6f} m/m |", f"| Outward coefficient | {p['beta_outward_m_per_m']:.6f} m/m |",
             f"| Outward minus goalward | {p['outward_minus_goalward_m_per_m']:.6f} m/m |", f"| Frozen 95% interval | [{b['primary_ci_low']:.6f}, {b['primary_ci_high']:.6f}] |",
             f"| Hypothetical 5 m outward versus 5 m goalward difference | {p['five_m_translation_m']:.6f} m |", "",
             "The 5 m translation compares straight outward and straight goalward movement at equal frozen path magnitude and starting context; it is not a causal or value comparison.", "",
             "## Secondary representation", "", f"Static macro heldout MAE: {s['static_macro_MAE_m']:.6f} m. Dynamic macro heldout MAE: {s['dynamic_macro_MAE_m']:.6f} m. The frozen paired static-minus-dynamic interval was [{b['secondary_ci_low']:.6f}, {b['secondary_ci_high']:.6f}] m.", "",
             "## Boundary", "", "The result does not establish influence, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, space creation, tactical success, player quality, gravity, or attacking value. No DRD residual, SkillCorner outcome, Metrica Game 3 datum, player ranking, or new spatial representation was used."]
    text = "\n".join(lines) + "\n"; (output / "result_report.md").write_text(text, encoding="utf-8"); DOC_RESULT.write_text(text, encoding="utf-8")


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "reproduction.json", "final_hashes.json"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def execute(output: Path = OUTPUT) -> dict[str, Any]:
    firewall = verify_frozen(output); output.mkdir(parents=True, exist_ok=True)
    data, sample_audit, exclusions = sample_data()
    pooled_beta, pooled_rank, names = fit(data); pooled = continuous_map(pooled_beta, BASE)
    per_match, lomo = primary_fits(data)[2:]
    trimmed, trim = trim_data(data)
    errors, secondary_data = secondary(data)
    boot, _contrasts, _error_diff = bootstrap(data, errors)
    contrast = float(pooled["attacker_outward_displacement_m"] - pooled["attacker_goalward_displacement_m"])
    primary_status, primary_gates = design.classify_primary(contrast, boot["primary_ci_low"], boot["primary_ci_high"], per_match.outward_minus_goalward_m_per_m, lomo.outward_minus_goalward_m_per_m, trim["outward_minus_goalward_m_per_m"])
    secondary_status, secondary_gates = design.classify_secondary(secondary_data["summary"]["static_macro_MAE_m"], secondary_data["summary"]["dynamic_macro_MAE_m"], secondary_data["summary"]["static_by_match"], secondary_data["summary"]["dynamic_by_match"], boot["secondary_ci_low"], boot["secondary_ci_high"])
    canonical_table, support = canonical(data, pooled_beta, names)
    sample_summary = data.groupby("match_id", sort=True).agg(eligible_rows=("observation_id", "size"), eligible_anchors=("time_period_s", "nunique"), periods=("period", lambda x: ",".join(str(int(v)) for v in sorted(set(x))))).reset_index()
    hard_qc = {"frozen_hashes": True, "exact_seven_IDSSE_matches": set(data.match_id) == set(MATCHES), "unique_observation_ids": not data.observation_id.duplicated().any(),
               "finite_frozen_geometry": bool(np.isfinite(data.loc[:, DYNAMIC].to_numpy(float)).all()), "positive_unit_width": bool((data.defending_unit_width_m > 0).all()),
               "exact_context_v1_observation_count": len(data) == 64805, "pooled_full_rank": pooled_rank == 16,
               "per_match_full_rank": bool((per_match.model_rank == 10).all()), "lomo_full_rank": bool((lomo.model_rank == 15).all()),
               "secondary_all_folds_full_rank": bool((secondary_data["per_match"].static_train_rank == 17).all() and (secondary_data["per_match"].dynamic_train_rank == 17).all()),
               "bootstrap_valid_at_least_1900": boot["valid_primary"] >= MIN_VALID and boot["valid_secondary"] >= MIN_VALID,
               "DRD_residual_not_read": True, "SkillCorner_not_opened": True, "Game3_untouched": True, "player_ranking_not_created": True,
               "no_provider_row_level_outputs_written": True}
    if not all(hard_qc.values()):
        raise RuntimeError(f"hard QC failure: {hard_qc}")
    primary = {"beta_goalward_m_per_m": pooled["attacker_goalward_displacement_m"], "beta_outward_m_per_m": pooled["attacker_outward_displacement_m"], "outward_minus_goalward_m_per_m": contrast, "five_m_translation_m": 5.0 * contrast, "pooled_model_rank": pooled_rank, "trimmed_outward_minus_goalward_m_per_m": trim["outward_minus_goalward_m_per_m"], "trimmed_rows": trim["rows_retained"], "trimmed_retention": trim["retention"]}
    result = {"primary_status": primary_status, "secondary_status": secondary_status, "firewall": firewall, "sample_audit": sample_audit, "primary": primary, "primary_gates": primary_gates,
              "secondary": {**secondary_data["summary"], **secondary_gates}, "bootstrap": boot, "support": support, "hard_qc": hard_qc,
              "execution": {"DRD_residual_inspected": False, "SkillCorner_opened": False, "Metrica_Game_3_accessed": False, "Metrica_transport_executed": False, "new_spatial_representation_added": False}}
    write_json(output / "result.json", result); sample_summary.to_csv(output / "sample_summary.csv", index=False); per_match.to_csv(output / "per_match_primary.csv", index=False); lomo.to_csv(output / "leave_one_match_out_primary.csv", index=False)
    pd.DataFrame([{"column": name, "estimate_m_per_m": value} for name, value in pooled.items()]).to_csv(output / "pooled_coefficients.csv", index=False)
    pd.DataFrame([{"estimate": contrast, "ci_low": boot["primary_ci_low"], "ci_high": boot["primary_ci_high"], "valid_bootstrap_replicates": boot["valid_primary"], "five_m_translation_m": 5.0 * contrast}]).to_csv(output / "primary_contrast.csv", index=False)
    pd.DataFrame([trim]).to_csv(output / "trim_robustness.csv", index=False); canonical_table.to_csv(output / "canonical_predictions.csv", index=False); secondary_data["per_match"].to_csv(output / "secondary_per_match_MAE.csv", index=False)
    pd.DataFrame([{**secondary_data["summary"], **secondary_gates, "ci_low": boot["secondary_ci_low"], "ci_high": boot["secondary_ci_high"], "valid_bootstrap_replicates": boot["valid_secondary"]}]).to_csv(output / "secondary_summary.csv", index=False)
    exclusions.to_csv(output / "eligibility_exclusions.csv", index=False); write_json(output / "hard_qc.json", hard_qc)
    write_json(output / "manifest.json", {"protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "implementation_sha256": sha(Path(__file__)), "status": primary_status, "secondary_status": secondary_status, "bootstrap_seed": SEED, "bootstrap_replicates": BOOT, "provider_row_level_outputs": "not_written"})
    write_report(result, output)
    if primary_status == "SPATIAL FORM SUPPORTED":
        paths = figure(data, canonical_table, per_match, primary_status, secondary_status); result["figure_paths"] = [str(path.relative_to(ROOT)) for path in paths]; write_json(output / "result.json", result)
    write_json(output / "governed_hashes.json", hash_outputs(output)); write_json(output / "final_hashes.json", {**json.loads((output / "governed_hashes.json").read_text(encoding="utf-8")), "governed_hashes.json": sha(output / "governed_hashes.json")})
    return result


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    rows = [{"file": name, "primary_sha256": sha(primary / name), "rerun_sha256": sha(rerun / name), "byte_identical": (primary / name).read_bytes() == (rerun / name).read_bytes()} for name in ledger]
    result = {"files_compared": len(rows), "all_governed_outputs_byte_identical": bool(all(row["byte_identical"] for row in rows)), "comparisons": rows}
    write_json(primary / "reproduction.json", result); write_json(primary / "final_hashes.json", {**ledger, "governed_hashes.json": sha(primary / "governed_hashes.json"), "reproduction.json": sha(primary / "reproduction.json")}); return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=OUTPUT); parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args(); result = verify(args.output, args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps({"status": result.get("primary_status"), "secondary_status": result.get("secondary_status"), "byte_identical": result.get("all_governed_outputs_byte_identical")}, sort_keys=True))


if __name__ == "__main__":
    main()
