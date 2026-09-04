"""Execute frozen DRD v2 without reading the response target before support gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import concurrent_attacker_defensive_geometry_idsse_v1 as concurrent  # noqa: E402
import defensive_reorganization_departure_v1 as v1  # noqa: E402
import phase4c_idsse_external_replication as idsse  # noqa: E402
from defensive_reorganization_departure_v2_support import (  # noqa: E402
    active_ball_nearest_attacker,
    active_outfield_at_anchor,
    active_set_support_is_complete,
)

PROTOCOL = ROOT / "docs/protocols/defensive_reorganization_departure_v2.md"
CONFIG = ROOT / "config/defensive_reorganization_departure_v2.json"
LEDGER = ROOT / "config/defensive_reorganization_departure_v2_hashes.json"
TARGET = ROOT / "outputs/spatial_defensive_response_footprint_idsse_v1/observation_rows.parquet"
OUTPUT = ROOT / "outputs/defensive_reorganization_departure_v2"
MATCHES = v1.MATCHES
FRAME_NS, EDGE = v1.FRAME_NS, v1.EDGE


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    bad = {}
    for section in ("frozen_v2_sha256", "preserved_v1_sha256"):
        for name, expected in ledger[section].items():
            actual = sha(ROOT / name)
            if actual != expected:
                bad[name] = {"actual": actual, "expected": expected}
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")


def target_metadata() -> pd.DataFrame:
    """Read only identifiers and ranks; deliberately exclude response values."""
    columns = ["observation_id", "match_id", "period", "time_period_s", "time_utc_ns",
               "attacker_key", "attacking_team", "defending_team", "block_id",
               "defender_key", "distance_rank"]
    data = pd.DataFrame(pl.read_parquet(TARGET, columns=columns).to_dict(as_series=False))
    rows = []
    for oid, group in data.groupby("observation_id", sort=False):
        group = group.sort_values("distance_rank")
        if group.distance_rank.tolist() != list(range(1, 11)):
            raise RuntimeError(f"invalid inherited rank vector: {oid}")
        first = group.iloc[0]
        rows.append({"observation_id": oid, "match_id": first.match_id,
                     "period": int(first.period), "time_period_s": float(first.time_period_s),
                     "time_utc_ns": int(first.time_utc_ns), "attacker_key": first.attacker_key,
                     "attacking_team": first.attacking_team, "defending_team": first.defending_team,
                     "block_id": int(first.block_id),
                     "defender_keys": tuple(group.defender_key.tolist())})
    return pd.DataFrame(rows).sort_values(
        ["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort"
    ).reset_index(drop=True)


def roster_registry(match_id: str, metadata: dict) -> tuple[dict[str, tuple[str, ...]], dict[str, list[dict[str, object]]]]:
    """Create an event-only active-outfield registry; no tracking values enter."""
    raw = ROOT / "data/idsse_raw"
    meta_path = idsse.find_file(raw, "metadata", match_id)
    event_path = idsse.find_file(raw, "events", match_id)
    starters: dict[str, list[str]] = defaultdict(list)
    root = ET.parse(meta_path).getroot()
    for node in root.iter():
        if idsse.local(node.tag) != "Team":
            continue
        team = node.attrib["TeamId"]
        for player in node.iter():
            if idsse.local(player.tag) != "Player":
                continue
            if player.attrib.get("Starting", "false").lower() == "true" and player.attrib.get("PlayingPosition") != "TW":
                starters[team].append(player.attrib["PersonId"])
    expected_teams = {metadata["home_team_id"], metadata["away_team_id"]}
    if set(starters) != expected_teams or any(len(set(players)) != 10 for players in starters.values()):
        raise RuntimeError("metadata starting-outfield registry is incomplete or ambiguous")
    events: dict[str, list[dict[str, object]]] = defaultdict(list)
    tree = ET.parse(event_path)
    for event in tree.getroot().iter():
        if idsse.local(event.tag) != "Event" or "EventTime" not in event.attrib:
            continue
        time_ns = idsse.iso_ns(idsse.parse_time(event.attrib["EventTime"]))
        event_id = event.attrib.get("EventId", "")
        for child in list(event):
            tag, attrs = idsse.local(child.tag), child.attrib
            if tag == "Substitution":
                required = ("Team", "PlayerOut", "PlayerIn")
                if not all(key in attrs for key in required):
                    raise RuntimeError("ambiguous substitution event")
                events[attrs["Team"]].append({"kind": "substitution", "time_ns": time_ns,
                                                "event_id": event_id, "player_out": attrs["PlayerOut"],
                                                "player_in": attrs["PlayerIn"]})
            elif tag == "Caution" and attrs.get("CardColor", "").lower() == "red":
                required = ("Team", "Player")
                if not all(key in attrs for key in required):
                    raise RuntimeError("ambiguous dismissal event")
                events[attrs["Team"]].append({"kind": "dismissal", "time_ns": time_ns,
                                                "event_id": event_id, "player": attrs["Player"]})
    return {team: tuple(sorted(players)) for team, players in starters.items()}, events


def period_signs(metadata: dict, tracking: dict) -> dict[tuple[int, str], int]:
    return v1.period_signs(metadata, tracking)


def add_features_for_match(base: pd.DataFrame, match_id: str) -> tuple[pd.DataFrame, list[dict], int, dict]:
    metadata, _, tracking = concurrent.load_native(match_id)
    starters, roster_events = roster_registry(match_id, metadata)
    signs = period_signs(metadata, tracking)
    period_cache = {
        period_name: (
            {int(t): i for i, t in enumerate(tracking[period_name]["time_ns"])},
            {(entity["team_id"], entity["person_id"]): entity for entity in tracking[period_name]["entities"]},
        )
        for period_name in idsse.PERIODS
    }
    result, exclusions, offball_base = [], [], 0
    roster_counts: dict[str, int] = defaultdict(int)
    for _, row in base.loc[base.match_id == match_id].iterrows():
        period_name = idsse.PERIODS[int(row.period) - 1]
        pdata = tracking[period_name]
        lookup, entity = period_cache[period_name]
        anchor = int(row.time_utc_ns)
        required = np.arange(anchor - 4_120_000_000, anchor + 120_000_000 + FRAME_NS, FRAME_NS, dtype=np.int64)
        if any(int(t) not in lookup for t in required):
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "feature_cadence_support"})
            continue
        idx = lookup[anchor]
        attack, defend = row.attacking_team, row.defending_team
        try:
            active = active_outfield_at_anchor(starters[attack], roster_events.get(attack, []), anchor)
        except ValueError:
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "ambiguous_active_attacking_roster"})
            continue
        complete = sorted(
            player.player_id for player in metadata["players"].values()
            if player.team_id == attack and not player.goalkeeper
            and (attack, player.player_id) in entity
            and entity[(attack, player.player_id)]["valid"][idx - EDGE:idx + EDGE + 1].all()
        )
        if not active_set_support_is_complete(active, complete):
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "complete_current_attacking_anchor_set"})
            continue
        roster_counts[str(len(active))] += 1
        ball = next((e for e in pdata["entities"] if e["team_id"] == "BALL"), None)
        if ball is None or not ball["valid"][idx - 53:idx + 4].all():
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "ball_feature_support"})
            continue
        positions = {player: v1.smoothed(entity[(attack, player)], idx) for player in active}
        nearest = active_ball_nearest_attacker(positions, v1.smoothed(ball, idx))
        if row.attacker_key == nearest:
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "ball_nearest_at_anchor"})
            continue
        offball_base += 1
        focal = entity.get((attack, row.attacker_key))
        if focal is None or not focal["valid"][idx - 103:idx + 4].all():
            exclusions.append({"observation_id": row.observation_id, "match_id": match_id, "reason": "focal_feature_support"})
            continue
        defenders = list(row.defender_keys)
        if len(defenders) != 10 or not all((defend, player) in entity and entity[(defend, player)]["valid"][idx - 53:idx + 4].all() for player in defenders):
            raise RuntimeError("inherited target and feature defender support disagree")
        prior = v1.smooth_series(focal, np.arange(idx - 100, idx - 49))
        exposure = v1.smooth_series(focal, np.arange(idx - 50, idx + 1))
        focal_start, focal_anchor = exposure[0], exposure[-1]
        defender_start = np.stack([v1.smoothed(entity[(defend, player)], idx - 50) for player in defenders])
        ball_start, ball_anchor = v1.smoothed(ball, idx - 50), v1.smoothed(ball, idx)
        transformed = v1.attacking_frame(np.vstack([focal_start, focal_anchor, defender_start, ball_start, ball_anchor]), signs[(int(row.period), attack)], focal_start[1])
        f0, ft, ds, b0, bt = transformed[0], transformed[1], transformed[2:12], transformed[12], transformed[13]
        unit = ds.mean(axis=0)
        values = row.to_dict()
        values.update({
            "attacker_path_exposure_m": v1.path(exposure), "attacker_path_prior_m": v1.path(prior),
            "attacker_goalward_displacement_m": float(ft[0] - f0[0]), "attacker_outward_displacement_m": float(ft[1] - f0[1]),
            "attacker_minus_unit_goalward_m": float(f0[0] - unit[0]), "attacker_minus_unit_outward_m": float(f0[1] - unit[1]),
            "defending_unit_depth_m": float(np.ptp(ds[:, 0])), "defending_unit_width_m": float(np.ptp(ds[:, 1])),
            "attacker_ball_distance_start_m": float(np.linalg.norm(f0 - b0)), "ball_minus_unit_goalward_m": float(b0[0] - unit[0]),
            "ball_minus_unit_outward_m": float(b0[1] - unit[1]), "attacker_ball_distance_change_m": float(np.linalg.norm(ft - bt) - np.linalg.norm(f0 - b0)),
            "ball_nearest_attacker_key": nearest,
        })
        result.append(values)
    return pd.DataFrame(result), exclusions, offball_base, dict(sorted(roster_counts.items()))


def build_outcome_blind_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    base = target_metadata()
    frames, excluded, offball_base, active_counts = [], [], {}, {}
    for match in MATCHES:
        data, log, count, counts = add_features_for_match(base, match)
        frames.append(data); excluded.extend(log); offball_base[match] = count; active_counts[match] = counts
    sample = pd.concat(frames, ignore_index=True).sort_values(
        ["match_id", "period", "time_period_s", "attacker_key"], kind="mergesort"
    ).reset_index(drop=True)
    ledger = pd.DataFrame(excluded, columns=["observation_id", "match_id", "reason"])
    all_counts = base.groupby("match_id").size(); kept = sample.groupby("match_id").size()
    report = {}
    for match in MATCHES:
        data = sample.loc[sample.match_id == match]
        blocks = data[["period", "block_id"]].drop_duplicates()
        coverage = {f"P{period}": {"anchors": int(part.time_period_s.nunique()), "start_s": float(part.time_period_s.min()), "end_s": float(part.time_period_s.max())}
                    for period, part in data.groupby("period", sort=True)}
        report[match] = {"inherited_target_rows": int(all_counts[match]), "threshold_free_off_ball_base_rows": int(offball_base[match]),
                         "common_sample_rows": int(kept.get(match, 0)), "retention_of_off_ball_base_rows": float(kept.get(match, 0) / offball_base[match]),
                         "unique_anchors": int(data[["period", "time_period_s"]].drop_duplicates().shape[0]),
                         "occupied_60_second_blocks": int(len(blocks)), "period_coverage": coverage,
                         "active_outfield_anchor_counts": active_counts[match]}
    return sample, ledger, report


def join_target_after_gate(sample: pd.DataFrame) -> pd.DataFrame:
    """This is the first permitted response-target read, after all support gates pass."""
    values = v1.target_rows()[["observation_id", "near_component_m", "middle_component_m", "Y_m"]]
    data = sample.merge(values, on="observation_id", validate="one_to_one")
    if len(data) != len(sample):
        raise RuntimeError("target join lost eligible rows")
    return data


def write_report(output: Path, result: dict) -> None:
    lines = ["# Defensive Reorganization Departure v2 — IDSSE result", "", f"**Formal status:** `{result['status']}`", ""]
    if result["status"] == "DRD APPLICATION FOUNDATION INVALID":
        lines += ["The frozen common-sample gate failed before any E0/E1 fit or target read.", ""]
    else:
        lines += ["The frozen v2 execution used the v1 target, models, validation, and classification unchanged.", ""]
    (output / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def hash_outputs(output: Path) -> dict[str, str]:
    omit = {"governed_hashes.json", "reproduction.json", "final_hashes.json", "eligibility_ledger.csv", "heldout_predictions.parquet"}
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name not in omit}


def execute(output: Path) -> dict:
    verify_frozen()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    sample, exclusions, retention = build_outcome_blind_sample()
    passed = all(value["common_sample_rows"] >= 1000 and value["retention_of_off_ball_base_rows"] >= .9 for value in retention.values())
    sample_retention = pd.DataFrame([{"match_id": match, **value} for match, value in retention.items()])
    exclusions.to_csv(output / "eligibility_ledger.csv", index=False)
    sample_retention.to_csv(output / "sample_retention.csv", index=False)
    v1.write_json(output / "feature_dictionary.json", {name: list(features) for name, features in v1.MODELS.items()})
    if not passed:
        hard_qc = {"frozen_hashes": True, "common_sample_minimum_rows": False,
                   "common_sample_retention_minimum": all(value["retention_of_off_ball_base_rows"] >= .9 for value in retention.values()),
                   "target_not_read_after_pre_fit_invalidity": True, "model_not_fitted_after_pre_fit_invalidity": True,
                   "no_prediction_error_or_residual_inspected": True, "no_skillcorner": True,
                   "no_metrica_transport": True, "no_player_ranking": True, "game3_untouched": True}
        result = {"status": "DRD APPLICATION FOUNDATION INVALID", "invalid_reason": "frozen_common_sample_gate_failure",
                  "sample_retention": retention, "hard_qc": hard_qc,
                  "execution": {"empirical_target_used": False, "model_fitted": False,
                                "prediction_error_or_residual_inspected": False, "DRD_computed": False,
                                "SkillCorner_outcome": False, "Game3_accessed": False}}
        v1.write_json(output / "hard_qc.json", hard_qc); v1.write_json(output / "result.json", result)
        v1.write_json(output / "manifest.json", {"protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "status": result["status"], "model_fitted": False})
        write_report(output, result); v1.write_json(output / "governed_hashes.json", hash_outputs(output)); return result
    data = join_target_after_gate(sample)
    if not np.isfinite(data[list(v1.MODELS["E1"]) + ["Y_m"]].to_numpy(float)).all():
        raise RuntimeError("nonfinite common features or target")
    predictions, alphas = v1.nested_predictions(data)
    metrics_table, metrics = v1.model_metrics(predictions)
    _, intervals = v1.bootstrap(predictions)
    status, stable, _ = v1.classification(metrics)
    ablation = {}
    for family in ("movement_direction", "start_position", "ball_geometry"):
        ablated = metrics[f"E1_minus_{family}"]["by_match"]
        full = metrics["E1"]["by_match"]
        macro = 100.0 * (metrics[f"E1_minus_{family}"]["macro_MAE_m"] - metrics["E1"]["macro_MAE_m"]) / metrics["E1"]["macro_MAE_m"]
        ablation[family] = {"macro_worsening_percent": macro,
                             "matches_worsened": int(sum(ablated[match] > full[match] for match in MATCHES)),
                             "passed_stable_family_gate": v1.family_is_stable(full, ablated)}
    e0, e1 = metrics["E0"], metrics["E1"]
    comparison = pd.DataFrame([{"match_id": match, "E0_MAE_m": e0["by_match"][match], "E1_MAE_m": e1["by_match"][match],
                                "relative_improvement_percent": v1.relative_improvement_percent(e0["by_match"][match], e1["by_match"][match])} for match in MATCHES])
    hard_qc = {"frozen_hashes": True, "common_sample_minimum_rows": True,
               "common_sample_retention_minimum": True, "finite_common_features_and_target": True,
               "one_outer_prediction_per_model_observation": len(predictions) == len(data) * len(v1.MODELS),
               "bootstrap_valid_at_least_950": all(value["valid"] >= v1.MIN_VALID for value in intervals.values()),
               "no_skillcorner": True, "no_metrica_transport": status != "DRD APPLICATION FOUNDATION SUPPORTED",
               "no_player_ranking": True, "game3_untouched": True}
    result = {"status": f"DRD APPLICATION FOUNDATION {status}", "sample_retention": retention,
              "metrics": metrics, "e1_vs_e0_absolute_macro_improvement_m": e0["macro_MAE_m"] - e1["macro_MAE_m"],
              "e1_vs_e0_relative_improvement_percent": v1.relative_improvement_percent(e0["macro_MAE_m"], e1["macro_MAE_m"]),
              "matches_improved": int(sum(e1["by_match"][m] < e0["by_match"][m] for m in MATCHES)),
              "maximum_match_worsening_percent": float(max(0.0, max(-v1.relative_improvement_percent(e0["by_match"][m], e1["by_match"][m]) for m in MATCHES))),
              "stable_context_families": stable, "family_ablations": ablation, "bootstrap_intervals": intervals,
              "hard_qc": hard_qc, "execution": {"empirical_target_used": True, "model_fitted": True,
                                                   "prediction_error_or_residual_inspected": False, "DRD_computed": False,
                                                   "SkillCorner_outcome": False, "Game3_accessed": False}}
    alphas.to_csv(output / "fold_alpha_ledger.csv", index=False)
    pl.DataFrame(predictions.to_dict("list")).write_parquet(output / "heldout_predictions.parquet")
    metrics_table.to_csv(output / "match_metrics.csv", index=False); comparison.to_csv(output / "e0_e1_per_match_comparison.csv", index=False)
    pd.DataFrame([{"family": key, **value} for key, value in ablation.items()]).to_csv(output / "family_ablations.csv", index=False)
    pd.DataFrame([{"quantity": key, **value} for key, value in intervals.items()]).to_csv(output / "bootstrap_intervals.csv", index=False)
    v1.write_json(output / "hard_qc.json", hard_qc); v1.write_json(output / "result.json", result)
    v1.write_json(output / "manifest.json", {"protocol_sha256": sha(PROTOCOL), "configuration_sha256": sha(CONFIG), "status": result["status"], "model_fitted": True})
    write_report(output, result); v1.write_json(output / "governed_hashes.json", hash_outputs(output)); return result


def verify(primary: Path, rerun: Path) -> dict:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    rows = []
    for name, expected in ledger.items():
        left, right = primary / name, rerun / name
        rows.append({"file": name, "expected_sha256": expected, "primary_sha256": sha(left),
                     "rerun_sha256": sha(right), "byte_identical": left.read_bytes() == right.read_bytes()})
    result = {"files_compared": len(rows), "all_governed_outputs_byte_identical": all(row["byte_identical"] for row in rows),
              "comparisons": rows}
    v1.write_json(primary / "reproduction.json", result)
    v1.write_json(primary / "final_hashes.json", {**ledger, "governed_hashes.json": sha(primary / "governed_hashes.json"),
                                                     "reproduction.json": sha(primary / "reproduction.json")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=OUTPUT); parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    result = verify(args.output, args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps({"status": result.get("status"), "byte_identical": result.get("all_governed_outputs_byte_identical")}, sort_keys=True))


if __name__ == "__main__":
    main()
