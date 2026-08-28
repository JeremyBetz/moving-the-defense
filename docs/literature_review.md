# Literature Review

## Refined Position

The initial novelty check has not eliminated the project, but it has narrowed the candidate contribution. Prior work already models time-varying man/zonal assignments and assignment switches, constructs open-play marking networks, studies what movements activate defenders, and quantifies marking coordination and entropy.

The candidate gap is therefore not defensive adjustment in general. The project initially framed the gap as a continuous **responsibility-resolution** process organized around Structure / Track / Close / Recover. Phase 1 evidence now challenges mutually exclusive states and shifts the provisional question toward continuously multi-relational behavior: whether changes in collective-team, ball-relative, opponent-relative, and local relationships can be described beyond assignments, marking networks, centroid translation, or aggregate spatial outcomes.

This remains a candidate gap. See [`novelty_risk_memo.md`](novelty_risk_memo.md) for claims at risk and reframing conditions.

## Closest Prior Art

### Groom et al. — Defensive Role and Assignment HMM

Groom et al. (2026) introduce a covariate-dependent Hidden Markov Model for corner kicks. The label-free model infers per-frame man-marking assignments and team- and delivery-specific zonal states from tracking data. Its transition model includes persistence in the same assignment, switches between attackers, and zonal-to-man switches; reported player summaries include switch rate.

This is the closest methodological neighbor and a major novelty constraint. It establishes that latent, time-resolved man/zonal responsibility and assignment transitions have already been modeled without manual assignment labels.

The remaining setting difference is substantial but not automatically novel. Corner kicks use constrained sequences and stationary learned zones. Open play has a moving block and ball, responsibility release, return toward structure, emerging and disappearing threats, and potentially competing explanations. Groom et al. report that man-to-zone transitions are not permitted in their model, making recovery/release a particularly relevant comparison. The project must not merely present their corner framework in open play.

### Calero-Sanz et al. — Marking Networks, Coordination, and Entropy

Calero-Sanz et al. (2026) construct dynamic bipartite marking networks from tracking data in 99 matches from the 2019/20 Spanish first division. Marking edges use spatial proximity and directional alignment. One-mode projections represent temporal coordination between teammates and similarity in target allocation. Entropy measures how evenly a player distributes marking effort among opponents.

This is the closest open-play neighbor. It establishes that transient marking relationships, coordinated defender activation, target transfers, marking load, and diversity of marking effort are already measurable research objects. The project cannot broadly claim to originate the question of what an off-ball movement forces defenders to do.

The publisher metadata and abstract do not establish instantaneous ambiguity between structural and opponent-relative explanations, transition execution quality, explicit return to structure, or recovery burden as primary objects. Those apparent differences require full-text verification.

## Critical Conceptual Comparisons

### Assignment Switch Rate Is Not the Full Transition Process

An inferred change from attacker A to attacker B records endpoints. The proposed construct also asks whether the path contains a period of competing responsibility, how long it lasts, whether teammates compensate, and whether the defender subsequently restores a structural relationship. This is a proposed distinction to validate, not evidence that switch rate is deficient.

### Marking Entropy Is Not Instantaneous Responsibility Ambiguity

Marking entropy describes how evenly marking effort is distributed across opponents over an aggregation period. Proposed responsibility ambiguity asks how similarly plausible competing behavioral explanations are at a moment. A defender may mark many opponents through clean transitions, or repeatedly hesitate near a boundary involving only two alternatives.

### Transition Count Is Not Transition Execution

Frequent switches may be normal and well coordinated. Transition ambiguity, persistence, teammate compensation, and recovery cost must remain distinct from frequency.

### Displacement Is Not Responsibility Revision

One clear tracking decision can create large displacement. Repeated small probes can induce several revisions without dramatic movement. The empirical question is whether responsibility-oriented quantities add information beyond basic spatial measures.

## Literature Comparison Matrix

“Unclear” means the currently verified source record does not establish the claim; it does not mean the work omits it.

