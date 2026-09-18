from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, to_rgba
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_reorganization_replay import (  # noqa: E402
    DefensiveReorganizationScores,
    DefenderRelativePathSpec,
    score_trailing_defender_relative_path,
)
from defensive_reorganization_replay_visualization import (  # noqa: E402
    ATTACKER_COLOR,
    ATTACKER_TRAIL_COLOR,
    DEFAULT_SCORE_VMAX_M,
    DEFENDER_CMAP,
    DEFENDER_TRAIL_COLOR,
    PITCH_COLOR,
    SCORE_LABEL,
    animate_defensive_reorganization,
    plot_defensive_reorganization_diagnostic,
)
from tracking_animation import TrackingClipSpec  # noqa: E402
from generate_defensive_reorganization_replay_demo import EXPECTED_DEMO_QA  # noqa: E402


SCORER_SHA256 = "6b5f33de5a034ae4000270e847ebcefe0164b1df1d21d4f3a7ed8adf9bd24a8a"


def tracking(*, missing_frame: int | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    defender_starts = np.column_stack([np.linspace(-18, 18, 10), np.linspace(-12, 12, 10)])
    for frame in range(27):
        time_s = frame / 10.0
        for index, start in enumerate(defender_starts):
            valid = not (index == 4 and frame == missing_frame)
            rows.append(
                {
                    "match_id": "synthetic",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": time_s,
                    "entity_type": "player",
                    "team_key": "D",
                    "player_key": f"D{index}",
                    "x_m": float(start[0] + (time_s if index == 0 else 0.0)) if valid else np.nan,
                    "y_m": float(start[1]),
                    "coordinate_valid": valid,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
        for index, (x_m, y_m) in enumerate(((-22 + time_s, -4), (-14, 7))):
            rows.append(
                {
                    "match_id": "synthetic",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": time_s,
                    "entity_type": "player",
                    "team_key": "A",
                    "player_key": f"A{index}",
                    "x_m": float(x_m),
                    "y_m": float(y_m),
                    "coordinate_valid": True,
                    "pitch_length_m": 105.0,
                    "pitch_width_m": 68.0,
                }
            )
        rows.append(
            {
                "match_id": "synthetic",
                "period": 1,
                "frame_id_provider": str(frame),
                "time_match_s": time_s,
                "entity_type": "ball",
                "team_key": pd.NA,
                "player_key": pd.NA,
                "x_m": 0.0,
                "y_m": 0.0,
                "coordinate_valid": True,
                "pitch_length_m": 105.0,
                "pitch_width_m": 68.0,
            }
        )
    return pd.DataFrame(rows)


def clip_spec() -> TrackingClipSpec:
    return TrackingClipSpec(
        match_id="synthetic",
        period=1,
        anchor_time_s=2.3,
        start_time_s=2.1,
        end_time_s=2.5,
        focal_player_key="A0",
        attacking_team_key="A",
        defending_team_key="D",
    )


def score(data: pd.DataFrame) -> DefensiveReorganizationScores:
    return score_trailing_defender_relative_path(
        data,
        DefenderRelativePathSpec(
            defending_team_key="D", source_fps=10.0, smoothing_frames=3
        ),
    )


def finish(bundle) -> None:
    bundle.animation._draw_was_started = True
    plt.close(bundle.figure)


def with_known_supported_values(scores: DefensiveReorganizationScores) -> DefensiveReorganizationScores:
    players = scores.player_scores.copy(deep=True)
    teams = scores.team_scores.copy(deep=True)
    display = players["frame_id_provider"].isin(["21", "22", "23", "24", "25"])
    for frame_id in ["21", "22", "23", "24", "25"]:
        frame = display & players["frame_id_provider"].eq(frame_id)
        mapping = {f"D{index}": float(index) / 3.0 for index in range(10)}
        mapping["D0"] = 5.0
        players.loc[frame, "trailing_relative_path_m"] = players.loc[frame, "player_key"].map(mapping)
        team_value = players.loc[frame, "trailing_relative_path_m"].mean()
        teams.loc[teams["frame_id_provider"].eq(frame_id), "mean_trailing_relative_path_m"] = team_value
    return DefensiveReorganizationScores(players, teams, scores.metadata)


def test_exact_join_frame_step_duration_team_meter_and_trails():
    q = tracking()
    scores = score(q)
    bundle = animate_defensive_reorganization(
        q, scores, clip_spec(), frame_step=2, playback_fps=5.0, trail_seconds=.4
    )
    assert bundle.native_frame_count == 5
    assert bundle.displayed_frame_count == 3
    assert bundle.displayed_frame_ids == ("21", "23", "25")
    assert bundle.elapsed_duration_s == pytest.approx(.4)
    assert bundle.playback_duration_s == pytest.approx(.4)
    bundle.animation._draw_frame(1)
    state = bundle.animation._reorganization_state
    expected = scores.player_scores.loc[
        scores.player_scores["frame_id_provider"].eq("23")
    ].set_index("player_key")["trailing_relative_path_m"]
    assert state["player_scores_m"] == pytest.approx(expected.to_dict())
    expected_team = scores.team_scores.loc[
        scores.team_scores["frame_id_provider"].eq("23"), "mean_trailing_relative_path_m"
    ].item()
    assert state["team_mean_m"] == pytest.approx(expected_team)
    assert max(state["trail_point_counts"].values()) == 3  # clip begins at 2.1 s
    assert bundle.animation._reorganization_metadata["pitch_background"] == PITCH_COLOR
    finish(bundle)


def test_renderer_default_and_closed_demo_qa_use_frozen_625_scale():
    default = inspect.signature(animate_defensive_reorganization).parameters[
        "score_vmax_m"
    ].default
    assert default == 6.25
    assert EXPECTED_DEMO_QA == {
        "native_frame_count": 501,
        "displayed_frame_count": 251,
        "elapsed_duration_s": 20.0,
        "saturation_count": 134,
        "frames_at_least_1_saturated": 97,
        "frames_at_least_2_saturated": 37,
        "frames_at_least_5_saturated": 0,
        "team_mean_saturation_count": 0,
    }


def test_attackers_are_fixed_blue_defenders_use_warm_scale_and_ball_is_white():
    q = tracking()
    scores = with_known_supported_values(score(q))
    bundle = animate_defensive_reorganization(q, scores, clip_spec(), show_trails=True)
    bundle.animation._draw_frame(0)
    axis = bundle.figure.axes[0]
    scatters = {
        float(collection.get_sizes()[0]): collection
        for collection in axis.collections
        if len(collection.get_sizes()) == 1
    }
    assert ATTACKER_COLOR == "#1565c0"
    assert ATTACKER_TRAIL_COLOR == "#0b3d91"
    assert DEFENDER_TRAIL_COLOR == "#9a9a9a"
    assert DEFENDER_CMAP == "YlOrRd"
    assert scatters[75.0].get_facecolors()[0] == pytest.approx(to_rgba(ATTACKER_COLOR))
    assert scatters[145.0].get_facecolors()[0] == pytest.approx(to_rgba(ATTACKER_COLOR))
    assert scatters[35.0].get_facecolors()[0] == pytest.approx(to_rgba("white"))
    defender_faces = scatters[92.0].get_facecolors()
    expected = plt.get_cmap(DEFENDER_CMAP)(Normalize(0.0, 6.25)(5.0))
    assert any(np.allclose(face, expected) for face in defender_faces)
    assert not any(np.allclose(face, to_rgba(ATTACKER_COLOR)) for face in defender_faces)
    finish(bundle)


def test_fixed_display_scale_saturation_and_raw_values_are_preserved():
    q = tracking()
    scores = with_known_supported_values(score(q))
    original = scores.player_scores.copy(deep=True)
    default_bundle = animate_defensive_reorganization(q, scores, clip_spec(), frame_step=2)
    assert DEFAULT_SCORE_VMAX_M == 6.25
    assert default_bundle.animation._reorganization_metadata["score_vmin_m"] == 0.0
    assert default_bundle.animation._reorganization_metadata["score_vmax_m"] == 6.25
    assert default_bundle.animation._reorganization_metadata["saturation_count"] == 0
    meter = next(axis for axis in default_bundle.figure.axes if axis.get_xlabel() == "Team mean (m)")
    assert meter.get_xlim() == pytest.approx((0.0, 6.25))
    finish(default_bundle)

    bundle = animate_defensive_reorganization(
        q, scores, clip_spec(), frame_step=2, score_vmax_m=4.0
    )
    assert bundle.animation._reorganization_metadata["score_vmax_m"] == 4.0
    assert bundle.animation._reorganization_metadata["saturation_count"] == 3
    bundle.animation._draw_frame(0)
    state = bundle.animation._reorganization_state
    assert state["player_scores_m"]["D0"] == 5.0
    assert state["frame_saturation_count"] == 1
    pd.testing.assert_frame_equal(scores.player_scores, original)
    finish(bundle)


def test_unsupported_scores_are_hollow_and_team_meter_is_unavailable():
    q = tracking(missing_frame=10)
    scores = score(q)
    bundle = animate_defensive_reorganization(q, scores, clip_spec(), show_trails=False)
    bundle.animation._draw_frame(0)
    state = bundle.animation._reorganization_state
    assert state["supported_marker_count"] == 0
    assert state["unsupported_marker_count"] == 10
    assert state["team_mean_m"] is None
    assert bundle.animation._reorganization_metadata["unsupported_score_frame_count"] == 3
    finish(bundle)


@pytest.mark.parametrize("failure", ["duplicate", "missing", "timestamp"])
def test_score_join_fails_closed(failure):
    q = tracking()
    scores = score(q)
    players = scores.player_scores.copy(deep=True)
    teams = scores.team_scores.copy(deep=True)
    target = players["frame_id_provider"].eq("21") & players["player_key"].eq("D0")
    if failure == "duplicate":
        players = pd.concat([players, players.loc[target]], ignore_index=True)
        message = "duplicate player score"
    elif failure == "missing":
        players = players.loc[~target].copy()
        message = "ten player scores"
    else:
        players.loc[target, "time_match_s"] += .01
        message = "timestamps"
    malformed = DefensiveReorganizationScores(players, teams, scores.metadata)
    with pytest.raises(ValueError, match=message):
        animate_defensive_reorganization(q, malformed, clip_spec())


def test_static_diagnostic_is_bounded_and_has_no_background_heat_field():
    q = tracking()
    figure = plot_defensive_reorganization_diagnostic(q, score(q), clip_spec())
    assert figure._reorganization_metadata["pitch_background"] == PITCH_COLOR
    assert any(axis.get_ylabel() == SCORE_LABEL for axis in figure.axes)
    pitch_axes = [axis for axis in figure.axes if np.allclose(axis.get_facecolor()[:3], (49 / 255, 93 / 255, 58 / 255), atol=.01)]
    assert pitch_axes and all(not axis.images for axis in pitch_axes)
    assert "not better or worse defending" in " ".join(text.get_text() for text in figure.texts)
    score_axis = next(axis for axis in figure.axes if axis.get_ylabel() == SCORE_LABEL)
    assert score_axis.get_ylim() == pytest.approx((0.0, 6.25))
    plt.close(figure)


def test_rendering_metadata_is_deterministic():
    q = tracking()
    scores = score(q)
    first = animate_defensive_reorganization(q, scores, clip_spec())
    second = animate_defensive_reorganization(q.sample(frac=1, random_state=8), scores, clip_spec())
    assert dict(first.animation._reorganization_metadata) == dict(second.animation._reorganization_metadata)
    assert first.displayed_frame_ids == second.displayed_frame_ids
    finish(first)
    finish(second)


def test_committed_scorer_source_is_byte_identical():
    actual = hashlib.sha256((ROOT / "src/defensive_reorganization_replay.py").read_bytes()).hexdigest()
    assert actual == SCORER_SHA256


def test_public_notebook_has_exactly_five_output_free_nonreconstructive_cells():
    path = ROOT / "notebooks" / "defender_relative_replay_demo.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert len(notebook["cells"]) == 5
    assert [cell["cell_type"] for cell in notebook["cells"]] == [
        "markdown", "code", "code", "code", "code"
    ]
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
    text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "DISPLAY_CEILING_M == 6.25" in text
    assert "to_inline_html(bundle)" in text
    assert "response_2s_m" not in text
    assert "player_scores.to_" not in text
    assert "tracking.to_" not in text
