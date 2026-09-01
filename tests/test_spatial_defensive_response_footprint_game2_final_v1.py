from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
import spatial_defensive_response_footprint_game2_final_v1 as x
class TestFinalFootprint(unittest.TestCase):
 def test_hashes(self):
  self.assertEqual(x.f1.sha256(x.CLAR),x.CLAR_HASH);self.assertEqual(x.f1.sha256(x.f1.PROTOCOL),x.f1.FROZEN_PROTOCOL_SHA256);self.assertEqual(x.f1.sha256(x.f1.CONFIG),x.f1.FROZEN_CONFIG_SHA256)
 def test_no_game2_status(self):
  self.assertNotIn("GAME 2 FOOTPRINT",Path(x.__file__).read_text())
if __name__=="__main__":unittest.main()
