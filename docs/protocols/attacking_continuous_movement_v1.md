# Continuous Attacking Movement Protocol v1.0

**Protocol status:** frozen before Game 1 execution

**Freeze date:** 2026-08-31

**Development match:** Metrica Sample Game 1

**Held-out discipline:** Sample Game 2 remains closed unless Game 1 classifies A; Sample Game 3 remains closed regardless

**Scientific boundary:** attacker-only geometric representation; no defensive outcomes, tactical labels, or attacker-to-defender bridge

## 1. Motivation and construct

Moving the Defense needs to describe what an attacker has recently done geometrically without asserting that every path contains a universal football-action boundary. Historical scalar speed valleys, prominence filtering, and penalized two-dimensional velocity regimes each produced a different reproducible boundary failure. Those results reject their frozen specifications for this purpose; they do not reject speed, change points, or discrete geometry generally.

At every eligible evaluation time $t$, v1 represents one supported outfield player's own movement over the trailing window

$$
W_w(t)=[t-w,t].
$$

Every supported outfield trace is treated prospectively as a possible attacker trace. Possession, ball position, teammates, opponents, events, defenders, outcomes, and visual interest do not select players, times, windows, or features. The representation describes observed motion only.

## 2. Feature-minimality decision

V1 retains three observable families, stored as four primary columns:

1. signed pitch-coordinate displacement: `delta_x_m`, `delta_y_m`;
2. travelled path length: `path_length_m`; and
3. straightness: `straightness`, a deterministic derived view of displacement and path.

Straightness adds no independent mathematical information beyond the first two families. It is retained because it exposes direct versus returning/curved travel in one bounded, pitch-readable view and prevents downstream users from substituting an undocumented ratio. Mean velocity and mean speed are not additional features: they are exactly displacement divided by $w$ and path divided by $w$.

Two fork candidates are excluded from v1:

- **Absolute heading change — deferred.** It requires a convention for headings at zero or near-zero steps. A low-speed cutoff would add an unvalidated parameter, while no cutoff makes the sum unstable under tracking noise and sampling frequency. Displacement, path, and straightness retain the most robust turning consequence without claiming how the path turned.
- **Total speed variation — deferred.** It is a derivative-sensitive kinematic-variability quantity rather than minimal path geometry. It would amplify sampling/smoothing choices and partially reintroduce the instability exposed by the constant-velocity-regime experiment. V1 cannot distinguish a brief slowdown from a steady traversal with identical endpoints and path; that loss is accepted prospectively.

Neither exclusion establishes that the quantity is useless. Reintroduction requires a later outcome-blind protocol and independent robustness justification.

## 3. Canonical input and reference frame

Use [canonical tracking contract v1.0.0](../canonical_tracking_contract.md): physical 105 × 68 m coordinates, pitch-centre origin, +x to the right and +y upward in the fixed pitch drawing. Use `Float64` throughout.

Here **longitudinal** means canonical pitch x and **lateral** means canonical pitch y. These names do not imply attacking direction. Do not flip by team, period, goal, possession, ball, or opponent. A mirrored view may be used only in a fixture/invariance test and must not replace primary output.

Eligible entities are metadata-rostered player rows with `is_goalkeeper == false`. Goalkeeper identity comes from canonical provenance. Ball rows and ball state are irrelevant. Team identity is retained for descriptive grouping but not feature construction.

## 4. Raw continuity and trajectory-validity registry

Before smoothing, a raw player row is valid only when:

- `entity_type == player`, `is_goalkeeper == false`;
- `support_state == observed`, `is_present == true`, and `coordinate_valid == true`;
- x/y are finite;
- period, provider frame ID, and both clocks are present;
- rows are unique on match/period/frame/player;
- within a player-period run, provider frames follow the documented Game 1 succession, time is strictly increasing, and adjacent `time_match_s` differs by exactly 0.04 s within canonical numerical tolerance $10^{-9}$ s; and
- the row is outside the frozen Game 1 invalidity registry below.

| Team/player | Period | Invalid raw support |
|---|---:|---|
| Home 10 | 1 | provider frames 2911–2945 inclusive |
| Home 3 | 2 | entire player-period |
| Away 22 | 2 | entire player-period |

