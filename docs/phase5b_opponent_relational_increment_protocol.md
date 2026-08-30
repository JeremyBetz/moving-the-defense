# Phase 5B Opponent-Relational Predictive-Increment Protocol v1.0

> **Status:** **FROZEN, UNEXECUTED.** Version 1.0 was approved and frozen before implementation or outcome inspection. No Phase 5B model, outcome, target correlation, feature importance, residual result, or MAE change has been inspected.

## 1. Research question and inference boundary

Phase 5B asks:

> **Does prospectively specified opponent-relative information improve held-out prediction of future focal-relative path beyond recent focal, collective, ball, and spatial context?**

The unchanged Phase 5A B4 model is the non-opponent baseline. Phase 5B adds an interpretable cumulative ladder:

- **B5 — opponent geometry:** where the selected nearby attackers are at cutoff $c$;
- **B6 — opponent recent motion:** how those fixed attackers moved before $c$; and
- **B7 — defender–opponent relational dynamics:** nonlinear geometric descriptions of how the focal defender and those attackers moved relative to one another before $c$.

An A result would support **opponent-information association at the predictive-information level**, immediately below any football-semantic attacker-association claim. It would not establish that an attacker caused movement, that the defender responded tactically, or that any selected attacker was responsible for the defender.

## 2. Inherited Phase 5A design

Phase 5B does not redesign B0–B4. It inherits exactly from frozen Phase 5A v1.0:

- the five-second accumulated focal-relative-path target;
- cutoff $c$, the raw-support firewall, 25 Hz sampling, and 105 × 68 m defending-oriented coordinates;
- the two-second primary history and frozen one-second sensitivity;
- causal trailing seven-frame history smoothing, centered target smoothing, and no interpolation;
- eligibility, open-play and possession logic, defending-outfield membership, and target/reference construction;
- the seven IDSSE/DFL matches as the only development/evaluation environment;
- nested leave-one-match-out Ridge, training-only constant removal and population-SD scaling, the alpha grid, calibration architecture, metrics, and match-level inference; and
- the existing B4 feature vector and target-independent direction standardization.

Metrica Games 1–2 remain construct history only. Metrica Game 3 remains uninspected and excluded.

## 3. Prospective opponent selection

At the tracking frame exactly equal to cutoff $c$, form the set of **attacking outfield players currently on the pitch with finite standardized coordinates at $c$**. An observation without that exact frame is ineligible; no nearest-frame substitution is allowed. Exclude the attacking goalkeeper using the same provider role metadata and on-pitch bookkeeping used by the IDSSE mapping. Rank these players by Euclidean distance from the focal defender in the standardized 105 × 68 m coordinate system:

$$
d_{fi}(c)=\left\|\mathbf x_i(c)-\mathbf x_f(c)\right\|_2.
$$

Break an exact distance tie by the stable provider player identifier in ascending lexical order. The identifier is retained only for deterministic selection and auditing; it is never a predictor.

- **Primary:** $K=3$, denoted A1, A2, and A3 from nearest to third-nearest at $c$.
- **Representation sensitivity:** $K=1$, denoted A1 and evaluated on the exact primary $K=3$/B7-complete observations.

The selected identities are fixed throughout the pre-cutoff history. They are not dynamically reranked. Selection never uses target-window position, movement, events, reception, future closure/coupling, future focal departure, future ball contact, or the outcome. “Nearest attacker” is a geometric rule, not a mark, assignment, responsibility, or tracked-player inference.

## 4. Notation and coordinate conventions

For focal defender $f$, fixed selected attacker $A_i$, and ball $b$:

- $\mathbf x_p(t)=(x_p(t),y_p(t))$ is the Phase 5A standardized position in metres; $x$ increases from the defending team's own goal toward the opponent goal and $y$ retains standardized pitch-width side from 0 to 68 m;
- raw cutoff positions use the transformed raw frame at $c$;
- $\widetilde{\mathbf x}_p(t)$ is the complete causal trailing seven-frame mean used for history quantities;
- $\mathbf v_p(c)=[\widetilde{\mathbf x}_p(c)-\widetilde{\mathbf x}_p(c-0.04)]/0.04$ in m/s;
- $\Delta\mathbf x_{fi}(c)=\mathbf x_f(c)-\mathbf x_{A_i}(c)$, so positive $x$ means the focal defender is farther toward the opponent goal than the attacker and positive $y$ means the focal defender has larger standardized pitch-width $y$;
- $\widetilde d_{fi}(t)=\|\widetilde{\mathbf x}_{A_i}(t)-\widetilde{\mathbf x}_f(t)\|_2$; and
- $\mathbf u_{f\rightarrow i}(c)=[\widetilde{\mathbf x}_{A_i}(c)-\widetilde{\mathbf x}_f(c)]/\widetilde d_{fi}(c)$.

