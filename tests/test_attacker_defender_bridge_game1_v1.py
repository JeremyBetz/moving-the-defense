from __future__ import annotations

import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402


class BridgeGame1V1Test(unittest.TestCase):
    def test_frozen_constants(self):
        self.assertEqual(bridge.K,3); self.assertEqual(bridge.CADENCE_S,4.0)
        self.assertEqual(bridge.RESPONSES,(1.0,2.0,4.0)); self.assertEqual(bridge.BOOTSTRAPS,2000)
        self.assertEqual(bridge.MASTER_SEED,20260831); self.assertEqual(bridge.MIN_VALID_BOOTSTRAPS,1900)
        self.assertEqual(bridge.sha256(bridge.PROTOCOL),bridge.FROZEN_PROTOCOL_SHA256)

    def test_ols_fixture(self):
        x=np.arange(12,dtype=float)
        baseline=x**2/20
        df=pd.DataFrame({"attacker_path_length_m":x,"prior_local_relative_path_m":baseline,"prior_defending_centroid_path_m":np.sin(x),"local_response_2s_m":1+0.4*x+0.2*baseline-0.1*np.sin(x)})
        coef=bridge.fit(df,*bridge.MODEL_SPECS["primary_local_2s"])
        self.assertTrue(np.allclose(coef,[1,.4,.2,-.1],atol=1e-12))

    def test_block_sampling_keeps_groups(self):
        df=pd.DataFrame({"period":[1]*4+[2]*2,"block_id":[0,0,1,1,0,1]})
        rng=np.random.Generator(np.random.PCG64(123))
        idx=bridge.sampled_indices(df,rng)
        self.assertEqual(len(idx),6)
        self.assertEqual(set(df.loc[idx,"period"]),{1,2})

    def test_summary_bootstraps(self):
        z=bridge.summarize_bootstraps({"x":[1.0,2.0,None,3.0]})
        self.assertEqual(int(z.iloc[0].valid),3); self.assertEqual(int(z.iloc[0].failed),1)


if __name__=="__main__": unittest.main()
