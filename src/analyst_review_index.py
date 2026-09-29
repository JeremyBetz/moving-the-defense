"""Portable presentation of frozen example queues; no scoring or selection."""
from __future__ import annotations

from html import escape
from pathlib import Path
import math

import pandas as pd

COMPACT_COLUMNS = (
    "Category", "Period", "Time (s)", "Evaluated team", "Rapid change (m)",
    "Reorganization level (m)", "Context", "Integrity", "Ball alignment support",
    "Ballward stratum", "Ballward share", "Off-ball linkage", "Top defender contributors",
    "Media status", "Static", "GIF",
)


def number(value, digits=2):
    try:
        return f"{float(value):.{digits}f}" if math.isfinite(float(value)) else "not_evaluated"
    except (TypeError, ValueError):
        return "not_evaluated"


def text(value, default="not_evaluated"):
    return default if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)


def describe(row, role):
    if role == "Rejected":
        return ("REJECTED — trajectory integrity failure", "rejected / integrity failure",
                "Impossible native-frame movement detected. Retained only to demonstrate QC; never valid analyst evidence.")
    if role == "Representative" and row.get("ballward_stratum") == "high_ballward":
        return ("Representative — high-ballward contrast", text(row.get("rapid_context")).replace("_", " "),
                "A rapid rise with substantial movement directed toward the ball. Review alongside the low-ballward example.")
    if role == "Representative":
        return ("Representative — low-ballward, localized attacker-linked", text(row.get("rapid_context")).replace("_", " "),
                "A rapid rise with low ballward alignment and localized co-occurring off-ball geometry. Rapid change and absolute level are different quantities.")
    if row.get("linkage_category") == "distributed":
        return ("Diagnostic — goalkeeper-distribution special context", "goalkeeper distribution / shape reset",
                "Known context of this closed Game 2 example. An advanced context example; geometric links do not establish marking or cause.")
    return ("Diagnostic — low-ballward, no strong attacker link", text(row.get("rapid_context")).replace("_", " "),
            "Method contrast: no pair meets all frozen strong-link rules. Zero links does not mean no attacker movement.")


def compact_row(row, role):
    label, context, _ = describe(row, role)
    rejected = role == "Rejected"
    paths = row.get("top_three_player_raw_paths_m")
    contributions = (
        " · ".join(f"#{i+1}: {number(v)} m" for i, v in enumerate(paths))
        if isinstance(paths, (tuple, list)) and len(paths) == 3
        else "not_evaluated — absent from closed summary"
    )
    linkage = text(row.get("attacker_link_status"))
    if rejected:
        linkage = "integrity_failed"
    elif linkage == "supported":
        linkage = f"supported — {text(row.get('linkage_category'))}; {number(row.get('strong_link_count'), 0)} links"
    return dict(zip(COMPACT_COLUMNS, (
        label, str(int(row["period"])), number(row["peak_time_s"]),
        str(row["team_key"]).split(":")[-1], number(row["one_second_change_m"]),
        number(row["team_score_m"]), context,
        "integrity_failed — impossible native-frame movement detected" if rejected else "supported — trajectory clean",
        "integrity_failed" if rejected else text(row.get("ball_alignment_support_status")),
        "not_applicable" if rejected else text(row.get("ballward_stratum")),
        "not_applicable" if rejected else number(row.get("team_ballward_projection_share"), 3),
        linkage, contributions, text(row.get("media_status")),
        text(row.get("static_path"), "not_rendered"), text(row.get("gif_path"), "not_rendered"),
    )))


