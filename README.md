# Asking Questions

## Quantifying Off-Ball Influence Through Defensive Adjustment

**Asking Questions** is a soccer analytics research project investigating whether off-ball player influence can be quantified through the defensive adjustments that players induce.

Football analysis remains heavily centered on actions involving the ball. Yet attacking players can influence possessions without receiving it: drawing defenders from a block, forcing marking decisions, creating responsibility transfers, inducing pressure, and creating space that must subsequently be recovered.

This project begins from the hypothesis that defensive movement can be understood partly through competing reference frames. A defender may:

1. move with the collective defensive structure,
2. maintain a relationship with an individual opponent,
3. close toward an immediate threat,
4. recover toward the defensive structure after engagement.

The working behavioral framework is:

**Structure → Track → Close → Recover → Structure**

These are hypothesized behavioral regimes, not assumed ground-truth tactical labels.

The project investigates whether these behaviors and transitions can be inferred from player-tracking data, and whether the defensive adjustment induced by attacking movement provides a useful measure of off-ball influence.

## Core Research Questions

1. Can a defender's movement be meaningfully characterized by its relationship to team structure, individual opponents, and immediate threats?
2. Can changes between these relationships be detected from tracking data without requiring manually assigned tactical labels?
3. Do particular attacking movements systematically precede defensive responsibility changes?
4. Do attackers differ in the defensive adjustment they induce after accounting for spatial and tactical context?
5. Does induced defensive adjustment identify off-ball contributions that conventional event data does not capture?

## Broader Motivation

A motivating tactical hypothesis is that football can be viewed partly as a process of creating and resolving problems.

Attacking actions may impose defensive work by forcing opponents to change assignments, leave structure, close threats, hand off responsibilities, or recover lost structural positions.

The project does **not** claim that tracking data directly measures cognition or mental workload. Instead, it investigates observable defensive adjustment as a possible consequence of tactical problems imposed by attackers.

A longer-term conceptual chain is:

**Attacking movement → Defensive response → Structural disruption → Recovery burden → Potential attacking value**

## Methodological Principle

> No modeling method should enter the core research pipeline unless its inputs, outputs, assumptions, failure modes, and reason for inclusion can be explained by the researcher.

The project will prioritize interpretable geometry, statistics, and transparent models before considering more complex methods.

## Current Status

**Stage: Conceptual development and literature review**

No tactical inference model has yet been selected.

Immediate priorities:

- formalize the conceptual framework,
- review related academic and industry work,
- identify the specific research gap,
- evaluate available public tracking datasets,
- define measurable quantities before modeling.

## Repository Structure

```text
docs/
    conceptual_framework.md
    research_questions.md
    literature_review.md
    research_log.md

references/
    bibliography.md

notebooks/
    exploratory analysis and visualization

src/
    reusable analysis code

data/
    local data only; excluded from Git

Then create the conceptual framework:

```bash
cat > docs/conceptual_framework.md <<'EOF'
# Conceptual Framework

## 1. Motivation

Football analysis is disproportionately centered on events involving the ball.

Passes, shots, carries, receptions, pressures, and turnovers are observable and relatively easy to record. However, many tactically important actions occur away from the ball and may never appear in conventional event data.

An attacker may create value by:

- drawing a defender away from a preferred structural position,
- forcing a defender to choose between space and an opponent,
- creating a defensive handoff,
- causing multiple defenders to adjust,
- opening space for a teammate,
- forcing a defender to recover after engagement,
- increasing the defensive work required to maintain organization.

The player may never receive the ball.

This project investigates whether player-tracking data can make some of this influence measurable.

---

## 2. Tactical Problems and Defensive Adjustment

The broader motivating hypothesis is that football can be understood partly as a process of creating and resolving tactical problems.

An attacking action may be useful when it creates a problem that is relatively inexpensive for the attacking team to pose but comparatively expensive for the defending team to solve.

The project does not attempt to directly measure cognition or mental bandwidth.

Instead, it studies an observable consequence:

**defensive adjustment induced by attacking behavior.**

---

## 3. Competing Defensive Reference Frames

