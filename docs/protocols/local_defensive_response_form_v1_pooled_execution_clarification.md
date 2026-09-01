# Local Defensive Response Form v1 — Pooled Execution Clarification

**Status:** frozen prospectively before any Game 2 response-form result

**Date:** 2026-09-01

**Starting commit:** `ab082c7c4d6dbb47e4edeb737e06fb1d28d72da7`

**Original protocol SHA-256:** `958c8aa80fe9ea43358c32a42a6be2eea7a41e7f727e23ff137eb3079ee80428`

**Original configuration SHA-256:** `b120f19c13b86f47f5b73311a4509cbd5de5f95fbaa1369f95dc061c998b8053`

**Closed Game 1 result SHA-256:** `fa0cf2fd53ea591d7e1266286bdb2d85603606de7df985d055f4ad92516bfcf6`

## 1. Prospective firewall and purpose

No Game 2 response-form coefficient, interval, secondary geometry, sample, control, classification, or output had been computed or inspected when this clarification was frozen. Game 3 remained untouched. The original protocol already requires Game 1 development, Game 2 replication, pooled execution, and Final Response Form A/B/C, but it did not fully specify the pooled statistical implementation.

This addendum makes that existing stage executable. It changes no scientific hypothesis, exposure, response window, rank region, primary estimand, contrast, temporal control, paired criterion, trim, horizon, axis-retention rule, bootstrap count, Game 1 status, Final A/B/C criterion, or claim boundary. The original protocol and configuration remain byte-identical and authoritative.

## 2. Closed footprint precedent

| Footprint pooled rule | Response-form analogue | Justification |
|---|---|---|
| Same rank-specific model plus one common `I_game2` main effect | Same response-form rank-specific terms plus one common `I_game2` main effect | Preserves the already-frozen common-effect architecture without a post-result interaction |
| Observation-weighted pooled design; no sample balancing | Concatenate eligible Game 1 and Game 2 observations without weights or downsampling | Exact closed precedent; estimates a common conditional observation-level association |
| Independently resample 60 s blocks within every `(game, period)` | Same, retaining complete attacker-anchor rank vectors and simultaneous attackers | Preserves within-match dependence and original match sample sizes |
| No game-by-rank or game-by-exposure interactions | No interactions | Match-specific replication is assessed separately; pooled fit is not a heterogeneity model |
| Pooled percentile intervals from a dedicated seed child | 2,000 replicates from response-form child 8 of `SeedSequence(20260831).spawn(9)` | Already reserved in the frozen response-form protocol |

## 3. Frozen pooled primary model

For pooled primary observations, fit

$$
Z^{\parallel}_{ik}=\sum_{r=1}^{10}I(k=r)
(\alpha_r+\beta^{\parallel}_rX_i+\gamma_rQ^{\parallel}_{ik}+\eta_rC_i)
+\delta I_{game2,i}+\varepsilon_{ik}.
$$

- outcome: focal-relative endpoint displacement along the preceding attacker direction;
- exposure: preceding attacker path over the frozen exposure interval;
- ten separate rank blocks, each with its own intercept, exposure, prior-parallel, and prior-centroid-path coefficient;
- one common additive Game 2 indicator outside the rank blocks;
- no Game × rank, Game × exposure, or other interaction;
- no standardization, regularization, random effect, or weighting; and
- 41 coefficients: 40 rank-specific terms plus the match indicator.

The pooled $\boldsymbol\beta^{\parallel}$ is a common conditional observation-level association across the two samples. It is not an equal-match average or a population-of-matches estimate. Reconstruct near, middle, far, and near-minus-middle exactly as in the original protocol. Far remains descriptive.

## 4. Match weighting

Concatenate all eligible Game 1 and Game 2 observations. Give every defender row unit weight; do not downsample, balance matches, or introduce inverse-size weights. Complete D1–D10 vectors ensure equal rank contribution within each anchor, while the larger match contributes more anchors to the common pooled estimand. Match-specific estimates remain the replication evidence required alongside pooled evidence.

