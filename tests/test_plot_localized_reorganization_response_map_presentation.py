"""Contracts for the aggregate-only presentation response-map renderer."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import plot_localized_reorganization_response_map_presentation as presentation  # noqa: E402


def test_centered_coordinates_map_to_exact_pitch_locations():
    x, y = presentation.centered_to_pitch(np.asarray([-52.5, 0.0, 52.5]), np.asarray([-34.0, 0.0, 34.0]))
    assert x.tolist() == [0.0, 52.5, 105.0]
    assert y.tolist() == [0.0, 34.0, 68.0]


def test_regulation_landmarks_are_exact_in_plot_coordinates():
    marks = presentation.pitch_landmarks()
    assert marks["halfway_line"] == (52.5,)
    assert marks["centre"] == (52.5, 34.0)
    assert marks["centre_circle_radius"] == (9.15,)
    assert marks["left_penalty_area"] == pytest.approx((0.0, 13.84, 16.5, 40.32))
    assert marks["right_penalty_area"] == pytest.approx((88.5, 13.84, 16.5, 40.32))
    assert marks["left_goal_area"] == pytest.approx((0.0, 24.84, 5.5, 18.32))
    assert marks["right_goal_area"] == pytest.approx((99.5, 24.84, 5.5, 18.32))
    assert marks["left_penalty_spot"] == (11.0, 34.0)
    assert marks["right_penalty_spot"] == (94.0, 34.0)
    pitch = presentation.pitch_model()
    assert (pitch.dim.length, pitch.dim.width, pitch.dim.center_length, pitch.dim.center_width) == (105.0, 68.0, 52.5, 34.0)


def test_closed_aggregate_package_and_presentation_scale_are_valid():
    hashes = presentation.verify_closed_package()
    assert hashes["figures/response_map.svg"] == "2d2817a96e367665c08f9e3657eb20e9917b612ea5906a123a8ab221bd0d29d0"
    aggregate, summary = presentation.load_aggregate_inputs()
    stats = presentation.validate_display_inputs(aggregate, summary)
    assert {h: int(stats[h]["saturation_count"]) for h in stats} == {5.0: 0, 7.5: 0, 10.0: 0}
    assert {h: int((aggregate[(aggregate.bandwidth_m == h) & aggregate.support_valid]).shape[0]) for h in presentation.VALID_CELLS} == presentation.VALID_CELLS


def test_h10_main_layout_is_presentation_only_and_h75_remains_primary():
    main, insets, label, subtitle = presentation.layout_spec("h10-main")
    assert (main, insets) == (10.0, (7.5,))
    assert label == "Near-complete-support presentation view"
    assert "h=7.5 remains the predeclared primary" in subtitle
    with pytest.raises(presentation.PresentationMapError, match="unknown presentation layout"):
        presentation.layout_spec("h12-main")


def test_h10_uses_only_closed_supported_cells_and_leaves_eight_cells_masked():
    aggregate, _ = presentation.load_aggregate_inputs()
    h10 = aggregate[aggregate.bandwidth_m == 10.0]
    assert h10.support_profile.eq("conservative").all()
    assert int(h10.support_valid.sum()) == 7132
    assert int((~h10.support_valid).sum()) == 8
    assert h10.loc[~h10.support_valid, "equal_match_local_mean_m"].isna().all()


def test_out_of_scale_aggregate_value_fails_instead_of_rescaling():
    aggregate, summary = presentation.load_aggregate_inputs()
    changed = aggregate.copy()
    changed.loc[(changed.bandwidth_m == 5.0) & changed.support_valid, "equal_match_local_mean_m"] = 0.56
    with pytest.raises(presentation.PresentationMapError, match="exceeds fixed"):
        presentation.validate_display_inputs(changed, summary)


def test_renderer_uses_only_compact_aggregate_inputs_and_writes_new_paths(tmp_path, monkeypatch):
    aggregate, summary = presentation.load_aggregate_inputs()
    presentation.validate_display_inputs(aggregate, summary)
    output = tmp_path / "presentation" / "response"
    presentation.render_presentation_map(aggregate, output)
    assert output.with_suffix(".png").is_file()
    assert output.with_suffix(".svg").is_file()
    assert all(not line.endswith((" ", "\t")) for line in output.with_suffix(".svg").read_text(encoding="utf-8").splitlines())
    assert presentation.DISPLAY_LIMIT_M == 0.55


def test_synthetic_presentation_render_is_deterministic(tmp_path):
    aggregate, summary = presentation.load_aggregate_inputs()
    presentation.validate_display_inputs(aggregate, summary)
    first, second = tmp_path / "first" / "response", tmp_path / "second" / "response"
    presentation.render_presentation_map(aggregate, first, "h10-main")
    presentation.render_presentation_map(aggregate, second, "h10-main")
    for suffix in (".png", ".svg"):
        assert first.with_suffix(suffix).read_bytes() == second.with_suffix(suffix).read_bytes()
