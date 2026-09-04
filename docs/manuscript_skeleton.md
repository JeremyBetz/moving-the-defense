# Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football

> **Internal manuscript spine — not submission prose.** This outline uses only closed governed results. Status labels identify drafting work, not evidence strength: `[READY]`, `[NEEDS WRITING]`, `[NEEDS CITATION]`, `[NEEDS DECISION]`, and `[SUPPLEMENT]`.

## Abstract

**[READY]**

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

## 1. Introduction

### 1.1 Football problem

**[READY]** In football, the importance of an off-ball movement is often described through what the movement appears to make the defence do. An attacker may move away from the ball and a defensive line may slide, a nearby defender may step out while teammates hold, or several players may adjust around a threat. These descriptions focus on the changing defensive picture rather than ball events alone. Yet they make a stronger claim than tracking data directly provide: tracking records where players moved, not attention, responsibility, instruction, or whether a particular attacker caused a particular defender to move.

**[READY]** The measurement problem is especially clear when a defensive unit shifts together. A defender can cover substantial ground simply because the whole unit has moved, while another defender can move differently from that shared shift even when their absolute displacement is smaller. Treating either movement as an individual response conflates collective defensive movement with movement within the defensive structure. Conversely, a purely team-level description can conceal the local deviations that make a passage football-interesting. A measurement intended to study localized defensive reorganization must preserve both: the common movement of the unit and each defender's movement relative to it.

Football tracking research already offers many ways to describe this terrain. Studies of collective geometry quantify centroids, team spread, width, depth, and synchronized movement; coordination research examines how players and groups move together; and attacker-defender work studies proximity, relative motion, pressure, marking-like relationships, and space. Other work models trajectories, predicts future movement, estimates receiver availability or pitch control, and describes off-ball actions. These are important precedents, not gaps to be ignored. They also show why a narrow measurement claim is preferable to immediately translating movement into tactical or value language.

### 1.2 Research question

**[READY]** This paper asks a deliberately limited question: can preceding off-ball attacker movement be associated with localized subsequent defender-relative movement in a reproducible way? The aim is not to infer a marking assignment, a tactical role, or an attacker’s value. Instead, it tests an observable geometric relationship: after an attacker’s preceding path, do nearby defenders move more relative to their defensive unit than middle-distance defenders do, after conditioning on strictly prior movement context? This framing makes the football intuition testable while retaining the distinction between association and explanation.

The core representation places each defender in a moving reference frame defined by the other defending outfield players. Shared translation of the defensive unit is therefore largely removed, while movement that differs from the unit remains visible. The primary temporal estimand compares the association between preceding attacker path and subsequent defender-relative path for prespecified near (D1--D3) and middle (D4--D7) defender-distance ranks. Rank is a transparent local ordering at the anchor time, not a claim that the nearest defender is responsible for the attacker. A reverse-time comparison further asks whether the forward temporal association exceeds structure preserved under the same construction in reverse time.

Once that measurement is established, the paper asks a second descriptive
question: in which starting spatial contexts is the measured near-minus-middle
reorganization larger or smaller? This is a characterization of observed ball
and defensive-unit geometry, not a claim about tactical purpose or mechanism.

### 1.3 Contributions and boundaries

**[READY]** The contribution is a prospectively validated measurement that
separates collective defensive movement from localized internal reorganization,
and shows that off-ball movement direction is associated with those different
geometric scales across tracking environments. The study develops the measure in one
Metrica sample match, replicates it unchanged in a heldout Metrica match, and
then externally tests it across seven IDSSE/DFL matches from one independent
provider environment. It reports the forward association alongside a paired
forward-minus-reverse qualification, grouped block-bootstrap uncertainty, and
frozen trimming and horizon checks. It also records negative and mixed
downstream tests rather than treating any localized movement association as
evidence of space creation, stable defensive style, tactical success, or
attacking value.

The resulting scope is intentionally modest. The paper measures observable defensive geometry associated with preceding attacker movement. It does not directly observe intent, attention, responsibility, tactical instruction, a marking assignment, causal influence, or attacking value. The question is whether a reproducible measurement layer can be established before those later football interpretations are attempted.

## 2. Related Work

### 2.1 Collective team geometry

**[READY]** Positional tracking has long supported descriptions of football teams as moving spatial systems. Centroids, player-to-team-center distance, team surface area, width, depth, and stretch are established ways to summarize collective shape and its evolution (Frencken and Lemmink, 2011; Sampaio and Maçãs, 2012; Low et al., 2020; Rico-González et al., 2020). These measures make shared defensive displacement visible and provide a necessary baseline for any claim about individual movement. Recent tactical-analysis work likewise uses team-center frames and longitudinal or lateral deviations to describe configurations from tracking data (Zhang et al., 2025).

Coordination research goes beyond static shape. Player-team and team-team relative phase, vector coding, cross-correlation, and collective movement analyses have been used to study synchrony, compensation, and patterned co-movement (Duarte, Araújo, and Correia, 2013; Moura et al., 2016; Carrilho et al., 2020; Marcelino et al., 2020). This literature establishes that individual and collective motion should not be treated as independent by default. It also limits the novelty claim available here: using a team-centered reference is not new, nor is studying deviations from collective movement.

This study takes a narrower geometric route. It uses each focal defender’s position relative to the other nine defending outfield players and accumulates movement in that reference frame. The leave-one-out construction avoids including the focal player in its own reference, but it is a transparent refinement of established collective-relative geometry rather than a new theory of team shape. The paper does not turn residual movement into a phase measure, a synchrony category, or a claim about tactical coordination. It asks instead whether that observable defender-relative movement has a reproducible temporal association with preceding attacker path.

