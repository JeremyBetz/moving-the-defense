# Outcome-Blind Defender-Rank Composition Audit

**Audit date:** 2026-09-03

**Frozen starting checkpoint:** `31efbbfe06aae057dba43bc95fd1b650a5b10789`

**Status:** `OUTCOME_BLIND_RANK_COMPOSITION_AUDIT_COMPLETE`

**Severity:** **MODERATE**

**Verdict:** **CORE RANK LOCALIZATION USABLE WITH MODERATE LIMITATION**

**Downstream decision:** **V3 MAY PROCEED WITH A PAPER LIMITATION / NONCLASSIFYING QC**

## Audit question and answer

The audit asked whether the frozen start-distance ranks encode nondefining
baseline geometry or prior activity strongly enough to threaten interpretation
of the closed core model's rank-specific attacker-path slopes. It compared
D1--D3 (near) with D4--D7 (middle), retained D8--D10 for descriptive summaries,
and evaluated out-of-match predictability of near versus middle without using
the defining scalar Euclidean attacker--defender distance.

The answer is **moderate, not major**. The strongest nondefining difference was
the defender's goalward offset from the defensive centroid: its median
match-specific standardized difference was -0.338, with the same negative sign
in all nine matches. A scalar-distance-excluded baseline classifier also
carried modest held-out information about rank group (median AUC 0.627).
Neither result reached
the frozen major threshold: no nondefining variable had an absolute median
standardized difference of at least 0.5, median held-out AUC was below 0.70,
and no held-out AUC reached 0.65.

The ranks therefore remain usable for the closed core localization analysis,
but the paper must disclose that near and middle defenders differ modestly in
their starting position within the defensive unit. This is a composition
finding, not a tactical-role classification and not evidence by itself that a
rank-specific attacker-path slope is confounded.

## Scope, construction, and outcome firewall

The governed sample contains Metrica Games 1 and 2 and seven IDSSE matches:
J03WMX, J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, and J03WR9. It contains 83,513
attacker-anchor observations and 835,130 defender-rank rows.

Only identifiers, anchor timing, teams, block, defender, frozen distance rank,
start distance, and the four already governed prior-path fields were projected
from the closed observation ledgers. Start positions, start geometry, and the
remaining prior variables were reconstructed from governed tracking inputs on
the same centered-seven-frame support, using the window from anchor minus 2.0
seconds through the anchor inclusive. Reconstructed start distance and prior
geometry agreed with the governed fields within `1e-6` m.

Coordinates are fixed-pitch, canonical centered 105 m by 68 m coordinates,
without attacking-direction normalization. The goalward sign is the sign of
the defending team's goalkeeper median fixed-pitch x-coordinate over the first
2.0 seconds of supported goalkeeper tracking in the period. Every retained
anchor has at least the governed two-second prior support, so this orientation
window is not future to an audited anchor. Positive goalward values point from
the attacker toward the defending goal; own-goal depth is
`52.5 - goalward_sign * defender_x_m`.

Rows without an available ball position were retained for all non-ball
summaries. Ball variables were summarized only on available anchors and were
excluded from the classifier.

| Match | Defender-rank rows | Attacker-anchor observations | Ball-supported anchors |
|---|---:|---:|---:|
| Metrica Game 1 | 82,650 | 8,265 | 4,914 (59.46%) |
| Metrica Game 2 | 11,820 | 1,182 | 786 (66.50%) |
| J03WMX | 123,530 | 12,353 | 12,353 (100%) |
| J03WN1 | 48,760 | 4,876 | 4,876 (100%) |
| J03WOH | 112,870 | 11,287 | 11,287 (100%) |
| J03WOY | 115,790 | 11,579 | 11,579 (100%) |
| J03WPY | 124,330 | 12,433 | 12,433 (100%) |
| J03WQQ | 100,000 | 10,000 | 10,000 (100%) |
| J03WR9 | 115,380 | 11,538 | 11,538 (100%) |
| **Total** | **835,130** | **83,513** | **79,766 (95.51%)** |

The firewall held throughout:

