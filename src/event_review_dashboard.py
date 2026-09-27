"""Small local browser dashboard for event-first football review.

The dashboard is a presentation layer over the committed event-window API. It
does not define scores, select new scientific outcomes, or classify tactics.
Runtime packages stay outside the repository by default.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import parse_qs, quote, urlparse

import numpy as np

from run_metrica_game2_application import (
    ANALYST_CLIP_CONTEXT_SECONDS,
    analyze_metrica_sample_match,
    normalize_event_outcome,
    physical_event_location,
    time_to_peak_text,
)


RANK_CHOICES = {
    "maximum_score": "Highest movement in the event window",
    "anchor_score": "Movement at the event",
    "post_minus_pre_change": "Largest increase after the event",
    "time_to_peak": "Earliest movement peak",
}
EVENT_CHOICES = {
    "shots_goals": ("SHOT", "GOAL"),
    "shots": ("SHOT",),
    "goals": ("GOAL",),
}
WINDOW_CHOICES = (2.0, 3.0, 5.0)


@dataclass(frozen=True)
class DashboardRequest:
    game: int = 1
    defending_side: str = "both"
    event_choice: str = "shots_goals"
    pre_seconds: float = 5.0
    post_seconds: float = 5.0
    rank_by: str = "maximum_score"
    limit: int = 3
    mode: str = "review"

    def __post_init__(self) -> None:
        if self.game not in {1, 2}:
            raise ValueError("game must be Metrica Sample Game 1 or 2")
        if self.defending_side not in {"both", "Home", "Away"}:
            raise ValueError("defending side must be Home, Away, or both")
        if self.event_choice not in EVENT_CHOICES:
            raise ValueError("unsupported event choice")
        if self.pre_seconds not in WINDOW_CHOICES or self.post_seconds not in WINDOW_CHOICES:
            raise ValueError("review windows must be 2, 3, or 5 seconds")
        if self.rank_by not in RANK_CHOICES:
            raise ValueError("unsupported ranking choice")
        if not 1 <= self.limit <= 10:
            raise ValueError("result limit must be between 1 and 10")
        if self.mode not in {"review", "discovery"}:
            raise ValueError("mode must be review or discovery")

    @property
    def defending_team_key(self) -> str | None:
        return None if self.defending_side == "both" else f"metrica:{self.defending_side}"

    @property
    def slug(self) -> str:
        events = "-".join(value.lower() for value in EVENT_CHOICES[self.event_choice])
        return (
            f"game{self.game}_{self.defending_side.lower()}_{events}_"
            f"{self.pre_seconds:g}-{self.post_seconds:g}_{self.rank_by}_{self.limit}_{self.mode}"
        )


def request_from_query(query: Mapping[str, list[str]]) -> DashboardRequest:
    """Parse a browser query into a validated, immutable request."""
    def first(name: str, default: str) -> str:
        values = query.get(name, [default])
        return values[0] if values else default

    return DashboardRequest(
        game=int(first("game", "1")),
        defending_side=first("defending_side", "both"),
        event_choice=first("event_choice", "shots_goals"),
        pre_seconds=float(first("pre_seconds", "5")),
        post_seconds=float(first("post_seconds", "5")),
        rank_by=first("rank_by", "maximum_score"),
        limit=int(first("limit", "3")),
        mode=first("mode", "review"),
    )


def run_review(request: DashboardRequest, *, output_root: Path, data_root: Path | None) -> Path:
    """Execute the existing deterministic review workflow into a local package."""
    destination = output_root / request.slug
    data_dir = None if data_root is None else data_root / f"metrica_sample_game_{request.game}"
    analyze_metrica_sample_match(
        request.game,
        destination,
        data_dir=data_dir,
        render_selected=True,
        discovery_audit=request.mode == "discovery",
        event_query_limit=request.limit,
        event_types=EVENT_CHOICES[request.event_choice],
        event_pre_seconds=request.pre_seconds,
        event_post_seconds=request.post_seconds,
        event_rank_by=request.rank_by,
        event_defending_team=request.defending_team_key,
    )
    return destination


def _ranking_text(row: Mapping[str, object]) -> str:
    rank_by = str(row.get("rank_by", "maximum_score"))
    value = float(row.get("rank_value", np.nan))
    if not np.isfinite(value):
        return "Unavailable"
    if rank_by == "time_to_peak":
        return f"{value:+.2f} s from event"
    return f"{value:+.2f} m" if rank_by == "post_minus_pre_change" else f"{value:.2f} m"


def _artifact_for_row(summary: Mapping[str, object], row: Mapping[str, object]) -> dict[str, str]:
    renders = summary.get("rendered_event_windows", [])
    for item in renders if isinstance(renders, list) else []:
        if (
            int(item.get("period", -1)) == int(row.get("period", -2))
            and np.isclose(
                float(item.get("peak_time_s", np.nan)),
                float(row.get("peak_time_s", row.get("event_time_s", np.nan))),
                atol=1e-7,
                rtol=0,
            )
            and str(item.get("defending_team_key")) == str(row.get("team_key"))
        ):
            return {key: str(value) for key, value in item.items() if isinstance(value, str)}
    return {}


def build_review_view_model(package: Path, *, selected_rank: int = 1) -> dict[str, object]:
    """Build browser-facing state from one generated local review package."""
    summary_path = package / "application_summary.json"
    rows_path = package / "ranked_event_windows.json"
    if not summary_path.exists() or not rows_path.exists():
        return {
            "status": "not_run",
            "message": "No review package exists for these settings. Choose Run review.",
            "rows": [],
            "selected": None,
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    source_rows = json.loads(rows_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for raw in source_rows:
        event_name = "shot" if str(raw.get("event_type", "")).upper() in {"SHOT", "GOAL"} else "event"
        previous_offset = raw.get("previous_event_offset_s")
        previous = "No earlier event in this period"
        if previous_offset is not None and np.isfinite(float(previous_offset)):
            previous = f"{raw.get('previous_event', 'Event unavailable')} ({float(previous_offset):+.2f} s)"
        row = {
            **raw,
            "outcome_text": normalize_event_outcome(raw.get("event_type"), raw.get("event_detail")),
            "location_text": physical_event_location(raw.get("event_x_m"), raw.get("event_y_m")),
            "peak_text": time_to_peak_text(float(raw.get("time_to_peak_s", 0.0)), event_name),
            "previous_text": previous,
            "ranking_text": _ranking_text(raw),
            "artifacts": _artifact_for_row(summary, raw),
        }
        rows.append(row)
    selected = next((row for row in rows if int(row.get("rank", -1)) == selected_rank), None)
    if selected is None and rows:
        selected = rows[0]
    return {
        "status": "ready" if rows else "no_result",
        "message": (
            "No supported, visually suitable event window matched these settings. "
            "No threshold was relaxed and no substitute passage was selected."
            if not rows else ""
        ),
        "rows": rows,
        "selected": selected,
        "summary": summary,
    }


def safe_artifact_path(output_root: Path, requested: str) -> Path:
    """Resolve one dashboard artifact without permitting path traversal."""
    root = output_root.resolve()
    candidate = Path(requested).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("artifact is outside the configured dashboard output root")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def _artifact_url(path: str) -> str:
    return f"/artifact?file={quote(path, safe='')}"


def _select(name: str, options: list[tuple[str, str]], current: str) -> str:
    rendered = []
    for value, label in options:
        selected = " selected" if value == current else ""
        rendered.append(f'<option value="{escape(value)}"{selected}>{escape(label)}</option>')
    return f'<select name="{escape(name)}">{"".join(rendered)}</select>'


def render_dashboard_html(
    request: DashboardRequest,
    view: Mapping[str, object],
    *,
    error: str = "",
) -> str:
    """Render the complete dependency-free local dashboard page."""
    rows = list(view.get("rows", []))
    selected = view.get("selected")
    table_rows = []
    for row in rows:
        rank = int(row["rank"])
        teams = f"{str(row.get('attacking_team_key', '')).split(':')[-1]} attack / {str(row.get('team_key', '')).split(':')[-1]} defend"
        location = f"{row['location_text']} · {row.get('attacking_direction', 'direction unavailable')}"
        table_rows.append(
            "<tr>"
            f'<td><a href="?{_request_query(request)}&selected={rank}">#{rank}</a></td>'
            f"<td>{escape(str(row.get('match_clock', 'time unavailable')))}</td>"
            f"<td>{escape(teams)}</td>"
            f"<td>{escape(str(row['outcome_text']))}</td>"
            f"<td>{escape(str(row.get('score_state', 'Score unavailable')))}</td>"
            f"<td>{escape(location)}</td>"
            f"<td>{escape(str(row['previous_text']))}</td>"
            f"<td>{escape(str(row['peak_text']))}</td>"
            f"<td>{escape(str(row['ranking_text']))}</td>"
            "</tr>"
        )
    detail = ""
    if isinstance(selected, Mapping):
        artifacts = selected.get("artifacts", {})
        card = artifacts.get("coach_review_card_png") or artifacts.get("moment_card_png")
        gif = artifacts.get("gif")
        analyst = artifacts.get("analyst_diagnostic_png")
        technical = artifacts.get("technical_appendix_png")
        media = "".join(
            f'<img src="{_artifact_url(path)}" alt="{escape(label)}">'
            for path, label in ((card, "Football review card"), (gif, "Tracking replay"))
            if path
        )
        appendix = "".join(
            f'<img src="{_artifact_url(path)}" alt="{escape(label)}">'
            for path, label in ((analyst, "Analyst trace"), (technical, "Technical appendix"))
            if path
        )
        detail = f"""
        <section class="detail">
          <h2>Selected review: #{int(selected['rank'])} at {escape(str(selected.get('match_clock', 'time unavailable')))}</h2>
          <p class="summary">{escape(str(selected['peak_text']))} Review which defenders changed position and whether the unit was still reorganizing afterward.</p>
          <div class="media">{media or '<p>Media was not rendered for this package.</p>'}</div>
          <details><summary>Analyst appendix: trace and technical detail</summary>
            <p>Exact values, individual contributors, score construction, and diagnostics belong here—not on the main football card.</p>
            <div class="media appendix">{appendix or '<p>No appendix images are available.</p>'}</div>
          </details>
        </section>"""
    status_message = escape(error or str(view.get("message", "")))
    active_review = "active" if request.mode == "review" else ""
    active_discovery = "active" if request.mode == "discovery" else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moving the Defense · Event review</title>
<style>
:root{{--ink:#172027;--muted:#53616b;--paper:#f5f2ea;--card:#fffefa;--red:#8f1d14;--line:#d5d0c6}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.45 system-ui,sans-serif}}
main{{max-width:1440px;margin:auto;padding:28px}} h1{{font-size:2rem;margin:.2rem 0}} h2{{margin-top:0}} .lede{{max-width:880px;color:var(--muted)}}
.caveat{{background:#fff3d8;border-left:6px solid #d98500;padding:12px 16px;margin:20px 0;font-weight:650}}
.tabs a{{display:inline-block;padding:9px 14px;margin-right:8px;border:1px solid var(--line);border-radius:8px;text-decoration:none;color:var(--ink)}} .tabs a.active{{background:var(--ink);color:white}}
form,.detail,.empty{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:18px 0}}
.controls{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px}} label{{font-size:.86rem;font-weight:700}} select,input{{display:block;width:100%;margin-top:5px;padding:9px;border:1px solid #aaa;border-radius:7px;background:white}}
button{{background:var(--red);color:white;border:0;border-radius:8px;padding:11px 20px;font-weight:750;margin-top:16px;cursor:pointer}}
.table-wrap{{overflow:auto;background:white;border:1px solid var(--line);border-radius:10px}} table{{border-collapse:collapse;width:100%;font-size:.87rem}} th,td{{padding:10px;border-bottom:1px solid #e7e3dc;text-align:left;vertical-align:top}} th{{background:#eae6dc;position:sticky;top:0}} td a{{font-weight:800;color:var(--red)}}
.media{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}} .media img{{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:8px;background:white}} details{{margin-top:18px;border-top:1px solid var(--line);padding-top:14px}} summary{{cursor:pointer;font-weight:800}} .summary{{font-size:1.08rem}}
.discovery{{border-left:5px solid #65737e;padding-left:14px;color:var(--muted)}} footer{{color:var(--muted);font-size:.9rem;margin:28px 0}}
</style></head><body><main>
<h1>Event-first defensive review</h1>
<p class="lede">Start with a football event, then review how the defending unit moved around it. The queue organizes video review; it does not name a tactic.</p>
<div class="caveat">Events organize review. This tool does not infer tactical intent, pressing, defensive quality, responsibility, causality, success, or player value.</div>
<nav class="tabs"><a class="{active_review}" href="?mode=review">Event review</a><a class="{active_discovery}" href="?mode=discovery">Discovery / Audit</a></nav>
{('<p class="discovery">Discovery / Audit is deliberately separate from the default queue. It exposes high, rapid-increase, and conditional-low score checks for metric audit—not tactical categories.</p>' if request.mode == 'discovery' else '')}
<form method="get"><input type="hidden" name="run" value="1"><input type="hidden" name="mode" value="{escape(request.mode)}">
<div class="controls">
<label>Match{_select('game', [('1','Metrica Sample Game 1'),('2','Metrica Sample Game 2')], str(request.game))}</label>
<label>Defending perspective{_select('defending_side', [('both','Both teams'),('Home','Home'),('Away','Away')], request.defending_side)}</label>
<label>Football event{_select('event_choice', [('shots_goals','Shots and goals'),('shots','Shots excluding goals'),('goals','Goals only')], request.event_choice)}</label>
<label>Seconds before{_select('pre_seconds', [(str(int(v)),f'{int(v)} seconds') for v in WINDOW_CHOICES], str(int(request.pre_seconds)))}</label>
<label>Seconds after{_select('post_seconds', [(str(int(v)),f'{int(v)} seconds') for v in WINDOW_CHOICES], str(int(request.post_seconds)))}</label>
<label>Queue order{_select('rank_by', list(RANK_CHOICES.items()), request.rank_by)}</label>
<label>Results<input type="number" name="limit" min="1" max="10" value="{request.limit}"></label>
</div><button type="submit">Run review</button></form>
{(f'<div class="empty">{status_message}</div>' if status_message else '')}
{('<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Event time</th><th>Teams</th><th>Outcome</th><th>Score</th><th>Pitch context</th><th>Previous action</th><th>Peak timing</th><th>Ranking value</th></tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table></div>' if table_rows else '')}
{detail}
<footer>Local prototype · generated packages stay outside Git · exact score definitions and units remain in the analyst appendix.</footer>
</main></body></html>"""


