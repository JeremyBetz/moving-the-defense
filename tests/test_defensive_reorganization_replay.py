from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_coverage_redistribution_v2 import focal_relative_path_lengths
from defensive_reorganization_replay import (
    INSUFFICIENT_FUTURE,
    INSUFFICIENT_HISTORY,
    MISSING_COORDINATES,
    PLAYER_SCORE_COLUMNS,
    SUPPORTED,
    TEAM_SCORE_COLUMNS,
    DefenderRelativePathSpec,
    defender_relative_path_lengths,
    normalize_scores_for_display,
    score_trailing_defender_relative_path,
)


FPS = 10.0


def tracking(frames: int = 41, source_fps: float = FPS) -> pd.DataFrame:
    rows: list[dict] = []
    starts = np.column_stack([np.linspace(-20, 20, 10), np.linspace(-12, 12, 10)])
    for frame in range(frames):
        time_s = frame / source_fps
        for player, xy in enumerate(starts):
            rows.append(
                {
                    "match_id": "synthetic",
                    "period": 1,
                    "frame_id_provider": str(frame),
                    "time_match_s": time_s,
                    "entity_type": "player",
                    "team_key": "D",
                    "player_key": f"D{player}",
                    "x_m": float(xy[0]),
                    "y_m": float(xy[1]),
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


def spec(**changes) -> DefenderRelativePathSpec:
    values = {
        "defending_team_key": "D",
        "source_fps": FPS,
        "window_seconds": 2.0,
        "smoothing_frames": 3,
    }
    values.update(changes)
    return DefenderRelativePathSpec(**values)


def move_player(data: pd.DataFrame, player: str, x_values, y_values=None) -> pd.DataFrame:
    q = data.copy(deep=True)
    mask = q["player_key"].eq(player)
    x = np.asarray(x_values, dtype=float)
    if len(x) != mask.sum():
        raise AssertionError("fixture length mismatch")
    q.loc[mask, "x_m"] = q.loc[mask, "x_m"].to_numpy(float) + x
    if y_values is not None:
        q.loc[mask, "y_m"] = q.loc[mask, "y_m"].to_numpy(float) + np.asarray(y_values, dtype=float)
    return q


def supported_at(result, frame: str) -> pd.DataFrame:
    return result.player_scores.loc[result.player_scores["frame_id_provider"].astype(str).eq(frame)]


def test_common_translation_is_zero_and_input_is_unchanged():
    q = tracking()
    q.loc[q.entity_type.eq("player"), "x_m"] += q.loc[q.entity_type.eq("player"), "time_match_s"]
    original = q.copy(deep=True)
    result = score_trailing_defender_relative_path(q, spec())
    pd.testing.assert_frame_equal(q, original)
    values = result.player_scores.loc[result.player_scores.support_status.eq(SUPPORTED), "trailing_relative_path_m"]
    np.testing.assert_allclose(values, 0.0, atol=1e-12)


def test_one_defender_deviation_has_independent_leave_one_out_oracle():
    q = move_player(tracking(), "D0", np.arange(41) / FPS)
    result = score_trailing_defender_relative_path(q, spec())
    values = supported_at(result, "39").sort_values("player_key").trailing_relative_path_m.to_numpy()
    assert values[0] == pytest.approx(2.0)
    np.testing.assert_allclose(values[1:], 2.0 / 9.0)


def test_uniform_expansion_matches_independent_oracle():
    q = tracking()
    player_mask = q.entity_type.eq("player")
    factors = 1.0 + q.loc[player_mask, "time_match_s"].to_numpy(float)[:, None] * 0.02
    xy = q.loc[player_mask, ["x_m", "y_m"]].to_numpy(float)
    q.loc[player_mask, ["x_m", "y_m"]] = xy * factors
    result = score_trailing_defender_relative_path(q, spec())
    final = supported_at(result, "39").sort_values("player_key")
    starts = tracking().query("entity_type == 'player' and frame_id_provider == '0'").sort_values("player_key")[["x_m", "y_m"]].to_numpy()
    centred = starts - starts.mean(axis=0)
    expected = np.linalg.norm((10.0 / 9.0) * centred, axis=1) * 0.04
    np.testing.assert_allclose(final.trailing_relative_path_m, expected, atol=1e-12)


def test_rotation_about_translating_centroid_is_positive():
    q = tracking()
    player_mask = q.entity_type.eq("player")
    for frame in range(41):
        mask = player_mask & q.frame_id_provider.eq(str(frame))
        xy = q.loc[mask, ["x_m", "y_m"]].to_numpy(float)
        centre = xy.mean(axis=0)
        angle = frame * 0.002
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        q.loc[mask, ["x_m", "y_m"]] = (xy - centre) @ rotation.T + centre + [frame / 10, 0]
    result = score_trailing_defender_relative_path(q, spec())
    assert (supported_at(result, "39").trailing_relative_path_m > 0).all()


def test_accumulated_path_is_not_net_displacement():
    excursion = np.zeros(41)
    excursion[12:23] = np.linspace(0, 2, 11)
    excursion[22:33] = np.linspace(2, 0, 11)
    q = move_player(tracking(), "D0", excursion)
    result = score_trailing_defender_relative_path(q, spec())
    value = supported_at(result, "32").sort_values("player_key").iloc[0].trailing_relative_path_m
    assert value > 3.0
    assert excursion[32] - excursion[12] == pytest.approx(0.0)


def test_trailing_window_and_centered_smoother_timing():
    q = move_player(tracking(), "D0", np.arange(41) ** 2 / 100.0)
    result = score_trailing_defender_relative_path(q, spec())
    target = 30
    raw = q.query("team_key == 'D'").pivot(index="frame_id_provider", columns="player_key", values=["x_m", "y_m"])
    raw = raw.reindex([str(i) for i in range(41)])
    trajectory = np.stack([
        raw.xs(axis=1, level=0, key=axis).reindex(columns=[f"D{i}" for i in range(10)]).to_numpy()
        for axis in ("x_m", "y_m")
    ], axis=2)
    smoothed = np.stack([trajectory[i - 1:i + 2].mean(axis=0) for i in range(target - 20, target + 1)])
    expected = defender_relative_path_lengths(smoothed)
    actual = supported_at(result, str(target)).sort_values("player_key").trailing_relative_path_m
    np.testing.assert_allclose(actual, expected)


def test_edge_support_statuses_are_explicit():
    result = score_trailing_defender_relative_path(tracking(), spec())
    assert result.team_scores.iloc[0].support_status == INSUFFICIENT_HISTORY
    assert result.team_scores.iloc[20].support_status == INSUFFICIENT_HISTORY
    assert result.team_scores.iloc[21].support_status == SUPPORTED
    assert result.team_scores.iloc[-1].support_status == INSUFFICIENT_FUTURE


def test_25_hz_seven_frame_support_has_exact_window_and_edges():
    source_fps = 25.0
    q = tracking(frames=61, source_fps=source_fps)
    q = move_player(q, "D0", np.arange(61, dtype=float) ** 2 / 625.0)
    settings = spec(source_fps=source_fps, smoothing_frames=7)
    result = score_trailing_defender_relative_path(q, settings)

    statuses = result.team_scores["support_status"].tolist()
    assert statuses[52] == INSUFFICIENT_HISTORY
    assert statuses[53] == SUPPORTED
    assert statuses[57] == SUPPORTED
    assert statuses[58:] == [INSUFFICIENT_FUTURE] * 3
    assert result.metadata["window_increments"] == 50
    assert result.metadata["smoother_future_support_seconds"] == pytest.approx(0.12)

    raw = q.query("team_key == 'D'").pivot(
        index="frame_id_provider", columns="player_key", values=["x_m", "y_m"]
    ).reindex([str(i) for i in range(61)])
    trajectory = np.stack(
        [
            raw.xs(axis=1, level=0, key=axis)
            .reindex(columns=[f"D{i}" for i in range(10)])
            .to_numpy()
            for axis in ("x_m", "y_m")
        ],
        axis=2,
    )
    target = 53
    smoothed = np.stack(
        [trajectory[position - 3 : position + 4].mean(axis=0) for position in range(3, 54)]
    )
    assert len(smoothed) == 51
    expected = defender_relative_path_lengths(smoothed)
    actual = (
        supported_at(result, str(target))
        .sort_values("player_key")
        .trailing_relative_path_m.to_numpy()
    )
    np.testing.assert_allclose(actual, expected)
    assert q.loc[q.frame_id_provider.eq("0"), "time_match_s"].iloc[0] == pytest.approx(
        target / source_fps - 2.12
    )
    assert q.loc[q.frame_id_provider.eq("56"), "time_match_s"].iloc[0] == pytest.approx(
        target / source_fps + 0.12
    )


def test_period_boundary_never_supplies_trailing_history():
    first = tracking()
    second = tracking().assign(period=2, time_match_s=lambda q: q.time_match_s + 45 * 60)
    result = score_trailing_defender_relative_path(pd.concat([first, second], ignore_index=True), spec())
    period_two = result.team_scores.loc[result.team_scores.period.eq(2)].reset_index(drop=True)
    assert period_two.iloc[0].support_status == INSUFFICIENT_HISTORY
    assert period_two.iloc[20].support_status == INSUFFICIENT_HISTORY
    assert period_two.iloc[21].support_status == SUPPORTED


def test_one_missing_coordinate_invalidates_complete_team_window():
    q = tracking()
    mask = q.player_key.eq("D4") & q.frame_id_provider.eq("25")
    q.loc[mask, ["coordinate_valid", "x_m", "y_m"]] = [False, np.nan, np.nan]
    result = score_trailing_defender_relative_path(q, spec())
    target = result.team_scores.loc[result.team_scores.frame_id_provider.eq("30")].iloc[0]
    assert target.support_status == MISSING_COORDINATES
    assert target.supported_defender_count == 0
    assert np.isnan(target.mean_trailing_relative_path_m)
    players = supported_at(result, "30")
    assert players.trailing_relative_path_m.isna().all()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda q: pd.concat([q, q.iloc[[0]]], ignore_index=True), "Duplicate"),
        (lambda q: q.assign(pitch_width_m=67.0), "105 x 68"),
        (lambda q: q.assign(time_match_s=q.time_match_s.where(~q.frame_id_provider.eq("8"), 0.85)), "cadence"),
    ],
)
def test_malformed_tracking_fails_closed(mutation, message):
    with pytest.raises(ValueError, match=message):
        score_trailing_defender_relative_path(mutation(tracking()), spec())


