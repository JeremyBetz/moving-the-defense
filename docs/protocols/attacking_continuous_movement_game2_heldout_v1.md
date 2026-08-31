# Continuous Attacking Movement v1 — Held-Out Game 2 Protocol

**Protocol status:** frozen before any Game 2 access

**Freeze date:** 2026-08-31

**Held-out match:** Metrica Sample Game 2

**Required first checkpoint:** raw canonical trajectory-support QC and registry freeze only

**Scientific boundary:** within-provider held-out replication of the attacker-only measurement; no defenders, defensive outcomes, tactical labels, or attacker-to-defender bridge

## 1. Held-out question

> Does the exact frozen continuous attacker-only geometric representation remain deterministically valid and numerically robust when applied unchanged to a previously untouched Metrica match?

Game 2 is a strict within-provider held-out replication. It cannot improve the construct, tune thresholds, compare playing styles, select attractive examples, or test attacker–defender relationships.

## 2. Inherited representation — no changes permitted

Game 2 inherits [continuous attacker movement protocol v1.0](attacking_continuous_movement_v1.md) and its [Game 1 implementation/result](../results/attacking_continuous_movement_game1_v1.md) unchanged:

- 2.0 s primary trailing window;
- 1.0 s and 4.0 s sensitivities, with no other durations;
- exact period-specific 0.20 s grid aligned to the first canonical frame's `time_period_s`, tolerance $10^{-9}$ s, and no nearest-frame fallback;
- fixed 105 × 68 m canonical coordinates, centred origin, +x right, +y up, with no attacking/goal/possession/ball/team/period normalization;
- centred seven-frame arithmetic mean at native 25 Hz, requiring all seven raw rows, with three-frame edge loss and no primary interpolation;
- `delta_x_m`, `delta_y_m`, `path_length_m`, `straightness`, and `straightness_valid` with the exact frozen formulas;
- zero path gives zero displacement/path, null straightness, and `straightness_valid == false`;
- positive path with zero displacement gives valid straightness zero;
- `Float64`, chronological within-window path summation, no epsilon, clipping, speed cutoff in feature construction, or repair;
- identical mathematical, fixture, invariance, output, provenance, and deterministic-rerun requirements; and
- the exact 25→10 Hz sensitivity construction and thresholds in Section 7.

Game 1 scientific files, hashes, protocol, source behavior, and result remain historical evidence. Game 2 requires a separate implementation/configuration wrapper or explicit match parameter, but no change to feature semantics.

## 3. Mandatory staged firewall

Game 2 access must occur in two separately committed passes.

### Stage A — trajectory-support QC only

Stage A may open Game 2 solely to construct the canonical table and audit raw support, clocks, roster identities, and trajectory continuity under Sections 4–6. It may not smooth positions, compute any 1/2/4 s feature, build the 0.20 s feature grid, compare feature distributions, resample features to 10 Hz, or inspect ball/events/defenders/outcomes.

Stage A must save and commit:

1. canonical/input/protocol/source hashes and adapter provenance;
2. roster/player-period inclusion and raw support counts;
3. frame/time/period continuity results;
4. deterministic identity-duplication and raw-jump diagnostics;
5. every candidate defect and its exact rule outcome;
6. a versioned Game 2 trajectory-validity registry, including an explicitly empty registry if no match-specific exclusions exist;
7. a machine-readable registry hash; and
8. a signed-off `READY` or `BLOCKED` decision.

The checkpoint must be committed and pushed before Stage B. **Stage A is required.** It cannot be skipped because the Game 1 history demonstrated that complete frames and coordinates can still conceal identity/trajectory discontinuity.

### Stage B — held-out representation execution

Stage B may occur only after a clean `READY` Stage-A checkpoint. It applies the frozen representation and registry, performs the unchanged fixtures/frequency gates and independent rerun, and classifies Game 2 mechanically. Stage B must not alter the Stage-A registry.

If Stage A is `BLOCKED`, no features are generated. A scientific ambiguity requires a pre-feature protocol amendment and new checkpoint; it cannot be resolved after aggregate features are visible.

## 4. Universal automatic support rules

For every rostered outfield player, period, and raw row, apply these rules before any Game-2-specific registry:

1. require canonical `entity_type == player`, `is_goalkeeper == false`, `support_state == observed`, `is_present == true`, and `coordinate_valid == true`;
2. require finite canonical x/y and non-null match, period, provider frame, both clocks, team, and player identity;
3. require unique `(match_id, period, frame_id_provider, player_key)` rows;
4. require strictly increasing provider frames and clocks within each observed player-period run;
5. require consecutive provider-frame succession and $0.04\pm10^{-9}$ s increments for this 25 Hz Metrica match;
6. split support at every missing/invalid row, period boundary, unexpected frame/time interval, or observed/unobserved transition;
7. never bridge a substitution/entry/exit boundary inferred from support; provider inactivity is not tactically interpreted;
8. retain finite coordinates outside nominal pitch bounds as the canonical contract requires, but count/report them separately;
9. never interpolate, pad, extrapolate, clip, winsorize, or repair raw coordinates; and
10. require the final Stage-A registry before smoothing or feature construction.

