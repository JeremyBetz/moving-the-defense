# Conceptual Framework

> **Current status (post–Phase 5B audits):** focal-relative path has passed held-out Metrica validation and external geometric replication across seven IDSSE matches from one independent provider environment. Phase 5A establishes contextual-prediction feasibility, driven primarily by recent focal movement. Phase 5B finds only a small, mixed opponent-information increment. Signed displacement is retained descriptively; continuation innovation is not a validated onset measure; and attacker-only speed-valley segmentation is B — mixed because fragmentation is common. Tactical defensive response and relational reconfiguration remain unvalidated. Historical sections preserve ideas later weakened or rejected and should be read with the [claim-status ledger](claim_status.md).

Frozen Phase 5B v1.0 produced B — mixed/partial: prospectively selected opponent information improved six of seven held-out matches, but median gains were below 1%, no adjacent increment was material, and local attackers did not consistently outperform nonlocal controls. This is limited opponent-information association. Geometric proximity is not a tactical relationship, and predictive increment is not attacker causation or defensive response.

The full evidentiary sequence is **football question → measurable attacking movement → measurable defensive movement → individual movement relative to the defensive unit → movement magnitude and signed geometric change → contextual expectation → opponent-information association → tactical defensive-response interpretation → attacker attribution → value**. Every arrow is conditional. Phase 5B supplies limited evidence only at opponent-information association; the post-5B segmentation audit moves upstream to the still-unvalidated attacking temporal unit.

Post-5B Measurement Audit A preserves focal-relative path as the validated amount-of-movement primitive while testing two additions in Sample Game 1: signed net displacement and deterministic short-horizon continuation innovation. Directional displacement is retained as a complementary descriptive representation because it preserves axis/sign distinctions that scalar path collapses. Continuation innovation receives only a mixed audit result because neutral windows overlap the anchors and several movements are already underway in the preceding two seconds. It is not retained as a validated response-onset measure; its horizons, thresholds, persistence rules, and candidate times must not be tuned from this audit. A future representation may need to describe change across a finite interval rather than require one universal onset instant, but that is a research implication rather than an established result. No new inference-ladder level is established.

The outcome-blind movement-segmentation audit moves upstream from defense and uses only an attacking player's own trajectory. Speed-valley intervals preserve signed geometry and substantial lower-speed movement, but the tested implementation is B — mixed because it over-fragments many trajectories and occasionally merges long or multi-leg motion. A frozen prominence refinement also classified B: it removed fragmentation aggressively but drove merging/direction far beyond the safety cap, so no threshold was selected and Game 2 was not opened. “Movement-effort episode” therefore remains an unresolved geometric temporal unit, not a tactical run, defensive response, or attacker-influence event.

## 1. Project Focus

The single formal primary research question is: **How can tracking data measure defensive responses to attacking movement in open-play football?**

The motivating football question is: **When an attacker does not receive the ball, can we measure what they made the defense do?** A downstream translation question asks whether football concepts such as pinning, dragging, tracking, covering, handing off, and stretching can eventually be connected to validated, interpretable tracking patterns. It is nested within the broader program and does not imply those concepts are already measurable.

**Defensive response** means observable individual or collective defensive behavior occurring in the context of attacking positioning or movement. It is an empirical umbrella, not a causal conclusion. Tracking does not observe cognition, attention, responsibility, instruction, intention, decision-making, or psychological workload. Association, attacker attribution, causation, and attacking value are separate stages.

Three vocabularies must remain distinct:

1. **Football language:** pin, drag, track, cover, pass on, step, hold, shift, squeeze, stretch, overload, recover.
2. **Observable tracking language:** position, displacement, velocity, focal-relative path, collective translation, local deformation, opponent coupling, distance, persistence, width/depth, temporal correspondence.
3. **Theoretical language:** defensive response, relational reconfiguration, ambiguity, collective accommodation, propagation, recovery burden, attacker-associated response, off-ball influence.

**Football concept ≠ tracking measurement ≠ theoretical mechanism.** See the [football-concept translation framework](football_concept_translation_framework.md).

The historical framing emphasized **defensive state change and decision instability**, not space creation alone. The current working hypothesis is more relational: open-play defensive behavior is continuously multi-relational and may not be well represented by mutually exclusive Structure / Track / Close / Recover states.

The historical refined phenomenon was **sharp changes in the relative explanatory strength of competing observable relationships**—including collective-team, ball-relative, and opponent-relative movement. It remains a conceptual candidate rather than the single organizing target.