These are the already documented outcome-blind trajectory-support decisions. They are not a general speed filter. A missing row, invalid coordinate, unexpected frame/time interval, registry interval, player entry/exit, or period boundary splits support on both sides. No interpolation, padding, extrapolation, clipping, winsorization, identity repair, or post-derived speed cap is allowed in the primary representation.

Substitution entry/exit is handled only through observed contiguous support; absence is not tactically interpreted. Temporary missingness breaks support. Duplicated identities are excluded only where the frozen registry says so; equality alone does not create a new exclusion. No ball-support requirement exists.

## 5. Governed smoothing

All included observables use one trajectory source. On each maximal raw-valid player-period run, apply the historical centred seven-frame arithmetic mean separately to x and y:

$$
\widetilde{\mathbf p}_i=\frac{1}{7}\sum_{j=i-3}^{i+3}\mathbf p_j.
$$

The smoothed position exists only when all seven raw rows are valid, consecutive, and in the same player-period run. The first and last three raw rows of every run therefore lack smoothed support. No partial window or edge padding is permitted. This 0.28 s sample window spans 0.24 s from its first to last observation. It stabilizes measurement; it does not infer a tactical path or intention.

The primary Game 1 calculation is native 25 Hz. The 10 Hz sensitivity is constructed from the already valid seven-frame-smoothed 25 Hz trace as specified in Section 11; it does not apply a second smoother. Thus there is no competing “10 Hz equivalent” smoothing kernel in v1. A future native-10-Hz provider requires a separately frozen equivalence rule and may not silently substitute a three-frame filter.

## 6. Windows and deterministic evaluation grid

Window roles are frozen before output:

| Window | Role | Football scale and limitation |
|---:|---|---|
| 2.0 s | Primary | Recent local movement long enough to exceed frame-scale variation while remaining short enough to describe a developing shift, run, check, or hold geometrically. It is not a tactical-action duration. |
| 1.0 s | Sensitivity | More immediate geometry, more sensitive to smoothing/noise and short reversals. |
| 4.0 s | Sensitivity | Longer local path, more likely to combine several football movements and return toward its start. |

No other duration may be inspected under v1.

Evaluate at a fixed **0.20 s grid** within each period. Let period-relative origin $o_p$ be `time_period_s` on the first canonical match frame of the period, common to all players rather than the first valid frame of an individual trace. Candidate endpoints are

$$
t_{p,k}=o_p+0.20k,\qquad k=0,1,2,\ldots
$$

An endpoint is present only when a provider frame matches $t_{p,k}$ within $10^{-9}$ s. There is no nearest-frame fallback or tie. Window start $t-w$ must likewise be an exact supported smoothed timestamp within $10^{-9}$ s. Grid indexing restarts independently at each period origin; windows never cross a period boundary.

At 25 Hz, the grid is every fifth frame. Adjacent 2.0 s observations overlap by 90%, 1.0 s observations by 80%, and 4.0 s observations by 95%. Rows are therefore repeated local descriptions, not independent samples. Counts, uncertainty, and any later model must respect player/match/time dependence.

The grid is selected for cross-frequency portability and to avoid treating every 0.04 s frame as a new scientific observation. It is not selected from Game 1 output or defensive behavior.

## 7. Exact feature formulas

For one eligible endpoint and window, let supported smoothed positions be $\widetilde{\mathbf p}_0,\ldots,\widetilde{\mathbf p}_n$ at every native sample from $t-w$ through $t$, inclusive. At 25 Hz, $n=25w$: 25, 50, or 100 steps for 1, 2, or 4 s.

### 7.1 Signed displacement

$$
\Delta\mathbf p_a(t;w)=\widetilde{\mathbf p}_n-\widetilde{\mathbf p}_0
=[\Delta x_a,\Delta y_a].
$$

Store `delta_x_m = Δx_a` and `delta_y_m = Δy_a` in metres. Values are unbounded in principle and reversible: start plus the vector gives the endpoint. Positive/negative values mean right/left and up/down on the canonical pitch, not toward/away from goal. Mean velocity is a derived view $\Delta\mathbf p_a/w$ and is not stored as a separate v1 feature.

### 7.2 Path length

$$
P_a(t;w)=\sum_{i=1}^{n}\left\|\widetilde{\mathbf p}_i-\widetilde{\mathbf p}_{i-1}\right\|_2.
$$

