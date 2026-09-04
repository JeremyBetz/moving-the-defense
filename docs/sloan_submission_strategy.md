# Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football

## Sloan submission strategy — September 2026

**Decision:** centre the paper on externally replicated, time-ordered localized
defensive reorganization. The contribution is a governed measurement-and-validation
result: greater attacker movement in a preceding interval is associated with
stronger subsequent defender-relative movement among nearby than middle-ranked
defenders, and the forward association exceeds the frozen reverse-time
comparison. Do not frame the work as attacker value, gravity, causal influence,
reaction time, or automatic tactical recognition.

The paper strategy uses only closed governed evidence. Metrica Sample Game 3
remains untouched and no Game 3 contextual holdout is authorized before the
Sloan abstract. The separate IDSSE-only [Context v1 result](results/defensive_reorganization_context_v1.md)
is **SUPPORTED**: the measured near-minus-middle geometry was smaller when an
attacker started farther goalward relative to the defensive unit
(`-0.010161 m/m`, 97.5% `[-0.011805, -0.008499]`) or farther from the ball
(`-0.007533 m/m`, 97.5% `[-0.008864, -0.006245]`). Both directions held in
all seven match and leave-one-match-out fits, with the frozen trim passing.
This bounded context characterization is not tactical, causal, or value
evidence.

The separate seven-match [Spatial Form v1 result](results/defensive_reorganization_spatial_value_v1.md)
is also **SUPPORTED**: conditional on frozen path and start context, outward
rather than goalward displacement was associated with 0.056856 m/m greater
subsequent localized reorganization [0.051358, 0.062430], with the direction
positive in all seven match and leave-one-match-out fits. Its static five-lane
versus dynamic unit-relative comparison found **NO CLEAR REPRESENTATIONAL
ADVANTAGE**. Treat this as a bounded geometric characterization for a results
table or supplement—not a tactical, causal, space-creation, or value claim.
The [SkillCorner external replication](results/defensive_reorganization_spatial_form_v1_skillcorner_external.md)
subsequently passed its separately frozen nine-match design: the
outward-minus-goalward contrast was 0.048883 m/m [0.042940, 0.054707], with
all match and leave-one-match-out directions positive. It strengthens the
geometric evidence across a third tracking environment, while remaining
observational and separate from any cross-provider pooled estimate.

## 1. The paper that exists today

### Strongest defensible claim

> Across two Metrica sample matches and seven IDSSE matches, greater attacker
> movement in a preceding interval was associated with stronger subsequent
> defender-relative movement among nearby than middle-ranked defenders. The
> forward association exceeded the prospectively frozen reverse-time
> comparison.

The Metrica near-minus-middle estimates were 0.04559 m/m [0.02979, 0.06428]
in development Game 1, 0.08553 [0.02917, 0.15786] in untouched Game 2, and
0.05029 [0.03433, 0.06858] pooled. The pooled Metrica reverse-time contrast
was 0.02117 [0.00936, 0.03332], leaving a paired forward-minus-reverse excess
of 0.02912 [0.01410, 0.04526].

Under the unchanged IDSSE external-replication design, the pooled primary
contrast was 0.06115 [0.05579, 0.06681], the reverse-time contrast was 0.03661
[0.03224, 0.04111], and paired excess was 0.02455 [0.01932, 0.02985]. Primary
and paired-excess point estimates were positive in all seven IDSSE matches;
all bootstrap families completed 2,000/2,000 replicates, the frozen trim
retained 95.35% of the primary magnitude, and 1/2/4-second signs were positive.

These are observational coefficients under frozen models, not estimates of an
attacker's causal effect. The positive reverse-time structure is an important
limitation: the evidence is a larger correctly ordered association under the
paired design, not the absence of shared temporal structure.

### Football problem and measurement contribution

Tracking records where defenders travelled but not whether one defender broke
from a collective shift. The method expresses each outfield defender relative
to the other defending outfield players, measures attacker movement in an
earlier fixed interval, fixes defender proximity ranks before the response
interval, and compares the nearby three with the middle four without inferring
marking assignments. The contribution is not the invention of centroid-relative
geometry. It is the governed combination of an interpretable defensive-unit
reference, attacker-only exposure, strict temporal ordering, frozen controls,
heldout testing, external replication, and explicit interpretation boundaries.