Historically, the project asked whether open-play tracking data could describe a defender's movement as an allocation between competing behavioral responsibilities, and whether attacking movement was associated with changes in that allocation. That remains a motivating theory, not the current validated empirical target. The current methodological frontier is narrower: whether attacking movement and defensive geometric change can each be represented as defensible finite units before their relationship is tested.

This is a behavioral framework. Tracking data observes player locations and movement; it does not observe cognition, communication, tactical instructions, or what a defender “believes.” Terms such as responsibility and decision instability are interpretations of observable behavior and must be written with that limitation intact.

**Defensive relational reallocation** is historical provisional language for substantial change in which observable relationships best explain movement. The preferred empirical term remains **relational reconfiguration**: a possible intermediate defensive response in which defender-team, defender-opponent, ball, and local relationships change coherently over time. It is not the project's umbrella and remains unvalidated.

## 2. Broader Theory: Asking Questions

Football can be viewed partly as a competition over which team determines the problems both teams must solve. Positioning, rotations, runs, and threatened actions can pose tactical questions. Physical and technical qualities can make a threat more credible or cheaper for the attacker to pose.

The broader hypothesis is that a team may gain control by imposing repeated defensive recognition and adjustment while its own movements remain comparatively simple or rehearsed. This is a theory about **asymmetric tactical decision load**, not a claim that tracking data measures mental bandwidth.

A cautious conceptual chain is:

**Attacking position or movement → credible tactical threat → possible reconsideration of defensive responsibility → observable behavioral state change or ambiguity → structural adjustment and recovery → possible error, space, or progression**

Every arrow is a proposition to investigate, not an established causal link.

## 3. Historical Construct-Development Framework: Four Hypothesized Behavioral Regimes

The following regimes generated early diagnostics. They are retained for auditability, but they are not an accepted ontology and are not current labels for tracking frames.

### Structure

The defender's behavior is better explained by maintaining a relationship to collective defensive organization than to one particular opponent.

Candidate structural references include a whole-team centroid, local teammate neighborhood, defensive line, unit- or role-specific centroid, ball-relative block position, or a combination. The correct reference may differ by role and phase and remains a research question.

### Track

The defender maintains a comparatively stable attacker-relative position. For defender $d$ and attacker $a$:

$$
\mathbf{r}_{da}(t)=\mathbf{x}_a(t)-\mathbf{x}_d(t)
$$

The early hypothesis was that low variation in this relative position over an appropriate window would be evidence consistent with tracking. Phase 1B rejected fixed attacker-relative Cartesian stability as a general Track primitive. Opponent-relative geometry can still be described, but it does not reveal a formal marking instruction or validated tracking relationship.

### Close

The defender actively changes a relationship by approaching an attacker or the ball. If attacker distance is

$$
r_{da}(t)=\lVert\mathbf{x}_a(t)-\mathbf{x}_d(t)\rVert,
$$

then sustained $dr_{da}/dt<0$, supported by defender velocity projected toward the threat, is evidence consistent with closing. Tracking maintains a relationship; closing reduces it.

This is the historical Phase 0/1 formulation. Phase 1C evidence now makes **Engage** a provisional replacement term for **Close**, but that terminology is not finalized and is not being applied globally yet. The reason is conceptual, not cosmetic: literal reduction of absolute defender–attacker distance is only one way a defender can strengthen or prioritize an opponent relationship.

### Recover

The defender is displaced and moves toward an expected structural position. If $\hat{\mathbf{x}}_{structure}(t)$ is a defensible estimate of that position, recovery is consistent with decreasing

$$
\lVert\mathbf{x}_d(t)-\hat{\mathbf{x}}_{structure}(t)\rVert.
$$

Structure and Recover are distinct: one maintains an existing structural relationship; the other repairs displacement. The expected structural position must be justified rather than assumed.

## 4. States, Transitions, and Ambiguity

The shorthand cycle **Structure → Track → Close → Recover → Structure** is not mandatory. States may be skipped or reversed, a defender may hand responsibility to a teammate, and some movement may be ambiguous or unexplained.

Following Phase 1C, the state-machine interpretation itself is under explicit reconsideration. Structure, Track, provisional Engage/Close, and Recover may be overlapping behavioral dimensions or relational constraints rather than mutually exclusive states. For example, a defender can preserve a structural relationship while also increasing opponent-directed engagement relative to collective movement. The historical state sequence remains useful as an organizing hypothesis, but current evidence does not justify treating it as the assumed ontology.

