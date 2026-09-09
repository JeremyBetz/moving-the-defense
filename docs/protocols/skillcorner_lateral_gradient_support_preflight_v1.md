# SkillCorner lateral gradient v1 — response-blind support preflight

**Status:** SUPPORT_DESIGN_FROZEN_IMPLEMENTATION_PENDING

**Design approval:** user-approved two-week science-frontier plan, 2026-09-09

**Repository baseline:** `fa87313255eb1df9b67dc1c9f34950b879c8ffe2`

**Preflight execution:** not performed; requires implementation and independent review

**Response access:** NOT AUTHORIZED

## 1. Scope and authority

This milestone freezes only the support-preflight design and implementation
contract in this protocol and its [configuration](../../config/skillcorner_lateral_gradient_support_preflight_v1.json).
It creates no extractor, provider execution, response estimate, or result report.
The next milestone is the dedicated support implementation and synthetic tests.

The scientific question motivating this preflight is whether starting farther
from the centreline is associated with larger subsequent localized defensive
reorganization in SkillCorner. The approved future A1 model is
`Y_im = alpha_m + beta_lat * abs(y_c(t-2)) + error`, with positive predicted
`beta_lat`. Here `Y` is the mean D1–D3 accumulated leave-one-out
defender-relative path minus the mean D4–D7 path over `[t,t+2]`, in metres.
The predictor is in canonical metres; the eventual coefficient is metres of
near-minus-middle path per metre of lateral starting position. A linear slope
does not establish monotonicity at every location.

This is prospective transport of an IDSSE-map-generated spatial hypothesis into
an already-used SkillCorner population. It is neither untouched-dataset
replication nor replication of an existing IDSSE lateral coefficient. The
outcome definition above is context, not permission to construct or read it.
Response-stage source, inference, classification, and execution require their
own freeze and explicit response-access gate. A2/A3 are not fallback analyses.

Inherit eligibility from the [SkillCorner external protocol](defensive_reorganization_spatial_form_v1_skillcorner_external.md),
its [configuration](../../config/defensive_reorganization_spatial_form_v1_skillcorner_external.json),
and the [canonical-rank response-blind reconciliation](defensive_reorganization_spatial_form_v1_skillcorner_external_preexecution_support_reconciliation.md).
The new branch requires all nine formal matches, not the historical minimum of
eight. The configuration binds these authorities and the inspected source
versions by SHA-256. A changed dependency requires review, not automatic rebinding.

Follow [research governance](../research_governance.md) and the
[execution policy](../execution_policy.md). Before a later execution freeze,
separately reconcile the governance document's stale unexecuted-IDSSE-map
wording using existing closure metadata only. This milestone neither edits that
document nor reopens the closed map. SkillCorner response-mode, DRD
residual/retrieval, and all Metrica Game 3 restrictions remain active.

## 2. Population and source identity

Use exactly `1886347, 1899585, 1925299, 1996435, 2006229, 2011166, 2013725,
2015213, 2017461`. Keep `1953632` excluded for the inherited provider-status
conflict. Never substitute a match or proceed with eight.

The release is SkillCorner Open Data at Git commit
`c1e17a0cc3e07e1774b52d929c1a0b85115143fc`. At authorized support execution,
verify the local `{match_id}_match.json`,
`{match_id}_tracking_extrapolated.jsonl`, and `{match_id}_phases_of_play.csv`
against their exact paths/blob identities in that pinned upstream tree. Record
SHA-256 of all 27 files before decoding and confirm those identities after
extraction. Merely hashing whatever local files happen to exist is insufficient.
Record the resolved upstream paths and blob IDs alongside the SHA-256 values.
An unavailable pinned-tree identity, mismatch, missing file, or changed file
stops execution; do not fetch a different release or silently repair inputs.
No provider file is opened, hashed, or inventoried during this design freeze.

Expected counts come only from the response-blind reconciliation:

