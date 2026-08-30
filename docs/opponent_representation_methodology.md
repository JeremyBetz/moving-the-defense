# Opponent-Representation Methodology and Provenance

> **Scope:** provenance for the frozen, unexecuted Phase 5B v1.0 protocol. This is a targeted extension, not a systematic review and not evidence that the proposed representation works.

| Origin | What prior work did | Why it matters here | Phase 5B adaptation | Not claimed as novel |
|---|---|---|---|---|
| Buldú et al. (2020) and Calero-Sanz et al. (2026) | Built soccer tracking networks from proximity, direction, and defender–attacker relationships. | Shows that local opponent geometry and defender–attacker edges are established tracking representations. | Uses fixed nearest-attacker ranks as transparent predictors, without constructing a network. | Proximity edges, local opponent selection, marking-network ideas, or coordinated relationships. |
| Beernaerts et al. (2020) | Recognized relative movement patterns among soccer objects from positional data. | Establishes pair-relative displacement/motion as prior methodology. | Keeps signed x/y, distance, relational path, and approach projections separate. | Pairwise relative position, velocity, path, or closure geometry. |
| Franks et al. (2015) | Used basketball tracking, inferred defensive matchups with a hidden Markov model, and modeled spatial defensive effects. | A close cross-sport precedent for linking defenders to nearby opponents and conditioning defensive analysis on matchup context. | Uses no latent matchup, assignment, responsibility, shot model, or value; selection is deterministic geometry at $c$. | Matchup-conditioned defense or spatial defensive modeling. |
| Wu and Swartz (2023) | Predicted a soccer defender's velocity from context and compared observed with typical movement. | Direct expected-versus-observed defensive-motion precedent. | Adds typed opponent information to the already validated scalar B4 expectation baseline. | Expected defensive movement or opponent-conditioned prediction. |
| Le et al. (2017) | Generated contextual soccer defensive ghost trajectories using deep imitation learning. | Establishes rich multi-player attacking context as a basis for defensive trajectory references. | Retains Ridge and a scalar target to isolate whether opponent information contributes at all. | Defensive ghosting, counterfactual trajectories, or “should” positioning. |
| Groom et al. (2026) | Inferred corner-kick man/zonal roles and used role-conditioned ghosting for defensive evaluation. | Demonstrates that roles and assignments can structure opponent-conditioned defensive references. | Explicitly postpones role, assignment, counterfactual, and value semantics. | Role inference, marking assignments, or defensive value. |
| NBA Gravity (2026) | Describes observed defensive pressure relative to expected pressure from player/ball context. | A downstream application precedent for opponent-associated response above expectation. | Tests only predictive information about focal-relative path. | Gravity, attraction, causation, or attacking value. |

## Representation choices

The proposed nearest-three rule is a reproducibility device, not a football-semantic pairing. Rank-fixed histories protect against using later movement to choose a favorable opponent and preserve identity continuity. They can still become locally stale, include the ball-nearest attacker, omit a tactically relevant distant attacker, or encode proximity rather than a meaningful relationship.

The cumulative ladder deliberately separates:

1. cutoff geometry;
2. attackers' independent recent motion; and
3. nonlinear pair-history/directional geometry.

Exact linear aliases are omitted because a Ridge ladder cannot attribute incremental information meaningfully when one block merely reconstructs earlier columns. Radial distance and approach projections are retained because they are nonlinear transforms of signed coordinates and velocity components under a linear estimator.

The A4–A6 **nonlocal-opponent locality control** retains physically possible soccer geometry while changing locality. It is evaluated only on a secondary subset complete for A1–A6, so it does not shrink or classify the primary experiment. It is preferable to temporal misalignment, which would splice focal and attacker locations from different moments. The control tests locality, not causal relevance or tactical assignment.

## Novelty boundary

Nearest-opponent geometry, local attacking configuration, pairwise closure, and relative velocity have clear prior methodological neighbors. The only potential differentiated contribution is the full prospective validation arrangement: begin from a frozen non-opponent baseline, add typed opponent channels without future selection, evaluate on a common sample by held-out match, and stop at opponent-information association. This combination is described as a hypothesis among reviewed literature, not as universally unprecedented.

Full metadata are in the [bibliography](../references/bibliography.md). The exact frozen design is the [Phase 5B protocol](phase5b_opponent_relational_increment_protocol.md).
