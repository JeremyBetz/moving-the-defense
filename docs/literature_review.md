# Literature Review

> **Current scope (2026-08-29):** targeted positioning for the frozen Phase 4 focal-departure primitive. This is not a systematic review of all soccer tracking research. It does not change the Phase 4A protocol or establish an empirical result.

## 1. Collective Organization and Team Geometry

Team geometrical centers, centroids, stretch indices, team length/width, surface area, and player-to-centroid distance are established soccer-tracking variables. Frencken and Lemmink (2011) used centroid oscillation and surface area as team-level attacking/defending variables. Sampaio and Maçãs (2012) analyzed each player's distance to the team center and its temporal regularity/relative phase. Later reviews catalogue player-geometrical-center distance as a standard dispersion variable rather than a novel construction (Low et al., 2020; Rico-González et al., 2020).

This literature is the strongest challenge to measurement novelty. Subtracting a team center from a player position is mathematically close to established centroid-relative positioning, and analyzing its evolution is not a new general idea. However, the reviewed work normally uses the centroid of all outfield players, scalar distance to it, team-aggregated stretch, or a phase representation. It does not establish the exact Phase 4 combination of

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t)
$$

with the focal defender and goalkeeper excluded, followed by accumulated two-dimensional focal-relative path

$$
L_d=\sum_t\left\|\mathbf r_d(t+\Delta t)-\mathbf r_d(t)\right\|.
$$

The leave-one-out choice matters because including the focal player mechanically attenuates its deviation from the reference. That difference is meaningful, but it does not make centroid-relative geometry broadly new.

Modern tactical pipelines continue to use the centroid of all outfield players and average longitudinal/lateral distance to it as team-level stretch measures (Zhang et al., 2025). Formation work also translates configurations into a team-center frame. These are close precedents for translation removal, although their units of analysis and research uses differ from focal accumulated path.

## 2. Synchronization and Interpersonal Coordination

The dynamical-systems literature goes beyond static centroid distance. Duarte, Araújo, and Correia (2013) introduced cluster-phase analysis for team-team and player-team synchrony in professional football. Carrilho et al. (2020) computed each player's phase relative to a group-average phase of player-ball-goal angles and interpreted deviations alongside team synchrony as reciprocal compensation. Marcelino et al. (2020) used pairwise spatiotemporal velocity correlations to characterize individual and collective coordination in full matches.

These studies undermine any claim that Phase 4 uniquely separates individual movement from collective behavior or uniquely studies deviations from a team-level pattern. They do **not**, however, make $L_d$ a standard relative-phase measure. Relative phase transforms oscillatory or angular time series into phase alignment; Phase 4 accumulates Euclidean increments of a translated Cartesian trajectory. The mathematics, units, and interpretation differ:

- player-team relative phase asks whether movement cycles are synchronized;
- focal-relative path asks how much motion remains after subtracting a contemporaneous collective translation reference.

The same passage can have a long residual path without a simple phase interpretation, and phase disagreement need not imply a long Cartesian residual path. Phase 4 therefore has close methodological precedent, not equivalence to standard relative phase.

## 3. Defensive Marking and Assignment Relationships

Forcher et al. (2022) show that professional defensive-tracking research already spans pressure, synchronization, group balance, compactness, and ball recovery. Two recent works are especially relevant but not operational equivalents to Phase 4.

Groom et al. (2026) use a covariate-dependent hidden Markov model on corner-kick tracking to infer time-resolved man-marking and zonal assignments, assignment persistence/switching, and role-conditioned defensive value. Their reference is a learned tactical state involving attackers or stationary zones—not a leave-one-out moving team centroid—and their purpose is latent assignment and counterfactual evaluation.

Calero-Sanz et al. (2026) construct open-play bipartite marking networks from proximity and directional alignment, then study marking load, coordinated marking, target-allocation similarity, and entropy. Their unit is a defender-attacker network relationship rather than focal movement relative to collective translation.

Both works are closer to any eventual interpretation of relational reconfiguration than to the frozen primitive itself. They sharply constrain future claims: this project did not invent dynamic marking, assignment switching, coordinated defensive relationships, or the question of how attacking movement activates defenders.

## 4. Off-Ball Movement and Space Valuation

Tracking-based tactical analysis already studies relative movement patterns, space occupation, pitch control, formation, and defensive outcomes. Beernaerts et al. (2020), for example, recognize qualitative relative movement patterns between soccer objects, while broader reviews document a large and heterogeneous tracking literature (Memmert, Lemmink, and Sampaio, 2017; Goes et al., 2021).

This work is conceptually adjacent but does not make focal departure an off-ball value measure. $L_d$ contains no attacker attribution, expected response, controlled-space change, possession value, or outcome. Phase 4B established reproducible focal-versus-collective movement in two sample matches; it did not establish who caused it or whether it was valuable.

## 5. Gravity and Defensive Response Above Expectation

The NBA's official Gravity statistic compares observed defensive pressure with expected pressure conditional on player and ball context. That expected-versus-observed architecture clarifies the distance from Phase 4: focal departure is an observed defensive geometric quantity, not an attacker-specific response above expectation.

Gravity is therefore a downstream/application neighbor. Although $L_d$ validated narrowly as geometry, a soccer gravity contribution would still require attacker attribution, an expected-response model, comparable contexts, and downstream interpretation. Conversely, existing gravity work does not operationally subsume the frozen focal-relative path.