Define the terminal projection-distance tolerance as exactly $\epsilon_d=10^{-9}$ m. If $\widetilde d_{fi}(c)\leq\epsilon_d$, both projection-derived B7 features for that attacker are incomplete and the entire observation is B7-incomplete. Do not divide by zero, replace the denominator, add an epsilon, or impute a direction. This tolerance is numerical protection in metre coordinates, not a football threshold, and was frozen before outcomes.

## 5. Exact cumulative ladder

### B5 — opponent geometry

B5 is B4 plus the following cutoff-only features for each rank $i\in\{1,2,3\}$:

| Feature | Formula | Units |
|---|---|---:|
| `focal_minus_Ai_x_m` | $x_f(c)-x_{A_i}(c)$ | m |
| `focal_minus_Ai_y_m` | $y_f(c)-y_{A_i}(c)$ | m |
| `focal_Ai_distance_m` | $\|\mathbf x_f(c)-\mathbf x_{A_i}(c)\|_2$ | m |
| `Ai_ball_distance_m` | $\|\mathbf x_{A_i}(c)-\mathbf x_b(c)\|_2$ | m |

Two configuration descriptors are then added across the fixed selected set:

| Feature | Formula | Units |
|---|---|---:|
| `selected_attackers_x_span_m` | $\max_i x_{A_i}(c)-\min_i x_{A_i}(c)$ | m |
| `selected_attackers_y_span_m` | $\max_i y_{A_i}(c)-\min_i y_{A_i}(c)$ | m |

This gives $3\times4+2=14$ B5 additions for $K=3$. Attacker absolute $x/y$ are omitted because B4 focal position plus signed focal–attacker displacement reconstruct them exactly. Minimum/mean/range focal distance are omitted because rank ordering and the three distances already encode them; distance to A3 is the continuous local-density/configuration diagnostic. Thresholded 5/10/15 m counts are not primary features. The radial distances remain alongside signed components because they are nonlinear transforms, not linear aliases in Ridge.

For $K=1$, B5 adds the four A1 features. The two spans are identically zero and are omitted before fitting under the inherited constant-removal rule.

### B6 — opponent recent motion

B6 is B5 plus, for each selected attacker:

| Feature | Formula from causally smoothed history | Units |
|---|---|---:|
| `Ai_recent_absolute_path_m` | $\sum_j\|\widetilde{\mathbf x}_{A_i}(t_{j+1})-\widetilde{\mathbf x}_{A_i}(t_j)\|_2$ | m/history |
| `Ai_terminal_vx_mps` | $[\widetilde x_{A_i}(c)-\widetilde x_{A_i}(c-0.04)]/0.04$ | m/s |
| `Ai_terminal_vy_mps` | $[\widetilde y_{A_i}(c)-\widetilde y_{A_i}(c-0.04)]/0.04$ | m/s |

This gives 9 B6 additions for $K=3$. Mean selected-attacker path and mean terminal velocities are omitted because they are exact linear combinations of the rank-specific features. Acceleration is excluded.

### B7 — defender–opponent relational dynamics

B7 is B6 plus, for each selected attacker:

| Feature | Formula from causally smoothed history | Units/sign |
|---|---|---:|
| `focal_Ai_distance_change_m` | $\widetilde d_{fi}(c)-\widetilde d_{fi}(t_0)$ | m; negative is contraction |
| `focal_Ai_relative_path_m` | $\sum_j\|[\widetilde{\mathbf x}_f-\widetilde{\mathbf x}_{A_i}](t_{j+1})-[\widetilde{\mathbf x}_f-\widetilde{\mathbf x}_{A_i}](t_j)\|_2$ | m/history |
| `focal_approach_toward_Ai_mps` | $\mathbf v_f(c)\cdot\mathbf u_{f\rightarrow i}(c)$ | m/s; positive toward attacker |
| `Ai_approach_toward_focal_mps` | $\mathbf v_{A_i}(c)\cdot[-\mathbf u_{f\rightarrow i}(c)]$ | m/s; positive toward focal |

