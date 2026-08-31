# Continuous Attacking Movement v1 — Game 1 Result

**Classification:** **A — qualifies for a separately frozen held-out Game 2 evaluation**

**Frozen protocol:** [`attacking_continuous_movement_v1.md`](../protocols/attacking_continuous_movement_v1.md)

**Scope:** Metrica Sample Game 1 development only. Game 2 and Game 3 were not opened. No defender coordinate, defensive outcome, event, possession, ball relationship, tactical label, or attacker-to-defender bridge entered execution or interpretation.

## 1. Question

Can the prospectively frozen continuous attacker-only representation be computed deterministically with valid trajectory support and preserve its physical geometry when the same smoothed Game 1 trace is sampled at 25 Hz and 10 Hz?

The representation retains signed canonical x/y displacement, travelled path length, and straightness over 2 s primary and 1/4 s sensitivity windows. It imposes no movement-episode boundaries.

## 2. Implementation and pre-interpretation QC

All frozen fixtures passed before Game 1 aggregation. An initial internal implementation used subtraction of long cumulative path totals as a computational shortcut. The frozen formula instead requires chronological summation inside each window; cancellation at approximately $10^{-11}$ m triggered the prospectively frozen $10^{-12}$ m invariant. The shortcut was removed, preliminary artifacts were replaced, and the exact frozen direct-sum formula was rerun. No feature, support rule, window, tolerance, gate, or protocol text changed.

The final source uses canonical tracking contract v1.0.0, the historical centred seven-frame mean, the frozen trajectory registry, the exact 0.20 s period grid, and direct `Float64` step summation. Primary 25 Hz output contains no interpolation, clipping, epsilon denominator, low-speed cutoff, period crossing, or trajectory repair.

## 3. Support and eligibility

The canonical match contains 26 outfield player identities and 52 possible player-period combinations. Forty-four player-periods contribute at least one eligible evaluation. Entire Home 3 period 2 and Away 22 period 2 traces and Home 10 period-1 frames 2911–2945 remain excluded exactly as frozen.

| Window | Candidate observations | Eligible | Eligible player-periods | Evaluation-grid player-time | Before period | Smoothing edge | Frozen registry | Raw support invalid |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 s | 754,052 | 557,856 | 44 | 111,571.2 s | 260 | 104 | 29,495 | 166,337 |
| 2 s | 754,052 | 557,631 | 44 | 111,526.2 s | 520 | 104 | 29,490 | 166,307 |
| 4 s | 754,052 | 557,181 | 44 | 111,436.2 s | 1,040 | 104 | 29,480 | 166,247 |

“Player-time” is eligible 0.20 s grid exposure, not independent sample duration: adjacent windows overlap heavily.

## 4. Frozen fixture and invariance results

All 14 fixture/support checks passed: stationary, constant-speed straight, accelerating straight, gradual quarter-circle, sharp cut, out-and-back, low-speed drift, stop/restart, frequency-equivalent straight movement, seven-frame smoothing/edges, support break, period-grid reset, stable identity, and invalid-duplicate rejection.

All five transformation checks passed. Path and straightness were invariant under translation, rotation, x/y mirror, and reversal. Signed displacement was translation-invariant and transformed equivariantly under rotation/mirror; exact traversal reversal negated it.

## 5. Representation summaries

Values are median [25th, 75th percentile], followed by the range. x/y are signed canonical pitch components.

| Window | $\Delta x$ m | $\Delta y$ m | Displacement m | Path m | Straightness among valid rows |
|---:|---:|---:|---:|---:|---:|
| 1 s | 0.0031 [−0.9644, 0.9621], −8.8031–8.9519 | −0.0026 [−0.7146, 0.6782], −11.1008–9.3007 | 1.4257 [0.8465, 2.5635], 0–11.1511 | 1.4411 [0.8709, 2.5858], 0–12.9138 | 0.99713 [0.98540, 0.99941], 0.00674–1.00000 |
| 2 s | 0.0072 [−1.8909, 1.8851], −17.4468–17.4797 | −0.0060 [−1.3886, 1.3172], −17.1234–16.0065 | 2.8065 [1.6409, 4.9652], 0–17.9096 | 2.9202 [1.7958, 5.1200], 0–17.9125 | 0.98826 [0.94073, 0.99763], 0.00387–1.00000 |
| 4 s | 0.0138 [−3.5739, 3.5669], −33.3168–33.4740 | −0.0137 [−2.5827, 2.4439], −31.2100–27.9073 | 5.3657 [3.0281, 9.0827], 0–34.3300 | 6.0536 [3.7876, 10.1130], 0–34.7790 | 0.94917 [0.80668, 0.98945], 0.00062–1.00000 |

No distribution is interpreted as a correct or desirable football pattern. Longer windows accumulate more travel and allow more returning/curved geometry, which is descriptive rather than tactical validation.

## 6. Stationary and mathematical behavior

| Window | Zero path | Rate | Invalid/null straightness | Nonfinite values | Path < displacement violations | Straightness range violations |
|---:|---:|---:|---:|---:|---:|---:|
| 1 s | 798 | 0.143048% | 798 | 0 | 0 | 0 |
| 2 s | 728 | 0.130552% | 728 | 0 | 0 | 0 |
| 4 s | 603 | 0.108223% | 603 | 0 | 0 | 0 |

