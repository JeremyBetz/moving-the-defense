from __future__ import annotations

import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import local_defensive_deformation_game1_v1 as execution  # noqa: E402


class LocalDefensiveDeformationExecutionTest(unittest.TestCase):
    def test_frozen_hashes_and_constants(self):
        self.assertTrue(all(execution.sha(p)==h for p,h in execution.HASHES.items()))
        self.assertEqual((execution.BOOT,execution.MIN_VALID,execution.CHILD),(2000,1900,6))

    def test_exact_four_column_rank_fit(self):
        rows=[]
        for rank in range(1,11):
            for i in range(8):
                x=float(i); prior=float(i*i/20); global_prior=float(np.sin(i))
                rows.append({"distance_rank":rank,"attacker_path_length_m":x,"focal_prior_endpoint_rms_m":prior,"global_prior_endpoint_rms_m":global_prior,"y":1+rank/10+.25*x+.1*prior-.05*global_prior})
        beta=execution.fit(pd.DataFrame(rows),"y","attacker_path_length_m")
        np.testing.assert_allclose(beta,.25,atol=1e-12)

    def test_region_identity(self):
        value=execution.regions(np.arange(1,11,dtype=float))
        self.assertEqual(value["near_minus_middle"],-3.5)


if __name__=="__main__": unittest.main()
