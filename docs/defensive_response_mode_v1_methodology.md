# Defensive Response Mode v1 methodology note

**Scope:** prospective construct selection only; no empirical response-mode
outcome has been computed.

## Prior art and construct boundary

Team centroids, width, depth, stretch, surface area, player-to-centroid
distance, and player/team coordination are established football-tracking
families. The repository's [literature review](literature_review.md) and
[Phase 4A audit](phase4a_literature_novelty_audit.md) document close precedents
including Frencken and Lemmink, Sampaio and Maçãs, Duarte, Araújo and Correia,
Carrilho et al., Ric et al., Low et al., and the positional-data reviews.

The present design borrows these standard geometric objects. It does not claim
that centroid movement, width, depth, compression, or response-mode analysis is
new. Its narrower contribution may lie in prospectively relating separately
modeled team translation and pitch-axis shape change to the same frozen
attacker-direction representation and established localized rank contrast.

## Why width and depth

Endpoint width and depth use all ten defending outfield players and the
project's canonical goalward/lateral axes. They are:

- readable as literal pitch-axis spans;
- invariant to common translation;
- computable without line, role, assignment, or opponent inference;
- available under IDSSE and likely portable through the governed SkillCorner
  support layer; and
- capable of retaining anisotropic change when kept separate.

Their limitation is equally important: max–min spans depend on extreme players
and are not invariant to rotation relative to pitch axes. A decrease in width
is therefore **narrowing**, not proof of uniform compression. A decrease in
depth is **depth reduction**, not proof that a line dropped or the block
compressed deliberately.

## Rejected alternatives

| Candidate | Why it is not selected for v1 |
|---|---|
| Width/depth composite | Requires arbitrary scaling or weights and hides opposing component changes. |
| Mean pairwise-distance change | Rotation-invariant, but collapses direction and anisotropy into one average. |
| Stretch index | Established but scalar; it does not say whether width or depth changed. |
| Convex-hull area | Boundary-player sensitive, nonlinear, and less direct for the proposed inward/outward question. |
| Principal-axis rotation | Potentially useful, but unstable for near-isotropic shapes and broadens the study beyond one clean mechanism hypothesis. |
| Shear tensor or line-specific geometry | Adds descriptor and role complexity not justified before the width hypothesis is tested. |

## Non-orthogonality

The response channels are views, not components of a conserved total.
Narrowing can generate localized defender-relative path; rotation can change
width/depth and local-relative path while preserving pairwise distances; shear
can alter pairwise geometry while leaving width/depth and the chosen rank
contrast nearly unchanged. Accordingly, v1 cannot estimate the “percentage” of
response allocated to translation, shape, or localization.

## Inference boundary

A supported primary result would mean only that inward rather than outward
displacement is associated with more subsequent pitch-axis width reduction
under the frozen linear comparison. It would not establish defensive intent,
scheme, responsibility, deliberate compression, protection of central space,
attacker influence, tactical success, or value. The secondary centroid result
and descriptive depth/localized channels cannot rescue an unsupported primary.
