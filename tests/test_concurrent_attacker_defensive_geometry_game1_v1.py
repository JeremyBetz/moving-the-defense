import hashlib
import json
from pathlib import Path

import pandas as pd
import numpy as np

from src.concurrent_attacker_defensive_geometry_game1_v1 import fit_sufficient


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_game1_v1"


def test_frozen_identities_and_saved_result_hash():
    expected = {
        "docs/protocols/concurrent_attacker_defensive_geometry_v1.md": "1382e97f401eafc2101f2d77ef2b7158e48500ce7df6b01d4db450f2ba1b8f32",
        "config/concurrent_attacker_defensive_geometry_v1.json": "5b37211295297fe4350c394500da27e72040aefcc7f4806b1c779a390a9c692d",
        "config/concurrent_attacker_defensive_geometry_v1_hashes.json": "7fb68191ec74278c7734a889c0452feb3398932579db6c4af67687143a38873d",
        "outputs/concurrent_attacker_defensive_geometry_game1_v1/final_results.json": "cd782fcf31b1822e397297278f43b82dcb9ce270318786c1db8c3d57d52e0da0",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


def test_status_and_all_frozen_gates():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT"
    assert all(result["criteria"].values())
    assert all(result["hard_qc"].values())
    assert all(family["valid"] == family["attempted"] == 2000 for family in result["bootstrap"].values())


def test_primary_contrast_and_trim_reconstruct():
    primary = pd.read_csv(OUT / "primary_coefficients.csv").set_index("estimand")
    trimmed = pd.read_csv(OUT / "trimmed_primary_coefficients.csv").set_index("estimand")
    assert abs(primary.loc["near", "estimate"] - primary.loc["middle", "estimate"] - primary.loc["near_minus_middle", "estimate"]) < 1e-12
    assert primary.loc["near_minus_middle", "ci_low"] > 0
    ratio = abs(trimmed.loc["near_minus_middle", "estimate"] / primary.loc["near_minus_middle", "estimate"])
    assert ratio >= 0.5


def test_sample_has_complete_rank_vectors():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    sample = result["sample"]
    assert sample["defender_rows"] == 10 * sample["eligible_attacker_anchor_observations"]
    assert sample["eligible_attacker_anchor_observations"] == 8265


def test_sufficient_statistic_lstsq_matches_direct_frozen_ols():
    rng = np.random.default_rng(20260902)
    x = rng.normal(size=(500, 72))
    x[:, 0] = 1.0
    y = rng.normal(size=500)
    direct, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    assert rank == 72
    sufficient = fit_sufficient(x.T @ x, x.T @ y)
    np.testing.assert_allclose(sufficient, direct, atol=2e-13, rtol=2e-12)
