# Defensive Reorganization Context v1

**Status:** frozen prospectively before any context-model or effect result

**Freeze date:** 2026-09-04

**Starting commit:** `06a039bf19cda76e27555cc44c1bc75d44e4dec0`

**Execution policy:** future IDSSE development execution under Tier 1 of the
[project execution policy](../execution_policy.md); a SUPPORTED result must be
closed under Tier 2 before paper use.

## 1. Question and boundary

> Which pre-movement spatial situations are associated with stronger
> subsequent localized defensive reorganization?

This is a separate descriptive context study. It does not reopen Defensive
Reorganization Departure (DRD) v2, inspect residuals, retrieve passages, or
change that execution's **DRD APPLICATION FOUNDATION MIXED** status. The target
is observed geometry, not prediction error.

The strongest possible claim is:

> Localized defensive reorganization associated with off-ball movement varies
> systematically with specific starting spatial relationships.

The study cannot establish why that variation occurs. It cannot establish
causation, influence, attention, marking, assignment, responsibility, tactical
response, tactical success, defensive quality, player quality, gravity,
off-ball value, or a player ranking.

## 2. Data, unit, timing, and support

Use exactly the seven governed IDSSE matches `J03WMX`, `J03WN1`, `J03WOH`,
`J03WOY`, `J03WPY`, `J03WQQ`, and `J03WR9`. One row is one eligible `(match,
period, anchor time, focal attacking outfield player)` with the complete
start-fixed D1–D10 defender vector.

Inherit unchanged from [DRD v2](defensive_reorganization_departure_v2.md) and
its v1 parent:

- the 25 Hz physical clock and period-origin `4 + 4k` second anchors;
- strictly prior attacker context `[t-4,t-2]`;
- attacker movement/exposure `[t-2,t]`;
- defender response `[t,t+2]`;
- centred seven-frame complete-window smoothing;
- open-play, restart, ball-out, cadence, raw-support, missingness, and no-
  interpolation rules;
- exact event-defined current attacking outfield set, including substitutions
  and confirmed dismissals;
- threshold-free exclusion of the unique ball-nearest active attacker at `t`;
- all ten defending outfield players, goalkeeper exclusion, and complete
  support; and
- start-fixed D1–D10 ranks by attacker–defender Euclidean distance at `t` with
  the existing canonical-player-key tie break.

The primary ledger must equal the closed v2 common-sample observation-ID set
exactly. Reconstruct it from frozen rules and compare identifiers without
reading v2 predictions or residuals. A mismatch is INVALID. The inherited
minimums of 1,000 rows per match and 90% retention remain hard checks.
Simultaneous focal attackers share defensive state and remain in the same
60-second block in every resampling operation.

Metrica Sample Game 3 and SkillCorner are prohibited in this execution.

## 3. Target

For defender rank `k`, retain the validated accumulated leave-one-out
defender-relative path `P_ik` in metres over `[t,t+2]`. Define

$$
N_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik},\qquad
M_i=\frac{1}{4}\sum_{k=4}^{7}P_{ik},\qquad
Y_i=N_i-M_i.
$$

The continuous primary target is `Y_i` in metres. Retain `N_i` and `M_i` for
descriptive decomposition only. Do not use DRD residuals, fitted temporal
coefficients, player aggregates, event outcomes, or D8–D10 in the target.

## 4. Context selection frozen before outcomes

The DRD v2 family ablation established only that start-position and ball-
geometry families contributed to heldout prediction. No individual DRD v2
coefficient, residual, passage, subgroup effect, or p-value was inspected to
select these quantities.

The two primary continuous contexts, both measured at movement start `t-2`,
are:

1. `attacker_minus_unit_goalward_m`: focal attacker goalward coordinate minus
   the ten-defender centroid goalward coordinate. A 10 m increase means the
   attacker starts 10 m more goalward relative to the unit.
2. `attacker_ball_distance_start_m`: Euclidean attacker–ball distance in
   canonical metres. A 10 m increase means the attacker starts 10 m farther
   from the ball.

Use the same rigid attacking-direction and focal-side reflection as DRD v1.
The first quantity is signed; the second is nonnegative and invariant to that
rigid transform.

No directional effect is predeclared. Football theory does not justify a
single sign without adding tactical-state assumptions, so both hypotheses are
two-sided:

- **H1:** localized defensive reorganization varies with the attacker's
  goalward starting position relative to the defensive unit.
- **H2:** localized defensive reorganization varies with attacker–ball
  distance at movement start.

Attacker lateral offset, normalized position, ball lateral offset, and
attacker–ball distance change are not primary contexts. The last is measured
across the exposure interval and is therefore not pure starting context.

## 5. Primary model

Fit one raw-unit weighted ordinary least-squares model:

$$
Y_i=\alpha_{m(i)}+
\beta_E E_i+\beta_P P_i+
\beta_X X_i+\beta_B B_i+
\gamma_D D_i+\gamma_G G_i+\varepsilon_i,
$$

where:

- `E_i = attacker_path_exposure_m` over `[t-2,t]`;
- `P_i = attacker_path_prior_m` over `[t-4,t-2]`;
- `X_i = attacker_minus_unit_goalward_m` (primary H1);
- `B_i = attacker_ball_distance_start_m` (primary H2);
- `D_i = defending_unit_depth_m` at `t-2`; and
- `G_i = ball_minus_unit_goalward_m` at `t-2`.

`D_i` separates raw attacker position from obvious defensive-depth scale;
`G_i` separates attacker–ball distance from the ball's basic depth relative to
the unit. These are predeclared nuisance terms, not additional context
hypotheses. Do not add lateral coordinates, unit width, distance change,
interactions, polynomials, splines, normalized ratios, identities, roles,
formation, assignments, event outcomes, or automated feature selection.

