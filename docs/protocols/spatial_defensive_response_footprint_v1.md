# Spatial Defensive-Response Footprint Protocol v1.0

**Protocol status:** **FROZEN / RESULTS UNOBSERVED**

**Freeze date:** 2026-09-01

**Design classification:** protocol ready for governed Game 1 implementation

**Scientific boundary:** observational spatial distribution of attacker-path association across defending outfield players. No assignment, intention, causation, tactical success, gravity, or value.

## 1. Purpose

The completed attacker-to-defender bridge established a replicated within-provider association: greater observed attacker movement was associated with greater subsequent local defender-relative movement beyond prespecified strictly prior defensive-motion context. This protocol does not retest whether that bridge exists. It asks where across the defending outfield unit the association is concentrated.

The footprint shape is the result. It may be monotonic, non-monotonic, flat, mixed, or unstable. No defender is assumed to be responsible for the attacker, and no spatial pattern is assumed to be tactically good or attacker-caused.

## 2. Primary scientific question

> **How is the subsequent defensive response spatially distributed across the defensive block relative to the moving attacker?**

Operationally:

> **Does the association between preceding attacker path and subsequent focal-relative defensive movement vary reproducibly across prospectively fixed defender-proximity ranks?**

“Defensive response” remains an observable-behaviour umbrella. The governed outcome is focal-relative movement magnitude, not tactical response, disruption, or intent.

## 3. Prior-art audit and design implications

Tracking research already represents attacker-defender relations through interpersonal distance and relative motion, closest-opponent dyads, pressure zones, arrival-time or influence fields, and learned defensive matchups. Football coordination work treats interpersonal distance and angle as contextual dyadic variables (Laakso et al., 2019), while positional-data reviews catalogue player-opponent distance at dyadic and team scales (Rico-González et al., 2020). Link, Lang, and Seidenschwarz (2016) and Forcher et al. (2024) use distance-conditioned pressure constructions. Fernández and Bornn (2018) use smooth pitch-control/influence surfaces. Franks et al. (2015) infer basketball matchups and estimate spatial defensive effects. Recent football assignment and marking-network work goes further by inferring latent or network relationships (Groom et al., 2026; Calero-Sanz et al., 2026).

The audit did not identify a standard whole-block curve of attacker-path coefficients indexed prospectively by all ten defender distance ranks. That absence is not a universal novelty claim.

Borrowed principles:

- physical distance and proximity ordering are established, interpretable relational coordinates;
- spatial context may be continuous and non-monotonic;
- multiple defenders attached to one moment are dependent observations;
- uncertainty must preserve shared match, anchor, attacker, and defensive-unit context; and
- spatial summaries should remain separate from assignment and outcome-value models.

Explicitly rejected for v1:

- latent marking or matchup inference;
- possession-outcome, shot, xG, pressure-success, or value labels;
- pitch-control, Gaussian influence, arrival-time, graph, HMM, ghosting, or learned response models;
- tactical responsibility attached to nearest rank;
- post-result bins, knots, kernels, smoothing, or monotonic constraints; and
- causal language derived from temporal order or proximity.

## 4. Dataset roles and execution order

- **Metrica Sample Game 1:** development execution and implementation validation.
- **Metrica Sample Game 2:** conditionally held out for the new rank/distance footprint relationship. It is not pristine generally: attacker representation and aggregate bridge results have already been inspected. No defender-rank or distance-conditioned response coefficient has been inspected.
- **Metrica Sample Game 3:** untouched, undesignated, and prohibited.
- **IDSSE:** not part of v1. External/native-frequency bridge transport requires a separate protocol.

No definition, contrast, model, threshold, figure selection, or interpretation may change after Game 1 footprint outcomes are viewed. A valid Game 1 execution proceeds to unchanged Game 2 execution whether its scientific classification is coherent or mixed. Only an invalid execution stops for a versioned pre-result repair.

## 5. Inherited observation sample and timing

Inherit the frozen bridge observation unit, endpoint grid, team-state rule, open-play exclusions, player support, smoothing, coordinates, and identity requirements unchanged.

