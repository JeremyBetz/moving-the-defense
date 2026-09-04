# Spatial Defensive-Response Footprint v1 — IDSSE External Replication

**Status:** **FROZEN BEFORE ANY IDSSE TEMPORAL-FOOTPRINT RESULT**

**Freeze date:** 2026-09-03

**Starting commit:** `be544395493d01aa35b02031fc0d958d36753afe`
**Execution tier:** Tier 3 external replication

## 1. Decision and question

The closed Metrica construct chosen for this test is the [Spatial
Defensive-Response Footprint v1](spatial_defensive_response_footprint_v1.md),
not the later response-form construct. It is the closed time-ordered model
whose primary estimand is exactly the frozen near (D1–D3) minus middle
(D4–D7) contrast in subsequent focal-relative path. It inherits the earlier
attacker-to-defender bridge's timing and movement primitive without creating a
new bridge metric.

> Across the seven governed IDSSE matches, is greater attacker path during the
> fixed preceding exposure interval associated with greater subsequent
> defender-relative path among the near than middle defender ranks, after the
> unchanged strictly earlier defender-path and defending-unit-path context?

The fixed match order is `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`,
`J03WQQ`, and `J03WR9`. They are seven match-level replications from one
independent provider environment, not seven providers. Metrica Sample Game 3
is prohibited.

This is an observational temporal-order test. Earlier exposure and later
movement do not establish reaction time, causation, attention, assignment,
marking, intent, tracking, space creation, tactical success, gravity, or
attacking value.

## 2. Unchanged measurement and timing

For an eligible `(match, period, t, attacker)` anchor:

- strictly earlier defensive context is `[t-4, t-2]` seconds;
- attacker exposure is path length over `[t-2, t]` seconds;
- primary focal response is focal-relative path over `[t, t+2]` seconds;
- one- and four-second response paths are frozen sensitivities;
- anchors are `period origin + 4 + 4k` seconds; and
- every rank is fixed once at `t` from Euclidean canonical-metre attacker–
  defender distance, using ascending canonical player key for an exact tie.

The ten defending outfield players must be complete and observed across every
required raw and smoothed support frame. Goalkeepers are excluded. D1–D3 are
near, D4–D7 are middle, and D8–D10 are descriptive far. Neither rank nor
membership may change within an anchor. All simultaneous attacking outfield
players remain separate observations and travel together in resampling.

For each fixed rank, the unchanged raw-metre OLS terms are intercept, attacker
path, that rank's strictly prior focal-relative path, and strictly prior full
defending-outfield centroid path. The primary rank coefficient is the attacker
path term. The primary contrast is

$$
\Delta_{NM}=\operatorname{mean}(\beta_{D1},\beta_{D2},\beta_{D3})-
\operatorname{mean}(\beta_{D4},\ldots,\beta_{D7}).
$$

The exact Metrica extreme-attacker-path cut, `12.198443079831405` m, transfers
unchanged. The frozen metric-distance complement, D8–D10 description, and
middle-minus-far contrast remain descriptive only and cannot rescue external
classification.

## 3. Provider equivalence before any association result

Use the canonical Kloppy IDSSE/Sportec adapter, raw timestamp sidecar, and the
[provider-equivalence specification](../spatial_defensive_response_footprint_v1_idsse_equivalence.md).
The original bridge/footprint implementation consumes a 25 Hz Metrica
trajectory with a centred seven-frame full-support mean. IDSSE's governed
files are expected to be 25 Hz as well. The external execution nevertheless
tests actual cadence rather than assuming it: every required native timestamp
increment must be 40 ms. Thus the same seven frames retain the same 0.28 s
physical support. If a governed IDSSE match fails this condition, it is
invalid—not a reason to reuse a frame count at a different cadence or choose a
new smoother.

Before fitting any attacker–defender association, every match must pass the
outcome-blind gate for raw UTC time/frame identity, period boundaries,
player/team/goalkeeper IDs, observed/null masks, canonical coordinates,
event-clock possession/open-play state, anchor identities, and D1–D10 rank
membership. It additionally compares mechanically derived prior/exposure/
response path components between the provider-native and canonical views.
The gate's tolerances and failure policy are in the configuration. No match may
be removed for its estimate or result direction.

The event clock supplies possession at `t` and the global restart/ball-out
exclusion across `[t-4,t+2]`; possession need not continue after `t`. Ball
coordinates and downstream football outcomes do not enter the construct.

