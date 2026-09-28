from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from event_review_dashboard import (
    DashboardRequest,
    CACHE_MANIFEST,
    _add_context_to_supported_candidates,
    _manifest_identity,
    build_review_view_model,
    create_server,
    current_query_package,
    expected_cache_manifest,
    export_review_pack,
    load_open_play_possession_changes,
    match_cache_path,
    package_ready,
    package_status,
    prepared_match_ready,
    render_dashboard_html,
    run_review,
    request_from_query,
    safe_artifact_path,
    start_prepare_job,
    start_render_job,
)


def test_run_review_prepares_match_once_then_reuses_query_cache(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_prepare(game, *, output_root, data_root):
        captured.setdefault("prepare", []).append((game, output_root, data_root))
        package = output_root / "prepared_matches" / f"metrica_sample_game_{game}"
        package.mkdir(parents=True, exist_ok=True)
        (package / CACHE_MANIFEST).write_text(json.dumps({"game": game}))
        return package

    def fake_query(request, match_package, destination):
        captured.setdefault("query", []).append((request, match_package, destination))
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "application_summary.json").write_text(
            json.dumps({
                "status": "CACHED_EVENT_REVIEW_QUERY_COMPLETE",
                "match_cache_identity": _manifest_identity({"game": request.game}),
            })
        )
        (destination / "ranked_event_windows.json").write_text("[]")
        return destination

    monkeypatch.setattr("event_review_dashboard._prepare_match_cache", fake_prepare)
    monkeypatch.setattr("event_review_dashboard._query_prepared_match", fake_query)
    request = DashboardRequest(
        game=2, defending_side="Away", event_choice="goals", pre_seconds=3,
        post_seconds=2, rank_by="post_minus_pre_change", limit=4,
    )
    destination = run_review(
        request, output_root=tmp_path / "outputs", data_root=tmp_path / "data"
    )
    assert destination == tmp_path / "outputs" / request.slug
    assert captured["prepare"] == [
        (2, tmp_path / "outputs", tmp_path / "data")
    ]
    assert captured["query"][0][0] == request
    assert captured["query"][0][1].name == "metrica_sample_game_2"

    run_review(request, output_root=tmp_path / "outputs", data_root=tmp_path / "data")
    assert len(captured["prepare"]) == 2
    assert len(captured["query"]) == 1


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


def test_possession_changes_use_recorded_possession_events_not_challenges(tmp_path: Path):
    events = pd.DataFrame([
        {"Team": "Home", "Type": "PASS", "Subtype": "", "Period": 1,
         "Start Frame": 100, "Start Time [s]": 4.0, "Start X": .4, "Start Y": .5},
        {"Team": "Away", "Type": "CHALLENGE", "Subtype": "TACKLE-WON", "Period": 1,
         "Start Frame": 110, "Start Time [s]": 4.4, "Start X": .5, "Start Y": .5},
        {"Team": "Away", "Type": "BALL LOST", "Subtype": "", "Period": 1,
         "Start Frame": 115, "Start Time [s]": 4.6, "Start X": .5, "Start Y": .5},
        {"Team": "Away", "Type": "RECOVERY", "Subtype": "INTERCEPTION", "Period": 1,
         "Start Frame": 120, "Start Time [s]": 4.8, "Start X": .6, "Start Y": .25},
        {"Team": "Home", "Type": "SET PIECE", "Subtype": "THROW IN", "Period": 1,
         "Start Frame": 200, "Start Time [s]": 8.0, "Start X": .2, "Start Y": .9},
        {"Team": "Home", "Type": "PASS", "Subtype": "", "Period": 1,
         "Start Frame": 205, "Start Time [s]": 8.2, "Start X": .2, "Start Y": .8},
        {"Team": "Away", "Type": "PASS", "Subtype": "", "Period": 2,
         "Start Frame": 300, "Start Time [s]": 12.0, "Start X": .8, "Start Y": .5},
        {"Team": "Home", "Type": "SHOT", "Subtype": "OFF TARGET", "Period": 2,
         "Start Frame": 325, "Start Time [s]": 13.0, "Start X": .9, "Start Y": .6},
    ])
    path = tmp_path / "events.csv"
    events.to_csv(path, index=False)
    changes = load_open_play_possession_changes(path, match_id="game")
    assert changes[["period", "event_time_s", "team_key", "possession_event_type"]].to_dict("records") == [
        {"period": 1, "event_time_s": 4.8, "team_key": "metrica:Away", "possession_event_type": "RECOVERY"},
        {"period": 2, "event_time_s": 13.0, "team_key": "metrica:Home", "possession_event_type": "SHOT"},
    ]
    assert changes["event_type"].eq("POSSESSION_CHANGE").all()
    assert changes["event_id"].is_unique