| Match | Match-specific anchor times | Attacker–anchor observations | Majority-detected observations |
|---|---:|---:|---:|
| 1886347 | 630 | 5670 | 1529 |
| 1899585 | 565 | 5083 | 1068 |
| 1925299 | 730 | 6570 | 1305 |
| 1996435 | 663 | 5967 | 2559 |
| 2006229 | 644 | 5795 | 2278 |
| 2011166 | 503 | 4522 | 625 |
| 2013725 | 608 | 5471 | 942 |
| 2015213 | 572 | 5143 | 803 |
| 2017461 | 543 | 4886 | 701 |
| **Total** | **5458** | **49107** | **11810** |

Require each per-match count and the totals to agree. Count agreement is not
proof of historical observation-ID equality: no historical row registry may be
opened for this comparison. Generate new prospective digests in memory for the
primary and quality populations, both per match and across all nine. An ID is
`match_id:period:anchor_provider_frame:focal_player_id` with decimal integer
components. Reject duplicate IDs. Hash UTF-8 of lexicographically sorted IDs
joined by `\n`, including one final `\n` for a nonempty list (empty bytes for an
empty list). Only digests and counts may be serialized. A later response
execution must reproduce these exact IDs/digests, not just their counts.

## 3. Outcome-free extraction contract

Implement later in `src/skillcorner_lateral_gradient_support_preflight_v1.py`.
The dedicated extractor may reuse `MatchSource`, `anchor_support_reason`,
`smooth_player`, `sorted_rank_ids`, `continuity_valid`, `quality_valid`, and the
outcome-blind adapter helpers from the bound sources. `support_match()` is an
eligibility reference and count cross-check, not a source of lateral diagnostics.
Keep existing scientific modules byte-unchanged.

Never call `construct_row()`, `construct_match()`, `path_length()`, response
centroid/path construction, fitting/bootstrap functions, or the historical
module's `execute()`. In particular, do not obtain starting coordinates by
constructing a response row and dropping its outcome afterward.

Only the following source information may be used:

- Metadata: match/status, pitch dimensions, team identities, period direction,
  player identity/team/goalkeeper role, and playing-time frame boundaries.
- Tracking: frame, period, timestamp, player ID/x/y/Boolean detection status,
  ball x/y/Boolean detection status, and possession group at the anchor.
- Phase file: inclusive `frame_start`/`frame_end` union; ignore phase labels.

Native JSON decoding may materialize a whole source record when reusing the
existing reader. That is not permission to extract unrelated fields: explicitly
project the working support record, and never consult a response-bearing
registry, derived response/path/prediction/residual field, or alternative
outcome. Post-anchor coordinates may be inspected only for inherited
support/identity QC, not accumulated movement or its distribution. Local
adjacent-step threshold checks are permitted identity QC, not path outcomes.
Keep projected anchor-level records in memory only, including temporary work;
do not serialize them, log them, or expose them in exceptions.

## 4. Timing, eligibility, coordinates, and quality

Inherit native 10 Hz cadence, the centred three-frame arithmetic mean, and
period-origin anchors `start_frame + 40 + 40*k`, ending at `end_frame - 21`.
The full required raw interval is `[anchor-41, anchor+21]` inclusive. Check
native frame and timestamp consistency; never interpolate or repair gaps.

Preserve the exact inherited eligibility order: required same-period support;
expected/observed ten-outfielder rosters and finite coordinates with Boolean
status at every required frame; ball support over `[anchor-41,anchor+1]`;
continuous phase-union coverage over `[anchor-40,anchor+20]`; possession team at
the anchor; exclude the ball-nearest attacking outfielder; then focal/D1–D7
identity QC. Use metadata roles/playing intervals for rosters. Do not add a
post-anchor possession requirement or silently impose a different roster rule.

Ball-nearest and defender ranks use smoothed **canonical** coordinates at `t`,
with numeric player-ID tie-breaking. D1–D10 stay fixed at `t`. The shared
rotation/reflection inside the existing rank helper preserves distances; it
must not become a lateral reflection of the exported support predictor.
The identity gate retains the native adjacent-step maximum of 1.5 m over
0.1 s for the focal player on `[anchor-41,anchor+1]` and fixed D1–D7 on
`[anchor-1,anchor+21]`. A retained anchor may have fewer than nine focal
perspectives after row-level QC; preserve all retained perspectives.

