# Defensive Reorganization Context v1 — Methodology Note

**Status:** prospective design; no empirical context effect has been computed.

## Why this is separate from DRD

DRD v2 asked whether a broad context feature bundle improved heldout prediction
enough to justify residual passage retrieval. It classified **MIXED** and its
stop rule remains binding. This study asks a different, narrower descriptive
question: whether the already measured near-minus-middle defensive geometry
varies with two starting relationships that an analyst can see on a pitch.

It uses observed `Y`, not DRD, predictions, or residuals. It cannot rescue the
application result or authorize retrieval.

## Candidate assessment

| Candidate | Decision | Prospective rationale |
|---|---|---|
| Attacker goalward position relative to defensive centroid | **Primary H1** | Signed continuous metres; directly expresses whether the attacker starts more goalward relative to the unit; portable and available before movement. |
| Attacker lateral position relative to defensive centroid | Not primary | Its football meaning depends more strongly on unit orientation and centrality conventions; adding it would increase multiplicity. |
| Position normalized by defensive depth/width | Not primary | Ratios obscure physical units and add unstable denominators; unit depth is retained only as a nuisance control. |
| Attacker–ball distance at movement start | **Primary H2** | Continuous Euclidean metres, provider-portable, visible to analysts, and free of tactical-zone labels. |
| Ball goalward position relative to defensive centroid | Nuisance only | Needed to separate simple ball depth from attacker–ball separation, but it is not a third hypothesis. |
| Ball lateral position relative to defensive centroid | Not selected | Adds another spatial axis without an independently compelling question. |
| Attacker–ball distance change over exposure | Excluded | It occurs during the movement interval and is not pure pre-movement context. |

No sign is frozen. “More goalward” or “farther from the ball” could plausibly
increase or decrease the response depending on football circumstances the
tracking geometry does not identify. A two-sided test is more honest than a
fabricated directional theory.

## Why this model

The raw-unit linear model keeps both primary contexts mutually adjusted and
controls only current attacker path, prior attacker path, defensive depth, and
ball depth relative to the unit. Match intercepts absorb level differences;
equal-match weights prevent the largest match sample from dominating. The
model does not use Ridge, identity effects, interactions, categories, splines,
or automated selection.

The context family has only two primary hypotheses. Their two-sided 97.5%
block-bootstrap intervals implement a simple Bonferroni familywise correction.
Per-match and leave-one-match-out signs prevent a pooled coefficient from
hiding contradictory matches. A single predictor-only central-support trim
tests whether context extremes dominate without opening a robustness search.

## Football and paper use

Each slope translates to the change in near-minus-middle defender-relative
path associated with a 10 m difference in starting context. One two-panel
figure can place those relationships on a pitch and show the adjusted curves
in metres. If SUPPORTED, this could add “where it tends to be strongest” to the
replicated measurement result. MIXED or NOT SUPPORTED is not an application
headline and closes this branch before Sloan.

Metrica Games 1–2 and SkillCorner are conditional future confirmation settings,
not part of this design execution. Game 3 remains untouched. The authoritative
definitions are the [protocol](protocols/defensive_reorganization_context_v1.md)
and [configuration](../config/defensive_reorganization_context_v1.json).
