from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_match_review import (
    PooledScoreReference,
    ReferenceMomentSpec,
    find_reorganization_windows,
)
from defensive_reorganization_replay import (
    PLAYER_SCORE_COLUMNS,
    TEAM_SCORE_COLUMNS,
    SUPPORTED,
    DefensiveReorganizationScores,
)
from possession_aware_defensive_review import (
    AMBIGUOUS,
    DEAD_BALL,
    IN_POSSESSION,
    OUT_OF_POSSESSION,
    DefensiveReviewEligibilitySpec,
    _normalize_events,
    build_metrica_possession_context,
    find_defensive_review_windows,
    metrica_event_endpoint_qc,
    possession_state_summary,
)


def frames(count: int = 251, *, periods: tuple[int, ...] = (1,)) -> pd.DataFrame:
    rows = []
    frame = 0
    for period in periods:
        for index in range(count):
            rows.append({
                "match_id": "m", "period": period, "frame_id_provider": frame,
                "time_match_s": (period - 1) * 20 + index / 25,
            })
            frame += 1
    return pd.DataFrame(rows)


def event(team: str, kind: str, frame: int, *, period: int = 1, subtype: str = "", end_frame: int | None = None) -> dict[str, object]:
    end = frame if end_frame is None else end_frame
    offset = (period - 1) * 20
    return {
        "Team": team, "Type": kind, "Subtype": subtype, "Period": period,
        "Start Frame": frame, "Start Time [s]": offset + (frame % 251) / 25,
        "End Frame": end, "End Time [s]": offset + (end % 251) / 25,
    }


def score_package(values: list[float], team: str, *, fps: float = 25.0) -> DefensiveReorganizationScores:
    team_rows, player_rows = [], []
    for index, value in enumerate(values):
        base = {
            "match_id": "m", "period": 1, "frame_id_provider": index,
            "time_match_s": index / fps, "team_key": team,
            "support_status": SUPPORTED,
        }
        team_rows.append({**base, "mean_trailing_relative_path_m": value, "supported_defender_count": 10})
        for player in range(10):
            player_rows.append({**base, "player_key": f"{team}:{player}", "trailing_relative_path_m": value + player / 100})
    return DefensiveReorganizationScores(
        pd.DataFrame(player_rows, columns=PLAYER_SCORE_COLUMNS),
        pd.DataFrame(team_rows, columns=TEAM_SCORE_COLUMNS),
        {"source_fps": fps, "stable_runs": [{
            "match_id": "m", "period": 1, "run_index": 1,
            "start_time_s": 0.0, "end_time_s": (len(values) - 1) / fps,
            "native_frame_count": len(values), "supported_frame_count": len(values),
        }]},
    )


def test_state_machine_is_fail_closed_and_buffer_starts_at_exactly_two_seconds():
    source = pd.DataFrame([
        event("Home", "SET PIECE", 0, subtype="KICK OFF"),
        event("Home", "BALL LOST", 25),
        event("Away", "RECOVERY", 30),
        event("Away", "BALL OUT", 100),
        event("Home", "SET PIECE", 125, subtype="THROW IN"),
    ])
    original = source.copy(deep=True)
    context = build_metrica_possession_context(source, frames(), match_id="m")
    home = context.loc[context.team_key.eq("metrica:Home")].set_index("frame_id_provider")
    assert home.loc[0, "possession_state"] == DEAD_BALL
    assert home.loc[1, "possession_state"] == IN_POSSESSION
    assert home.loc[25, "possession_state"] == AMBIGUOUS
    assert home.loc[30, "possession_state"] == OUT_OF_POSSESSION
    assert not bool(home.loc[79, "defensive_review_eligible"])
    assert bool(home.loc[80, "defensive_review_eligible"])
    assert home.loc[100, "possession_state"] == DEAD_BALL
    assert home.loc[125, "possession_state"] == DEAD_BALL
    assert home.loc[126, "possession_state"] == IN_POSSESSION
    pd.testing.assert_frame_equal(source, original)