Scale centred native coordinates before smoothing/ranking:
`x_c = 105*x_native/L`, `y_c = 68*y_native/W`.
The primary predictor is `z = abs(smoothed_y_c(anchor-20))`. Physical y is not
focal-side reflected. Goalward-signed starting x may be summarized only as
support context, using the existing metadata direction. Absolute y avoids,
but does not resolve, the exact-centreline outward-direction disagreement.

Keep all finite native out-of-pitch positions; do not clip or exclude them.
Count focal starts outside `abs(x_c)<=52.5` and `abs(y_c)<=34`, and separately
outside the lateral bounds. Boundary equality is inside. Invalid dimensions,
unknown conventions, or a suspected convention capable of manufacturing a
gradient must stop for review, not trigger data-dependent thresholds.

The inherited majority-detected subset requires fraction `>=0.5` separately
for focal player and ball on 43 raw frames `[anchor-41,anchor+1]` and each of
D1–D7 on 23 raw frames `[anchor-1,anchor+21]`. Report focal, ball, and minimum
D1–D7 fractions; detection flags do not establish coordinate accuracy.

## 5. Fixed diagnostics and feasibility gates

Compute each primary/quality sample's counts, period coverage, period-aware
block coverage, z distribution, and population variance (`ddof=0`). Quantiles
are 0.05, 0.25, 0.50, 0.75, 0.95 using NumPy's linear method; report min/max too.
Summarize detection fractions overall and within the reporting bands. Report
out-of-pitch counts and quality retention overall and by band. Optional
goalward-x context is limited to per-match/sample min, median, max.

Reporting bands are `[0,10)`, `[10,20)`, `[20,30)`, `[30,34]`, `(34,infinity)`
metres. They do not replace the continuous predictor. Distinct time anchors
are `(period,provider_frame)` within match. Blocks are
`(period,floor((anchor_frame-period_start_frame)/600))`. Do not merge periods
or count simultaneous attacker perspectives as distinct times/blocks.

Require all of the following before recommending response-stage preparation:

1. All nine sources and count checks pass, with unique observation identities.
2. Primary and quality populations each represent both periods in every match.
3. A1 predictor-only designs are full rank, overall and separately in every
   match, for both primary and quality samples.
4. In **each match**, the **quality** subset has at least **20 distinct anchor
   times** across **four period-aware blocks** in each broad region `[0,10)`,
   `[10,20)`, `[20,infinity)` m. These are distinct from the five reporting
   bands. Both-period representation is a per-match/sample gate, not an
   additional unapproved requirement in every broad region.
5. Independent support review finds no unresolved coordinate/detection/support
   issue capable of creating the gradient.

Twenty times and four blocks are prospectively approved feasibility safeguards,
not statistical laws, a power calculation, or an independence guarantee.
Unequal lateral density alone does not fail the preflight. Do not search
thresholds or lower them to rescue participation.

For outcome-free A1 design QC, use an intercept, eight match indicators (first
sorted match reference), and continuous z. Set each row's weight to `1/n_m`
within its sample. Use `A=sqrt(weight)*X`. Numerical rank uses singular values
above `max(A.shape)*float64_epsilon*largest_singular_value`; full rank is ten
pooled columns and two columns for each single-match intercept-plus-z design.
For a full-rank design, report maximum and mean leverage from rowwise squared
sums of its thin left-singular-vector matrix. No Y, coefficient, or regression
fit is required. For a deficient design, report rank failure and null leverage.
Equal total match weight is not an arithmetic mean of match slopes; lateral
variation would determine each match's slope information in the future model.

