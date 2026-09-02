# Opportunity Redistribution v1 — Focused Literature and Construct Audit

**Audit date:** 2026-09-02

**Status:** prospective methodology audit completed before any opportunity outcome

## Literature findings

The literature supplies several established meanings of attacking opportunity, but they are not interchangeable.

- **Separation and pressure geometry.** Link, Lang, and Seidenschwarz (2016) make defender distance and defender–goal angle explicit ingredients of pressure around the ball carrier. This is interpretable and tracking-direct, but their thresholded dangerousity model is ball-carrier and value oriented. A nearest-defender distance is therefore defensible as **separation**, not as validated pressure or opportunity value.
- **Passing availability.** Dick, Link, and Brefeld (2022) define availability as the probability that a pass can reach a receiver and model ball dynamics, player movement, interception, and technical skill. This shows why defender distance alone cannot be called pass availability.
- **Passing-lane geometry.** Power et al. (2017), Goes et al. (2019), and later option models use defenders, the ball carrier, potential receivers, interception or corridor geometry, and downstream reward. These are relevant to a future ball-relative option construct, but they require more assumptions and event/ball semantics than the present question needs.
- **Dominant/access-controlled space.** Taki and Hasegawa-style dominant regions, Voronoi variants, and Spearman's (2018) potential pitch control estimate who can reach spatial locations. Fernández and Bornn (2018) combine motion-aware control with ball-relative space value and explicitly formulate space generation for teammates. These are the closest conceptual precedents, but they require player-motion models, ball travel/value assumptions, or hand-set closeness/attraction thresholds.
- **Receiver and off-ball value.** Spearman's OBSO, Fernández and Bornn's valued space, Teranishi et al.'s trajectory-counterfactual C-OBSO, and later OBPV/DAS work attach scoring, transition, completion, or field value. These answer richer questions and are inappropriate before a simpler geometric bridge validates.
- **Defensive density and numerical superiority.** Counts or weighted density around a receiver are readable, but require an arbitrary radius/kernel and can change discontinuously at a boundary. They also conflate how many defenders are nearby with how close the nearest defender is.

The 2026 Dangerous Accessible Space review/model emphasizes an important caution: space-control definitions vary, may lack direct validation, and can become tautologically related to success when value surfaces already use shots or goals. Opportunity Redistribution v1 therefore avoids value, learned reachability, and pass-completion labels.

## Candidate-construct comparison

| Construct | Football interpretation | Tracking inputs | Ball / possession | Model burden | Main failure mode | Development/heldout suitability | Decision |
|---|---|---|---|---|---|---|---|
| Change in nearest-defender separation | Whether a different attacker has more immediate geometric room from the closest defender | Recipient and all defending outfield positions at two endpoints | Ball not required; attacking-team continuity required | Minimal geometry | Nearest identity can switch; distance is not pressure, pass availability, or responsibility | High: deterministic, rigid-transform invariant, short-interval compatible | **Selected as primary primitive** |
| Mean $k$-nearest separation | Broader local defensive proximity | Recipient plus all defenders | Ball not required | Minimal after choosing $k$ | $k$ is a design choice and averages away the closest constraint | Good as frozen robustness | Robustness only, $k=3$ |
| Fixed-start nearest-defender distance | Change relative to one prospectively chosen defender | Recipient and start-nearest defender | Ball not required | Minimal | Becomes stale; may miss a covering defender | Good falsification of dynamic-nearest behavior | Robustness only |
| Fixed-radius defender density | Number/weight of defenders around a recipient | Recipient and defenders | Ball not required | Radius or kernel required | Boundary discontinuity and unvalidated spatial scale | Moderate, but risks tuning | Rejected for v1 |
| Passing corridor / angular openness | Whether a ball-target route is geometrically obstructed | Ball carrier, receiver, ball, defenders | Ball and carrier essential; possession continuity essential | Moderate; corridor width/ball-flight choices | Straight corridor does not establish executable pass | Possible later | Rejected for v1 |
| Voronoi area | Geometric territory closest to a player | All players, pitch boundary | Ball optional | Moderate geometry | Proximity is not reachability; boundary effects | Reproducible but weak football semantics | Rejected for v1 |
| Motion-aware pitch control | Probability/degree of reaching or controlling space | Positions, velocities, ball/travel assumptions | Usually ball dependent | Substantial physics/calibration | Parameter and validation dependence | Poor first bridge; feasible later | Rejected for v1 |
| Passing availability | Probability a hypothetical pass reaches a receiver | Full tracking, ball, dynamics, skill/interception model | Required | High learned/physical model | Model defines much of the result | Requires larger training/validation data | Rejected for v1 |
| OBSO / valued accessible space | Scoring or possession value of controlled/reachable space | Full tracking, ball, events/value surfaces | Required | High | Conflates geometric bridge with value and outcome assumptions | Inappropriate before association validates | Rejected for v1 |
| Local numerical superiority | Attacker/defender count balance in a region | Players and chosen region | Ball optional | Low after scale choice | Arbitrary boundary; ignores distances and directions | Possible descriptive supplement | Rejected for v1 |

