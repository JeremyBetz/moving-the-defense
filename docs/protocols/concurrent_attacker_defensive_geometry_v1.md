# Concurrent Attacker–Defensive Geometry v1.0

**Status:** **FROZEN / RESULTS UNOBSERVED**

**Freeze date:** 2026-09-01

**Starting commit:** `619bcbb4af482e345d720ce7e0744a0623b3bded`
**Execution:** future Tier 1 development on Metrica Sample Game 1 only

No concurrent-geometry match result existed or was inspected when this protocol was frozen. Game 2 is reserved for a separately governed held-out step; Game 3 and IDSSE are untouched by this design.

## 1. Motivation and questions

Closed evidence supports spatially localized attacker–defender association more consistently than a clean attacker-before/defender-after decomposition or universally valid discrete attacker-episode boundary. Focal-relative movement is reproducible; the footprint localized a preceding-path/subsequent-path association; response-form and deformation timing-specific controls only partially replicated; and Attacker Movement Episode v2 closed mixed because its selected boundary audit failed on Game 2 and long merging persisted.

The primary question is:

> During a fixed observation interval, is greater attacker movement associated with greater concurrent defender-relative movement among near defender ranks than among middle defender ranks, beyond pre-interval movement context?

The sole secondary question is whether the same spatial localization appears for concurrent internal defensive deformation.

**Concurrent local defensive geometric change** means defender movement relative to the defensive unit, or defender-to-defender relational change, measured during the same fixed interval as attacker movement and localized using attacker–defender distance at a predeclared reference time. It is geometry—not reaction, latency, causation, assignment, attention, intent, influence, or tactical meaning.

## 2. Fixed time and sampling architecture

Use centred seven-frame positions in canonical 105 × 68 m coordinates. Let $t$ be a period-grid anchor:

- pre-context: $[t-2,t)$ conceptually;
- concurrent interval: $[t,t+2)$ conceptually;
- required tracking support: $[t-2,t+2]$.

For exact discrete calculation, positions at $t-2$, $t$, and $t+2$ are retained. Pre-context path contains increments ending in $(t-2,t]$; concurrent path contains increments ending in $(t,t+2]$. The two path sums share only the position at $t$, never an increment. Endpoint quantities use the stated endpoints. This convention preserves exact existing 25 Hz endpoint/path implementations while maintaining strict pre-context information.

Anchors occur every four seconds from each period origin. Thus required four-second spans do not overlap in their increments. Inherit the bridge's governed period, open-play, restart/ball-out, canonical-time, cadence, and terminal-support rules. The attacking team is the governed event-established possession team at $t$; possession need not continue after $t$. Retain every supported attacking outfield player, with simultaneous attackers kept together. Require complete, finite support for the attacker and exactly ten unique defending outfield players throughout the full span. Exclude goalkeepers by governed metadata. Do not interpolate or partially retain support.

The two-second duration is frozen because it is the established footprint/response-form/deformation timescale, is football-readable as a short local interaction, supports strictly prior context, and avoids dependence on unresolved episode boundaries. No duration sensitivity is defined in v1.

## 3. Exposure and outcomes

Primary continuous exposure is attacker path over $[t,t+2]$:

$$X_i=\sum_k\|\mathbf x_a(s_{k+1})-\mathbf x_a(s_k)\|_2.$$

It imposes no speed or tactical threshold. Net signed displacement, peak/mean speed, and straightness may be serialized descriptively, but cannot classify v1. Path magnitude does not encode football meaning.

For focal defender $d$, let

$$\mathbf r_d(s)=\mathbf x_d(s)-\mathbf c_{-d}(s),$$

where $\mathbf c_{-d}$ is the centroid of the other nine defending outfield players. The unchanged primary outcome is concurrent focal-relative path:

$$P_d=\sum_k\|\mathbf r_d(s_{k+1})-\mathbf r_d(s_k)\|_2.$$

The focal defender is excluded from its reference; the goalkeeper is excluded from the defensive set.

The secondary outcome is the closed endpoint deformation construct:

$$R_d(t,t+2)=\sqrt{\frac{1}{9}\sum_{j\ne d}[D_{dj}(t+2)-D_{dj}(t)]^2},$$

where $D_{dj}(s)=\|\mathbf x_d(s)-\mathbf x_j(s)\|_2$. It is supportive or non-supportive only and never co-primary.

## 4. Spatial localization

At $t$, rank the ten defending outfield players D1–D10 by attacker–defender Euclidean distance in metres, breaking exact ties by ascending canonical player ID. Freeze membership for pre-context and concurrent calculations; never rerank using future movement.

- near: D1–D3;
- middle: D4–D7;
- far: D8–D10, descriptive only.

Distance alone does not imply marking, responsibility, relevance, openness, or assignment.

## 5. Primary and secondary models

Fit one stacked rank-specific raw-metre OLS model using `numpy.linalg.lstsq(..., rcond=None)` and float64. For rank $r$:

$$Y_{ir}=\alpha_r+\beta_rX_i+\gamma_rB_{ir}+\delta_rC_i+\eta_rO_{ir}+\zeta_rA_i+\kappa_rZ_{ir}+\pi P2_i+\tau HomeAttack_i+\epsilon_{ir}.$$

Here $Y$ is focal-relative path, $B$ prior focal-relative path, $C$ prior defensive-centroid path, $O$ mean prior absolute path of the other nine defenders, $A$ prior attacker path, and $Z$ attacker–defender distance at $t$. `P2` and `HomeAttack` are common fixed design indicators. Rank-specific columns are serialized in exactly the order in the configuration, followed by common indicators. No standardization, weighting, nonlinear term, player effect, ball term, formation term, or model selection is allowed.