- Unit: one eligible `(match, period, t, attacker)` anchor with its complete ten-defender vector.
- Cadence: the bridge's nonoverlapping four-second endpoint cadence.
- Strictly prior defensive context: $[t-4,t-2]$.
- Attacker exposure: $[t-2,t]$.
- Primary defender response: $[t,t+2]$.
- Secondary response sensitivities: $[t,t+1]$ and $[t,t+4]$ only.
- Primary exposure: the frozen attacker `path_length_m`, $X_i=P_a(t;2\,\mathrm{s})$.
- Extreme-exposure threshold: inherit exactly **12.198443079831405 m**.

Primary eligibility requires complete raw and centred-seven-frame smoothed support for the attacker and the same ten defending outfield players across $[t-4,t+2]$, exact canonical endpoints, no period crossing, and the frozen restart/ball-out exclusion. Four-second sensitivity support extends to $t+4$ and is reported on its separately eligible sample. No eligibility rule may use rank-specific outcomes or response magnitudes.

## 6. Defender-rank footprint

At the exact anchor $t$, calculate for attacker $a_i$ and each of the ten supported defending outfield players $d$:

$$
q_{id}=\|\mathbf x_d(t)-\mathbf x_{a_i}(t)\|_2.
$$

Order defenders lexicographically by:

1. ascending $q_{id}$ in canonical metres; then
2. ascending canonical `player_key` for an exact floating-point tie.

Assign fixed ranks $D1,\ldots,D10$. `D1` means nearest at $t$ and `D10` farthest at $t$. Rank is calculated once, from the smoothed canonical positions at the exact anchor, and never reassigned during context or response windows. Distance equality for tie-breaking is exact equality of the stored float64 distance; no tolerance or jitter is introduced.

Rank is relative ordering within this complete defensive block. It is not marking, role, responsibility, pressure, or tactical relevance.

## 7. Defender-specific outcomes and context

For every rank $k$, define the primary response:

$$
Y_{ik}=P_{\mathrm{rel}}(D_k;t,t+2),
$$

using the bridge's validated focal-relative path. Each focal defender is referenced to the leave-one-out centroid of the **other nine** defending outfield players, with the goalkeeper excluded. The same definition supplies 1 s and 4 s sensitivity outcomes.

Define the rank-specific strictly earlier baseline:

$$
B_{ik}=P_{\mathrm{rel}}(D_k;t-4,t-2),
$$

and inherit the bridge's full defending-outfield centroid path over $[t-4,t-2]$:

$$
C_i=C_D(t).
$$

No rank average replaces $Y_{ik}$ in the primary footprint. All ten rank-specific values remain available.

## 8. Primary model and estimand

Use one stacked ordinary least-squares model with a complete rank vector per anchor. For each match, fit without a separate global intercept:

$$
Y_{ik}=\sum_{r=1}^{10}I(k=r)
\left(\alpha_r+\beta_rX_i+\gamma_rB_{ik}+\eta_rC_i\right)+\varepsilon_{ik}.
$$

This is algebraically equivalent to ten rank-specific raw-metre regressions while providing one transparent coefficient system and one jointly resampled covariance structure. Rank-specific intercepts and context coefficients avoid imposing equal baselines across ranks. No random effect, shrinkage, regularization, standardization, weighting, or black-box model is used.

The primary footprint is:

$$
\boldsymbol\beta=(\beta_1,\ldots,\beta_{10}),
$$

where $\beta_k$ is the additional subsequent focal-relative path in metres associated with one additional metre of preceding attacker path for defender rank $D_k$, conditional on that defender's strictly prior focal-relative path and the strictly prior defending-unit centroid path.

The pooled model uses the same rank-specific terms and adds one common `I_game2` main effect. It adds no game-by-rank, game-by-exposure, or higher-order interaction.

## 9. Primary new spatial-structure criterion

Define three prespecified rank regions only for joint contrasts:

$$
N=\frac{\beta_1+\beta_2+\beta_3}{3},\qquad
M=\frac{\beta_4+\beta_5+\beta_6+\beta_7}{4},\qquad
F=\frac{\beta_8+\beta_9+\beta_{10}}{3}.
$$

The two **new adjacent-region contrasts** are:

$$
\Delta_{NM}=N-M,\qquad \Delta_{MF}=M-F.
$$

The rank-slope near/far contrast is:

$$
\Delta_{NF}=N-F=\Delta_{NM}+\Delta_{MF}.
$$

$\Delta_{NF}$ is a rank-specific-model consistency description. It is related to, but not algebraically identical to, the completed bridge's aggregate nearest-three/farthest-three coefficient difference because v1 uses defender-specific baseline coefficients. It cannot classify the new footprint. The exact old aggregate specification is reproduced separately in Section 13.1.

