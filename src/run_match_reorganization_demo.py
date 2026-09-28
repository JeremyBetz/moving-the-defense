"""Build the current analyst demo from closed public application packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd

from match_reorganization_review import analyze_match_reorganization


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
    _write_frame(review.rapid_episodes, output_dir / "rapid_episodes.csv")
    _write_frame(review.representative_examples, output_dir / "representative_examples.csv")
    _write_frame(review.diagnostic_examples, output_dir / "diagnostic_examples.csv")
    _write_frame(review.rejected_examples, output_dir / "rejected_examples.csv")
    copied_media: list[str] = []
    if render_media:
        media_dir = output_dir / "media"
        media_dir.mkdir()
        valid = pd.concat(
            [review.representative_examples, review.diagnostic_examples], ignore_index=True
        )
        packages = (BALL_MANIFEST, ATTACKER_MANIFEST)
        for time_s in valid.peak_time_s:
            token = f"{float(time_s):.2f}"
            for manifest_path in packages:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                for name in payload["files_sha256"]:
                    if token not in name or Path(name).suffix.lower() not in {".png", ".gif"}:
                        continue
                    source = manifest_path.parent / name
                    destination = media_dir / name
                    if not destination.exists():
                        shutil.copyfile(source, destination)
                        copied_media.append(str(destination.relative_to(output_dir)))
    summary = {
        "status": "MATCH_REORGANIZATION_DEMO_COMPLETE",
        "measurement": review.metadata["measurement"],
        "source": "hash-validated closed public application packages",
        "rapid_episode_count": len(review.rapid_episodes),
        "representative_example_count": len(review.representative_examples),
        "diagnostic_example_count": len(review.diagnostic_examples),
        "rejected_example_count": len(review.rejected_examples),
        "media_copied": copied_media,
        "claim_boundary": "descriptive analyst review; no causal, tactical, marking, quality or value interpretation",
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
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
    print(json.dumps(run_demo(
        args.output_dir, data_root=args.data_root, render_media=args.render_media
    ), indent=2))


if __name__ == "__main__":
    main()
