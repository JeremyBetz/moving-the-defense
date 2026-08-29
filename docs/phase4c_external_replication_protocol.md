# Phase 4C External Focal-Departure Replication Protocol

## Status and research question

**Status:** frozen prospective protocol v1.0, designed and approved without accessing IDSSE/DFL files or outcomes. Data access and execution remain separate future steps.

> **Does the focal-relative path primitive exhibit stable measurement behavior across multiple professional matches from an independent tracking dataset?**

Phase 4C attacks one threat: the successful Metrica Game 1→2 result may be specific to two sample matches, one provider representation, or one narrow match environment. It is an external replication of geometry, not a football-semantic validation.

The machine-readable companion is [`config/phase4c_external_replication_protocol.json`](../config/phase4c_external_replication_protocol.json). If this prose and the frozen config later conflict, execution must stop before focal-relative outcomes.

## Evidence inherited from Phase 4B

Phase 4B supports only: **focal-relative path is a reproducible focal-versus-collective geometric primitive with stable activity-context structure in these two sample matches.** It remains substantially activity-associated. The established inference level is:

**physical movement → collective movement → individual/local behavior relative to collective movement**

Phase 4C does not advance the project to contextual expectation, tactical defensive response, attacker association, attribution, or value.

## Target dataset and outcome blindness

The intended target is IDSSE/DFL, described in already recorded metadata as seven complete Bundesliga/2. Bundesliga matches with official optical/TRACAB tracking at 25 Hz and synchronized events/metadata. No dataset file, schema, support count, trajectory, player value, distribution, or example was inspected during protocol design.

Exact provider schema mapping is unresolved. Field names, coordinate convention, pitch metadata, identity tables, goalkeeper flags, possession/event representation, substitutions, missingness codes, and ball-quality fields must be mapped outcome-blind after access and before focal-relative outcomes.

## Frozen construct

For focal defending outfield player $d$,

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),
\qquad
\mathbf c_{-d}(t)=\frac{1}{|O_d(t)|}\sum_{j\in O_d(t)}\mathbf x_j(t),
$$

where $O_d(t)$ contains the other available defending outfield players and excludes the goalkeeper and focal defender. Membership is fixed within an interval.

The primary outcome remains accumulated Euclidean path of the centered seven-frame-smoothed $\mathbf r_d(t)$ over a half-open five-second interval. Coordinates must be in physical metres. No orientation normalization is needed for Euclidean path; any provider conversion must preserve distances and be documented. The construct must not be changed to improve replication.

Secondary quantities remain separate: net relative x/y change, net relative displacement, focal absolute path, leave-one-out centroid path, full defending-outfield centroid path, summed defending-outfield paths, and ball path. No ratio, residual score, activity-free score, or composite is permitted.

## Construct requirements versus provider implementation

### Construct requirements

- 25 Hz or verified equivalent time indexing;
- physical metric coordinates and documented pitch dimensions;
- continuous player identities within intervals;
- unambiguous team and goalkeeper identification;
- defending-team identification from synchronized context;
- focal plus at least eight other complete defending outfield players throughout an interval;
- fixed interval membership, with no coordinate interpolation;
- complete ball trajectory and event/context information needed to reproduce the Phase 4 open-play interval eligibility;
- substitution and period boundaries respected.

### Provider-specific implementation details to resolve outcome-blind

- raw field names and table joins;
- coordinate origin, axis order, scale, and pitch-dimension fields;
- time, frame, period, and match clocks;
- missing/extrapolated/quality flags;
- lineup, substitution, goalkeeper, and identity fields;
- possession-bearing events and restart vocabulary;
- ball validity and event–tracking synchronization.

A schema problem is a **measurement-portability issue**, not evidence of football-behavior failure. It must not be repaired by silently altering the construct.

## Sampling and eligibility

Primary intervals transfer the Phase 4 family: non-overlapping half-open $[t,t+5)$ windows aligned to the smallest elapsed-match multiple of five not before tracking begins in each period, exactly 125 frames at 25 Hz. An interval must remain within one period; have one event-defined possession team throughout; contain no restart, set piece, or ball-out passage; have a complete valid ball path; and contain at least nine complete defending outfield players, with the goalkeeper excluded. Every member of the fixed complete outfield set becomes a focal observation.

