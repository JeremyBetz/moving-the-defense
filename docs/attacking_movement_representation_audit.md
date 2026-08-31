# Attacking Movement Representation Audit

**Status:** construct-selection and prior-art audit; no segmentation executed  
**Development/held-out boundary:** Metrica Sample Game 1 development only; Sample Games 2 and 3 unopened for attacker segmentation

> **Retrospective status (2026-08-31):** the selected frozen 2D velocity change-point representation executed on Game 1 and classified B, with 99.799332% fragmentation and failed 10 Hz recall/F1/count stability. The result rejects that specification for held-out use. The subsequent [representation fork](attacking_movement_representation_fork.md) selects continuous fixed-window attacker geometry as the next primary family while retaining geometry-first episodes as deferred. The historical reasoning below is preserved.

## Current problem

Moving the Defense needs a finite, attacker-only interval over which defensive geometric change can later be measured. It does not yet need a provider-style run or a tactical action. The historical Game 1 speed-valley rule generated 38,651 reproducible movement-effort episodes and retained lower-speed geometry, but 42.22% met a frozen fragmentation diagnostic. The frozen prominence experiment removed many shallow valleys, yet every nonzero candidate raised merging/direction failures from 1.974% to 35.878%–69.032%. No candidate qualified.

Prominence failed conceptually because it judges only the vertical depth of a minimum in scalar speed. A modest slowdown can separate two movements when direction changes, while a deep slowdown can occur inside one continuing movement. Removing scalar valleys therefore cannot preserve boundaries whose evidence lies in the two-dimensional velocity vector.

No defensive coordinate, event outcome, tactical label, Game 2 attacker-segmentation result, or Game 3 data was inspected for this audit.

## Construct distinctions

| Construct | Immediate meaning | Context required | Status here |
|---|---|---|---|
| Locomotor effort | A bout of physical work, commonly delimited or described by speed and acceleration | Player trajectory; often physical-load thresholds | Historical speed-valley construct, not the present target |
| Movement episode | A generic finite interval of player motion | Depends on its operational definition | Useful umbrella, but too underspecified to choose boundaries |
| **Directional movement segment** | A finite interval in which the player's two-dimensional velocity is adequately represented by one local movement regime | Attacker trajectory only | **Immediate construct required** |
| Tactical run | Movement interpreted as an overlap, run in behind, support run, and so on | Ball, possession, teammates, opponents, and football semantics | Downstream; not defined here |
| Off-ball action | A broader football action that may include moving, checking, or holding position | Match context and semantic interpretation | Downstream; stationary/holding behaviour may later need its own construct |

The selected construct can retain low-speed translation, acceleration and deceleration within a regime, continuation through brief slowing, and sustained directional changes. It does not claim intention or tactical meaning.

## Targeted prior art

| Source/method | Sport problem and input | Boundary definition and parameters | Direction / speed / context | Validation | Legitimate transfer | Does not transfer |
|---|---|---|---|---|---|---|
| Llana et al. (2022), speed valleys | Football physical efforts from smoothed player speed | Consecutive local speed minima; smoothing and high-intensity descriptor | Scalar speed; later context, but valley construction is player based | Descriptive football application | Outcome-blind finite efforts and speed as a descriptor | Scalar valleys as sufficient directional boundaries; high-speed inclusion as the present construct |
| Kai et al. (2021), change of direction | Football change-of-direction angle/time from 2D tracking | Acceleration candidate and jerk-defined onset/end; smoothing and acceleration rules | Explicit velocity direction, speed, acceleration, jerk; no defensive outcome | Set-angle trials plus match application | Direction is observable and a turn occupies an interval rather than one frame | COD/load thresholds as universal movement segmentation; jerk-sensitive rules without separate validation |
| Corbett, Sweeting, and Robertson (2019), binary segmentation | Australian-football locomotor states from wearable-sensor velocity time series | Binary change-point segmentation; change-point quotient and feature choices | Scalar velocity; no tactical outcome needed for boundaries | Segment similarity assessed using descriptive/spectral features | Sustained regime changes can replace every local extremum | Their scalar signal, quotient, match-scale aim, and classifier as direct football rules |
| Edelhoff, Signer, and Balkenhol (2016), movement-path review | General movement-path segmentation | Reviews topology-, change-point-, and state-space methods | Speed, heading/turning angle, straightness, and temporal properties | Comparative methodological synthesis | Segmentation method must match the behavioural/geometric question; parameters and autocorrelation matter | Any single method as domain-valid without a prospective test |
| Lee, Han, and Whang (2007), TRACLUS partitioning | Piecewise-linear trajectory representation before clustering | Minimum-description-length partition using perpendicular and angular error | Direction/shape explicit; speed and football context absent | Algorithmic experiments | Direction and perpendicular deviation can preserve turns hidden by scalar speed | Clustering, its MDL balance, or spatial-only segments as the selected football method |
| Yin, Song, and Yang (2018), 2D change points | Changes in two-dimensional trajectory velocity/diffusivity | Likelihood-based recursive change points with significance and minimum-length controls | Full 2D displacement state; no sport context | Simulated and empirical particle trajectories | Joint dimensions can define sustained state changes with explicit false-positive control | Diffusion model, biological interpretation, or its parameters as football truth |
| Gradient Sports (2026), off-ball runs | Forward off-ball runs in broadcast tracking/event data | Start above 15 km/h with acceleration at least 2.5 m/s², or above 20 km/h; contextual termination rules | High speed, acceleration, ball/event context | Product/application examples | Transparent comparator showing what a run product targets | Lower-speed coverage, outcome-blind boundaries, or tactical run labels |
| SkillCorner Game Intelligence (2023–2025) | Ten tactical off-ball-run types | Public material says speed, distance, and threat enter; complete boundary algorithm is not public | Tactical and contextual; direction matters through run type | Product use and player-profile applications | Evidence that tactical runs are a later, context-rich construct | Proprietary boundaries, tactical labels, threat, or passing-option logic as attacker-only segmentation |

