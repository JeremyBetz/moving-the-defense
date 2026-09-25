# Off-Ball Movement Direction and Localized Defensive Reorganization in Football

## Sloan submission strategy — September 2026

## Submission case

This paper asks a football-facing measurement question: when a defensive unit
shifts together, how can tracking distinguish that shared shift from nearby
defenders changing position within the unit? The paper's contribution is a
prospectively tested, externally replicated temporal estimand for localized
defensive reorganization. It does not claim a new centroid method, a causal
attacker effect, tactical superiority, or attacking value.

The argument proceeds in two steps. First, preceding off-ball attacker movement
is associated with stronger subsequent defender-relative movement among near
than middle-ranked defenders, under a protected Metrica sequence and an
external IDSSE analysis. The paired reverse-time comparison qualifies this
result: reverse-time structure remains positive, but the correctly ordered
association is larger. Second, the paper's main empirical centerpiece is a
replicated directional difference: conditional on path magnitude and starting
geometry, outward movement is more strongly associated with subsequent
localized defensive reorganization than goalward movement in separate IDSSE and
original SkillCorner analyses, then prospectively replicates in ten additional
nonoverlapping SkillCorner matches.

## Submission abstract

**Introduction.** A defence can shift together while nearby defenders also change
position within the unit. We call movement by nearby defenders relative to the
wider defensive unit localized defensive reorganization. Distinguishing these
geometries lets us ask whether off-ball movement away from the pitch centreline
(“outward”) is associated with different subsequent reorganization than comparable
movement toward goal.

**Methods.** Fixed, adjacent two-second intervals measured attacker movement
and subsequent defender-relative path. We compared the average accumulated
defender-relative path of the nearest three defenders with that of four
middle-ranked defenders, fixing proximity ranks before the defender interval
without inferring marking assignments. The temporal design was developed in
Metrica Game 1, tested in held-out Game 2, and evaluated externally in seven
IDSSE matches using a paired reverse-time comparison. Directional models
conditioned on attacker path magnitude and starting geometry, with a separate
nine-match SkillCorner replication and a prospectively frozen replication in
ten additional nonoverlapping SkillCorner matches; cohorts and tracking
environments were analysed separately, not pooled. Uncertainty was estimated by block bootstrap,
preserving simultaneous attacker perspectives and temporal grouping rather
than treating individual observations as independent.

**Results.** Outward movement was associated with greater subsequent localized
reorganization than goalward movement in all three separately analysed cohorts. For the
prespecified comparison of straight 5 m outward versus straight 5 m goalward
movement, holding modeled path magnitude and context equal, the
near-minus-middle path difference was approximately 28 cm in IDSSE (95%
interval: 26–31 cm) and 24 cm in SkillCorner (21–27 cm). These are
differences between group-average defender-relative paths, not additional
movement by each defender. Directional contrasts were positive in all seven
IDSSE and all nine original SkillCorner matches. In the prospectively frozen
additional SkillCorner population, the contrast was 0.05501 m/m [0.05006,
0.06002], with positive match and leave-one-match-out estimates in all 10/10
matches. The temporal near-minus-middle
association also replicated from Metrica to IDSSE (0.06115 m/m, 95% CI
[0.05579, 0.06681]) and was positive in all seven IDSSE matches. The IDSSE
forward-minus-reverse excess was 0.02455 m/m [0.01932, 0.02985], positive in
all seven matches, although reverse-time structure remained positive. A
secondary analysis associated goalward movement more strongly with
collective defensive translation; the proposed width-narrowing explanation
was not established.

**Conclusion.** The findings show that goalward progression and localized
defensive reorganization are distinct geometric descriptions of off-ball movement.
They do not establish causation, marking responsibility, tactical
effectiveness or attacking value. The measurement could provide a
descriptive layer for organizing candidate passages for subsequent video
review; its football interpretation and review usefulness remain unvalidated.

## Visual argument

Use exactly two main figures. They should make one visual argument:

> What is being measured? → What surprising directional result does the measure reveal?

