# Frozen Protocol: Attacking Directional Segmentation v1.0

**Frozen:** 2026-08-31, before any directional-segmentation execution  
**Development data:** Metrica Sample Game 1 only  
**Held out:** Metrica Sample Game 2 remains unopened for attacker segmentation; Sample Game 3 remains untouched  
**Execution status:** not executed

## 1. Question and construct

This protocol asks whether an attacker-only partition into **directional movement segments** can reduce the fragmentation/merging trade-off left by scalar speed valleys.

A directional movement segment is a finite interval whose smoothed two-dimensional velocity is adequately represented by one constant local mean under the penalized objective below. “Constant” describes the fitted local representation, not literally constant player speed or a tactical action.

The only permitted inputs are each supported outfield player's own raw x/y tracking coordinates, provider frame/time/period identity, roster/team identity, and governed support/continuity metadata. Every included outfield trace is treated prospectively as a possible attacker trace without using possession. Ball, teammates, opponents, events, defensive outcomes, possession outcomes, and visual football judgments do not enter segmentation or selection.

## 2. Canonical input and time

Use canonical tracking contract v1.0.0 in fixed 105 × 68 m coordinates and include every roster player row with `is_goalkeeper == false` when supported. For each player-period, sort by `time_match_s`, preserve provider frame IDs, and require strictly consecutive 0.04 s Game 1 observations inside each eligible block. Do not normalize by attacking direction.

Let raw supported position be

$$
\mathbf p_i=(x_i,y_i)\quad\text{metres}.
$$

Apply the historical centred seven-frame arithmetic mean separately to x and y:

$$
\widetilde{\mathbf p}_i=\frac{1}{7}\sum_{j=i-3}^{i+3}\mathbf p_j.
$$

It exists only when all seven raw rows are valid and belong to the same eligible block. No partial window, interpolation, padding, extrapolation, clipping, or winsorization is allowed.

Velocity is the consecutive smoothed-position difference:

$$
\mathbf X_i=\mathbf v_i=
\frac{\widetilde{\mathbf p}_i-\widetilde{\mathbf p}_{i-1}}
{t_i-t_{i-1}}=[v_{x,i},v_{y,i}]
\quad\text{m/s}.
$$

Both smoothed positions must be supported inside the same block and $t_i-t_{i-1}=0.04$ s. The velocity timestamp and provider frame ID are those of the later position, $i$.

## 3. Support pipeline

Eligibility is evaluated before smoothing in this order:

> raw row support → trajectory validity → smoothing support → velocity support → eligible change-point block → segmentation

### Raw support

Require one finite x/y observation, canonical `support_state == observed`, expected provider frame succession, strictly increasing time, and exactly 0.04 s between Game 1 frames. A missing/invalid row splits the block on both sides.

### Trajectory validity

The earlier tracking-support audit did not validate a universal speed cutoff and this protocol does not invent one. It freezes a conservative Game 1 invalidity registry from the already documented audit:

| Team/player | Period | Invalid support |
|---|---:|---|
| Home 10 | 1 | provider frames 2911–2945 inclusive |
| Home 3 | 2 | entire player-period; larger unresolved discontinuity documented at frame 71279 |
| Away 22 | 2 | entire player-period; larger unresolved discontinuity documented at frame 71287 |

Home 10 has a diagnosed duplicated-identity/restoration passage. Home 3 and Away 22 are excluded conservatively because the prior audit documented larger unresolved discontinuities but did not freeze trustworthy local boundaries. These exclusions are Game 1 development support decisions, not a provider-general tracking-validity rule. They must be reported separately and must not alter historical analyses.

No segment may use a raw frame in the registry. Smoothing support that touches an invalid raw frame is invalid. There is no post-derivation speed cap.

### Blocks

A block is a maximal run of valid consecutive velocity observations within one player and period. Period boundaries, raw/support gaps, registry exclusions, smoothing loss, velocity loss, or a non-0.04 s interval split blocks. Event stoppages do not split blocks because they are contextual and are outside this attacker-trajectory construct.

Blocks shorter than 20 velocity observations (0.80 s of velocity bins) are retained in a support ledger but not segmented: two legal 0.40 s segments could not exist. A block with 10–19 observations is emitted as one untested short regime; a block with fewer than 10 is emitted as unsupported for directional-regime estimation. Neither enters pass/fail episode rates.

## 4. Physical scaling and noise scale

Keep $v_x$ and $v_y$ in physical m/s. Do not centre or standardize axes independently. Their Euclidean geometry and rotation symmetry must remain intact.

Use one common scalar velocity-noise estimate for every Game 1 block. From all consecutive supported velocity pairs in the eligible Game 1 development scope, compute