Prior focal absolute path was evaluated prospectively and omitted because focal-relative path plus collective and other-defender activity already represent the intended defensive context; including it would add a highly overlapping activity measure. Ball context was also omitted because it is not required to define either construct and would add support/interpretive burden. These omissions may not be revisited after results.

The sole primary estimand is

$$\Delta_{NM}=\frac{1}{3}\sum_{r=1}^{3}\beta_r-\frac{1}{4}\sum_{r=4}^{7}\beta_r.$$

Use a two-sided empirical 95% percentile interval. A positive overall attacker-path slope is insufficient: spatial specificity requires positive near-minus-middle association. D1–D10 and far summaries are descriptive.

Fit the secondary deformation outcome with the identical model architecture and report its $\Delta_{NM}$ as supportive only if positive with its descriptive 95% interval strictly above zero; otherwise report non-supportive (or opposite if strictly below zero). It cannot alter the primary status.

## 6. Common activity and temporal-control decision

Concurrent attacker and defender movement can covary because everyone is moving. V1 addresses that threat through strictly prior attacker, focal-relative, defensive-centroid, and other-defender activity; anchor distance; fixed design indicators; and the required near-minus-middle contrast.

No shifted temporal control is defined. A shift would reintroduce an arbitrary timing relation into an intentionally concurrent estimand and would not test reaction. Autocorrelation remains a limitation. A future control cannot be added after seeing v1 results.

## 7. Uncertainty and robustness

Use 2,000 deterministic 60-second period-origin block bootstrap replicates, retaining terminal partial blocks and requiring at least 1,900 valid replicates. Complete D1–D10 vectors and all simultaneous attackers remain grouped. Initialize `Generator(PCG64(SeedSequence(20260831).spawn(2)[0]))` freshly for each governed family; child 1 is reserved for a future Game 2 addendum. Reuse identical draws for primary, secondary, and trim families.

Extreme-exposure robustness removes complete anchors whose concurrent attacker path exceeds the already-governed `12.198443079831405` m threshold. It passes if the trimmed primary contrast remains positive and retains at least 50% of the full absolute magnitude. No new percentile, horizon, threshold, model, or sensitivity is allowed.

## 8. Descriptive directional geometry

If attacker net displacement over the concurrent interval exceeds $10^{-9}$ m, serialize the focal-relative endpoint displacement parallel and orthogonal to that attacker axis, plus radial displacement toward the attacker at $t$, using the closed response-form sign conventions. Undefined axes remain null. These quantities are descriptive only and cannot classify v1.

## 9. Construct validity and hard QC

Synthetic and empirical checks require:

- common-translation, rigid-rotation, and reflection invariance within $10^{-12}$ m;
- no focal leakage into the leave-one-out centroid;
- exactly ten unique outfield defenders and D1–D10 once per anchor;
- goalkeeper exclusion and canonical-ID tie handling;
- fixed rank membership with no future reranking;
- complete support, correct endpoint allocation, no interpolation, and no period/restart crossing;
- unique observation IDs and grouped simultaneous attackers;
- finite full-rank raw-metre designs and estimable coefficients;
- at least 1,900 valid bootstrap replicates with correct block grouping;
- unchanged closed-artifact and protocol/configuration hashes;
- deterministic reproduction before any promotion; and
- no tactical/outcome labels, Game 2, Game 3, IDSSE, or opportunity outcome.

A hard scientific-validity failure yields INVALID. A null result never does.

## 10. Frozen Game 1 decision

Evaluate in order:

1. **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT INVALID** if execution or hard QC fails.
2. **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT NEGATIVE** if valid and primary $\Delta_{NM}\le0$.
3. **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT** if valid and all hold:
   - primary $\Delta_{NM}>0$;
   - its 95% interval is strictly above zero; and
   - trimming preserves positive sign and at least 50% of magnitude.
4. **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT MIXED** for every other valid positive result.

Secondary deformation is supportive/non-supportive only. Game 2 receives no standalone status in this protocol and may not be opened until Game 1 closes and a separate prospective held-out addendum is frozen. Game 3 remains reserved. No pooled final analysis or classification exists in v1.

## 11. Claim boundary and future link

If coherent on Game 1, the strongest development claim is: **within fixed two-second intervals, greater attacker path is associated with a stronger concurrent focal-relative path coefficient among near than middle defender ranks after the specified pre-interval movement context.** It remains a development-sample observational association.

V1 cannot establish reaction time, attacker-first ordering, latency, causation, influence, intent, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoff, space creation, tactical success, player quality, gravity, or attacking value.

Only after this defensive-side relationship survives separately governed validation may another protocol ask whether attacking opportunity is redistributed elsewhere. No opportunity metric is selected here.

## 12. Provenance and novelty

Relative-phase, vector-coding, centroid/spread, team-shape, expected-defender-position, and fixed-window tracking analyses are established precedent. V1 transfers their geometric and coordination logic but does not claim invention of player movement, dyads, centroids, pairwise distance, or fixed windows. The project-specific contribution is the prospectively governed combination of continuous concurrent attacker path, validated leave-one-out defender-relative path, closed deformation geometry, start-fixed D1–D10 localization, strictly prior activity context, negative geometric controls, and development/held-out separation.

The conservative prospective novelty claim is therefore **potentially meaningful validation/application novelty in an interpretable combined framework**, not a universal first. See the [provenance note](../concurrent_attacker_defensive_geometry_v1_provenance.md).