### 2.2 Attacker--defender relationships and marking/proximity

**[READY]** Football research also studies relationships between attackers and defenders directly. Dyadic distance, angle, relative velocity, directional alignment, and relative phase have all been used to describe interpersonal coordination in controlled and match contexts (Laakso et al., 2019; Vilar et al., 2014; Caetano et al., 2023; Narizuka and Yamazaki, 2016). Network and assignment-oriented approaches extend those relationships to whole defensive systems, including proximity-based marking dynamics and latent or role-conditioned defensive assignments (Buldú et al., 2020; Chacoma et al., 2022; Groom et al., 2026; Calero-Sanz et al., 2026). Such work is directly relevant to the football question of how attackers and defenders organize around one another.

Those approaches answer different questions from the one considered here. A proximity or assignment model can be designed to infer who is covering whom, whereas the present analysis does not infer a pairing at all. Defenders are ranked only by distance to an attacker at a fixed anchor time, and the rank is held fixed to define a reproducible comparison. Near, middle, and far are thus spatial categories within a complete defensive block, not labels for pressure, marking, responsibility, or relevance. This distinction matters because a nearby defender can be covering space, recovering from another action, or simply sharing the same local geometry.

The paper is consequently complementary to relational and marking research. It tests whether the defender-relative movement association is more pronounced among prespecified nearby ranks than among middle ranks, while leaving any interpretation of the relationship to later work with richer context. The aim is not to replace dyadic coordination, marking networks, or assignment inference; it is to establish a simple observational quantity that can eventually sit alongside them.

### 2.3 Space, pressure, and availability

**[READY]** Pressure and space models show why proximity alone is not a complete football concept. Pressure can depend on distance, angle, speed, ball location, and the wider local configuration; space-control and availability models combine player dynamics, interception or reachability, and sometimes technical or value assumptions (Link, Lang, and Seidenschwarz, 2016; Spearman, 2018; Fernández and Bornn, 2018; Dick, Link, and Brefeld, 2022; Forcher et al., 2024). These models are valuable when the target is ball pressure, pass availability, controlled space, chance creation, or outcome value.

The present outcome is deliberately earlier in that chain. It is subsequent defender-relative movement, not pressure, accessible space, receiver availability, or a possession outcome. This choice avoids importing an unvalidated equivalence between a change in defensive geometry and a football consequence. The paper’s negative and mixed downstream results are therefore substantive boundaries: localized defensive reorganization should not be read as demonstrated teammate separation, coverage, or attacking value merely because it is observable in tracking data.

### 2.4 Off-ball movement and trajectory modelling

**[READY]** Off-ball movement is already an active tracking topic. Relative-movement pattern recognition, trajectory prediction, ghosting, and commercial run-detection systems demonstrate that player paths can be described at multiple temporal scales and for several purposes (Beernaerts et al., 2020; Le et al., 2017; Llana et al., 2022). Recent reviews also emphasize fragmented definitions, heterogeneous methods, and limited integration of opponents and situational context in off-ball football research (Esposito et al., 2026). These are reasons to avoid treating a two-second path as a universal definition of a run or an off-ball action.

Here, preceding attacker path is an exposure variable over a fixed, prospectively governed interval. It is not a tactical run label, an episode segmentation claim, or an assessment of movement quality. The fixed-window choice allows a direct temporal question—whether a preceding observed path is associated with later defender-relative movement—while the project’s separate movement-representation work remains appropriately cautious about defining finite attacker efforts. This paper therefore contributes neither a new run detector nor a new trajectory model; it uses a transparent observed path to test a narrower defender-relative association.

### 2.5 Closest analogues outside football

**[READY]** Cross-sport defensive models further illustrate both the opportunity and the boundary of the present work. Basketball matchup inference can use player tracking to describe spatial defensive structure without assuming that simple nearest-player rules are assignments (Franks et al., 2015). Football ghosting and multi-agent trajectory work show how predicted movement can support later contextual or counterfactual questions (Le et al., 2017; Yeh et al., 2019). Space-creation and gravity-style architectures likewise demonstrate that an observed defensive pattern can be separated from an expected pattern only after additional modeling and validation (Fernández and Bornn, 2018; NBA.com Staff, 2026).

**[READY] Narrow gap.** This study does not claim those later layers. Its potentially differentiated contribution is the governed combination of an attacker-centered exposure, a leave-one-out defender-relative outcome, fixed rank localization, strictly prior movement conditioning, a reverse-time qualification, and prospective replication across development, heldout, and external environments. The contribution is therefore principally one of measurement discipline and validation: it tests whether a simple localized temporal association survives designs intended to expose rather than conceal its limits. It does not establish that the observed association is causal, tactical, assignment-specific, or valuable.

## 3. Data

### 3.1 Development and heldout sample: Metrica

**[READY]** We used two Metrica sample matches for within-provider development and replication. Game 1 was used to develop and close the governed temporal measurement; Game 2 was then held out for the rank-conditioned temporal relationship and executed under the unchanged protocol. Analyses used canonical metric pitch coordinates, complete tracking support over each governed interval, and nonoverlapping four-second endpoint cadence. These sample matches provide a transparent development environment, not a representative population of football matches or teams.

### 3.2 External replication: IDSSE / DFL