- no empirical concurrent-response column was selected, summarized, or
  recomputed;
- no coverage outcome was selected, and no Game 2 or IDSSE coverage outcome
  was inspected;
- no IDSSE provider event file was opened during reconstruction;
- the v1 pre-execution rejection and v2 INVALID closure remained unchanged;
- no Defensive Coverage Redistribution v3 empirical output existed or was
  executed;
- the closed concurrent-geometry and coordination-form scientific artifacts
  remained unchanged;
- Game 3 was not accessed; and
- every frozen input hash matched.

Before commit, a read-only implementation review found that the preliminary
IDSSE code used full-period goalkeeper positions while Metrica used an opening
window, contrary to the start/prior-only firewall. The authoritative rerun
uses the same opening two-second goalkeeper support at both providers. The
review also required an explicit hash-bound input-provenance artifact and
corrected the classifier description from “distance-free” to
“scalar-Euclidean-distance excluded.” These were pre-closure integrity fixes,
not empirical tuning: no feature set, model, threshold, seed, severity rule,
protected response, or coverage outcome changed, and the corrected execution
was authoritative regardless of its result. All numerical findings and the
**MODERATE** verdict were unchanged.

A final pre-commit consistency review also made explicit that feature-based
severity applies only to unresolved nondefining composition: the mechanically
defining attacker distance and another variable already fully conditioned in
the closed core model remain reported as QC and do not alone trigger severity.
This was a wording disambiguation of the implemented rule, not a new threshold
or post-result reclassification; all numerical findings and the verdict again
remained unchanged.

The synthetic outcome used below was only a constructed coordinate-level
mechanical analogue. It did not import a match loader, governed empirical
response, observation table, or coverage artifact.

## Frozen methods and decision rules

For each match and rank group, the audit recorded the median, quartiles, mean,
standard deviation, and row count. The standardized difference was

$$
d = \frac{\bar{x}_{near}-\bar{x}_{middle}}
{\sqrt{\left[(n_{near}-1)s^2_{near}+(n_{middle}-1)s^2_{middle}\right]
/(n_{near}+n_{middle}-2)}}.
$$

Cross-match summaries are unweighted across the nine matches. A large stable
unresolved nondefining composition difference required `abs(median d) >= 0.5`
and the same sign in at least seven of nine matches. The feature-based severity
arm applies only when the variable is not the defining attacker distance and
is partially or not conditioned in the closed core model.

The classifier target was near = 1 versus middle = 0; far ranks were excluded.
The defining scalar Euclidean attacker--defender start distance and all ball
variables were also excluded. The 15 predictors were own-goal depth; defender goalward offset,
absolute lateral offset, and centroid distance; focal prior absolute path,
focal prior relative path, terminal speed, defensive-centroid prior path,
other-nine mean prior absolute path, and attacker prior path; local two-neighbor
distance; unit depth and width; and attacker goalward and absolute lateral
offsets. The model was a linear logistic regression with an intercept and fixed
`1e-6` L2 coefficient on standardized slopes. Each training match received
equal total weight; standardization was estimated on the training fold; and
performance was evaluated in nine deterministic leave-one-match-out folds,
without tuning.

The paired attacker and defender goalward centroid offsets reconstruct signed
longitudinal separation. The classifier therefore retains a component proxy
for the excluded scalar distance. Its performance is a conservative upper
bound on broader baseline-composition predictability, not evidence of rank
structure independent of every distance component. The direct univariate
composition summaries remain the primary basis for identifying which specific
nondefining differences are present.

Strong predictability required both median held-out AUC of at least 0.70 and at
least seven of nine held-out AUCs of at least 0.65. **MAJOR** required either a
large stable unresolved nondefining difference or strong predictability.
**MODERATE** required median AUC of at least 0.60 or an unresolved nondefining
feature with `abs(median d) >= 0.2` and the same sign in at least six matches.
**MINOR** required neither. Fully conditioned variables remained visible as QC;
they could still motivate an interpretive caveat about nonlinearity or effect
modification, but did not alone trigger severity.

## Full baseline comparison

