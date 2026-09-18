from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_replay_display_scale_v1 import candidate_audit, perceptual_spread  # noqa: E402
from defensive_reorganization_replay_display_scale_v2 import (  # noqa: E402
    CANDIDATE_CEILINGS,
    EXPECTED_PLAYER_COUNT,
    EXPECTED_RUN_COUNT,
    EXPECTED_TEAM_COUNT,
    SCORER_SHA256,
    load_config,
    select_ceiling,
    verify_v1_authority,
)


def test_v2_candidate_set_is_exact_and_bounded():
    config = load_config()
    assert CANDIDATE_CEILINGS == (6.25, 6.5, 7.0)
    assert tuple(config["candidate_ceilings_m"]) == CANDIDATE_CEILINGS


def test_v1_authority_thresholds_population_and_definitions_are_unchanged():
    config = load_config()
    verify_v1_authority(config)
    v1 = json.loads((ROOT / "config/defensive_reorganization_replay_display_scale_v1.json").read_text())
    assert config["selection_rule"] == v1["selection_rule"]
    for key in ("games", "teams", "periods", "source_fps", "goalkeeper_ids"):
        assert config["reference_population"][key] == v1["reference_population"][key]
    assert config["perceptual_bins"] == v1["perceptual_bins"]
    assert config["quantile_method"] == "linear"
    assert config["saturation_operator"] == ">"
    assert config["inherits_v1"]["supported_player_frame_count"] == EXPECTED_PLAYER_COUNT
    assert config["inherits_v1"]["supported_team_frame_count"] == EXPECTED_TEAM_COUNT
    assert config["inherits_v1"]["stable_lineup_run_count"] == EXPECTED_RUN_COUNT


def _rows(player, team):
    return [
        {"ceiling_m": ceiling, "player_saturation_fraction": p, "team_mean_saturation_fraction": t}
        for ceiling, p, t in zip(CANDIDATE_CEILINGS, player, team, strict=True)
    ]


def test_selection_uses_lowest_candidate_meeting_unchanged_thresholds():
    assert select_ceiling(_rows((0.049, 0.03, 0.02), (0.009, 0.004, 0.002))) == ("A_FREEZE_6_25_M", 6.25)
    assert select_ceiling(_rows((0.051, 0.049, 0.02), (0.005, 0.004, 0.002))) == ("B_FREEZE_6_50_M", 6.5)
    assert select_ceiling(_rows((0.08, 0.07, 0.06), (0.005, 0.004, 0.002))) == ("D_UNRESOLVED", None)
    with pytest.raises(ValueError, match="exactly the frozen v2 candidates"):
        select_ceiling(_rows((0.01, 0.01, 0.01), (0.0, 0.0, 0.0))[:2])


def test_raw_values_drive_saturation_and_perceptual_summaries():
    raw = np.array([[0, 1, 2, 3, 4, 5, 6.25, 6.26, 7, 8]], dtype=float)
    row = candidate_audit(raw, raw.mean(axis=1), 6.25)
    assert row["player_saturation_count"] == 3
    spread = perceptual_spread(raw.ravel(), 6.25)
    assert spread["saturated_fraction"] == pytest.approx(0.3)
    assert spread["p95_normalized"] == 1.0


def test_no_outcome_event_ball_or_game3_input_is_authorized():
    config = load_config()
    assert not config["reference_population"]["events_read"]
    assert not config["reference_population"]["ball_read"]
    assert not config["reference_population"]["game_3_accessed"]
    assert {"events", "ball", "scientific_outcomes", "skillcorner", "metrica_game_3"} <= set(config["prohibited_inputs"])


def test_scorer_hash_is_unchanged():
    actual = hashlib.sha256((ROOT / "src/defensive_reorganization_replay.py").read_bytes()).hexdigest()
    assert actual == SCORER_SHA256