def _request_query(request: DashboardRequest) -> str:
    return (
        f"game={request.game}&defending_side={quote(request.defending_side)}&"
        f"event_choice={quote(request.event_choice)}&pre_seconds={request.pre_seconds:g}&"
        f"post_seconds={request.post_seconds:g}&rank_by={quote(request.rank_by)}&"
        f"limit={request.limit}&mode={quote(request.mode)}"
    )


def create_server(
    *,
    host: str,
    port: int,
    output_root: Path,
    data_root: Path | None = None,
    server_factory: Callable[..., ThreadingHTTPServer] = ThreadingHTTPServer,
) -> ThreadingHTTPServer:
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/artifact":
                try:
                    artifact = safe_artifact_path(output_root, query.get("file", [""])[0])
                    payload = artifact.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(artifact.name)[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (ValueError, FileNotFoundError):
                    self.send_error(404)
                return
            error = ""
            try:
                request = request_from_query(query)
                package = output_root / request.slug
                if query.get("run") == ["1"]:
                    package = run_review(request, output_root=output_root, data_root=data_root)
                selected_rank = int(query.get("selected", ["1"])[0])
                view = build_review_view_model(package, selected_rank=selected_rank)
            except (ValueError, RuntimeError) as exc:
                request = DashboardRequest(mode=query.get("mode", ["review"])[0])
                view = {"status": "error", "message": "", "rows": [], "selected": None}
                error = f"Review could not run: {exc}"
            payload = render_dashboard_html(request, view, error=error).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    return server_factory((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/moving_the_defense_dashboard"))
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()
    server = create_server(
        host=args.host, port=args.port, output_root=args.output_root, data_root=args.data_root
    )
    print(f"Event review dashboard: http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
