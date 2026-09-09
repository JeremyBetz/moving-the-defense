"""Synthetic-only preflight tests: no real provider directory or outcome input."""

import ast
import copy
import hashlib
import inspect
import json
import subprocess
import sys
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import skillcorner_lateral_gradient_support_preflight_v1 as preflight
import defensive_reorganization_spatial_form_skillcorner_external as inherited
import defensive_reorganization_spatial_value_v1_design as design


@pytest.fixture
def config():
    return json.loads((ROOT / preflight.CONFIG).read_text(encoding="utf-8"))


def native_fragments(match=preflight.MATCHES[0], end=142, length=105.0, width=68.0):
    players = [{"id": p, "team_id": 1 if p <= 10 else 2, "player_role": {"id": 1},
                "playing_time": {"total": {"start_frame": 0, "end_frame": 20000}}} for p in range(1, 21)]
    metadata = {"id": match, "status": "played", "home_team": {"id": 1}, "away_team": {"id": 2},
                "home_team_side": ["right_to_left", "left_to_right"], "pitch_length": length,
                "pitch_width": width, "players": players}
    tracking = []
    for period, start in ((1, 0), (2, 10000)):
        for index in range(end + 1):
            seconds = index / 10 + (2700 if period == 2 else 0)
            records = [{"player_id": p, "x": -30 + 2 * p + index * 0.01,
                        "y": 5 + ((p - 1) % 3) * 12, "is_detected": True} for p in range(1, 21)]
            tracking.append({"frame": start + index, "period": period,
                "timestamp": f"{int(seconds // 60)}:{seconds % 60:04.1f}", "player_data": records,
                "ball_data": {"x": records[0]["x"], "y": records[0]["y"], "is_detected": True},
                "possession": {"group": "home team"}})
    phases = [{"frame_start": 0, "frame_end": end}, {"frame_start": 10000, "frame_end": 10000 + end}]
    return metadata, tracking, phases


def source_from(fragments, match=preflight.MATCHES[0]):
    return preflight.SupportSource.from_records(match, *fragments)


def support_rows():
    """24 times per broad region, 4 period-aware blocks, with simultaneity."""
    rows = []
    for match in preflight.MATCHES:
        for region, base in enumerate((4.0, 14.0, 24.0)):
            for index in range(24):
                period, block = 1 + index // 12, (index % 12) // 6
                frame = (period - 1) * 10000 + block * 600 + (index % 6) * 40 + region * 2 + 80
                z = base + (index % 2)
                for player in (2, 3):
                    rows.append(preflight.SupportObservation(match, period, frame, player, block,
                        2.0, -z, z, -2.0, 1.0, 1.0, 1.0, True))
    return rows


def exclusions():
    return {match: Counter() for match in preflight.MATCHES}


def synthetic_counts(config, rows):
    """Change only synthetic expected counts; production verifies frozen hashes."""
    result = copy.deepcopy(config)
    result["population_reconciliation"]["rows"] = [
        [match, len({(r.period, r.anchor_provider_frame) for r in rows if r.match_id == match}),
         sum(r.match_id == match for r in rows), sum(r.match_id == match and r.quality_pass for r in rows)]
        for match in preflight.MATCHES]
    return result


def test_frozen_config_and_protocol_and_inherited_hashes():
    config, hashes = preflight.verify_freeze()
    assert hashes[preflight.PROTOCOL] == preflight.FROZEN[preflight.PROTOCOL]
    assert hashes[preflight.CONFIG] == preflight.FROZEN[preflight.CONFIG]
    assert config["data"]["formal_matches"] == list(preflight.MATCHES)


