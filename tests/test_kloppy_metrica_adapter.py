from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.kloppy_metrica_adapter import (  # noqa: E402
    CANONICAL_COLUMNS,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    game1_paths,
    load_dataset,
    read_provider_frame_index,
    to_long_dataframe,
)


class KloppyMetricaAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home, cls.away = game1_paths(ROOT)
        cls.index = read_provider_frame_index(cls.home)
        cls.dataset = load_dataset(cls.home, cls.away, limit=620)
        cls.long = to_long_dataframe(cls.dataset, cls.index)

    def test_schema_and_identity_preservation(self):
        self.assertEqual(list(self.long.columns), CANONICAL_COLUMNS)
        players = self.long[self.long.object_type == "player"]
        self.assertEqual(set(players.team_id.dropna()), {"Home", "Away"})
        first = players[players.frame_id == 1]
        self.assertEqual(len(first), 28)
        self.assertEqual(int(first.is_goalkeeper.sum()), 2)
        self.assertEqual(set(first[first.is_goalkeeper].player_id), {"11", "25"})

    def test_pitch_conversion_and_axes_match_raw_provider(self):
        raw = pd.read_csv(self.home, skiprows=3, header=None)
        row = self.long[
            (self.long.frame_id == 1)
            & (self.long.team_id == "Home")
            & (self.long.player_id == "11")
        ].iloc[0]
        self.assertAlmostEqual(row.x_norm, float(raw.iloc[0, 3]), places=14)
        self.assertAlmostEqual(row.y_norm, float(raw.iloc[0, 4]), places=14)
        self.assertAlmostEqual(row.x_m, row.x_norm * PITCH_LENGTH_M, places=12)
        self.assertAlmostEqual(row.y_m, row.y_norm * PITCH_WIDTH_M, places=12)

    def test_frame_and_timestamp_preservation(self):
        frames = self.long[["period", "frame_id", "provider_time_s"]].drop_duplicates()
        expected = self.index.iloc[: len(self.dataset.frames)].reset_index(drop=True)
        pd.testing.assert_frame_equal(frames.reset_index(drop=True), expected, check_exact=True)

    def test_missing_rows_are_retained_without_interpolation(self):
        # Substitute Home 12 is unsupported at the opening frame.
        missing_player = self.long[
            (self.long.frame_id == 1)
            & (self.long.team_id == "Home")
            & (self.long.player_id == "12")
        ].iloc[0]
        self.assertFalse(bool(missing_player.observed))
        self.assertTrue(np.isnan(missing_player.x_norm))
        self.assertTrue(np.isnan(missing_player.y_norm))

        # The provider ball is missing at frame 617 and must remain an explicit null row.
        missing_ball = self.long[
            (self.long.frame_id == 617) & (self.long.object_type == "ball")
        ].iloc[0]
        self.assertFalse(bool(missing_ball.observed))
        self.assertTrue(np.isnan(missing_ball.x_norm))
        self.assertTrue(np.isnan(missing_ball.y_norm))


if __name__ == "__main__":
    unittest.main()