| Work | Data setting | Open play? | Primary object | Dynamic assignments? | Transitions modeled? | Ambiguity modeled? | Structural recovery? | Attacker-induced response? | Primary outcome | Overlap with this project | Remaining difference |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| Groom et al. (2026) | Premier League corner-kick tracking; 2023/24 season | No | Latent man-marking and zonal assignments; role-conditioned defensive evaluation | Yes, per frame | Yes: persistence, attacker switches, zonal-to-man switches; man-to-zone disallowed | State probabilities exist, but equivalence to proposed ambiguity is unclear | No explicit return-to-moving-structure process verified | Yes, through assignment and downstream coverage/reception analysis | Assignments, switch behavior, role-conditioned defensive credit | Label-free responsibility inference, man/zonal competition, transitions | Open-play moving references; responsibility release; Recover; proposed instantaneous ambiguity and execution process |
| Calero-Sanz et al. (2026) | Tracking from 99 matches, 2019/20 Spanish first division | Yes | Dynamic marking networks, coordination, target similarity, marking entropy | Dynamic marking relationships; “assignment” terminology requires care | Responsibility transfer is discussed; explicit transition-state model unclear | No equivalent instantaneous construct verified | Unclear / requires full-text verification | Yes: marking load and defenders activated by attackers | Marking load, coordination, similarity, entropy | Open-play transient relationships, multi-defender coordination, target diversity | Competition with collective structure, instantaneous ambiguity, execution and recovery require verification |
| Space generation / pitch-control literature | Tracking or event/tracking, source-dependent | Often | Spatial control and space created | Not necessarily | Not necessarily | Generally not the primary object; source-specific | Generally not the primary object; source-specific | Yes | Space or control outcomes | Measures consequences of defender/attacker movement | Responsibility revision before or beyond spatial outcome |
| Off-ball run valuation literature | Source-dependent | Often | Value or consequence of off-ball runs | Not necessarily | Unclear / source-specific | Unclear / source-specific | Unclear / source-specific | Yes | Run or possession value | Non-receiving movement and downstream outcomes | Subtle probes and defensive responsibility process, if measurable |
| Player-gravity literature | Basketball and emerging soccer work | Source-dependent | Defensive attention beyond context | Not necessarily | Unclear / source-specific | Unclear / source-specific | Unclear / source-specific | Yes | Gravity or attention measure | Defender response to attacker presence/movement | Gravity is a later application, not the state-resolution object |
| Defensive influence / EPV / graph approaches | Tracking/event setting varies | Often | Off-ball defensive influence or responsibility | Source-dependent | Unclear / source-specific | Unclear / source-specific | Unclear / source-specific | Sometimes | Defensive value or possession outcome | Tracking-based off-ball defensive evaluation | Whether transition ambiguity/recovery supplies distinct information requires source-level comparison |

## Claims Excluded by Prior Art

The project should not claim to invent:

- man/zonal assignment inference or assignment switches,
- label-free time-resolved defensive-role inference,
- dynamic open-play marking networks,
- asking what an off-ball movement forces defenders to do,
- space creation by dragging defenders,
- valuation of non-receiving runs,
- player gravity,
- tracking-based off-ball defensive evaluation.

## Evidence Needed Before a Novelty Claim

- Full-text comparison of definitions, temporal resolution, uncertainty, transitions, and validation in both closest works.
- A broader search for open-play responsibility, change-point, handoff, recovery, and ambiguity formulations.
- Source-level verification of the neighboring categories in the matrix.
- Evidence that proposed ambiguity is distinguishable from observation noise and generic model uncertainty.
- Evidence that state-transition quantities add meaning beyond proximity, displacement, and marking-network measures.
- Evidence that relational balance, reallocation, accommodation, or recovery add meaning beyond proximity, displacement, centroid translation, aggregate compactness, and marking-network measures.
- A precise statement of whether any contribution is conceptual, measurement-based, empirical, or methodological.

## Source Review Template

For every source, record the soccer question and setting; data and measured inputs; method and assumptions; output and non-measured interpretations; uncertainty and validation; failure modes; descriptive, predictive, or causal claim type; and the exact overlap, difference, or challenge for this project.