The near and middle location entries below are the median of the nine
match-specific medians, followed in brackets by the medians of the nine
match-specific first and third quartiles. The effect entry is the unweighted
median match-specific standardized difference, followed by its cross-match
interquartile range. Positive effects mean larger values in near; negative
effects mean smaller values in near. “Core adjustment” describes the already
closed core model; it is not a change made by this audit.

| Baseline variable | Near median [Q1, Q3] | Middle median [Q1, Q3] | Median standardized difference [Q1, Q3] | Same-sign matches | Core adjustment | Audit flag |
|---|---:|---:|---:|---:|---|---|
| Attacker absolute lateral offset from centroid (m) | 9.549 [4.493, 16.372] | 9.549 [4.493, 16.372] | 0.000 [0.000, 0.000] | 3/9 | None | MINOR |
| Attacker--defender start distance (m) | 9.936 [5.827, 15.014] | 21.633 [16.234, 28.267] | -1.481 [-1.528, -1.413] | 9/9 | Full | MINOR; defining variable |
| Attacker goalward offset from centroid (m) | -6.131 [-14.983, 3.487] | -6.131 [-14.983, 3.487] | 0.000 [0.000, 0.000] | 4/9 | None | MINOR |
| Ball absolute lateral offset from centroid (m) | 11.725 [5.393, 17.596] | 11.725 [5.393, 17.596] | 0.000 [0.000, 0.000] | 3/9 | None | MINOR |
| Ball--defender distance (m) | 22.145 [13.133, 33.042] | 22.661 [13.553, 32.224] | -0.001 [-0.029, 0.016] | 6/9 | None | MINOR |
| Ball goalward offset from centroid (m) | -6.744 [-17.279, 6.120] | -6.744 [-17.279, 6.120] | 0.000 [0.000, 0.000] | 6/9 | None | MINOR |
| Defender absolute lateral offset from centroid (m) | 7.555 [3.839, 12.961] | 7.103 [3.533, 12.258] | 0.084 [0.033, 0.098] | 9/9 | None | MINOR |
| Defender distance from centroid (m) | 13.667 [8.776, 18.592] | 12.274 [7.942, 17.400] | 0.167 [0.149, 0.177] | 9/9 | None | MINOR |
| Defender fixed-pitch x (m) | 0.500 [-15.776, 16.011] | 0.782 [-16.847, 17.483] | 0.003 [-0.020, 0.018] | 5/9 | None | MINOR |
| Defender fixed-pitch y (m) | -1.129 [-11.154, 8.496] | -0.850 [-11.626, 8.570] | 0.013 [-0.015, 0.026] | 6/9 | None | MINOR |
| Defender goalward offset from centroid (m) | -3.252 [-10.440, 4.684] | 1.557 [-6.442, 7.942] | **-0.338 [-0.368, -0.327]** | **9/9** | None | **MODERATE** |
| Defender signed lateral offset from centroid (m) | -0.253 [-7.640, 7.471] | -0.564 [-7.079, 6.693] | 0.018 [-0.021, 0.038] | 6/9 | None | MINOR |
| Defender own-goal depth (m) | 50.336 [35.582, 67.357] | 46.817 [32.087, 63.834] | 0.151 [0.147, 0.159] | 9/9 | None | MINOR |
| Local two-neighbor mean distance (m) | 10.422 [7.728, 13.226] | 10.156 [7.590, 12.857] | 0.064 [0.046, 0.086] | 9/9 | None | MINOR |
| Focal prior absolute path (m) | 3.224 [2.158, 5.754] | 3.267 [2.125, 5.781] | -0.002 [-0.007, 0.005] | 5/9 | Partial | MINOR |
| Attacker prior path (m) | 3.072 [2.001, 5.392] | 3.072 [2.001, 5.392] | 0.000 [0.000, 0.000] | 1/9 | Full | MINOR |
| Defensive-centroid prior path (m) | 2.674 [1.380, 4.763] | 2.674 [1.380, 4.763] | 0.000 [0.000, 0.000] | 1/9 | Full | MINOR |
| Focal prior relative path (m) | 2.285 [1.417, 3.608] | 2.259 [1.416, 3.520] | 0.043 [0.033, 0.047] | 9/9 | Full | MINOR |
| Other-nine mean prior absolute path (m) | 3.673 [2.289, 5.503] | 3.678 [2.287, 5.508] | 0.000 [-0.001, 0.001] | 5/9 | Full | MINOR |
| Prior terminal speed (m/s) | 1.565 [1.010, 2.933] | 1.582 [0.995, 2.937] | -0.005 [-0.014, 0.003] | 6/9 | Partial | MINOR |
| Unit depth span (m) | 31.859 [26.873, 38.034] | 31.859 [26.873, 38.034] | 0.000 [0.000, 0.000] | 3/9 | None | MINOR |
| Unit width span (m) | 38.564 [33.153, 43.646] | 38.564 [33.153, 43.646] | 0.000 [0.000, 0.000] | 3/9 | None | MINOR |

