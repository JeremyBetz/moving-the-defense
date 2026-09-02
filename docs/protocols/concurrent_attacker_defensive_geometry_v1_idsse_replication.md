# Concurrent Attacker–Defensive Geometry v1 — IDSSE External Replication

**Status:** **FROZEN BEFORE ANY IDSSE CONCURRENT-GEOMETRY RESULT**

**Freeze date:** 2026-09-02

**Starting commit:** `1f4786277592fea2cf2c5e15465e29bf7f92dbf3`

**Execution tier:** Tier 3 external replication

## 1. External question and firewall

> Across the seven IDSSE matches, does the unchanged Concurrent Attacker–Defensive Geometry v1 design reproduce a positive near-minus-middle association between concurrent attacker path and focal-relative defender path under the same pre-interval movement context?

This protocol was frozen after the within-provider Metrica result closed and before any IDSSE concurrent-geometry sample, coefficient, interval, robustness result, or deformation result was computed or inspected. Opportunity Redistribution v1 is excluded. Metrica Sample Game 3 remains untouched.

The governed matches, in fixed order, are `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, and `J03WR9`. They are seven match-level replications from one independent provider/data environment, not seven independent providers.

## 2. Scientific construct is unchanged

Apply [Concurrent Attacker–Defensive Geometry v1](concurrent_attacker_defensive_geometry_v1.md) unchanged:

- two-second pre-context $[t-2,t)$ and two-second concurrent interval $[t,t+2)$ under the original exact endpoint/increment convention;
- concurrent attacker path as exposure;
- focal defender path relative to the leave-one-out centroid of the other nine defending outfield players as the primary outcome;
- D1–D10 ranked at $t$ by focal-attacker distance, with ascending canonical player ID as the exact tie-break and membership then fixed;
- near D1–D3, middle D4–D7, and descriptive far D8–D10; and
- primary estimand $\Delta_{NM}=\overline\beta_{D1:D3}-\overline\beta_{D4:D7}$.

The same 72-column float64 stacked rank-specific OLS is fitted with `numpy.linalg.lstsq(..., rcond=None)`. Per-rank columns remain intercept, concurrent attacker path, prior focal-relative path, prior defending-outfield centroid path, prior mean absolute path of the other nine defenders, prior attacker path, and anchor distance; common columns remain period-2 and home-attacking indicators. No predictor, interaction, weighting term, nonlinear term, regularizer, football-context variable, or alternate model is added.

## 3. Provider adapter and exact sampling

Use the established Kloppy IDSSE/Sportec adapter and [canonical tracking contract](../canonical_tracking_contract.md), not a second ingestion path. Provider mechanics are separate from the scientific construct:

- raw `Frame.X`/`Frame.Y` are native centred metres on a 105 × 68 m fixed pitch, +x right and +y up; no attacking-direction normalization;
- raw `Frame.T` is retained as UTC nanoseconds and mapped to period-relative time using the period-opening `KickOff`; `Frame.N` is retained;
- native sampling is 25 Hz; the centered seven-frame rolling mean uses full support and no interpolation;
- the exact anchor grid is $t=\text{period origin}+2+4k$;
- each pre/concurrent span contains 101 smoothed endpoint samples and 100 increments over four seconds; centered smoothing additionally requires the three observed raw frames on each side of every used endpoint;
- all required coordinates must be finite and observed for the focal attacking outfield player and exactly ten defending outfield players across the full raw smoothing support;
- goalkeeper identity is `Player.PlayingPosition == TW`, checked against provider metadata; substitutions and tracking gaps are handled only through explicit roster/support availability;
- possession at $t$ and open-play/restart state use the already-governed IDSSE event-clock mapping; possession need not continue after $t$; and
- no interpolation, imputation, role inference, assignment inference, or tactical event label is permitted.

Before scientific execution, every match must pass an outcome-blind equivalence gate against the established provider-native IDSSE representation. Exact agreement is required for periods, frame numbers, UTC timestamps, player/team IDs, goalkeeper flags, observed/null masks, possession/open-play state, anchor IDs, retained focal IDs, and D1–D10 membership. Coordinate discrepancies must be at most $10^{-5}$ m, derived component discrepancies at most $10^{-4}$ m, and path discrepancies at most $10^{-3}$ m. Failure in any governed match makes the external execution invalid; no match may be removed because of its effect direction.

## 4. Match-level replication

Fit the unchanged model independently in every match. Report for each match:

- eligible focal-attacker observations and unique time anchors;
- primary $\Delta_{NM}$ and its two-sided 95% percentile interval;
- the frozen trim result and retained magnitude; and
- the sign of the primary estimate.

Individual-match intervals need not exclude zero. The seven signs remain visible and are not replaced by the pooled estimate.

For each match, use 2,000 period-origin 60-second block bootstrap replicates, retain terminal partial blocks, and group complete D1–D10 vectors plus all simultaneous attackers at an anchor. Require at least 1,900 valid replicates. Initialize `Generator(PCG64(SeedSequence(20260902).spawn(8)[i]))` afresh for each governed family, where `i=0..6` follows the fixed match order. Primary, secondary, and trim families use identical block draws within a match.

The frozen Metrica extreme-exposure threshold, concurrent attacker path greater than `12.198443079831405` m, is transported unchanged. No IDSSE percentile or replacement cut is calculated.

## 5. Pooled external precision summary

The pooled analysis is secondary to the seven match-level replications but is the primary precision summary. Concatenate all eligible observations and fit the same unweighted 72-column stacked model, with no match indicator or interaction. This is observation-weighted pooling; match identity is retained for reporting and resampling only.

For each of 2,000 pooled replicates, independently resample period-origin 60-second blocks within every match, retain terminal partial blocks and grouped anchors, concatenate the seven resampled match tables, then fit the unchanged model. Use child `i=7` of the same fixed `SeedSequence(20260902).spawn(8)` construction, require at least 1,900 valid replicates, and use paired identical block draws for primary, secondary, and trim families.

This pooled estimate does not turn observations into independent replications and does not override disagreement across matches.

## 6. Exact external status

Evaluate in this order:

1. **IDSSE EXTERNAL REPLICATION INVALID** if any governed match or pooled execution has a provider-equivalence, scientific-validity, model-rank, solver, bootstrap, support, governance, or deterministic-reproduction failure.
2. **IDSSE EXTERNAL REPLICATION NOT SUPPORTED** if execution is valid and either pooled $\Delta_{NM}\le0$ or three or fewer of seven match estimates are positive.
3. **IDSSE EXTERNAL REPLICATION SUPPORTED** if execution is valid and all hold: pooled $\Delta_{NM}>0$; its 95% interval is strictly above zero; at least five of seven match estimates are positive; pooled trimmed $\Delta_{NM}>0$; and trimming retains at least 50% of the untrimmed pooled absolute magnitude.
4. **IDSSE EXTERNAL REPLICATION MIXED** for every other valid case with pooled $\Delta_{NM}>0$ and at least four of seven match estimates positive.

These clauses are exhaustive and non-overlapping. A null or opposite result is not invalidity. No D1-specific, monotonicity, far-rank, effect-size, or individual-match interval gate exists.

## 7. Secondary deformation

Carry the already-defined concurrent endpoint RMS focal-to-nine-teammate distance change through the same match-level and pooled 72-column architecture. Label it **SUPPORTIVE** when its near-minus-middle estimate is positive with interval strictly above zero, **DIRECTIONALLY SUPPORTIVE** when positive with an interval including zero, and **NON-SUPPORTIVE** when nonpositive. It cannot change the external status. No additional secondary outcome is authorized.

## 8. Closure and claim boundary

Tier 3 requires serialization, hashing, independent byte-identical reproduction, at least 1,900 valid bootstrap replicates per governed family, focused and repository QC, and documentation before closure. Match comparison and pooled interpretation occur only after all seven match-level outputs close.

If **SUPPORTED**, the maximum claim is:

> Across the two Metrica sample matches and an independent seven-match IDSSE dataset, greater attacker movement within fixed two-second intervals was associated with stronger concurrent focal-relative defender movement among nearby than middle-ranked defenders after conditioning on the prospectively specified pre-interval movement context.

This is an observational cross-provider association. It does not establish causation, reaction time, attention, responsibility, marking assignment, defender intent, space creation, tactical success, gravity, or player value. **MIXED** or **NOT SUPPORTED** must report the external inconsistency directly.
