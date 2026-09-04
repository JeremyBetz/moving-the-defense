# Application Sprint Strategy — Defensive Reorganization Departure

**Status:** [Defensive Reorganization Departure v1](protocols/defensive_reorganization_departure_v1.md)
closed **INVALID before model fitting**. The seven-match common sample failed
its frozen 1,000-rows-per-match gate because `J03WN1` retained 782
threshold-free off-ball rows under the exact 10-attacking-outfielder support
rule. See the [governed result](results/defensive_reorganization_departure_v1.md).
An [outcome-blind support audit](defensive_reorganization_departure_v2_support_audit.md)
subsequently froze a [superseding v2 protocol](protocols/defensive_reorganization_departure_v2.md)
that changes only the attacking entity-support definition: complete support
must equal the event-defined current on-pitch outfield set, including after a
confirmed dismissal. The 1,000-row gate and every downstream scientific rule
remain unchanged. Its [v2 execution](results/defensive_reorganization_departure_v2.md)
passed every support gate and classified **MIXED**: E1 improved all seven
matches but its 2.130% macro MAE improvement missed the frozen 3.0% SUPPORT
gate. Therefore no residual/DRD inspection, retrieval, Metrica transport,
SkillCorner outcome, or player ranking was computed; Metrica Sample Game 3
remains untouched.

A separate [Defensive Reorganization Context v1 protocol](protocols/defensive_reorganization_context_v1.md)
is now frozen but unexecuted. It does not rescue DRD or use residuals. It asks
whether observed near-minus-middle geometry varies with two prospectively
chosen starting relationships: attacker goalward position relative to the
defensive unit and attacker–ball distance.

**Working paper:** *Measuring Localized Defensive Reorganization Associated
with Off-Ball Movement in Football*

## 1. Decision

The strongest bounded application is a **context-adjusted passage-retrieval
layer**. It would estimate how much localized defensive reorganization normally
accompanies an observed attacking movement and its pre-response geometry, then
surface heldout passages where the observed reorganization was substantially
above or below that statistical expectation.

The provisional quantity is **Defensive Reorganization Departure (DRD)**:

\[
\mathrm{DRD}_i = R_i - \widehat{\mathbb E}_{-m(i)}[R_i\mid\mathbf z_i],
\]

where $R_i$ is an anchor-level observed near-versus-middle defender-relative
response, $\mathbf z_i$ contains only attacker movement and information
available before the response, and the prediction for observation $i$ comes
from a model that did not train on its match. Positive DRD means **more localized
defender-relative movement than the fitted model expected for the observed
movement and context**; negative DRD means less. It does not mean better,
worse, influential, disruptive, valuable, or causal.

The primary football use is:

> Find passages in which an off-ball movement was followed by an unusually
> large local change within the defensive unit, relative to comparable
> movement and geometry, so an analyst can inspect the passage in video and
> wider tracking context.

This would add something raw tracking cannot supply: a reproducible comparison
against ordinary movement-conditioned defensive geometry rather than a list of
the longest runs or largest defensive displacements.

## 2. Target and observation unit

Retain the governed footprint observation unit: one eligible `(provider,
match, period, anchor time, attacker)` with a complete start-fixed D1–D10
defender vector. For each attacker-anchor, define the direct observed target:

\[
R_i = \frac{1}{3}\sum_{k=1}^{3}Y_{ik}
      -\frac{1}{4}\sum_{k=4}^{7}Y_{ik},
\]

where $Y_{ik}$ is defender $D_k$'s accumulated leave-one-out
defender-relative path over the established subsequent two-second response
window. This is the underlying observed near-minus-middle response in metres,
not a fitted match coefficient. D8–D10 remain descriptive and are not silently
folded into the application target.

Retain the near and middle means separately in every output. The same $R_i$
can arise from larger near movement, smaller middle movement, or both, so a
positive departure must not be summarized as “the near defenders reacted more”
without inspecting its two observed components.

The near and middle ranks are fixed at the anchor exactly as in the validated
temporal design. They are proximity categories, not marking assignments. A
positive $R_i$ means the near ranks accumulated more defender-relative path
than the middle ranks in that passage. It does not say why.

