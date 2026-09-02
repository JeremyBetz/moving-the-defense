# Opportunity Redistribution v1 — Frozen Game 1 Development Protocol

**Status:** frozen before any opportunity outcome was computed or inspected

**Freeze date:** 2026-09-02

**Starting checkpoint:** `858b0caa0d99cdb17be0a6cad2e6f8cb0ae21604`

## Purpose and boundary

Closed work established a reproducible focal-relative movement primitive and replicated a stronger concurrent attacker-path association among near than middle defender ranks in two Metrica sample matches. This protocol asks the next football question:

> When an attacker moves during open play and the nearby defence undergoes greater concurrent geometric change, does a different attacker experience a measurable improvement in attacking opportunity?

Here **opportunity** means only defender separation. It is not pass availability, pitch control, expected goals, attacking value, tactical success, or causal space creation. Tracking observes geometry, not why it occurred.

No Game 1 opportunity sample, outcome, coefficient, interval, or figure existed when this protocol was frozen. Game 2 is held out and requires a separate replication addendum after Game 1 closes. Game 3 and IDSSE remain untouched.

## Associational structure

Let $A$ be concurrent focal-attacker path, $D$ the focal anchor's closed local defensive-geometry contrast, and $O$ differential separation change for other attackers. The primary question is whether $D$ is conditionally associated with $O$ beyond $A$, initial separation, recipient movement, and prior focal/defensive movement. This is not a causal chain, mediation analysis, or attribution model.

## Inherited sample and time

Use Metrica Sample Game 1 development data and the exact Concurrent Attacker–Defensive Geometry v1 conventions:

- fixed 105 × 68 m pitch coordinates, centre origin, +x right, +y up, with no attacking-direction normalization;
- 25 Hz tracking and seven-frame centred rolling position mean;
- no interpolation or partial support;
- period-origin anchors $t=o_p+2+4k$;
- pre-context positions from $t-2$ through $t$ and concurrent positions from $t$ through $t+2$;
- prior increments ending in $(t-2,t]$ and concurrent increments ending in $(t,t+2]$;
- exact-frame endpoint tolerance and inherited open-play/restart rules;
- event-derived attacking team at $t$; and
- all simultaneous focal attackers retained and grouped.

Opportunity validity adds two prospective requirements:

1. the focal attacker, the other nine attacking outfield players, and all ten defending outfield players have complete support from $t-2$ through $t+2$; and
2. no possession-defining event (`PASS`, `RECOVERY`, `SET PIECE`, or `SHOT`) by the opposing team occurs after $t$ through $t+2$. Same-team events do not end eligibility. This is a conservative event-clock continuity rule, not proof of uninterrupted possession.

Home11 and Away25 are goalkeepers and are excluded. The focal attacker may be the ball carrier. A recipient may be the ball carrier because ball-carrier identity is not inferred and the selected construct does not claim pass availability. No episode boundary, receipt, pass outcome, shot, xG, or later success selects the sample.

## Prospective other-attacker definition

For each focal attacker $a$ at $t$, take the other nine same-team outfield attackers with complete support. Rank them R1–R9 by Euclidean distance to $a$ at $t$, breaking exact ties by ascending canonical player ID, and freeze membership:

- focal-local recipients: R1–R3;
- middle recipients: R4–R6, descriptive;
- focal-remote recipients: R7–R9.

Every retained focal anchor must contain all nine recipients. No recipient is selected because their later separation improves.

## Primary opportunity construct

At endpoint $u$, define recipient $j$'s nearest-defender separation

$$
s_j(u)=\min_{d\in\mathcal D}\|\mathbf x_j(u)-\mathbf x_d(u)\|_2,
$$

where $\mathcal D$ is the complete ten-player defending-outfield set. Nearest identity may differ between endpoints; no responsibility or assignment is implied.

Define $\Delta s_j=s_j(t+2)-s_j(t)$ and the primary differential opportunity outcome

$$
O=\frac{1}{3}\sum_{j\in R1:R3}\Delta s_j-
  \frac{1}{3}\sum_{j\in R7:R9}\Delta s_j.
$$

Positive $O$ means attackers initially closest to the focal attacker gained more defender separation than the three focal-remote attackers. It does not mean a pass was available or that the change was beneficial. This local-minus-remote construction distinguishes differential redistribution from a shared increase in separation; it does not assume opportunity is globally zero-sum.

## Defensive-geometry predictor

Rank defenders D1–D10 by their Euclidean distance to the focal attacker at $t$, with canonical-ID tie handling and fixed membership exactly as in the closed concurrent protocol. For each defender, compute concurrent focal-relative path using the leave-one-out defending-outfield centroid. The sole defensive predictor is

$$
D=\overline{P^{rel}}_{D1:D3}-\overline{P^{rel}}_{D4:D7}.
$$

This is the per-anchor realization corresponding most directly to the replicated primary near-minus-middle construct. Endpoint deformation remains a separate descriptive sensitivity and is not combined with $D$.

## Covariates and within-anchor identification

For each focal-attacker anchor construct:

- $A$: concurrent focal-attacker path;
- $D$: concurrent defensive contrast above;
- $S_0$: local-minus-remote mean nearest-defender separation at $t$;
- $M_R$: local-minus-remote mean concurrent recipient path;
- $A_{pre}$: prior focal-attacker path; and
- $D_{pre}$: the same fixed-rank near-minus-middle focal-relative defender-path contrast over the pre-context interval.

Within each period/time anchor, demean $O$ and every predictor across simultaneous focal attackers. Groups with fewer than two eligible focal attackers are excluded as unidentified. Fit the fixed six-column no-intercept float64 OLS

$$
\widetilde O=\beta_A\widetilde A+\beta_D\widetilde D+
\beta_S\widetilde S_0+\beta_R\widetilde M_R+
\beta_{Apre}\widetilde A_{pre}+\beta_{Dpre}\widetilde D_{pre}+\epsilon.
$$

Every point and bootstrap fit must use `numpy.linalg.lstsq(..., rcond=None)`. The within-anchor transformation absorbs quantities shared by simultaneous focal attackers—including ball movement, broad phase, and defensive-centroid translation—without pretending to remove focal-specific or unobserved confounding. An anchor fixed effect would absorb anchor-level main effects in an equivalent dummy-variable formulation; demeaning is the governed implementation.

The sole primary estimand is $\beta_D$. The predicted sign is positive: greater focal-local versus middle defender movement is associated with relatively greater separation gain for focal-local versus focal-remote teammates, conditional on the frozen terms.

## Uncertainty

Use 2,000 bootstrap replicates with master seed `20260902`, `SeedSequence.spawn(2)[0]` for Game 1, and child 1 reserved for a future Game 2 addendum. Resample independent 60-second blocks within period with replacement, retaining terminal partial blocks. A period/time anchor, every simultaneous focal attacker, all nine recipients, and both endpoint defender sets remain grouped. Redo within-anchor demeaning after resampling complete anchor groups. Require at least 1,900 valid full-rank replicates. Use the percentile 95% interval for $\beta_D$.

## Prospectively frozen robustness

These checks cannot rescue a failed primary result:

1. **Fixed-start defender:** replace $s_j(t+2)$ with distance at $t+2$ to the defender nearest $j$ at $t$; require the $\beta_D$ point sign to remain positive.
2. **Three-nearest separation:** replace $s_j(u)$ with the mean distance to the three nearest defenders at each endpoint; require the $\beta_D$ point sign to remain positive.
3. **Extreme focal movement:** exclude complete focal anchors with $A>12.198443079831405$ m, the already-closed Game 1 threshold; require the $\beta_D$ point sign to remain positive. No new percentile is calculated.
4. **Secondary deformation:** replace $D$ with near-minus-middle endpoint RMS deformation. Report its point estimate and interval descriptively; it cannot classify v1.
5. **Rigid transforms and player-ID relabeling:** the primary opportunity outcome and $D$ must be invariant under shared translation, rotation, reflection, and canonical-label permutations that preserve geometry and tie order.

Report initial nearest-defender identity churn between endpoints, pitch-boundary proximity, full/local/remote separation changes, recipient paths, and sample attrition descriptively. No threshold is tuned after inspection.

## Negative controls deliberately not adopted

A shifted-time placebo would impose an unsupported temporal story on a concurrent design. Far defenders are not a credible negative control because closed concurrent results showed far coefficients above middle descriptively. Shuffling focal identity within an anchor destroys the prospectively defined focal-local recipient geometry rather than preserving a meaningful football null. These controls are therefore not used. The within-anchor local-minus-remote outcome and anchor demeaning are the primary protections against generic opening and shared activity.

## Game 1 status

Evaluate in this order:

1. **GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT INVALID** — any frozen-hash, sample-integrity, support, leakage, geometry, design-rank, solver, bootstrap-minimum, or deterministic-serialization failure.
2. **GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT NEGATIVE** — valid execution and primary $\hat\beta_D\le0$.
3. **GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT COHERENT** — valid execution, $\hat\beta_D>0$, its 95% interval strictly above zero, and positive signs in all three primary robustness checks.
4. **GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT MIXED** — every other valid execution with positive $\hat\beta_D$.

A raw $A$ association, overall separation gain, secondary deformation, subgroup pattern, or descriptive metric cannot rescue the primary result. A valid null result is not INVALID.

## Claims and stopping rule

The maximum Game 1 claim if coherent is:

> In Metrica Sample Game 1, greater concurrent focal-local versus middle defender movement was associated with relatively greater nearest-defender separation gain for other attackers initially local rather than remote to the focal attacker, after the prospectively specified within-anchor and movement-context adjustments.

This reaches Level 2: association between defensive geometric change and another attacker's opportunity proxy. The label “redistribution” is justified only descriptively by the within-anchor local-minus-remote contrast. It does not establish Level 4 attacker attribution or Level 5 value, nor causation, reaction, responsibility, marking, dragging, pinning, tracking, pass availability, controlled space, tactical success, gravity, or off-ball value.

Execute Game 1 development only under separate authorization. Stop after its governed status. Game 2 may be opened only after Game 1 closes and a heldout addendum freezes replication criteria. External IDSSE testing is conditional on sufficiently coherent Game 1 and Game 2 evidence for the complete chain.