Every zero path has null straightness and `straightness_valid == false`; no other row has invalid straightness. No epsilon or low-motion exclusion was used. Straightness is within $10^{-12}$ of one for 31, 9, and 3 valid rows at 1, 2, and 4 s respectively; this is not a pathological concentration.

## 7. Exact 25 Hz versus 10 Hz results

Errors are 10 Hz minus the 25 Hz reference. All comparisons use identical physical windows and exact common 0.20 s endpoints.

| Window | Observable | Denominator | Signed bias | Median absolute error | 95th-percentile absolute error | Additional relative metric | Pass |
|---:|---|---:|---:|---:|---:|---|:---:|
| 1 s | $\Delta x$ m | 557,856 | $5.225\times10^{-18}$ | 0 | $1.741\times10^{-13}$ | — | Yes |
| 1 s | $\Delta y$ m | 557,856 | $-1.738\times10^{-17}$ | 0 | $1.661\times10^{-13}$ | — | Yes |
| 1 s | Path m | 557,856 | −0.000410142 | 0.000085443 | 0.001354869 | $n=389{,}520$: median 0.003215%, p95 0.058864% | Yes |
| 1 s | Straightness | 557,058 | 0.000504278 | 0.000057876 | 0.002213160 | validity mismatches 0 | Yes |
| 1 s | Eligibility | 557,856 | — | — | — | 557,856/557,856 = 100% | Yes |
| 2 s | $\Delta x$ m | 557,631 | $1.229\times10^{-17}$ | 0 | $3.136\times10^{-13}$ | — | Yes |
| 2 s | $\Delta y$ m | 557,631 | $-4.115\times10^{-17}$ | 0 | $2.887\times10^{-13}$ | — | Yes |
| 2 s | Path m | 557,631 | −0.000819729 | 0.000234058 | 0.002451530 | $n=490{,}731$: median 0.005929%, p95 0.088945% | Yes |
| 2 s | Straightness | 556,903 | 0.000390881 | 0.000076119 | 0.001572987 | validity mismatches 0 | Yes |
| 2 s | Eligibility | 557,631 | — | — | — | 557,631/557,631 = 100% | Yes |
| 4 s | $\Delta x$ m | 557,181 | $3.500\times10^{-17}$ | 0 | $4.997\times10^{-13}$ | — | Yes |
| 4 s | $\Delta y$ m | 557,181 | $-9.806\times10^{-17}$ | 0 | $4.388\times10^{-13}$ | — | Yes |
| 4 s | Path m | 557,181 | −0.001638225 | 0.000668918 | 0.004276090 | $n=530{,}504$: median 0.010365%, p95 0.093293% | Yes |
| 4 s | Straightness | 556,578 | 0.000292250 | 0.000099579 | 0.001152350 | validity mismatches 0 | Yes |
| 4 s | Eligibility | 557,181 | — | — | — | 557,181/557,181 = 100% | Yes |

All 15 frozen gates pass. The largest individual path difference is about 0.492 m, but maxima were descriptive rather than frozen gates; the prospectively governed bias, median, p95, and relative-error criteria all pass. This tail remains a portability caution rather than a post-hoc failure criterion.

## 8. Deterministic reproduction

A clean second execution wrote to an independent temporary directory. Seventeen governed pre-classification files—including all support, feature, frequency-comparison, diagnostic, manifest, and hash artifacts—were byte-identical. [`reproduction_verification.json`](../../outputs/attacking_continuous_movement_game1_v1/reproduction_verification.json) records every paired SHA-256 digest.

## 9. Mechanical classification

- Hard QC: **pass**.
- Fixtures/invariance: **pass**.
- Mathematical/support invariants: **pass**.
- Deterministic reproduction: **pass**.
- Frozen frequency gates: **15/15 pass**.

Therefore Game 1 classifies **A** under the frozen decision tree.

## 10. Supported interpretation

> The frozen continuous attacker-only geometric representation is deterministically computable on Game 1, preserves governed support and geometry, and meets the prospectively frozen 25 Hz/10 Hz robustness criteria across the 1/2/4-second windows.

It qualifies for a separately designed and frozen held-out Game 2 evaluation. This is development feasibility, not external validation.

## 11. Prohibited interpretation

This result does not identify tactical runs, movement episodes, decoys, pinning, dragging, tracking, covering, handoffs, successful movement, defensive response, opponent association, intention, causation, gravity, off-ball value, or player/team quality. It does not establish native-10-Hz provider equivalence; the diagnostic resamples one valid 25 Hz trace.

## 12. Relationship to the discrete attempts

Scalar speed valleys retained lower-speed movement but fragmented heavily. Prominence reduced fragmentation but overmerged directionally complex movement. Frozen 2D velocity PELT controlled the historical merging diagnostic but produced overwhelming minimum-duration fragmentation and unstable boundary recall/F1/counts. Continuous v1 avoids the disputed requirement that every movement have a universal boundary. Its A result supports its own fixed-window geometry and portability gates; it does not prove universal superiority over discrete geometry.

## 13. Held-out status and next question

Game 1 satisfies the prerequisite for freezing a separate held-out Game 2 continuous-representation protocol. Game 2 was not opened in this pass, Game 3 remains closed, and no attacker-to-defender bridge was executed.

The next legitimate scientific question is whether this exact attacker-side representation reproduces under a prospectively frozen held-out Game 2 protocol before any relationship with defensive movement is tested.
