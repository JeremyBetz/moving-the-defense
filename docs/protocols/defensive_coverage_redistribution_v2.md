# Defensive Coverage Redistribution v2 — Frozen Game 1 Development Protocol

**Status:** frozen prospectively before any empirical coverage outcome

**Freeze date:** 2026-09-03

**Starting checkpoint:** `c3346602f706dedab237a0b2c4148485e5f31ade`

**Supersedes:** [Defensive Coverage Redistribution v1](defensive_coverage_redistribution_v1_rejection.md), rejected before execution because repeated focal exclusion plus within-anchor demeaning did not identify the intended other-attacker construct

## 1. Football question and narrower physical unit

When the defence reorganizes more strongly around the attacking player nearest
the observed ball at the start of a two-second interval, is that local response
associated with worse geometric coverage over the other nine attacking
outfield players?

V2 narrows the reference attacker prospectively so that each physical anchor
has exactly one analytical row. The ball-nearest attacker is a geometric
reference, not an inferred ball carrier, tactical role, responsible opponent,
or valuable player. The other nine players are a fixed “elsewhere” set for that
anchor. V2 does not generalize its prospective result to arbitrary focal
attackers.

The maximum development claim remains a concurrent observational association
between focal-local defender movement and a fixed-set matching-distance change.
“Coverage” is provisional shorthand for this geometric capacity proxy. It is
not pass availability, pitch control, marking, responsibility, space creation,
success, gravity, or value.

No Game 1 v1 or v2 empirical coverage sample, outcome, coefficient, interval,
or figure existed or was inspected before this freeze. Games 2 and 3 and IDSSE
coverage outcomes remain prohibited.

## 2. Inherited tracking conventions and eligibility

Use Metrica Sample Game 1 and inherit the exact
[Concurrent Attacker–Defensive Geometry v1](concurrent_attacker_defensive_geometry_v1.md)
conventions unless this protocol states a stricter requirement:

- 105 × 68 m pitch coordinates, centre origin, +x right and +y up;
- 25 Hz tracking and the frozen seven-frame centred rolling mean for player and ball positions;
- period-origin anchors $t=o_p+2+4k$;
- pre-context $[t-2,t]$ and concurrent interval $[t,t+2]$;
- event-derived attacking team, restart/ball-out exclusions and cadence rules;
- Home11 and Away25 excluded as goalkeepers;
- complete fixed outfield identities, no interpolation or partial support; and
- D1–D10 fixed at $t$ by reference-attacker distance, with canonical-ID tie handling for defender ranks only.

All ten attacking and all ten defending outfield players require complete
support from $t-2$ through $t+2$. The ball requires complete support over the
same interval because its anchor position selects the physical unit and its
pre/current path enters adjustment. No opponent possession-defining event
(`PASS`, `RECOVERY`, `SET PIECE`, `SHOT`) may occur after $t$ through $t+2$.
Same-team events do not end eligibility. These rules establish conservative
tracking/event continuity, not possession intent.

## 3. One start-defined reference attacker

At the nearest available frame to anchor $t$, calculate Euclidean distance from
the observed ball to every attacking outfield player. Define

$$
a^*(t)=\arg\min_{a\in\mathcal A}
\lVert\mathbf x_a(t)-\mathbf x_{ball}(t)\rVert_2.
$$

The nearest attacker must be unique by more than $10^{-9}$ m; otherwise the
anchor is excluded. Player identity never resolves a reference-attacker tie.
The selected identity and the other-nine set $\mathcal A_{-a^*}$ are fixed
through $t+2$.

There is exactly one row per eligible period/time anchor. No alternate focal
perspectives are generated, duplicated, demeaned, averaged, or selected after
defender movement or matching outcomes are inspected. The reference rule uses
start geometry only and is invariant to player-ID relabeling away from a
rejected exact/numerical tie.

## 4. Fixed-set elsewhere matching outcome

At endpoint $u\in\{t,t+2\}$, construct the fixed $9\times10$ Euclidean matrix

$$
C_{jd}(u)=\lVert\mathbf x_j(u)-\mathbf x_d(u)\rVert_2,
\qquad j\in\mathcal A_{-a^*},\ d\in\mathcal D.
$$

Let $\Pi$ contain injective mappings from the same nine attackers to nine
distinct outfield defenders. Define

$$
G_{else}(u)=\frac{1}{9}\min_{\pi\in\Pi}
\sum_{j\in\mathcal A_{-a^*}}C_{j,\pi(j)}(u)
$$

and the primary outcome

$$
Y=G_{else}(t+2)-G_{else}(t).
$$