The audit did not identify a football paper that makes a full 2D velocity-state change-point rule a validated universal attacking-movement representation. That is a limitation of this targeted search, not a novelty claim.

## Candidate families

### 1. Penalized change points in 2D velocity state — selected

- **Football intuition:** keep a player in the same segment while their movement vector remains one sustained local pattern; split when the vector changes persistently enough to constitute a new geometric leg.
- **Observable:** $\mathbf v(t)=[v_x(t),v_y(t)]$, derived from the already fixed, smoothed attacker trajectory in physical units.
- **Prospective rule family:** piecewise-constant multivariate mean fitted with an offline penalized change-point algorithm (recommended implementation: PELT with squared-error cost). A boundary is retained only when the reduction in within-segment 2D velocity error pays a fixed change penalty and satisfies a fixed minimum duration.
- **Parameters to freeze before execution:** inherited seven-frame position smoothing and edge/support policy; robust velocity scaling policy; one primary penalty rule; minimum segment duration; period/support boundary convention. A small sensitivity may be predeclared, but it cannot select the primary result.
- **Strengths:** uses speed and heading jointly; suppresses isolated fluctuations; partitions all supported movement rather than requiring high speed; deterministic; interpretable in metres and metres per second; computationally near-linear with PELT under standard conditions.
- **Risks:** gradual curves may become several straight-ish regimes; one mean velocity can hide acceleration; scale and penalty determine granularity; stop/restart can create a stationary segment; correlated tracking noise challenges simple squared-error assumptions.
- **Compatibility:** the Metrica and IDSSE tracking used here are both 25 Hz. Because the rule is expressed in seconds and physical units, it can also be tested on a deterministic 10 Hz representation after the canonical support/time contract; frequency equivalence must still be demonstrated.
- **Why it addresses the failure:** it asks whether the complete movement vector changes persistently, rather than whether a scalar valley is deep.

### 2. Piecewise direction/curvature or trajectory simplification — deferred

This family uses turning angle, chord deviation, or a minimum-description-length line approximation. It makes sharp turns visible and is easy to draw, but a spatial-only rule can miss stop/restart or speed-regime changes in the same direction. Curved runs also force an arbitrary geometric-error tolerance and can be oversegmented even when football movement is continuous. It is retained as a diagnostic comparator or later alternative, not the next primary candidate.

### 3. Hand-built speed + heading/acceleration/jerk event rules — rejected for the next test

Kai et al. show that acceleration, jerk, and velocity direction can quantify a prescribed change of direction; commercial run definitions likewise combine speed and acceleration. A hybrid could catch sharp turns and stops, but it would require several interacting thresholds, persistence rules, and conflict resolution. Adding such a rule immediately after the prominence failure would be an ad hoc direction split rather than a clean construct change. It is not selected.

## Attacker-only thought tests

