# Conceptual Framework

## 1. Project Focus

The primary phenomenon is **defensive state change and decision instability**, not space creation alone.

The project asks whether open-play tracking data can describe a defender's movement as an allocation between competing behavioral responsibilities, and whether attacking movement is associated with changes in that allocation. A movement may matter even when the attacker never receives the ball, completes a run, or creates immediate space if it credibly tests a defensive responsibility boundary.

This is a behavioral framework. Tracking data observes player locations and movement; it does not observe cognition, communication, tactical instructions, or what a defender “believes.” Terms such as responsibility and decision instability are interpretations of observable behavior and must be written with that limitation intact.

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

### Recover

The defender is displaced and moves toward an expected structural position. If \(\hat{\mathbf{x}}_{structure}(t)\) is a defensible estimate of that position, recovery is consistent with decreasing

\[
\lVert\mathbf{x}_d(t)-\hat{\mathbf{x}}_{structure}(t)\rVert.
\]

Structure and Recover are distinct: one maintains an existing structural relationship; the other repairs displacement. The expected structural position must be justified rather than assumed.

## 4. States, Transitions, and Ambiguity

The shorthand cycle **Structure → Track → Close → Recover → Structure** is not mandatory. States may be skipped or reversed, a defender may hand responsibility to a teammate, and some movement may be ambiguous or unexplained.

Three quantities should remain separate:

1. **Current state:** which behavioral explanation currently fits best?
2. **Transition frequency:** how often does the best-fitting explanation change?
3. **State ambiguity:** how clearly does one explanation dominate alternatives?

Repeated near-ties between Structure and Track may reveal operation near a behavioral boundary even when no clean discrete transition can be defended. The project should not force every frame into a single state, nor prematurely decide whether the best representation is discrete or continuous.

## 5. Reference-Frame Principle

The core analytical formulation is:

> Which coordinate system makes the defender look most stationary?

Attacker-centered stability supports an opponent-relative interpretation. Stability in an appropriate structure-centered coordinate system supports a structural interpretation. Closing and recovery involve directed changes in these relationships.

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

The first-paper ambition is deliberately modest: determine whether tracking data can identify shifts between collective structural and individual opponent responsibility in open play, and identify which attacking movements are associated with those shifts.

The initial workflow is:

**soccer understanding → measurable concept → simple calculation → visualization → interpretation → next step**

No method should enter the core pipeline unless its inputs, outputs, purpose, assumptions, failure modes, and validation strategy can be explained. No final decision-load formula, gravity score, player rating, or causal claim is currently endorsed.
