"""Execute the frozen attacker-linked off-ball application review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import Normalize
from mplsoccer import Pitch
import numpy as np
import pandas as pd

from attacker_linked_reorganization_review import (
    AttackerLinkedReviewSpec,
    LinkReferenceThresholds,
    classify_episode_links,
    derive_reference_thresholds,
    rank_attacker_linked_episodes,
    summarize_off_ball_attackers,
    summarize_pair_geometry,
)
from ball_alignment_reorganization_review import (
    TrajectoryIntegritySpec,
    _centered_mean,
    reference_ballward_thresholds,
    select_ball_alignment_review,
)
from run_ball_alignment_reorganization_review import (
    _alignment_row,
    _game_review,
    _load_population,
)
from run_metrica_game2_application import GOALKEEPERS


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "attacker_linked_off_ball_reorganization_review_v1.json"
PROTOCOL = ROOT / "docs" / "protocols" / "attacker_linked_off_ball_reorganization_review_v1.md"
DEFAULT_OUTPUT = Path("/tmp/moving_the_defense_attacker_linked_review")


class EpisodeSupportError(RuntimeError):
    """A candidate lacks the complete player/ball support required by the freeze."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path = CONFIG) -> dict[str, object]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "FROZEN_BEFORE_ATTACKER_LINK_REFERENCE_OR_CANDIDATE_INSPECTION":
        raise RuntimeError("attacker-linked review is not frozen")
    for section in ("source_sha256", "dependency_sha256"):
        for relative, expected in config[section].items():
            if sha256(ROOT / relative) != expected:
                raise RuntimeError(f"frozen hash mismatch: {relative}")
    manifests = {
        "v1": ROOT / "figures/presentation/full_match_application_case_study/manifest.json",
        "v2": ROOT / "figures/presentation/possession_aware_defensive_review/manifest.json",
        "v3": ROOT / "figures/presentation/rapid_change_defensive_review/manifest.json",
        "v4": ROOT / "figures/presentation/ball_alignment_reorganization_review/manifest.json",
    }
    for label, manifest in manifests.items():
        if sha256(manifest) != config["historical_manifest_sha256"][label]:
            raise RuntimeError(f"historical {label} manifest changed")
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for name, expected in payload.get("files_sha256", {}).items():
            if sha256(manifest.parent / name) != expected:
                raise RuntimeError(f"historical {label} media changed: {name}")
    return config


