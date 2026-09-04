# Defensive response-mode decomposition feasibility

**Decision:** **FEASIBLE AS A NARROW WIDTH-RESPONSE TEST; NOT AN EXHAUSTIVE
DECOMPOSITION**

**Audit date:** 2026-09-04

**Outcome firewall:** no new IDSSE response-mode outcome, coefficient,
interval, model, or status was computed. SkillCorner response-mode outcomes,
DRD residuals, player/team rankings, and Metrica Game 3 remained unopened.

## Football question

The replicated Spatial Form result says that, after conditioning on movement
amount and the frozen starting context, outward attacker displacement has a
larger association with subsequent localized defender-relative movement than
goalward displacement. It does not say why.

This audit asks whether a later study can distinguish three observable forms:

1. the defensive unit shifts together;
2. its pitch-axis width or depth changes; and
3. defenders near the attacker move differently relative to the unit than
   middle-ranked defenders.

These are geometric response descriptions, not intent, scheme, assignment,
causation, or value.

## Candidate response channels

| Channel | Candidates considered | Selection | Reason and limit |
|---|---|---|---|
| Collective translation | centroid net displacement, path, goalward and lateral components | **Signed goalward centroid displacement** is the channel's modeled quantity; centroid path, net magnitude, and lateral displacement are descriptive | Direct football meaning and stable provider geometry. A signed component is needed to distinguish retreat/advance; path alone loses direction. |
| Global shape | width, depth, joint width/depth, mean pairwise distance, convex-hull area | **Separate width reduction and depth reduction**; no combined score | Width/depth are established, readable, translation-invariant, and provider-portable. Keeping them separate preserves anisotropy. They are axis-dependent and can change under rotation. |
| Localized internal reorganization | alternative local pairs, deformation, established rank target | **Unchanged mean D1–D3 minus mean D4–D7 subsequent leave-one-out-relative path** | Already validated and externally replicated. It is a path contrast, not compression. |

Mean pairwise distance was not selected because it collapses lateral and
longitudinal change. Convex-hull area was not selected because it is governed
by boundary players, is less football-readable, and adds a nonlinear scalar
without resolving direction. A joint width/depth index was rejected because it
would conceal narrowing-with-depth-expansion and invite arbitrary weighting.

## Synthetic falsification audit

The fixture uses ten defenders, a fixed focal attacker, and two endpoint frames.
Values are illustrative geometry, not empirical calibration. Positive width or
depth reduction means the relevant pitch-axis span decreased.

| Synthetic case | Centroid net (m) | Width reduction (m) | Depth reduction (m) | Mean pairwise change (m) | Localized contrast (m) | Reading |
|---|---:|---:|---:|---:|---:|---|
| Pure translation | 7.6158 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | Translation separates cleanly. |
| Pure narrowing | 0.0000 | 9.0000 | 0.0000 | -2.8616 | 1.9907 | Narrowing can also produce local-relative path; the channels are not mutually exclusive. |
| Pure depth compression | 0.0000 | 0.0000 | 6.0000 | -1.9774 | 0.0000 | Longitudinal compression need not produce localization. |
| Local outward adjustment | 0.8000 | -4.0000 | 0.0000 | 0.9146 | 1.7778 | Local motion can coexist with modest translation and width expansion. |
| Whole-side shift | 2.0000 | -4.0000 | 0.0000 | 1.9347 | ~0.0000 | A partial-unit shift combines collective translation and global shape change without necessarily localizing by rank. |
| Rigid rotation | 0.0000 | 1.8256 | -7.4451 | 0.0000 | 2.3259 | Axis spans and localized path change although intrinsic pairwise geometry does not. |
| Shear | 0.0000 | 0.0000 | 0.0000 | 0.1813 | ~0.0000 | The selected channels can miss a real internal geometric change. |

The audit therefore rejects any claim that the three channels form an
orthogonal or exhaustive partition. Rotation and shear are genuine missing or
confounding forms. Adding principal-axis orientation, line-specific motion, or
a shear tensor now would broaden multiplicity and introduce stability/role
questions. V1 instead calls its primary outcome literal **pitch-axis width
reduction**, not intrinsic compression. Rotation and shear remain declared
limitations and possible future constructs only after this branch closes.

