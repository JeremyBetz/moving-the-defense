# Continuous Attacking Movement v1 — Held-Out Game 2 Result

**Classification:** **A — replicated under the frozen within-provider held-out protocol**

**Protocols:** [`attacking_continuous_movement_v1.md`](../protocols/attacking_continuous_movement_v1.md) and [`attacking_continuous_movement_game2_heldout_v1.md`](../protocols/attacking_continuous_movement_game2_heldout_v1.md)

**Scope:** Metrica Sample Game 2 only. The frozen Stage-A support registry was consumed unchanged. No defender coordinate, defensive outcome, event, possession, tactical label, attacker-to-defender bridge, or Game 3 data entered the execution or interpretation.

## 1. Held-out question and chronology

Can the continuous attacker-only geometric representation that qualified on development Game 1 retain its mathematical behavior and frozen 25-to-10 Hz robustness on held-out Game 2?

The representation and all gates were frozen before Game 2 access. A separately committed Stage-A audit then classified raw Game 2 trajectory support **READY**, freezing 2,093,028 valid raw outfield rows in 134 maximal support segments. This execution was the first authorized calculation of Game 2 continuous features. It did not rediscover or revise support.

## 2. Representation execution

At a period-reset 0.20 s evaluation grid, the implementation applied the frozen centred seven-frame mean within each valid 25 Hz support segment. It retained signed canonical x/y displacement, travelled path length, and derived straightness over 2 s primary and 1/4 s sensitivity windows. Primary output used no interpolation, clipping, epsilon denominator, low-speed cutoff, direction normalization, period crossing, or support repair.

Twenty-four outfield players were represented. Of 48 available player-periods, 44 supplied at least one eligible observation at each window.

| Window | Eligible observations | Player-periods | Evaluation-grid player-time | Frozen registry/boundary | Raw support invalid | Smoothing edge | Before period |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 s | 417,872 | 44 | 83,574.4 s | 146,484 | 112,900 | 72 | 240 |
| 2 s | 417,309 | 44 | 83,461.8 s | 146,827 | 112,880 | 72 | 480 |
| 4 s | 416,199 | 44 | 83,239.8 s | 147,497 | 112,840 | 72 | 960 |

Player-time is overlapping evaluation-grid exposure, not independent sample duration.

## 3. Feature summaries

Values are median [IQR] and range in metres except straightness.

| Window | $\Delta x$ | $\Delta y$ | Displacement | Path | Valid straightness |
|---:|---:|---:|---:|---:|---:|
| 1 s | -0.003 [-0.969, 0.937], -9.071–8.630 | -0.003 [-0.704, 0.703], -8.032–8.506 | 1.414 [0.872, 2.492], 0–10.672 | 1.429 [0.899, 2.515], 0–10.679 | 0.9968 [0.9845, 0.9993], 0.0058–1 |
| 2 s | -0.006 [-1.901, 1.834], -17.715–16.875 | -0.006 [-1.364, 1.361], -15.122–16.030 | 2.785 [1.689, 4.825], 0–17.861 | 2.894 [1.853, 4.975], 0–17.995 | 0.9872 [0.9375, 0.9973], 0.0057–1 |
| 4 s | -0.021 [-3.611, 3.456], -30.971–30.931 | -0.014 [-2.532, 2.526], -26.420–30.566 | 5.346 [3.125, 8.843], 0–34.155 | 5.997 [3.908, 9.833], 0–34.176 | 0.9459 [0.8002, 0.9884], 0.0013–1 |

Zero path and therefore invalid straightness occurred in 935/417,872 observations at 1 s (0.2238%), 866/417,309 at 2 s (0.2075%), and 746/416,199 at 4 s (0.1792%). Nonfinite counts were zero.

## 4. Descriptive Game 1 comparison

Game 1 and Game 2 primary medians were close descriptively: 2 s path was 2.920 m versus 2.894 m, displacement 2.807 m versus 2.785 m, and valid straightness 0.9883 versus 0.9872. At 1/2/4 s, Game 2 zero-path rates (0.224%/0.208%/0.179%) were slightly higher than Game 1 (0.143%/0.131%/0.108%). Full medians, quartiles, ranges, and zero-path rates are saved in `game1_game2_descriptive_comparison.csv`.

Different football matches may legitimately produce different movement distributions. The held-out replication target was measurement behavior, not identical football behavior; none of these distribution comparisons was a validation gate.

## 5. Mathematical QC, fixtures, and invariances

All 36 window-specific mathematical checks had zero violations: identity uniqueness, support linkage, finite values, nonnegative path/displacement, path at least displacement, straightness bounds and null validity, and both zero-path rules. Every feature observation linked to the frozen Stage-A segment that authorized it; no period or segment crossing occurred.

