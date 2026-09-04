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

**[READY]** Metrica Sample Game 1 served as development and Metrica Sample Game 2 as the protected heldout replication for the temporal footprint. Both are sample-match tracking environments with limited match and provider breadth; they are not a population of football matches.

### 3.2 External replication: IDSSE / DFL

**[READY]** Seven complete professional matches from the IDSSE/DFL environment provided external replication in one independent provider environment, not seven providers. Native tracking cadence was 25 Hz. The external temporal sample contained 72,316 anchor observations, 7,300 unique anchors, and 723,160 defender rows.

### 3.3 Availability and provenance

**[READY]** Where provider restrictions prevent redistribution of raw or observation-level tracking, the repository provides source code, compact governed outputs, hash ledgers, and regeneration procedures. Provider-specific loading, coordinate equivalence, and support requirements belong in the supplement.

**[SUPPLEMENT]** Dataset licensing, raw-data access paths, canonical coordinate contract, tracking cadence/support requirements, player metadata, and the full eligibility/exclusion ledgers.

## 4. Methods

### 4.1 Defender-relative representation

**[READY] Plain-language statement.** For each defender, measure position relative to the other defending outfield players, not relative to a fixed pitch point. A shared defensive shift therefore largely cancels, while motion that differs from the unit remains visible.

**[READY] Formal definition.** With ten defending outfield players and focal defender \(d\),

\[
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),\qquad
\mathbf c_{-d}(t)=\frac{1}{9}\sum_{j\ne d}\mathbf x_j(t).
\]

The goalkeeper is excluded. For ten defenders, \(\mathbf x_d-\mathbf c_{-d}=\tfrac{10}{9}(\mathbf x_d-\mathbf c)\), which makes the reference-frame relationship transparent without changing its interpretation.

**[READY] Boundary.** This geometry measures movement within a defensive structure. It does not identify a mark, assignment, tactical responsibility, or why a defender moved.

### 4.2 Temporal spatial defensive-response footprint

**[READY] Timing.** At anchor \(t\), strictly prior defensive context is \([t-4,t-2]\), attacker exposure is \([t-2,t]\), and the primary subsequent defender window is \([t,t+2]\). The exposure \(X_i\) is the attacker's preceding two-second path length. The primary defender outcome is the two-second focal-relative path \(Y_{ik}=P_{\mathrm{rel}}(D_k;t,t+2)\).

**[READY] Rank construction.** At \(t\), the ten supported defending outfield players are ranked by Euclidean distance to the attacker, with ranks fixed for the whole context/exposure/response construction. D1--D3 are the prespecified near region; D4--D7 are middle; D8--D10 remain descriptive. Rank is relative ordering, not a marking label.

**[READY] Frozen primary model.** For rank \(k\), with prior rank-specific focal-relative path \(B_{ik}=P_{\mathrm{rel}}(D_k;t-4,t-2)\) and prior full defending-outfield centroid path \(C_i\), fit the stacked rank-specific model without a global intercept:

\[
Y_{ik}=\sum_{r=1}^{10}I(k=r)
\left(\alpha_r+\beta_rX_i+\gamma_rB_{ik}+\eta_rC_i\right)+\varepsilon_{ik}.
\]

The primary estimand is the near-minus-middle contrast \(N-M\), where \(N=(\beta_1+\beta_2+\beta_3)/3\) and \(M=(\beta_4+\beta_5+\beta_6+\beta_7)/4\).

### 4.3 Validation controls and uncertainty

**[READY]** Use the frozen reverse-time comparison and the paired forward-minus-reverse contrast as the timing qualification. Block bootstrap, trim, and 1/2/4-second horizon checks are validation safeguards, not ways to select a preferred result after inspection.

**[SUPPLEMENT]** Full endpoint, smoothing, support, restart/ball-out, tie-handling, bootstrap, classification, numerical-boundary, and provider-equivalence specifications.

## 5. Validation Design

**[READY]** The temporal footprint was developed in Metrica Game 1, replicated without changing the governed method in heldout Metrica Game 2, then externally replicated across seven IDSSE matches. Protocols and classifications were frozen before their protected outcomes. The provider-equivalence gates tested that the representation and governed pipeline transferred before interpreting external coefficients.

**[READY]** Inference uses grouped time-block resampling specified in the governed protocols. The main paper reports results and robustness; hashes, classification mechanics, and complete rank tables are retained as reproducibility material rather than main-text clutter.

## 6. Results

### 6.1 Primary temporal footprint

**[READY] Metrica.** The pooled Metrica near-minus-middle contrast was `0.05029 m/m` with frozen 97.5% interval `[0.03433, 0.06858]`. Its paired forward-minus-reverse excess was `0.02912` `[0.01410, 0.04526]`.

**[READY] IDSSE external replication.** The pooled IDSSE primary contrast was `0.06115 m/m` `[0.05579, 0.06681]`; the reverse-time contrast was `0.03661` `[0.03224, 0.04111]`; and the paired excess was `0.02455` `[0.01932, 0.02985]`. All seven matches had positive primary contrasts and positive paired excesses. The 1-, 2-, and 4-second horizon signs were positive; the extreme-exposure trim retained 95.35% of the primary magnitude.

**[READY] Effect-size translation.** In the fitted observational IDSSE model, an additional metre of preceding attacker path was associated with about `6.1 cm` more subsequent defender-relative movement for near versus middle ranks. A five-metre exposure difference would correspond to about `0.306 m` as an illustrative linear translation, not as a claim about a typical run or causal effect. The corresponding pooled Metrica estimate is about `5.0 cm` per metre (`0.05029 m/m`) and `0.251 m` for the same illustrative five metres.

### Figure 1. Measurement and replication overview

**[READY — place at the Methods/Results transition, immediately before Section 6.1.]**

> **Figure 1 introduction draft.** Figure 1 links the measurement to the population result. Panel A shows a real heldout passage in which the defensive unit shifts while individual defenders move differently from that unit. Panel B summarizes the cross-match forward-time near-versus-middle association. Panel C shows why the result is qualified by the prospectively frozen paired forward-minus-reverse comparison rather than by an assumption that reverse time contains no structure.

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
