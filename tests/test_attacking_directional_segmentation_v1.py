from __future__ import annotations
import sys
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from attacking_directional_segmentation_game1_v1 import (
    FIXTURE_SIGMA_MPS,
    exact_dp,
    exact_pelt,
    fixture_trace,
    run_fixtures,
    run_noise_estimator_fixture,
    smooth_velocity,
)


class DirectionalSegmentationV1Test(unittest.TestCase):
    def test_pelt_matches_oracle_on_deterministic_signals(self):
        rng=np.random.default_rng(20260831)
        for n in (20,31,55,80):
            for _ in range(5):
                x=rng.normal(size=(n,2))
                self.assertEqual(exact_pelt(x,.75,4),exact_dp(x,.75,4))

    def test_tie_prefers_fewer_then_earlier(self):
        x=np.zeros((30,2))
        self.assertEqual(exact_pelt(x,1.,10),())

    def test_complete_seven_frame_smoothing(self):
        pos,t,f,_=fixture_trace("constant",25)
        q=smooth_velocity(pos,t,f)
        self.assertEqual(len(q["positions"]),len(pos)-6)
        self.assertEqual(len(q["velocity"]),len(pos)-7)
        self.assertEqual(q["position_frames"][0],3)

    def test_all_frozen_algorithm_fixtures(self):
        rows=run_fixtures()
        self.assertEqual(FIXTURE_SIGMA_MPS,1.0)
        self.assertTrue(all(row["required_pass"] for row in rows))

    def test_noise_estimator_fixture(self):
        result=run_noise_estimator_fixture()
        self.assertTrue(result["pass"])
        self.assertAlmostEqual(result["estimated_sigma_mps"],0.25,places=12)


if __name__=="__main__": unittest.main()
