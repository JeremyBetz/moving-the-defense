# Attacking Movement Representation Fork

**Status:** construct-selection and targeted prior-art audit; no new empirical analysis

**Decision:** **B — pivot to a continuous attacking-movement representation.** Geometry-first discrete episodes remain a secondary, deferred possibility rather than the next experiment.

> **Prospective resolution (2026-08-31):** [continuous protocol v1.0](protocols/attacking_continuous_movement_v1.md) subsequently retained signed displacement, path length, and derived straightness, while deferring heading change and speed variation before any Game 1 continuous output. The five-family discussion below records the construct fork that preceded that minimality decision.

## Why this fork exists

Moving the Defense eventually wants to ask:

> During an attacker's observed movement, what measurable defensive adjustment followed?

That question requires a defensible attacker-side representation, but it does not logically require one universal set of start/end boundaries. Three outcome-blind discrete approaches have now exposed different failure modes on Metrica Sample Game 1:

| Approach | Empirical result | Construct lesson | Algorithm lesson |
|---|---|---|---|
| Scalar speed valleys | 38,651 reproducible episodes; substantial lower-speed retention; 42.22% fragmentation | A local speed minimum is a physical-effort boundary candidate, not necessarily a coherent football movement boundary. | The deterministic valley implementation works as specified; its boundary evidence is too permissive for this target. |
| Valley prominence | Fragmentation fell to 1.17%–7.78%, but merging/direction rose to 35.88%–69.03%; no threshold qualified | Valley depth alone cannot decide whether a boundary separates two meaningful geometric legs. | The frozen prominence filter works; as a standalone boundary filter it removes both trivial and necessary valleys. |
| Penalized 2D velocity means | 247,175 regimes; 99.799332% fragmentation; duration median/IQR at 0.40 s; frequency recall/F1/count gates failed | Ordinary football movement contains many small velocity changes. A statistical constant-velocity regime is not equivalent to a coherent football movement. | Exact PELT correctly optimizes the frozen objective. The Game 1 result rejects that objective/scaling/penalty/duration combination as the representation—not PELT or change points generally. |

The evidence does **not** show that speed is useless, change points are useless, or discrete segmentation is impossible. It shows that none of these three frozen boundary semantics supplies the required universal attacking-movement unit.

## Targeted prior art: continuous and discrete representations

| Source or family | Question/input | Representation | Boundaries required? | Key parameters | Output/validation | What transfers | What does not |
|---|---|---|---|---|---|---|---|
| Duarte et al. (2013) | Team-team and player-team synchrony from professional football positions | Time-varying cluster phase and relative phase | No universal movement episodes | Directional signal construction and phase conventions | Match-level synchrony, dispersion, entropy | Continuous relationships can remain interpretable through time | Phase as an attacker-movement construct or tactical response |
| Marcelino et al. (2020) | Collective football coordination from player trajectories | Spatiotemporal velocity correlations | Local time windows, not movement episodes | Window and time-delay choices | Five-match collective/player patterns | Windowed velocity relationships are established football practice | Their coordination interpretation or team fingerprint as this construct |
| Kai et al. (2021) | Change-of-direction load from football positional data | One-second heading-change and velocity summaries; event rules for COD | Windows for summaries; thresholds for COD events | Window, smoothing, speed/direction criteria | Prescribed-angle trials and match application | Heading and velocity can be summarized locally and physically | COD thresholds as universal attacking boundaries |
| Llana et al. (2022) | Physical effort in football tracking | Smoothed speed and valley-to-valley sections | Yes | Smoothing, valley rule, intensity descriptor | Descriptive football application | Lower-speed movement and speed remain relevant descriptors | Scalar valleys as sufficient geometric boundaries |
| Edelhoff, Signer, and Balkenhol (2016) | General movement-path analysis | Stepwise and multi-step speed, turn, displacement, straightness; moving windows or segmentation | No for moving-window description; yes for segmentation families | Sampling grain, window/segment method | Comparative methodological review | Representation should follow the question; scale and sampling matter | Animal behavioral states or a universal method |
| Lee, Han, and Whang (2007), TRACLUS | Geometric trajectory simplification and clustering | Piecewise lines using parallel, perpendicular, and angular error | Yes | MDL balance and geometric errors | Algorithmic trajectory experiments | Geometry can preserve turns/shape while tolerating within-leg speed change | Clustering, parameters, or football meaning |
| Ramer–Douglas–Peucker family | Polyline simplification | Retained characteristic points under perpendicular-error tolerance | Yes | Spatial tolerance | Geometric approximation | A simple geometry-first episode backbone | Time, speed, stop/restart, or football semantics without additions |
| Shpurov et al. (2024) | Football trajectory movement statistics | Step-size/trajectory distributions | No universal episodes | Sampling and inclusion rules | J-League tracking summaries | Continuous paths can be studied without tactical boundaries | Foraging interpretation or direct response measurement |
| Rodríguez-Sánchez et al. (2026) | Collective football motion | Spatially reconstructed velocity vector fields and potentials | No player movement episodes | Spatial/temporal field reconstruction | Season-level team patterns and ball progression associations | Continuous velocity fields are a current football representation precedent | Their collective potential, control claims, or scale as an individual attacker descriptor |
| Football motion/pitch-control models | Reachable space from position, velocity, acceleration | Instantaneous or short-horizon motion state | No movement episodes | Motion horizon and physical model | Provider/paper-specific trajectory or control prediction | Local kinematics can support continuous downstream questions | Space control, intention, value, or attacker influence as current results |

