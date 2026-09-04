# Defensive Reorganization Spatial Form v1

> The governed filenames retain the planning label `spatial_value`; this
> protocol measures spatial form of observed reorganization, not attacking
> value.

**Status:** frozen prospectively before any new spatial-form outcome

**Freeze date:** 2026-09-04

**Starting commit:** `a270650e980ed770769cfd7169b10c5e3b26e762`

**Execution:** not authorized by this protocol-freeze pass

## 1. Question and maximum claim

Primary question:

> Conditional on attacker path magnitude and frozen starting context, does
> allocating movement outward rather than goalward have a different association
> with subsequent localized defensive reorganization?

Secondary question:

> Does compact dynamic lateral position relative to the defending outfield unit
> predict the observed response better out of match than static five-lane
> membership?

The maximum claim is that movement direction or a starting spatial
representation is associated with variation in observed near-minus-middle
defender-relative path. The study cannot establish causation, influence,
attention, marking, assignment, responsibility, tactical success, space
creation, gravity, attacking value, optimal movement, or player quality.

## 2. Data, sample, timing, and target

Use exactly the seven governed IDSSE matches and exact observation-ID set from
closed Defensive Reorganization Context v1. Reconstruct identifiers from frozen
rules without reading DRD predictions/residuals. Exact set mismatch is INVALID.

Inherit unchanged:

- 25 Hz clock and period-origin `4 + 4k` second anchors;
- prior attacker path `[t-4,t-2]`, exposure `[t-2,t]`, response `[t,t+2]`;
- centred seven-frame complete-support smoothing;
- attacking-direction and focal-side rigid transform;
- open-play, restart, ball-out, roster, cadence, support, and no-interpolation
  rules;
- unique ball-nearest attacking-outfielder exclusion at the anchor;
- complete ten-defender outfield unit and goalkeeper exclusion; and
- D1--D10 ranks fixed at `t` with the governed tie break.

For rank `k`, let `P_ik` be accumulated leave-one-out defender-relative path in
metres over `[t,t+2]`. The target is

$$
Y_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik}
-\frac{1}{4}\sum_{k=4}^{7}P_{ik}.
$$

No DRD residual, event outcome, passage, player aggregate, or D8--D10 quantity
enters the target.

## 3. Frozen geometry

All start geometry is measured at `t-2` after the inherited rigid transform.
Positive x is goalward. The focal attacker begins on nonnegative y; positive
signed y displacement is outward from the centre line.

Primary movement variables:

1. `attacker_goalward_displacement_m = x(t)-x(t-2)`;
2. `attacker_outward_displacement_m = y(t)-y(t-2)`; and
3. `attacker_path_exposure_m`, kept separately as total movement amount.

Baseline/start controls:

1. `attacker_path_prior_m`;
2. `attacker_minus_unit_goalward_m`;
3. `attacker_ball_distance_start_m`;
4. `defending_unit_width_m = max(defender_y)-min(defender_y)`;
5. `defending_unit_depth_m = max(defender_x)-min(defender_x)`; and
6. `ball_minus_unit_goalward_m`.

Static lane at `t-2`, using canonical `abs(y)`:

- `central` when `abs(y) <= 9.15`;
- `half_space` when `9.15 < abs(y) <= 20.16`;
- `wide` when `abs(y) > 20.16`.

Use central as the reference and retain two indicators. These boundaries derive
from the centre-circle/goal-area and penalty-area width conventions documented
in the design audit. Membership has no directional or value hypothesis.

Dynamic lateral representation at `t-2`:

1. `attacker_unit_lateral_position =
   (attacker_y-unit_centroid_y)/(defending_unit_width_m/2)`; and
2. `attacker_beyond_same_side_edge_m =
   max(0, attacker_y-max(defender_y))`.

Require positive finite unit width. Do not clip normalized position. Exact edge
equality gives zero beyond-edge distance. No hull, seam, defender pair,
neighborhood transition, line identity, or dynamic rank reassignment is allowed.

## 4. Primary model and estimand

Fit equal-match-weighted raw-unit OLS with one intercept per match and continuous
columns in this exact order:

1. `attacker_path_exposure_m`;
2. `attacker_path_prior_m`;
3. `attacker_minus_unit_goalward_m`;
4. `attacker_ball_distance_start_m`;
5. `defending_unit_width_m`;
6. `defending_unit_depth_m`;
7. `ball_minus_unit_goalward_m`;
8. `attacker_goalward_displacement_m`;
9. `attacker_outward_displacement_m`.

Every match receives total weight one. Use `numpy.linalg.lstsq(rcond=None)` and
require full rank. No standardization, regularization, interaction, polynomial,
spline, threshold, target scaling, clipping, identity, or automated selection.