def test_identity_change_and_extra_defender_fail_closed():
    q = tracking()
    q.loc[q.player_key.eq("D1") & q.frame_id_provider.eq("3"), "team_key"] = "X"
    with pytest.raises(ValueError, match="identity"):
        score_trailing_defender_relative_path(q, spec())
    extra = tracking().query("player_key == 'D0'").copy()
    extra["player_key"] = "D10"
    with pytest.raises(ValueError, match="exactly ten"):
        score_trailing_defender_relative_path(pd.concat([tracking(), extra]), spec())


def test_ten_to_ten_substitution_does_not_bridge_rosters():
    q = tracking()
    late = q["entity_type"].eq("player") & (q["time_match_s"] >= 2.1)
    q.loc[late, "player_key"] = q.loc[late, "player_key"].map(lambda value: f"sub:{value}")
    with pytest.raises(ValueError, match="exactly ten"):
        score_trailing_defender_relative_path(q, spec())


@pytest.mark.parametrize(
    ("column", "player_only", "message"),
    [
        ("match_id", False, "null match_id"),
        ("period", False, "null period"),
        ("frame_id_provider", False, "null frame_id_provider"),
        ("player_key", True, "null player_key"),
        ("team_key", True, "null team_key"),
    ],
)
def test_null_identifiers_fail_closed(column, player_only, message):
    q = tracking()
    index = q.index[q["entity_type"].eq("player")][0] if player_only else q.index[0]
    q.loc[index, column] = pd.NA
    with pytest.raises(ValueError, match=message):
        score_trailing_defender_relative_path(q, spec())


