# Defender-relative replay display-scale audit v2

**Status:** frozen before the v2 response-free score audit

**Purpose:** resolve the v1 display-scale decision using one bounded higher
candidate set. This is visualization QA only. It does not change the committed
score, renderer, demo passage, or any scientific claim.

## Inherited authority

V2 binds to the closed v1 protocol, configuration, aggregate result, source
identities, final hash ledger, implementation, and tests. V1 classified
`D_UNRESOLVED` because 6.0 m produced 5.037580561% player saturation, narrowly
above the frozen 5% threshold.

The reference population is unchanged: both teams and both periods from public
Metrica Sample Games 1 and 2, evaluated as 18 stable-lineup native-25-Hz runs.
No events, ball data, outcomes, research anchors, attacker direction, ranks,
SkillCorner data, or Game 3 may be read.

The score remains the unchanged raw-metre trailing two-second defender-relative
path with a centered seven-frame mean. Quantiles use NumPy's linear method.
Saturation is strictly `raw > ceiling`.

## Frozen candidates and decision

The only v2 candidates are 6.25, 6.50, and 7.00 metres. No adaptive or
additional candidate may be introduced after execution begins.

Select the lowest candidate satisfying both:

1. player saturation at most 5% across all 5,713,060 supported player-frames;
2. team-mean saturation at most 1% across all 571,306 supported team-frames.

Classify exactly one of:

- `A — FREEZE 6.25 M`;
- `B — FREEZE 6.50 M`;
- `C — FREEZE 7.00 M`;
- `D — UNRESOLVED` if none qualifies.

Perceptual bins remain:

- `x < 0.25c`;
- `0.25c <= x < 0.75c`;
- `0.75c <= x <= c`;
- `x > c`.

For every candidate report the same player, team-frame, and perceptual-spread
statistics as v1. Counts must reproduce the v1 supported population exactly or
the v2 audit is invalid.

## Secondary fixed-demo check

Only after A, B, or C is assigned, evaluate that ceiling on the unchanged
Metrica Sample Game 2 interval 2326.04–2346.04 s. Report displayed player
saturation, affected frames, and team-meter saturation. Bounded untracked visual
QA may use only the fixed `t=-10`, `t=0`, and `t=+10` snapshots. Do not
regenerate the GIF.

A selected ceiling is frozen consistently for a future GIF colorbar, defender
fill transform, team meter, and static diagnostic y-axis. Raw scores remain
unchanged and values above the ceiling require visible saturation disclosure.

## Publication boundary

Publish aggregate QA, provenance, QC, and hashes only. Do not serialize score
rows, identities, coordinates, timestamps, or frame IDs. Do not update renderer
defaults, regenerate public media, or build the notebook in this audit.
