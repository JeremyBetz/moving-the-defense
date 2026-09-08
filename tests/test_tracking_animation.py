from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tracking_animation import (
    REQUIRED_COLUMNS,
    TrackingClipSpec,
    _prepare,
    animate_tracking_window,
    centered_to_pitch,
    export_animation,
    to_inline_html,
)
from tracking_animation_metrica_demo import DEMO_SPEC, load_demo_tracking


def spec(**changes):
    values = dict(
        match_id="synthetic", period=1, anchor_time_s=0.4, start_time_s=0.0,
        end_time_s=0.8, focal_player_key="A1", attacking_team_key="A",
        defending_team_key="D", defender_ranks={"D1": 1, "D2": 2},
    )
    values.update(changes)
    return TrackingClipSpec(**values)


def tracking() -> pd.DataFrame:
    rows = []
    for i, time_s in enumerate(np.arange(0, .81, .04)):
        entities = [
            ("player", "A", "A1", -20 + i, -5, True),
            ("player", "A", "A2", -10, 8, True),
            # Defenders cross, but supplied ranks must not change.
            ("player", "D", "D1", 8 - i, 2, True),
            ("player", "D", "D2", -8 + i, -2, True),
            ("ball", pd.NA, pd.NA, 0, 0, True),
        ]
        for kind, team, player, x, y, valid in entities:
            rows.append(dict(
                match_id="synthetic", period=1, frame_id_provider=str(i),
                time_match_s=round(float(time_s), 2), entity_type=kind,
                team_key=team, player_key=player, x_m=float(x), y_m=float(y),
                coordinate_valid=valid, pitch_length_m=105.0, pitch_width_m=68.0,
            ))
    return pd.DataFrame(rows)


def bundle(data=None, **kwargs):
    result = animate_tracking_window(data if data is not None else tracking(), spec(), source_fps=25, **kwargs)
    return result


def finish(result):
    result.animation._draw_was_started = True
    plt.close(result.figure)


def test_required_schema_and_centered_transform():
    q = tracking().drop(columns=["x_m"])
    with pytest.raises(ValueError, match="Missing normalized"):
        bundle(q)
    x, y = centered_to_pitch([-52.5, 52.5], [-34, 34])
    np.testing.assert_allclose(x, [0, 105]); np.testing.assert_allclose(y, [0, 68])
    x2, _ = centered_to_pitch([60], [0])
    assert x2[0] == 112.5  # translation, never clipping


def test_deterministic_order_decimation_and_duration():
    q = tracking().sample(frac=1, random_state=4)
    result = bundle(q)
    assert result.native_frame_count == 21
    assert result.displayed_frame_count == 11
    assert result.displayed_frame_ids == tuple(str(i) for i in range(0, 21, 2))
    assert result.elapsed_duration_s == pytest.approx(.8)
    assert result.playback_duration_s == pytest.approx(.8)
    finish(result)


def test_input_is_unchanged_and_team_identity_persists():
    q = tracking(); original = q.copy(deep=True)
    prepared, _ = _prepare(q, spec(), 25)
    pd.testing.assert_frame_equal(q, original)
    assert prepared.loc[prepared.player_key == "A1", "team_key"].unique().tolist() == ["A"]


def test_focal_and_fixed_rank_styling_survives_crossing():
    result = bundle(show_trails=False)
    result.animation._draw_frame(10)
    texts = {text.get_text() for text in result.figure.axes[0].texts}
    assert {"D1", "D2"} <= texts
    # Rank labels remain tied to supplied identities rather than recomputed distance.
    d1 = tracking().query("player_key == 'D1' and frame_id_provider == '20'").iloc[0]
    label = next(text for text in result.figure.axes[0].texts if text.get_text() == "D1")
    assert label.get_position() == pytest.approx((d1.x_m + 52.5 + .8, d1.y_m + 34 + .8))
    finish(result)