def _require_open_play(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen open-play candidate boundary without altering rows."""
    if "rapid_context" not in frame.columns:
        raise RuntimeError("rapid candidate table is missing rapid_context")
    return frame.loc[frame["rapid_context"].eq("open_play")].copy()


def _smoothed_cube(
    tracking: pd.DataFrame,
    *,
    match_id: str,
    period: int,
    team_key: str,
    peak_time_s: float,
    excluded_player_key: str,
    spec: AttackerLinkedReviewSpec,
) -> tuple[np.ndarray, tuple[str, ...]]:
    start = peak_time_s - spec.window_seconds - (spec.smoothing_frames // 2) / spec.source_fps
    end = peak_time_s + (spec.smoothing_frames // 2) / spec.source_fps
    q = tracking.loc[
        tracking["match_id"].astype(str).eq(str(match_id))
        & tracking["period"].eq(int(period))
        & tracking["entity_type"].eq("player")
        & tracking["team_key"].astype(str).eq(str(team_key))
        & ~tracking["player_key"].astype(str).eq(str(excluded_player_key))
        & tracking["time_match_s"].between(start - 1e-7, end + 1e-7)
    ].copy()
    expected_raw = spec.expected_positions + spec.smoothing_frames - 1
    complete_keys = []
    for key, group in q.groupby("player_key", sort=True):
        valid = group["coordinate_valid"].astype(bool) & np.isfinite(
            group[["x_m", "y_m"]].to_numpy(float)
        ).all(axis=1)
        if (
            len(group) == expected_raw
            and group["frame_id_provider"].nunique() == expected_raw
            and bool(valid.all())
        ):
            complete_keys.append(str(key))
    keys = tuple(sorted(complete_keys))
    q = q.loc[q["player_key"].astype(str).isin(keys)].copy()
    if len(keys) != 10 or q.duplicated(["frame_id_provider", "player_key"]).any():
        raise EpisodeSupportError("episode lacks ten stable player identities")
    frames = q[["frame_id_provider", "time_match_s"]].drop_duplicates().sort_values(
        ["time_match_s", "frame_id_provider"], kind="mergesort"
    )
    if len(frames) != expected_raw:
        raise EpisodeSupportError("episode lacks complete raw smoothing support")
    times = frames["time_match_s"].to_numpy(float)
    if not np.allclose(np.diff(times), 1 / spec.source_fps, atol=1e-7, rtol=0):
        raise EpisodeSupportError("episode cadence is irregular")
    cube = np.full((len(frames), 10, 2), np.nan)
    frame_index = {value: index for index, value in enumerate(frames.frame_id_provider)}
    key_index = {value: index for index, value in enumerate(keys)}
    for row in q.itertuples(index=False):
        if not bool(row.coordinate_valid):
            raise EpisodeSupportError("episode contains invalid coordinates")
        cube[frame_index[row.frame_id_provider], key_index[str(row.player_key)]] = [row.x_m, row.y_m]
    if not np.isfinite(cube).all():
        raise EpisodeSupportError("episode contains missing coordinates")
    return _centered_mean(cube, spec.smoothing_frames), keys


def _smoothed_ball(
    ball: pd.DataFrame, *, match_id: str, period: int, peak_time_s: float,
    spec: AttackerLinkedReviewSpec,
) -> np.ndarray:
    half = (spec.smoothing_frames // 2) / spec.source_fps
    start, end = peak_time_s - spec.window_seconds - half, peak_time_s + half
    q = ball.loc[
        ball["match_id"].astype(str).eq(str(match_id))
        & ball["period"].eq(int(period))
        & ball["entity_type"].eq("ball")
        & ball["time_match_s"].between(start - 1e-7, end + 1e-7)
    ].sort_values(["time_match_s", "frame_id_provider"], kind="mergesort")
    if q.duplicated(["frame_id_provider"]).any() or len(q) != spec.expected_positions + spec.smoothing_frames - 1:
        raise EpisodeSupportError("episode lacks complete ball support")
    xy = q[["x_m", "y_m"]].to_numpy(float)
    if not q["coordinate_valid"].astype(bool).all() or not np.isfinite(xy).all():
        raise EpisodeSupportError("episode ball support is invalid")
    return _centered_mean(xy, spec.smoothing_frames)


def _episode_inputs(game: int, row: pd.Series, tracking_by_team, ball, scores_by_team, spec):
    defending = str(row.team_key)
    attacking = "metrica:Away" if defending == "metrica:Home" else "metrica:Home"
    match_id, period, peak = str(row.match_id), int(row.period), float(row.peak_time_s)
    attacker_xy, attacker_keys = _smoothed_cube(
        tracking_by_team[attacking], match_id=match_id, period=period,
        team_key=attacking, peak_time_s=peak, excluded_player_key=GOALKEEPERS[attacking], spec=spec,
    )
    defender_xy, defender_keys = _smoothed_cube(
        tracking_by_team[defending], match_id=match_id, period=period,
        team_key=defending, peak_time_s=peak, excluded_player_key=GOALKEEPERS[defending], spec=spec,
    )
    ball_xy = _smoothed_ball(ball, match_id=match_id, period=period, peak_time_s=peak, spec=spec)
    stored = scores_by_team[defending].player_scores
    values = stored.loc[
        stored["match_id"].astype(str).eq(match_id)
        & stored["period"].eq(period)
        & np.isclose(stored["time_match_s"], peak, atol=1e-7, rtol=0)
        & stored["player_key"].astype(str).isin(defender_keys)
    ].set_index("player_key")["trailing_relative_path_m"].reindex(defender_keys)
    contributions = values.to_numpy(float)
    if not np.isfinite(contributions).all() or len(contributions) != 10:
        raise EpisodeSupportError("episode lacks ten stored defender contributions")
    attackers = summarize_off_ball_attackers(attacker_xy, ball_xy, attacker_keys, spec=spec)
    pairs = summarize_pair_geometry(
        attacker_xy, defender_xy, attacker_keys, defender_keys, contributions, attackers, spec=spec
    )
    return {
        "attacking_team": attacking, "defending_team": defending,
        "attacker_xy": attacker_xy, "attacker_keys": attacker_keys,
        "defender_xy": defender_xy, "defender_keys": defender_keys,
        "ball_xy": ball_xy, "contributions": contributions,
        "attackers": attackers, "pairs": pairs,
    }


def _low_candidates(game, tracking_by_team, ball, events, reference, spec):
    analysis, possession, rapid = _game_review(game, reference, tracking_by_team, events)
    rows = []
    integrity_spec = TrajectoryIntegritySpec()
    for _, row in rapid.classified_increases.iterrows():
        rows.append(_alignment_row(
            row, tracking_by_team=tracking_by_team, ball=ball,
            scores_by_team=analysis.scores_by_team, integrity=True, spec=integrity_spec,
        ))
    annotated = pd.DataFrame(rows)
    # Rebuild the closed ballward reference thresholds before selecting the unchanged low stratum.
    return analysis, annotated


def _public_episode(row: pd.Series, linkage, attacker_labels: pd.DataFrame) -> dict[str, object]:
    eligible = attacker_labels.loc[attacker_labels.off_ball_eligible].sort_values(
        ["attacker_path_m", "attacker_key"], ascending=[False, True], kind="mergesort"
    )
    return {
        "team_key": str(row.team_key), "period": int(row.period),
        "peak_time_s": float(row.peak_time_s),
        "one_second_change_m": float(row.one_second_change_m),
        "team_score_m": float(row.team_score_m),
        "reference_percentile": float(row.reference_percentile),
        "team_ballward_projection_share": float(row.team_ballward_projection_share),
        "team_signed_ball_alignment": float(row.team_signed_ball_alignment),
        "eligible_off_ball_attacker_count": int(linkage.metadata["eligible_off_ball_attacker_count"]),
        "maximum_eligible_attacker_path_m": float(linkage.metadata["maximum_eligible_attacker_path_m"]),
        "top_eligible_attacker_paths_m": [round(float(v), 10) for v in eligible.attacker_path_m.head(3)],
        "strong_link_count": int(linkage.metadata["strong_link_count"]),
        "linked_defender_count": int(linkage.metadata["linked_defender_count"]),
        "linkage_category": linkage.category,
        "rapid_context": str(row.rapid_context),
        "continuous_out_of_possession_s": float(row.continuous_out_of_possession_s),
        "trajectory_integrity_status": str(row.trajectory_integrity_status),
    }


def _render_selected(row, inputs, linkage, output: Path, stem: str, spec: AttackerLinkedReviewSpec) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    attacker_order = linkage.attacker_summary.sort_values(
        ["attacker_path_m", "attacker_key"], ascending=[False, True], kind="mergesort"
    )
    defender_order = sorted(
        range(10), key=lambda i: (-inputs["contributions"][i], inputs["defender_keys"][i])
    )
    alabel = {key: f"A{i+1}" for i, key in enumerate(attacker_order.attacker_key)}
    dlabel = {inputs["defender_keys"][idx]: f"D{i+1}" for i, idx in enumerate(defender_order)}
    aindex = {key: i for i, key in enumerate(inputs["attacker_keys"])}
    dindex = {key: i for i, key in enumerate(inputs["defender_keys"])}
    strong = linkage.strong_links
    pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68,
                  pitch_color="#315d3a", line_color="#f5f5f0")

    def draw(ax, frame: int, *, title: str):
        pitch.draw(ax=ax)
        for key in attacker_order.loc[attacker_order.off_ball_eligible, "attacker_key"]:
            i = aindex[key]
            xy = inputs["attacker_xy"][:, i]
            ax.plot(xy[:, 0] + 52.5, xy[:, 1] + 34, color="#2468b4", lw=1.8, alpha=.75)
        ax.scatter(inputs["attacker_xy"][frame, :, 0] + 52.5, inputs["attacker_xy"][frame, :, 1] + 34,
                   c="#2468b4", edgecolors="white", s=55, zorder=4)
        norm = Normalize(0, 6.25)
        colors = plt.get_cmap("YlOrRd")(norm(inputs["contributions"]))
        ax.scatter(inputs["defender_xy"][frame, :, 0] + 52.5, inputs["defender_xy"][frame, :, 1] + 34,
                   c=colors, edgecolors="#202124", s=70, zorder=5)
        ax.plot(inputs["ball_xy"][:, 0] + 52.5, inputs["ball_xy"][:, 1] + 34,
                color="white", lw=1.2, alpha=.8)
        ax.scatter([inputs["ball_xy"][frame, 0] + 52.5], [inputs["ball_xy"][frame, 1] + 34],
                   c="white", edgecolors="#202124", s=28, zorder=7)
        for link in strong.itertuples(index=False):
            ai, di = aindex[str(link.attacker_key)], dindex[str(link.defender_key)]
            ax.plot([inputs["attacker_xy"][frame, ai, 0] + 52.5, inputs["defender_xy"][frame, di, 0] + 52.5],
                    [inputs["attacker_xy"][frame, ai, 1] + 34, inputs["defender_xy"][frame, di, 1] + 34],
                    color="#f5f5f0", lw=.9, alpha=.65, zorder=3)
        if frame == len(inputs["attacker_xy"]) - 1:
            for key in attacker_order.loc[attacker_order.off_ball_eligible, "attacker_key"]:
                i = aindex[key]
                ax.text(inputs["attacker_xy"][frame, i, 0] + 52.8, inputs["attacker_xy"][frame, i, 1] + 34.3,
                        alabel[key], color="white", fontsize=7, zorder=9)
            for idx in defender_order[:3]:
                key = inputs["defender_keys"][idx]
                ax.text(inputs["defender_xy"][frame, idx, 0] + 52.8, inputs["defender_xy"][frame, idx, 1] + 34.3,
                        dlabel[key], color="#111111", fontsize=7, zorder=9)
        ax.set_title(title, fontsize=10)

    title = (
        f"{linkage.category.title()} attacker linkage · rapid +{float(row.one_second_change_m):.2f} m · "
        f"ballward share {float(row.team_ballward_projection_share):.2f} · "
        f"{len(strong)} strong links"
    )
    png = output / f"{stem}_diagnostic.png"
    fig, ax = plt.subplots(figsize=(9, 5.8))
    draw(ax, len(inputs["attacker_xy"]) - 1, title=title)
    fig.text(.5, .015, "Episode-local labels only · linked means frozen geometric co-occurrence, not causation or marking",
             ha="center", fontsize=8)
    fig.savefig(png, dpi=150, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)

    gif = output / f"{stem}.gif"
    fig, ax = plt.subplots(figsize=(9, 5.8))
    def update(frame):
        ax.clear(); draw(ax, frame, title=title + f" · t {frame/spec.source_fps-2:+.2f} s")
        return []
    animation = FuncAnimation(fig, update, frames=range(0, spec.expected_positions, 2), interval=80, blit=False)
    animation.save(gif, writer=PillowWriter(fps=12.5))
    plt.close(fig)
    return [png, gif]


def execute(output_dir: Path = DEFAULT_OUTPUT, *, render_media: bool = True) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"output destination already exists: {output_dir}")
    config = load_config()
    spec = AttackerLinkedReviewSpec()
    reference, tracking_by_game, ball_by_game, events_by_game = _load_population()
    analyses, low_by_game = {}, {}
    all_alignment_values = []
    annotated_by_game = {}
    for game in (1, 2):
        analysis, annotated = _low_candidates(
            game, tracking_by_game[game], ball_by_game[game], events_by_game[game], reference, spec
        )
        analyses[game], annotated_by_game[game] = analysis, annotated
        all_alignment_values.extend(
            annotated.loc[annotated.ball_alignment_support_status.eq("supported"),
                          "team_ballward_projection_share"].tolist()
        )
    closed = reference_ballward_thresholds(all_alignment_values)
    for game in (1, 2):
        _, low, _, _ = select_ball_alignment_review(
            annotated_by_game[game], p25=closed["p25"], p75=closed["p75"]
        )
        low_by_game[game] = _require_open_play(low)

    # Stage 1: anonymous reference arrays only.
    attacker_reference, pair_reference = [], []
    reference_support_exclusions = {"game1": 0, "game2": 0}
    for game in (1, 2):
        for _, row in low_by_game[game].iterrows():
            try:
                inputs = _episode_inputs(
                    game, row, tracking_by_game[game], ball_by_game[game],
                    analyses[game].scores_by_team, spec,
                )
            except EpisodeSupportError:
                reference_support_exclusions[f"game{game}"] += 1
                continue
            eligible = inputs["attackers"].loc[inputs["attackers"].off_ball_eligible]
            attacker_reference.extend(eligible.attacker_path_m.tolist())
            pair_reference.extend(
                inputs["pairs"].loc[
                    inputs["pairs"].attacker_off_ball_eligible
                    & inputs["pairs"].defender_top_three,
                    "relative_vector_path_m",
                ].tolist()
            )
    thresholds = derive_reference_thresholds(attacker_reference, pair_reference)
    output_dir.mkdir(parents=True)
    gate = {
        "status": "REFERENCE_THRESHOLDS_FROZEN_BEFORE_GAME2_CANDIDATE_EXPOSURE",
        "attacker_path_p75_m": thresholds.attacker_path_p75_m,
        "relative_vector_path_p75_m": thresholds.relative_vector_path_p75_m,
        "attacker_count": thresholds.attacker_count,
        "pair_count": thresholds.pair_count,
        "support_exclusions": reference_support_exclusions,
        "quantile_method": "numpy_linear",
        "protocol_sha256": sha256(PROTOCOL), "config_sha256": sha256(CONFIG),
    }
    gate_path = output_dir / "reference_thresholds.json"
    gate_path.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate_loaded = LinkReferenceThresholds(
        gate["attacker_path_p75_m"], gate["relative_vector_path_p75_m"],
        gate["attacker_count"], gate["pair_count"],
    )

    # Stage 2: evaluate Game 2 only after loading the threshold gate.
    episode_rows, local = [], {}
    game2_candidate_support_exclusions = 0
    for _, row in low_by_game[2].iterrows():
        try:
            inputs = _episode_inputs(
                2, row, tracking_by_game[2], ball_by_game[2], analyses[2].scores_by_team, spec
            )
        except EpisodeSupportError:
            game2_candidate_support_exclusions += 1
            continue
        linkage = classify_episode_links(inputs["attackers"], inputs["pairs"], gate_loaded, spec=spec)
        public = _public_episode(row, linkage, inputs["attackers"])
        episode_rows.append(public)
        local[(public["team_key"], public["period"], public["peak_time_s"])] = (row, inputs, linkage)
    episodes = pd.DataFrame(episode_rows)
    rankings = rank_attacker_linked_episodes(episodes)

    public_dir = output_dir / "public"
    public_dir.mkdir()
    audit_path = public_dir / "episode_audit.csv"
    episodes.sort_values(["period", "peak_time_s", "team_key"], kind="mergesort").to_csv(
        audit_path, index=False, float_format="%.10f"
    )
    media = []
    if render_media:
        for row in rankings.public_examples.itertuples(index=False):
            key = (str(row.team_key), int(row.period), float(row.peak_time_s))
            source_row, inputs, linkage = local[key]
            stem = f"{row.linkage_category}_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            media.extend(_render_selected(source_row, inputs, linkage, public_dir, stem, spec))

    def records(frame, rank_name):
        keep = list(episodes.columns) + ([rank_name] if rank_name in frame.columns else [])
        return frame.loc[:, [c for c in keep if c in frame.columns]].head(10).to_dict(orient="records")

    historical = episodes.loc[
        episodes.team_key.eq("metrica:Home") & episodes.period.eq(2)
        & np.isclose(episodes.peak_time_s, 4443.16, atol=1e-7, rtol=0)
    ]
    if len(historical) != 1:
        raise RuntimeError("historical low-ballward example did not reconcile")
    governed = [gate_path, audit_path, *media]
    manifest = {
        "artifact_id": "attacker_linked_off_ball_reorganization_review_v1",
        "status": "ATTACKER_LINKED_REVIEW_COMPLETE",
        "created": "2026-09-28",
        "protocol": "docs/protocols/attacker_linked_off_ball_reorganization_review_v1.md",
        "reference_thresholds": gate,
        "low_ballward_candidate_count": int(len(episodes)),
        "game2_candidate_support_exclusion_count": game2_candidate_support_exclusions,
        "category_counts": {str(k): int(v) for k, v in episodes.linkage_category.value_counts().sort_index().items()},
        "historical_home_p2_4443_16": historical.iloc[0].to_dict(),
        "top_rapid_magnitude": records(rankings.rapid_ranking, "rapid_rank"),
        "top_off_ball_movement": records(rankings.movement_ranking, "movement_rank"),
        "top_link_density": records(rankings.density_ranking, "density_rank"),
        "selected_public_examples": rankings.public_examples.to_dict(orient="records"),
        "files_sha256": {path.name: sha256(path) for path in sorted(governed)},
        "historical_manifest_sha256": config["historical_manifest_sha256"],
        "qc": {
            "thresholds_frozen_before_candidate_exposure": True,
            "stable_provider_identities_public": False,
            "coordinates_or_pair_rows_public": False,
            "historical_packages_unchanged": True,
            "raw_scores_and_rapid_selection_unchanged": True,
        },
        "claim_boundary": "descriptive co-occurrence only; no causal, marking, tactical, quality, intent, space-creation, or value interpretation",
    }
    manifest_path = public_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-media", action="store_true")
    args = parser.parse_args()
    print(json.dumps(execute(args.output_dir, render_media=not args.no_media), indent=2, default=str))


if __name__ == "__main__":
    main()
