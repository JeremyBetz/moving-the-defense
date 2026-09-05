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
SkillCorner analyses.

## Submission abstract

**Introduction.** Off-ball movement can coincide with a shared defensive shift
or with defenders changing position within the defensive unit. Tracking analyses
need to distinguish those geometries. We examine whether this localized movement
is associated differently with outward and goalward attacker movement, rather
than treating either direction as a tactical label or a measure of value.

**Methods.** Fixed windows measured attacker path before subsequent
defender-relative path. Start-fixed proximity ranks compared the three nearest
defenders with four middle-ranked defenders without inferring marking
assignments. The temporal design was developed and held out in Metrica, then
tested externally in seven IDSSE matches with a paired reverse-time comparison.
The directional comparison was separately replicated in nine SkillCorner
matches. The local outcome retained a shared defensive shift as context rather
than treating all observed defender movement as one quantity. Proximity was a
localization device, not an assignment of defensive responsibility.

**Results.** In pooled Metrica, the near-minus-middle association was 0.05029
m/m (97.5% interval [0.03433, 0.06858]). In IDSSE it was 0.06115 m/m (95% CI
[0.05579, 0.06681]), and the paired forward-minus-reverse excess was 0.02455
[0.01932, 0.02985]; both estimates were positive in all seven matches.
Reverse-time structure nevertheless remained positive. The central finding was
a replicated directional difference: conditional on path magnitude and starting
geometry, outward minus goalward movement was 0.056856 m/m [0.051358, 0.062430]
in IDSSE and 0.048883 m/m [0.042940, 0.054707] in SkillCorner. Goalward movement
was instead more strongly associated with secondary collective defensive
translation, while the proposed width-narrowing mechanism was not established.
The external environments were analysed separately under provider-compatible
specifications, so their agreement is replication evidence rather than a pooled
cross-provider effect.

**Conclusion.** The analysis provides a prospectively tested and externally
replicated temporal measure of localized defensive reorganization. It can help
structure later video review by separating internal movement from a shared
defensive shift. The findings are observational associations, not estimates of
causal influence, named tactical behaviour, or attacking value. The measure is
a descriptive layer for later football interpretation, not a tactical classifier.

## Visual argument

Use exactly two main figures. They should make one visual argument:

> What is being measured? → What surprising directional result does the measure reveal?

| Figure | Role | Required message |
|---|---|---|
| **Figure 1 — Temporal flagship** | Establishes the measurement and temporal validation. | A protected-holdout Metrica passage distinguishes a shared defensive shift from defender-relative movement; accompanying estimates show the Metrica/IDSSE temporal pattern and paired forward-versus-reverse qualification. The passage illustrates geometry and does not assign movement to one attacker. |
| **Figure 2 — Outward-versus-goalward replication** | Main empirical centerpiece. | Separate IDSSE and SkillCorner estimates show the replicated directional difference. Keep provider-specific results and uncertainty visible; do not pool the environments. |

If a combined figure/table limit of two applies, retain these two figures. Keep
the comprehensive results table supplementary or repository-facing.

## Results hierarchy

1. **Temporal localization:** near defenders show a stronger subsequent
   defender-relative association than middle-ranked defenders after preceding
   attacker movement.
2. **Replicated directional difference:** outward rather than goalward movement
   is more strongly associated with subsequent localized defensive
   reorganization in the separate IDSSE and SkillCorner analyses.
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