**[READY]** External replication used seven complete professional matches from the IDSSE/DFL environment, an independent tracking-provider environment rather than seven distinct providers. Native tracking cadence was 25 Hz, so the frozen centred seven-frame support spans 0.28 seconds. The external temporal analysis contained 72,316 attacker-anchor observations, 7,300 unique match-period-time anchors, and 723,160 defender rows. Its purpose was to test transport of the already specified measurement and temporal association, not to estimate a league-wide effect.

### 3.3 Availability and provenance

**[READY]** Provider-derived raw tracking and observation-level rows are not redistributed where restricted. The public materials instead provide source code, compact governed outputs, hash ledgers, and regeneration procedures. Provider-specific ingestion, coordinate equivalence, and detailed support requirements are reported in the supplement so that the main paper can focus on the measurement and its validation boundary.

**[READY]** Across both environments, an observation is retained only when the attacker and a complete defending outfield unit have the governed support needed for the full context, exposure, and response construction. This requirement makes the defender-relative reference interpretable at every path step, but it also means that results apply to supported open-play observations rather than every frame of every match.

**[SUPPLEMENT]** Dataset licensing, raw-data access paths, canonical coordinate contract, tracking cadence/support requirements, player metadata, and the full eligibility/exclusion ledgers.

## 4. Methods

### 4.1 Defender-relative representation

**[READY] Plain-language statement.** A defender can move substantially because the entire defensive unit shifts. We therefore measure each defender relative to the other defending outfield players rather than relative to a fixed pitch point. A shared shift largely cancels in this moving reference frame, while movement that differs from the unit remains visible. This is a description of geometry within the unit, not a claim about why that defender moved.

**[READY] Formal definition.** With ten defending outfield players and focal defender \(d\),

\[
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),\qquad
\mathbf c_{-d}(t)=\frac{1}{9}\sum_{j\ne d}\mathbf x_j(t).
\]

The goalkeeper is excluded, and the focal defender is excluded from its own reference. We then measure focal-relative path by accumulating Euclidean changes in \(\mathbf r_d(t)\) over a governed interval. For ten defenders, \(\mathbf x_d-\mathbf c_{-d}=\tfrac{10}{9}(\mathbf x_d-\mathbf c)\). Thus leave-one-out centering is a rank-independent rescaling of the focal defender’s deviation from the full outfield centroid, rather than a mechanism that can create a rank-specific pattern.

**[READY] Boundary.** This geometry measures movement within a defensive structure. It does not identify a mark, assignment, tactical responsibility, pressure, or why a defender moved.

The representation also retains a useful football distinction that raw distance-to-attacker measures do not. A defender may remain close to an attacker while moving with the unit, or may become more distant while departing from the unit; neither situation alone establishes a defensive meaning. The focal-relative path is therefore a movement-magnitude primitive, not a substitute for proximity, pressure, coverage, or space-control measures. Those constructs require their own context and validation.

### 4.2 Temporal defender-relative association

**[READY] Timing.** At each anchor \(t\), strictly prior defensive context is measured over \([t-4,t-2]\), attacker exposure over \([t-2,t]\), and the primary subsequent defender response over \([t,t+2]\). The exposure \(X_i\) is the attacker’s two-second path length before the defender outcome begins. The primary outcome for rank \(k\) is the two-second focal-relative path \(Y_{ik}=P_{\mathrm{rel}}(D_k;t,t+2)\). This ordering does not prove that the attacker caused the subsequent movement, but it prevents the outcome itself from defining the exposure.

**[READY] Rank construction.** At \(t\), the ten supported defending outfield players are ranked by Euclidean distance to the attacker; the ranks are fixed before the response interval and never reassigned during the context, exposure, or response windows. D1--D3 form the prespecified near region, D4--D7 the middle region, and D8--D10 remain descriptive. Rank is relative ordering within a complete defensive block, not a marking label or a proxy for responsibility.

Each retained anchor requires complete raw and centred-seven-frame smoothed support for the attacker and the same ten defending outfield players across the primary \([t-4,t+2]\) span, exact canonical endpoints, no period crossing, and the frozen restart/ball-out exclusion. The goalkeeper is excluded before rank construction. This complete-unit requirement avoids changing the collective reference or the membership of a rank vector midway through the comparison. Exact ties are resolved prospectively by canonical player key; no tolerance or jitter is added.

**[READY] Frozen primary model.** For rank \(k\), with prior rank-specific focal-relative path \(B_{ik}=P_{\mathrm{rel}}(D_k;t-4,t-2)\) and prior full defending-outfield centroid path \(C_i\), fit the stacked rank-specific model without a global intercept:

\[
Y_{ik}=\sum_{r=1}^{10}I(k=r)
\left(\alpha_r+\beta_rX_i+\gamma_rB_{ik}+\eta_rC_i\right)+\varepsilon_{ik}.
\]

The model permits each rank to have its own intercept, attacker-path association, strictly prior focal-relative baseline, and strictly prior full-unit centroid-path association. It therefore does not impose a common baseline across ranks or a smooth distance-decay curve. The primary estimand is the near-minus-middle contrast \(N-M\), where \(N=(\beta_1+\beta_2+\beta_3)/3\) and \(M=(\beta_4+\beta_5+\beta_6+\beta_7)/4\). D8--D10 are retained to show the whole rank profile but do not define the primary claim.

The baseline \(B_{ik}\) and centroid-path context \(C_i\) are strictly earlier than attacker exposure. They therefore adjust for pre-existing rank-specific defender-relative movement and whole-unit movement without conditioning on movement from the exposure interval itself. The model remains an observational association model: conditioning makes the comparison more specific, but cannot eliminate unmeasured shared match context.

