"""Gated execution for the frozen ten-match SkillCorner replication.

`preflight` is response-blind. Only `run`, after every frozen identity and
authorization gate passes, may call the inherited response constructor.
Published files are compact aggregates; provider and observation rows remain
in memory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_reorganization_spatial_form_skillcorner_external as inherited  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/skillcorner_additional_directional_replication_v1.md"
CONFIG = ROOT / "config/skillcorner_additional_directional_replication_v1.json"
LEDGER = ROOT / "config/skillcorner_additional_directional_replication_v1_hashes.json"
PREFLIGHT_OUTPUT = ROOT / "outputs/skillcorner_additional_directional_support_preflight_v1"
OUTPUT = ROOT / "outputs/skillcorner_additional_directional_replication_v1"
FINAL_MARKER = "FINAL_PACKAGE_VALID.json"

FORMAL_MATCHES = (
    1874553, 1927964, 1959846, 1986691, 1996436,
    2006363, 2007448, 2007721, 2010085, 2016236,
)
ORIGINAL_MATCHES = (
    1886347, 1899585, 1925299, 1996435, 2006229,
    2011166, 2013725, 2015213, 2017461,
)
EXCLUDED_MATCH = 1953632
SOURCE_COMMIT = "02a396ffd09b283c9f092fdedeff11da6d535b66"
SOURCE_TREE = "44fd5081d0e6a441dbafadd12c51d6ffca8ab98b"

CSV_SCHEMAS = {
    "primary_contrast.csv": ("classification", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "five_m_translation_m", "ci_low", "ci_high", "valid_bootstrap_replicates"),
    "per_match_coefficients.csv": ("match_id", "eligible_rows", "eligible_anchors", "model_rank", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "positive_contrast"),
    "leave_one_match_out.csv": ("heldout_match_id", "training_rows", "model_rank", "outward_minus_goalward_m_per_m"),
    "trim_sensitivity.csv": ("rows_retained", "retained_proportion", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "model_rank"),
    "quality_sensitivity.csv": ("rows", "anchors", "matches", "full_rank", "model_rank", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m"),
    "sample_summary.csv": ("match_id", "candidate_anchors", "retained_anchors", "retained_rows", "period_1_anchors", "period_2_anchors", "majority_detected_rows"),
    "provider_equivalence.csv": ("match_id", "pass"),
}
ROW_COUNTS = {
    "primary_contrast.csv": 1,
    "per_match_coefficients.csv": 10,
    "leave_one_match_out.csv": 10,
    "trim_sensitivity.csv": 1,
    "quality_sensitivity.csv": 1,
    "sample_summary.csv": 10,
    "provider_equivalence.csv": 10,
}
JSON_KEYS = {
    "result.json": {"classification", "sample", "primary", "bootstrap", "trim", "quality_sensitivity", "classification_criteria"},
    "hard_qc.json": {"status", "checks"},
    "classification_criteria.json": {"valid_execution", "positive_matches", "valid_matches", "positive_match_percent", "minimum_positive_matches_required", "trimmed_to_full_absolute_ratio", "quality_to_full_absolute_ratio", "gates"},
    "manifest.json": {"status", "authorization_reference", "protocol_sha256", "configuration_sha256", "freeze_ledger_sha256", "implementation_sha256", "tests_sha256", "source_commit", "source_tree", "formal_matches", "bootstrap_seed", "bootstrap_replicates", "classification", "preflight_lineage", "publication_policy"},
}
HARD_QC_KEYS = {
    "exact_ten_matches", "pooled_full_rank", "per_match_full_rank",
    "lomo_full_rank", "bootstrap_valid_at_least_1900",
    "unique_observation_ids", "finite_response_and_design",
    "aggregate_outputs_only",
}
CRITERIA_KEYS = {
    "valid_execution", "positive_matches", "valid_matches",
    "positive_match_percent", "minimum_positive_matches_required",
    "trimmed_to_full_absolute_ratio", "quality_to_full_absolute_ratio", "gates",
}
CRITERIA_GATE_KEYS = {
    "at_least_8_valid_matches", "pooled_contrast_strictly_positive",
    "bootstrap_95_percent_interval_strictly_positive",
    "at_least_70_percent_match_contrasts_positive",
    "all_leave_one_match_out_contrasts_positive",
    "trim_positive_and_50_to_150_percent_magnitude",
    "quality_full_rank_positive_and_50_to_150_percent_magnitude",
}
FORBIDDEN_KEYS = {
    "observation_id", "observation_ids", "timestamp", "timestamps",
    "coordinate", "coordinates", "x_m", "y_m", "player_id", "player_ids",
    "team_id", "team_ids", "anchor_frame", "anchor_frames", "anchor_time",
    "anchor_times", "individual_response", "individual_responses", "prediction",
    "predictions", "residual", "residuals", "rank_row", "rank_rows",
}
GOVERNED_FILES = tuple(CSV_SCHEMAS) + tuple(JSON_KEYS) + ("result_report.md",)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            raise RuntimeError("nonfinite value cannot be serialized")
        return number
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"nonfinite JSON: {token}")))


def verify_hash_ledger() -> dict[str, str]:
    ledger = read_json(LEDGER)
    if set(ledger) != {"schema_version", "files"} or ledger["schema_version"] != "1.0.0":
        raise RuntimeError("invalid freeze ledger schema")
    actual: dict[str, str] = {}
    for relative, expected in ledger["files"].items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing frozen file: {relative}")
        actual[relative] = sha256(path)
        if actual[relative] != expected:
            raise RuntimeError(f"frozen hash mismatch: {relative}")
    return actual


def require_clean_committed_freeze() -> None:
    for relative in read_json(LEDGER)["files"]:
        check = subprocess.run(["git", "cat-file", "-e", f"HEAD:{relative}"], cwd=ROOT, capture_output=True)
        if check.returncode:
            raise RuntimeError(f"frozen file is not committed at HEAD: {relative}")
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    if status:
        raise RuntimeError("run requires a clean committed worktree")


def verify_preflight_lineage() -> dict[str, Any]:
    config = read_json(CONFIG)
    lineage = config["preflight_lineage"]
    for key in ("protocol", "config", "inventory", "manifest", "source_ledger", "final_hashes"):
        path = ROOT / lineage[key]
        if sha256(path) != lineage[f"{key}_sha256"]:
            raise RuntimeError(f"preflight lineage mismatch: {key}")
    manifest = read_json(ROOT / lineage["manifest"])
    if manifest["qc"]["status"] != lineage["required_status"]:
        raise RuntimeError("support preflight did not pass")
    with (ROOT / lineage["inventory"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    classes = {int(row["match_id"]): row["population_class"] for row in rows}
    if {key for key, value in classes.items() if value == "nonoverlapping_candidate"} != set(FORMAL_MATCHES):
        raise RuntimeError("preflight candidate population mismatch")
    if any(classes.get(match) != "existing_project1" for match in ORIGINAL_MATCHES) or classes.get(EXCLUDED_MATCH) != "excluded_incompatible":
        raise RuntimeError("preflight overlap/exclusion identity mismatch")
    return {"manifest_sha256": lineage["manifest_sha256"], "source_ledger_sha256": lineage["source_ledger_sha256"]}


def expected_candidate_sources() -> dict[str, str]:
    records = read_json(PREFLIGHT_OUTPUT / "source_hashes.json")["files"]
    return {row["file"]: row["sha256"] for row in records if int(row["match_id"]) in FORMAL_MATCHES}


def verify_sources(data_dir: Path, source_repository: Path) -> None:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source_repository, capture_output=True, text=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=source_repository, capture_output=True, text=True, check=True).stdout.strip()
    if (commit, tree) != (SOURCE_COMMIT, SOURCE_TREE):
        raise RuntimeError("upstream source revision mismatch")
    expected = expected_candidate_sources()
    present_ids = {int(path.name.split("_", 1)[0]) for path in data_dir.glob("*_match.json")}
    if not set(FORMAL_MATCHES).issubset(present_ids):
        raise RuntimeError("data directory is missing one or more frozen matches")
    for name, expected_hash in expected.items():
        path = data_dir / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise RuntimeError(f"source identity mismatch: {name}")


def classify(contrast: float, bootstrap: dict[str, Any], per_match: pd.DataFrame, lomo: pd.DataFrame, trim: dict[str, Any], quality: dict[str, Any], valid: bool = True) -> tuple[str, dict[str, Any]]:
    inherited_status, criteria = inherited.classification(valid, tuple(map(str, FORMAL_MATCHES)), contrast, bootstrap, per_match, lomo, trim, quality)
    suffix = next(label for label in ("NOT SUPPORTED", "SUPPORTED", "MIXED", "INVALID") if inherited_status.endswith(label))
    return f"ADDITIONAL SKILLCORNER DIRECTIONAL REPLICATION {suffix}", criteria


def _quality(data: pd.DataFrame) -> dict[str, Any]:
    quality_data = data.loc[data.quality_pass].reset_index(drop=True)
    if quality_data.empty:
        raise RuntimeError("majority-detected sensitivity has no rows")
    beta, rank, _ = inherited.fit(quality_data)
    mapping = inherited.continuous_map(beta)
    return {
        "rows": int(len(quality_data)), "anchors": int(quality_data.anchor_frame.nunique()),
        "matches": int(quality_data.match_id.nunique()), "full_rank": rank == len(inherited.BASE) + len(FORMAL_MATCHES),
        "model_rank": rank, "beta_goalward_m_per_m": mapping["attacker_goalward_displacement_m"],
        "beta_outward_m_per_m": mapping["attacker_outward_displacement_m"],
        "outward_minus_goalward_m_per_m": mapping["attacker_outward_displacement_m"] - mapping["attacker_goalward_displacement_m"],
    }


def compute_payload(data_dir: Path, destination: Path, authorization_reference: str) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    samples, supports, equivalence_rows = [], [], []
    for match_id in FORMAL_MATCHES:
        source = inherited.MatchSource(match_id, data_dir)
        equivalence = source.provider_equivalence()
        if not equivalence["pass"]:
            raise RuntimeError(f"provider equivalence failed: {match_id}")
        support = inherited.support_match(source)
        sample, summary = inherited.construct_match(source)
        for key in ("retained_anchors", "retained_rows", "majority_detected_rows"):
            if support[key] != summary[key]:
                raise RuntimeError(f"support identity mismatch for {match_id}: {key}")
        samples.append(sample)
        supports.append(summary)
        equivalence_rows.append({"match_id": match_id, "pass": True})
    data = pd.concat(samples, ignore_index=True).sort_values(["match_id", "period", "anchor_frame", "observation_id"], kind="mergesort").reset_index(drop=True)
    if set(data.match_id.astype(str)) != set(map(str, FORMAL_MATCHES)) or data.observation_id.duplicated().any():
        raise RuntimeError("final observation identity failure")
    matches = tuple(map(str, FORMAL_MATCHES))
    pooled, pooled_rank, per_match, lomo = inherited.primary_fit_table(data, matches)
    contrast = pooled["attacker_outward_displacement_m"] - pooled["attacker_goalward_displacement_m"]
    bootstrap = inherited.bootstrap(data, matches)
    _trimmed, trim = inherited.trim_fit(data)
    quality = _quality(data)
    status, criteria = classify(contrast, bootstrap, per_match, lomo, trim, quality)
    primary = {
        "beta_goalward_m_per_m": pooled["attacker_goalward_displacement_m"],
        "beta_outward_m_per_m": pooled["attacker_outward_displacement_m"],
        "outward_minus_goalward_m_per_m": contrast,
        "five_m_translation_m": 5.0 * contrast,
    }
    checks = {
        "exact_ten_matches": len(samples) == 10,
        "pooled_full_rank": pooled_rank == len(inherited.BASE) + 10,
        "per_match_full_rank": bool((per_match.model_rank == len(inherited.BASE) + 1).all()),
        "lomo_full_rank": bool((lomo.model_rank == len(inherited.BASE) + 9).all()),
        "bootstrap_valid_at_least_1900": bootstrap["valid_replicates"] >= 1900,
        "unique_observation_ids": not data.observation_id.duplicated().any(),
        "finite_response_and_design": bool(np.isfinite(data.loc[:, ["Y_m", *inherited.BASE]].to_numpy(float)).all()),
        "aggregate_outputs_only": True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"hard QC failed: {checks}")
    result = {
        "classification": status,
        "sample": {"rows": len(data), "anchors": int(data.anchor_frame.nunique()), "matches": 10, "match_ids": list(FORMAL_MATCHES)},
        "primary": primary, "bootstrap": bootstrap,
        "trim": {key: value for key, value in trim.items() if key != "bounds"},
        "quality_sensitivity": quality, "classification_criteria": criteria,
    }
    write_json(destination / "result.json", result)
    write_json(destination / "hard_qc.json", {"status": "PASSED", "checks": checks})
    write_json(destination / "classification_criteria.json", criteria)
    hashes = verify_hash_ledger()
    write_json(destination / "manifest.json", {
        "status": "PENDING_AUTHORITATIVE_VALIDATION", "authorization_reference": authorization_reference,
        "protocol_sha256": hashes[str(PROTOCOL.relative_to(ROOT))], "configuration_sha256": hashes[str(CONFIG.relative_to(ROOT))],
        "freeze_ledger_sha256": sha256(LEDGER), "implementation_sha256": hashes[str(Path(__file__).relative_to(ROOT))],
        "tests_sha256": hashes["tests/test_skillcorner_additional_directional_replication_v1.py"],
        "source_commit": SOURCE_COMMIT, "source_tree": SOURCE_TREE, "formal_matches": list(FORMAL_MATCHES),
        "bootstrap_seed": 20260905, "bootstrap_replicates": 2000, "classification": status,
        "preflight_lineage": verify_preflight_lineage(), "publication_policy": "compact_aggregate_outputs_only",
    })
    pd.DataFrame([{**primary, "classification": status, "ci_low": bootstrap["ci_low"], "ci_high": bootstrap["ci_high"], "valid_bootstrap_replicates": bootstrap["valid_replicates"]}]).loc[:, list(CSV_SCHEMAS["primary_contrast.csv"])].to_csv(destination / "primary_contrast.csv", index=False)
    per_match.loc[:, list(CSV_SCHEMAS["per_match_coefficients.csv"])].to_csv(destination / "per_match_coefficients.csv", index=False)
    lomo.loc[:, list(CSV_SCHEMAS["leave_one_match_out.csv"])].to_csv(destination / "leave_one_match_out.csv", index=False)
    pd.DataFrame([{key: trim[key] for key in CSV_SCHEMAS["trim_sensitivity.csv"]}]).to_csv(destination / "trim_sensitivity.csv", index=False)
    pd.DataFrame([quality]).loc[:, list(CSV_SCHEMAS["quality_sensitivity.csv"])].to_csv(destination / "quality_sensitivity.csv", index=False)
    pd.DataFrame([{key: row[key] for key in CSV_SCHEMAS["sample_summary.csv"]} for row in supports]).to_csv(destination / "sample_summary.csv", index=False)
    pd.DataFrame(equivalence_rows).to_csv(destination / "provider_equivalence.csv", index=False)
    (destination / "result_report.md").write_text(render_report(result) + "\n", encoding="utf-8")


def render_report(result: dict[str, Any]) -> str:
    primary, boot, quality = result["primary"], result["bootstrap"], result["quality_sensitivity"]
    return "\n".join([
        "# Additional SkillCorner Directional Replication v1", "",
        f"**Classification:** **{result['classification']}**", "",
        "The ten matches were prospectively frozen as a nonoverlapping Project 1 replication population after independent reacquisition and response-blind compatibility checking. Project 1 had not previously evaluated its frozen directional response on these matches. Global prior exposure outside this project is not claimed to be absent.", "",
        "## Primary result", "",
        f"The outward-minus-goalward macro contrast was {primary['outward_minus_goalward_m_per_m']:.6f} m/m (95% interval [{boot['ci_low']:.6f}, {boot['ci_high']:.6f}]).",
        f"Positive match contrasts: {result['classification_criteria']['positive_matches']}/10. All ten leave-one-match-out estimates are reported in the aggregate package.", "",
        "## Robustness and identity", "",
        f"The majority-detected sensitivity contrast was {quality['outward_minus_goalward_m_per_m']:.6f} m/m. The frozen joint trim and quality gates are recorded in classification_criteria.json. The package is bound to the closed support population, source identities, protocol, configuration and bootstrap provenance; {boot['valid_replicates']} paired block draws were valid.", "",
        "## Boundary", "",
        "This prospective association test used an already-used provider environment. It does not validate the IDSSE heatmap itself and does not establish causation, marking, intent, tactical effectiveness, value, optimal areas or space creation.",
    ])


def _finite_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_SCHEMAS[path.name]:
            raise RuntimeError(f"CSV schema mismatch: {path.name}")
        rows = list(reader)
    if len(rows) != ROW_COUNTS[path.name]:
        raise RuntimeError(f"CSV row count mismatch: {path.name}")
    for row in rows:
        for value in row.values():
            if value.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
                raise RuntimeError(f"nonfinite CSV value: {path.name}")
    return rows


def _validate_no_reconstructive_keys(value: Any, context: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_KEYS:
                raise RuntimeError(f"reconstructive JSON field in {context}: {key}")
            _validate_no_reconstructive_keys(item, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_no_reconstructive_keys(item, f"{context}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise RuntimeError(f"nonfinite JSON value in {context}")


def _require_keys(value: Any, keys: set[str], context: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise RuntimeError(f"nested JSON schema mismatch: {context}")


def validate_package(directory: Path, *, final: bool = False) -> dict[str, Any]:
    for name in CSV_SCHEMAS:
        rows = _finite_csv(directory / name)
        if name == "per_match_coefficients.csv" and {int(row["match_id"]) for row in rows} != set(FORMAL_MATCHES):
            raise RuntimeError("per-match identity mismatch")
        if name == "leave_one_match_out.csv" and {int(row["heldout_match_id"]) for row in rows} != set(FORMAL_MATCHES):
            raise RuntimeError("LOMO identity mismatch")
        if name in {"sample_summary.csv", "provider_equivalence.csv"} and {int(row["match_id"]) for row in rows} != set(FORMAL_MATCHES):
            raise RuntimeError(f"match identity mismatch: {name}")
    objects = {name: read_json(directory / name) for name in JSON_KEYS}
    for name, allowed in JSON_KEYS.items():
        if set(objects[name]) != allowed:
            raise RuntimeError(f"JSON schema mismatch: {name}")
        _validate_no_reconstructive_keys(objects[name], name)
    result = objects["result.json"]
    _require_keys(result["sample"], {"rows", "anchors", "matches", "match_ids"}, "result.sample")
    _require_keys(result["primary"], {"beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "five_m_translation_m"}, "result.primary")
    _require_keys(result["bootstrap"], {"replicates_requested", "valid_replicates", "seed", "block_seconds", "ci_low", "ci_high"}, "result.bootstrap")
    _require_keys(result["trim"], {"rows_retained", "retained_proportion", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m", "model_rank"}, "result.trim")
    _require_keys(result["quality_sensitivity"], {"rows", "anchors", "matches", "full_rank", "model_rank", "beta_goalward_m_per_m", "beta_outward_m_per_m", "outward_minus_goalward_m_per_m"}, "result.quality_sensitivity")
    _require_keys(result["classification_criteria"], CRITERIA_KEYS, "result.classification_criteria")
    _require_keys(result["classification_criteria"]["gates"], CRITERIA_GATE_KEYS, "result.classification_criteria.gates")
    _require_keys(objects["hard_qc.json"]["checks"], HARD_QC_KEYS, "hard_qc.checks")
    _require_keys(objects["classification_criteria.json"], CRITERIA_KEYS, "classification_criteria")
    _require_keys(objects["classification_criteria.json"]["gates"], CRITERIA_GATE_KEYS, "classification_criteria.gates")
    _require_keys(objects["manifest.json"]["preflight_lineage"], {"manifest_sha256", "source_ledger_sha256"}, "manifest.preflight_lineage")
    classification = objects["result.json"]["classification"]
    if objects["manifest.json"]["classification"] != classification:
        raise RuntimeError("classification mismatch")
    if objects["result.json"]["sample"]["match_ids"] != list(FORMAL_MATCHES):
        raise RuntimeError("result population mismatch")
    if objects["result.json"]["sample"]["matches"] != 10 or objects["classification_criteria.json"]["valid_matches"] != 10:
        raise RuntimeError("result match count mismatch")
    primary_row = _finite_csv(directory / "primary_contrast.csv")[0]
    if primary_row["classification"] != classification:
        raise RuntimeError("primary classification mismatch")
    per_match_rows = _finite_csv(directory / "per_match_coefficients.csv")
    positive = sum(row["positive_contrast"].lower() == "true" for row in per_match_rows)
    if positive != objects["classification_criteria.json"]["positive_matches"]:
        raise RuntimeError("positive match count mismatch")
    if result["classification_criteria"] != objects["classification_criteria.json"]:
        raise RuntimeError("classification criteria mismatch")
    if result["bootstrap"]["seed"] != 20260905 or result["bootstrap"]["replicates_requested"] != 2000:
        raise RuntimeError("bootstrap provenance mismatch")
    if objects["manifest.json"]["formal_matches"] != list(FORMAL_MATCHES):
        raise RuntimeError("manifest population mismatch")
    if objects["manifest.json"]["source_commit"] != SOURCE_COMMIT or objects["manifest.json"]["source_tree"] != SOURCE_TREE:
        raise RuntimeError("manifest source lineage mismatch")
    if final:
        ledger = read_json(directory / "final_hashes.json")
        _validate_no_reconstructive_keys(ledger, "final_hashes.json")
        if set(ledger) != set(GOVERNED_FILES) | {"reproduction.json"}:
            raise RuntimeError("final hash ledger schema mismatch")
        for name, expected in ledger.items():
            if sha256(directory / name) != expected:
                raise RuntimeError(f"authoritative hash mismatch: {name}")
    return {"classification": classification, "files_validated": len(GOVERNED_FILES)}


def compare_staging(primary: Path, reproduction: Path) -> dict[str, Any]:
    comparisons = []
    for name in GOVERNED_FILES:
        left, right = primary / name, reproduction / name
        comparisons.append({"file": name, "sha256": sha256(left), "byte_identical": left.read_bytes() == right.read_bytes()})
    if not all(row["byte_identical"] for row in comparisons):
        raise RuntimeError("isolated reproduction differs")
    return {"status": "STAGING_REPRODUCTION_PASSED", "files_compared": len(comparisons), "comparisons": comparisons}


def validate_final_authority(directory: Path) -> dict[str, Any]:
    validate_package(directory, final=True)
    marker = read_json(directory / FINAL_MARKER)
    _validate_no_reconstructive_keys(marker, FINAL_MARKER)
    expected = {"status": "FINAL_PACKAGE_VALID", "final_hashes_sha256": sha256(directory / "final_hashes.json")}
    if marker != expected:
        raise RuntimeError("final authority marker mismatch")
    return marker


def close_execution(output: Path, authorization_reference: str, build: Callable[[Path], None], replace: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace) -> dict[str, Any]:
    if output.exists():
        raise RuntimeError("authoritative destination already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="skillcorner_additional_directional_", dir=output.parent))
    primary, rerun = temporary / "primary", temporary / "reproduction"
    try:
        build(primary)
        build(rerun)
        validate_package(primary)
        validate_package(rerun)
        write_json(primary / "reproduction.json", compare_staging(primary, rerun))
        write_json(primary / "final_hashes.json", {name: sha256(primary / name) for name in GOVERNED_FILES + ("reproduction.json",)})
        validate_package(primary, final=True)
        replace(primary, output)
        validate_package(output, final=True)
        marker_tmp = output.parent / f".{output.name}.{FINAL_MARKER}.tmp"
        write_json(marker_tmp, {"status": "FINAL_PACKAGE_VALID", "final_hashes_sha256": sha256(output / "final_hashes.json")})
        replace(marker_tmp, output / FINAL_MARKER)
        result = validate_final_authority(output)
        return {"status": result["status"], "authorization_reference": authorization_reference, "output": str(output)}
    except Exception:
        marker = output / FINAL_MARKER
        if marker.exists():
            marker.unlink()
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def preflight(data_dir: Path | None = None, source_repository: Path | None = None) -> dict[str, Any]:
    result = {"freeze": verify_hash_ledger(), "lineage": verify_preflight_lineage(), "response_constructed": False}
    if data_dir is not None or source_repository is not None:
        if data_dir is None or source_repository is None:
            raise RuntimeError("both data and source repository paths are required")
        verify_sources(data_dir, source_repository)
        result["sources_verified"] = True
    if OUTPUT.exists():
        raise RuntimeError("authoritative response result already exists")
    return result


def run(data_dir: Path, source_repository: Path, authorization_reference: str) -> dict[str, Any]:
    if not authorization_reference.strip():
        raise RuntimeError("explicit authorization reference is required")
    verify_hash_ledger()
    require_clean_committed_freeze()
    verify_preflight_lineage()
    verify_sources(data_dir, source_repository)
    return close_execution(OUTPUT, authorization_reference, lambda destination: compute_payload(data_dir, destination, authorization_reference))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    pre = subparsers.add_parser("preflight")
    pre.add_argument("--data-dir", type=Path)
    pre.add_argument("--source-repository", type=Path)
    execute = subparsers.add_parser("run")
    execute.add_argument("--data-dir", type=Path, required=True)
    execute.add_argument("--source-repository", type=Path, required=True)
    execute.add_argument("--authorization-reference", required=True)
    publication = subparsers.add_parser("publication-check")
    publication.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "preflight":
        result = preflight(args.data_dir, args.source_repository)
    elif args.command == "run":
        result = run(args.data_dir, args.source_repository, args.authorization_reference)
    else:
        result = validate_final_authority(args.output)
    print(json.dumps(_clean(result), sort_keys=True))


if __name__ == "__main__":
    main()
