"""Synthetic-only checks for the defender-rank composition audit.

No match loader, governed observation table, real response, or coverage artifact
is imported here.  The construction isolates two mechanical questions:

1. Can exact start-distance ranking plus leave-one-out centering manufacture a
   near-versus-middle attacker-movement slope when the individual concurrent
   movement innovations are independent of attacker movement and rank?
2. When prior activity is deliberately rank-composed and is the *only* cause
   of individual concurrent movement, does the synthetic linear analogue of
   the core's focal-relative and other-nine prior-activity conditioning remove
   the resulting omitted-variable localization?

For ten defenders, with ordinary centroid ``c`` and leave-one-out centroid
``c_-d``, the identity tested below is

    x_d - c_-d = (10 / 9) * (x_d - c).

The response used by the null is the signed x component of the synthetic
endpoint defender-relative displacement.  It is a coordinate-level mechanical
test, not a simulated estimate of any protected empirical response.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from src.concurrent_attacker_defensive_geometry_v1 import rank_defenders


N_DEFENDERS = 10
NEAR = slice(0, 3)
MIDDLE = slice(3, 7)
ACTIVITY_EFFECT = 0.45

# A compact outfield shape in a 105 m by 68 m pitch-supported coordinate frame.
# Absolute origin is immaterial to distance ranks and the tested centroid
# identities. Bounded shifts, stretches, and player jitter below create
# heterogeneous scenes without reading any tracking data.
BASE_FORMATION_M = np.array(
    [
        [27.0, 34.0],
        [35.0, 8.0],
        [35.0, 25.0],
        [35.0, 43.0],
        [35.0, 60.0],
        [44.0, 14.0],
        [44.0, 28.0],
        [44.0, 40.0],
        [44.0, 54.0],
        [52.0, 34.0],
    ],
    dtype=np.float64,
)
DEFENDER_IDS = tuple(f"D{i:02d}" for i in range(1, N_DEFENDERS + 1))


@dataclass(frozen=True)
class SyntheticScenes:
    attacker_start_m: np.ndarray
    defender_start_m: np.ndarray
    defender_end_m: np.ndarray
    distance_rank: np.ndarray
    attacker_path_m: np.ndarray
    prior_activity_m: np.ndarray
    other_nine_prior_activity_m: np.ndarray
    individual_displacement_m: np.ndarray
    collective_translation_m: np.ndarray
    innovation_m: np.ndarray
    relative_displacement_m: np.ndarray


def _project_distance_ranks(attacker: np.ndarray, defenders: np.ndarray) -> np.ndarray:
    """Assign each synthetic defender the project's exact frozen start rank."""
    id_to_column = {defender_id: i for i, defender_id in enumerate(DEFENDER_IDS)}
    ranks = np.empty(defenders.shape[:2], dtype=np.int64)
    for scene in range(len(defenders)):
        order = rank_defenders(attacker[scene], list(DEFENDER_IDS), defenders[scene])
        for rank, defender_id in enumerate(order, start=1):
            ranks[scene, id_to_column[defender_id]] = rank
    return ranks


def _leave_one_out_relative_displacement(start: np.ndarray, end: np.ndarray) -> np.ndarray:
    displacement = end - start
    other_nine_mean = (
        displacement.sum(axis=1, keepdims=True, dtype=np.float64) - displacement
    ) / (N_DEFENDERS - 1)
    return displacement - other_nine_mean