### Revised “so what?”

The project now supplies a reproducible way to surface passages with strong
measured localized reorganization and contextualize them using the attacker’s
starting relationship to the ball and defensive unit before an analyst assigns
tactical meaning. A coach can separate a whole-unit shift from one or more
defenders moving differently within it; a club analyst can compare similar
attacker movements from different starting ball/block geometry without first
inventing marking labels; a sports scientist gets a provider-tested
individual–collective coordination measure with an explicit temporal control;
and a Sloan reviewer gets a prospectively governed, nine-match result plus
genuine negative boundaries. This is strong enough as a
measurement-and-validation paper without a value model, provided the paper does
not promise causation, tactics, or a demonstrated downstream benefit.

## 2. Evidence organized by scientific role

| Role | Closed evidence | Paper use |
|---|---|---|
| Measurement problem | Focal-relative path separates a defender's movement from the contemporaneous defensive-unit shift and replicated in heldout Metrica and IDSSE | Explain the primitive and acknowledge close centroid/coordination precedent |
| Main temporal result | Final Footprint A in Metrica; unchanged IDSSE external replication supported | Lead result: preceding attacker movement is associated with stronger subsequent near-than-middle defender-relative movement |
| Temporal qualification | Forward-minus-reverse paired excess is positive pooled in Metrica and IDSSE; reverse-time structure itself remains positive | Establish frozen time-order evidence without implying reaction or causation |
| Concurrent spatial form | Near-minus-middle concurrent localization is positive in Metrica Games 1–2 and all seven IDSSE matches | Supporting characterization, not the paper's primary result |
| Directional form | Metrica Game 1 coherent, Game 2 mixed; seven IDSSE matches supported | Secondary evidence about geometric form, with mixed internal replication explicit |
| Starting spatial context | IDSSE Context v1 supported: goalward attacker--unit offset and attacker--ball distance both have consistent negative slopes in 7/7 match and 7/7 LOMO fits | Characterize where measured reorganization is larger or smaller; do not infer why |
| Conditional spatial form | IDSSE Spatial Form v1 supported: outward-minus-goalward was 0.056856 m/m [0.051358, 0.062430] in 7/7 match and 7/7 LOMO directions; static versus dynamic lateral representation was inconclusive | Compact geometric characterization; do not call outward movement better or a source of value |
| Falsification and QC | Rank-only null is approximately zero; activity adjustment removed about 99.2% of induced synthetic localization; rank composition remains a moderate limitation | Address simple mechanical alternatives without claiming all confounding is removed |
| Consequence boundary | Opportunity Redistribution negative; Coverage Redistribution v3 mixed | Show that measured response is not established as separation, coverage, space creation, or value |

## 3. Manuscript skeleton

1. **Football problem:** analysts say that movement shifted or pulled a defence,
   but tracking alone does not say why defenders moved.
2. **Measurement problem:** raw displacement conflates collective defensive
   shift with internal defender reorganization.
3. **Construct:** leave-one-out defender-relative path, attacker-only preceding
   path, start-fixed D1–D10 ranks, and strictly prior context.
4. **Prospective evidence design:** Metrica development and untouched heldout
   replication, then unchanged seven-match IDSSE external replication.
5. **Main result:** stronger subsequent near-than-middle defender-relative
   association in both environments.
6. **Temporal control:** forward association exceeds the paired reverse-time
   comparison even though reverse-time structure remains positive.
7. **Contextual characterization:** starting attacker--unit and attacker--ball
   geometry characterize where the measured footprint is larger or smaller.
8. **Supporting form:** concurrent localization and attacker-direction geometry
   provide secondary geometric evidence.
9. **Interpretation boundaries:** observational common causes, moderate rank
   composition, negative opportunity, mixed coverage, and unsupported
   match-side identity.
