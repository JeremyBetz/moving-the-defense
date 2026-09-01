"""Small, read-only helpers for governed research execution and closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT = ROOT / "config/execution_governance_checkpoint.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def verify_checkpoint(manifest: Path = DEFAULT_CHECKPOINT, root: Path = ROOT) -> dict[str, Any]:
    config = load_json(manifest)
    files = []
    passed = True
    for relative, expected in sorted(config.get("required_sha256", {}).items()):
        path = root / relative
        actual = sha256(path) if path.is_file() else None
        ok = actual == expected
        passed &= ok
        files.append({"path": relative, "expected": expected, "actual": actual, "pass": ok})
    forbidden = []
    for pattern in config.get("forbidden_output_globs", []):
        matches = sorted(str(path.relative_to(root)) for path in root.glob(pattern))
        ok = not matches
        passed &= ok
        forbidden.append({"pattern": pattern, "matches": matches, "pass": ok})
    return {
        "pass": passed,
        "checkpoint_commit": config.get("checkpoint_commit"),
        "scientific_state": config.get("scientific_state"),
        "files": files,
        "forbidden_outputs": forbidden,
    }


def verify_hash_ledger(directory: Path, ledger: Path) -> dict[str, Any]:
    entries = load_json(ledger)
    rows = []
    passed = True
    for relative, expected in sorted(entries.items()):
        path = directory / relative
        actual = sha256(path) if path.is_file() else None
        ok = actual == expected
        passed &= ok
        rows.append({"path": relative, "expected": expected, "actual": actual, "pass": ok})
    return {"pass": passed, "count": len(rows), "files": rows}


def repository_state(root: Path = ROOT) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, text=True, capture_output=True
        ).stdout.strip()
    branch = git("branch", "--show-current")
    status = git("status", "--porcelain")
    remote = git("remote", "get-url", "origin")
    counts = git("rev-list", "--left-right", "--count", "origin/main...main").split()
    return {
        "branch": branch,
        "clean": not status,
        "origin": remote,
        "behind_origin_main": int(counts[0]),
        "ahead_of_origin_main": int(counts[1]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    checkpoint = sub.add_parser("verify-checkpoint")
    checkpoint.add_argument("--manifest", type=Path, default=DEFAULT_CHECKPOINT)
    ledger = sub.add_parser("verify-ledger")
    ledger.add_argument("directory", type=Path)
    ledger.add_argument("ledger", type=Path)
    sub.add_parser("repo-state")
    args = parser.parse_args()
    if args.command == "verify-checkpoint":
        result = verify_checkpoint(args.manifest)
    elif args.command == "verify-ledger":
        result = verify_hash_ledger(args.directory, args.ledger)
    else:
        result = repository_state()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("pass") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