Store `path_length_m = P_a` in metres. Summation is chronological in `Float64` over every consecutive smoothed native-frequency position, including both window endpoints. $P_a\ge0$. It captures ground travelled even if the attacker curves or returns, but it is sensitive to sampling and residual coordinate noise. Mean speed $P_a/w$ is derived, not a separate feature.

### 7.3 Straightness

Let net displacement magnitude be

$$
D_a(t;w)=\sqrt{\Delta x_a^2+\Delta y_a^2}.
$$

Define

$$
S_a(t;w)=
\begin{cases}
D_a/P_a,&P_a>0,\\
\text{undefined},&P_a=0.
\end{cases}
$$

Store `straightness` as dimensionless `Float64` and `straightness_valid` as Boolean. For positive path, numerical tolerance aside, $S_a\in[0,1]$. If `path_length_m == 0.0` exactly, store `straightness = null` and `straightness_valid = false`. Otherwise store the unrounded ratio and `true`. Values within $10^{-12}$ of 0 or 1 are retained unrounded; values outside $[-10^{-12},1+10^{-12}]$ fail hard QC rather than being clipped.

Straightness near one means travel was direct between endpoints; a low value means substantial path relative to net relocation, which may reflect curvature, an out-and-back movement, or wandering. It does not distinguish those causes and does not measure movement quality.

## 8. Low-motion and stationary behavior

No valid row is removed for low speed, low path, or zero displacement.

- If every smoothed position is exactly equal, displacement components and path are `0.0`; straightness is null with `straightness_valid == false`.
- If displacement magnitude is zero but path is positive, straightness is exactly `0.0` subject to ordinary floating arithmetic.
- Near-zero positive path receives the ordinary ratio; no low-speed/path threshold is introduced. Such rows are counted in boundary diagnostics and may expose numerical instability.
- Heading is not a v1 feature, so undefined heading requires no imputation.
- Exact zeros, straightness nulls, and values near mathematical limits are reported descriptively by player, team, period, and window.

Stationarity may later be football-relevant, but v1 does not call it holding, occupying, pinning, or successful off-ball play.

## 9. Eligibility for one observation

An observation at $(player,t,w)$ is eligible only if:

1. the player is an eligible rostered outfielder;
2. $t$ is on the exact period grid and $t-w$ is in the same period;
3. every raw sample needed for every smoothed position from $t-w$ through $t$ is valid under Sections 4–5;
4. all smoothed positions from $t-w$ through $t$ exist at consecutive 0.04 s timestamps;
5. no sample or smoothing support crosses a period, entry/exit, missingness, identity-registry, coordinate, frame, or time discontinuity; and
6. all three feature families can be calculated according to Section 7 (straightness may be explicitly undefined only under its governed zero-path rule).

There is no partial-window calculation. Eligibility is computed independently for 1, 2, and 4 s; a row eligible at one duration need not be eligible at another. The primary table contains 2 s rows. Sensitivity tables retain their own exact identities. Stable observation ID is `match_id|period|frame_id_provider|player_key|window_ms`.

## 10. Interpretability standard

| Observable | Pitch visualization | Plain football meaning | High value | Low value | Important failure mode | Prohibited interpretation |
|---|---|---|---|---|---|---|
| Signed x/y displacement | Arrow from window start to end | Where the player finished relative to where they began | Large component: substantial movement along that fixed pitch axis | Near zero: little net change on that axis | Out-and-back movement cancels | Direction of attack, intent, threat, or success |
| Path length | Player trail with its small steps summed | How much ground the player covered | More travelled distance | Little travelled distance | Residual jitter inflates distance | Work rate, tactical value, or defensive influence |
| Straightness | Chord divided by drawn trail | How directly the path connected start and end | Direct path | Curved, returning, or wandering path | Different shapes share the same ratio; short paths can be unstable | Run type, quality, deception, or purpose |

Every variable can be drawn on the pitch and explained without a statistical model. None is a tactical label.

## 11. Frozen 25 Hz versus 10 Hz sensitivity

This test measures representation-frequency sensitivity on the same Game 1 physical trace; it does not claim full equivalence to a native 10 Hz provider.

For each maximal valid seven-frame-smoothed 25 Hz player-period run:

