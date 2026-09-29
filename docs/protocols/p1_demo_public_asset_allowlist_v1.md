# P1 public demo asset allowlist v1

Frozen from `b7d618ea6bb0a0f3f45aff519c4903dbdf2fc204` under the explicit
static-export authorization. This is a presentation/publication contract,
not a scientific protocol or a change to example selection.

The single JSON block below is the exporter's machine-readable authority.
Its source-manifest hash binds the complete previously verified package.
The input inventory permits validation only: caches, CSVs, local HTML and the
978.32 diagnostic must never be copied into the public site. The four public
examples each permit exactly one unchanged PNG and GIF plus the listed
compact fields. No new rendering, provider access, recomputation or ranking
is authorized. Unknown files, unsafe paths, symlinks and hash failures stop
export. Existing output destinations must not be overwritten.

```json
{
  "version": "p1-demo-public-assets-v1",
  "source_demo_head": "1e3f206d39bdd476741f35dc2e4355725823343c",
  "source_manifest_sha256": "b48cb40bfb79052e952267afc5354615aade06dec3c4a5d3b2b1df6614483a4b",
  "input_files": [
    "manifest.json",
    "analyst_review_index.html",
    "compact_episode_review.csv",
    "detailed_episode_table.csv",
    "diagnostic_examples.csv",
    "diagnostic_examples/home_p1_978.32.gif",
    "diagnostic_examples/home_p1_978.32.png",
    "diagnostic_examples/home_p2_4443.16.gif",
    "diagnostic_examples/home_p2_4443.16.png",
    "rapid_episodes.csv",
    "rejected_examples.csv",
    "rejected_examples/home_p1_1734.72.gif",
    "rejected_examples/home_p1_1734.72.png",
    "representative_examples.csv",
    "representative_examples/home_p1_336.76.gif",
    "representative_examples/home_p1_336.76.png",
    "representative_examples/home_p2_5355.64.gif",
    "representative_examples/home_p2_5355.64.png",
    "selected_window_cache.json",
    "summary.json"
  ],
  "public_fields": [
    "category", "period", "timestamp_s", "evaluated_team",
    "rapid_change_m", "reorganization_level_m", "context_label",
    "integrity_status", "ballward_stratum", "ballward_share",
    "attacker_link_category", "total_strong_link_count",
    "top_three_defender_contributions_m"
  ],
  "examples": [
    {"period": 2, "timestamp_s": 5355.64, "team": "Home", "role": "representative", "public": true, "linkage": "localized", "link_count": 2, "stratum": "low_ballward"},
    {"period": 1, "timestamp_s": 336.76, "team": "Home", "role": "representative", "public": true, "linkage": "not_evaluated", "link_count": "not_evaluated", "stratum": "high_ballward"},
    {"period": 2, "timestamp_s": 4443.16, "team": "Home", "role": "diagnostic", "public": true, "linkage": "distributed", "link_count": 12, "stratum": "low_ballward"},
    {"period": 1, "timestamp_s": 978.32, "team": "Home", "role": "diagnostic", "public": false, "linkage": "none", "link_count": 0, "stratum": "low_ballward"},
    {"period": 1, "timestamp_s": 1734.72, "team": "Home", "role": "rejected", "public": true, "linkage": "integrity_failed", "link_count": "integrity_failed", "stratum": "integrity_failed"}
  ],
  "assets": [
    {"source": "representative_examples/home_p2_5355.64.png", "destination": "assets/representative/home_p2_5355.64.png", "sha256": "844a699a65c48548b5114014c41bcdc49b45c2dece0afd5e544be2b0a2e42832"},
    {"source": "representative_examples/home_p2_5355.64.gif", "destination": "assets/representative/home_p2_5355.64.gif", "sha256": "91a083330946a87a187bca3301d06dfc4beb00c3b458a72cf358ed4f42ea40e6"},
    {"source": "representative_examples/home_p1_336.76.png", "destination": "assets/representative/home_p1_336.76.png", "sha256": "15a5e468bdabc367ca6678f39eaefcda1da33b1cc5cbc215e38d5f7fbe3ae406"},
    {"source": "representative_examples/home_p1_336.76.gif", "destination": "assets/representative/home_p1_336.76.gif", "sha256": "e82aabab10f02de70982472360cd740d01e74bb9262842294e53888521346f05"},
    {"source": "diagnostic_examples/home_p2_4443.16.png", "destination": "assets/diagnostic/home_p2_4443.16.png", "sha256": "243aebde46abe92673e57b4b04d82ee0a2b2db9d607d7625ba33a19eb2373ec8"},
    {"source": "diagnostic_examples/home_p2_4443.16.gif", "destination": "assets/diagnostic/home_p2_4443.16.gif", "sha256": "e636575d4a77b3bed1a70d24c82e2486eb7e08307290991b081f17d7c2130c92"},
    {"source": "rejected_examples/home_p1_1734.72.png", "destination": "assets/rejected/home_p1_1734.72.png", "sha256": "09ff526c269b386648ef0692536f2a4cb71d2349897faa12eb24edad5b0b23e1"},
    {"source": "rejected_examples/home_p1_1734.72.gif", "destination": "assets/rejected/home_p1_1734.72.gif", "sha256": "9f04017ab69923fb8e888e7417165cb090377384804c42d73aed014a866e8896"}
  ]
}
```

## Public presentation and boundaries

Representatives are expanded. The goalkeeper-distribution diagnostic and
rejected QC example are separate, collapsed sections. Rejected downstream
fields remain explicitly integrity-failed. Missing high-ballward linkage is
not evaluated, never zero. The 978.32 diagnostic remains part of the local
package only. These visibility decisions do not change underlying categories.

Use the title “Moving the Defense — Analyst Demo”, subtitle “Exploratory
application of the defensive relational-reorganization framework.”, and top
boundary “Descriptive review only. Does not infer marking, causation, tactical
success, or player value.” Preserve the scientific/application distinction.

Only HTML, CSS, the public JSON manifest and the eight media files may appear
in the exported directory. The public manifest contains the approved fields,
relative provenance paths and hashes, never local directories, stable player
identities, coordinates, raw rows or internal linkage records. It hashes every
payload except itself, avoiding a self-referential hash. External HTTPS links
are restricted to repository/reproduction/paper resources and Metrica source
attribution; all site assets use relative links.

Tracking data: Metrica Sports sample data. Animation rendered by Moving the
Defense; no original match video is included. Retain a link to the
[official sample-data repository](https://github.com/metrica-sports/sample-data).
These media are provider-derived and permit approximate positional recovery
from pixels. This exact asset authorization is not a blanket redistribution
determination; it does not authorize raw data publication or a repository
policy exception.

The exporter consumes an already-complete package and has no scientific or
provider-loading dependency. Source demo revision denotes the verified
presentation implementation, not a newly executed scientific result. Exporter
provenance is the committed exporter version/source hash and its last-changing
commit, so later documentation commits do not change generated bytes.

No deployment workflow, settings change, push, merge or public deployment is
authorized in this pass. Any input, media, metric-field or visibility change
requires separate review rather than an automatic allowlist expansion.
