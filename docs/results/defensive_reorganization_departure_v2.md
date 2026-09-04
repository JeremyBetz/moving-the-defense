# Defensive Reorganization Departure v2 — IDSSE result

**Formal status:** **DRD APPLICATION FOUNDATION MIXED**

V2 corrected only the anchor-time attacking entity-support rule: the complete
event-defined current on-pitch attacking outfield set, rather than an invariant
ten-player set, supplies the ball-nearest exclusion. V1 remains historically
**INVALID before fitting**. V2 retained the v1 target, features, seven-match
nested Ridge validation, 1,000-row/90% support gates, classification, and stop
rules unchanged.

## Support and active-roster reconstruction

All common-sample gates passed. `J03WN1` retained 4,268 rows across 523 anchors
and 81 occupied 60-second blocks, covering both periods. Its valid active-set
construction comprised 869 ten-outfielder and 3,922 nine-outfielder candidate
anchors; every retained anchor required exact equality between event-defined
current players and complete seven-frame tracking support.

| Match | Common rows | Anchors | 60-s blocks | Period coverage |
|---|---:|---:|---:|---|
| J03WMX | 10,850 | 1,206 | 97 | P1 8–2,816; P2 8–3,000 |
| J03WN1 | 4,268 | 523 | 81 | P1 8–2,768; P2 8–2,840 |
| J03WOH | 9,853 | 1,095 | 92 | P1 8–2,764; P2 8–2,668 |
| J03WOY | 10,097 | 1,122 | 95 | P1 8–2,752; P2 8–2,928 |
| J03WPY | 10,913 | 1,213 | 98 | P1 8–2,756; P2 8–3,068 |
| J03WQQ | 8,682 | 988 | 94 | P1 8–2,760; P2 8–2,872 |
| J03WR9 | 10,142 | 1,127 | 93 | P1 8–2,720; P2 8–3,044 |

## Held-out prediction

E0's equal-match macro held-out MAE was **0.933017 m**. E1's was
**0.913141 m**, an absolute reduction of **0.019876 m** and a relative
improvement of **2.130%**. E1 improved all seven match MAEs; no match worsened.
The frozen 1,000-replicate paired bootstrap gave 2.126% [1.594%, 2.590%] and
0.019855 m [0.014739, 0.024504]. All outer-fold model selections used
`alpha = 100.0` and the direct solver.

| Match | E0 MAE (m) | E1 MAE (m) | E1 improvement |
|---|---:|---:|---:|
| J03WMX | 0.921181 | 0.895809 | 2.754% |
| J03WN1 | 0.913732 | 0.895445 | 2.001% |
| J03WOH | 0.906185 | 0.893904 | 1.355% |
| J03WOY | 0.946913 | 0.923892 | 2.431% |
| J03WPY | 0.918105 | 0.904703 | 1.460% |
| J03WQQ | 0.975465 | 0.950591 | 2.550% |
| J03WR9 | 0.949540 | 0.927642 | 2.306% |

The frozen SUPPORT gate required at least 3.0% macro improvement, improvement
in at least six matches, no 10% match-level worsening, and at least one stable
context family. The first condition failed; the other stated performance
conditions passed. Thus the exhaustive frozen status is MIXED.

## Context-family ablations

Removing start-position or ball-geometry features worsened E1 macro MAE by
1.054% and 1.117%, respectively, and worsened all seven matches. Both meet the
frozen stability rule. Removing movement direction worsened macro MAE by 0.311%
across all seven matches and does not meet the 1.0% materiality threshold.
These are held-out predictive associations, not mechanisms or tactical
interpretations.

## Stop rule and boundary

Because the formal status is MIXED, DRD was not computed or named from
residuals. No passage was inspected, no retrieval board was generated, no
Metrica transport ran, no SkillCorner outcome was opened, and no player ranking
was created. The result does not establish tactical response, causation,
influence, marking, responsibility, disruption, quality, gravity, or off-ball
value.

All 11 compact governed outputs reproduced byte-for-byte in an independent
rerun. Provider-linked row-level eligibility and prediction tables remain
local-only; compact result files and hashes are in
`outputs/defensive_reorganization_departure_v2/`.