Provider event semantics may not be invented. If the Phase 4 possession/restart rule cannot be mapped faithfully from documented IDSSE fields, stop before outcomes and use the implementation-resolution procedure below.

### Exact usable-match definition and support

A match is **primary-usable** if and only if all of the following hold before focal-relative outcomes are inspected:

1. provider fields can be mapped faithfully to metric coordinates, periods/time, continuous player/team identities, goalkeepers, lineups/substitutions, defending team, ball validity, possession continuity, and open-play/restart exclusions;
2. no unresolved coordinate, identity, goalkeeper, substitution, ball, possession, or event-synchronization issue can alter interval membership or the leave-one-out reference;
3. at least 100 eligible five-second intervals remain;
4. each defending team contributes at least 40 eligible intervals; and
5. at least eight distinct focal defenders each contribute at least 25 eligible intervals.

If any condition fails, the match is not primary-usable and contributes only to the portability report, not the behavioral A/B/C evidence.

The previous draft also required 800 defender-interval observations. That gate is removed as logically redundant: every eligible interval contains at least nine complete defending outfield players and every one becomes a focal observation, so 100 eligible intervals already imply at least 900 valid defender-interval observations. The interval threshold protects temporal/match coverage; the team and focal-defender thresholds protect representation across both teams and player identities.

Strong external replication requires at least six of seven primary-usable matches. Five usable matches permit behavioral evaluation but cannot support A. Fewer than five yields **P — portability-inconclusive**, not football-behavior failure.

All exclusions and attrition must be reported by match and reason. No support rule may be loosened after focal outcomes.

## Primary replication dimensions

### A. Construct portability and data quality

Report whether the same reference and outcome can be computed, provider mappings, missingness, substitutions, active-player counts, interval attrition, match/team/player support, and any outcome-blind amendments. Coordinate and timing sanity checks precede outcomes.

Pathological behavior includes negative/nonfinite path values; exact-zero paths inconsistent with the underlying trajectories; implausible discontinuities traceable to identity, period, coordinate, or substitution errors; zero IQR caused by quantization; or conclusions driven by one player or a small number of intervals. Such findings trigger implementation audit before behavioral interpretation.

### B. Distributional behavior

Report median, IQR, and 10th/25th/50th/75th/90th percentiles overall and separately by match and defending team; show distributions by match; and report eligible-defender summaries without role inference. Numerical equality to the Metrica median, IQR, correlations, or cells is neither expected nor a success criterion.

Construct portability is supported when every primary-usable match has all paths finite/nonnegative, median and IQR greater than $10^{-8}$ m, and no unresolved pre-outcome mapping issue. Report the proportion of paths at or below $10^{-8}$ m as a data-quality diagnostic, not an independent behavioral boundary. If unexpectedly high numerical-zero prevalence suggests quantization or another provider/schema defect, use the outcome-blind implementation-resolution procedure; if it makes the median or IQR degenerate, the frozen distributional criteria already fail. Cross-match magnitude differences are evidence to report, not nuisance to normalize away.

### C. Generic activity relationships

For each match, report separate Spearman relationships between focal-relative path and:

1. focal absolute path;
2. full defending-outfield centroid path;
3. summed defending-outfield paths; and
4. ball path.

Report interval-cluster bootstrap uncertainty. Do not residualize, fit an activity-free score, or combine activity channels. The primary external property is direction and broad structure across matches, not equality to Metrica coefficients.

### D. Common-translation invariance

Apply one observed valid collective translation trajectory identically to fixed relative defender positions. The maximum focal-relative path must be no greater than $10^{-8}$ m under every implemented smoothing setting. Failure is a calculation/reference failure and blocks behavioral interpretation.

### E. Temporally misaligned collective reference

Within each match, assign eligible intervals to three collective-activity bins before focal outcomes by stable-ranking full defending-outfield-centroid path ascending, breaking equal-path ties by period, start time, then interval identifier, and assigning rank $r$ among $N$ intervals to $\min(2,\lfloor3r/N\rfloor)$ for zero-based $r$. This creates a deterministic low/middle/high activity bin without quantile-interpolation ambiguity.