Simultaneous focal attackers share defensive state and can share response
paths under different rank orderings. They must remain grouped in folds,
resampling, uncertainty, and example selection. No attacker-anchor or defender
row is an independent match-level replication.

## 3. Expected-reorganization model

### 3.1 Model family

Begin with one interpretable nested linear architecture:

1. **Movement-only baseline:** attacker path magnitude over the exposure
   interval and attacker path over the immediately prior interval.
2. **Context model:** the same baseline plus three predeclared geometric
   families below.

Use Ridge regression with training-fold-only centering/scaling and nested
leave-match-out selection of the regularization parameter. Keep raw-unit
descriptions alongside standardized coefficients. Do not use trees, boosting,
neural networks, embeddings, latent states, clustering, or tactical labels.

The model estimates statistical expectation, not correct tactical position or
the response a defender *should* have produced. DRD is an out-of-sample model
residual, not tactical error or attacker effect.

### 3.2 Three theory-driven context families

Only these families should enter v1 development.

#### A. Attacker movement form

- signed goalward displacement over the preceding movement interval;
- signed lateral displacement in a consistently mirrored pitch frame; and
- path magnitude retained in the baseline so direction is not a proxy for
  simply moving farther.

This distinguishes goalward, lateral, and mixed movement geometrically. It does
not label runs as overlaps, checks, decoys, or threats.

#### B. Starting geometry relative to the defensive unit

- attacker's signed goalward offset from the defending-outfield centroid at
  movement start;
- attacker's lateral offset from that centroid, represented continuously; and
- defending-unit width and depth as transparent scale/context variables.

This asks whether the same movement amount has a different expected response
when it begins within different parts of the defensive geometry. It does not
define “between the lines” or “inside the block” without separate validation.

#### C. Ball relationship

- attacker-to-ball distance at movement start;
- ball position relative to the defensive-unit centroid; and
- change in attacker-to-ball distance during the preceding movement interval.

These are continuous context variables. They do not prove that the attacker is
off-ball, a passing option, or the cause of the defensive movement. The frozen
protocol operationalizes off-ball eligibility by excluding the threshold-free
ball-nearest attacking outfielder at the anchor; it explicitly does not call
that player the observed ball carrier. V1 contains no interactions.

### 3.3 Primary prospective question

> Do the three predeclared movement/geometry families improve heldout
> prediction of anchor-level localized defender-relative reorganization beyond
> current and prior attacker path alone?

Feature-family claims require heldout ablations on identical rows and folds.
Coefficient signs may describe the fitted linear model, but no family should be
called explanatory merely because an in-sample coefficient is large.

## 4. Existing-data support and player feasibility

The closed temporal-footprint registries supply **81,226** eligible
attacker-anchor observations: 8,910 across Metrica Games 1–2 and 72,316 across
the seven IDSSE matches. These are many observations but only nine match units.

An outcome-blind support count from the already-closed IDSSE anchor registry
found 148 attacking players. Of these, 132 (89.2%) appear in one match, 3 in two
matches, 1 in three, 6 in four, and 6 in five. Only 16 players have observations
in at least two matches and 13 in at least three. Metrica's anonymized player
keys are match-local and cannot support cross-match player effects.

Therefore **player-level ranking is not defensible in v1**. The current data
cannot cleanly separate player, team, match, provider, and movement-context
effects for most players. Player identity must not be a predictor or target in
the first application model. At most, player-grouped diagnostic summaries may
test whether a small number of individuals dominate residuals; they cannot be
published as stable player ability.

## 5. SkillCorner feasibility