def test_frame_identifier_canonicalization_collision_fails_closed():
    q = tracking()
    q.loc[q["frame_id_provider"].eq("2"), "frame_id_provider"] = 1
    with pytest.raises(ValueError, match="collide after canonicalization"):
        score_trailing_defender_relative_path(q, spec())


def test_nonfinite_valid_coordinate_fails_but_declared_missing_is_supported_status():
    q = tracking()
    q.loc[q.player_key.eq("D2") & q.frame_id_provider.eq("25"), "x_m"] = np.nan
    with pytest.raises(ValueError, match="marked valid"):
        score_trailing_defender_relative_path(q, spec())
    q.loc[q.player_key.eq("D2") & q.frame_id_provider.eq("25"), "coordinate_valid"] = False
    result = score_trailing_defender_relative_path(q, spec())
    assert result.team_scores.loc[result.team_scores.frame_id_provider.eq("30"), "support_status"].item() == MISSING_COORDINATES


def test_output_is_deterministic_and_schema_is_exact():
    q = move_player(tracking(), "D0", np.arange(41) / FPS)
    first = score_trailing_defender_relative_path(q, spec())
    second = score_trailing_defender_relative_path(q.sample(frac=1, random_state=7), spec())
    pd.testing.assert_frame_equal(first.player_scores, second.player_scores)
    pd.testing.assert_frame_equal(first.team_scores, second.team_scores)
    assert tuple(first.player_scores.columns) == PLAYER_SCORE_COLUMNS
    assert tuple(first.team_scores.columns) == TEAM_SCORE_COLUMNS