The near-minus-middle contrast is intended to test localization rather than to select the visually most active defender after the fact. Averaging within the two pre-specified rank regions reduces emphasis on any single rank while keeping the comparison close to the attacker-centered football question. A positive contrast means that the fitted attacker-path association is larger for the near group than for the middle group; it does not mean that every nearby defender moved more in every passage, that middle defenders were uninvolved, or that the near group had a tactical assignment.

### 4.3 Starting spatial context

**[READY]** A separate, IDSSE-only governed context analysis used the same
anchor-level near-minus-middle subsequent defender-relative path as its target.
It fit raw-unit OLS models for two predeclared starting relationships: the
focal attacker’s goalward position relative to the defensive-unit centroid and
the focal attacker’s distance to the ball. Each model included attacker
exposure path, prior attacker path, defensive-unit depth, and the ball’s
goalward position relative to the defensive-unit centroid, plus match
intercepts. We report the pooled association, seven match-specific fits, seven
leave-one-match-out fits, familywise 97.5% block-bootstrap intervals, and the
predeclared central-support trim. This characterization asks where the observed
near-minus-middle geometry is larger or smaller; it does not estimate tactical
intent, a causal mechanism, or a new response outcome.

### 4.4 Validation controls and uncertainty

**[READY] Reverse-time comparison.** Football movement is temporally autocorrelated, and attacker and defender motion can share ball, phase, or other common causes. A positive forward association alone therefore does not establish meaningful time ordering. The frozen reverse-time control pairs earlier defender-relative movement over \([t-2,t]\) with nominally future attacker path over \([t,t+2]\), while retaining the same anchor, rank construction, and strictly earlier covariates. We report the paired forward-minus-reverse excess from identical bootstrap draws. A positive excess supports a stronger correctly ordered temporal association; it does not establish causality or a reaction time.

**[READY] Inference and sensitivity.** Uncertainty uses the frozen 60-second match-period block bootstrap with 2,000 replicates and empirical percentile intervals. Blocks are resampled within match-period, while simultaneous attacker observations at an anchor and their complete ten-defender rank vectors remain together. This preserves the grouped dependence structure better than treating defender rows or frames as independent. The analysis also retains pre-specified extreme-exposure trimming and 1-, 2-, and 4-second response-horizon checks. These are robustness checks fixed in advance, not a search for a preferred lag, rank, or window.

**[SUPPLEMENT]** Full endpoint, smoothing, support, restart/ball-out, tie-handling, bootstrap, classification, numerical-boundary, and provider-equivalence specifications.

## 5. Validation Design

**[READY]** Validation was staged to distinguish a development finding from a reproducible measurement. Metrica Game 1 was used for development under a frozen protocol. Metrica Game 2 was then analyzed as a protected heldout replication with the same representation, temporal windows, ranks, model, reverse-time comparison, and robustness rules. Only after Game 2 outputs were serialized, hashed, and independently reproduced were the two Metrica matches compared and pooled under the pre-specified model.

External replication then applied the same temporal design across seven IDSSE/DFL matches. Before interpreting external coefficients, a provider-equivalence gate verified the relevant raw time and frame identities, player/team/goalkeeper identity, coordinates and masks, cadence, event context, complete ranks, and derived components. The gate is not a claim that providers are interchangeable in every respect; it establishes that the governed representation and its inputs transferred for this analysis.

All protocols, rank regions, windows, controls, and classification rules were frozen before their protected outcomes. No alternate lag, rank definition, or response window was selected after results were seen. We retain match-level external estimates alongside the prospectively defined pooled summary, so a pooled coefficient does not conceal inconsistent match signs. Full hash ledgers, classification mechanics, and equivalence details are supplied as reproducibility material rather than main-text clutter.

The validation sequence was designed to make a negative or mixed result informative. A failure to replicate would have remained part of the evidence record rather than prompting a new rank grouping, lag, or model in the protected sample. Independent reruns reproduced governed outputs before their role in the next validation stage was interpreted. This discipline does not remove all observational uncertainty, but it separates a reproducible measurement result from a pattern found only through iterative development.

The resulting validation claim is correspondingly narrow: a result can be externally replicated as observable geometry without being a validated account of defensive tactics. The staged design tests reproducibility of the measurement and its time-ordered association, while preserving the need for separate semantic, causal, and value validation.

## 6. Results

### 6.1 Primary temporal association

**[READY] Metrica.** Across the prospectively pooled Metrica analysis, the near-minus-middle association was `0.05029 m/m` with a frozen 97.5% bootstrap interval of `[0.03433, 0.06858]`. In the fitted observational model, one additional metre of preceding attacker path was associated with approximately `5.0 cm` more subsequent defender-relative path for the near ranks than for the middle ranks. The paired forward-minus-reverse excess was `0.02912` `[0.01410, 0.04526]`. Reverse-time structure was therefore not absent; the qualifying evidence is that the correctly ordered association was larger under the prospectively paired comparison.

The Metrica result is a within-provider replication across the development and heldout sample matches, not a claim of general professional-football prevalence. Its stepped rank profile also matters: the primary evidence concerns the pre-specified near-versus-middle average, not a smooth assertion that every additional metre of defender distance weakens the association.

The pooled Metrica intervals use the frozen 97.5% convention. They quantify stability under the specified match-period block resampling scheme rather than a population-wide causal effect. The same caution applies to the positive paired excess: it is evidence that the forward contrast was larger than its reverse-time counterpart under the governed comparison, not evidence that all common causes were removed.