Attacker, ball, unit-span, defensive-centroid-path, and attacker-prior-path
variables are shared by all ten defender rows at a given attacker-anchor. Their
near and middle summaries can therefore be exactly equal by construction. This
means there is no *within-anchor rank contrast* in those variables; it does not
mean there is no contextual variation across anchors or matches.

The defining start-distance difference is large, as it must be, but is not a
nondefining composition threat and is directly included as a rank-specific
linear control in the closed core model. Among prior-activity measures, focal
absolute path (`d = -0.002`), terminal speed (`d = -0.005`), and other-nine
activity (`d` approximately zero) were effectively balanced. Focal relative
prior path had a small stable difference (`d = 0.043`, 9/9) and is directly
conditioned in the core model.

## Scalar-distance-excluded rank predictability

All 584,591 near-or-middle rows were complete for the 15 non-ball predictors.
Held-out performance was:

| Held-out match | Rows | Near rows | AUC | Balanced accuracy at 0.5 |
|---|---:|---:|---:|---:|
| J03WMX | 86,471 | 37,059 | 0.6214 | 0.5272 |
| J03WN1 | 34,132 | 14,628 | 0.6348 | 0.5337 |
| J03WOH | 79,009 | 33,861 | 0.6192 | 0.5353 |
| J03WOY | 81,053 | 34,737 | 0.6143 | 0.5261 |
| J03WPY | 87,031 | 37,299 | 0.6223 | 0.5311 |
| J03WQQ | 70,000 | 30,000 | 0.6299 | 0.5291 |
| J03WR9 | 80,766 | 34,614 | 0.6267 | 0.5331 |
| Metrica Game 1 | 57,855 | 24,795 | 0.6337 | 0.5358 |
| Metrica Game 2 | 8,274 | 3,546 | 0.6460 | 0.5468 |
| **Median** |  |  | **0.6267** | **0.5331** |

The AUC range was 0.6143--0.6460. Zero of nine folds reached 0.65. The median
AUC crossed the frozen 0.60 moderate threshold but did not satisfy either part
of the strong-predictability rule.

The largest standardized coefficient medians across the nine fits were
defender goalward offset (-0.392; fold range -0.398 to -0.386), defender
centroid distance (+0.176; +0.165 to +0.194), attacker goalward offset (+0.121;
+0.118 to +0.122), and local two-neighbor distance (-0.093; -0.107 to -0.087).
These are multivariable diagnostic loadings, not causal effects or a tactical
role classifier. In particular, a coefficient does not override the direct
near--middle balance summaries for an anchor-shared variable.

## Synthetic null and prior-confounding checks

The frozen synthetic suite used 12,000 heterogeneous ten-defender scenes per
variant, the project's exact start-distance ranker, collective translation,
and independent random streams for geometry, attacker movement, prior activity,
individual innovation, and translation. Its response was the signed x-component
of a constructed endpoint defender-relative displacement.