def write_index(destination: Path, groups):
    rows, sections = [], []
    for role, frame in groups:
        cards = []
        for _, row in frame.iterrows():
            compact = compact_row(row, role)
            rows.append(compact)
            label, _, interpretation = describe(row, role)
            cells = []
            for key in COMPACT_COLUMNS:
                value = compact[key]
                if key in {"Static", "GIF"} and value not in {"not_rendered", "not_applicable"}:
                    path = Path(value)
                    if path.is_absolute() or ".." in path.parts or not (destination / path).is_file():
                        raise ValueError("media link must resolve inside the review package")
                    value = f'<a href="{escape(value, quote=True)}">Open {key}</a>'
                else:
                    value = escape(value)
                cells.append(f"<td>{value}</td>")
            table = '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{escape(k)}</th>' for k in COMPACT_COLUMNS) + '</tr></thead><tbody><tr>' + ''.join(cells) + '</tr></tbody></table></div>'
            media = ""
            if role != "Rejected" and text(row.get("static_path"), "not_rendered") != "not_rendered":
                media = f'<a href="{escape(str(row["gif_path"]), quote=True)}"><img loading="lazy" src="{escape(str(row["static_path"]), quote=True)}" alt="{escape(label, quote=True)} — static diagnostic; open GIF"></a>'
            cue = ("QC failure — exclude from football interpretation" if role == "Rejected" else
                   f"Ballward: {compact['Ballward stratum'].replace('_ballward', '').upper()} ({compact['Ballward share']})")
            actions = ""
            for key in ("Static", "GIF"):
                if compact[key] != "not_rendered":
                    actions += f'<a href="{escape(compact[key], quote=True)}">Open {key}</a> · '
            cards.append(f'<article class="{role.lower()}"><h3>{escape(label)}</h3><p>{escape(interpretation)}</p><p><strong>{escape(cue)}</strong> · Period {compact["Period"]} · {compact["Time (s)"]} s · {escape(compact["Evaluated team"])}</p><p>{actions or "Media: not_rendered"}</p>{table}{media}</article>')
        sections.append(f'<section id="{role.lower()}"><h2>{role} ({len(frame)})</h2>{"".join(cards)}</section>')
    pd.DataFrame(rows, columns=COMPACT_COLUMNS).to_csv(destination / "compact_episode_review.csv", index=False)
    document = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Match reorganization review</title><style>
body{font:16px/1.55 system-ui,sans-serif;color:#17212b;background:#f3f5f7;margin:0 auto;padding:24px;max-width:1200px}h1,h2,h3{line-height:1.2}a{color:#124b91}nav{display:flex;gap:20px;flex-wrap:wrap}article{background:white;border-left:5px solid #286c90;padding:20px;margin:20px 0;border-radius:6px}.diagnostic{border-color:#987000}.rejected{border-color:#aa2020;background:#fff1f1}.scroll{overflow:auto}table{border-collapse:collapse;font-size:14px}th,td{padding:10px;border-bottom:1px solid #cdd4db;text-align:left;min-width:100px}img{max-width:100%;height:auto;margin-top:16px}aside{padding:16px;background:#e5edf4}
</style></head><body><h1>Match reorganization review</h1>
<p>Find moments when the defending unit's movement relative to teammates increased sharply, then inspect ball orientation and off-ball attacker movement. Metres remain the measurement; a reference percentile is descriptive context.</p>
<aside>Representative = valid default review example. Diagnostic = valid special context or method contrast. Rejected = failed QC, never valid analyst evidence. This retrospective tracking review does not establish cause, marking, tactical success or player value.</aside>
<nav><a href="#representative">Representative</a><a href="#diagnostic">Diagnostic</a><a href="#rejected">Rejected QC</a><a href="compact_episode_review.csv">Compact CSV</a><a href="detailed_episode_table.csv">Detailed CSV</a><a href="summary.json">Summary</a></nav>
<p>Ballward LOW/HIGH labels and shares use the frozen classification. Defender colors show trailing two-second relative path. Historical media retain their original duration and overlays; linked clips span two seconds and ball-alignment clips ten seconds. Missing closed-summary details are explicitly marked.</p>
''' + ''.join(sections) + '</body></html>\n'
    (destination / "analyst_review_index.html").write_text(document, encoding="utf-8")