The literature contains both continuous and discrete traditions. It does not establish that one is universally correct. It does show that displacement, velocity, heading, straightness, and coupling can be analyzed at fixed or moving temporal scales without first asserting behavioral episode boundaries. Conversely, geometry-first simplification remains a legitimate discrete family when finite legs are the actual construct.

## Candidate A — discrete geometric movement episodes

The simplest defensible discrete alternative would partition the attacker's smoothed path by **geometric shape**, not constant velocity. One candidate is an adaptive polyline or heading-persistence representation that:

- permits acceleration and deceleration along one leg;
- permits gradual curvature within a bounded chord/curvature error;
- separates a persistent sharp turn or reversal;
- treats stop/restart with an explicit time/speed rule rather than spatial shape alone;
- retains lower-speed displacement; and
- reports wandering or heterogeneous paths rather than forcing a tactical label.

Its required choices would include geometric deviation tolerance, curvature/heading persistence, minimum temporal support, and a stop/restart convention. Those choices interact and would create a substantial new validation burden. This family is fundamentally different from speed valleys (no scalar minimum defines the boundary), prominence (no valley-depth filter), and constant-velocity PELT (acceleration along a geometrically coherent leg need not split it).

It remains scientifically plausible but is **deferred**. The project does not currently need universal episodes strongly enough to justify another boundary-optimization cycle.

## Candidate B — continuous attacking movement

The primary candidate represents each attacker at time $t$ by directly interpretable geometry over a fixed trailing attacker-only window

$$
W_w(t)=[t-w,t].
$$

The recommended v1 primary window is **$w=2.0$ s**, with prospectively frozen **1.0 s and 4.0 s sensitivities**. Two seconds is reused as an already established local history scale, not selected against a new defensive outcome. Only windows with complete governed attacker support are computed; no interpolation bridges invalid support.

For smoothed attacker positions $\mathbf p_0,\ldots,\mathbf p_n$ and step vectors $\delta_i=\mathbf p_i-\mathbf p_{i-1}$, retain five observable families:

### 1. Signed displacement vector

$$
\Delta\mathbf p_a(t;w)=\mathbf p_n-\mathbf p_0=[\Delta x_a,\Delta y_a]\quad\text{m}.
$$

This says where the attacker ended relative to where they began. It preserves longitudinal and lateral direction. It can cancel on an out-and-back path.

### 2. Path length

$$
P_a(t;w)=\sum_{i=1}^{n}\|\delta_i\|_2\quad\text{m}.
$$

This says how much ground the attacker covered, including curved or reversing movement. It is sensitive to tracking noise and smoothing.

### 3. Straightness

$$
S_a(t;w)=\frac{\|\Delta\mathbf p_a(t;w)\|_2}{P_a(t;w)}.
$$

