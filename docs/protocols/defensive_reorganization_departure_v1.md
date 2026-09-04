# Defensive Reorganization Departure v1

**Status:** frozen prospectively before any DRD prediction result

**Freeze date:** 2026-09-04

**Starting commit:** `00116e83c195cfeb4719261a42f22b25ea7f02b5`

**Execution policy:** Tier 2 development under
[the project execution policy](../execution_policy.md); any later external
SkillCorner execution requires a separately frozen Tier 3 protocol.

## 1. Question, use, and boundary

> Can a compact set of predeclared movement and starting-geometry features
> materially improve heldout prediction of anchor-level localized defensive
> reorganization beyond attacker movement alone?

The application use is passage retrieval: surface off-ball attacking movements
followed by more localized defender-relative movement than a compact statistical
model expected from comparable movement and starting geometry.

The observable remains geometry. This protocol cannot establish causation,
influence, attention, marking, assignment, responsibility, tactical response,
disruption, success, defensive quality, player quality, gravity, or off-ball
value. A statistical expectation is not a tactically correct trajectory, and a
residual is not tactical error.

## 2. Data and unit

The primary development environment is exactly the seven governed IDSSE/Sportec
matches `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, and
`J03WR9`. Use the validated canonical IDSSE adapter and the closed Spatial
Defensive-Response Footprint v1 observation registry as the target/rank source.
Metrica Sample Game 3 is prohibited.

One row is one eligible `(provider, match, period, anchor time, focal attacking
outfield player)` with one complete start-fixed D1–D10 defender vector.
Simultaneous focal attackers are distinct observations but share an anchor-level
defensive state. They remain together in every block bootstrap and passage
selection operation. Match, period, time, player, team, and anchor IDs are
audit/split fields only; none is a model feature.

## 3. Timing, support, and off-ball eligibility

Inherit the validated 25 Hz IDSSE timing and seven-frame centred, complete-window
position mean:

- strictly prior context: `[t-4,t-2]` seconds;
- attacker movement/exposure: `[t-2,t]` seconds;
- defensive response: `[t,t+2]` seconds;
- anchor grid: period origin plus `4 + 4k` seconds; and
- no interpolation, padding, partial windows, restart crossing, ball-out
  crossing, unsupported gap, or period crossing.

At `t`, the event clock must identify the attacking team and open play must be
valid throughout `[t-4,t+2]`. Possession after `t` is not required. The focal
attacker must be an attacking outfield player with complete required support.
All ten defending outfield players must have complete raw and smoothed support
for the inherited target. Goalkeepers are excluded. Ball coordinates must be
complete at every 0.04-second frame from `t-2.12` through `t+0.12` (57 raw
frames), yielding centred-smoothed ball coordinates from `t-2` through `t`.
The focal attacker must be complete from `t-4.12` through `t+0.12` (107 raw
frames), yielding the two consecutive 51-position path windows. All ten
attacking outfield players must have complete seven-frame support from `t-0.12`
through `t+0.12` so the off-ball proxy is defined.

### Frozen operational off-ball rule

Player-level ball-carrier identity is not reliably supplied by the governed
IDSSE tracking/event mapping. An event-defined carrier would also be unavailable
at most fixed anchors, while a ball-distance cutoff would add an unvalidated
provider-sensitive threshold. The least assumption-heavy common rule is
therefore geometric and threshold-free:

1. at `t`, calculate each attacking outfield player's Euclidean distance to the
   centred-smoothed ball coordinate;
2. select the unique nearest attacker, breaking an exact tie by ascending
   canonical player key; and
3. exclude that one attacker from focal eligibility. The other nine attacking
   outfield players are operationally eligible.

This rule means **not the ball-nearest attacking outfielder at the anchor**. It
does not identify the actual ball carrier, guarantee that the focal player is
uninvolved with the ball throughout `[t-2,t]`, or label a tactical off-ball run.
No distance threshold, receipt, pass, shot, xG, later possession outcome, or
defensive response enters eligibility.

## 4. Outcome

For defender proximity rank `k`, let `P_ik` be the validated accumulated
leave-one-out defender-relative path in metres over `[t,t+2]`. Ranks are fixed
once at `t` by Euclidean focal-attacker–defender distance, with ascending
canonical defender key resolving an exact tie. Define

$$
N_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik},\qquad
M_i=\frac{1}{4}\sum_{k=4}^{7}P_{ik},\qquad
Y_i=N_i-M_i.
$$

`Y`, `N`, and `M` are in metres. `Y` is the direct anchor-level observed
near-minus-middle response, not a fitted match/rank coefficient. D8–D10 remain
outside the target. Retain `N` and `M` beside `Y` because the same contrast can
arise through different component geometries.

## 5. Coordinate and feature construction

All coordinates remain canonical metres on a 105 by 68 m pitch centred at
`(0,0)`. The governed period registry supplies `s_x=+1` when the attacking team
moves toward canonical `+x` and `s_x=-1` otherwise. First rotate every player
and the ball by 180 degrees when `s_x=-1`, so positive x is goalward. Then mirror
the lateral coordinate for the complete anchor using the focal attacker's
movement-start coordinate: the focal player's transformed y at `t-2` is made
nonnegative. An exact centre-line start uses the unreflected `+y` convention.
Consequently positive signed lateral displacement is outward from the centre
line and negative is inward. The identical rigid transform is applied to the
attacker, ball, and defenders; Euclidean distances and paths are unchanged.

Paths use centred seven-frame smoothed coordinates, full raw edge support, and
the established sum of consecutive Euclidean increments. Endpoint displacement
uses the corresponding smoothed positions at `t-2` and `t`. Start geometry is
measured at `t-2`. Defending-unit width/depth use the ten defending outfield
players at `t-2`; the defensive centroid is their arithmetic mean.

### E0 — movement-only expectation

E0 contains exactly:

1. `attacker_path_exposure_m`: focal path over `[t-2,t]`;
2. `attacker_path_prior_m`: focal path over `[t-4,t-2]`.

There are no match/team/player indicators, defensive-motion covariates, ball
features, or tactical labels. The intercept is unpenalized.

### E1 — full context

E1 contains E0 plus exactly three families.

**A. Movement direction**

1. `attacker_goalward_displacement_m`: signed goalward displacement over
   `[t-2,t]`;
2. `attacker_outward_displacement_m`: signed outward/inward lateral
   displacement over `[t-2,t]`.

**B. Start position relative to the defensive unit**

1. `attacker_minus_unit_goalward_m` at `t-2`;
2. `attacker_minus_unit_outward_m` at `t-2`;
3. `defending_unit_depth_m` at `t-2` (`max x - min x`);
4. `defending_unit_width_m` at `t-2` (`max y - min y`).

**C. Ball-relative geometry**

1. `attacker_ball_distance_start_m` at `t-2`;
2. `ball_minus_unit_goalward_m` at `t-2`;
3. `ball_minus_unit_outward_m` at `t-2`;
4. `attacker_ball_distance_change_m`, distance at `t` minus distance at `t-2`.

No interaction, polynomial, categorical run type, normalized geometry,
formation, role, opponent assignment, value feature, or automated feature
selection is allowed. All models and ablations use the identical E1-complete
sample.

## 6. Model and nested validation

Fit Ridge regression with an unpenalized intercept. Standardize each continuous
column from the current training matches only using mean and population standard
deviation (`ddof=0`). Drop a training-zero-variance column from that fitted
pipeline only, apply the same mask to its validation/test rows, and record it.
No target scaling or prediction clipping is allowed.

The fixed alpha grid is `[0.01, 0.1, 1, 10, 100]`. For each of seven outer
leave-one-match-out folds:

1. hold out one complete match;
2. on the remaining six matches, run six inner leave-one-training-match-out
   folds;
3. choose the alpha with lowest equal-match inner heldout MAE;
4. treat alpha MAEs within `0.000001` m as tied and select the largest tied
   alpha; and
5. refit on all six outer-training matches and predict the untouched seventh.

Each of E0, E1, and the three ablations selects alpha independently using only
its current outer-training data. Use the deterministic NumPy closed-form Ridge
solver with an unpenalized intercept. `numpy.linalg.solve` is primary; a
deterministic `numpy.linalg.pinv` fallback with `rcond=1e-15` is permitted only
if recorded. No model-family or hyperparameter search is permitted.

The common sample must retain at least 1,000 observations per match and at
least 90% of the otherwise eligible, threshold-free off-ball footprint rows in
that match. Failure is INVALID; it cannot motivate feature removal or
imputation.

## 7. Metrics and ablations

The primary metric is **equal-match macro heldout MAE in metres**: compute MAE
inside each of seven heldout matches, then take their arithmetic mean. Also
report per-match MAE, observation-weighted MAE, RMSE, median per-match MAE, and
the selected alpha for every outer fold/model.

For baseline `B` and model `A`, relative improvement is

$$
100\frac{MAE_B-MAE_A}{MAE_B}.
$$

Predeclare exactly:

- E0 movement only;
- E1 full context;
- E1 minus movement direction;
- E1 minus start position;
- E1 minus ball geometry.

A context family is **stable** only when, on the identical seven heldout
matches, removing it:

1. satisfies
   `100 * (MAE_ablated - MAE_E1) / MAE_E1 >= 1.0%`;
   and
2. raises per-match MAE in at least 5 of 7 matches.

The family test supports only heldout predictive contribution of that feature
family. It does not establish a mechanism.

## 8. Paired uncertainty

Use the single out-of-fold prediction ledger. Run 1,000 paired hierarchical
bootstrap replicates with seed `20260903`. Resample the seven matches with
replacement; within each selected match, resample period-origin 60-second
anchor blocks with replacement. Preserve all simultaneous attackers and every
row sharing an anchor. Calculate the absolute and relative E1-minus-E0 macro
MAE improvement and corresponding family-ablation improvements with identical
draws. Report two-sided 95% percentile intervals and require at least 950 valid
replicates. These intervals are supporting uncertainty, not an extra success
condition.

## 9. Application-foundation status

Evaluate in this order:

1. **INVALID:** frozen-hash, eligibility, support, common-sample, leakage,
   fold, solver, finite-prediction, bootstrap-minimum, deterministic
   reproduction, or hard-QC failure; any match below 1,000 rows or 90% common
   retention also makes the execution invalid.
2. **NOT SUPPORTED:** valid execution with E1 macro improvement at or below
   zero, or E1 improving no more than 3 of 7 match MAEs.
3. **SUPPORTED:** valid execution satisfying every condition:
   - E1 versus E0 equal-match macro MAE improvement at least 3.0%;
   - E1 improves at least 6 of 7 match MAEs;
   - no match has E1 MAE at least 10.0% worse than E0; and
   - at least one of the three predeclared context families is stable under the
     frozen ablation rule.
4. **MIXED:** every other valid result.

Exactly 10.0% counts as a 10% worsening. Exactly 3.0%, 1.0%, 6/7, and 5/7 meet
their respective inclusive gates. This protocol defines no “strong mixed”
continuation category: only SUPPORTED authorizes DRD retrieval, Metrica
transport, or the SkillCorner compatibility gate.

## 10. DRD and retrieval reliability

Before classification, model residuals are ordinary out-of-fold prediction
errors. If and only if the application foundation is SUPPORTED, define

$$
\operatorname{DRD}_i=Y_i-\widehat Y_{E1,-m(i)}.
$$

Positive DRD means more localized defender-relative movement than the fitted
movement/geometry expectation; negative means less. Only outer-fold predictions
may be called DRD or used for retrieval. No in-sample DRD may be ranked or
displayed.

Before producing the board, run three frozen reliability checks:

1. report per-match residual mean, median, IQR, MAD, calibration intercept, and
   calibration slope;
2. for each heldout match, refit E1 six times, each time omitting one of the six
   outer-training matches while retaining the original outer-fold alpha and
   feature mask logic. A high-positive candidate must remain positive and in
   the within-match top 20% in at least 5 of 6 perturbations. A near-expected
   candidate must remain within the lowest 50% of absolute residuals in at
   least 5 of 6 perturbations; and
3. apply an eight-second nonmaximum-suppression interval within
   `(match, period, focal attacker)`, retaining the larger DRD and then earlier
   time/lexical observation ID on a tie.

The retrieval layer is ready only if at least five of seven matches yield a
complete deterministic pair satisfying these rules. Failure with a SUPPORTED
prediction result preserves the prediction status but withholds the retrieval
board; it cannot trigger revised thresholds.

## 11. Deterministic retrieval board

Construct at most one pair per heldout match.

1. Within each match, assign stable rank-based bins (ties resolved by
   observation ID): attacker-path quintile, start goalward-offset tercile, and
   absolute start lateral-offset tercile.
2. The high-positive pool contains DRD from the inclusive 90th through 99th
   within-match percentiles, after reliability checks and nonmaximum
   suppression. The upper 1% is excluded as an extreme-residual safeguard.
3. The near-expected pool contains rows at or below the within-match 10th
   percentile of absolute DRD.
4. Keep high-positive rows having at least one near-expected row in the same
   three-bin cell. Select the high-positive row nearest the within-match 95th
   DRD percentile; break ties by observation ID.
5. Pair it with the same-cell near-expected row minimizing Euclidean distance
   over attacker path, start goalward offset, and absolute start lateral
   offset after division by the match IQR of each quantity. Omit a zero-IQR
   dimension; break ties by observation ID. Do not relax the cell if no pair
   exists.

Display real pitch geometry, preceding attacker movement, subsequent absolute
and defender-relative D1–D7 movement, `N`, `M`, observed `Y`, expected `Y`, DRD,
model inputs, time, and player ID. Every panel must say: **candidate for analyst
review; tactical meaning not inferred**. No shot, xG, reception, possession
outcome, video attractiveness, or analyst preference may select a passage.

## 12. Conditional Metrica and SkillCorner work

If and only if IDSSE is SUPPORTED and retrieval reliability passes, Metrica
Games 1–2 may receive one nonclassifying transport check. Select alpha for each
model from a seven-fold IDSSE leave-one-match-out macro-MAE evaluation, refit on
all seven IDSSE matches with IDSSE-fitted scaling, and apply the unchanged model
to Metrica Games 1–2. Do not tune on Metrica outcomes. Game 3 remains prohibited.

SkillCorner is not integrated or outcome-tested by this protocol. A later
outcome-blind compatibility gate may begin only after the same IDSSE conditions
pass. It must verify, before any response outcome:

- all ten open-data matches and metadata parse without ambiguous match/team/
  player identities or simultaneous duplicate on-pitch IDs;
- goalkeeper identity and ten-outfield membership are available;
- `is_detected` versus provider-extrapolated support remains explicit;
- ball coordinates and team-possession/event alignment are present;
- native timestamps have exact 10 Hz physical cadence within `1e-6` s and
  reproduce the physical windows without frame-count substitution;
- canonical 105 by 68 m coordinates/orientation reproduce within `1e-5` m;
- each match retains at least 1,000 common prospective rows and at least 80% of
  its threshold-free off-ball base sample;
- no match retention is more than 20 percentage points below overall
  retention;
- extrapolated-coordinate fractions and feature/support attrition are reported
  by match/team rather than hidden; and
- repeated-player/team support is counted before any player-level proposal.

Gate failure means no external application claim. Gate passage only authorizes
a separately frozen external protocol; it does not authorize outcome access or
retuning.

## 13. Stop rule and nonclaims

If IDSSE is MIXED, NOT SUPPORTED, or INVALID, stop the application sprint. Do
not add features, change moderators, change target, alter off-ball eligibility,
change thresholds, use examples to rescue the result, run Metrica transport,
open SkillCorner, or rank players. Return to the validated measurement paper.

Player ranking is prohibited in v1: 132 of 148 governed IDSSE attackers appear
in only one match and only 16 appear in multiple matches. Do not calculate top
DRD players, attacker value, or player ability.

The strongest claim available only after a SUPPORTED result and a ready
retrieval layer is:

> Context-adjusted DRD provides an out-of-sample retrieval signal for
> identifying off-ball movements followed by more localized defensive
> reorganization than expected from comparable movement and starting geometry.

That claim remains observational and application-bounded.

## 14. Closure and planned outputs

The eventual IDSSE execution must preserve protocol/config hashes, use the
common sample and folds, save predictions before retrieval, validate every
machine-readable artifact, and independently reproduce governed outputs
byte-for-byte. Planned outputs are a manifest, eligibility/exclusion ledger,
feature dictionary, fold/alpha ledger, common heldout predictions, per-match
metrics, comparisons, ablations, bootstrap intervals, reliability diagnostics,
hard QC, governed hashes, reproduction record, bounded result report, and—only
if authorized—the deterministic retrieval board.

This freeze computes no empirical target, prediction, residual, DRD, status,
retrieval example, Metrica transport result, or SkillCorner result.
