# Off-Ball Movement Direction and Localized Defensive Reorganization in Football

> **Internal manuscript skeleton — argument architecture, not submission prose.**
> This document organizes closed results; it does not add claims, results, or protocol choices.

## Abstract

**Introduction.** Off-ball movement can coincide either with a whole defensive
unit shifting or with defenders changing position within that unit; tracking
analyses need to distinguish them. Outward attacker movement was more strongly
associated with localized internal defensive reorganization than equivalently
modelled goalward movement, showing that reorganization is not simply aligned
with movement toward goal.

**Methods.** Using fixed windows, we measured attacker movement before each
defender's response path relative to the other defending outfield players,
separating local reorganization from shared translation. Start-fixed proximity
ranks compared the three nearest defenders with four middle-ranked defenders
without inferred marking assignments. We developed and held out the temporal
design in Metrica, tested it externally across seven IDSSE matches, replicated
directional form in nine SkillCorner matches, and included a reverse-time
comparison.

**Results.** In pooled Metrica, the pre-specified near-minus-middle association
was 0.05029 m/m (97.5% interval [0.03433, 0.06858]); its paired
forward-minus-reverse excess was 0.02912 [0.01410, 0.04526]. The development
and protected heldout estimates were both positive (0.04559 and 0.08553 m/m).
Across Metrica, frozen 1-, 2-, and 4-second horizons were positive (0.02916,
0.05029, and 0.07566 m/m), and the predeclared trim retained 88.74% of primary
magnitude. Across seven IDSSE matches, the corresponding association was
0.06115 m/m (95% CI [0.05579, 0.06681]) and the forward-minus-reverse excess
was 0.02455 [0.01932, 0.02985]. All seven primary and paired-excess estimates
were positive; 1-, 2-, and 4-second horizons were likewise positive (0.03536,
0.06115, and 0.09549 m/m), although reverse-time structure itself remained
positive. The IDSSE trim retained 95.35% of primary magnitude. The directional
asymmetry replicated across independent tracking environments: conditional on
equal path magnitude and frozen starting geometry, outward minus goalward
movement was 0.056856 m/m [0.051358, 0.062430] in IDSSE, positive in all 7/7
match and leave-one-match-out fits, and 0.048883 m/m [0.042940, 0.054707] in
SkillCorner, positive in all 9/9 match and leave-one-match-out fits.
SkillCorner's trim retained 90.19% of rows, and a majority-directly-detected
sensitivity estimated 0.046780 m/m. All governed bootstrap families had
2,000 valid replicates each; the two external environments used separate
frozen models, interval conventions, and checks and were not pooled across
providers. In IDSSE, 5 m outward rather than goalward displacement corresponded
to approximately 0.284 m more subsequent localized defender-relative
reorganization. Thus reorganization was not simply aligned with movement
toward goal. Goalward movement instead had a secondary, nonclassifying
2.962709 m [2.870720, 3.048322] collective-translation association, while the
proposed inward-versus-outward narrowing mechanism was not established.

**Conclusion.** This is not a new centroid or tracking primitive, but a
prospectively validated temporal measure of internal defensive reorganization
with replicated directional asymmetry. It can distinguish shared defensive
shifts from localized internal reorganization and surface passages for video
analysis. It does not automatically assign tactical labels. These are
observational geometric associations, not estimates of causal influence or
attacking value.

## 1. Introduction

### 1.1 The football problem

Football language often says an attacker pulled a defender, pinned a line, or
forced the defence to adjust. Tracking data instead record positions and
movement. If a defensive unit shifts together, large absolute movement may be a
shared shift; if one defender moves differently from that unit, a smaller
absolute displacement may be the more locally distinctive geometry. The
measurement task is to separate those observable patterns before inferring why
they occurred.

### 1.2 Research question and contribution

This paper asks whether preceding off-ball attacker movement is associated with
subsequent localized defensive reorganization: defender movement relative to
the defensive unit among initially nearer defenders compared with a
pre-specified middle-distance reference. It then asks whether that association
depends on attacker-movement direction after accounting for path magnitude and
starting geometry.

The contribution is a transparent, replicated measurement and directional
association—not an assignment, tactical label, causal effect, or attacking
value model. The argument proceeds from a validated time-ordered measurement to
the outward-versus-goalward asymmetry, then characterizes starting context and
tests the boundary between local and collective-scale geometry.

### 1.3 Boundaries from the outset

