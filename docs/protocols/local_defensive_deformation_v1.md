# Local Defensive Deformation Protocol v1.0

**Status:** **FROZEN / RESULTS UNOBSERVED**

**Freeze date:** 2026-09-01

**Starting commit:** `7226a4ac2b59e38b92d2565034e32e2150fdde3a`

**Execution tier:** Tier 1 development on Metrica Sample Game 1 only

## 1. Question and construct

The football concept is **local defensive deformation**: a change in a defender's spatial relationships with the rest of the defensive unit, distinct from rigid movement of the defensive unit as a whole.

The measurement question is:

> Is greater preceding attacker movement associated with greater subsequent internal defensive relational change among nearby defenders than among middle-ranked defenders, beyond recent defensive relational activity and a predeclared temporal control?

Football concept ≠ tracking measurement ≠ tactical mechanism. Pairwise distances and team dispersion geometry are established methods; v1 does not claim their invention. The project literature review records player-to-team-center, interpersonal/relative, stretch, width, length, surface-area, and coordination precedents. This experiment tests a narrow attacker-path association with a focal defender's nine teammate-distance vector.

The measurement does not establish disruption, stretching, dragging, pinning, tracking, covering, handoff, responsibility, attention, reaction, causation, influence, success, space creation, gravity, or value.

## 2. Inherited sample, coordinates, and support

Inherit unchanged from spatial-footprint v1:

- Game 1 attacker anchors and observation IDs;
- attacker path over $[t-2,t]$;
- D1–D10 distance ranking fixed at $t$, including tie handling;
- near D1–D3, middle D4–D7, and descriptive far D8–D10;
- centred seven-frame positions in canonical 105 × 68 m coordinates;
- exact four-second cadence, period and open-play exclusions;
- complete ten-defender outfield set and goalkeeper exclusion;
- simultaneous-attacker grouping, missingness, no interpolation, and full support.

Primary timing is context $[t-4,t-2]$, exposure $[t-2,t]$, and response $[t,t+2]$. The sole response-horizon sensitivity is $[t,t+4]$. No lag or onset search is allowed.

## 3. Frozen geometric outcomes

For focal defender $d$ and each of the other nine outfield defenders $j$, define

$$D_{dj}(s)=\lVert\mathbf x_d(s)-\mathbf x_j(s)\rVert_2.$$

The primary endpoint relational deformation is

$$R_d(t_0,t_1)=\sqrt{\frac{1}{9}\sum_{j\ne d}[D_{dj}(t_1)-D_{dj}(t_0)]^2}.$$

Units are metres. The prior focal baseline is the same quantity over $[t-4,t-2]$.

For all 45 unique defender pairs, define the whole-unit prior baseline

$$G_{prior}=\sqrt{\frac{1}{45}\sum_{j<k}[D_{jk}(t-2)-D_{jk}(t-4)]^2}.$$

Secondary quantities are:

$$P_d=\sum_k\sqrt{\frac{1}{9}\sum_{j\ne d}[D_{dj}(s_{k+1})-D_{dj}(s_k)]^2},$$

$$S_d=\frac{1}{9}\sum_{j\ne d}[D_{dj}(t_1)-D_{dj}(t_0)],$$

and whole-unit endpoint deformation, the RMS endpoint change across all 45 unique distances. $P_d$ is relational path and $S_d$ is signed mean spacing change. Neither receives tactical semantics or classifies v1.

All endpoint values use the exact smoothed positions at the inherited interval endpoints. Path uses every consecutive 25 Hz smoothed position in the closed interval. Float64 is mandatory; no imputation, interpolation, clipping, or deformation-based trimming is allowed.

## 4. Exact primary model

For each rank $r=1,\ldots,10$, fit raw-metre OLS separately:

$$R_{id}=\alpha_r+\beta_rX_i+\gamma_rR_{prior,id}+\delta_rG_{prior,i}+\varepsilon_{id}.$$

The serialized design order is exactly:

1. intercept;
2. `attacker_path_length_m`;
3. `focal_prior_endpoint_rms_m`;
4. `global_prior_endpoint_rms_m`.

There is no standardization, weighting, interaction, nonlinear term, player effect, ball term, formation term, opponent identity, or additional covariate. The model uses `numpy.linalg.lstsq(..., rcond=None)` and requires fitted rank four.