| Figure | Role | Required message |
|---|---|---|
| **Figure 1 — Temporal flagship** | Establishes the measurement and temporal validation. | A protected-holdout Metrica passage distinguishes a shared defensive shift from defender-relative movement; accompanying estimates show the Metrica/IDSSE temporal pattern and paired forward-versus-reverse qualification. The passage illustrates geometry and does not assign movement to one attacker. |
| **Figure 2 — Outward-versus-goalward replication** | Main empirical centerpiece. | Separate IDSSE, original SkillCorner, and prospective additional SkillCorner estimates show the replicated directional difference. Keep cohort-specific results and uncertainty visible; do not pool providers or the two SkillCorner cohorts. |

If a combined figure/table limit of two applies, retain these two figures. Keep
the comprehensive results table supplementary or repository-facing.

## Results hierarchy

1. **Temporal localization:** near defenders show a stronger subsequent
   defender-relative association than middle-ranked defenders after preceding
   attacker movement.
2. **Replicated directional difference:** outward rather than goalward movement
   is more strongly associated with subsequent localized defensive
   reorganization in the separate IDSSE and original SkillCorner analyses and
   in the prospectively frozen ten-match additional SkillCorner cohort.
3. **Starting context:** attacker--unit goalward position and attacker--ball
   distance characterize where the IDSSE association is larger or smaller. Keep
   this in the full paper, not as a central abstract result.
4. **Response-scale boundary:** goalward movement is secondarily associated
   with collective defensive translation; the proposed width-narrowing
   mechanism was not established.
5. **Downstream boundary:** a separate opportunity-redistribution test did not
   support equating measured reorganization with improved nearby teammate
   separation. Keep this qualitative limitation outside the abstract.

## Practical relevance and claim boundary

The bounded application is:

> The measurement can filter for passages in which nearby defenders moved
> differently from the defensive unit after an attacker moved, allowing analysts
> to inspect video and decide whether the geometry has football meaning.

This is a plausible analyst workflow, not independently validated retrieval
usefulness. It does not support player rankings, automatic tactical labels, or
a value model.

Use the following concise limits in the paper and abstract as needed:

- the results are observational associations, not causation;
- the directional result is not a claim of tactical superiority or value;
- reverse-time structure remains positive, so the temporal evidence is an
  ordered excess rather than a null control; and
- the mechanism behind the directional difference remains unresolved.

## Novelty positioning

Centroid and player-to-team-relative geometry, temporal defensive change, and
directional coordination all have established precedents. The contribution is
the specific prospectively ordered, start-fixed local-response estimand and its
replicated outward-versus-goalward directional difference across independent
tracking environments. Position this as a bounded measurement and validation
contribution, not as the first defensive-response metric or an unprecedented
football concept.

## Reproducibility and supplementary material

The public repository is [moving-the-defense](https://github.com/JeremyBetz/moving-the-defense).
Direct readers to [REPRODUCE.md](../REPRODUCE.md) for the human-first
reproduction path and to the repository documentation for detailed technical
materials. Keep full support rules, provider-compatibility details, complete
rank profiles, robustness tables, and result provenance supplementary or
repository-facing rather than in the submission narrative.

## Submission administration — manual verification

Before portal submission, complete the following manual checks. Items are not
assertions about current portal requirements.

- [ ] Confirm the title: *Off-Ball Movement Direction and Localized Defensive
  Reorganization in Football*. **FINAL PORTAL CHECK REQUIRED**
- [ ] Confirm abstract word count and required section labels. **FINAL PORTAL
  CHECK REQUIRED**
- [ ] Confirm the combined figure/table limit and retain the two-figure plan
  only if permitted. **FINAL PORTAL CHECK REQUIRED**
- [ ] Confirm the public repository link. **FINAL PORTAL CHECK REQUIRED**
- [ ] Confirm author information and affiliations. **FINAL PORTAL CHECK
  REQUIRED**
- [ ] Confirm final portal fields, submission format, and upload requirements.
  **FINAL PORTAL CHECK REQUIRED**
- [ ] Confirm final figure file format and resolution. **FINAL PORTAL CHECK
  REQUIRED**
