"""Execute the frozen v2 response-free defender-replay display-scale audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from defensive_reorganization_replay_display_scale_v1 import (
    ROOT,
    SCORER_PATH,
    SCORER_SHA256,
    _demo_check,
    _summary_rows,
    candidate_audit,
    distribution_summary,
    perceptual_spread,
    score_team_file,
    sha256,
    verify_frozen_inputs,
    write_json,
)


CONFIG_PATH = ROOT / "config" / "defensive_reorganization_replay_display_scale_v2.json"
PROTOCOL_PATH = ROOT / "docs" / "protocols" / "defensive_reorganization_replay_display_scale_v2.md"
V1_CONFIG_PATH = ROOT / "config" / "defensive_reorganization_replay_display_scale_v1.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "defensive_reorganization_replay_display_scale_v2"
DEFAULT_REPORT = ROOT / "docs" / "results" / "defensive_reorganization_replay_display_scale_v2.md"
DEFAULT_SNAPSHOT = Path("/tmp/defensive_reorganization_replay_display_scale_v2_snapshots.png")

CANDIDATE_CEILINGS = (6.25, 6.5, 7.0)
STATUS_BY_CEILING = {
    6.25: "A_FREEZE_6_25_M",
    6.5: "B_FREEZE_6_50_M",
    7.0: "C_FREEZE_7_00_M",
}
EXPECTED_PLAYER_COUNT = 5_713_060
EXPECTED_TEAM_COUNT = 571_306
EXPECTED_RUN_COUNT = 18


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if tuple(float(value) for value in config["candidate_ceilings_m"]) != CANDIDATE_CEILINGS:
        raise RuntimeError("candidate ceilings differ from the frozen v2 set")
    if config["reference_population"]["events_read"] or config["reference_population"]["ball_read"]:
        raise RuntimeError("v2 forbids event and ball access")
    return config


def verify_v1_authority(config: Mapping[str, object]) -> None:
    for relative, expected in config["inherits_v1"]["artifacts_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"closed v1 authority hash mismatch: {relative}")
    v1 = json.loads(V1_CONFIG_PATH.read_text(encoding="utf-8"))
    current = config["selection_rule"]
    inherited = v1["selection_rule"]
    if current != inherited:
        raise RuntimeError("v2 selection thresholds or ordering differ from v1")
    for key in ("games", "teams", "periods", "source_fps", "goalkeeper_ids"):
        if config["reference_population"][key] != v1["reference_population"][key]:
            raise RuntimeError(f"v2 reference population differs from v1: {key}")
    for key in ("source_fps", "smoothing_method", "smoothing_frames", "window_seconds", "units", "raw_scores_only"):
        if config["scorer"][key] != v1["scorer"][key]:
            raise RuntimeError(f"v2 scorer specification differs from v1: {key}")
    if config["quantile_method"] != v1["quantile_method"]:
        raise RuntimeError("v2 quantile method differs from v1")
    if config["saturation_operator"] != v1["saturation_operator"]:
        raise RuntimeError("v2 saturation operator differs from v1")
    if config["perceptual_bins"] != v1["perceptual_bins"]:
        raise RuntimeError("v2 perceptual bins differ from v1")


def select_ceiling(rows: Iterable[Mapping[str, float | int]]) -> tuple[str, float | None]:
    ordered = sorted(rows, key=lambda row: float(row["ceiling_m"]))
    if tuple(float(row["ceiling_m"]) for row in ordered) != CANDIDATE_CEILINGS:
        raise ValueError("selection requires exactly the frozen v2 candidates")
    for row in ordered:
        if float(row["player_saturation_fraction"]) <= 0.05 and float(
            row["team_mean_saturation_fraction"]
        ) <= 0.01:
            ceiling = float(row["ceiling_m"])
            return STATUS_BY_CEILING[ceiling], ceiling
    return "D_UNRESOLVED", None


def _render_qa_snapshots(demo: Mapping[str, object], ceiling: float, path: Path) -> dict[str, object]:
    """Render anonymous fixed-time color swatches from aggregate snapshot summaries.

    The closed demo check intentionally does not serialize row-level scores. This
    figure therefore shows the fixed-time saturation/distinct-color diagnostics,
    not identities or coordinates.
    """
    summaries = demo["predeclared_snapshot_summary"]
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.1), sharey=True)
    ordered_labels = ("t_-10_s", "t_+0_s", "t_+10_s")
    for ax, label in zip(axes, ordered_labels, strict=True):
        summary = summaries[label]
        saturated = int(summary["saturated_defender_count"])
        distinct = int(summary["distinct_display_values"])
        ax.barh([0], [min(float(summary["team_mean_m"]), ceiling)], color="#6f7d83", height=.35)
        ax.set_xlim(0, ceiling)
        ax.set_yticks([])
        ax.set_title(label.replace("_", " "))
        ax.text(.5, -.27, f"team mean {summary['team_mean_m']:.2f} m\n{saturated}/10 saturated · {distinct} display values", transform=ax.transAxes, ha="center", va="top", fontsize=8)
        ax.grid(axis="x", alpha=.2)
    fig.suptitle("Bounded fixed-time display-scale QA (no player identities)")
    fig.supxlabel("Fixed selected scale (m)", y=.04)
    fig.subplots_adjust(left=.06, right=.99, bottom=.31, top=.77, wspace=.08)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {"rendered": True, "path": str(path), "times": list(ordered_labels)}


def _report(
    status: str,
    selected: float | None,
    distribution: Mapping[str, object],
    rows: list[dict[str, object]],
    demo: Mapping[str, object],
) -> str:
    lines = [
        "# Defender-relative replay display-scale audit v2",
        "",
        "**Boundary:** response-free visualization QA inheriting the complete closed v1 population and rules.",
        "",
        f"**Decision:** `{status}`",
        f"**Selected ceiling:** {selected if selected is not None else 'none'}",
        "",
        "The unchanged scorer reproduced 5,713,060 supported player-frames and 571,306 supported team-frames across the same 18 stable-lineup Metrica runs.",
        "",
        "## Candidate ceilings",
        "",
        "| Ceiling | Player saturation | Team-mean saturation | Qualifies |",
        "|---:|---:|---:|:---:|",
    ]
    for row in rows:
        qualifies = row["player_saturation_fraction"] <= 0.05 and row["team_mean_saturation_fraction"] <= 0.01
        lines.append(f"| {row['ceiling_m']:.2f} m | {100*row['player_saturation_fraction']:.3f}% | {100*row['team_mean_saturation_fraction']:.3f}% | {'yes' if qualifies else 'no'} |")
    lines.extend(
        [
            "",
            "## Reference distribution identity",
            "",
            f"Player median / p95 / p99 / maximum (m): {distribution['player']['median']:.6f} / {distribution['player']['p95']:.6f} / {distribution['player']['p99']:.6f} / {distribution['player']['maximum']:.6f}.",
            f"Team median / p95 / p99 / maximum (m): {distribution['team_mean']['median']:.6f} / {distribution['team_mean']['p95']:.6f} / {distribution['team_mean']['p99']:.6f} / {distribution['team_mean']['maximum']:.6f}.",
            "",
            "## Fixed-demo secondary check",
            "",
            (
                f"At {selected:.2f} m, {demo['displayed']['player_saturation_count']} of 2,510 displayed defender-frame values saturated ({100*demo['displayed']['player_saturation_fraction']:.3f}%). Team means exceeded the ceiling in {demo['displayed']['team_mean_saturation_count']} displayed frames."
                if demo.get("performed")
                else "Not performed because no candidate met the frozen rule."
            ),
            "",
            "These are display-QA summaries, not football results. No score definition, scientific result, or renderer default changed.",
            "",
        ]
    )
    return "\n".join(lines)


def execute(
    output_dir: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
    snapshot_path: Path = DEFAULT_SNAPSHOT,
) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"authoritative output already exists: {output_dir}")
    config = load_config()
    verify_v1_authority(config)
    v1_config = json.loads(V1_CONFIG_PATH.read_text(encoding="utf-8"))
    source_hashes = verify_frozen_inputs(v1_config)
    output_dir.mkdir(parents=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    per_game: dict[int, dict[str, object]] = {}
    source_run_counts: dict[str, int] = {}
    for game in (1, 2):
        matrices: list[np.ndarray] = []
        teams: list[np.ndarray] = []
        for team in ("Home", "Away"):
            path = ROOT / f"data/metrica_sample_game_{game}/Sample_Game_{game}_RawTrackingData_{team}_Team.csv"
            matrix, team_means, runs = score_team_file(path, game=game, team=team)
            matrices.append(matrix)
            teams.append(team_means)
            source_run_counts[f"game_{game}_{team.lower()}"] = runs
        per_game[game] = {"players": np.vstack(matrices), "teams": np.concatenate(teams)}

    player_matrix = np.vstack([per_game[game]["players"] for game in (1, 2)])
    team_means = np.concatenate([per_game[game]["teams"] for game in (1, 2)])
    player_values = player_matrix.reshape(-1)
    run_count = sum(source_run_counts.values())
    if player_values.size != EXPECTED_PLAYER_COUNT or team_means.size != EXPECTED_TEAM_COUNT or run_count != EXPECTED_RUN_COUNT:
        raise RuntimeError("v2 reference population does not reproduce closed v1 authority")

    distribution = {
        "player": distribution_summary(player_values, (0.5, 0.75, 0.9, 0.95, 0.975, 0.99)),
        "team_mean": distribution_summary(team_means, (0.5, 0.9, 0.95, 0.99)),
    }
    rows = [candidate_audit(player_matrix, team_means, ceiling) for ceiling in CANDIDATE_CEILINGS]
    spreads = [perceptual_spread(player_values, ceiling) for ceiling in CANDIDATE_CEILINGS]
    status, selected = select_ceiling(rows)
    demo = _demo_check(selected)
    snapshot = _render_qa_snapshots(demo, selected, snapshot_path) if selected is not None else {"rendered": False, "reason": "no candidate qualified"}

    write_json(output_dir / "distribution_summary.json", distribution)
    pd.DataFrame(_summary_rows(per_game)).to_csv(output_dir / "per_game_summary.csv", index=False, lineterminator="\n")
    pd.DataFrame(rows).to_csv(output_dir / "candidate_scale_audit.csv", index=False, lineterminator="\n")
    pd.DataFrame(spreads).to_csv(output_dir / "perceptual_spread.csv", index=False, lineterminator="\n")
    write_json(output_dir / "demo_secondary_check.json", demo)
    write_json(
        output_dir / "source_identities.json",
        {
            "tracking_sha256": source_hashes,
            "scorer_path": str(SCORER_PATH.relative_to(ROOT)),
            "scorer_sha256": sha256(SCORER_PATH),
            "v2_protocol_sha256": sha256(PROTOCOL_PATH),
            "v2_config_sha256": sha256(CONFIG_PATH),
            "v1_authority_sha256": config["inherits_v1"]["artifacts_sha256"],
        },
    )
    manifest = {
        "audit_id": config["audit_id"],
        "classification": status,
        "selected_ceiling_m": selected,
        "candidate_ceilings_m": list(CANDIDATE_CEILINGS),
        "supported_player_frame_count": int(player_values.size),
        "supported_team_frame_count": int(team_means.size),
        "source_run_counts": source_run_counts,
        "v1_population_reproduced": True,
        "events_read": False,
        "ball_read": False,
        "scientific_outcomes_used": False,
        "game_3_accessed": False,
        "row_level_output_written": False,
        "qa_snapshot": {"rendered": snapshot["rendered"], "committed": False},
    }
    write_json(output_dir / "manifest.json", manifest)
    hard_qc = {
        "passed": True,
        "candidate_set_exact": tuple(row["ceiling_m"] for row in rows) == CANDIDATE_CEILINGS,
        "v1_player_count_exact": player_values.size == EXPECTED_PLAYER_COUNT,
        "v1_team_count_exact": team_means.size == EXPECTED_TEAM_COUNT,
        "v1_run_count_exact": run_count == EXPECTED_RUN_COUNT,
        "team_means_match_players": bool(np.allclose(player_matrix.mean(axis=1), team_means, atol=1e-12, rtol=0)),
        "scorer_hash_unchanged": sha256(SCORER_PATH) == SCORER_SHA256,
        "events_read": False,
        "ball_read": False,
        "protected_outcomes_read": False,
        "game_3_accessed": False,
    }
    positive = [key for key in hard_qc if key not in {"passed", "events_read", "ball_read", "protected_outcomes_read", "game_3_accessed"}]
    negative = ["events_read", "ball_read", "protected_outcomes_read", "game_3_accessed"]
    hard_qc["passed"] = all(hard_qc[key] for key in positive) and not any(hard_qc[key] for key in negative)
    write_json(output_dir / "hard_qc.json", hard_qc)
    report_path.write_text(_report(status, selected, distribution, rows, demo), encoding="utf-8")

    governed = [
        output_dir / "candidate_scale_audit.csv",
        output_dir / "demo_secondary_check.json",
        output_dir / "distribution_summary.json",
        output_dir / "hard_qc.json",
        output_dir / "manifest.json",
        output_dir / "per_game_summary.csv",
        output_dir / "perceptual_spread.csv",
        output_dir / "source_identities.json",
        report_path,
    ]
    write_json(output_dir / "final_hashes.json", {str(path.relative_to(ROOT)): sha256(path) for path in governed})
    return {
        "classification": status,
        "selected_ceiling_m": selected,
        "qa_snapshot": snapshot,
        "output_dir": str(output_dir),
        "report": str(report_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-audit", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--qa-snapshot-path", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    if not args.execute_audit:
        raise SystemExit("response-free v2 audit requires explicit --execute-audit")
    print(json.dumps(execute(args.output_dir, args.report_path, args.qa_snapshot_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
