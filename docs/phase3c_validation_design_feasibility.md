# Phase 3C Validation-Design Feasibility After Phase 3B

## Purpose and constraint

Phase 3C asks what prospective test, if any, is scientifically justified after the Phase 3B result. It is a design memo, not another empirical analysis. No candidate or control samples are constructed, no new match is loaded, and no Phase 3B rule is loosened or retuned.

The construct remains unchanged:

> Defensive relational reconfiguration is a coherent, temporally localized change in prospectively specified typed defensive geometric relationships that is not adequately described by the relevant pre-specified baseline motion alone.

Its current status is **unvalidated**.

## What Phase 3B established

Phase 3B separated two findings that must not be conflated.

### Design limitation: inadequate prospective control support

The frozen matching design supported only 46 of 315 reception candidates (14.6%), against a pre-specified requirement of 70%. Support fell to 21 of 244 (8.6%) for eight-second windows, 15 of 315 (4.8%) when pre-anchor movement strata were added, and 23 of 136 (16.9%) for possession-change anchors. These results make estimates unstable and restrict the contexts represented by matched pairs. They do not justify loosening calipers after inspecting outcomes.

### Construct counterevidence: apparent effects resemble passage-level activity

Reception windows contained more collective-centroid movement, more focal leave-one-out-relative movement, and much more summed defending-player movement. Local-configuration descriptors were broadly null, and opponent-specific evidence was weak and context-sensitive. Seeded shifted anchors within the same possession reproduced or exceeded the principal apparent effects. The sparse pre-anchor movement-matched sensitivity removed them.

Receptions therefore did not function as validated positive conditions for reconfiguration. They functioned as metric-independent temporal anchors that disproportionately selected active passages. Phase 3B falsified the claim that this reception-based design distinguishes the umbrella construct from ordinary passage-level activity. It did not prove that relational reconfiguration never occurs or that activity explains every relational change.

## The pre-anchor activity result

The pre-anchor sensitivity has two defensible interpretations:

1. Pre-existing ball and defensive movement may explain the reception contrasts.
2. Sample Game 1 may lack enough comparable windows to separate pre-existing activity from reception context.

The 4.8% support prevents choosing between them. A discriminating design needs many more prospectively eligible passages spanning the same pre-anchor activity and context cells, with the activity representation and support criteria frozen before relational outcomes are inspected. Adequate overlap must be demonstrated as a design property, not obtained by successively changing bins or calipers.

## Adversarial assessment of future-design families

### Option A — Redesign matching within Sample Game 1

**Assessment: reject as the next empirical study.**

A new outcome-blind scheme could be written, but it would be designed with detailed knowledge of how this match defeated Phase 3A. One match supplies a sparse control pool, repeated dependent possessions, and limited overlap after activity and context are controlled. Improving support by deleting constraints, widening calipers, or changing bins would be difficult to distinguish from post-hoc accommodation. Sample Game 1 remains useful for implementation tests and frozen examples, not another primary construct test.

### Option B — Within-possession or self-controlled contrasts

**Assessment: useful design ingredient, insufficient by itself.**

Pre/post, earlier/later within-possession, or possession-level difference-in-differences comparisons can control stable match and possession context. They do not automatically control the evolving intensity of an attack. The Phase 3B shifted-anchor result is direct evidence that other moments in the same possession can exhibit equal or larger movement. A defensible self-controlled design would need prospective anchor semantics, time-varying activity controls, boundary rules, and a comparison showing that the selected interval differs from the possession's ordinary activity trajectory. Otherwise it merely relocates the confound.

### Option C — Activity-stratified prospective sampling

**Assessment: necessary in some form, but not feasible as a one-match repair.**

The next design should condition on passage-level activity before inspecting post-anchor relational geometry. Candidate ingredients could include pre-anchor ball motion and defending-team motion, but Phase 3B values must not be used to choose thresholds. Strata or a prespecified continuous balancing method should be developed without relational outcomes and validated for overlap. Broader data are likely required because the frozen coarse bins already reduced Sample Game 1 support to 4.8%.

Activity conditioning must also avoid controlling away the phenomenon. The design should distinguish baseline motion before the candidate interval from typed relational change during it, rather than matching on the same post-anchor quantity it seeks to explain.

### Option D — Additional matches before another construct test

**Assessment: recommended.**

