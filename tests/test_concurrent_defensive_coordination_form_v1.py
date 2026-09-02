import numpy as np
import unittest

from src.concurrent_defensive_coordination_form_v1 import (
    centered_rolling_mean,
    coordination_form,
    displacement_audit_form,
    zero_phase_butterworth,
)


def fixture(attacker_steps, focal_steps, collective_steps=None):
    attacker = np.vstack(([0.0, 0.0], np.cumsum(attacker_steps, axis=0)))
    collective_steps = np.zeros_like(focal_steps) if collective_steps is None else collective_steps
    collective = np.vstack(([0.0, 0.0], np.cumsum(collective_steps, axis=0)))
    relative = np.vstack(([0.0, 0.0], np.cumsum(focal_steps, axis=0)))
    focal = collective + relative
    others = np.repeat(collective[:, None, :], 9, axis=1)
    return attacker, focal, others


class CoordinationFormTests(unittest.TestCase):
    def assert_close(self, actual, expected, places=12):
        self.assertAlmostEqual(actual, expected, places=places)

    def test_a_collective_translation_removed(self):
        a, d, o = fixture(np.tile([1.0, 0.0], (4, 1)), np.zeros((4, 2)), np.tile([0.5, 0.0], (4, 1)))
        result = coordination_form(a, d, o, np.arange(len(a), dtype=float))
        self.assert_close(result.absolute_aligned_mps, 0.5)
        self.assert_close(result.relative_aligned_mps, 0.0)

    def test_b_focal_relative_following_positive(self):
        a, d, o = fixture(np.tile([1.0, 0.0], (4, 1)), np.tile([0.4, 0.0], (4, 1)))
        self.assert_close(coordination_form(a, d, o, np.arange(len(a), dtype=float)).relative_aligned_mps, 0.4)

    def test_c_opposite_motion_negative(self):
        a, d, o = fixture(np.tile([1.0, 0.0], (4, 1)), np.tile([-0.25, 0.0], (4, 1)))
        self.assert_close(coordination_form(a, d, o, np.arange(len(a), dtype=float)).relative_aligned_mps, -0.25)

    def test_d_perpendicular_motion_is_cross_only(self):
        a, d, o = fixture(np.tile([1.0, 0.0], (4, 1)), np.tile([0.0, 0.3], (4, 1)))
        result = coordination_form(a, d, o, np.arange(len(a), dtype=float))
        self.assert_close(result.relative_aligned_mps, 0.0)
        self.assert_close(result.relative_cross_mps, 0.3)

    def test_e_stops_and_all_stop(self):
        a, d, o = fixture(np.array([[1, 0], [0, 0], [1, 0]], float), np.array([[0.2, 0], [9, 7], [0.2, 0]], float))
        self.assert_close(coordination_form(a, d, o, np.arange(len(a), dtype=float)).relative_aligned_mps, 0.2)
        z, d, o = fixture(np.zeros((3, 2)), np.ones((3, 2)))
        result = coordination_form(z, d, o, np.arange(len(z), dtype=float))
        self.assertEqual(result.attacker_path_m, 0)
        self.assertIsNone(result.relative_aligned_mps)

    def test_f_turn_and_endpoint_cancellation(self):
        steps = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]], float)
        a, d, o = fixture(steps, 0.5 * steps)
        result = coordination_form(a, d, o, np.arange(len(a), dtype=float))
        self.assertTrue(np.allclose(a[-1] - a[0], 0))
        self.assert_close(result.relative_aligned_mps, 0.5)

    def test_g_common_translation_invariance(self):
        steps = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]], float)
        a, d, o = fixture(steps, 0.3 * steps)
        time = np.arange(len(a), dtype=float)
        base = coordination_form(a, d, o, time)
        common = np.column_stack((np.linspace(0, 9, len(a)), np.linspace(0, -4, len(a))))
        shifted = coordination_form(a, d + common, o + common[:, None, :], time)
        self.assert_close(shifted.relative_aligned_mps, base.relative_aligned_mps)
        self.assert_close(shifted.relative_cross_mps, base.relative_cross_mps)

    def test_displacement_form_scales_with_sample_interval(self):
        values=[]
        for hz in (10.0,25.0):
            t=np.arange(0,4+0.5/hz,1/hz)
            a=np.column_stack((t,np.zeros_like(t)))
            r=0.4*a
            o=np.zeros((len(t),9,2))
            values.append(displacement_audit_form(a,r,o).relative_aligned_m)
        self.assert_close(values[0]/values[1],2.5,places=10)

    def test_velocity_form_constant_motion_frequency_invariant(self):
        values=[]
        for hz in (10.0,25.0,100.0):
            t=np.arange(0,4+0.5/hz,1/hz)
            a=np.column_stack((t,np.zeros_like(t)))
            r=0.4*a
            o=np.zeros((len(t),9,2))
            values.append(coordination_form(a,r,o,t).relative_aligned_mps)
        np.testing.assert_allclose(values,0.4,atol=1e-12)

    def test_lowpass_preserves_slow_signal(self):
        for sample_hz in (10.0, 25.0):
            t = np.arange(0, 20, 1 / sample_hz)
            slow = np.sin(2 * np.pi * 0.3 * t)
            noise = 0.25 * np.sin(2 * np.pi * 3.0 * t)
            xy = np.column_stack((slow + noise, np.zeros_like(t)))
            filtered = zero_phase_butterworth(xy, sample_hz, 1.0)
            core = slice(int(sample_hz), -int(sample_hz))
            self.assertLess(np.sqrt(np.mean((filtered[core, 0] - slow[core]) ** 2)), 0.03)

    def test_butterworth_cutoffs_are_finite_and_preserve_constant_edges(self):
        for sample_hz in (10.0, 25.0):
            constant = np.repeat([[4.0, -2.0]], int(5 * sample_hz), axis=0)
            for cutoff_hz in (1.0, 1.5):
                filtered = zero_phase_butterworth(constant, sample_hz, cutoff_hz)
                self.assertTrue(np.isfinite(filtered).all())
                np.testing.assert_allclose(filtered, constant, atol=1e-12)

    def test_physical_time_filter_rate_consistency(self):
        errors = {"butter": [], "rolling": []}
        for hz in (10.0, 25.0):
            t = np.arange(0, 20, 1 / hz)
            truth = np.column_stack((2 * np.sin(2 * np.pi * 0.35 * t), np.cos(2 * np.pi * 0.2 * t)))
            observed = truth + np.column_stack((0.2 * np.sin(2 * np.pi * 3 * t), 0.1 * np.cos(2 * np.pi * 2.5 * t)))
            b = zero_phase_butterworth(observed, hz, 1.0)
            r = centered_rolling_mean(observed, 7)
            errors["butter"].append(float(np.sqrt(np.mean((b - truth) ** 2))))
            errors["rolling"].append(float(np.sqrt(np.mean((r - truth[3:-3]) ** 2))))
        self.assertLess(abs(errors["butter"][0] - errors["butter"][1]), abs(errors["rolling"][0] - errors["rolling"][1]))


if __name__ == "__main__":
    unittest.main()