def _make_scenes(*, seed: int, n_scenes: int, rank_composed_activity: bool) -> SyntheticScenes:
    geometry_seed, exposure_seed, activity_seed, response_seed, translation_seed = (
        np.random.SeedSequence(seed).spawn(5)
    )
    geometry_rng = np.random.default_rng(geometry_seed)
    exposure_rng = np.random.default_rng(exposure_seed)
    activity_rng = np.random.default_rng(activity_seed)
    response_rng = np.random.default_rng(response_seed)
    translation_rng = np.random.default_rng(translation_seed)

    formation_center = BASE_FORMATION_M.mean(axis=0)
    relative_shape = BASE_FORMATION_M - formation_center
    stretch = geometry_rng.uniform([0.90, 0.90], [1.10, 1.10], size=(n_scenes, 1, 2))
    unit_shift = geometry_rng.uniform([-3.0, -2.5], [3.0, 2.5], size=(n_scenes, 1, 2))
    player_jitter = geometry_rng.uniform(
        [-1.25, -1.50], [1.25, 1.50], size=(n_scenes, N_DEFENDERS, 2)
    )
    defender_start = formation_center + relative_shape * stretch + unit_shift + player_jitter
    attacker_start = geometry_rng.uniform([54.0, 16.0], [68.0, 52.0], size=(n_scenes, 2))
    ranks = _project_distance_ranks(attacker_start, defender_start)

    # Attacker movement is generated on a separate random stream.  In the
    # confounded variant it predicts prior activity with a rank-specific
    # loading, but it never enters the individual concurrent response equation.
    attacker_path = exposure_rng.uniform(1.5, 8.5, size=n_scenes)
    attacker_z = (attacker_path - attacker_path.mean()) / attacker_path.std(ddof=0)

    if rank_composed_activity:
        rank_offset = np.array(
            [0.30, 0.24, 0.18, 0.06, 0.02, -0.02, -0.06, -0.10, -0.14, -0.18]
        )
        rank_loading = np.array(
            [0.28, 0.24, 0.20, 0.06, 0.03, 0.00, -0.03, -0.06, -0.08, -0.10]
        )
    else:
        rank_offset = np.zeros(N_DEFENDERS)
        rank_loading = np.zeros(N_DEFENDERS)

    rank_index = ranks - 1
    prior_activity = (
        1.50
        + activity_rng.normal(0.0, 0.12, size=(n_scenes, 1))
        + rank_offset[rank_index]
        + rank_loading[rank_index] * attacker_z[:, None]
        + activity_rng.normal(0.0, 0.09, size=(n_scenes, N_DEFENDERS))
    )
    other_nine_prior = (
        prior_activity.sum(axis=1, keepdims=True, dtype=np.float64) - prior_activity
    ) / (N_DEFENDERS - 1)

    # Conditional response equation (and the only one):
    #
    #   q_sd,x = 0.45 * prior_activity_sd + epsilon_sd,x.
    #
    # Innovations come from a separate stream and have no attacker/rank term.
    innovation = response_rng.normal(
        0.0, [0.060, 0.080], size=(n_scenes, N_DEFENDERS, 2)
    )
    individual_displacement = innovation.copy()
    individual_displacement[:, :, 0] += ACTIVITY_EFFECT * prior_activity

    # Translation may itself track attacker movement.  Applying the exact
    # leave-one-out reference must remove it for every defender and rank.
    collective_translation = np.column_stack(
        [
            0.12 * attacker_path + translation_rng.normal(0.0, 0.15, n_scenes),
            translation_rng.normal(0.0, 0.25, n_scenes),
        ]
    )
    defender_end = (
        defender_start
        + collective_translation[:, None, :]
        + individual_displacement
    )
    relative_displacement = _leave_one_out_relative_displacement(
        defender_start, defender_end
    )

    return SyntheticScenes(
        attacker_start_m=attacker_start,
        defender_start_m=defender_start,
        defender_end_m=defender_end,
        distance_rank=ranks,
        attacker_path_m=attacker_path,
        prior_activity_m=prior_activity,
        other_nine_prior_activity_m=other_nine_prior,
        individual_displacement_m=individual_displacement,
        collective_translation_m=collective_translation,
        innovation_m=innovation,
        relative_displacement_m=relative_displacement,
    )


def _rank_specific_attacker_slopes(
    scenes: SyntheticScenes, *, condition_on_prior_activity: bool
) -> np.ndarray:
    """Fit the synthetic analogue of a separate attacker slope at each rank."""
    scene_index = np.arange(len(scenes.attacker_path_m))
    slopes = []
    for rank in range(1, N_DEFENDERS + 1):
        defender_column = np.argmax(scenes.distance_rank == rank, axis=1)
        outcome = scenes.relative_displacement_m[scene_index, defender_column, 0]
        columns = [np.ones(len(scene_index)), scenes.attacker_path_m]
        if condition_on_prior_activity:
            prior_relative_activity = (
                scenes.prior_activity_m[scene_index, defender_column]
                - scenes.other_nine_prior_activity_m[scene_index, defender_column]
            )
            columns.extend(
                [
                    prior_relative_activity,
                    scenes.other_nine_prior_activity_m[scene_index, defender_column],
                ]
            )
        design = np.column_stack(columns)
        slopes.append(np.linalg.lstsq(design, outcome, rcond=None)[0][1])
    return np.asarray(slopes)


def _near_minus_middle(slopes: np.ndarray) -> float:
    return float(slopes[NEAR].mean() - slopes[MIDDLE].mean())


@pytest.fixture(scope="module")
def rank_only_scenes() -> SyntheticScenes:
    return _make_scenes(seed=2026090301, n_scenes=12_000, rank_composed_activity=False)


@pytest.fixture(scope="module")
def activity_composed_scenes() -> SyntheticScenes:
    return _make_scenes(seed=2026090302, n_scenes=12_000, rank_composed_activity=True)