| Check | Frozen result | Interpretation |
|---|---:|---|
| Rank-only null, D1--D10 maximum absolute attacker-path slope | 0.000532 | Exact start ranking plus leave-one-out centering did not mechanically localize an otherwise null attacker slope. |
| Rank-only null, near-minus-middle attacker-path slope | -0.0000464241 | Approximately zero under heterogeneous start geometry and collective translation. |
| Prior-confounded variant, near versus middle prior activity | 1.7406424 m versus 1.5004393 m (difference 0.2402031 m) | The synthetic confound was deliberately material and rank-composed. |
| Prior-confounded variant, unadjusted near-minus-middle slope | 0.0562980 | Omitting prior activity created the intended spurious localization even though the true attacker-path coefficient was zero. |
| Prior-confounded variant, adjusted near-minus-middle slope | -0.000437238 | Conditioning on focal-relative and other-nine prior activity removed 99.2234% of the absolute localization; the maximum absolute adjusted D1--D10 slope was 0.001008. |

All four frozen synthetic tests passed. These checks establish the intended
mechanical properties of ranking, centering, and the declared prior controls;
they are not empirical validation of a protected response and do not prove
that every possible baseline composition feature is harmless.

## Leave-one-out identity

For ten defenders, let `c` be the full defensive centroid and `c_-d` the mean
of the other nine defenders. Then

$$
c_{-d}=\frac{10c-x_d}{9}
\quad\Longrightarrow\quad
x_d-c_{-d}=\frac{10}{9}(x_d-c).
$$

The same identity holds for displacement vectors. The factor `10/9` is
constant for every defender and every distance rank, so leave-one-out centering
cannot create differential D1--D10 scaling. A common team translation also
cancels exactly. The deterministic synthetic check reproduced both properties
to machine precision (maximum absolute discrepancy below `1.43e-14`).

## Existing conditioning coverage

The closed core model already has, for each D1--D10 rank, a rank-specific
intercept and rank-specific slopes for concurrent attacker path, prior focal
leave-one-out-relative path, prior full defensive-centroid path, prior
other-nine mean absolute path, prior attacker path, and anchor
attacker--defender distance, plus common period-2 and home-attacking indicators.

Accordingly:

- **Fully conditioned:** attacker--defender start distance, focal relative
  prior path, defensive-centroid prior path, other-nine mean prior absolute
  path, and attacker prior path.
- **Partially conditioned:** focal prior absolute path and prior terminal
  speed. The fixed two-second relative, centroid, and other-nine paths capture
  important activity components but do not reconstruct either quantity
  exactly.
- **Not conditioned:** fixed-pitch x/y, own-goal depth, centroid-relative
  longitudinal/lateral/radial position, attacker position relative to the unit,
  local density, unit width/depth, ball geometry, and player, role, or formation
  effects. Later context models do not retroactively adjust the closed core
  rank-specific attacker-path estimates.

Rank-specific intercepts absorb stable rank-level response levels, and the
direct prior and distance controls protect against important known composition
paths. They do not automatically remove slope confounding from an omitted
baseline feature that covaries with attacker movement and response or modifies
the attacker-path slope.

## Threats, protections, and interpretation

The principal threats are:

1. **Within-unit goalward position.** Near defenders were typically less
   goalward relative to the defensive centroid (near median -3.252 m; middle
   +1.557 m), with a stable moderate standardized difference of -0.338 in 9/9
   matches. This feature is not in the closed core model.
2. **Smaller stable structural differences.** Near defenders were modestly
   farther from the centroid (`d = 0.167`, 9/9), had greater own-goal depth
   (`d = 0.151`, 9/9), slightly greater absolute lateral offset (`d = 0.084`,
   9/9), and slightly larger local neighbor distance (`d = 0.064`, 9/9).
3. **Residual multivariable composition.** A scalar-distance-excluded
   classifier achieved median held-out AUC 0.627, so rank group is not
   exchangeable across the measured start-state variables. Because its paired
   goalward offsets retain longitudinal-separation information, this is an
   upper-bound diagnostic rather than proof of composition independent of all
   distance components.

The principal protections are:

1. **Frozen direct conditioning.** Start distance and the four central prior
   movement controls already enter as rank-specific core terms, and rank-specific
   intercepts absorb persistent rank-level outcome levels.