**[READY] IDSSE external replication.** In the independent provider environment, the pooled primary near-minus-middle association was `0.06115 m/m` with a 95% bootstrap interval of `[0.05579, 0.06681]`. The reverse-time comparison was also positive, `0.03661` `[0.03224, 0.04111]`, but the paired forward-minus-reverse excess was `0.02455` `[0.01932, 0.02985]`. Primary and paired-excess point estimates were positive in all seven matches. The near-minus-middle sign also remained positive at the frozen 1-, 2-, and 4-second response horizons; the extreme-exposure trim retained 95.35% of the primary magnitude.

The external result therefore reproduces the direction and timing-qualified association in seven matches within one independent provider environment. It does not convert the seven matches into seven provider replications, nor does it establish a causal attacker-to-defender mechanism. The positive reverse-time estimate remains a reminder that shared movement structure persists even under the temporal comparison.

The IDSSE intervals use the transported 95% convention. Keeping both the forward and reverse estimates visible is important: reporting only the primary association would overstate what time ordering contributes. The paired excess is the relevant temporal comparison, while the continuing reverse-time structure is an explicit limitation of a purely observational design.

**[READY] Effect-size translation.** As an illustrative model-based translation, a five-metre difference in preceding attacker path corresponds to roughly `0.31 m` more subsequent near-versus-middle defender-relative path under the pooled IDSSE model. This is a linear translation of the fitted association, not a claim that five metres is a typical run or that attacker movement caused the difference.

In practical terms, the coefficient describes how the fitted difference between nearby and middle defender-relative movement changes with observed preceding attacker path. It does not estimate how far a named defender must move in a particular play, and it should not be read as a threshold for analyst judgment.

### 6.2 Spatial context of defensive reorganization

**[READY]** The temporal result establishes a reproducible, time-ordered
association; the separate Context v1 analysis asks in which observable starting
geometries its measured magnitude was larger or smaller. It uses the same
anchor-level near-minus-middle subsequent defender-relative path, rather than a
DRD residual or a tactical label. Both predeclared contexts were evaluated in
the seven-match IDSSE sample using raw-unit OLS with frozen attacker-movement,
prior-movement, defensive-depth, ball-position, and match controls.

First, the attacker’s goalward position relative to the defensive-unit centroid
had a pooled association of `-0.010161 m/m` (familywise 97.5% interval
`[-0.011805, -0.008499]`). Thus, conditional on the frozen controls, the
measured near-minus-middle defender-relative movement was smaller when the
attacker started farther goalward of the defensive unit. The estimate had the
pooled negative sign in all `7/7` match-specific and all `7/7`
leave-one-match-out fits, and the central-support trim passed. A 10 m greater
goalward offset corresponds to `-0.10161 m` in the fitted response; across the
observed 10th--90th percentile span, the fitted difference is approximately
`-0.32453 m`.

Second, attacker--ball distance at exposure start had a pooled association of
`-0.007533 m/m` (familywise 97.5% interval `[-0.008864, -0.006245]`). The
measured difference was therefore also smaller when the attacker began farther
from the ball. This direction was retained in all `7/7` match-specific and
`7/7` leave-one-match-out fits, and the trim passed. A 10 m greater
attacker--ball distance corresponds to `-0.07533 m`; across its observed
10th--90th percentile span, the fitted difference is approximately `-0.28586
m`.

In football-readable terms, the governed geometry was larger when attackers
started less far goalward relative to the defensive unit and closer to the
ball. This is a contextual description of observed movement, not evidence of
between-the-lines positioning, showing short, drawing defenders, press baiting,
tactical intent, or value. It nevertheless makes the measurement more useful
for review: analysts can compare passages with similar attacker movement but
different starting ball and defensive-unit geometry, then inspect the wider
football context on video.

### Table 1. Compact main-paper results recommendation

**[READY — main paper.]** Keep the temporal visual evidence in Figure 1 and
use one compact table for the principal estimates and context characterization.
It should not replace the full rank, robustness, or match-level tables in the
supplement.

| Analysis | Estimate (m/m) | Interval | Replication / consistency |
|---|---:|---|---|
| Temporal Metrica near--middle | 0.05029 | 97.5% [0.03433, 0.06858] | Pooled Games 1--2 |
| Temporal Metrica paired forward--reverse | 0.02912 | 97.5% [0.01410, 0.04526] | Pooled Games 1--2 |
| Temporal IDSSE near--middle | 0.06115 | 95% [0.05579, 0.06681] | Positive in 7/7 matches |
| Temporal IDSSE paired forward--reverse | 0.02455 | 95% [0.01932, 0.02985] | Positive in 7/7 matches |
| Context H1: attacker minus unit, goalward | -0.010161 | 97.5% [-0.011805, -0.008499] | 7/7 match; 7/7 LOMO; trim passed |
| Context H2: attacker--ball distance | -0.007533 | 97.5% [-0.008864, -0.006245] | 7/7 match; 7/7 LOMO; trim passed |
| Spatial Form IDSSE: outward minus goalward | 0.056856 | 95% [0.051358, 0.062430] | 7/7 match; 7/7 LOMO |
| Spatial Form SkillCorner: outward minus goalward | 0.048883 | 95% [0.042940, 0.054707] | 9/9 match; 9/9 LOMO |

### Figure 1. Measurement and replication overview

**[READY — position at the Methods/Results transition in final layout; retained
here after the compact results table for drafting reference.]**

> **Figure 1 introduction draft.** Figure 1 links the measurement to the population result. Panel A shows a real heldout passage, selected solely from attacker movement and chronology, in which the defensive unit shifts while individual defenders move differently from that shift. Panel B summarizes the Metrica and IDSSE temporal replication. Panel C shows why the result is qualified by the prospectively frozen paired forward-minus-reverse comparison rather than by an assumption that reverse time contains no structure.

