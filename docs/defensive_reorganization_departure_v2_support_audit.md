# Defensive Reorganization Departure v1 support audit

**Audit date:** 2026-09-04

**Outcome firewall:** no E0/E1 fit, prediction error, residual, DRD, retrieval,
SkillCorner outcome, or Metrica Sample Game 3 access

## Decision

The exact verdict is **C — freeze DRD v2 with a principled change to
entity-support requirements**.

V1 remains closed as **DRD APPLICATION FOUNDATION INVALID**. It failed its
prospective 1,000-row-per-match gate before model fitting. V2 does not lower
that threshold, exclude the limiting match, or change any target, feature,
model, validation, success, retrieval, or stopping rule. It only replaces the
assumption that an attacking side always has exactly ten outfield players with
a complete, event-defined **current on-pitch attacking outfield set**.

The required disclosure is:

> v1 prospectively failed support before fitting; v2 was designed after
> observing support composition but before outcomes.

## What the 1,000-row rule was based on

Repository history contains the value in the frozen v1 protocol and
configuration, and an earlier expectation protocol uses the same minimum. It
contains no power calculation, sampling-variance analysis, numerical-rank
derivation, or effective-block argument that yields 1,000. The basis is
therefore **D — an arbitrary/conservative convenience threshold**, not a
mathematical or empirical requirement.

The rule superficially guards the number of heldout observations available for
match-level MAE, retrieval, and nested validation. It does not establish ridge
estimability and it does not measure independent support: simultaneous focal
attackers share an anchor, and anchors within 60-second blocks are temporally
dependent. The number and spread of occupied blocks are more informative about
effective temporal support, but replacing 1,000 after observing 782 would be a
new validation choice. V2 therefore retains 1,000 unchanged.

## Outcome-blind effective support under v1

These summaries use only observation identifiers, match, period, anchor time,
block, focal-player identity, and the local eligibility ledger. No response or
prediction quantity was selected.

| Match | Rows | Anchors | Eligible period coverage (s) | 60-s blocks | Span (s) | Rows/block median [IQR], range | Focals/anchor median [IQR], range | Largest block |
|---|---:|---:|---|---:|---:|---|---|---:|
| J03WMX | 10,863 | 1,208 | P1 8–2,816; P2 8–3,000 | 97 | 5,800 | 117 [108, 135], 9–135 | 9 [9, 9], 6–9 | 1.2% |
| J03WN1 | 782 | 87 | P1 8–424; no P2 | 8 | 416 | 108 [92.25, 119.25], 17–135 | 9 [9, 9], 8–9 | 17.3% |
| J03WOH | 9,877 | 1,098 | P1 8–2,764; P2 8–2,668 | 92 | 5,416 | 117 [99, 126], 18–135 | 9 [9, 9], 6–9 | 1.4% |
| J03WOY | 10,114 | 1,124 | P1 8–2,752; P2 8–2,928 | 95 | 5,664 | 117 [90, 126], 27–135 | 9 [9, 9], 8–9 | 1.3% |
| J03WPY | 10,947 | 1,217 | P1 8–2,756; P2 8–3,068 | 98 | 5,808 | 117 [108, 126], 9–135 | 9 [9, 9], 7–9 | 1.2% |
| J03WQQ | 7,100 | 789 | P1 8–2,760; P2 8–804 | 61 | 3,548 | 117 [108, 135], 9–135 | 9 [9, 9], 8–9 | 1.9% |
| J03WR9 | 10,142 | 1,127 | P1 8–2,720; P2 8–3,044 | 93 | 5,748 | 117 [90, 126], 36–135 | 9 [9, 9], 8–9 | 1.3% |

J03WN1's 782 rows are concentrated in the first 416 seconds of period 1 and
eight blocks; one block contains 17.3% of its rows. That is not broad
match-level temporal support. A block rule is conceptually preferable to raw
rows, but this observed support does not justify choosing a passing block
threshold post hoc.

## Which entities each quantity requires

| Quantity | Focal attacker | Ball | Defending outfield set | Attacking outfield set |
|---|:---:|:---:|:---:|---|
| Audit/split fields | yes | no | no | no |
| Target `Y`, near `N`, middle `M` | yes | no | all ten, through the inherited fixed D1–D10 vector | no |
| E0 prior/exposure paths | yes | no | no | no |
| Movement-direction features | yes | no | no | no |
| Start-position/unit width/depth | yes | no | all ten | no |
| Ball-relative features | yes | yes | all ten for unit-relative ball position | no |
| Ball-nearest exclusion | focal candidate | yes | no | every current on-pitch attacking outfielder |

All ten attackers are not mathematically required. Complete simultaneous
support for **every current on-pitch attacking outfielder** is required: with
partial support an unseen player might be nearer the ball, so the frozen
threshold-free exclusion would be undefined. The reduced rule is logically
valid only when event metadata defines the complete current active set and
tracking support agrees with it exactly.

J03WN1 supplies the concrete non-outcome support case. Provider event metadata
confirms the dismissal of a starting outfielder. Requiring ten afterward
confuses complete support with pre-dismissal team size. V2 instead requires
the exact current set after deterministic substitutions and confirmed player
dismissals. Ambiguous roster events or disagreement between the event-defined
set and complete tracking support fail closed. The observation-level provider
ledger and exact provider-linked event identity remain local-only.

## Alternatives considered prospectively

| Option | Assessment |
|---|---|
| A — keep v1 and stop | Lowest discretion and scientifically valid, but it abandons an application test because of a support definition that confounds completeness with a confirmed dismissal. |
| B — effective-block gate | Blocks better represent temporal dependence than rows, but J03WN1 has only eight first-period blocks. Selecting a passing rule now would be result-driven and would alter validation support. Rejected. |
| C — exclude low-support matches | Preserves v1 eligibility but removes a known difficult match after seeing support and weakens seven-match leave-one-match-out validation. Rejected. |
| D — current-active-set support | Corrects the entity definition while preserving complete ball-nearest identification, all seven matches, and every downstream scientific rule. This is the selected basis for verdict C. |
| E — different dataset | A defensible fallback if current roster governance cannot be implemented, but it is not necessary before testing the principled active-set rule and has lower near-term value than preserving the governed seven-match environment. |

## Degrees of freedom and boundary

Supersession is acceptable only because invalidity occurred before any outcome
model or performance result. The observed fact was support composition: 782
rows under v1 and a confirmed dismissal underlying the missing tenth attacker.
The change is fixed before outcomes and cannot be tuned to model performance.
It retains the v1 1,000-row and 90% retention gates. V2 execution remains a
separate future governed step.

This audit establishes neither v2 sample sufficiency nor application value.
It authorizes a prospectively frozen support definition only.