The multi-relational working hypothesis requires three objects to remain distinct:

1. **Current relational balance:** the contemporaneous pattern of observable fit across collective-team, ball-relative, opponent-relative, and potentially other justified relationships.
2. **Relational ambiguity:** situations in which multiple observable relationships are similarly plausible explanations.
3. **Rate or magnitude of defensive relational reallocation:** how sharply or substantially that explanatory pattern changes.

No relational weights, composite score, or reallocation metric has been defined. “Explanatory strength” remains a construct-development question rather than a licensed numerical object.

Relational strengths also need not be zero-sum. Opponent engagement can increase while collective coherence remains high or also increases. The relevant phenomenon may be coordinated change in several relationships rather than transfer of a fixed amount of defensive “attention.” Any future representation must permit coexistence and reinforcement rather than forcing relational explanations to sum to a fixed total.

### Collective accommodation hypothesis

A new working hypothesis is that effective defending may permit one defender to engage a threat while teammates adjust collectively so that the engagement does not produce large structural compromise. **Collective accommodation** is provisional language for teammate movement that appears to absorb, cover, or support an individual defender's engagement.

This is not a conclusion, causal claim, or team-quality claim. Sample Game 1 cannot establish that better teams accommodate engagement more effectively. Teammate movement may instead reflect ball movement, general block translation, transition, compression, rotation, or independent responsibilities. No accommodation score has been defined.

### Interior-threat structural counterexample

An opponent can receive or occupy space inside the defensive shape, including between recognizable defensive lines, and draw convergence from several defenders. That convergence may increase compactness locally while leaving the whole-team centroid nearly unchanged. At the same time, converging defenders can alter distances and relative positions to other opponents elsewhere.

This is a counterexample to treating centroid stability, whole-team translation, or aggregate compactness as sufficient evidence that defensive structure has been preserved. Opposing defender movements can cancel in a centroid calculation even while local and opponent-relative geometry changes substantially. Aggregate compactness can likewise improve around one threat while other relationships are redistributed.

The resulting distinction is between **local compression around a threat** and **relational exposure elsewhere**. Relational exposure is provisional descriptive language only. Increased distance to another attacker does not by itself mean that attacker is open or that defensive quality has deteriorated: passing access, cover, goal-side position, other defenders, and tactical context may make the change appropriate. No exposure or structure score has been defined.

Current evidence is therefore testing whether defensive structure needs to be represented relationally rather than by a single team-level reference point.

### Phase 2A representation requirement

Phase 2A treats representation design as an information-preservation problem rather than beginning with a metric. Across fixed Phase 1 cases, no single reference view is sufficient. Centroid-relative geometry preserves a useful collective-translation baseline and focal deviation, but it does not identify which local, opponent, or ball relationships changed. Defender–defender geometry preserves local spacing and depth changes but lacks threat and phase context. Defender–opponent geometry preserves threat-relative change but does not establish responsibility, openness, or defensive quality. Ball-relative geometry supplies important shared context but can dominate collective movement without isolating opponent-specific response.

The 1230.12s counterexample makes the minimum information requirement concrete: small centroid movement coexists with changing defender–defender spacing and depth, changing distances and x/y relationships to the focal and secondary attackers, and partially cancelling defender movements. The negative 4197.04s case remains heterogeneous across the same views, showing why access to more pairwise relationships must not be mistaken for coherent reorganization.

The provisional minimum is a sparse, typed relational description that retains: (1) absolute pitch position and a collective-translation baseline; (2) local defender–defender x/y geometry; (3) selected defender–opponent x/y geometry, including secondary opponents only when inspection justifies it; and (4) ball-relative context. Clearly interpretable line/depth views may supplement these quantities but must not be imposed as universal inferred units. These views remain separate; no composite representation, structure score, network, or ranking has been defined. Sparsity and stable relationship types are requirements against making the representation so flexible that arbitrary post hoc pairs can explain every movement.

### Phase 2B temporal refinement

Phase 2B adds a temporal requirement: a defensible relational representation must preserve not only before/after differences but the direction, persistence, and approximate ordering of change within each relationship type. In the 1230.12s case, Away20 and Away21 converge toward Home10 before the event anchor, Away19 initially separates and then reverses, and different defender-pair spacings begin contracting at different times. Selected secondary-opponent and ball-relative relationships also change non-uniformly. The reorganization can therefore be watched unfolding without forcing a discrete state transition.