**[READY] Panel A uses Metrica Game 2, period 1, 2336.04 s, Home 1. The unit shifts goalward and laterally; D2 and D3 are less goalward than their leave-one-out unit shifts, while D1 is more goalward. This is a heterogeneous, factual illustration of the representation, not population evidence and not a tactical label. Panels B and C are the governed cross-match temporal replication and forward-versus-reverse summaries.

### 6.3 Supporting concurrent geometry and coordination form

**[READY] Concurrent localization.** A separately governed concurrent analysis provides supporting evidence that the temporal finding is not solely a consequence of the lagged construction. In Metrica Game 1, the concurrent near-minus-middle contrast was `0.02667 m/m` with a 95% interval of `[0.01134, 0.04487]`; the unchanged Game 2 replication was `0.04463 m/m` `[0.02151, 0.07848]`. Both were positive under their frozen within-provider design.

The external concurrent analysis likewise found a pooled IDSSE near-minus-middle contrast of `0.05115 m/m` `[0.04595, 0.05642]`, with positive estimates in all seven matches and 91.71% of the magnitude retained after the transported trim. Concurrent localization remains supporting rather than the paper’s spine: attacker and defender movement share the same interval, so common movement or phase context is especially difficult to exclude. Together with the temporal result, however, it shows that the near-versus-middle pattern is visible both during and after the governed attacker-path interval.

The within-provider results also show why the result should be expressed as a regional contrast rather than a single-defender story. In Game 1, the nearest rank was especially elevated, while in Game 2 both D1 and D2 contributed to the near-region pattern. Descriptive far ranks exceeded middle ranks in both matches. The concurrent analysis therefore supports a localized comparison, not the claim that one closest defender alone carries the relevant geometry or that the entire defensive block follows a rigid distance gradient.

**[READY] Directional form.** A second supporting analysis asked whether defender-relative motion aligned with attacker direction, rather than only whether its scalar path was larger. In Metrica Game 1, the prespecified D2--D3 minus D4--D7 contrast was `0.04045 m/s` `[0.02366, 0.05538]`, yielding a development-coherent result. The heldout Metrica Game 2 point estimate was similar in direction, `0.04587 m/s`, but its interval `[-0.01056, 0.09260]` crossed zero; that replication is formally mixed and should not be presented as individually decisive.

The external directional-form replication was supported across all seven IDSSE matches: every primary estimate was positive with an interval above zero, D1 was the largest coefficient in every match, and D2 and D3 were individually positive in every match. This matters because the directional signal was not confined to a single nearest defender. It remains geometric evidence, not proof of tracking, marking, tactical coordination, or responsibility.

The scalar and directional analyses answer complementary measurement questions. The temporal footprint asks how much defender-relative movement is associated with preceding attacker path; the directional analysis asks whether a component of local movement aligns with attacker direction. Neither converts that alignment into a behavioral label. Their agreement across the external matches strengthens the case that the primary result is not merely a generic aggregate-movement summary, while their differing Metrica precision cautions against collapsing them into one score.

**[READY] Rank shape.** Neither the scalar nor directional results form a simple monotonic distance-decay curve. Near ranks are elevated relative to the pre-specified middle region, but far ranks can rebound; all pooled IDSSE scalar rank coefficients were positive. The main text therefore reports a localized near-versus-middle contrast and a stepped, nonmonotonic rank structure. Full D1--D10 tables belong in the supplement.

### 6.4 Movement direction and scale of defensive response

**[READY]** A separate Spatial Form analysis asks whether the established
localized near-versus-middle geometry differs by the direction of attacker
movement, after the frozen path and starting-context adjustment. In IDSSE,
outward rather than goalward displacement was associated with `0.056856 m/m`
greater subsequent localized reorganization (95% interval `[0.051358,
0.062430]`), with the same direction in all `7/7` match-specific and
leave-one-match-out fits. A separately governed SkillCorner replication found
the same outward-minus-goalward contrast, `0.048883 m/m` `[0.042940,
0.054707]`, in all `9/9` match and leave-one-match-out fits. These are
replicated directional associations in localized geometry, not evidence that
outward movement drags a defender or is football-superior.

Response Mode v1 then tested a narrower possible explanation: whether inward
rather than outward movement was associated with greater pitch-axis width
reduction. The frozen 5 m inward-minus-outward contrast was positive at
`0.134003 m`, but its 95% interval crossed zero (`[-0.006622, 0.273430]`) and
only `5/7` match contrasts were positive. Although all leave-one-match-out
fits were positive and the signed-movement trim passed, the primary width
hypothesis was therefore **MIXED**. This is suggestive but insufficient
evidence for a narrowing mechanism, and the protocol’s stop rule precludes
searching another shape metric to recover one.

Under that same frozen model, goalward movement was descriptively associated
with substantially greater goalward defensive-centroid displacement than
outward movement: the 5 m goalward-minus-outward contrast was `2.962709 m`
`[2.870720, 3.048322]`, with positive directions in all `7/7` match and
leave-one-match-out fits. This translation result was secondary and
nonclassifying, so it is not retroactive confirmation of a mechanism.
Together, the results support a limited response-scale synthesis: different
movement directions are associated with defensive geometry at different
observable scales. They do not establish why the block translated, why local
reorganization differed, how the channels relate mechanically, or whether
either pattern has tactical or attacking value. In particular, the results do
not partition a fixed defensive response into mutually exclusive collective and
local shares: the same passage can translate, narrow, rotate, shear, and
reorganize internally at once. Separate models keep those observable views
legible without turning their combination into a new response score.

