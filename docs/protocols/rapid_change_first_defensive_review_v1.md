# Rapid-Change-First Defensive Review v1

**Status:** frozen before rapid-candidate inspection
**Frozen:** 2026-09-27
**Starting commit:** `35c43f35dcdd5822615bf6c3454f1a4ec03f7d7c`

## Purpose and boundary

The raw measurement remains team relational reorganization: the arithmetic
mean of ten supported defenders' trailing two-second accumulated
defender-relative paths, in metres. Absolute high and low values remain useful
for distribution and extreme-state inspection. They are not the primary public
retrieval mode because unusual resets and restarts can produce absolute
extremes.

The primary analyst question is: **When did the defensive unit begin
reorganizing much more strongly than one second earlier?** Rapid increase is the
exact one-second change in the unchanged raw team mean. It does not identify
failure, disruption, attacker influence, danger, quality, prediction, tactics,
effectiveness, or value.

## Frozen eligibility and ranking

Reuse possession-aware defensive eligibility without modification. Both
one-second endpoints must be defensively eligible after the existing 2.00-second
buffer and must belong to the same uninterrupted out-of-possession state run.
The pooled Games 1--2 P95 rapid threshold remains exactly
`0.6251746256690309 m`. Qualifying native frames cluster by existing adjacency;
each episode is represented by its maximum one-second increase. Rank descending
by increase, then ascending by period, peak time, and team key. Retain the top
six renderable candidates. No manual substitution is permitted.

## Context classification

A restart boundary is a native-frame transition into or out of
`dead_ball_or_restart`. Restart adjacency is the closed interval within 5.00
seconds of the nearest such boundary in the same period. This is derived from
the existing normalized state table and does not change possession semantics.

Context precedence is:

1. `ambiguous_context` when required normalized context cannot be resolved;
2. `restart_adjacent` within the closed +/-5.00-second restart boundary window;
3. `transition` within the existing closed +/-2.00-second possession-change window;
4. `open_play` otherwise.

Transition candidates remain eligible. Public examples must be defensively
eligible, renderable, unambiguous, and not restart-adjacent. Contradictory event,
frame, or state reconciliation invalidates execution rather than relaxing a
rule.

## Contribution pattern

At each episode peak, calculate each defender's signed one-second change from
the same supported score rows. Normalize positive player increases only for the
share calculation. Player identities remain local.

- `localized`: the three largest positive increases supply at least 60% of the
  total positive increase;
- `broad_unit`: not localized, and at least five defenders have a signed
  increase at or above the team-mean increase;
- `mixed`: every other valid pattern.

The public manifest may contain only anonymized contribution magnitudes, the
top-three share, the count at or above the team mean, and the resulting class.

## Public and secondary selection

Public example 1 is rapid-review rank 1. Example 2 is the highest remaining
episode whose context or contribution class differs from example 1. Example 3
is included only if both its context and contribution class are new relative
to the selected examples. Publish fewer rather than substitute for appearance.

As a secondary local diagnostic, rank the three most negative one-second
changes using the same possession, state-run, render-support, and restart rules.
They may be inspected locally but are not public v3 media in this pass. Any
future promotion requires a separate freeze.

## Execution and publication

Execute once on public Metrica Sample Game 2 after implementation tests pass.
Render all six increases and three decreases under `/tmp`. Publish a separately
named v3 package containing one rapid-change timeline, only the deterministic
public diagnostics/GIFs, an aggregate manifest, hashes, and QC. Detailed frame
states, player identities, and unselected media remain untracked.

Historical v1 and v2 packages, the production scorer, reference thresholds,
possession reconstruction, event alignment, Candidate V1, manuscript, governed
figures, Game 3, protected outcomes, and DRS work remain unchanged.
