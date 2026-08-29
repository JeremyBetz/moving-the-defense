# Phase 5A Contextual-Expectation Feasibility Protocol

> **Status: protocol v1.0 frozen before execution.** No model has been fitted, no target/model performance or residual has been inspected, and no feature has been selected from outcome association. Any substantive change now requires a versioned pre-execution amendment.

## 1. Scope and research question

Phase 5A asks:

> **To what extent can focal-relative path over the next five seconds be predicted from observable pre-interval movement and spatial context?**

This is contextual-expectation feasibility only. It moves from replicated individual-versus-collective geometry toward an expected geometric baseline; it does not establish tactical defensive response, contextual correctness, attacker influence, or value.

## 2. Data and validation unit

- **IDSSE/DFL:** the only Phase 5A development/evaluation environment; seven matches.
- **Metrica Games 1/2:** prior construct history; excluded from model fitting and evaluation.
- **Metrica Game 3:** not inspected and outside Phase 5A.
- **Independent evaluation unit:** match. Outer validation leaves one complete match out, trains on six, and evaluates once on the seventh.

## 3. Prediction cutoff and unchanged Phase 4 target

IDSSE tracking is sampled every $\Delta=0.04$ s. Let $s$ be the first raw tracking timestamp in an eligible Phase 4 interval. The validated target consumes exactly the 125 raw coordinates

$$
R=\{s+k\Delta:k=0,\ldots,124\}=\{s,\ldots,s+4.96\}.
$$

For focal defender $d$ and the fixed complete target-interval set $O_d$ of the other defending outfield players,

$$
\mathbf r_d(u)=\mathbf x_d(u)-\frac{1}{|O_d|}\sum_{j\in O_d}\mathbf x_j(u).
$$

The focal defender and goalkeeper are excluded from $O_d$. The implementation applies a centered seven-frame rolling mean with a complete-window requirement **inside these 125 raw interval frames**. Therefore:

- nominal raw target frames: $s$ through $s+4.96$ (125 frames);
- valid smoothed-coordinate timestamps: $s+0.12$ through $s+4.84$ (119 frames);
- raw support for those smoothed coordinates: $s$ through $s+4.96$;
- earliest raw target support: $s$;
- latest raw target support: $s+4.96$;
- accumulated target path: 118 Euclidean increments between the 119 valid smoothed coordinates.

Thus centered smoothing extends three raw frames before/after the valid smoothed-coordinate timestamps, but the validated implementation does **not** consume raw observations outside the nominal 125-frame interval. Phase 5A preserves that exact target rather than changing to causal smoothing.

Define the prediction cutoff

$$
c=s-\Delta=s-0.04\text{ s}.
$$

This is the nearest valid frame immediately before raw target support. The first valid smoothed path position occurs at $c+0.16$ s, while the target's raw support begins at $c+0.04$ s. Every observation must satisfy the raw-support firewall

$$
\texttt{feature\_max\_raw\_time}\le c < \texttt{target\_min\_raw\_support\_time}=s.
$$

The implementation must additionally assert the exact 25 Hz relationships `target_min_raw_support_time - prediction_cutoff == 0.04 s`, `target_max_raw_support_time - prediction_cutoff == 5.00 s`, 125 raw frames, 119 valid smoothed positions, and 118 path increments, within a frozen timestamp tolerance. Failure stops execution before fitting.

## 4. Retrospective estimand and eligibility

Phase 5A estimates the conditional expectation of five-second focal-relative path **among observations that retrospectively satisfy the frozen Phase 4-compatible uninterrupted target eligibility and have complete pre-cutoff B4 context**. Future target completeness, open-play, possession, restart, set-piece, ball-out, fixed defending-team, and fixed target-reference requirements may determine whether the validated target exists.

This is a retrospective prediction/evaluation design, not an online forecast available from information at $c$ alone. Future eligibility variables are sample selectors only and are never predictors. History eligibility, completeness, and reference membership use only data at or before $c$. Prospective deployability would require a separate estimand and protocol.

## 5. Causal history, construction order, and common sample

- Primary history: exactly 50 raw frames $c-1.96,c-1.92,\ldots,c$—50 observations in the immediately preceding 2.0-second sampling window.
- Frozen sensitivity: exactly 25 raw frames $c-0.96,c-0.92,\ldots,c$—25 observations in the immediately preceding 1.0-second sampling window.
- Predictor smoothing: trailing seven-frame mean ending no later than $c$.
- Terminal velocity: backward difference of consecutive trailing-smoothed positions divided by 0.04 s.
- No centered predictor smoothing, interpolation, future-informed imputation, or acceleration.

