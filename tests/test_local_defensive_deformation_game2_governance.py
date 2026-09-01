from __future__ import annotations

import hashlib,json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class LocalDefensiveDeformationGame2GovernanceTest(unittest.TestCase):
    def test_frozen_inheritance_and_unclassified_status(self):
        cfg=json.loads((ROOT/"config/local_defensive_deformation_v1_game2_replication.json").read_text(encoding="utf-8"))
        for relative,key in [("docs/protocols/local_defensive_deformation_v1.md","original_protocol"),("config/local_defensive_deformation_v1.json","original_config"),("outputs/local_defensive_deformation_game1_v1/final_results.json","game1_final_results"),("outputs/local_defensive_deformation_game1_v1/final_hashes.json","game1_final_hashes"),("outputs/spatial_defensive_response_footprint_game2_final_v1/game2_anchors.parquet","game2_anchors"),("outputs/spatial_defensive_response_footprint_game2_final_v1/game2_linkage.parquet","game2_linkage")]:
            self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),cfg["frozen_hashes"][key])
        self.assertEqual(cfg["game2_status"],"standalone_descriptive_unclassified")
        self.assertEqual(cfg["bootstrap"]["child_index"],7)
        self.assertEqual(cfg["closure"]["pooled_execution"],"prohibited_in_this_pass")


if __name__=="__main__": unittest.main()