This supports **defensive relational reallocation** only in a limited descriptive sense: an interpretable temporal reconfiguration of typed geometric relationships. It does not mean transfer of zero-sum relational weights or movement through mutually exclusive states. The typed channels may share ball-driven or collective motion and are not independent causal mechanisms.

Temporal ordering remains coarse. Centered 5/7/9-frame smoothing preserves broad direction changes but shifts or rounds local extrema, while unsmoothed 25 Hz first differences are too noisy for reliable interpretation. Current evidence supports partially staggered change at a broad sub-second-to-second scale, not frame-exact onset, optimized lead–lag estimates, or causal sequencing. The heterogeneous 4197.04s case remains distinguishable descriptively because its typed channels change in opposing ways rather than showing broadly convergent local reorganization; this is not a classification rule.

### Phase 2C episode feasibility

Phase 2C tests whether temporal reconfiguration can be bounded as a candidate interval without collapsing channels. A fixed illustrative diagnostic retains same-direction 7-frame-smoothed change lasting at least 0.6s and examines overlap across typed channels. Direction-agnostic overlap is too permissive: once focal, defender–defender, and defender–opponent relationships are inspected, most eligible active-play windows contain sustained simultaneous change. **Activity is therefore not relational reconfiguration.**

A narrower interior-compression lens—persistent contraction in at least two already-fixed defender pairs and two already-fixed defender–opponent distances—produces a visually defensible 1230.12s interval from approximately −1.20s to +1.84s. Across that interval, all three selected defender pairs contract, all three defenders reduce distance to Home10, selected secondary-opponent relationships redistribute in different directions, and centroid movement remains modest relative to several local changes. The same interval is visible in raw pitch snapshots.

This does not yield a general episode definition. The same fixed logic also identifies tackle/engagement and accommodation intervals and a late interval in the collective-translation contrast, where shared motion remains a strong explanation. It does not represent the focal excursion well. The 4197.04s negative case remains negative without retuning because its selected relationship directions are mixed. Fixed 5/7/9-frame sensitivity preserves broad intervals but shifts their edges.

The conservative conclusion is **B — partially feasible**. A pattern-specific, non-optimized interval can describe one kind of relational reconfiguration, but episode boundaries and interpretation remain too context-sensitive for general use. “Defensive relational reallocation” may provisionally include a bounded interval of persistent, jointly interpretable change in preserved relationship types. It must not mean any multi-channel activity, a universal event, scalar magnitude, causal mechanism, or tactical state.

### Phase 2D geometric motif vocabulary

Phase 2D replaces the search for one universal episode signature with a small descriptive vocabulary of three overlapping geometric motifs. **Coordinated collective translation** emphasizes substantial, broadly aligned absolute and centroid movement with internal geometry remaining comparatively coherent rather than rigid. **Focal excursion** emphasizes one defender's movement relative to the leave-one-out centroid or fixed local teammates, without implying opponent tracking or closing. **Local compression** emphasizes contraction across multiple preselected defender pairs, with centroid movement permitted to be small or large and without implying defensive success or threat control.

The canonical fixed cases support different emphases in raw geometry. At 1888–1896s, centroid net displacement is 31.021m, median outfield displacement is 31.042m, mean displacement-direction cosine is 0.990, and focal leave-one-out net displacement is only 2.099m; internal pair distances still change, so translation is not rigid-shape preservation. At 590–598s, the centroid moves 13.763m while focal leave-one-out net/path movement is 7.625/12.392m and local pair directions are mixed, supporting a focal-excursion description. At 1228.12–1232.12s, centroid net movement is only 2.856m while the three fixed defender-pair changes are −12.40m, −14.73m, and −2.75m, supporting local compression.

The motifs are not mutually exclusive. The tackle window combines highly aligned translation, focal deviation, opponent convergence, and mixed local contraction/expansion. The accommodation window contains compression followed by expansion. The 3682.88s contrast combines a 19.314m centroid displacement with contraction in two fixed local pairs, showing translation plus compression. The unchanged 4197.04s trio remains heterogeneous: two pair distances expand, one contracts, and focal leave-one-out net movement is only 0.524m.