The 50-frame history yields 44 valid trailing-smoothed positions and 43 path increments. The 25-frame sensitivity yields 19 valid trailing-smoothed positions and 18 increments. The first valid smoothed position is always the seventh raw frame. No padding occurs. Exact raw/smoothed/increment counts are pre-fit assertions.

History feature order is frozen:

1. select the exact complete raw history frames and history membership;
2. transform raw player and ball coordinates into standardized defending orientation;
3. form the raw leave-one-out centroid at each frame from the fixed eligible other-defender membership;
4. independently apply the complete trailing seven-frame mean to focal, centroid, other-defender, and ball coordinate series;
5. form smoothed focal-relative coordinates as smoothed focal minus smoothed leave-one-out centroid; and
6. calculate paths and terminal velocities from the resulting smoothed series.

With fixed complete membership, smoothing defenders before averaging would be algebraically equivalent, but the implementation must use raw-centroid-then-smooth. Terminal velocity uses the final two smoothed coordinates.

History membership is fixed at cutoff $c$. Eligible history defenders are players identified as non-goalkeepers and on the defending team at $c$, with finite coordinates at every raw frame in the selected history. The focal must also be complete. The leave-one-out reference excludes the focal and goalkeeper and requires at least eight eligible other outfield defenders; otherwise the focal observation is history-incomplete. Membership uses only roster/role/substitution information timestamped at or before $c$, never future substitutions or target completeness. Store history and target membership separately and report differences; target membership cannot be back-propagated into predictors.

All direct B0–B4 comparisons use the same B4-complete focal observations inside each outer fold. Prospectively report by match and defending team:

1. Phase 4-eligible focal observations;
2. observations with complete 2-second history;
3. observations with complete required ball history;
4. final B4-complete observations; and
5. B4 retention percentage relative to Phase 4 eligibility; and
6. final common-comparison observations.

Report this chain by match, defending team, and overall. Attrition is a diagnostic and cannot be hidden by level-specific performance summaries.

## 6. Standardized defending coordinates

Provider metric coordinates are centered on a 105 by 68 m pitch: $x_p\in[-52.5,52.5]$, $y_p\in[-34,34]$. For each defending team-period, let $\sigma=+1$ when its own goal is at provider $x=-52.5$ and $\sigma=-1$ when its own goal is at provider $x=+52.5$. Transform every player and the ball identically:

$$
x_D=\sigma x_p+52.5,\qquad y_D=\sigma y_p+34.
$$

Own-goal center is then $(0,34)$, opponent-goal center $(105,34)$, and pitch center $(52.5,34)$. For $\sigma=-1$ this is a 180-degree rotation plus translation, preserving handedness relative to the defending direction.

Direction comes from provider kickoff/team-period metadata or equivalent known geometric orientation independent of the future target. If no explicit field exists, use the defending goalkeeper's median provider x during the first two seconds of the period, fixed before any candidate prediction and never revisited. No target-window movement or outcome may determine orientation.

## 7. Frozen B0–B4 feature ladder

All feature support ends at $c$. IDs remain audit/split fields only.

“Current” B3/B4 positions and distances use the transformed **raw** coordinates at $c$. History paths and terminal velocities use the transformed, causally smoothed history series defined above. Thus smoothing is not silently substituted for current spatial context.

### B0 — unconditional

Prediction is the median target among the six outer-training matches on the common sample.

### B1 — focal recent motion

- `focal_recent_absolute_path_m`
- `focal_recent_relative_path_m` (focal minus contemporaneous history-only leave-one-out centroid)
- `focal_terminal_vx_mps`, `focal_terminal_vy_mps`
- `focal_relative_terminal_vx_mps`, `focal_relative_terminal_vy_mps`

No acceleration enters the primary specification.

### B2 — collective defensive motion

Retain B1 and add:

- `loo_centroid_recent_path_m`
- `loo_centroid_terminal_vx_mps`, `loo_centroid_terminal_vy_mps`
- `other_defenders_recent_mean_path_m`: mean individual absolute history path across valid other defending outfield players.

The aggregate excludes the focal defender and goalkeeper. Mean, not sum, prevents player-count variation from mechanically changing activity.