def test_team_mean_matches_independent_oracle():
    q = move_player(tracking(), "D0", np.arange(41) / FPS)
    result = score_trailing_defender_relative_path(q, spec())
    players = supported_at(result, "39")
    team = result.team_scores.loc[result.team_scores.frame_id_provider.eq("39")].iloc[0]
    assert team.mean_trailing_relative_path_m == pytest.approx(players.trailing_relative_path_m.mean())
    assert team.supported_defender_count == 10


def test_fixed_display_normalization_is_continuous_and_reports_saturation():
    result = normalize_scores_for_display([0.0, 1.0, 2.0, 4.0, 5.0, np.nan])
    np.testing.assert_allclose(result.normalized[:5], [0, .25, .5, 1, 1])
    np.testing.assert_allclose(result.clipped_m[:5], [0, 1, 2, 4, 4])
    assert result.saturation_count == 1
    assert result.missing_count == 1


def test_equivalence_with_existing_and_independent_formulas():
    rng = np.random.default_rng(17)
    trajectory = rng.normal(size=(21, 10, 2)).cumsum(axis=0)
    actual = defender_relative_path_lengths(trajectory)
    np.testing.assert_allclose(actual, focal_relative_path_lengths(trajectory), atol=1e-12)
    total = trajectory.sum(axis=1)
    independent = np.array([
        np.linalg.norm(np.diff(trajectory[:, j] - (total - trajectory[:, j]) / 9.0, axis=0), axis=1).sum()
        for j in range(10)
    ])
    skillcorner_form = np.linalg.norm(
        np.diff((10.0 * trajectory - trajectory.sum(axis=1, keepdims=True)) / 9.0, axis=0), axis=2
    ).sum(axis=0)
    np.testing.assert_allclose(actual, independent, atol=1e-12)
    np.testing.assert_allclose(actual, skillcorner_form, atol=1e-12)


def test_metadata_declares_analogue_units_support_and_no_normalization():
    result = score_trailing_defender_relative_path(tracking(), spec())
    assert result.metadata["inferential_response"] is False
    assert result.metadata["units"] == "metres"
    assert result.metadata["window_seconds"] == 2.0
    assert result.metadata["smoother_future_support_seconds"] == pytest.approx(.1)
    assert result.metadata["normalization"] == "none_raw_metres"
    assert result.metadata["required_defenders"] == 10


def test_score_layer_has_no_outcome_dependency_or_dynamic_discovery():
    q = tracking().assign(response_2s_m=np.arange(len(tracking())), outcome=np.nan)
    baseline = score_trailing_defender_relative_path(tracking(), spec())
    extra = score_trailing_defender_relative_path(q, spec())
    pd.testing.assert_frame_equal(baseline.player_scores, extra.player_scores)
    pd.testing.assert_frame_equal(baseline.team_scores, extra.team_scores)


@pytest.mark.parametrize(
    "changes",
    [
        {"source_fps": 0},
        {"window_seconds": 2.05},
        {"smoothing_frames": 2},
        {"smoothing_method": "causal_mean"},
    ],
)
def test_invalid_score_spec_fails_closed(changes):
    with pytest.raises(ValueError):
        spec(**changes)
