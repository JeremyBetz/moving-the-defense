# Moving the Defense — Research Roadmap

**Measuring Defensive Responses to Attacking Movement in Football**

This roadmap is a dependency map, not a promise that the project will reach tactical attribution or value.

## Conditional evidence hierarchy

```text
football question
        ↓
measurable attacking movement
        ↓
measurable defensive movement
        ↓
defender movement relative to the collective
        ↓
movement magnitude + signed geometric change
        ↓
contextual expectation
        ↓
opponent association
        ↓
tactical interpretation
        ↓
attacker attribution
        ↓
attacking value
```

Every arrow can fail. Football language does not become a tracking construct merely because a trajectory looks familiar, and a tracking association does not become a causal mechanism merely because it is predictable.

## Completed evidence

### Negative foundation

- The historical Structure / Track / Close / Recover state ontology was weakened: behaviours overlap and a simple fixed attacker-relative Track representation failed.
- Prospective relationship selection showed that local compression and opponent stories are reference-sensitive.
- Phase 3’s frozen reception-based relational validation produced **C**. Generic active-play movement and poor matching support defeated the proposed validation route.

### Replicated defensive geometry

- Phase 4B replicated focal-relative path from Metrica Sample Game 1 to held-out Sample Game 2 under a frozen protocol.
- Phase 4C externally replicated it across seven IDSSE professional matches from one independent tracking dataset/provider environment.
- The validated result is geometric: how much a defender moves differently from the other defending outfield players. It remains activity-associated and has no tactical or attacker semantics.

### Context and opponent information

- Phase 5A produced **A — contextual expectation feasible**. Future focal-relative path is predictably structured, but recent focal movement supplies almost all material gain.
- Phase 5B produced **B — mixed/partial**. Opponent information adds a small held-out association, but nearest-opponent locality is not materially superior to nonlocal controls.

### Post-5B measurement audits

- Signed focal-relative displacement is retained descriptively because scalar path loses direction.
- Constant-velocity continuation innovation is not validated as response onset.
- Historical outcome-blind speed-valley segmentation is **B — mixed**: 42.22% of episodes meet a fragmentation diagnostic. [Attacker Movement Episode v2](results/attacker_movement_episode_v2_game2.md) reproduced its numerical fragmentation/merging/coverage trade-off on heldout Game 2, but failed its prospectively selected direction-boundary audit and therefore closed **MIXED**. The segmentation remains attacker-only and unresolved at the boundary-interpretation level; long episodes persist and no defender outcome was opened.

### Outcome-blind rank-composition audit

- The [defender-rank composition audit](defender_rank_composition_audit.md) examined start geometry and strictly prior context across both Metrica matches and seven IDSSE matches without opening concurrent response or coverage outcomes.
- The one moderate nondefining signal was defender goalward offset from the unit centroid (median match standardized difference −0.3384; 9/9 in the same direction). Prior-activity differences were negligible.
- A scalar-Euclidean-distance-excluded 15-feature leave-one-match-out classifier had median AUC 0.6267, and every fold remained below 0.65. Because paired goalward offsets retain longitudinal-separation information, this is a conservative upper-bound diagnostic. Rank composition is modestly predictable, not proof of confounding.
- Synthetic checks showed an approximately zero rank-only near-minus-middle null, removal of 99.22% of deliberately activity-induced localization by the established focal/other-nine activity controls, and rank-independent 10/9 leave-one-out scaling.
- The exact verdict is **CORE RANK LOCALIZATION USABLE WITH MODERATE LIMITATION**. No prospective core sensitivity is required; downstream work must retain the limitation and nonclassifying QC.

## Current methodological frontier

> **During the same fixed interval, is attacker movement associated with spatially localized defensive geometric change beyond strictly prior movement context?**

