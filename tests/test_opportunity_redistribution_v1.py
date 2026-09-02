import numpy as np
import pytest

from src.opportunity_redistribution_v1 import (
    defensive_contrast,
    nearest_defender_separation,
    opportunity_contrast,
    rank_other_attackers,
    within_anchor_demean,
)


def fixture():
    focal = np.array([0.0, 0.0])
    recipients = np.column_stack((np.arange(1.0, 10.0), np.zeros(9)))
    defenders = np.column_stack((np.arange(1.0, 11.0), np.full(10, 2.0)))
    keys = [f"A:{i}" for i in range(1, 10)]
    return focal, recipients, defenders, keys


@pytest.mark.parametrize("transform", [
    lambda x: x + np.array([14.0, -8.0]),
    lambda x: x @ np.array([[0.0, -1.0], [1.0, 0.0]]).T,
    lambda x: x * np.array([-1.0, 1.0]),
])
def test_opportunity_geometry_is_rigid_transform_invariant(transform):
    focal, recipients, defenders, keys = fixture()
    order = rank_other_attackers(focal, keys, recipients)
    base = nearest_defender_separation(recipients, defenders)
    moved_recipients = recipients.copy(); moved_recipients[:3, 1] -= 1.0
    moved = nearest_defender_separation(moved_recipients, defenders)
    expected = opportunity_contrast(base, moved, order)
    order_t = rank_other_attackers(transform(focal[None])[0], keys, transform(recipients))
    actual = opportunity_contrast(
        nearest_defender_separation(transform(recipients), transform(defenders)),
        nearest_defender_separation(transform(moved_recipients), transform(defenders)),
        order_t,
    )
    assert actual == pytest.approx(expected, abs=1e-12)


def test_recipient_tie_break_is_canonical_and_deterministic():
    focal = np.zeros(2); recipients = np.tile([1.0, 0.0], (9, 1))
    keys = ["A:9", "A:1", "A:5", "A:3", "A:7", "A:2", "A:8", "A:4", "A:6"]
    order = rank_other_attackers(focal, keys, recipients)
    assert [keys[i] for i in order] == sorted(keys)


def test_contrasts_and_demeaning_are_exact():
    assert defensive_contrast(np.arange(1.0, 11.0)) == pytest.approx(2.0 - 5.5)
    values = np.array([[1.0, 4.0], [3.0, 8.0], [2.0, 1.0], [4.0, 5.0]])
    out = within_anchor_demean(values, np.array([1, 1, 2, 2]))
    assert np.allclose(out[[0, 1]].sum(axis=0), 0)
    assert np.allclose(out[[2, 3]].sum(axis=0), 0)


def test_shape_and_identification_fail_closed():
    with pytest.raises(ValueError):
        nearest_defender_separation(np.zeros((8, 2)), np.zeros((10, 2)))
    with pytest.raises(ValueError):
        within_anchor_demean(np.ones((2, 1)), np.array([1, 2]))