All three motifs are **descriptively supported** in these fixed examples, with context qualifications. A motif vocabulary is provisionally more empirically defensible than a universal relational-reallocation detector because it preserves geometric type, permits overlap and no-clean-motif cases, and remains readable from raw trajectories. It is not a complete taxonomy, motif classifier, or generalizable result. Relationship selection must remain prospective and stable or the vocabulary becomes unfalsifiable.

Defensive relational reallocation is therefore refined as temporal change that may be described through one or more overlapping, football-interpretable geometric motifs while preserving the typed relationships underneath. It is not itself a motif, class, state, score, or universal event. Pinning, handoff, accommodation, rotation, and exposure remain unresolved possibilities rather than motifs added in Phase 2D.

### Phase 2E prospective relationship selection

Phase 2E treats relationship selection as a falsifiability condition rather than a presentation choice. Defender–defender and defender–opponent relationships are selected from raw geometry at the window start, before subsequent change is inspected. Anchor-time selection is retained only as a separate sensitivity check. Fixed-at-start relationships preserve identity and expose staleness; dynamically reselecting the nearest player stays locally current but can introduce identity churn and erase the fixed-pair change under study.

The results weaken any claim that the Phase 2D motifs are already stable under relationship choice. Coordinated translation and focal collective-relative excursion remain comparatively visible because their primary evidence depends less on a selected opponent. By contrast, the 1230.12s local-compression case is rule-sensitive: start-nearest-two and a fixed 15m neighborhood each contain one contracting and at least one expanding focal pair, while the prospectively selected depth/lateral neighbors both contract. The previously illustrated local trio is not recovered by the primary proximity rule. The 3682.88s translation-plus-compression interpretation is likewise not robustly reproduced by the tested start rules, although large collective translation remains clear. The 4197.04s case remains mixed/no-clean-motif without retuning.

The current reproducibility baseline for defender–defender geometry is a start-fixed focal defender plus two nearest outfield teammates, always shown against raw pitch geometry and accompanied by churn and rule-sensitivity reporting. It is usable but context-sensitive, not a validated representation of a defensive unit. Start-fixed nearest opponents can provide prospective geometric context, but proximity is not responsibility, threat, access, or openness; opponent relationships are not yet reliably selectable as substantive defensive relationships. Different relationship types may therefore require different selection logic. Motifs that disappear under a pre-specified rule must be weakened rather than rescued through post hoc pair changes.

### Phase 2F local-configuration representation

Phase 2F tests whether the Phase 2E relationship-selection failure reflects a mismatch of geometric scale. A prospectively fixed local set can be represented through separate internal pair distances, x/y spans, polygon area, component ordering, local-centroid translation, and member coordinates relative to that local centroid. These descriptors separate **translation of a local configuration** from **deformation within it** and preserve contraction, expansion, anisotropic change, rotation/reordering, and heterogeneous deformation as different observations.

The result is **B — partially supported**. Local-configuration deformation is a more defensible descriptive primitive than local compression, but it does not rescue the earlier compression claim. In the 1230.12s primary start trio (Away19/22/17), x/y spans are almost unchanged, area increases, and pair changes are mixed. The 15m neighborhood contracts modestly in span and hull area but still contains mixed pair directions; the anchor trio expands in x and area while contracting in y. The visually compelling Away19/20/21 convergence is not reproduced by the prospective primary membership. At 3682.88s, large local translation coexists with mixed deformation rather than clean compression. At 4197.04s, the primary trio shows area loss and partial contraction while the larger neighborhood changes anisotropically with mixed pairs, demonstrating that deformation alone can also make a negative case look compression-like.

“Local compression” should therefore be weakened to a possible subtype of **local configuration deformation**, meaning contraction in specified dimensions or relationships. Configuration deformation is not automatically meaningful defensive reconfiguration: membership remains context-sensitive, area can hide anisotropy, ordering can change through small crossings, and ordinary continuous or collective play can deform local sets. The current motif vocabulary is consequently scale-aware but less categorical: coordinated translation is collective-scale, focal excursion is focal-relative, and local deformation is a configuration-scale descriptive family. None is a detected state, score, cause, or attacker attribution.

### Phase 2G cross-scale geometric correspondence

Phase 2G aligns five preserved views within each fixed sequence: collective translation, focal leave-one-out collective-relative movement, prospectively fixed local-configuration deformation, start-fixed nearest-opponent geometry as context, and ball-relative geometry. **Cross-scale correspondence** means only visible co-occurrence or disagreement among these typed scales. It does not mean causal propagation, responsibility transfer, a reallocation magnitude, or an inferred state.

