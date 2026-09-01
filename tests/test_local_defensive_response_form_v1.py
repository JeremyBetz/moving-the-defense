import math
import unittest

import numpy as np

from src.local_defensive_response_form_v1 import (
    VECTOR_NORM_EPSILON_M,
    decompose_response,
    rank_defenders,
)


class TestLocalDefensiveResponseForm(unittest.TestCase):
    def form(self, attacker, defender, centroid=(0, 0), a0=(10, 0), d0=(0, 0)):
        return decompose_response(attacker, defender, centroid, a0, d0)

    def test_same_and_opposite_attacker_direction(self):
        self.assertEqual(self.form((2, 0), (3, 0)).parallel_m, 3.0)
        self.assertEqual(self.form((2, 0), (-3, 0)).parallel_m, -3.0)

    def test_toward_and_away_from_attacker(self):
        self.assertEqual(self.form((0, 2), (3, 0)).radial_m, 3.0)
        self.assertEqual(self.form((0, 2), (-3, 0)).radial_m, -3.0)

    def test_stationary_defender_while_unit_shifts(self):
        form = self.form((1, 0), (0, 0), (2, 0))
        self.assertEqual(form.parallel_m, -2.0)
        self.assertEqual(form.defender_displacement_m, 0.0)
        self.assertEqual(form.centroid_displacement_m, 2.0)

    def test_defender_and_unit_translate_identically(self):
        form = self.form((1, 0), (4, -2), (4, -2))
        np.testing.assert_array_equal(form.focal_relative_delta, [0, 0])
        self.assertEqual(form.focal_relative_displacement_m, 0.0)
        self.assertIsNone(form.alignment_cosine)

    def test_pure_perpendicular_response(self):
        form = self.form((3, 0), (0, 2))
        self.assertEqual(form.parallel_m, 0.0)
        self.assertEqual(form.orthogonal_m, 2.0)

    def test_zero_and_near_zero_attacker_displacement(self):
        self.assertFalse(self.form((0, 0), (1, 0)).attacker_axis_valid)
        self.assertIsNone(self.form((0, 0), (1, 0)).parallel_m)
        self.assertFalse(self.form((VECTOR_NORM_EPSILON_M / 2, 0), (1, 0)).attacker_axis_valid)

    def test_translation_rotation_and_mirror(self):
        base = self.form((2, 1), (1, 2), (0.2, -0.1), (10, 4), (3, 1))
        theta = 0.73
        rotation = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
        rotated = decompose_response(
            rotation @ np.array((2, 1)), rotation @ np.array((1, 2)),
            rotation @ np.array((0.2, -0.1)), rotation @ np.array((10, 4)),
            rotation @ np.array((3, 1)),
        )
        self.assertAlmostEqual(base.parallel_m, rotated.parallel_m)
        self.assertAlmostEqual(base.orthogonal_m, rotated.orthogonal_m)
        self.assertAlmostEqual(base.radial_m, rotated.radial_m)
        translated = self.form((2, 1), (1, 2), (0.2, -0.1), (110, -46), (103, -49))
        self.assertAlmostEqual(base.parallel_m, translated.parallel_m)
        self.assertAlmostEqual(base.radial_m, translated.radial_m)
        mirror = np.diag([-1.0, 1.0])
        mirrored = decompose_response(
            mirror @ np.array((2, 1)), mirror @ np.array((1, 2)),
            mirror @ np.array((0.2, -0.1)), mirror @ np.array((10, 4)),
            mirror @ np.array((3, 1)),
        )
        self.assertAlmostEqual(base.parallel_m, mirrored.parallel_m)
        self.assertAlmostEqual(abs(base.orthogonal_m), abs(mirrored.orthogonal_m))
        self.assertAlmostEqual(base.radial_m, mirrored.radial_m)

    def test_rank_ties_and_non_tie_relabeling(self):
        tied = rank_defenders((0, 0), [("p2", (1, 0)), ("p1", (-1, 0)), ("p3", (2, 0))])
        self.assertEqual([row[1] for row in tied], ["p1", "p2", "p3"])
        relabeled = rank_defenders((0, 0), [("z", (1, 0)), ("x", (3, 0)), ("y", (2, 0))])
        self.assertEqual([row[2] for row in relabeled], [1.0, 2.0, 3.0])

    def test_deterministic_output(self):
        first = self.form((2, 3), (4, 1), (1, -1))
        second = self.form((2, 3), (4, 1), (1, -1))
        np.testing.assert_array_equal(first.focal_relative_delta, second.focal_relative_delta)
        self.assertEqual(first.__dict__ | {"focal_relative_delta": None},
                         second.__dict__ | {"focal_relative_delta": None})


if __name__ == "__main__":
    unittest.main()