1. retain the primary 25 Hz smoothed positions;
2. create target times on a 0.10 s grid from the same period origin;
3. when a target is an exact 25 Hz time, use that smoothed position;
4. otherwise linearly interpolate only between the immediately bracketing valid smoothed 25 Hz positions, which are 0.04 s apart and in the same valid run;
5. never interpolate across a raw/smoothed support break or outside support;
6. compute features from consecutive 10 Hz positions over identical physical 1/2/4 s windows; and
7. compare only exact common 0.20 s evaluation endpoints with identical player, period, start, and end times.

The interpolation is confined to this deterministic sensitivity trace. It cannot create primary support, repair missing data, or enter later bridge analysis.

For each window and observable, report common count, unmatched eligible identities on both sides, signed error, absolute error, median, 95th percentile, maximum, and Spearman correlation as supplemental. Relative path error is evaluated only where 25 Hz path is at least 1.0 m; this reporting boundary is frozen and does not exclude primary rows.

All the following gates must pass separately at 1, 2, and 4 s:

| Observable | Frozen pass criteria |
|---|---|
| `delta_x_m` | absolute signed bias ≤0.010 m; median absolute error ≤0.020 m; 95th percentile absolute error ≤0.050 m |
| `delta_y_m` | absolute signed bias ≤0.010 m; median absolute error ≤0.020 m; 95th percentile absolute error ≤0.050 m |
| `path_length_m` | 10 Hz minus 25 Hz bias in [−0.050, +0.010] m; median absolute error ≤0.050 m; 95th percentile absolute error ≤0.150 m; among reference paths ≥1 m, median relative error ≤2.0% and 95th percentile ≤5.0% |
| `straightness` | compare only rows valid on both sides: absolute signed bias ≤0.010; median absolute difference ≤0.015; 95th percentile ≤0.050 |
| Eligibility | at least 99.9% of 25 Hz eligible observation IDs have a matched 10 Hz sensitivity row; every unmatched row must be explained by the deterministic resampling support edge |

Inclusive comparisons apply (`<=`, and inclusive interval endpoints). Quantiles use NumPy's default linear method. Bias is arithmetic mean of `10 Hz − 25 Hz`; absolute signed bias means the absolute value of that mean. Relative error is $|P_{10}-P_{25}|/P_{25}$. No epsilon is added. Null straightness rows are excluded from straightness error denominators and their validity agreement is reported separately; valid/null disagreement fails hard QC.

The displacement tolerances are tied to centimetre-scale coordinate equivalence and a local smoothed path. Path tolerances are wider because coarser sampling shortens curved polylines systematically. Straightness tolerances reflect the bounded ratio. These are prospective engineering/physical-portability gates, not validated football thresholds.

## 12. Geometric invariance and equivariance

Fixtures must verify to absolute tolerance $10^{-12}$ unless a fixture specifies otherwise:

| Transformation | Displacement x/y | Path | Straightness |
|---|---|---|---|
| Rigid coordinate translation / axis-origin shift | unchanged | unchanged | unchanged |
| Rotation by angle $\phi$ | vector rotates by the same rotation matrix; components need not remain equal | unchanged | unchanged |
| Mirror x or y | mirrored component changes sign; other component unchanged | unchanged | unchanged |
| Exact path traversal reversal | displacement vector negates | unchanged | unchanged |
| Uniform time-preserving resampling of a straight/affine path | same endpoints and displacement | unchanged analytically | unchanged |
| Uniform time-preserving resampling of a curved path | same endpoints and displacement | polygonal path may shorten at lower frequency and is governed by Section 11 | may change correspondingly |

Signed components are intentionally not rotation- or mirror-invariant. Smoothing must commute with translation, rotation, and reflection on complete support to numerical tolerance.

## 13. Frozen synthetic fixtures

Geometry-kernel fixtures use exact `Float64` positions at 25 Hz over $t\in[0,2]$ s, with 51 positions and 50 steps, unless stated otherwise. They enter the feature kernel as already smoothed positions so formulas can be tested independently. A separate smoothing fixture applies the seven-frame mean to each trace and verifies the 3+3 edge loss and affine-path preservation. Default exact-value tolerance is $10^{-12}$; curved polygonal paths use $10^{-10}$.