The result is **B — partially supported**. Collective-dominant movement at 1888–1896s remains distinguishable from focal-dominant movement at 590–598s without thresholds. At 1230.12s, small team-centroid movement, substantial focal deviation, mixed prospective local deformation, changing opponent geometry, and substantial ball-relative motion support only a weak/provisional multi-scale description; the prospective representation does not restore the original compression coherence. The 3682.88s case is only partly local-within-collective because large translation coexists with expanding spans/area and mixed pair changes. The 1232.28s start trio expands while its anchor trio contracts strongly, so an appealing cross-scale sequence depends on reference time and is not robust. The tackle and 4197.04s cases remain unresolved/heterogeneous.

Cross-scale correspondence adds information primarily by making **disagreement among scales** auditable. It does not yet operationalize defensive relational reallocation or show ordered spread across scales. Ball motion and shared collective movement remain major alternative explanations, and prospective membership weakens several apparently compelling cases. A future “asking questions” hypothesis may test whether attacking actions are consequential when defensive geometry changes across multiple scales, but no observed correspondence is attributed to a specific attacker here.

### Phase 2H construct synthesis

The broad definition—any change in a typed relationship—is rejected because ordinary active football satisfies it. A mandatory cross-scale definition is also rejected: generic activity and shared ball/collective movement can affect many scales, while the supported 590 focal departure does not require robust local change.

The narrowest surviving candidate is: **Defensive relational reconfiguration is a coherent, temporally localized change in prospectively specified typed defensive geometric relationships that is not adequately described by the relevant pre-specified baseline motion alone.** This is conceptual, not operational. “Coherent,” “localized,” and “adequately described” require prospective matched-contrast validation and must not hide post-hoc references or thresholds.

Terminology decision **B**: retain **defensive relational reallocation** provisionally as historical/theoretical shorthand, but prefer **relational reconfiguration** in empirical sections. “Reallocation” risks cognitive, responsibility-transfer, and zero-sum implications that tracking cannot support. Reference dependence is legitimate only when references are pre-specified and justified; post-hoc reference selection remains unacceptable. Reconfiguration may occur within one scale or across scales.

### Phase 3A prospective validation design

Phase 3A freezes an internal matched-contrast protocol without inspecting outcomes. Completed open-play receptions are metric-independent primary anchors; matched ordinary open-play pseudo-anchors are controls. All references, typed outputs, matching rules, statistics, negative controls, leakage checks, and A/B/C interpretations are fixed in `config/phase3a_validation_protocol.json`. The target is internal geometric discrimination beyond generic movement, not tactical truth or attacker value.

Protocol version 1.1 retains the v1.0 outcome-blind commitments—deterministic overlap suppression, symmetric ball-nearest focal selection, fixed identity conventions, strict missingness, explicit resampling, a matching-support failure rule, and a seeded shifted-anchor negative control—while removing only the pre-execution challenge sensitivity whose event semantics were ambiguous. These are design commitments rather than findings.

### Phase 3B prospective matched-contrast result

Phase 3B executes the pre-outcome-amended protocol v1.1, which differs from v1.0 only by removing the semantically ambiguous tackle/challenge sensitivity. The primary reception design is poorly supported: 46 of 315 retained candidates match (14.6%), below the frozen 70% requirement. The rules were not loosened.

Reception windows have longer collective-centroid paths, focal leave-one-out-relative paths, nearest-opponent distance changes, and generic defending-player path length than matched controls. These are not specific evidence of relational reconfiguration. The seeded within-possession shifted-anchor comparison reproduces or exceeds the same broad movement pattern, and the pre-anchor movement-matching sensitivity retains only 15 pairs and removes those contrasts. Eight-second and possession-change results likewise emphasize collective/focal movement, ball motion, and generic activity rather than stable local-configuration or opponent-specific changes.

The frozen conclusion is **C**. The Phase 2H construct remains conceptually coherent enough to specify typed measurements prospectively, but this design does not show that reception-anchored changes are inadequately described by baseline movement. “Coherent” and “temporally localized” are not validated as discriminating empirical properties here; prospective typing is supported procedurally, not substantively. Relational reconfiguration therefore remains an unvalidated descriptive idea rather than an event, state, score, or causal mechanism.