For each contemporaneous interval, candidate references must be eligible, non-overlapping, from the same match, period, defending team, and collective-activity rank bin, and 10–120 seconds away by interval start. Select the candidate with minimum absolute temporal separation; earlier start wins an exact tie, then interval identifier. No continuous activity-distance optimization is used beyond exact same-bin membership, and the rule cannot be changed after outcomes.

Replace the contemporaneous leave-one-out collective trajectory with the selected interval's equivalent trajectory while retaining the focal trajectory. Control support is the percentage of eligible intervals with a valid selected reference.

A match-level control **passes** when support is at least 70%, the paired median difference (misaligned minus contemporaneous) is strictly positive, and strictly more than 50% of supported focal observations have larger misaligned path. A **material contradiction** requires adequate support but both a strictly negative paired median and fewer than 50% positive paired differences. Exact-zero/equal-direction cases, or support below 70%, are inconclusive and fail the match-level pass without counting as material contradiction. Bootstrap uncertainty is reported but does not change this directional classification.

The 70% support floor prevents a control result from being inferred from a narrow subset; the strict-majority rule requires the inappropriate reference to worsen the description for more focal observations than it improves. Neither requires a Metrica-sized effect. This is a reference-alignment check, not a tactical null or evidence of coordination.

### F. Window and smoothing robustness

Primary: five seconds and seven frames. Frozen sensitivities: 4/5/6-second windows crossed with centered 5/7/9-frame position means. At 25 Hz these correspond to the same temporal scales as Phase 4B. Means are applied separately to x/y within intervals, without padding or interpolation; invalid edge frames are omitted from path accumulation.

If verified sampling differs from 25 Hz despite current metadata, do not silently reuse frame counts. Resolve physical-time-equivalent smoothing outcome-blind and version the protocol if the change is material.

For each of the nine settings, a **setting-consistent result** requires all paths finite/nonnegative, median and IQR greater than $10^{-8}$ m, none of the four activity relationships at $\rho\leq-0.10$, at least 70% misaligned-control support, a nonnegative misaligned paired median, and at least 50% nonnegative paired focal differences. Report numerical-zero prevalence for every setting, but do not apply an independent percentage cutoff. A match passes sensitivity if the primary 5-second/7-frame setting satisfies the core distribution and activity rules and passes the strict match-level control; at least eight of nine settings are setting-consistent; and no setting has either any activity relationship at $\rho\leq-0.10$ or a material misaligned-control contradiction. Allowing one inconclusive setting protects against a single support-edge combination without permitting a directional reversal.

### G. Cross-match hierarchy and heterogeneity

The hierarchy is **frames ⊂ intervals ⊂ possessions/sequences ⊂ players ⊂ teams ⊂ matches**. Seven matches—not millions of frames—are the main replication gain.

Primary reporting is per match. Team and eligible-player summaries show heterogeneity; pooled summaries are secondary and may not override match-level contradiction. Bootstrap resampling is clustered by interval within match. No complex hierarchical model is required. If inferential modeling later becomes necessary, it requires a separate pre-outcome amendment.

Use 10,000 interval-cluster bootstrap resamples per match with seed `20260830` for reported uncertainty in medians and activity relationships. Bootstrap intervals contextualize estimates but do not replace the match-level directional criteria or create frame-level significance claims.

## Activity-conditioning strategy

Activity is handled in three explicitly separate ways:

1. **Primary continuous relationships:** per-match Spearman associations with the four activity quantities above. These drive directional replication.
2. **Metrica-threshold transport diagnostic:** apply the already-frozen Metrica physical-metre cuts unchanged. Report cell occupancy and medians without requiring the IDSSE distribution to match Metrica or requiring all cells to be populated. This asks whether the original absolute activity strata transport.
3. **Provider-portable descriptive stratification:** define within-match terciles from activity quantities only, before focal-relative outcomes. Use focal-absolute × full-centroid 3×3 cells and separate aggregate/ball terciles descriptively. These bins compare relative activity context within each match; because occupancy is created by construction, they are not evidence of distributional replication, cannot count as evidence that Metrica physical thresholds transported, and do not enter the A/B/C/P classification.