SkillCorner should be added **conditionally as an external application
validation environment**, not pooled into development merely to increase row
count. Its [official open-data release](https://github.com/SkillCorner/opendata)
contains ten 2024/25 Australian A-League matches with 10 Hz broadcast tracking,
lineups, ball/possession fields, Dynamic Events, and phases of play. The release
contains 12 clubs; six appear in more than one of the ten matches, including
Auckland in four. This improves match, team, movement-context, competition, and
provider diversity. [Kloppy documents a SkillCorner loader](https://kloppy.pysport.org/user-guide/loading-data/skillcorner/),
so the existing canonical adapter strategy should reduce ingestion cost.
Compatibility between that loader and the release's current
`tracking_extrapolated.jsonl` schema must still be verified; provider support in
principle is not a passed project equivalence gate.

The benefit comes with material measurement risk. SkillCorner states that the
tracking combines detected and extrapolated player locations, exposes an
`is_detected` flag, estimates identity accuracy at about 97%, and recommends
speed/acceleration quality control. The first SkillCorner work must therefore
be an outcome-blind provider/support gate covering identities, complete
defending-outfield membership, goalkeeper status, ball support, detection versus
extrapolation, time/period boundaries, coordinates, cadence, and the exact
two-second path construction. Detected and extrapolated support must remain
visible; no silent interpolation or quality filtering is allowed.

Dynamic Events and vendor off-ball-run labels should not define or select the
primary expected-reorganization sample. They can later annotate already-frozen
retrieval examples descriptively, because using them as model labels or outcome
filters would change the construct and weaken cross-provider comparability.

SkillCorner materially improves external-validity and analyst-interpretability
potential. It does **not yet establish player-level feasibility**: repeated
player support must be counted prospectively from match metadata before any
player effect is considered, and ten matches remain a small schedule for
separating players from teams and roles.

## 6. Validation plan

### Stage A — application development

- Treat the seven IDSSE matches as the primary development environment because
  they provide seven match units under one established provider-equivalence
  layer.
- Use nested leave-one-match-out evaluation. Inner model selection also leaves
  matches out; random row splitting is prohibited.
- Keep match-period time blocks, simultaneous attackers, and complete rank
  vectors grouped. Use an embargo at least as large as overlapping feature and
  response support if anchors are made denser than the existing four-second
  cadence.
- Compare the full context model with the movement-only baseline on exactly
  the same rows and folds.
- Use Metrica Games 1–2 only as a secondary cross-environment transport check;
  they are already scientifically used and are not a pristine application
  holdout.
- Keep Metrica Game 3 untouched.

### Stage B — external application validation

Proceed only if Stage A meets the frozen materiality/stability gate and the
SkillCorner outcome-blind support gate passes. Freeze feature definitions,
model class, regularization grid, transformations, eligibility, metrics, and
classification before computing SkillCorner response outcomes. Train using the
development design and assess the unchanged model on SkillCorner match by
match. Do not retune on external residuals.

External reporting should include baseline-versus-context MAE/RMSE, calibration
slope/intercept, residual distributions, match signs, detected/extrapolated
support strata, and the deterministic retrieval examples. Provider differences
must be reported directly; calibration failure cannot be repaired after seeing
external outcomes.

## 7. Primary analyst-facing output

Build one **context-adjusted passage-retrieval board**. Each retrieved passage
should show:

- the preceding attacker path and pre-response ball/unit geometry;
- the subsequent absolute and defender-relative paths for D1–D7;
- observed near and middle means, $R_i$, heldout expected $\widehat R_i$, and
  DRD in metres;
- the small set of model inputs in football-readable units; and
- match/video time for human review.

The primary contrast is not “best player” but **similar movement, different
defensive reorganization**. After the model and QC rules are frozen, select one
near-expected and one high-positive-departure passage by deterministic heldout
residual strata, with a predeclared match/player diversity cap. Avoid the single
largest residual, which is more likely to be a tracking or support anomaly.
Selection cannot use tactical attractiveness, possession outcome, shots, xG,
or analyst preference.

For a club, the output answers: *Which passages deserve review because the
defensive unit reorganized more than would ordinarily be expected from this
movement and starting geometry?* Raw tracking can display the passage; the
application adds a governed comparison set and retrieval rule.

## 8. Success, failure, and stopping rules

The frozen v1 standard is intentionally demanding:

### Include as a Sloan application result only if

1. the full context model improves equal-match macro leave-match-out MAE by at least the
   project's established 3% materiality convention versus the movement/history
   baseline;
2. it improves at least six of seven IDSSE matches, with no match worsening by
   10% or more;
3. at least one predeclared context family shows stable heldout value under
   identical-fold ablation rather than only an in-sample coefficient;
4. calibration and residual diagnostics do not reveal domination by provider,
   missing-support, extrapolation, or extreme-motion artifacts;
5. deterministic passages are interpretable from raw pitch geometry and remain
   examples of model departure rather than tactical labels; and
6. deterministic retrieval yields complete stable pairs in at least five of
   seven matches under the frozen reliability rule.

The exact definitions, inclusive boundaries, family-ablation rule, and
SUPPORTED/MIXED/NOT SUPPORTED/INVALID tree are governed by the
[v1 protocol](protocols/defensive_reorganization_departure_v1.md). SkillCorner
remains behind an outcome-blind compatibility gate and a separate future
external protocol.

### Stop and retain the existing measurement paper if

- context adds little beyond current and prior attacker path;
- feature-family gains or signs vary materially by heldout match/provider;
- residual extremes concentrate in identity, missingness, extrapolation, or
  tracking-QC failures;
- the output becomes interpretable only after adding tactical run labels,
  assignment inference, or a value model;
- SkillCorner cannot reproduce complete defensive-unit support; or
- repeated support remains insufficient for any player-level conclusion.

A null is informative: it would show that the validated localization is useful
as a measurement but that this simple context model does not support an
application layer. Do not add features or relax gates to rescue it.

## 9. Novelty position

The expected-versus-observed architecture is not new. Basketball gravity,
football ghosting/trajectory prediction, expected defensive velocity, and
contextual baselines are close precedents. Nor are pitch control, receiver
availability, pressure, marking networks, or off-ball-run detection empty
spaces.

| Neighbor | What it primarily represents | Difference from proposed DRD |
|---|---|---|
| Pitch control / receiver availability | Reachability, interception, possession or value of space | DRD predicts a validated internal defensive-unit movement contrast, not controlled space or pass availability. |
| Defensive pressure | Constraint or arrival around the ball carrier/local ball zone | DRD is attacker-centered and can concern movement away from the ball; it does not label pressure. |
| Marking networks / matchup models | Inferred attacker-defender responsibilities or latent relations | DRD keeps start-fixed proximity ranks and makes no assignment inference. |
| Off-ball-run detection | Movement boundaries, types, speed, threat or outcomes | DRD accepts the validated fixed movement interval and asks what defensive geometry followed. |
| Trajectory/ghosting models | Expected player positions or counterfactual futures | DRD uses a model-light expected scalar local-reorganization target, not a generated tactical trajectory. |
| Basketball gravity | Expected versus observed defensive pressure/attention | This is the closest application architecture and prevents a novelty claim for residualization; DRD withholds attention, causation, gravity and value semantics. |

The defensible novelty hypothesis is therefore limited:

> Contextualize how much localized internal defensive reorganization follows
> an attacking movement relative to what would ordinarily be expected from
> that movement and pre-response geometry, then use heldout departures to
> retrieve passages for analyst review.

This combination appears differentiated among the literature already reviewed
for this project, especially through its leave-one-out defensive-unit reference,
near-versus-middle target, strict temporal order, reverse-time-qualified
measurement foundation, and external application gate. It is not claimed to be
universally unprecedented. The [literature review](literature_review.md),
[bibliography](../references/bibliography.md), and [Sloan strategy](sloan_submission_strategy.md)
remain the governing provenance sources.

## 10. Upgraded Sloan story if successful

1. Separate individual defender movement from the shift of the defensive unit.
2. Validate the localized, time-ordered attacker-movement association across
   Metrica and IDSSE.
3. Estimate ordinary localized reorganization from movement and pre-response
   geometry.
4. Measure heldout departures from that statistical expectation.
5. Show which movement/geometry families add reproducible predictive value.
6. Retrieve real passages where observed local reorganization differs from
   expectation for analyst review.

The impact statement remains observational:

> The application helps analysts identify off-ball movements followed by
> unusually large localized defensive reorganization, including movements
> where the attacker never receives the ball, before tactical meaning or value
> is assigned.

If the application fails its gates, the existing externally replicated
measurement paper remains intact and should be submitted without a residual
application claim.

## 11. Ten-to-fourteen-day sprint

| Day | Work | Gate |
|---|---|---|
| 1–2 | Outcome-blind target/support audit; finalize feature formulas, off-ball language, fold grouping, metrics, and numeric criteria | Freeze only if every feature is provider-computable and no response outcome has been inspected for this question. |
| 3–5 | Implement the anchor-level target, baseline/full Ridge models, match-grouped folds, ablations, calibration, and synthetic/unit tests | No alternative model family; no Game 3. |
| 6 | Execute the primary IDSSE development evaluation once and independently reproduce it | Stop if materiality, match stability, or QC fails. |
| 7–8 | If Stage A passes, apply the already-frozen residual diagnostics and retrieval-board selection rule; produce internal Metrica transport descriptions | No player rankings or tactical labels. |
| 9–11 | Conduct SkillCorner metadata/support/equivalence work; freeze external transfer before response outcomes | Stop if identities, support, ball, cadence, or detected/extrapolated strata are inadequate. |
| 12 | Execute unchanged SkillCorner external validation only if authorized gates passed | No external retuning. |
| 13–14 | Build the retrieval board, update manuscript/abstract only if supported, and close the sprint | Choose application headline or measurement-paper fallback. |

By mid-September choose exactly one:

- **A — application headline:** context adds stable heldout value and, ideally,
  transports to SkillCorner; or
- **B — measurement paper:** freeze application work and submit the existing
  validated measurement with the application null/mixed result omitted from the
  headline but preserved in the research record.

## 12. Cost and operating discipline

| Dimension | Conditional estimate | Reason |
|---|---|---|
| Scientific value | **Moderate-to-high** | A positive result would establish a reproducible contextual layer above the validated measurement; a clean null would set a valuable boundary on what simple geometry adds. |
| Sloan application/impact value | **High if Stage A and external transport pass; low as a headline if they do not** | Context-adjusted passage retrieval is directly legible to analysts, but an unstable residual model should not displace the already coherent measurement paper. |
| Data/integration cost | **Moderate without SkillCorner; moderate-to-high with it** | Existing IDSSE registries and model utilities are reusable, whereas a new broadcast-tracking provider requires identity/support/equivalence governance. |

This is a **moderate-to-high integration sprint**, not a small extra figure.
A bounded estimate is five to seven focused Codex tasks and roughly 20–30
percentage points of the expanded weekly allowance if SkillCorner integration
is attempted; the SkillCorner gate alone may consume 8–12 points because of
provider/support equivalence. Without SkillCorner, the IDSSE development and
retrieval prototype should fit nearer 12–18 points. These are planning ranges,
not guarantees.

- Use Sol Extra High only to finalize identification and freeze the protocol.
- Use Terra High with Turbo for implementation, execution, and focused QC.
- Reuse the canonical tracking contract, Kloppy adapters, closed anchor
  registries, and established block/fold utilities.
- Run focused development tests; reserve full repository QC for a promoted
  milestone.
- Do not repeat repo-wide audits or reopen frozen measurement analyses.
- Stop at the first failed scientific gate rather than spending budget on
  feature search.

## 13. Decisions resolved by the v1 freeze

The [v1 protocol](protocols/defensive_reorganization_departure_v1.md) froze
freezes a threshold-free ball-nearest-attacker exclusion as the operational
off-ball rule; direct anchor-level near-minus-middle path as the target; a
two-feature movement baseline; three compact context families; nested
leave-match-out Ridge; exact materiality and ablation gates; and a deterministic
heldout retrieval rule. Only a SUPPORTED IDSSE result can authorize retrieval,
Metrica transport, or the outcome-blind SkillCorner gate. SkillCorner outcome
access still requires a separately frozen external protocol.

The execution stopped at the mandatory common-sample gate before a model error,
residual, DRD, retrieval passage, or external-provider outcome was computed.