$$
\widehat\sigma_v=
\frac{\operatorname{median}\left(\|\mathbf v_i-\mathbf v_{i-1}\|_2\right)}
{2\sqrt{\log 2}}.
$$

Under independent isotropic Gaussian velocity error, a two-frame velocity difference has a Rayleigh radial median of $2\sigma_v\sqrt{\log 2}$. Here the estimate is a deterministic common scale, not a claim that smoothed football velocity is independent Gaussian noise. Genuine changes may inflate it conservatively. If the estimate is nonfinite or nonpositive, execution fails QC and no fallback scale is permitted.

Dividing cost by this one scalar preserves rotations, angles, and relative x/y weighting. Report $\widehat\sigma_v$ in m/s and its source-frame count.

## 5. Segment model, cost, and objective

For an eligible block $\mathbf X_{1:n}$ and a candidate segment containing indices $a+1,\ldots,b$, fit the constant two-dimensional mean

$$
\overline{\mathbf X}_{a+1:b}=
\frac{1}{b-a}\sum_{i=a+1}^{b}\mathbf X_i.
$$

The segment cost is normalized squared Euclidean error:

$$
\mathcal C(a,b)=
\frac{1}{\widehat\sigma_v^2}
\sum_{i=a+1}^{b}
\left\|\mathbf X_i-\overline{\mathbf X}_{a+1:b}\right\|_2^2.
$$

For change points $0=\tau_0<\tau_1<\cdots<\tau_m<\tau_{m+1}=n$, minimize

$$
\sum_{j=0}^{m}\mathcal C(\tau_j,\tau_{j+1})
+m\,\beta_n,
\qquad
\beta_n=3\log n.
$$

The three BIC parameters added by a change are two segment-mean components plus one unknown change location. The common scale is estimated once, not per segment. This is the single primary penalty. There is no development ladder and no visual or empirical penalty selection.

The penalty is an information-criterion approximation derived from Gaussian mean-change precedent (Yao, 1988), extended transparently to two mean components. Its independence/common-variance assumptions are imperfect after rolling smoothing; that limitation is tested rather than repaired.

## 6. Algorithm and deterministic conventions

Use exact PELT (Killick, Fearnhead, and Eckley, 2012) with:

- squared-error cost exactly as above;
- candidate `jump = 1` (every legal velocity boundary);
- minimum segment length $L_{\min}=10$ Game 1 velocity observations;
- Float64 inputs and accumulation;
- natural logarithm;
- no pruning approximation that changes the optimum.

If multiple partitions have exactly equal Float64 objective values, choose the one with fewer change points, then the lexicographically earliest change-point vector. The implementation must include a small dynamic-programming oracle on deterministic fixtures to verify that PELT returns the governed optimum and tie rule.

## 7. Minimum duration

The minimum is **0.40 s of velocity bins**, converted as

$$
L_{\min}(f)=\lceil0.40f\rceil.
$$

Thus it is 10 observations at 25 Hz and 4 at 10 Hz. This is a development convention, not a football definition. It is longer than the 0.28 s smoothing support, supplies several observations for a two-component mean at both frequencies, and still allows shorter units than the historical 1.0 s rule. Changing 0.40 s requires a new protocol version; no duration ladder is allowed.

Segment time bounds use velocity-bin support: start is the earlier position time underlying the first velocity; end is the later position time of the last velocity. Adjacent segments share a boundary time but not a velocity observation.

## 8. Stationary and low-motion regimes

PELT partitions all eligible velocity support. After segmentation, tag a fitted regime as `low_motion_regime` when

$$
\left\|\overline{\mathbf X}\right\|_2<0.50\ \text{m/s},
$$

and otherwise as `directional_movement_segment`. The 0.50 m/s boundary is a frozen development convention used only to keep holding/near-stationary intervals from being called movement. It does not affect change points, penalty choice, A/B/C classification, or lower-speed reporting. Boundary-sensitive cases within the canonical numerical tolerance are flagged. Low-motion regimes remain in the partition and outputs; no occupancy, pinning, or tactical interpretation is made.

## 9. Deterministic fixtures

Before Game 1 segmentation, run a source-controlled fixture suite at 25 Hz and 10 Hz through the full smoothing/velocity/segmentation path. Fixtures use six seconds of integrated piecewise velocity, start at (0,0), and add deterministic positional perturbation

$$
\boldsymbol\epsilon(t)=0.005[\sin(2\pi\,1.7t),\cos(2\pi\,1.3t)]\ \text{m}.
$$

The suite and required primary outcomes are:

