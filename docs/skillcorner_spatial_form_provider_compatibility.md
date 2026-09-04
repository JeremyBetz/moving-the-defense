# SkillCorner compatibility for Spatial Form v1

**Decision:** **A — SKILLCORNER EXTERNAL REPLICATION FEASIBLE — FREEZE**

**Audit date:** 2026-09-04

**Outcome firewall:** no SkillCorner localized defensive-reorganization target,
coefficient, interval, model, or classification was computed. DRD residuals and
Metrica Game 3 remained unopened.

## Release inventory

The official [SkillCorner Open Data release](https://github.com/SkillCorner/opendata)
at commit `c1e17a0cc3e07e1774b52d929c1a0b85115143fc` contains ten men's
2024/25 Australian A-League matches. Tracking is broadcast-derived at 10 Hz.
Native coordinates are centred metres; pitch lengths are 104--106 m and every
pitch width is 68 m. Each match supplies two periods, ball tracking, possession
team/player fields, image-coverage projection, frame-level player/ball
`is_detected` flags, lineups and playing intervals, player/team identities,
goalkeeper roles, Dynamic Events, and concurrent phase files. Phase files are
defined only while the ball is in play; this audit uses only their interval
coverage, never their tactical labels.

The release itself warns that some points are erroneous, player identity is
approximately 97% accurate, and speed/acceleration QC is needed. SkillCorner
describes the product as full-player broadcast tracking that extrapolates
off-screen positions. Provider environment replication is therefore useful,
but it is not replication with identical measurement technology.

## Outcome-blind support audit

All tracking objects were downloaded to temporary ignored storage and matched
to the official Git LFS SHA-256 identifiers before parsing. The audit used only
metadata, raw support, ball-in-play intervals, coordinate/status continuity,
and prospective anchors. It did not construct the target.

One release entry, `1953632`, reports top-level status `not_started` despite
complete two-period files. It is excluded prospectively rather than manually
overridden. Nine matches remain potentially valid:

| Match | Primary-support anchors | Rows before identity gate | Rows after 15 m/s identity gate | Majority-detected sensitivity rows |
|---|---:|---:|---:|---:|
| 1886347 | 630 | 5,670 | 5,670 | 1,526 |
| 1899585 | 565 | 5,085 | 5,083 | 1,066 |
| 1925299 | 730 | 6,570 | 6,570 | 1,305 |
| 1996435 | 663 | 5,967 | 5,967 | 2,559 |
| 2006229 | 644 | 5,796 | 5,795 | 2,278 |
| 2011166 | 503 | 4,527 | 4,509 | 625 |
| 2013725 | 608 | 5,472 | 5,470 | 945 |
| 2015213 | 572 | 5,148 | 5,134 | 807 |
| 2017461 | 543 | 4,887 | 4,886 | 701 |
| **Total** | **5,458** | **49,122** | **49,084** | **11,812** |

These are support counts, not results. They are allowed to change only if the
frozen implementation reveals a mechanical discrepancy; no coefficient may be
read before correction and refreeze.

Detected-only full-team paths are infeasible. Across all ten release matches,
only 49 prospective primary anchors had every current outfielder detected over
the complete support window. The provider's detected-plus-extrapolated feed is
therefore primary, with flags retained and a stricter majority-detected
sensitivity. Direct-detection rates vary by pitch region, reinforcing the need
to preserve status rather than treat extrapolation as invisible missingness.

All formal matches have 22 starters, two goalkeeper identities, substitution
playing intervals, and no reported dismissals. Every player record used in the
audit had a Boolean status and mapped to metadata. Raw adjacent-step checks
found a small number of impossible player jumps in several matches; the frozen
15 m/s continuity rule removes affected focal/D1--D7 windows before outcomes.
This catches obvious discontinuities but cannot certify the provider's remaining
identity assignments.

## Kloppy equivalence

Kloppy 3.19.0 supports the current V3 JSONL schema. A complete native-versus-
Kloppy check on match `1886347` covered all 59,042 period frames:

- frame IDs, period IDs, player sets, and possession team were exact;
- maximum raw player/ball coordinate difference was `0.0 m`;
- maximum period-time difference was `4.55e-13 s`;
- pitch dimensions and inferred home/away orientation were consistent.

Kloppy does **not** retain `is_detected`, image-corners projection, or possession
player ID in its tracking records. Pure Kloppy ingestion is therefore
insufficient for the support gate. The frozen architecture is:

> native SkillCorner JSONL support + Kloppy objects → governed provider adapter
> → canonical 105 × 68 m table and provenance → project-owned measurement

Future execution must repeat full equivalence on every formal match before
constructing an outcome.

## Physical-time and coordinate equivalence

The IDSSE 25 Hz frame counts are not reused. The 2 s prior, 2 s exposure, and
2 s response intervals remain physical time at native 10 Hz. The nearest
physical equivalent of the inherited 0.28 s centred smoother is frozen as a
three-frame 0.30 s centred mean. This is the only provider-specific smoothing
choice; it was made before outcomes.

Native centred metres are scaled match by match to 105 × 68 m. Goalward sign
comes from `home_team_side` by period. The entire frame is then reflected in y
when the focal attacker starts below the centre line. Outward is positive y
change under that start-fixed transform. No future coordinate determines the
sign.

## Compatibility conclusion

The construct is compatible provided native support flags remain authoritative,
the anomalous-status match stays excluded, at least eight matches pass final
equivalence, the three-frame smoother remains frozen, and identity/quality
gates are enforced. This supports protocol freeze, not execution approval or a
claim that the IDSSE result replicates.

Expected execution cost is approximately 6--10 percentage points of the weekly
allowance using Terra/high/Turbo, including implementation, 2,000 grouped
bootstrap replicates, independent reproduction, and focused QC. This estimate
is operational only and cannot change scientific rules.