Include one intercept per match. Give every match equal total weight:
`w_i = 1/n_m` for observations in match `m`. Fit in physical units without
standardization, regularization, target scaling, or clipping. Use deterministic
weighted least squares (`numpy.linalg.lstsq`, `rcond=None`) and require full
design rank. Record the rank, column order, and coefficient units.

The primary estimands are `beta_X` and `beta_B` in metres of `Y` per metre of
context, mutually adjusted and conditional on the four frozen controls. They
are associations, not mechanisms.

## 6. Match-respecting evaluation and uncertainty

Report the same six-column model:

1. pooled with match intercepts and equal match weights;
2. separately in each of seven matches; and
3. seven times pooled while leaving one complete match out.

No model is chosen from these results. Match-specific and leave-one-match-out
fits assess whether the pooled form hides disagreement.

For pooled uncertainty, use 2,000 deterministic paired bootstrap replicates
with seed `20260904`. Within every match-period, resample period-origin
60-second anchor blocks with replacement, preserving all simultaneous focal
attackers and all rows sharing an anchor. Keep all seven matches in every
replicate and refit the complete model. Use the same draws for both primary
coefficients. Report two-sided 97.5% percentile intervals for each primary
coefficient, controlling the two-hypothesis family at 5% by Bonferroni. Require
at least 1,900 finite full-rank replicates for each coefficient.

These intervals quantify block-level uncertainty conditional on the seven
observed matches. They are not population-level inference to all football.

An interval excludes zero only when its lower bound is strictly above zero or
its upper bound is strictly below zero. Touching zero fails.

## 7. One frozen robustness check

Run one central-support robustness fit. Within each match, compute predictor-
only 2.5th and 97.5th percentiles for each of the two primary contexts. Retain
rows lying inside both inclusive ranges, then refit the unchanged primary
model with equal-match weights and match intercepts.

For a primary context, robustness passes only when its trimmed coefficient has
the same strict sign as the full coefficient and its absolute magnitude is
from 50% through 150% of the full magnitude, inclusively. Do not change the
quantiles or add further trims after outcomes.

## 8. Context-level and study-level decisions

A primary context passes only when all four conditions hold:

1. its pooled 97.5% interval excludes zero;
2. at least 6 of 7 match-specific estimates share the pooled strict sign;
3. all 7 leave-one-match-out pooled estimates share that strict sign; and
4. the central-support robustness rule passes.

Evaluate the study status exhaustively:

1. **INVALID:** frozen-hash, sample-identity, support, leakage, finite-value,
   full-rank, bootstrap-minimum, deterministic, or hard-QC failure.
2. **SUPPORTED:** at least one of the two primary contexts passes all four
   gates.
3. **MIXED:** no context passes, but at least one has either a pooled 97.5%
   interval excluding zero or at least 6 of 7 match-specific estimates sharing
   the pooled strict sign.
4. **NOT SUPPORTED:** every other valid result.

Exactly 6 of 7 meets the match gate; 5 of 7 fails. Exactly 50% and 150% meet
the robustness range. A zero point estimate has no sign and cannot pass.

SUPPORTED means one or two simple pre-movement contexts robustly characterize
variation in the measured geometry. MIXED is not a Sloan application headline.
NOT SUPPORTED ends this context branch before Sloan unless an independently
motivated, substantively different question is frozen. No result may reopen
DRD retrieval or trigger feature, threshold, model, context, or example repair.

## 9. Effect-size and figure plan

For each primary context, report:

- the raw coefficient in m/m;
- the associated change in `Y` for a 10 m context difference (`10 * beta`);
- the predictor-only pooled 10th-to-90th percentile span in metres; and
- the associated change across that span (`beta * (q90-q10)`).

Do not headline standardized coefficients. The main analyst-facing figure is
one two-panel football graphic: a pitch schematic shows the selected start
relationship, and an adjusted linear curve shows change in expected localized
reorganization over the observed 10th-to-90th percentile context range. Show
raw metres, uncertainty, and all seven match-specific slopes. It is not a
machine-learning performance plot.

Any optional real geometry panels must be selected deterministically from
predictor context strata before reading `Y`: within each context, choose rows
nearest the pooled 20th and 80th predictor percentiles, then earliest lexical
observation ID on a tie. They illustrate geometry and do not prove the effect.

## 10. Conditional transport and future external role

Only after the IDSSE study is frozen, executed, reproduced, and classified
SUPPORTED may a separately authorized nonclassifying Metrica Games 1–2
transport check apply the identical target, contexts, model form, signs, and
support logic. Do not tune with Metrica. Game 3 remains prohibited.

SkillCorner is not integrated in this study. A SUPPORTED IDSSE result could
justify a separate outcome-blind provider/support gate and then a newly frozen
external protocol testing the same two football-readable relationships. That
would be external confirmation, not DRD residual validation. No SkillCorner
outcome may be opened by this protocol.

## 11. Sloan value, cost, and stop rule

A SUPPORTED result could upgrade the paper from “we can measure localized
reorganization” to “we can measure it and identify spatial situations in which
it tends to be stronger.” It would improve interpretation and application
without creating a tactical recommendation. MIXED or NOT SUPPORTED leaves the
externally replicated measurement paper as the contribution.

The eventual IDSSE execution should reuse the closed v2 eligibility/features
and target infrastructure and is budgeted at roughly 5–8 weekly allowance
points. Tier 1 does not require an independent full rerun. A SUPPORTED result
is milestone-worthy and must receive Tier 2 deterministic reproduction,
governed figures, hashes, and documentation before paper use.

Stop after classification. Do not calculate DRD, inspect residual passages,
retrieve examples by response, rank players, open SkillCorner, access Game 3,
or design a replacement context study from the outcome.
