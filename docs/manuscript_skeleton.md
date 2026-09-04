# Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football

> **Internal manuscript spine — not submission prose.** This outline uses only closed governed results. Status labels identify drafting work, not evidence strength: `[READY]`, `[NEEDS WRITING]`, `[NEEDS CITATION]`, `[NEEDS DECISION]`, and `[SUPPLEMENT]`.

## Abstract placeholder

**[NEEDS WRITING]** Start from the football problem: an attacker can move off-ball while the defensive unit shifts, but raw defender displacement alone does not distinguish a shared unit shift from a defender's movement within that unit. State the narrow observational question, the leave-one-out defender-relative representation, and the temporal near-versus-middle result. Report the external IDSSE primary contrast, `0.06115 m/m` (97.5% interval `[0.05579, 0.06681]`), and the paired forward-minus-reverse excess, `0.02455` `[0.01932, 0.02985]`. End with the nonclaim: this is not evidence of marking, causation, tactical success, or attacking value.

## 1. Introduction

### 1.1 Football problem

**[READY]** Football analysts often describe an off-ball attacker as drawing a defender, changing a defensive shape, or forcing a defensive shift. Tracking data record positions and movement, however, rather than the tactical meaning or cause of those movements.

**[READY]** A useful measurement must separate two things that can occur in the same passage: a shared defensive-unit shift and movement by an individual defender relative to that shifting unit. If a back line slides together, raw movement alone is not evidence that any one defender reorganized locally.

### 1.2 Research question

**[READY]** Can preceding off-ball attacker movement be associated with localized subsequent defender-relative movement, without inferred marking assignments, tactical-role labels, or an attacking-value model?

### 1.3 Contributions and boundaries

**[READY]** The contribution is a transparent, model-light measurement design:

- defender movement relative to the other nine defending outfield players;
- a pre-specified temporal near-versus-middle defender-rank estimand;
- frozen development, heldout, and external validation steps;
- a reverse-time comparison and paired forward-minus-reverse qualification;
- explicit negative results that prevent interpreting geometry as space creation, stable style, or value.

**[NEEDS CITATION]** Position this as a bounded measurement and validation contribution, not as the invention of player-versus-team geometry or of defender response to attacker movement. Cite the closest collective-geometry, synchronization, marking-geometry, and off-ball tracking precedents.

## 2. Related Work

### 2.1 Collective team geometry

**[NEEDS CITATION]** Review centroids, width/depth, surface area, player-to-team center distance, and synchrony as established football tracking approaches. Explain that the present representation is a leave-one-out Cartesian reference frame and accumulated path, rather than a claim that collective-relative geometry is new. Candidate sources are the existing Sampaio and Maçãs, Duarte--Araújo--Correia, Carrilho, and collective-geometry review references in the [literature review](literature_review.md).

### 2.2 Attacker-defender coordination and marking geometry

**[NEEDS CITATION]** Review dyadic coordination, proximity/marking networks, and assignment approaches. Distinguish them from this paper: proximity rank is not marking, responsibility, or a learned assignment. Cite the existing Groom and Calero-Sanz conceptual neighbors where appropriate.

### 2.3 Space, pressure, and availability

**[NEEDS CITATION]** Situate pitch control, pressure, receiver availability, and space representations as related but distinct: this paper does not measure controlled space, access, pressure success, or possession value.

### 2.4 Off-ball movement and trajectory modelling

**[NEEDS CITATION]** Review tracking-based off-ball movement, trajectory modelling, and run/effort segmentation. Clarify that the exposure here is preceding observed attacker path, not a tactical run label.

### 2.5 Closest analogues outside football

**[NEEDS CITATION]** Mention basketball matchup or gravity architectures only as downstream conceptual analogues. They do not validate attacker attribution or value here.

**[READY] Narrow gap.** The paper asks whether a simple attacker-centered, defender-relative temporal measurement can reproduce across protected football tracking data without first inferring assignments or value.

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
