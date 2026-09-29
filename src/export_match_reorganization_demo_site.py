"""Export the frozen analyst presentation only; no provider access or analysis."""
from __future__ import annotations

import argparse
import csv
import hashlib
from html import escape
from html.parser import HTMLParser
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/p1_demo_public_asset_allowlist_v1.md"
VERSION = "1.0.0"
REPOSITORY = "https://github.com/JeremyBetz/moving-the-defense"
LINKS = {
    "Repository": REPOSITORY,
    "README": REPOSITORY + "/blob/main/README.md",
    "Reproduce the paper": REPOSITORY + "/blob/main/REPRODUCE.md",
    "Technical API and demo guide": REPOSITORY + "/blob/main/docs/replay_scoring_api.md",
    "Paper submission candidate": REPOSITORY + "/blob/main/submission/SSAC27_abstract_candidate_v1.pdf",
    "Metrica Sports sample data": "https://github.com/metrica-sports/sample-data",
}
PUBLIC_FIELDS = {
    "category", "period", "timestamp_s", "evaluated_team", "rapid_change_m",
    "reorganization_level_m", "context_label", "integrity_status", "ballward_stratum",
    "ballward_share", "attacker_link_category", "total_strong_link_count",
    "top_three_defender_contributions_m",
}
TITLE = "Moving the Defense — Analyst Demo"
SUBTITLE = "Exploratory application of the defensive relational-reorganization framework."
BOUNDARY = "Descriptive review only. Does not infer marking, causation, tactical success, or player value."
STYLES = """/* Self-contained presentation; no external fonts or runtime. */
:root{color-scheme:light;--ink:#173039;--muted:#4a6168;--paper:#f3f5f1;--line:#cbd6ce;--accent:#176151}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:48px 28px}h1,h2,h3{line-height:1.18;letter-spacing:-.025em}h1{font-size:clamp(2rem,5vw,3.7rem);max-width:850px;margin:.4em 0}h2{font-size:1.7rem;margin-top:2rem}h3{font-size:1.35rem;margin:.4em 0}
a{color:#075b78;text-underline-offset:3px;overflow-wrap:anywhere}a:focus-visible,summary:focus-visible{outline:3px solid #d07717;outline-offset:4px}.eyebrow{font-size:.8rem;font-weight:750;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}.subtitle{font-size:1.15rem;color:var(--muted);max-width:800px}
.boundary{border-left:5px solid var(--accent);padding:16px 20px;background:#e1ebe4;border-radius:0 8px 8px 0}.nav{display:flex;gap:12px 24px;flex-wrap:wrap;margin:24px 0}.workflow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;padding:0;list-style:none}.workflow li{border-top:3px solid var(--line);padding-top:10px}.workflow strong{display:block}.workflow span{font-size:.93rem;color:var(--muted)}
.card{background:white;border:1px solid var(--line);border-radius:12px;margin:22px 0;padding:24px;overflow:hidden}.tag{display:inline-block;background:#e1ebe4;border-radius:4px;padding:3px 9px;font-weight:700;font-size:.8rem}.meta{color:var(--muted);font-size:.95rem}.interpretation{max-width:850px}.media{display:block;margin:20px 0 8px}.media img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:6px}.media-links{display:flex;flex-wrap:wrap;gap:12px 22px;font-size:.94rem}
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:24px 0 12px}.metrics div{min-width:0;background:#f3f6f3;padding:12px;border-radius:6px}.metrics dt{font-size:.82rem;color:var(--muted)}.metrics dd{margin:3px 0 0;font-weight:650;overflow-wrap:anywhere}.note{font-size:.9rem;color:var(--muted)}details{border:1px solid var(--line);border-radius:10px;background:#fafbf8;margin:20px 0;padding:18px}summary{font-weight:750;cursor:pointer}.diagnostic .tag{background:#f5e9c8}.rejected{border-color:#b97c82;background:#fff8f8}.rejected .tag{background:#842c39;color:white}.rejected .card{border-color:#c9979c}.rejected .metrics div{background:#faedef}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e7ece6;padding:18px;border-radius:8px;font-size:.85rem}footer{border-top:1px solid var(--line);padding-top:20px;margin-top:36px;font-size:.9rem;color:var(--muted)}
@media(max-width:680px){main{padding:24px 16px}.workflow{grid-template-columns:1fr 1fr}.card{padding:16px}.metrics{grid-template-columns:1fr 1fr}details{padding:12px}h2{font-size:1.45rem}}
@media(max-width:380px){.metrics,.workflow{grid-template-columns:1fr}}
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_name(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("unsafe relative path")
    parts = value.split("/")
    if PurePosixPath(value).is_absolute() or any(p in {"", ".", ".."} for p in parts):
        raise ValueError("unsafe relative path")
    return value


def inventory(root: Path) -> set[str]:
    """Enumerate names to reject extras, never to discover files to copy."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("package must be a regular directory")
    result = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("symlinks and special files are prohibited")
        result.add(relative_name(path.relative_to(root).as_posix()))
    return result