| Fixture | Velocity before positional perturbation | Required result |
|---|---|---|
| Constant | (3,0) m/s | no change point |
| Low speed | (0.8,0.3) m/s | no change point |
| Brief slowdown | (3,0), then (1,0) only from 2.9–3.1 s, then (3,0) | no change point; the excursion is shorter than two legal segments |
| Sustained speed change | (2,0) before 3 s; (4,0) after | exactly one point within one native frame of 3 s |
| Sharp turn | (3,0) before 3 s; (0,3) after | exactly one point within one native frame of 3 s |
| Stop/restart | (3,0) to 2 s; (0,0) to 3 s; (3,0) thereafter | exactly two points, each within one native frame |
| Invalid gap | constant (3,0), raw support invalid from 2.8–3.2 s | two separate blocks; no segment crosses gap |

A smooth 90-degree six-second arc and a multi-leg wandering path are required descriptive stress fixtures, but have no asserted true segment count. Their counts and geometry must reproduce exactly between repeated runs.

Failure of a required fixture is hard implementation/model QC failure. Fixtures do not tune the penalty.

## 10. Independent development diagnostics

Every accepted regime retains duration, path, displacement, signed x/y displacement, peak/mean speed, fitted mean velocity, within-regime squared residual, displacement/path ratio, maximum chord deviation, total absolute heading change, and support provenance. Heading calculations omit velocity samples below 0.50 m/s and break across such samples; they are diagnostics only.

### Fragmentation

The historical definitions remain an external-to-objective practical diagnostic:

- duration ≤1.5 s;
- path ≤1.0 m;
- displacement ≤0.5 m;
- `fragmentation_any`: at least one condition.

These thresholds are historically anchored development conventions, not definitions of geometric truth. A directional method passes the fragmentation balance gate only if `fragmentation_any ≤ 33.776%`, the prospectively frozen 20% relative reduction from the historical 42.22% baseline. Each component must be reported. The earlier representation-audit gate of 31.665% (25% reduction) is withdrawn as arbitrary before execution.

Also report, without a pass threshold, the number of adjacent same-class regimes whose union has displacement/path ≥0.95 and total absolute heading change <45°. This is an independent possible redundant-boundary diagnostic; it cannot alter classification because its thresholds lack prior validation.

### Inappropriate merging/direction complexity

Retain the historical independent composite:

- duration ≥8.0 s;
- displacement/path ≤0.5 when path is nonzero;
- total absolute heading change ≥180°;
- `merging_direction_any`: at least one condition.

Pass requires `merging_direction_any ≤ 3.97%`, the already frozen historical safety cap (approximately twice the 1.974% baseline). This protects against solving fragmentation by creating long, reversing, or tortuous units. The audit's proposed 5% cap is withdrawn as an unjustified relaxation.

Additionally report within-segment moving-direction resultant

$$
R=\left\|\frac{1}{q}\sum_{i=1}^{q}\frac{\mathbf v_i}{\|\mathbf v_i\|_2}\right\|_2
$$

over the $q$ samples with speed ≥0.50 m/s, and counts with $R≤0.5$. This directly describes directional dispersion but is descriptive because 0.5 has no external football validation.

### Lower-speed retention

Every eligible frame is partitioned regardless of speed; no high-speed inclusion threshold is permitted. Report historical-style counts for peak speed <5.5 m/s and displacement ≥3 m, plus total low-speed time/path coverage. The proposed ≥95% gate is demoted: its denominator depended on historical valley episodes and is not construct-invariant. The hard QC condition is instead that no supported regime is removed because of speed.

### Duration and geometry

Report full distributions by player/team/period, including historical thresholds above, but do not add post-hoc bands. Visual examples are selected deterministically from chronological strata and objective extremes after outputs exist; appearance has no selection or classification role except exposing a reproducible implementation mismatch.

## 11. Sampling-frequency sensitivity

The primary remains native 25 Hz. To isolate representation frequency from smoothing choice:

1. construct the valid seven-frame-smoothed 25 Hz position trace first;
2. within each supported smoothed-position block, create exact times `block_start + 0.1 k` that do not exceed block end;
3. linearly interpolate only between adjacent valid smoothed 25 Hz positions to those times;
4. derive 10 Hz velocity by consecutive differences;
5. use $L_{\min}=4$, recompute the one common 10 Hz radial noise scale, and use the same $3\log n$ rule per block.

This is deterministic downsampling sensitivity, not a claim of equivalence to a native 10 Hz provider or permission to bridge an invalid gap.

Match boundaries within each player-period-block using one-to-one minimum-absolute-time assignment, accepting a pair only when $|t_{25}-t_{10}|≤0.20$ s. Unmatched boundaries are false negatives from the 25 Hz reference or false positives in 10 Hz. Report precision, recall, F1, median/max paired offset, and segment counts.

Pass requires boundary precision, recall, and F1 each ≥0.90 and absolute segment-count difference ≤10% of the 25 Hz count. The 0.20 s tolerance is an engineering convention: two 10 Hz intervals and half the 0.40 s minimum, allowing derivative/grid localization without treating adjacent regimes as the same boundary. The 0.90 and 10% rules are pre-execution portability conventions, not externally validated football thresholds. Any change requires a new protocol version.

