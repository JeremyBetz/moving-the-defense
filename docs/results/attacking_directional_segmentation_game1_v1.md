# Attacking Directional Segmentation v1 — Game 1 Result

**Execution date:** 2026-08-31

**Development data:** Metrica Sample Game 1 only

**Frozen protocol:** [`attacking_directional_segmentation_v1.md`](../protocols/attacking_directional_segmentation_v1.md)

**Mechanical classification:** **B — hard QC passed, but multiple empirical gates failed**

## Question and firewall

This execution tested whether the frozen attacker-only partition of smoothed two-dimensional velocity could supply finite directional movement segments suitable for later held-out evaluation. It used canonical observed outfield-player coordinates, the frozen trajectory-validity registry, and no ball, event, possession, defender, opponent, outcome, or tactical information. Metrica Games 2 and 3 were not opened for attacker segmentation.

The complete Game 1 partition was produced before the frozen diagnostics were evaluated. No penalty, scale, threshold, duration, smoothing, support rule, or diagnostic was changed after outcomes were visible.

## Production inputs and partition

The empirical Game 1 radial velocity-noise scale was **0.016098810494 m/s**, estimated from **2,790,392** consecutive eligible velocity pairs. The synthetic fixture scale of 1.0 m/s was not used in production.

| Quantity | Result |
|---|---:|
| Eligible outfield players | 26 |
| Eligible segmented blocks | 45 |
| Supported velocity duration | 111,617.48 s (1,860.29 player-minutes) |
| Total regimes | 247,175 |
| Directional movement regimes | 217,151 |
| Low-motion regimes | 30,024 |
| Regimes per supported player-minute | 132.869 |

All 247,175 evaluated regimes have governed support, stay within one player/period/block, and form a contiguous non-overlapping partition of their eligible blocks.

## Descriptive geometry

| Quantity | Median | IQR | Range |
|---|---:|---:|---:|
| Duration (s) | 0.400 | 0.400–0.400 | 0.400–95.400 |
| Path (m) | 0.662 | 0.387–1.146 | 0.000–11.088 |
| Displacement (m) | 0.661 | 0.385–1.145 | 0.000–11.088 |
| Mean speed (m/s) | 1.493 | 0.904–2.701 | 0.000–19.038 |
| Displacement/path | 0.999 | 0.998–1.000 | 0.019–1.000 |
| Adjacent fitted-mean velocity-vector change (m/s) | 0.269 | 0.145–0.503 | 0.003–30.321 |

The duration quartiles all equal the frozen 0.40 s minimum. This concentration is the dominant empirical failure; it is not evidence of tactical movement units.

## Frozen diagnostics

### Fragmentation

| Quantity | Result |
|---|---:|
| Numerator | 246,679 |
| Denominator | 247,175 |
| Rate | **99.799332%** |
| Historical speed-valley reference | 42.22% |
| Frozen limit | ≤33.776% |
| Result | **FAIL** |

Component counts were 246,317 regimes at or below 1.5 s, 169,969 at or below 1 m path, and 87,766 at or below 0.5 m displacement. The composite uses the frozen union, not the sum.

### Merging/direction complexity

The restored direction component required both path at least 3 m and absolute heading change at least 180°.

| Quantity | Result |
|---|---:|
| Numerator | 547 |
| Denominator | 247,175 |
| Rate | **0.221301%** |
| Historical reference | 763/38,651 = 1.974076% |
| Frozen limit | ≤3.97% |
| Result | **PASS** |

Component counts were 24 long regimes, 522 low-displacement/path regimes, and one direction-change regime. These descriptions do not imply football meaning.

## Frozen 10 Hz sensitivity

The 10 Hz sensitivity began from the supported seven-frame-smoothed 25 Hz positions and followed the frozen interpolation and matching rules.

| Quantity | Result | Gate | Outcome |
|---|---:|---:|---|
| 25 Hz boundaries | 247,130 | — | — |
| 10 Hz boundaries | 195,625 | — | — |
| Matched boundaries | 193,956 | — | — |
| Unmatched 25 Hz | 53,174 | — | — |
| Unmatched 10 Hz | 1,669 | — | — |
| Precision | 0.991468 | ≥0.90 | **PASS** |
| Recall | 0.784834 | ≥0.90 | **FAIL** |
| F1 | 0.876132 | ≥0.90 | **FAIL** |
| Segment-count difference | 51,505 / 247,175 = 20.837463% | ≤10% | **FAIL** |

The median accepted boundary offset was 0.04 s; the maximum was 0.20 s within floating-point representation of the frozen tolerance.

## Decision

Hard QC passed. The merging/direction and 10 Hz precision gates passed. Fragmentation, 10 Hz recall, 10 Hz F1, and segment-count stability failed. Because merging/direction remained controlled and hard QC passed, the frozen decision tree assigns **B**, not C.

Compared with the scalar speed-valley audit, the directional method moved in the wrong direction on the dominant problem: fragmentation increased from 42.22% to 99.80%. Compared with the failed prominence candidates, which reduced fragmentation but overmerged, this method occupies the opposite failure extreme: it controls merging largely by creating overwhelmingly minimum-duration regimes. No alternative model or rescue analysis was run.

## Claim boundary

### Supported

> Under frozen Game 1 rules, the two-dimensional velocity change-point representation is reproducibly executable with valid support, but it produces an overwhelmingly minimum-duration, frequency-sensitive partition and does not qualify for held-out evaluation.

### Interpretation

The dominant failure is excessive boundary density rather than inappropriate merging. The result shows that changing from scalar speed valleys to this frozen directional mean-change objective does not by itself provide defensible finite attacking movement units.

### Speculation

Why the objective fails is not resolved here. No alternative scaling, penalty, duration, smoothing, or model may be selected from this result without a new prospective research decision.

The regimes are not tactical runs, intentional movements, off-ball actions, decoys, pins, drags, successful movements, defensive responses, attacker influence, or value. Game 2's held-out-protocol prerequisite is **not met**.

## Reproduction

Run:

```bash
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/attacking_directional_segmentation_game1_v1.py
```

Machine-readable outputs are in [`outputs/attacking_directional_segmentation_game1_v1/`](../../outputs/attacking_directional_segmentation_game1_v1/). The production and independent rerun matched byte-for-byte for every governed output and the manifest.