Nearness is a start-fixed spatial rank, not marking responsibility. Defender
movement relative to the defensive unit is observable geometry, not a direct
measure of attention, instruction, intent, or correctness. A temporal
association that exceeds its reverse-time comparison remains observational;
ball, phase, possession, and other unmeasured context may still contribute.

## 2. Related work

### 2.1 Collective defensive geometry and coordination

Position-tracking research has established centroids, width, depth, surface
area, player-to-team distances, synchrony, relative phase, and other ways to
describe collective football geometry. This paper builds on—not claims to
invent—player-to-collective representations. Its leave-one-out defensive-unit
reference is a transparent way to keep shared defensive shifts visible as
context while measuring a focal defender's deviation from them.

### 2.2 Attacker-defender spatial relationships

Prior work models attacker-defender distance, angles, relative motion,
coordination, marking-like relationships, and assignments. Here, start-fixed
distance ranks offer a reproducible localization comparison without inferring
who is marking, covering, or responsible for an attacker. The paper is
complementary to assignment or network approaches rather than a replacement for
them.

### 2.3 Off-ball movement and directional movement

Off-ball paths can be described as movement efforts, runs, trajectory patterns,
or directional changes, but no observed path automatically identifies a
tactical movement type. This paper uses governed fixed-window path and signed
directional displacement as geometric exposures. It does not label attackers'
movements as decoys, overlaps, checks, or threats.

### 2.4 Measurement limits before tactical or value claims

Pressure, pitch control, space, expected movement, and value frameworks address
later layers of football analysis. They motivate the importance of defensive
geometry but also make the present boundary clear: localized reorganization is
not thereby teammate separation, opportunity creation, tactical success,
gravity, or off-ball value.

## 3. Data

### 3.1 Metrica development and protected holdout

Metrica Sample Game 1 developed the governed temporal measurement. Metrica
Sample Game 2 then tested the unchanged design as a protected within-provider
holdout. Both use supported open-play tracking intervals in standardized metric
coordinates; they are transparent sample matches, not a representative
population of football.

### 3.2 IDSSE external temporal validation

Seven complete professional IDSSE/DFL matches provide the external temporal
test in an independent tracking-provider environment. The analysis evaluates
transport of the already specified measurement and time-ordered association,
not a league-wide effect or seven distinct provider replications.

### 3.3 SkillCorner directional replication

Nine SkillCorner matches provide a separate external replication of the
outward-versus-goalward movement-direction analysis. SkillCorner is not pooled
with IDSSE: the environments retain their own pre-specified models, intervals,
support checks, and provider-specific compatibility work.

### 3.4 Availability and provenance

Restricted provider tracking and row-level derivatives are not redistributed.
Public materials provide implementation, compact governed summaries, figure
artifacts, hash ledgers, and regeneration guidance. Full source-data access,
coordinate handling, support rules, and eligibility details are documented in
the supplement and repository materials.

## 4. Methods

### 4.1 Analysis unit and attacker movement

One observation is a supported attacker-time anchor with a preceding fixed
attacker-movement interval and a subsequent defender-response interval. The
attacker's path and signed displacement are computed only over the governed
history/exposure interval. Complete support, restart/ball-out exclusions, and
endpoint cadence apply before modelling; the paper does not call every such
interval a tactical run or movement effort.

### 4.2 Defender-relative representation

For focal defender \(d\), the representation is the defender's position
relative to the other defending outfield players:

\[
\mathbf r_d(t)=\mathbf x_d(t)-\frac{1}{9}\sum_{j\ne d}\mathbf x_j(t).
\]

Accumulated movement in \(\mathbf r_d\) over the subsequent interval is the
primary local outcome. Shared translation of the defensive unit largely cancels
from this moving reference frame; it is not assumed to be the only relevant
defensive change.

### 4.3 Temporal ordering and start-fixed proximity groups

Attacker movement precedes the defensive response interval. At the anchor,
outfield defenders are ordered by distance to the attacker and retained in
fixed ranks through the response interval. The primary localized comparison is
the three nearest ranks (D1–D3) versus the four middle ranks (D4–D7). These
groups express local versus reference geometry, not an inferred assignment.

### 4.4 Primary temporal association and reverse-time comparison

The primary model estimates how preceding attacker path is associated with
subsequent defender movement relative to the defensive unit by start-fixed
rank, conditioning only on pre-interval movement and spatial context. Its
pre-specified near-minus-middle contrast is the headline temporal quantity. A
paired reverse-time comparison asks whether the correctly ordered association
exceeds background structure preserved under the same construction in reverse
time; it does not require the reverse-time control itself to be structure-free.