The endpoint optimization uses float64
`scipy.optimize.linear_sum_assignment`. Scalar minimum cost is authoritative;
optimized links and the unused defender are descriptive. Positive $Y$ means
the minimum average distance needed to pair the fixed elsewhere set with
distinct defenders increased. Missing endpoint geometry invalidates the
anchor.

V2 does not remove a different attacker for repeated perspectives and does not
apply within-anchor demeaning. A dramatic change confined to the reference
attacker's otherwise unused defender leaves $G_{else}$ unchanged. Perfect
replacement for a defender who leaves an elsewhere attacker can also leave it
unchanged. The complete ten-to-ten matching cost is reported only as a
descriptive direct-pathway comparator because it necessarily includes the
reference attacker's own relationship.

## 5. Focal-local defensive-response predictor

Start-rank the ten defenders by distance to $a^*(t)$. Compute the inherited
leave-one-out defending-outfield-centroid-relative path $P^{rel}_{Dk}$ over
$[t,t+2]$. The sole primary response predictor remains

$$
D=\overline{P^{rel}}_{D1:D3}-
\overline{P^{rel}}_{D4:D7},
$$

in metres. The predicted sign is positive. This is observed focal-local versus
middle defender movement, not a tactical response label or fitted upstream
coefficient.

## 6. Model and identification

The statistical unit is the anchor. Fit one no-duplicated-outcome row per
eligible anchor. Do **not** demean within anchors.

The fixed raw-unit model is

$$
Y=\alpha+\beta_A A+\beta_D D+\beta_GG_0+\beta_OM_O+
\beta_BB+\beta_CC+\beta_RR+\beta_{Apre}A_{pre}+
\beta_{Dpre}D_{pre}+\beta_{Bpre}B_{pre}+\beta_PP_2+\epsilon,
$$

where:

- $A$: concurrent absolute path of $a^*$;
- $D$: primary concurrent response contrast;
- $G_0$: $G_{else}(t)$;
- $M_O$: mean concurrent absolute path of the fixed other nine attackers;
- $B$: concurrent ball path;
- $C$: concurrent defending-outfield centroid path;
- $R$: mean concurrent leave-one-out defender-relative path over D1–D10;
- $A_{pre}$: prior absolute path of the same reference attacker;
- $D_{pre}$: prior response contrast using the same fixed defender ranks;
- $B_{pre}$: prior ball path; and
- $P_2$: period-2 indicator.

Use float64 `numpy.linalg.lstsq(..., rcond=None)` with an intercept. Full column
rank is mandatory; report the singular values and condition number. The sole
primary estimand is $\beta_D$, in metres of elsewhere matching-cost change per
metre of local-versus-middle response contrast, conditional on the frozen
columns. Same-interval adjustment is descriptive and does not create causal
identification.

## 7. Shared-geometry direction null

V2 adds a classifying null directed at shared-coordinate circularity. For each
anchor and each null replicate, preserve the observed defending-team centroid
trajectory and start formation. Let

$$
\mathbf z_d(s)=\mathbf x_d(s)-\overline{\mathbf x}(s)
$$

and rotate every defender's internal change from its start-centred position by
one common random angle $\theta$:

$$
\mathbf x'_d(s)=\overline{\mathbf x}(s)+\mathbf z_d(t)+
Q_\theta[\mathbf z_d(s)-\mathbf z_d(t)].
$$

This preserves the start positions, centroid path, every defender's
leave-one-out-relative path length, $D$, $R$, ranks and all attacker/ball
quantities exactly, while changing defender movement direction relative to the
attacker configuration. Recompute $Y$ and the model.

Use 200 replicates from `Generator(PCG64(SeedSequence(20260910)))`, with one
independent angle drawn uniformly on $[0,2\pi)$ per eligible anchor. The null
passes when observed $\hat\beta_D$
exceeds the 95th percentile of valid null estimates. This does not prove
attacker causation; it asks whether the observed directional arrangement
exceeds magnitude-preserving alternatives.

## 8. Uncertainty and other frozen checks

Use 2,000 deterministic bootstrap replicates from
`Generator(PCG64(SeedSequence(20260909).spawn(2)[0]))`; child 1 is reserved for
possible later Game 2 governance. Resample the observed number of independent
60-second anchor blocks within each period with replacement, retaining terminal
partial blocks. Require at least 1,900 valid full-rank replicates and use a
two-sided percentile 95% interval. Reuse the governed block draws across the
primary, remote and trim families wherever their eligible blocks remain
available.

The following checks are frozen:

1. **Remote response comparator:** replace $D,D_{pre}$ by D8–D10 minus D4–D7; pass when the primary point estimate is larger.
2. **Focal-movement trim:** exclude anchors with concurrent $A>12.198443079831405$ m; pass when the trimmed estimate is positive and retains at least 50% of primary absolute magnitude.
3. **Fixed-start matching:** evaluate the start links at $t+2$; descriptive only.
4. **Full ten-to-ten matching:** report its change and coefficient to expose the reference-attacker direct pathway; descriptive only.
5. **Mean-two-nearest depth:** report the fixed elsewhere set's independent-nearest change; descriptive only.
6. **Rigid transformations and relabeling:** $G_{else}$, $Y$ and $D$ must be invariant to shared translation, rotation and reflection; scalar matching must be invariant to attacker/defender row order. Reference-attacker selection must be label invariant except that numerical ties are excluded.

Report start/end unit width/depth, ball/centroid paths, matching-link churn and
unused-defender identity descriptively. No band, region, kernel, threshold,
assignment penalty, response aggregation or additional covariate may be chosen
after inspection.

## 9. Required synthetic gates

Before empirical execution, the pure-geometry implementation must demonstrate:

1. local defender movement with perfect compensation: neutral elsewhere cost;
2. the same movement without compensation: worse elsewhere cost;
3. shared rigid translation of both teams: neutral response and cost change;
4. symmetric whole-defence expansion: matching cost can change while the local-versus-middle contrast remains neutral, explicitly separating global deformation from focal-local response;
5. independent movement of another attacker: cost can worsen with neutral response, motivating $M_O$;
6. smooth defender-position exchange: stable scalar matching geometry;
7. a near-tie assignment switch: no artificial large scalar jump; and
8. dramatic change confined to the reference attacker's spare defender relationship: neutral elsewhere cost even though full ten-to-ten cost changes.

The internal-direction transformation must also preserve centroid paths and all
leave-one-out-relative defender path lengths numerically. Failure blocks
execution and requires a new prospective version.

## 10. Matching-representation decision

V2 retains rectangular minimum-distance assignment only for the one fixed
elsewhere set. Full ten-to-ten matching fails the direct-focal-pathway test as a
primary outcome. Nearest-$k$ capacity, soft-capacity/optimal-transport,
spare-defender penalties and thresholded bipartite networks require unvalidated
capacity, regularization, penalty or distance/direction choices. They are not
introduced. The selected scalar remains a deliberately narrow geometric proxy,
not a standard validated football-coverage measure.

## 11. Development decision tree

Evaluate in order:

1. **GAME 1 COVERAGE REDISTRIBUTION v2 DEVELOPMENT INVALID** — frozen-hash, sample/support, unique-reference, complete-set, full-rank, solver, bootstrap-minimum, synthetic-gate, null-preservation, hard-QC or deterministic-serialization failure.
2. **GAME 1 COVERAGE REDISTRIBUTION v2 DEVELOPMENT NOT SUPPORTED** — valid execution with primary $\hat\beta_D\le0$.
3. **GAME 1 COVERAGE REDISTRIBUTION v2 DEVELOPMENT COHERENT** — valid execution; $\hat\beta_D>0$; its 95% interval is strictly above zero; the shared-geometry direction null passes; the primary estimate exceeds the remote comparator; and the frozen trim passes.
4. **GAME 1 COVERAGE REDISTRIBUTION v2 DEVELOPMENT MIXED** — every other valid execution with $\hat\beta_D>0$.

Secondary representations cannot rescue the primary. A valid null or negative
result is not INVALID.

## 12. Validation sequence and claim boundary

Execute Game 1 only under separate authorization, then stop. Game 2 governance
may be considered only after closure and only if the narrower ball-nearest
reference construct remains warranted. Game 3 and IDSSE remain closed.

The maximum coherent development claim is:

> In Metrica Sample Game 1, stronger concurrent focal-local versus middle defender-relative movement around the start-defined ball-nearest attacking player was associated with increased minimum mean distinct-defender matching distance over the fixed other nine attacking outfield players, after the prospectively specified anchor-level movement and baseline adjustments and relative to the frozen motion-direction null.

Even a coherent result cannot establish causation, influence, attention,
marking, assignment, responsibility, pinning, dragging, tracking, covering,
handoffs, passing availability, pitch control, space creation, tactical success
or failure, player quality, gravity, or off-ball value.

## 13. Planned governed outputs

Persist a manifest, eligibility/exclusion ledger, anchor/reference ledger,
complete model table, bootstrap estimates, direction-null estimates, remote
comparator, trim, descriptive matching alternatives, synthetic-gate record,
hard QC, governed hash ledger, independent reproduction record, bounded figures
and result report. Licensed observation-level derivatives remain local-only.
Every governed machine-readable output must reproduce byte-for-byte before
closure.