Ball state, possession, events, opponent identity, player position/role beyond goalkeeper exclusion, and all football outcomes are prohibited.

## 5. Deterministic trajectory-integrity diagnostics

Stage A runs the following rules on raw canonical coordinates only. Thresholds are frozen now and may not be changed after Game 2 opens.

### 5.1 Hard raw-jump link

For consecutive observed rows $i-1,i$ with the expected 0.04 s interval, compute

$$
v^{raw}_i=\frac{\|\mathbf p_i-\mathbf p_{i-1}\|_2}{0.04}.
$$

A link is a **hard raw-jump link** when $v^{raw}_i>20.0$ m/s. Equality at exactly 20.0 m/s does not flag. The 20 m/s ceiling is a conservative trajectory-continuity engineering rule, not a football-performance threshold and not a feature inclusion criterion.

For every hard link:

- invalidate both endpoint raw rows $i-1$ and $i$;
- split support across the link; and
- persist player, team, period, frames, times, coordinates, displacement, and raw speed.

If a contiguous observed trace segment is bounded by a hard raw-jump link on both its entry and exit sides, invalidate the **entire bounded segment**, including both bounding-link endpoints. Identity/position support within such a teleport-and-return segment is unresolved. A segment touching the beginning or end of an observed run is not wholly removed merely because its one boundary is a hard link; only the two link endpoints are automatically invalid, and the remaining side becomes a separate support run.

Adjacent/overlapping hard-link invalid intervals are merged. Smoothing later expands support loss mechanically by its governed three raw frames on each side; Stage A does not add that expansion to the raw registry.

### 5.2 Sustained exact same-team duplication

At one provider frame, two distinct players on the same team are exactly duplicated when both canonical `Float64` x and y compare equal with no rounding. A **sustained duplicate run** is at least five consecutive expected provider frames (0.20 s) in which the same two player identities are exactly duplicated.

Invalidate both players' raw rows for the full maximal sustained duplicate run. Runs shorter than five frames are counted and reported but are not excluded. Cross-team equality is reported but is not an identity exclusion because opposing players can physically coincide. Near-equality receives no invented distance threshold.

Exact equality by itself outside this duration rule is not proof of invalidity. The five-frame rule is a prospective provider-identity support convention, not a tactical or biological claim.

### 5.3 Missingness, coordinate validity, and discontinuities

Missing/nonfinite/provider-invalid rows are already invalid under Section 4 and split support. A coordinate outside pitch bounds, high but sub-20 m/s raw speed, isolated exact duplicate shorter than five frames, or visually unusual path is **diagnostic only** and cannot be excluded post hoc.

Stage A reports:

- missing/absent/invalid rows by player and period;
- all unexpected frame/time intervals;
- all raw speeds above 10 m/s descriptively, while only `>20 m/s` governs exclusion;
- all exact same-team duplicate runs of any length;
- all out-of-bounds finite coordinates; and
- observed-run entry/exit boundaries.

The 10 m/s report threshold does not alter support and cannot be promoted after inspection.

## 6. Game-2-specific registry governance

The registry is the deterministic union of:

1. raw rows invalid under universal support rules;
2. hard-jump endpoints and wholly bounded hard-jump segments under Section 5.1; and
3. maximal sustained same-team duplicate runs under Section 5.2.

Each registry row/interval must contain match, team, player, period, inclusive provider-frame bounds, inclusive clock bounds, rule code, triggering diagnostic IDs, and an explanation generated from the rule—not football judgment. Intervals are sorted and merged only when they overlap or touch for the same player/period/rule set. The unmerged trigger table is also preserved.

No manual visual selection can add or remove an interval. Raw trajectory plots may verify serialization and rule application but cannot govern the registry.

An unresolved defect exists only when (a) a canonical schema/identity/frame/time invariant fails without receiving a deterministic status, (b) two frozen rules assign contradictory statuses, or (c) provider serialization/provenance directly contradicts the canonical identity/support record. A visually unusual path, sub-threshold jump, short duplicate, or raw-trajectory plot is not by itself an unresolved defect and remains supported under v1.

If one of those exact unresolved conditions occurs, Stage A is `BLOCKED`. Do not guess a boundary, exclude a visually suspicious passage, or compute features. Amend the support protocol prospectively while still outcome/feature-blind, document why the existing rules were insufficient, commit/push the amendment and registry, and only then reconsider Stage B. This stop rule resolves rather than conceals residual researcher disagreement.

The Stage-A `READY` condition is exact:

- canonical schema and provenance pass;
- every raw row has one deterministic support/registry status;
- all diagnostic triggers reproduce byte-for-byte;
- all generated registry intervals follow the frozen union rules;
- no unresolved defect remains; and
- an independent rerun reproduces the registry and QC outputs exactly.

## 7. Unchanged 25→10 Hz robustness gates

