# Asking Questions

## Multi-Relational Defensive Behavior and Off-Ball Influence in Soccer

**Asking Questions** is a soccer analytics research project about observable changes in defensive behavior during open play. It began with defensive state transitions and decision instability. Phase 1 evidence increasingly challenges a mutually exclusive state interpretation; the current working view is that defending is continuously multi-relational.

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

Current Phase 1 evidence places this state-machine interpretation under explicit reconsideration. The working hypothesis is that defensive behavior is continuously multi-relational, with collective-team, ball-relative, and opponent-relative relationships potentially operating at the same time. The refined phenomenon of interest is **sharp changes in the relative explanatory strength of competing observable relationships**. **Defensive relational reallocation** is provisional language for such behavioral/geometric change; it does not imply cognition, intention, instruction, or literal psychological allocation. No relational weights or composite score have been defined.

These relationships are not assumed to be zero-sum. A defender may increase opponent engagement while collective coherence remains high or also increases. **Collective accommodation** is provisional language for teammate movement consistent with absorbing or supporting an individual engagement; it is a hypothesis, not an accommodation score, causal claim, or conclusion about team quality.

The original core reference-frame question was:

> Which coordinate system makes the defender look most stationary?

Attacker-relative stability may be consistent with tracking. Stability relative to an appropriate defensive structure may be consistent with structural behavior. Closing and recovery concern directional changes in those relationships. What counts as the appropriate structural reference is itself an open research question.

Phase 1F shows why no single answer is likely sufficient: substantial local and opponent-relative reorganization can occur with little whole-team centroid movement. Centroid and whole-block translation remain useful baselines, but defensive structure increasingly appears to require a relational representation spanning team, ball, opponents, nearby teammates, goal, and space.

## Analytical Hierarchy

The project keeps the theory, observables, consequences, and applications distinct:

1. **Broader theory:** game control may partly arise from asymmetric tactical decision load.
2. **Proposed mechanism:** credible attacking threats can force defenders to reconsider Structure, Track, Close, and Recover responsibilities.
3. **Intermediate observables:** behavioral state, transition frequency, ambiguity, persistence, displacement, and recovery burden.
4. **Possible consequences:** structural disruption, defensive errors, and space creation.
5. **Later player applications:** attacking probes, off-ball influence, player gravity, and defensive positional economy.

This ordering matters. Space may be a downstream consequence rather than the primary phenomenon, and defensive response is not automatically attacking value.

## Primary Research Question

Can open-play tracking identify sharp changes in the relative explanatory strength or configuration of competing observable defensive relationships without forcing them into mutually exclusive tactical states?

A secondary question is whether attacking movements—including movements that never become completed runs or receptions—systematically precede those transitions. Testing whether accumulated transition or ambiguity burden predicts later instability beyond simple movement or displacement is optional later work, not required for the first empirical contribution.

Closest prior work already infers time-varying man/zonal assignments and switches during corner kicks and constructs dynamic marking networks in open play. The candidate contribution is therefore narrower: whether open-play relational balance, ambiguity, reallocation, accommodation, and recovery can be described transparently beyond assignment or marking-network summaries. This is not yet a confirmed novelty claim or finalized model.

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

**Stage: relational representation requirements following early construct diagnostics.**

Metrica Sports Sample Game 1 is the sole empirical sample so far. Phase 0 documented the dataset representation; Phases 1A–1F performed narrowly scoped construct diagnostics spanning structural translation, opponent-relative position, event-anchored convergence, kinematic decomposition, movement coupling, collective accommodation, and local compression. Phase 2A compares what separate relational views preserve or lose across those fixed cases. No tactical inference model, state system, composite representation, relational weighting scheme, or final metric has been selected.

## What We Have Learned So Far

