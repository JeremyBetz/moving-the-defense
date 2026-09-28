# Ball-Alignment Reorganization Review v1

**Status:** closed descriptive application review

**Executed:** 2026-09-28

**Protocol:** [Ball-alignment reorganization review v1](../protocols/ball_alignment_reorganization_review_v1.md)

## Question

When possession-eligible rapid relational reorganization begins, how strongly
is the measured defender-relative movement directed toward the ball? This is a
review diagnostic, not a new scientific outcome or a tactical classification.

## Reference

The frozen public Metrica Games 1–2 population contained 282 eligible rapid
episodes, of which 270 had complete ball-alignment support. Team ballward
projection share had P25 **0.322059**, median **0.437381**, and P75
**0.545519**. Signed alignment had P25 **-0.046449**, median **0.186816**, and
P75 **0.404416**.

The strata were applied without visual tuning:

- low ballward: share at or below 0.322059;
- middle: share between 0.322059 and 0.545519;
- high ballward: share at or above 0.545519.

## Historical top-six audit

| Old rank | One-second rise (m) | Before / after (m) | Integrity | Impossible speeds | Swap suspicion | Ballward share | Signed alignment | Stratum |
|---:|---:|---:|---|---:|---:|---:|---:|---|
| 1 | 1.786 | 2.202 / 3.988 | Failed | 6 | 0 | 0.367 | 0.078 | Middle |
| 2 | 1.733 | 2.992 / 4.725 | Clean | 0 | 0 | 0.158 | -0.363 | Low |
| 3 | 1.561 | 2.793 / 4.355 | Failed | 9 | 0 | 0.358 | -0.048 | Middle |
| 4 | 1.513 | 3.954 / 5.467 | Clean | 0 | 0 | Unsupported | Unsupported | Unsupported |
| 5 | 1.472 | 1.903 / 3.376 | Clean | 0 | 0 | 0.389 | -0.049 | Middle |
| 6 | 1.419 | 5.046 / 6.465 | Clean | 0 | 0 | 0.730 | 0.687 | High |

All six were open-play passages under the frozen possession context. The old
rank 1 failed because six native player transitions exceeded 15 m/s. It did not
meet the separate identity-swap rule. The old rank 2 goalkeeper-distribution
passage was integrity-clean and strongly low ballward: most of the measured
relational movement was not directed toward the ball.

## Public contrast

The frozen selection rule retained the top integrity-clean low-ballward episode
and the top integrity-clean high-ballward episode. The low example was also the
top overall clean rapid rise, so no duplicate third example was added.

- Low ballward: one-second rise **1.733 m**, share **0.158**, signed alignment
  **-0.363**.
- High ballward: one-second rise **1.419 m**, share **0.730**, signed alignment
  **0.687**.

The diagnostics and replays were visually plausible. The low example showed
substantial within-unit movement with weak/opposed ball alignment; the high
example showed movement substantially toward the ball. Neither establishes
attacker causation, defensive quality, intent, effectiveness, or value.

The publication-safe [manifest and media](../../figures/presentation/ball_alignment_reorganization_review/manifest.json)
contain only aggregate audit records and the two deterministic examples. No
player identities, coordinates, raw tracking rows, or repaired trajectories are
published.
