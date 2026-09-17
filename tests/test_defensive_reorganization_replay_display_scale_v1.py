from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_replay_display_scale_v1 import (  # noqa: E402
    CANDIDATE_CEILINGS,
    SCORER_SHA256,
    candidate_audit,
    distribution_summary,
    load_config,
    perceptual_spread,
    select_ceiling,
    split_complete_runs,
)


def test_frozen_candidate_set_and_config_boundaries():
    config = load_config()
    assert CANDIDATE_CEILINGS == (4.0, 5.0, 6.0)
    assert tuple(config["candidate_ceilings_m"]) == CANDIDATE_CEILINGS
    assert config["reference_population"]["games"] == [1, 2]
    assert config["reference_population"]["teams"] == ["Home", "Away"]
    assert not config["reference_population"]["events_read"]
    assert not config["reference_population"]["ball_read"]
    prohibited = set(config["prohibited_inputs"])
    assert {"events", "research_anchors", "scientific_outcomes", "metrica_game_3"} <= prohibited


def test_raw_distribution_uses_unclipped_values_and_linear_quantiles():
    raw = np.array([0.0, 1.0, 2.0, 9.0])
    summary = distribution_summary(raw, (0.5, 0.75, 0.9, 0.95, 0.975, 0.99))
    assert summary["maximum"] == 9.0
    assert summary["median"] == pytest.approx(1.5)
    assert summary["p75"] == pytest.approx(3.75)


def test_candidate_counts_are_deterministic_and_strictly_greater_than_ceiling():
    matrix = np.array([[0, 1, 2, 3, 4, 5, 6, 4, 4, 4], [1] * 10], dtype=float)
    teams = matrix.mean(axis=1)
    row = candidate_audit(matrix, teams, 4.0)
    assert row["player_saturation_count"] == 2
    assert row["frames_at_least_1_saturated"] == 1
    assert row["frames_at_least_2_saturated"] == 1
    assert row["frames_at_least_5_saturated"] == 0
    assert row["team_mean_saturation_count"] == 0


def test_perceptual_bins_partition_raw_values():
    raw = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0])
    row = perceptual_spread(raw, 4.0)
    fractions = [
        row["below_25_fraction"],
        row["between_25_75_fraction"],
        row["above_75_unsaturated_fraction"],
        row["saturated_fraction"],
    ]
    assert sum(fractions) == pytest.approx(1.0)
    assert row["saturated_fraction"] == pytest.approx(1 / 6)
    assert row["p95_normalized"] == 1.0


def _selection_rows(player=(0.1, 0.04, 0.02), team=(0.02, 0.009, 0.001)):
    return [
        {"ceiling_m": ceiling, "player_saturation_fraction": p, "team_mean_saturation_fraction": t}
        for ceiling, p, t in zip(CANDIDATE_CEILINGS, player, team, strict=True)
    ]


def test_selection_is_lowest_qualifier_and_unresolved_without_one():
    assert select_ceiling(_selection_rows()) == ("B_FREEZE_5_M", 5.0)
    assert select_ceiling(_selection_rows(player=(0.2, 0.1, 0.06))) == ("D_UNRESOLVED", None)
    with pytest.raises(ValueError, match="exactly the frozen candidates"):
        select_ceiling(_selection_rows()[:2])


def test_run_segmentation_breaks_identity_and_cadence_changes():
    rows = []
    mapping = {str(i): (f"x{i}", f"y{i}") for i in range(11)}
    for index in range(6):
        row = {"Period": 1, "Frame": index + 1, "Time [s]": (index + 1) / 25}
        for number in mapping:
            row[f"x{number}"] = float(number) if number != "10" else np.nan
            row[f"y{number}"] = float(number) if number != "10" else np.nan
        if index >= 3:
            row["x9"] = row["y9"] = np.nan
            row["x10"] = row["y10"] = 10.0
        if index == 5:
            row["Frame"] = 8
            row["Time [s]"] = 8 / 25
        rows.append(row)
    runs = split_complete_runs(pd.DataFrame(rows), mapping)
    assert [(start, end) for _, start, end, _ in runs] == [(0, 2), (3, 4), (5, 5)]
    assert runs[0][3] != runs[1][3]


def test_no_anchor_event_or_outcome_dependency_in_public_contract():
    config = load_config()
    serialized = str(config).lower()
    assert config["reference_population"]["frame_scope"] == "all_native_tracking_support_without_event_filtering"
    assert "candidate passage" not in serialized
    assert config["publication"]["forbid_row_level_scores"]


def test_scorer_source_hash_is_unchanged():
    digest = hashlib.sha256((ROOT / "src/defensive_reorganization_replay.py").read_bytes()).hexdigest()
    assert digest == SCORER_SHA256
