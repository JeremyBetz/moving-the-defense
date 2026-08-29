# Phase 4A Focal-Departure Literature and Novelty Audit

Date: 2026-08-29

Checkpoint audited: `d873b381fd1626ee7eff13f6150add8118f01538`

## Governing Boundary

This audit changes literature positioning only. It does not modify the frozen Phase 4A protocol, config, sampling, metric, conditioning variables, replication criteria, sensitivities, or falsification rules. It does not execute Phase 4B or inspect any Game 2 focal-departure outcome.

## Central Question

Has prior sports research already operationalized something substantively equivalent to

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t)
$$

and especially

$$
L_d=\sum_t\left\|\mathbf r_d(t+\Delta t)-\mathbf r_d(t)\right\|,
$$

where the collective reference excludes the focal defender and goalkeeper?

## Search Strategy

The targeted search used combinations of soccer/football with team centroid, geometrical center, center of mass, player-to-team distance, centroid-relative position, collective translation, residual movement, individual versus collective motion, stretch index, synchronization, cluster phase, relative phase, reciprocal compensation, tactical tracking, defensive organization, marking networks, assignment inference, off-ball movement, and gravity. Searches also covered reviews of distance variables and defensive tracking, plus directly informative invasion-sport and NBA methodology.

Sources were prioritized in this order:

1. peer-reviewed primary research;
2. systematic/scoping reviews for coverage and terminology;
3. original preprints for recent unpublished work;
4. official methodology descriptions where no peer-reviewed product paper was identified.

The audit reviewed 18 material sources: 11 primary empirical/method papers, five systematic/scoping or field reviews, one theory/method paper, and one official NBA methodology description. Citation metadata were checked against publisher, PubMed/PMC, institutional, DOI, or original arXiv records.

This was systematic across the specified concepts but not a database-exported PRISMA review. Searches of proprietary analytics, non-English work, theses, and conference proceedings remain incomplete.

## Similarity Scale

- **A — operationally equivalent:** essentially the same reference, quantity, and research use.
- **B — close methodological precedent:** similar player-versus-collective decomposition with a material difference in reference, quantity, or use.
- **C — conceptual neighbor:** coordination, marking, shape, or defense is studied through a different primitive.
- **D — downstream/application neighbor:** relevant to later interpretation but not Phase 4 measurement.

## Closest Source-Level Comparison