$t_0$ is the first valid causally smoothed position in the exact frozen history (offset −1.72 s for the two-second primary history; −0.72 s for the one-second sensitivity). This gives 12 B7 additions for $K=3$.

Terminal pairwise closure is intentionally omitted because it is the exact sum of the two approach components (up to the shared finite-difference convention). Relative terminal $v_x/v_y$ are omitted because they are exact linear combinations of B1 focal velocity and B6 attacker velocity. Bearing change is excluded from the primary protocol because wraparound and near-coincident geometry make it unstable and its interpretation depends on an arbitrary unwrapping convention.

Thus the levels retain their intended distinction: B5 locates nearby attackers, B6 describes their independent recent movement, and B7 adds nonlinear pair-history and direction-of-approach geometry.

## 6. Completeness and samples

Selection occurs first at $c$. A missing coordinate anywhere in a selected attacker's required raw history makes that observation incomplete for B6/B7. Do not interpolate, impute, shorten the history, rerank, or replace the selected attacker with A4 after selection.

The primary B4–B7 comparison uses one **B7-complete $K=3$ common sample** within every training/validation/test fold. All B4–B7 target values and features must be finite on that same sample before fitting. This prevents ladder changes from being confounded with sample composition.

The exact Phase 5A B4 specification must be refitted and re-evaluated inside the same outer and inner folds on this Phase 5B common sample. Do not copy Phase 5A's aggregate B4 MAE values when membership differs. No B4 feature, preprocessing, alpha-selection, model, target, or validation rule may change; only the governed evaluation sample changes so B4 versus B5–B7 is a same-observation comparison.

Separately report, by match, attacking team and overall:

1. Phase 4/5A target-eligible observations;
2. B4-complete observations;
3. observations with at least three attacking outfield players finite at $c$;
4. B5-complete observations;
5. selected A1/A2/A3 complete across the two-second history;
6. B6-complete observations;
7. B7-complete/final primary common observations; and
8. each retention percentage relative to B4 and Phase 4 eligibility.

B5- and B6-level support are descriptive computability reports only; no ladder model is fit on their larger level-specific samples. The $K=1$ sensitivity is fit on the **exact same observations as the primary $K=3$/B7-complete common sample**. Its broader computable support may be reported descriptively but is never used for model comparison. Thus $K=3$ versus $K=1$ is a representation comparison rather than a sample-composition comparison.

## 7. Model, validation, and metrics

Reuse Phase 5A's exact Ridge implementation and alpha grid $\{0.01,0.1,1,10,100\}$. Outer validation is seven-fold leave-one-match-out. Within each outer training set, alpha is selected by leave-one-training-match-out using the lowest median inner held-out match MAE; the Phase 5A tie tolerance and larger-alpha rule remain unchanged. Means, population SDs (`ddof=0`), constant masks, and all preprocessing are learned inside each training split only. No IDs are predictors. The NumPy closed-form direct solver and deterministic pseudoinverse fallback remain specified; actual solver use is reported.

Primary metric is held-out MAE by match. Retain Phase 5A secondary metrics, calibration construction, cross-match median/range/IQR, and prediction/error distributions. Report B4→B5, B5→B6, B6→B7, and B4→the lowest-median opponent level. No pooled interval-level result drives inference.

The **best opponent-information model** is the B5–B7 level with lowest median outer-heldout match MAE. Ties within $10^{-6}$ m select the earliest ladder level. This technical winner is reported separately from which adjacent information block, if any, passes materiality.

## 8. Prospective decision rules

An adjacent opponent-information step is **materially useful** only when all hold:

- median per-match MAE reduction is at least 3%;
- at least five of seven matches improve; and
- no more than one match worsens by at least 10%.

Classification precedence is A, then C, then B:

- **A — opponent-relational predictive increment supported:** some B5–B7 level reduces median per-match MAE by at least 5% versus B4, improves at least six of seven matches, and has at most one match worsening by at least 10%. No adjacent-step pass is required for A because predictive information may be distributed across the prospectively separated feature families.
- **C — no practically useful opponent increment:** no B5–B7 level reduces median per-match MAE by at least 2% versus B4 **and** no B5–B7 level improves at least four of seven matches versus B4.
- **B — mixed/partial:** every valid result that is neither A nor C.

