from __future__ import annotations

import sys
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import local_defensive_deformation_v1 as deformation  # noqa: E402


class LocalDefensiveDeformationTest(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(42); self.start=rng.normal(size=(10,2))*10

    def test_rigid_transform_invariance(self):
        theta=.73; rotation=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        for end in [self.start+np.array([8.,-3.]),self.start@rotation.T,self.start*np.array([-1.,1.])]:
            xy=np.stack([self.start,end]); np.testing.assert_allclose(deformation.focal_endpoint_rms(xy),0,atol=1e-12); self.assertAlmostEqual(deformation.global_endpoint_rms(xy),0,delta=1e-12)

    def test_uniform_scale_positive_control(self):
        center=self.start.mean(axis=0); end=center+1.15*(self.start-center); xy=np.stack([self.start,end])
        self.assertTrue((deformation.focal_endpoint_rms(xy)>0).all()); self.assertGreater(deformation.global_endpoint_rms(xy),0)

    def test_local_displacement_positive_control(self):
        end=self.start.copy(); end[0]+=np.array([4.,-2.]); value=deformation.focal_endpoint_rms(np.stack([self.start,end]))
        self.assertGreater(value[0],0); self.assertTrue((value[1:]>0).all())

    def test_path_and_signed_geometry(self):
        end=self.start.copy(); end[0]+=[2.,0.]; xy=np.stack([self.start,(self.start+end)/2,end])
        self.assertTrue((deformation.focal_relational_path(xy)>=deformation.focal_endpoint_rms(xy)-1e-12).all())
        self.assertEqual(deformation.focal_signed_mean_change(xy).shape,(10,))


if __name__=="__main__": unittest.main()