Retain the inherited first-failure exclusion reasons with their units (anchor
or attacker–anchor). An added diagnostic breakdown of roster versus coordinate
versus Boolean-status failure must be explicitly nonexclusive and must not
change eligibility/order. Never sum overlapping diagnostics as unique excluded
observations. Count ball-nearest exclusions separately as a planned design
exclusion; identity exclusions are row-level.

## 6. Aggregate publication contract

Future output root: `outputs/skillcorner_lateral_gradient_support_preflight_v1/`.
Future report: `docs/results/skillcorner_lateral_gradient_support_preflight_v1.md`.
These paths are not created by this design milestone.

The configuration freezes exact CSV column allowlists and table keys:

- `sample_summary.csv`: match × primary/quality aggregate counts,
  z/detection summaries, out-of-pitch counts, and optional x context.
- `period_summary.csv`: match × sample × period aggregate counts only.
- `lateral_support.csv`: match × sample × fixed reporting band; counts,
  temporal diversity, and mean detection fractions. Quality retention is
  derived from the paired primary/quality counts, null when primary is zero.
- `quality_region_support.csv`: match × broad region quality counts and gates.
- `exclusions.csv`: match × reason × counting unit, with exclusive/diagnostic
  classification. No candidate identity is published.
- `design_qc.csv`: sample × pooled/single-match scope; ranks and leverage only.
- `source_hashes.json`: release/commit and 27 path/blob/SHA-256 records only.
- `manifest.json`: protocol/config/source/test identities, software environment,
  authorization reference, count totals, observation-ID digests, and output list.
- `hard_qc.json`: source/count/identity/support/design/publication checks, numeric
  feasibility status, and human-review requirement; no response classification.
- `final_hashes.json`: nonrecursive hashes of the completed aggregate package
  and report, excluding itself.

Only match and period identifiers used for aggregate grouping are public.
No observation, player, or team IDs; anchor times/frames; block membership/keys;
individual x/y/z; rank rows; individual paths; Y; or response/prediction/residual
fields may be serialized. Neither per-anchor debug exports nor provider rows
may be written to temporary files. CSV column allowlists are necessary but not
sufficient: validate row-key uniqueness, expected aggregate row counts, and
aggregation from synthetic fixtures, so renamed row-level data cannot pass.
JSON writers accept only the described provenance/QC schemas, never raw
support-record dictionaries. Null represents undefined aggregate statistics;
JSON NaN/Infinity are forbidden. Non-access flags in QC are metadata, not data
fields or proof of non-access.

Use installed NumPy/Pandas and existing ingestion helpers; no new dependencies,
CI, release infrastructure, plots, SkillCorner heatmap, or model search.
Credit SkillCorner Open Data and preserve its MIT licence attribution.
Run the existing change-aware publication guard on all changed/generated files.
Passing a filename/size guard cannot prove safe table contents or non-access.

## 7. Implementation and synthetic test specification

Keep the following seams explicit in the future source; exact function names
are prescribed to make pre-access review concrete:

| Function | Contract |
|---|---|
| `verify_source_identity` | Verify nine × three files against pinned tree; return hashes, never data rows. |
| `extract_match_support` | Produce projected in-memory records through inherited support/rank/quality helpers only. |
| `observation_digest` | Reject duplicates; hash the exact canonical IDs without serialization. |
| `aggregate_support` | Produce the fixed tables with period-aware unique-time/block counts. |
| `check_support_gates` | Evaluate fixed source/count/period/rank/region gates without outcomes. |
| `validate_public_outputs` | Enforce columns, grouping/cardinality, JSON contracts, and no row exports. |
| `execute_support` | Require explicit support gate, verify dependencies, extract, aggregate, validate and write only approved outputs. |

Normal import, `--help`, and `--verify-freeze` must not open provider files.
Future execution requires `--execute-support`, explicit local data directory,
and nonempty `--authorization-reference`, after independent review. A supplied
reference is provenance metadata, not independent proof of human approval.
There is no response execution option in the preflight. Bind future source/test
hashes before provider execution; do not represent nonexistent files as frozen.