All 14 frozen fixtures passed, including stationary, straight, accelerating, curved, cut, out-and-back, low-speed, stop/restart, support-break, smoothing/grid, identity, and frequency cases. Translation, rotation, x/y mirror, traversal reversal, and frequency-equivalent invariance/equivariance checks all passed.

## 6. Frozen 25-to-10 Hz diagnostic

The diagnostic 10 Hz trace was constructed only by linear interpolation between adjacent supported samples of the same frozen 25 Hz smoothed trajectory. It tests temporal resampling of the same observed trajectory; it does **not** establish equivalence to a native independent 10 Hz provider.

| Window | Observable | Signed bias | Median absolute error | p95 absolute error | Relative median / p95 / $n$ | Result |
|---:|---|---:|---:|---:|---:|:---:|
| 1 s | $\Delta x$ | $1.57\times10^{-17}$ m | 0 m | $1.80\times10^{-13}$ m | — | Pass |
| 1 s | $\Delta y$ | $-6.65\times10^{-17}$ m | 0 m | $1.81\times10^{-13}$ m | — | Pass |
| 1 s | Path | -0.000465 m | 0.000104 m | 0.001614 m | 0.00398% / 0.06546% / 295,958 | Pass |
| 1 s | Straightness | 0.000579 | 0.000069 | 0.002549 | — | Pass |
| 2 s | $\Delta x$ | $3.24\times10^{-17}$ m | 0 m | $3.18\times10^{-13}$ m | — | Pass |
| 2 s | $\Delta y$ | $-1.30\times10^{-16}$ m | 0 m | $3.02\times10^{-13}$ m | — | Pass |
| 2 s | Path | -0.000928 m | 0.000277 m | 0.002906 m | 0.00714% / 0.10675% / 371,265 | Pass |
| 2 s | Straightness | 0.000454 | 0.000089 | 0.001891 | — | Pass |
| 4 s | $\Delta x$ | $7.51\times10^{-17}$ m | 0 m | $4.97\times10^{-13}$ m | — | Pass |
| 4 s | $\Delta y$ | $-2.73\times10^{-16}$ m | 0 m | $4.43\times10^{-13}$ m | — | Pass |
| 4 s | Path | -0.001848 m | 0.000770 m | 0.005191 m | 0.01175% / 0.14382% / 400,422 | Pass |
| 4 s | Straightness | 0.000343 | 0.000109 | 0.001407 | — | Pass |

Eligibility matched exactly: 417,872/417,872 at 1 s, 417,309/417,309 at 2 s, and 416,199/416,199 at 4 s (100% each), with zero mismatches. Thus all 15 independently required observable-by-window gates passed.

## 7. Deterministic reproduction and classification

An independent complete rerun produced the same governed file list and byte-identical SHA-256 hashes for all 19 scientific outputs. The final mechanical classification is therefore **A**: frozen support, hard QC, fixtures, invariances, deterministic reproduction, and every frozen frequency gate passed.

## 8. Supported interpretation and claim boundary

> **The frozen continuous attacker-only geometric representation replicated across both Metrica sample matches under a prospectively frozen within-provider held-out protocol.**

This validates the representation's governed measurement behavior within the Metrica sample environment. It does not validate native-provider frequency equivalence, movement episodes, tactical run types, threat, defensive response, opponent association, attacker causation, relational reconfiguration, gravity, off-ball value, or football quality.

## 9. Relationship to prior discrete attempts

Scalar speed valleys retained lower-speed movement but fragmented heavily. Prominence reduced fragmentation but overmerged directionally complex movement. Frozen two-dimensional velocity change points produced overwhelming minimum-duration fragmentation and frequency sensitivity. Continuous v1 avoids imposing universal episode boundaries and has now passed the project's frozen within-provider held-out measurement-validation criteria. This does not show that discrete movement is impossible or that continuous geometry is universally superior.

## 10. Next-stage implication

The continuous attacker representation has satisfied its frozen within-provider held-out prerequisite. A later pass may return to the main scientific question and freeze the attacker-to-defender bridge. No such protocol was designed or executed here. Game 3 remains untouched and is not automatically designated for that bridge.

## 11. Governed artifacts

Source: `src/attacking_continuous_movement_game2_v1.py`. Tests: `tests/test_attacking_continuous_movement_game2_v1.py`. Machine-readable support, feature, comparison, QC, fixture, provenance, hash, reproduction, and classification artifacts are under `outputs/attacking_continuous_movement_game2_v1/`.
