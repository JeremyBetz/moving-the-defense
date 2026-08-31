from __future__ import annotations

import sys
from pathlib import Path
import unittest

from kloppy.domain import PositionType
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.kloppy_idsse_adapter import (  # noqa: E402
    IDSSE_CANONICAL_COLUMNS,
    idsse_paths,
    iter_long_chunks,
    load_dataset,
    read_ball_frame_sidecar,
    roster,
)
from infrastructure.kloppy_metrica_adapter import CANONICAL_COLUMNS  # noqa: E402


class KloppyIDSSEAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata, _, cls.tracking = idsse_paths(ROOT, "J03WMX")
        cls.sidecar = read_ball_frame_sidecar(cls.tracking)
        cls.dataset = load_dataset(cls.metadata, cls.tracking, limit=5)
        cls.long = next(iter_long_chunks(cls.dataset, cls.sidecar, frames_per_chunk=5))

    def test_shared_canonical_core_and_explicit_null_rows(self):
        self.assertEqual(IDSSE_CANONICAL_COLUMNS[: len(CANONICAL_COLUMNS)], CANONICAL_COLUMNS)
        self.assertEqual(list(self.long.columns), IDSSE_CANONICAL_COLUMNS)
        first = self.long[self.long.frame_id == 10000]
        self.assertEqual(len(first), 41)
        self.assertEqual(int((first.object_type == "player").sum()), 40)
        self.assertEqual(int(first[first.object_type == "player"].observed.sum()), 22)
        unsupported = first[(first.object_type == "player") & ~first.observed].iloc[0]
        self.assertTrue(np.isnan(unsupported.x_m))
        self.assertTrue(np.isnan(unsupported.y_m))

    def test_ids_teams_and_goalkeepers_are_reversible(self):
        entries = roster(self.dataset)
        self.assertEqual({team for _, team, _ in entries}, {"DFL-CLU-000008", "DFL-CLU-00000G"})
        self.assertEqual(len({player.player_id for player, _, _ in entries}), 40)
        goalkeepers = {player.player_id for player, _, goalkeeper in entries if goalkeeper}
        self.assertEqual(goalkeepers, {"DFL-OBJ-0002DR", "DFL-OBJ-0002HE"})
        self.assertTrue(
            all(
                player.starting_position == PositionType.Goalkeeper
                for player, _, goalkeeper in entries
                if goalkeeper
            )
        )

    def test_frame_absolute_time_and_period_time_are_separate(self):
        first = self.long[self.long.frame_id == 10000].iloc[0]
        raw = self.sidecar[self.sidecar.frame_id == 10000].iloc[0]
        self.assertEqual(int(first.provider_timestamp_ns), int(raw.provider_timestamp_ns))
        self.assertEqual(first.provider_time_s, raw.provider_timestamp_ns / 1e9)
        self.assertEqual(first.kloppy_period_time_s, 0.0)
        self.assertEqual(first.period_label, "firstHalf")

    def test_native_metres_orientation_and_ball_metadata(self):
        first = self.long[self.long.frame_id == 10000]
        sommer = first[first.player_id == "DFL-OBJ-0002DR"].iloc[0]
        self.assertAlmostEqual(sommer.x_m, -46.73, places=12)
        self.assertAlmostEqual(sommer.y_m, 0.18, places=12)
        ball = first[first.object_type == "ball"].iloc[0]
        self.assertAlmostEqual(ball.x_m, 0.18, places=12)
        self.assertAlmostEqual(ball.y_m, -0.17, places=12)
        self.assertEqual(ball.ball_state, "alive")
        self.assertEqual(ball.ball_owning_team_id, "DFL-CLU-00000G")
        raw = self.sidecar[self.sidecar.frame_id == 10000].iloc[0]
        self.assertEqual(raw.provider_ball_object_id, "DFL-OBJ-0000XT")


if __name__ == "__main__":
    unittest.main()
