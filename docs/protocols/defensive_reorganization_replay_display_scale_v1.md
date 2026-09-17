# Defender-relative replay display-scale audit v1

**Status:** frozen before response-free score audit

**Purpose:** choose one fixed physical display ceiling for the retrospective
defender-relative replay. This is visualization QA, not a scientific outcome or
a change to the committed score.

## Reference population

Use public Metrica Sample Games 1 and 2, both teams and both periods. Include
all native 25 Hz tracking support without reading event files or conditioning on
open play, goals, shots, passes, possession, research anchors, attacker motion,
or any scientific response. Game 3 is excluded.

Home 11 and Away 25 are the governed goalkeeper identities. For each
game/team/period, split tracking into maximal regular-cadence runs with exactly
the same ten finite non-goalkeeper identities. A substitution, missing
coordinate, nonfinite coordinate, frame gap, or timestamp gap ends a run. Score
support never crosses a run, period, substitution, or gap.

Both teams are evaluated independently as the defending unit. A supported
"frame" in this audit means one supported defending-team frame. No row-level
score, identity, coordinate, timestamp, or frame identifier may be published.

## Score

Use `src/defensive_reorganization_replay.py` unchanged:

- source cadence: 25 Hz;
- centered seven-frame mean;
- trailing window: 2.0 seconds;
- raw score unit: metres;
- complete ten-defender support only;
- no interpolation, clipping, normalization, ranking, or response construction.

The frozen scorer SHA-256 is
`6b5f33de5a034ae4000270e847ebcefe0164b1df1d21d4f3a7ed8adf9bd24a8a`.

## Candidate ceilings and summaries

The only candidates are 4.0, 5.0, and 6.0 metres. Saturation is strictly a raw
value greater than the candidate ceiling. Quantiles use NumPy's linear method.

Report for supported player-frame scores: count, mean, median, 75th, 90th,
95th, 97.5th and 99th percentiles, and maximum. Report for supported team-frame
means: count, mean, median, 90th, 95th and 99th percentiles, and maximum. Also
report the key quantiles separately for Games 1 and 2.

For each ceiling report player saturation count and percentage; supported team
frames with at least 1, 2, and 5 saturated defenders; mean saturated defenders
per supported team frame; and team-mean exceedance count and percentage.

Perceptual bins partition supported player scores as:

- below 25%: `x < 0.25c`;
- middle: `0.25c <= x < 0.75c`;
- high but unsaturated: `0.75c <= x <= c`;
- saturated: `x > c`.

Also report clipped normalized display positions for the pooled player median,
75th, 90th and 95th percentiles.

## Selection rule

Select the lowest candidate satisfying both:

1. player-level saturation is at most 5% across the full reference population;
2. team-mean saturation is at most 1% of supported team frames.

If none qualifies, classify the audit as `D — UNRESOLVED`. No other ceiling may
be introduced in v1. A qualifying result is `A — FREEZE 4 M`, `B — FREEZE 5 M`,
or `C — FREEZE 6 M`.

## Secondary fixed-demo check

Only after applying the selection rule, evaluate the selected ceiling on the
already-approved Metrica Sample Game 2 display interval 2326.04–2346.04 s with
the existing score support. Report player saturation, supported frames with
saturation, and team-mean saturation. For visual QA, untracked snapshots may be
rendered only at `t=-10`, `t=0`, and `t=+10` relative to the fixed 2336.04 s
anchor. Do not regenerate a GIF or change renderer defaults in this audit.

## Publication and interpretation boundary

Publish aggregate QA summaries, source identities, QC, provenance, and hashes
only. These quantities describe visualization behavior, not football findings.
Do not read or publish events, outcomes, attacker directions, ranks, anchors,
near-minus-middle responses, coefficients, protected branches, or Game 3.

The future static diagnostic should use the selected fixed ceiling consistently
for its y-axis, colorbar, and team meter while retaining raw values and visibly
disclosing saturation. Renderer changes, a regenerated demo, and a notebook are
outside this audit.
