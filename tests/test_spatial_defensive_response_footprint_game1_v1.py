from __future__ import annotations
import sys
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import spatial_defensive_response_footprint_game1_v1 as f  # noqa: E402


class FootprintV1Test(unittest.TestCase):
    def test_frozen_hashes_and_constants(self):
        self.assertEqual(f.sha256(f.PROTOCOL),f.FROZEN_PROTOCOL_SHA256); self.assertEqual(f.sha256(f.CONFIG),f.FROZEN_CONFIG_SHA256)
        self.assertEqual((f.BOOTSTRAPS,f.MASTER_SEED,f.CHILD_INDEX,f.MIN_VALID),(2000,20260831,3,1900))
    def test_regions(self):
        r=f.regional(np.arange(1,11,dtype=float)); self.assertAlmostEqual(r["N"],2); self.assertAlmostEqual(r["M"],5.5); self.assertAlmostEqual(r["F"],9); self.assertAlmostEqual(r["Delta_NF"],r["Delta_NM"]+r["Delta_MF"])
    def test_band_boundaries(self):
        self.assertEqual([f.band_label(x) for x in [0,9.999,10,20,50,100]],["[0,10)","[0,10)","[10,20)","[20,30)","[50,inf)","[50,inf)"])
    def test_rank_model_fixture(self):
        x=np.arange(12,dtype=float); b=x*x/30; c=np.sin(x); X=f.design(x,b,c); y=1+.4*x+.2*b-.1*c; self.assertTrue(np.allclose(f.fit_xy(X,y),[1,.4,.2,-.1],atol=1e-12))
    def test_invariances(self):
        self.assertTrue(all(f.synthetic_invariances().values()))


if __name__=="__main__": unittest.main()
