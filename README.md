# Asking Questions

## Defensive State Transitions and Off-Ball Influence in Soccer

**Asking Questions** is a soccer analytics research project about observable changes in defensive behavior during open play. Its primary phenomenon is **defensive state change and decision instability**: moments when a defender's movement becomes more consistent with a different behavioral responsibility, or when several explanations remain similarly plausible.

The motivating soccer theory is that attacking teams can gain control by repeatedly posing credible tactical problems that require defenders to adjust. Tracking data does not reveal a defender's thoughts, instructions, or mental workload. It records behavior. The empirical project therefore studies defensive movement consistent with reconsideration of responsibility, without treating that movement as a direct measure of cognition.

## Working Behavioral Framework

The current hypotheses distinguish four behavioral regimes:

- **Structure:** maintain a relationship to the defensive block or unit.
- **Track:** maintain a comparatively stable relationship to a particular opponent.
- **Close:** actively reduce distance to an immediate threat.
- **Recover:** reduce displacement from an expected structural position after engagement.

A useful shorthand is:

**Structure → Track → Close → Recover → Structure**

This is neither a mandatory sequence nor a set of known tactical instructions. Transitions may skip or reverse, responsibilities may be handed off, and some behavior may remain ambiguous or unexplained.

The core reference-frame question is:

> Which coordinate system makes the defender look most stationary?

Attacker-relative stability may be consistent with tracking. Stability relative to an appropriate defensive structure may be consistent with structural behavior. Closing and recovery concern directional changes in those relationships. What counts as the appropriate structural reference is itself an open research question.

## Analytical Hierarchy

The project keeps the theory, observables, consequences, and applications distinct:

1. **Broader theory:** game control may partly arise from asymmetric tactical decision load.
2. **Proposed mechanism:** credible attacking threats can force defenders to reconsider Structure, Track, Close, and Recover responsibilities.
3. **Intermediate observables:** behavioral state, transition frequency, ambiguity, persistence, displacement, and recovery burden.
4. **Possible consequences:** structural disruption, defensive errors, and space creation.
5. **Later player applications:** attacking probes, off-ball influence, player gravity, and defensive positional economy.

This ordering matters. Space may be a downstream consequence rather than the primary phenomenon, and defensive response is not automatically attacking value.

## Primary Research Question

Can tracking data identify meaningful changes in defensive behavioral responsibility during open play, and can attacking movements be associated with the frequency and ambiguity of those changes?

The first paper is intended to be narrower than the broader theory: establish whether an interpretable open-play behavioral-state framework is measurable and useful before attempting player ratings, causal claims, or a composite decision-load metric.

## Competing Hypothesis

Frequent transitions are not inherently harmful. Strong defenses may exchange and update responsibilities frequently but fluidly. The research must therefore distinguish **high transition frequency** from **poor transition execution** and consider alternative explanations such as positioning, compactness, attacking speed, numerical disadvantage, coordination, opponent quality, and fatigue.

## Research Principles

- Soccer understanding should lead to a measurable concept, simple calculation, visualization, interpretation, and only then a next step.
- Tracking data observes behavior, not cognition or tactical instruction.
- Manually assigned tactical labels will not be treated as unquestioned ground truth.
- Geometry, visualization, descriptive statistics, and interpretable models take priority over complex machine learning.
- No method enters the core pipeline unless its inputs, outputs, purpose, assumptions, failure modes, and validation can be explained.
- Association between attacking movement and defensive response is not automatically causal.
- No final decision-load, gravity, or off-ball-value metric has been defined.

## Current Status

**Stage: conceptual development and literature review.**

No dataset, tactical inference model, or final metric has been selected. When data work begins, Phase 0 will use one public dataset and one match to understand coordinates, timestamps, possession, tracking quality, basic geometry, and short visual sequences before tactical inference is attempted.

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── data/
│   └── .gitkeep
├── docs/
│   ├── conceptual_framework.md
│   ├── literature_review.md
│   ├── research_log.md
│   └── research_questions.md
└── references/
    └── bibliography.md
```

Detailed project thinking lives in [`docs/conceptual_framework.md`](docs/conceptual_framework.md), with questions, hypotheses, literature notes, and dated decisions in the other files under `docs/`.