| Source | Sport/data | Unit | Collective reference | Focal-relative quantity | Focal excluded? | Movement/path? | Translation removed? | Activity controlled? | Claim type/use | Class and novelty threat |
|---|---|---|---|---|---:|---|---:|---:|---|---|
| Sampaio & Maçãs (2012) | Soccer; 5 Hz GPS; 5v5 training games | Player time series and team | Center of team | Scalar player distance to team center; entropy and relative phase | Not reported; apparently no | Dynamic distance, not accumulated 2D relative path | Partly through center-relative distance | No Phase 4-equivalent conditioning | Descriptive/inferential tactical coordination and training effect | **B. Strongest direct threat:** player-to-team-center dynamics are established. Reference inclusion, scalar distance, and validation differ. |
| Duarte, Araújo, & Correia (2013) | Professional soccer tracking | Player-team and team-team synchrony | Group/cluster phase by direction | Player phase minus team phase | No leave-one-out centroid | Phase evolution, not Cartesian path | Collective phase is the comparison baseline | Possession/direction context, not activity conditioning | Descriptive/inferential synchronization | **B.** Establishes explicit individual-versus-team movement decomposition, but not the same measure. |
| Carrilho et al. (2020) | Soccer optical tracking; one match | Player relative phase and team order parameter | Group-average phase of player-ball-goal angles | Player phase deviation from group phase | No | Movement phase, not accumulated path | No Cartesian translation subtraction | Match zone/possession context, not generic activity controls | Descriptive synergic behavior/reciprocal compensation | **B.** Close conceptual and mathematical decomposition; different angular object and use. |
| Marcelino et al. (2020) | Soccer optical tracking; five matches | Pair, player, and team correlations | Pairwise/all-player velocity field | Spatiotemporal velocity-correlation fingerprint | Not applicable | Movement correlations | Not via centroid subtraction | Context comparisons, not Phase 4 conditioning | Descriptive/inferential collective coordination | **C/B boundary.** Individual contribution to collective motion is established, but reference and quantity differ materially. |
| Zhang et al. (2025) | Football tracking plus events; match pipeline | Team/phase | Mean of all outfield players | Longitudinal/lateral average distance to centroid (stretch) | No | Positions aggregated over phases; no focal relative path | Centroid frame implicit in stretch | Match phase, not general activity | Descriptive/inferential tactical pipeline | **B/C.** Confirms centroid-relative shape is current standard practice, but not focal accumulated residual movement. |
| Groom et al. (2026) | Premier League corner tracking | Defender assignment/state and counterfactual outcome | Learned zones and attackers | Relative position/velocity in HMM covariates; role-conditioned ghosting | Not applicable | Dynamic assignment and relative motion | No team-centroid translation subtraction | Rich model context; not Phase 4 activity test | Predictive/inferential assignment and defensive evaluation; not causal | **C.** Strong downstream defensive precedent, not operational equivalence. |
| Calero-Sanz et al. (2026) | 99 LaLiga matches; tracking | Defender-attacker edge/network | Opponent relationships; team projections | Proximity/alignment marking edges, loads, coordination, similarity, entropy | Not applicable | Dynamic/cumulative relationships, not focal residual path | No | Contextual aggregation; no Phase 4-equivalent activity conditioning identified | Descriptive network characterization | **C.** Strong open-play relational precedent; threatens broad conceptual novelty, not measurement novelty. |
| NBA Gravity (2026) | Basketball optical/pose tracking | Attacker defensive-pressure differential | Expected pressure conditional on player/ball context | Observed minus expected defensive pressure | Not applicable | Frame-level modeled pressure | Not the focal centroid reference | Yes, via expected model rather than Phase 4 controls | Predictive/descriptive commercial metric | **D.** Clarifies later response-above-expectation architecture; not the primitive. |

## Other Material Sources

| Source | Sport/data and unit | Reference and quantity | Exclusion/path/translation/activity | Claim type and use | Class |
|---|---|---|---|---|---|
| Frencken & Lemmink (2011) | Soccer small-sided-game tracking; team | Team centroid position and surface area | All-player team reference; team motion, not focal path; no focal/activity conditioning | Descriptive/inferential collective attacking/defending dynamics | **C** |
| Ric et al. (2016) | Soccer match positional data; multilevel team patterns | Team geometrical center, stretch, length, width, area | Team aggregates; no leave-one-out focal path or translation residual | Descriptive multiscale tactical dynamics | **C** |
| Memmert, Lemmink, & Sampaio (2017) | Soccer tracking; review/illustrative match | Centroid, compactness, inter-player/team coordination | Reviews multiple references; no focal accumulated residual validation | Methodological field review | **C** |
| Low et al. (2020) | Football positional studies; systematic review | Centroid, dispersion, dyads, synchronization families | Documents player-centroid measures but not a frozen leave-one-out path test | Evidence synthesis | **B/C coverage evidence** |
| Rico-González et al. (2020) | Invasion-sport positional studies; systematic review | Player-player, player-space, player-ball, and geometrical-center distance families | Explicitly catalogs player-GC distance and nonlinear analyses; no single focal protocol | Computational/methodological evidence synthesis | **B/C coverage evidence** |
| Araújo & Davids (2016) | Team-sport theory and methods | Order parameters, dimensional compression, reciprocal compensation | No Phase 4 coordinate/path or activity test | Conceptual/methodological synergy framework | **C** |
| Forcher et al. (2022) | Professional soccer defensive tracking; scoping review | Pressure, synchronization, balance, compactness, recovery | Multiple methods; no identified exact leave-one-out accumulated path | Descriptive evidence synthesis of defensive analysis | **C** |
| Beernaerts et al. (2020) | Soccer tracking; player/group trajectory fragments | Qualitative relative movement between selected objects | Dynamic object relationships; not a team-centroid residual or activity-conditioned path | Descriptive/pattern-recognition method | **C** |
| Goes et al. (2021) | Professional soccer tracking; systematic review | Broad tactical positional-data methods | Multiple references; no identified Phase 4-equivalent validation | Evidence synthesis | **C** |
| Shpurov, Froese, & Ikegami (2024) | Soccer trajectories; individual and team | Individual trajectories, team center of mass, player-center distance statistics | Center apparently includes players; movement distributions but not leave-one-out residual path/activity controls | Descriptive Lévy-walk/collective-motion analysis | **B/C** |

