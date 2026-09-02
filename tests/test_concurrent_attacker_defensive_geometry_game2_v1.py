import hashlib
import json
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/concurrent_attacker_defensive_geometry_game2_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_result_and_classification():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    assert result["status"] == "GAME 2 CONCURRENT GEOMETRY REPLICATION SUPPORTED"
    assert all(result["criteria"].values())
    assert all(result["hard_qc"].values())
    assert all(x["valid"] == 2000 for x in result["bootstrap"].values())


def test_complete_rank_vectors_and_fixed_goalkeepers():
    data = pl.read_parquet(OUT / "observation_rows.parquet")
    assert data.height == 11_820
    assert data["observation_id"].n_unique() == 1_182
    counts = data.group_by("observation_id").len()
    assert counts["len"].min() == counts["len"].max() == 10
    assert not data["defender_key"].is_in(["metrica:Home:11", "metrica:Away:25"]).any()


def test_governed_hashes_and_reproduction():
    ledger = json.loads((OUT / "governed_hashes.json").read_text(encoding="utf-8"))
    assert all(sha(OUT / name) == expected for name, expected in ledger.items())
    final = json.loads((OUT / "final_hashes.json").read_text(encoding="utf-8"))
    assert all(sha(OUT / name) == expected for name, expected in final.items())
    reproduction = json.loads((OUT / "reproduction.json").read_text(encoding="utf-8"))
    assert reproduction["all_governed_outputs_byte_identical"]
    assert reproduction["files_compared"] == 10


def test_primary_and_trimmed_values_are_serialized_consistently():
    result = json.loads((OUT / "final_results.json").read_text(encoding="utf-8"))
    primary = pd.read_csv(OUT / "primary_coefficients.csv").set_index("estimand")
    trimmed = pd.read_csv(OUT / "trimmed_primary_coefficients.csv").set_index("estimand")
    assert primary.loc["near_minus_middle", "estimate"] == pytest.approx(result["primary"]["near_minus_middle"], abs=1e-15)
    assert trimmed.loc["near_minus_middle", "estimate"] == pytest.approx(result["trimmed_primary"]["near_minus_middle"], abs=1e-15)
    assert result["trimmed_primary"]["retained_magnitude_fraction"] >= 0.5
