"""Build the current analyst demo from closed public application packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from match_reorganization_review import MatchReorganizationReview
from analyst_review_index import write_index


ROOT = Path(__file__).resolve().parents[1]
BALL_MANIFEST = ROOT / "figures/presentation/ball_alignment_reorganization_review/manifest.json"
ATTACKER_MANIFEST = ROOT / "figures/presentation/attacker_linked_reorganization_review/manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for name, expected in payload["files_sha256"].items():
        artifact = path.parent / name
        if not artifact.is_file() or _sha256(artifact) != expected:
            raise RuntimeError(f"closed application artifact mismatch: {artifact}")
    return payload


def _records(manifest: dict[str, object]) -> list[dict[str, object]]:
    rows: dict[tuple[object, ...], dict[str, object]] = {}
    for field in ("historical_six_audit", "top_overall", "top_low_ballward", "top_high_ballward"):
        for row in manifest.get(field, []):
            key = ("metrica_sample_game_2", row["team_key"], row["period"], row["peak_time_s"])
            rows[key] = {"match_id": key[0], **row}
    return list(rows.values())


def _write_frame(frame: pd.DataFrame, path: Path) -> None:
    serial = frame.copy()
    for column in serial.columns:
        serial[column] = serial[column].map(
            lambda value: json.dumps(value) if isinstance(value, (list, tuple, dict)) else value
        )
    serial.to_csv(path, index=False, float_format="%.10f")


def frozen_demo_review(ball, attacker):
    """Hydrate the five explicitly authorized identities, without candidate ranking."""
    identities = [(2, 5355.64), (1, 336.76), (2, 4443.16), (1, 978.32), (1, 1734.72)]
    rows = []
    for period, time in identities:
        matches = [r for field in ("historical_six_audit", "top_overall", "top_low_ballward", "top_high_ballward")
                   for r in ball.get(field, []) if r['period'] == period and r['peak_time_s'] == time and r['team_key'] == 'metrica:Home']
        linked = [r for r in attacker['top_rapid_magnitude'] if r['period'] == period and r['peak_time_s'] == time and r['team_key'] == 'metrica:Home']
        if not matches and not linked:
            raise RuntimeError('missing frozen demo identity')
        authorities = matches + linked
        for field in ('period', 'peak_time_s', 'team_key', 'team_score_m',
                      'one_second_change_m', 'reference_percentile',
                      'trajectory_integrity_status', 'team_ballward_projection_share',
                      'team_signed_ball_alignment', 'rapid_context',
                      'continuous_out_of_possession_s'):
            values = [r[field] for r in authorities if field in r]
            if values and any(
                not (math.isclose(v, values[0], rel_tol=1e-9, abs_tol=1e-8)
                     if isinstance(v, (int, float)) else v == values[0])
                for v in values[1:]
            ):
                raise RuntimeError(f'closed selected-record mismatch: {field}')
        row = dict(matches[-1] if matches else linked[0])
        row.update(match_id='metrica_sample_game_2', attacker_link_status='not_evaluated',
                   maximum_off_ball_attacker_path_m=None, strong_link_count=None, linkage_category='not_evaluated',
                   media_status='not_requested', static_path=None, gif_path=None)
        if linked:
            row.update(attacker_link_status='supported', maximum_off_ball_attacker_path_m=linked[0]['maximum_eligible_attacker_path_m'],
                       strong_link_count=linked[0]['strong_link_count'], linkage_category=linked[0]['linkage_category'])
            row.setdefault('ballward_stratum', 'low_ballward')
        row.setdefault('possession_state', 'out_of_possession')
        row.setdefault('top_three_player_raw_paths_m', None)
        row['trajectory_integrity_reason'] = 'none' if row['trajectory_integrity_status'] == 'trajectory_integrity_clean' else 'impossible_native_speed'
        rows.append(row)
    frame = pd.DataFrame(rows)
    return MatchReorganizationReview(frame, frame.iloc[:2], frame.iloc[2:4], frame.iloc[4:],
                                    {'measurement':'team relational reorganization'})


def run_demo(output_dir: Path, *, data_root: Path | None = None, render_media: bool = False) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"output destination already exists: {output_dir}")
    expected_root = (ROOT / "data") if data_root is None else data_root
    if render_media:
        for game in (2,):
            required = expected_root / f"metrica_sample_game_{game}"
            if not required.is_dir():
                raise FileNotFoundError(
                    f"missing public Metrica Sample Game {game}: {required}; see REPRODUCE.md"
                )

    ball_manifest = _load_manifest(BALL_MANIFEST)
    attacker_manifest = _load_manifest(ATTACKER_MANIFEST)
    review = frozen_demo_review(ball_manifest, attacker_manifest)
    output_dir.mkdir(parents=True)
    groups = [("Representative", review.representative_examples.copy(deep=True)),
              ("Diagnostic", review.diagnostic_examples.copy(deep=True)),
              ("Rejected", review.rejected_examples.copy(deep=True))]
    recovered = {}
    if render_media:
        from selected_window_demo import AUTHORIZED, recover, render_detail
        selected = pd.concat([frame for _, frame in groups], ignore_index=True)
        if set(zip(selected.period.astype(int),selected.peak_time_s.astype(float))) != AUTHORIZED or len(selected) != 5:
            raise RuntimeError('frozen demo selection changed')
        # Recovery uses only these already-closed selections; no scanner or reference rebuild.
        for _, row in selected.iterrows():
            key = (int(row.period),float(row.peak_time_s))
            recovered[key] = recover(row,expected_root,ball_manifest)
        (output_dir / 'selected_window_cache.json').write_text(json.dumps({
            'status':'CONSISTENCY_PASSED', 'kind':'application/demo derivative; not scientific result; not selection input',
            'episodes':[detail['cache'] for detail in recovered.values()],
        },indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    copied_media: list[str] = []
    for role, frame in groups:
        media_dir = output_dir / f"{role.lower()}_examples"
        media_dir.mkdir()
        for index, row in frame.iterrows():
            failed = row.trajectory_integrity_status != "trajectory_integrity_clean"
            frame.at[index, "ball_alignment_support_status"] = (
                "integrity_failed" if failed else
                "unsupported" if row.ballward_stratum == "unsupported" else "supported"
            )
            frame.at[index, "media_status"] = "not_rendered"
            if not render_media:
                continue
            detail = recovered[(int(row.period),float(row.peak_time_s))]
            frame.at[index,'top_three_player_raw_paths_m'] = detail['cache']['top_three_contributions_m']
            png,gif = render_detail(row,detail,media_dir)
            frame.at[index,'static_path'] = str(png.relative_to(output_dir))
            frame.at[index,'gif_path'] = str(gif.relative_to(output_dir))
            frame.at[index,'media_status'] = 'integrity_failed' if failed else 'supported'
            copied_media.extend([str(png.relative_to(output_dir)),str(gif.relative_to(output_dir))])
        _write_frame(frame, output_dir / f"{role.lower()}_examples.csv")
    detailed = review.rapid_episodes.copy(deep=True)
    detailed["media_status"] = "not_rendered"
    for _, frame in groups:
        for _, row in frame.iterrows():
            mask = (detailed.team_key.eq(row.team_key) & detailed.period.eq(row.period)
                    & detailed.peak_time_s.eq(row.peak_time_s))
            for field in ("ball_alignment_support_status", "media_status", "static_path", "gif_path", "top_three_player_raw_paths_m"):
                for idx in detailed.index[mask]:
                    detailed.at[idx, field] = row[field]
    _write_frame(detailed, output_dir / "rapid_episodes.csv")
    _write_frame(detailed, output_dir / "detailed_episode_table.csv")
    write_index(output_dir, groups)
    summary = {
        "status": "MATCH_REORGANIZATION_DEMO_COMPLETE",
        "measurement": review.metadata["measurement"],
        "source": "hash-validated closed public application packages",
        "rapid_episode_count": len(review.rapid_episodes),
        "representative_example_count": len(review.representative_examples),
        "diagnostic_example_count": len(review.diagnostic_examples),
        "rejected_example_count": len(review.rejected_examples),
        "media_rendered": copied_media,
        "index": "analyst_review_index.html",
        "presentation_limitations": [] if render_media else [
            "No provider data read; media not rendered",
            "Contributor values absent from closed summaries remain not_evaluated",
        ],
        "claim_boundary": "descriptive analyst review; no causal, tactical, marking, quality or value interpretation",
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    (output_dir / "manifest.json").write_text(json.dumps({
        "source_manifests_sha256": {
            "ball_alignment": _sha256(BALL_MANIFEST), "attacker_linked": _sha256(ATTACKER_MANIFEST)},
        "files_sha256": {str(path.relative_to(output_dir)): _sha256(path) for path in files},
        "status": "SELECTED_WINDOW_MEDIA_COMPLETE" if render_media else "DATA_FREE_REVIEW",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=int, default=2, choices=(2,))
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render-media", action="store_true")
    parser.add_argument("--no-media", action="store_true")
    args = parser.parse_args()
    if args.render_media and args.no_media:
        parser.error("choose either --render-media or --no-media")
    result = run_demo(
        args.output_dir, data_root=args.data_root, render_media=args.render_media
    )
    print(f"Review complete.\nOpen:\n  {args.output_dir.resolve() / 'analyst_review_index.html'}")
    print(f"Representative: {result['representative_example_count']}\n"
          f"Diagnostic: {result['diagnostic_example_count']}\nRejected: {result['rejected_example_count']}")


if __name__ == "__main__":
    main()