The [Concurrent Attacker–Defensive Geometry v1 protocol](protocols/concurrent_attacker_defensive_geometry_v1.md) removed the artificial attacker-before/defender-after requirement and did not use unresolved episode boundaries. [Game 1 development](results/concurrent_attacker_defensive_geometry_game1_v1.md) was coherent, and the prospectively governed [Game 2 heldout replication](results/concurrent_attacker_defensive_geometry_game2_v1.md) was **SUPPORTED**. The unchanged [seven-match IDSSE external replication](results/concurrent_attacker_defensive_geometry_idsse_v1.md) is also **SUPPORTED**: all seven match estimates were positive and the pooled estimate was 0.05115 [0.04595, 0.05642] with robust trimming. All-rank positivity, nonmonotonic shapes, far-above-middle geometry, possible concurrent common motion, and provider-specific smoothing timescales remain important caveats. Game 3 remains reserved.

The completed bridge resolves the first within-provider association test, not its tactical or causal meaning. Continuous attacker intervals remain defined without defensive outcomes, and defensive change remains geometric rather than tactical. Historical segmentation failures still constrain any future episode-based extension. No new empirical phase may begin unless its design is prospectively specified and frozen.

The [Opportunity Redistribution v1 protocol](protocols/opportunity_redistribution_v1.md) tested whether the replicated focal-local defensive contrast was associated with differential nearest-defender separation gain for other attackers initially local rather than remote to the focal attacker. The [Game 1 result](results/opportunity_redistribution_game1_v1.md) is **NEGATIVE**: the primary $\beta_D$ was −0.02407 [−0.09392, 0.04776], and two of three robustness signs were negative. This narrow geometric bridge did not survive development. Game 2 was not opened; Game 3 remains reserved.

### Research decision point after Opportunity Redistribution v1

- **A — Measurement-paper path:** make the replicated defender-relative and localized concurrent geometry the primary contribution, with the negative opportunity result defining a substantive interpretation boundary.
- **B — Downstream-consequence path:** pursue a different consequence only if independent football theory and literature motivate a substantively different construct. Do not select another metric merely because nearest-defender separation was negative.
- **C — External-validation path:** completed. The unchanged concurrent geometry passed the frozen seven-match IDSSE external-replication criteria. This strengthens the measurement-paper path without supplying tactical or causal semantics.

The next downstream design was subjected to a pre-execution adversarial review. [Defensive Coverage Redistribution v1](protocols/defensive_coverage_redistribution_v1_rejection.md) was rejected before any sample or outcome because repeated focal exclusion plus within-anchor demeaning did not identify the intended other-attacker construct. Its frozen artifacts remain unchanged. The [superseding v2 protocol](protocols/defensive_coverage_redistribution_v2.md) narrowed the physical unit to one anchor, one start-defined ball-nearest reference attacker and one fixed other-nine matching set. Its [Game 1 closure](results/defensive_coverage_redistribution_game1_v2.md) is **INVALID before estimation**: complete support retained 281 period-1 anchors but no period-2 anchors, so the mandatory period-2 indicator was constant and the frozen 12-column model had rank 11. The [prospective v3 protocol](protocols/defensive_coverage_redistribution_v3.md) froze a single estimability remedy: omit only that explicitly designated non-scientific nuisance when exactly constant over the complete eligible sample, then keep the active column set fixed. Its [Game 1 result](results/defensive_coverage_redistribution_game1_v3.md) is **MIXED**: $\hat\beta_D=0.09839$ m/m, but its frozen 95% interval crossed zero and it did not exceed the shared-geometry direction-null threshold. The remote comparator and movement trim passed, but cannot rescue the primary result. This is a valid period-1-only geometric development result, not evidence for football coverage, opportunity, tactics, gravity, or value. Game 2, Game 3, and IDSSE coverage outcomes remain unopened.

A design-only [Concurrent Defensive Coordination Form measurement review](concurrent_defensive_coordination_form_measurement_validation.md) asks whether the replicated scalar localization has a component aligned with the attacker's changing local path. The velocity formulation and physical-time filtering passed synthetic checks, and the [prospective protocol](protocols/concurrent_defensive_coordination_form_v1.md) now freezes a 2.0-second support-block interior, the unchanged 72-column context model, D2–D3 minus D4–D7 primary estimand, D1 benchmark, bootstrap, and Game 1 decision rules. No match-level scientific outcome has been computed.