Precisely, if $P_j$ is the causally smoothed absolute path of eligible other defender $j$ and $m\ge8$ is the fixed reference-set size, `other_defenders_recent_mean_path_m` is $m^{-1}\sum_{j=1}^mP_j$. Units are metres per player over the history window. It is neither a sum nor divided by a nominal player count.

### B3 — ball context

Retain B2 and add:

- `ball_x_m`, `ball_y_m` at $c$ in standardized defending coordinates;
- `ball_terminal_vx_mps`, `ball_terminal_vy_mps`;
- `ball_recent_path_m`;
- `focal_minus_ball_x_m`, `focal_minus_ball_y_m`;
- `focal_ball_distance_m`.

Ball-history quantities must be causally complete; no interpolation is allowed.

### B4 — simple spatial/goal context

Retain B3 and add:

- `focal_own_goal_depth_m` (also the focal standardized x coordinate; a duplicate `focal_x_m` alias is omitted);
- `focal_y_m`;
- `focal_own_goal_distance_m`;
- `focal_lateral_distance_m = abs(focal_y_m - 34)`;
- `ball_lateral_distance_m = abs(ball_y_m - 34)`.

Ball longitudinal depth is already represented exactly by B3 `ball_x_m`, so a duplicate ball-depth alias is omitted. Ball standardized y is likewise already B3 `ball_y_m`. This retains focal x/y, focal goal distance/depth/lateral position, and ball depth/lateral position without exact duplicate columns.

Exact B4 definitions at cutoff $c$, all in the standardized defending frame, are:

| Feature | Formula | Units | Signed? |
|---|---|---:|---|
| `focal_own_goal_depth_m` | $x_{D,d}(c)$ | m | nonnegative pitch coordinate; longitudinal depth from own goal |
| `focal_y_m` | $y_{D,d}(c)$ | m | nonnegative pitch coordinate; retains standardized lateral side |
| `focal_own_goal_distance_m` | $\sqrt{x_{D,d}(c)^2+[y_{D,d}(c)-34]^2}$ | m | nonnegative Euclidean distance |
| `focal_lateral_distance_m` | $|y_{D,d}(c)-34|$ | m | nonnegative absolute lateral distance |
| `ball_lateral_distance_m` | $|y_{D,b}(c)-34|$ | m | nonnegative absolute lateral distance |

`ball_x_m` in B3 is the ball's longitudinal own-goal depth and is not repeated. These are the only B4 additions.

Excluded throughout: opponents; local teammate geometry; IDs as predictors; inferred roles; score; future events; assignments; outcome-derived features; target eligibility indicators.

## 8. Model, preprocessing, and nested validation

- B0: training median.
- B1–B4: Ridge regression with intercept.
- Alpha grid: $\{0.01,0.1,1,10,100\}$.
- Outer loop: seven leave-one-match-out folds.
- Inner loop: leave one of the six outer-training matches out in turn.
- Preprocessing inside every inner split: means/standard deviations and constant-feature removal fit on the five inner-training matches only, then applied to the inner-heldout match.
- Alpha selection: lowest **median** MAE across the six inner-heldout matches. Alphas within $10^{-6}$ m of the minimum are tied; choose the larger alpha.
- Refit: after selecting alpha, refit preprocessing and Ridge on all six outer-training matches and test once on the seventh.
- Outer-test data never affect scaling, feature removal, alpha, or model selection.
- No outcome transformation, per-player/team baseline, clipping, OLS fallback, target-derived feature selection, or outer-test tuning.

Each inner or outer fitted pipeline independently identifies constant columns from its own training observations. A column removed in one split may remain in another; the fitted column mask and scaling parameters are applied unchanged to that split's validation/test observations and logged. The target is never scaled.

Negative predictions are retained and reported as misspecification diagnostics.

## 9. Metrics and calibration

Primary: held-out MAE per match. Secondary: held-out median absolute error, RMSE, $R^2$, prediction/error distributions, and all seven match results with median, range, and IQR. Pooled metrics cannot override match disagreement.

For calibration in each outer fold, use the selected-alpha predictions produced when each of the six outer-training matches served as the inner-heldout match (each prediction therefore comes from the other five matches with inner-training-only preprocessing). Concatenate these training-side cross-fitted predictions and define five bins using linear empirical quantiles at 0%, 20%, 40%, 60%, 80%, and 100%. Freeze the edges and apply them to the outer-heldout predictions. If edges repeat, collapse duplicates and report fewer than five realized bins rather than perturbing them. Outer outcomes never define bins. Report held-out predicted-versus-observed mean/median by bin and descriptive calibration intercept/slope when estimable. Calibration is descriptive and does not enter A/B/C classification.