2. **Weak prior-activity imbalance.** The observed prior absolute path,
   terminal-speed, other-nine-activity, and focal-relative-path effects were
   small; the latter two are directly conditioned. In a deliberately
   prior-confounded synthetic variant, the matching controls removed more than
   99.2% of the induced localization.
3. **No major signal.** No nondefining baseline feature crossed the frozen 0.5
   large/stable threshold, median AUC remained below 0.70, and no fold reached
   0.65. The algebraic and synthetic checks also exclude rank assignment,
   leave-one-out scaling, or collective translation as explanations for a
   localized slope by themselves.
4. **Governed design protections.** Ranks were fixed at the anchor with no
   future geometry, all D1--D10 defenders were retained within simultaneous
   attacker-anchor groupings, and inference in the closed analysis remains
   match/provider replicated and block-aware.

The required interpretive guard is:

> Rank composition can threaten a rank-specific attacker-path slope only if
> the baseline feature also covaries with attacker movement and response or
> modifies that slope; balance alone is not proof of confounding.

The audit therefore does not label defenders by role, reinterpret a baseline
difference as a response, or claim that the moderate goalward-position
difference changes the closed core estimate. It identifies the most plausible
unmodeled composition channel and constrains how the core localization can be
described.

## Decision and relation to Defensive Coverage Redistribution v3

The frozen decision is **MODERATE** and the exact verdict is:

> **CORE RANK LOCALIZATION USABLE WITH MODERATE LIMITATION**

The exact downstream decision is:

> **V3 MAY PROCEED WITH A PAPER LIMITATION / NONCLASSIFYING QC**

The paper limitation should state that attacker-distance ranks also carry a
modest, stable within-unit goalward-position composition difference and weaker
radial/depth differences. The rank-specific attacker-path pattern may still be
reported, but it should not be described as isolated from all starting role or
zone composition.

**No sensitivity was frozen.** No prospective core sensitivity was required,
specified, or authorized because the frozen rule requires one only after a
**MAJOR** audit result. The **MODERATE** result permits v3 to proceed only with
the paper limitation and nonclassifying QC above. No closed core model,
eligible sample, coefficient, decision threshold, or inferential procedure was
changed, and no v3 empirical result was examined in making this decision.

## Reproducibility record

The final audit configuration SHA-256 is
`3664d4353390d028221d354b611c6172ebb35acd3fc2f0cfc8b5f24c1c3d49a9`.
Its pre-closure integrity history records the initial prospective freeze and
the outcome-blind correction above.
The unchanged Defensive Coverage Redistribution v3 protocol and configuration
SHA-256 values are
`5bf577758202aed13b47fce54fd40c88b1a443d675d832f93f69c62570303988`
and
`54a01d0aeba846b1e245a0c0552234b2390cfc3ec10ec0a187dc94c0b10fed42`.
An independent complete rerun reproduced all 10/10 governed outputs
byte-for-byte.
The governed machine-readable record is retained in:

- `config/defender_rank_composition_audit.json`;
- `outputs/defender_rank_composition_audit/audit_results.json`;
- `outputs/defender_rank_composition_audit/sample_counts.csv`;
- `outputs/defender_rank_composition_audit/input_provenance.json`;
- `outputs/defender_rank_composition_audit/rank_group_summaries.csv`;
- `outputs/defender_rank_composition_audit/rank_D1_D10_summaries.csv`;
- `outputs/defender_rank_composition_audit/near_middle_effects.csv`;
- `outputs/defender_rank_composition_audit/cross_match_effects.csv`;
- `outputs/defender_rank_composition_audit/rank_predictability_folds.csv`;
- `outputs/defender_rank_composition_audit/rank_predictability_coefficients.csv`;
- `outputs/defender_rank_composition_audit/conditioning_coverage.csv`;
- `outputs/defender_rank_composition_audit/governed_hashes.json`; and
- `outputs/defender_rank_composition_audit/reproduction.json`.

The individual D1--D10 medians and interquartile ranges remain available in
the governed output even though the inferential audit contrast was frozen as
near versus middle.
