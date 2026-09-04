# Artificial-Transition Feasibility and Design Audit

**Date:** 2026-09-04

**Scope:** literature and design only; no artificial-transition outcome was computed

**Decision:** **C — strong post-Sloan follow-up; do not distract the current paper**

## Bottom line

An artificial transition is a useful practitioner concept for a rapid attack launched from retained, previously settled possession after the defending team has been drawn away from a compact or stable arrangement. It differs from a natural transition because no turnover launches the attack. The concept fits Moving the Defense: the project can measure internal defensive movement that a shared team shift would hide. But the existing localized near-versus-middle result is only one attacker-centred component of the required possession-level construct. It does not by itself establish that the defending team was destabilized, that a press was baited, or that the later attack was caused by the earlier geometry.

The strongest first study would ask whether greater, pre-release defensive destabilization during objectively retained and settled possession is associated with a subsequent rapid goalward release in the same possession. That study should preserve several interpretable geometric channels rather than collapse them into an index. It also needs a separately defined natural-transition control, ordinary-possession controls, and later blinded football/video review. This is scientifically promising but too large and semantically dependent to add safely before the October 1 Sloan abstract deadline.

## 1. Literature and terminology

### Practical definition

For a future study, use **candidate artificial transition** to mean:

> a rapid goalward release from retained possession, preceded by an objectively settled possession interval and measurable defensive reorganization, with no intervening possession turnover.

“Candidate” is essential. Tracking can establish the temporal and geometric sequence; it cannot establish that the attacking team deliberately baited a press or caused the defensive change.

### Closest precedents