def expected_inventory(files) -> set[str]:
    result = {relative_name(name) for name in files}
    for name in list(result):
        result.update(str(p) for p in PurePosixPath(name).parents if str(p) != ".")
    return result


def committed_identity(path: Path) -> dict[str, str]:
    name = path.relative_to(ROOT).as_posix()
    revision = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", name], cwd=ROOT, text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("export requires committed source and protocol")
    committed = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
    if committed != path.read_bytes():
        raise ValueError("export source or protocol differs from its committed revision")
    return {"commit": revision, "sha256": hashlib.sha256(committed).hexdigest()}


def load_contract() -> dict:
    committed_identity(PROTOCOL)
    blocks = re.findall(r"```json\n(.*?)\n```", PROTOCOL.read_text(encoding="utf-8"), re.S)
    if len(blocks) != 1:
        raise ValueError("expected one machine-readable allowlist")
    contract = json.loads(blocks[0])
    if contract["version"] != "p1-demo-public-assets-v1" or set(contract["public_fields"]) != PUBLIC_FIELDS:
        raise ValueError("unsupported publication contract")
    if len(contract["assets"]) != 8 or len(contract["examples"]) != 5 or sum(e["public"] for e in contract["examples"]) != 4:
        raise ValueError("unexpected allowlist cardinality")
    for asset in contract["assets"]:
        for field in ("source", "destination"):
            relative_name(asset[field])
        if Path(asset["destination"]).suffix not in {".png", ".gif"}:
            raise ValueError("unapproved asset extension")
    return contract


def finite_number(value) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite metric")
    return number


def integer(value) -> int:
    number = finite_number(value)
    if not number.is_integer():
        raise ValueError("expected integer")
    return int(number)


def project_metrics(row: dict, example: dict) -> dict:
    """Explicit projection; no source row is ever serialized to the public site."""
    rejected = example["role"] == "rejected"
    expected_integrity = "trajectory_integrity_failed" if rejected else "trajectory_integrity_clean"
    if row["trajectory_integrity_status"] != expected_integrity:
        raise ValueError("integrity/classification mismatch")
    expected_support = "integrity_failed" if rejected else "supported"
    if row["media_status"] != expected_support or row["ball_alignment_support_status"] != expected_support:
        raise ValueError("missing expected support")
    if row["rapid_context"] != "open_play" or row["possession_state"] != "out_of_possession":
        raise ValueError("unexpected closed context")
    if not rejected:
        if row["ballward_stratum"] != example["stratum"] or row["linkage_category"] != example["linkage"]:
            raise ValueError("ball/link classification mismatch")
        expected_link_support = "not_evaluated" if example["linkage"] == "not_evaluated" else "supported"
        if row["attacker_link_status"] != expected_link_support:
            raise ValueError("attacker support mismatch")
    else:
        if row["trajectory_integrity_reason"] != "impossible_native_speed" or row["attacker_link_status"] != "not_evaluated":
            raise ValueError("rejected example has invalid downstream interpretation")
    count = example["link_count"]
    if isinstance(count, int):
        if integer(row["strong_link_count"]) != count:
            raise ValueError("strong-link count mismatch")
    elif row["strong_link_count"]:
        raise ValueError("unsupported link count must remain unavailable")
    contributions = json.loads(row["top_three_player_raw_paths_m"])
    if not isinstance(contributions, list) or len(contributions) != 3:
        raise ValueError("missing top-three contributions")
    contributions = [finite_number(v) for v in contributions]
    share = "integrity_failed" if rejected else finite_number(row["team_ballward_projection_share"])
    if not rejected and not 0 <= share <= 1:
        raise ValueError("ballward share outside range")
    if min(contributions) < 0 or contributions != sorted(contributions, reverse=True):
        raise ValueError("invalid contribution ordering")
    context = ("rejected / integrity failure" if rejected else
               "goalkeeper-distribution special context" if example["role"] == "diagnostic" and example["public"] else
               "open play (event-derived context)")
    result = {
        "category": example["role"], "period": example["period"],
        "timestamp_s": example["timestamp_s"], "evaluated_team": "Home",
        "rapid_change_m": finite_number(row["one_second_change_m"]),
        "reorganization_level_m": finite_number(row["team_score_m"]),
        "context_label": context, "integrity_status": "integrity_failed" if rejected else "trajectory_integrity_clean",
        "ballward_stratum": example["stratum"], "ballward_share": share,
        "attacker_link_category": example["linkage"], "total_strong_link_count": count,
        "top_three_defender_contributions_m": contributions,
    }
    if result["rapid_change_m"] <= 0 or result["reorganization_level_m"] < 0:
        raise ValueError("invalid selected movement summary")
    return result


