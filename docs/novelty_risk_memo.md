# Novelty and Research Risk Memo

## Current Judgment

**B - limited measurement novelty but potentially meaningful validation/application novelty.**

Centroid-relative player position, distance to a team geometrical center, player-team synchronization, and relative-phase analysis are established in soccer. Phase 4 must not be presented as inventing the decomposition of individual from collective movement.

## Strongest Prior-Art Threat

Sampaio and Maçãs (2012) analyzed soccer players' distance to the team center through time, including approximate entropy and relative phase. Duarte, Araújo, and Correia (2013) explicitly quantified player-team synchrony. Carrilho et al. (2020) measured player deviation from a group-average phase and interpreted reciprocal compensation.

Together, these works support the adversarial statement:

> Player-versus-collective movement is established soccer-tracking methodology; focal departure is a simple refinement, not a wholly new mathematical family.

The statement that Phase 4 is "simply standard relative phase expressed differently" is too strong. Relative phase and accumulated Cartesian residual path have different definitions, units, and questions. The statement that centroid-relative geometry is already widely used is substantially true.

## If Phase 4 Succeeds Unchanged, What Could Be New?

A successful held-out result could support this limited claim:

> A leave-one-out defensive collective-relative path quantity—excluding the focal defender and goalkeeper—shows reproducible structure beyond absolute focal movement, collective translation, aggregate defensive activity, and ball movement under a frozen development/held-out design.

Possible novelty would lie primarily in:

- **validation:** explicit confound conditioning, negative collective references, frozen sensitivities, and held-out replication;
- **defensive application:** using the simple geometry as an interpretation-light individual defensive primitive rather than a team dispersion or synchrony summary;
- **methodological discipline:** demonstrating what the primitive does and does not add beyond ordinary activity before tactical attribution.

Even then, "reproducible focal departure" would not mean meaningful reconfiguration. A soccer interpretation beyond differential movement would remain a separate requirement.

## What Could Definitely Not Be Claimed as New?

- Team centroids or geometrical centers in soccer.
- Player distance or position relative to a team center.
- Removing or normalizing for team location to study shape or formation.
- Player-team synchronization, cluster phase, or relative-phase analysis.
- Interpersonal coordination, reciprocal compensation, or collective-motion analysis.
- Dynamic marking networks, man/zonal assignment inference, or assignment switching.
- Tracking-based defensive evaluation, off-ball movement analysis, pitch control, or space valuation.
- Player gravity or observed-versus-expected defensive pressure.
- Relational reconfiguration, attacker-induced response, attention, responsibility, gravity, or off-ball value on the basis of Phase 4 alone.

## Exact Operational Distinction

The frozen primitive uses:

$$
\mathbf c_{-d}(t)=\frac{1}{|O_d(t)|}\sum_{j\in O_d(t)}\mathbf x_j(t),
\qquad
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),
$$

where $O_d(t)$ contains the other available defending outfield players. It then accumulates Euclidean increments of $\mathbf r_d(t)$. The closest centroid literature generally uses all-player centers, scalar player-center distance, aggregate stretch, or phase-derived synchrony. This is a real operational difference, but not enough for strong measurement novelty by itself.

## Key Risks After the Audit

1. **Trivial-transform risk:** reviewers may regard leave-one-out centroid-relative path as an obvious variant of established centroid-distance measures.
2. **Activity risk:** the result may be almost entirely focal activity expressed in a translated frame.
3. **Interpretation risk:** replication may not provide meaning beyond "the defender moved differently from teammates."
4. **Scope risk:** two public sample matches are insufficient for a broad soccer contribution.
5. **Prior-art scope risk:** formation-normalization or proprietary analytics work may contain closer operational equivalents not visible in the reviewed public literature.
6. **Conceptual overreach risk:** marking, coordination, and gravity literature already occupies much of the downstream narrative.

## Reframing Conditions

- If a closer source proves operationally equivalent, retain Phase 4 as a replication/validation test and abandon measurement novelty.
- If Phase 4 replicates but is absorbed by activity, describe it as a geometric accounting result, not a tactical primitive.
- If it replicates beyond activity but lacks soccer interpretation, claim validated geometry only.
- If it fails held-out replication, preserve the falsification; do not rescue it by changing the frozen test.
- Do not proceed from success directly to reconfiguration, attacker attribution, gravity, or value.

## Bottom Line

The credible novelty proposition is not "we invented focal-relative movement." It is "we subjected a simple, defensively framed leave-one-out collective-relative path to unusually explicit confound and held-out validation." Whether that proposition becomes scientifically meaningful depends entirely on the unchanged Phase 4 result and later interpretation.
