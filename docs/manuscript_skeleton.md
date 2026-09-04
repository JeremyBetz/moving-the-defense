# Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football

> **Internal manuscript spine — not submission prose.** This outline uses only closed governed results. Status labels identify drafting work, not evidence strength: `[READY]`, `[NEEDS WRITING]`, `[NEEDS CITATION]`, `[NEEDS DECISION]`, and `[SUPPLEMENT]`.

## Abstract placeholder

**[NEEDS WRITING]** Start from the football problem: an attacker can move off-ball while the defensive unit shifts, but raw defender displacement alone does not distinguish a shared unit shift from a defender's movement within that unit. State the narrow observational question, the leave-one-out defender-relative representation, and the temporal near-versus-middle result. Report the external IDSSE primary contrast, `0.06115 m/m` (97.5% interval `[0.05579, 0.06681]`), and the paired forward-minus-reverse excess, `0.02455` `[0.01932, 0.02985]`. End with the nonclaim: this is not evidence of marking, causation, tactical success, or attacking value.

## 1. Introduction

### 1.1 Football problem

**[READY]** In football, the importance of an off-ball movement is often described through what the movement appears to make the defence do. An attacker may move away from the ball and a defensive line may slide, a nearby defender may step out while teammates hold, or several players may adjust around a threat. These descriptions focus on the changing defensive picture rather than ball events alone. Yet they make a stronger claim than tracking data directly provide: tracking records where players moved, not attention, responsibility, instruction, or whether a particular attacker caused a particular defender to move.

**[READY]** The measurement problem is especially clear when a defensive unit shifts together. A defender can cover substantial ground simply because the whole unit has moved, while another defender can move differently from that shared shift even when their absolute displacement is smaller. Treating either movement as an individual response conflates collective defensive movement with movement within the defensive structure. Conversely, a purely team-level description can conceal the local deviations that make a passage football-interesting. A measurement intended to study localized defensive reorganization must preserve both: the common movement of the unit and each defender's movement relative to it.

Football tracking research already offers many ways to describe this terrain. Studies of collective geometry quantify centroids, team spread, width, depth, and synchronized movement; coordination research examines how players and groups move together; and attacker-defender work studies proximity, relative motion, pressure, marking-like relationships, and space. Other work models trajectories, predicts future movement, estimates receiver availability or pitch control, and describes off-ball actions. These are important precedents, not gaps to be ignored. They also show why a narrow measurement claim is preferable to immediately translating movement into tactical or value language.

### 1.2 Research question

**[READY]** This paper asks a deliberately limited question: can preceding off-ball attacker movement be associated with localized subsequent defender-relative movement in a reproducible way? The aim is not to infer a marking assignment, a tactical role, or an attacker’s value. Instead, it tests an observable geometric relationship: after an attacker’s preceding path, do nearby defenders move more relative to their defensive unit than middle-distance defenders do, after conditioning on strictly prior movement context? This framing makes the football intuition testable while retaining the distinction between association and explanation.

The core representation places each defender in a moving reference frame defined by the other defending outfield players. Shared translation of the defensive unit is therefore largely removed, while movement that differs from the unit remains visible. The primary temporal estimand compares the association between preceding attacker path and subsequent defender-relative path for prespecified near (D1--D3) and middle (D4--D7) defender-distance ranks. Rank is a transparent local ordering at the anchor time, not a claim that the nearest defender is responsible for the attacker. A reverse-time comparison further asks whether the forward temporal association exceeds structure preserved under the same construction in reverse time.

### 1.3 Contributions and boundaries

**[READY]** The contribution is primarily the combination of a model-light, attacker-centered defender-relative temporal measurement with prospective cross-environment validation and explicit interpretation boundaries. The study develops the measure in one Metrica sample match, replicates it unchanged in a heldout Metrica match, and then externally tests it across seven IDSSE/DFL matches from one independent provider environment. It reports the forward association alongside a paired forward-minus-reverse qualification, grouped block-bootstrap uncertainty, and frozen trimming and horizon checks. It also records negative and mixed downstream tests rather than treating any localized movement association as evidence of space creation, stable defensive style, tactical success, or attacking value.

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

### 4.2 Temporal spatial defensive-response footprint

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

### 4.3 Validation controls and uncertainty

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

### 6.1 Primary temporal footprint

**[READY] Metrica.** Across the prospectively pooled Metrica analysis, the near-minus-middle association was `0.05029 m/m` with a frozen 97.5% bootstrap interval of `[0.03433, 0.06858]`. In the fitted observational model, one additional metre of preceding attacker path was associated with approximately `5.0 cm` more subsequent defender-relative path for the near ranks than for the middle ranks. The paired forward-minus-reverse excess was `0.02912` `[0.01410, 0.04526]`. Reverse-time structure was therefore not absent; the qualifying evidence is that the correctly ordered association was larger under the prospectively paired comparison.

