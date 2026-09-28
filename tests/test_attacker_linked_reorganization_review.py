from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from attacker_linked_reorganization_review import (
    AttackerLinkedReviewSpec,
    LinkReferenceThresholds,
    classify_episode_links,
    derive_reference_thresholds,
    rank_attacker_linked_episodes,
    summarize_off_ball_attackers,
    summarize_pair_geometry,
)
from run_attacker_linked_reorganization_review import (
    EpisodeSupportError,
    _require_open_play,
    _smoothed_cube,
    load_config,
)


def _geometry():
    frames = 51
    t = np.linspace(0, 2, frames)
    attackers = np.zeros((frames, 10, 2))
    defenders = np.zeros((frames, 10, 2))
    for index in range(10):
        attackers[:, index, 0] = index * 4 + t * (index + 1) / 5
        attackers[:, index, 1] = index
        defenders[:, index, 0] = index * 4 + 2 + t * index / 10
        defenders[:, index, 1] = index + 1
    ball = np.column_stack([t, np.zeros(frames)])
    return attackers, defenders, ball, tuple(f"a{i}" for i in range(10)), tuple(f"d{i}" for i in range(10))


def test_off_ball_nearest_ties_paths_and_input_immutability():
    attackers, _, ball, akeys, _ = _geometry()
    original = attackers.copy()
    # a0 and a1 are tied at the first frame; lexical a0 is excluded there.
    attackers[0, 1] = attackers[0, 0]
    summary = summarize_off_ball_attackers(attackers, ball, akeys)
    assert summary.loc[summary.attacker_key.eq("a0"), "off_ball_frame_count"].item() < 51
    assert summary.loc[summary.attacker_key.eq("a1"), "off_ball_frame_count"].item() == 51
    assert summary["attacker_path_m"].ge(0).all()
    np.testing.assert_allclose(attackers[1:], original[1:])


def test_exact_41_of_51_off_ball_boundary_and_missing_ball_fails():
    attackers, _, ball, akeys, _ = _geometry()
    # Make a9 nearest for ten frames, leaving exactly 41 off-ball frames.
    attackers[1:11, 9] = ball[1:11]
    summary = summarize_off_ball_attackers(attackers, ball, akeys)
    row = summary.loc[summary.attacker_key.eq("a9")].iloc[0]
    assert row.off_ball_frame_count == 41
    assert bool(row.off_ball_eligible)
    bad = ball.copy(); bad[4, 0] = np.nan
    with pytest.raises(ValueError):
        summarize_off_ball_attackers(attackers, bad, akeys)


def test_known_stationary_and_ball_relative_movement():
    attackers, _, ball, akeys, _ = _geometry()
    attackers[:, 2] = [20, 5]
    summary = summarize_off_ball_attackers(attackers, ball, akeys).set_index("attacker_key")
    assert summary.loc["a2", "attacker_path_m"] == pytest.approx(0)
    assert summary.loc["a2", "net_displacement_m"] == pytest.approx(0)
    assert summary.loc["a2", "attacker_minus_ball_path_m"] == pytest.approx(2)


def test_pair_geometry_oracles_and_coherence():
    attackers, defenders, ball, akeys, dkeys = _geometry()
    summary = summarize_off_ball_attackers(attackers, ball, akeys)
    contributions = np.arange(10, dtype=float)
    pairs = summarize_pair_geometry(
        attackers, defenders, akeys, dkeys, contributions, summary
    )
    row = pairs.loc[(pairs.attacker_key.eq("a0")) & (pairs.defender_key.eq("d9"))].iloc[0]
    assert bool(row.defender_top_three)
    assert row.start_distance_m == pytest.approx(np.linalg.norm(defenders[0, 9] - attackers[0, 0]))
    assert row.end_distance_m == pytest.approx(np.linalg.norm(defenders[-1, 9] - attackers[-1, 0]))
    assert row.relative_vector_path_m >= abs(row.signed_distance_change_m)
    assert -1 <= row.movement_direction_coherence <= 1
    stationary = attackers.copy(); stationary[:, 3] = stationary[0, 3]
    stationary_summary = summarize_off_ball_attackers(stationary, ball, akeys)
    stationary_pairs = summarize_pair_geometry(
        stationary, defenders, akeys, dkeys, contributions, stationary_summary
    )
    assert np.isnan(
        stationary_pairs.loc[
            (stationary_pairs.attacker_key.eq("a3"))
            & (stationary_pairs.defender_key.eq("d9")),
            "movement_direction_coherence",
        ].item()
    )