## 12. Gate provenance audit

| Gate | Provenance/class | Failure protected against | v1.0 decision |
|---|---|---|---|
| Deterministic fixtures | engineering/QC | incorrect cost, support, boundary, or solver implementation | retained and made exact |
| 100% valid support | governed project contract | segments crossing missing/invalid/known discontinuous trajectory | retained; known registry added |
| Fragmentation ≤31.665% | arbitrary/unjustified 25% choice in representation audit | excessive units | replaced by historical 33.776% material-reduction gate |
| Fragmentation ≤33.776% | historically anchored | failure to materially improve dominant historical problem | retained from frozen prominence protocol |
| Merging/direction ≤5% | arbitrary/unjustified relaxation | overmerging | replaced by historical 3.97% safety cap |
| Merging/direction ≤3.97% | historically anchored | long/reversing/tortuous merged units | retained |
| Lower-speed coverage ≥95% | arbitrary and denominator-dependent | losing low-speed geometry | demoted; partition/no-speed-filter is hard QC, coverage descriptive |
| Boundary match within 0.20 s | engineering tolerance | grid/localization disagreement | retained with explicit one-to-one rule |
| Boundary agreement ≥90% | development/engineering convention | provider-frequency instability | retained as precision, recall, and F1 gates |
| Segment-count difference ≤10% | development/engineering convention | frequency-dependent granularity | retained |
| Deterministic reproduction | engineering/QC | irreproducible partition | retained |

None of these thresholds defines a tactical run or validates football meaning.

## 13. Game 1 decision tree

There is one penalty and no candidate selection.

1. **Preflight:** verify input/contract hashes, frozen invalidity registry, firewall, source hash, and no Game 2/3 access.
2. **Hard QC:** common scale finite/positive; required fixtures pass; PELT matches the oracle; repeated outputs hash identically; every segment obeys support/period/minimum rules; no speed filter, repair, or prohibited input occurs.
3. **Balance gates:** fragmentation ≤33.776%; merging/direction ≤3.97%.
4. **Frequency gates:** precision, recall, F1 ≥0.90 and count difference ≤10%.

Classification is mechanical:

- **A — promising:** hard QC and every balance/frequency gate pass.
- **B — mixed:** hard QC passes, but at least one balance or frequency gate fails, unless C applies.
- **C — not useful/invalid:** hard QC fails; or both fragmentation fails to improve at all relative to 42.22% **and** merging/direction exceeds 3.97%.

Visual review cannot change A/B/C. After A, freeze the exact implementation, dependency versions, source/config/input hashes, and Game 1 outputs. After B or C, stop. No penalty, minimum duration, scaling, support rule, smoothing, stationary cutoff, diagnostic, or threshold may change under v1.0. A scientifically motivated redesign requires v2.0 and a new pre-execution justification; it may use Game 1 only. No post-hoc rescue or additional v1 candidate is allowed.

## 14. Held-out discipline

Game 2 may be opened for attacker segmentation only when all are true:

1. Game 1 classifies A mechanically;
2. v1.0 implementation and all hashes are frozen;
3. repository history still confirms no Game 2 attacker-segmentation output was inspected;
4. a Game 2 trajectory-support registry/procedure is frozen from raw-support QC before segmentation; and
5. a held-out protocol fixes exact replication gates without using Game 2 outcomes.

Game 2 then receives the identical smoothing, objective, BIC penalty rule, duration, tags, diagnostics, and frequency sensitivity—no retuning. If it fails the held-out frozen criteria, the representation fails held-out replication and Game 3 remains closed. Game 3 requires a later explicit protocol regardless of Game 2 outcome.

## 15. Claims and nonclaims

The maximum allowed claim after a successful development result is:

> A reproducible attacker-only temporal representation of observed movement.

The protocol cannot establish a tactical or intentional run, off-ball action, defensive response, pinning, dragging, tracking, marking, decoy, reconfiguration, responsibility, attention, threat, success, causality, influence, gravity, or value.

## 16. Provenance and stopping rule

PELT is an exact search algorithm for penalized change-point objectives, not a football theory (Killick, Fearnhead, and Eckley, 2012). Schwarz/BIC mean-change selection has established statistical precedent (Yao, 1988). The two-dimensional extension, common radial scale, 0.40 s minimum, support registry, diagnostics, and decision gates are transparent project choices to be falsified. No novelty is claimed for change-point segmentation.

Do not execute until a separate instruction authorizes implementation. Do not inspect Game 2 or Game 3 attacker segmentation, defensive outcomes, or football clips while implementing or evaluating v1.0.
