# Literature Review

## Purpose

This review will establish what is already known about tracking-based defensive behavior and where an open-play state-transition framework may add something. It should prevent novelty claims based merely on measuring off-ball runs, defenders being dragged, space creation, marking relationships, or player gravity.

The candidate gap is narrower:

> Existing work has studied several neighboring phenomena separately. This project asks whether open-play defensive behavior can be represented as a dynamic allocation between competing behavioral responsibilities, and whether attacking movement is associated with the frequency, ambiguity, persistence, and consequences of changes in that allocation.

This is a candidate gap, not a confirmed novelty claim. It must be tested through a systematic review of the closest work.

## Neighboring Research Areas

### Man/Zonal Assignment Inference

Unsupervised and Hidden Markov Model approaches have been used to infer man-marking and zonal assignments, particularly for corner kicks. This is a close methodological cousin because it treats defensive responsibility as latent and time-varying.

The important comparison is whether methods developed for highly structured restarts transfer conceptually or empirically to dynamic open play. The existence of these methods also means this project should not claim to invent assignment inference. An HMM is not currently selected for this project.

### Dynamic Marking Networks

Tracking studies have constructed transient defender-attacker marking relationships using proximity, direction, and related features. This supports representing defensive relationships as dynamic networks.

The review should ask whether those methods model changes between collective structural responsibility, opponent responsibility, engagement, and recovery—or primarily identify marking edges.

### Space Generation and Pitch Control

Pitch-control and space-generation research measures spatial control and how movement changes available space. Prior work explicitly recognizes that attackers can create space by moving defenders.

This project's proposed distinction is not “off-ball movement creates space.” It is that a movement may change or destabilize the defensive behavioral solution before clear space is created. Space is a possible downstream consequence and an eventual validation target.

### Off-Ball Run Valuation and Decoy Runs

Existing work values off-ball runs, including runs without a reception, and examines decoy movements. Therefore, “event data misses useful off-ball action” is not a sufficient novelty claim.

Relevant questions are how these studies define the start and end of a run, attribute affected defenders, handle incomplete probes, and connect movement to later value.

### Player Gravity

Player-gravity ideas are established in basketball and emerging in soccer. Raw defensive response is confounded by location and situation, so later player comparisons would need to distinguish situational gravity from player-associated residual response.

Gravity remains an application rather than the primary construct, and neither attention nor residual response is automatically value or causal influence.

### Defensive Structure and Team Shape

Work on centroids, compactness, defensive lines, formations, local organization, and role-relative position is directly relevant to defining Structure and Recover. The key review question is which structural reference is appropriate for an individual defender in open play and how that choice is validated.

### Change Points, Ambiguity, and Responsibility Handoffs

The review should search beyond soccer-specific state names for interpretable methods that represent changing explanations, uncertainty between states, persistence, and handoffs. A method's availability does not justify its use: any candidate must have soccer-interpretable inputs, outputs, assumptions, failure modes, and validation.

## Review Questions for Every Source

For each work, record:

1. What soccer question is asked?
2. What tracking and event data are used, at what frequency and quality?
3. What observable inputs enter the method?
4. What output is estimated, and what does it not measure?
5. What assumptions connect the geometry to the tactical interpretation?
6. How are assignments, states, relationships, or outcomes validated?
7. How are uncertainty, ambiguity, and missing tracking handled?
8. Is the setting open play, a restart, or another constrained phase?
9. Are claims descriptive, predictive, or causal?
10. Which part of this project's framework is informed, contradicted, or left open?

## Evidence Needed Before a Novelty Claim

- A documented search across the neighboring areas above.
- Direct comparison with the closest open-play and assignment-inference papers.
- Confirmation that prior work does not already operationalize the same Structure/Track/Close/Recover competition and transition ambiguity.
- A clear statement of whether the contribution is conceptual, measurement-based, empirical, or methodological.
- Negative and conflicting findings, not only supportive examples.

## Working Source Template

### Citation

Full citation and link; add the canonical entry to `references/bibliography.md`.

### Research Question and Setting

State the soccer problem and whether the data concern open play, set pieces, or another constrained situation.

### Data and Observables

Record provider, sample, tracking frequency, coordinates, events, quality limitations, and the exact measured inputs.

### Method, Assumptions, and Output

Explain first in soccer terms and then mathematically. Separate the estimated quantity from tactical or cognitive interpretation.

### Validation and Failure Modes

Record the validation target, uncertainty treatment, plausible confounders, and known failure cases.

### Relevance, Difference, and Challenge

State which project question the source informs, what remains different, and whether it challenges the motivating theory or proposed measurement.
