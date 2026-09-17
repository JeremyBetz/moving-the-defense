"""Execute the frozen response-free defender-replay display-scale audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from defensive_reorganization_replay import (
    SUPPORTED,
    DefenderRelativePathSpec,
    score_trailing_defender_relative_path,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "defensive_reorganization_replay_display_scale_v1.json"
PROTOCOL_PATH = ROOT / "docs" / "protocols" / "defensive_reorganization_replay_display_scale_v1.md"
SCORER_PATH = ROOT / "src" / "defensive_reorganization_replay.py"
DEFAULT_OUTPUT = ROOT / "outputs" / "defensive_reorganization_replay_display_scale_v1"
DEFAULT_REPORT = ROOT / "docs" / "results" / "defensive_reorganization_replay_display_scale_v1.md"

CANDIDATE_CEILINGS = (4.0, 5.0, 6.0)
GOALKEEPERS = {"Home": "11", "Away": "25"}
SOURCE_FPS = 25.0
EXPECTED_STEP_S = 1.0 / SOURCE_FPS
SCORER_SHA256 = "6b5f33de5a034ae4000270e847ebcefe0164b1df1d21d4f3a7ed8adf9bd24a8a"
STATUS_BY_CEILING = {
    4.0: "A_FREEZE_4_M",
    5.0: "B_FREEZE_5_M",
    6.0: "C_FREEZE_6_M",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if tuple(float(value) for value in config["candidate_ceilings_m"]) != CANDIDATE_CEILINGS:
        raise RuntimeError("candidate ceilings differ from the frozen set")
    if config["reference_population"]["events_read"] or config["reference_population"]["ball_read"]:
        raise RuntimeError("frozen audit forbids event and ball access")
    return config


def verify_frozen_inputs(config: Mapping[str, object]) -> dict[str, str]:
    if sha256(SCORER_PATH) != SCORER_SHA256:
        raise RuntimeError("committed scorer hash mismatch")
    actual: dict[str, str] = {}
    for relative, expected in config["inputs_sha256"].items():
        path = ROOT / relative
        observed = sha256(path)
        if observed != expected:
            raise RuntimeError(f"tracking source hash mismatch: {relative}")
        actual[relative] = observed
    return actual


def _player_columns(path: Path, team: str) -> tuple[list[str], dict[str, tuple[str, str]]]:
    header = pd.read_csv(path, skiprows=2, nrows=0)
    columns = list(header.columns)
    mapping: dict[str, tuple[str, str]] = {}
    for index, column in enumerate(columns[:-1]):
        label = str(column).strip()
        if not label.startswith("Player"):
            continue
        number = label[len("Player") :].strip()
        if not number or number == GOALKEEPERS[team]:
            continue
        mapping[number] = (column, columns[index + 1])
    if len(mapping) < 10:
        raise RuntimeError(f"{path} contains fewer than ten non-goalkeeper identities")
    usecols = ["Period", "Frame", "Time [s]"]
    for x_col, y_col in mapping.values():
        usecols.extend([x_col, y_col])
    return usecols, mapping


def read_tracking_team(path: Path, team: str) -> tuple[pd.DataFrame, dict[str, tuple[str, str]]]:
    """Read structural clocks and player coordinates only; never ball or events."""
    usecols, mapping = _player_columns(path, team)
    table = pd.read_csv(path, skiprows=2, usecols=usecols)
    if set(table["Period"].dropna().astype(int).unique()) != {1, 2}:
        raise RuntimeError(f"{path} does not contain exactly periods 1 and 2")
    clocks = table[["Period", "Frame", "Time [s]"]].to_numpy(float)
    if not np.isfinite(clocks).all():
        raise RuntimeError(f"{path} contains nonfinite period/frame/timestamp values")
    return table, mapping


def active_identity_tuple(
    row: pd.Series,
    mapping: Mapping[str, tuple[str, str]],
) -> tuple[str, ...] | None:
    active = tuple(
        sorted(
            number
            for number, (x_col, y_col) in mapping.items()
            if np.isfinite(float(row[x_col])) and np.isfinite(float(row[y_col]))
        )
    )
    return active if len(active) == 10 else None


def split_complete_runs(
    table: pd.DataFrame,
    mapping: Mapping[str, tuple[str, str]],
) -> list[tuple[int, int, int, tuple[str, ...]]]:
    """Return inclusive row-index runs with one stable complete ten-player set."""
    runs: list[tuple[int, int, int, tuple[str, ...]]] = []
    for period, period_rows in table.groupby("Period", sort=True):
        q = period_rows.sort_values(["Time [s]", "Frame"], kind="mergesort")
        current_start: int | None = None
        current_ids: tuple[str, ...] | None = None
        previous_frame: int | None = None
        previous_time: float | None = None
        previous_index: int | None = None
        for index, row in q.iterrows():
            identities = active_identity_tuple(row, mapping)
            frame = int(row["Frame"])
            time_s = float(row["Time [s]"])
            contiguous = (
                previous_frame is not None
                and frame == previous_frame + 1
                and np.isclose(time_s - float(previous_time), EXPECTED_STEP_S, atol=1e-7, rtol=0)
            )
            continues = identities is not None and identities == current_ids and contiguous
            if not continues:
                if current_start is not None and previous_index is not None and current_ids is not None:
                    runs.append((int(period), current_start, previous_index, current_ids))
                current_start = int(index) if identities is not None else None
                current_ids = identities
            previous_frame, previous_time, previous_index = frame, time_s, int(index)
        if current_start is not None and previous_index is not None and current_ids is not None:
            runs.append((int(period), current_start, previous_index, current_ids))
    return runs


def normalized_run(
    table: pd.DataFrame,
    mapping: Mapping[str, tuple[str, str]],
    *,
    game: int,
    team: str,
    run_number: int,
    period: int,
    start: int,
    end: int,
    identities: Iterable[str],
) -> pd.DataFrame:
    q = table.loc[start:end].sort_values(["Time [s]", "Frame"], kind="mergesort")
    records: list[dict[str, object]] = []
    match_id = f"metrica:sample-game-{game}:{team}:period-{period}:run-{run_number}"
    for number in identities:
        x_col, y_col = mapping[number]
        for frame, time_s, x, y in q[["Frame", "Time [s]", x_col, y_col]].itertuples(index=False):
            records.append(
                {
                    "match_id": match_id,
                    "period": period,
                    "frame_id_provider": str(int(frame)),
                    "time_match_s": float(time_s),
                    "entity_type": "player",
                    "team_key": f"metrica:{team}",
                    "player_key": f"metrica:{team}:{number}",
                    "x_m": float(x) * 105.0 - 52.5,
                    "y_m": float(y) * 68.0 - 34.0,
                    "coordinate_valid": True,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
    return pd.DataFrame.from_records(records)


def score_team_file(path: Path, *, game: int, team: str) -> tuple[np.ndarray, np.ndarray, int]:
    table, mapping = read_tracking_team(path, team)
    matrices: list[np.ndarray] = []
    team_means: list[np.ndarray] = []
    scored_runs = 0
    for run_number, (period, start, end, identities) in enumerate(
        split_complete_runs(table, mapping), start=1
    ):
        # 50 trailing increments plus six smoother-edge frames are needed for support.
        if end - start + 1 < 57:
            continue
        tracking = normalized_run(
            table,
            mapping,
            game=game,
            team=team,
            run_number=run_number,
            period=period,
            start=start,
            end=end,
            identities=identities,
        )
        scores = score_trailing_defender_relative_path(
            tracking,
            DefenderRelativePathSpec(
                defending_team_key=f"metrica:{team}",
                source_fps=SOURCE_FPS,
                window_seconds=2.0,
                smoothing_frames=7,
            ),
        )
        players = scores.player_scores.loc[scores.player_scores["support_status"].eq(SUPPORTED)]
        teams = scores.team_scores.loc[scores.team_scores["support_status"].eq(SUPPORTED)]
        if players.empty:
            continue
        grouped = players.groupby("frame_id_provider", sort=False)["trailing_relative_path_m"]
        if not grouped.size().eq(10).all() or len(grouped) != len(teams):
            raise RuntimeError("scorer did not return ten supported players per team frame")
        matrix = np.vstack([group.to_numpy(float) for _, group in grouped])
        means = teams["mean_trailing_relative_path_m"].to_numpy(float)
        if not np.allclose(matrix.mean(axis=1), means, atol=1e-12, rtol=0):
            raise RuntimeError("team mean differs from player-score arithmetic mean")
        matrices.append(matrix)
        team_means.append(means)
        scored_runs += 1
    if not matrices:
        raise RuntimeError(f"no supported score runs for Game {game} {team}")
    return np.vstack(matrices), np.concatenate(team_means), scored_runs


def distribution_summary(values: np.ndarray, quantiles: Iterable[float]) -> dict[str, float | int]:
    raw = np.asarray(values, dtype=float)
    if raw.size == 0 or not np.isfinite(raw).all():
        raise ValueError("distribution values must be nonempty and finite")
    result: dict[str, float | int] = {
        "count": int(raw.size),
        "mean": float(raw.mean()),
        "maximum": float(raw.max()),
    }
    for quantile in quantiles:
        label = {0.5: "median", 0.75: "p75", 0.9: "p90", 0.95: "p95", 0.975: "p97_5", 0.99: "p99"}[float(quantile)]
        result[label] = float(np.quantile(raw, quantile, method="linear"))
    return result


def candidate_audit(player_matrix: np.ndarray, team_means: np.ndarray, ceiling: float) -> dict[str, float | int]:
    matrix = np.asarray(player_matrix, dtype=float)
    teams = np.asarray(team_means, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != 10 or len(matrix) != len(teams):
        raise ValueError("candidate audit requires [team frames, ten defenders] and matching means")
    if not np.isfinite(matrix).all() or not np.isfinite(teams).all():
        raise ValueError("candidate audit requires finite raw scores")
    saturated = matrix > ceiling
    per_frame = saturated.sum(axis=1)
    return {
        "ceiling_m": float(ceiling),
        "player_saturation_count": int(saturated.sum()),
        "player_saturation_fraction": float(saturated.mean()),
        "frames_at_least_1_saturated": int(np.count_nonzero(per_frame >= 1)),
        "frames_at_least_2_saturated": int(np.count_nonzero(per_frame >= 2)),
        "frames_at_least_5_saturated": int(np.count_nonzero(per_frame >= 5)),
        "mean_saturated_defenders_per_frame": float(per_frame.mean()),
        "team_mean_saturation_count": int(np.count_nonzero(teams > ceiling)),
        "team_mean_saturation_fraction": float(np.mean(teams > ceiling)),
    }


def perceptual_spread(values: np.ndarray, ceiling: float) -> dict[str, float]:
    raw = np.asarray(values, dtype=float)
    if raw.size == 0 or not np.isfinite(raw).all():
        raise ValueError("perceptual spread requires finite raw values")
    q = {name: float(np.quantile(raw, probability, method="linear")) for name, probability in (
        ("median", 0.5), ("p75", 0.75), ("p90", 0.9), ("p95", 0.95)
    )}
    lower, upper = 0.25 * ceiling, 0.75 * ceiling
    return {
        "ceiling_m": float(ceiling),
        **{f"{name}_normalized": float(np.clip(value / ceiling, 0.0, 1.0)) for name, value in q.items()},
        "below_25_fraction": float(np.mean(raw < lower)),
        "between_25_75_fraction": float(np.mean((raw >= lower) & (raw < upper))),
        "above_75_unsaturated_fraction": float(np.mean((raw >= upper) & (raw <= ceiling))),
        "saturated_fraction": float(np.mean(raw > ceiling)),
    }


def select_ceiling(rows: Iterable[Mapping[str, float | int]]) -> tuple[str, float | None]:
    ordered = sorted(rows, key=lambda row: float(row["ceiling_m"]))
    if tuple(float(row["ceiling_m"]) for row in ordered) != CANDIDATE_CEILINGS:
        raise ValueError("selection requires exactly the frozen candidates")
    for row in ordered:
        if float(row["player_saturation_fraction"]) <= 0.05 and float(
            row["team_mean_saturation_fraction"]
        ) <= 0.01:
            ceiling = float(row["ceiling_m"])
            return STATUS_BY_CEILING[ceiling], ceiling
    return "D_UNRESOLVED", None


def _summary_rows(per_game: Mapping[int, Mapping[str, np.ndarray]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for game in sorted(per_game):
        player = per_game[game]["players"].reshape(-1)
        team = per_game[game]["teams"]
        for level, values, quantiles in (
            ("player", player, (0.5, 0.75, 0.9, 0.95, 0.975, 0.99)),
            ("team_mean", team, (0.5, 0.9, 0.95, 0.99)),
        ):
            rows.append({"game": game, "level": level, **distribution_summary(values, quantiles)})
    return rows


def _demo_check(ceiling: float | None) -> dict[str, object]:
    if ceiling is None:
        return {"performed": False, "reason": "no frozen candidate qualified"}
    path = ROOT / "data/metrica_sample_game_2/Sample_Game_2_RawTrackingData_Away_Team.csv"
    table, mapping = read_tracking_team(path, "Away")
    display_start, anchor, display_end = 2326.04, 2336.04, 2346.04
    raw_start, raw_end = 2323.92, 2346.16
    bounded = table.loc[
        table["Period"].eq(1) & table["Time [s]"].between(raw_start, raw_end)
    ].copy()
    required = tuple(sorted(("15", "16", "17", "18", "19", "20", "21", "22", "23", "24")))
    tracking = normalized_run(
        bounded.reset_index(drop=True),
        mapping,
        game=2,
        team="Away",
        run_number=1,
        period=1,
        start=0,
        end=len(bounded) - 1,
        identities=required,
    )
    scores = score_trailing_defender_relative_path(
        tracking,
        DefenderRelativePathSpec("metrica:Away", 25.0, 2.0, 7),
    )
    players = scores.player_scores.loc[
        scores.player_scores["support_status"].eq(SUPPORTED)
        & scores.player_scores["time_match_s"].between(display_start, display_end)
    ]
    teams = scores.team_scores.loc[
        scores.team_scores["support_status"].eq(SUPPORTED)
        & scores.team_scores["time_match_s"].between(display_start, display_end)
    ]
    grouped = players.groupby("frame_id_provider", sort=False)["trailing_relative_path_m"]
    matrix = np.vstack([group.to_numpy(float) for _, group in grouped])
    if len(matrix) != 501 or len(teams) != 501:
        raise RuntimeError("fixed demo secondary check does not contain 501 native frames")
    native = candidate_audit(matrix, teams["mean_trailing_relative_path_m"].to_numpy(float), ceiling)
    displayed = matrix[::2]
    displayed_teams = teams["mean_trailing_relative_path_m"].to_numpy(float)[::2]
    if len(displayed) != 251:
        raise RuntimeError("fixed demo secondary check does not contain 251 displayed frames")
    display = candidate_audit(displayed, displayed_teams, ceiling)
    snapshots = {}
    times = teams["time_match_s"].to_numpy(float)
    for offset in (-10.0, 0.0, 10.0):
        index = np.flatnonzero(np.isclose(times, anchor + offset, atol=1e-7, rtol=0))
        if len(index) != 1:
            raise RuntimeError("predeclared demo snapshot is unavailable")
        values = matrix[index[0]]
        snapshots[f"t_{offset:+.0f}_s"] = {
            "team_mean_m": float(values.mean()),
            "saturated_defender_count": int(np.count_nonzero(values > ceiling)),
            "distinct_display_values": int(np.unique(np.minimum(values, ceiling)).size),
        }
    return {
        "performed": True,
        "selected_ceiling_m": ceiling,
        "native_frame_count": 501,
        "displayed_frame_count": 251,
        "native": native,
        "displayed": display,
        "predeclared_snapshot_summary": snapshots,
        "high_value_ordering_improved": display["player_saturation_fraction"] < 769 / 2510,
    }


def _report(
    selected_status: str,
    selected_ceiling: float | None,
    distribution: Mapping[str, object],
    candidate_rows: list[dict[str, object]],
    demo: Mapping[str, object],
) -> str:
    lines = [
        "# Defender-relative replay display-scale audit v1",
        "",
        "**Boundary:** response-free visualization QA using public Metrica tracking only.",
        "",
        f"**Decision:** `{selected_status}`",
        f"**Selected ceiling:** {selected_ceiling if selected_ceiling is not None else 'none'}",
        "",
        "The audit used both teams and both periods from Sample Games 1 and 2, with no event files, ball data, anchors, ranks, attacker direction, or scientific outcomes.",
        "",
        "## Pooled raw-score summary",
        "",
        f"- Supported player-frame scores: {distribution['player']['count']}",
        f"- Player median / p95 / p99 / max (m): {distribution['player']['median']:.6f} / {distribution['player']['p95']:.6f} / {distribution['player']['p99']:.6f} / {distribution['player']['maximum']:.6f}",
        f"- Supported team frames: {distribution['team_mean']['count']}",
        f"- Team median / p95 / p99 / max (m): {distribution['team_mean']['median']:.6f} / {distribution['team_mean']['p95']:.6f} / {distribution['team_mean']['p99']:.6f} / {distribution['team_mean']['maximum']:.6f}",
        "",
        "## Candidate ceilings",
        "",
        "| Ceiling | Player saturation | Team-mean saturation | Qualifies |",
        "|---:|---:|---:|:---:|",
    ]
    for row in candidate_rows:
        qualifies = row["player_saturation_fraction"] <= 0.05 and row["team_mean_saturation_fraction"] <= 0.01
        lines.append(
            f"| {row['ceiling_m']:.1f} m | {100*row['player_saturation_fraction']:.3f}% | {100*row['team_mean_saturation_fraction']:.3f}% | {'yes' if qualifies else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Fixed-demo secondary check",
            "",
            (
                f"At the selected ceiling, {demo['displayed']['player_saturation_count']} of 2,510 displayed defender-frame values saturated ({100*demo['displayed']['player_saturation_fraction']:.3f}%)."
                if demo.get("performed")
                else "Not performed because no candidate met the frozen rule."
            ),
            "",
            "## Interpretation",
            "",
            "These are display-QA distributions, not football findings. The score remains raw accumulated trailing defender-relative path in metres. No scientific claim or scorer behavior changed.",
            "",
        ]
    )
    return "\n".join(lines)


def execute(output_dir: Path = DEFAULT_OUTPUT, report_path: Path = DEFAULT_REPORT) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"authoritative output already exists: {output_dir}")
    config = load_config()
    source_hashes = verify_frozen_inputs(config)
    output_dir.mkdir(parents=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    per_game: dict[int, dict[str, object]] = {}
    source_run_counts: dict[str, int] = {}
    for game in (1, 2):
        matrices: list[np.ndarray] = []
        team_arrays: list[np.ndarray] = []
        for team in ("Home", "Away"):
            path = ROOT / f"data/metrica_sample_game_{game}/Sample_Game_{game}_RawTrackingData_{team}_Team.csv"
            matrix, teams, run_count = score_team_file(path, game=game, team=team)
            matrices.append(matrix)
            team_arrays.append(teams)
            source_run_counts[f"game_{game}_{team.lower()}"] = run_count
        per_game[game] = {"players": np.vstack(matrices), "teams": np.concatenate(team_arrays)}

    player_matrix = np.vstack([per_game[game]["players"] for game in (1, 2)])
    team_means = np.concatenate([per_game[game]["teams"] for game in (1, 2)])
    player_values = player_matrix.reshape(-1)
    distribution = {
        "player": distribution_summary(player_values, (0.5, 0.75, 0.9, 0.95, 0.975, 0.99)),
        "team_mean": distribution_summary(team_means, (0.5, 0.9, 0.95, 0.99)),
    }
    candidate_rows = [candidate_audit(player_matrix, team_means, ceiling) for ceiling in CANDIDATE_CEILINGS]
    spread_rows = [perceptual_spread(player_values, ceiling) for ceiling in CANDIDATE_CEILINGS]
    status, selected = select_ceiling(candidate_rows)
    demo = _demo_check(selected)

    write_json(output_dir / "distribution_summary.json", distribution)
    pd.DataFrame(_summary_rows(per_game)).to_csv(output_dir / "per_game_summary.csv", index=False, lineterminator="\n")
    pd.DataFrame(candidate_rows).to_csv(output_dir / "candidate_scale_audit.csv", index=False, lineterminator="\n")
    pd.DataFrame(spread_rows).to_csv(output_dir / "perceptual_spread.csv", index=False, lineterminator="\n")
    write_json(output_dir / "demo_secondary_check.json", demo)
    write_json(
        output_dir / "source_identities.json",
        {
            "tracking_sha256": source_hashes,
            "scorer_path": str(SCORER_PATH.relative_to(ROOT)),
            "scorer_sha256": sha256(SCORER_PATH),
            "protocol_sha256": sha256(PROTOCOL_PATH),
            "config_sha256": sha256(CONFIG_PATH),
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
        "events_read": False,
        "ball_read": False,
        "research_anchors_used": False,
        "scientific_outcomes_used": False,
        "game_3_accessed": False,
        "row_level_output_written": False,
    }
    write_json(output_dir / "manifest.json", manifest)
    hard_qc = {
        "passed": True,
        "candidate_set_exact": tuple(row["ceiling_m"] for row in candidate_rows) == CANDIDATE_CEILINGS,
        "player_team_cardinality": int(player_values.size) == 10 * int(team_means.size),
        "all_scores_finite_nonnegative": bool(np.isfinite(player_values).all() and (player_values >= 0).all()),
        "team_means_match_players": bool(np.allclose(player_matrix.mean(axis=1), team_means, atol=1e-12, rtol=0)),
        "scorer_hash_unchanged": sha256(SCORER_PATH) == SCORER_SHA256,
        "events_read": False,
        "ball_read": False,
        "protected_outcomes_read": False,
        "game_3_accessed": False,
    }
    hard_qc["passed"] = all(value for key, value in hard_qc.items() if key not in {"passed", "events_read", "ball_read", "protected_outcomes_read", "game_3_accessed"}) and not any(
        hard_qc[key] for key in ("events_read", "ball_read", "protected_outcomes_read", "game_3_accessed")
    )
    write_json(output_dir / "hard_qc.json", hard_qc)
    report_path.write_text(_report(status, selected, distribution, candidate_rows, demo), encoding="utf-8")

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
    write_json(
        output_dir / "final_hashes.json",
        {str(path.relative_to(ROOT)): sha256(path) for path in governed},
    )
    return {"classification": status, "selected_ceiling_m": selected, "output_dir": str(output_dir), "report": str(report_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-audit", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if not args.execute_audit:
        raise SystemExit("response-free audit requires explicit --execute-audit")
    print(json.dumps(execute(args.output_dir, args.report_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
