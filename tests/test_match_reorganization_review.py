import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from match_reorganization_review import analyze_match_reorganization
from run_match_reorganization_demo import run_demo



def _committed_inputs():
    ball = json.loads((ROOT / "figures/presentation/ball_alignment_reorganization_review/manifest.json").read_text())
    linked = json.loads((ROOT / "figures/presentation/attacker_linked_reorganization_review/manifest.json").read_text())
    rows = {}
    for field in ("historical_six_audit", "top_overall", "top_low_ballward", "top_high_ballward"):
        for row in ball.get(field, []):
            key = ("metrica_sample_game_2", row["team_key"], row["period"], row["peak_time_s"])
            rows[key] = {"match_id": key[0], **row}
    links = [{"match_id": "metrica_sample_game_2", **row} for row in linked["top_rapid_magnitude"]]
    return pd.DataFrame(rows.values()), pd.DataFrame(links)


def test_closed_examples_are_rule_derived_and_separated():
    ball, linked = _committed_inputs()
    result = analyze_match_reorganization(ball, linked)
    assert result.representative_examples.peak_time_s.tolist() == [5355.64, 336.76]
    assert result.diagnostic_examples.peak_time_s.tolist() == [4443.16, 978.32]
    assert result.rejected_examples.peak_time_s.tolist() == [1734.72]
    assert result.representative_examples.trajectory_integrity_status.eq(
        "trajectory_integrity_clean"
    ).all()
    groups = [
        set(frame.peak_time_s) for frame in (
            result.representative_examples, result.diagnostic_examples, result.rejected_examples
        )
    ]
    assert not groups[0] & groups[1]
    assert not groups[0] & groups[2]
    assert not groups[1] & groups[2]


def test_result_is_deterministic_and_inputs_are_unchanged():
    ball, linked = _committed_inputs()
    ball_before, linked_before = ball.copy(deep=True), linked.copy(deep=True)
    first = analyze_match_reorganization(ball.sample(frac=1, random_state=2), linked.sample(frac=1, random_state=3))
    second = analyze_match_reorganization(ball, linked)
    pd.testing.assert_frame_equal(first.rapid_episodes, second.rapid_episodes)
    pd.testing.assert_frame_equal(first.representative_examples, second.representative_examples)
    pd.testing.assert_frame_equal(ball, ball_before)
    pd.testing.assert_frame_equal(linked, linked_before)


def test_unsupported_alignment_is_explicit_and_never_representative():
    ball, linked = _committed_inputs()
    unsupported = ball.loc[ball.ballward_stratum.eq("unsupported")]
    assert not unsupported.empty
    result = analyze_match_reorganization(ball, linked)
    assert result.rapid_episodes.loc[
        result.rapid_episodes.ball_alignment_support_status.eq("unsupported"), "ballward_stratum"
    ].eq("unsupported").all()
    assert not result.representative_examples.ball_alignment_support_status.eq("unsupported").any()


def test_rejects_duplicate_episode_identity():
    ball, linked = _committed_inputs()
    with pytest.raises(ValueError, match="identities must be unique"):
        analyze_match_reorganization(pd.concat([ball, ball.iloc[[0]]]), linked)


def test_defensive_copy_properties():
    ball, linked = _committed_inputs()
    result = analyze_match_reorganization(ball, linked)
    clean = result.integrity_clean
    clean.loc[:, "team_score_m"] = -1
    assert (result.rapid_episodes.team_score_m >= 0).all()


def test_production_selection_contains_no_expected_timestamp_constants():
    source = (ROOT / "src/match_reorganization_review.py").read_text()
    for timestamp in ("5355.64", "336.76", "4443.16", "1734.72"):
        assert timestamp not in source


def test_demo_fails_closed_for_existing_destination(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        run_demo(destination)


def test_demo_fails_clearly_for_missing_public_data_root(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing public Metrica Sample Game 2"):
        run_demo(tmp_path / "output", data_root=tmp_path / "data", render_media=True)


def test_closed_demo_is_fast_deterministic_and_separates_outputs(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    result1 = run_demo(first)
    result2 = run_demo(second)
    assert result1 == result2
    assert result1["representative_example_count"] == 2
    assert result1["rejected_example_count"] == 1
    for name in (
        "rapid_episodes.csv", "representative_examples.csv",
        "diagnostic_examples.csv", "rejected_examples.csv", "summary.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()
