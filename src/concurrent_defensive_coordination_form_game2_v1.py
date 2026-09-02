"""Execute frozen Concurrent Defensive Coordination Form v1 on Game 2 only."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import attacking_continuous_movement_game2_v1 as tracking2
import concurrent_defensive_coordination_form_game1_v1 as g1


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/metrica_sample_game_2/Sample_Game_2_RawEventsData.csv"
CLARIFICATION = ROOT / "docs/protocols/concurrent_defensive_coordination_form_v1_game2_replication.md"
CLARIFICATION_LEDGER = ROOT / "config/concurrent_defensive_coordination_form_v1_game2_replication_hashes.json"
DEFAULT_OUTPUT = ROOT / "outputs/concurrent_defensive_coordination_form_game2_v1"
FROZEN = {
    g1.PROTOCOL: "3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032",
    g1.CONFIG: "d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3",
    CLARIFICATION: "b5cec238d04649217a39549587ebfb292278829fb8c9c434ff5ef40b8a2786e9",
}
GAME1_BUILD_SAMPLE = g1.build_sample


def verify_frozen() -> None:
    bad = {str(path.relative_to(ROOT)): [g1.sha(path), expected]
           for path, expected in FROZEN.items() if g1.sha(path) != expected}
    ledger = json.loads(CLARIFICATION_LEDGER.read_text(encoding="utf-8"))
    if ledger["clarification_sha256"] != FROZEN[CLARIFICATION]:
        bad[str(CLARIFICATION_LEDGER.relative_to(ROOT))] = [ledger["clarification_sha256"], FROZEN[CLARIFICATION]]
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")


def load_game2() -> tuple[Any, Any, Any]:
    players, frames, provenance, support = tracking2.load_game2_from_frozen_support()
    return players, frames, {**provenance, "frozen_support_consumption": support}


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    old_loader, old_events = g1.tracking.load_game1, g1.EVENTS
    try:
        g1.tracking.load_game1 = load_game2
        g1.EVENTS = EVENTS
        data, exclusions, provenance = GAME1_BUILD_SAMPLE()
    finally:
        g1.tracking.load_game1, g1.EVENTS = old_loader, old_events
    data["observation_id"] = data.observation_id.str.replace("CDFG1|", "CDFG2|", regex=False)
    return data, exclusions, provenance


def paired_bootstrap(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    stores = {}
    for method in ("primary", "sensitivity"):
        x = g1.design(data, method)
        y = data[f"{method}_aard_vel_mps"].to_numpy(float)
        stores[method] = g1.sufficient(data, x, y)
    keys = sorted(stores["primary"])
    periods = {p: [k for k in keys if k[0] == p] for p in sorted({k[0] for k in keys})}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(g1.SEED).spawn(2)[1]))
    primary, sensitivity = [], []
    for _ in range(g1.BOOT):
        chosen = []
        for blocks in periods.values():
            chosen.extend(blocks[int(i)] for i in rng.integers(0, len(blocks), size=len(blocks)))
        try:
            values = []
            for method in ("primary", "sensitivity"):
                xtx = sum((stores[method][k][0] for k in chosen), np.zeros((g1.P, g1.P)))
                xty = sum((stores[method][k][1] for k in chosen), np.zeros(g1.P))
                values.append(g1.summary(g1.fit_sufficient(xtx, xty)))
            primary.append([*values[0]["D1_D10"], values[0]["primary_D2_D3_minus_D4_D7"], values[0]["D1_minus_D4_D7"]])
            sensitivity.append([*values[1]["D1_D10"], values[1]["primary_D2_D3_minus_D4_D7"], values[1]["D1_minus_D4_D7"]])
        except (np.linalg.LinAlgError, RuntimeError):
            pass
    return np.asarray(primary), np.asarray(sensitivity)


def execute(output: Path) -> dict[str, Any]:
    verify_frozen()
    old_build, old_boot, old_frozen = g1.build_sample, g1.paired_bootstrap, g1.FROZEN
    try:
        g1.build_sample, g1.paired_bootstrap, g1.FROZEN = build_sample, paired_bootstrap, FROZEN
        result = g1.execute(output)
    finally:
        g1.build_sample, g1.paired_bootstrap, g1.FROZEN = old_build, old_boot, old_frozen

    checks = dict(result["hard_qc"])
    checks.pop("game2_not_accessed", None)
    checks["game2_authorized_execution"] = True
    checks["heldout_clarification_frozen_before_result"] = True
    valid = all(checks.values()) and result["paired_valid_bootstraps"] >= g1.MIN_VALID
    estimate = result["primary"]["primary_D2_D3_minus_D4_D7"]
    sensitivity = result["sensitivity"]["primary_D2_D3_minus_D4_D7"]
    if not valid:
        status = "GAME 2 COORDINATION FORM REPLICATION INVALID"
    elif estimate <= 0:
        status = "GAME 2 COORDINATION FORM REPLICATION NOT SUPPORTED"
    elif result["primary_contrast_ci95"][0] > 0 and sensitivity > 0:
        status = "GAME 2 COORDINATION FORM REPLICATION SUPPORTED"
    else:
        status = "GAME 2 COORDINATION FORM REPLICATION MIXED"
    result["status"] = status
    result["hard_qc"] = checks
    result["replication_criteria"] = {
        "valid_execution_and_qc": valid,
        "paired_valid_bootstraps_at_least_1900": result["paired_valid_bootstraps"] >= g1.MIN_VALID,
        "primary_1hz_positive": estimate > 0,
        "primary_95_percent_interval_strictly_above_zero": result["primary_contrast_ci95"][0] > 0,
        "sensitivity_1_5hz_positive": sensitivity > 0,
    }
    g1.write_json(output / "final_results.json", result)
    g1.write_json(output / "hard_qc.json", checks)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    manifest.update({
        "starting_commit": "55c3b27fcc1cead8595ec7e2d8e2ae43bca0ee76",
        "source": str(Path(__file__).relative_to(ROOT)),
        "source_sha256": g1.sha(Path(__file__)),
        "clarification": str(CLARIFICATION.relative_to(ROOT)),
        "clarification_sha256": g1.sha(CLARIFICATION),
        "protected": {"game2": "authorized_executed", "idsse": False, "game3": False},
        "python": platform.python_version(),
    })
    g1.write_json(output / "manifest.json", manifest)
    governed = ["exclusions.csv", "observation_rows.parquet", "rank_coefficients.csv", "secondary_coefficients.csv",
                "paired_bootstrap.npz", "final_results.json", "hard_qc.json", "manifest.json"]
    g1.write_json(output / "governed_hashes.json", {name: g1.sha(output / name) for name in governed})
    return result


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    comparisons = {name: (primary / name).read_bytes() == (rerun / name).read_bytes() for name in ledger}
    return {"all_governed_outputs_byte_identical": all(comparisons.values()), "files_compared": len(comparisons), "comparisons": comparisons}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    value = verify(args.output, args.verify_against) if args.verify_against else execute(args.output)
    print(json.dumps(g1.clean(value), indent=2, sort_keys=True))