- Premier League tactical analysis describes press baiting as drawing opponents toward the ball to create space, then accelerating forward while retaining possession so that the attack resembles a counterattack. This is the clearest practitioner account of the distinction between a turnover transition and an [“artificial transition”](https://www.premierleague.com/en/news/3906870).
- Daniel A. Pritchard’s 2024 Hudl StatsBomb Conference paper, [*Risks and rewards of executing transition events from settled possession*](https://blogarchive.statsbomb.com/uploads/2024/11/Daniel-Pritchard-Research-Paper-Hudl-Statsbomb-Conference-2024.pdf), is the closest quantitative precedent. Its “Torero” approach identifies settled possession using three passes or a pause, uses StatsBomb events and 360 frames to identify defenders outside a half-level block envelope, and defines transition events through passes/carries that pack defenders. Several choices were refined through footage review. This is substantive prior art, not merely a tactical article.
- Academic transition research generally defines transition relative to a possession change. For example, [Forcher et al.](https://link.springer.com/article/10.1007/s10618-021-00763-7) define the transition phase after a win/loss of possession and show that a tactical construct such as counterpressing required expert definitions and more than 20,000 manually labelled situations.
- [Deb et al.](https://doi.org/10.1177/22150218241290988) combine event possessions with expert-notated phases and opposition states. Their agreement results support the view that possession boundaries can be data-defined while higher-level phase and pressure semantics still require operational definitions and human validation.
- Tracking-only possession/event detection is possible in principle, as shown by [Vidal-Codina et al.](https://link.springer.com/article/10.1007/s12283-022-00381-6), but this project should prefer explicit provider/event possession where it is available rather than introduce a new possession model.

### Consensus boundary

The reviewed sources do **not** establish an accepted quantitative definition of artificial transition. The practitioner concept is recognizable; the measurement is not standardized. Pritchard already operationalizes transition events from settled possession and includes defensive-block displacement, so neither artificial-transition detection nor defensive geometry in this setting can be claimed as new in general.

Events are best suited to possession continuity, turnovers, passes/carries, line breaks, and release anchors. Continuous tracking is needed to decide whether the defense was initially settled, separate collective shifting from internal reorganization, and measure shape change. Deliberate baiting, tactical intent, whether a defense was genuinely “drawn,” and whether a sequence deserves the football label remain interpretive.

## 2. Connection to the current project

The existing governed quantities map onto the concept as follows.

| Existing quantity | Possible role | Boundary |
|---|---|---|
| Defensive centroid movement | Shared defensive shift and baseline stability | A stable centroid can hide opposing player movements; a moving centroid is not itself destabilization. |
| Defender-relative movement | Internal movement beyond the shared shift | Validated geometry, not a tactical response or press-baiting measure. |
| Near-versus-middle localization | Localized attacker-centred reorganization channel | Too local and focal-player-centred to represent possession-level destabilization alone. |
| Defensive width/depth and internal spacing | Team/local shape deformation | Must stay separate by axis; contraction can be appropriate and is not automatically instability. |
| Prior unit activity | Settled-state and generic-motion context | A covariate/baseline, not a definition of organization. |
| Attacker–ball and attacker–unit position | Starting context | The supported IDSSE context result does **not** prove press baiting and should not define artificial-transition candidates. |
| Attacker-before-defender temporal design | Ordering template | Temporal order is not causation; positive reverse-time/shared-context structure remains possible. |

**Assessment:** the validated defender-relative primitive is **one component of a broader, low-dimensional destabilization representation**. It is not sufficient by itself. A future design must operate at the possession level and retain collective shift, internal shape, and local reorganization as separate channels.

The supported IDSSE context result found stronger localized reorganization when the focal attacker began less goalward relative to the unit and closer to the ball, conditional on the frozen controls. That pattern is compatible with many kinds of ordinary circulation and shared match context. It must not be used as a press-baiting label or as a post-hoc candidate-selection rule.

### Candidate measurement families

| Candidate | Audit decision | Reason |
|---|---|---|
| Existing localized defender-relative reorganization aggregated across active attackers | **Integrate, not sufficient alone** | It is the best validated local channel, but aggregation can double-count simultaneous attackers and does not describe the whole unit. |
| Width, depth, stretch, and selected spacing | **Integrate as separate shape channels** | They expose anisotropic deformation but can hide offsetting player movements and have no inherent good/bad interpretation. |
| Centroid-relative player displacement from a recent baseline | **Primary team-level candidate** | It directly separates collective shift from internal movement while retaining individual vectors. |
| Defender-to-ball convergence plus movement elsewhere | **Secondary contextual channel** | It can distinguish ballward redistribution from generic shape change, but ball motion may drive both. |
| Graph/relational shape change | **Defer** | Relationship selection and flexibility create avoidable falsifiability and complexity risks for v1. |
| Low-dimensional destabilization vector | **Preferred architecture, not a score** | Report the above channels jointly and separately; do not weight, sum, or optimize them into an index. |

## 3. Three-stage framework

This is a design scaffold, not a protocol. Thresholds, durations, and cut-points are intentionally not selected here.

### Stage A — settled or controlled possession

Require all of the following classes of evidence over a fixed pre-release baseline:

1. **Retained possession:** the same team has controlled the ball continuously; no recent turnover, restart, or dead-ball interruption.
2. **Time to settle:** a prospectively chosen minimum possession duration or event sequence, informed by prior literature rather than later outcomes.
3. **Controlled progression:** recent goalward ball progression and ball speed are low or stable relative to a prospectively stated physical-unit rule.
4. **Defensive baseline:** defending-team centroid speed and width/depth/configuration variability are sufficiently stable to define a recent reference.
5. **Support:** complete, valid player/ball tracking and attacking direction throughout the baseline and candidate interval.

The football label “build-up” is not required. The geometry should establish only that possession was retained and the recent ball/defensive configuration supplied a usable baseline.

### Stage B — defensive destabilization or reorganization

Keep a small vector of transparent measurements rather than construct a score:

- **internal defender-relative movement:** accumulated defender displacement relative to the defending unit, including the existing near-versus-middle view where a prospectively eligible focal attacker exists;
- **shape deformation:** separate changes in defensive width, depth, selected local spacing, and possibly centroid-relative configuration;
- **ballward redistribution:** defender-to-ball convergence together with separately reported movement elsewhere in the unit;
- **collective shift:** centroid displacement retained as context so internal change is not confused with the whole unit moving together.

This stage should be called **measurable defensive reorganization** until semantic review supports stronger football language. A simple graph representation is unnecessary for v1. The existing localized primitive may be a primary channel, but it cannot be the only channel because artificial transition is a team/possession-level concept and may be created by on-ball as well as off-ball movement.

### Stage C — rapid release

Prefer a model-light, physical-unit definition based on retained possession:

1. a marked increase in attacking-direction ball velocity relative to the preceding baseline; and
2. a minimum cumulative goalward territory gain over a fixed short horizon;
3. with no possession change between the settled baseline and release.

Event-based line breaking, final-third entry, or a progressive pass/carry can be secondary descriptors or anchor checks. They should not replace the continuous ball criterion, and no xT/value model is needed. A normal forward pass must not qualify solely because it is progressive; the release requires a predeclared change in tempo plus substantial short-horizon progression.

Attacking-team forward velocity and the number of attackers ahead of the ball are plausible secondary descriptions, but they add support and interpretation burdens and should not enter the first release rule unless independently justified before outcomes.

## 4. Natural and ordinary controls

| Sequence | Required temporal structure | Purpose |
|---|---|---|
| Candidate artificial transition | Retained possession → settled baseline → defensive reorganization → rapid release | Target observational sequence; no intent/causation label. |
| Natural transition | Possession gain immediately precedes rapid goalward progression | Tests whether the retained-possession sequence resembles turnover-led transition geometry. |
| Ordinary positional attack | Retained/settled possession without a qualifying rapid release, matched on period, ball location, possession duration, and broad game context | Tests whether reorganization is merely ordinary active-possession movement. |

Natural and artificial sequences should not be treated as exchangeable without adjustment: their starting shapes and possession histories differ by construction. Ordinary controls should be selected without using the future defensive measurement. A shifted-time or within-possession placebo remains useful for shared motion, but it is not a semantic control.

## 5. Unit of analysis

The most defensible unit is a **possession segment anchored at a candidate release**:

- one row represents one retained possession’s settled baseline, reorganization interval, and release horizon;
- the possession is the grouping unit for simultaneous attackers and repeated candidate anchors;
- candidate release anchors are defined from ball/event information before inspecting defender outcomes;
- overlapping anchors within one possession require a prospective earliest/non-overlap or hierarchical rule;
- bootstrap or uncertainty must group within match-period and possession, with player/team repetition treated explicitly.

Rolling frame windows would create millions of dependent pseudo-observations and obscure the football sequence. A whole possession is too coarse when it contains several slow/fast phases. The anchored possession segment preserves both interpretation and temporal order.

## 6. Data-source feasibility

This is a support/metadata audit only. No SkillCorner outcome, Game 3 data, or artificial-transition result was opened.

| Data source | Useful support | Main limitation | Feasibility role |
|---|---|---|---|
| Metrica Sample Games 1–2 | Synchronized 25 Hz tracking/events, ball, period/frame clocks, full-pitch player support, attacking direction; already governed locally | Only two anonymized sample matches; possession is event-derived rather than an explicit frame field; no synchronized public match video in the sample repository | Best low-cost development fixtures and visual geometry checks, not a sufficient final study. |
| Seven IDSSE/Sportec matches | Continuous official 25 Hz full-team/ball tracking; synchronized events; explicit ball state/possessing team; identities, lineups, substitutions; 10 teams with Fortuna Düsseldorf repeated in five matches | Only seven matches and one repeatedly observed team; the public release explicitly excludes match video | Strongest current quantitative environment and best first multi-match execution after a protocol is frozen. |
| Metrica Sample Game 3 | Public tracking/events and a separate Metrica video-project route are documented | Reserved pristine holdout; different format and no authorization here | **Untouched; do not use for this audit or initial design.** |
| SkillCorner Open Data | Ten 2024/25 A-League matches; 10 Hz broadcast tracking with ball, possession, detected/extrapolated flags; Dynamic Events and concurrent in/out-of-possession phase files; repeated teams (Auckland FC appears in four matches) | Broadcast visibility/extrapolation, reported identity error, kinematic QC need, and provider-derived/ML phase semantics; no source broadcast video in the repository | Materially useful later for candidate release/possession scaffolding and cross-provider support, but not automatically better than IDSSE for complete defensive geometry. |
| PFF/Gradient World Cup | Documented future broadcast/off-ball context source | Not integrated; visibility and derived-run semantics require equivalence work | Later comparator only. |
| Alfheim/Signality and other small public sources | Some tracking and video availability | Very small samples; tracking/video may be unsynchronized; events often absent | Potential semantic fixture after an explicit alignment audit, not a primary dataset. |

### Is SkillCorner materially better?

SkillCorner is **materially better for ready-made possession/phase and release-candidate metadata**, not necessarily for the core defensive-geometry measurement. Its current [open-data release](https://github.com/SkillCorner/opendata) includes ten matches, frame-level possession, Dynamic Events, and phases of play. The phase specification itself combines tracking, dynamic possession events, ball location, pressure, and defensive-line position. Those fields can support an independent comparison, but using them as definitions would import provider models into the target construct.

IDSSE remains better for continuous complete-team geometry and exact event/tracking synchronization. SkillCorner should enter only after an outcome-blind support/equivalence gate preserves player identity, observed versus extrapolated status, full defensive-unit coverage, ball continuity, and the existing defender-relative quantities. Its phase labels should be treated as a comparator or semantic aid, not ground truth.

## 7. Candidate primary questions

Scores are qualitative (1 low, 5 high); causal risk and cost are worse when higher.

| Rank | Question | Football value | Novelty | Causal risk | Data need | Sloan appeal | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | **A. Is greater defensive destabilization during settled possession associated with a subsequent rapid release without turnover?** | 5 | 4 | 3 | 4 | 5 | 4 |
| 2 | **B. Do prospectively defined candidate artificial-transition possessions show more prior reorganization than matched ordinary positional possessions?** | 4 | 3 | 3 | 4 | 4 | 4 |
| 3 | **D. Can a model-light representation distinguish retained-possession releases from natural transitions?** | 4 | 3 | 2 | 5 | 4 | 5 |
| 4 | **C. Can reorganization identify sequences that “successfully manufacture” transition-like conditions?** | 5 | 4 | 5 | 5 | 5 | 5 |

**Best v1 question:** Option A, phrased as a time-ordered observational association. It allows continuous or binary rapid-release outcomes, does not require the public claim that every candidate is truly artificial, and directly tests whether defensive reorganization adds information beyond a settled-possession baseline. Option C is not suitable for v1 because “manufacture” and “successfully” embed causation and value.

## 8. Semantic validation

Human/video validation is essential before a public claim about artificial transitions, press baiting, or deliberate induced movement. A later validation should:

1. freeze the candidate generator and controls before review;
2. draw a deterministic, balanced sample across matches, teams, candidate strengths, and controls;
3. hide the defensive measurement and algorithmic class from reviewers;
4. use at least two football analysts and an explicit rubric: artificial transition, natural transition, ordinary progression, or unclear;
5. report inter-rater agreement and adjudication separately;
6. preserve “unclear” rather than forcing consensus.

The current public Metrica 1–2, IDSSE, and SkillCorner repositories do not provide a straightforward synchronized broadcast-video validation layer. That is a real feasibility constraint, not a reason to substitute 2D tracking animations for football-semantic evidence.

## 9. Novelty assessment

Pritchard already combines settled-possession rules, defender displacement relative to an estimated block, packed-player counts, events, 360 context, and footage review. Therefore the broad idea “quantify artificial transitions by how the defense is pulled” is prior art.

The potentially differentiated contribution, among the reviewed sources, is narrower:

- decompose shared defensive shifting from internal defender-relative reorganization using full continuous tracking;
- retain localized, whole-unit, and shape-deformation channels separately rather than using a half-level block envelope;
- prospectively separate settled state, defensive change, and release without defining any stage from later value;
- compare retained-possession releases with natural transitions and ordinary positional controls;
- carry the same governed geometry across full-tracking providers before tactical interpretation.

That is potential measurement/validation novelty, not a claim that artificial transitions or defensive-block analysis are new.

## 10. Sloan payoff, cost, and risk

### Payoff

If successful, the sequence would give the current measurement a compelling football application. But it would also add three new constructs—settled state, destabilization, and rapid release—plus controls and semantic validation. With less than one month to the October 1 abstract deadline, a credible result would require more than a bounded add-on. The current paper already has replicated measurement, time-order controls, context characterization, and explicit negative boundaries. It does not need artificial transitions to form a coherent submission.

### Expected cost

**Implementation/Codex cost: high.** A defensible study requires at least four governed passes after this audit: (1) outcome-blind support and possession/release feasibility, (2) prospective construct/protocol freeze, (3) development plus deterministic reproduction, and (4) heldout/external and semantic validation. SkillCorner would add a separate identity/support/equivalence pass. The human-review burden is also nontrivial because video access, rubric design, and multiple reviewers cannot be replaced by code.

### Major risks

- no standardized quantitative definition and substantial semantic ambiguity;
- circularity if “destabilization” helps select candidates and is then the tested predictor;
- ordinary ball-driven collective movement masquerading as induced defensive change;
- local near-versus-middle geometry missing team-level opening elsewhere;
- many releases arising without measurable destabilization, or much reorganization not followed by release;
- natural transitions differing in starting state so strongly that comparison becomes confounded;
- limited match/team independence in Metrica and IDSSE;
- unavailable public synchronized video for the strongest full-tracking datasets;
- SkillCorner visibility, identity, extrapolation, and provider-model dependence;
- scope creep and an inconclusive result weakening the clarity of the current paper.

## 11. Decision and recommended next step

**Decision: C — STRONG POST-SLOAN FOLLOW-UP, DO NOT DISTRACT CURRENT PAPER.**

The concept is a good fit for the measurement, and Option A is a defensible candidate v1 question. It is not ready for an empirical protocol because the settled-state and release representations, video-validation access, and possession-level use of local versus whole-unit geometry are not yet uniquely justified.

**Exact next step (post-Sloan):** conduct an outcome-blind support and annotation-feasibility sprint on metadata/ball/event streams only. Before opening defender outcomes, predeclare candidate possession-segment construction, quantify candidate counts and support in Metrica Games 1–2 and IDSSE, verify that natural-transition and ordinary-possession controls can be formed, and secure a blinded video-review route. Stop if complete possession segments or semantic video cannot be supported. Do not open Game 3 or SkillCorner defensive outcomes in that sprint.

No empirical protocol is frozen by this document.