| Trajectory | 2D velocity change points | Direction/curvature family | Hybrid event rules |
|---|---|---|---|
| Straight run, brief deceleration | Should remain one segment if the change is brief relative to penalty/duration | One segment | May split if acceleration thresholds fire |
| Accelerate → decelerate → continue same direction | One segment if gradual; multiple sustained speed regimes remain possible | Usually one segment | Threshold-sensitive |
| Sharp turn without stopping | Boundary from changed $v_x/v_y$ mean | Strong boundary | Boundary if heading rule is met |
| Stop then restart in same direction | Moving–stationary–moving regimes | May merge because geometry is collinear | Usually separable, but needs stop thresholds |
| Curved run | A few regimes if curvature is sustained; possible staircase failure | Natural but tolerance-dependent | May create repeated turn events |
| Long wandering movement | Multiple sustained vector regimes | Multiple line segments | Potentially many threshold events |
| Short low-speed displacement | Retained if duration/support rules permit | Retained | Often lost by run thresholds |
| Small speed fluctuations | Penalized away if they do not improve fit enough | Usually ignored if spatial deviation is small | Vulnerable to repeated triggers |

These are falsifiable expectations, not observed results.

## Prospective validation design

The next task should freeze a versioned Game 1 protocol before generating candidate segments. It should inherit the existing seven-frame smoothing and governed tracking-support policy unchanged, derive $v_x/v_y$ in metres per second, and specify one deterministic multivariate change-point implementation. No defensive data may enter construction, parameter selection, evaluation, or visual sampling.

### Pre-execution test layers

1. **Deterministic geometric fixtures.** Freeze synthetic attacker trajectories for constant translation, a brief same-direction slowdown, a sustained speed change, a sharp turn, stop/restart, a smooth curve, low-speed displacement, and noise-only motion. Known boundaries must be reproducible within one source frame; constant/noise-only fixtures must not acquire unsupported boundaries. The curved fixture may admit a predeclared bounded segment-count range rather than a fictitious single truth.
2. **Game 1 development audit.** Apply the frozen rule to all prospectively supported attacking outfield traces. Report all segment durations, path/displacement, signed displacement, peak/mean speed, within-segment velocity residuals, adjacent-regime vector differences, lower-speed coverage, support validity, and player/team/period balance.
3. **Frequency sensitivity.** Compare the identical physical-time rule on native Game 1 and a deterministic 10 Hz representation. Report boundary matching within 0.20 s, segment-count change, and geometry differences. This is sensitivity, not a substitute dataset.
4. **Visual audit.** Select cases deterministically before plotting. Visuals can expose a coordinate, support, or boundary implementation defect; subjective football appearance cannot change classification or parameters.

### Superseded proposed gates

The preliminary audit proposed gates before the mathematical model and penalty were fixed. The later [frozen v1.0 protocol](protocols/attacking_directional_segmentation_v1.md) audited rather than mechanically copied them:

- deterministic fixtures, governed support, deterministic reproduction, and frequency checks were retained and specified exactly;
- the arbitrary 31.665% fragmentation and 5% merging gates were replaced by the previously frozen historical anchors of 33.776% and 3.97%;
- the 95% lower-speed gate was demoted because its historical-episode denominator is not invariant to a new construct; no speed-based exclusion is permitted instead; and
- the 0.20 s, 90%, and 10% frequency rules remain explicit engineering/development conventions, now expressed through one-to-one precision, recall, F1, and count agreement.

The protocol freezes one BIC-derived penalty rather than a development ladder. No result informed these revisions; no segmentation was executed.

## Held-out plan

- **Game 1:** protocol development and the only empirical execution in the next pass.
- **Game 2:** remains untouched for attacker segmentation. Open it only if Game 1 earns A under the frozen gates, the primary rule is selected without visual discretion, and tracking-support QC is complete. Execute the exact frozen transformation and gates with no retuning; a held-out B or C is preserved as failure to replicate.
- **Game 3:** remains untouched. It is not opened by success on Game 1 or Game 2; use would require a later, separately justified validation protocol.

Prior unrelated Phase 4 use of Game 2 does not reveal attacker-segmentation outcomes, but repository-history verification should be repeated when the protocol freezes.

## Claim boundary and provenance

If successful, the method may claim only a reproducible, attacker-only temporal representation of observed movement: a **directional movement segment**. It may not claim a tactical or intentional run, off-ball action, decoy, pinning, dragging, tracking, defensive response or reconfiguration, causality, responsibility, attention, success, threat, gravity, or value.

Speed-based efforts, change-of-direction measurement, change-point segmentation, trajectory simplification, and commercial off-ball-run detection are all prior art. The proposed contribution is not invention of segmentation. Any later contribution depends on prospectively validating an outcome-blind attacker interval and then separately testing its association with defensive geometric change under the project's inference ladder.

## Exact next-step recommendation

The [Game 1 protocol](protocols/attacking_directional_segmentation_v1.md) is now frozen. The next step, only after explicit authorization, is to implement and execute it exactly. Do not reopen scalar-prominence tuning or add a post-hoc heading threshold.