## 6. Position of the Present Project

Among the reviewed literature, we did not identify an operationally equivalent study combining all of the following:

1. a focal outfield defender's two-dimensional position relative to the other defending outfield players;
2. explicit exclusion of both focal player and goalkeeper from the collective reference;
3. accumulated path in that moving reference frame;
4. separate conditioning against focal absolute movement, collective path, aggregate defensive activity, and ball movement;
5. frozen negative references and smoothing/window sensitivities; and
6. development/held-out replication without assigning tactical meaning in advance.

This is a bounded search conclusion, not proof that no such work exists.

### Similarity assessment of the closest work

| Source | Classification | Why |
|---|---|---|
| Sampaio and Maçãs (2012) | **B - close methodological precedent** | Uses player distance to team center as a dynamic tactical time series and applies nonlinear/phase analysis. It includes the focal player in the center, uses scalar distance rather than a leave-one-out Cartesian path, and does not use Phase 4's activity-conditioned held-out design. |
| Duarte, Araújo, and Correia (2013) | **B - close methodological precedent** | Explicit player-team synchrony and collective phase decomposition, but a phase measure rather than residual Cartesian path and no leave-one-out centroid. |
| Carrilho et al. (2020) | **B - close methodological precedent** | Measures player deviation from group-average phase and reciprocal compensation, but the primitive is player-ball-goal angular phase, not centroid-relative path. |
| Groom et al. (2026) | **C - conceptual neighbor** | Time-resolved defensive assignments and contextual baselines, but corner-kick HMM states/ghosting rather than collective-translation subtraction. |
| Calero-Sanz et al. (2026) | **C - conceptual neighbor** | Open-play defensive relationships and coordination, but defender-attacker network edges rather than focal-to-team residual movement. |
| NBA Gravity (2026) | **D - downstream/application neighbor** | Expected versus observed defensive pressure is relevant to future response-above-expectation work, not the Phase 4 measurement. |

No reviewed source is classified A, but the B precedents mean strong measurement novelty is not defensible.

## Novelty Decomposition

### Measurement novelty

**Limited.** Player-to-centroid position/distance and player-team synchronization are established. The precise leave-one-out vector path appears less commonly operationalized among the sources reviewed, but it is a transparent refinement of known geometry.

### Validation novelty

**Potentially meaningful.** The explicit test of whether residual path contains reproducible activity-context structure—using frozen negative references, sensitivities, and a held-out match—was not identified in the closest literature. Phase 4B succeeded narrowly at that geometric level, while leaving tactical interpretation and external generalization unresolved.

### Defensive-application novelty

**Plausible but unestablished.** The reviewed centroid literature often targets collective coordination, dispersion, training effects, or phase differences. We did not identify the exact primitive used as a deliberately interpretation-light measure of individual defensive departure from collective translation. Assignment and marking studies address defense more directly but use different representations.

### Conceptual novelty

**Conditional and high-risk.** Connecting a validated primitive to multi-relational defensive adjustment may be distinctive in combination, but relational reconfiguration itself remains unvalidated and prior marking/coordination work already covers much of the conceptual territory.

### Future-application novelty

**Separate and unresolved.** Attacker-induced defensive response, gravity, and off-ball value would require new designs. They are not secured by novelty—or success—of the primitive.

## Conservative Conclusion

**B - limited measurement novelty but potentially meaningful validation/application novelty.**

The strongest prior-art threat is the established use of player-to-team-centroid distance and player-team relative phase. Phase 4 should eventually be described as a stringent validation of a simple leave-one-out collective-relative movement primitive, not as the invention of player-versus-team geometry. If it succeeds, the defensible contribution would concern reproducibility, confound control, and a narrowly defensive application. If it fails, the result is publishable only if the failure teaches a broader, well-supported lesson about validating collective-relative tracking quantities.

Full source records are in the [bibliography](../references/bibliography.md), and the detailed search audit is in [the Phase 4A literature and novelty audit](phase4a_literature_novelty_audit.md).

## Post–Phase 4B Translation Program

After Phase 4B closed, the broader program was reframed around translating football concepts into validated defensive-response signatures. This later synthesis did not motivate the frozen focal-departure test.

The translation problem sits within established and fragmented prior work rather than opening an empty field:

- player-to-team-centroid distance, relative phase, synchronization, and collective geometry provide close measurement precedents;
- off-ball space-generation research already considers attackers attracting or dragging defenders and creating space;
- off-ball-run work has measured subsequent defensive pressure;
- marking-network research represents defender–attacker relationships and changing marking organization;
- tactical/action literature includes football concepts related to balance, withdrawal, covering, and reorganization;
- basketball gravity provides an observed-versus-expected defensive-response application precedent;
- ghosting and counterfactual trajectory research provide expected-defensive-movement precedents; and
- recent off-ball football reviews and taxonomies emphasize fragmented methods and inconsistent terminology.

Accordingly, neither pinning nor the three-vocabulary framework should be claimed as universally unprecedented. The conservative future contribution hypothesis is a validated, interpretable bridge between football tactical language, observable defensive tracking behavior, contextual expectation, and later attacker-associated response or value. This is a research direction, not a current novelty result.
