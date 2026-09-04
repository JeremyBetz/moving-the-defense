# Defensive Response Mode v1

**Status:** frozen prospectively; no empirical response-mode result observed

**Freeze date:** 2026-09-04

**Starting commit:** `a1835f6b73543bffd805d3f64b23d0d7470b119a`

**Execution:** not authorized by this design pass

## 1. Question and boundary

Primary question:

> Conditional on equal attacker path magnitude and frozen starting context,
> is 5 m inward rather than 5 m outward displacement associated with greater
> defensive width reduction over the following two seconds?

Secondary, nonclassifying question:

> Is 5 m goalward rather than 5 m outward displacement associated with greater
> goalward defensive-centroid displacement over the following two seconds?

The study characterizes observable directional response form. It does not
infer tactical intent, defensive scheme, marking or responsibility, deliberate
compression, protection of the center, defender confusion, attacker influence,
causation, success, gravity, or value.

## 2. Data and inherited sample

Use exactly the seven IDSSE matches and observation IDs from closed Defensive
Reorganization Context v1 / Spatial Form v1. Exact set mismatch is INVALID.
Reuse unchanged:

- 25 Hz time and period-origin `4 + 4k` second anchors;
- prior `[t-4,t-2]`, exposure `[t-2,t]`, and response `[t,t+2]`;
- centered seven-frame complete-support smoothing;
- canonical 105 by 68 m pitch, positive x goalward, and focal-start-side y
  reflection;
- open-play, restart, ball-out, roster, cadence, missingness, no-interpolation,
  ball-nearest attacker exclusion, and complete ten-defender rules; and
- D1–D10 fixed at `t` by attacker distance and the governed tie break.

Do not use SkillCorner, Metrica, Game 3, DRD residuals, event outcomes,
player/team aggregates, or tactical labels.

## 3. Frozen attacker movement and context

Reuse the exact Spatial Form v1 continuous columns and order:

1. exposure path magnitude;
2. prior attacker path;
3. attacker-minus-unit goalward offset at `t-2`;
4. attacker-ball distance at `t-2`;
5. unit width at `t-2`;
6. unit depth at `t-2`;
7. ball-minus-unit goalward offset at `t-2`;
8. signed goalward displacement over `[t-2,t]`; and
9. signed outward displacement over `[t-2,t]`.

No extra context, interaction, nonlinear term, threshold, spatial lane, or
movement category is permitted.

## 4. Separate response channels

All endpoint quantities use the exact smoothed positions at `t` and `t+2`.
Let the complete defending-outfield centroid be `c(s)`.

### A. Collective translation

The modeled quantity is signed goalward centroid displacement:

$$T_i=c_x(t+2)-c_x(t).$$

Positive means the defending unit centroid moved in the attacker's goalward
direction. Report centroid lateral displacement, net displacement, and
accumulated centroid path descriptively. They are nonclassifying.

### B. Global pitch-axis shape

With `W(s)=max_d y_d(s)-min_d y_d(s)` and
`D(s)=max_d x_d(s)-min_d x_d(s)`, define:

$$N_i=W(t)-W(t+2),$$

$$K_i=D(t)-D(t+2).$$

Positive `N` is literal width reduction; positive `K` is literal depth
reduction. `N` is the primary outcome. `K` is descriptive. Neither is called
uniform or deliberate compression. Do not compute area, hull, stretch,
pairwise entropy, principal-axis orientation, shear, or line-specific shape.

### C. Localized internal reorganization

Reuse unchanged:

$$L_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik}
-\frac{1}{4}\sum_{k=4}^{7}P_{ik},$$

where `P_ik` is subsequent accumulated leave-one-out defender-relative path
over `[t,t+2]`. This outcome is descriptive here and cannot serve as a new
classification target.

The channels are separate, nonexclusive views. Do not sum them, standardize
them into a joint index, estimate allocation shares, or compare raw
coefficients as though the outcomes had equivalent meanings.

## 5. Models and contrasts