def validate_input(root: Path, contract: dict) -> list[dict]:
    if inventory(root) != expected_inventory(contract["input_files"]):
        raise ValueError("unexpected or missing input file/directory")
    if sha256(root / "manifest.json") != contract["source_manifest_sha256"]:
        raise ValueError("source manifest hash mismatch")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "SELECTED_WINDOW_MEDIA_COMPLETE":
        raise ValueError("source package is not complete")
    files = manifest["files_sha256"]
    if set(files) != set(contract["input_files"]) - {"manifest.json"}:
        raise ValueError("source manifest inventory mismatch")
    for name, digest in files.items():
        relative_name(name)
        if sha256(root / name) != digest:
            raise ValueError(f"source file hash mismatch: {name}")
    for asset in contract["assets"]:
        if files[asset["source"]] != asset["sha256"]:
            raise ValueError("asset differs from frozen publication allowlist")
    rows = {}
    for role in ("representative", "diagnostic", "rejected"):
        with (root / f"{role}_examples.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = (integer(row["period"]), finite_number(row["peak_time_s"]))
                if key in rows or row["team_key"] != "metrica:Home" or row["match_id"] != "metrica_sample_game_2":
                    raise ValueError("duplicate or unexpected episode identity")
                stem = f"{role}_examples/home_p{key[0]}_{key[1]:.2f}"
                if relative_name(row["static_path"]) != stem + ".png" or relative_name(row["gif_path"]) != stem + ".gif":
                    raise ValueError("episode asset path mismatch")
                rows[key] = (role, row)
    if set(rows) != {(e["period"], e["timestamp_s"]) for e in contract["examples"]}:
        raise ValueError("frozen five-example identity mismatch")
    projected = []
    for example in contract["examples"]:
        role, row = rows[(example["period"], example["timestamp_s"])]
        if role != example["role"]:
            raise ValueError("episode role mismatch")
        metrics = project_metrics(row, example)
        if example["public"]:
            projected.append(metrics)
    return projected


def label_and_copy(metrics: dict) -> tuple[str, str]:
    if metrics["category"] == "rejected":
        return "REJECTED — trajectory integrity failure", "Impossible native-frame movement detected. This is a QC lesson only; the displayed measurements must not be interpreted as valid football evidence."
    if metrics["category"] == "diagnostic":
        return "Goalkeeper-distribution special context", "An advanced example with 12 qualifying spatial links; the replay displays only the three highest-priority links. The context label is inherited from prior review, not inferred by this page."
    if metrics["ballward_stratum"] == "high_ballward":
        return "Movement oriented toward the ball", "A rapid increase accompanied by substantial ballward movement orientation. Compare it with the low-ballward example; attacker linkage was not evaluated here."
    return "Low-ballward movement with off-ball spatial linkage", "A rapid increase co-occurs with off-ball attacker movement and two qualifying spatial links. Those links describe geometry, not marking assignments or attacker influence."


def display(value) -> str:
    if isinstance(value, (float, int)):
        return f"{value:.2f}"
    return str(value).replace("_", " ")


def card(metrics: dict) -> str:
    title, interpretation = label_and_copy(metrics)
    role = metrics["category"]
    stem = f"assets/{role}/home_p{metrics['period']}_{metrics['timestamp_s']:.2f}"
    values = [
        ("One-second increase", display(metrics["rapid_change_m"]) + " m"),
        ("Selected team reorganization", display(metrics["reorganization_level_m"]) + " m"),
        ("Trajectory integrity", display(metrics["integrity_status"])),
        ("Ballward stratum", display(metrics["ballward_stratum"])),
        ("Ballward share", f"{metrics['ballward_share']:.3f}" if isinstance(metrics["ballward_share"], float) else display(metrics["ballward_share"])),
        ("Off-ball linkage", display(metrics["attacker_link_category"])),
        ("Total qualifying links", str(metrics["total_strong_link_count"]).replace("_", " ")),
        ("Selected defender contributions", " · ".join(f"#{i+1}: {v:.2f} m" for i, v in enumerate(metrics["top_three_defender_contributions_m"]))),
    ]
    cells = "".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in values)
    return f'''<article class="card {role}" data-category="{role}">
<span class="tag">{escape(role.upper() if role == 'rejected' else role.title())}</span>
<h3>{escape(title)}</h3><p class="meta">Home · Period {metrics['period']} · {metrics['timestamp_s']:.2f} s · {escape(metrics['context_label'])}</p>
<p class="interpretation">{escape(interpretation)}</p>
<picture class="media"><source media="(prefers-reduced-motion: reduce)" srcset="{stem}.png"><img src="{stem}.gif" width="1000" height="700" loading="lazy" alt="{escape(title)} — ten-second tracking replay"></picture>
<div class="media-links"><a href="{stem}.png">Open static diagnostic</a><a href="{stem}.gif">Open GIF</a></div>
<dl class="metrics">{cells}</dl></article>'''


