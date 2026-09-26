from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_application import (
    MOMENT_COLUMNS,
    MatchApplicationConfig,
    MomentDiscoverySpec,
    analyze_match,
    align_events,
    discover_moments,
    export_scores,
    score_match,
    score_stable_runs,
    _select_global_moments,
)
from defensive_reorganization_replay import DefensiveReorganizationScores
from run_metrica_game2_application import (
    add_analyst_context,
    audit_visual_suitability,
    classify_attacking_activity,
    select_analyst_moments,
)


def test_global_selection_deduplicates_overlapping_categories():
    rows = []
    for kind, time, score, change in (
        ("high", 10.0, 9.0, .1),
        ("rapid_increase", 10.5, 8.5, 2.0),
        ("rapid_increase", 30.0, 7.0, 1.5),
        ("low", 50.0, .5, -.1),
    ):
        row = {column: None for column in MOMENT_COLUMNS}
        row.update(
            moment_type=kind,
            match_id="m",
            period=1,
            team_key="D",
            peak_time_s=time,
            team_score_m=score,
            positive_change_m=change,
            interior_eligible=True,
        )
        rows.append(row)
    selected = _select_global_moments(
        pd.DataFrame(rows), 1, exclusion_seconds=6.0
    )
    assert selected.moment_type.tolist() == ["high", "low", "rapid_increase"]
    assert selected.loc[selected.moment_type.eq("rapid_increase"), "peak_time_s"].item() == 30.0
    assert not np.isclose(selected.peak_time_s, 10.5).any()


def _analyst_context_fixture() -> tuple[
    pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame
]:
    teams = {}
    for team, keeper in (("metrica:Home", "metrica:Home:11"), ("metrica:Away", "metrica:Away:25")):
        rows = []
        outfield = [f"{team}:{player}" for player in range(1, 11)]
        for time in (0.0, 1.0, 2.0):
            for index, player in enumerate(outfield):
                rows.append(
                    {
                        "period": 1,
                        "time_match_s": time,
                        "player_key": player,
                        "x_m": float(index + time),
                        "y_m": float(index),
                        "coordinate_valid": True,
                    }
                )
            rows.append(
                {
                    "period": 1,
                    "time_match_s": time,
                    "player_key": keeper,
                    "x_m": -50.0 if team == "metrica:Away" else 50.0,
                    "y_m": 0.0,
                    "coordinate_valid": True,
                }
            )
        teams[team] = pd.DataFrame(rows)
    ball = pd.DataFrame(
        {
            "period": [1, 1, 1],
            "time_match_s": [0.0, 1.0, 2.0],
            "x_m": [0.0, 10.0, 20.0],
            "y_m": [0.0, 0.0, 0.0],
            "coordinate_valid": [True, True, True],
        }
    )
    events = pd.DataFrame(
        [
            {"Period": 1, "Start Time [s]": .5, "Type": "PASS", "Subtype": "", "Team": "Away"},
            {"Period": 1, "Start Time [s]": 1.5, "Type": "PASS", "Subtype": "", "Team": "Away"},
        ]
    )
    moments = pd.DataFrame(
        [{"match_id": "m", "period": 1, "team_key": "metrica:Home", "peak_time_s": 1.0}]
    )
    return moments, teams, ball, events


def test_add_analyst_context_computes_on_ball_activity_and_fails_on_incomplete_shape():
    moments, teams, ball, events = _analyst_context_fixture()
    contextual = add_analyst_context(
        moments, teams, ball, events, context_seconds=1.0
    ).iloc[0]
    assert contextual.ball_path_length_m == pytest.approx(20.0)
    assert contextual.ball_progression_m == pytest.approx(20.0)
    assert contextual.directed_ball_progress_m == pytest.approx(20.0)
    assert contextual.attacking_action_count == 2
    assert contextual.attacking_on_ball_score == 4
    assert bool(contextual.meaningful_attacking_activity)

    incomplete = {key: value.copy() for key, value in teams.items()}
    away = incomplete["metrica:Away"]
    incomplete["metrica:Away"] = away.loc[
        ~(away["time_match_s"].eq(2.0) & away["player_key"].eq("metrica:Away:10"))
    ]
    with pytest.raises(RuntimeError, match="exactly ten outfield players"):
        add_analyst_context(moments, incomplete, ball, events, context_seconds=1.0)