### 4.5 Movement-direction analysis

The central directional model contrasts outward versus goalward attacker
movement while conditioning on equal path magnitude and pre-specified starting
geometry. IDSSE and SkillCorner are analyzed separately, with no cross-provider
pool. Goalward/away and outward/inward signed components remain geometric
descriptions; the analysis does not identify a tactical run type or an
attacker-caused defensive action.

### 4.6 Starting-context characterization

Separate, non-mechanistic models characterize when the localized temporal
association is larger or smaller in observed starting geometry, including the
attacker's ball distance and goalward position relative to the defensive unit.
These models describe context around the measurement; they do not identify a
tactical cause or a complete situational model.

### 4.7 Response-scale follow-up

Separate follow-ups retain local reorganization, defensive-unit translation,
and pitch-axis width as distinct observable scales. The goalward collective
translation result is secondary and nonclassifying. The inward-versus-outward
width/narrowing test was mixed, so the analyses do not allocate a response into
exclusive local and collective shares or establish a geometric mechanism.

### 4.8 Validation and inference

Development, protected Metrica holdout, and external IDSSE validation were
prospectively governed. Uncertainty uses the specified grouped block-bootstrap
procedures, with trimming, horizon, placebo/reverse-time, support, invariance,
and provider-equivalence checks documented in full in the supplement. Results
are observational associations with provider-specific inference; external
results are not pooled across IDSSE and SkillCorner.

## 5. Results

### 5.1 Time-ordered localized defensive reorganization

The temporal result is the first empirical result. In pooled Metrica, the
near-minus-middle association was 0.05029 m/m (97.5% interval [0.03433,
0.06858]); the development and protected heldout estimates were positive
(0.04559 and 0.08553 m/m). The paired forward-minus-reverse excess was 0.02912
[0.01410, 0.04526].

Across seven IDSSE matches, the corresponding estimate was 0.06115 m/m (95%
CI [0.05579, 0.06681]) and the paired excess was 0.02455 [0.01932, 0.02985].
All seven primary and paired-excess estimates were positive. Frozen 1-, 2-, and
4-second IDSSE horizons were positive (0.03536, 0.06115, and 0.09549 m/m),
while reverse-time structure itself also remained positive. This supports a
stronger time-ordered association, not reaction time or causation.

**Main Figure 1 — temporal flagship.** Show the football-readable distinction
between a shared defensive shift and defender movement relative to the unit,
with the pooled temporal estimate and reverse-time qualification. Use the
existing temporal flagship figure; do not make it an illustrative proof of
causation.

### 5.2 Movement direction: outward versus goalward

The directional result is the manuscript headline. Conditional on equal path
magnitude and starting geometry, outward minus goalward attacker movement was
0.056856 m/m [0.051358, 0.062430] in IDSSE, positive in all 7/7 match-specific
and leave-one-match-out fits. The independent SkillCorner analysis estimated
0.048883 m/m [0.042940, 0.054707], positive in all 9/9 match-specific and
leave-one-match-out fits. In IDSSE, 5 m outward rather than goalward movement
corresponded descriptively to about 0.284 m more subsequent localized defender
movement relative to the defensive unit.

The asymmetry says measured local reorganization was not simply aligned with
movement toward goal. It does not say outward movement is tactically better,
that it dragged defenders, or that it created value.

**Main Figure 2 — outward versus goalward replication.** Present the two
external environments side by side, their separate estimates and intervals,
and their all-match/leave-one-match-out sign consistency. Make explicit that
the estimates are not cross-provider pooled.

### 5.3 Starting context

Starting context characterizes the temporal measurement rather than explaining
it. In IDSSE, the localized association was larger when attackers started less
far goalward relative to the defensive unit and closer to the ball; the context
slopes were -0.010161 [-0.011805, -0.008499] m/m and -0.007533
[-0.008864, -0.006245] m/m, respectively, with consistent signs across match
and leave-one-match-out fits. Present this as a compact contextual “when”
description, not a mechanism or tactical prescription.

### 5.4 Response scale and mechanism boundary

Goalward rather than outward movement had a secondary, nonclassifying
collective-translation association of 2.962709 m [2.870720, 3.048322] for a
5 m directional contrast. The proposed inward-versus-outward narrowing
mechanism was not established: its width contrast was 0.134003 m
[-0.006622, 0.273430], with 5/7 match contrasts positive. Localized
reorganization and collective translation can co-occur; these analyses do not
partition a response into fixed shares or establish why either movement
occurred.

