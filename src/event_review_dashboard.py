"""Small local browser dashboard for event-first football review.

The dashboard is a presentation layer over the committed event-window API. It
does not define scores, select new scientific outcomes, or classify tactics.
Runtime packages stay outside the repository by default.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import os
import shutil
import tempfile
import threading
from typing import Callable, Mapping
from urllib.parse import parse_qs, quote, urlparse
import zipfile

import matplotlib

# Dashboard rendering runs in background worker threads.  Force a non-interactive
# backend before importing the application renderer (which imports pyplot).
matplotlib.use("Agg", force=True)

import numpy as np
import pandas as pd

from defensive_reorganization_application import EventWindowQuery, query_event_windows
from defensive_reorganization_replay import DefensiveReorganizationScores
from run_metrica_game2_application import (
    ANALYST_CLIP_CONTEXT_SECONDS,
    add_analyst_context,
    analyze_metrica_sample_match,
    audit_visual_suitability,
    load_ball,
    load_normalized_team,
    load_shots,
    metrica_sample_preset,
    normalize_event_outcome,
    physical_event_location,
    render_selected,
    time_to_peak_text,
)


RANK_CHOICES = {
    "maximum_score": "Most movement within the defensive unit",
    "anchor_score": "Defensive movement at the event",
    "post_minus_pre_change": "Biggest rise in defensive movement after the event",
    "time_to_peak": "Earliest point of greatest defensive movement",
}
EVENT_CHOICES = {
    "shots_goals": ("SHOT", "GOAL"),
    "shots": ("SHOT",),
    "goals": ("GOAL",),
    "possession_changes": ("POSSESSION_CHANGE",),
}
WINDOW_CHOICES = (2.0, 3.0, 5.0)
STATUS_FILE = "dashboard_status.json"
READY_FILES = ("application_summary.json", "ranked_event_windows.json")
MATCH_CACHE_FILES = ("event_catalog.json", "application_summary.json")
CACHE_MANIFEST = "cache_manifest.json"
CACHE_SCHEMA_VERSION = 2
_JOBS: dict[str, threading.Thread] = {}
_JOBS_LOCK = threading.Lock()
_SCORE_CACHE: dict[tuple[str, str, int, int], DefensiveReorganizationScores] = {}
_SCORE_CACHE_LOCK = threading.Lock()
_RESOURCE_LOCKS: dict[str, threading.Lock] = {}
_RESOURCE_LOCKS_GUARD = threading.Lock()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DashboardRequest:
    game: int = 1
    defending_side: str = "both"
    event_choice: str = "shots_goals"
    pre_seconds: float = 5.0
    post_seconds: float = 5.0
    rank_by: str = "maximum_score"
    limit: int = 3

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

    @property
    def defending_team_key(self) -> str | None:
        return None if self.defending_side == "both" else f"metrica:{self.defending_side}"

    @property
    def slug(self) -> str:
        events = "-".join(value.lower() for value in EVENT_CHOICES[self.event_choice])
        return (
            f"game{self.game}_{self.defending_side.lower()}_{events}_"
            f"{self.pre_seconds:g}-{self.post_seconds:g}_{self.rank_by}_{self.limit}_review"
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
    )


def match_cache_path(output_root: Path, game: int) -> Path:
    return output_root / "prepared_matches" / f"metrica_sample_game_{game}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_cache_manifest(game: int, data_root: Path | None) -> dict[str, object]:
    data_dir = None if data_root is None else data_root / f"metrica_sample_game_{game}"
    preset = metrica_sample_preset(game, data_dir=data_dir)
    source_paths = {
        "home_tracking": preset.data_dir / preset.team_files["metrica:Home"],
        "away_tracking": preset.data_dir / preset.team_files["metrica:Away"],
        "events": preset.data_dir / preset.events_file,
    }
    implementation_paths = {
        name: PROJECT_ROOT / "src" / name
        for name in (
            "defensive_reorganization_replay.py",
            "defensive_reorganization_application.py",
            "run_metrica_game2_application.py",
            "event_review_dashboard.py",
        )
    }
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "game": game,
        "match_id": preset.match_id,
        "sources": {
            name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for name, path in source_paths.items()
        },
        "implementations": {
            name: _sha256(path) for name, path in implementation_paths.items()
        },
        "preparation": {
            "source_fps": 25.0,
            "smoothing_frames": 7,
            "window_seconds": 2.0,
            "visual_context_seconds": ANALYST_CLIP_CONTEXT_SECONDS,
        },
    }


def _manifest_identity(manifest: Mapping[str, object]) -> str:
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _resource_lock(key: str) -> threading.Lock:
    with _RESOURCE_LOCKS_GUARD:
        return _RESOURCE_LOCKS.setdefault(key, threading.Lock())


def prepared_match_ready(
    package: Path, expected_manifest: Mapping[str, object] | None = None
) -> bool:
    required = (*MATCH_CACHE_FILES, CACHE_MANIFEST)
    structural = all((package / name).is_file() for name in required) and all(
        all((package / team.replace(":", "_") / name).is_file() for name in (
            "player_scores.parquet", "team_scores.parquet", "score_metadata.json"
        ))
        for team in ("metrica:Home", "metrica:Away")
    )
    if not structural:
        return False
    try:
        actual = json.loads((package / CACHE_MANIFEST).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return expected_manifest is None or actual == dict(expected_manifest)


def _add_context_to_supported_candidates(
    candidates: pd.DataFrame,
    scores: DefensiveReorganizationScores,
    *,
    defending: str,
    attacking: str,
    tracking: Mapping[str, pd.DataFrame],
    ball: pd.DataFrame,
    raw_events: pd.DataFrame,
) -> pd.DataFrame:
    """Contextualize only windows that pass the unchanged support/suitability query."""
    eligibility_query = EventWindowQuery(
        defending_team_key=defending,
        attacking_team_key=attacking,
        event_types=tuple(sorted(candidates["event_type"].astype(str).str.upper().unique())),
        pre_seconds=5.0,
        post_seconds=5.0,
        rank_by="maximum_score",
        limit=max(1, len(candidates)),
        require_suitable=True,
    )
    eligible = query_event_windows(candidates, scores, eligibility_query).windows
    if not eligible.empty:
        eligible_ids = set(eligible["event_id"].astype(str))
        context_input = candidates.loc[
            candidates["event_id"].astype(str).isin(eligible_ids)
        ].rename(columns={"event_time_s": "peak_time_s"})
        context_input["team_key"] = defending
        contextual = add_analyst_context(
            context_input,
            tracking,
            ball,
            raw_events,
            context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
        ).rename(columns={"peak_time_s": "event_time_s"})
        contextual["attacking_team_key"] = attacking
        contextual["defending_team_key"] = defending
        contextual["team_key"] = attacking
        context_columns = [
            column
            for column in contextual.columns
            if column not in candidates.columns
            and column not in {"attacking_team_key", "defending_team_key"}
        ]
        candidates = candidates.merge(
            contextual[["event_id", *context_columns]],
            on="event_id",
            how="left",
            validate="one_to_one",
        )
    candidates["attacking_team_key"] = attacking
    candidates["defending_team_key"] = defending
    candidates["team_key"] = attacking
    return candidates


def load_open_play_possession_changes(
    path: Path, *, match_id: str
) -> pd.DataFrame:
    """Return deterministic event-derived changes of possession.

    PASS, RECOVERY, SET PIECE, and SHOT establish the recorded possession team.
    A team change at PASS, RECOVERY, or SHOT is retained; SET PIECE changes
    update the clock but are not review anchors. CHALLENGE and BALL LOST never
    establish possession on their own.
    """
    raw = pd.read_csv(path).reset_index(names="provider_event_index")
    required = {
        "Team", "Type", "Period", "Start Frame", "Start Time [s]",
        "Subtype", "Start X", "Start Y",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"missing Metrica event columns: {sorted(missing)}")
    raw["Type"] = raw["Type"].astype(str).str.strip().str.upper()
    raw["Team"] = raw["Team"].astype(str).str.strip()
    qualifying = raw.loc[
        raw["Type"].isin({"PASS", "RECOVERY", "SET PIECE", "SHOT"})
        & raw["Team"].isin({"Home", "Away"})
    ].copy()
    qualifying = qualifying.sort_values(
        ["Period", "Start Time [s]", "Start Frame", "provider_event_index"],
        kind="mergesort",
    )
    qualifying["previous_possession_team"] = qualifying.groupby(
        "Period", sort=False
    )["Team"].shift()
    changes = qualifying.loc[
        qualifying["previous_possession_team"].notna()
        & qualifying["Team"].ne(qualifying["previous_possession_team"])
        & qualifying["Type"].ne("SET PIECE")
    ].copy()
    sequence = changes.groupby("Period", sort=False).cumcount() + 1
    return pd.DataFrame(
        {
            "event_id": [
                f"{match_id}-possession-change-p{int(period)}-{int(index):03d}"
                for period, index in zip(changes["Period"], sequence, strict=True)
            ],
            "match_id": match_id,
            "period": changes["Period"].astype(int),
            "event_time_s": pd.to_numeric(changes["Start Time [s]"], errors="raise"),
            "event_type": "POSSESSION_CHANGE",
            "event_detail": "POSSESSION WON",
            "event_x_m": pd.to_numeric(changes["Start X"], errors="coerce") * 105.0 - 52.5,
            "event_y_m": pd.to_numeric(changes["Start Y"], errors="coerce") * 68.0 - 34.0,
            "team_key": "metrica:" + changes["Team"].astype(str),
            "possession_event_type": changes["Type"].astype(str),
        }
    ).reset_index(drop=True)


def _prepare_match_cache(game: int, *, output_root: Path, data_root: Path | None) -> Path:
    """Score one match once and cache response-free event context for later queries."""
    destination = match_cache_path(output_root, game)
    expected = expected_cache_manifest(game, data_root)
    with _resource_lock(f"match-cache:{destination.resolve()}"):
        if prepared_match_ready(destination, expected):
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent))
        backup = destination.with_name(f".{destination.name}.replaced")
        data_dir = None if data_root is None else data_root / f"metrica_sample_game_{game}"
        try:
            analyze_metrica_sample_match(
                game,
                staging,
                data_dir=data_dir,
                render_selected=False,
                discovery_audit=False,
                event_query_limit=10,
                event_types=("SHOT", "GOAL"),
                event_pre_seconds=5.0,
                event_post_seconds=5.0,
                event_rank_by="maximum_score",
                event_defending_team=None,
            )
            preset = metrica_sample_preset(game, data_dir=data_dir)
            tracking = {
                team_key: load_normalized_team(
                    preset.data_dir / filename, team_key, match_id=preset.match_id
                )
                for team_key, filename in preset.team_files.items()
            }
            ball = load_ball(
                preset.data_dir / preset.team_files["metrica:Home"], match_id=preset.match_id
            )
            raw_events = pd.read_csv(preset.data_dir / preset.events_file)
            shots = load_shots(preset.data_dir / preset.events_file, match_id=preset.match_id)
            possession_changes = load_open_play_possession_changes(
                preset.data_dir / preset.events_file, match_id=preset.match_id
            )
            review_events = pd.concat(
                [shots, possession_changes], ignore_index=True, sort=False
            )
            suitability = audit_visual_suitability(
                review_events.rename(columns={"event_time_s": "peak_time_s"}),
                tracking,
                raw_events,
                ball_tracking=ball,
                clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
            ).rename(columns={"peak_time_s": "event_time_s"})
            catalog_rows = []
            for defending in sorted(preset.team_files):
                attacking = "metrica:Away" if defending == "metrica:Home" else "metrica:Home"
                candidates = suitability.loc[suitability["team_key"].eq(attacking)].copy()
                catalog_rows.append(_add_context_to_supported_candidates(
                    candidates,
                    _read_scores(staging, defending),
                    defending=defending,
                    attacking=attacking,
                    tracking=tracking,
                    ball=ball,
                    raw_events=raw_events,
                ))
            catalog = pd.concat(catalog_rows, ignore_index=True).sort_values(
                ["period", "event_time_s", "event_id", "defending_team_key"],
                kind="mergesort",
            )
            (staging / "event_catalog.json").write_text(
                catalog.to_json(orient="records", indent=2) + "\n", encoding="utf-8"
            )
            (staging / CACHE_MANIFEST).write_text(
                json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if not prepared_match_ready(staging, expected):
                raise RuntimeError("staged match cache failed provenance validation")
            if backup.exists():
                shutil.rmtree(backup)
            if destination.exists():
                os.replace(destination, backup)
            os.replace(staging, destination)
            if backup.exists():
                shutil.rmtree(backup)
        except Exception:
            if backup.exists() and not destination.exists():
                os.replace(backup, destination)
            if staging.exists():
                shutil.rmtree(staging)
            raise
    return destination


def _query_prepared_match(
    request: DashboardRequest, match_package: Path, destination: Path
) -> Path:
    """Create a lightweight query package from one already-prepared match."""
    cache_manifest = json.loads((match_package / CACHE_MANIFEST).read_text(encoding="utf-8"))
    match_identity = _manifest_identity(cache_manifest)
    if current_query_package(destination, match_identity):
        return destination
    catalog = pd.read_json(match_package / "event_catalog.json")
    teams = (
        (request.defending_team_key,)
        if request.defending_team_key is not None
        else ("metrica:Away", "metrica:Home")
    )
    results = []
    metadata = []
    for defending in teams:
        attacking = "metrica:Away" if defending == "metrica:Home" else "metrica:Home"
        events = catalog.loc[catalog["defending_team_key"].eq(defending)].copy()
        query = EventWindowQuery(
            defending_team_key=defending,
            attacking_team_key=attacking,
            event_types=EVENT_CHOICES[request.event_choice],
            pre_seconds=request.pre_seconds,
            post_seconds=request.post_seconds,
            rank_by=request.rank_by,
            limit=request.limit,
            require_suitable=True,
        )
        queried = query_event_windows(events, _read_scores(match_package, defending), query)
        windows = queried.windows
        if not windows.empty:
            context_columns = [
                column for column in events.columns
                if column not in windows.columns and column not in {"team_key"}
            ]
            windows = windows.merge(
                events[["event_id", "defending_team_key", *context_columns]],
                on=["event_id", "defending_team_key"], how="left", validate="one_to_one"
            )
        results.append(windows)
        metadata.append(dict(queried.metadata))
    rows = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    if not rows.empty:
        ascending = request.rank_by == "time_to_peak"
        rows = rows.sort_values(
            ["rank_value", "event_time_s", "event_id"],
            ascending=[ascending, True, True], kind="mergesort"
        ).head(request.limit).reset_index(drop=True)
        rows["rank"] = np.arange(1, len(rows) + 1)
        rows["team_key"] = rows["defending_team_key"]
        rows["peak_time_s"] = rows["event_time_s"]
    destination.mkdir(parents=True, exist_ok=True)
    rows.to_csv(destination / "ranked_event_windows.csv", index=False, lineterminator="\n")
    (destination / "ranked_event_windows.json").write_text(
        rows.to_json(orient="records", indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "status": "CACHED_EVENT_REVIEW_QUERY_COMPLETE",
        "game": request.game,
        "match_cache": str(match_package),
        "match_cache_identity": match_identity,
        "event_window_count": int(len(rows)),
        "rendered_event_window_count": 0,
        "rendered_event_windows": [],
        "query": {
            "defending_side": request.defending_side,
            "event_types": list(EVENT_CHOICES[request.event_choice]),
            "pre_seconds": request.pre_seconds,
            "post_seconds": request.post_seconds,
            "rank_by": request.rank_by,
            "limit": request.limit,
        },
        "no_result_reasons": [
            reason for item in metadata for reason in item.get("no_result_reasons", ())
        ],
        "claim_boundary": "review organization only; no tactical or causal classification",
    }
    (destination / "application_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def run_review(request: DashboardRequest, *, output_root: Path, data_root: Path | None) -> Path:
    """Prepare one match once, then cache this lightweight deterministic query."""
    destination = output_root / request.slug
    match_package = _prepare_match_cache(
        request.game, output_root=output_root, data_root=data_root
    )
    cache_manifest = json.loads((match_package / CACHE_MANIFEST).read_text(encoding="utf-8"))
    if current_query_package(destination, _manifest_identity(cache_manifest)):
        return destination
    return _query_prepared_match(request, match_package, destination)


def package_ready(package: Path) -> bool:
    return all((package / name).is_file() for name in READY_FILES)


def current_query_package(package: Path, expected_match_identity: str | None = None) -> bool:
    if not package_ready(package):
        return False
    try:
        summary = json.loads(
            (package / "application_summary.json").read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return False
    return (
        summary.get("status") == "CACHED_EVENT_REVIEW_QUERY_COMPLETE"
        and (
            expected_match_identity is None
            or summary.get("match_cache_identity") == expected_match_identity
        )
    )


def _write_status(package: Path, state: str, message: str, **extra: object) -> None:
    package.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": state,
        "message": message,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    temporary = package / f".{STATUS_FILE}.tmp"
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(package / STATUS_FILE)


def package_status(package: Path) -> dict[str, object]:
    path = package / STATUS_FILE
    if path.is_file():
        try:
            status = json.loads(path.read_text(encoding="utf-8"))
            if status.get("state") in {"preparing", "rendering", "error"}:
                return status
        except (json.JSONDecodeError, OSError):
            return {"state": "error", "message": "Preparation status could not be read."}
    if package_ready(package):
        return {"state": "ready", "message": "Match is ready to review."}
    return {"state": "not_prepared", "message": "Prepare this match before reviewing passages."}


def _start_job(key: str, target: Callable[[], None]) -> bool:
    """Start one background job per key; return False when already running."""
    with _JOBS_LOCK:
        current = _JOBS.get(key)
        if current is not None and current.is_alive():
            return False

        def guarded() -> None:
            try:
                target()
            finally:
                with _JOBS_LOCK:
                    _JOBS.pop(key, None)

        thread = threading.Thread(target=guarded, name=f"review-{key}", daemon=True)
        _JOBS[key] = thread
        thread.start()
        return True


def start_prepare_job(
    request: DashboardRequest, *, output_root: Path, data_root: Path | None
) -> bool:
    package = output_root / request.slug

    def prepare() -> None:
        try:
            run_review(request, output_root=output_root, data_root=data_root)
            _write_status(package, "ready", "Match is ready to review.")
        except Exception as exc:  # surfaced in the local UI; scientific code remains fail-closed
            _write_status(package, "error", f"Preparation failed: {exc}")

    # Publish the busy state before the worker starts so the first HTTP response
    # cannot race ahead of the status file and look like a no-op.
    _write_status(
        package,
        "preparing",
        "Preparing the match and building the review queue…",
        detail=(
            "The first preparation can take a few minutes. Keep this page open; "
            "it refreshes automatically. Later filters reuse the prepared match."
        ),
    )
    started = _start_job(f"prepare:game:{request.game}", prepare)
    if not started:
        _write_status(
            package,
            "preparing",
            "This match is already being prepared in another request.",
            detail=(
                "No duplicate job was started. Wait for that preparation to finish, "
                "then choose Prepare match review once for these filters."
            ),
        )
    return started


def _read_scores(package: Path, team_key: str) -> DefensiveReorganizationScores:
    directory = package / team_key.replace(":", "_")
    player_path = directory / "player_scores.parquet"
    team_path = directory / "team_scores.parquet"
    cache_key = (
        str(package.resolve()), team_key,
        player_path.stat().st_mtime_ns, team_path.stat().st_mtime_ns,
    )
    with _SCORE_CACHE_LOCK:
        cached = _SCORE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        player = pd.read_parquet(player_path)
        team = pd.read_parquet(team_path)
    except ImportError:
        import polars as pl

        player = pd.DataFrame(pl.read_parquet(player_path).to_dicts())
        team = pd.DataFrame(pl.read_parquet(team_path).to_dicts())
    metadata = json.loads((directory / "score_metadata.json").read_text(encoding="utf-8"))
    scores = DefensiveReorganizationScores(player, team, metadata)
    with _SCORE_CACHE_LOCK:
        for key in tuple(_SCORE_CACHE):
            if key[:2] == cache_key[:2] and key != cache_key:
                _SCORE_CACHE.pop(key, None)
        _SCORE_CACHE[cache_key] = scores
    return scores


def render_cached_passage(
    request: DashboardRequest,
    rank: int,
    *,
    output_root: Path,
    data_root: Path | None,
) -> Path:
    """Render one selected passage from cached scores; never rescore the match."""
    package = output_root / request.slug
    if not package_ready(package):
        raise RuntimeError("prepare the review before rendering a passage")
    rows = pd.read_json(package / "ranked_event_windows.json")
    selected = rows.loc[rows["rank"].astype(int).eq(rank)].copy()
    if len(selected) != 1:
        raise ValueError("selected review rank is unavailable")
    if "team_key" not in selected:
        selected = selected.rename(columns={"defending_team_key": "team_key"})
    if "peak_time_s" not in selected:
        selected = selected.rename(columns={"event_time_s": "peak_time_s"})
    selected["moment_type"] = "event_window"
    selected["presentation_role"] = "event_window"
    selected["analyst_interpretation"] = "Event-anchored descriptive movement window"
    selected["display_order"] = selected["rank"].astype(int)
    selected["selected_for_clip"] = True
    selected["default_render"] = True
    selected["review_pre_seconds"] = request.pre_seconds
    selected["review_post_seconds"] = request.post_seconds
    selected["review_rank_label"] = RANK_CHOICES[request.rank_by]

    preset_data = None if data_root is None else data_root / f"metrica_sample_game_{request.game}"
    preset = metrica_sample_preset(request.game, data_dir=preset_data)
    tracking = {
        team_key: load_normalized_team(
            preset.data_dir / filename, team_key, match_id=preset.match_id
        )
        for team_key, filename in preset.team_files.items()
    }
    match_package = match_cache_path(output_root, request.game)
    expected_manifest = expected_cache_manifest(request.game, data_root)
    if not prepared_match_ready(match_package, expected_manifest):
        raise RuntimeError("prepared match cache is unavailable")
    query_summary = json.loads(
        (package / "application_summary.json").read_text(encoding="utf-8")
    )
    if query_summary.get("match_cache_identity") != _manifest_identity(expected_manifest):
        raise RuntimeError("review query is not bound to the current prepared match cache")
    scores = {
        team_key: _read_scores(match_package, team_key)
        for team_key in preset.team_files
    }
    rendered = render_selected(
        selected,
        tracking,
        scores,
        package / "event_review",
        preset.data_dir,
        match_id=preset.match_id,
        team_files=preset.team_files,
        clip_context_seconds=ANALYST_CLIP_CONTEXT_SECONDS,
    )
    if len(rendered) != 1:
        raise RuntimeError("selected passage did not produce exactly one media package")
    summary_path = package / "application_summary.json"
    with _resource_lock(f"query-summary:{package.resolve()}"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        existing = [
            item for item in summary.get("rendered_event_windows", [])
            if int(item.get("period", -1)) != int(selected.iloc[0]["period"])
            or not np.isclose(float(item.get("peak_time_s", np.nan)), float(selected.iloc[0]["peak_time_s"]), atol=1e-7, rtol=0)
            or str(item.get("defending_team_key")) != str(selected.iloc[0]["team_key"])
        ]
        summary["rendered_event_windows"] = [*existing, rendered[0]]
        summary["rendered_event_window_count"] = len(summary["rendered_event_windows"])
        temporary = summary_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(summary_path)
    return Path(rendered[0]["gif"])


def start_render_job(
    request: DashboardRequest,
    rank: int,
    *,
    output_root: Path,
    data_root: Path | None,
) -> bool:
    package = output_root / request.slug

    def render() -> None:
        _write_status(package, "rendering", f"Rendering replay for review #{rank}…", rank=rank)
        try:
            render_cached_passage(
                request, rank, output_root=output_root, data_root=data_root
            )
            _write_status(package, "ready", f"Replay #{rank} is cached.")
        except Exception as exc:
            _write_status(package, "error", f"Replay render failed: {exc}", rank=rank)

    return _start_job(f"render:{request.slug}", render)


def _ranking_text(row: Mapping[str, object]) -> str:
    rank_by = str(row.get("rank_by", "maximum_score"))
    value = float(row.get("rank_value", np.nan))
    if not np.isfinite(value):
        return "Unavailable"
    if rank_by == "time_to_peak":
        return f"{value:+.2f} s from event"
    return f"{value:+.2f} m" if rank_by == "post_minus_pre_change" else f"{value:.2f} m"


def _ranking_heading(rank_by: str) -> str:
    return {
        "maximum_score": "Most movement (m)",
        "anchor_score": "Movement at event (m)",
        "post_minus_pre_change": "Rise after event (m)",
        "time_to_peak": "Peak timing",
    }[rank_by]


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
            "message": "This match has not been prepared yet. Choose Prepare match review.",
            "rows": [],
            "selected": None,
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    source_rows = json.loads(rows_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for raw in source_rows:
        event_type = str(raw.get("event_type", "")).upper()
        event_name = (
            "shot" if event_type in {"SHOT", "GOAL"}
            else "possession change" if event_type == "POSSESSION_CHANGE"
            else "event"
        )
        previous_offset = raw.get("previous_event_offset_s")
        previous = "No earlier event in this period"
        if previous_offset is not None and np.isfinite(float(previous_offset)):
            previous = f"{raw.get('previous_event', 'Event unavailable')} ({float(previous_offset):+.2f} s)"
        row = {
            **raw,
            "outcome_text": (
                "Possession lost"
                if event_type == "POSSESSION_CHANGE"
                else normalize_event_outcome(raw.get("event_type"), raw.get("event_detail"))
            ),
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
            "No complete, viewable passage matched these choices. "
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


def _safe_package_artifact(package: Path, value: str) -> Path:
    root = package.resolve()
    candidate = Path(value).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise ValueError("review-pack artifact is unavailable or outside its package")
    return candidate


def export_review_pack(package: Path, ranks: tuple[int, ...], destination: Path) -> Path:
    """Create a portable coach-facing HTML pack plus a separate audit manifest."""
    if not ranks:
        raise ValueError("select at least one rendered passage before export")
    view = build_review_view_model(package)
    indexed = {int(row["rank"]): row for row in view.get("rows", [])}
    selected = []
    for rank in dict.fromkeys(ranks):
        row = indexed.get(rank)
        if row is None:
            raise ValueError(f"review rank {rank} is unavailable")
        artifacts = row.get("artifacts", {})
        if not artifacts.get("gif") or not artifacts.get("coach_review_card_png"):
            raise ValueError(f"review rank {rank} must be rendered before export")
        selected.append(row)

    if destination.exists():
        shutil.rmtree(destination)
    media = destination / "media"
    media.mkdir(parents=True)
    manifest_rows = []
    sections = []
    for order, row in enumerate(selected, start=1):
        artifacts = row["artifacts"]
        copied: dict[str, str] = {}
        for key in ("coach_review_card_png", "gif", "analyst_diagnostic_png", "technical_appendix_png"):
            value = artifacts.get(key)
            if not value:
                continue
            source = _safe_package_artifact(package, str(value))
            target = media / f"{order:02d}_{source.name}"
            shutil.copyfile(source, target)
            copied[key] = target.relative_to(destination).as_posix()
        sections.append(
            f'''<section><h2>Passage {order} · {escape(str(row.get("match_clock", "time unavailable")))}</h2>
<p><strong>{escape(str(row.get("outcome_text", "Event outcome unavailable")))}</strong> · {escape(str(row.get("score_state", "Score unavailable")))} · {escape(str(row.get("location_text", "Location unavailable")))}</p>
<p>{escape(str(row.get("peak_text", "Movement timing unavailable")))}</p>
<div class="media"><img src="{escape(copied["coach_review_card_png"])}" alt="Review context card"><img src="{escape(copied["gif"])}" alt="Tracking replay"></div>
<p class="prompt">Review prompt: Which defenders changed position most around the event, and was the unit still reorganizing afterward?</p></section>'''
        )
        manifest_rows.append({
            "display_order": order,
            "rank": int(row["rank"]),
            "event_id": str(row.get("event_id", "")),
            "match_id": str(row.get("match_id", "")),
            "period": int(row.get("period", 0)),
            "match_clock": str(row.get("match_clock", "")),
            "files": copied,
        })
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Defensive event review pack</title>
<style>body{{max-width:1100px;margin:0 auto;padding:32px;font:16px/1.5 system-ui;color:#182126;background:#f4f1e9}}header,section{{background:white;padding:24px;margin:0 0 24px;border-radius:12px}}h1,h2{{margin-top:0}}.media{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}img{{width:100%;height:auto}}.prompt{{font-size:1.08rem;font-weight:650}}.boundary{{border-left:5px solid #cf8500;padding-left:14px}}@media(max-width:760px){{.media{{grid-template-columns:1fr}}}}</style></head><body>
<header><h1>Event-first defensive review</h1><p>Selected passages for a focused football conversation.</p><p class="boundary">This pack organizes human review. It does not identify tactics, intent, quality, responsibility, causation, success, or player value.</p></header>
{''.join(sections)}</body></html>'''
    (destination / "index.html").write_text(html, encoding="utf-8")
    manifest = {
        "status": "LOCAL_ANALYST_REVIEW_PACK",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_package": package.name,
        "selected_passages": manifest_rows,
        "interpretation_boundary": "descriptive review support only; no tactical or causal classification",
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    archive = destination.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                bundle.write(path, Path(destination.name) / path.relative_to(destination))
    return archive


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
    picked: tuple[int, ...] = (),
) -> str:
    """Render the complete dependency-free local dashboard page."""
    rows = list(view.get("rows", []))
    selected = view.get("selected")
    table_rows = []
    for row in rows:
        rank = int(row["rank"])
        retained = rank in picked
        rendered = bool(row.get("artifacts", {}).get("gif"))
        toggle = (
            tuple(value for value in picked if value != rank)
            if retained
            else (*picked, rank)
        )
        action_picked = toggle if retained or rendered else picked
        common = (
            f"{_request_query(request)}&selected={rank}&"
            f"picked={quote(','.join(str(value) for value in action_picked))}"
        )
        pack_label = "Remove" if retained else ("Keep" if rendered else "Render first")
        teams = f"{str(row.get('attacking_team_key', '')).split(':')[-1]} attack / {str(row.get('team_key', '')).split(':')[-1]} defend"
        location = f"{row['location_text']} · {row.get('attacking_direction', 'direction unavailable')}"
        table_rows.append(
            "<tr>"
            f'<td><a href="?{common}">#{rank}</a></td>'
            f"<td>{escape(str(row.get('match_clock', 'time unavailable')))}</td>"
            f"<td>{escape(teams)}</td>"
            f"<td>{escape(str(row['outcome_text']))}</td>"
            f"<td>{escape(str(row.get('score_state', 'Score unavailable')))}</td>"
            f"<td>{escape(location)}</td>"
            f"<td>{escape(str(row['previous_text']))}</td>"
            f"<td>{escape(str(row['peak_text']))}</td>"
            f"<td>{escape(str(row['ranking_text']))}</td>"
            f'<td><a href="?{common}">{pack_label}</a></td>'
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
          <div class="media">{media or '<p>This passage is ready, but its replay has not been rendered yet.</p>'}</div>
          {('' if gif else f'<p><a class="action" href="?{_request_query(request)}&selected={int(selected["rank"])}&picked={quote(",".join(str(value) for value in picked))}&{("retry_render=1" if str(view.get("status")) == "error" else "render=1")}">{("Retry replay" if str(view.get("status")) == "error" else "Render this replay")}</a></p>')}
          <details><summary>Analyst appendix: trace and technical detail</summary>
            <p>Exact values, individual contributors, score construction, and diagnostics belong here—not on the main football card.</p>
            <div class="media appendix">{appendix or '<p>No appendix images are available.</p>'}</div>
          </details>
        </section>"""
    state = str(view.get("status", ""))
    status_message = escape(error or str(view.get("message", "")))
    status_detail = str(view.get("status_detail", ""))
    if not status_detail and state in {"preparing", "rendering"}:
        status_detail = (
            "Keep this page open. It refreshes automatically, and repeated clicks "
            "will not start duplicate work."
        )
    busy = state in {"preparing", "rendering"}
    refresh = '<meta http-equiv="refresh" content="2">' if state in {"preparing", "rendering"} else ""
    picked_text = ",".join(str(value) for value in picked)
    export_action = (
        f'<a class="action secondary" href="/export?package={quote(request.slug)}&ranks={quote(picked_text)}">Export {len(picked)} selected passage{"s" if len(picked) != 1 else ""}</a>'
        if picked else '<span class="muted">Keep rendered passages to build the portable review pack.</span>'
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moving the Defense · Event review</title>{refresh}
<style>
:root{{--ink:#172027;--muted:#53616b;--paper:#f5f2ea;--card:#fffefa;--red:#8f1d14;--line:#d5d0c6}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.45 system-ui,sans-serif}}
main{{max-width:1440px;margin:auto;padding:28px}} h1{{font-size:2rem;margin:.2rem 0}} h2{{margin-top:0}} .lede{{max-width:880px;color:var(--muted)}}
.caveat{{background:#fff3d8;border-left:6px solid #d98500;padding:12px 16px;margin:20px 0;font-weight:650}}
form,.detail,.empty{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:18px 0}}
.progress-panel{{display:flex;align-items:center;gap:14px;background:#fff8e8;border:2px solid #d98500;border-radius:12px;padding:16px 18px;margin:18px 0}} .progress-panel p{{margin:2px 0}} .spinner{{width:26px;height:26px;border:4px solid #ead8b4;border-top-color:#9d4e00;border-radius:50%;animation:spin .9s linear infinite;flex:0 0 auto}} @keyframes spin{{to{{transform:rotate(360deg)}}}}
.controls{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px}} label{{font-size:.86rem;font-weight:700}} select,input{{display:block;width:100%;margin-top:5px;padding:9px;border:1px solid #aaa;border-radius:7px;background:white}}
button,.action{{display:inline-block;background:var(--red);color:white;border:0;border-radius:8px;padding:11px 20px;font-weight:750;margin-top:16px;cursor:pointer;text-decoration:none}} button:disabled{{background:#777;cursor:wait}} .action.secondary{{background:var(--ink)}} .muted{{color:var(--muted)}}
.table-wrap{{overflow:auto;background:white;border:1px solid var(--line);border-radius:10px}} table{{border-collapse:collapse;width:100%;font-size:.87rem}} th,td{{padding:10px;border-bottom:1px solid #e7e3dc;text-align:left;vertical-align:top}} th{{background:#eae6dc;position:sticky;top:0}} td a{{font-weight:800;color:var(--red)}}
.media{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}} .media img{{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:8px;background:white}} details{{margin-top:18px;border-top:1px solid var(--line);padding-top:14px}} summary{{cursor:pointer;font-weight:800}} .summary{{font-size:1.08rem}}
footer{{color:var(--muted);font-size:.9rem;margin:28px 0}}
</style></head><body><main>
<h1>Event-first defensive review</h1>
<p class="lede">Prepare a match once, review passages around football events, and export a short clip pack for discussion. The queue organizes review; it does not name a tactic.</p>
<div class="caveat">Events organize review. This tool does not infer tactical intent, pressing, defensive quality, responsibility, causality, success, or player value.</div>
<form id="review-form" method="get" aria-busy="{'true' if busy else 'false'}"><input type="hidden" name="run" value="1">
<div class="controls">
<label>Match{_select('game', [('1','Metrica Sample Game 1'),('2','Metrica Sample Game 2')], str(request.game))}</label>
<label>Defending perspective{_select('defending_side', [('both','Both teams'),('Home','Home'),('Away','Away')], request.defending_side)}</label>
<label>Football moment{_select('event_choice', [('shots_goals','Shots and goals'),('shots','Shots excluding goals'),('goals','Goals only'),('possession_changes','Possession changes')], request.event_choice)}</label>
<label>Seconds before{_select('pre_seconds', [(str(int(v)),f'{int(v)} seconds') for v in WINDOW_CHOICES], str(int(request.pre_seconds)))}</label>
<label>Seconds after{_select('post_seconds', [(str(int(v)),f'{int(v)} seconds') for v in WINDOW_CHOICES], str(int(request.post_seconds)))}</label>
<label>Queue order{_select('rank_by', list(RANK_CHOICES.items()), request.rank_by)}</label>
<label>Results<input type="number" name="limit" min="1" max="10" value="{request.limit}"></label>
</div><button id="prepare-button" type="submit"{' disabled' if busy else ''}>{'Preparing…' if state == 'preparing' else 'Rendering…' if state == 'rendering' else 'Prepare match review'}</button></form>
<div id="client-progress" class="progress-panel" style="display:none" role="status" aria-live="polite"><span class="spinner" aria-hidden="true"></span><div><strong>Starting match preparation…</strong><p>Please keep this page open. Repeated clicks are disabled.</p></div></div>
{(f'<div class="progress-panel" role="status" aria-live="polite"><span class="spinner" aria-hidden="true"></span><div><strong>{status_message}</strong><p>{escape(status_detail)}</p></div></div>' if busy else f'<div class="empty">{status_message}</div>' if status_message else '')}
{('<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Event time</th><th>Teams</th><th>Outcome</th><th>Score</th><th>Pitch context</th><th>Previous action</th><th>Greatest movement</th><th>' + escape(_ranking_heading(request.rank_by)) + '</th><th>Pack</th></tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table></div>' if table_rows else '')}
{('<p>' + export_action + '</p>' if table_rows else '')}
{detail}
<footer>Local prototype · generated packages stay outside Git · exact score definitions and units remain in the analyst appendix.</footer>
<script>document.getElementById('review-form').addEventListener('submit',function(){{const button=document.getElementById('prepare-button');button.disabled=true;button.textContent='Preparing…';document.getElementById('client-progress').style.display='flex';}});</script>
</main></body></html>"""


def _request_query(request: DashboardRequest) -> str:
    return (
        f"game={request.game}&defending_side={quote(request.defending_side)}&"
        f"event_choice={quote(request.event_choice)}&pre_seconds={request.pre_seconds:g}&"
        f"post_seconds={request.post_seconds:g}&rank_by={quote(request.rank_by)}&"
        f"limit={request.limit}"
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
            if parsed.path == "/export":
                try:
                    slug = query.get("package", [""])[0]
                    package = (output_root / slug).resolve()
                    if package.parent != output_root or not package_ready(package):
                        raise ValueError("unknown prepared package")
                    ranks = tuple(
                        int(value) for value in query.get("ranks", [""])[0].split(",") if value
                    )
                    archive = export_review_pack(
                        package, ranks, output_root / "exports" / f"{slug}_review_pack"
                    )
                    payload = archive.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f'attachment; filename="{archive.name}"')
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (ValueError, OSError) as exc:
                    self.send_error(400, str(exc))
                return
            error = ""
            try:
                request = request_from_query(query)
                package = output_root / request.slug
                selected_rank = int(query.get("selected", ["1"])[0])
                picked = tuple(
                    int(value) for value in query.get("picked", [""])[0].split(",") if value
                )
                if query.get("run") == ["1"]:
                    expected = expected_cache_manifest(request.game, data_root)
                    cache_ready = prepared_match_ready(
                        match_cache_path(output_root, request.game), expected
                    )
                    query_ready = current_query_package(
                        package, _manifest_identity(expected)
                    )
                    active_state = package_status(package).get("state")
                    if (
                        active_state not in {"preparing", "rendering"}
                        and (not cache_ready or not query_ready)
                    ):
                        start_prepare_job(
                            request, output_root=output_root, data_root=data_root
                        )
                view = build_review_view_model(package, selected_rank=selected_rank)
                render_requested = query.get("render") == ["1"]
                retry_requested = query.get("retry_render") == ["1"]
                if package_ready(package) and (render_requested or retry_requested):
                    selected = view.get("selected")
                    artifacts = selected.get("artifacts", {}) if isinstance(selected, Mapping) else {}
                    existing_status = package_status(package)
                    may_start = existing_status.get("state") != "error" or retry_requested
                    if not artifacts.get("gif") and may_start:
                        start_render_job(
                            request, selected_rank, output_root=output_root, data_root=data_root
                        )
                status = package_status(package)
                if status["state"] in {"preparing", "rendering", "error"}:
                    view = {
                        **view,
                        "status": status["state"],
                        "message": status["message"],
                        "status_detail": status.get("detail", ""),
                    }
            except (ValueError, RuntimeError) as exc:
                request = DashboardRequest()
                view = {"status": "error", "message": "", "rows": [], "selected": None}
                error = f"Review could not run: {exc}"
                picked = ()
            payload = render_dashboard_html(request, view, error=error, picked=picked).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                return

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
