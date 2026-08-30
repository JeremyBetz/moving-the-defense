"""Execute the frozen Game-1 speed-valley prominence refinement once.

Only player-own tracking geometry and the historical global eligibility boundaries
are used. Game 2, Game 3, defensive outcomes, and tactical annotations are absent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from post5b_attacking_movement_segmentation_audit import (
    DATA,
    GK,
    add_diagnostics,
    consolidate_valleys,
    geometry,
    global_exclusions,
    load_tracking,
    player_blocks,
    raw_valleys,
    segment_method_a,
    segment_method_b,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "post5b_attacking_movement_prominence_refinement_rules.json"
HISTORICAL = ROOT / "outputs" / "post5b_movement_segmentation_audit"
OUT = ROOT / "outputs" / "post5b_attacking_movement_prominence_refinement"
FIG = ROOT / "figures" / "post5b_attacking_movement_prominence_refinement"
THRESHOLDS = (0.0, 0.25, 0.5, 1.0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valley_prominence(speed: np.ndarray, index: int) -> float:
    """Frozen speed-domain equivalent of peak prominence on negative speed."""
    value = float(speed[index])
    left = index - 1
    left_max = value
    while left >= 0:
        left_max = max(left_max, float(speed[left]))
        if speed[left] < value:
            break
        left -= 1
    right = index + 1
    right_max = value
    while right < len(speed):
        right_max = max(right_max, float(speed[right]))
        if speed[right] < value:
            break
        right += 1
    return min(left_max, right_max) - value


def prominence_self_test() -> None:
    tests = [
        (np.array([4.0, 3.8, 4.1]), 1, 0.2),
        (np.array([4.0, 1.2, 4.3]), 1, 2.8),
        (np.array([5.0, 2.0, 4.0, 1.0, 5.0]), 1, 2.0),
        (np.array([5.0, 2.0, 4.0, 1.0, 5.0]), 3, 4.0),
    ]
    for signal, index, expected in tests:
        actual = valley_prominence(signal, index)
        if not np.isclose(actual, expected, atol=1e-12):
            raise AssertionError((signal, index, expected, actual))


def segment_with_prominence(
    block: pd.DataFrame, team: str, player: str, block_id: str, threshold: float
) -> tuple[list[dict], list[int], list[dict]]:
    speed = block.speed_mps.to_numpy()
    times = block["Time [s]"].to_numpy()
    candidates = raw_valleys(speed)
    candidate_rows = []
    qualified = []
    for index in candidates:
        prominence = valley_prominence(speed, index)
        passes = prominence >= threshold
        candidate_rows.append({
            "block_id": block_id, "team": team, "player": player,
            "period": int(block.Period.iloc[index]), "index": int(index),
            "frame": int(block.Frame.iloc[index]), "time_s": float(times[index]),
            "speed_mps": float(speed[index]), "prominence_mps": float(prominence),
            "threshold_mps": threshold, "passes_prominence": bool(passes)
        })
        if passes:
            qualified.append(index)
    valleys = consolidate_valleys(qualified, speed, times, 1.0)
    retained = set(valleys)
    for row in candidate_rows:
        row["retained_after_consolidation"] = row["index"] in retained

    episodes = []
    for start, end in zip(valleys[:-1], valleys[1:]):
        q = block.iloc[start:end + 1]
        if q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0] < 1.0 - 1e-9:
            continue
        result = geometry(q)
        result.update({
            "team": team, "player": player, "period": int(q.Period.iloc[0]), "block_id": block_id,
            "start_frame": int(q.Frame.iloc[0]), "end_frame": int(q.Frame.iloc[-1]),
            "start_s": float(q["Time [s]"].iloc[0]), "end_s": float(q["Time [s]"].iloc[-1]),
            "start_x_m": float(q.sx_m.iloc[0]), "start_y_m": float(q.sy_m.iloc[0]),
            "end_x_m": float(q.sx_m.iloc[-1]), "end_y_m": float(q.sy_m.iloc[-1])
        })
        episodes.append(result)
    return episodes, valleys, candidate_rows


def add_ids(rows: list[dict], prefix: str) -> pd.DataFrame:
    table = pd.DataFrame(rows)
    table.insert(0, "episode_id", [f"{prefix}{i:06d}" for i in range(1, len(table) + 1)])
    return table


def baseline_reproduction(actual: pd.DataFrame) -> dict:
    expected = pd.read_csv(HISTORICAL / "method_a_episodes.csv", dtype={"player": str})
    actual = actual.copy(); actual["player"] = actual.player.astype(str)
    key = ["team", "player", "period", "block_id", "start_frame", "end_frame", "start_s", "end_s"]
    same_keys = expected[key].astype(str).equals(actual[key].astype(str))
    numerical = [
        "duration_s", "path_m", "displacement_m", "delta_x_m", "delta_y_m",
        "displacement_path_ratio", "peak_speed_mps", "mean_speed_mps"
    ]
    max_difference = max(float(np.nanmax(np.abs(expected[c].to_numpy() - actual[c].to_numpy()))) for c in numerical)
    diagnostic = ["diag_fragmentation_any", "diag_merging_any", "method_b_overlap"]
    same_diagnostics = all(expected[c].astype(bool).equals(actual[c].astype(bool)) for c in diagnostic)
    passed = len(actual) == 38651 and len(expected) == len(actual) and same_keys and same_diagnostics and max_difference <= 1e-9
    return {
        "passed": bool(passed), "expected_episodes": int(len(expected)), "actual_episodes": int(len(actual)),
        "same_episode_keys": bool(same_keys), "same_diagnostics": bool(same_diagnostics),
        "maximum_numeric_difference": max_difference
    }


def metrics(table: pd.DataFrame, baseline: dict | None = None) -> dict:
    n = len(table)
    fragmentation = float(table.diag_fragmentation_any.mean() * 100)
    merging = float(table.diag_merging_any.mean() * 100)
    coverage = float(((table.peak_speed_mps < 5.5) & (table.displacement_m >= 3.0)).mean())
    result = {
        "episodes": n,
        "fragmentation_any_n": int(table.diag_fragmentation_any.sum()),
        "fragmentation_any_pct": fragmentation,
        "merging_direction_any_n": int(table.diag_merging_any.sum()),
        "merging_direction_any_pct": merging,
        "lower_speed_displacement_ge3_n": int(((table.peak_speed_mps < 5.5) & (table.displacement_m >= 3.0)).sum()),
        "lower_speed_coverage": coverage,
        "diag_short_n": int(table.diag_short.sum()), "diag_short_pct": float(table.diag_short.mean() * 100),
        "diag_tiny_path_n": int(table.diag_tiny_path.sum()), "diag_tiny_path_pct": float(table.diag_tiny_path.mean() * 100),
        "diag_tiny_displacement_n": int(table.diag_tiny_displacement.sum()), "diag_tiny_displacement_pct": float(table.diag_tiny_displacement.mean() * 100),
        "diag_long_n": int(table.diag_long.sum()), "diag_long_pct": float(table.diag_long.mean() * 100),
        "diag_low_displacement_path_ratio_n": int(table.diag_low_displacement_path_ratio.sum()),
        "diag_low_displacement_path_ratio_pct": float(table.diag_low_displacement_path_ratio.mean() * 100),
        "diag_direction_change_n": int(table.diag_direction_change.sum()),
        "diag_direction_change_pct": float(table.diag_direction_change.mean() * 100),
    }
    if baseline is None:
        result["fragmentation_relative_reduction_pct"] = 0.0
        result["coverage_relative_change_pct"] = 0.0
    else:
        result["fragmentation_relative_reduction_pct"] = float(
            100 * (baseline["fragmentation_any_pct"] - fragmentation) / baseline["fragmentation_any_pct"]
        )
        result["coverage_relative_change_pct"] = float(
            100 * (coverage - baseline["lower_speed_coverage"]) / baseline["lower_speed_coverage"]
        )
    result["fragmentation_pass"] = bool(fragmentation <= 33.776)
    result["merging_direction_pass"] = bool(merging <= 3.97)
    result["coverage_pass"] = bool(coverage >= 0.368955525083439)
    return result


def classify(summary: pd.DataFrame, qc_pass: bool) -> tuple[list[float], float | None, str]:
    nonzero = summary[summary.threshold_mps > 0].copy()
    eligible = nonzero[
        nonzero.fragmentation_pass & nonzero.merging_direction_pass & nonzero.coverage_pass & qc_pass
    ].threshold_mps.astype(float).tolist()
    selected = min(eligible) if eligible else None
    if eligible:
        classification = "A"
    elif bool(nonzero.fragmentation_pass.any()):
        classification = "B"
    else:
        classification = "C"
    return eligible, selected, classification


def distribution_summary(tables: dict[float, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    columns = ["duration_s", "path_m", "displacement_m", "peak_speed_mps", "displacement_path_ratio"]
    for threshold, table in tables.items():
        for column in columns:
            values = table[column].dropna()
            rows.append({
                "threshold_mps": threshold, "quantity": column, "n": int(len(values)),
                "min": float(values.min()), "q1": float(values.quantile(.25)),
                "median": float(values.median()), "q3": float(values.quantile(.75)), "max": float(values.max())
            })
    return pd.DataFrame(rows)


def group_counts(tables: dict[float, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    definitions = {
        "team": ["team"], "period": ["period"], "team_period": ["team", "period"],
        "player": ["team", "player"]
    }
    baseline_shares = {}
    for grouping, columns in definitions.items():
        counts = tables[0.0].groupby(columns, dropna=False).size()
        baseline_shares[grouping] = (counts / len(tables[0.0])).to_dict()
    for threshold, table in tables.items():
        for grouping, columns in definitions.items():
            counts = table.groupby(columns, dropna=False).size()
            for identity, count in counts.items():
                identity_tuple = identity if isinstance(identity, tuple) else (identity,)
                baseline_key = identity if len(columns) > 1 else identity_tuple[0]
                share = float(count / len(table))
                rows.append({
                    "threshold_mps": threshold, "grouping": grouping,
                    "group": "|".join(map(str, identity_tuple)), "episodes": int(count),
                    "episode_share": share, "baseline_episode_share": float(baseline_shares[grouping].get(baseline_key, 0.0)),
                    "share_change_percentage_points": float(100 * (share - baseline_shares[grouping].get(baseline_key, 0.0)))
                })
    return pd.DataFrame(rows)


def deterministic_sample(baseline: pd.DataFrame) -> pd.DataFrame:
    selected = []
    for (team, period), group in baseline.groupby(["team", "period"], sort=True):
        ordered = group.assign(player_number=group.player.astype(int)).sort_values(
            ["start_s", "player_number", "start_frame", "end_frame"]
        )
        n = len(ordered)
        for q, label in [(1/6, "chronological_1_6"), (3/6, "chronological_3_6"), (5/6, "chronological_5_6")]:
            index = int(np.floor((n - 1) * q + 0.5))
            selected.append((ordered.iloc[index].episode_id, label))
        fragmentation = ordered[ordered.diag_fragmentation_any]
        selected.append((fragmentation.iloc[0].episode_id, "earliest_fragmentation"))
        merging = ordered[ordered.diag_merging_any].sort_values(
            ["duration_s", "start_s", "player_number", "start_frame", "end_frame"],
            ascending=[False, True, True, True, True]
        )
        selected.append((merging.iloc[0].episode_id, "longest_merging_risk"))
    reasons = pd.DataFrame(selected, columns=["episode_id", "reason"]).groupby("episode_id").reason.apply(
        lambda x: "|".join(x)
    ).reset_index()
    return reasons.merge(baseline, on="episode_id", how="left", validate="one_to_one")


def boundary_tables(
    retained: dict[float, list[dict]], candidate_rows: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for threshold, rows in retained.items():
        for row in rows:
            frames.append({"threshold_mps": threshold, **row})
    retained_table = pd.DataFrame(frames)
    baseline_keys = set(zip(retained_table.loc[retained_table.threshold_mps.eq(0), "block_id"],
                            retained_table.loc[retained_table.threshold_mps.eq(0), "index"]))
    summaries, removed_rows = [], []
    prominence_lookup = candidate_rows.drop_duplicates(["block_id", "index"]).set_index(["block_id", "index"]).prominence_mps
    for threshold in THRESHOLDS:
        current = set(zip(retained_table.loc[retained_table.threshold_mps.eq(threshold), "block_id"],
                          retained_table.loc[retained_table.threshold_mps.eq(threshold), "index"]))
        removed = baseline_keys - current; added = current - baseline_keys
        summaries.append({"threshold_mps": threshold, "retained_boundaries": len(current),
                          "historical_boundaries_removed": len(removed), "nonhistorical_boundaries_added": len(added)})
        values = np.array([prominence_lookup.loc[key] for key in removed], dtype=float)
        removed_rows.append({
            "threshold_mps": threshold, "removed_n": len(values),
            "min": float(np.min(values)) if len(values) else np.nan,
            "q1": float(np.quantile(values, .25)) if len(values) else np.nan,
            "median": float(np.median(values)) if len(values) else np.nan,
            "q3": float(np.quantile(values, .75)) if len(values) else np.nan,
            "max": float(np.max(values)) if len(values) else np.nan
        })
    return pd.DataFrame(summaries), pd.DataFrame(removed_rows)


def plot_visual_sample(
    sample: pd.DataFrame, blocks: dict[str, pd.DataFrame], retained: dict[float, list[dict]], selected: float | None
) -> None:
    rows = sample.sort_values(["team", "period", "start_s"]).reset_index(drop=True)
    columns = 4; nrows = int(np.ceil(len(rows) / columns))
    fig, axes = plt.subplots(nrows, columns, figsize=(18, 3.3 * nrows), constrained_layout=True)
    axes = np.atleast_1d(axes).ravel()
    colors = {0.0: "#666666", 0.25: "#1f77b4", 0.5: "#ff7f0e", 1.0: "#2ca02c"}
    for ax, (_, row) in zip(axes, rows.iterrows()):
        block = blocks[row.block_id]
        view = block[block["Time [s]"].between(row.start_s - 1.0, row.end_s + 1.0)]
        ax.plot(view["Time [s]"], view.speed_mps, color="black", linewidth=1)
        ax.axvspan(row.start_s, row.end_s, color="#bbbbbb", alpha=.15)
        for threshold in THRESHOLDS:
            boundaries = [r for r in retained[threshold] if r["block_id"] == row.block_id and row.start_s - 1 <= r["time_s"] <= row.end_s + 1]
            for boundary in boundaries:
                alpha = .9 if threshold == 0 or threshold == selected else .32
                ax.axvline(boundary["time_s"], color=colors[threshold], alpha=alpha,
                           linewidth=1.2 if threshold == selected else .8,
                           linestyle="--" if threshold == 0 else "-")
        ax.set_title(f"{row.episode_id} | {row.team} {row.player} P{row.period}\n{row.reason}", fontsize=8)
        ax.set_xlabel("time (s)"); ax.set_ylabel("speed (m/s)")
    for ax in axes[len(rows):]:
        ax.axis("off")
    title = "Deterministic boundary audit — baseline and frozen prominence ladder"
    if selected is not None:
        title += f" (selected {selected:.2f} m/s)"
    fig.suptitle(title)
    legend = [Line2D([0], [0], color=colors[t], linestyle="--" if t == 0 else "-",
                     label=f"{t:.2f} m/s") for t in THRESHOLDS]
    axes[0].legend(handles=legend, loc="lower right", fontsize=7, title="boundary branch", title_fontsize=7)
    fig.savefig(FIG / "deterministic_boundary_comparison.png", dpi=170)
    plt.close(fig)


def main() -> None:
    rules = json.loads(CONFIG.read_text())
    if tuple(rules["candidate_prominence_mps"]) != THRESHOLDS:
        raise RuntimeError("Candidate ladder differs from frozen protocol")
    prominence_self_test()

    home_path = DATA / "Sample_Game_1_RawTrackingData_Home_Team.csv"
    away_path = DATA / "Sample_Game_1_RawTrackingData_Away_Team.csv"
    event_path = DATA / "Sample_Game_1_RawEventsData.csv"
    home, home_ids = load_tracking(home_path, "Home")
    away, away_ids = load_tracking(away_path, "Away")
    events = pd.read_csv(event_path)
    exclusions, boundaries = global_exclusions(events)
    tracking = {"Home": home, "Away": away}
    players = {"Home": [p for p in home_ids if p != GK["Home"]],
               "Away": [p for p in away_ids if p != GK["Away"]]}

    blocks, baseline_rows, method_b_rows, baseline_boundaries = {}, [], [], []
    for team in ("Home", "Away"):
        for player in sorted(players[team], key=int):
            player_data = player_blocks(tracking[team], team, player, exclusions, boundaries)
            for number, block in enumerate(player_data):
                block_id = f"{team}_{player}_{int(block.Period.iloc[0])}_{number}"
                blocks[block_id] = block
                episodes, valleys = segment_method_a(block, team, player, block_id)
                baseline_rows.extend(episodes)
                method_b_rows.extend(segment_method_b(block, team, player, block_id))
                for index in valleys:
                    baseline_boundaries.append({"block_id": block_id, "index": int(index), "team": team,
                                                "player": player, "period": int(block.Period.iloc[index]),
                                                "frame": int(block.Frame.iloc[index]),
                                                "time_s": float(block["Time [s]"].iloc[index])})
    method_b = pd.DataFrame(method_b_rows)
    baseline = add_diagnostics(add_ids(baseline_rows, "P000_"), method_b)
    baseline_check = baseline_reproduction(baseline)
    if not baseline_check["passed"]:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "baseline_reproduction_failure.json").write_text(json.dumps(baseline_check, indent=2) + "\n")
        raise RuntimeError("Historical baseline reproduction failed; nonzero branches not constructed")

    tables = {0.0: baseline}
    retained = {0.0: baseline_boundaries}
    all_candidate_rows = []
    for threshold in THRESHOLDS[1:]:
        rows, threshold_boundaries = [], []
        for block_id, block in blocks.items():
            team, player = block_id.split("_")[:2]
            episodes, valleys, candidates = segment_with_prominence(block, team, player, block_id, threshold)
            rows.extend(episodes); all_candidate_rows.extend(candidates)
            for index in valleys:
                threshold_boundaries.append({"block_id": block_id, "index": int(index), "team": team,
                                             "player": player, "period": int(block.Period.iloc[index]),
                                             "frame": int(block.Frame.iloc[index]),
                                             "time_s": float(block["Time [s]"].iloc[index])})
        prefix = f"P{int(round(threshold * 100)):03d}_"
        tables[threshold] = add_diagnostics(add_ids(rows, prefix), method_b)
        retained[threshold] = threshold_boundaries

    summary_rows = []
    base_metrics = metrics(tables[0.0])
    for threshold, table in tables.items():
        row = {"threshold_mps": threshold, **metrics(table, None if threshold == 0 else base_metrics)}
        row["implementation_qc_pass"] = True
        row["eligible"] = bool(threshold > 0 and row["fragmentation_pass"] and
                               row["merging_direction_pass"] and row["coverage_pass"])
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    eligible, selected, classification = classify(summary, True)

    sensitivity_tables = {}
    for threshold, table in tables.items():
        raw_start = table.start_frame - 4
        raw_end = table.end_frame + 3
        affected = (table.team.eq("Home") & table.player.astype(str).eq("10") & table.period.eq(1) &
                    (raw_start <= 2945) & (raw_end >= 2911))
        sensitivity_tables[threshold] = table.loc[~affected].copy()
    sensitivity_rows = []
    sensitivity_base = metrics(sensitivity_tables[0.0])
    for threshold, table in sensitivity_tables.items():
        row = {"threshold_mps": threshold, "excluded_episodes": int(len(tables[threshold]) - len(table)),
               **metrics(table, None if threshold == 0 else sensitivity_base)}
        row["implementation_qc_pass"] = True
        row["eligible"] = bool(threshold > 0 and row["fragmentation_pass"] and
                               row["merging_direction_pass"] and row["coverage_pass"])
        sensitivity_rows.append(row)
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity_eligible, sensitivity_selected, sensitivity_classification = classify(sensitivity, True)

    candidate_rows = pd.DataFrame(all_candidate_rows)
    boundary_summary, removed_summary = boundary_tables(retained, candidate_rows)
    distributions = distribution_summary(tables)
    groups = group_counts(tables)
    sample = deterministic_sample(baseline)

    # Objective visual/reproducibility checks; appearance has no classification role.
    retained_candidate_keys = set(zip(candidate_rows.loc[candidate_rows.retained_after_consolidation, "threshold_mps"],
                                      candidate_rows.loc[candidate_rows.retained_after_consolidation, "block_id"],
                                      candidate_rows.loc[candidate_rows.retained_after_consolidation, "index"]))
    reported_keys = {(threshold, row["block_id"], row["index"])
                     for threshold in THRESHOLDS[1:] for row in retained[threshold]}
    boundary_identity_match = retained_candidate_keys == reported_keys
    qualifying_match = bool(candidate_rows.loc[candidate_rows.retained_after_consolidation]
                            .eval("prominence_mps >= threshold_mps").all())
    visual_qc_pass = bool(boundary_identity_match and qualifying_match and sample.episode_id.notna().all())
    if not visual_qc_pass:
        raise RuntimeError("Objective visual/machine-readable boundary QC failed")

    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "candidate_summary.csv", index=False)
    sensitivity.to_csv(OUT / "home10_tracking_sensitivity.csv", index=False)
    distributions.to_csv(OUT / "distribution_summary.csv", index=False)
    boundary_summary.to_csv(OUT / "boundary_summary.csv", index=False)
    removed_summary.to_csv(OUT / "removed_boundary_prominence_summary.csv", index=False)
    groups.to_csv(OUT / "group_concentration.csv", index=False)
    sample.to_csv(OUT / "deterministic_visual_sample.csv", index=False)
    if selected is not None:
        tables[selected].to_csv(OUT / "selected_candidate_episodes.csv", index=False)
    else:
        pd.DataFrame(columns=baseline.columns).to_csv(OUT / "selected_candidate_episodes.csv", index=False)
    plot_visual_sample(sample, blocks, retained, selected)

    group_nonzero = groups[groups.threshold_mps > 0]
    largest_group_shifts = (group_nonzero.loc[group_nonzero.groupby(["threshold_mps", "grouping"])
                            .share_change_percentage_points.apply(lambda s: s.abs().idxmax())]
                            .sort_values(["threshold_mps", "grouping"]).to_dict("records"))
    result = {
        "classification": classification,
        "eligible_candidates_mps": eligible,
        "selected_prominence_mps": selected,
        "baseline_reproduction": baseline_check,
        "candidate_summary": summary.to_dict("records"),
        "home10_sensitivity": {
            "classification": sensitivity_classification,
            "eligible_candidates_mps": sensitivity_eligible,
            "selected_prominence_mps": sensitivity_selected,
            "changes_primary_classification": sensitivity_classification != classification,
            "changes_selected_candidate": sensitivity_selected != selected
        },
        "largest_group_share_shifts": largest_group_shifts,
        "visual_role": "descriptive; objective implementation/QC only",
        "visual_qc_pass": visual_qc_pass,
        "supported_claim_if_A": "An outcome-blind prominence requirement improves the tested finite representation of an attacker's own movement under the predeclared Game 1 development criteria.",
        "game2_executed": False, "game3_accessed": False, "defensive_outcomes_used": False
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    qc = {
        "passed": True, "baseline_reproduction": baseline_check,
        "candidate_ladder_mps": list(THRESHOLDS), "prominence_self_test": True,
        "historical_smoothing_unchanged": True, "historical_duration_unchanged": True,
        "historical_valley_spacing_unchanged": True, "direction_splitting_added": False,
        "objective_visual_qc_pass": visual_qc_pass, "deterministic_sample_rows": int(len(sample)),
        "game2_executed": False, "game3_accessed": False, "defensive_outcomes_used": False,
        "config_sha256": sha256(CONFIG), "source_sha256": sha256(Path(__file__)),
        "historical_rules_sha256": sha256(ROOT / "config" / "post5b_movement_segmentation_audit_rules.json"),
        "historical_episode_table_sha256": sha256(HISTORICAL / "method_a_episodes.csv"),
        "input_sha256": {p.name: sha256(p) for p in (home_path, away_path, event_path)}
    }
    (OUT / "qc_results.json").write_text(json.dumps(qc, indent=2) + "\n")
    print(json.dumps({"classification": classification, "selected": selected,
                      "eligible": eligible, "summary": summary.to_dict("records"),
                      "sensitivity": result["home10_sensitivity"]}, indent=2))


if __name__ == "__main__":
    main()
