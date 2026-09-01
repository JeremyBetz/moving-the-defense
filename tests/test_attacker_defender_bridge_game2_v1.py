from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacker_defender_bridge_game2_v1 as bridge  # noqa: E402


class BridgeGame2V1Test(unittest.TestCase):
    def test_frozen_inheritance(self):
        self.assertEqual(bridge.FROZEN_GAME1_P99_M, 12.198443079831405)
        self.assertEqual(bridge.g1.sha256(bridge.PROTOCOL), bridge.g1.FROZEN_PROTOCOL_SHA256)

    def test_pooled_fit_fixture(self):
        x = np.arange(20, dtype=float)
        b = x**2 / 30
        c = np.sin(x)
        game = np.tile([0.0, 1.0], 10)
        y = 1 + .4*x + .2*b - .1*c + .3*game
        df = pd.DataFrame({"attacker_path_length_m": x, "prior_local_relative_path_m": b,
                           "prior_defending_centroid_path_m": c, "game2_indicator": game,
                           "local_response_2s_m": y})
        coef = bridge.fit_pooled(df, "local_response_2s_m", "attacker_path_length_m", "prior_local_relative_path_m")
        self.assertTrue(np.allclose(coef, [1, .4, .2, -.1, .3], atol=1e-12))

    def test_pooled_sampling_retains_all_match_period_groups(self):
        df = pd.DataFrame({"game": ["Game 1"]*4 + ["Game 2"]*4,
                           "period": [1,1,2,2,1,1,2,2], "block_id": [0,1,0,1,0,1,0,1]})
        idx = bridge.sampled_indices_pooled(df, np.random.default_rng(1))
        z = df.loc[idx]
        self.assertEqual(set(zip(z["game"], z["period"])), {("Game 1",1),("Game 1",2),("Game 2",1),("Game 2",2)})


if __name__ == "__main__":
    unittest.main()