For positive path, $S_a\in[0,1]$: values near one indicate a direct path; lower values indicate curvature, reversal, or wandering. It is undefined—not imputed—when path is numerically zero.

### 4. Absolute heading change

$$
H_a(t;w)=\sum_i |\operatorname{wrap}(\theta_i-\theta_{i-1})|\quad\text{degrees}.
$$

This distinguishes a straight displacement from a curved, cutting, or reversing path. The future protocol must freeze the smoothing, valid-step, and low-speed heading conventions before calculation. It is noise- and sampling-frequency-sensitive.

### 5. Total speed variation

$$
V_a(t;w)=\sum_i |s_i-s_{i-1}|\quad\text{m/s}.
$$

This distinguishes steady travel from slowing, stopping/restarting, or repeated speed adjustment without requiring a boundary. It is the most noise-sensitive core observable and must earn retention through synthetic and frequency robustness; it may be dropped prospectively if it cannot reproduce, but it must not be tuned using defensive outcomes.

Mean velocity is available exactly as $\Delta\mathbf p_a/w$ and mean speed as $P_a/w$; they should not be duplicated as independent core variables. The five families remain separate. There is no composite movement score, embedding, cluster, or tactical label.

## Football thought tests

| Football movement | Discrete geometric episodes | Continuous v1 |
|---|---|---|
| Straight run with brief deceleration | Ideally one geometric leg; stop rule must not overreact | Large directed displacement/path, straightness near one; speed variation records the slowdown |
| Curved run | One curved segment or a few tolerance-dependent legs | Path exceeds displacement; heading change rises while net direction remains visible |
| Sharp cut | Persistent turn creates a boundary | Heading change and usually speed variation rise; pre/post signed displacement can be inspected without declaring an event |
| Stop and restart | Requires an explicit temporal stop rule | Path/displacement show travel; speed variation distinguishes stop/restart from steady travel |
| Low-speed drift | Retained if geometry/support rules allow | Modest signed displacement and path remain measurable without a speed inclusion threshold |
| Holding width almost stationary | Risks an artificial stationary episode | Near-zero path/displacement is a valid observation; heading is undefined when unsupported |
| Check toward the ball then spin away | Likely two or more legs depending tolerance | Path can be high while net displacement/straightness are low and heading change is high |
| Long wandering path | Several geometry-dependent legs | High path, low straightness, high heading change; still no claim of one coherent action |
| Repeated small stride/velocity adjustments | Geometry should ignore most if path remains coherent | Speed variation/heading can expose noise; sampling sensitivity must decide whether those observables are usable |
| Movement starts before defender visibly responds | Episode start may be ambiguous or precede the chosen leg | Trailing windows preserve developing movement; a later response window can begin at $t$ without claiming a universal onset |

## Attacker-to-defender bridge compatibility

Discrete episodes would offer a convenient interval $[t_0,t_1]$ over which to measure defender focal-relative path and signed displacement. Convenience is not sufficient reason to assert unstable boundaries.

The continuous representation supports a cleaner prospective bridge:

> attacker geometry over $[t-w,t]$ → defensive geometric change over $[t,t+h]$.

The bridge can later compare attacker-window features with the already validated defender focal-relative path and retained signed focal-relative displacement over a separately frozen future horizon $h$. Contextual/matched comparisons or cross-lag descriptions can follow only after the attacker representation validates. Temporal precedence would support association timing, not causality. No response onset, assignment, tactical label, or attacker attribution is required.

Discrete segmentation is therefore **not necessary** for the immediate downstream science. Continuous windows also allow movements already developing before a defender change to remain observable rather than forcing one candidate onset instant.

## Outcome blindness and leakage control

Both families must use only attacker trajectory, canonical time/support, and period boundaries. Defender movement, events, receptions, passes, shots, outcomes, threat, and visual interest cannot define or select attacker boundaries/features.

For continuous v1:

- freeze $w=2.0$ s primary and 1.0/4.0 s sensitivities before any bridge output;
- compute features at a deterministic supported time grid;
- require complete attacker support throughout each window;
- keep future defensive horizon $h$ out of attacker-feature construction;
- freeze $h$ and any sampling scheme before inspecting attacker–defender associations; and
- do not choose $w$, $h$, or feature retention by predictive performance on defensive outcomes.

