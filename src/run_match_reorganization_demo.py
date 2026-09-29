"""Build the current analyst demo from closed public application packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd

from match_reorganization_review import analyze_match_reorganization
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


def run_demo(output_dir: Path, *, data_root: Path | None = None, render_media: bool = False) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"output destination already exists: {output_dir}")
    expected_root = (ROOT / "data") if data_root is None else data_root
    if data_root is not None:
        for game in (1, 2):
            required = expected_root / f"metrica_sample_game_{game}"
            if not required.is_dir():
                raise FileNotFoundError(
                    f"missing public Metrica Sample Game {game}: {required}; see REPRODUCE.md"
                )

    ball_manifest = _load_manifest(BALL_MANIFEST)
    attacker_manifest = _load_manifest(ATTACKER_MANIFEST)
    links = [
        {"match_id": "metrica_sample_game_2", **row}
        for row in attacker_manifest["top_rapid_magnitude"]
    ]
    review = analyze_match_reorganization(
        _records(ball_manifest), links,
        metadata={"match": "Metrica Sample Game 2", "media_rendered": render_media},
    )
    output_dir.mkdir(parents=True)
    groups = [("Representative", review.representative_examples.copy(deep=True)),
              ("Diagnostic", review.diagnostic_examples.copy(deep=True)),
              ("Rejected", review.rejected_examples.copy(deep=True))]
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
            if not render_media or role == "Rejected":
                continue
            manifest_path = BALL_MANIFEST if row.ballward_stratum == "high_ballward" else ATTACKER_MANIFEST
            payload = ball_manifest if manifest_path == BALL_MANIFEST else attacker_manifest
            token = f"_{str(row.team_key).split(':')[-1].lower()}_p{int(row.period)}_{float(row.peak_time_s):.2f}"
            matched = {}
            for name in payload["files_sha256"]:
                suffix = Path(name).suffix.lower()
                if token not in name or suffix not in {".png", ".gif"}:
                    continue
                if suffix in matched:
                    raise RuntimeError("ambiguous governed media identity")
                destination = media_dir / name
                shutil.copyfile(manifest_path.parent / name, destination)
                matched[suffix] = str(destination.relative_to(output_dir))
                copied_media.append(matched[suffix])
            if set(matched) != {".png", ".gif"}:
                raise RuntimeError("selected example lacks governed media")
            frame.at[index, "static_path"] = matched[".png"]
            frame.at[index, "gif_path"] = matched[".gif"]
            frame.at[index, "media_status"] = "supported"
        _write_frame(frame, output_dir / f"{role.lower()}_examples.csv")
    detailed = review.rapid_episodes.copy(deep=True)
    detailed["media_status"] = "not_rendered"
    for _, frame in groups:
        for _, row in frame.iterrows():
            mask = (detailed.team_key.eq(row.team_key) & detailed.period.eq(row.period)
                    & detailed.peak_time_s.eq(row.peak_time_s))
            for field in ("ball_alignment_support_status", "media_status", "static_path", "gif_path"):
                detailed.loc[mask, field] = row[field]
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
        "media_copied": copied_media,
        "index": "analyst_review_index.html",
        "presentation_limitations": [
            "Historical media durations and link overlays reused unchanged",
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
        "status": "NAVIGATION_READY_MEDIA_POLISH_INCOMPLETE",
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
