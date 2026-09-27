from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from event_review_dashboard import (
    DashboardRequest,
    build_review_view_model,
    create_server,
    render_dashboard_html,
    run_review,
    request_from_query,
    safe_artifact_path,
)


def test_run_review_passes_bounded_query_to_existing_runner(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_analyze(game, destination, **kwargs):
        captured.update(game=game, destination=destination, **kwargs)
        return {"status": "ok"}

    monkeypatch.setattr("event_review_dashboard.analyze_metrica_sample_match", fake_analyze)
    request = DashboardRequest(
        game=2, defending_side="Away", event_choice="goals", pre_seconds=3,
        post_seconds=2, rank_by="post_minus_pre_change", limit=4,
    )
    destination = run_review(
        request, output_root=tmp_path / "outputs", data_root=tmp_path / "data"
    )
    assert destination == tmp_path / "outputs" / request.slug
    assert captured["game"] == 2
    assert captured["data_dir"] == tmp_path / "data" / "metrica_sample_game_2"
    assert captured["event_types"] == ("GOAL",)
    assert captured["event_pre_seconds"] == 3
    assert captured["event_post_seconds"] == 2
    assert captured["event_rank_by"] == "post_minus_pre_change"
    assert captured["event_defending_team"] == "metrica:Away"
    assert captured["discovery_audit"] is False


def _package(tmp_path: Path, *, rows: list[dict[str, object]] | None = None) -> Path:
    package = tmp_path / "package"
    media = package / "media"
    media.mkdir(parents=True)
    for name in ("card.png", "replay.gif", "analyst.png", "technical.png"):
        (media / name).write_bytes(b"fixture")
    row = {
        "event_id": "m-shot-01", "match_id": "m", "period": 1,
        "peak_time_s": 10.0, "event_time_s": 10.0, "event_type": "SHOT",
        "event_detail": "ON TARGET-SAVED", "event_x_m": -31.0, "event_y_m": 2.0,
        "attacking_team_key": "metrica:Away", "team_key": "metrica:Home",
        "time_to_peak_s": .68, "previous_event": "Away PASS",
        "previous_event_offset_s": -1.2, "score_state": "Home 1–0 Away",
        "attacking_direction": "toward physical left", "match_clock": "00:10",
        "rank_by": "maximum_score", "rank_value": 3.2, "rank": 1,
    }
    summary = {
        "rendered_event_windows": [{
            "period": 1, "peak_time_s": 10.0, "defending_team_key": "metrica:Home",
            "coach_review_card_png": str(media / "card.png"),
            "gif": str(media / "replay.gif"),
            "analyst_diagnostic_png": str(media / "analyst.png"),
            "technical_appendix_png": str(media / "technical.png"),
        }]
    }
    (package / "application_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (package / "ranked_event_windows.json").write_text(
        json.dumps([row] if rows is None else rows), encoding="utf-8"
    )
    return package


def test_dashboard_request_is_bounded_and_deterministic():
    request = request_from_query({
        "game": ["2"], "defending_side": ["Away"], "event_choice": ["goals"],
        "pre_seconds": ["3"], "post_seconds": ["2"],
        "rank_by": ["post_minus_pre_change"], "limit": ["4"],
    })
    assert request == DashboardRequest(
        game=2, defending_side="Away", event_choice="goals", pre_seconds=3,
        post_seconds=2, rank_by="post_minus_pre_change", limit=4,
    )
    assert request.defending_team_key == "metrica:Away"
    assert "game2_away_goal_3-2" in request.slug
    with pytest.raises(ValueError, match="2, 3, or 5"):
        DashboardRequest(pre_seconds=4)
    with pytest.raises(ValueError, match="between 1 and 10"):
        DashboardRequest(limit=11)


def test_view_model_uses_plain_context_and_separates_appendix(tmp_path: Path):
    package = _package(tmp_path)
    view = build_review_view_model(package)
    assert view["status"] == "ready"
    row = view["rows"][0]
    assert row["outcome_text"] == "saved"
    assert row["location_text"] == "physical left third · central band"
    assert row["peak_text"] == "Peak within-unit movement occurred 0.68 s after the shot."
    assert row["ranking_text"] == "3.20 m"
    assert view["selected"]["artifacts"]["gif"].endswith("replay.gif")
    html = render_dashboard_html(DashboardRequest(), view)
    assert "Events organize review" in html
    assert "Football review card" in html
    assert "Analyst appendix: trace and technical detail" in html
    assert html.index("Football review card") < html.index("Analyst appendix")
    assert "class=\"discovery\"" not in html


def test_no_result_and_discovery_are_explicit(tmp_path: Path):
    package = _package(tmp_path, rows=[])
    view = build_review_view_model(package)
    assert view["status"] == "no_result"
    assert "No threshold was relaxed" in view["message"]
    html = render_dashboard_html(DashboardRequest(mode="discovery"), view)
    assert "Discovery / Audit is deliberately separate" in html
    assert "not tactical categories" in html
    assert "No supported, visually suitable event window" in html


def test_missing_package_is_an_actionable_not_run_state(tmp_path: Path):
    view = build_review_view_model(tmp_path / "missing")
    assert view["status"] == "not_run"
    assert "Choose Run review" in view["message"]


def test_artifacts_are_confined_to_output_root(tmp_path: Path):
    root = tmp_path / "outputs"
    artifact = root / "package" / "card.png"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"png")
    assert safe_artifact_path(root, str(artifact)) == artifact.resolve()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"no")
    with pytest.raises(ValueError, match="outside"):
        safe_artifact_path(root, str(outside))


def test_server_import_and_startup_smoke(tmp_path: Path):
    captured = {}

    class FakeServer:
        server_port = 8765

        def __init__(self, address, handler):
            captured["address"] = address
            captured["handler"] = handler

    server = create_server(
        host="127.0.0.1", port=8765, output_root=tmp_path / "runtime",
        server_factory=FakeServer,
    )
    assert server.server_port == 8765
    assert captured["address"] == ("127.0.0.1", 8765)
    assert captured["handler"].__name__ == "Handler"