### 6.5 What the measurement does not establish

**[READY] Boundary results.** The measurement does not show that local defensive reorganization creates a downstream opportunity. Opportunity Redistribution v1 tested the simple hypothesis that a larger focal-local defensive change would be associated with relatively improved nearest-defender separation for other initially local attackers. The Game 1 primary estimate was negative and uncertain, \(\beta_D=-0.02407\) with a 95% bootstrap interval of `[-0.09392, 0.04776]`. The predicted separation consequence was therefore not supported. This is a boundary result for the tested representation, not evidence that attacker movement never changes teammates’ opportunities.

A second, more structured geometric consequence was also not robustly established. Defensive Coverage Redistribution v3 produced \(\hat\beta_D=0.0983933\) m/m with a 95% bootstrap interval of `[-0.0384013, 0.2050032]`; its formal status was **MIXED** because the interval crossed zero and the estimate did not exceed the frozen direction-null 95th percentile. Neither result justifies translating measured defensive geometry into coverage, space creation, or attacking value.

Finally, Defensive Response Expectation found no material match-side-specific predictive increment beyond movement and modelled spatial context under its frozen design. The E2b model worsened relative to E1 by `0.0616%` and improved `0/7` matches, yielding **NOT SUPPORTED**. This result does not imply that teams lack defensive styles; it says only that this design did not establish a material match-specific component. Full robustness, expectation-model, and downstream-consequence detail belongs in the supplement.

**[SUPPLEMENT]** Complete negative/mixed branch reports, rank-profile tables, and the defender-rank composition audit. The audit found a moderate composition limitation: goalward centroid-offset separation had a median standardized difference of `-0.3384` across nine checks, while leave-one-match-out AUC was `0.6267` (all below `0.65`), and activity conditioning removed 99.22% of induced localization in a synthetic rank-only null.

## 7. Football Interpretation / Analyst Use

**[READY]** The method is best understood as a measurement and retrieval layer. It can identify passages in which preceding attacker movement is followed by defenders moving differently from their collective defensive structure, then make that geometry available for football review. It does not decide whether the movement was a step, drop, cover, track, hold, recovery, or error. Those are football interpretations that require ball position, teammates, opponents, video, and analyst judgment beyond the representation itself.

Figure 1 provides a concrete heldout example. In Metrica Game 2 at 2336.04 s, the defensive unit shifted `+7.498 m` goalward and `+5.672 m` laterally. Within that shared shift, D2 and D3 moved less goalward relative to their leave-one-out unit shifts, whereas D1 moved more goalward. The passage is heterogeneous: its point is not that one defender has been shown to mark, track, or respond correctly to a named attacker. Rather, it demonstrates how the defender-relative representation makes internal unit movement visible when raw absolute trajectories would primarily show the common shift.

A practical analyst workflow is therefore deliberately simple:

1. identify a governed attacker-movement interval;
2. quantify the subsequent localized defender-relative reorganization;
3. surface passages with a notable defender-relative pattern for review;
4. inspect video and the wider tracking context; and
5. assign any tactical interpretation only after that contextual review.

This workflow can support retrieval of candidate off-ball passages, comparison
of how similar attacker movements coincide with different defensive geometries,
and contextualization using the attacker’s starting relationship to the ball and
defensive unit. It is a research layer before more assumption-heavy tactical or
value models, not a player-ranking system or an automatic tactical-labeling
tool. Figure 1 plus Table 1 and this prose are sufficient for the main paper;
the Context v1 figure is recommended for the supplement because the two compact
context rows communicate the limited “when” result without adding a second main
figure.

For a club analyst, the value is in narrowing a large tracking archive to reviewable questions without pre-committing to an answer. A high footprint may prompt review of whether the unit was shifting, whether a defender had to protect another space, whether the ball or another attacker supplied the more plausible context, or whether the apparent pattern is ordinary transition movement. A low footprint can be equally informative when an attacker moved but the unit stayed internally coherent. The measurement supplies comparable geometric evidence; football judgment remains with the analyst.

Because the output is continuous and rank-specific, it can also support side-by-side review rather than a binary event feed. Analysts can compare passages where the defensive block largely translates with passages where local defender-relative geometry is more pronounced, then decide whether the extra context warrants a tactical label. The system should preserve uncertainty and raw geometry at that review stage rather than conceal them behind a single score.

## 8. Limitations

**[READY]** First, the evidence is observational. Forward associations exceeded their reverse-time comparisons, but reverse-time structure remained positive. Attacker and defender motion can share ball, phase, possession, transition, or other unmeasured context. The paired excess strengthens evidence for correctly ordered temporal association; it does not establish causal influence, reaction time, or a one-way attacker-to-defender mechanism.

Second, proximity rank is a representation rather than a direct football role. Near and middle ranks encode attacker proximity together with some unit-relative geometry. The outcome-blind rank-composition audit found only moderate non-distance structure, but residual role, zone, or match-state structure can remain. The rank profile is also stepped and nonmonotonic: near ranks are elevated relative to middle ranks, while far ranks can rebound. The results should therefore not be summarized as a simple law that an effect weakens with distance.

Third, the empirical breadth remains limited. Two Metrica sample matches and seven IDSSE matches in one independent provider environment provide meaningful heldout and external replication, but not a representative sample of football, teams, tactics, or tracking providers. Metrica and IDSSE differ in provider processing and sampling environment, including the physical span of the fixed seven-frame smoother. The design establishes transfer of this governed measurement, not provider-invariant effect magnitudes.