No IDSSE outcome is used to define activity bins. No IDSSE-specific cut is tuned to improve agreement.

## Ball and open-play mapping

The focal-relative construct itself requires defender positions, team identity, goalkeeper exclusion, and time. Phase 4C comparability additionally requires complete valid ball tracking and exclusion of possession changes, restarts, set pieces, and ball-out passages because these conditions define the inherited open-play sample and ball-activity diagnostic.

Metrica column names, event labels, and its “latest possession-bearing event” implementation are not scientific requirements. An IDSSE possession flag, event code, restart state, or synchronized metadata field is implementation-equivalent when it represents the same football condition deterministically and without focal outcomes. Coordinate-field renaming, provider event-vocabulary crosswalks, and timestamp tolerances justified from schema/synchronization checks are also implementation mappings.

Removing complete-ball eligibility, admitting restarts or possession changes, inferring possession from focal-relative outcomes, changing the football meaning of open play, or dropping ball activity to increase support changes the protocol. Such changes require a versioned pre-outcome amendment. If no faithful outcome-blind mapping exists, affected matches are not primary-usable and may lead to P.

## Exact match-level core replication rule

A match counts as a **core-replicating match** if and only if all of the following hold:

1. it is primary-usable;
2. every primary focal-relative path is finite and nonnegative, and its median and IQR are strictly greater than $10^{-8}$ m;
3. primary focal-relative path has a positive Spearman point estimate with focal absolute path;
4. none of the four primary activity relationships is materially reversed, prospectively defined as $\rho\leq-0.10$;
5. the match-level misaligned-reference control passes; and
6. the match-level sensitivity rule passes.

The $10^{-8}$ path tolerance matches the invariance tolerance and identifies numerical zero rather than slow movement. Numerical-zero prevalence is reported but has no independent hard cutoff: provider precision, quantization, preprocessing, or genuine stationarity can affect it, while prevalent zeros already cause failure when they degenerate the median or IQR. The $-0.10$ boundary distinguishes a material adverse relationship from weak or near-null sign variation; it is frozen before IDSSE inspection and is not a tactical effect threshold. For the full-centroid, aggregate-defender, and ball relationships, signs and magnitudes are reported, but values in $-0.10<\rho\leq0$ do not independently make a match non-core.

Ball activity is required for primary eligibility, so every primary-usable match must have a computable ball-path relationship. An unavailable ball-path association indicates unresolved eligibility or implementation, not a reduced activity rule.

## Material activity-reversal accounting

The $\rho\leq-0.10$ rule applies separately to focal absolute path, full defending-outfield centroid path, summed defending-outfield paths, and ball path at the primary setting.

- One reversed variable in one match is reported, makes that match non-core, but is an **isolated reversal** and does not alone preclude A if six other matches are core.
- The same variable reversed in two matches, or two or more variables reversed within one match, is a **repeated/concentrated reversal**. It precludes A and leads to B unless a C rule applies.
- The same variable reversed in at least three usable matches, or at least two variables reversed within each of at least two usable matches, is a **behavioral failure pattern** contributing directly to C.

Correlations need not equal Metrica magnitudes. Bootstrap intervals are descriptive uncertainty only; the frozen point-estimate rules determine classification.

## Mutually exclusive Phase 4C conclusion

Apply this precedence mechanically:

1. Determine primary usability without focal-relative outcomes.
2. If fewer than five matches are primary-usable, classify **P** and do not make a behavioral replication claim.
3. With at least five usable matches, if any C criterion holds, classify **C**.
4. Otherwise, if every A criterion holds, classify **A**.
5. Otherwise classify **B**.

### A — Strong external replication

All of the following are required:

- at least six of seven matches are primary-usable;
- common-translation invariance passes;
- at least six of seven total target matches are core-replicating;
- at least six matches pass the misaligned-reference control;
- no repeated/concentrated activity reversal is present;
- no primary-usable match has a material misaligned-control contradiction.

This establishes external measurement replication only.

### B — Mixed / partial external replication

After P and C have been excluded, classify B whenever A is not met. Examples include:

- four or five total matches are core-replicating, or six are core-replicating but one A criterion is not met;
- distributional behavior is computable but activity or misaligned-reference behavior is inconsistent by match/team;
- one or two matches have material misaligned-control contradictions;
- isolated or repeated/concentrated activity reversals remain below the C frequency;
- one frozen dimension replicates broadly while another is mixed;
- sensitivity conclusions are stable in some matches but not others; or
- provider-portability decisions limit comparability without changing the construct.

### C — Behavioral external-replication failure

With at least five primary-usable matches, classify C if any of the following holds:

- common-translation invariance fails after implementation audit;
- three or fewer total matches are core-replicating;
- the same activity relationship has $\rho\leq-0.10$ in at least three usable matches;
- at least two activity relationships have $\rho\leq-0.10$ within each of at least two usable matches;
- at least three usable matches materially contradict the misaligned control; or
- at least three usable matches fail the frozen sensitivity rule.

Do not use pooled significance to override C. Exact Metrica magnitudes never enter classification.

The six-of-seven A rule demands consistency in all but at most one target match. The three-match C boundaries treat directional/control/sensitivity failure in nearly half the dataset as behavioral non-replication rather than an isolated anomaly. The separate “two variables in two matches” activity rule captures breadth across both variables and matches. One or two isolated match failures remain visible as B rather than being averaged away.

### P — Portability-inconclusive

Classify P when fewer than five matches are primary-usable because equivalent implementation or minimum support cannot be established, including unresolved provider mapping, identity, coordinate, goalkeeper, substitution, ball, possession, event, or missingness problems. P is not evidence that football behavior failed to replicate. Report whether the limitation is dataset-wide or match-specific and stop before behavioral A/B/C interpretation.

## Inferential purpose of frozen numeric boundaries

Every remaining numeric boundary has a specific prospective role. The 100-interval minimum protects temporal support; 40 intervals per defending team prevents one-side domination; and eight focal defenders with 25 intervals each prevents a very small player subset from carrying a match. The 70% misaligned-control support floor requires broad applicability, while its strict median and majority directions require the inappropriate reference to worsen the description without imposing an effect-size target. The $\rho\leq-0.10$ boundary separates material reversal from weak or near-null deviations. The 5-second/7-frame primary and fixed 4/5/6-second × 5/7/9-frame family transfer the established measurement scales; eight of nine consistent settings permits one support-edge result but not a material reversal. The six-of-seven A requirement demands replication in all but one target match, and the three-match C boundaries represent repeated failure across nearly half the dataset. The $10^{-8}$ tolerances identify numerical zero/calculation failure, not football effect sizes. No numeric boundary is justified by subjective visual resemblance to Metrica.

## Outcome-blind implementation-resolution procedure

After first data access, perform only provenance, checksum, license/access, schema, coordinate, timing, identity, goalkeeper, lineup/substitution, event/possession, ball-quality, missingness, and support checks. Do not construct $\mathbf r_d(t)$ or any focal-relative outcome during this stage.

If an unforeseen provider-specific issue requires a methodological choice:

1. document the issue and all plausible mappings without focal outcomes;
2. choose the mapping that most faithfully preserves the frozen construct and inclusion logic, not the one likely to match Metrica;
3. record checksums and a deterministic implementation decision;
4. if the resolution is implementation-only and does not alter the construct, primary quantities, success criteria, or inferential role, add a pre-outcome implementation note and continue;
5. if it changes the construct, eligibility meaning, outcome, negative control, robustness family, or A/B/C/P criteria, stop, version/amend the protocol, obtain review, and only then inspect outcomes; and
6. if no faithful mapping exists, record measurement-portability failure rather than substitute a new primitive.

No post-outcome threshold, normalization, filtering, interval, reference, missingness, or subgroup change is permitted to rescue replication. No illustrative IDSSE sequence may be selected by focal-relative outcome before the replication conclusion.

## Explicit nonclaims

Phase 4C does not test or establish tactical defensive response, pinning, dragging, tracking, covering, handoffs, step-outs, relational reconfiguration, attacker association, attribution, causation, defensive quality, gravity, or off-ball value. It does not define an activity-free focal-departure score or claim provider-invariant numerical magnitudes.