## 5. Pooled bootstrap

Use 2,000 replicates and require at least 1,900 finite estimable replicates. Initialize `Generator(PCG64(SeedSequence(20260831).spawn(9)[8]))` afresh for each governed pooled sample family.

Within each replicate:

1. process games in `G1`, `G2` order and periods in ascending order;
2. construct inherited 60-second period-origin blocks, retaining terminal partial blocks;
3. independently within each `(game, period)`, draw `n_blocks` block indices with replacement from its `n_blocks` blocks;
4. concatenate the sampled blocks without resampling matches as units;
5. carry each copied attacker anchor, all ten ranked defender rows, and every simultaneous attacker together;
6. preserve the number of block draws and therefore the expected sample size within each match-period; realized row counts may vary because terminal/observed blocks differ in size;
7. fit all rank coefficients from the same replicate and reconstruct near-minus-middle from that vector; and
8. use two-sided empirical 97.5% percentile intervals.

Discard only nonfinite or unestimable replicates and apply the frozen 1,900-valid floor. No IID defender, player, row, or frame resampling is allowed.

The pooled one-/two-/four-second and trimmed primary families follow the same construction. The four-second family uses its own complete extended-support inventory and a freshly initialized child-8 generator, matching the original sample-family reinitialization rule.

## 6. Primary/control common sample and paired excess

The classifying paired primary-minus-control calculation uses an exact common sample, formed separately within each match and then concatenated. An anchor enters only when:

- its primary attacker axis is valid;
- its future temporal-control attacker axis is valid;
- primary and temporal-control defender support are complete;
- all D1–D10 rows are present exactly once; and
- the identical observation ID, rank vector, match, period, and block membership can be used for both fits.

Refit both primary and temporal-control pooled models on these same rows in every replicate. Draw one block sample per replicate and use it for both fits. Reconstruct each near-minus-middle from its own ten-coefficient vector, then compute primary minus control within that replicate. This prevents sample differences from producing a nominal paired excess.

The primary pooled contrast and its interval use the complete primary-axis-valid pooled sample. The classifying paired excess uses the common sample only. The frozen extreme-exposure trim remains a robustness check on the complete primary sample; it does not redefine the paired common sample.

## 7. Game 2 closure and final sequence

1. Execute unchanged Game 2 response form.
2. Serialize and hash all governed Game 2 outputs.
3. Independently reproduce Game 2 under Tier 3.
4. Keep Game 2 standalone-descriptive and unclassified.
5. Only after Game 2 closure, compare Game 1 and Game 2.
6. Only after Game 2 closure, execute the pooled design above.
7. Reproduce and hash pooled outputs.
8. Apply only the original Final Response Form A/B/C rules.

## 8. Unchanged final classification

The original criteria remain controlling:

- **FINAL RESPONSE FORM A:** Game 1, Game 2, and pooled executions are valid/reproducible with at least 80% primary-axis retention; primary near-minus-middle intervals strictly exclude zero with the same sign in all three; paired primary-minus-control intervals strictly exclude zero with that same sign in all three; and pooled trim/horizon robustness passes.
- **FINAL RESPONSE FORM B:** every authorized execution is valid/reproducible, but one or more Final A scientific conditions fails.
- **FINAL RESPONSE FORM C:** Game 2 or pooled execution is scientifically invalid under the frozen hard rules.

No radial, orthogonal, cosine, far-region, visual, or post-hoc result can rescue Final A. This clarification defines how pooled quantities are computed, not what qualifies.

## 9. Implementation boundary

The machine-readable addendum is `config/local_defensive_response_form_v1_pooled_execution_clarification.json`. Synthetic-only mechanics are in `src/local_defensive_response_form_pooled_v1.py`. Neither file contains a Game 2 loader or empirical execution entrypoint. Clarification hashes are recorded in the research log and documentation index after final QC.
