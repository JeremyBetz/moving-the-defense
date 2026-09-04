import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_reorganization_spatial_value_v1_design as design  # noqa: E402


def test_raw_unit_equal_match_fixed_effect_fit_recovers_directional_contrast():
    matches = np.repeat(["A", "B"], 8)
    goalward = np.tile(np.array([-2.0, -1.0, 1.0, 2.0]), 4)
    outward = np.tile(np.array([2.0, -1.0, -2.0, 1.0]), 4)
    controls = np.column_stack([np.arange(16.0) ** power for power in range(1, 8)])
    z = np.column_stack([controls, goalward, outward])
    y = 3.0 + np.where(matches == "B", 2.0, 0.0) + .2 * goalward + .7 * outward
    beta, rank, _ = design.fit_equal_match_ols(y, z, matches)
    assert rank == 11
    np.testing.assert_allclose(design.primary_contrast(beta), .5, atol=1e-12)


def test_primary_status_tree_requires_every_frozen_support_gate():
    status, audit = design.classify_primary(.03, .01, .05, [.02] * 7, [.02] * 7, .028)
    assert status == "SPATIAL FORM SUPPORTED"
    assert all(audit["gates"].values())
    status, _ = design.classify_primary(.03, .01, .05, [.02] * 7, [.02] * 6 + [-.01], .028)
    assert status == "SPATIAL FORM MIXED"


def test_secondary_requires_all_three_frozen_conditions():
    static = {name: 1.0 for name in design.MATCHES}
    dynamic = {name: .98 for name in design.MATCHES}
    status, _ = design.classify_secondary(1.0, .98, static, dynamic, .001, .03)
    assert status == "DYNAMIC PREFERRED"
    status, _ = design.classify_secondary(1.0, .995, static, {name: .995 for name in design.MATCHES}, .001, .03)
    assert status == "NO CLEAR REPRESENTATIONAL ADVANTAGE"
