"""Outcome-free execution-plan checks for frozen Coverage Redistribution v3."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_coverage_redistribution_game1_v3 as runner  # noqa: E402


OUTPUT = ROOT / "outputs/defensive_coverage_redistribution_game1_v3"


def _toy_data() -> pd.DataFrame:
    rng = np.random.default_rng(17)
    n = 40
    values = {name: rng.normal(size=n) for name in ("A", "D", "G0", "MO", "B", "C", "R", "Apre", "Dpre", "Bpre")}
    values["Dremote"] = rng.normal(size=n)
    values["Dpre_remote"] = rng.normal(size=n)
    values["P2"] = np.zeros(n, dtype=int)
    values["Y"] = 0.4 + 0.6 * values["D"] - 0.1 * values["A"] + rng.normal(scale=.1, size=n)
    return pd.DataFrame(values)


def test_constant_period_nuisance_is_resolved_once_and_reused_for_every_fit() -> None:
    config = json.loads((ROOT / "config/defensive_coverage_redistribution_v3.json").read_text(encoding="utf-8"))
    data = _toy_data()
    plan = runner.resolve_primary_plan(data, config)

    assert plan.omitted_constant_nuisance_columns == ("period_2_indicator",)
    assert len(plan.nominal_columns) == 12
    assert len(plan.active_columns) == 11
    assert "period_2_indicator" not in plan.active_columns
    assert runner.fit(data, plan)["rank"] == 11
    assert runner.fit(data, plan, "Dremote", "Dpre_remote")["rank"] == 11


def test_v3_runner_uses_only_the_frozen_column_order_and_primary_key() -> None:
    config = json.loads((ROOT / "config/defensive_coverage_redistribution_v3.json").read_text(encoding="utf-8"))
    assert tuple(config["nominal_model_columns_in_order"])[2] == runner.PRIMARY
    assert config["constant_nuisance_rule"]["designated_non_scientific_nuisance_columns"] == ["period_2_indicator"]


def test_governed_game1_result_preserves_the_frozen_active_plan_and_reproduction() -> None:
    result = json.loads((OUTPUT / "model_results.json").read_text(encoding="utf-8"))
    plan = json.loads((OUTPUT / "active_column_plan.json").read_text(encoding="utf-8"))
    reproduction = json.loads((OUTPUT / "reproduction.json").read_text(encoding="utf-8"))

    assert result["classification"] == "MIXED"
    assert result["primary"]["rank"] == 11
    assert result["sample"]["eligible_anchors"] == 281
    assert plan["omitted_constant_nuisance_columns"] == ["period_2_indicator"]
    assert result["hard_qc"]["valid"] is True
    assert reproduction["all_governed_outputs_byte_identical"] is True
    assert reproduction["governed_outputs"] == 11