More matches provide a larger support pool, broader possession and activity contexts, and a way to separate match-specific behavior from reproducible geometry. They also permit genuine design/test separation: use one source or development subset to confirm deterministic implementation and support, freeze the protocol, then inspect relational outcomes on held-out matches.

Metrica Sample Game 2 or another transparent tracking source can be considered at the design level, but no new relational outcomes should be viewed until data harmonization, quality checks, sampling rules, activity conditioning, and support criteria are frozen. More frames from the same match would not solve dependence or match idiosyncrasy; the unit of expansion must include additional matches.

### Option E — Abandon event anchors as validation surrogates

**Assessment: event anchors should not remain the sole validation surrogate.**

Relational reconfiguration may precede an event, follow it, persist across several events, or occur without a recorded on-ball event. Receptions and possession changes are useful clocks and context markers, but Phase 3B shows that their semantics do not identify the construct. Treating another event type as a positive label would repeat the same problem unless its link to the geometric target is independently justified.

Future alternatives include independently specified soccer situations, prospective visual annotation, tactical contexts defined without viewing relational outcomes, or an external semantic label source. Human annotation is desirable for semantic validation but is not mandatory for the immediate design work: a narrower geometric primitive can first be tested for reproducibility and discrimination from activity.

## Should the umbrella construct remain the immediate target?

Phase 3 attempted to validate coherence, temporal localization, typed relational specificity, and excess beyond baseline motion simultaneously, using an indirect event anchor. That is too demanding for the current data and too ambiguous diagnostically when the design fails.

Three narrower primitives merit design consideration:

- focal departure beyond collective translation;
- local deformation beyond an activity-conditioned expectation;
- cross-scale disagreement with stable prospectively defined components.

None is automatically adopted. A primitive qualifies only if it has independent soccer meaning, prospectively fixed membership/reference rules, and a falsifiable contrast against ordinary activity. “Easy to measure” is insufficient. Local deformation, for example, remains vulnerable to membership sensitivity and generic active-play deformation; focal departure remains geometry rather than opponent responsibility; cross-scale disagreement may reflect noise or reference mismatch.

The umbrella construct should therefore remain the theoretical target but not the next direct empirical endpoint. The next empirical target should be one narrower, independently meaningful primitive selected and defined before outcomes, with the umbrella construct reserved for later synthesis if several primitives validate.

## Decision

### Recommendation: **B + C — expand data first, then preregister a narrower validation target**

This is not a recommendation to do every possible next step. It is a sequence:

1. Expand to additional matches and perform only harmonization, missingness, and prospective support diagnostics.
2. Select one narrower geometric primitive on conceptual grounds, not because it separated Phase 3B samples.
3. Freeze an activity-conditioned validation protocol with development/test separation.
4. Execute once on held-out matches.

Option A is rejected because another Sample Game 1 matching redesign would be post-hoc and support-limited. Option B may contribute a self-controlled comparison but cannot stand alone after the shifted-anchor result. Option C is necessary but requires Option D's larger data base. Option E changes the role of events: retain them as temporal/context information, not positive-condition labels.

The decisive scientific criterion is whether the study can distinguish **relational structure beyond ordinary defensive activity** from **more movement during more active passages**. If overlap or semantic information is insufficient to make that distinction, execution should stop rather than relax the design.

## Items to freeze before the next empirical execution

Before inspecting held-out relational outcomes, freeze:

1. the exact narrower primitive and why it is independently meaningful in soccer terms;
2. datasets and match-level development/test split;
3. coordinate, period, possession, player-availability, and missingness conventions;
4. sampling unit, anchor or interval semantics, and dependence/overlap rules;
5. pre-interval activity representation, measured strictly before the outcome interval;
6. balancing or self-control method, including calipers/strata chosen without Phase 3B outcome optimization;
7. minimum overall and per-context support and a mandatory stop rule;
8. prospectively selected references, local membership, and opponent relationships where applicable;
9. typed outcomes kept separate, with no composite rescue;
10. negative controls capable of exposing generic activity;
11. multiplicity, uncertainty, sensitivity analyses, seeds, and missing-data handling;
12. criteria that would reject the primitive or show that event/context semantics remain inadequate.

No attacker value, gravity, responsibility, causal, tactical-state, or umbrella reconfiguration claim should be evaluated in that execution.
