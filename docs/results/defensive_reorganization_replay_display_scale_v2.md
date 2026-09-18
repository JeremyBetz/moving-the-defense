# Defender-relative replay display-scale audit v2

**Boundary:** response-free visualization QA inheriting the complete closed v1 population and rules.

**Decision:** `A_FREEZE_6_25_M`
**Selected ceiling:** 6.25

The unchanged scorer reproduced 5,713,060 supported player-frames and 571,306 supported team-frames across the same 18 stable-lineup Metrica runs.

## Candidate ceilings

| Ceiling | Player saturation | Team-mean saturation | Qualifies |
|---:|---:|---:|:---:|
| 6.25 m | 4.322% | 0.112% | yes |
| 6.50 m | 3.704% | 0.071% | yes |
| 7.00 m | 2.700% | 0.036% | yes |

## Reference distribution identity

Player median / p95 / p99 / maximum (m): 2.045556 / 6.012149 / 8.524744 / 86.683002.
Team median / p95 / p99 / maximum (m): 2.450241 / 4.233209 / 5.023939 / 17.938759.

## Fixed-demo secondary check

At 6.25 m, 134 of 2,510 displayed defender-frame values saturated (5.339%). Team means exceeded the ceiling in 0 displayed frames.

These are display-QA summaries, not football results. No score definition, scientific result, or renderer default changed.
