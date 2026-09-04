# Spatial Movement and Defensive Reorganization — Feasibility Audit

**Decision:** freeze one narrow, interpretable study. The study concerns the
spatial form of observed localized defensive reorganization. Despite the
historical planning filename `spatial_value`, it does **not** measure attacking
value.

**Design date:** 2026-09-04

**Starting commit:** `a270650e980ed770769cfd7169b10c5e3b26e762`

**Outcome firewall:** no new response result, DRD residual, SkillCorner outcome,
Metrica Game 3 datum, passage, or player ranking was inspected.

## 1. Why this is distinct from Context v1

The closed Context v1 result established that the observed anchor-level
near-minus-middle defender-relative path varied with two **starting**
relationships: attacker goalward position relative to the defensive unit and
attacker--ball distance. It did not test how the attacker allocated a given
amount of movement between goalward and outward directions, and it did not
compare fixed pitch lanes with dynamic defensive-unit geometry.

DRD v2 provides counterweight rather than selection evidence: removing its
movement-direction family worsened heldout macro MAE by only `0.311%`, below
that protocol's materiality rule. The present study can still ask a direct
raw-unit directional contrast on the observed response, but a positive result
must not be presented as rescuing DRD or as proof that direction is an important
prediction family.

The new question is therefore bounded and distinct:

> With attacker path magnitude and starting context held constant, is the
> association with localized defensive reorganization different when movement
> is allocated outward rather than goalward?

The secondary question is:

> Does a compact dynamic description of the attacker's lateral position
> relative to the current defensive unit predict the same observed response
> better out of match than conventional static five-lane membership?

Both are geometric questions. Neither establishes causation, tactical success,
space creation, gravity, or value.

## 2. Candidate representations considered

| Representation | Decision | Reason |
|---|---|---|
| Signed goalward and signed outward displacement, conditional on path | **Primary** | Continuous, raw-metre, already constructible under the governed coordinate transform, and directly answers whether direction adds information beyond movement amount. |
| Movement toward/away from the defensive centroid | Not separately frozen | With a start-fixed pitch-aligned unit frame, its longitudinal component largely duplicates goalward displacement plus starting centroid offset; following the moving centroid during exposure would import concurrent defender motion into the attacker representation. |
| Dynamic lateral position relative to unit centroid/width and same-side edge | **Secondary** | Continuous geometry tied to the current defensive shape rather than a fixed pitch lane. |
| Static five-lane / half-space membership | **Secondary comparator only** | Football-readable and reproducible once pitch-marking boundaries are declared, but categorical and not a validated value zone. |
| Continuous distance to a half-space centre or boundary | Not frozen | The choice of centre versus boundary and distance sign would add an unmotivated definition after the lane comparator is already available. |
| Convex-hull inside/outside | Not frozen | A binary hull boundary can change discontinuously with one defender and does not distinguish lateral from longitudinal location. |
| Defender-pair seam or neighborhood crossing | **Rejected for v1** | “Adjacent” defenders cannot be defined without choosing lateral ordering, depth tolerance, line identity, or a dynamic neighborhood rule. Those choices can silently imply roles or handoffs and make the construct too flexible. |
| Broad 2D spline/GAM surface | Not frozen | The two signed linear displacement terms yield the simplest interpretable directional contrast; a flexible surface would add avoidable multiplicity before linear form is tested. |
| xT/EPV change versus reorganization | Not frozen | It would import a separate value model and turn a geometric study into an attacking-value study before either bridge is validated. |

## 3. Half-space definition audit

The reviewed tactical sources converge on the **concept** of five longitudinal
lanes: two wide lanes, two half-spaces, and one central lane. They do not define
a universal quantitative analytics standard. Coaches' Voice describes the wide
lanes as extending from the touchline to the outside edge of the penalty area
and the central lane as the width of the centre circle or six-yard box. The
IFAB markings make those references reproducible on the canonical 105 by 68 m
pitch: centre-circle radius `9.15 m`, goal-area half-width `9.16 m`, and
penalty-area half-width `20.16 m`. The near-equivalence of the first two
references is useful, but it remains a coaching convention rather than a law
that half-space occupation has a particular effect.

The frozen static comparator therefore uses absolute lateral position at
movement start:

- central: `abs(y) <= 9.15 m`;
- half-space: `9.15 m < abs(y) <= 20.16 m`;
- wide: `abs(y) > 20.16 m`.

Exact equality is assigned inward as written. The three-level variable is
mirrored-side invariant and enters as two indicators with central as reference.
It is secondary and two-sided. No hypothesis says that the half-space is
superior or more valuable.

The dynamic alternative is more closely aligned with this project's question
because it moves with the defending outfield unit. It retains two predeclared
quantities at `t-2` after the governed attacking-direction/focal-side rigid
transform:

