# Conceptual Framework

## 1. Project Focus

The historical framing emphasized **defensive state change and decision instability**, not space creation alone. The current working hypothesis is more relational: open-play defensive behavior is continuously multi-relational and may not be well represented by mutually exclusive Structure / Track / Close / Recover states.

The refined main phenomenon is **sharp changes in the relative explanatory strength of competing observable relationships**—including collective-team, ball-relative, and opponent-relative movement. This is a conceptual refinement, not a finalized model or operational definition.

The project asks whether open-play tracking data can describe a defender's movement as an allocation between competing behavioral responsibilities, and whether attacking movement is associated with changes in that allocation. A movement may matter even when the attacker never receives the ball, completes a run, or creates immediate space if it credibly tests a defensive responsibility boundary.

This is a behavioral framework. Tracking data observes player locations and movement; it does not observe cognition, communication, tactical instructions, or what a defender “believes.” Terms such as responsibility and decision instability are interpretations of observable behavior and must be written with that limitation intact.

**Defensive relational reallocation** is provisional language for a substantial change in which observable relationships best explain a defender's movement. It refers only to behavioral geometry. It must not be interpreted as cognition, intention, tactical instruction, or literal psychological allocation.

## 2. Broader Theory: Asking Questions

Soccer can be viewed partly as a competition over which team determines the problems both teams must solve. Positioning, rotations, runs, and threatened actions can pose tactical questions. Physical and technical qualities can make a threat more credible or cheaper for the attacker to pose.

The broader hypothesis is that a team may gain control by imposing repeated defensive recognition and adjustment while its own movements remain comparatively simple or rehearsed. This is a theory about **asymmetric tactical decision load**, not a claim that tracking data measures mental bandwidth.

A cautious conceptual chain is:

**Attacking position or movement → credible tactical threat → possible reconsideration of defensive responsibility → observable behavioral state change or ambiguity → structural adjustment and recovery → possible error, space, or progression**

Every arrow is a proposition to investigate, not an established causal link.

## 3. Four Hypothesized Behavioral Regimes

### Structure

The defender's behavior is better explained by maintaining a relationship to collective defensive organization than to one particular opponent.

Candidate structural references include a whole-team centroid, local teammate neighborhood, defensive line, unit- or role-specific centroid, ball-relative block position, or a combination. The correct reference may differ by role and phase and remains a research question.

### Track

The defender maintains a comparatively stable attacker-relative position. For defender \(d\) and attacker \(a\):

\[
\mathbf{r}_{da}(t)=\mathbf{x}_a(t)-\mathbf{x}_d(t)
\]

Low variation in this relative position over an appropriate window is evidence consistent with tracking. It is more informative than velocity similarity alone, but it does not reveal a formal marking instruction.

### Close

The defender actively changes a relationship by approaching an attacker or the ball. If attacker distance is

\[
r_{da}(t)=\lVert\mathbf{x}_a(t)-\mathbf{x}_d(t)\rVert,
\]

then sustained \(dr_{da}/dt<0\), supported by defender velocity projected toward the threat, is evidence consistent with closing. Tracking maintains a relationship; closing reduces it.

This is the historical Phase 0/1 formulation. Phase 1C evidence now makes **Engage** a provisional replacement term for **Close**, but that terminology is not finalized and is not being applied globally yet. The reason is conceptual, not cosmetic: literal reduction of absolute defender–attacker distance is only one way a defender can strengthen or prioritize an opponent relationship.

### Recover

The defender is displaced and moves toward an expected structural position. If \(\hat{\mathbf{x}}_{structure}(t)\) is a defensible estimate of that position, recovery is consistent with decreasing

\[
\lVert\mathbf{x}_d(t)-\hat{\mathbf{x}}_{structure}(t)\rVert.
\]

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

Defensive adjustment may precede structural disruption, space, progression, or error, but response is not equivalent to value. An attacker can attract attention without producing a useful consequence. Later work may connect defensive response to pitch control, passing options, progression, box entries, shots, xThreat, or EPV, but these outcomes are outside the initial scope.

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

**soccer understanding → measurable concept → simple calculation → visualization → interpretation → next step**

No method should enter the core pipeline unless its inputs, outputs, purpose, assumptions, failure modes, and validation strategy can be explained. No final decision-load formula, gravity score, player rating, or causal claim is currently endorsed.
