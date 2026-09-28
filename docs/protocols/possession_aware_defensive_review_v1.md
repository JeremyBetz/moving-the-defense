# Possession-Aware Defensive Review v1

**Status:** frozen before possession-aware Game 2 rescan
**Frozen:** 2026-09-27
**Starting commit:** `988b00baae33db5140c238914307e5c7f9769050`

## Purpose and boundary

The existing raw team mean remains **team relational reorganization**: the
arithmetic mean of ten supported players' trailing two-second accumulated
leave-one-out defender-relative paths, in metres. It is valid observable
geometry regardless of possession.

This protocol adds a contextual application label. A frame is eligible for
**defensive review** only when the evaluated team has been continuously and
unambiguously out of possession for at least 2.00 seconds. Event-derived
possession is review metadata, not a new scientific estimand or provider-ground
truth possession feed. No score, percentile, threshold, event alignment,
smoother, renderer default, or scientific claim changes.

Metrica Sample Game 3, DRS work, Candidate V1, the manuscript, governed paper
figures, protected outcomes, and tactical or causal interpretation remain
outside scope.

## Event source and ordering

Use public Metrica Sample Game 2 events and native 25 Hz score frames. Required
event fields are team, type, subtype, period, start/end frame, and start/end
time. Events are ordered by period, boundary frame/time, and original provider
row. Provider frames and times must be finite and mutually consistent. More
than one possession-establishing team at one timestamp is invalid.

Possession-establishing event types are `PASS`, `RECOVERY`, `SET PIECE`, and
`SHOT`. `CHALLENGE` never establishes possession. `BALL LOST` ends the recorded
team's possession and produces ambiguity until the next valid possession-
establishing event.

Dead ball starts at `BALL OUT`; `FAULT RECEIVED`; `CARD`; the end of a `SHOT`
whose subtype contains `GOAL` or `OUT`; or a `BALL LOST` subtype containing
`FORCED-END HALF`. It ends at an explicit `SET PIECE`, or at the first later
possession-establishing action when no separate restart is recorded. The
restart frame remains `dead_ball_or_restart`; active possession begins on the
next native frame. Period state never carries across halftime. A period is
ambiguous until its first valid restart or possession event.

At a shared frame, resolution priority is: period/dead-ball boundary, restart,
then possession evidence. A restart frame remains excluded even when a pass is
recorded simultaneously. Possession otherwise carries forward within a period.
No player proximity, ball location, interpolation, or arbitrary silent-gap
expiry may infer possession.

## State and eligibility

Each evaluated-team frame has exactly one state:

- `in_possession`;
- `out_of_possession`;
- `dead_ball_or_restart`; or
- `ambiguous`.

The out-of-possession clock resets at every possession, ambiguity, dead-ball,
restart, period, or stable-run boundary. Defensive-review eligibility begins at
2.00 seconds inclusive, equal to 50 native 25 Hz increments.

A direct change between two recorded teams at a non-restart `PASS`, `RECOVERY`,
or `SHOT` is an event-derived possession-change anchor. Transition context is
the closed interval from two seconds before through two seconds after that
anchor. It is descriptive and separate from defensive retrieval.

## Moment rules

Reuse the frozen full-match application thresholds without recalibration:

- high: raw team mean at or above pooled P95;
- low: raw team mean at or below pooled P05;
- rapid increase: exact one-second change at or above pooled delta P95.

High and low retain the one-second sustained-duration rule. Rapid increase
requires both endpoints to be defensively eligible inside the same uninterrupted
out-of-possession state run. Ineligible frames split clusters. Ranking, ties,
render support, two slots per category, and overlap preservation remain
unchanged. Publish fewer rather than relax a rule.

High or rapid raw passages within the frozen transition window receive the
separate `transition_reorganization` tag. They never replace a defensive slot
unless they independently satisfy defensive eligibility.

## Execution and publication

Rescan only Metrica Sample Game 2. Preserve the historical ungated v1 protocol,
manifest, timeline, diagnostics, and GIFs byte-for-byte. Publish a separately
named v2 package containing aggregate state coverage, eligible episode counts,
new selections, transition examples, the six-selection historical audit, media
hashes, and hard QC. Native state rows and provider-linked detailed exports
remain local and untracked.

Every selected defensive visual states opponent possession, defensive-review
eligibility, and continuous time out of possession. Raw metres, reference
percentiles, and the 0--6.25 m display scale remain visible. The application
does not establish defending quality, tactical intent, causation, prediction,
marking, space creation, effectiveness, or value.

If event/frame reconciliation, ownership ordering, state support, deterministic
regeneration, publication validation, or frozen-hash validation fails, stop and
classify the pass as `POSSESSION CONTEXT STILL AMBIGUOUS`. No rule may be tuned
after the selections are inspected.
