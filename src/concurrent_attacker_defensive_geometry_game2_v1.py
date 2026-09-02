"""Tier-3 execution of frozen Concurrent Attacker–Defensive Geometry v1 on Game 2."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import attacking_continuous_movement_game2_v1 as tracking2
import concurrent_attacker_defensive_geometry_game1_v1 as g1

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/concurrent_attacker_defensive_geometry_v1.md"
CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1.json"
REPLICATION_PROTOCOL = ROOT / "docs/protocols/concurrent_attacker_defensive_geometry_v1_game2_replication.md"
REPLICATION_CONFIG = ROOT / "config/concurrent_attacker_defensive_geometry_v1_game2_replication.json"
REPLICATION_LEDGER = ROOT / "config/concurrent_attacker_defensive_geometry_v1_game2_replication_hashes.json"
GAME1_RESULT = ROOT / "outputs/concurrent_attacker_defensive_geometry_game1_v1/final_results.json"
EVENTS = ROOT / "data/metrica_sample_game_2/Sample_Game_2_RawEventsData.csv"
DEFAULT_OUTPUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_game2_v1"
DEFAULT_FIGURES = ROOT / "figures/concurrent_attacker_defensive_geometry_game2_v1"
FROZEN = {
    PROTOCOL: "1382e97f401eafc2101f2d77ef2b7158e48500ce7df6b01d4db450f2ba1b8f32",
    CONFIG: "5b37211295297fe4350c394500da27e72040aefcc7f4806b1c779a390a9c692d",
    GAME1_RESULT: "cd782fcf31b1822e397297278f43b82dcb9ce270318786c1db8c3d57d52e0da0",
    REPLICATION_PROTOCOL: "ae22d4894e73eafe23ba8947dd54a0d3e2d5cd51dab19ae24c6e0117824c903b",
    REPLICATION_CONFIG: "2382e7f759c49f3c3cc8826dbc15c529ac48a30e1ebc791f18123e22120430ca",
    REPLICATION_LEDGER: "ad24bdaceba8dfdbb05c13d4f22691ecb387fa86385756090fcf8a9cad4a5fe1",
}
GAME1_BUILD_SAMPLE = g1.build_sample


def verify_frozen() -> None:
    bad = {str(p.relative_to(ROOT)): [g1.sha(p), expected] for p, expected in FROZEN.items() if g1.sha(p) != expected}
    if bad:
        raise RuntimeError(f"frozen hash failure: {bad}")


def load_game2() -> tuple[Any, Any, Any]:
    players, frames, provenance, support = tracking2.load_game2_from_frozen_support()
    provenance = {**provenance, "frozen_support_consumption": support}
    return players, frames, provenance


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    old_loader, old_events = g1.tracking.load_game1, g1.EVENTS
    try:
        g1.tracking.load_game1 = load_game2
        g1.EVENTS = EVENTS
        data, exclusions, provenance = GAME1_BUILD_SAMPLE()
    finally:
        g1.tracking.load_game1 = old_loader
        g1.EVENTS = old_events
    data["observation_id"] = data.observation_id.str.replace("CAG1|", "CAG2|", regex=False)
    return data, exclusions, provenance


def bootstrap(data: pd.DataFrame, matrix: np.ndarray, outcomes: dict[str, np.ndarray], trim_mask: np.ndarray) -> dict[str, np.ndarray]:
    full = {name: g1.block_sufficient(data, matrix, y) for name, y in outcomes.items()}
    td, tx = data.loc[trim_mask].reset_index(drop=True), matrix[trim_mask]
    trimmed = g1.block_sufficient(td, tx, outcomes["primary"][trim_mask])
    keys = sorted(full["primary"])
    by_period = {p: [key for key in keys if key[0] == p] for p in sorted({key[0] for key in keys})}
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(g1.SEED).spawn(2)[1]))
    result: dict[str, list[np.ndarray]] = {"primary": [], "secondary": [], "trimmed": []}
    for _ in range(g1.BOOT):
        selected = []
        for blocks in by_period.values():
            selected.extend(blocks[int(i)] for i in rng.integers(0, len(blocks), size=len(blocks)))
        for name in ("primary", "secondary"):
            xtx = sum((full[name][key][0] for key in selected), np.zeros((g1.P, g1.P)))
            xty = sum((full[name][key][1] for key in selected), np.zeros(g1.P))
            try:
                result[name].append(g1.summarize(g1.fit_sufficient(xtx, xty))["D1_D10"])
            except np.linalg.LinAlgError:
                pass
        available = [key for key in selected if key in trimmed]
        xtx = sum((trimmed[key][0] for key in available), np.zeros((g1.P, g1.P)))
        xty = sum((trimmed[key][1] for key in available), np.zeros(g1.P))
        try:
            result["trimmed"].append(g1.summarize(g1.fit_sufficient(xtx, xty))["D1_D10"])
        except np.linalg.LinAlgError:
            pass
    return {name: np.asarray(values) for name, values in result.items()}


def execute(output: Path, figures: Path) -> dict[str, Any]:
    verify_frozen()
    old_build, old_boot, old_frozen = g1.build_sample, g1.bootstrap, g1.FROZEN
    try:
        g1.build_sample = build_sample
        g1.bootstrap = bootstrap
        g1.FROZEN = FROZEN
        result = g1.execute(output)
    finally:
        g1.build_sample, g1.bootstrap, g1.FROZEN = old_build, old_boot, old_frozen

    primary = result["primary"]["near_minus_middle"]
    primary_row = pd.read_csv(output / "primary_coefficients.csv").query("estimand == 'near_minus_middle'").iloc[0]
    retained = result["trimmed_primary"]["retained_magnitude_fraction"]
    valid = all(result["hard_qc"].values()) and all(v["valid"] >= g1.MIN_VALID for v in result["bootstrap"].values())
    if not valid:
        status = "GAME 2 CONCURRENT GEOMETRY REPLICATION INVALID"
    elif primary <= 0:
        status = "GAME 2 CONCURRENT GEOMETRY REPLICATION NOT SUPPORTED"
    elif primary_row.ci_low > 0 and result["trimmed_primary"]["near_minus_middle"] > 0 and retained >= 0.5:
        status = "GAME 2 CONCURRENT GEOMETRY REPLICATION SUPPORTED"
    else:
        status = "GAME 2 CONCURRENT GEOMETRY REPLICATION MIXED"
    secondary_row = pd.read_csv(output / "secondary_deformation_coefficients.csv").query("estimand == 'near_minus_middle'").iloc[0]
    secondary_status = (
        "SUPPORTIVE" if secondary_row.estimate > 0 and secondary_row.ci_low > 0
        else "DIRECTIONALLY SUPPORTIVE" if secondary_row.estimate > 0
        else "NON-SUPPORTIVE"
    )
    result["status"] = status
    result["secondary_deformation_classification"] = secondary_status
    result["criteria"] = {
        "valid_execution_and_all_hard_qc": valid,
        "primary_near_minus_middle_positive": primary > 0,
        "primary_95_percent_interval_strictly_above_zero": bool(primary_row.ci_low > 0),
        "trimmed_primary_near_minus_middle_positive": result["trimmed_primary"]["near_minus_middle"] > 0,
        "trim_retains_at_least_0.5_absolute_magnitude": retained >= 0.5,
        "no_construct_validity_failure": valid,
    }
    result["hard_qc"].pop("no_game2_game3_idsse_or_opportunity_access", None)
    result["hard_qc"]["no_game3_idsse_or_opportunity_access"] = True
    result["hard_qc"]["reserved_bootstrap_child_1"] = True
    result["hard_qc"]["governed_lstsq_solver"] = True
    result["hard_qc"]["game2_only_no_pooling"] = True
    g1.write_json(output / "final_results.json", result)
    g1.write_json(output / "result_hash.json", {"final_results.json": g1.sha(output / "final_results.json")})
    g1.write_json(output / "execution_metadata.json", {
        "starting_commit": "ddfb93804b5e2cf42b94c5c1011322224a1b74e8",
        "tier": 3,
        "status": status,
        "game2_result_observed_only_after_replication_freeze": True,
        "execution_source": str(Path(__file__).relative_to(ROOT)),
        "execution_source_sha256": g1.sha(Path(__file__)),
        "python": platform.python_version(),
    })
    figures.mkdir(parents=True, exist_ok=True)
    table = pd.read_csv(output / "primary_coefficients.csv")
    ranks = table[table.estimand.str.match(r"D\d+$")]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.errorbar(range(1, 11), ranks.estimate, yerr=[ranks.estimate-ranks.ci_low, ranks.ci_high-ranks.estimate], fmt="o-", capsize=3)
    ax.axhline(0, color="black", linewidth=.8)
    ax.set(xlabel="Defender proximity rank at interval start", ylabel="Attacker-path coefficient (m/m)", title="Game 2 concurrent defensive geometry")
    ax.set_xticks(range(1, 11)); fig.tight_layout()
    fig.savefig(figures / "game2_rank_coefficients.png", dpi=180); plt.close(fig)
    governed = [p.name for p in sorted(output.iterdir()) if p.is_file() and p.name not in {"governed_hashes.json", "reproduction.json", "final_hashes.json"}]
    g1.write_json(output / "governed_hashes.json", {name: g1.sha(output / name) for name in governed})
    return result


def verify(primary: Path, rerun: Path) -> dict[str, Any]:
    ledger = json.loads((primary / "governed_hashes.json").read_text(encoding="utf-8"))
    comparisons = [{"file": name, "byte_identical": (primary/name).read_bytes() == (rerun/name).read_bytes()} for name in ledger]
    record = {"all_governed_outputs_byte_identical": all(x["byte_identical"] for x in comparisons), "files_compared": len(comparisons), "comparisons": comparisons}
    g1.write_json(primary / "reproduction.json", record)
    final = list(ledger) + ["governed_hashes.json", "reproduction.json"]
    g1.write_json(primary / "final_hashes.json", {name: g1.sha(primary/name) for name in final})
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    value = verify(args.output, args.verify_against) if args.verify_against else execute(args.output, args.figures)
    print(json.dumps(value if args.verify_against else {"status": value["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