Phase 5A required a 10% gain against an unconditional baseline. Phase 5B freezes a smaller 5% A gate because it tests incremental information beyond a much stronger B4 baseline. This is prospective design logic fixed before outcomes, not an outcome-derived concession.

Predeclared interpretations:

- B5-only materiality: local opponent geometry adds information; recent opponent motion/relational dynamics do not materially add under this ladder.
- B6 materiality: selected attackers' recent motion adds information beyond cutoff geometry.
- B7 materiality: pre-cutoff pair dynamics add information beyond independent focal and attacker motion.
- C: the validated focal-relative primitive lacks practically useful opponent-specific predictive increment under this prospective representation.
- heterogeneous B: the increment may be match/context dependent or require a different prospectively justified representation; it is not license for post-hoc selection.

The frozen failure interpretations are:

- **C:** “The validated focal-relative primitive did not demonstrate practically useful opponent-specific predictive information under the tested representation.” This constrains progression toward attacker-response interpretation but does not prove attackers do not influence defenders.
- **B:** report mixed/partial opponent-information increment and identify the exact A and C criteria that failed.
- **A:** later football/tactical interpretation becomes justified as a new validation question; causation remains unsupported.

The A/B/C rule answers whether the complete prospectively specified opponent-information ladder adds predictive information. Adjacent-step materiality separately governs which component family, if any, earns a material interpretation. For example, an A result can coexist with three sub-3% adjacent gains; in that case opponent information is cumulatively useful but no individual feature family is materially dominant under the frozen decomposition.

## 9. Nonlocal-opponent locality control

The secondary control is the **nonlocal-opponent locality control**. At $c$, rank all attacking outfield players by focal distance using the primary deterministic rule and select ranks A4–A6 instead of A1–A3. Fix those identities through history and construct the same-dimensional B5–B7 feature architecture.

Do not require A4–A6 completeness in the primary sample. Construct a separate **locality-control-complete subset** requiring the primary A1–A3 B7 completeness plus complete A4–A6 raw histories and finite A4–A6 B5–B7 features. On that identical subset, compare the local A1–A3 model with the matched-dimensional nonlocal A4–A6 model using the same nested Ridge architecture. Report attrition by match, defending team, and overall.

This preserves physically possible contemporaneous geometry and match/period context while asking whether predictive information associated with the local representation is stronger than information from more distant contemporaneous opponents. It tests locality—not causality, tactical assignment, or arbitrary-opponent irrelevance. A4–A6 may still be relevant. A temporally misaligned control is not used because combining focal and opponent coordinates from different moments creates geometrically impossible pair relationships and requires arbitrary matching choices.

The control is descriptive/supporting and cannot alter the primary A/B/C classification. It can qualify interpretation if nonlocal opponents perform similarly or better.

## 10. Ball-proximity diagnostic

Selected attackers may include the player in possession; excluding that player would distort local geometry and undermine the off-ball-inclusive question. Phase 5B will not select on ball possession or split primary models by possession status.

Because player-level ball-carrier identity is not guaranteed by the tracking/event mapping, the primary diagnostic is geometric: identify the attacking outfield player nearest the ball at $c$, report its ball distance, and report whether its identity is A1, A2, A3, or outside the selected set. Name this the **ball-nearest attacking-player proxy**, not “ball carrier.” If an independently mapped provider event supplies an unambiguous carrier identity at $c$, report overlap separately without using it for selection, eligibility, fitting, or classification. No distance threshold is introduced.

## 11. Residual diagnostics

For the lowest-median B5–B7 level, report held-out residual relationships with:

- B4 prediction magnitude;
- focal recent absolute and focal-relative paths;
- A1/A2/A3 cutoff distances;
- mean A1–A3 recent absolute path, with the three paths averaged per observation;
- A3 distance and selected-set x/y spans as continuous local-configuration diagnostics;
- ball recent path;
- focal depth and lateral distance;
- match, defending team, and focal player groups.

Use the Phase 5A diagnostic architecture: Spearman correlations for continuous quantities and descriptive count/median/range/IQR distributions for groups. These do not enter model choice or A/B/C. Residual means statistical prediction error only—not tactical error, response, responsibility, or attacker effect.

## 12. One-second sensitivity

