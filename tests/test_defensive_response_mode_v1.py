import sys
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_response_mode_v1 as execution  # noqa: E402


def test_frozen_interval_smoother_is_centred_and_has_exact_two_second_length():
    points = np.arange(57.0)
    entity = {"x": points, "y": 2.0 * points, "valid": np.ones(57, dtype=bool)}
    smoothed = execution.smooth_interval(entity, index=3)
    assert smoothed.shape == (51, 2)
    np.testing.assert_allclose(smoothed[0], [3.0, 6.0])
    np.testing.assert_allclose(smoothed[-1], [53.0, 106.0])


def test_width_and_translation_contrasts_keep_the_frozen_signed_meaning():
    beta = np.zeros(16)
    beta[-2], beta[-1] = 0.2, -0.1
    assert math.isclose(execution.width_contrast(beta), 1.0)
    assert math.isclose(execution.translation_contrast(beta), 1.5)