## Adversarial Novelty Tests

### “This is just centroid-relative player motion already widely used.”

**Substantially true at the family level.** Player position/distance relative to a team centroid is established, and centering formations or measuring stretch is common. It is not true at the full protocol level: the audit did not identify the exact leave-one-out defender reference, accumulated Cartesian path, and activity-conditioned held-out validation together.

### “This is simply a standard synchronization/relative-phase measure expressed differently.”

**Not substantially true.** Both compare an individual with a collective pattern, but relative phase measures cyclic/instantaneous phase alignment. $L_d$ measures accumulated Euclidean movement in a translated coordinate frame. Similar motivation does not make the measurements interchangeable.

### “Prior defensive tracking already decomposes individual movement from collective defensive translation.”

**Partly true, but not verified as an exact operational match.** Defensive tracking and player-team coordination are established. The reviewed sources did not show the full Phase 4 decomposition and validation use. Proprietary and formation-normalization work remains a gap, so the claim must stay bounded.

## What Appears Established

- Team centroids/geometrical centers and player-to-center distances.
- Team stretch/dispersion and centroid-relative formation descriptions.
- Player-team and team-team synchronization/relative phase.
- Pairwise and collective movement correlation.
- Dynamic marking networks and target-allocation summaries.
- Time-resolved man/zonal assignment inference in structured set pieces.
- Tracking-based defensive analysis and expected-versus-observed gravity concepts.

## What Appears Less Explored Among the Reviewed Sources

- A leave-one-out defending-outfield centroid explicitly excluding focal defender and goalkeeper.
- Accumulated two-dimensional focal-relative path as the primary individual primitive.
- Validation that separates this path from focal absolute, collective, aggregate defensive, and ball activity.
- Frozen misaligned/common-translation negative references plus smoothing/window sensitivity.
- Development/held-out replication while withholding tactical interpretation.

These are “not identified” findings, not universal absence claims.

## Novelty Decomposition

### Measurement Novelty

**Limited.** We did not identify the exact formula in the reviewed sources, but it is a transparent refinement of established player-centroid geometry. Strong measurement novelty is not supportable.

### Validation Novelty

**Potentially meaningful.** The closest literature did not reveal Phase 4's combination of explicit activity alternatives, negative collective references, frozen sensitivities, and held-out replication. The contribution exists only if the unchanged test produces interpretable evidence or a generalizable falsification lesson.

### Defensive-Application Novelty

**Plausible, not established.** Existing centroid work often targets team shape, dispersion, synchrony, or training effects. The specific interpretation-light focus on an individual defender's residual movement relative to the other defenders appears less developed. Recent defensive assignment/network work uses different relational objects.

### Conceptual Novelty

**High-risk and conditional.** A later bridge from validated residual movement to multi-relational defensive adjustment may be distinctive, but marking, synchronization, and reciprocal-compensation literatures occupy much of that conceptual space. Relational reconfiguration remains empirically unvalidated.

### Future-Application Novelty

**Separate.** Attacker-induced response, gravity, and off-ball value would require attribution and expected-response models. They remain possible later contributions whether or not the primitive is mathematically novel.

## Implications for Phase 4 Description

If Phase 4 succeeds, describe it as rigorous held-out validation of a simple leave-one-out collective-relative defensive movement primitive. Do not describe it as invention of centroid-relative motion, player-team decomposition, synchronization, defensive response, or gravity.

If Phase 4 fails, do not assume a publishable negative result. A methodological contribution would require showing that the failure generalizes or exposes a consequential validation problem in widely used centroid-relative measures.

## Final Assessment

**B — Limited measurement novelty but meaningful validation/application novelty may be possible.**

Among the reviewed sources, we did not identify a paper operationally equivalent across reference, quantity, validation, and soccer use. Nevertheless, the geometric family is clearly established. The strongest credible future claim is about what the frozen validation design establishes beyond ordinary activity, not ownership of the underlying centroid-relative idea.