The first bounded refinement executed under its frozen rules and classified **B**. Prominence sharply reduced fragmentation but drove merging/direction to 35.88%–69.03% against a 3.97% cap. No candidate was selected, so the protocol forbids Game 2 execution and further threshold repair.

The completed [representation audit](attacking_movement_representation_audit.md) selected penalized change points in the attacker's two-dimensional velocity state. [Protocol v1.0](protocols/attacking_directional_segmentation_v1.md) froze its BIC-derived penalty, fixtures, support treatment, diagnostics, and decision tree before execution. The [Game 1 result](results/attacking_directional_segmentation_game1_v1.md) is **B**: hard QC and merging control passed, but 99.80% fragmentation and unstable 10 Hz recall/F1/counts reject the representation for held-out use. Game 2 remains unopened for attacker segmentation, and the A-only prerequisite was not met.

The subsequent [representation fork](attacking_movement_representation_fork.md) selected **continuous fixed-window attacker geometry**. [Protocol v1.0](protocols/attacking_continuous_movement_v1.md) retained signed displacement, path length, and derived straightness over a 2 s primary window with 1/4 s sensitivities; heading change and speed variation were deferred. The representation classified **A** on [Game 1](results/attacking_continuous_movement_game1_v1.md) and, under a separately frozen protocol and Stage-A registry, **A** on [held-out Game 2](results/attacking_continuous_movement_game2_v1.md). Hard QC and every frozen 25/10 Hz gate passed at both matches with byte-identical reproduction. That within-provider prerequisite enabled the separately frozen bridge without reinterpreting or tuning the attacker representation.

That design was frozen in [attacker-to-defender bridge protocol v1.0](protocols/attacker_defender_bridge_v1.md). Game 1 was development-coherent, and the unchanged [held-out Game 2 plus pooled execution](results/attacker_defender_bridge_game2_v1.md) is **FINAL BRIDGE A**. Local coefficients were positive and exceeded nonlocal/placebo controls in both matches; pooled primary and paired-control intervals were positive; every frozen robustness, hard-QC, and reproduction gate passed. This is a replicated observational association across two within-provider sample matches, not tactical response or causation.

The [spatial defensive-response footprint v1.0](protocols/spatial_defensive_response_footprint_v1.md) is complete at **FINAL FOOTPRINT A**. The [Game 1 development result](results/spatial_defensive_response_footprint_game1_v1.md) was coherent; untouched [Game 2 measurements](results/spatial_defensive_response_footprint_game2_v1.md) remained descriptively unclassified and were closed before comparison; the [pooled/final result](results/spatial_defensive_response_footprint_final_v1.md) reproduced the positive near-minus-middle distinction while middle-minus-far remained null. The unchanged [seven-match IDSSE external replication](results/spatial_defensive_response_footprint_idsse_v1.md) is **SUPPORTED**: the pooled primary contrast was 0.06115 [0.05579, 0.06681] and its paired excess over the frozen reverse-time control was 0.02455 [0.01932, 0.02985], with both signs positive in all seven matches. This is an externally replicated, stepped, time-ordered observational spatial association—not assignment, tactics, causation, or value. No alternate lag, window, rank definition, or bridge metric was searched.

The [local defensive response form v1 protocol](protocols/local_defensive_response_form_v1.md) preserves the validated movement magnitude and separately tests signed endpoint geometry. Game 1 development was coherent; [Game 2](results/local_defensive_response_form_game2_v1.md) reproduced the positive primary near-minus-middle distinction, but its paired primary-minus-control interval crossed zero. The [pooled/final execution](results/local_defensive_response_form_final_v1.md) therefore closed at **FINAL RESPONSE FORM B**. Directional localization is supported descriptively across both matches, but the beyond-control distinction did not fully replicate. Radial, orthogonal, and absolute-versus-unit views remain descriptive rather than tactical labels; Game 3 remains reserved.