Fourth, Game 1 was used iteratively during development of several constructs. The heldout Game 2 and external IDSSE results are therefore especially important, but they do not erase the distinction between development evidence and preregistered-like confirmation. The full protocol history, equivalence checks, and reproducibility materials remain available so readers can separate those roles.

The required complete-support construction is another scope condition. It produces a consistent leave-one-out reference and fixed rank vector, but excludes intervals with incomplete player support, period crossings, or governed restart/ball-out context. The estimand is consequently about eligible, supported open-play observations, not every possible defensive action. Restricted provider-derived observation rows also limit independent reconstruction without approved data access, although compact outputs, code, and hash-ledger materials make the governed workflow inspectable.

The separate supporting analyses should not be treated as interchangeable replications. Concurrent geometry has the strongest shared-time confounding concern; directional form has a mixed Metrica Game 2 result even though all seven IDSSE matches support it. These differences are informative about scope and measurement, not an invitation to choose whichever representation is most favorable in a particular passage.

The response-scale descriptions are also nonorthogonal and nonexhaustive.
Translation, pitch-axis width/depth, and localized defender-relative movement
can change together; rotation and shear were not separately modelled. The
centroid-translation result in Response Mode v1 was secondary/nonclassifying,
and its width-collapse mechanism was mixed. The evidence therefore supports
observable scale differences, not a complete allocation of a defensive
response or a resolved mechanism.

Finally, the statistical intervals describe uncertainty under fixed grouped resampling and the governed samples. They are not estimates of a universal player-, team-, or league-level distribution. More repeated-team and multi-competition data would be needed before comparing teams or players, estimating heterogeneity, or attaching a stable style interpretation to the measurement.

Finally, tracking geometry does not reveal marking responsibility, tactical instruction, attention, intent, or whether a movement was correct. The real examples are illustrative and cannot validate the population estimand by themselves. Nor are downstream consequences established: Opportunity Redistribution did not support the tested nearest-defender-separation consequence, Coverage Redistribution was mixed, and the expectation analysis did not identify a material match-specific predictive increment. Localized defensive reorganization is therefore a measured geometric layer, not demonstrated opportunity creation, tactical success, gravity, or off-ball value.

## 9. Conclusion

**[READY]** This study establishes a reproducible observational measurement layer for localized defensive reorganization associated with preceding off-ball attacker movement. Across Metrica development and heldout matches and seven IDSSE matches in an independent provider environment, preceding attacker path was more strongly associated with subsequent defender-relative movement among near than middle defender ranks. The forward association also exceeded the prospectively paired reverse-time comparison. Concurrent and directional analyses provide supporting evidence that localized internal unit reorganization is visible beyond a single scalar temporal result.

The conclusion is deliberately narrower than common football language. The measurement does not show that an attacker caused a response, created space, drew a marker, or added value. Reverse-time structure remained positive, rank profiles were stepped rather than monotonic, and the negative or mixed downstream analyses prevented interpretation of observed geometry as demonstrated opportunity, coverage, stable defensive identity, or tactical success.

For analysts and researchers, the method is best viewed as a transparent way to
retrieve and describe passages in which nearby defenders moved differently from
their defensive unit after attacker movement, and to contextualize that geometry
with starting ball and unit position. Future work should add semantic and video
validation, broader match and provider replication, and independently motivated
downstream tactical or value consequences. Those steps should extend the
measurement only after their own constructs have been validated.

The immediate contribution is thus not an automated verdict on what an attacker “made” the defence do. It is a reproducible geometric starting point for asking that question more carefully: first describe local defensive reorganization, then test its interpretation and consequences with designs capable of supporting them.

## Supplement plan

- **[SUPPLEMENT] S1 — Protocol and representation:** exact support, smoothing, coordinate, rank, timing, tie, and numerical-boundary definitions.
- **[SUPPLEMENT] S2 — Validation and reproducibility:** frozen protocols, provider-equivalence gates, block-bootstrap/classification mechanics, hash ledgers, and regeneration instructions.
- **[SUPPLEMENT] S3 — Complete primary results:** D1--D10 tables, regional contrasts, reverse-time outputs, horizons, trims, and match-level external results.
- **[SUPPLEMENT] S4 — Synthetic and composition audits:** invariance fixtures, rank-composition audit, and provider/canonical-contract checks.
- **[SUPPLEMENT] S5 — Boundary results:** opportunity redistribution, coverage redistribution, response expectation, and other mixed/negative outcomes.
- **[SUPPLEMENT] S6 — Additional visuals:** governed figure set, sample/exclusion ledgers, and analyst-context figures clearly marked illustrative.

### Preliminary main-paper versus supplement recommendation

**[READY]** Keep Figure 1, Table 1, and one short boundary-results paragraph in
the main paper. Place the Context v1 figure, full D1--D10 and match-level
coefficient tables, robustness details, provider-equivalence checks, synthetic
audits, the rank-composition audit, Opportunity Redistribution detail, Coverage
v1/v2/v3 history, expectation-model detail, and hashes/reproducibility
mechanics in the supplement. This is a manuscript-organization recommendation,
not final venue formatting.

## Drafting decisions before full prose

- **[NEEDS DECISION]** Confirm target venue, word budget, author list, and citation style.
- **[NEEDS DECISION]** Choose which compact external-match table belongs in the main paper versus the supplement.
- **[NEEDS DECISION]** Confirm data-access and code-availability wording with provider terms.