10. **Practical use:** surface and contextualize candidate passages for review before assigning
   tactical meaning.
11. **Literature and limitations:** limited metric novelty; meaningful
   validation/application contribution; no gravity or value result.

Protocol history, rejected segmentation methods, complete robustness tables,
and consequence-design lineage belong in supplementary material rather than
the main narrative.

## 4. Reviewer attack and response

| Objection | Current answer | Required paper treatment |
|---|---|---|
| Forward ordering is not causation | The reverse-time control remains positive, but the paired forward excess is positive in pooled Metrica and IDSSE | Use “associated with” throughout; never use reaction, caused, induced, or influence |
| Player-to-team geometry is established | The project claims a governed validation/application contribution, not invention of relative geometry | Lead with the football measurement problem and replication design |
| Rank proximity may encode starting structure | Start-distance and prior-movement controls, synthetic nulls, and the composition audit reduce but do not eliminate this concern | Report the moderate goalward-offset composition limitation |
| Effect size may be statistically clear but practically abstract | The measure can surface localized reorganization for analyst review | Do not convert metres per metre into tactical value or decision quality |
| Far ranks rebound | The profile is stepped and non-monotonic; middle-minus-far is null in Metrica | Describe a near-versus-middle footprint, not a universal distance-decay law |
| Seven IDSSE matches are not seven providers | They are seven matches from one independent provider environment | State the sampling unit and provider scope explicitly |
| Provider smoothing support differs in physical time | Metrica's seven frames span 0.70 s and IDSSE's span 0.28 s; this was prospectively retained | Treat sign transport as support, not exact magnitude equivalence |
| The response has no demonstrated consequence | Opportunity was negative and coverage was mixed | Present this as a substantive boundary, not a result to rescue |

## 5. Game 3 contextual-hypothesis decision

### Candidates considered without opening Game 3

| Candidate | Football rationale | Identification risk | Decision |
|---|---|---|---|
| Movement direction relative to the defensive unit | Movement across or through a unit may require different adjustment than parallel movement | Requires an unvalidated unit axis, choice of signed/absolute projection, and interaction estimand | Do not spend Game 3; not selected for IDSSE Context v1 after its family lacked material DRD v2 contribution |
| Initial attacker position relative to the block | An attacker inside or near the block may have different local geometry | “Inside/near” requires consequential line, hull, or distance definitions | Do not spend Game 3; later narrowed to raw goalward centroid offset for IDSSE Context v1 |
| Initial distance to ball | Simple continuous geometry and interpretable even if null | Ball proximity mixes phase and possible on-ball/off-ball status without resolving why | Do not spend Game 3; later selected as a two-sided continuous IDSSE Context v1 hypothesis |
| Central versus wide start | Familiar football context | Pitch-band thresholds are arbitrary and can become role labels | Reject before Sloan |
| Defensive depth or compactness | Response may differ in compressed and stretched shapes | Several defensible compactness measures and cut points create multiplicity | Reject before Sloan |

**Game 3 decision remains B — KEEP GAME 3 UNTOUCHED BEFORE SLOAN.** None of the
candidates justified spending the last pristine Metrica holdout. After the
separate DRD v2 family-level result, an IDSSE-only
[context protocol](protocols/defensive_reorganization_context_v1.md) froze two
continuous starting relationships without using individual coefficients or
residuals. Its governed IDSSE result is **SUPPORTED**, but it does not alter
this Game 3 decision or supply a Game 3 authorization. No Game 3 outcome is
opened.

## 6. Working abstract drafts

### Sloan working draft (under 500 words)

**Working title:** *Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football*

**Introduction.** Analysts often describe an off-ball run as having shifted a
defence, but tracking data conflate two different phenomena: collective movement
of the defensive unit and individual defenders moving differently from that
unit. We develop a transparent observational method that separates those
quantities and tests whether preceding attacker movement is followed by
localized defensive reorganization in defender-relative movement without
inferring marking assignments, tactical roles, or attacking value.