def test_reference_linear_quantiles():
    thresholds = derive_reference_thresholds([0, 1, 2, 3, 4], [0, 2, 4, 6, 8])
    assert thresholds.attacker_path_p75_m == pytest.approx(3)
    assert thresholds.relative_vector_path_p75_m == pytest.approx(6)


@pytest.mark.parametrize("trigger", ["distance", "change", "relative"])
def test_strong_link_each_geometry_trigger_and_boundaries(trigger):
    attackers = pd.DataFrame({
        "attacker_key": ["a"], "off_ball_eligible": [True], "attacker_path_m": [4.0]
    })
    pair = {
        "attacker_key": "a", "defender_key": "d", "attacker_off_ball_eligible": True,
        "attacker_path_m": 4.0, "defender_contribution_m": 2.0,
        "defender_top_three": True, "defender_above_median": True,
        "start_distance_m": 20.0, "end_distance_m": 20.0,
        "signed_distance_change_m": 0.0, "absolute_distance_change_m": 0.0,
        "minimum_distance_m": 9.0, "relative_vector_path_m": 4.0,
        "movement_direction_coherence": 0.0,
    }
    if trigger == "distance": pair["minimum_distance_m"] = 8.0
    elif trigger == "change": pair["absolute_distance_change_m"] = 3.0
    else: pair["relative_vector_path_m"] = 5.0
    result = classify_episode_links(
        attackers, pd.DataFrame([pair]), LinkReferenceThresholds(4, 5, 10, 30)
    )
    assert len(result.strong_links) == 1
    assert result.category == "localized"


def test_strong_link_rejects_low_movement_and_non_top_three():
    attackers = pd.DataFrame({
        "attacker_key": ["a"], "off_ball_eligible": [True], "attacker_path_m": [3.99]
    })
    pair = pd.DataFrame([{
        "attacker_key": "a", "defender_key": "d", "attacker_off_ball_eligible": True,
        "attacker_path_m": 3.99, "defender_contribution_m": 2.0,
        "defender_top_three": True, "defender_above_median": True,
        "start_distance_m": 7.0, "end_distance_m": 7.0,
        "signed_distance_change_m": 0.0, "absolute_distance_change_m": 0.0,
        "minimum_distance_m": 7.0, "relative_vector_path_m": 6.0,
        "movement_direction_coherence": 0.0,
    }])
    thresholds = LinkReferenceThresholds(4, 5, 10, 30)
    assert classify_episode_links(attackers, pair, thresholds).category == "none"
    pair["attacker_path_m"] = 4.0; pair["defender_top_three"] = False
    assert classify_episode_links(attackers, pair, thresholds).category == "none"
    pair["defender_top_three"] = True; pair["attacker_off_ball_eligible"] = False
    assert classify_episode_links(attackers, pair, thresholds).category == "none"


def test_link_category_boundaries():
    attackers = pd.DataFrame({
        "attacker_key": ["a"], "off_ball_eligible": [True], "attacker_path_m": [4.0]
    })
    base = {
        "attacker_key": "a", "attacker_off_ball_eligible": True,
        "attacker_path_m": 4.0, "defender_contribution_m": 2.0,
        "defender_top_three": True, "defender_above_median": True,
        "start_distance_m": 8.0, "end_distance_m": 8.0,
        "signed_distance_change_m": 0.0, "absolute_distance_change_m": 0.0,
        "minimum_distance_m": 8.0, "relative_vector_path_m": 0.0,
        "movement_direction_coherence": 0.0,
    }
    thresholds = LinkReferenceThresholds(4, 5, 10, 30)
    for count, category in ((0, "none"), (1, "localized"), (2, "localized"), (3, "distributed")):
        pairs = pd.DataFrame([base | {"defender_key": f"d{i}"} for i in range(count)])
        if count == 0:
            pairs = pd.DataFrame([base | {"defender_key": "d0", "defender_top_three": False}])
        result = classify_episode_links(attackers, pairs, thresholds)
        assert result.category == category
        assert len(result.strong_links) == count