## Validation and complexity comparison

| Criterion | Discrete geometry | Continuous v1 |
|---|---|---|
| Football readability | Strong if legs are valid | Strong for signed movement, distance, directness, and turning |
| Parameters/thresholds | Several interacting boundary rules | Window, smoothing/support, heading convention; no boundary threshold |
| Sampling portability | Boundary identity can change | Values still change with frequency, but can be compared directly |
| Lower-speed movement | Retainable | Retained automatically |
| Curved movement | Natural but tolerance-dependent | Path/straightness/heading describe it without splitting |
| Noise sensitivity | Boundaries can move discontinuously | Path, heading, and speed variation are sensitive but remain graded |
| Labels required | No labels for geometry, but episode validity is hard to judge | No labels for deterministic geometry |
| Held-out burden | Boundary stability plus episode coherence | Numerical/distributional replication of each observable |
| Defensive-primitive compatibility | Same-interval summary is simple | Lagged window-to-window bridge is direct |
| Statistical tractability | Irregular episode rows and selection | Regular supported time grid; overlap dependence must be handled |
| Sloan explainability | Intuitive if boundaries survive | Highly explainable geometry without claiming run types |
| Artificial-structure risk | High: every path must be partitioned | Lower: no claim that nature supplies universal boundaries |

The biggest scientific risk for continuous v1 is **scale dependence disguised as meaning**. Overlapping windows, smoothing, sampling rate, and selected $w$ can make descriptors look stable while generating strongly dependent observations. Validation must address this directly.

## Prospective Game 1 validation plan

Before Game 2 can be opened, freeze a versioned continuous-representation protocol that specifies:

1. canonical attacker-only support and the existing trajectory-validity registry;
2. seven-frame smoothing and edge behavior;
3. $w=2.0$ s primary plus 1.0/4.0 s sensitivity windows;
4. deterministic evaluation-grid timing;
5. exact formulas and numerical behavior for zero path and low-speed headings;
6. no interpolation across unsupported data;
7. synthetic fixtures for straight movement, acceleration/deceleration, curve, cut, stop/restart, low-speed drift, stationary holding, out-and-back, and invalid gaps;
8. 25 Hz versus deterministic 10 Hz numerical robustness for each observable;
9. translation/rotation/reflection sanity checks where mathematically appropriate;
10. player/team/period distribution and missing-support summaries; and
11. deterministic rerun hashes.

Game 1 must show deterministic computation, support validity, geometric fixture correctness, acceptable frequency robustness under prospectively frozen observable-specific tolerances, and no unexplained player/team/period concentration. There are no fragmentation or merging gates because no episodes exist. Only after an **A** result under that future frozen protocol may a separate held-out Game 2 protocol be prepared. Game 2 and Game 3 remain untouched.

## Decision and claim boundary

### Primary

**Continuous fixed-window attacker geometry** using the five separate observable families above.

### Secondary/deferred

**Discrete geometric movement episodes** based on path shape/heading persistence. Revisit only if a later football or bridge question genuinely requires finite boundaries that continuous windows cannot answer.

### Allowed now

- the three tested discrete specifications have distinct, reproducible failure modes;
- the frozen PELT representation is rejected for held-out use;
- continuous fixed-window geometry is the selected next candidate family;
- discrete geometry remains plausible but unvalidated and deferred; and
- segmentation is not logically necessary for the next attacker-to-defender bridge.

### Not allowed

This audit does not validate the continuous observables, select a tactical window, identify movement episodes, detect runs, establish defensive response, opponent association, attacker causation, tactical intent, assignment, pinning, dragging, tracking, covering, handoffs, reconfiguration, gravity, off-ball value, or movement quality.

## Next protocol recommendation

Freeze and review a **continuous attacker geometry v1** Game 1 protocol. Do not execute it in the same pass, do not reopen PELT/prominence tuning, and do not design the attacker-to-defender bridge until the attacker-side representation passes its own outcome-blind validation.
