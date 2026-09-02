from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacker_movement_episode_v2 as execution  # noqa: E402


class AttackerMovementEpisodeV2GovernanceTest(unittest.TestCase):
    def test_frozen_constants_and_firewall(self):
        cfg = json.loads((ROOT / "config/attacker_movement_episode_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["candidate_b"]["direction_angle_deg_min"], 45.0)
        self.assertEqual(cfg["candidate_b"]["redundant_valley_union_directness_min"], 0.95)
        self.assertEqual(cfg["development_gates"]["merging_direction_pct_max"], 3.97)
        self.assertFalse(cfg["candidate_c"]["executed"])
        self.assertFalse(any(cfg["firewall"][key] for key in ("defender_variables", "ball_variables", "outcome_events", "game2", "game3", "idsse")))

    def test_game1_only_visual_cases_are_frozen(self):
        cfg = json.loads((ROOT / "config/attacker_movement_episode_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cfg["visual_audit"]["required"]), 3)
        self.assertEqual(len(cfg["visual_audit"]["chronological"]), 8)
        self.assertEqual(cfg["support_breaks"][0]["raw_frame_start"], 2911)
        self.assertEqual(cfg["support_breaks"][0]["raw_frame_end"], 2945)

    def test_angle_and_direction_candidate(self):
        self.assertAlmostEqual(execution.angle_deg(np.array([1.0, 0.0]), np.array([0.0, 1.0])), 90.0)
        self.assertTrue(np.isnan(execution.angle_deg(np.zeros(2), np.ones(2))))
        n = 40
        xy = np.zeros((n, 2), dtype=float)
        for i in range(1, 20):
            xy[i] = xy[i - 1] + [0.04, 0.0]
        for i in range(20, n):
            xy[i] = xy[i - 1] + [0.0, 0.04]
        block = pd.DataFrame({
            "sx_m": xy[:, 0], "sy_m": xy[:, 1], "Time [s]": np.arange(n) * 0.04,
            "speed_mps": np.r_[np.nan, np.ones(n - 1)], "Frame": np.arange(n), "Period": 1,
        })
        cfg = json.loads((ROOT / "config/attacker_movement_episode_v2.json").read_text(encoding="utf-8"))
        turns = execution.direction_candidates(block, cfg)
        self.assertEqual(len(turns), 1)
        self.assertGreaterEqual(turns[0]["angle_deg"], 45.0)

    def test_support_break(self):
        cfg = json.loads((ROOT / "config/attacker_movement_episode_v2.json").read_text(encoding="utf-8"))
        self.assertTrue(execution.crosses_support_break("Home", "10", 1, 2900, 2920, cfg))
        self.assertFalse(execution.crosses_support_break("Away", "10", 1, 2900, 2920, cfg))


if __name__ == "__main__":
    unittest.main()