## 4. Temporal control and sensitivities

The unchanged reverse-time placebo uses future attacker path `[t,t+2]` to
model earlier focal-relative path `[t-2,t]`, with the same strictly earlier
`[t-4,t-2]` covariates. For the same blocked bootstrap draws, retain the paired
primary-minus-placebo near-minus-middle contrast. This distinguishes temporal
ordering from a claim of causation.

Also retain unchanged:

- the transported extreme-exposure trim and its 50% retained-magnitude rule;
- the one- and four-second response horizon sign check; and
- the temporal placebo's rank-specific and regional descriptive output.

## 5. Match-level and pooled execution

Fit each match independently and report its eligible attacker-anchor count,
unique anchor count, D1–D10 coefficients, near/middle/far estimates,
`Delta_NM`, temporal placebo, paired excess, trim, 1/2/4-second sensitivities,
and bootstrap validity. Individual intervals are descriptive; their signs
remain visible.

The pooled precision summary is frozen before outcomes. It uses the same
rank-specific four-term model plus six common match indicators, with `J03WMX`
as reference. There are no match-by-rank, match-by-exposure, or higher-order
interactions; observations are unweighted. This is the direct seven-match
analogue of the closed Metrica pooled model's common Game-2 indicator, not a
new football covariate.

Use 2,000 period-origin 60-second block-bootstrap replicates, retaining
terminal partial blocks. Resample independently within every match-period,
retain each complete D1–D10 vector and all simultaneous attackers together,
and use paired identical block draws for primary, placebo, trim, and horizon
families. Require at least 1,900 finite, estimable replicates for every
governed interval. `PCG64(SeedSequence(20260903).spawn(8)[i])` is reconstructed
afresh: children 0–6 follow the stated match order and child 7 is pooled.

## 6. External statuses

Evaluate these exhaustive statuses in order.

1. **IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION INVALID** — any governed
   match or pooled execution fails provider equivalence, support, rank,
   solver, bootstrap, frozen-hash, governance, or deterministic-reproduction
   requirements.
2. **IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION NOT SUPPORTED** — valid
   execution with pooled primary `Delta_NM <= 0`, three or fewer positive
   match-level primary estimates, pooled paired primary-minus-placebo
   `Delta_NM <= 0`, or three or fewer positive match-level paired-excess
   estimates.
3. **IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION SUPPORTED** — valid
   execution; pooled primary `Delta_NM > 0` with a 95% percentile interval
   strictly above zero; at least five of seven primary estimates positive;
   pooled paired primary-minus-placebo `Delta_NM > 0` with its 95% paired
   percentile interval strictly above zero; at least five of seven paired
   excess estimates positive; positive pooled trimmed `Delta_NM` retaining at
   least 50% of the untrimmed absolute magnitude; and neither 1 s nor 4 s
   pooled primary `Delta_NM` is opposite in sign to the two-second estimate.
4. **IDSSE TEMPORAL FOOTPRINT EXTERNAL REPLICATION MIXED** — every other valid
   execution.

The stricter paired-control requirement applies because this final external
test is specifically a *time-ordered* bridge. It is a prospective external
classification rule; it does not retroactively alter the closed Metrica Final
Footprint A rule, whose spatial placebo was diagnostic and nonclassifying.

## 7. Closure, value, and failure use

This test is worth external replication. A supported result would add
cross-provider evidence for the project’s strongest nonconcurrent statement:
earlier attacker movement is associated with later localized
defender-relative movement. A mixed or unsupported result is equally
informative: the Sloan paper will centre the externally supported concurrent
geometry and state directly that time ordering beyond the frozen controls did
not externally generalize. No alternate lag, window, rank grouping, or bridge
metric may be searched after such a result.

Tier 3 closure requires saved hashes before interpretation, independent
byte-identical reproduction, focused equivalence/footprint/governance tests,
machine-readable validation, and a concise result report. Avoid new figures or
feature engineering unless a frozen output requires them.

## 8. Claim boundary

If supported, the maximum claim is:

> Across two Metrica sample matches and an independent seven-match IDSSE
> dataset, greater observed attacker movement in a fixed preceding interval
> was associated with greater subsequent defender-relative movement among the
> near than middle defender ranks under the frozen observational design.

That remains an association with temporal ordering, not evidence of causal
attacker influence or a football-tactical mechanism.
