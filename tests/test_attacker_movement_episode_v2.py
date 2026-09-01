from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