def test_goal_out_and_implicit_restart_remain_excluded_at_restart_frame():
    source = pd.DataFrame([
        event("Home", "PASS", 0),
        event("Home", "SHOT", 20, subtype="ON TARGET-GOAL", end_frame=25),
        event("Away", "RECOVERY", 75),
    ])
    context = build_metrica_possession_context(source, frames(101), match_id="m")
    away = context.loc[context.team_key.eq("metrica:Away")].set_index("frame_id_provider")
    assert away.loc[24, "possession_state"] == OUT_OF_POSSESSION
    assert away.loc[25, "possession_state"] == DEAD_BALL
    assert away.loc[75, "possession_state"] == DEAD_BALL
    assert away.loc[76, "possession_state"] == IN_POSSESSION


def test_period_boundary_never_carries_possession_and_conflicts_fail_closed():
    native = frames(51, periods=(1, 2))
    source = pd.DataFrame([
        event("Home", "PASS", 0, period=1),
        event("Away", "PASS", 51, period=2),
    ])
    source.loc[1, ["Start Time [s]", "End Time [s]"]] = 20.0
    context = build_metrica_possession_context(source, native, match_id="m")
    home = context.loc[context.team_key.eq("metrica:Home")]
    assert home.loc[home.period.eq(2)].iloc[0].possession_state == OUT_OF_POSSESSION
    conflicting = pd.DataFrame([event("Home", "PASS", 0), event("Away", "RECOVERY", 0)])
    with pytest.raises(ValueError, match="conflicting possession teams"):
        build_metrica_possession_context(conflicting, frames(10), match_id="m")
    contradictory = pd.DataFrame([event("Home", "PASS", 0, period=2)])
    with pytest.raises(ValueError, match="event period is absent"):
        build_metrica_possession_context(contradictory, frames(10), match_id="m")


def test_challenge_never_establishes_possession_and_nonfinite_clock_fails():
    source = pd.DataFrame([event("Home", "CHALLENGE", 10)])
    context = build_metrica_possession_context(source, frames(30), match_id="m")
    assert set(context.possession_state) == {AMBIGUOUS}
    bad = source.copy(); bad.loc[0, "Start Time [s]"] = np.nan
    with pytest.raises(ValueError, match="event start times must be finite"):
        build_metrica_possession_context(bad, frames(30), match_id="m")


def test_unused_malformed_endpoint_is_preserved_tolerated_and_reported():
    source = pd.DataFrame([
        event("Home", "SET PIECE", 1, subtype="KICK OFF", end_frame=0),
        event("Home", "PASS", 2),
    ])
    original = source.copy(deep=True)
    normalized = _normalize_events(source)
    assert normalized.loc[0, "End Frame"] == 0
    assert normalized.loc[0, "End Time [s]"] == 0.0
    assert bool(normalized.loc[0, "end_metadata_malformed"])
    qc = metrica_event_endpoint_qc(source)
    assert dict(qc) == {
        "total_event_count": 2,
        "endpoint_required_count": 0,
        "malformed_unused_end_count": 1,
        "malformed_required_end_count": 0,
        "tolerated_unused_end_count": 1,
        "blocked_required_end_count": 0,
    }
    context = build_metrica_possession_context(source, frames(10), match_id="m")
    assert context.attrs["event_endpoint_qc"] == dict(qc)
    pd.testing.assert_frame_equal(source, original)


def test_malformed_required_endpoint_blocks_without_repair():
    source = pd.DataFrame([
        event("Home", "SHOT", 2, subtype="ON TARGET-GOAL", end_frame=1),
    ])
    original = source.copy(deep=True)
    qc = metrica_event_endpoint_qc(source)
    assert qc["malformed_required_end_count"] == 1
    assert qc["blocked_required_end_count"] == 1
    with pytest.raises(ValueError, match="required Metrica event endpoint is malformed"):
        build_metrica_possession_context(source, frames(10), match_id="m")
    pd.testing.assert_frame_equal(source, original)


def test_disordered_or_unreconciled_start_still_blocks():
    disordered = pd.DataFrame([event("Home", "PASS", 2), event("Home", "PASS", 1)])
    with pytest.raises(ValueError, match="event starts are disordered"):
        build_metrica_possession_context(disordered, frames(10), match_id="m")
    mismatch = pd.DataFrame([event("Home", "PASS", 2)])
    mismatch.loc[0, "Start Time [s]"] = 0.09
    mismatch.loc[0, "End Time [s]"] = 0.09
    with pytest.raises(ValueError, match="start time cannot be reconciled"):
        build_metrica_possession_context(mismatch, frames(10), match_id="m")


