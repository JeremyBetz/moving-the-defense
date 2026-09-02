# Concurrent Defensive Coordination Form v1 — prospective draft

**Status: draft, unexecuted, and not frozen.** This document may be reviewed before freeze; it authorizes no match-data outcome computation.

## Question and scope

Does the replicated scalar localization have a concurrent component aligned with the attacker's local path after collective defensive movement is removed? The estimand is observable geometry only.

The exact velocity-based measurement definitions, units, zero-path rule, absolute comparator, cross-trajectory secondary, preprocessing comparison, and synthetic validation are in the [measurement-validation note](../concurrent_defensive_coordination_form_measurement_validation.md) and draft configuration. The original displacement-increment candidate was shown analytically and numerically to scale with the sampling interval and is superseded.

## Proposed preprocessing

- Canonical physical pitch coordinates and existing exact-support/no-interpolation rules.
- Primary: fourth-order zero-phase Butterworth, 1.0 Hz cutoff, on complete continuous x/y support blocks before window extraction.
- One filtering sensitivity: same filter at 1.5 Hz.
- Historical comparator: complete-support centred seven-frame mean.
- Filter each continuously valid support block independently; never cross halftime, invalid tracking gaps, unsupported-player blocks, or other discontinuities.
- The fourth-order SOS implementation uses 15 reflected-padding samples and requires more than 15 samples. Candidate windows must remain within one block and anchors must exclude at least those 15 samples at each edge.
- Before freeze, choose whether the final exclusion uses that sample minimum or a common physical-time edge margin across providers. This choice may not be informed by defender-rank outcomes.

## Proposed primary contrasts

Preserve the established start-rank and modelling architecture unless formal pre-execution review identifies an incompatibility. Two co-primary geometric contrasts are proposed:

1. **A:** D1 minus mean D4–D7 attacker-aligned relative velocity.
2. **B:** mean D2–D3 minus mean D4–D7 attacker-aligned relative velocity.

The final protocol must specify multiplicity/interval handling and classification conditions prospectively. No such conditions are frozen by this draft.

| A | B | Permitted geometric reading |
|---|---|---|
| Positive/supportive | Positive/supportive | Aligned concurrent geometry extends beyond the nearest defender. |
| Positive/supportive | Unsupported | Aligned concurrent geometry is concentrated at the nearest-defender/dyadic scale. |
| Unsupported | Unsupported | The established scalar localization is not principally attacker-path-aligned under this representation. |
| Any other signs | Any | Report signs and uncertainty directly; do not repair or rescue. |

“Nearest” is a distance rank, not an inferred assignment.

## Secondary quantities

- absolute attacker-aligned defender movement;
- cross-trajectory focal-relative magnitude;
- descriptive D1–D10 profile;
- established local deformation quantities if their frozen definitions can be inherited unchanged;
- conventional vector coding only if a pre-result review establishes a clean, nonduplicative definition.

No secondary quantity can reverse or rescue the primary outcome.

## Future governance sequence

1. Human review resolves open preprocessing/support, model, inference, and decision rules.
2. Freeze protocol, configuration, hashes, tests, and exact Game 1 statuses before outcomes.
3. Execute Metrica Sample Game 1 development.
4. Open Metrica Sample Game 2 only if the frozen Game 1 rule authorizes it under separate heldout governance.
5. Open IDSSE directional replication only under separately frozen provider-equivalence and external criteria.

Game 3 remains reserved. Historical response-form, footprint, concurrent-geometry, deformation, bridge, opportunity, and external-replication artifacts remain authoritative and unchanged.

## Explicit nonclaims

This representation cannot by itself establish reaction, causation, influence, attention, marking, assignment, responsibility, following, tracking, covering, pinning, dragging, handoffs, space creation, tactical success, quality, gravity, or value.