def test_possession_change_filter_and_plain_language_are_exposed(tmp_path: Path):
    request = DashboardRequest(event_choice="possession_changes")
    assert request.slug.startswith("game1_both_possession_change")
    package = _package(tmp_path, rows=[{
        "event_id": "m-change-01", "match_id": "m", "period": 1,
        "peak_time_s": 10.0, "event_time_s": 10.0,
        "event_type": "POSSESSION_CHANGE", "event_detail": "POSSESSION WON",
        "event_x_m": 0.0, "event_y_m": 0.0,
        "attacking_team_key": "metrica:Away", "team_key": "metrica:Home",
        "time_to_peak_s": .4, "rank_by": "maximum_score", "rank_value": 2.0,
        "rank": 1,
    }])
    view = build_review_view_model(package)
    assert view["rows"][0]["outcome_text"] == "Possession lost"
    assert "possession change" in view["rows"][0]["peak_text"].lower()
    html = render_dashboard_html(request, view)
    assert "Possession changes" in html
    assert "Turnover" not in html


def test_view_model_uses_plain_context_and_separates_appendix(tmp_path: Path):
    package = _package(tmp_path)
    view = build_review_view_model(package)
    assert view["status"] == "ready"
    row = view["rows"][0]
    assert row["outcome_text"] == "saved"
    assert row["location_text"] == "physical left third · central band"
    assert row["peak_text"] == "Defenders moved most within the unit 0.68 s after the shot."
    assert row["ranking_text"] == "3.20 m"
    assert view["selected"]["artifacts"]["gif"].endswith("replay.gif")
    html = render_dashboard_html(DashboardRequest(), view)
    assert "Events organize review" in html
    assert "Football review card" in html
    assert "Analyst appendix: trace and technical detail" in html
    assert html.index("Football review card") < html.index("Analyst appendix")
    assert "class=\"discovery\"" not in html
    assert "Prepare match review" in html
    assert "Most movement (m)" in html
    assert "Export" not in html