def test_required_endpoint_must_reconcile_to_native_tracking():
    missing = pd.DataFrame([
        event("Home", "SHOT", 2, subtype="ON TARGET-GOAL", end_frame=20),
    ])
    with pytest.raises(ValueError, match="required event end frame cannot be reconciled"):
        build_metrica_possession_context(missing, frames(10), match_id="m")
    mismatch = pd.DataFrame([
        event("Home", "SHOT", 2, subtype="ON TARGET-GOAL", end_frame=3),
    ])
    mismatch.loc[0, "End Time [s]"] = 0.13
    with pytest.raises(ValueError, match="required event end time cannot be reconciled"):
        build_metrica_possession_context(mismatch, frames(10), match_id="m")


def test_defensive_selector_keeps_thresholds_but_excludes_ineligible_peaks_and_splits_states():
    values = [1.0] * 251
    values[20:55] = [9.0] * 35       # in-possession high: excluded
    values[105:170] = [9.0] * 65     # out-of-possession but buffer ends at 130
    values[200:235] = [0.1] * 35     # eligible low
    scores = score_package(values, "metrica:Home")
    reference = PooledScoreReference(
        np.linspace(0, 10, 101), np.linspace(0, 8.4, 101), np.linspace(-1, .5, 101), 25, {}
    )
    source = pd.DataFrame([
        event("Home", "SET PIECE", 0, subtype="KICK OFF"),
        event("Away", "RECOVERY", 80),
    ])
    context = build_metrica_possession_context(source, frames(), match_id="m")
    raw, _ = find_reorganization_windows(
        {"metrica:Home": scores}, reference,
        ReferenceMomentSpec(render_context_seconds=.5, selection_per_category=2),
    )
    result = find_defensive_review_windows(
        {"metrica:Home": scores}, reference, context,
        moment_spec=ReferenceMomentSpec(render_context_seconds=.5, selection_per_category=2),
    )
    assert len(raw.loc[raw.moment_type.eq("high")]) == 2
    high = result.moments.loc[result.moments.moment_type.eq("high")]
    assert len(high) == 1
    assert high.start_time_s.item() == pytest.approx(130 / 25)
    assert high.defensive_review_eligible.all()
    assert result.moments.loc[result.moments.moment_type.eq("low")].shape[0] == 1
    assert result.metadata["thresholds_unchanged"] is True


def test_rapid_requires_both_endpoints_in_same_eligible_state_run():
    values = [1.0] * 251
    values[100:] = [3.0] * 151
    values[200:] = [6.0] * 51
    scores = score_package(values, "metrica:Home")
    reference = PooledScoreReference(
        np.linspace(0, 10, 101), np.linspace(0, 10, 101), np.linspace(-1, 1, 101), 25, {}
    )
    source = pd.DataFrame([
        event("Away", "PASS", 0),
        event("Home", "PASS", 90),
        event("Away", "RECOVERY", 100),
    ])
    context = build_metrica_possession_context(source, frames(), match_id="m")
    result = find_defensive_review_windows(
        {"metrica:Home": scores}, reference, context,
        moment_spec=ReferenceMomentSpec(render_context_seconds=.5),
    )
    rapid = result.moments.loc[result.moments.moment_type.eq("rapid_increase")]
    assert not rapid.empty
    assert rapid.peak_time_s.min() >= 200 / 25