A defender's movement may be explainable relative to different reference frames.

### Structure

The defender maintains a relatively stable relationship to the collective defensive organization.

Possible structural references may include:

- team centroid,
- local defensive-unit centroid,
- defensive line,
- neighboring defenders,
- role-specific expected location,
- ball-relative defensive structure.

A defender behaving structurally should appear relatively stable in an appropriate team-structure-centered coordinate system.

### Track

The defender maintains a relatively stable relationship with a particular opponent.

A defender tracking an attacker should appear relatively stable in an attacker-centered coordinate system, even when this causes deviation from the broader defensive structure.

### Close

The defender actively reduces distance toward an immediate threat.

This differs from tracking.

Tracking implies maintaining a relationship.

Closing implies changing that relationship by approaching the opponent or ball.

### Recover

After engagement or displacement, the defender moves toward an expected structural position.

A recovering defender may not yet be moving with the block. Instead, the defender is reducing the distance between their current position and the position implied by the defensive structure.

---

## 4. Working Behavioral Cycle

The initial conceptual model is:

**Structure → Track → Close → Recover → Structure**

This is not assumed to be a mandatory or complete sequence.

Possible transitions may include:

- Structure → Track
- Structure → Close
- Track → Close
- Track → Structure
- Close → Recover
- Recover → Structure
- Track → Track with responsibility transfer
- ambiguous or unexplained behavior

The framework should allow uncertainty rather than forcing every observation into a tactical state.

---

## 5. Reference-Frame Interpretation

The core analytical question is:

**Which reference frame best explains a defender's observed movement at a given time?**

For example:

- similarity to team movement may indicate structural behavior,
- stability relative to an attacker may indicate tracking,
- decreasing distance toward an opponent may indicate closing,
- decreasing displacement from expected structural location may indicate recovery.

This framing may allow tactical states to be inferred from observable geometry rather than manually imposed labels.

---

## 6. Defensive Disruption and Recovery Burden

An attacking movement may create value not only through immediate defensive displacement but also through the effort required to restore defensive structure.

Possible observable consequences include:

- defender displacement from expected structure,
- duration of displacement,
- responsibility changes,
- multiple-defender reactions,
- changes in defensive spacing,
- defensive line distortion,
- recovery distance,
- recovery time.

One possible future concept is **recovery burden** or **disruption burden**: the amount and duration of structural correction required after an attacking action.

This concept is exploratory and has not yet been formally defined.

---

## 7. Attacking Gravity

A longer-term goal is to evaluate whether attackers differ in how strongly they induce defensive adjustment.

Raw defensive attention is not sufficient because dangerous locations naturally attract defenders.

A useful player-level gravity concept would therefore require adjustment for context such as:

- player location,
- ball location,
- movement type,
- possession phase,
- defensive shape,
- nearby teammates,
- nearby opponents,
- game state.

The eventual question is:

**Does a particular player induce more defensive adjustment than would normally be expected from an attacker behaving similarly in the same context?**

---

## 8. Off-Ball Movement Value

Defensive adjustment is not necessarily equivalent to attacking value.

An attacker may attract defenders without creating useful consequences.

A longer-term framework may therefore examine:

**Attacking movement → Defensive adjustment → Spatial consequence → Possession consequence**

Potential downstream outcomes include:

- newly available space,
- passing-lane creation,
- increased teammate accessibility,
- improved pitch control,
- progression,
- box entry,
- shot creation,
- increased possession value.

This stage is explicitly outside the initial scope.

---

## 9. Defensive Positional Economy

The same framework may eventually support defensive evaluation.

A defender who makes large corrective movements is not necessarily better than one who solves the same threats from an already advantageous position.

A longer-term defensive question is:

**How effectively does a defender control attacking threats while minimizing unnecessary structural adjustment?**

This concept is exploratory and should not be treated as a finalized metric.

---

## 10. Interpretability Constraint

No model should enter the core research pipeline unless its:

- inputs,
- outputs,
- assumptions,
- tactical interpretation,
- failure modes,
- validation strategy

can be clearly explained.

The soccer concept should drive the methodology, not the reverse.