The primary footprint gate asks whether at least one adjacent-region contrast, $\Delta_{NM}$ or $\Delta_{MF}$, replicates. For the two predeclared contrasts, use two-sided **97.5% percentile intervals** (1.25th and 98.75th percentiles) so the two intervals form a Bonferroni-controlled 95% family. A contrast is a replicated new spatial feature only when:

1. its Game 1 point estimate and 97.5% interval are strictly on one side of zero;
2. the same contrast's Game 2 point estimate and 97.5% interval are strictly on the same side of zero; and
3. its pooled point estimate and 97.5% interval are strictly on that same side of zero.

This criterion does not require monotonic decline, adjacent-rank significance, or $D1>D2>\cdots>D10$. A U-shape, middle concentration, or other non-monotonic pattern can qualify if one predeclared adjacent-region feature replicates. A flat or nonreplicating footprint is valid mixed evidence.

Rank-specific 95% intervals are descriptive and cannot be searched to rescue classification. No 45-pair rank comparison family is permitted.

## 10. Metric-distance complement

Metric distance is secondary and cannot classify v1. Freeze six absolute-distance bands at the anchor:

- $[0,10)$ m;
- $[10,20)$ m;
- $[20,30)$ m;
- $[30,40)$ m;
- $[40,50)$ m; and
- $[50,\infty)$ m.

The bands are frozen before footprint-outcome inspection from transparent ten-metre physical increments, not from Game 1 footprint distance or response distributions. Boundary values enter the higher band. Each defender retains the band assigned at $t$ throughout all windows.

Fit the rank-model analogue with band-specific intercept, exposure, defender-baseline, and centroid-context terms. Because defender counts per band vary, retain every defender row and keep the complete anchor vector jointly resampled. Report band counts and omit a band coefficient only when its design is not estimable; this does not invalidate the rank-primary analysis.

The complement asks whether attacker-path association differs across absolute physical separation. It imposes no linear decay, spline, kernel, smoothness, or monotonicity. Rank and metric distance are not interchangeable.

## 11. Distance diagnostics

During governed execution, and not before, report for each rank:

- count;
- median anchor distance;
- Q1/Q3 and IQR;
- p10/p90; and
- adjacent-rank distribution overlap, defined as the overlapping coefficient of two empirical histograms using frozen 2 m bins on $[0,80)$ plus one $[80,\infty)$ bin.

Also report the fixed metric-band counts. These geometry-only diagnostics interpret what each rank represents; they do not select ranks, bands, models, or conclusions.

## 12. Dependence and bootstrap

Use a deterministic 60-second match-period block bootstrap inherited from the bridge:

- 2,000 replicates;
- retain nonempty terminal partial blocks;
- sample separately within each match-period, drawing the original number of block labels with replacement;
- keep every simultaneous attacker at an anchor together;
- keep all ten defender-rank rows for every attacker-anchor together;
- keep rank, distance band, exposure, baselines, outcomes, and controls attached to that anchor copy;
- fit all rank coefficients and all contrasts from the same resampled blocks;
- use empirical percentile intervals;
- require at least 1,900 finite estimable replicates for every governed coefficient or contrast; and
- prohibit IID defender-, player-, frame-, or row-level uncertainty.

Reserve new deterministic streams with NumPy `Generator(PCG64)` from `SeedSequence(20260831).spawn(6)`:

- child index 3: Game 1 footprint;
- child index 4: Game 2 footprint;
- child index 5: pooled footprint.

Indices 0–2 remain the closed bridge streams. Reconstruct the applicable child sequence afresh for each separately governed sample family. Within each replicate, process `(game, period)` groups in ascending order and draw block indices with `rng.integers(0,n_blocks,size=n_blocks)`. The primary rank model, metric complement, inherited near/far check, temporal placebo, and trimmed fits use the primary sample's identical resampled blocks. The 4 s sensitivity initializes a fresh generator from the same scope child and its own extended-support block inventory.

For pooled replicates, independently resample blocks within each match-period of each match, concatenate them, and fit the pooled model. Do not resample the two matches as units. With two matches, no match-level asymptotics or population-general p-value claims are allowed.

## 13. Controls

### 13.1 Inherited near-versus-far consistency