Create later `tests/test_skillcorner_lateral_gradient_support_preflight_v1.py`
with these mandatory synthetic tests (no provider fixture is needed now):

- `test_preflight_never_calls_outcome_construction_or_fit`: synthetic
  `MatchSource` fragments exercise the real extractor with `construct_row`,
  `construct_match`, path construction, fit/bootstrap and legacy `execute`
  replaced by immediate failures; verify explicit field projection too.
- `test_default_and_verify_freeze_never_open_provider_files`: reader sentinels
  prove the command gate is fail-closed without any data directory access.
- `test_source_identity_requires_all_nine_pinned_matches`: synthetic file/tree
  manifests cover absent, substituted, changed and matching input identities.
- `test_eligibility_matches_inherited_support`: synthetic native fragments
  exercise cadence, phase/possession, missing support, rosters, ball-nearest,
  identity gates and canonical (not native) rank ordering with ties/crossings.
- `test_start_location_uses_three_frame_canonical_t_minus_two`: asymmetric pitch
  dimensions and analytic positions prove scaling, smoothing and start timing.
- `test_absolute_y_retains_finite_out_of_pitch_starts`: signs/zero/boundaries
  verify absolute y with no focal-side reflection, clipping or exclusion.
- `test_quality_uses_frozen_focal_ball_and_seven_defender_windows`: synthetic
  Boolean flags test edge inclusion, >=0.5, and each required entity independently.
- `test_period_blocks_and_simultaneous_time_counts`: period 1/block 3 and
  period 2/block 3 count twice; simultaneous focal perspectives share a time.
- `test_diagnostic_bands_and_quality_region_gates`: exact 10/20/30/34 m edges,
  >34 retention, 19 versus 20 times, three versus four blocks, and absent periods.
- `test_a1_design_rank_and_leverage_are_response_free`: constant versus varied
  within-match z, unequal n_m and both samples; use small analytic rank/leverage
  oracles, never synthetic or real Y to build the predictor-only design.
- `test_identity_digest_is_order_invariant_and_membership_sensitive`: stable
  shuffle digest, duplicate failure and changed member with identical counts.
- `test_aggregate_outputs_reject_row_fields_and_wrong_granularity`: reject IDs,
  individual coordinates/times/blocks, response fields and extra aggregate rows.
- `test_support_serialization_is_deterministic`: shuffled synthetic inputs
  reproduce stable sorted tables/JSON/report bytes and package hashes.

Real integration tests must be marked `provider_data`, remain support-only,
and run only at the separately reviewed/authorized preflight stage. No real
test may call a response constructor to obtain an expected count or position.

## 8. Review, execution, and stop conditions

The gate sequence is: design freeze; support implementation/synthetic validation;
independent support pre-access review; explicitly authorized support-only run;
human review of aggregate support; separate response-stage freeze/review;
explicit response authorization. No gate implies the next authorization.

Support validation must cover compilation, focused synthetic tests, portable
non-provider tests, exact source/count identities, JSON/CSV schema checks,
deterministic independent aggregate rerun, publication guard and whitespace
checks. Use isolated output directories; do not overwrite a closed package.

Numeric success is `SUPPORT_PREFLIGHT_QC_PASSED_AWAITING_HUMAN_REVIEW`, not
SUPPORTED and not permission to read Y. Any failed validity/feasibility gate
is `SUPPORT_PREFLIGHT_INVALID`. Retain aggregate failure evidence. Human
review must resolve measurement-quality concerns before advancement; flags
alone cannot prove spatial accuracy. If support fails, stop before response
access instead of changing thresholds, exclusions, covariates or model form.

No A2/A3, zones, trim search, alternative blocks, extra providers, heatmap,
orientation empirical work or new outcome search is authorized here. The
approved later A1 analysis and Branch B mathematical/synthetic scoping remain
separate bounded tasks. If A is not execution-ready by September 16, do not
compress review. Close the science window September 22 and reserve September
23 onward for submission assembly. The locked abstract and two figures remain
unchanged unless separately approved editorially.