## 6. Discussion

### 6.1 A reproducible temporal measurement

Interpret the validated temporal result as a measurement layer: nearby
defenders moved more relative to the defensive unit than middle-distance ranks
after preceding attacker movement. The reverse-time control retained structure;
the qualifying evidence is the pre-specified paired forward-minus-reverse
excess, not an assumption that controls should be null.

### 6.2 Directional asymmetry

Lead the discussion with the replicated outward-versus-goalward asymmetry in
IDSSE and SkillCorner. It narrows the descriptive claim: local reorganization
is not simply stronger for movement toward goal once path magnitude and starting
geometry are modeled. It neither names a tactical mechanism nor estimates
attacker influence.

### 6.3 Local and collective response scales

Localized reorganization, shared defensive shifts, and width/depth changes are
distinct views that may overlap in one passage. The secondary goalward
translation result and mixed narrowing result supply a response-scale boundary,
not a complete mechanism or a composite response score.

### 6.4 Starting context

Context results describe where the observed temporal association was stronger
or weaker under the pre-specified geometry. They are not evidence that ball
proximity or a goalward starting position caused the response, and they should
not be translated into a tactical template.

### 6.5 Analyst use

The measurement can surface passages for video review and distinguish a shared
defensive shift from a more localized internal adjustment. Analysts still need
the ball, teammates, opponents, video, and football judgment to decide whether
a passage reflects a step, drop, cover, hold, recovery, or another football
concept.

### 6.6 Limitations and negative boundaries

The evidence is observational; residual shared context, rank composition,
limited match/provider coverage, support restrictions, and provider-specific
processing remain material limitations. Opportunity Redistribution v1 did not
support the tested nearest-defender-separation consequence
(\(\beta_D=-0.02407\), 95% bootstrap interval [-0.09392, 0.04776]). This is a
boundary result, not a metric to tune until positive, and it prevents treating
localized reorganization as demonstrated space creation or attacking value.

### 6.7 Future work

Future work needs semantic/video validation, broader multi-team and
multi-competition replication, independently motivated downstream consequences,
and—only once their constructs are validated—tests of tactical interpretation
or value. The immediate aim is better defensible measurement, not an automatic
labeler of pinning, dragging, tracking, or tactical correctness.

## 7. Conclusion

The paper establishes a reproducible observational measurement of localized
defensive reorganization associated with preceding off-ball movement and a
replicated outward-versus-goalward directional asymmetry. It separates a shared
defensive shift from defender movement relative to the defensive unit, but does
not establish causation, assignment, tactical meaning, opportunity creation,
or attacking value. Its practical role is to make candidate passages more
legible for analyst review while preserving those boundaries.

## Supplement plan

- **S1 — Representation and eligibility:** coordinate contract; complete
  support; smoothing; endpoint, timing, tie, and numerical-boundary rules.
- **S2 — Full temporal results:** complete statistics, D1–D10 profiles,
  regional estimates, horizons, trimming, reverse-time/placebo results, and
  all match-level external estimates.
- **S3 — Validation and provenance:** Metrica holdout, provider-equivalence
  checks, bootstrap and reproducibility materials, hash ledgers, and
  regeneration pointers.
- **S4 — Additional geometry:** concurrent geometry/coordination, rank
  composition and synthetic audits, starting-context diagnostics, and the full
  response-scale follow-up.
- **S5 — Directional detail:** IDSSE and SkillCorner compatibility checks,
  separate provider-specific specifications, sensitivity results, and complete
  movement-direction tables.
- **S6 — Boundary findings:** Opportunity Redistribution, Defensive Coverage,
  Defensive Response Expectation, and other negative or mixed outcomes.
- **S7 — Additional visuals:** D1–D10, context, response-scale, robustness,
  and provider-equivalence figures. The comprehensive results table is
  supplementary for a two-slot Sloan package.

## Internal drafting decisions

- Main paper: Figure 1 is the temporal flagship; Figure 2 is the
  outward-versus-goalward external replication. All other result visuals are
  supplementary unless venue rules require otherwise.
- Keep concurrent geometry/coordination to one contextual sentence in the main
  paper, if retained at all; its full result is supplementary because it shares
  the attacker and defender interval.
- Do not promote Opportunity Redistribution, Defensive Coverage, Defensive
  Response Expectation, segmentation, or construct-development branches into
  headline results. They remain boundary evidence in repository and supplement
  materials as specified above.
- Before polished prose: confirm target venue and word limit, author list,
  citation style, data-access language, and final figure typography.
