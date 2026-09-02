# Concurrent Defensive Coordination Form v1.0

**Status:** **FROZEN / RESULTS UNOBSERVED**

**Freeze date:** 2026-09-02

**Starting commit:** `1f034a2224dc2a0470e10910719109223c3d4c43`

**First authorized execution:** future Metrica Sample Game 1 development only

No Game 1, Game 2, IDSSE, or Game 3 coordination-form rank result existed or was inspected when this protocol was frozen. The [outcome-blind measurement audit](../concurrent_defensive_coordination_form_measurement_validation.md) superseded a sampling-dependent displacement formula before this freeze.

## 1. Football question and claim boundary

When an attacker moves during a fixed two-second interval, does defender movement *within the moving defensive unit* point along the attacker's locally changing path beyond the nearest defender alone?

This is concurrent geometry. It cannot establish attention, marking, assignment, responsibility, reaction time, causal response, instruction, influence, tactical success, gravity, or value. “Nearest” is a start-time distance rank, not a football role.

## 2. Coordinates and velocity outcomes

For attacker position $\mathbf A(t)$, defender position $\mathbf x_d(t)$, and the centroid $\mathbf c_{-d}(t)$ of the other nine defending outfield players,

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t).
$$

On consecutive filtered native samples, use secant velocities

$$
\mathbf v_{A,k}=\frac{\mathbf A_{k+1}-\mathbf A_k}{\Delta t_k},\qquad
\mathbf v_{r_d,k}=\frac{\mathbf r_{d,k+1}-\mathbf r_{d,k}}{\Delta t_k}.
$$

The sole classification-driving outcome is

$$
\operatorname{AARD}^{\mathrm{vel}}_d=
\frac{\sum_k(\mathbf v_{r_d,k}\cdot\mathbf v_{A,k})\Delta t_k}
{\sum_k\lVert\mathbf v_{A,k}\rVert_2\Delta t_k},
$$

in metres per second. Positive means defender-relative velocity points, on balance, along the attacker's local movement; negative means opposite; near zero can arise from no relative movement, perpendicular movement, cancellation, or weak alignment.

The unsigned secondary is

$$
\operatorname{CROSS}^{\mathrm{vel}}_d=
\frac{\sum_k|v_{r_d,k,x}v_{A,k,y}-v_{r_d,k,y}v_{A,k,x}|\Delta t_k}
{\sum_k\lVert\mathbf v_{A,k}\rVert_2\Delta t_k},
$$

also in metres per second. It has no left/right, inside/outside, goal-side, or ball-side meaning and cannot rescue the primary.

Stationary attacker steps contribute zero numerator and denominator. If total filtered attacker path is at or below $64\epsilon_{64}\sqrt{105^2+68^2}$ metres, aligned/cross outcomes are undefined and the attacker observation is excluded without imputation. All arithmetic is chronological `float64`.

## 3. Preprocessing and continuous support

Use canonical 105 × 68 m coordinates. The primary preprocessing is a fourth-order zero-phase Butterworth low-pass at 1.0 Hz, implemented with SciPy `butter(..., output="sos", fs=native_hz)` and `sosfiltfilt(..., axis=0, padtype="odd")` independently on each player's x/y coordinates.

Construct each player-period's maximal raw/native blocks before filtering. A block contains only finite provider-supported coordinates not invalidated by the frozen tracking-support registry. Adjacent samples belong to one block only when provider frame IDs increase by exactly one and native timestamps increase by the declared native cadence within $10^{-9}$ seconds. Period boundaries, missing/invalid coordinates, frame or timestamp gaps, and registry-invalid support split blocks. No interpolation, bridge, padding with observations, or fragment joining is allowed.

The order is fixed:

1. create maximal player-level native support blocks;
2. filter each block independently;
3. define its scientific interior using the physical margin below;
4. intersect the required attacker's and ten defenders' interiors;
5. determine observation eligibility and only then extract pre-context and concurrent windows;
6. form the leave-one-out centroid from the nine already-filtered teammate trajectories and calculate secant velocities.

The current Metrica registry exposes raw validity, registry invalidity, provider frames, native timestamps, and continuity links, so this construction is compatible without changing its scientific invalidity registry. Future provider adapters must expose the same canonical fields.

### Physical edge rule

Every datum in the required scientific span $[t-2,t+2]$ must lie at least 2.0 seconds inside every required player's native support-block boundary. Equivalently, each required player block must cover at least $[t-4,t+4]$ inclusive. Endpoint comparisons use canonical seconds with tolerance $10^{-9}$:

$$
t-2\ge b_{start}+2-10^{-9},\qquad
t+2\le b_{end}-2+10^{-9}.
$$

At 10 Hz and 25 Hz the two-second margin is respectively 20 and 50 native intervals, both exceeding the implementation's 15-sample SOS padding length. The rule is always expressed in seconds. Blocks must also exceed the filter's implementation minimum of 15 samples; the physical-margin rule is the scientific eligibility rule.

Required sensitivity: repeat all position-derived measurement/model construction at 1.5 Hz on the identical primary observation IDs and primary 1.0 Hz rank membership. Raw/secant results are descriptive measurement robustness. Centred seven-frame results are a historical comparator only and never classify.

## 4. Sampling, timing, and ranks

Inherit Concurrent Attacker–Defensive Geometry v1 unchanged except for preprocessing and the directional outcome:

- fixed pre-context $[t-2,t]$ and concurrent $[t,t+2]$ endpoint convention;
- four-second period-origin anchor cadence, beginning at period origin +2 seconds;
- governed event-established attacking team at $t$;
- inherited open-play, restart/ball-out, possession, cadence, and terminal-support rules;
- every supported attacking outfield player retained and simultaneous attackers grouped;
- goalkeeper excluded by governed metadata;
- exactly ten unique defending outfield players required;
- no interpolation or partial support.

