from __future__ import annotations

import sys
from pathlib import Path
import unittest

import polars as pl


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.canonical_tracking import (  # noqa: E402
    CANONICAL_SCHEMA,
    CONTRACT_VERSION,
    canonical_frame,
    validate_chunk,
)
from infrastructure import kloppy_idsse_adapter as idsse  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402


class CanonicalContractUnitTest(unittest.TestCase):
    def test_explicit_dtypes_and_row_invariants(self):
        row = {
            "match_id": "test:match",
            "period": 1,
            "frame_id_provider": "1",
            "time_period_s": 0.0,
            "time_match_s": 0.0,
            "entity_type": "ball",
            "team_key": None,
            "player_key": None,
            "is_goalkeeper": False,
            "x_m": None,
            "y_m": None,
            "z_m": None,
            "is_present": False,
            "coordinate_valid": False,
            "support_state": "ball_absent",
            "ball_state": "unknown",
            "possession_team_key": None,
            "pitch_length_m": 105.0,
            "pitch_width_m": 68.0,
        }
        table = canonical_frame([row])
        self.assertEqual(table.schema, CANONICAL_SCHEMA)
        self.assertEqual(validate_chunk(table)["rows"], 1)
        self.assertEqual(CONTRACT_VERSION, "1.0.0")

    def test_invalid_present_coordinate_relation_fails(self):
        table = pl.DataFrame(
            {
                name: pl.Series(name, [None], dtype=dtype)
                for name, dtype in CANONICAL_SCHEMA.items()
            }
        ).with_columns(
            pl.lit("x").alias("match_id"),
            pl.lit(1, dtype=pl.UInt8).alias("period"),
            pl.lit("1").alias("frame_id_provider"),
            pl.lit(0.0).alias("time_period_s"),
            pl.lit(0.0).alias("time_match_s"),
            pl.lit("player").alias("entity_type"),
            pl.lit("t").alias("team_key"),
            pl.lit("p").alias("player_key"),
            pl.lit(False).alias("is_goalkeeper"),
            pl.lit(False).alias("is_present"),
            pl.lit(True).alias("coordinate_valid"),
            pl.lit("provider_entity_absent").alias("support_state"),
            pl.lit(105.0).alias("pitch_length_m"),
            pl.lit(68.0).alias("pitch_width_m"),
        )
        with self.assertRaises(ValueError):
            validate_chunk(table)


class CanonicalProviderCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m_home, cls.m_away = metrica.game1_paths(ROOT)
        cls.m_index = metrica.read_provider_frame_index(cls.m_home)
        cls.m_dataset = metrica.load_dataset(cls.m_home, cls.m_away, limit=4)
        cls.m_table = next(
            metrica.iter_canonical_polars_chunks(
                cls.m_dataset, cls.m_index, frames_per_chunk=len(cls.m_dataset.frames)
            )
        )
        cls.i_meta, cls.i_event, cls.i_tracking = idsse.idsse_paths(ROOT, "J03WMX")
        cls.i_sidecar = idsse.read_ball_frame_sidecar(cls.i_tracking)
        cls.i_dataset = idsse.load_dataset(cls.i_meta, cls.i_tracking, limit=4)
        cls.i_table = next(
            idsse.iter_canonical_polars_chunks(
                cls.i_dataset, cls.i_sidecar, frames_per_chunk=len(cls.i_dataset.frames)
            )
        )

    def test_both_providers_have_identical_schema(self):
        self.assertEqual(self.m_table.schema, CANONICAL_SCHEMA)
        self.assertEqual(self.i_table.schema, CANONICAL_SCHEMA)
        validate_chunk(self.m_table)
        validate_chunk(self.i_table)

    def test_time_and_fixed_pitch_coordinate_contract(self):
        m_first = self.m_table.filter(
            (pl.col("frame_id_provider") == "1")
            & (pl.col("player_key") == "metrica:Home:11")
        ).row(0, named=True)
        self.assertEqual(m_first["time_period_s"], 0.04)
        self.assertEqual(m_first["time_match_s"], 0.04)
        self.assertGreaterEqual(m_first["x_m"], -52.5)
        self.assertLessEqual(m_first["x_m"], 52.5)
        i_first = self.i_table.filter(
            (pl.col("frame_id_provider") == "10000")
            & (pl.col("player_key") == "sportec:DFL-OBJ-0002DR")
        ).row(0, named=True)
        self.assertEqual(i_first["time_period_s"], 0.0)
        self.assertEqual(i_first["time_match_s"], 0.0)
        self.assertAlmostEqual(i_first["x_m"], -46.73, places=12)
        self.assertAlmostEqual(i_first["y_m"], 0.18, places=12)

    def test_reversible_ids_goalkeepers_and_null_support(self):
        m_null = self.m_table.filter(
            (pl.col("frame_id_provider") == "1")
            & (pl.col("player_key") == "metrica:Home:12")
        ).row(0, named=True)
        self.assertFalse(m_null["is_present"])
        self.assertFalse(m_null["coordinate_valid"])
        self.assertEqual(m_null["support_state"], "not_observed_unspecified")
        self.assertEqual(
            set(self.m_table.filter(pl.col("is_goalkeeper")).get_column("player_key").unique().to_list()),
            {"metrica:Home:11", "metrica:Away:25"},
        )
        i_null = self.i_table.filter(
            (pl.col("frame_id_provider") == "10000")
            & (pl.col("player_key") == "sportec:DFL-OBJ-0000M0")
        ).row(0, named=True)
        self.assertFalse(i_null["is_present"])
        self.assertEqual(i_null["support_state"], "provider_entity_absent")

    def test_provenance_sidecars_are_complete_and_noninferential(self):
        m = metrica.canonical_provenance(self.m_dataset, self.m_home, self.m_away)
        i = idsse.canonical_provenance(
            self.i_dataset, self.i_sidecar, self.i_meta, self.i_event, self.i_tracking
        )
        for sidecar in (m, i):
            self.assertEqual(sidecar["contract_version"], CONTRACT_VERSION)
            self.assertFalse(sidecar["coordinates_attacking_direction_normalized"])
            self.assertFalse(sidecar["interpolation_used"])
            self.assertTrue(sidecar["team_id_map_provider_to_canonical"])
            self.assertTrue(sidecar["player_id_map_provider_to_canonical"])
        self.assertFalse(m["possession_team_available"])
        self.assertTrue(i["possession_team_available"])


if __name__ == "__main__":
    unittest.main()