## Selected hypotheses

The one primary new hypothesis is:

> Conditional on equal path magnitude and the frozen starting context, 5 m of
> inward rather than 5 m of outward attacker displacement is associated with
> greater defensive width reduction over the following two seconds.

For the width-reduction model, with signed outward coefficient
$\beta^{N}_{out}$, the primary physical contrast is

$$
C_W(5)=-10\beta^{N}_{out}.
$$

It compares `outward = -5 m` with `outward = +5 m`, holding goalward
displacement at zero and exposure path at 5 m. The expected sign is positive.

One secondary, nonclassifying hypothesis is:

> Conditional on equal path magnitude and starting context, 5 m of goalward
> rather than 5 m of outward attacker displacement is associated with greater
> goalward defensive-centroid displacement over the following two seconds.

For the centroid model this is

$$
C_T(5)=5(\beta^{T}_{goal}-\beta^{T}_{out}).
$$

The secondary cannot rescue or change the primary status. Depth reduction and
the established localized target are reported as separate descriptive response
channels. No coefficient is converted into a share of “response,” and outcomes
are not summed or ranked by magnitude.

## Proposed study

Use the exact seven-match IDSSE observation-ID set closed by Context v1 and
Spatial Form v1. Reuse the frozen timing, smoothing, coordinates, ranks,
eligibility, support, movement variables, and seven starting controls. For each
outcome, fit a separate equal-match-weighted raw-unit OLS with match intercepts.

The primary width hypothesis alone receives the frozen status tree: invalid for
scientific/QC failure; supported when its point and two-sided 95% interval are
strictly positive, at least 6/7 match estimates and all 7/7 leave-one-match-out
estimates are positive, and the unchanged signed-movement trim retains positive
sign and 50–150% magnitude; mixed for a positive point estimate that misses any
support gate; not supported for every other valid result. If mixed or not
supported, stop without trying area, hull, pairwise entropy, orientation,
line-specific width, subgroups, or alternative directions.

## Proposed response-mode figure

Use one football-first figure with four columns for the canonical 5 m attacker
movements: goalward, outward, away from goal, and inward. Show the attacker
arrow above three separate rows: signed goalward defensive-centroid movement,
pitch-axis width and depth change, and the established localized D1–D3 minus
D4–D7 defender-relative path contrast. Each row should show predicted physical
units with its own 95% interval and observed IQR; the rows must not share a
normalized response scale or be added into a total. A small geometry key should
make clear that width reduction is lateral narrowing in the canonical pitch
axes, not intrinsic compression, and that rotation or shear can cross channel
boundaries. The figure is specified prospectively here and is not generated in
this design-only pass.

## Provider portability

Centroid, width, depth, and the established local path require only complete
outfield coordinates, pitch dimensions, direction, identity, and time support.
They are therefore mechanically compatible with the now-governed SkillCorner
adapter at 10 Hz, subject to the already documented broadcast
detected/extrapolated and identity limitations. No SkillCorner response-mode
outcome is opened here. A SkillCorner replication would require its own
prospective cadence/smoothing and publication governance after IDSSE closure.

## Novelty and Sloan value

Centroid translation, width, depth, stretch, area, and coordination are
established football-tracking methods; this design does not claim their
invention. The potentially useful contribution is the prospectively governed
combination of a replicated attacker-direction representation, separate
football-readable response channels, match/leave-one-out stability, and an
explicit refusal to treat localized movement as mechanism or value.

If supported, the result could sharpen the paper from “outward movement has a
larger localized association” to “different movement directions are associated
with different observed geometric response forms.” It still could not say that
one direction caused, improved, or tactically induced a response. If the width
hypothesis fails, the mechanism branch closes before Sloan and the replicated
outward–goalward asymmetry remains real but mechanistically unresolved.

Estimated future execution cost is **5–8 weekly allowance points** using the
existing IDSSE observations and compact governed outputs.
