import numpy as np
import pytest

from src.concurrent_attacker_defensive_geometry_v1 import (
    endpoint_deformation,
    focal_relative_path,
    period_grid_anchors,
    rank_defenders,
)


def _fixture():
    t = np.linspace(0.0, 1.0, 6)
    focal = np.column_stack((2 * t, t))
    offsets = np.column_stack((np.arange(1, 10), np.arange(1, 10) * 0.2))
    others = focal[:, None, :] + offsets[None, :, :]
    others[:, 0, 0] += t
    return focal, others


@pytest.mark.parametrize("transform", [
    lambda x: x + np.array([17.0, -9.0]),
    lambda x: x @ np.array([[0.0, -1.0], [1.0, 0.0]]).T,
    lambda x: x * np.array([-1.0, 1.0]),
])
def test_geometry_is_rigid_transform_invariant(transform):
    focal, others = _fixture()
    assert focal_relative_path(transform(focal), transform(others)) == pytest.approx(
        focal_relative_path(focal, others), abs=1e-12
    )
    assert endpoint_deformation(transform(focal[[0, -1]]), transform(others[[0, -1]])) == pytest.approx(
        endpoint_deformation(focal[[0, -1]], others[[0, -1]]), abs=1e-12
    )


def test_leave_one_out_path_excludes_focal_from_centroid():
    focal = np.array([[0.0, 0.0], [9.0, 0.0]])
    others = np.zeros((2, 9, 2))
    assert focal_relative_path(focal, others) == pytest.approx(9.0)


def test_endpoint_deformation_known_displacement():
    focal = np.zeros((2, 2))
    others = np.zeros((2, 9, 2))
    others[:, :, 0] = np.arange(1.0, 10.0)
    others[1, 0, 0] += 3.0
    assert endpoint_deformation(focal, others) == pytest.approx(1.0)


def test_rank_ties_use_canonical_identifier_and_membership_is_fixed():
    ids = [f"D{i}" for i in range(10, 0, -1)]
    xy = np.column_stack((np.ones(10), np.zeros(10)))
    frozen = rank_defenders(np.zeros(2), ids, xy)
    assert frozen == sorted(ids)
    moved = xy.copy()
    moved[0] = [100.0, 0.0]
    assert frozen != rank_defenders(np.zeros(2), ids, moved)


def test_period_grid_has_complete_nonoverlapping_increment_spans():
    anchors = period_grid_anchors(0.0, 20.0)
    np.testing.assert_array_equal(anchors, [2.0, 6.0, 10.0, 14.0, 18.0])
    assert np.all(np.diff(anchors) >= 4.0)


def test_incomplete_support_is_rejected():
    focal, others = _fixture()
    others[2, 3, 0] = np.nan
    with pytest.raises(ValueError, match="interpolation is prohibited"):
        focal_relative_path(focal, others)