def test_default_and_verify_freeze_never_open_provider_files(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("provider access")

    monkeypatch.setattr(preflight, "SupportSource", forbidden)
    monkeypatch.setattr(preflight, "verify_source_identity", forbidden)
    with pytest.raises(SystemExit) as ordinary:
        preflight.main([])
    assert ordinary.value.code == 2
    with pytest.raises(SystemExit) as help_result:
        preflight.main(["--help"])
    assert help_result.value.code == 0
    assert preflight.main(["--verify-freeze"]) == 0
    assert preflight.main(["--execute-support"]) == 1
    with pytest.raises(preflight.SupportError, match="authorization"):
        preflight.execute_support()
    with pytest.raises(preflight.SupportError, match="reviewed source/test"):
        preflight.execute_support(execute=True, data_dir="unused", pinned_repository="unused", authorization_reference="synthetic")
    capsys.readouterr()


def test_projection_does_not_discover_other_fields_and_does_not_mutate():
    metadata, tracking, phases = native_fragments()
    metadata["irrelevant"] = "ignored"
    tracking[0]["unrelated"] = "ignored"
    tracking[0]["player_data"][0]["unrelated"] = "ignored"
    phases[0]["label"] = "ignored"
    original = copy.deepcopy((metadata, tracking, phases))
    source = source_from((metadata, tracking, phases))
    assert (metadata, tracking, phases) == original
    assert "irrelevant" not in source.meta
    assert set(source.rows[0]) == {"frame", "period", "timestamp", "player_data", "ball_data", "possession"}
    assert set(source.rows[0]["player_data"][0]) == {"player_id", "x", "y", "is_detected"}
    before = copy.deepcopy(source.rows)
    rows, _ = preflight.extract_match_support(source)
    assert rows and source.rows == before


def test_native_file_loader_uses_only_three_synthetic_inputs(tmp_path, monkeypatch):
    match = preflight.MATCHES[0]
    metadata, tracking, phases = native_fragments(match)
    (tmp_path / f"{match}_match.json").write_text(json.dumps(metadata), encoding="utf-8")
    (tmp_path / f"{match}_tracking_extrapolated.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in tracking), encoding="utf-8")
    (tmp_path / f"{match}_phases_of_play.csv").write_text(
        "frame_start,frame_end\n" + "".join(f"{p['frame_start']},{p['frame_end']}\n" for p in phases), encoding="utf-8")
    original_open, accessed = Path.open, []
    def bounded_open(path, *args, **kwargs):
        assert path.parent == tmp_path
        accessed.append(path.name)
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", bounded_open)
    source = preflight.SupportSource(match, tmp_path)
    rows, _ = preflight.extract_match_support(source)
    assert len(rows) == 36
    assert set(accessed) == {t.format(match) for t in preflight.TEMPLATES}


@pytest.mark.parametrize("bad_match", [1953632, 123])
def test_excluded_and_nonformal_match_rejected(bad_match):
    with pytest.raises(preflight.SupportError, match="formal population"):
        source_from(native_fragments(bad_match), bad_match)


def test_start_location_uses_three_frame_canonical_t_minus_two():
    fragments = native_fragments(length=100, width=80)
    for row in fragments[1]:
        k = row["frame"] % 10000
        p = row["player_data"][1]
        p["x"] = -10 + 0.001 * k * k
        p["y"] = -5 - 0.0005 * k * k
    rows, _ = preflight.extract_match_support(source_from(fragments))
    row = next(r for r in rows if r.period == 1 and r.anchor_provider_frame == 80 and r.focal_player_id == 2)
    # Mean of (60-1)^2, 60^2, (60+1)^2 is 60^2 + 2/3.
    mean_square = 3600 + 2 / 3
    assert row.x_start_m == pytest.approx(1.05 * (-10 + 0.001 * mean_square))
    assert row.y_start_m == pytest.approx(0.85 * (-5 - 0.0005 * mean_square))
    assert row.z_m == -row.y_start_m
    assert row.goalward_x_m == -row.x_start_m
    assert row.y_start_m < 0


def test_absolute_y_retains_finite_out_of_pitch_starts():
    fragments = native_fragments()
    for frame in fragments[1]:
        frame["player_data"][1].update(x=56.0, y=-36.0)
    rows, _ = preflight.extract_match_support(source_from(fragments))
    focal = [r for r in rows if r.focal_player_id == 2]
    assert len(focal) == 4
    assert all(r.x_start_m == 56 and r.y_start_m == -36 and r.z_m == 36 for r in focal)


@pytest.mark.parametrize("case", ["cadence", "clock", "duplicate_frame", "duplicate_player", "pitch"])
def test_malformed_native_input_fails(case):
    fragments = native_fragments()
    if case == "cadence":
        del fragments[1][50]
    elif case == "clock":
        fragments[1][50]["timestamp"] = "0:5.1"
    elif case == "duplicate_frame":
        fragments[1].insert(50, copy.deepcopy(fragments[1][50]))
    elif case == "duplicate_player":
        fragments[1][50]["player_data"].append(copy.deepcopy(fragments[1][50]["player_data"][0]))
    else:
        fragments[0]["pitch_width"] = float("nan")
    with pytest.raises(preflight.SupportError):
        source_from(fragments)


@pytest.mark.parametrize("timestamp", ["nan:0", "inf:0", "-inf:0"], ids=["nan", "positive_infinity", "negative_infinity"])
def test_nonfinite_native_timestamp_fails_before_support_observations(timestamp):
    fragments = native_fragments()
    fragments[1][50]["timestamp"] = timestamp
    # Source construction fails before an extractor can accept any observation.
    with pytest.raises(preflight.SupportError, match="timestamp/cadence"):
        source_from(fragments)


def test_finite_clock_controls_preserve_valid_and_mismatch_behavior():
    valid = source_from(native_fragments())
    rows, _ = preflight.extract_match_support(valid)
    assert rows
    mismatch = native_fragments()
    mismatch[1][50]["timestamp"] = "0:5.1"
    with pytest.raises(preflight.SupportError, match="timestamp/cadence"):
        source_from(mismatch)


def test_eligibility_matches_inherited_support():
    source = source_from(native_fragments())
    rows, counts = preflight.extract_match_support(source)
    reference = inherited.support_match(source)
    assert len(rows) == reference["retained_rows"] == 36
    assert len({(r.period, r.anchor_provider_frame) for r in rows}) == reference["retained_anchors"] == 4
    assert counts["cadence_or_period"] == 2  # The period-origin first anchor lacks its raw left edge.
    assert counts["ball_nearest"] == 4
    assert all(r.focal_player_id != 1 for r in rows)


@pytest.mark.parametrize("reason", ["not_continuously_ball_in_play", "possession_at_anchor", "ball_support", "complete_player_support"])
def test_support_exclusions_preserve_inherited_first_failure(reason):
    source = source_from(native_fragments())
    if reason == "not_continuously_ball_in_play":
        source.phase_coverage.remove(80)
    elif reason == "possession_at_anchor":
        source.rows[80]["possession"]["group"] = None
    elif reason == "ball_support":
        source.rows[80]["ball_data"]["x"] = None
    else:
        source.rows[80]["player_data"].pop()
    assert source.anchor_support_reason(80) == reason
    rows, counts = preflight.extract_match_support(source)
    assert counts[reason] >= 1
    assert not any(r.anchor_provider_frame == 80 for r in rows)
    if reason == "complete_player_support":
        assert counts["roster_support"] >= 1


def test_identity_gate_can_remove_one_focal_perspective_without_removing_anchor():
    source = source_from(native_fragments())
    source.rows[60]["player_data"][1]["x"] += 10
    rows, exclusions_result = preflight.extract_match_support(source)
    at_anchor = [r for r in rows if r.anchor_provider_frame == 80]
    assert len(at_anchor) == 8
    assert 2 not in {r.focal_player_id for r in at_anchor}
    assert exclusions_result["identity_gate_row"] >= 1


def test_ranks_are_canonical_at_anchor_despite_later_crossing(monkeypatch):
    fragments = native_fragments(length=100, width=80)
    for frame in fragments[1]:
        frame["player_data"][1].update(x=0.0, y=0.0)
        frame["player_data"][10].update(x=1.0, y=0.0)
        frame["player_data"][11].update(x=0.0, y=1.1)
        if frame["frame"] > 80:
            frame["player_data"][11]["y"] += (frame["frame"] - 80) * 0.01
    source = source_from(fragments)
    recorded = []
    original = preflight.continuity_valid
    def spy(source, focal, ranks, anchor):
        if focal == 2 and anchor == 80:
            recorded.append(ranks)
        return original(source, focal, ranks, anchor)
    monkeypatch.setattr(preflight, "continuity_valid", spy)
    preflight.extract_match_support(source)
    # Native nearest is 11 (1m); canonical nearest is 12 (1.1 * .85 < 1 * 1.05).
    assert recorded[0][:2] == (12, 11)
    assert set(recorded[0]) == set(range(11, 21))


@pytest.mark.parametrize("entity", ["focal", "ball", "defender"])
def test_quality_uses_frozen_focal_ball_and_seven_defender_windows(entity):
    source = source_from(native_fragments())
    if entity == "defender":
        ranks = inherited.sorted_rank_ids(source, 80, 2, tuple(range(11, 21)), -1, 17)
        player = ranks[6]
        frames = list(range(79, 102))
    else:
        player = 2
        frames = list(range(39, 82))
    for frame in frames[:len(frames) // 2 + 1]:
        if entity == "ball":
            source.rows[frame]["ball_data"]["is_detected"] = False
        else:
            source.rows[frame]["player_data"][player - 1]["is_detected"] = False
    rows, _ = preflight.extract_match_support(source)
    row = next(r for r in rows if r.anchor_provider_frame == 80 and r.focal_player_id == 2)
    assert not row.quality_pass
    assert getattr(row, {"focal": "focal_detected_fraction", "ball": "ball_detected_fraction", "defender": "min_D1_D7_detected_fraction"}[entity]) == pytest.approx((len(frames) // 2) / len(frames))
    # Restore one edge-inclusive sample: the inherited >= .5 rule now passes.
    f = frames[len(frames) // 2]
    target = source.rows[f]["ball_data"] if entity == "ball" else source.rows[f]["player_data"][player - 1]
    target["is_detected"] = True
    rows, _ = preflight.extract_match_support(source)
    assert next(r for r in rows if r.anchor_provider_frame == 80 and r.focal_player_id == 2).quality_pass


@pytest.mark.parametrize("z, expected", [(0, "0_10"), (10, "10_20"), (20, "20_30"), (30, "30_34"), (34, "30_34"), (34.01, "over_34")])
def test_reporting_band_boundaries(z, expected):
    assert preflight.lateral_band(z) == expected


def test_period_blocks_and_simultaneous_time_counts(config):
    first = support_rows()[0]
    sample = [replace(first, period=1, block_id=3), replace(first, period=1, block_id=3, focal_player_id=4),
              replace(first, period=2, block_id=3)]
    tables = preflight.aggregate_support(sample, exclusions(), config)
    row = tables["sample_summary.csv"].query('sample == "primary"').iloc[0]
    assert row.observation_count == 3
    assert row.unique_time_anchor_count == 2
    assert row.temporal_block_count == 2
    assert row.period_count == 2


def test_full_rank_and_leverage_oracle(config):
    base = support_rows()[0]
    rows = [replace(base, anchor_provider_frame=i, z_m=float(z), y_start_m=float(z)) for i, z in enumerate((0, 1, 2))]
    table = preflight.aggregate_support(rows, exclusions(), config)["design_qc.csv"]
    row = table.query('sample == "primary" and scope == "match"').iloc[0]
    assert row["rank"] == 2 and row.full_rank
    assert row.mean_leverage == pytest.approx(2 / 3)
    assert row.max_leverage == pytest.approx(5 / 6)
    rows = [replace(r, z_m=1.0, y_start_m=1.0) for r in rows]
    table = preflight.aggregate_support(rows, exclusions(), config)["design_qc.csv"]
    row = table.query('sample == "primary" and scope == "match"').iloc[0]
    assert row["rank"] == 1 and not row.full_rank
    assert pd.isna(row.max_leverage)


def test_all_nine_support_gates_and_quality_coverage(config):
    rows = support_rows()
    cfg = synthetic_counts(config, rows)
    tables = preflight.aggregate_support(rows, exclusions(), cfg)
    qc = preflight.check_support_gates(tables, True, cfg)
    assert qc["status"] == preflight.STATUS_PASS and all(qc["checks"].values())
    assert qc["human_review_required"]
    assert preflight.check_support_gates(tables, False, cfg)["status"] == preflight.STATUS_FAIL
    # Counts cannot establish historic identity: a future digest is separate.
    assert cfg["population_reconciliation"]["count_agreement_proves_historical_id_equality"] is False


@pytest.mark.parametrize("failure", ["match", "period", "quality", "rank", "times", "blocks", "counts"])
def test_each_support_failure_blocks(config, failure):
    rows = support_rows()
    if failure == "match":
        rows = [r for r in rows if r.match_id != preflight.MATCHES[-1]]
    elif failure == "period":
        rows = [r for r in rows if not (r.match_id == preflight.MATCHES[0] and r.period == 2)]
    elif failure == "quality":
        rows = [replace(r, focal_detected_fraction=0.0, quality_pass=False) if r.match_id == preflight.MATCHES[0] else r for r in rows]
    elif failure == "rank":
        rows = [replace(r, z_m=4.0, y_start_m=-4.0) if r.match_id == preflight.MATCHES[0] else r for r in rows]
    elif failure == "times":
        times = sorted({(r.period, r.anchor_provider_frame) for r in rows if r.match_id == preflight.MATCHES[0] and r.z_m < 10})[:19]
        rows = [r for r in rows if r.match_id != preflight.MATCHES[0] or r.z_m >= 10 or (r.period, r.anchor_provider_frame) in times]
    elif failure == "blocks":
        rows = [replace(r, block_id=0) if r.match_id == preflight.MATCHES[0] and r.z_m < 10 and r.period == 2 else r for r in rows]
    cfg = synthetic_counts(config, rows)
    if failure == "counts":
        cfg["population_reconciliation"]["rows"][0][2] += 1
    tables = preflight.aggregate_support(rows, exclusions(), cfg)
    qc = preflight.check_support_gates(tables, True, cfg)
    assert qc["status"] == preflight.STATUS_FAIL
    key = {"match": "all_nine_matches", "period": "both_periods_primary_and_quality", "quality": "both_periods_primary_and_quality",
           "rank": "full_rank_primary_and_quality", "times": "quality_region_times", "blocks": "quality_region_blocks", "counts": "count_reconciliation"}[failure]
    assert not qc["checks"][key]


def test_twenty_unique_times_and_four_blocks_are_inclusive(config):
    rows = support_rows()
    times = sorted({(r.period, r.anchor_provider_frame) for r in rows if r.match_id == preflight.MATCHES[0] and r.z_m < 10})[:20]
    rows = [r for r in rows if r.match_id != preflight.MATCHES[0] or r.z_m >= 10 or (r.period, r.anchor_provider_frame) in times]
    cfg = synthetic_counts(config, rows)
    tables = preflight.aggregate_support(rows, exclusions(), cfg)
    row = tables["quality_region_support.csv"].iloc[0]
    assert row.unique_time_anchor_count == 20 and row.temporal_block_count == 4
    assert preflight.check_support_gates(tables, True, cfg)["status"] == preflight.STATUS_PASS


def test_missing_match_extraction_record_is_not_minimum_eight_fallback(config):
    ex = exclusions()
    del ex[preflight.MATCHES[-1]]
    with pytest.raises(preflight.SupportError, match="nine match"):
        preflight.aggregate_support(support_rows(), ex, config)


def test_identity_digest_is_order_invariant_and_membership_sensitive():
    rows = support_rows()
    expected = preflight.observation_digest(rows)
    assert expected == preflight.observation_digest(reversed(rows))
    changed = [replace(rows[0], focal_player_id=99), *rows[1:]]
    assert preflight.observation_digest(changed) != expected
    with pytest.raises(preflight.SupportError, match="duplicate observation"):
        preflight.observation_digest([*rows, rows[0]])
    first = rows[0]
    explicit = f"{first.match_id}:{first.period}:{first.anchor_provider_frame}:{first.focal_player_id}\n"
    assert preflight.observation_digest([first]) == hashlib.sha256(explicit.encode()).hexdigest()
    assert preflight.observation_digest([]) == hashlib.sha256(b"").hexdigest()


@pytest.mark.parametrize("field", ["Y", "response_2s_m", "defender_path", "prediction", "residual", "coefficient", "anchor_time", "player_id"])
def test_aggregate_schema_rejects_row_and_outcome_fields(config, field):
    tables = preflight.aggregate_support(support_rows(), exclusions(), config)
    tables["sample_summary.csv"][field] = 0
    with pytest.raises(preflight.SupportError, match="allowlist"):
        preflight.validate_public_outputs(tables, config)


def test_aggregate_grouping_rejects_wrong_granularity(config):
    tables = preflight.aggregate_support(support_rows(), exclusions(), config)
    tables["sample_summary.csv"] = pd.concat([tables["sample_summary.csv"], tables["sample_summary.csv"].iloc[:1]], ignore_index=True)
    with pytest.raises(preflight.SupportError, match="grouping"):
        preflight.validate_public_outputs(tables, config)


def test_internal_record_schema_forbids_outcome_and_digest_rejects_dict():
    names = {f.name for f in fields(preflight.SupportObservation)}
    assert names == {"match_id", "period", "anchor_provider_frame", "focal_player_id", "block_id", "x_start_m", "y_start_m", "z_m", "goalward_x_m",
                     "focal_detected_fraction", "ball_detected_fraction", "min_D1_D7_detected_fraction", "quality_pass"}
    with pytest.raises(preflight.SupportError, match="internal support schema"):
        preflight.observation_digest([{"Y": 0}])


def test_aggregate_determinism_with_unequal_sample_sizes_and_no_mutation(config):
    rows = support_rows()
    rows = [r for i, r in enumerate(rows) if r.match_id != preflight.MATCHES[-1] or i % 2]
    before = list(rows)
    first = preflight.aggregate_support(rows, exclusions(), config)
    second = preflight.aggregate_support(reversed(rows), exclusions(), config)
    assert rows == before
    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name], check_exact=True)


@pytest.fixture
def synthetic_git(tmp_path, monkeypatch):
    repo, local = tmp_path / "release", tmp_path / "local"
    repo.mkdir()
    local.mkdir()
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout.decode().strip()
    git("init", "-q")
    for match in preflight.MATCHES:
        for template in preflight.TEMPLATES:
            filename = template.format(match)
            # Identity-only synthetic bytes; no tracking-coordinate records.
            payload = ("synthetic identity fixture " + filename + "\n").encode()
            (repo / filename).write_bytes(payload)
            (local / filename).write_bytes(payload)
    git("add", ".")
    git("-c", "user.name=Synthetic Test", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic release")
    commit = git("rev-parse", "HEAD")
    monkeypatch.setattr(preflight, "RELEASE", commit)
    return repo, local


def test_real_synthetic_git_source_identity_and_mismatch(synthetic_git):
    repo, local = synthetic_git
    verified = preflight.verify_source_identity(local, repo)
    assert len(verified["files"]) == 27
    assert len({f["path"] for f in verified["files"]}) == 27
    first = verified["files"][0]
    assert first["lfs_oid_sha256"] is None
    assert first["materialized_sha256"] == hashlib.sha256((local / first["path"]).read_bytes()).hexdigest()
    assert first["identity_valid"] is True
    (local / first["path"]).write_text("changed synthetic bytes", encoding="utf-8")
    with pytest.raises(preflight.SupportError, match="blob mismatch"):
        preflight.verify_source_identity(local, repo)


def test_missing_source_and_unavailable_pinned_commit_fail(synthetic_git, monkeypatch):
    repo, local = synthetic_git
    (local / preflight.TEMPLATES[0].format(preflight.MATCHES[-1])).unlink()
    with pytest.raises(preflight.SupportError, match="missing"):
        preflight.verify_source_identity(local, repo)
    monkeypatch.setattr(preflight, "RELEASE", "f" * 40)
    with pytest.raises(preflight.SupportError, match="unavailable"):
        preflight.verify_source_identity(local, repo)


@pytest.fixture
def synthetic_lfs_git(tmp_path, monkeypatch):
    repo, local = tmp_path / "release", tmp_path / "local"
    repo.mkdir()
    local.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout.decode().strip()

    git("init", "-q")
    materialized = b"synthetic materialized LFS tracking payload\n"
    target = preflight.TEMPLATES[1].format(preflight.MATCHES[0])
    pointer = (b"version https://git-lfs.github.com/spec/v1\n"
               + b"oid sha256:" + hashlib.sha256(materialized).hexdigest().encode() + b"\n"
               + b"size " + str(len(materialized)).encode() + b"\n")
    for match in preflight.MATCHES:
        for template in preflight.TEMPLATES:
            filename = template.format(match)
            payload = pointer if filename == target else ("ordinary synthetic source " + filename + "\n").encode()
            (repo / filename).write_bytes(payload)
            (local / filename).write_bytes(materialized if filename == target else payload)
    git("add", ".")
    git("-c", "user.name=Synthetic Test", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic LFS release")
    monkeypatch.setattr(preflight, "RELEASE", git("rev-parse", "HEAD"))
    return repo, local, target, pointer, materialized


def test_lfs_materialized_source_identity_and_provenance(synthetic_lfs_git):
    repo, local, target, _pointer, materialized = synthetic_lfs_git
    verified = preflight.verify_source_identity(local, repo)
    lfs = next(item for item in verified["files"] if item["path"] == target)
    assert lfs["lfs_oid_sha256"] == hashlib.sha256(materialized).hexdigest()
    assert lfs["lfs_declared_size"] == len(materialized)
    assert lfs["materialized_sha256"] == hashlib.sha256(materialized).hexdigest()
    assert lfs["materialized_size"] == len(materialized)
    assert lfs["identity_valid"] is True
    ordinary = next(item for item in verified["files"] if item["path"] != target)
    assert ordinary["lfs_oid_sha256"] is None and ordinary["lfs_declared_size"] is None


@pytest.mark.parametrize("case", ["pointer", "sha", "size", "symlink", "missing"])
def test_lfs_source_identity_rejects_unresolved_or_invalid_payload(synthetic_lfs_git, case):
    repo, local, target, pointer, materialized = synthetic_lfs_git
    path = local / target
    if case == "pointer":
        path.write_bytes(pointer)
        message = "unresolved"
    elif case == "sha":
        path.write_bytes(b"x" * len(materialized))
        message = "SHA-256"
    elif case == "size":
        changed_pointer = (b"version https://git-lfs.github.com/spec/v1\n"
                           + b"oid sha256:" + hashlib.sha256(materialized).hexdigest().encode() + b"\n"
                           + b"size " + str(len(materialized) + 1).encode() + b"\n")
        (repo / target).write_bytes(changed_pointer)
        subprocess.run(["git", "-C", str(repo), "add", target], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Synthetic Test", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "wrong LFS size"], check=True)
        preflight.RELEASE = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        message = "size"
    elif case == "symlink":
        path.unlink()
        path.symlink_to(local / preflight.TEMPLATES[0].format(preflight.MATCHES[0]))
        message = "symlinked"
    else:
        path.unlink()
        message = "missing"
    with pytest.raises(preflight.SupportError, match=message):
        preflight.verify_source_identity(local, repo)


@pytest.mark.parametrize("pointer", [
    b"version https://git-lfs.github.com/spec/v2\noid sha256:" + b"0" * 64 + b"\nsize 1\n",
    b"version https://git-lfs.github.com/spec/v1\noid sha1:" + b"0" * 40 + b"\nsize 1\n",
    b"version https://git-lfs.github.com/spec/v1\noid sha256:not-a-hash\nsize 1\n",
    b"version https://git-lfs.github.com/spec/v1\nsize 1\n",
    b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"0" * 64 + b"\nsize -1\n",
])
def test_lfs_pointer_parser_rejects_malformed_metadata(pointer):
    with pytest.raises(preflight.SupportError, match="malformed"):
        preflight._parse_lfs_pointer(pointer)


def test_source_has_no_dangerous_calls_or_imports():
    tree = ast.parse(inspect.getsource(preflight))
    dangerous = {"construct_row", "construct_match", "path_length", "fit", "fit_equal_match_ols", "bootstrap", "execute"}
    called = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))}
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert not dangerous & called
    assert not dangerous & imported


def test_full_synthetic_execution_never_calls_outcome_and_reproduces(config, synthetic_git, tmp_path, monkeypatch):
    repo, local = synthetic_git
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden scientific call")
    for name in ("construct_row", "construct_match", "path_length", "fit", "primary_fit_table", "trim_fit", "block_statistics", "bootstrap", "execute"):
        monkeypatch.setattr(inherited, name, forbidden)
    monkeypatch.setattr(design, "fit_equal_match_ols", forbidden)
    real_class = preflight.SupportSource
    # Exercise the production extractor and writer, using synthetic native
    # objects only. No historic outcome functions supply expected values.
    source_rows = []
    def make_source(match, _data_dir):
        return real_class.from_records(match, *native_fragments(match, end=742))
    for match in preflight.MATCHES:
        source_rows.extend(preflight.extract_match_support(make_source(match, None))[0])
    cfg = synthetic_counts(config, source_rows)
    _, real_hashes = preflight.verify_freeze()
    monkeypatch.setattr(preflight, "verify_freeze", lambda: (cfg, real_hashes))
    monkeypatch.setattr(preflight, "SupportSource", make_source)
    outputs = []
    for index in range(2):
        output, report = tmp_path / f"aggregate{index}", tmp_path / f"report{index}.md"
        result = preflight.execute_support(execute=True, data_dir=local, pinned_repository=repo,
            authorization_reference="synthetic-only-test", expected_implementation_hashes={p: real_hashes[p] for p in (preflight.SOURCE, preflight.TESTS)},
            output=output, report=report)
        assert result["status"] == preflight.STATUS_PASS
        assert result["human_review_required"]
        assert set(p.name for p in output.iterdir()) == set(config["publication"]["csv_columns"]) | set(config["publication"]["json_artifacts"])
        ledger = json.loads((output / "final_hashes.json").read_text())
        for name, expected in ledger["artifacts"].items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
        assert hashlib.sha256(report.read_bytes()).hexdigest() == ledger["report_sha256"]
        outputs.append((output, report))
    for path in outputs[0][0].iterdir():
        assert path.read_bytes() == (outputs[1][0] / path.name).read_bytes()
    assert outputs[0][1].read_bytes() == outputs[1][1].read_bytes()
    # Nested JSON metadata cannot smuggle a row table into the public package.
    package = {name: json.loads((outputs[0][0] / name).read_text())
               for name in ("source_hashes.json", "manifest.json", "hard_qc.json")}
    package["manifest.json"]["observation_digests"]["primary"]["individual_rows"] = []
    with pytest.raises(preflight.SupportError, match="JSON schema"):
        preflight._validate_json_package(package["source_hashes.json"], package["manifest.json"], package["hard_qc.json"], real_hashes, cfg)
    del package["manifest.json"]["observation_digests"]["primary"]["individual_rows"]
    package["manifest.json"]["outputs"].append("unapproved.csv")
    with pytest.raises(preflight.SupportError, match="output manifest"):
        preflight._validate_json_package(package["source_hashes.json"], package["manifest.json"], package["hard_qc.json"], real_hashes, cfg)
    # No overwrite of a completed package, even in synthetic mode.
    with pytest.raises(preflight.SupportError, match="overwrite"):
        preflight.execute_support(execute=True, data_dir=local, pinned_repository=repo,
            authorization_reference="synthetic-only-test", expected_implementation_hashes={p: real_hashes[p] for p in (preflight.SOURCE, preflight.TESTS)},
            output=outputs[0][0], report=outputs[0][1])