| Phase | Question | Main finding | Consequence |
|---|---|---|---|
| 0 | What does one Metrica match actually contain? | Tracking/events align at 25 Hz; identifiers, missingness, coordinates, and halftime orientation are documented. | Reproducible raw-data understanding precedes tactical inference. |
| 1A | Can a leave-one-out team centroid remove collective translation? | Often yes, but it fails under deformation and split shapes. | Centroid is a useful baseline, not a structural representation. |
| 1B | Do clear Track/Close examples validate simple primitives? | Fixed attacker-relative Cartesian position was not sufficient for visually Track-like behavior; geometric closure was clearer. | Preserve components and challenge constructs with positive controls. |
| 1C | Can events enrich Close candidates, and who produces convergence? | Tackles are precise but sparse; receptions are broad and noisy. Closure can come from defender, attacker, or collective movement. | Separate pairwise closure, absolute approach, collective translation, and residual approach. |
| 1D | Is following better seen as movement coupling? | Coupling was difficult to isolate cleanly after removing collective motion; one example was only partially supportive. | Fixed relative position and movement coupling capture different, incomplete aspects. |
| 1E | Do teammates accommodate individual engagement? | Accommodation-consistent movement was heterogeneous across fixed cases. | Engagement and collective coherence may coexist; relational strengths need not be zero-sum. |
| 1F | Can local reorganization occur with a stable centroid? | Yes: the 1230.12 s counterexample shows substantial local compression and relationship changes with little centroid movement. | Stable centroid does not imply stable defensive relationships; structure likely needs relational representation. |
| 2A | What minimum information must a relational representation preserve? | No single tested view suffices: centroid, defender–defender, defender–opponent, and ball-relative views preserve different necessary context. | Retain a sparse set of typed relations separately before proposing any composite representation. |

Negative and ambiguous results are research findings, not implementation failures. They delimit what a future representation must be capable of seeing.

## Minimal Notation

For defender (d), attacker (a), and leave-one-out defensive centroid (c):

- Relative position: \(\mathbf r_{da}(t)=\mathbf x_a(t)-\mathbf x_d(t)\); pairwise distance: \(D_{da}(t)=\lVert\mathbf r_{da}(t)\rVert\).
- Pairwise closure rate: \(-dD_{da}/dt\). This does not identify which player caused convergence.
- Defender absolute approach: \(A_d=\mathbf v_d\cdot\mathbf u_{da}\), where \(\mathbf u_{da}=\mathbf r_{da}/D_{da}\).
- Collective translation: centroid velocity \(\mathbf v_c\), or its opponent-directed component \(\mathbf v_c\cdot\mathbf u_{da}\).
- Opponent-directed residual movement: \((\mathbf v_d-\mathbf v_c)\cdot\mathbf u_{da}\).
- Relational configuration and **defensive relational reallocation** remain conceptual descriptions of which observable relationships explain movement and how sharply that configuration changes. No numerical relational weights or reallocation formula exist yet.

## Future Applications — Not Yet Implemented

### Defensive style

Individual defenders and teams may differ systematically in how observable movement responds to different “sources of gravity” or relational constraints: collective organization, ball, opponents, nearby teammates, goal, and space. This is a future hypothesis, not a team-quality result from Sample Game 1.

### Attacking gravity above expectation

A later application may evaluate how much defensive response or relational reallocation an attacker induces beyond what the context would ordinarily predict:

\[
\text{attacking gravity above expectation}
=\text{observed defensive response}
-\text{expected defensive response given context}.
\]

This is conceptual notation, not an existing or validated metric. Future work may distinguish response magnitude, reallocation cost, persistence or recovery burden, and interaction with defensive team style.

## Executed Notebooks

### Phase 0 notebook