Define near, middle, and descriptive far as means of D1–D3, D4–D7, and D8–D10 coefficient estimates. The sole primary contrast is

$$C_{primary}=\bar\beta_{D1:D3}-\bar\beta_{D4:D7}.$$

Use a two-sided empirical 97.5% percentile interval.

## 5. Frozen temporal control

Inherit the response-form reverse-time construction exactly where compatible:

- control outcome: focal endpoint deformation over $[t-2,t]$;
- control exposure: attacker path over $[t,t+2]$;
- covariates: focal and global endpoint deformation over $[t-4,t-2]$;
- ranks: the same ranks fixed at $t$; and
- common sample: complete D1–D10 rows with all primary/control quantities.

Fit the identical model and define $C_{control}$. On the common sample, refit the primary and compute the paired replicate difference

$$C_{excess}=C_{primary,common}-C_{control}.$$

The control may retain structure. Timing-specific evidence requires a positive paired excess whose interval excludes zero. No other temporal shift is permitted.

## 6. Resampling and robustness

Inherit the response-form Game 1 bootstrap literally: 2,000 replicates, at least 1,900 valid, 60-second period-origin blocks, simultaneous attackers and complete ten-rank vectors kept together, terminal partial blocks retained, and `Generator(PCG64(SeedSequence(20260831).spawn(9)[6]))` freshly initialized for every governed family.

Extreme-exposure robustness removes complete anchors with inherited attacker path above `12.198443079831405` m. It passes when the trimmed contrast retains the primary sign and at least 50% of its absolute magnitude.

The four-second sensitivity recomputes the endpoint RMS outcome over $[t,t+4]$ on inherited complete four-second anchors. It passes when its near-minus-middle point estimate is positive. No one-second sensitivity is defined.

## 7. Construct validity and hard QC

Synthetic tests must verify within `1e-12` m:

- common translation, rigid rotation, and reflection invariance;
- positive deformation under nonunit uniform scaling about the centroid; and
- positive focal deformation when one defender alone is displaced.

Empirical hard QC requires frozen hashes, unique observation IDs, exactly ten unique outfield defenders and D1–D10 once per anchor, goalkeeper exclusion, complete endpoint/path support, correct temporal order, finite raw-metre designs, fitted rank four, at least 1,900 bootstrap replicates, correct paired draws, canonical units, and no Game 2/Game 3 access.

Translation/rotation/reflection failure or another hard scientific failure yields INVALID. A null result never does.

## 8. Frozen development decision

Evaluate in this order:

1. **GAME 1 DEFORMATION DEVELOPMENT INVALID** if execution or hard QC fails.
2. **GAME 1 DEFORMATION DEVELOPMENT NEGATIVE** if valid and the primary near-minus-middle point estimate is nonpositive.
3. **GAME 1 DEFORMATION DEVELOPMENT COHERENT** if valid and all hold:
   - primary contrast is positive and its 97.5% interval is strictly above zero;
   - paired excess is positive and its 97.5% interval is strictly above zero;
   - four-second contrast is positive;
   - trim retains positive sign and at least 50% magnitude; and
   - secondary path does not show a materially opposite result, defined prospectively as a negative path near-minus-middle coefficient contrast whose 97.5% interval is strictly below zero.
4. **GAME 1 DEFORMATION DEVELOPMENT MIXED** for every other valid result.

Game 2 is not authorized by this execution. Coherence does not automatically authorize promotion.

## 9. Falsification map and claims

| Observed pattern | Permitted interpretation |
|---|---|
| Directional response form present; deformation absent | Differential defender movement need not imply internal shape change. |
| Endpoint deformation absent; path deformation present | Transient relational reorganization followed by recovery is possible. |
| Whole-unit deformation present; near-minus-middle absent | Defensive shape changed, but localization near the attacker is unsupported. |
| Primary positive; paired excess absent | Association exists, but timing-specific attacker relation is unsupported. |
| Primary and paired excess positive | Candidate local attacker-associated deformation may justify separate prospective replication. |

Allowed claims remain observational: internal defensive relational change, defender-level relational deformation, change in defender-to-defender spacing relationships, and—only if supported—attacker-associated local relational change. No causal or tactical interpretation is permitted.
