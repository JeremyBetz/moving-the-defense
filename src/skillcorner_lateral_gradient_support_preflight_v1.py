"""Response-blind SkillCorner lateral support preflight (SkillCorner Open Data, MIT).

Import/--help/--verify-freeze read no provider data. Future --execute-support
requires explicit authorization, reviewed source/test hashes and a local Git
repository containing the pinned release. The authorization reference records
review context (including the separately required governance reconciliation);
it is not independent proof of human approval. No outcome constructor is used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd

from defensive_reorganization_spatial_form_skillcorner_external import (
    MatchSource,
    continuity_valid,
    sorted_rank_ids,
)
from infrastructure.skillcorner_spatial_form_adapter import (
    anchor_frames,
    detected_fraction,
    goalward_sign,
    required_frame_ids,
    stricter_quality_pass,
)


ROOT = Path(__file__).resolve().parents[1]
NAME = "skillcorner_lateral_gradient_support_preflight_v1"
PROTOCOL = f"docs/protocols/{NAME}.md"
CONFIG = f"config/{NAME}.json"
SOURCE = f"src/{NAME}.py"
TESTS = f"tests/test_{NAME}.py"
FROZEN = {
    PROTOCOL: "02303400884ad6054d4aed123e13186c9706c887d0a618319953f2563ba25b94",
    CONFIG: "8a25438a31d954d0f0d3a43577ebc6b39f16af3e902625b2554ca9150c9d17fb",
}
MATCHES = (1886347, 1899585, 1925299, 1996435, 2006229, 2011166, 2013725, 2015213, 2017461)
RELEASE = "c1e17a0cc3e07e1774b52d929c1a0b85115143fc"
TEMPLATES = ("{}_match.json", "{}_tracking_extrapolated.jsonl", "{}_phases_of_play.csv")
SAMPLES = ("primary", "quality")
STATUS_PASS = "SUPPORT_PREFLIGHT_QC_PASSED_AWAITING_HUMAN_REVIEW"
STATUS_FAIL = "SUPPORT_PREFLIGHT_INVALID"
DETECTION = ("focal_detected_fraction", "ball_detected_fraction", "min_D1_D7_detected_fraction")
EXCLUSION_SPECS = {
    "cadence_or_period": ("anchor", "first_failure"),
    "complete_player_support": ("anchor", "first_failure"),
    "ball_support": ("anchor", "first_failure"),
    "not_continuously_ball_in_play": ("anchor", "first_failure"),
    "possession_at_anchor": ("anchor", "first_failure"),
    "identity_gate_row": ("attacker_anchor", "first_failure"),
    "ball_nearest": ("attacker_anchor", "design"),
    "roster_support": ("anchor", "nonexclusive_diagnostic"),
    "coordinate_support": ("anchor", "nonexclusive_diagnostic"),
    "detection_status_support": ("anchor", "nonexclusive_diagnostic"),
}


class SupportError(RuntimeError):
    """A fail-closed error; messages never include observation records."""


def _require(condition, message):
    if not condition:
        raise SupportError(message)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_freeze(root=ROOT):
    """Verify code/document identities only; never inspect a provider path."""
    root = Path(root)
    for path, expected in FROZEN.items():
        _require(_sha(root / path) == expected, "support protocol/config hash mismatch")
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    for path, expected in config["inherited_sha256"].items():
        _require(_sha(root / path) == expected, "inherited dependency hash mismatch")
    hashes = {**FROZEN, **config["inherited_sha256"]}
    hashes.update({path: _sha(root / path) for path in (SOURCE, TESTS)})
    return config, hashes


def _git(repository, *args):
    result = subprocess.run(["git", "-C", str(repository), *args], capture_output=True)
    _require(result.returncode == 0, "pinned source Git identity unavailable")
    return result.stdout


def _pinned_tree(repository):
    resolved = _git(repository, "rev-parse", "--verify", RELEASE + "^{commit}").decode().strip()
    _require(resolved == RELEASE, "pinned source commit mismatch")
    tree = {}
    for record in _git(repository, "ls-tree", "-rz", "--full-tree", RELEASE).split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        tree[path.decode("utf-8")] = (mode, kind, blob)
    return tree


def verify_source_identity(data_dir, pinned_repository):
    """Verify exactly 27 local files against Git blob IDs in the pinned tree.

    Streaming Git blob SHA-1 includes the Git header; SHA-256 is recorded for
    package provenance. No fields are decoded and no network request is made.
    """
    tree = _pinned_tree(pinned_repository)
    records = []
    for match in MATCHES:
        for template in TEMPLATES:
            filename = template.format(match)
            candidates = [path for path in tree if PurePosixPath(path).name == filename]
            _require(len(candidates) == 1, "missing or ambiguous pinned source path")
            upstream_path = candidates[0]
            mode, kind, expected_blob = tree[upstream_path]
            _require(mode in {"100644", "100755"} and kind == "blob", "source must be a regular Git blob")
            local = Path(data_dir) / filename
            _require(not local.is_symlink() and local.is_file(), "missing or symlinked source file")
            size = local.stat().st_size
            blob = hashlib.sha1(f"blob {size}\0".encode("ascii"))
            sha256 = hashlib.sha256()
            read_size = 0
            with local.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    read_size += len(chunk)
                    blob.update(chunk)
                    sha256.update(chunk)
            _require(read_size == size and blob.hexdigest() == expected_blob, "source blob mismatch")
            records.append({"path": filename, "upstream_path": upstream_path,
                            "blob_id": expected_blob, "sha256": sha256.hexdigest()})
    return {"release_commit": RELEASE, "files": records}


class SupportSource(MatchSource):
    """Explicit projection plus inherited support methods; never legacy execute.

    from_records is also the synthetic seam: input mappings are copied, and
    unrelated keys are never examined. The native loader is used only by the
    explicitly gated execution function.
    """

    def __init__(self, match_id, data_dir):
        _require(match_id in MATCHES, "match outside formal population")
        data_dir = Path(data_dir)
        with (data_dir / f"{match_id}_match.json").open(encoding="utf-8") as handle:
            metadata = json.load(handle)
        with (data_dir / f"{match_id}_tracking_extrapolated.jsonl").open(encoding="utf-8") as handle:
            projected = self.from_records(match_id, metadata, (json.loads(line) for line in handle), ())
        with (data_dir / f"{match_id}_phases_of_play.csv").open(encoding="utf-8", newline="") as handle:
            projected.phase_coverage = self._coverage(csv.DictReader(handle))
        self.__dict__.update(projected.__dict__)

    @staticmethod
    def _coverage(phases):
        coverage = set()
        for phase in phases:
            start, end = int(phase["frame_start"]), int(phase["frame_end"])
            _require(end >= start, "invalid phase interval")
            coverage.update(range(start, end + 1))
        return coverage

    @classmethod
    def from_records(cls, match_id, metadata, tracking, phases):
        _require(match_id in MATCHES, "match outside formal population")
        source = cls.__new__(cls)
        source.match_id = int(match_id)
        _require(int(metadata["id"]) == match_id, "metadata match identity mismatch")
        _require(metadata.get("status") != "not_started", "invalid match status")
        meta = {key: metadata[key] for key in ("id", "status", "pitch_length", "pitch_width")}
        meta["home_team_side"] = list(metadata["home_team_side"])
        for key in ("home_team", "away_team"):
            meta[key] = {"id": int(metadata[key]["id"])}
        meta["players"] = []
        for player in metadata["players"]:
            playing = player.get("playing_time")
            total = playing.get("total") if playing else None
            meta["players"].append({
                "id": int(player["id"]), "team_id": player.get("team_id"),
                "player_role": {"id": player["player_role"]["id"]},
                "playing_time": {"total": {key: total[key] for key in ("start_frame", "end_frame")}} if total else None,
            })
        _require(all(math.isfinite(float(meta[key])) and float(meta[key]) > 0
                     for key in ("pitch_length", "pitch_width")), "invalid pitch dimensions")
        source.meta = meta
        source.home_team_id = meta["home_team"]["id"]
        source.away_team_id = meta["away_team"]["id"]
        _require(source.home_team_id != source.away_team_id, "team identity mismatch")
        source.team_ids = (source.home_team_id, source.away_team_id)
        players = meta["players"]
        _require(len({p["id"] for p in players}) == len(players), "duplicate metadata player identity")
        source.player_team = {p["id"]: int(p["team_id"]) for p in players if p["team_id"] is not None}
        source.goalkeepers = {p["id"] for p in players if p["team_id"] is not None and int(p["player_role"]["id"]) == 0}
        source.rows, source.period_frames = {}, {1: [], 2: []}
        for row in tracking:
            if row.get("period") not in (1, 2):
                continue
            frame, period = int(row["frame"]), int(row["period"])
            _require(frame not in source.rows, "duplicate native frame")
            player_data = [{key: p.get(key) for key in ("player_id", "x", "y", "is_detected")}
                           for p in row["player_data"]]
            _require(len({p["player_id"] for p in player_data}) == len(player_data), "duplicate native player identity")
            source.rows[frame] = {
                "frame": frame, "period": period, "timestamp": row["timestamp"],
                "player_data": player_data,
                "ball_data": {key: row["ball_data"].get(key) for key in ("x", "y", "is_detected")},
                "possession": {"group": row["possession"].get("group")},
            }
            source.period_frames[period].append(frame)
        for period, frames in source.period_frames.items():
            _require(bool(frames) and all(b - a == 1 for a, b in zip(frames, frames[1:])), "native cadence gap or order disagreement")
            goalward_sign(meta["home_team_side"], period, True)
        source.period_start = {p: frames[0] for p, frames in source.period_frames.items()}
        source.period_end = {p: frames[-1] for p, frames in source.period_frames.items()}
        source.support_cache = {}
        source.phase_coverage = cls._coverage(phases)
        # Suppress inherited error messages that contain individual frame IDs.
        try:
            source._verify_native_clock()
        except (RuntimeError, ValueError, KeyError):
            raise SupportError("native timestamp/cadence disagreement") from None
        return source


@dataclass(frozen=True, repr=False)
class SupportObservation:
    """Memory-only; deliberately no row repr or general serialization method."""

    match_id: int
    period: int
    anchor_provider_frame: int
    focal_player_id: int
    block_id: int
    x_start_m: float
    y_start_m: float
    z_m: float
    goalward_x_m: float
    focal_detected_fraction: float
    ball_detected_fraction: float
    min_D1_D7_detected_fraction: float
    quality_pass: bool


def _validate_rows(rows):
    for row in rows:
        _require(type(row) is SupportObservation, "unexpected internal support schema")
        _require(row.match_id in MATCHES and row.period in (1, 2), "invalid support identity")
        _require(all(type(getattr(row, key)) is int for key in
                     ("match_id", "period", "anchor_provider_frame", "focal_player_id", "block_id")), "noninteger support identity")
        _require(row.block_id >= 0, "invalid temporal block")
        _require(all(math.isfinite(getattr(row, key)) for key in
                     ("x_start_m", "y_start_m", "z_m", "goalward_x_m", *DETECTION)), "nonfinite support value")
        _require(row.z_m == abs(row.y_start_m), "lateral predictor mismatch")
        _require(all(0 <= getattr(row, key) <= 1 for key in DETECTION), "invalid detection fraction")
        _require(type(row.quality_pass) is bool and row.quality_pass == all(getattr(row, key) >= 0.5 for key in DETECTION), "quality subset mismatch")


def observation_digest(rows):
    rows = tuple(rows)
    _validate_rows(rows)
    ids = [f"{r.match_id}:{r.period}:{r.anchor_provider_frame}:{r.focal_player_id}" for r in rows]
    _require(len(ids) == len(set(ids)), "duplicate observation identity")
    payload = "\n".join(sorted(ids)) + ("\n" if ids else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _support_diagnostics(source, anchor):
    """Nonexclusive reasons inside the inherited complete-player-support gate."""
    reasons = set()
    for frame in required_frame_ids(anchor):
        records = source.rows[frame]["player_data"]
        if any(not np.isfinite(np.asarray([r.get("x"), r.get("y")], float)).all() for r in records):
            reasons.add("coordinate_support")
        if any(not isinstance(r.get("is_detected"), bool) for r in records):
            reasons.add("detection_status_support")
        if any(source.player_team.get(int(r["player_id"])) not in source.team_ids for r in records):
            reasons.add("roster_support")
        for team in source.team_ids:
            expected = set(source.active_outfield(frame, team))
            observed = {int(r["player_id"]) for r in records if int(r["player_id"]) not in source.goalkeepers
                        and source.player_team.get(int(r["player_id"])) == team}
            if len(expected) != 10 or observed != expected:
                reasons.add("roster_support")
    return reasons


def extract_match_support(source):
    _require(source.match_id in MATCHES, "match outside formal population")
    observations, exclusions = [], Counter()
    for period in (1, 2):
        for anchor in anchor_frames(source.period_start[period], source.period_end[period]):
            reason = source.anchor_support_reason(anchor)
            if reason:
                _require(reason in EXCLUSION_SPECS, "unexpected inherited support reason")
                exclusions[reason] += 1
                if reason == "complete_player_support":
                    exclusions.update(_support_diagnostics(source, anchor))
                continue
            team = source.attacking_team(anchor)
            defending = source.away_team_id if team == source.home_team_id else source.home_team_id
            attackers = source.active_outfield(anchor, team)
            defenders = source.active_outfield(anchor, defending)
            ball = source.smooth_ball(anchor)
            nearest = min(attackers, key=lambda p: (float(np.linalg.norm(source.smooth_player(anchor, p) - ball)), int(p)))
            sign = goalward_sign(source.meta["home_team_side"], period, source.is_home(team))
            exclusions["ball_nearest"] += 1
            for focal in attackers:
                if focal == nearest:
                    continue
                x, y = map(float, source.smooth_player(anchor - 20, focal))
                ranks = sorted_rank_ids(source, anchor, focal, defenders, sign, y)
                if not continuity_valid(source, focal, ranks, anchor):
                    exclusions["identity_gate_row"] += 1
                    continue
                focal_flags = [source.detected(f, focal) for f in range(anchor - 41, anchor + 2)]
                ball_flags = [source.ball_detected(f) for f in range(anchor - 41, anchor + 2)]
                defender_flags = [[source.detected(f, p) for f in range(anchor - 1, anchor + 22)] for p in ranks[:7]]
                observations.append(SupportObservation(
                    source.match_id, period, anchor, int(focal), (anchor - source.period_start[period]) // 600,
                    x, y, abs(y), sign * x, detected_fraction(focal_flags), detected_fraction(ball_flags),
                    min(map(detected_fraction, defender_flags)),
                    stricter_quality_pass(focal_flags, ball_flags, defender_flags),
                ))
    observation_digest(observations)
    return tuple(observations), exclusions


def lateral_band(z):
    _require(math.isfinite(z) and z >= 0, "invalid lateral position")
    return "0_10" if z < 10 else "10_20" if z < 20 else "20_30" if z < 30 else "30_34" if z <= 34 else "over_34"


def _region(z):
    return "0_10" if z < 10 else "10_20" if z < 20 else "20_plus"


def _counts(rows):
    return {"observation_count": len(rows),
            "unique_time_anchor_count": len({(r.period, r.anchor_provider_frame) for r in rows}),
            "temporal_block_count": len({(r.period, r.block_id) for r in rows})}


def _detection_means(rows):
    return {"mean_" + key: float(np.mean([getattr(r, key) for r in rows])) if rows else None for key in DETECTION}


def _design_qc(rows, sample, match=None):
    matches = MATCHES if match is None else (match,)
    n, p = len(rows), len(matches) + 1
    result = {"sample": sample, "scope": "pooled" if match is None else "match", "match_id": match,
              "observation_count": n, "column_count": p, "rank": 0, "full_rank": False,
              "mean_leverage": None, "max_leverage": None}
    if not n:
        return result
    counts = Counter(r.match_id for r in rows)
    x = np.asarray([[1.0, *[float(r.match_id == m) for m in matches[1:]], r.z_m] for r in rows])
    a = x / np.sqrt(np.asarray([counts[r.match_id] for r in rows]))[:, None]
    u, singular, _ = np.linalg.svd(a, full_matrices=False)
    threshold = max(a.shape) * np.finfo(np.float64).eps * singular[0]
    rank = int(np.count_nonzero(singular > threshold))
    result.update(rank=rank, full_rank=rank == p)
    if rank == p:
        leverage = np.sum(u ** 2, axis=1)
        result.update(mean_leverage=float(leverage.mean()), max_leverage=float(leverage.max()))
    return result


def aggregate_support(rows, exclusions, config):
    rows = tuple(sorted(rows, key=lambda r: (r.match_id, r.period, r.anchor_provider_frame, r.focal_player_id)))
    observation_digest(rows)
    _require(set(exclusions) == set(MATCHES), "nine match extraction records required")
    tables = {name: [] for name in config["publication"]["csv_columns"]}
    for sample in SAMPLES:
        selected = rows if sample == "primary" else tuple(r for r in rows if r.quality_pass)
        tables["design_qc.csv"].append(_design_qc(selected, sample))
        for match in MATCHES:
            group = tuple(r for r in selected if r.match_id == match)
            z = [r.z_m for r in group]
            quantiles = np.quantile(z, [0.05, 0.25, 0.5, 0.75, 0.95], method="linear").tolist() if z else [None] * 5
            x = [r.goalward_x_m for r in group]
            tables["sample_summary.csv"].append({
                "match_id": match, "sample": sample, **_counts(group),
                "period_count": len({r.period for r in group}),
                "z_min_m": min(z) if z else None, "z_max_m": max(z) if z else None,
                **dict(zip(("z_q05_m", "z_q25_m", "z_median_m", "z_q75_m", "z_q95_m"), quantiles)),
                "z_variance_m2": float(np.var(z, ddof=0)) if z else None,
                **_detection_means(group),
                "out_of_pitch_count": sum(abs(r.x_start_m) > 52.5 or abs(r.y_start_m) > 34 for r in group),
                "outside_lateral_pitch_count": sum(abs(r.y_start_m) > 34 for r in group),
                "goalward_x_min_m": min(x) if x else None,
                "goalward_x_median_m": float(np.median(x)) if x else None,
                "goalward_x_max_m": max(x) if x else None,
            })
            for period in (1, 2):
                tables["period_summary.csv"].append({"match_id": match, "sample": sample, "period": period,
                    **_counts(tuple(r for r in group if r.period == period))})
            for band in ("0_10", "10_20", "20_30", "30_34", "over_34"):
                subgroup = tuple(r for r in group if lateral_band(r.z_m) == band)
                tables["lateral_support.csv"].append({"match_id": match, "sample": sample, "band": band,
                                                     **_counts(subgroup), **_detection_means(subgroup)})
            tables["design_qc.csv"].append(_design_qc(group, sample, match))
            if sample == "quality":
                for region in ("0_10", "10_20", "20_plus"):
                    counts = _counts(tuple(r for r in group if _region(r.z_m) == region))
                    time_ok, block_ok = counts["unique_time_anchor_count"] >= 20, counts["temporal_block_count"] >= 4
                    tables["quality_region_support.csv"].append({"match_id": match, "region": region, **counts,
                        "time_count_pass": time_ok, "block_count_pass": block_ok, "region_pass": time_ok and block_ok})
    for match in MATCHES:
        _require(set(exclusions[match]) <= set(EXCLUSION_SPECS), "unexpected exclusion reason")
        for reason, (unit, count_class) in sorted(EXCLUSION_SPECS.items()):
            count = exclusions[match].get(reason, 0)
            _require(type(count) is int and count >= 0, "invalid exclusion count")
            tables["exclusions.csv"].append({"match_id": match, "reason": reason, "counting_unit": unit,
                                            "count_class": count_class, "count": count})
    return {name: pd.DataFrame(data, columns=config["publication"]["csv_columns"][name])
            .sort_values(config["publication"]["csv_keys"][name], na_position="first").reset_index(drop=True)
            for name, data in tables.items()}


def validate_public_outputs(tables, config):
    """Column AND grouping/domain checks on aggregates; never a raw-row writer."""
    publication = config["publication"]
    _require(set(tables) == set(publication["csv_columns"]), "unexpected aggregate file")
    domains = {"sample": SAMPLES, "period": (1, 2),
               "band": ("0_10", "10_20", "20_30", "30_34", "over_34"),
               "region": ("0_10", "10_20", "20_plus"), "scope": ("pooled", "match")}
    for name, table in tables.items():
        _require(list(table.columns) == publication["csv_columns"][name], "aggregate column allowlist failure")
        _require(not table.duplicated(publication["csv_keys"][name]).any(), "aggregate grouping is not unique")
        expected = publication["complete_grid_row_counts"].get(name, len(MATCHES) * len(EXCLUSION_SPECS))
        _require(len(table) == expected, "aggregate cardinality mismatch")
        for key, allowed in domains.items():
            if key in table:
                _require(table[key].isin(allowed).all(), "aggregate grouping domain mismatch")
        if name == "design_qc.csv":
            pooled = table.scope == "pooled"
            _require(table.loc[pooled, "match_id"].isna().all() and pooled.sum() == 2, "pooled design grouping mismatch")
            _require(table.loc[~pooled, "match_id"].isin(MATCHES).all(), "match design grouping mismatch")
        else:
            _require(table.match_id.isin(MATCHES).all(), "aggregate match domain mismatch")
        for column in table:
            if column in {*domains, "match_id", "reason", "counting_unit", "count_class"}:
                continue
            values = pd.to_numeric(table[column], errors="raise")
            _require(not np.isinf(values.to_numpy(dtype=float)).any(), "nonfinite aggregate value")
            if column.endswith("count") or column in {"rank", "column_count", "period_count"}:
                _require(values.notna().all() and ((values >= 0) & (values % 1 == 0)).all(), "invalid aggregate count")
        if name == "exclusions.csv":
            for row in table.itertuples(index=False):
                _require(row.reason in EXCLUSION_SPECS and (row.counting_unit, row.count_class) == EXCLUSION_SPECS[row.reason], "exclusion vocabulary mismatch")


def check_support_gates(tables, source_identities_match, config):
    validate_public_outputs(tables, config)
    summary = tables["sample_summary.csv"].set_index(["match_id", "sample"])
    reconciled = True
    for match, times, primary, quality in config["population_reconciliation"]["rows"]:
        reconciled &= (int(summary.loc[(match, "primary"), "observation_count"]) == primary
                       and int(summary.loc[(match, "primary"), "unique_time_anchor_count"]) == times
                       and int(summary.loc[(match, "quality"), "observation_count"]) == quality)
    periods = tables["period_summary.csv"]
    regions = tables["quality_region_support.csv"]
    designs = tables["design_qc.csv"]
    gates = {
        "all_nine_matches": bool((summary.observation_count > 0).all()),
        "source_identities": source_identities_match is True,
        "count_reconciliation": bool(reconciled),
        "both_periods_primary_and_quality": bool((periods.observation_count > 0).all()),
        "full_rank_primary_and_quality": bool((designs["rank"] == designs.column_count).all()),
        "quality_region_times": bool((regions.unique_time_anchor_count >= 20).all()),
        "quality_region_blocks": bool((regions.temporal_block_count >= 4).all()),
    }
    return {"checks": gates, "status": STATUS_PASS if all(gates.values()) else STATUS_FAIL,
            "human_review_required": True}


def _population_digests(rows):
    result = {}
    for sample in SAMPLES:
        selected = tuple(r for r in rows if sample == "primary" or r.quality_pass)
        result[sample] = {"all_matches": observation_digest(selected),
                          "per_match": {str(m): observation_digest(r for r in selected if r.match_id == m) for m in MATCHES}}
    return result


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _validate_json_package(source_hashes, manifest, qc, hashes, config):
    """Fixed nested structures; arbitrary metadata/row dictionaries rejected."""
    def keys(value, expected):
        _require(type(value) is dict and set(value) == set(expected), "JSON schema mismatch")

    def sha(value):
        _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid provenance hash")

    keys(source_hashes, ("release_commit", "files"))
    _require(source_hashes["release_commit"] == RELEASE, "release provenance mismatch")
    files = source_hashes["files"]
    expected_paths = {t.format(m) for m in MATCHES for t in TEMPLATES}
    _require(len(files) == 27 and {f["path"] for f in files} == expected_paths, "source provenance population mismatch")
    for item in files:
        keys(item, ("path", "upstream_path", "blob_id", "sha256_before", "sha256_after"))
        path = PurePosixPath(item["upstream_path"])
        _require(not path.is_absolute() and ".." not in path.parts and path.name == item["path"], "source provenance path mismatch")
        _require(re.fullmatch(r"[0-9a-f]{40}", item["blob_id"]) is not None, "invalid blob identity")
        sha(item["sha256_before"])
        sha(item["sha256_after"])
        _require(item["sha256_before"] == item["sha256_after"], "source changed during extraction")
    keys(manifest, ("hashes", "environment", "authorization_reference", "counts", "observation_digests", "outputs"))
    expected_outputs = sorted([*config["publication"]["csv_columns"], *config["publication"]["json_artifacts"]])
    _require(manifest["outputs"] == expected_outputs, "output manifest allowlist mismatch")
    _require(manifest["hashes"] == hashes, "freeze provenance mismatch")
    for value in hashes.values():
        sha(value)
    keys(manifest["environment"], ("python", "numpy", "pandas"))
    _require(all(type(v) is str for v in manifest["environment"].values()), "invalid environment metadata")
    _require(type(manifest["authorization_reference"]) is str and bool(manifest["authorization_reference"].strip()), "missing authorization reference")
    keys(manifest["counts"], SAMPLES)
    _require(all(type(v) is int and v >= 0 for v in manifest["counts"].values()), "invalid sample counts")
    keys(manifest["observation_digests"], SAMPLES)
    for population in manifest["observation_digests"].values():
        keys(population, ("all_matches", "per_match"))
        sha(population["all_matches"])
        keys(population["per_match"], map(str, MATCHES))
        for value in population["per_match"].values():
            sha(value)
    keys(qc, ("checks", "status", "human_review_required"))
    keys(qc["checks"], ("all_nine_matches", "source_identities", "count_reconciliation", "both_periods_primary_and_quality",
                       "full_rank_primary_and_quality", "quality_region_times", "quality_region_blocks"))
    _require(all(type(v) is bool for v in qc["checks"].values()), "invalid QC flags")
    _require(qc["status"] == (STATUS_PASS if all(qc["checks"].values()) else STATUS_FAIL)
             and qc["human_review_required"] is True, "invalid QC status")
    for value in (source_hashes, manifest, qc):
        _json_bytes(value)


def _report(tables, qc):
    lines = ["# SkillCorner lateral support preflight v1", "", qc["status"], "",
             "Support-only aggregates. Human spatial-quality review and separate response authorization remain required.", "",
             "Counts are not proof of historical observation-ID equality. Detection flags do not prove coordinate accuracy.", "",
             "All nine matches are required. Twenty unique times/four period-aware blocks per quality region are fixed feasibility safeguards.", "",
             "Quality retention by sample/band is quality count divided by primary count (undefined for zero primary count).", "",
             "SkillCorner Open Data; Copyright (c) 2020 SkillCorner; MIT.", ""]
    for name, table in sorted(tables.items()):
        lines.extend([f"## {name}", "", "```csv", table.to_csv(index=False, float_format="%.17g", lineterminator="\n").rstrip(), "```", ""])
    return "\n".join(lines).encode("utf-8")


def execute_support(*, execute=False, data_dir=None, pinned_repository=None,
                    authorization_reference=None, expected_implementation_hashes=None,
                    output=None, report=None):
    """Future gated execution. Tests inject only synthetic source fixtures."""
    _require(execute is True and isinstance(authorization_reference, str) and bool(authorization_reference.strip()), "explicit support execution authorization required")
    _require(data_dir is not None and pinned_repository is not None, "explicit data and pinned repository paths required")
    config, hashes = verify_freeze()
    _require(expected_implementation_hashes == {p: hashes[p] for p in (SOURCE, TESTS)}, "reviewed source/test hashes required")
    output = Path(output) if output is not None else ROOT / config["publication"]["output_root"]
    report = Path(report) if report is not None else ROOT / config["publication"]["report"]
    _require(not output.exists() and not output.is_symlink() and not report.exists() and not report.is_symlink(), "refusing to overwrite existing support artifacts")
    _require(not report.resolve().is_relative_to(output.resolve()), "report must be outside output directory")
    before = verify_source_identity(data_dir, pinned_repository)
    observations, exclusions = [], {}
    for match in MATCHES:
        source = SupportSource(match, data_dir)
        rows, match_exclusions = extract_match_support(source)
        observations.extend(rows)
        exclusions[match] = match_exclusions
        del source, rows
    after = verify_source_identity(data_dir, pinned_repository)
    _require(before == after, "source identities changed during extraction")
    tables = aggregate_support(observations, exclusions, config)
    validate_public_outputs(tables, config)
    qc = check_support_gates(tables, True, config)
    source_hashes = {"release_commit": RELEASE, "files": [
        {"path": f["path"], "upstream_path": f["upstream_path"], "blob_id": f["blob_id"],
         "sha256_before": f["sha256"], "sha256_after": f["sha256"]} for f in before["files"]]}
    names = sorted([*tables, "source_hashes.json", "manifest.json", "hard_qc.json", "final_hashes.json"])
    manifest = {"hashes": hashes, "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
                "authorization_reference": authorization_reference,
                "counts": {"primary": len(observations), "quality": sum(r.quality_pass for r in observations)},
                "observation_digests": _population_digests(observations), "outputs": names}
    _validate_json_package(source_hashes, manifest, qc, hashes, config)
    del observations
    # Assemble and validate everything before any serialization. Only this
    # aggregate allowlist reaches the writer; no callback receives row records.
    payloads = {name: table.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8") for name, table in tables.items()}
    payloads.update({"source_hashes.json": _json_bytes(source_hashes), "manifest.json": _json_bytes(manifest), "hard_qc.json": _json_bytes(qc)})
    report_bytes = _report(tables, qc)
    final = {"artifacts": {name: hashlib.sha256(value).hexdigest() for name, value in sorted(payloads.items())},
             "report_sha256": hashlib.sha256(report_bytes).hexdigest()}
    output.mkdir(parents=True, exist_ok=False)
    for name, value in payloads.items():
        (output / name).write_bytes(value)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("xb") as handle:
        handle.write(report_bytes)
    (output / "final_hashes.json").write_bytes(_json_bytes(final))
    for name, expected in final["artifacts"].items():
        _require(_sha(output / name) == expected, "aggregate artifact hash mismatch")
    _require(_sha(report) == final["report_sha256"], "support report hash mismatch")
    # A failed gate publishes only aggregate diagnostic evidence, then fails.
    _require(qc["status"] == STATUS_PASS, "support preflight invalid; aggregate diagnosis retained")
    return qc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify-freeze", action="store_true")
    mode.add_argument("--execute-support", action="store_true")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--pinned-repository", type=Path)
    parser.add_argument("--authorization-reference")
    parser.add_argument("--source-sha256")
    parser.add_argument("--tests-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.verify_freeze:
        print(json.dumps(verify_freeze()[1], indent=2, sort_keys=True))
        return 0
    if not args.execute_support:
        parser.error("support access disabled; use --verify-freeze for data-free verification")
    try:
        result = execute_support(execute=True, data_dir=args.data_dir, pinned_repository=args.pinned_repository,
            authorization_reference=args.authorization_reference,
            expected_implementation_hashes={SOURCE: args.source_sha256, TESTS: args.tests_sha256},
            output=args.output, report=args.report)
    except (SupportError, OSError, ValueError, KeyError, TypeError):
        # Do not leak provider records or paths in tracebacks/console diagnostics.
        print(STATUS_FAIL)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
