# Research Questions

## Primary Research Question

Can player-tracking data be used to infer changes in defensive responsibility and quantify the defensive adjustment induced by off-ball attacking movement?

## Initial Questions

### RQ1 — Defensive Reference Frames

Can a defender's movement be meaningfully decomposed according to competing reference frames such as:

- collective defensive structure,
- individual opponent,
- immediate threat,
- expected structural recovery location?

### RQ2 — Behavioral Transitions

Can transitions between structural, opponent-relative, closing, and recovery behavior be detected from tracking data without requiring manually assigned tactical labels as the primary modeling target?

### RQ3 — Attacking Triggers

Which attacking movements systematically precede changes in defensive behavior?

### RQ4 — Defensive Adjustment

Can the magnitude and duration of defensive adjustment following an attacking movement be quantified?

### RQ5 — Player Gravity

After accounting for spatial and tactical context, do attackers differ systematically in the defensive adjustment they induce?

### RQ6 — Off-Ball Contribution

Can induced defensive adjustment identify attacking contributions that are invisible in conventional event data, including movements by players who never receive the ball?

### RQ7 — Defensive Positional Economy

Can defenders be evaluated by how effectively they maintain or restore defensive structure in response to attacking problems?

---

# Initial Hypotheses

These are provisional and should be revised after the literature review.

## H1

Defensive movement is better explained by multiple tactical reference frames than by team movement alone.

## H2

Periods of opponent-oriented tracking will show greater stability in attacker-relative position than in team-structure-relative position.

## H3

Closing behavior will be distinguishable from tracking by sustained reduction in defender-threat distance.

## H4

Recovery behavior will be characterized by reduction in displacement from an expected structural position after an engagement or tracking episode.

## H5

Some off-ball attacking movements will induce defensive adjustment disproportionate to the attacking movement itself.

## H6

Attackers will differ in induced defensive adjustment even after controlling for basic spatial context.

---

# Open Questions

- What is the appropriate definition of defensive structure?
- Should structure be global, local, role-specific, or learned?
- What temporal window is appropriate for velocity and movement comparison?
- Should tactical behavior be represented as discrete states or continuous weights?
- Can multiple states coexist?
- How should uncertainty be represented?
- How should possession transitions be treated?
- How should pressing and emergency recovery runs be distinguished?
- How should defensive handoffs be represented?
- What minimum tracking quality is required?
