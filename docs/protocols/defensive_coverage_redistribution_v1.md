# Defensive Coverage Redistribution v1 — Frozen Game 1 Development Protocol

**Status:** frozen prospectively before any protected coverage outcome

**Freeze date:** 2026-09-03

**Starting checkpoint:** `d8a1f42a5915b42a9fa8f79c292f79c25361f393`

## 1. Football question and boundary

When defenders reorganize locally around one attacking movement, is stronger focal-local defensive response associated with deterioration in the defence's ability to maintain distinct geometric coverage over the other nine attacking outfield players?

This protocol does **not** use simple nearest-defender separation. It represents multi-attacker coverage as the minimum mean distance needed to pair every non-focal attacker with a different outfield defender. The pairings are a mathematical capacity representation, not observed marking assignments. A successful v1 could establish only an observational association between focal-local response and geometric coverage redistribution.

No Game 1 coverage outcome, model coefficient, interval, or empirical figure existed when this protocol was frozen. Metrica Sample Games 2 and 3 and IDSSE are prohibited during Game 1 development.

## 2. Inherited sample and coordinates

Use Metrica Sample Game 1 and inherit the exact [Concurrent Attacker–Defensive Geometry v1](concurrent_attacker_defensive_geometry_v1.md) conventions:

- fixed 105 × 68 m pitch coordinates, centre origin, +x right and +y up;
- 25 Hz tracking with the frozen seven-frame centred rolling position mean;
- period-origin anchors $t=o_p+2+4k$;
- pre-context $[t-2,t]$ and concurrent interval $[t,t+2]$;
- complete supported samples with no interpolation or partial support;
- event-derived attacking team, open-play/restart exclusions and cadence rules;
- Home11 and Away25 excluded as goalkeepers;
- D1–D10 fixed at $t$ by focal-attacker distance, with canonical-player-ID tie handling; and
- every simultaneous eligible focal attacker retained and grouped at the same anchor.

Coverage validity additionally requires the focal attacker, all nine other attacking outfield players and all ten defending outfield players to have complete support from $t-2$ through $t+2$. No opponent possession-defining event (`PASS`, `RECOVERY`, `SET PIECE` or `SHOT`) may occur after $t$ through $t+2$. Same-team events do not end eligibility. The rule is conservative event-clock continuity, not proof of possession or attacking intent.

Every retained row is one focal-attacker perspective at one anchor. All focal perspectives sharing an anchor remain grouped. No pass, receipt, shot, xG, later outcome, visual interest or tactical label selects a row.

## 3. Prospective other-attacker set

For focal attacker $a$ at $t$, define $\mathcal A_{-a}$ as the other nine same-team outfield players. Their identities are frozen from $t$ through $t+2$. All nine are included equally: there is no local/remote recipient rank, future reranking or improving-attacker selection.

The complete defending-outfield set $\mathcal D$ contains ten fixed player identities. One defender can be unused by the nine-pair matching. No role, responsibility, marking or handoff is inferred.

## 4. Primary coverage consequence

At endpoint $u\in\{t,t+2\}$, construct the $9\times10$ Euclidean cost matrix

$$
C_{jd}(u)=\lVert\mathbf x_j(u)-\mathbf x_d(u)\rVert_2,
\qquad j\in\mathcal A_{-a},\ d\in\mathcal D.
$$

Let $\Pi$ be the set of injective mappings from the nine attackers to nine distinct defenders. Define mean distinct-defender coverage cost

$$
G_a(u)=\frac{1}{9}\min_{\pi\in\Pi}
\sum_{j\in\mathcal A_{-a}} C_{j,\pi(j)}(u).
$$

Compute the rectangular assignment in float64 with `scipy.optimize.linear_sum_assignment`. Its scalar minimum cost is authoritative. Matched identities are descriptive only; equal-cost alternative pairings do not imply tactical ambiguity or assignment. Missing endpoint geometry invalidates the focal row; it is never interpolated.

The primary outcome is

$$
Y_a=G_a(t+2)-G_a(t),
$$

in metres. Positive $Y_a$ means the minimum average distance required to give all nine other attackers distinct defender coverage increased during the shared interval. “Coverage loss” is permitted only as shorthand for this geometric increase. It is not pass availability, accessibility, control, danger, value or defensive failure.