The sole primary contrast is

$$
\Delta_{O-G}=\beta_{outward}-\beta_{goalward}.
$$

It is two-sided. Positive means the fitted outward association is larger;
negative means the fitted goalward association is larger. Separate component
coefficients are descriptive.

Report pooled equal-match-weighted, seven match-specific, and seven
leave-one-match-out fits. Do not hide sign heterogeneity behind the pooled fit.

## 5. Secondary static-versus-dynamic comparison

Fit seven fixed leave-one-match-out models for each representation:

- `S_static`: the primary model columns plus `half_space` and `wide` indicators;
- `S_dynamic`: the primary model columns plus
  `attacker_unit_lateral_position` and
  `attacker_beyond_same_side_edge_m`.

There is no hyperparameter selection. Record train/test design ranks, column
counts, per-match MAE, observation-weighted MAE, equal-match macro MAE, and the
single out-of-match absolute-error ledger. The secondary estimand is
`MAE_static - MAE_dynamic` in metres and its relative version against static.

## 6. Uncertainty and robustness

Primary uncertainty uses 2,000 deterministic paired match-period 60-second
block bootstrap replicates with seed `20260905`. Preserve every match,
simultaneous focal attackers, and all rows sharing an anchor. Use a two-sided
95% percentile interval and require at least 1,900 finite full-rank replicates.
Zero touching fails exclusion.

Primary trim robustness retains rows inside each match's inclusive
2.5th--97.5th percentiles for both signed displacement variables. The trimmed
contrast must have the strict primary sign and retain 50--150% of the full
absolute magnitude.

Secondary uncertainty applies the same 2,000 paired block draws to the fixed
out-of-match absolute-error ledger and reports a two-sided 95% interval for
`MAE_static - MAE_dynamic`. No refitting, threshold tuning, alternative score,
or additional representation is allowed after results.

## 7. Classification

Evaluate in order.

1. **INVALID:** frozen-hash, sample identity, leakage, support, finite geometry,
   design-rank, bootstrap-minimum, fold, deterministic-reproduction, or hard-QC
   failure.
2. **SPATIAL FORM SUPPORTED:** the primary 95% interval excludes zero, at least
   6/7 match estimates have the pooled sign, all 7/7 leave-one-match-out
   estimates have that sign, and the primary trim passes.
3. **SPATIAL FORM MIXED:** no support classification, but the interval excludes
   zero; or at least 6/7 match and 7/7 leave-one-match-out estimates have the
   same nonzero sign; or the untrimmed support gates pass but the trim fails.
4. **SPATIAL FORM NOT SUPPORTED:** every other valid result.

A supported positive primary result is additionally described as `OUTWARD
GREATER`; a supported negative result as `GOALWARD GREATER`. These are geometric
coefficient directions only.

The secondary is:

- `DYNAMIC PREFERRED` when dynamic macro heldout MAE is at least 1.0% below
  static, dynamic improves at least 5/7 matches, and the paired interval for
  `MAE_static - MAE_dynamic` is above zero;
- `STATIC PREFERRED` under the exact symmetric conditions; or
- `NO CLEAR REPRESENTATIONAL ADVANTAGE` otherwise.

Secondary status cannot rescue or change primary classification.

## 8. Reporting and stopping rule

Report primary coefficients and contrast in raw units, `5*Delta_O-G`, observed
predictor support, all match and leave-one-match-out estimates, bootstrap
validity, trim, secondary prediction results, and all hard QC. Canonical 5 m
goalward/outward/away/inward descriptions are model-derived and nonclassifying.
Set continuous controls to their within-match medians, use each match intercept,
average the seven predictions equally, and report the observed `Y` IQR beside
them. Do not invent a threshold for “substantial.”

If primary is supported, a single defensive-unit-relative movement-arrow figure
may be produced from the governed model. Do not create xT/EPV, a value quadrant,
or tactical labels. If the result is mixed, not supported, or conventionally
goalward-dominant, report it and stop. No subgroup search, seam construction,
boundary change, nonlinear rescue, SkillCorner execution, Metrica transport, or
Game 3 access is authorized.

## 9. Hard QC and reproduction

Require frozen hashes; exact Context v1 observation IDs; unique observations;
complete support; valid ranks; finite geometry; positive unit width; exact lane
boundaries; no DRD residual/output read; no SkillCorner or Game 3 access; full
design ranks; complete folds; grouped bootstrap integrity; canonical units;
transformation invariance; deterministic byte-identical governed outputs; and
focused source/config/document checks.

This protocol freeze computes no empirical spatial-form result.