1. `attacker_unit_lateral_position`: attacker lateral offset from the
   defensive centroid divided by half the defending-unit width; and
2. `attacker_beyond_same_side_edge_m`: `max(0, attacker_y - max(defender_y))`.

The first is dimensionless and may exceed one; the second is zero inside the
same-side defensive edge and positive outside it. They are descriptive geometry,
not “between lines,” a role, or a seam.

Sources reviewed:

- [Coaches' Voice: The half-spaces](https://learning.coachesvoice.com/cv/half-spaces-football-tactics-explained/)
- [FourFourTwo: Half-space explained](https://www.fourfourtwo.com/features/half-space-football-tactics-explained)
- [IFAB Law 1: The field of play](https://www.theifab.com/laws/latest/the-field-of-play/)
- [Sotudeh (2025), formation-identification survey](https://doi.org/10.3389/fspor.2024.1512386)

The survey's broader point is also relevant: fixed tactical zones are only one
possible spatial reference alongside the ball, goals, teammates, opponents,
and space. That supports testing static lanes against a defensive-unit-relative
alternative rather than treating the lane labels as ground truth.

## 4. Frozen target and variables

One row is one governed eligible `(match, period, anchor, focal attacker)` from
the exact closed Context v1 observation-ID set. The response remains:

$$
Y_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik}
-\frac{1}{4}\sum_{k=4}^{7}P_{ik},
$$

where `P_ik` is subsequent accumulated leave-one-out defender-relative path in
metres over `[t,t+2]`. Attacker movement is measured over `[t-2,t]`; prior
attacker path is `[t-4,t-2]`. Ranks, support, smoothing, off-ball eligibility,
goalkeeper exclusion, restarts, cadence, and missingness remain unchanged.

Primary movement variables:

- `attacker_goalward_displacement_m = x(t) - x(t-2)`;
- `attacker_outward_displacement_m = y(t) - y(t-2)` after the focal-side
  reflection that makes positive movement outward from the centre line; and
- `attacker_path_exposure_m`, retained as a control so direction is not a proxy
  for moving farther.

Starting-shape variables:

- `attacker_minus_unit_goalward_m`;
- `attacker_ball_distance_start_m`;
- `defending_unit_width_m`;
- `defending_unit_depth_m`;
- `ball_minus_unit_goalward_m`;
- the two dynamic lateral variables above; and
- the static three-level lane comparator above.

No movement threshold, tactical run type, convex hull, seam, defender
assignment, DRD residual, event outcome, identity, or player aggregate enters
the study.

## 5. Model and estimands

### Primary model

Fit equal-match-weighted raw-unit OLS with one intercept per match:

$$
Y_i=\alpha_{m(i)}+\beta_EE_i+\beta_PP_i+\beta_XX_i+\beta_BB_i+
\beta_WW_i+\beta_DD_i+\beta_GG_i+\beta_g g_i+\beta_o o_i+\varepsilon_i.
$$

`E` is exposure path, `P` prior attacker path, `X` attacker--unit goalward
offset, `B` attacker--ball distance, `W/D` unit width/depth, `G` ball--unit
goalward offset, and `g/o` signed goalward/outward displacement. Every match has
equal total weight. There is no standardization, regularization, interaction,
polynomial, spline, target scaling, or clipping.

The single primary estimand is

$$
\Delta_{O-G}=\beta_o-\beta_g.
$$

It is the fitted difference in `Y` per metre reallocated from pure goalward to
pure outward displacement while total path and starting context remain fixed.
A positive value means outward allocation has the larger association; a
negative value means goalward allocation has the larger association. Either
sign is scientifically interpretable. Separate `beta_g` and `beta_o` estimates
are descriptive and cannot create a second primary claim.

### Secondary comparison

Use seven fixed leave-one-match-out fits, without hyperparameter selection:

- `S_static`: primary controls and movement variables plus the two static-lane
  indicators;
- `S_dynamic`: the identical base plus normalized unit-relative lateral
  position and beyond-edge distance.

Compare equal-match macro heldout MAE in metres. This is a predictive comparison
of two compact representations, not proof that a football concept is true. The
models have different functional forms; reporting column count and rank is
mandatory.

## 6. Multiplicity hierarchy and inference

The hierarchy is fixed:

1. **Primary:** the one two-sided `Delta_O-G` contrast.
2. **Secondary:** dynamic unit-relative lateral geometry versus static
   five-lane membership in out-of-match prediction.
3. **Exploratory only:** model-derived canonical direction descriptions and a
   possible upper-left visualization. No seam analysis is authorized.

Primary uncertainty uses 2,000 paired 60-second match-period block bootstrap
replicates, preserving all anchors and simultaneous attackers, with a two-sided
95% percentile interval and at least 1,900 valid full-rank fits. Report the
pooled fit, seven match-specific fits, and seven leave-one-match-out fits.

Primary trim robustness retains observations inside each match's inclusive
2.5th--97.5th percentiles for both signed displacement components. The trimmed
contrast must retain the strict sign and 50--150% of the full-sample absolute
magnitude. No alternative trim is allowed.

Secondary uncertainty uses the same 2,000 paired block draws applied to the
fixed out-of-match absolute-error ledger. It reports the interval for
`MAE_static - MAE_dynamic`; it does not tune either representation.

## 7. Frozen decision rules

Hard scientific/QC failure is **INVALID**.

The primary is:

- **SUPPORTED** when the 95% interval for `Delta_O-G` excludes zero, at least
  6/7 match estimates have its sign, all 7/7 leave-one-match-out estimates have
  its sign, and the trim passes;
- **MIXED** when no support gate is met but the interval excludes zero, or at
  least 6/7 match and 7/7 leave-one-match-out estimates share a nonzero sign,
  or the untrimmed gates pass but the trim fails; and
- **NOT SUPPORTED** for every other valid result.

A supported positive contrast is labelled **OUTWARD GREATER**; a supported
negative contrast is **GOALWARD GREATER**. These are coefficient directions,
not tactical or value labels.

The secondary result is **DYNAMIC PREFERRED** only if its equal-match macro
heldout MAE is at least 1.0% lower than the static model, it improves at least
5/7 heldout matches, and the paired 95% interval for
`MAE_static - MAE_dynamic` is above zero. **STATIC PREFERRED** applies the
symmetric rule. Otherwise it is **NO CLEAR REPRESENTATIONAL ADVANTAGE**. The
1.0% materiality rule is inherited from the project's prior frozen context-
family standard rather than selected after this result.

The secondary result cannot rescue or overturn the primary status.

## 8. Effect-size and figure plan

Report `beta_g`, `beta_o`, and `Delta_O-G` in metres of `Y` per metre of
displacement. Translate the primary contrast as `5 * Delta_O-G`: the fitted
difference between a straight 5 m outward movement and a straight 5 m goalward
movement at the same 5 m path and fixed starting context. Also report
model-derived 5 m away-from-goal, goalward, outward, and inward descriptions.
For those descriptions, set continuous controls to their within-match medians,
predict with each match intercept, and average the seven predictions equally.
Report the observed response IQR beside them so “substantial” is not assigned by
visual rhetoric. These descriptions are nonclassifying canonical geometry;
also report observed predictor p10--p90 ranges.

If the primary is supported, one figure may show a start-fixed
defensive-unit-relative pitch panel with four 5 m movement arrows and their
conditional fitted `Y`, accompanied by the static-lane versus dynamic-edge
comparison. It must show observed support and cannot use an xT/EPV axis. The
“upper-left” idea is scientifically meaningful only as a descriptive view of
low/negative goalward displacement with model-supported reorganization; it is
not a value quadrant. If the primary is mixed/not supported, do not promote the
graphic by selecting a favorable subgroup.

## 9. Novelty, Sloan payoff, and failure value

The likely Sloan value ranks as follows:

1. **Highest:** dynamic defensive-shape-relative position clearly transports
   better out of match than static five-lane membership. This would question a
   familiar fixed-zone shorthand with an interpretable moving reference.
2. **High:** outward movement has a stable larger association than goalward
   movement at comparable path and starting context. This would be surprising
   without claiming that outward movement is better or more valuable.
3. **Moderate:** goalward movement dominates consistently. This is clean but
   intuitive and should remain a secondary spatial characterization rather than
   the paper headline.
4. **Low:** mixed or null direction and no representational advantage. Close
   the branch; do not search subgroups or redefine zones.

The contribution would not be the invention of half-spaces, centroids, or
movement components. It would be the prospective comparison of fixed and
dynamic spatial representations against an externally replicated defender-
relative response while preserving negative results.

Estimated Codex cost for eventual execution is **medium-high**: one governed
seven-match IDSSE construction, fourteen untuned leave-one-match-out fits,
2,000 grouped primary bootstraps, 2,000 paired error bootstraps, one independent
reproduction, and compact reporting. It requires no new provider integration.

SkillCorner becomes justified only after a supported, non-obvious IDSSE result
and a separate provider-equivalence protocol. An obvious, mixed, or null result
does not justify that integration cost. Metrica Game 3 remains untouched.

## 10. Freeze decision

The design meets the freeze conditions:

- the primary directional-allocation contrast is distinct from Context v1's
  starting-position hypotheses;
- one primary and one secondary question control multiplicity;
- every sign has an interpretable geometric meaning;
- the static half-space comparator has explicit pitch-marking provenance;
- the dynamic representation is compact and prospectively defined; and
- null, intuitive, and surprising outcomes all have explicit stopping value.

The accompanying protocol and configuration are therefore frozen for a future,
separately authorized IDSSE execution. This audit computes no empirical result.