Refit the completed bridge's exact aggregate nearest-three and farthest-three specifications on the identical inherited sample and verify their point estimates against the closed bridge outputs within frozen float64 tolerance. Report this aggregate local-minus-nonlocal difference separately from rank-model $\Delta_{NF}$. The aggregate refit is a pipeline consistency check and replication of old evidence, not new footprint evidence.

### 13.2 Temporal-placebo footprint

Retain one spatial-shape temporal control. Using the bridge's reverse-time construction, fit the same ten-rank stacked model and calculate placebo $\Delta_{NM}$ and $\Delta_{MF}$ from the same primary-sample bootstrap draws. Report paired primary-minus-placebo differences for the two region contrasts with 97.5% percentile intervals. This is diagnostic and does not enter A/B/C because the aggregate bridge already passed temporal ordering and v1 does not require every spatial feature to dominate its placebo.

### 13.3 Omitted controls

No rank shuffle/reversal, alternative nearest set, dynamic rank, ball-relative feature, assignment model, or all-rank local/nonlocal duplicate is allowed. Far ranks and $\Delta_{NF}$ already expose the inherited nonlocal comparison. Additional controls would multiply analyses without changing the primary spatial question.

## 14. Horizons and extreme-exposure robustness

The 2 s response is primary. Refit the exact rank model for inherited 1 s and 4 s response windows as sensitivities; no other horizon is permitted.

Repeat the complete primary rank model and the two adjacent-region contrasts after excluding anchors with attacker path greater than **12.198443079831405 m**. All ten defender rows for an excluded anchor are removed together. The full sample remains authoritative.

For a contrast that otherwise qualifies as a replicated feature:

- its pooled trimmed estimate must retain the full-sample sign and at least 50% of the full-sample absolute magnitude; and
- its pooled 1 s and 4 s estimates may not both have the opposite sign from the pooled 2 s estimate.

No rank-specific deletion, winsorization, clipping, robust regression, or new influence threshold is allowed.

## 15. Development and final classifications

Hard validity takes precedence over scientific pattern.

### Game 1

- **GAME 1 FOOTPRINT DEVELOPMENT COHERENT:** every hard-QC and reproduction check passes; all governed intervals have at least 1,900 valid replicates; at least one of $\Delta_{NM}$ or $\Delta_{MF}$ has a Game 1 97.5% interval strictly excluding zero; its Game 1 trimmed estimate keeps the sign and at least 50% of the full magnitude; and its 1 s and 4 s estimates are not both opposite in sign to the 2 s estimate.
- **GAME 1 FOOTPRINT DEVELOPMENT MIXED:** execution, support, hard QC, bootstrap validity, and deterministic reproduction pass, but one or more scientific-pattern conditions above fail. Flat, non-monotonic, weak, unstable, or null footprints belong here.
- **GAME 1 FOOTPRINT DEVELOPMENT INVALID:** any support leakage, rank contradiction, model/bootstrap failure, fewer than 1,900 valid replicates for a governed interval, deterministic mismatch, frozen-artifact change, or other hard scientific/QC failure.

A valid coherent or mixed Game 1 execution proceeds unchanged to Game 2. Invalid execution stops and requires a versioned prospective amendment before any retry.

### Final two-match classification

- **FINAL FOOTPRINT A:** both match executions, pooled execution, hard QC, bootstrap validity, and deterministic reproduction pass; the same adjacent-region contrast satisfies all three replication conditions in Section 9; and that qualifying contrast passes both robustness conditions in Section 14. More than one contrast may qualify, but one is sufficient.
- **FINAL FOOTPRINT B:** both match and pooled executions are valid and reproducible, but no adjacent-region contrast satisfies every Final A replication and robustness condition. This includes flat, weak, nonreplicating, match-heterogeneous, or only inherited near-versus-far structure.
- **FINAL FOOTPRINT C:** either match or pooled analysis is invalid because of implementation, support, leakage, rank, model, bootstrap, reproducibility, frozen-artifact, or other hard scientific/QC failure.

Final A cannot be obtained from $\Delta_{NF}$ alone, any rank-specific confidence interval, the metric-distance complement, or visual shape judgment.

## 16. Hard QC and mathematical invariances

Every governed execution must verify:

1. protocol and inherited bridge source/config hashes match the manifest;
2. Game 3 is not accessed;
3. no prior footprint result artifact existed at freeze;
4. observation IDs are unique before stacking;
5. every eligible anchor has exactly ten rows and ranks `1...10` once each;
6. no defender appears twice within an anchor;
7. the ranked set equals the complete ten defending outfield players and excludes the goalkeeper;
8. anchor distances are finite and nondecreasing by `(distance, player_key)`;
9. exact-distance ties obey ascending canonical `player_key`;
10. rank and band membership use only positions at $t$ and remain fixed;
11. every focal defender is excluded from its own nine-player centroid;
12. attacker and all ten defenders have complete required raw/smoothed support;
13. no interpolation, partial smoother, missing-player centroid, support crossing, or period crossing occurs;
14. $[t-4,t-2]$, $[t-2,t]$, and $[t,t+2]$ have the frozen strict temporal order and no future leakage;
15. restart/open-play rules and cadence equal the bridge;
16. all ten rank rows and simultaneous attackers travel together in every bootstrap draw;
17. terminal partial blocks and period grouping follow the frozen rule;
18. every model matrix and governed estimate is finite and estimable;
19. at least 1,900/2,000 replicates are valid per governed interval;
20. region contrasts exactly equal their coefficient definitions;
21. $\Delta_{NF}=\Delta_{NM}+\Delta_{MF}$ within $10^{-12}$;
22. the separately refitted inherited aggregate near/far models reproduce the closed bridge point construction within $10^{-12}$ on the identical sample, while rank-model $\Delta_{NF}$ remains distinctly labeled;
23. adding a constant translation vector to every player position leaves distance ranks, bands, focal-relative paths, and fitted targets unchanged within $10^{-10}$;
24. rigid rotation or mirror transformation leaves Euclidean ranks, bands, path magnitudes, and coefficients unchanged within $10^{-10}$;
25. canonical player-ID relabeling leaves all non-tied assignments and results unchanged; tied ranks change only by the frozen tie rule;
26. units are metres and seconds in canonical fixed-pitch coordinates;
27. no tactical label or outcome enters construction or classification; and
28. an independent deterministic rerun reproduces every governed scientific file byte-for-byte under the established hash policy.

Synthetic fixtures may test ranking, ties, focal exclusion, grouping, time order, invariances, and contrasts. They may not be parameterized from real footprint outcomes.

## 17. Governed output and figure plan

Freeze the later machine-readable outputs:

- manifest and inherited-artifact hashes;
- eligibility waterfall and exclusions;
- anchor-defender linkage table with fixed rank/distance/band;
- rank distance diagnostics;
- rank coefficient and bootstrap interval tables;
- adjacent-region and inherited near/far contrast tables;
- metric-distance coefficient table;
- temporal-placebo contrast table;
- 1 s, 2 s, 4 s, and trimmed robustness tables;
- classification criteria;
- hard-QC table; and
- deterministic reproduction hashes/report.

Primary figure: defender rank `D1...D10` on the x-axis and $\beta_k$ on the y-axis, showing Game 1, Game 2, and pooled point estimates with 95% intervals and no imposed trend line.

Secondary figures:

1. rank-specific anchor-distance distributions;
2. the six metric-distance-band coefficients with intervals; and
3. the two adjacent-region primary/placebo contrasts.

Figures must use football-readable labels and state “observational association.” No result figure is created during this protocol pass.

## 18. Claim boundary

The strongest permitted claim after **FINAL FOOTPRINT A** is:

> **The association between attacker movement and subsequent defender-relative movement showed a reproducible spatial structure across the defensive block in the two Metrica sample matches under the frozen within-provider protocol.**

Even Final A would not establish causal influence, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoffs, space creation, tactical success/failure, attacker or defender quality, positional/functional play, fatigue, energy efficiency, gravity, off-ball value, general professional-football validity, or cross-provider bridge portability.

Final B supports only that the governed footprint executed validly but spatial structure was mixed, weak, flat, or nonreplicating. Final C supports no scientific footprint interpretation.

## 19. Stopping rule and next-step boundary

Stop after the governed Game 1 result and its required reproduction/reporting. Do not alter this protocol after outcomes. If Game 1 is valid, execute unchanged Game 2 in a separate pass. Do not inspect Game 3.

This phase remains about response **magnitude by spatial location**. Defender heading, radial/tangential response, compression, line movement, cover/handoff geometry, and spatial response vectors belong to a later response-geometry protocol and may not be added here.

No real Game 1, Game 2, pooled, rank-specific, or metric-distance footprint outcome was computed or inspected while freezing v1.0.