def test_portable_review_pack_contains_selected_media_and_boundary(tmp_path: Path):
    package = _package(tmp_path)
    archive = export_review_pack(package, (1,), tmp_path / "exports" / "review_pack")
    assert archive.is_file()
    index = (archive.with_suffix("") / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((archive.with_suffix("") / "manifest.json").read_text())
    assert "Selected passages for a focused football conversation" in index
    assert "does not identify tactics" in index
    assert "media/01_replay.gif" in index
    assert manifest["selected_passages"][0]["rank"] == 1
    assert manifest["status"] == "LOCAL_ANALYST_REVIEW_PACK"


def test_package_ready_requires_both_index_files(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    assert not package_ready(package)
    (package / "application_summary.json").write_text("{}")
    assert not package_ready(package)
    (package / "ranked_event_windows.json").write_text("[]")
    assert package_ready(package)

    (package / "dashboard_status.json").write_text(
        json.dumps({"state": "rendering", "message": "Rendering one replay…"})
    )
    assert package_status(package)["state"] == "rendering"


def test_no_result_is_explicit_and_dashboard_has_no_audit_mode(tmp_path: Path):
    package = _package(tmp_path, rows=[])
    view = build_review_view_model(package)
    assert view["status"] == "no_result"
    assert "No threshold was relaxed" in view["message"]
    html = render_dashboard_html(DashboardRequest(), view)
    assert "Discovery / Audit" not in html
    assert "name=\"mode\"" not in html
    assert "No complete, viewable passage" in html


def test_missing_package_is_an_actionable_not_run_state(tmp_path: Path):
    view = build_review_view_model(tmp_path / "missing")
    assert view["status"] == "not_run"
    assert "Choose Prepare match review" in view["message"]


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


def _prepared_match_fixture(root: Path, manifest: dict[str, object]) -> Path:
    package = root / "prepared_matches" / "metrica_sample_game_1"
    package.mkdir(parents=True)
    for name in ("event_catalog.json", "application_summary.json"):
        (package / name).write_text("[]" if name.startswith("event") else "{}")
    (package / CACHE_MANIFEST).write_text(json.dumps(manifest))
    for team in ("metrica_Home", "metrica_Away"):
        directory = package / team
        directory.mkdir()
        for name in ("player_scores.parquet", "team_scores.parquet", "score_metadata.json"):
            (directory / name).write_bytes(b"{}")
    return package


def test_prepared_match_requires_exact_provenance_manifest(tmp_path: Path):
    manifest = {"schema_version": 1, "game": 1, "sources": {"home": "abc"}}
    package = _prepared_match_fixture(tmp_path, manifest)
    assert prepared_match_ready(package, manifest)
    changed = {**manifest, "sources": {"home": "different"}}
    assert not prepared_match_ready(package, changed)
    (package / CACHE_MANIFEST).write_text("not-json")
    assert not prepared_match_ready(package, manifest)


def test_query_package_is_bound_to_prepared_match_identity(tmp_path: Path):
    package = tmp_path / "query"
    package.mkdir()
    (package / "ranked_event_windows.json").write_text("[]")
    (package / "application_summary.json").write_text(json.dumps({
        "status": "CACHED_EVENT_REVIEW_QUERY_COMPLETE",
        "match_cache_identity": "cache-a",
    }))
    assert current_query_package(package, "cache-a")
    assert not current_query_package(package, "cache-b")


def test_same_game_preparation_jobs_are_serialized_across_queries(
    tmp_path: Path, monkeypatch
):
    entered = threading.Event()
    release = threading.Event()

    def blocking_review(*args, **kwargs):
        entered.set()
        assert release.wait(2)

    monkeypatch.setattr("event_review_dashboard.run_review", blocking_review)
    first = DashboardRequest(game=1, defending_side="Home")
    second = DashboardRequest(game=1, defending_side="Away")
    assert start_prepare_job(first, output_root=tmp_path, data_root=None)
    assert entered.wait(1)
    active = package_status(tmp_path / first.slug)
    assert active["state"] == "preparing"
    assert "first preparation can take a few minutes" in active["detail"].lower()
    assert not start_prepare_job(second, output_root=tmp_path, data_root=None)
    waiting = package_status(tmp_path / second.slug)
    assert waiting["state"] == "preparing"
    assert "already being prepared" in waiting["message"]
    assert "No duplicate job was started" in waiting["detail"]
    release.set()


def test_preparing_page_has_visible_progress_and_disables_repeat_submission():
    view = {
        "status": "preparing",
        "message": "Preparing the match and building the review queue…",
        "status_detail": "The first preparation can take a few minutes.",
        "rows": [],
        "selected": None,
    }
    html = render_dashboard_html(DashboardRequest(), view)
    assert 'class="progress-panel"' in html
    assert 'role="status"' in html
    assert "The first preparation can take a few minutes" in html
    assert '<button id="prepare-button" type="submit" disabled>Preparing…</button>' in html
    assert "repeated clicks are disabled" in html.lower()
    assert 'content="2"' in html


def test_render_jobs_are_serialized_per_query_package(tmp_path: Path, monkeypatch):
    entered = threading.Event()
    release = threading.Event()

    def blocking_render(*args, **kwargs):
        entered.set()
        assert release.wait(2)

    monkeypatch.setattr("event_review_dashboard.render_cached_passage", blocking_render)
    request = DashboardRequest()
    assert start_render_job(request, 1, output_root=tmp_path, data_root=None)
    assert entered.wait(1)
    assert not start_render_job(request, 2, output_root=tmp_path, data_root=None)
    release.set()


def test_request_parser_ignores_retired_dashboard_mode():
    request = request_from_query({"mode": ["discovery"], "game": ["2"]})
    assert request == DashboardRequest(game=2)
    assert "mode=" not in request.slug


def test_context_is_added_only_after_support_filter(tmp_path: Path, monkeypatch):
    candidates = pd.DataFrame({
        "event_id": ["supported", "unsupported"],
        "event_time_s": [10.0, 20.0],
        "event_type": ["SHOT", "SHOT"],
        "team_key": ["metrica:Away", "metrica:Away"],
    })
    seen: list[str] = []

    def fake_query(events, scores, query):
        return SimpleNamespace(windows=events.loc[events["event_id"].eq("supported")].copy())

    def fake_context(events, *args, **kwargs):
        seen.extend(events["event_id"].tolist())
        result = events.copy()
        result["score_state"] = "0–0"
        return result

    monkeypatch.setattr("event_review_dashboard.query_event_windows", fake_query)
    monkeypatch.setattr("event_review_dashboard.add_analyst_context", fake_context)
    result = _add_context_to_supported_candidates(
        candidates,
        object(),
        defending="metrica:Home",
        attacking="metrica:Away",
        tracking={},
        ball=pd.DataFrame(),
        raw_events=pd.DataFrame(),
    )
    assert seen == ["supported"]
    assert result["event_id"].tolist() == ["supported", "unsupported"]
    assert result.loc[result["event_id"].eq("supported"), "score_state"].iloc[0] == "0–0"
    assert pd.isna(
        result.loc[result["event_id"].eq("unsupported"), "score_state"].iloc[0]
    )


def test_unrendered_passage_cannot_be_kept(tmp_path: Path):
    package = _package(tmp_path)
    summary_path = package / "application_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["rendered_event_windows"] = []
    summary_path.write_text(json.dumps(summary))
    view = build_review_view_model(package)
    html = render_dashboard_html(DashboardRequest(), view)
    assert "Render first" in html
    assert ">Keep<" not in html
    assert "Render this replay" in html


def test_failed_render_requires_explicit_retry(tmp_path: Path):
    package = _package(tmp_path)
    summary_path = package / "application_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["rendered_event_windows"] = []
    summary_path.write_text(json.dumps(summary))
    view = {
        **build_review_view_model(package),
        "status": "error",
        "message": "Replay render failed",
    }
    html = render_dashboard_html(DashboardRequest(), view)
    assert "Retry replay" in html
    assert "retry_render=1" in html
    assert "&render=1" not in html


def test_background_worker_can_render_matplotlib_figure(tmp_path: Path, monkeypatch):
    import matplotlib
    import matplotlib.pyplot as plt

    completed = threading.Event()
    image = tmp_path / "worker.png"

    def render_figure(*args, **kwargs):
        figure, axis = plt.subplots()
        axis.plot([0, 1], [0, 1])
        figure.savefig(image)
        plt.close(figure)
        completed.set()
        return image

    monkeypatch.setattr("event_review_dashboard.render_cached_passage", render_figure)
    request = DashboardRequest(game=2)
    assert matplotlib.get_backend().lower() == "agg"
    assert start_render_job(request, 1, output_root=tmp_path, data_root=None)
    assert completed.wait(5)
    assert image.is_file()