The Metrica result is a within-provider replication across the development and heldout sample matches, not a claim of general professional-football prevalence. Its stepped rank profile also matters: the primary evidence concerns the pre-specified near-versus-middle average, not a smooth assertion that every additional metre of defender distance weakens the association.

The pooled Metrica intervals use the frozen 97.5% convention. They quantify stability under the specified match-period block resampling scheme rather than a population-wide causal effect. The same caution applies to the positive paired excess: it is evidence that the forward contrast was larger than its reverse-time counterpart under the governed comparison, not evidence that all common causes were removed.

**[READY] IDSSE external replication.** In the independent provider environment, the pooled primary near-minus-middle association was `0.06115 m/m` with a 95% bootstrap interval of `[0.05579, 0.06681]`. The reverse-time comparison was also positive, `0.03661` `[0.03224, 0.04111]`, but the paired forward-minus-reverse excess was `0.02455` `[0.01932, 0.02985]`. Primary and paired-excess point estimates were positive in all seven matches. The near-minus-middle sign also remained positive at the frozen 1-, 2-, and 4-second response horizons; the extreme-exposure trim retained 95.35% of the primary magnitude.

The external result therefore reproduces the direction and timing-qualified association in seven matches within one independent provider environment. It does not convert the seven matches into seven provider replications, nor does it establish a causal attacker-to-defender mechanism. The positive reverse-time estimate remains a reminder that shared movement structure persists even under the temporal comparison.

The IDSSE intervals use the transported 95% convention. Keeping both the forward and reverse estimates visible is important: reporting only the primary association would overstate what time ordering contributes. The paired excess is the relevant temporal comparison, while the continuing reverse-time structure is an explicit limitation of a purely observational design.

**[READY] Effect-size translation.** As an illustrative model-based translation, a five-metre difference in preceding attacker path corresponds to roughly `0.31 m` more subsequent near-versus-middle defender-relative path under the pooled IDSSE model. This is a linear translation of the fitted association, not a claim that five metres is a typical run or that attacker movement caused the difference.

In practical terms, the coefficient describes how the fitted difference between nearby and middle defender-relative movement changes with observed preceding attacker path. It does not estimate how far a named defender must move in a particular play, and it should not be read as a threshold for analyst judgment.

### Figure 1. Measurement and replication overview

**[READY — place at the Methods/Results transition, immediately before Section 6.1.]**

> **Figure 1 introduction draft.** Figure 1 links the measurement to the population result. Panel A shows a real heldout passage, selected solely from attacker movement and chronology, in which the defensive unit shifts while individual defenders move differently from that shift. Panel B summarizes the Metrica and IDSSE temporal replication. Panel C shows why the result is qualified by the prospectively frozen paired forward-minus-reverse comparison rather than by an assumption that reverse time contains no structure.

**[READY] Panel A uses Metrica Game 2, period 1, 2336.04 s, Home 1. The unit shifts goalward and laterally; D2 and D3 are less goalward than their leave-one-out unit shifts, while D1 is more goalward. This is a heterogeneous, factual illustration of the representation, not population evidence and not a tactical label. Panels B and C are the governed cross-match temporal replication and forward-versus-reverse summaries.

### 6.2 Supporting concurrent geometry and coordination form

**[READY] Concurrent geometry.** The pooled IDSSE near-minus-middle concurrent contrast was `0.05115` `[0.04595, 0.05642]`; every external match was positive and the trim retained 91.71% of the estimate. This supports localization that is not solely a lagged-design artifact, but it is subordinate to the temporal footprint.

**[READY] Coordination form.** Directional coordination form was coherent in Metrica Game 1 (D2--D3 minus D4--D7: `0.04045 m/s` `[0.02366, 0.05538]`) and mixed in Game 2 (`0.04587 m/s` `[-0.01056, 0.09260]`). All seven IDSSE matches supported the prespecified directional form; their primary estimates ranged from `0.03317` to `0.05165 m/s`. D1 was strongest, but D2 and D3 were individually positive in each external match. These results describe geometric form; they do not infer tracking or a defensive assignment.

### 6.3 What the measurement does not establish