Rebuild B5–B7 using the frozen one-second history and its causal-smoothed support. Opponent identities are still selected at $c$. Cutoff-only B5 is unchanged; B6/B7 path and distance-change histories use the one-second valid-smoothed window. Use a separate $K=3$ one-second B7-complete common sample and rerun the full nested validation without changing the primary two-second conclusion post hoc. The sensitivity classification is reported under the same rules but cannot replace the primary specification. Within this one-second analysis, any $K=1$ comparison must again use the exact corresponding $K=3$ observations.

## 13. Prohibitions and nonclaims

No Phase 5B predictor or result may be named marking, tracking, pinning, dragging, covering, handoff, attraction, gravity, responsibility, or assignment. Prohibited: future-informed opponent selection; target-window opponent features; tactical labels; player/team/match IDs as predictors; inferred roles beyond provider goalkeeper metadata; nonlinear challengers; feature-selection tuning; threshold optimization; HMMs; clustering; networks; ML model expansion; causal inference; value modeling; Metrica development; and Game 3 access.

Even an A result would not validate attacker causation, tactical defensive response, marking, assignment, responsibility, attention, decision-making, pinning, dragging, tracking, covering, handoffs, relational reconfiguration, tactical correctness, defensive quality, gravity, or off-ball value. Predictive information is not causal influence. Nearest attacker is not marked attacker. Relational dynamics are not tactical responsibility. Statistical predictability is not tactical expectation, and association is not attribution.

## 14. Maximum claim if A

> **Prospectively specified opponent-relative information adds reproducible held-out predictive information about future focal-relative movement beyond the tested non-opponent contextual baseline.**

The evidence-ladder label is **opponent-information association**, not validated tactical attacker association.

## 15. Provenance and novelty boundary

Tracking-based proximity and marking networks, pairwise relative movement, basketball matchup models, soccer ghosting, contextual defensive-velocity prediction, and role-conditioned defensive counterfactuals are established precedents. Phase 5B does not claim novelty for nearest-opponent selection, signed pair geometry, distance, closure, relative motion, or opponent-conditioned prediction. See the [opponent-representation methodology note](opponent_representation_methodology.md), [literature review](literature_review.md), and [bibliography](../references/bibliography.md).

The prospective contribution hypothesis is narrower: a frozen, match-heldout bridge from an established non-opponent baseline to a typed opponent-information increment, with no tactical semantics assigned in advance. Whether that bridge works is unknown until execution.

## 16. Required execution audit if later frozen

Before fitting, an independent mechanical audit must confirm protocol/config equality; selection uses only $t\le c$; rank ties are deterministic; fixed identities persist; no selected attacker is replaced; all formulas and units match; primary/control/sensitivity samples are constructed without outcomes; Phase 4/5A artifacts are unchanged; and no Game 3 data were accessed. Execution must stop on any unresolved ambiguity.

## 17. Frozen v1.0 decisions

The following reviewed decisions are frozen in v1.0:

1. $K=3$ primary and $K=1$ sensitivity.
2. Cutoff-fixed nearest-attacker selection with deterministic tie-breaking.
3. The 14-feature B5 addition, with rank-specific pair geometry plus selected-set x/y spans.
4. The 9-feature B6 addition of rank-specific path and terminal velocity.
5. The 12-feature B7 addition; exclude exact velocity/closure aliases and bearing.
6. One B7-complete $K=3$ common sample across B4–B7; report larger B5/B6 support only; use those same observations for $K=1$.
7. Complete selected histories; no interpolation, imputation, shortening, reranking, or replacement.
8. Exact reuse of the Phase 5A Ridge alpha grid and fitting implementation.
9. Exact reuse of the adjacent 3% / five-of-seven / at-most-one-10%-worse rule.
10. The A/B/C thresholds and A→C→B precedence; A does not require an adjacent-step pass.
11. Same-frame A4–A6 nonlocal-opponent locality control on a separate A1–A6-complete subset; it cannot affect A/B/C.
12. Ball-nearest attacking-player overlap diagnostic; no primary ball-carrier split.
13. Keep all three selected attackers rank-specific; add only x/y configuration spans.
14. Exclude bearing/angular change from primary features as too convention-sensitive.

Any substantive change requires a versioned, documented, pre-outcome protocol amendment. Implementation must begin with an outcome-blind mechanical audit and stop on any unresolved ambiguity.
