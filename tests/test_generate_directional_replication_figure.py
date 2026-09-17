from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import generate_directional_replication_figure as figure  # noqa: E402


AGGREGATE_SCHEMAS = {
    figure.IDSSE_POOLED: [
        "estimate", "ci_low", "ci_high", "valid_bootstrap_replicates", "five_m_translation_m"
    ],
    figure.IDSSE_MATCHES: [
        "match_id", "rows", "model_rank", "beta_goalward_m_per_m",
        "beta_outward_m_per_m", "outward_minus_goalward_m_per_m",
    ],
    figure.SKILLCORNER_POOLED: [
        "beta_goalward_m_per_m", "beta_outward_m_per_m",
        "outward_minus_goalward_m_per_m", "five_m_translation_m",
        "pooled_model_rank", "ci_low", "ci_high", "valid_bootstrap_replicates",
    ],
    figure.SKILLCORNER_MATCHES: [
        "match_id", "eligible_rows", "eligible_anchors", "model_rank",
        "beta_goalward_m_per_m", "beta_outward_m_per_m",
        "outward_minus_goalward_m_per_m", "positive_contrast",
    ],
    figure.ADDITIONAL_POOLED: [
        "classification", "beta_goalward_m_per_m", "beta_outward_m_per_m",
        "outward_minus_goalward_m_per_m", "five_m_translation_m", "ci_low",
        "ci_high", "valid_bootstrap_replicates",
    ],
    figure.ADDITIONAL_MATCHES: [
        "match_id", "eligible_rows", "eligible_anchors", "model_rank",
        "beta_goalward_m_per_m", "beta_outward_m_per_m",
        "outward_minus_goalward_m_per_m", "positive_contrast",
    ],
}


def test_governed_directional_inputs_are_exact_and_positive() -> None:
    assert figure.checked_pooled(figure.IDSSE_POOLED, figure.IDSSE_EXPECTED, "estimate") == figure.IDSSE_EXPECTED
    assert figure.checked_pooled(
        figure.SKILLCORNER_POOLED,
        figure.SKILLCORNER_EXPECTED,
        "outward_minus_goalward_m_per_m",
    ) == figure.SKILLCORNER_EXPECTED
    assert figure.checked_pooled(
        figure.ADDITIONAL_POOLED,
        figure.ADDITIONAL_EXPECTED,
        "outward_minus_goalward_m_per_m",
    ) == figure.ADDITIONAL_EXPECTED
    assert len(figure.checked_matches(figure.IDSSE_MATCHES, 7)) == 7
    assert len(figure.checked_matches(figure.SKILLCORNER_MATCHES, 9)) == 9
    assert len(figure.checked_matches(figure.ADDITIONAL_MATCHES, 10)) == 10


def test_figure_reads_only_frozen_aggregate_schemas() -> None:
    for path, expected_columns in AGGREGATE_SCHEMAS.items():
        assert path.is_relative_to(figure.ROOT / "outputs")
        with path.open(newline="", encoding="utf-8") as handle:
            assert csv.DictReader(handle).fieldnames == expected_columns


def test_render_is_deterministic_and_uses_aggregate_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(figure, "OUTPUT", tmp_path)
    figure.render()
    first = {suffix: (tmp_path / f"directional_replication.{suffix}").read_bytes() for suffix in ("png", "svg", "pdf")}
    figure.render()
    second = {suffix: (tmp_path / f"directional_replication.{suffix}").read_bytes() for suffix in ("png", "svg", "pdf")}
    assert first == second
    svg = first["svg"].decode("utf-8")
    assert "Separate frozen cohort estimates" in svg
    assert "10/10" in svg
    assert "Prospective" in svg or "prospective" in svg
