"""Synthetic publication tests: no tracking, scores, or rendering required."""
import copy
import csv
import json
import re
from pathlib import Path

import pytest

from src import export_match_reorganization_demo_site as site


def contract():
    return json.loads(re.search(r"```json\n(.*?)\n```", site.PROTOCOL.read_text(), re.S)[1])


def refresh(root, frozen):
    manifest = {"status": "SELECTED_WINDOW_MEDIA_COMPLETE", "files_sha256": {
        name: site.sha256(root / name) for name in frozen["input_files"] if name != "manifest.json"
    }}
    (root / "manifest.json").write_text(json.dumps(manifest))
    frozen["source_manifest_sha256"] = site.sha256(root / "manifest.json")


@pytest.fixture
def package(tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()
    frozen = copy.deepcopy(contract())
    for name in frozen["input_files"]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic validation-only payload")
    for role in ("representative", "diagnostic", "rejected"):
        rows = []
        for e in frozen["examples"]:
            if e["role"] != role:
                continue
            rejected = role == "rejected"
            stem = f"{role}_examples/home_p{e['period']}_{e['timestamp_s']:.2f}"
            rows.append(dict(period=e["period"], peak_time_s=e["timestamp_s"],
                team_key="metrica:Home", match_id="metrica_sample_game_2",
                static_path=stem+".png", gif_path=stem+".gif",
                trajectory_integrity_status="trajectory_integrity_failed" if rejected else "trajectory_integrity_clean",
                trajectory_integrity_reason="impossible_native_speed" if rejected else "",
                media_status="integrity_failed" if rejected else "supported",
                ball_alignment_support_status="integrity_failed" if rejected else "supported",
                rapid_context="open_play", possession_state="out_of_possession",
                ballward_stratum=e["stratum"], linkage_category=e["linkage"],
                attacker_link_status="not_evaluated" if rejected or e["linkage"]=="not_evaluated" else "supported",
                strong_link_count=e["link_count"] if isinstance(e["link_count"], int) else "",
                top_three_player_raw_paths_m="[3, 2, 1]", team_ballward_projection_share="0.3",
                one_second_change_m="0.8", team_score_m="2.1",
                player_key="NEVER_PUBLISH", coordinates="NEVER_PUBLISH"))
        with (root / f"{role}_examples.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for asset in frozen["assets"]:
        asset["sha256"] = site.sha256(root / asset["source"])
    refresh(root, frozen)
    monkeypatch.setattr(site, "load_contract", lambda: frozen)
    monkeypatch.setattr(site, "committed_identity", lambda path: {"commit": "a"*40, "sha256": "b"*64})
    return root, frozen


def test_frozen_contract():
    c = contract()
    assert len(c["input_files"]) == 20
    assert len(c["assets"]) == 8
    assert set(c["public_fields"]) == site.PUBLIC_FIELDS
    assert [(e["timestamp_s"], e["role"]) for e in c["examples"] if e["public"]] == [
        (5355.64, "representative"), (336.76, "representative"),
        (4443.16, "diagnostic"), (1734.72, "rejected")]
    assert not next(e for e in c["examples"] if e["timestamp_s"] == 978.32)["public"]


def test_double_export_projection_and_media(package, tmp_path):
    root, c = package
    a, b = tmp_path / "a", tmp_path / "b"
    manifest = site.export_site(root, a)
    site.export_site(root, b)
    assert len([p for p in a.rglob("*") if p.is_file()]) == 11
    for path in a.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (b / path.relative_to(a)).read_bytes()
    assert "manifest.json" not in manifest["files_sha256"]
    assert len(manifest["files_sha256"]) == 10
    assert all(set(e) == site.PUBLIC_FIELDS for e in manifest["examples"])
    assert manifest["examples"][1]["total_strong_link_count"] == "not_evaluated"
    assert manifest["examples"][-1]["ballward_share"] == "integrity_failed"
    assert manifest["examples"][2]["total_strong_link_count"] == 12
    text = (a / "index.html").read_text() + (a / "manifest.json").read_text()
    assert all(token not in text for token in ("NEVER_PUBLISH", "978.32", "player_key", "coordinates"))
    assert '<details id="diagnostic"' in text and '<details id="qc"' in text
    assert " open>" not in text
    assert 'media="(prefers-reduced-motion: reduce)"' in text
    assert "Goalkeeper-distribution special context" in text
    for asset in c["assets"]:
        assert (root / asset["source"]).read_bytes() == (a / asset["destination"]).read_bytes()


@pytest.mark.parametrize("name", ["/tmp/a", "../a", "a/../b", "a\\b", "https://evil", "a//b", "./a", ""])
def test_unsafe_paths(name):
    with pytest.raises(ValueError):
        site.relative_name(name)


@pytest.mark.parametrize("mutation", ["extra", "extra_dir", "missing", "tamper", "symlink", "manifest"])
def test_inventory_fail_closed(package, tmp_path, mutation):
    root, c = package
    path = root / c["assets"][0]["source"]
    if mutation == "extra": (root / "extra.csv").write_text("x")
    elif mutation == "extra_dir": (root / "extra").mkdir()
    elif mutation == "missing": path.unlink()
    elif mutation == "tamper": path.write_bytes(b"changed")
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to(root / "summary.json")
    else: (root / "manifest.json").write_text("{}")
    dest = tmp_path / "output"
    with pytest.raises((ValueError, FileNotFoundError)):
        site.export_site(root, dest)
    assert not dest.exists()


@pytest.mark.parametrize("field,value", [
    ("static_path", "/private/a.png"), ("gif_path", "../bad.gif"),
    ("peak_time_s", "1"), ("team_key", "metrica:Away"),
    ("trajectory_integrity_status", "trajectory_integrity_failed"),
    ("ball_alignment_support_status", "unsupported"),
    ("team_score_m", "NaN"), ("one_second_change_m", "inf"),
    ("strong_link_count", "3"), ("attacker_link_status", "not_evaluated"),
])
def test_records_fail_closed_even_with_valid_hashes(package, tmp_path, field, value):
    root, c = package
    path = root / "representative_examples.csv"
    with path.open() as handle: rows = list(csv.DictReader(handle))
    rows[0][field] = value
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    refresh(root, c)
    with pytest.raises(ValueError): site.export_site(root, tmp_path / "output")


def test_existing_destination_and_staging_failure(package, tmp_path, monkeypatch):
    root, _ = package
    dest = tmp_path / "output"
    dest.mkdir()
    with pytest.raises(FileExistsError): site.export_site(root, dest)
    dest.rmdir()
    def reject(*args): raise ValueError("staged validation failure")
    monkeypatch.setattr(site, "validate_site", reject)
    with pytest.raises(ValueError): site.export_site(root, dest)
    assert not dest.exists()
    assert not list(tmp_path.glob(".p1-demo-export-*"))


def test_finished_package_tamper_rejected(package, tmp_path):
    root, c = package
    dest = tmp_path / "output"
    m = site.export_site(root, dest)
    (dest / "index.html").write_text("<script>alert(1)</script>")
    with pytest.raises(ValueError): site.validate_site(dest, c, m["examples"], m["exporter"])


def test_runtime_links_rejected():
    with pytest.raises(ValueError): site.PageLinks().feed('<img onload="bad()">')
    with pytest.raises(ValueError): site.PageLinks().feed('<script src="evil"></script>')
