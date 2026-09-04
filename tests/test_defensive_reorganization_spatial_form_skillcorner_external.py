import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_reorganization_spatial_form_skillcorner_external as external  # noqa: E402


def _frame(match_ids):
    rows = []
    for match in match_ids:
        for value in range(12):
            controls = [float((value + 1) ** power) for power in range(1, 8)]
            rows.append({
                "match_id": str(match),
                "Y_m": 1.0 + 0.2 * value + 0.4 * (value % 3) + 0.8 * ((2 * value) % 5),
                "anchor_frame": value,
                "period": 1,
                "block_id": 0,
                **dict(zip(external.BASE[:7], controls, strict=True)),
                "attacker_goalward_displacement_m": float(value % 3),
                "attacker_outward_displacement_m": float((2 * value) % 5),
            })
    return pd.DataFrame(rows)


def test_equal_match_fit_keeps_raw_goalward_and_outward_columns_last():
    frame = _frame(["A", "B"])
    beta, rank, names = external.fit(frame)
    assert names == ("A", "B")
    assert rank == len(external.BASE) + 2
    mapping = external.continuous_map(beta)
    assert np.isfinite(mapping["attacker_goalward_displacement_m"])
    assert np.isfinite(mapping["attacker_outward_displacement_m"])


def test_external_classification_requires_every_support_gate():
    matches = tuple(str(index) for index in range(9))
    per_match = pd.DataFrame({"positive_contrast": [True] * 9})
    lomo = pd.DataFrame({"outward_minus_goalward_m_per_m": [0.01] * 9})
    trim = {"outward_minus_goalward_m_per_m": 0.08}
    quality = {"full_rank": True, "outward_minus_goalward_m_per_m": 0.09}
    status, audit = external.classification(True, matches, 0.1, {"ci_low": 0.01}, per_match, lomo, trim, quality)
    assert status == "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION SUPPORTED"
    assert all(audit["gates"].values())
    lomo.loc[0, "outward_minus_goalward_m_per_m"] = -0.01
    status, _ = external.classification(True, matches, 0.1, {"ci_low": 0.01}, per_match, lomo, trim, quality)
    assert status == "SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION MIXED"


def test_retained_simultaneous_anchor_group_can_have_row_specific_identity_qc():
    """Identity-QC row exclusion must not impose an undeclared nine-row gate."""
    frame = pd.DataFrame({
        "match_id": ["A", "A", "A", "A"],
        "period": [1, 1, 1, 1],
        "anchor_frame": [40, 40, 40, 80],
        "block_id": [0, 0, 0, 1],
    })
    groups_preserved = (frame.groupby(["match_id", "period", "anchor_frame"]).block_id.nunique() == 1)
    assert groups_preserved.all()
    assert frame.groupby(["match_id", "period", "anchor_frame"]).size().tolist() == [3, 1]