Phase 3C does not redefine or rescue that construct. It recommends additional matches followed by preregistration of one narrower, independently meaningful geometric primitive. Event records may supply time and context, but receptions or possession changes are not validated positive conditions for reconfiguration. Any future test must condition prospectively on passage-level activity and demonstrate adequate support before relational outcomes are inspected.

Phase 4A selects **focal departure from collective defensive motion** as that narrower primitive: $\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t)$. It is continuous reference-relative geometry, not a state or interpretation. Focal-relative path length is the proposed primary magnitude because accumulated relative motion can cancel at endpoints, but it may still be only focal activity after translation subtraction. Development Game 1 and held-out Game 2 must establish reproducibility and contextual structure before any opponent, reconfiguration, or attacker meaning is considered.

### Phase 4B held-out result and post-validation synthesis

Phase 4B executed the unchanged frozen protocol and supports only this claim: **focal-relative path is a reproducible focal-versus-collective geometric primitive with stable activity-context structure in these two sample matches.** All nine activity cells met the frozen compatibility rule, activity relationships retained direction, common translation cancelled, misaligned similarly active references produced much larger paths, and all frozen window/smoothing sensitivities preserved the qualitative conclusion.

Focal departure remains substantially associated with generic activity; focal absolute-path correlations were 0.541 and 0.462. Phase 4B did not estimate an activity-independent effect or validate defensive response in a tactical sense, relational reconfiguration, pinning, dragging, tracking, covering, handoffs, attacker induction, defensive quality, gravity, or value.

Only after that result was closed did the project adopt defensive response as its broader empirical umbrella and formalize the football/observable/theoretical translation problem. The core inference ladder is:

**physical movement → collective defensive movement → individual/local behavior relative to collective movement → contextual expectation → opponent-information association → tactical defensive-response interpretation → attacker attribution → attacking value**

Phase 4B reaches the individual-relative-to-collective behavior stage. Every later arrow requires new evidence.

### Phase 4C external replication and Phase 5A boundary

Phase 4C extended the same narrow geometric conclusion to seven professional IDSSE matches in one independent tracking dataset/provider environment relative to Metrica. All seven matches met the frozen core criteria, but focal departure remained strongly associated with generic activity. This strengthens the third inference-ladder level; it does not establish contextual expectation or defensive response.

The frozen [Phase 5A protocol](phase5a_contextual_expectation_protocol.md) finds category-A predictive feasibility across seven held-out matches. The [execution](phase5a_contextual_expectation_results.md) shows that focal recent movement contains nearly all useful improvement: collective, ball, and spatial additions are consistent but not materially incremental. Phase 4 externally validated the ladder's individual/local-relative geometry level; Phase 5A supplies feasibility evidence for contextual expectation, not a definitive cross-provider contextual-expectation metric. The residual remains only observed minus predicted geometry. Prediction is not causation, and unexplained movement is not tactical response. Opponent-information association, tactical defensive-response interpretation, attribution, and value remain unvalidated.

Three quantities should remain separate:

1. **Current state:** which behavioral explanation currently fits best?
2. **Transition frequency:** how often does the best-fitting explanation change?
3. **State ambiguity:** how clearly does one explanation dominate alternatives?

Repeated near-ties between Structure and Track may reveal operation near a behavioral boundary even when no clean discrete transition can be defended. The project should not force every frame into a single state, nor prematurely decide whether the best representation is discrete or continuous.

Assignment switch rate does not by itself describe the process around a change: the duration of competing responsibility, teammate compensation, false movements, or subsequent recovery. Likewise, marking entropy across opponents over time is not equivalent to instantaneous ambiguity between behavioral explanations. These distinctions are hypotheses that require operational and construct validation.

## 5. Reference-Frame Principle

The core analytical formulation is:

> Which coordinate system makes the defender look most stationary?

Attacker-centered stability supports an opponent-relative interpretation. Stability in an appropriate structure-centered coordinate system supports a structural interpretation. Closing and recovery involve directed changes in these relationships.

### Phase 1C refinement: decompose opponent-directed movement

Phase 1C requires four quantities to remain conceptually distinct:

1. **Pairwise closure:** whether defender–attacker distance decreases. This describes convergence of the pair but does not identify which player caused it.
2. **Defender absolute approach:** the defender's pitch-frame velocity projected toward the attacker. This separates defender motion from attacker motion.
3. **Collective defensive translation:** the leave-one-out defending-outfield centroid velocity projected in the same opponent direction. This captures movement shared with the defensive block.
4. **Defender opponent-directed deviation from collective movement:** defender velocity minus collective-centroid velocity, projected toward the attacker. A positive value means the defender moves more toward—or less rapidly away from—the attacker than the block does.

