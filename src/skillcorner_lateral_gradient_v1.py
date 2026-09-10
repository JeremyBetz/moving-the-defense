"""Frozen SkillCorner lateral-gradient v1 analysis.

Import, ``--help`` and ``--verify-freeze`` are response-free. Provider response
construction is reachable only through the explicit, separately authorized
``--execute-response`` path after source and observation identities agree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

import defensive_reorganization_spatial_value_v1_design as design
from defensive_reorganization_spatial_form_skillcorner_external import sorted_rank_ids
from infrastructure.skillcorner_spatial_form_adapter import goalward_sign
from skillcorner_lateral_gradient_support_preflight_v1 import (
    MATCHES,
    SupportObservation,
    SupportSource,
    extract_match_support,
    observation_digest,
    verify_source_identity,
)


ROOT = Path(__file__).resolve().parents[1]
NAME = "skillcorner_lateral_gradient_v1"
PROTOCOL = ROOT / f"docs/protocols/{NAME}.md"
CONFIG = ROOT / f"config/{NAME}.json"
LEDGER = ROOT / f"config/{NAME}_hashes.json"
SOURCE = ROOT / f"src/{NAME}.py"
TESTS = ROOT / f"tests/test_{NAME}.py"
DEFAULT_OUTPUT = ROOT / f"outputs/{NAME}"
DEFAULT_REPORT = ROOT / f"docs/results/{NAME}.md"
REQUIRED_COLUMNS = ("observation_id", "match_id", "period", "block_id", "z_m", "Y_m", "quality_pass")
STATUS_INVALID = "INVALID"


class LateralGradientInvalid(RuntimeError):
    """Fail-closed scientific or publication error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LateralGradientInvalid(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    def clean(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): clean(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(val) for val in item]
        if isinstance(item, (np.integer,)):
            return int(item)
        if isinstance(item, (np.floating, float)):
            number = float(item)
            _require(math.isfinite(number), "nonfinite JSON value")
            return number
        if isinstance(item, (np.bool_, bool)):
            return bool(item)
        return item
    return (json.dumps(clean(value), indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_config(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((Path(root) / CONFIG.relative_to(ROOT)).read_text(encoding="utf-8"))


def verify_freeze(root: Path = ROOT) -> dict[str, str]:
    """Verify repository identities only; never read provider data."""
    root = Path(root)
    ledger = json.loads((root / LEDGER.relative_to(ROOT)).read_text(encoding="utf-8"))
    recorded = ledger.get("frozen_artifacts_sha256", {})
    required = {
        str(PROTOCOL.relative_to(ROOT)), str(CONFIG.relative_to(ROOT)),
        str(SOURCE.relative_to(ROOT)), str(TESTS.relative_to(ROOT)),
    }
    _require(set(recorded) >= required, "incomplete response-analysis hash ledger")
    _require("src/defensive_reorganization_spatial_value_v1_design.py" in
             ledger.get("bound_response_construction_sha256", {}), "missing shared OLS identity")
    verified = {}
    for group_name in ("frozen_artifacts_sha256", "bound_support_sha256", "bound_response_construction_sha256"):
        group = ledger.get(group_name, {})
        _require(bool(group), f"missing hash-ledger group: {group_name}")
        for relative, expected in group.items():
            _require(sha(root / relative) == expected, f"frozen artifact hash mismatch: {relative}")
            verified[relative] = expected
    cfg = load_config(root)
    for key in ("manifest", "source_hashes"):
        relative = cfg["support"][f"{key}_path"]
        _require(sha(root / relative) == cfg["support"][f"{key}_sha256"], f"support {key} hash mismatch")
    return verified


def reconcile_support_observations(rows: Sequence[SupportObservation], manifest: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Require exact frozen IDs before any provider response path is evaluated."""
    rows = tuple(rows)
    _require({row.match_id for row in rows} == set(cfg["matches"]), "support match population mismatch")
    primary_by_match = {str(match): tuple(row for row in rows if row.match_id == match) for match in cfg["matches"]}
    quality_by_match = {match: tuple(row for row in selected if row.quality_pass) for match, selected in primary_by_match.items()}
    primary = observation_digest(rows)
    quality_rows = tuple(row for row in rows if row.quality_pass)
    quality = observation_digest(quality_rows)
    expected = manifest["observation_digests"]
    _require(primary == cfg["support"]["primary_digest"] == expected["primary"]["all_matches"], "primary observation digest mismatch")
    _require(quality == cfg["support"]["quality_digest"] == expected["quality"]["all_matches"], "quality observation digest mismatch")
    _require(len(rows) == cfg["support"]["primary_count"] == manifest["counts"]["primary"], "primary count mismatch")
    _require(len(quality_rows) == cfg["support"]["quality_count"] == manifest["counts"]["quality"], "quality count mismatch")
    for match in cfg["matches"]:
        key = str(match)
        _require(len(primary_by_match[key]) == cfg["support"]["per_match_counts"][key]["primary"], "per-match primary count mismatch")
        _require(len(quality_by_match[key]) == cfg["support"]["per_match_counts"][key]["quality"], "per-match quality count mismatch")
        _require(observation_digest(primary_by_match[key]) == expected["primary"]["per_match"][key], "per-match primary digest mismatch")
        _require(observation_digest(quality_by_match[key]) == expected["quality"]["per_match"][key], "per-match quality digest mismatch")
    return {"primary": primary, "quality": quality}


def _source_identities_match(actual: Mapping[str, Any], committed: Mapping[str, Any]) -> bool:
    if actual.get("release_commit") != committed.get("release_commit"):
        return False
    expected = {row["path"]: row for row in committed["files"]}
    if {row["path"] for row in actual["files"]} != set(expected):
        return False
    for row in actual["files"]:
        old = expected[row["path"]]
        for key in ("upstream_path", "git_blob_sha", "lfs_oid_sha256", "lfs_declared_size"):
            if row[key] != old[key]:
                return False
        if row["materialized_sha256"] != old["materialized_sha256_before"] or row["materialized_size"] != old["materialized_size_before"]:
            return False
    return True


def construct_y_from_rank_paths(paths: Mapping[int, float]) -> float:
    _require(set(paths) == set(range(1, 8)), "exact D1-D7 paths required")
    values = np.asarray([paths[rank] for rank in range(1, 8)], dtype=float)
    _require(np.isfinite(values).all(), "nonfinite required response")
    return float(values[:3].mean() - values[3:].mean())


def _construct_governed_response(source: SupportSource, row: SupportObservation) -> float:
    """Construct only the frozen Y field; caller must reconcile IDs first."""
    anchor, focal, period = row.anchor_provider_frame, row.focal_player_id, row.period
    attacking = source.attacking_team(anchor)
    defending = source.away_team_id if attacking == source.home_team_id else source.home_team_id
    defenders = source.active_outfield(anchor, defending)
    sign = goalward_sign(source.meta["home_team_side"], period, source.is_home(attacking))
    ranks = sorted_rank_ids(source, anchor, focal, defenders, sign, row.y_start_m)
    _require(len(ranks) == 10 and len(set(ranks)) == 10, "invalid governed defender ranks")
    relative = []
    for frame in range(anchor, anchor + 21):
        positions = np.stack([source.smooth_player(frame, player) for player in ranks])
        relative.append((10.0 * positions - positions.sum(axis=0)) / 9.0)
    paths = np.linalg.norm(np.diff(np.asarray(relative), axis=0), axis=2).sum(axis=0)
    return construct_y_from_rank_paths({rank: float(paths[rank - 1]) for rank in range(1, 8)})


def _load_execution_rows(data_dir: Path, pinned_repository: Path, cfg: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Future-only loader: identity gates precede all response construction."""
    source_identity = verify_source_identity(data_dir, pinned_repository)
    committed_sources = json.loads((ROOT / cfg["support"]["source_hashes_path"]).read_text(encoding="utf-8"))
    _require(_source_identities_match(source_identity, committed_sources), "provider source identity mismatch")
    support_rows: list[SupportObservation] = []
    sources: dict[int, SupportSource] = {}
    for match in cfg["matches"]:
        source = SupportSource(match, data_dir)
        rows, _ = extract_match_support(source)
        sources[match] = source
        support_rows.extend(rows)
    manifest = json.loads((ROOT / cfg["support"]["manifest_path"]).read_text(encoding="utf-8"))
    digests = reconcile_support_observations(support_rows, manifest, cfg)
    result = []
    for row in support_rows:
        result.append({
            "observation_id": f"{row.match_id}:{row.period}:{row.anchor_provider_frame}:{row.focal_player_id}",
            "match_id": row.match_id, "period": row.period, "block_id": row.block_id,
            "z_m": row.z_m, "Y_m": _construct_governed_response(sources[row.match_id], row),
            "quality_pass": row.quality_pass,
        })
    source_identity_after = verify_source_identity(data_dir, pinned_repository)
    _require(source_identity_after == source_identity, "provider source identity changed during response construction")
    return pd.DataFrame(result, columns=REQUIRED_COLUMNS), {"observation_digests": digests, "source_identity": source_identity}


def validate_rows(rows: pd.DataFrame, matches: Sequence[int], expected_ids: Iterable[str] | None = None) -> pd.DataFrame:
    _require(list(rows.columns) == list(REQUIRED_COLUMNS), "unexpected response-row schema")
    data = rows.copy(deep=True)
    _require(not data.observation_id.duplicated().any(), "duplicate observation identity")
    _require(set(data.match_id) == set(matches), "required match population missing")
    _require(data.period.isin([1, 2]).all() and (data.block_id >= 0).all(), "invalid temporal identity")
    _require(np.isfinite(data[["z_m", "Y_m"]].to_numpy(float)).all(), "nonfinite predictor or response")
    _require((data.z_m >= 0).all() and data.quality_pass.map(type).eq(bool).all(), "invalid predictor or quality flag")
    if expected_ids is not None:
        _require(set(data.observation_id) == set(expected_ids), "incomplete identity join")
    return data.sort_values(["match_id", "period", "block_id", "observation_id"]).reset_index(drop=True)


def fit_equal_match(rows: pd.DataFrame, matches: Sequence[int]) -> dict[str, Any]:
    data = validate_rows(rows, matches)
    beta, rank, names = design.fit_equal_match_ols(data.Y_m, data[["z_m"]], data.match_id.astype(str))
    _require(tuple(names) == tuple(sorted(map(str, matches))), "match intercept ordering mismatch")
    return {"beta_lat_m_per_m": float(beta[-1]), "coefficients": tuple(map(float, beta)), "rank": rank, "match_names": names}


def match_slopes(rows: pd.DataFrame, matches: Sequence[int]) -> pd.DataFrame:
    values = []
    for match in matches:
        group = rows.loc[rows.match_id == match]
        _require(len(group) >= 2 and float(group.z_m.var(ddof=0)) > 0, "match-specific slope is not estimable")
        slope = float(np.linalg.lstsq(np.column_stack([np.ones(len(group)), group.z_m]), group.Y_m, rcond=None)[0][-1])
        values.append({"match_id": match, "beta_lat_m_per_m": slope, "sign": "positive" if slope > 0 else "negative" if slope < 0 else "zero"})
    return pd.DataFrame(values)


def lomo_slopes(rows: pd.DataFrame, matches: Sequence[int]) -> pd.DataFrame:
    values = []
    for omitted in matches:
        retained = tuple(match for match in matches if match != omitted)
        slope = fit_equal_match(rows.loc[rows.match_id != omitted], retained)["beta_lat_m_per_m"]
        values.append({"omitted_match_id": omitted, "beta_lat_m_per_m": slope, "sign": "positive" if slope > 0 else "negative" if slope < 0 else "zero"})
    return pd.DataFrame(values)


def _resample_blocks(rows: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    pieces = []
    for (_, _), stratum in rows.groupby(["match_id", "period"], sort=True):
        blocks = np.sort(stratum.block_id.unique())
        _require(len(blocks) > 0, "empty bootstrap stratum")
        chosen = rng.choice(blocks, size=len(blocks), replace=True)
        for draw_index, block in enumerate(chosen):
            piece = stratum.loc[stratum.block_id == block].copy()
            piece["bootstrap_block_instance"] = draw_index
            # A block may be selected repeatedly. Preserve every simultaneous
            # perspective while giving replicated rows draw-local identities.
            piece["observation_id"] = piece["observation_id"].astype(str) + f"#b{draw_index}"
            pieces.append(piece)
    return pd.concat(pieces, ignore_index=True)


def paired_block_bootstrap(rows: pd.DataFrame, matches: Sequence[int], draws: int, seed: int) -> dict[str, np.ndarray]:
    data = validate_rows(rows, matches)
    rng = np.random.Generator(np.random.PCG64(seed))
    primary, quality = [], []
    for _ in range(draws):
        sampled = _resample_blocks(data, rng)
        try:
            primary_beta = fit_equal_match(sampled[list(REQUIRED_COLUMNS)], matches)["beta_lat_m_per_m"]
            q = sampled.loc[sampled.quality_pass, list(REQUIRED_COLUMNS)]
            quality_beta = fit_equal_match(q, matches)["beta_lat_m_per_m"]
        except (LateralGradientInvalid, ValueError, np.linalg.LinAlgError):
            continue
        primary.append(primary_beta)
        quality.append(quality_beta)
    return {"primary": np.asarray(primary), "quality": np.asarray(quality)}


def classify_result(primary_beta: float, ci_low: float, quality_beta: float, lomo: Sequence[float], *, valid: bool = True) -> str:
    if not valid:
        return "INVALID"
    values = np.asarray([primary_beta, ci_low, quality_beta, *lomo], dtype=float)
    _require(np.isfinite(values).all() and len(lomo) == 9, "invalid classification inputs")
    if primary_beta <= 0:
        return "NOT SUPPORTED"
    if ci_low > 0 and quality_beta > 0 and all(value > 0 for value in lomo):
        return "SUPPORTED"
    return "MIXED"


def analyze(rows: pd.DataFrame, cfg: Mapping[str, Any]) -> dict[str, Any]:
    matches = tuple(cfg["matches"])
    data = validate_rows(rows, matches)
    primary_fit = fit_equal_match(data, matches)
    quality_rows = data.loc[data.quality_pass].copy()
    quality_fit = fit_equal_match(quality_rows, matches)
    matches_table = match_slopes(data, matches)
    lomo = lomo_slopes(data, matches)
    boot = paired_block_bootstrap(data, matches, int(cfg["bootstrap"]["draws"]), int(cfg["bootstrap"]["seed"]))
    valid = len(boot["primary"])
    _require(valid == len(boot["quality"]) and valid >= int(cfg["bootstrap"]["minimum_valid_paired_draws"]), "insufficient valid paired bootstrap draws")
    low, high = np.quantile(boot["primary"], [0.025, 0.975], method="linear")
    qlow, qhigh = np.quantile(boot["quality"], [0.025, 0.975], method="linear")
    status = classify_result(primary_fit["beta_lat_m_per_m"], low, quality_fit["beta_lat_m_per_m"], lomo.beta_lat_m_per_m.tolist())
    return {
        "primary": {"beta": primary_fit["beta_lat_m_per_m"], "low": float(low), "high": float(high)},
        "quality": {"beta": quality_fit["beta_lat_m_per_m"], "low": float(qlow), "high": float(qhigh)},
        "match_estimates": matches_table, "lomo_estimates": lomo,
        "valid_bootstrap_draws": valid, "classification": status,
        "fit_qc": {"primary_full_rank": primary_fit["rank"] == len(matches) + 1,
                   "quality_full_rank": quality_fit["rank"] == len(matches) + 1},
        "counts": {"primary": len(data), "quality": len(quality_rows), "per_match": {
            str(match): {"primary": int((data.match_id == match).sum()),
                         "quality": int((quality_rows.match_id == match).sum())}
            for match in matches}},
    }


def _csv_bytes(frame: pd.DataFrame, columns: Sequence[str]) -> bytes:
    _require(list(frame.columns) == list(columns), "aggregate output schema mismatch")
    return frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")


def build_payloads(result: Mapping[str, Any], provenance: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, bytes]:
    valid = result["valid_bootstrap_draws"]
    primary = result["primary"]; quality = result["quality"]
    pooled = pd.DataFrame([{"sample": "primary", "beta_lat_m_per_m": primary["beta"], "ci_low_m_per_m": primary["low"], "ci_high_m_per_m": primary["high"], "ten_m_contrast_m": 10 * primary["beta"], "valid_bootstrap_draws": valid, "classification": result["classification"]}])
    quality_table = pd.DataFrame([{"sample": "majority_detected", "beta_lat_m_per_m": quality["beta"], "ci_low_m_per_m": quality["low"], "ci_high_m_per_m": quality["high"], "ten_m_contrast_m": 10 * quality["beta"], "valid_bootstrap_draws": valid}])
    schemas = cfg["outputs"]["schemas"]
    payloads = {
        "pooled_estimate.csv": _csv_bytes(pooled, schemas["pooled_estimate.csv"]),
        "quality_estimate.csv": _csv_bytes(quality_table, schemas["quality_estimate.csv"]),
        "match_estimates.csv": _csv_bytes(result["match_estimates"], schemas["match_estimates.csv"]),
        "lomo_estimates.csv": _csv_bytes(result["lomo_estimates"], schemas["lomo_estimates.csv"]),
    }
    payloads["bootstrap_summary.json"] = _json_bytes({"draws_requested": cfg["bootstrap"]["draws"], "valid_paired_draws": valid, "seed": cfg["bootstrap"]["seed"], "prng": "PCG64"})
    expected_digests = {key: cfg["support"][f"{key}_digest"] for key in ("primary", "quality")}
    expected_counts = _expected_counts(cfg)
    payloads["manifest.json"] = _json_bytes({"status": "STAGING_QC_PASSED_NOT_AUTHORITATIVE", "classification": result["classification"], "counts": result["counts"], "support_digests": provenance["observation_digests"], "authorization_reference": provenance["authorization_reference"], "frozen_hashes": provenance["frozen_hashes"], "outputs": cfg["outputs"]["files"], "source_ledger_sha256": cfg["support"]["source_hashes_sha256"]})
    payloads["hard_qc.json"] = _json_bytes({"status": "STAGING_QC_PASSED_NOT_AUTHORITATIVE", "exact_support_identity": provenance["observation_digests"] == expected_digests and result["counts"] == expected_counts, "exact_source_identity": provenance["frozen_hashes"].get(cfg["support"]["source_hashes_path"]) == cfg["support"]["source_hashes_sha256"], "all_nine_matches": set(result["match_estimates"].match_id) == set(cfg["matches"]), "full_rank": result["fit_qc"]["primary_full_rank"] and result["fit_qc"]["quality_full_rank"], "valid_paired_draws": valid, "source_rows_absent": all(list(pd.read_csv(io.BytesIO(payloads[name])).columns) == list(columns) for name, columns in schemas.items())})
    return payloads


def _expected_counts(cfg: Mapping[str, Any]) -> dict[str, Any]:
    return {"primary": cfg["support"]["primary_count"], "quality": cfg["support"]["quality_count"],
            "per_match": cfg["support"]["per_match_counts"]}


def _expected_frozen_hashes() -> dict[str, str]:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    return {path: digest for group in ("frozen_artifacts_sha256", "bound_support_sha256",
                                      "bound_response_construction_sha256")
            for path, digest in ledger[group].items()}


def _keys(value: Any, expected: Iterable[str], name: str) -> None:
    _require(type(value) is dict and set(value) == set(expected), f"unexpected structural fields in {name}")


def _read_json(value: bytes, name: str, cfg: Mapping[str, Any]) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, item in pairs:
            _require(key not in result, f"duplicate JSON key in {name}")
            result[key] = item
        return result
    def invalid_constant(value):
        raise LateralGradientInvalid(f"nonfinite JSON constant in {name}")
    try:
        result = json.loads(value.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, UnicodeError) as exc:
        raise LateralGradientInvalid(f"forbidden or malformed JSON in {name}") from exc
    _keys(result, cfg["outputs"]["json_keys"][name], name)
    # Finite JSON syntax can still overflow, e.g. 1e999.
    def finite(item):
        if isinstance(item, dict):
            for child in item.values(): finite(child)
        elif isinstance(item, list):
            for child in item: finite(child)
        elif isinstance(item, float):
            _require(math.isfinite(item), f"nonfinite JSON value in {name}")
    finite(result)
    return result


def _integer(value: Any, name: str) -> None:
    _require(type(value) is int and value >= 0, f"invalid integer {name}")


def _sign(value: float) -> str:
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def validate_public_payloads(payloads: Mapping[str, bytes], cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Allow only the frozen aggregate structure, never arbitrary nested data."""
    expected = set(cfg["outputs"]["files"]) - {"reproduction.json", "final_hashes.json"}
    _require(set(payloads) == expected, "unexpected aggregate package")
    for name, value in payloads.items():
        _require(len(value) < 10 * 1024 * 1024, "aggregate output exceeds publication limit")
    tables = {}
    text_fields = {"sample", "classification", "sign"}
    for name, columns in cfg["outputs"]["schemas"].items():
        records = list(csv.reader(io.StringIO(payloads[name].decode("utf-8"))))
        _require(bool(records) and records[0] == columns and all(len(row) == len(columns) for row in records[1:]), f"aggregate output schema mismatch: {name}")
        expected_n = cfg["outputs"]["csv_rows"][name]
        _require(len(records) - 1 == expected_n, f"aggregate row cardinality mismatch: {name}")
        frame = pd.read_csv(io.BytesIO(payloads[name]), float_precision="round_trip")
        for column in set(columns) - text_fields:
            try:
                values = pd.to_numeric(frame[column], errors="raise").to_numpy(float)
            except (ValueError, TypeError) as exc:
                raise LateralGradientInvalid(f"invalid numeric column in {name}") from exc
            _require(np.isfinite(values).all(), f"nonfinite numeric column in {name}")
        if name in ("match_estimates.csv", "lomo_estimates.csv"):
            identity = "match_id" if name.startswith("match") else "omitted_match_id"
            _require(not frame[identity].duplicated().any() and set(frame[identity]) == set(cfg["matches"]), f"aggregate match identity mismatch: {name}")
            _require(frame.sign.tolist() == [_sign(x) for x in frame.beta_lat_m_per_m], f"sign mismatch: {name}")
        tables[name] = frame
    primary = tables["pooled_estimate.csv"].iloc[0]
    quality = tables["quality_estimate.csv"].iloc[0]
    _require(primary["sample"] == "primary" and quality["sample"] == "majority_detected", "sample status mismatch")
    for row in (primary, quality):
        _require(row.ci_low_m_per_m <= row.ci_high_m_per_m, "reversed interval")
        _require(row.ten_m_contrast_m == 10 * row.beta_lat_m_per_m, "translation mismatch")
        _require(float(row.valid_bootstrap_draws).is_integer(), "noninteger bootstrap count")
    valid = int(primary.valid_bootstrap_draws)
    _require(valid == quality.valid_bootstrap_draws and cfg["bootstrap"]["minimum_valid_paired_draws"] <= valid <= cfg["bootstrap"]["draws"], "invalid paired bootstrap count")
    classification = classify_result(primary.beta_lat_m_per_m, primary.ci_low_m_per_m, quality.beta_lat_m_per_m, tables["lomo_estimates.csv"].beta_lat_m_per_m.tolist())
    _require(primary.classification == classification, "classification mismatch")
    manifest = _read_json(payloads["manifest.json"], "manifest.json", cfg)
    qc = _read_json(payloads["hard_qc.json"], "hard_qc.json", cfg)
    boot = _read_json(payloads["bootstrap_summary.json"], "bootstrap_summary.json", cfg)
    _require(manifest["status"] == qc["status"] == "STAGING_QC_PASSED_NOT_AUTHORITATIVE", "invalid staging status")
    _require(manifest["classification"] == classification, "manifest classification mismatch")
    _keys(manifest["counts"], ("primary", "quality", "per_match"), "counts")
    _keys(manifest["counts"]["per_match"], map(str, cfg["matches"]), "per-match counts")
    for sample in ("primary", "quality"):
        _integer(manifest["counts"][sample], sample)
    for counts in manifest["counts"]["per_match"].values():
        _keys(counts, ("primary", "quality"), "match counts")
        for key, value in counts.items(): _integer(value, key)
        _require(0 < counts["quality"] <= counts["primary"], "invalid quality count")
    _require(manifest["counts"] == _expected_counts(cfg), "support counts mismatch")
    for sample in ("primary", "quality"):
        _require(sum(v[sample] for v in manifest["counts"]["per_match"].values()) == manifest["counts"][sample], "inconsistent total count")
    _require(manifest["support_digests"] == {key: cfg["support"][f"{key}_digest"] for key in ("primary", "quality")}, "support lineage mismatch")
    _require(manifest["source_ledger_sha256"] == cfg["support"]["source_hashes_sha256"], "source lineage mismatch")
    _require(manifest["frozen_hashes"] == _expected_frozen_hashes(), "frozen dependency lineage mismatch")
    _require(manifest["outputs"] == cfg["outputs"]["files"], "output inventory mismatch")
    _require(type(manifest["authorization_reference"]) is str and bool(manifest["authorization_reference"].strip()), "missing authorization metadata")
    for key in ("draws_requested", "valid_paired_draws", "seed"):
        _integer(boot[key], key)
    _require(boot == {"draws_requested": cfg["bootstrap"]["draws"], "valid_paired_draws": valid, "seed": cfg["bootstrap"]["seed"], "prng": "PCG64"}, "bootstrap metadata mismatch")
    _integer(qc["valid_paired_draws"], "QC draws")
    _require(qc["valid_paired_draws"] == valid and all(qc[key] is True for key in set(qc) - {"status", "valid_paired_draws"}), "hard QC mismatch")
    return {"tables": tables, "manifest": manifest}


def _write_package(path: Path, payloads: Mapping[str, bytes]) -> None:
    path.mkdir(parents=True, exist_ok=False)
    for name, value in payloads.items():
        (path / name).write_bytes(value)


def _report_bytes(checked: Mapping[str, Any], cfg: Mapping[str, Any]) -> bytes:
    manifest, tables = checked["manifest"], checked["tables"]
    primary, quality = tables["pooled_estimate.csv"].iloc[0], tables["quality_estimate.csv"].iloc[0]
    matches, lomo = tables["match_estimates.csv"], tables["lomo_estimates.csv"]
    lines = ["# SkillCorner Lateral Gradient v1", "", cfg["report_lineage"], "",
             "Frozen hypothesis: beta_lat > 0 for |y_c(t-2)| under match-intercept equal-total-match-weight OLS.", "",
             f"**Classification:** {manifest['classification']}", "",
             f"Primary beta_lat: {primary.beta_lat_m_per_m:.6f} m/m; 95% interval [{primary.ci_low_m_per_m:.6f}, {primary.ci_high_m_per_m:.6f}].",
             f"Majority-detected beta_lat: {quality.beta_lat_m_per_m:.6f} m/m; 95% interval [{quality.ci_low_m_per_m:.6f}, {quality.ci_high_m_per_m:.6f}]; sign: {_sign(quality.beta_lat_m_per_m)}.",
             f"Positive match slopes: {int((matches.sign == 'positive').sum())}/9. Match slopes are descriptive, not independent replications.", "",
             "## Leave-one-match-out estimates", ""]
    lines.extend(f"- Omit {int(row.omitted_match_id)}: {row.beta_lat_m_per_m:.6f} m/m ({row.sign})." for row in lomo.itertuples())
    lines.extend(["", "## Population and provenance", "",
                  f"Primary observations: {manifest['counts']['primary']}; quality observations: {manifest['counts']['quality']}.",
                  f"Valid paired bootstrap draws: {int(primary.valid_bootstrap_draws)}/{cfg['bootstrap']['draws']}.",
                  f"Support manifest: `{cfg['support']['manifest_path']}`; SHA-256 `{cfg['support']['manifest_sha256']}`.",
                  f"Pinned source ledger: `{cfg['support']['source_hashes_path']}`; SHA-256 `{manifest['source_ledger_sha256']}`."])
    for match, counts in manifest["counts"]["per_match"].items():
        lines.append(f"- Match {match}: primary {counts['primary']}; quality {counts['quality']}.")
    for sample, digest in manifest["support_digests"].items():
        lines.append(f"- {sample} observation digest: `{digest}`.")
    for path, digest in sorted(manifest["frozen_hashes"].items()):
        lines.append(f"- `{path}`: `{digest}`.")
    lines.extend(["", "## Measurement and interpretation boundaries", "",
                  "Coordinates include detected and provider-extrapolated positions; direct-detection retention varies by match. The aggregate support audit did not establish coordinate accuracy. The majority-detected sensitivity is not ground truth.",
                  "The interval is conditional on these nine matches, the frozen 60-second block convention, and this measurement process. Finite out-of-pitch starts remain retained; the sparse tail beyond 34 m is not interpreted.",
                  "This is an observational spatial association, not causation, influence, marking, tactical effectiveness, or value. It does not validate the IDSSE heatmap itself. No post-result model, filter, or diagnostic changes are authorized.", ""])
    return "\n".join(lines).encode("utf-8")


def _report_path(output: Path, report: Path) -> str:
    return Path(os.path.relpath(report.resolve(), output.resolve())).as_posix()


def _digest_map(payloads: Mapping[str, bytes]) -> dict[str, str]:
    return {name: hashlib.sha256(value).hexdigest() for name, value in sorted(payloads.items())}


def _validate_authoritative(output: Path, cfg: Mapping[str, Any], recorded: Mapping[str, Any], report: Path) -> dict[str, str]:
    """Validate actual final paths before (and after) publishing authority."""
    _keys(recorded, cfg["outputs"]["json_keys"]["final_hashes.json"], "final authority")
    _require(recorded["closure_status"] == "FINAL_PACKAGE_VALID" and recorded["self_hash_excluded"] is True, "invalid final authority")
    expected = set(cfg["outputs"]["files"]) - {"final_hashes.json"}
    _keys(recorded["artifacts_sha256"], expected, "final artifact identities")
    _require({p.name for p in output.iterdir()} in (expected, expected | {"final_hashes.json"}), "unexpected authoritative file set")
    _require(not output.is_symlink() and not report.is_symlink() and report.is_file(), "unsafe authoritative path")
    for name in expected:
        _require(not (output / name).is_symlink() and (output / name).is_file(), "unsafe authoritative artifact")
        _require((output / name).stat().st_size < 10 * 1024 * 1024, "aggregate output exceeds publication limit")
    payloads = {name: (output / name).read_bytes() for name in expected}
    base = {name: value for name, value in payloads.items() if name != "reproduction.json"}
    checked = validate_public_payloads(base, cfg)
    reproduction = _read_json(payloads["reproduction.json"], "reproduction.json", cfg)
    _require(reproduction["status"] == "DETERMINISTIC_REPRODUCTION_PASSED" and reproduction["byte_identical"] is True, "invalid reproduction status")
    _require(reproduction["authorization_reference"] == checked["manifest"]["authorization_reference"], "authorization metadata mismatch")
    report_bytes = _report_bytes(checked, cfg)
    expected_staging = _digest_map({**base, "report.md": report_bytes})
    _require(reproduction["primary_staging_sha256"] == reproduction["reproduction_staging_sha256"] == expected_staging, "staging hash mismatch")
    expected_report = {"path": _report_path(output, report), "sha256": hashlib.sha256(report_bytes).hexdigest()}
    _require(reproduction["report_metadata"] == expected_report, "reproduction report identity mismatch")
    _require(recorded["report_path"] == expected_report["path"] and recorded["report_sha256"] == expected_report["sha256"], "final report path/hash mismatch")
    _require(report.read_bytes() == report_bytes and sha(report) == recorded["report_sha256"], "final report content/hash mismatch")
    actual = {name: sha(output / name) for name in sorted(expected)}
    _require(actual == recorded["artifacts_sha256"], "final authoritative hash mismatch")
    return actual


def close_reproduced_package(primary: Mapping[str, bytes], rerun: Mapping[str, bytes], output: Path, report: Path, cfg: Mapping[str, Any], authorization_reference: str) -> dict[str, Any]:
    """Promote pending files, validate final paths, then publish authority last."""
    output, report = Path(output), Path(report)
    _require(not output.exists() and not output.is_symlink() and not report.exists() and not report.is_symlink(), "refusing to overwrite authoritative result")
    _require(not report.resolve().is_relative_to(output.resolve()), "report must be outside package directory")
    checked = [validate_public_payloads(p, cfg) for p in (primary, rerun)]
    _require(all(item["manifest"]["authorization_reference"] == authorization_reference for item in checked), "authorization metadata mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    # Keep isolated staging on failure as diagnosis evidence. No row data enter it.
    temporary = Path(tempfile.mkdtemp(prefix=".lateral-staging-", dir=output.parent))
    staged_runs = []
    for name, payload, validated in zip(("primary", "reproduction"), (primary, rerun), checked):
        run = temporary / name
        _write_package(run, {**payload, "report.md": _report_bytes(validated, cfg)})
        actual = {p.name: p.read_bytes() for p in run.iterdir()}
        validate_public_payloads({k: v for k, v in actual.items() if k != "report.md"}, cfg)
        staged_runs.append(actual)
    _require(staged_runs[0] == staged_runs[1], "deterministic reproduction failed")
    report_bytes = staged_runs[0]["report.md"]
    report_metadata = {"path": _report_path(output, report), "sha256": hashlib.sha256(report_bytes).hexdigest()}
    reproduction = _json_bytes({"status": "DETERMINISTIC_REPRODUCTION_PASSED", "authorization_reference": authorization_reference, "primary_staging_sha256": _digest_map(staged_runs[0]), "reproduction_staging_sha256": _digest_map(staged_runs[1]), "byte_identical": True, "report_metadata": report_metadata})
    complete = {**primary, "reproduction.json": reproduction}
    final = {"closure_status": "FINAL_PACKAGE_VALID", "self_hash_excluded": True,
             "artifacts_sha256": _digest_map(complete), "report_path": report_metadata["path"], "report_sha256": report_metadata["sha256"]}
    pending = temporary / "pending"
    _write_package(pending, complete)
    # Validate the staged package using its own physical report location.
    staged_report = temporary / "primary" / "report.md"
    staging_record = dict(final, report_path=_report_path(pending, staged_report))
    staged_reproduction = dict(_read_json(reproduction, "reproduction.json", cfg), report_metadata={"path": staging_record["report_path"], "sha256": report_metadata["sha256"]})
    (pending / "reproduction.json").write_bytes(_json_bytes(staged_reproduction))
    staging_record["artifacts_sha256"] = {name: sha(pending / name) for name in complete}
    _validate_authoritative(pending, cfg, staging_record, staged_report)
    (pending / "reproduction.json").write_bytes(reproduction)
    _require({name: sha(pending / name) for name in complete} == final["artifacts_sha256"], "final staging hash mismatch")
    # Exclusive report creation; existing authoritative files are never replaced.
    with report.open("xb") as handle:
        handle.write(report_bytes)
    _require(not output.exists() and not output.is_symlink(), "refusing to overwrite authoritative result")
    os.replace(pending, output)
    marker = output / "final_hashes.json"
    try:
        _validate_authoritative(output, cfg, final, report)
        candidate = temporary / "final_hashes.json"
        candidate.write_bytes(_json_bytes(final))
        os.replace(candidate, marker)
        validate_final_hashes(output, cfg, report)
        # Successful staging contains aggregates only; remove exact owned files.
        # Cleanup failure is also fail-closed: the exception handler revokes authority.
        for run in (temporary / "primary", temporary / "reproduction"):
            for path in run.iterdir(): path.unlink()
            run.rmdir()
        temporary.rmdir()
    except BaseException:
        # Only our newly published marker is removed; pending evidence remains.
        if marker.exists() or marker.is_symlink():
            marker.unlink()
        raise
    return final


def validate_final_hashes(output: Path, cfg: Mapping[str, Any], report: Path | None = None) -> dict[str, str]:
    output = Path(output)
    _require(not (output / "final_hashes.json").is_symlink(), "unsafe final authority")
    recorded = _read_json((output / "final_hashes.json").read_bytes(), "final_hashes.json", cfg)
    _require(type(recorded["report_path"]) is str and not Path(recorded["report_path"]).is_absolute(), "invalid report path")
    actual_report = Path(report) if report is not None else output / recorded["report_path"]
    return _validate_authoritative(output, cfg, recorded, actual_report)


def execute_response(*, execute: bool = False, data_dir: Path | None = None, pinned_repository: Path | None = None, authorization_reference: str = "", expected_implementation_hashes: Mapping[str, str] | None = None, output: Path = DEFAULT_OUTPUT, report: Path = DEFAULT_REPORT) -> dict[str, Any]:
    """Future explicit gate. This function is not invoked during the freeze."""
    _require(execute is True and bool(authorization_reference.strip()), "explicit response execution authorization required")
    _require(data_dir is not None and pinned_repository is not None, "explicit provider paths required")
    frozen = verify_freeze()
    expected = {str(SOURCE.relative_to(ROOT)): frozen[str(SOURCE.relative_to(ROOT))], str(TESTS.relative_to(ROOT)): frozen[str(TESTS.relative_to(ROOT))]}
    _require(expected_implementation_hashes == expected, "reviewed source/test hashes required")
    _require(not Path(output).exists() and not Path(report).exists(), "refusing to overwrite authoritative result")
    cfg = load_config()
    primary_rows, primary_provenance = _load_execution_rows(Path(data_dir), Path(pinned_repository), cfg)
    rerun_rows, rerun_provenance = _load_execution_rows(Path(data_dir), Path(pinned_repository), cfg)
    _require(primary_provenance["observation_digests"] == rerun_provenance["observation_digests"], "rerun support identity mismatch")
    base = {"authorization_reference": authorization_reference, "frozen_hashes": frozen, "observation_digests": primary_provenance["observation_digests"]}
    primary = build_payloads(analyze(primary_rows, cfg), base, cfg)
    rerun = build_payloads(analyze(rerun_rows, cfg), base, cfg)
    return close_reproduced_package(primary, rerun, Path(output), Path(report), cfg, authorization_reference)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-freeze", action="store_true")
    modes.add_argument("--execute-response", action="store_true")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--pinned-repository", type=Path)
    parser.add_argument("--authorization-reference", default="")
    parser.add_argument("--source-sha256")
    parser.add_argument("--tests-sha256")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    if args.verify_freeze:
        print(json.dumps(verify_freeze(), indent=2, sort_keys=True)); return 0
    if not args.execute_response:
        parser.error("response access disabled; use --verify-freeze for data-free verification")
    try:
        result = execute_response(execute=True, data_dir=args.data_dir, pinned_repository=args.pinned_repository, authorization_reference=args.authorization_reference, expected_implementation_hashes={str(SOURCE.relative_to(ROOT)): args.source_sha256, str(TESTS.relative_to(ROOT)): args.tests_sha256}, output=args.output, report=args.report)
    except (LateralGradientInvalid, OSError, ValueError, KeyError, TypeError):
        print(STATUS_INVALID); return 1
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