The **contextual departure residual** $e=Y-\widehat Y$ means more or less focal-relative path than predicted by the current model: positive is more and negative is less. It is not defensive response, adjustment, tactical surprise, attacker effect, gravity, or value. Report residual associations with pre-cutoff focal, collective, ball, spatial, prediction, match, team, and player context; do not repair them automatically.

Evidence remains hierarchical: frames $\subset$ intervals $\subset$ sequences $\subset$ players $\subset$ teams $\subset$ matches. Primary conclusions use the seven outer-heldout matches. Interval abundance or interval-level significance cannot override match disagreement.

## 10. Frozen decision rules

Relative MAE reduction for a model against a reference is calculated separately within each outer-heldout match, then summarized by its median across seven matches.

### Adjacent materiality

An adjacent step is material when median relative MAE reduction is at least 3%, at least five of seven matches improve, and no more than one match worsens by at least 10%.

### Best simple model

The best simple B1–B4 model has the lowest median outer-heldout MAE. Models within $10^{-6}$ m of the minimum are tied; choose the earliest ladder level.

### Phase 5A A/B/C

Apply the mutually exclusive rules in order A, then C, then B:

- **A — contextual expectation feasible:** at least one B1–B4 model reduces median MAE by at least 10% versus B0, improves at least six of seven matches, and no more than one match worsens by at least 10%.
- **C — simple contextual expectation insufficient:** no B1–B4 model reduces median MAE by at least 3% versus B0 **and** no B1–B4 model improves at least four of seven matches.
- **B — partial/mixed:** every valid result that is neither A nor C.

If A occurs, the strongest supported claim is only: **future focal-relative path contains reproducibly predictable structure from pre-interval observable context.** No class validates tactical meaning.

Category A does not mean B4 wins. If B1 contains nearly all useful information, A can still hold and the conservative interpretation is that future focal-relative path is predictably structured primarily by the focal defender's own recent motion. Any incremental B2–B4 gain describes predictive structure, not causal importance.

Allowed decomposition language is limited to frozen material adjacent steps: B1 dominance means most useful information in the tested ladder was already in focal recent movement; material B2, B3, or B4 steps mean respectively that recent collective motion, ball context, or simple spatial context added reproducible predictive information beyond the preceding ladder. None implies causal importance.

## 11. Complexity gate

No nonlinear challenger is fitted in Phase 5A. A later prospectively specified challenger must beat the **best simple model** by at least 5% median held-out MAE, improve at least five of seven matches, worsen at least 10% in no more than one match, and supply a meaningful scientific gain or resolve a prospectively named residual failure. It cannot be admitted merely for a small predictive gain.

## 12. Leakage, identity, and change control

Before fitting, mechanically verify raw-time support, causal smoothing, history-only reference selection, common-sample identity, no target-derived eligibility predictor, no ID predictor, training-only preprocessing, and exact outer/inner match separation. Any failure stops execution.

Outcome-blind implementation clarifications may cover provider field names, frozen timestamp tolerance, deterministic record ordering, output schema, software versions, or computational batching. Any change to target/support, cutoff, histories, features, missingness, direction, model/grid/ties, folds, preprocessing, calibration, metrics, or decision rules requires a versioned amendment before target/performance inspection.

## 13. Deferred methods and nonclaims

Deferred: opponent/local geometry, nonlinear/graph/neural models, full trajectory forecasting, ADE/FDE, tactical counterfactuals, Metrica transport, player/team effects, and value models.

Phase 5A does not validate a correct tactical position, a correct defender trajectory, tactical defensive response, contextual correctness, responsibility, decision-making, attention, pinning, dragging, tracking, covering, handoffs, relational reconfiguration, attacker association, attribution, attacker causation, defensive quality, gravity, or off-ball value. **Statistically expected is not tactically expected. Prediction residual is not tactical error. Unexpected focal departure is not attacker-induced response. Prediction is not causation; residual is not tactical meaning.**

## 14. Freeze record

Protocol v1.0 is frozen before execution. Protocol-only QC confirmed the unchanged Phase 4 target support, exact discrete history support and smoothing counts, feature/config agreement, raw-time firewall, membership separation, nested match splits, decision-rule precedence, links, math, and JSON validity. No target construction, model fitting, performance inspection, residual calculation, or Metrica Game 3 access occurred. Execution requires a separate task after this frozen protocol is committed.