The [Concurrent Defensive Coordination Form v1 Game 1 execution](results/concurrent_defensive_coordination_form_game1_v1.md) classified **COHERENT**. In the prospectively governed [Game 2 replication](results/concurrent_defensive_coordination_form_game2_v1.md), the primary and 1.5 Hz point directions remained positive, but the primary interval crossed zero; its heldout status is **MIXED**. The unchanged construct subsequently achieved **SUPPORTED** [external replication across all seven governed IDSSE matches](results/concurrent_defensive_coordination_form_idsse_v1.md): all seven primary intervals were strictly positive and all 1.5 Hz directions were retained. No pooled estimator or team-response taxonomy was introduced. The interpretation remains geometric and observational.

[Defensive Response Expectation v1](protocols/defensive_response_expectation_v1.md) is now [executed](results/defensive_response_expectation_v1.md) and **NOT SUPPORTED**. E1's compact movement/spatial context improved E0 slightly in all seven IDSSE matches, but E2b's match-side intercept/path increment worsened E1 macro MAE, improved 0/7 matches, had a paired interval below zero, and failed the shifted-label control. The sole repeated-team check was directionally consistent but remains secondary and cannot establish stable team identity or tactical style.

## October 1, 2026 constraint

The [2027 MIT Sloan Sports Analytics Conference Research Paper Competition](https://www.sloansportsconference.com/research-paper-competition) lists **October 1, 2026, 11:59 p.m. Eastern** as the round-one abstract deadline. The abstract is limited to actual evidence; the deadline is a communication constraint, not a reason to relax scientific gates.

### Pre-October 1 priorities

The bounded priorities and stopping rules are consolidated in the
[Sloan submission strategy](sloan_submission_strategy.md). The preferred paper
is a hybrid measurement-and-validation contribution. The external IDSSE
time-ordered bridge is now closed as supported; any additional empirical
investment requires a new prospectively frozen question and must not reopen
its timing, ranks, or controls.

1. Preserve the negative Opportunity Redistribution v1 result; do not tune it or open Game 2 without a separately justified prospective decision.
2. Preserve the completed Final A bridge and its local, nonlocal, temporal, activity/context, tracking-quality, and influence limits.
3. Preserve the completed Final A spatial footprint and its supported frozen external/native-frequency replication; do not search another bridge specification.
4. Preserve a conservative result even if it is mixed or negative.
5. Produce an abstract-ready evidence story, clear football figures, and a reproducible public repository.
6. Complete literature positioning around movement segmentation, expected defence, opponent relationships, and off-ball action—without novelty inflation.

The October submission can succeed as a validated measurement/bridge contribution or a well-supported methodological warning. It does not require a gravity metric, final player value, tactical classifier, or causal attribution.

## Conditional post-October work

Only if the attacking-interval and defensive-change representations survive prospective validation:

- replicate the bridge across additional matches/provider environments;
- test whether ball, team, opponent, and spatial context explain the association;
- investigate concept-specific observable consequences with independent football interpretation;
- examine whether candidate moments can support analyst video review.

These are conditional directions, not approved experiments.

## Later interpretive steps

Tactical language such as pinning, dragging, tracking, covering, handing off, stretching, or recovery requires semantic evidence beyond geometry. Attacker attribution requires a stronger design than opponent association. Gravity and off-ball value additionally require an expected-response reference and downstream consequence model.

Potential applications—team or player defensive-style profiles, scouting descriptions, match-review surfacing, video indexing, and coaching feedback—remain downstream and must not be presented as current capabilities.

## Legitimate stopping conditions

- An attacker-only temporal representation remains too unstable without outcome-informed tuning.
- A bridge test cannot separate active play or ball movement from attacker-associated defensive geometry.
- Opponent association remains too weak or nonlocal for football interpretation.
- A replicated geometric primitive remains useful only as descriptive movement.
- Semantic validation contradicts the proposed football concept.
- Attribution or value cannot be supported without causal overreach.

A scientifically successful project may stop at any of these points if it establishes clearly why the next arrow is unsupported.
