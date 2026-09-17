"""Outcome-blind audit of independently acquired SkillCorner Open Data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path, PurePosixPath

from defensive_reorganization_spatial_form_skillcorner_external import MatchSource
from infrastructure.skillcorner_spatial_form_adapter import timestamp_seconds

ROOT = Path(__file__).resolve().parents[1]
NAME = "skillcorner_additional_directional_support_preflight_v1"
PROTOCOL = ROOT / "docs" / "protocols" / f"{NAME}.md"
CONFIG = ROOT / "config" / f"{NAME}.json"
OUTPUT = ROOT / "outputs" / NAME
REPORT = ROOT / "docs" / "results" / f"{NAME}.md"
LFS = re.compile(rb"version https://git-lfs\.github\.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n")


class AuditError(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise AuditError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repository, *args):
    result = subprocess.run(["git", "-C", str(repository), *args], capture_output=True)
    require(result.returncode == 0, "pinned source Git identity unavailable")
    return result.stdout


def source_identities(data_dir, repository, config):
    commit = config["source"]["commit"]
    require(git(repository, "rev-parse", "HEAD").decode().strip() == commit, "source checkout mismatch")
    tree = {}
    for record in git(repository, "ls-tree", "-rrz", commit).split(b"\0"):
        if record:
            meta, path = record.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            tree[path.decode()] = (mode, kind, oid)
    records = []
    matches = sorted(config["existing_formal_matches"] + config["previously_excluded_matches"] + config["candidate_matches"])
    for match in matches:
        for template in config["required_files"]:
            name = template.format(match_id=match)
            found = [path for path in tree if PurePosixPath(path).name == name]
            require(len(found) == 1, "missing or ambiguous pinned source path")
            upstream = found[0]
            mode, kind, oid = tree[upstream]
            require(mode == "100644" and kind == "blob", "unexpected source object")
            local = Path(data_dir) / name
            require(local.is_file() and not local.is_symlink(), "missing or unsafe materialized source")
            pointer = LFS.fullmatch(git(repository, "cat-file", "blob", oid))
            actual_sha, size = sha256(local), local.stat().st_size
            if pointer:
                require(actual_sha == pointer.group(1).decode() and size == int(pointer.group(2)), "LFS identity mismatch")
            records.append({"match_id": match, "file": name, "upstream_path": upstream,
                            "git_blob_sha": oid, "sha256": actual_sha, "bytes": size,
                            "lfs": bool(pointer)})
    return records


def audit_source(source, expected_hz=10, tolerance=1e-9):
    meta = source.meta
    required_meta = ("id", "status", "pitch_length", "pitch_width", "home_team", "away_team", "home_team_side", "players")
    require(all(key in meta for key in required_meta), "metadata schema mismatch")
    require(math.isfinite(float(meta["pitch_length"])) and float(meta["pitch_length"]) > 0, "invalid pitch length")
    require(math.isfinite(float(meta["pitch_width"])) and float(meta["pitch_width"]) > 0, "invalid pitch width")
    require(len(meta["home_team_side"]) >= 2, "missing attacking direction")
    ids = [int(player["id"]) for player in meta["players"]]
    require(len(ids) == len(set(ids)), "duplicate roster identity")
    keepers = [player for player in meta["players"] if int(player["player_role"]["id"]) == 0]
    require(len(keepers) >= 2, "goalkeeper roles unavailable")
    substitutions = any(int(player["playing_time"]["total"]["start_frame"]) > min(source.period_frames[1]) or
                        int(player["playing_time"]["total"]["end_frame"]) < max(source.period_frames[2])
                        for player in meta["players"])
    player_status_seen = ball_status_seen = False
    possession = True
    for period, frames in source.period_frames.items():
        start = frames[0]
        for frame in frames:
            row = source.rows[frame]
            actual = timestamp_seconds(row["timestamp"], period)
            require(math.isfinite(actual), "nonfinite native timestamp")
            require(abs(actual - (frame - start) / expected_hz) <= tolerance, "native clock mismatch")
            possession &= row.get("possession", {}).get("group") in {"home team", "away team", None}
            ball = row.get("ball_data", {})
            if ball.get("x") is not None or ball.get("y") is not None:
                require(ball.get("x") is not None and ball.get("y") is not None, "partial ball coordinate")
                require(math.isfinite(float(ball["x"])) and math.isfinite(float(ball["y"])), "nonfinite ball coordinate")
                require(isinstance(ball.get("is_detected"), bool), "missing ball detection status")
                ball_status_seen = True
            for player in row.get("player_data", []):
                require(int(player["player_id"]) in source.player_team, "tracking identity outside roster")
                if player.get("x") is None or player.get("y") is None:
                    require(player.get("x") is None and player.get("y") is None, "partial player coordinate")
                    continue
                require(math.isfinite(float(player["x"])) and math.isfinite(float(player["y"])), "nonfinite player coordinate")
                require(isinstance(player.get("is_detected"), bool), "missing player detection status")
                player_status_seen = True
    require(player_status_seen and ball_status_seen, "detection flag unavailable")
    require(possession, "unsupported possession group")
    require(source.phase_coverage, "empty ball-in-play phase support")
    equivalence = source.provider_equivalence()
    require(equivalence["pass"], "native/Kloppy equivalence failure")
    return {
        "match_id": source.match_id,
        "status": str(meta["status"]),
        "pitch_length_m": float(meta["pitch_length"]),
        "pitch_width_m": float(meta["pitch_width"]),
        "period_count": len(source.period_frames),
        "frame_count": sum(map(len, source.period_frames.values())),
        "native_hz": expected_hz,
        "clock_valid": True,
        "identity_valid": True,
        "goalkeeper_support": True,
        "substitution_support": bool(substitutions),
        "possession_support": True,
        "ball_support": True,
        "detection_support": True,
        "phase_support": True,
        "attacking_direction_support": True,
        "provider_equivalence": True,
    }


def classify(match, config):
    if match in config["existing_formal_matches"]:
        return "existing_project1"
    if match in config["previously_excluded_matches"]:
        return "excluded_incompatible"
    if match in config["candidate_matches"]:
        return "nonoverlapping_candidate"
    return "unresolved"


def execute(data_dir, repository, output=OUTPUT, report=REPORT):
    config = json.loads(CONFIG.read_text())
    identities = source_identities(data_dir, repository, config)
    matches = sorted({row["match_id"] for row in identities})
    require(len(matches) == config["required_total_matches"], "match count mismatch")
    rows = []
    for match in matches:
        result = audit_source(MatchSource(match, Path(data_dir)), config["native_hz"], config["clock_tolerance_s"])
        result["population_class"] = classify(match, config)
        rows.append(result)
    candidates = [row for row in rows if row["population_class"] == "nonoverlapping_candidate"]
    require(len(candidates) == config["required_candidate_matches"], "candidate count mismatch")
    require(all(row["provider_equivalence"] and row["clock_valid"] for row in candidates), "candidate compatibility failure")
    output, report = Path(output), Path(report)
    require(not output.exists() and not report.exists(), "authoritative output already exists")
    output.mkdir(parents=True)
    columns = ["match_id", "population_class", "status", "pitch_length_m", "pitch_width_m", "period_count", "frame_count", "native_hz", "clock_valid", "identity_valid", "goalkeeper_support", "substitution_support", "possession_support", "ball_support", "detection_support", "phase_support", "attacking_direction_support", "provider_equivalence"]
    with (output / "inventory.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, columns, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (output / "source_hashes.json").write_text(json.dumps({"repository": config["source"]["repository"], "commit": config["source"]["commit"], "files": identities}, sort_keys=True, indent=2) + "\n")
    qc = {"status": "OUTCOME_BLIND_COMPATIBILITY_PASSED", "total_matches": len(rows),
          "existing_overlap": sum(classify(m, config) == "existing_project1" for m in matches),
          "candidate_matches": len(candidates), "excluded_incompatible": sum(classify(m, config) == "excluded_incompatible" for m in matches),
          "unresolved": sum(classify(m, config) == "unresolved" for m in matches), "response_constructed": False,
          "directional_contrast_run": False, "animation_generated": False}
    (output / "hard_qc.json").write_text(json.dumps(qc, sort_keys=True, indent=2) + "\n")
    manifest = {"protocol_sha256": sha256(PROTOCOL), "config_sha256": sha256(CONFIG),
                "source_sha256": sha256(Path(__file__)), "qc": qc,
                "source": config["source"], "acquisition": config["acquisition"],
                "contamination_caveat": "Project 1 nonoverlap is verified; global prior exposure was not audited because no sibling repository was accessed.",
                "next_action": "freeze one prospective ten-match directional replication protocol; no execution is authorized"}
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# SkillCorner additional directional replication support preflight v1\n\n"
                      "**OUTCOME-BLIND COMPATIBILITY PASSED — RESPONSE EXECUTION NOT AUTHORIZED**\n\n"
                      f"The official upstream release at `{config['source']['commit']}` contained 20 matches: 9 overlap the existing Project 1 formal population, 10 are nonoverlapping candidates, and 1 is the previously excluded provider-status conflict. All ten candidates passed the frozen source, schema, clock, identity, pitch, roster, ball, phase, detection, direction, and native/Kloppy equivalence checks.\n\n"
                      "No rank, defender-relative path, response, outward-versus-goalward contrast, model, bootstrap, or animation was constructed. The candidates are prospectively nonoverlapping within Project 1, not globally untouched; exposure in another project was deliberately not inspected.\n\n"
                      "The sole recommended next action is to freeze a one-execution ten-match directional-replication protocol with no tuning and preservation of mixed, negative, or invalid results.\n", encoding="utf-8")
    hashes = {path.name: sha256(path) for path in sorted(output.iterdir())}
    hashes[report.as_posix()] = sha256(report)
    (output / "final_hashes.json").write_text(json.dumps(hashes, sort_keys=True, indent=2) + "\n")
    return qc


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-support", action="store_true")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--pinned-repository", type=Path)
    args = parser.parse_args(argv)
    if not args.execute_support:
        parser.error("outcome-blind execution requires --execute-support")
    require(args.data_dir and args.pinned_repository, "data and pinned repository are required")
    print(json.dumps(execute(args.data_dir, args.pinned_repository), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
