"""Synthetic pre-access tests for SkillCorner lateral-gradient v1."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import skillcorner_lateral_gradient_v1 as lateral  # noqa: E402
from skillcorner_lateral_gradient_support_preflight_v1 import SupportObservation, observation_digest  # noqa: E402


def _cfg(draws=40):
    cfg = copy.deepcopy(lateral.load_config())
    cfg["bootstrap"]["draws"] = draws
    cfg["bootstrap"]["minimum_valid_paired_draws"] = max(1, draws - 2)
    return cfg


def _rows(beta=0.25, matches=None):
    matches = tuple(matches or lateral.MATCHES)
    values = []
    for match_index, match in enumerate(matches):
        for period in (1, 2):
            for block in range(3):
                for within, z in enumerate((1.0, 4.0, 8.0)):
                    values.append({
                        "observation_id": f"{match}:{period}:{block}:{within}",
                        "match_id": match, "period": period, "block_id": block,
                        "z_m": z, "Y_m": 2.0 + match_index + beta * z,
                        "quality_pass": within != 2 or block % 2 == 0,
                    })
    return pd.DataFrame(values, columns=lateral.REQUIRED_COLUMNS)


def _support_row(match, focal, quality=True):
    return SupportObservation(match, 1, 100 + focal, focal, 0, 0.0, float(focal), float(focal), 0.0, 1.0, 1.0, 1.0 if quality else 0.0, quality)


def test_y_oracle_is_exact_near_minus_middle_difference():
    paths = {1: 3.0, 2: 6.0, 3: 9.0, 4: 4.0, 5: 8.0, 6: 12.0, 7: 16.0}
    assert lateral.construct_y_from_rank_paths(paths) == pytest.approx(-4.0)


@pytest.mark.parametrize("bad", [{1: 1.0}, {**{rank: 1.0 for rank in range(1, 8)}, 8: 1.0}])
def test_y_requires_exact_D1_D7_rank_set(bad):
    with pytest.raises(lateral.LateralGradientInvalid, match="exact D1-D7"):
        lateral.construct_y_from_rank_paths(bad)


def test_y_rejects_nonfinite_required_path():
    paths = {rank: 1.0 for rank in range(1, 8)}; paths[4] = np.nan
    with pytest.raises(lateral.LateralGradientInvalid, match="nonfinite"):
        lateral.construct_y_from_rank_paths(paths)


def test_equal_total_match_weight_recovers_analytic_beta_and_intercepts():
    rows = _rows(beta=0.375)
    fitted = lateral.fit_equal_match(rows, lateral.MATCHES)
    assert fitted["beta_lat_m_per_m"] == pytest.approx(0.375)
    assert fitted["rank"] == 10
    assert fitted["match_names"] == tuple(map(str, lateral.MATCHES))
    assert fitted["coefficients"][:-1] == pytest.approx(tuple([2.0, *range(1, 9)]))


def test_governed_response_constructor_uses_start_fixed_ranks_and_leave_one_out_paths():
    class Source:
        match_id = lateral.MATCHES[0]
        home_team_id, away_team_id = 1, 2
        meta = {"home_team_side": ["left_to_right", "right_to_left"]}

        def attacking_team(self, anchor): return 1
        def active_outfield(self, anchor, team): return (1,) if team == 1 else tuple(range(10, 20))
        def is_home(self, team): return team == 1
        def smooth_player(self, frame, player):
            if player == 1:
                return np.asarray([0.0, 0.0])
            rank = player - 9
            velocity = 0.01 * rank
            return np.asarray([float(rank) + velocity * (frame - 100), 0.0])

    row = SupportObservation(lateral.MATCHES[0], 1, 100, 1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, True)
    velocities = np.arange(1, 11, dtype=float) * 0.01
    relative_path = np.abs((10 * velocities - velocities.sum()) / 9) * 20
    expected = relative_path[:3].mean() - relative_path[3:7].mean()
    assert lateral._construct_governed_response(Source(), row) == pytest.approx(expected)


def test_equal_match_fit_is_not_mean_of_match_slopes():
    matches = lateral.MATCHES
    rows = _rows(beta=0.0)
    rows.loc[rows.match_id == matches[0], "Y_m"] = rows.loc[rows.match_id == matches[0], "z_m"] * 1.0
    rows.loc[rows.match_id == matches[1], "Y_m"] = rows.loc[rows.match_id == matches[1], "z_m"] * 3.0
    # Collapse z variation in match 1, so it carries less slope information even
    # though each match still has equal total row weight.
    mask = rows.match_id == matches[0]
    rows.loc[mask, "z_m"] = np.tile([1.0, 1.1, 1.2], int(mask.sum() / 3))
    pooled = lateral.fit_equal_match(rows, matches)["beta_lat_m_per_m"]
    slopes = lateral.match_slopes(rows, matches).beta_lat_m_per_m
    assert pooled != pytest.approx(float(slopes.mean()))


def test_match_slopes_and_lomo_use_frozen_A1_model():
    rows = _rows(beta=0.2)
    match = lateral.match_slopes(rows, lateral.MATCHES)
    lomo = lateral.lomo_slopes(rows, lateral.MATCHES)
    assert len(match) == len(lomo) == 9
    assert np.allclose(match.beta_lat_m_per_m, 0.2)
    assert np.allclose(lomo.beta_lat_m_per_m, 0.2)
    assert set(match.sign) == set(lomo.sign) == {"positive"}


def test_row_contract_rejects_duplicates_missing_matches_and_nonfinite_values():
    rows = _rows()
    with pytest.raises(lateral.LateralGradientInvalid, match="duplicate"):
        lateral.validate_rows(pd.concat([rows, rows.iloc[[0]]]), lateral.MATCHES)
    with pytest.raises(lateral.LateralGradientInvalid, match="population"):
        lateral.validate_rows(rows.loc[rows.match_id != lateral.MATCHES[-1]], lateral.MATCHES)
    bad = rows.copy(); bad.loc[0, "Y_m"] = np.inf
    with pytest.raises(lateral.LateralGradientInvalid, match="nonfinite"):
        lateral.validate_rows(bad, lateral.MATCHES)


def test_primary_and_quality_populations_remain_separate():
    rows = _rows()
    assert len(rows.loc[rows.quality_pass]) < len(rows)
    assert set(rows.loc[rows.quality_pass].observation_id) < set(rows.observation_id)
    assert lateral.fit_equal_match(rows.loc[rows.quality_pass], lateral.MATCHES)["beta_lat_m_per_m"] == pytest.approx(0.25)


def test_paired_block_bootstrap_is_deterministic_and_full_rank():
    result1 = lateral.paired_block_bootstrap(_rows(), lateral.MATCHES, 20, 20260909)
    result2 = lateral.paired_block_bootstrap(_rows(), lateral.MATCHES, 20, 20260909)
    assert len(result1["primary"]) == len(result1["quality"]) == 20
    assert np.array_equal(result1["primary"], result2["primary"])
    assert np.array_equal(result1["quality"], result2["quality"])


def test_block_resampling_preserves_simultaneous_attacker_rows():
    rows = _rows(matches=(1,))
    sampled = lateral._resample_blocks(rows, np.random.Generator(np.random.PCG64(7)))
    sizes = sampled.groupby(["match_id", "period", "bootstrap_block_instance"]).size()
    assert set(sizes) == {3}


def test_valid_draw_threshold_fails_closed():
    cfg = _cfg(draws=4); cfg["bootstrap"]["minimum_valid_paired_draws"] = 5
    with pytest.raises(lateral.LateralGradientInvalid, match="insufficient"):
        lateral.analyze(_rows(), cfg)


@pytest.mark.parametrize(
    ("beta", "low", "quality", "lomo", "expected"),
    [
        (0.2, 0.1, 0.1, [0.1] * 9, "SUPPORTED"),
        (0.2, -0.1, 0.1, [0.1] * 9, "MIXED"),
        (0.2, 0.1, -0.1, [0.1] * 9, "MIXED"),
        (0.2, 0.1, 0.1, [0.1] * 8 + [-0.1], "MIXED"),
        (0.0, -0.1, 0.1, [0.1] * 9, "NOT SUPPORTED"),
        (-0.2, -0.3, 0.1, [0.1] * 9, "NOT SUPPORTED"),
    ],
)
def test_frozen_result_classification(beta, low, quality, lomo, expected):
    assert lateral.classify_result(beta, low, quality, lomo) == expected
    assert lateral.classify_result(beta, low, quality, lomo, valid=False) == "INVALID"


def test_exact_support_digest_reconciliation_including_quality():
    matches = lateral.MATCHES[:2]
    rows = (_support_row(matches[0], 1, True), _support_row(matches[0], 2, False), _support_row(matches[1], 1, True))
    primary = observation_digest(rows); quality = observation_digest(tuple(row for row in rows if row.quality_pass))
    per_primary = {str(m): observation_digest(tuple(row for row in rows if row.match_id == m)) for m in matches}
    per_quality = {str(m): observation_digest(tuple(row for row in rows if row.match_id == m and row.quality_pass)) for m in matches}
    cfg = {"matches": matches, "support": {"primary_digest": primary, "quality_digest": quality, "primary_count": 3, "quality_count": 2, "per_match_counts": {str(matches[0]): {"primary": 2, "quality": 1}, str(matches[1]): {"primary": 1, "quality": 1}}}}
    manifest = {"counts": {"primary": 3, "quality": 2}, "observation_digests": {"primary": {"all_matches": primary, "per_match": per_primary}, "quality": {"all_matches": quality, "per_match": per_quality}}}
    assert lateral.reconcile_support_observations(rows, manifest, cfg) == {"primary": primary, "quality": quality}
    bad = copy.deepcopy(manifest); bad["observation_digests"]["primary"]["all_matches"] = "0" * 64
    with pytest.raises(lateral.LateralGradientInvalid, match="digest"):
        lateral.reconcile_support_observations(rows, bad, cfg)


def test_response_constructor_is_not_called_before_support_reconciliation(monkeypatch):
    cfg = lateral.load_config()
    monkeypatch.setattr(lateral, "verify_source_identity", lambda *_: {"release_commit": "synthetic", "files": []})
    monkeypatch.setattr(lateral, "_source_identities_match", lambda *_: True)
    monkeypatch.setattr(lateral, "SupportSource", lambda match, data: object())
    monkeypatch.setattr(lateral, "extract_match_support", lambda source: ((), {}))
    monkeypatch.setattr(lateral, "_construct_governed_response", lambda *_: pytest.fail("response must remain unopened"))
    with pytest.raises(lateral.LateralGradientInvalid, match="population"):
        lateral._load_execution_rows(Path("unused"), Path("unused"), cfg)


def test_default_and_missing_authorization_paths_never_call_provider_loader(monkeypatch):
    monkeypatch.setattr(lateral, "_load_execution_rows", lambda *_: pytest.fail("provider loader called"))
    with pytest.raises(lateral.LateralGradientInvalid, match="authorization"):
        lateral.execute_response()
    with pytest.raises(SystemExit):
        lateral.main([])


def test_reviewed_source_test_hashes_gate_precedes_provider_loader(monkeypatch, tmp_path):
    monkeypatch.setattr(lateral, "_load_execution_rows", lambda *_: pytest.fail("provider loader called"))
    with pytest.raises(lateral.LateralGradientInvalid, match="reviewed source/test hashes"):
        lateral.execute_response(
            execute=True, data_dir=tmp_path, pinned_repository=tmp_path,
            authorization_reference="synthetic-review", expected_implementation_hashes={},
            output=tmp_path / "output", report=tmp_path / "report.md",
        )


def test_verify_freeze_is_data_free_and_hash_binds_support_package(monkeypatch):
    monkeypatch.setattr(lateral, "_load_execution_rows", lambda *_: pytest.fail("provider loader called"))
    frozen = lateral.verify_freeze()
    assert str(lateral.SOURCE.relative_to(ROOT)) in frozen
    assert str(lateral.TESTS.relative_to(ROOT)) in frozen


def test_output_schema_is_compact_and_forbids_row_content(tmp_path):
    cfg = _cfg(draws=4)
    result = lateral.analyze(_rows(), cfg)
    provenance = {"authorization_reference": "synthetic", "frozen_hashes": {}, "observation_digests": {"primary": "a", "quality": "b"}}
    payloads = lateral.build_payloads(result, provenance, cfg)
    lateral.validate_public_payloads(payloads, cfg)
    assert set(payloads) == set(cfg["outputs"]["files"]) - {"reproduction.json", "final_hashes.json"}
    bad = dict(payloads); bad["manifest.json"] += b'"row_level_Y"\n'
    with pytest.raises(lateral.LateralGradientInvalid, match="forbidden"):
        lateral.validate_public_payloads(bad, cfg)


def test_deterministic_closure_and_authoritative_hashes(tmp_path):
    cfg = _cfg(draws=4)
    result = lateral.analyze(_rows(), cfg)
    provenance = {"authorization_reference": "synthetic", "frozen_hashes": {}, "observation_digests": {"primary": "a", "quality": "b"}}
    payloads = lateral.build_payloads(result, provenance, cfg)
    output, report = tmp_path / "outputs", tmp_path / "report.md"
    final = lateral.close_reproduced_package(payloads, dict(payloads), output, report, cfg, "synthetic")
    assert final["closure_status"] == "FINAL_PACKAGE_VALID"
    assert lateral.validate_final_hashes(output, cfg, report)
    assert output.exists() and report.exists()


def test_closure_rejects_nondeterminism_and_existing_destination(tmp_path):
    cfg = _cfg(draws=4)
    result = lateral.analyze(_rows(), cfg)
    provenance = {"authorization_reference": "synthetic", "frozen_hashes": {}, "observation_digests": {"primary": "a", "quality": "b"}}
    payloads = lateral.build_payloads(result, provenance, cfg)
    changed = dict(payloads); changed["bootstrap_summary.json"] += b" "
    with pytest.raises(lateral.LateralGradientInvalid, match="reproduction"):
        lateral.close_reproduced_package(payloads, changed, tmp_path / "out", tmp_path / "report", cfg, "synthetic")
    (tmp_path / "existing").mkdir()
    with pytest.raises(lateral.LateralGradientInvalid, match="overwrite"):
        lateral.close_reproduced_package(payloads, payloads, tmp_path / "existing", tmp_path / "other", cfg, "synthetic")


def test_protocol_config_and_support_package_are_bound_without_response_access():
    cfg = lateral.load_config()
    assert cfg["status"].endswith("RESPONSE_ACCESS_NOT_AUTHORIZED")
    assert cfg["outcome"]["formula"].startswith("mean_D1_D3")
    assert cfg["model"]["additional_covariates"] == []
    assert cfg["support"]["primary_digest"] == "2dc4e404e2c462c54416ac122f9a33950ced22d5e5e2fe5dc6ca7760d892d018"
    assert lateral.sha(ROOT / cfg["support"]["manifest_path"]) == cfg["support"]["manifest_sha256"]
    assert lateral.sha(ROOT / cfg["support"]["source_hashes_path"]) == cfg["support"]["source_hashes_sha256"]


@pytest.mark.provider_data
def test_future_provider_execution_remains_explicitly_unauthorized():
    pytest.skip("requires a separate reviewed response-access authorization")