def test_category_and_rankings_are_deterministic():
    rows = pd.DataFrame([
        {"team_key": "H", "period": 1, "peak_time_s": 3.0, "one_second_change_m": 2.0,
         "maximum_eligible_attacker_path_m": 6.0, "strong_link_count": 3, "linkage_category": "distributed"},
        {"team_key": "A", "period": 1, "peak_time_s": 2.0, "one_second_change_m": 1.5,
         "maximum_eligible_attacker_path_m": 8.0, "strong_link_count": 1, "linkage_category": "localized"},
        {"team_key": "H", "period": 2, "peak_time_s": 4.0, "one_second_change_m": 1.0,
         "maximum_eligible_attacker_path_m": 4.0, "strong_link_count": 0, "linkage_category": "none"},
    ])
    result = rank_attacker_linked_episodes(rows.sample(frac=1, random_state=7))
    assert result.rapid_ranking.iloc[0].linkage_category == "distributed"
    assert result.movement_ranking.iloc[0].linkage_category == "localized"
    assert result.density_ranking.iloc[0].strong_link_count == 3
    assert result.public_examples.public_selection_reason.tolist() == [
        "top_distributed", "top_localized", "top_none_contrast"
    ]


def test_frozen_config_and_historical_hashes_validate():
    config = load_config()
    assert config["strong_link"]["geometry_any"]["minimum_distance_m"]["value"] == 8.0
    assert config["strong_link"]["geometry_any"]["absolute_distance_change_m"]["value"] == 3.0
    assert config["off_ball"]["minimum_frames"] == 41


def test_frozen_candidate_population_excludes_transition_and_restart_contexts():
    candidates = pd.DataFrame({
        "rapid_context": ["open_play", "transition", "restart_adjacent", "ambiguous_context"],
        "episode": ["keep", "transition", "restart", "ambiguous"],
    })
    original = candidates.copy(deep=True)
    selected = _require_open_play(candidates)
    assert selected["episode"].tolist() == ["keep"]
    pd.testing.assert_frame_equal(candidates, original)
    with pytest.raises(RuntimeError, match="missing rapid_context"):
        _require_open_play(pd.DataFrame({"episode": ["missing"]}))


def test_incomplete_episode_support_fails_closed_without_generic_suppression():
    rows = []
    for frame in range(57):
        for player in range(9):
            rows.append({
                "match_id": "m", "period": 1, "entity_type": "player",
                "team_key": "A", "player_key": f"p{player}",
                "frame_id_provider": frame, "time_match_s": frame / 25,
                "coordinate_valid": True, "x_m": float(player), "y_m": 0.0,
            })
    with pytest.raises(EpisodeSupportError, match="ten stable"):
        _smoothed_cube(
            pd.DataFrame(rows), match_id="m", period=1, team_key="A",
            peak_time_s=2.12, excluded_player_key="gk", spec=AttackerLinkedReviewSpec(),
        )


def test_inactive_provider_columns_do_not_count_as_stable_identities():
    rows = []
    for frame in range(57):
        for player in range(10):
            rows.append({
                "match_id": "m", "period": 1, "entity_type": "player",
                "team_key": "A", "player_key": f"p{player}",
                "frame_id_provider": frame, "time_match_s": frame / 25,
                "coordinate_valid": True, "x_m": float(player), "y_m": float(frame) / 25,
            })
        rows.append({
            "match_id": "m", "period": 1, "entity_type": "player",
            "team_key": "A", "player_key": "inactive",
            "frame_id_provider": frame, "time_match_s": frame / 25,
            "coordinate_valid": False, "x_m": np.nan, "y_m": np.nan,
        })
    cube, keys = _smoothed_cube(
        pd.DataFrame(rows), match_id="m", period=1, team_key="A",
        peak_time_s=2.12, excluded_player_key="gk", spec=AttackerLinkedReviewSpec(),
    )
    assert cube.shape == (51, 10, 2)
    assert "inactive" not in keys
