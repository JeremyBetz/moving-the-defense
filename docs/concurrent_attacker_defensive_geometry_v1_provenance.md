# Concurrent Attacker–Defensive Geometry v1 — Methodology Provenance

**Status:** literature/design audit completed before protocol freeze; no v1 match result observed.

## What precedent establishes

- **Interpersonal and dyadic coordination:** football/futsal studies use relative phase or vector coding to describe attacker–defender coordination. Vilar et al. studied attacker/defender coordination relative to ball and goal ([2014, *Human Movement Science*](https://doi.org/10.1016/j.humov.2013.08.012)) and goal-opportunity creation/prevention ([2014, *European Journal of Sport Science*](https://doi.org/10.1080/17461391.2012.725103)). Caetano et al. applied vector coding to nearest-opponent dyads in official football tracking ([2023](https://doi.org/10.1080/14763141.2023.2212664)).
- **Team coordination and shape:** Moura et al. combined cross-correlation and vector coding for football player distributions ([2016](https://doi.org/10.1080/02640414.2016.1173222)). Centroids, stretch, width, length, surface area, and pairwise geometry are established team-shape tools summarized in the project [literature review](literature_review.md).
- **Expected defensive positioning and contextual baselines:** Franks et al., Wu/Lucas and Swartz, Groom et al., and Calero-Sanz et al. motivate context-sensitive defensive geometry. They do not validate this project's focal-relative or concurrent estimand.
- **Method fragmentation:** Esposito et al.'s 2026 elite-football tracking review describes heterogeneous methods and limited contextual/opponent integration ([PubMed record](https://pubmed.ncbi.nlm.nih.gov/42549950/)). That supports explicit definitions and replication, not a new threshold.

## What v1 transfers and changes

V1 transfers fixed-window observation, dyadic distance, team-relative coordinates, pairwise defensive geometry, and context-aware observational modeling. It changes the question by measuring attacker path and defender geometry **concurrently**, fixing defender ranks at interval start, conditioning only on strictly prior movement, and requiring the near-minus-middle coefficient contrast rather than treating generic co-movement as evidence.

No temporal phase, lag, response onset, assignment, or tactical label is inferred. A shifted-time placebo was deliberately omitted because it would impose another arbitrary timing relation on a concurrent question.

## Conservative novelty statement

The ingredients are established. What may be differentiated among the reviewed literature is their prospectively governed combination: continuous attacker path, validated leave-one-out defensive movement, internal deformation, start-fixed spatial rank, pre-interval common-activity controls, and development/held-out validation before football interpretation. This is **limited measurement novelty with potentially meaningful validation/application novelty**, not a universal claim of precedence.

## Literature-audit limits

The search focused on football/futsal attacker–defender coordination, vector coding, team shape, expected defensive positioning, and recent tracking reviews. It was not an exhaustive systematic review. Literature supports construct choices and cautions; it does not determine v1's empirical outcome.