def html_page(examples: list[dict]) -> str:
    representatives = "".join(card(e) for e in examples if e["category"] == "representative")
    diagnostic = "".join(card(e) for e in examples if e["category"] == "diagnostic")
    rejected = "".join(card(e) for e in examples if e["category"] == "rejected")
    links = " · ".join(f'<a href="{url}">{escape(label)}</a>' for label, url in LINKS.items() if label != "Metrica Sports sample data")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{TITLE}</title><link rel="stylesheet" href="styles.css"></head>
<body><main><header><p class="eyebrow">Football tracking · exploratory analyst application</p><h1>{TITLE}</h1><p class="subtitle">{SUBTITLE}</p><p class="boundary">{BOUNDARY}</p></header>
<nav class="nav" aria-label="Demo sections"><a href="#representatives">Representative examples</a><a href="#diagnostic">Advanced diagnostic</a><a href="#qc">Rejected QC</a><a href="#reproduce">Reproduce</a></nav>
<section aria-labelledby="what"><h2 id="what">What this shows</h2><ol class="workflow">
<li><strong>1. Rapid reorganization</strong><span>Find an increase in movement relative to teammates over one second.</span></li>
<li><strong>2. Trajectory integrity</strong><span>Exclude implausible tracking before football interpretation.</span></li>
<li><strong>3. Ball alignment</strong><span>Describe how much of that movement is oriented toward the ball.</span></li>
<li><strong>4. Off-ball context</strong><span>Inspect concurrent attacker movement and qualifying spatial links.</span></li></ol>
<p>The team measure is the mean trailing two-second defender-relative path across ten outfield defenders, in metres. A large value is not a rating of defending. These are fixed review examples, not a live analysis service.</p>
<p class="note">Retrospective centered smoothing needs tracking through 0.12 seconds after the displayed time. Each clip adds five seconds of visual context on either side; selected measurements still use their frozen intervals. The fixed 0–6.25 m colour ceiling affects display only; larger raw values remain unchanged. A reference percentile shown in a clip is descriptive context, not a probability or performance rating. Clip source span: 10.00 s; encoded GIF duration: 10.08 s.</p></section>
<section id="representatives"><h2>Representative examples</h2>{representatives}</section>
<details id="diagnostic" class="diagnostic"><summary>Advanced diagnostic — goalkeeper-distribution special context</summary>{diagnostic}</details>
<details id="qc" class="rejected"><summary>REJECTED — trajectory integrity failure · QC lesson only</summary><p>Impossible native-frame movement detected. This passage is excluded from valid analyst recommendations.</p>{rejected}</details>
<section><h2>Paper versus demo</h2><p>The paper studies off-ball movement direction and localized defensive reorganization using frozen scientific evidence. This demo is a separate exploratory application. Its illustrative passages add no inferential evidence and establish no causal or tactical mechanism.</p></section>
<section id="reproduce"><h2>Reproduce and inspect</h2><p>{links}</p>
<p>From the reviewed application checkout, build the data-free local review with:</p><pre><code>.venv/bin/python src/run_match_reorganization_demo.py --game 2 --output-dir review-output --no-media</code></pre>
<p>The API guide documents the public Metrica prerequisites and bounded media route. This static export needs only the already-verified presentation package, not tracking files. <a href="manifest.json">Inspect public provenance and hashes</a>.</p></section>
<footer>Tracking data: <a href="{LINKS['Metrica Sports sample data']}">Metrica Sports sample data</a>. Animation rendered by Moving the Defense; no original match video is included. These tracking-derived images permit approximate positional recovery; they are not anonymized raw data or a general redistribution grant.</footer>
</main></body></html>
'''


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "iframe", "object", "embed", "base", "form"}:
            raise ValueError("unexpected runtime or embedded content")
        for name, value in attrs:
            if name.startswith("on"):
                raise ValueError("event handlers are prohibited")
            if name in {"href", "src", "srcset"}:
                self.links.append(value)


def validate_site(root: Path, contract: dict, expected_examples: list[dict], provenance: dict) -> None:
    payloads = {"index.html", "styles.css", *(a["destination"] for a in contract["assets"])}
    if inventory(root) != expected_inventory(payloads | {"manifest.json"}):
        raise ValueError("unexpected public file/directory")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if set(manifest) != {"status", "exporter", "source_demo_head", "source_manifest_sha256", "allowlist_sha256", "examples", "media", "files_sha256"}:
        raise ValueError("unexpected public manifest fields")
    if manifest["status"] != "PREPARED_NOT_DEPLOYED" or manifest["exporter"] != provenance:
        raise ValueError("public provenance mismatch")
    if manifest["source_demo_head"] != contract["source_demo_head"] or manifest["source_manifest_sha256"] != contract["source_manifest_sha256"] or manifest["allowlist_sha256"] != sha256(PROTOCOL):
        raise ValueError("public lineage mismatch")
    if manifest["examples"] != expected_examples or any(set(e) != PUBLIC_FIELDS for e in manifest["examples"]):
        raise ValueError("public metric schema/content mismatch")
    expected_media = [{"source": a["source"], "source_sha256": a["sha256"], "destination": a["destination"], "exported_sha256": a["sha256"]} for a in contract["assets"]]
    if manifest["media"] != expected_media or set(manifest["files_sha256"]) != payloads:
        raise ValueError("public media/hash schema mismatch")
    for name, digest in manifest["files_sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError("public file hash mismatch")
    for asset in contract["assets"]:
        if sha256(root / asset["destination"]) != asset["sha256"]:
            raise ValueError("copied media mismatch")
    if (root / "index.html").read_text(encoding="utf-8") != html_page(expected_examples) or (root / "styles.css").read_text(encoding="utf-8") != STYLES:
        raise ValueError("public presentation mismatch")
    for name in ("index.html", "styles.css", "manifest.json"):
        content = (root / name).read_text(encoding="utf-8")
        if any(token in content for token in ("/Users/", "/private/", "/tmp/", "file://", "player_key", "attacker_key", "defender_key", "978.32")):
            raise ValueError("private or unapproved public content")
    parser = PageLinks()
    parser.feed((root / "index.html").read_text(encoding="utf-8"))
    for link in parser.links:
        if link in LINKS.values() or link.startswith("#"):
            continue
        relative_name(link)
        if link not in payloads | {"manifest.json"} or not (root / link).is_file():
            raise ValueError("unapproved or broken public link")


def export_site(demo_root: Path, output_dir: Path) -> dict:
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError("output destination already exists")
    contract = load_contract()
    examples = validate_input(demo_root, contract)
    provenance = {"version": VERSION, **committed_identity(Path(__file__))}
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".p1-demo-export-", dir=output_dir.parent) as temporary:
        staging = Path(temporary) / "site"
        staging.mkdir()
        for asset in contract["assets"]:
            destination = staging / asset["destination"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(demo_root / asset["source"], destination)
        (staging / "index.html").write_text(html_page(examples), encoding="utf-8")
        (staging / "styles.css").write_text(STYLES, encoding="utf-8")
        payloads = ["index.html", "styles.css", *(a["destination"] for a in contract["assets"])]
        manifest = {
            "status": "PREPARED_NOT_DEPLOYED", "exporter": provenance,
            "source_demo_head": contract["source_demo_head"],
            "source_manifest_sha256": contract["source_manifest_sha256"],
            "allowlist_sha256": sha256(PROTOCOL), "examples": examples,
            "media": [{"source": a["source"], "source_sha256": a["sha256"], "destination": a["destination"], "exported_sha256": sha256(staging / a["destination"])} for a in contract["assets"]],
            "files_sha256": {name: sha256(staging / name) for name in sorted(payloads)},
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        validate_site(staging, contract, examples, provenance)
        if output_dir.exists() or output_dir.is_symlink():
            raise FileExistsError("output destination appeared during export")
        staging.rename(output_dir)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    export_site(args.demo_root, args.output_dir)
    print("Static analyst demo prepared; not deployed.")
    for name in sorted(p.relative_to(args.output_dir).as_posix() for p in args.output_dir.rglob("*") if p.is_file()):
        print(name)


if __name__ == "__main__":
    main()