## Selection rationale

The chosen primitive is the endpoint change in each non-focal attacker's nearest-defender separation. It is directly observed, needs no learned model, assigns geometry to a different attacker, and is invariant to shared rigid transforms. The protocol does not treat it as pass availability or value.

To make **redistribution** more than general opening, recipients are ranked prospectively by distance to the focal attacker at interval start. The outcome contrasts mean separation change for R1–R3 with R7–R9. This asks whether room changes differentially among the focal attacker's local and remote teammates. Membership is fixed before the outcome, all nine teammates are required, and no improving recipient is selected after the fact.

## Identification choice

The primary unit is one focal-attacker anchor, not one selectively chosen recipient. At each period/time anchor, all eligible simultaneous focal attackers are retained. Demeaning outcome and predictors within that shared time identifies whether focal-specific defensive geometry is associated with focal-specific teammate redistribution while absorbing match activity shared by the anchor. It cannot estimate effects of ball or team movement that are identical for every focal attacker at that time, and it does not remove focal-specific confounding.

The primary defensive predictor is the per-anchor D1–D3 minus D4–D7 focal-relative path contrast. It is selected because it is the simplest anchor-level realization of the already-replicated primary construct—not because it had the largest Game 1 coefficient. Endpoint deformation remains separate and secondary.

## Ball and temporal choice

The primary outcome does not use the ball. This is deliberate: adding passing corridors or pitch control would change “separation” into modeled pass opportunity. The event clock supplies the attacking team and a conservative no-opponent-possession-event continuity rule. Ball movement and broad phase shared at a time anchor are absorbed by within-anchor demeaning. Neither focal nor recipient ball-carrier identity is inferred.

Defensive geometry and separation change use the same two-second interval. A subsequent window would revive the unsupported attacker-before/defender-after ordering; a pre/post design would introduce another arbitrary timing boundary. The concurrent design is descriptive association, not reaction or mediation.

## Novelty boundary

Player separation, pressure zones, receiver availability, pitch control, space generation, and off-ball opportunity/value are established research areas. The project does not claim a first off-ball, space-creation, defensive-response, or gravity metric.

The potentially differentiated contribution is the prospectively governed chain: continuous attacker movement; replicated start-ranked focal-relative defensive geometry; a different attacker's outcome-independent separation change; within-anchor differential redistribution; and development/heldout separation before tactical or value interpretation. This combination is described as differentiated among the reviewed literature, not universally unprecedented.

## Predeclared visualization plan

No empirical opportunity figure is produced during design. A future authorized Game 1 execution should create:

1. a deterministic first-eligible-anchor pitch panel showing the focal attacker path, D1–D10 start ranks, R1–R9 teammate groups, defenders, and start/end nearest-defender links for recipients—without tactical labels; and
2. an aggregate coefficient plot showing the primary $\beta_D$ and its frozen interval alongside the three non-rescuing robustness estimates.

The sequence must be selected by deterministic sample order, not visual appeal or effect magnitude. Captions must call the outcome differential defender separation, not space creation, passing availability, or value.

## Sources

- Bischofberger, Jonas, and Arnold Baca. 2026. “Dangerous Accessible Space: A Unified Model of Space and Value in Team Sports.” *Journal of Big Data* 13. <https://doi.org/10.1186/s40537-026-01387-8>
- Dick, Uwe, Daniel Link, and Ulf Brefeld. 2022. “Who Can Receive the Pass? A Computational Model for Quantifying Availability in Soccer.” *Data Mining and Knowledge Discovery* 36: 987–1014. <https://doi.org/10.1007/s10618-022-00827-2>
- Fernández, Javier, and Luke Bornn. 2018. “Wide Open Spaces: A Statistical Technique for Measuring Space Creation in Professional Soccer.” *MIT Sloan Sports Analytics Conference*. <https://static.capabiliaserver.com/frontend/clients/barca/wp/wp-content/uploads/2018/05/Wide-Open-Spaces.pdf>
- Link, Daniel, Steffen Lang, and Philipp Seidenschwarz. 2016. “Real Time Quantification of Dangerousity in Football Using Spatiotemporal Tracking Data.” *PLOS ONE* 11 (12): e0168768. <https://doi.org/10.1371/journal.pone.0168768>
- Spearman, William. 2018. “Beyond Expected Goals.” *MIT Sloan Sports Analytics Conference*. <https://static.hudl.com/craft/downloads/SSAC2018_Beyond_Expected_Goals.pdf>
- Teranishi, Masakiyo, Kazushi Tsutsui, Kazuya Takeda, and Keisuke Fujii. 2022. “Evaluation of Creating Scoring Opportunities for Teammates in Soccer via Trajectory Prediction.” arXiv:2206.01899. <https://arxiv.org/abs/2206.01899>

The broader prior-art record remains in the [literature review](literature_review.md) and [bibliography](../references/bibliography.md).
