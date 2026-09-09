"""Frozen SkillCorner lateral-gradient v1 analysis.

Import, ``--help`` and ``--verify-freeze`` are response-free. Provider response
construction is reachable only through the explicit, separately authorized
``--execute-response`` path after source and observation identities agree.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import platform
import tempfile
from collections import Counter
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
    for group_name in ("frozen_artifacts_sha256", "bound_support_sha256", "bound_response_construction_sha256"):
        group = ledger.get(group_name, {})
        _require(bool(group), f"missing hash-ledger group: {group_name}")
        for relative, expected in group.items():
            _require(sha(root / relative) == expected, f"frozen artifact hash mismatch: {relative}")
    cfg = load_config(root)
    for key in ("manifest", "source_hashes"):
        relative = cfg["support"][f"{key}_path"]
        _require(sha(root / relative) == cfg["support"][f"{key}_sha256"], f"support {key} hash mismatch")
    return recorded


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
        "counts": {"primary": len(data), "quality": len(quality_rows)},
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
    payloads["manifest.json"] = _json_bytes({"status": "STAGING_QC_PASSED_NOT_AUTHORITATIVE", "classification": result["classification"], "counts": result["counts"], "support_digests": provenance["observation_digests"], "authorization_reference": provenance["authorization_reference"], "frozen_hashes": provenance["frozen_hashes"], "outputs": cfg["outputs"]["files"]})
    payloads["hard_qc.json"] = _json_bytes({"status": "STAGING_QC_PASSED_NOT_AUTHORITATIVE", "exact_support_identity": True, "exact_source_identity": True, "all_nine_matches": True, "full_rank": True, "valid_paired_draws": valid, "source_rows_absent": True})
    return payloads


def validate_public_payloads(payloads: Mapping[str, bytes], cfg: Mapping[str, Any]) -> None:
    expected = set(cfg["outputs"]["files"]) - {"reproduction.json", "final_hashes.json"}
    _require(set(payloads) == expected, "unexpected aggregate package")
    forbidden = tuple(cfg["outputs"]["forbidden_serialized_content"])
    for name, value in payloads.items():
        _require(len(value) < 10 * 1024 * 1024, "aggregate output exceeds publication limit")
        lowered = value.decode("utf-8").lower()
        _require(not any(token.lower() in lowered for token in forbidden), f"forbidden serialized field in {name}")


def _write_package(path: Path, payloads: Mapping[str, bytes]) -> None:
    path.mkdir(parents=True, exist_ok=False)
    for name, value in payloads.items():
        (path / name).write_bytes(value)


def close_reproduced_package(primary: Mapping[str, bytes], rerun: Mapping[str, bytes], output: Path, report: Path, cfg: Mapping[str, Any], authorization_reference: str) -> dict[str, Any]:
    """Publish only after byte-identical isolated staging payloads."""
    _require(not output.exists() and not output.is_symlink() and not report.exists() and not report.is_symlink(), "refusing to overwrite authoritative result")
    validate_public_payloads(primary, cfg); validate_public_payloads(rerun, cfg)
    _require(primary == rerun, "deterministic reproduction failed")
    with tempfile.TemporaryDirectory(prefix="skillcorner-lateral-gradient-close-") as tmp:
        staging = Path(tmp) / "finalized"
        reproduction = _json_bytes({"status": "DETERMINISTIC_REPRODUCTION_PASSED", "authorization_reference": authorization_reference, "primary_staging_sha256": {name: hashlib.sha256(value).hexdigest() for name, value in sorted(primary.items())}, "reproduction_staging_sha256": {name: hashlib.sha256(value).hexdigest() for name, value in sorted(rerun.items())}, "byte_identical": True})
        complete = dict(primary); complete["reproduction.json"] = reproduction
        manifest = json.loads(primary["manifest.json"])
        pooled = pd.read_csv(io.BytesIO(primary["pooled_estimate.csv"])).iloc[0]
        report_bytes = (
            "# SkillCorner Lateral Gradient v1\n\n"
            f"**Classification:** {manifest['classification']}\n\n"
            f"Primary beta: {pooled['beta_lat_m_per_m']:.6f} m/m "
            f"(95% interval [{pooled['ci_low_m_per_m']:.6f}, {pooled['ci_high_m_per_m']:.6f}]).\n\n"
            "This is an observational within-match lateral association. The majority-detected "
            "sample is a required measurement-quality sensitivity, not ground truth. The interval "
            "is conditional on these nine matches and this measurement process.\n"
        ).encode("utf-8")
        final = {
            "closure_status": "FINAL_PACKAGE_VALID", "self_hash_excluded": True,
            "artifacts_sha256": {name: hashlib.sha256(value).hexdigest() for name, value in sorted(complete.items())},
            "report_path": cfg["outputs"]["report"], "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        }
        complete["final_hashes.json"] = _json_bytes(final)
        _write_package(staging, complete)
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("xb") as handle:
            handle.write(report_bytes)
        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, output)
    validate_final_hashes(output, cfg, report)
    return final


def validate_final_hashes(output: Path, cfg: Mapping[str, Any], report: Path | None = None) -> dict[str, str]:
    recorded = json.loads((output / "final_hashes.json").read_text(encoding="utf-8"))
    expected = set(cfg["outputs"]["files"]) - {"final_hashes.json"}
    _require(recorded.get("closure_status") == "FINAL_PACKAGE_VALID" and recorded.get("self_hash_excluded") is True, "invalid final authority")
    _require(set(recorded.get("artifacts_sha256", {})) == expected, "unexpected final artifact set")
    actual = {name: sha(output / name) for name in sorted(expected)}
    _require(actual == recorded["artifacts_sha256"], "final authoritative hash mismatch")
    if report is not None:
        _require(recorded.get("report_path") == cfg["outputs"]["report"] and sha(report) == recorded.get("report_sha256"), "final report hash mismatch")
    return actual


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