This matching can distinguish the central synthetic cases. If one defender leaves an attacker and another defender replaces them, the optimum can remain unchanged. If no defender compensates, the minimum cost increases. Unlike Opportunity Redistribution v1, it does not reduce each attacker independently to their nearest defender.

## 5. Defensive-response predictor

For each start-ranked defender, compute the inherited concurrent focal-relative path $P^{rel}_{Dk}$ using the leave-one-out defending-outfield centroid. The sole primary response predictor is the observed anchor-level contrast

$$
D_a=\overline{P^{rel}}_{D1:D3}-\overline{P^{rel}}_{D4:D7},
$$

in metres. This is the replicated scalar local-versus-middle response quantity, not a fitted coefficient. The attacker-aligned coordination-form contrast remains prior supporting geometry but is not added to v1, avoiding a two-predictor interpretation problem.

The predicted primary sign is positive: stronger focal-local relative movement corresponds to greater increase in distinct-defender coverage cost over the other attackers.

## 6. Timing and ball role

$D_a$ and $Y_a$ are both measured over $[t,t+2]$. This is a concurrent association within a shared interval, not a downstream causal chain, response-onset model or reaction-time claim. A later window is not introduced because the project has not validated a universal response onset and because doing so would add an arbitrary timing assumption.

The ball does not enter $G_a$, eligibility or the model. Event labels establish the attacking team and open-play continuity. Ball path may be reported descriptively when observed, but missing ball coordinates do not remove an otherwise valid focal row. Ball-carrier identity, passing corridors, ball flight, pass completion, xThreat, EPV and value are excluded.

## 7. Model and primary estimand

Construct exactly these six columns for each eligible focal row:

- $A$: concurrent focal-attacker path;
- $D$: concurrent response contrast above;
- $G_0$: $G_a(t)$;
- $M_O$: mean concurrent absolute path of the nine other attackers;
- $A_{pre}$: focal-attacker path over $[t-2,t]$; and
- $D_{pre}$: the same fixed-rank response contrast over $[t-2,t]$.

Within each period/time anchor, demean $Y$ and every column across simultaneous eligible focal attackers. Groups with fewer than two eligible focal attackers are unidentified and excluded. This absorbs anchor-shared ball path, defensive-centroid movement, unit width/depth and broad match activity. Those quantities must still be reported descriptively, but adding them as columns after demeaning would create zeros rather than extra adjustment.

Fit the fixed six-column, no-intercept float64 OLS

$$
\widetilde Y=
\beta_A\widetilde A+\beta_D\widetilde D+
\beta_G\widetilde G_0+\beta_O\widetilde M_O+
\beta_{Apre}\widetilde A_{pre}+
\beta_{Dpre}\widetilde D_{pre}+\epsilon
$$

with `numpy.linalg.lstsq(..., rcond=None)`. Every point and bootstrap design must have full column rank.

The sole primary estimand is $\beta_D$, reported as metres of coverage-cost change per metre of focal-local-versus-middle response contrast (numerically dimensionless). Positive means focal perspectives with greater $D$ had greater geometric coverage-cost increase than other focal perspectives at the same anchor, conditional on the frozen columns. It is not a causal effect.

## 8. Uncertainty

Use 2,000 deterministic bootstrap replicates with master seed `20260905`; reserve `SeedSequence.spawn(2)[0]` for Game 1 and child 1 for a possible later Game 2 addendum. Resample independent 60-second blocks within period with replacement, retaining terminal partial blocks. Every simultaneous focal row and all player geometry at an anchor remain grouped. Redo within-anchor demeaning after resampling. Require at least 1,900 valid full-rank replicates and use a two-sided percentile 95% interval.

## 9. Frozen controls and robustness

These checks cannot rescue a nonpositive primary estimate.