**[READY] Opportunity redistribution.** Game 1 Opportunity Redistribution v1 was negative: \(\beta_D=-0.02407\), 95% bootstrap interval `[-0.09392, 0.04776]`. The three-nearest-defender robustness estimate was negative (`-0.08117` `[-0.15251, -0.00282]`), and the frozen movement trim remained negative (`-0.02852` `[-0.10268, 0.04578]`). This does not support equating local defensive reorganization with improved teammate separation.

**[READY] Coverage redistribution.** Coverage Redistribution v3 was mixed: the primary estimate was `0.09839` `[-0.03840, 0.20500]`, its remote estimate was `-0.01872`, and the direction-null 95th percentile (`0.10194`) was not exceeded. It does not support a coverage claim.

**[READY] Defensive response expectation.** A focal-history addition improved the baseline on all seven matches by a median `0.5350%`, but the match-side specific addition worsened performance by `0.0616%` relative to that model (`0/7` matches; bootstrap interval `[-0.1094%, -0.0167%]`). No stable defensive-style conclusion follows.

**[SUPPLEMENT]** Complete negative/mixed branch reports, rank-profile tables, and the defender-rank composition audit. The audit found a moderate composition limitation: goalward centroid-offset separation had a median standardized difference of `-0.3384` across nine checks, while leave-one-match-out AUC was `0.6267` (all below `0.65`), and activity conditioning removed 99.22% of induced localization in a synthetic rank-only null.

## 7. Football Interpretation / Analyst Use

**[READY]** The measurement can surface passages where defenders moved differently from their collective defensive structure after preceding attacker movement. For an analyst, it is a descriptive way to ask, “which nearby defenders departed from the unit's shift, and by how much?” It does not answer whether that departure was required, correct, caused by the attacker, or good.

**[NEEDS DECISION]** Decide whether the manuscript uses a short analyst-review workflow panel: identify a high association passage, inspect video/context, and retain human interpretation as a separate step. Do not present it as automation or a validated tagging system.

## 8. Limitations

**[READY]** The evidence is observational: shared context may explain both attacker and defender movement, and reverse-time structure remains positive. The paired excess is a timing qualification, not a reaction-time or causal claim.

**[READY]** Proximity rank can encode some unit-relative geometry. The rank composition audit supports use with a moderate limitation rather than proving rank is a pure distance construct. The observed rank profile is stepped and nonmonotonic, not a simple distance-decay law.

**[READY]** Metrica and IDSSE provide limited provider and match breadth; Metrica Game 1 was used repeatedly for development. Provider filtering and support rules differ. Tactical roles and marking assignments are not inferred, and no downstream opportunity, value, or space-creation consequence was established.

**[NEEDS DECISION]** Confirm the final venue-appropriate wording for restricted data access, replication claims, and the scope of the external-provider generalization.

## 9. Conclusion

**[READY]** This study establishes a reproducible observational measurement layer for localized defensive reorganization associated with preceding off-ball attacker movement: focal defender motion relative to the moving defensive unit was more strongly associated with preceding attacker path for near than middle defender ranks, with a positive paired forward-minus-reverse excess in heldout and external validation.

**[READY]** The result is narrower than common football language. It does not show that an attacker caused a response, created space, drew a marker, or added value. Future work should add richer football context, semantic/video validation, repeated-team data, and independently motivated downstream consequences before tactical or value interpretation.

## Supplement plan

- **[SUPPLEMENT] S1 — Protocol and representation:** exact support, smoothing, coordinate, rank, timing, tie, and numerical-boundary definitions.
- **[SUPPLEMENT] S2 — Validation and reproducibility:** frozen protocols, provider-equivalence gates, block-bootstrap/classification mechanics, hash ledgers, and regeneration instructions.
- **[SUPPLEMENT] S3 — Complete primary results:** D1--D10 tables, regional contrasts, reverse-time outputs, horizons, trims, and match-level external results.
- **[SUPPLEMENT] S4 — Synthetic and composition audits:** invariance fixtures, rank-composition audit, and provider/canonical-contract checks.
- **[SUPPLEMENT] S5 — Boundary results:** opportunity redistribution, coverage redistribution, response expectation, and other mixed/negative outcomes.
- **[SUPPLEMENT] S6 — Additional visuals:** governed figure set, sample/exclusion ledgers, and analyst-context figures clearly marked illustrative.

## Drafting decisions before full prose

- **[NEEDS DECISION]** Confirm target venue, word budget, author list, and citation style.
- **[NEEDS CITATION]** Complete the concept-organized related-work citations from the existing bibliography; do not turn the section into a novelty claim.
- **[NEEDS DECISION]** Choose which compact external-match table belongs in the main paper versus the supplement.
- **[NEEDS DECISION]** Confirm data-access and code-availability wording with provider terms.