def tracking(frames: int = 31) -> pd.DataFrame:
    rows = []
    for frame in range(frames):
        for player in range(10):
            rows.append(
                {
                    "match_id": "m",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": frame / 10,
                    "entity_type": "player",
                    "team_key": "D",
                    "player_key": f"D{player}",
                    "x_m": float(player + (frame / 10 if player == 0 else 0)),
                    "y_m": float(player),
                    "coordinate_valid": True,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
    return pd.DataFrame(rows)


def synthetic_scores() -> DefensiveReorganizationScores:
    team_values = [0, 1, 2, 8, 9, 8, 2, 1, 0, 5, 10, 5, 0]
    team_rows = []
    player_rows = []
    for frame, value in enumerate(team_values):
        team_rows.append(
            {
                "match_id": "m",
                "period": 1,
                "frame_id_provider": str(frame),
                "time_match_s": float(frame),
                "team_key": "D",
                "mean_trailing_relative_path_m": float(value),
                "supported_defender_count": 10,
                "support_status": "supported",
            }
        )
        for player in range(10):
            player_rows.append(
                {
                    "match_id": "m",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": float(frame),
                    "team_key": "D",
                    "player_key": f"D{player}",
                    "trailing_relative_path_m": float(value + player / 100),
                    "support_status": "supported",
                }
            )
    return DefensiveReorganizationScores(
        pd.DataFrame(player_rows), pd.DataFrame(team_rows), {"source_fps": 1.0}
    )


def test_score_match_filters_after_scoring_full_support():
    result = score_match(
        tracking(),
        defending_team_key="D",
        source_fps=10,
        smoothing_frames=3,
        window_seconds=1,
        start_time_s=1.1,
        end_time_s=1.3,
    )
    assert result.team_scores.time_match_s.tolist() == pytest.approx([1.1, 1.2, 1.3])
    assert result.team_scores.support_status.eq("supported").all()


def test_export_scores_writes_csv_parquet_and_metadata(tmp_path):
    result = score_match(
        tracking(), defending_team_key="D", source_fps=10, smoothing_frames=3, window_seconds=1
    )
    written = export_scores(result, tmp_path)
    assert set(written) == {
        "player_scores_csv",
        "player_scores_parquet",
        "team_scores_csv",
        "team_scores_parquet",
        "metadata_json",
    }
    assert len(pd.read_csv(written["player_scores_csv"])) == len(result.player_scores)
    assert len(pl.read_parquet(written["team_scores_parquet"])) == len(result.team_scores)
    assert json.loads(written["metadata_json"].read_text())["source_fps"] == 10


def test_moment_discovery_clusters_adjacent_peaks_and_returns_contributors():
    moments = discover_moments(
        synthetic_scores(),
        MomentDiscoverySpec(
            top_n_per_type=2,
            tail_fraction=.2,
            adjacency_seconds=1.1,
            interior_guard_seconds=0,
        ),
    )
    assert tuple(moments.columns) == MOMENT_COLUMNS
    assert set(moments.moment_type) == {"high", "low", "rapid_increase"}
    assert len(moments.query("moment_type == 'high'")) <= 2
    assert not moments.duplicated(["moment_type", "peak_time_s"]).any()
    leaders = json.loads(moments.iloc[0].leading_player_contributors)
    assert len(leaders) == 3
    assert leaders[0]["score_m"] >= leaders[-1]["score_m"]


def test_moment_discovery_is_deterministic_and_percentiles_are_bounded():
    settings = MomentDiscoverySpec(
        top_n_per_type=2,
        tail_fraction=.2,
        adjacency_seconds=1.1,
        interior_guard_seconds=0,
    )
    first = discover_moments(synthetic_scores(), settings)
    second = discover_moments(synthetic_scores(), settings)
    pd.testing.assert_frame_equal(first, second)
    assert first.within_match_percentile.between(0, 1).all()


def test_no_supported_scores_returns_empty_contract():
    scores = synthetic_scores()
    scores.team_scores["support_status"] = "missing_coordinate_support"
    scores.player_scores["support_status"] = "missing_coordinate_support"
    moments = discover_moments(scores)
    assert moments.empty
    assert tuple(moments.columns) == MOMENT_COLUMNS


def test_boundary_candidates_remain_auditable_but_are_not_selected():
    settings = MomentDiscoverySpec(
        top_n_per_type=2,
        tail_fraction=.2,
        adjacency_seconds=1.1,
        interior_guard_seconds=3,
    )
    audit = discover_moments(synthetic_scores(), settings, audit=True)
    assert audit.boundary_flag.any()
    assert not audit.loc[audit.boundary_flag, "selected_for_clip"].any()
    selected = discover_moments(synthetic_scores(), settings)
    assert selected.interior_eligible.all()
    assert selected.selected_for_clip.all()


def test_stable_run_scoring_splits_roster_changes_without_bridging():
    first = tracking(16)
    second = tracking(16).assign(
        frame_id_provider=lambda q: q.frame_id_provider.astype(int).add(16).astype(str),
        time_match_s=lambda q: q.time_match_s.add(1.6),
        player_key=lambda q: q.player_key.mask(q.player_key.eq("D9"), "D10"),
    )
    q = pd.concat([first, second], ignore_index=True)
    scores = score_stable_runs(
        q,
        defending_team_key="D",
        source_fps=10,
        smoothing_frames=3,
        window_seconds=1,
    )
    assert len(scores.metadata["stable_runs"]) == 2
    assert scores.metadata["stable_runs"][0]["end_time_s"] == pytest.approx(1.5)
    assert scores.metadata["stable_runs"][1]["start_time_s"] == pytest.approx(1.6)
    assert not scores.team_scores.duplicated(["period", "frame_id_provider"]).any()


def test_event_alignment_reports_current_windows_percentile_and_change():
    scores = synthetic_scores()
    events = pd.DataFrame(
        [
            {
                "event_id": "e1",
                "match_id": "m",
                "period": 1,
                "event_time_s": 10.0,
                "event_type": "SHOT",
                "team_key": "A",
            }
        ]
    )
    summary = align_events(events, scores, defending_team_key="D", lookbacks_seconds=(2, 5, 10))
    row = summary.iloc[0]
    assert row.score_at_event_m == pytest.approx(10)
    assert row.within_match_percentile == pytest.approx(1)
    assert row.previous_2s_mean_m == pytest.approx(5)
    assert row.previous_2s_peak_m == pytest.approx(10)
    assert row.previous_2s_change_m == pytest.approx(10)


def test_one_call_notebook_pipeline_records_defaults_and_exports_audit(tmp_path):
    defenders = tracking(81)
    attackers = tracking(81).assign(
        team_key="A",
        player_key=lambda q: "A" + q.player_key.str.removeprefix("D"),
        x_m=lambda q: q.x_m + 5,
    )
    normalized = pd.concat([defenders, attackers], ignore_index=True)
    events = pd.DataFrame(
        [
            {
                "event_id": "shot-1",
                "match_id": "m",
                "period": 1,
                "event_time_s": 5.0,
                "event_type": "SHOT",
                "team_key": "A",
            }
        ]
    )
    config = MatchApplicationConfig(
        source_fps=10,
        smoothing_frames=3,
        window_seconds=1,
        interior_guard_seconds=1.5,
        clip_context_seconds=.25,
        tail_fraction=.2,
        category_quota=1,
        event_lookbacks_seconds=(1, 2),
        export_formats=("csv",),
    )
    result = analyze_match(
        normalized,
        defending_team_keys=("D", "A"),
        config=config,
        events=events,
        output_dir=tmp_path,
    )
    assert result.metadata["interior_guard_seconds"] == 1.5
    assert result.metadata["category_quota"] == 1
    assert result.metadata["selection_policy"]["selection_scope"] == (
        "global across the two defending-team timelines"
    )
    assert not result.moment_audit.loc[
        result.moment_audit.boundary_flag, "selected_for_clip"
    ].any()
    assert len(result.event_summary) == 1
    assert Path(result.artifacts["moment_audit_csv"]).exists()
    assert Path(result.artifacts["application_metadata_json"]).exists()
    assert set(result.scores_by_team) == {"A", "D"}


def test_application_config_rejects_guard_shorter_than_score_plus_clip_context():
    with pytest.raises(ValueError, match="interior guard"):
        MatchApplicationConfig(
            source_fps=10,
            smoothing_frames=3,
            window_seconds=2,
            clip_context_seconds=3,
            interior_guard_seconds=4.9,
        )


def test_one_call_pipeline_is_deterministic_without_writes():
    defenders = tracking(81)
    attackers = tracking(81).assign(
        team_key="A",
        player_key=lambda q: "A" + q.player_key.str.removeprefix("D"),
        x_m=lambda q: q.x_m + 5,
    )
    normalized = pd.concat([defenders, attackers], ignore_index=True)
    config = MatchApplicationConfig(
        source_fps=10,
        smoothing_frames=3,
        window_seconds=1,
        interior_guard_seconds=1.5,
        clip_context_seconds=.25,
        tail_fraction=.2,
        category_quota=1,
    )
    first = analyze_match(
        normalized, defending_team_keys=("D", "A"), config=config
    )
    second = analyze_match(
        normalized.sample(frac=1, random_state=12),
        defending_team_keys=("D", "A"),
        config=config,
    )
    pd.testing.assert_frame_equal(first.moment_audit, second.moment_audit)
    pd.testing.assert_frame_equal(first.selected_moments, second.selected_moments)
    pd.testing.assert_frame_equal(first.distributions, second.distributions)
    assert first.artifacts == {}


def test_one_call_pipeline_rejects_unsupported_team_count_and_render_without_destination():
    config = MatchApplicationConfig(
        source_fps=10,
        smoothing_frames=3,
        window_seconds=1,
        interior_guard_seconds=1.5,
        clip_context_seconds=.25,
    )
    with pytest.raises(ValueError, match="exactly two"):
        analyze_match(tracking(81), defending_team_keys=("D",), config=config)

    multiple_matches = pd.concat(
        [tracking(81), tracking(81).assign(match_id="another")], ignore_index=True
    )
    with pytest.raises(ValueError, match="exactly one match"):
        analyze_match(
            multiple_matches, defending_team_keys=("D", "A"), config=config
        )

    defenders = tracking(81)
    attackers = tracking(81).assign(
        team_key="A",
        player_key=lambda q: "A" + q.player_key.str.removeprefix("D"),
    )
    with pytest.raises(ValueError, match="requires output_dir"):
        analyze_match(
            pd.concat([defenders, attackers], ignore_index=True),
            defending_team_keys=("D", "A"),
            config=config,
            render_selected=True,
        )


def test_visual_suitability_rejects_dead_ball_and_tracking_teleport():
    home = tracking(81).assign(team_key="metrica:Home")
    home["player_key"] = "metrica:Home:" + home.player_key.str.removeprefix("D")
    away = tracking(81).assign(team_key="metrica:Away")
    away["player_key"] = "metrica:Away:" + away.player_key.str.removeprefix("D")
    moments = pd.DataFrame(
        [
            {"period": 1, "peak_time_s": 2.0},
            {"period": 1, "peak_time_s": 5.0},
        ]
    )
    # The first window overlaps a ball-out-to-restart interval. The second
    # contains a gross but finite coordinate jump.
    events = pd.DataFrame(
        [
            {"Period": 1, "Start Time [s]": 1.0, "Type": "BALL OUT", "Subtype": np.nan},
            {"Period": 1, "Start Time [s]": 2.5, "Type": "SET PIECE", "Subtype": "THROW IN"},
        ]
    )
    away.loc[
        away.player_key.eq("metrica:Away:0") & away.time_match_s.eq(5.0), "x_m"
    ] += 10
    audited = audit_visual_suitability(
        moments,
        {"metrica:Home": home, "metrica:Away": away},
        events,
        clip_context_seconds=.5,
        max_visual_speed_mps=15,
    )
    assert audited.visual_suitable.tolist() == [False, False]
    assert "dead_ball_or_restart" in audited.iloc[0].visual_suitability_reason
    assert "tracking_discontinuity" in audited.iloc[1].visual_suitability_reason


def test_visual_suitability_requires_complete_ball_and_rejects_goal_kick():
    home = tracking(81).assign(team_key="metrica:Home")
    home["player_key"] = "metrica:Home:" + home.player_key.str.removeprefix("D")
    away = tracking(81).assign(team_key="metrica:Away")
    away["player_key"] = "metrica:Away:" + away.player_key.str.removeprefix("D")
    ball = tracking(81).drop_duplicates("frame_id_provider").copy()
    ball["entity_type"] = "ball"
    ball["team_key"] = pd.NA
    ball["player_key"] = pd.NA
    ball.loc[ball.time_match_s.eq(5.0), "coordinate_valid"] = False
    moments = pd.DataFrame(
        [{"period": 1, "peak_time_s": 2.0}, {"period": 1, "peak_time_s": 5.0}]
    )
    events = pd.DataFrame(
        [
            {
                "Period": 1,
                "Start Time [s]": 2.0,
                "Type": "PASS",
                "Subtype": "GOAL KICK",
            }
        ]
    )
    audited = audit_visual_suitability(
        moments,
        {"metrica:Home": home, "metrica:Away": away},
        events,
        ball_tracking=ball,
        clip_context_seconds=.5,
        source_fps=10,
    )
    assert "restart_event_in_clip" in audited.iloc[0].visual_suitability_reason
    assert "incomplete_ball_support" in audited.iloc[1].visual_suitability_reason


def test_analyst_selection_matches_context_and_deduplicates_categories():
    rows = []
    for kind, time, value, change, possession, zone in (
        ("high", 10.0, 6.0, .1, "A", "middle"),
        ("low", 40.0, .5, -.1, "A", "middle"),
        ("rapid_increase", 10.5, 5.8, .9, "A", "middle"),
        ("rapid_increase", 70.0, 5.0, .8, "A", "middle"),
    ):
        rows.append(
            {
                "moment_type": kind,
                "team_key": "D",
                "period": 1,
                "peak_time_s": time,
                "team_score_m": value,
                "positive_change_m": change,
                "possession_team_key": possession,
                "field_zone": zone,
                "visual_suitable": True,
                "meaningful_attacking_activity": kind != "rapid_increase" or time == 70.0,
                "attacking_activity_score": 4 if kind == "low" else 3,
            }
        )
    selected, metadata = select_analyst_moments(
        pd.DataFrame(rows),
        reviewed_primary={"high": ("D", 1, 10.0), "rapid_increase": ("D", 1, 70.0)},
    )
    assert selected.public_category.tolist() == [
        "high movement",
        "rapid increase",
        "conditional low response",
    ]
    assert selected.peak_time_s.tolist() == [10.0, 70.0, 40.0]
    assert selected.default_render.all()
    assert metadata["conditional_low_available"] is True
    assert metadata["conditional_low_activity_score"] == 4
    assert metadata["reviewed_primary_passages_preserved"] is True
    assert metadata["matched_defending_team"] is True
    assert metadata["matched_possession"] is True


def test_inert_low_passage_is_not_promoted_to_primary_comparison():
    rows = []
    for kind, time, value, change, active, activity in (
        ("high", 10.0, 6.0, .1, True, 4),
        ("low", 40.0, .5, -.1, False, 1),
        ("rapid_increase", 70.0, 5.0, .8, True, 3),
    ):
        rows.append(
            {
                "moment_type": kind,
                "team_key": "D",
                "period": 1,
                "peak_time_s": time,
                "team_score_m": value,
                "positive_change_m": change,
                "possession_team_key": "A",
                "field_zone": "middle",
                "visual_suitable": True,
                "meaningful_attacking_activity": active,
                "attacking_activity_score": activity,
            }
        )
    selected, metadata = select_analyst_moments(pd.DataFrame(rows))
    assert selected.moment_type.tolist() == ["high", "rapid_increase"]
    assert metadata["conditional_low_available"] is False


def test_attacking_activity_gate_is_transparent_and_requires_possession_proxy():
    score, eligible, components = classify_attacking_activity(
        possession_matches_attack=True,
        ball_path_length_m=15.0,
        endpoint_change_m=9.9,
        directed_ball_progress_m=5.0,
        attacking_action_count=1,
        attacker_centroid_shift_m=4.9,
        attacker_shape_change_m=5.0,
    )
    assert score == 3
    assert eligible is True
    assert components == {
        "ball_path_15m": True,
        "endpoint_change_10m": False,
        "directed_progress_5m": True,
        "two_attacking_actions": False,
        "attacker_centroid_shift_5m": False,
        "attacker_shape_change_5m": True,
    }
    _, shape_only_eligible, _ = classify_attacking_activity(
        possession_matches_attack=True,
        ball_path_length_m=5.0,
        endpoint_change_m=5.0,
        directed_ball_progress_m=0.0,
        attacking_action_count=0,
        attacker_centroid_shift_m=8.0,
        attacker_shape_change_m=8.0,
    )
    assert shape_only_eligible is False
    _, eligible_without_possession, _ = classify_attacking_activity(
        possession_matches_attack=False,
        ball_path_length_m=30.0,
        endpoint_change_m=20.0,
        directed_ball_progress_m=10.0,
        attacking_action_count=3,
        attacker_centroid_shift_m=8.0,
        attacker_shape_change_m=8.0,
    )
    assert eligible_without_possession is False