| Fixture | Coordinate rule | Expected 2 s output / support |
|---|---|---|
| Stationary | $p(t)=(1,2)$ | $\Delta=(0,0)$ m; $P=0$ m; straightness null/invalid |
| Straight constant speed | $p(t)=(2t,0)$ | $\Delta=(4,0)$ m; $P=4$ m; $S=1$ |
| Straight acceleration | $p(t)=(0.5t^2,0)$ | $\Delta=(2,0)$ m; $P=2$ m; $S=1$ |
| Gradual quarter-circle | $p(t)=(2\sin(\pi t/4),2[1-\cos(\pi t/4)])$ | $\Delta=(2,2)$ m; $P=200\sin(\pi/200)$ m; $S=\sqrt8/P$ |
| Sharp cut | $p(t)=(t,0)$ for $t\le1$; $(1,t-1)$ afterward | $\Delta=(1,1)$ m; $P=2$ m; $S=\sqrt2/2$ |
| Out and back | $p(t)=(t,0)$ for $t\le1$; $(2-t,0)$ afterward | $\Delta=(0,0)$ m; $P=2$ m; $S=0$ valid |
| Low-speed drift | $p(t)=(0,0.1t)$ | $\Delta=(0,0.2)$ m; $P=0.2$ m; $S=1$ |
| Stop then restart | $x=t$ to 0.75 s; $x=0.75$ through 1.25 s; $x=t-0.5$ afterward; $y=0$ | $\Delta=(1.5,0)$ m; $P=1.5$ m; $S=1$ |
| Support break | straight path with raw coordinate null at $t=1.00$ s | raw run splits; every smoothed/window row whose support touches the break is ineligible; no interpolation |
| Frequency-equivalent path | straight $p(t)=(1.5t,-0.5t)$ evaluated through governed 25/10 Hz paths | identical $\Delta=(3,-1)$ m, $P=\sqrt{10}$ m, $S=1$; all frequency errors zero within $10^{-12}$ |

Additional fixture assertions cover exact 1 s and 4 s window step counts, 0.20 s grid alignment, period reset, no cross-period window, stable observation IDs, translation/rotation/reflection/reversal behavior, zero-path null handling, no clipping, and a deliberately invalid duplicate row that must fail QC. Fixtures validate geometry and implementation, not football semantics.

## 14. Football thought tests

| Observed football movement | V1 description | Remaining ambiguity |
|---|---|---|
| Straight run with brief slowdown | large directed displacement/path and straightness near one | slowdown is not retained |
| Straight accelerating run | same geometric summary as steady travel with the same sampled path | acceleration is intentionally absent |
| Gradual curved run | path exceeds net displacement; straightness falls | curvature location and direction are not identified |
| Sharp cut | signed endpoint remains visible; path exceeds displacement and straightness falls | cut time and angle are not identified |
| Stop/restart | path and endpoint remain visible | stop duration is not distinguished from slower travel on the same path |
| Low-speed lateral drift | small signed y displacement and path are retained | no tactical meaning follows from drifting |
| Holding width almost stationary | near-zero displacement/path; straightness may be undefined | holding and tracking error look identical geometrically |
| Check toward ball then spin away | path can be substantial while net displacement/straightness are low | ball relation and two legs are not identified |
| Long wandering path | high path with low straightness | different wandering shapes can share the summary |
| Repeated small stride adjustments | usually similar endpoint, with possible modest path inflation | residual tracking noise and real adjustment are not separated |

The ambiguity is a deliberate cost of minimality. V1 must not recover missing detail by adding post-outcome labels.

## 15. Game 1 descriptive sanity checks

Execution must report, separately for each window:

- candidate grid rows, eligible rows, and exclusion counts by reason;
- coverage by player, team, and period;
- uniqueness of observation IDs and duplicate input rows;
- distributions and min/max/mean/median/IQR/1st/99th percentiles for every feature;
- exact-zero displacement components, zero displacement magnitude, zero path, null straightness, and straightness at/near 0 and 1;
- nonfinite values and values outside mathematical ranges;
- path shorter than displacement beyond $10^{-12}$ m;
- support loss at run, registry, substitution/absence, and period boundaries; and
- concentration summaries by player/team/period, without a football-correctness threshold.

These checks detect implementation errors or degeneracy; they cannot declare a football distribution correct. No observed distribution, visual example, or attractive shape may tune the protocol.

## 16. Hard QC and A/B/C decision

### Hard QC

Hard QC passes only if all are true:

1. canonical schema/time/coordinate validation passes;
2. the frozen registry and support pipeline are applied exactly;
3. input and output identities are unique and deterministic;
4. no ineligible support contributes to any feature;
5. all eligible displacement/path values are finite, path is nonnegative, and path is not shorter than displacement beyond $10^{-12}$ m;
6. straightness null/valid behavior and range are exact;
7. all synthetic, smoothing, grid, and invariance fixtures pass;
8. a clean independent rerun reproduces governed CSV/JSON scientific outputs byte-for-byte; the manifest comparison may exclude only `run_timestamp_utc`, `repository_root`, and absolute `input_paths`, while hashes, relative identities, parameters, counts, gates, and results remain exact;
9. source, protocol, dependency, canonical-contract, adapter, trajectory-registry, and input hashes are recorded; and
10. no prohibited data source or post-output parameter change occurred.

### Classification

- **A — qualifies for held-out evaluation:** hard QC passes; every 25/10 Hz gate in Section 11 passes at all three frozen windows; and the descriptive sanity report reveals no violation of a mathematical/support invariant. Game 2 may then receive a separately frozen held-out protocol.
- **B — interpretable but not portable enough:** hard QC passes and the representation remains computable under its definitions, but at least one Section 11 frequency gate fails. Stop; do not open Game 2.
- **C — invalid implementation/construct realization:** any hard-QC item fails, any fixture fails, any supported primary feature is undefined outside the explicitly allowed zero-path straightness case, deterministic reproduction fails, or a mathematical/support contradiction occurs. Stop; do not open Game 2.

Descriptive player/team/period distributions do not by themselves move A to B or C. If they expose a hard invariant violation, classification is C under the corresponding hard-QC rule. There is no subjective visual override, tactical-label gate, or defensive-outcome criterion. Inclusive tolerance boundaries pass.

## 17. Planned attacker-to-defender bridge — design only

After attacker-side Game 1 A and a successful held-out representation protocol, a separate prospective bridge may ask:

> Is an attacker's recent observed geometry over $[t-w,t]$ associated with a defender's subsequent individual movement relative to the defensive unit over $[t,t+h]$?

The attacker window must contain no information after $t$. Candidate future response horizons for later consideration are **1, 2, and 4 s**; none is selected or frozen here, and they must not be chosen from current defensive outcomes. Candidate defender outputs are the validated focal-relative path plus signed focal-relative x/y displacement, kept separate.

A later protocol must handle defender recent motion, collective shift, ball movement, attacker-defender proximity, possession context, overlapping observations, multiple attackers/defenders, pairing logic, and within-match dependence. Temporal ordering supports association, not causation. This protocol neither selects focal defenders nor executes the bridge.

## 18. Claims and held-out discipline

After this freeze it is permissible to say:

> A continuous attacker-only geometric representation has been prospectively defined for observed movement over fixed local time windows.

It is also permissible to say:

> The representation preserves signed displacement, distance travelled, and a directness view of path shape without imposing universal attacking-movement episode boundaries.

It is not yet permissible to say the representation is validated, provider-portable, tactically meaningful, or associated with defensive behavior. It does not identify a tactical run, movement episode, decoy, pin, drag, track, cover, handoff, successful movement, defensive response, opponent association, causation, attacking value, gravity, or off-ball value.

Game 1 is development. **Game 2 may be opened for attacker representation only if Game 1 receives A under this exact frozen protocol. If Game 1 is B or C, Game 2 remains closed. Game 3 remains closed regardless.** No window, grid, support rule, smoother, formula, tolerance, fixture, or classification rule may change after Game 1 output under v1.0. A correction discovered before execution must be documented as a pre-execution erratum; after execution, a scientific change requires a new protocol version.

## 19. Pre-execution ambiguity resolution

The freeze resolves the implementation choices most likely to diverge: endpoint inclusion, native step counts, arithmetic smoothing, edge loss, support order, registry, exact grid origin/tolerance, period reset, no nearest-frame fallback, path summation order, zero-path straightness, float precision, 10 Hz interpolation scope, matched identities, error signs, quantile method, inclusive gates, relative-error denominator, null comparison, stable IDs, and rerun hashing policy.

Two competent implementations must produce the same observation identities and values subject only to the explicit numerical tolerances above. If implementation discovers an unlisted case capable of changing scientific rows, features, or classification, execution must stop before Game 1 outputs and the protocol must be clarified prospectively.