At $t$, rank defenders D1–D10 by primary 1.0 Hz filtered attacker–defender Euclidean distance, with exact ties broken by ascending canonical player ID. Membership is fixed through pre-context, concurrent calculation, bootstrap, and every sensitivity.

## 5. Exact model matrix

Fit one 72-column stacked rank-specific raw-unit OLS model using `numpy.linalg.lstsq(..., rcond=None)` and `float64`. For rank $r$:

$$
Y_{ir}=\alpha_r+\beta_rX_i+\gamma_rB_{ir}+\delta_rC_i+\eta_rO_{ir}+\zeta_rA_i+\kappa_rZ_{ir}+\pi P2_i+\tau HomeAttack_i+\epsilon_{ir}.
$$

$Y$ is concurrent AARD velocity (m/s); $X$ is concurrent attacker path (m); $B$ prior focal-relative path (m); $C$ prior full defending-outfield centroid path (m); $O$ mean prior absolute path of the other nine defenders (m); $A$ prior attacker path (m); $Z$ attacker–defender distance at $t$ (m). `P2` and `HomeAttack` are common indicators. Every trajectory-derived term uses the same cutoff as its outcome. Column order is seven rank-specific terms—intercept, $X,B,C,O,A,Z$—for D1 through D10, then `P2`, then `HomeAttack`.

All covariates remain dimensionally and scientifically compatible. The exposure coefficient has units s$^{-1}$; other continuous slopes likewise map metre predictors to m/s. No standardization, weighting, nonlinear term, player effect, ball term, formation term, model selection, or replacement covariate is allowed.

## 6. Primary estimand and D1 benchmark

The sole classification-driving estimand is

$$
\Delta_{2:3,M}=\frac{\beta_2+\beta_3}{2}-\frac{\beta_4+\beta_5+\beta_6+\beta_7}{4}.
$$

It asks whether aligned internal defensive movement extends beyond D1 into the surrounding local structure.

The mechanistic benchmark

$$
\Delta_{1,M}=\beta_1-\frac{\beta_4+\beta_5+\beta_6+\beta_7}{4}
$$

is reported with its interval but never classifies or upgrades the result. Supportive D1 with unsupported D2–D3 is described only as geometry concentrated at the nearest-defender/dyadic scale; supportive values for both suggest aligned localization beyond D1; neither supportive means the established scalar localization is not principally attacker-path-aligned under this representation.

## 7. Bootstrap and inference

Use 2,000 deterministic 60-second period-origin block-bootstrap replicates, retaining terminal partial blocks. Resample blocks independently within period. Each block retains complete D1–D10 vectors and all simultaneous attackers. Initialize `Generator(PCG64(SeedSequence(20260831).spawn(2)[0]))` once for Game 1 and use identical block draws for primary 1.0 Hz, required 1.5 Hz sensitivity, D1 benchmark, and secondary profiles.

Fit with the exact 72-column `lstsq` design. A replicate is governed-valid only when both required primary-cutoff fits are full rank and finite; otherwise omit that paired replicate from both primary families. At least 1,900 paired-valid replicates are required. Report two-sided empirical 95% percentile intervals using NumPy linear quantiles at 0.025 and 0.975. No multiplicity correction applies because only $\Delta_{2:3,M}$ classifies; D1 and all secondary outcomes are nonclassifying.

## 8. Game 1 classification

Evaluate in order:

1. **GAME 1 COORDINATION FORM DEVELOPMENT INVALID** if support/filter/model/bootstrap execution fails, fewer than 1,900 paired-valid bootstrap replicates exist, or a hard scientific-QC condition fails.
2. **GAME 1 COORDINATION FORM DEVELOPMENT NOT SUPPORTED** if valid and the primary 1.0 Hz point estimate is $\le0$.
3. **GAME 1 COORDINATION FORM DEVELOPMENT COHERENT** if valid, the primary point estimate is $>0$, its 95% interval is strictly above zero, and the 1.5 Hz primary point estimate is $>0$.
4. **GAME 1 COORDINATION FORM DEVELOPMENT MIXED** for every other valid positive primary estimate.

For this decision, “materially unstable under sensitivity” means exactly that the 1.5 Hz primary point estimate is nonpositive. No magnitude-retention or effect-size threshold is introduced. The D1 benchmark and secondary quantities cannot alter status.

## 9. Secondary and descriptive outputs

Nonclassifying outputs are D1–D10 AARD velocity coefficients/intervals; D1 benchmark; D1–D10 CROSS velocity profile; absolute-coordinate aligned velocity comparator; raw/secant measurement robustness; historical centred-seven-frame comparator; and the unchanged endpoint deformation quantity if computed for context. Conventional vector coding is not added in v1.

## 10. Hard QC and execution order

Focused synthetic and future empirical checks require formula/config identity; exact 1.0/1.5 Hz filters; maximal native blocks; no discontinuity crossing; 2.0-second edge support for every required datum/player; one connected span per observation; complete ten-defender vectors; goalkeeper/focal exclusions; fixed primary ranks; finite full-rank designs; paired bootstrap grouping/counts; canonical units; common-translation invariance; deterministic reproduction; and no tactical/outcome labels.

Execution order is fixed: Game 1 development, stop and classify; Game 2 heldout only after closed Game 1 and separate prospective governance; stop and classify replication; IDSSE seven-match external replication only after Game 2 closure and separate provider governance. Metrica Game 3 is outside this phase and remains untouched.

No scientific result may change this protocol. A substantive change requires a versioned pre-outcome amendment.
