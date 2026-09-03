# Defensive Coverage Redistribution v2 — Prospective Supersession Audit

**Audit date:** 2026-09-03
**Status:** completed before any empirical coverage outcome

## Why v1 could not execute

The [v1 rejection record](protocols/defensive_coverage_redistribution_v1_rejection.md)
shows an exact stable-pairing failure: excluding a different focal attacker in
each row and then demeaning across those rows turns the other-nine outcome into
a scaled negative focal matching-cost change. The flaw is identification, not
uncertainty. V1 remains frozen and unexecuted.

## Candidate units and outcome sets

| Candidate | Unit | Outcome set | Identification result | Decision |
|---|---|---|---|---|
| A. Full ten-to-ten matching for every focal perspective | Focal perspective | All ten attackers | Outcome is identical within anchor, so within-anchor demeaning makes it zero. Replicating it across focal rows does not create information. | Reject as focal-perspective primary |
| B1. Mean focal-response contrast + full matching | Anchor | All ten attackers | Symmetric and identified, but it answers global matching change and mechanically includes every focal's direct relationship. It fails the required reference-only-change test. | Reject for “elsewhere” |
| B2. Maximum/top-$k$ focal response + full matching | Anchor | All ten attackers | Identified, but adds response-based selection, maximum noise and a direct focal pathway; $k$ has no independent justification. | Reject |
| C1. Ball-nearest start reference + fixed other nine | Anchor | Same nine non-reference attackers at both endpoints | One physical row, no repeated exclusions, no demeaning, start-defined selection, and direct reference-only relationship change can remain outside the outcome. | **Select** |
| C2. Region/front-line/advanced subset | Anchor | Fixed start-geometry subset | Requires a region, line or role boundary without independent validation. | Reject |
| Arbitrary ID or rotating focal | Anchor | Other nine | Algebraically identified but football-arbitrary and player-label dependent. | Reject |

The selected reference is the unique attacker nearest the observed ball at the
anchor. It is not called the ball carrier. This is a deliberately narrower
football question: local defensive response around one objectively start-defined
attacking reference versus the geometry available to the other nine. It does
not recover arbitrary-focal attribution.

## Matching representations considered

| Representation | Strength | Failure/assumption | Decision |
|---|---|---|---|
| Full ten-to-ten injective matching | Fixed and symmetric; no spare defender | Includes the reference attacker's own relationship, so it can change when nothing changes elsewhere | Descriptive comparator |
| Fixed nine-to-ten injective matching | Fixed elsewhere set; distinct-defender capacity; metre units; compensation can be neutral | One spare defender; proximity is not tactical coverage | **Primary narrow proxy** |
| Nearest-$k$ with defender capacity | Can represent depth and limited shared cover | Requires unvalidated $k$ and capacity; turns one scalar choice into two | Reject |
| Soft-capacity/optimal transport | Smooth under assignment changes | Requires regularization, mass and capacity choices; units/meaning become model-dependent | Reject |
| Matching plus spare-defender penalty | Can force the spare defender to matter | Penalty has no football-grounded scale and can manufacture the result | Reject |
| Thresholded proximity/direction network | Closer to published marking-network representations | Requires distance/alignment thresholds and stronger marking semantics | Defer |
| Pitch control/availability | Includes reachability, ball and dynamics | Advances into a substantially more model-dependent consequence | Defer |

Minimum assignment is established optimization machinery, not a novel coverage
model. The selected quantity remains a transparent exploratory matching-distance
proxy. Published marking, availability and control approaches motivate a
multi-player representation while also showing why raw distance is insufficient
for tactical interpretation.

## Identification and dependence decision

V2 has one row per anchor. The reference attacker is fixed from ball/attacker
start geometry before defender-response or matching change is calculated. The
same nine attacker identities enter both endpoints. There is no focal-row
duplication, no within-anchor demeaning, and no algebraic complement comparison.
The grouped resampling unit is a 60-second block of anchors within period.

The full ten-to-ten solution was not used to remove a focal component because
per-attacker components can depend on which equal-cost optimum a solver returns.
Reoptimizing the one fixed nine-attacker set gives an invariant scalar and
allows defender compensation directly. This differs from v1 because the set is
defined once for the physical anchor rather than ten times for analytical focal
labels.

## Shared-geometry audit

The outcome still uses defender coordinates, so generic movement can alter it.
V2 does not claim otherwise. It adds three protections:

1. the primary predictor is a local-minus-middle path contrast rather than total defender movement;
2. the model adjusts for centroid path and mean D1–D10 leave-one-out-relative path; and
3. a frozen direction null preserves each defender's relative path magnitude, the response contrast, start formation and centroid trajectory while rotating internal movement relative to attacker positions.

The null is stronger than a focal-label permutation for this construct: it
directly tests whether the observed defender-motion direction contributes more
than equally large internally reorganized movement. Passing it would still be
observational and would not establish why players moved.

## Synthetic audit result

Eighteen focused tests pass. The required football geometries show:

- perfect compensation is neutral and absent compensation worsens the fixed-set cost;
- shared translation is neutral, while defence-only translation and balanced independent defender motion can change the cost with neutral local contrast;
- rigid defensive rotation can change both cost and the rank contrast, making the frozen direction null necessary;
- symmetric defensive expansion can alter global matching cost without creating a focal-local contrast;
- independent other-attacker motion can alter the outcome with neutral response;
- smooth swaps and near-tie assignment switches do not create a large scalar jump;
- changing only the reference attacker's spare-defender relationship leaves the elsewhere outcome neutral while the full ten-to-ten comparator changes; and
- the internal-direction null preserves the defending centroid, start formation and every leave-one-out-relative path length to numerical precision.

These are algebra and implementation checks, not match evidence.

## Remaining construct limitations

- The reference is ball-nearest, not an observed ball carrier or arbitrary moving attacker.
- Complete ball support becomes necessary and may reduce usable anchors.
- Nine-to-ten assignment assumes one-to-one geometric capacity and permits one unused defender.
- Euclidean distance ignores direction, goal side, reachability, passing lanes, zones and tactical roles.
- A mean can hide large offsetting changes for individual attackers.
- Dynamic assignment provides a stable scalar but not stable marking identities.
- The outcome and response remain concurrent and share defender coordinates.
- The direction null tests a specific circularity mechanism, not all common causes.
- Game 1 is development in a repeatedly studied match; any positive result requires untouched governance before broader interpretation.

The design is therefore ready to freeze only as a narrow ball-nearest-reference
matching-geometry test. It is not a general metric of defensive coverage,
attacking opportunity, tactical success, gravity, or value.

## Provenance

The prior-art record remains in the [v1 methodology audit](defensive_coverage_redistribution_v1_methodology.md)
and [bibliography](../references/bibliography.md). V2 changes the unit,
start-defined reference, adjustment structure and shared-geometry control; it
does not claim invention of bipartite matching or geometric coverage.