**Methods.** Each defender's path is expressed relative to the contemporaneous
movement of the other defending outfield players. Attacker movement is measured
over a preceding fixed interval, defender proximity ranks are fixed before the
subsequent response interval, and the primary estimand compares the
attacker-movement coefficient for the three nearest defenders with the four
middle-ranked defenders. Models condition on strictly prior movement and spatial
context. Protocols were frozen before development, heldout, and external tests.
A reverse-time comparison assessed whether the attacker-before-defender
association exceeded background temporal structure.

**Results.** In two Metrica sample matches, the pooled near-minus-middle contrast
was 0.05029 m of defender-relative path per metre of preceding attacker path
(97.5% interval 0.03433–0.06858), with a paired forward-minus-reverse excess of
0.02912 (0.01410–0.04526). Under the unchanged design across seven IDSSE
matches, the pooled primary contrast was 0.06115 (95% interval
0.05579–0.06681). The reverse-time comparison remained positive at 0.03661
(0.03224–0.04111), but the paired forward-minus-reverse excess was 0.02455
(0.01932–0.02985). Primary and paired-excess estimates were positive in all
seven IDSSE matches and remained positive across frozen 1-, 2-, and 4-second
sensitivity windows. Across the seven IDSSE matches, reorganization was also
larger when attackers started less far goalward relative to the defensive unit
and closer to the ball; both context slopes had consistent signs in all seven
match and leave-one-match-out fits. The predeclared trim also passed for both
contexts, which were evaluated separately from the temporal primary model and
do not identify a tactical mechanism.

**Conclusion.** Preceding attacker movement is reproducibly associated with
stronger subsequent defender-relative movement among nearby than middle-ranked
defenders across two tracking environments. Because reverse-time structure
remains positive, the result supports a stronger time-ordered association, not
reaction time or causation. Separate prospectively specified tests did not
establish teammate separation or a robust downstream matching-geometry
consequence. The method therefore provides a reproducible measurement layer for
surfacing passages where off-ball movement is followed by localized defensive
reorganization before tactical meaning or value is assigned.

### Concise abstract (175 words)

Football tracking records where defenders move but not whether one defender
adjusted differently from a collective defensive shift. We measure each
outfield defender's path relative to the contemporaneous movement of the other
defending outfield players, then test whether attacker movement in a preceding
two-second interval is associated with stronger subsequent movement among
nearby than middle-ranked defenders. Proximity ranks are fixed before the
response interval, marking assignments are not inferred, and protocols were
frozen before development, heldout, and external tests. In two Metrica sample
matches, the pooled near-minus-middle contrast was 0.05029 m/m (97.5% interval
0.03433–0.06858), with paired forward-minus-reverse excess 0.02912
(0.01410–0.04526). Under the unchanged design across seven IDSSE matches, the
pooled primary contrast was 0.06115 (95% interval 0.05579–0.06681) and paired
excess was 0.02455 (0.01932–0.02985); both point estimates were positive in
all seven matches. Reverse-time structure remained positive, so this is an
observational time-order result, not causation. Across the seven IDSSE matches,
the measured reorganization was also larger when attackers started less far
goalward relative to the defensive unit and closer to the ball; both context
slopes had consistent signs in all seven match and leave-one-match-out fits. A
teammate-separation test was negative. The framework can surface and
contextualize passages of localized defensive reorganization for analyst review,
but does not establish tactical meaning, space creation, gravity, or attacking
value.

### Practitioner summary

The method separates a defender's movement from the shared shift of the rest
of the defensive unit, then asks whether nearby defenders move differently
after an attacker has moved. It also describes how the measured pattern varies
with the attacker’s starting relationship to the ball and defensive unit. The
pattern repeated in both Metrica matches and all seven IDSSE matches, so it can
help surface and contextualize candidate passages for video review—but it does
not say that the attacker caused the movement or that the movement created value.

## 7. Pre-Sloan work plan

1. Use the [flagship measurement-to-replication figure](figures/sloan/temporal_footprint_flagship.svg).
   Its real-pitch explanatory panel is the earliest chronological heldout
   Metrica Game 2 eligible anchor at or above the upper quartile of the
   governed preceding-attacker-path distribution. It is selected before, and
   without reference to, defender response magnitude or any football outcome.