Fit one equal-match-weighted raw-unit OLS per modeled outcome (`N`, `T`, `K`,
and `L`) with one intercept per match and the exact nine columns in Section 3.
Use `numpy.linalg.lstsq(rcond=None)` and require full rank. No regularization,
standardization, weighting change, player/team effect, interaction, or model
selection is allowed.

The sole primary contrast is 5 m inward minus 5 m outward predicted width
reduction, at equal 5 m path and zero goalward displacement:

$$C_W=-10\beta^{N}_{out}.$$

The expected sign is positive. Use a two-sided 95% interval; zero touching
fails support.

The sole secondary contrast is 5 m goalward minus 5 m outward signed centroid
goalward displacement:

$$C_T=5(\beta^{T}_{goal}-\beta^{T}_{out}).$$

Its expected sign is positive, but it is nonclassifying. Component
coefficients, depth directional contrasts, and the previously established
localized outward-minus-goalward contrast are descriptive.

For football-readable predictions, set controls to within-match medians,
compute pure 5 m goalward, outward, away-from-goal, and inward predictions, and
average matches equally. Report each outcome's observed IQR beside predictions.
Do not compare outcome magnitudes as a common response scale.

## 6. Inference and robustness

Use 2,000 deterministic paired match-period 60-second block bootstrap
replicates with `PCG64` seed `20260906`. Preserve every match, simultaneous
focal attackers, and all rows sharing an anchor. Use two-sided 95% percentile
intervals and require at least 1,900 finite full-rank replicates.

Report pooled equal-match-weighted, seven match-specific, and seven
leave-one-match-out fits for all four outcomes. Only the primary `C_W` uses
these as classification gates.

The sole robustness check retains rows inside each match's inclusive
2.5th–97.5th percentiles jointly for signed goalward and outward displacement,
exactly as Spatial Form v1. It passes when trimmed `C_W` is positive and
retains 50–150% of the full absolute magnitude. No outcome-based trim or shape
threshold is allowed.

## 7. Classification and stop rule

Evaluate in order:

1. **RESPONSE MODE INVALID:** frozen-hash, sample identity, support, geometry,
   model-rank, bootstrap, reproduction, or hard-QC failure.
2. **RESPONSE MODE WIDTH HYPOTHESIS SUPPORTED:** valid; `C_W` strictly
   positive; its 95% interval strictly above zero; at least 6/7 match estimates
   positive; all 7/7 leave-one-match-out estimates positive; and trim passes.
3. **RESPONSE MODE WIDTH HYPOTHESIS MIXED:** valid and `C_W` positive but one
   or more support gates fail.
4. **RESPONSE MODE WIDTH HYPOTHESIS NOT SUPPORTED:** every other valid result.

The secondary centroid hypothesis, depth outcome, and localized outcome cannot
change this status. If the primary is mixed or not supported, stop: do not test
area, convex hull, pairwise entropy, orientation, shear, line-specific widths,
subgroups, players, teams, alternative directions, windows, lags, thresholds,
or another response-mode mechanism.

## 8. Synthetic validity and known incompleteness

Before empirical execution, fixtures must verify:

- common translation changes centroid motion while width, depth, and localized
  relative path remain zero;
- symmetric narrowing and depth compression change the matching pitch-axis
  span without centroid translation;
- a local adjustment can produce localized path without pure translation;
- a partial-unit lateral shift can combine translation and width change;
- rigid rotation preserves pairwise distances but may change pitch-axis spans
  and localized path; and
- shear may change internal pairwise geometry while the selected channels show
  little change.

The final two cases establish that v1 is not an exhaustive decomposition.
Rotation and shear are declared limitations, not post-result rescue channels.

## 9. Hard QC and reproduction

Require frozen hashes; exact closed observation IDs; unique rows; complete ten
outfield defenders; goalkeeper exclusion; exact rank construction; complete
endpoint/path support; no interpolation; finite canonical geometry; correct
temporal order; full model ranks; complete match/LOMO fits; at least 1,900
valid paired bootstrap replicates; exact contrast identities; synthetic tests;
deterministic byte-identical governed outputs; no SkillCorner response-mode
outcome, DRD residual, Game 3 access, ranking, or tactical/value label.

This freeze pass computes no empirical response-mode result.