def test_start_geometry_is_heterogeneous_and_ranked_by_exact_start_distance(
    rank_only_scenes: SyntheticScenes,
) -> None:
    scenes = rank_only_scenes
    start = scenes.defender_start_m
    assert np.all((0.0 <= start[:, :, 0]) & (start[:, :, 0] <= 105.0))
    assert np.all((0.0 <= start[:, :, 1]) & (start[:, :, 1] <= 68.0))
    assert np.ptp(start[:, :, 0]) > 30.0
    assert np.ptp(start[:, :, 1]) > 55.0

    distances = np.linalg.norm(start - scenes.attacker_start_m[:, None, :], axis=2)
    assert np.median(distances.std(axis=1)) > 8.0
    np.testing.assert_array_equal(
        np.sort(scenes.distance_rank, axis=1),
        np.broadcast_to(np.arange(1, 11), scenes.distance_rank.shape),
    )
    for scene in range(len(start)):
        order = np.argsort(distances[scene], kind="stable")
        np.testing.assert_array_equal(
            scenes.distance_rank[scene, order], np.arange(1, 11)
        )


def test_leave_one_out_is_ten_ninths_and_removes_collective_translation(
    rank_only_scenes: SyntheticScenes,
) -> None:
    scenes = rank_only_scenes
    start = scenes.defender_start_m
    end = scenes.defender_end_m

    ordinary_start = start - start.mean(axis=1, keepdims=True, dtype=np.float64)
    other_nine_start = (
        start.sum(axis=1, keepdims=True, dtype=np.float64) - start
    ) / (N_DEFENDERS - 1)
    loo_start = start - other_nine_start
    np.testing.assert_allclose(loo_start, (10.0 / 9.0) * ordinary_start, atol=2e-14)

    absolute_displacement = end - start
    ordinary_displacement = absolute_displacement - absolute_displacement.mean(
        axis=1, keepdims=True, dtype=np.float64
    )
    np.testing.assert_allclose(
        scenes.relative_displacement_m,
        (10.0 / 9.0) * ordinary_displacement,
        atol=2e-14,
    )

    no_translation_end = start + scenes.individual_displacement_m
    no_translation_response = _leave_one_out_relative_displacement(
        start, no_translation_end
    )
    np.testing.assert_allclose(
        scenes.relative_displacement_m, no_translation_response, atol=2e-14
    )

    # The scaling factor is identical at every exact attacker-distance rank.
    loo_norm = np.linalg.norm(loo_start, axis=2)
    ordinary_norm = np.linalg.norm(ordinary_start, axis=2)
    ratio = loo_norm / ordinary_norm
    for rank in range(1, N_DEFENDERS + 1):
        np.testing.assert_allclose(
            ratio[scenes.distance_rank == rank], 10.0 / 9.0, atol=2e-14
        )


def test_rank_only_null_has_no_near_minus_middle_attacker_slope(
    rank_only_scenes: SyntheticScenes,
) -> None:
    slopes = _rank_specific_attacker_slopes(
        rank_only_scenes, condition_on_prior_activity=False
    )
    assert np.max(np.abs(slopes)) < 0.0015
    assert abs(_near_minus_middle(slopes)) < 0.0005


def test_prior_activity_conditioning_removes_induced_localization(
    activity_composed_scenes: SyntheticScenes,
) -> None:
    scenes = activity_composed_scenes

    # This is an executable check that concurrent individual movement contains
    # exactly the declared prior-activity term plus independent innovation—no
    # hidden attacker-path or rank term.
    np.testing.assert_allclose(
        scenes.individual_displacement_m[:, :, 0],
        ACTIVITY_EFFECT * scenes.prior_activity_m + scenes.innovation_m[:, :, 0],
        atol=1e-15,
    )

    unadjusted = _rank_specific_attacker_slopes(
        scenes, condition_on_prior_activity=False
    )
    adjusted = _rank_specific_attacker_slopes(
        scenes, condition_on_prior_activity=True
    )
    unadjusted_localization = _near_minus_middle(unadjusted)
    adjusted_localization = _near_minus_middle(adjusted)

    assert unadjusted_localization > 0.050
    assert abs(adjusted_localization) < 0.0015
    assert abs(adjusted_localization) < 0.03 * abs(unadjusted_localization)
    assert np.max(np.abs(adjusted)) < 0.0025

    # The confound was deliberately material: near defenders had more prior
    # activity than middle defenders before any concurrent response was made.
    near_activity = scenes.prior_activity_m[scenes.distance_rank <= 3].mean()
    middle_activity = scenes.prior_activity_m[
        (scenes.distance_rank >= 4) & (scenes.distance_rank <= 7)
    ].mean()
    assert near_activity - middle_activity > 0.18