def test_blinded_switches_remove_annotation_and_rank_cues():
    result = bundle(show_annotations=False, show_rank_highlights=False, show_trails=False)
    result.animation._draw_frame(0)
    assert all(text.get_text() == "" or text.get_text() == "Physical tracking replay" for text in result.figure.axes[0].texts)
    # Two ordinary team collections, focal, and ball; no rank-outline collections.
    assert len(result.figure.axes[0].collections) == 4
    finish(result)


def test_trails_are_backward_only_and_break_on_missing_support():
    q = tracking()
    q.loc[(q.player_key == "A2") & (q.frame_id_provider == "8"), ["coordinate_valid", "x_m", "y_m"]] = [False, np.nan, np.nan]
    result = bundle(q, trail_seconds=.4)
    result.animation._draw_frame(5)  # displayed source frame 10
    a2_lines = [line for line in result.figure.axes[0].lines if line.get_color() == "#ed8b32"]
    assert a2_lines
    assert max(a2_lines[-1].get_xdata()) == pytest.approx(42.5)  # A2 remains constant, post-gap tail only
    assert len(a2_lines[-1].get_xdata()) == 2
    finish(result)


def test_missing_ball_and_nonfocal_hide_without_interpolation():
    q = tracking()
    mask = (q.frame_id_provider == "10") & ((q.entity_type == "ball") | (q.player_key == "A2"))
    q.loc[mask, ["coordinate_valid", "x_m", "y_m"]] = [False, np.nan, np.nan]
    result = bundle(q, show_trails=False)
    result.animation._draw_frame(5)
    assert len(result.figure.axes[0].collections) == 4  # defender team, focal, two rank rings; no ball/A2
    finish(result)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda q: q.drop(q[(q.player_key == "A1") & (q.frame_id_provider == "2")].index), "Focal attacker"),
        (lambda q: q.drop(q[q.frame_id_provider == "2"].index), "cadence"),
        (lambda q: pd.concat([q, q.iloc[[0]]], ignore_index=True), "Duplicate"),
        (lambda q: q.assign(pitch_length_m=104.0), "105 x 68"),
        (lambda q: q.assign(time_match_s=q.time_match_s + 10), "unavailable"),
    ],
)
def test_malformed_tracking_fails(mutator, message):
    with pytest.raises(ValueError, match=message):
        bundle(mutator(tracking()))


def test_identity_change_fails():
    q = tracking(); q.loc[(q.player_key == "A2") & (q.frame_id_provider == "3"), "team_key"] = "D"
    with pytest.raises(ValueError, match="identity"):
        bundle(q)


def test_jshtml_and_supported_exports(tmp_path):
    result = bundle(frame_step=10, playback_fps=2.5)
    html = to_inline_html(result)
    assert "animation" in html.data.lower()
    path = export_animation(result, tmp_path / "clip.html")
    assert path.read_text(encoding="utf-8").startswith("\n<link") or "animation" in path.read_text(encoding="utf-8").lower()
    with pytest.raises(ValueError, match="Only"):
        export_animation(result, tmp_path / "clip.mp4")
    finish(result)


def test_renderer_does_not_require_or_discover_response_fields():
    assert not any("response" in column.lower() or "outcome" in column.lower() for column in REQUIRED_COLUMNS)
    q = tracking().assign(response_2s_m=np.arange(len(tracking())))
    result = bundle(q, show_trails=False)
    assert result.native_frame_count == 21
    finish(result)


@pytest.mark.provider_data
def test_real_game2_demo_is_structural_only():
    q = load_demo_tracking()
    prepared, frames = _prepare(q, DEMO_SPEC, 25)
    assert len(frames) == 151
    assert frames.time_match_s.iloc[-1] - frames.time_match_s.iloc[0] == pytest.approx(6.0)
    assert {DEMO_SPEC.focal_player_key, *DEMO_SPEC.defender_ranks} <= set(prepared.player_key.dropna())
    assert not any("response" in column.lower() or "outcome" in column.lower() for column in q.columns)