Use the valid seven-frame-smoothed 25 Hz trajectory as reference. Construct the 10 Hz diagnostic only by linear interpolation between adjacent valid smoothed positions inside the same support run. Never interpolate across registry, missingness, period, entry/exit, frame/time, or smoothing breaks. Evaluate identical 1/2/4 s physical windows at exact common 0.20 s endpoints.

Every criterion passes inclusively and separately at all three windows:

| Observable | Frozen criterion |
|---|---|
| `delta_x_m` | absolute signed bias ≤0.010 m; median absolute error ≤0.020 m; p95 absolute error ≤0.050 m |
| `delta_y_m` | absolute signed bias ≤0.010 m; median absolute error ≤0.020 m; p95 absolute error ≤0.050 m |
| `path_length_m` | signed bias in [−0.050, +0.010] m; median absolute error ≤0.050 m; p95 absolute error ≤0.150 m |
| Path where 25 Hz reference ≥1 m | median relative error ≤2%; p95 relative error ≤5% |
| `straightness` valid on both sides | absolute signed bias ≤0.010; median absolute difference ≤0.015; p95 absolute difference ≤0.050; zero validity mismatches |
| Eligibility | at least 99.9% of 25 Hz eligible IDs matched; every mismatch explained by deterministic resampling support-edge semantics |

Use 10 Hz minus 25 Hz for signed errors, NumPy linear quantiles, no epsilon for relative errors, and the exact Game 1 null-validity behavior. Correlation and maximum errors remain supplemental rather than gates.

The diagnostic tests resampling of the same observed trajectory. Even a pass does not establish native-10-Hz or cross-provider equivalence.

## 8. Replication target and descriptive distributions

Replication concerns measurement properties:

- deterministic computation and output hashes;
- governed raw/smoothing/window support;
- exact feature formulas and mathematical invariants;
- unchanged fixtures and geometric transformations;
- numerical stability and zero/null semantics; and
- every frozen frequency gate.

Game 2 feature medians, IQRs, ranges, signs, straightness distribution, movement amount, support count, player/team/period distribution, and zero-path rate are **not required to match Game 1**. They must be reported descriptively to expose implementation degeneracy, but football matches may differ. No equal-distribution, style, player-quality, or visually attractive-example gate is permitted.

## 9. Hard QC and held-out A/B/C classification

Stage B hard QC inherits every Game 1 requirement and additionally requires the committed Stage-A registry hash and `READY` decision. The Game 2 implementation must independently rerun into a temporary location and compare all governed pre-classification outputs byte-for-byte before final classification.

- **A — within-provider held-out replication:** Stage A is `READY`; all support governance and hard QC pass; all unchanged fixtures/invariances pass; deterministic reproduction passes; mathematical/zero/null invariants pass; and every frozen frequency gate passes at 1, 2, and 4 s.
- **B — robustness did not fully replicate:** Stage A is `READY`; hard QC/support/fixtures/reproduction pass; the representation remains computable and interpretable; but at least one empirical frequency gate fails. Stop without tuning.
- **C — invalid held-out realization:** Stage A is `BLOCKED` or unresolved identity/support semantics reach attempted execution; or hard QC, fixtures, deterministic reproduction, mathematical invariants, support semantics, or substantial valid-support usability fails. Stop without rescue.

There is no visual, tactical, distribution-similarity, or football-outcome override.

## 10. Claims after Game 2

If Game 2 is A, the maximum claim is:

> The frozen continuous attacker-only representation replicated across two Metrica sample matches under a within-provider held-out protocol, preserving deterministic support, geometry, and the prospectively fixed 25 Hz/10 Hz resampling-robustness criteria.

This would be within-provider held-out replication—not cross-provider validation, native-10-Hz equivalence, general football universality, tactical movement validity, defensive influence, opponent association, intention, causation, gravity, or off-ball value.

If Game 2 is B, Game 1 numerical robustness did not fully replicate and no tuning is permitted. If C, the representation/support realization failed its held-out hard requirements.

## 11. Consequence for the future bridge

Only Game 2 A makes the attacker representation sufficiently validated for the project to return to designing the main bridge:

> attacker geometry over $[t-w,t]$ → subsequent defender focal-relative geometry over $[t,t+h]$.

This protocol does not select $h$, defenders, attacker–defender pairings, controls, outcomes, or bridge statistics. If Game 2 is B or C, bridge work using this representation remains blocked pending scientific review.

## 12. Game 3 discipline

Metrica Sample Game 3 remains untouched regardless of the Game 2 result. It is not automatically the next validation match, bridge dataset, or tuning resource. A later explicit protocol must justify any access.

## 13. Freeze and anti-tuning rule

Before Stage A, record the protocol hash and confirm the Game 1 protocol/result hashes. After Game 2 opens, no feature, window, grid, coordinate rule, smoother, support threshold, duplicate duration, raw-jump ceiling, registry algorithm, frequency gate, invariant, or A/B/C rule may change under held-out v1.

Stage A may reveal that the predeclared support procedure is insufficient. In that case stop before any feature aggregate. A documented pre-feature amendment may clarify support semantics, but the current held-out version is not silently edited and no Game 2 representation result may exist before the amended freeze.