def test_transition_window_is_closed_and_historical_audit_is_explicit():
    values = [9.0] * 251
    scores = score_package(values, "metrica:Home")
    reference = PooledScoreReference(
        np.linspace(0, 10, 101), np.linspace(0, 8.4, 101), np.linspace(-1, .5, 101), 25, {}
    )
    source = pd.DataFrame([event("Home", "PASS", 0), event("Away", "RECOVERY", 100)])
    context = build_metrica_possession_context(source, frames(), match_id="m")
    historical = pd.DataFrame([
        {"moment_type": "high", "team_key": "metrica:Home", "period": 1, "peak_time_s": 0.8},
        {"moment_type": "high", "team_key": "metrica:Home", "period": 1, "peak_time_s": 4.0},
        {"moment_type": "high", "team_key": "metrica:Home", "period": 1, "peak_time_s": 6.0},
    ])
    result = find_defensive_review_windows(
        {"metrica:Home": scores}, reference, context,
        moment_spec=ReferenceMomentSpec(render_context_seconds=.5),
        historical_selected=historical,
    )
    transition_frames = result.possession_timelines["metrica:Home"]
    offsets = transition_frames["nearest_possession_change_offset_s"]
    assert offsets.abs().le(2.0 + 1e-9).any()
    assert result.historical_selection_audit.classification.tolist() == [
        "evaluated_team_in_possession", "transition_context", "still_defensively_eligible"
    ]


def test_state_summary_is_aggregate_and_source_hash_is_frozen():
    source = pd.DataFrame([event("Away", "PASS", 0)])
    context = build_metrica_possession_context(source, frames(60), match_id="m")
    summary = possession_state_summary(context)
    assert set(summary.columns) == {
        "team_key", "period", "possession_state", "frame_count", "eligible_frame_count"
    }
    assert not {"frame_id_provider", "time_match_s", "possession_team_key"}.intersection(summary.columns)
    event_path = ROOT / "data/metrica_sample_game_2/Sample_Game_2_RawEventsData.csv"
    assert hashlib.sha256(event_path.read_bytes()).hexdigest() == "edf31a18599265b77a8baf150f2ce6d89456fb0324b62ea7a391229657a619ba"


def test_public_v2_package_is_aggregate_and_historical_v1_bytes_are_unchanged():
    v2 = ROOT / "figures/presentation/possession_aware_defensive_review"
    manifest = json.loads((v2 / "manifest.json").read_text())
    assert manifest["measurement"] == "team relational reorganization in raw metres"
    assert manifest["possession_source"].endswith("not provider ground truth")
    assert manifest["qc"] == {
        "both_teams_and_periods_have_eligible_support": True,
        "event_alignment_unchanged": True,
        "historical_v1_package_modified": False,
        "native_state_rows_published": False,
        "raw_scores_unchanged": True,
        "reference_percentiles_unchanged": True,
        "tactical_or_causal_claim_created": False,
    }
    expected_files = {"manifest.json", *manifest["files_sha256"]}
    assert {path.name for path in v2.iterdir() if path.is_file()} == expected_files
    assert not any(path.suffix in {".csv", ".parquet"} for path in v2.iterdir())
    for name, expected_hash in manifest["files_sha256"].items():
        assert hashlib.sha256((v2 / name).read_bytes()).hexdigest() == expected_hash

    v1 = ROOT / "figures/presentation/full_match_application_case_study"
    v1_manifest = json.loads((v1 / "manifest.json").read_text())
    for name, expected_hash in v1_manifest["files_sha256"].items():
        assert hashlib.sha256((v1 / name).read_bytes()).hexdigest() == expected_hash


def test_endpoint_compatibility_qc_is_aggregate_and_complete():
    qc_path = ROOT / "outputs/metrica_event_endpoint_compatibility/compatibility_qc.json"
    qc = json.loads(qc_path.read_text())
    assert qc["status"] == "COMPATIBILITY_RULE_IMPLEMENTED_AND_VALIDATED"
    assert qc["no_provider_rows_serialized"] is True
    assert qc["games"]["game_1"]["endpoint_qc"] == {
        "blocked_required_end_count": 0,
        "endpoint_required_count": 15,
        "malformed_required_end_count": 0,
        "malformed_unused_end_count": 1,
        "tolerated_unused_end_count": 1,
        "total_event_count": 1745,
    }
    assert qc["games"]["game_2"]["endpoint_qc"]["malformed_unused_end_count"] == 0
    serialized = json.dumps(qc).lower()
    assert not any(
        forbidden in serialized
        for forbidden in ("start time [s]", "end time [s]", "frame_id_provider", "player_key")
    )
