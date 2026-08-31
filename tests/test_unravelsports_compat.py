from __future__ import annotations

import sys
from pathlib import Path
import unittest

import polars as pl


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402
from infrastructure.unravelsports_compat import (  # noqa: E402
    UNRAVEL_REFERENCE_COLUMNS,
    canonical_to_unravel_reference_view,
)


class UnravelSportsCompatibilityViewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home, away = metrica.game1_paths(ROOT)
        index = metrica.read_provider_frame_index(home)
        dataset = metrica.load_dataset(home, away, limit=4)
        cls.canonical = next(
            metrica.iter_canonical_polars_chunks(dataset, index, frames_per_chunk=4)
        )
        cls.view = canonical_to_unravel_reference_view(cls.canonical)

    def test_view_is_row_preserving_and_schema_bounded(self):
        self.assertEqual(self.view.height, self.canonical.height)
        self.assertEqual(self.view.columns, UNRAVEL_REFERENCE_COLUMNS)
        self.assertEqual(self.view.get_column("frame_id").dtype, pl.String)

    def test_view_preserves_null_support_and_does_not_infer_possession(self):
        self.assertEqual(
            self.view.filter(pl.col("x").is_null()).height,
            self.canonical.filter(pl.col("x_m").is_null()).height,
        )
        self.assertTrue(self.view.get_column("ball_owning_team_id").is_null().all())
        self.assertNotIn("is_ball_carrier", self.view.columns)
        self.assertNotIn("vx", self.view.columns)


if __name__ == "__main__":
    unittest.main()