A fifth construct must also remain separate: **opponent-movement coupling**, meaning visible correspondence between changes in attacker movement and defender adjustment, especially after collective defensive motion is removed. Coupling concerns coordinated change rather than constant relative position. It is not interchangeable with pairwise closure, absolute defender approach, or opponent-directed residual approach.

The fourth quantity motivates reconsideration of “Close.” Suppose the defender remains stationary or retreats in absolute pitch coordinates while the rest of the defensive block retreats faster. Pairwise distance need not decrease, and defender absolute approach can be zero or negative. Yet the defender's opponent-directed deviation from collective movement can be positive: relative to the block, the defender has prioritized maintaining or strengthening the opponent relationship. Calling this behavior non-Close solely because absolute distance does not shrink would discard the relational defensive action the project is trying to describe.

**Engage** is therefore the provisional working alternative to **Close**. It can encompass literal absolute closing and opponent-directed deviation from collective movement, while avoiding a premature claim that either behavior proves assignment, responsibility, or intent. Whether Engage is the correct final term—and whether it is a state, continuous dimension, or relational constraint—remains unresolved.

This approach starts from observable geometry and then validates a small, stratified collection of clear and ambiguous examples. Human inspection is intended to test face and construct validity, not to create unquestioned tactical ground truth for a classifier.

## 6. Intermediate Observables

Candidate observables should be examined individually before any composite is proposed:

- behavioral state or competing state scores,
- transition frequency and transition direction,
- ambiguity between explanations,
- persistence of engagement or displacement,
- defender and block displacement,
- responsibility handoffs and multi-defender reactions,
- recovery time and recovery distance,
- possible recovery or disruption burden.

One exploratory idea for disruption burden is the time integral of structural displacement until recovery. This is not a finalized metric; it depends on a credible structural expectation and recovery criterion.

## 7. Consequences Are Separate from Response

Defensive adjustment may precede structural disruption, space, progression, or error, but response is not equivalent to value. Defensive positioning may change around an attacker without producing a useful consequence; tracking does not establish attention. Later work may connect defensive response to pitch control, passing options, progression, box entries, shots, xThreat, or EPV, but these outcomes are outside the initial scope.

Likewise, a residual association between a player's movement and unusually large defensive response is not automatically causal.

## 8. Later Applications

### Attacking Probes

A partial or checked movement may be valuable if its credible future possibility induces defensive preparation or a responsibility change. The initial project should seek observable cases without assuming intent.

### Player Gravity

Raw defensive attention confounds player identity with location and situation. A later gravity analysis would compare observed response with expected response in comparable situations. It should distinguish situational gravity from player-associated residual response and should not equate either with attacking value.

### Defensive Positional Economy

A defender who moves less is not necessarily better. Later defensive evaluation could ask which defenders control comparable threats with less corrective adjustment, conditional on the threats faced.

## 9. Competing Hypothesis and Falsification

Frequent state transitions may reflect fluid, successful defensive coordination rather than overload. The analysis must distinguish transition volume from transition execution. Errors may instead be explained by poor positioning, compactness, attacking speed, numerical disadvantage, opponent quality, coordination, fatigue, or other context.

Evidence against the motivating theory would include transitions that are reliably handled without persistent displacement or adverse outcomes, weak reproducibility of the proposed state quantities, poor agreement between geometry and inspected examples, or outcomes explained better by simpler spatial and contextual variables.

## 10. Scope and Methodological Guardrails

The first-paper ambition is deliberately modest. Its primary target is whether tracking data can identify responsibility transitions and periods of ambiguity between collective structure and individual threats in open play. Its secondary target is whether attacking movements, including incomplete and non-receiving movements, systematically precede those transitions. Predicting later defensive instability beyond movement or displacement is optional later work.

Prior work already models man/zonal assignment switches in corner kicks and transient marking relationships in open play. The proposed contribution must therefore be evaluated against those objects rather than described as the first study of defensive adjustment or transitions.

The initial workflow is:

**football understanding → measurable concept → simple calculation → visualization → interpretation → next step**

No method should enter the core pipeline unless its inputs, outputs, purpose, assumptions, failure modes, and validation strategy can be explained. No final decision-load formula, gravity score, player rating, or causal claim is currently endorsed.
