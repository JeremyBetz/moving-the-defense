# Defensive Reorganization Departure v2

**Status:** frozen prospectively before any DRD v2 target/model outcome

**Freeze date:** 2026-09-04

**Starting commit:** `0a25e09`

**Supersedes:** v1 for future execution only; v1 remains closed
`DRD APPLICATION FOUNDATION INVALID`

**Outcome disclosure:** v1 prospectively failed support before fitting; v2 was
designed after observing support composition but before outcomes.

## 1. Inheritance and sole change

This protocol inherits [Defensive Reorganization Departure v1](defensive_reorganization_departure_v1.md)
in full, including its data, observation unit, timing, target `Y`, E0, E1,
Ridge implementation, alpha grid, nested leave-match-out validation, paired
bootstrap, success thresholds, context-family ablations, DRD definition,
retrieval rules, Metrica/SkillCorner gates, player-ranking prohibition,
nonclaims, and stopping rules.

The sole scientific change is anchor-time attacking-entity support. V1
required exactly ten attacking outfield players even after a confirmed player
dismissal. V2 requires complete support for the exact current on-pitch
attacking outfield set. It does not lower the 1,000-row or 90% retention gate.
The [outcome-blind support audit](../defensive_reorganization_departure_v2_support_audit.md)
records the rationale and alternatives.

## 2. Current on-pitch attacking outfield registry

For each team and anchor, construct the active set deterministically from:

1. the ten match-metadata outfield players marked `Starting="true"`;
2. provider substitution events at or before the anchor, replacing the
   identified outgoing active player with the identified incoming player; and
3. confirmed player-dismissal events at or before the anchor, removing the
   identified active player.

Sort simultaneous roster events by provider event time and then lexical event
ID. An event after the anchor has no effect. A substitution whose outgoing
player is not active, whose incoming player is already active, a dismissal of
a player who is not active, an unsupported roster-event type, duplicated
identity, missing event time/identity, or otherwise ambiguous roster history
invalidates that anchor. No tracking trajectory, response quantity, or model
outcome may be used to infer membership.

## 3. Complete support and ball-nearest exclusion

At the anchor, require exact set equality between:

- the event-defined current attacking outfield set; and
- attacking outfield players with complete, finite seven-frame centred
  support from `t-0.12` through `t+0.12`.

Missing any current player or observing an extra non-current player fails the
anchor. At least two active outfield players are required so exclusion leaves
a possible focal attacker; no team-size threshold is used to rescue support.

Using every member of that exact complete set, calculate Euclidean distance to
the centred-smoothed ball at `t`, select the nearest player, and resolve an
exact tie by ascending canonical player key. Exclude that player. Every other
member is an operational off-ball focal candidate, subject to all unchanged v1
support rules. This remains a geometric proxy, not observed possession,
ball-carrier identity, or a tactical label.

Complete support for an arbitrary subset is prohibited because an unsupported
current player might be nearer the ball. Exactly ten remains mandatory for the
defending outfield target and unit geometry under the unchanged inherited
rules.

## 4. Gates, execution, and stopping

The common sample must still retain at least 1,000 rows and at least 90% of the
otherwise eligible threshold-free off-ball rows in every one of the same seven
matches. All v1 model and classification gates are unchanged. Failure remains
INVALID and cannot motivate threshold, roster, feature, target, match-set, or
provider repair.

No v2 target, E0/E1 fit, prediction, residual, DRD, retrieval, transport,
SkillCorner outcome, or Game 3 result exists at freeze. This document does not
authorize execution by itself; execution must follow the project governance
policy from a clean commit containing the frozen hash ledger.