1. **Focal-identity permutation control.** For each of 200 replicates with seed `20260906`, independently apply a random nonzero cyclic shift to the paired $(D,D_{pre})$ values within each anchor after sorting focal attackers by canonical ID. Preserve outcomes, other covariates and anchor membership. The control passes when observed $\hat\beta_D$ exceeds the 95th percentile of permuted estimates.
2. **Remote-defender comparator.** Replace $D$ and $D_{pre}$ with D8–D10 minus D4–D7 focal-relative path contrasts. Use the same rows/model/bootstrap. The control passes when the primary point estimate is greater than the remote-comparator point estimate. The comparator is not a second primary model.
3. **Frozen focal-movement trim.** Exclude complete focal anchors with concurrent $A>12.198443079831405$ m, the already-closed threshold used by Opportunity Redistribution v1. The robustness passes when $\hat\beta_D>0$ and retains at least 50% of the absolute primary magnitude. No new percentile is calculated.
4. **Fixed-start matching description.** Freeze the start optimum and evaluate those same links at $t+2$. Report its coefficient descriptively. It is expected to treat handoff-like compensation differently and is not a robustness gate.
5. **Two-nearest depth description.** For each other attacker, average its two nearest defender distances at each endpoint and average the nine changes. This is nonclassifying and explicitly retains independent-nearest semantics; it cannot replace the primary after results.
6. **Rigid transformations and relabeling.** $G$, $Y$ and $D$ must be invariant to shared translation, rotation and reflection, and scalar $G$ must be invariant to player-ID relabeling. Matching identities may change under exact ties without changing the scalar.

Report defensive-centroid path, start/end width and depth, ball path, focal and other-attacker paths, matching-link churn and unused-defender identity descriptively. No subgroup, band, rank, matching penalty or threshold may be selected after inspection.

## 10. Synthetic construct-validity gates

Before freeze, the pure-geometry implementation must pass all six fixtures:

1. focal-local response with perfect defender compensation: high $D$, approximately neutral $Y$;
2. the same local response without compensation: high $D$, positive $Y$;
3. shared collective translation with preserved geometry: approximately zero $D$ and $Y$;
4. independent movement by another attacker: positive $Y$ with approximately zero $D$, demonstrating why $M_O$ is required;
5. focal movement ignored by defenders: approximately zero $D$ and $Y$; and
6. multi-defender collapse toward the focal movement: high $D$ and larger positive $Y$.

These are design tests, not empirical evidence or tactical labels. Failure of any fixture prevents empirical execution until an explicit pre-result protocol revision.

## 11. Game 1 development status

Evaluate in this order:

1. **GAME 1 COVERAGE REDISTRIBUTION DEVELOPMENT INVALID** — frozen hash, sample/support, complete-set, geometry, design-rank, solver, bootstrap-minimum, synthetic-gate or deterministic-serialization failure.
2. **GAME 1 COVERAGE REDISTRIBUTION DEVELOPMENT NOT SUPPORTED** — valid execution and primary $\hat\beta_D\le0$.
3. **GAME 1 COVERAGE REDISTRIBUTION DEVELOPMENT COHERENT** — valid execution; $\hat\beta_D>0$; the primary 95% interval is strictly above zero; the focal-identity permutation passes; the primary point estimate exceeds the remote comparator; and the frozen trim passes.
4. **GAME 1 COVERAGE REDISTRIBUTION DEVELOPMENT MIXED** — every other valid execution with $\hat\beta_D>0$.

Secondary quantities cannot rescue the primary. A valid null or negative result is not INVALID.

## 12. Validation sequence and stopping rule

Execute Game 1 only under separate authorization, then stop. A held-out Game 2 addendum may be designed only after Game 1 closes and only if the construct remains scientifically warranted; no Game 2 result is authorized here. IDSSE is conditional on coherent within-provider evidence and provider-equivalent complete-set support. Metrica Sample Game 3 remains untouched.

## 13. Claim boundary

The maximum development claim if coherent is:

> In Metrica Sample Game 1, stronger concurrent focal-local versus middle defender-relative movement was associated with an increase in the minimum mean distinct-defender matching distance over the other nine attacking outfield players, after the prospectively specified within-anchor and movement-context adjustments.

Even a coherent result cannot establish attacker causation or influence, defensive attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoffs, passing availability, pitch control, space creation, tactical success or failure, player quality, gravity or off-ball value.

## 14. Planned governed outputs

Persist a manifest, eligibility/exclusion ledger, complete model table, bootstrap table, permutation control, remote comparator, trim, descriptive alternative representations, synthetic-gate record, hard QC, governed hashes, independent reproduction record, figures and a bounded result report. Licensed observation-level derivatives remain local-only under repository policy. Every governed machine-readable output must reproduce byte-for-byte before closure.