2. Turn the working abstract into the paper's introduction, methods spine, and
   results table, keeping Context v1 and Spatial Form v1 as compact
   “where/what directional form?” characterizations rather than new primary
   results.
3. Complete a claim-language, reproducibility, and literature-positioning
   audit of the closed evidence.
4. Preserve the negative consequence results as compact interpretation
   boundaries.

Game 3 is not a generic replication reserve to spend merely because it exists.
Reconsider it only after Sloan or after an independently motivated contextual
construct has a unique, predeclared representation and estimand.

### Submission checklist from current repository guidance

- [x] Use the working paper title above and an abstract grounded only in closed
  governed methods and results.
- [x] Keep the abstract below the repository's documented 500-word target.
- [x] Lead with the football measurement problem, then state the reproducible
  time-ordered association and its interpretation boundary.
- [x] Use the flagship Figure 1 sequence: a heldout illustrative passage,
  cross-match temporal replication, and forward-versus-reverse comparison.
- [x] Keep the result observational; do not claim causation, tactical labels,
  space creation, gravity, or attacking value.
- [x] Preserve development, heldout, and external-validation provenance and
  the negative/mixed downstream results.
- [x] Include the supported IDSSE Context v1 result as bounded descriptive
  characterization, not tactical or causal interpretation.
- [ ] Resolve the existing manuscript decisions on target venue, author list,
  citation style, compact external-match table placement, and data/code
  availability wording before submission.

### Flagship figure caption

**Figure 1. Measuring localized defensive reorganization associated with off-ball movement.**
**(A)** A deterministic heldout Metrica Game 2 pitch passage: the earliest
chronological governed eligible anchor at or above the upper quartile of
preceding attacker path (period 1, 2336.04 s). This selection uses attacker
movement only—not defender response magnitude or an outcome. The three frames
show the preceding attacker path, actual absolute defender paths in the next
two seconds, and those paths after subtracting each defender's leave-one-out
defensive-unit shift. Near (D1–D3) and middle (D4–D7) are start-fixed proximity
ranks; no marking assignment is inferred. In this explanatory passage, the
defensive unit shifts goalward and laterally; D2 and D3 move less goalward than
their leave-one-out unit shifts, whereas D1 moves more goalward. This is not
evidence for a common all-near-defender pattern. **(B)** Governed near-minus-middle
associations between preceding attacker path and subsequent defender-relative
path across Metrica development, heldout, and seven IDSSE matches.
Within-environment pools are shown separately and are not a nine-match
meta-analysis. **(C)** The forward association exceeds the frozen reverse-time
comparison in pooled Metrica and IDSSE results, while reverse-time structure
remains positive. The figure shows an observational time-ordered geometric
association, not causation, tactical meaning, opportunity, or value.

**Figure strategy.** Keep the existing flagship as the sole main-text figure.
The governed Context v1 figure belongs in the supplement: its two continuous
context slopes are read more efficiently in the compact main-results table and
context subsection, while the figure provides useful supplementary diagnostics
for readers who need the full contextual shape. This is a presentation decision,
not a judgment about the validity of the Context v1 result.

## 8. Stop researching before submission

- Another consequence, opportunity, coverage, gravity, space-creation, or
  value metric.
- Another lag, response window, smoothing window, rank cutoff, or distance
  band.
- Marking, assignment, responsibility, reaction-time, or tactical-archetype
  classifiers.
- Player rankings, team-style models, scouting scores, or coaching verdicts.
- Further attacker-segmentation redesign.
- Generic Game 3 replication or an under-specified contextual moderator.
- Repairs or threshold searches intended to rescue closed negative or mixed
  results.
- GNNs, HMMs, clustering, latent-role models, or other complexity without a
  paper-critical identification need.

The submission can stop at an externally replicated, spatially localized,
time-ordered observational measurement with explicit limits. Attribution and
value remain future research rather than prerequisites for a coherent paper.
