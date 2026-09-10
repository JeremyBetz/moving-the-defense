"""Synthetic pre-access tests for SkillCorner lateral-gradient v1."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
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
    rows = _rows()
    observations = _support_observations(rows)
    cfg["support"].update(primary_count=len(rows), quality_count=int(rows.quality_pass.sum()),
                          primary_digest=observation_digest(observations),
                          quality_digest=observation_digest(tuple(r for r in observations if r.quality_pass)),
                          per_match_counts={str(m): {"primary": int((rows.match_id == m).sum()),
                                                    "quality": int(((rows.match_id == m) & rows.quality_pass).sum())}
                                            for m in cfg["matches"]})
    return cfg


def _rows(beta=0.25, matches=None):
    matches = tuple(matches or lateral.MATCHES)
    values = []
    for match_index, match in enumerate(matches):
        for period in (1, 2):
            for block in range(3):
                for within, z in enumerate((1.0, 4.0, 8.0)):
                    values.append({
                        "observation_id": f"{match}:{period}:{600 * block + 100}:{within + 1}",
                        "match_id": match, "period": period, "block_id": block,
                        "z_m": z, "Y_m": 2.0 + match_index + beta * z,
                        "quality_pass": within != 2 or block % 2 == 0,
                    })
    return pd.DataFrame(values, columns=lateral.REQUIRED_COLUMNS)


def _support_observations(rows):
    return tuple(SupportObservation(int(r.match_id), int(r.period), int(r.observation_id.split(":")[2]),
                                    int(r.observation_id.split(":")[3]), int(r.block_id), 0., float(r.z_m),
                                    float(r.z_m), 0., 1., 1., 1. if r.quality_pass else 0., bool(r.quality_pass))
                 for r in rows.itertuples())


def _provenance(cfg):
    return {"authorization_reference": "synthetic", "frozen_hashes": lateral.verify_freeze(),
            "observation_digests": {key: cfg["support"][f"{key}_digest"] for key in ("primary", "quality")}}


def _payloads(cfg):
    return lateral.build_payloads(lateral.analyze(_rows(), cfg), _provenance(cfg), cfg)


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
    provenance = _provenance(cfg)
    payloads = lateral.build_payloads(result, provenance, cfg)
    lateral.validate_public_payloads(payloads, cfg)
    assert set(payloads) == set(cfg["outputs"]["files"]) - {"reproduction.json", "final_hashes.json"}
    bad = dict(payloads); bad["manifest.json"] += b'"row_level_Y"\n'
    with pytest.raises(lateral.LateralGradientInvalid, match="forbidden"):
        lateral.validate_public_payloads(bad, cfg)


def test_deterministic_closure_and_authoritative_hashes(tmp_path):
    cfg = _cfg(draws=4)
    result = lateral.analyze(_rows(), cfg)
    provenance = _provenance(cfg)
    payloads = lateral.build_payloads(result, provenance, cfg)
    output, report = tmp_path / "outputs", tmp_path / "report.md"
    final = lateral.close_reproduced_package(payloads, dict(payloads), output, report, cfg, "synthetic")
    assert final["closure_status"] == "FINAL_PACKAGE_VALID"
    assert lateral.validate_final_hashes(output, cfg, report)
    assert output.exists() and report.exists()


def test_closure_rejects_nondeterminism_and_existing_destination(tmp_path):
    cfg = _cfg(draws=4)
    result = lateral.analyze(_rows(), cfg)
    provenance = _provenance(cfg)
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


def test_unequal_match_size_variance_and_slopes_require_equal_total_weights(monkeypatch):
    values = []
    for match, zs, slope in [(1, [0., 2.], 1.), (2, [0., 4.] * 4, 3.)]:
        for index, z in enumerate(zs):
            values.append((f"{match}:{index}", match, 1, 0, z, 7 * match + slope * z, True))
    rows = pd.DataFrame(values, columns=lateral.REQUIRED_COLUMNS)
    # Variances 1 and 4: (1*1 + 4*3)/(1+4) = 13/5.
    # Row pooling instead gives (2*1*1 + 8*4*3)/(2*1 + 8*4) = 49/17.
    correct = lateral.fit_equal_match(rows, (1, 2))["beta_lat_m_per_m"]
    assert correct == pytest.approx(13 / 5)
    assert correct != pytest.approx(49 / 17)
    monkeypatch.setattr(lateral.design, "equal_match_weights", lambda ids: np.ones(len(ids)))
    assert lateral.fit_equal_match(rows, (1, 2))["beta_lat_m_per_m"] == pytest.approx(49 / 17)


class CrossingSource:
    home_team_id, away_team_id = 1, 2
    meta = {"home_team_side": ["left_to_right", "right_to_left"]}

    def attacking_team(self, anchor): return 1
    def active_outfield(self, anchor, team): return tuple(range(10, 20))
    def is_home(self, team): return team == 1
    def smooth_player(self, frame, player):
        if player < 10:
            return np.asarray([0., 0.])
        k = frame - 100
        excursion = min(k, 20 - k) * .5 if player == 12 else 0.
        return np.asarray([player - 9 + excursion, 0.])


def test_response_fixed_rank_crossing_matches_independent_oracle(monkeypatch):
    source = CrossingSource()
    row = _support_row(lateral.MATCHES[0], 1)
    from dataclasses import replace
    row = replace(row, anchor_provider_frame=100)
    recorded = []
    original = lateral.sorted_rank_ids
    def ranks(*args):
        result = original(*args); recorded.append((args[1], result)); return result
    monkeypatch.setattr(lateral, "sorted_rank_ids", ranks)
    actual = lateral._construct_governed_response(source, row)
    assert recorded == [(100, tuple(range(10, 20)))]
    assert original(source, 110, 1, tuple(range(10, 20)), 1, 0.) != recorded[0][1]
    # Only original D3 travels 10m. Each other defender's relative path is 10/9.
    assert actual == pytest.approx((10 + 2 * 10 / 9) / 3 - 10 / 9)
    assert actual == pytest.approx(80 / 27)
    # Deliberately wrong rank-slot trajectories demonstrate discrimination.
    wrong = []
    for frame in range(100, 121):
        ordered = original(source, frame, 1, tuple(range(10, 20)), 1, 0.)
        positions = np.stack([source.smooth_player(frame, p) for p in ordered])
        wrong.append((10 * positions - positions.sum(axis=0)) / 9)
    paths = np.linalg.norm(np.diff(wrong, axis=0), axis=2).sum(axis=0)
    assert actual != pytest.approx(paths[:3].mean() - paths[3:7].mean())


def test_returning_trajectory_requires_accumulated_path_not_net_displacement():
    from dataclasses import replace
    source = CrossingSource(); row = replace(_support_row(lateral.MATCHES[0], 1), anchor_provider_frame=100)
    for player in range(10, 20):
        np.testing.assert_array_equal(source.smooth_player(100, player), source.smooth_player(120, player))
    assert lateral._construct_governed_response(source, row) == pytest.approx(80 / 27)
    assert lateral._construct_governed_response(source, row) > 2  # net oracle is exactly zero


def test_paired_bootstrap_uses_actual_shared_block_multiplicities(monkeypatch):
    rows = _rows()
    rows["Y_m"] += rows.block_id * rows.z_m ** 2 + rows.period * .3
    calls = []
    fit = lateral.fit_equal_match
    def spy(frame, matches):
        calls.append(frame.copy()); return fit(frame, matches)
    monkeypatch.setattr(lateral, "fit_equal_match", spy)
    actual = lateral.paired_block_bootstrap(rows, lateral.MATCHES, 8, 20260909)
    assert len(actual["primary"]) == len(actual["quality"]) == 8
    assert len(calls) == 16
    for primary, quality in zip(calls[::2], calls[1::2]):
        pd.testing.assert_frame_equal(primary.loc[primary.quality_pass].reset_index(drop=True), quality.reset_index(drop=True))
    # Independent draws really differ for this fixture, unlike constant-slope data.
    rng = np.random.Generator(np.random.PCG64(20260910))
    wrong = []
    for _ in range(8):
        sample = lateral._resample_blocks(rows.loc[rows.quality_pass], rng)
        wrong.append(fit(sample[list(lateral.REQUIRED_COLUMNS)], lateral.MATCHES)["beta_lat_m_per_m"])
    assert not np.allclose(actual["quality"], wrong)


@pytest.mark.parametrize("case", ["individual_y", "coordinates", "one_match", "duplicate_match", "nan", "inf", "json_overflow", "duplicate_key", "classification", "sample", "counts", "lomo", "lineage", "qc", "extra_column"])
def test_structural_validator_rejects_malformed_or_reconstructive_packages(case):
    cfg = _cfg(4); payloads = _payloads(cfg)
    if case in ("individual_y", "coordinates", "classification", "counts", "lineage", "duplicate_key", "json_overflow"):
        data = json.loads(payloads["manifest.json"])
        if case == "individual_y": data["observations"] = [{"observation_id": "synthetic", "Y_m": 1.}]
        if case == "coordinates": data["position"] = {"player_id": 1, "x_m": 3., "y_m": 2.}
        if case == "classification": data["classification"] = "NOT SUPPORTED"
        if case == "counts": data["counts"]["primary"] += 1
        if case == "lineage": data["support_digests"]["quality"] = "0" * 64
        payloads["manifest.json"] = json.dumps(data).encode()
        if case == "duplicate_key": payloads["manifest.json"] = payloads["manifest.json"][:-1] + b', "status": "duplicate"}'
        if case == "json_overflow": payloads["manifest.json"] = payloads["manifest.json"].replace(b'"primary": 162', b'"primary": 1e999', 1)
    elif case == "qc":
        data = json.loads(payloads["hard_qc.json"]); data["full_rank"] = False
        payloads["hard_qc.json"] = json.dumps(data).encode()
    else:
        name = "lomo_estimates.csv" if case == "lomo" else "quality_estimate.csv" if case == "sample" else "match_estimates.csv"
        data = pd.read_csv(io.BytesIO(payloads[name]))
        if case in ("one_match", "lomo"): data = data.iloc[:1]
        if case == "duplicate_match": data.loc[1, "match_id"] = data.loc[0, "match_id"]
        if case in ("nan", "inf"): data.loc[0, "beta_lat_m_per_m"] = np.nan if case == "nan" else np.inf
        if case == "sample": data.loc[0, "sample"] = "primary"
        if case == "extra_column": data["observation_id"] = "synthetic"
        payloads[name] = data.to_csv(index=False).encode()
    with pytest.raises(lateral.LateralGradientInvalid):
        lateral.validate_public_payloads(payloads, cfg)


@pytest.mark.parametrize("failure", ["authoritative_hash", "publish", "revalidate"])
def test_closure_failure_never_leaves_final_valid_marker(tmp_path, monkeypatch, failure):
    cfg = _cfg(4); payloads = _payloads(cfg)
    output, report = tmp_path / "out", tmp_path / "report.md"
    if failure == "authoritative_hash":
        original = lateral.sha
        monkeypatch.setattr(lateral, "sha", lambda path: "0" * 64 if Path(path) == output / "pooled_estimate.csv" else original(path))
    elif failure == "publish":
        original = lateral.os.replace
        def replace(src, dst):
            if Path(dst) == output / "final_hashes.json": raise OSError("synthetic publication failure")
            return original(src, dst)
        monkeypatch.setattr(lateral.os, "replace", replace)
    else:
        def fail(*args): raise lateral.LateralGradientInvalid("synthetic final revalidation failure")
        monkeypatch.setattr(lateral, "validate_final_hashes", fail)
    with pytest.raises((lateral.LateralGradientInvalid, OSError)):
        lateral.close_reproduced_package(payloads, payloads, output, report, cfg, "synthetic")
    assert output.exists()  # pending diagnosis evidence is retained
    assert not (output / "final_hashes.json").exists()
    assert json.loads((output / "manifest.json").read_text())["status"] == "STAGING_QC_PASSED_NOT_AUTHORITATIVE"


@pytest.mark.parametrize("custom", [False, True])
def test_actual_report_identity_and_final_marker_order(tmp_path, monkeypatch, custom):
    cfg = _cfg(4); payloads = _payloads(cfg)
    output = tmp_path / cfg["outputs"]["directory"]
    report = tmp_path / ("custom/location.md" if custom else cfg["outputs"]["report"])
    events = []
    replace = lateral.os.replace; validate = lateral._validate_authoritative
    def record_replace(src, dst):
        if Path(dst) == output / "final_hashes.json": events.append("publish")
        return replace(src, dst)
    def record_validate(out, *args):
        if out == output: events.append("final-check" if (out / "final_hashes.json").exists() else "pending-check")
        return validate(out, *args)
    monkeypatch.setattr(lateral.os, "replace", record_replace)
    monkeypatch.setattr(lateral, "_validate_authoritative", record_validate)
    final = lateral.close_reproduced_package(payloads, payloads, output, report, cfg, "synthetic")
    assert events == ["pending-check", "publish", "final-check"]
    assert (output / final["report_path"]).resolve() == report.resolve()
    assert lateral.validate_final_hashes(output, cfg)  # report check cannot be omitted
    reproduction = json.loads((output / "reproduction.json").read_text())
    assert reproduction["report_metadata"] == {"path": final["report_path"], "sha256": lateral.sha(report)}
    for name, digest in final["artifacts_sha256"].items(): assert lateral.sha(output / name) == digest
    for text in ("IDSSE spatial pattern", "already used previously", "Majority-detected beta_lat", "Positive match slopes", "Leave-one-match-out", "Valid paired bootstrap", "does not validate the IDSSE heatmap"):
        assert text in report.read_text()
    wrong = dict(final, report_path="wrong/report.md")
    with pytest.raises(lateral.LateralGradientInvalid, match="path/hash"):
        lateral._validate_authoritative(output, cfg, wrong, report)


@pytest.mark.parametrize("name,case", [("reproduction.json", "extra"), ("final_hashes.json", "extra"), ("reproduction.json", "wrong_report")])
def test_final_json_unknown_nested_fields_rejected(tmp_path, name, case):
    cfg = _cfg(4); payloads = _payloads(cfg)
    output, report = tmp_path / "out", tmp_path / "report.md"
    lateral.close_reproduced_package(payloads, payloads, output, report, cfg, "synthetic")
    data = json.loads((output / name).read_text())
    if case == "wrong_report": data["report_metadata"]["path"] = "wrong/report.md"
    elif name == "reproduction.json": data["report_metadata"]["individual"] = {"Y_m": 1.}
    else: data["artifacts_sha256"]["player_id"] = "synthetic"
    (output / name).write_text(json.dumps(data))
    with pytest.raises(lateral.LateralGradientInvalid): lateral.validate_final_hashes(output, cfg, report)


def test_ols_dependency_mismatch_stops_before_loader(monkeypatch, tmp_path):
    original = lateral.sha
    target = ROOT / "src/defensive_reorganization_spatial_value_v1_design.py"
    monkeypatch.setattr(lateral, "sha", lambda path: "0" * 64 if Path(path) == target else original(path))
    monkeypatch.setattr(lateral, "_load_execution_rows", lambda *_: pytest.fail("provider access"))
    with pytest.raises(lateral.LateralGradientInvalid, match="hash mismatch"):
        lateral.execute_response(execute=True, data_dir=tmp_path, pinned_repository=tmp_path, authorization_reference="synthetic")


def test_synthetic_execution_reconciles_and_closes_end_to_end(tmp_path, monkeypatch):
    cfg = _cfg(4); observations = _support_observations(_rows())
    manifest = {"counts": {"primary": len(observations), "quality": sum(r.quality_pass for r in observations)},
                "observation_digests": {sample: {"all_matches": cfg["support"][f"{sample}_digest"],
                    "per_match": {str(m): observation_digest(tuple(r for r in observations if r.match_id == m and (sample == "primary" or r.quality_pass))) for m in lateral.MATCHES}}
                    for sample in ("primary", "quality")}}
    committed = json.loads((ROOT / cfg["support"]["source_hashes_path"]).read_text())
    identity = copy.deepcopy(committed)
    for item in identity["files"]:
        item["materialized_sha256"] = item["materialized_sha256_before"]
        item["materialized_size"] = item["materialized_size_before"]
    class Source(CrossingSource):
        def __init__(self, match, unused): self.match_id = match
        def smooth_player(self, frame, player):
            if player < 10: return np.asarray([0., 0.])
            rank = player - 9
            return np.asarray([rank + rank * .01 * (frame % 600 - 100), 0.])
    read = Path.read_text
    def read_metadata(path, *args, **kwargs):
        if path == ROOT / cfg["support"]["manifest_path"]: return json.dumps(manifest)
        return read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read_metadata)
    monkeypatch.setattr(lateral, "load_config", lambda *args: cfg)
    monkeypatch.setattr(lateral, "verify_source_identity", lambda *_: copy.deepcopy(identity))
    monkeypatch.setattr(lateral, "SupportSource", Source)
    monkeypatch.setattr(lateral, "extract_match_support", lambda source: (tuple(r for r in observations if r.match_id == source.match_id), {}))
    frozen = lateral.verify_freeze()
    hashes = {str(path.relative_to(ROOT)): frozen[str(path.relative_to(ROOT))] for path in (lateral.SOURCE, lateral.TESTS)}
    output, report = tmp_path / "out", tmp_path / "report.md"
    final = lateral.execute_response(execute=True, data_dir=tmp_path / "synthetic-input", pinned_repository=tmp_path / "synthetic-release", authorization_reference="synthetic", expected_implementation_hashes=hashes, output=output, report=report)
    assert final["closure_status"] == "FINAL_PACKAGE_VALID"
    assert lateral.validate_final_hashes(output, cfg, report)
    result = json.loads((output / "manifest.json").read_text())
    assert result["counts"] == lateral._expected_counts(cfg)
    assert result["classification"] in {"SUPPORTED", "MIXED", "NOT SUPPORTED"}


@pytest.mark.provider_data
def test_future_provider_execution_remains_explicitly_unauthorized():
    pytest.skip("requires a separate reviewed response-access authorization")