The executed [`notebooks/phase0_metrica_sample_game_1.ipynb`](notebooks/phase0_metrica_sample_game_1.ipynb) downloads and verifies the three Sample Game 1 CSVs when absent. Local data remain under the gitignored `data/` directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-phase0.txt
jupyter notebook notebooks/phase0_metrica_sample_game_1.ipynb
```

The notebook stops before structural-reference calculations or defensive-state constructs.

### Phase 1A diagnostic

The executed [`notebooks/phase1a_whole_team_centroid_diagnostics.ipynb`](notebooks/phase1a_whole_team_centroid_diagnostics.ipynb) tests only the leave-one-out whole-team defensive centroid for three manually selected eight-second sequences. Pitch-length and pitch-width components remain separate. The notebook ends without defining states, scores, thresholds, ambiguity, or another structural reference.

### Phase 1B extreme-case diagnostic

The executed [`notebooks/phase1b_extreme_case_construct_diagnostics.ipynb`](notebooks/phase1b_extreme_case_construct_diagnostics.ipynb) freezes one visually selected Track-like candidate and one visually selected Close-like candidate before inspecting their diagnostic coordinates. It uses only the existing centroid- and attacker-relative components and retains x/y alongside raw-coordinate distance. These are positive-control candidates, not tactical states or inferred assignments.

### Phase 1C event-anchored Close diagnostics

The executed [`notebooks/phase1c_event_anchored_close_diagnostics.ipynb`](notebooks/phase1c_event_anchored_close_diagnostics.ipynb) uses conservatively paired tackle events and completed-pass receptions to generate candidate windows before inspecting tracking geometry. It reports candidate coverage and endpoint distance changes, then plots fixed event-order samples with raw paths, separate opponent-relative x/y, distance, and the existing team-centroid-relative components. A narrow continuation converts coordinates to 105 × 68 m pitch units and decomposes closure into defender, attacker, collective-centroid, and defender-residual approach using centered 5/7/9-frame rolling-position means. It does not define Close or build a detector.

### Phase 1D opponent-movement coupling diagnostic

The executed [`notebooks/phase1d_opponent_movement_coupling_diagnostics.ipynb`](notebooks/phase1d_opponent_movement_coupling_diagnostics.ipynb) fixes two examples from raw trajectories before velocity inspection. It compares attacker, defender, leave-one-out centroid, and defender-residual x/y velocity alongside attacker-relative x/y position, with the existing 105 × 68 m conversion and 5/7/9-frame smoothing framework. The diagnostic is visual only: it does not calculate correlation, response lags, regressions, similarity scores, assignments, or Track classifications.

### Phase 1E collective-accommodation diagnostic

The executed [`notebooks/phase1e_collective_accommodation_diagnostics.ipynb`](notebooks/phase1e_collective_accommodation_diagnostics.ipynb) reuses three of the 11 fixed Phase 1C tackle candidates: two with descriptively large positive focal residual approach and one collective-translation contrast. Soccer-first trajectories and simple teammate displacement, centroid, local-spacing, and separate x/y spread diagnostics examine whether teammate movement is consistent with accommodating focal engagement. No accommodation score, causal inference, success classification, or team-quality comparison is introduced.

### Phase 1F interior-threat / local-compression diagnostic

The executed [`notebooks/phase1f_interior_threat_local_compression_diagnostics.ipynb`](notebooks/phase1f_interior_threat_local_compression_diagnostics.ipynb) fixes three reception-anchored examples from raw full-team trajectories. Snapshot sequences and separate centroid, threat-distance, defender-pair spacing, relative-depth, other-opponent, and movement-cancellation diagnostics test whether local defensive reorganization can occur while a team centroid remains stable. One case provides a clear counterexample; another combines compression with translation; the third visual candidate does not support coherent multi-defender convergence. No structure or exposure score is introduced.

### Phase 2A relational-representation requirements

The executed [`notebooks/phase2a_relational_representation_requirements.ipynb`](notebooks/phase2a_relational_representation_requirements.ipynb) reuses seven fixed Phase 1 cases to compare separate centroid-relative, defender–defender, defender–opponent, depth, ball-relative, and local-neighborhood views. A before/during/after figure for 1230.12s makes visible why small centroid movement does not imply stable relational geometry. The diagnostic proposes only a provisional minimum information requirement—sparse typed relations with collective and ball context—and does not combine them into a score, network, assignment system, or model.

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── requirements-phase0.txt
├── data/
│   └── .gitkeep
├── docs/
│   ├── conceptual_framework.md
│   ├── literature_review.md
│   ├── novelty_risk_memo.md
│   ├── research_log.md
│   └── research_questions.md
├── notebooks/
│   ├── phase0_metrica_sample_game_1.ipynb
│   ├── phase1a_whole_team_centroid_diagnostics.ipynb
│   ├── phase1b_extreme_case_construct_diagnostics.ipynb
│   ├── phase1c_event_anchored_close_diagnostics.ipynb
│   ├── phase1d_opponent_movement_coupling_diagnostics.ipynb
│   ├── phase1e_collective_accommodation_diagnostics.ipynb
│   └── phase1f_interior_threat_local_compression_diagnostics.ipynb
└── references/
    └── bibliography.md
```

Detailed project thinking lives in [`docs/conceptual_framework.md`](docs/conceptual_framework.md), with questions, hypotheses, literature notes, and dated decisions in the other files under `docs/`.
