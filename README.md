# Moving the Defense

**Measuring Defensive Responses to Attacking Movement in Football**

**Moving the Defense** is a tracking-data research project about a familiar football idea:

> When an attacker does not receive the ball, can we measure what they made the defence do?

Analysts say that an attacker pinned a full-back, dragged a centre-back away, or forced a line to drop. Tracking data records where everyone moved, but it does not record why. This project is building the measurement foundation needed to separate one defender’s movement from the shift of the defensive unit, define attacking movement without using the defensive outcome, and eventually test whether particular attacking movements are associated with particular defensive changes.

The formal research question is:

> **How can tracking data measure defensive responses to attacking movement in open-play football?**

The governing distinction is:

> **Football concept ≠ tracking measurement ≠ theoretical mechanism.**

A geometric association is not a marking assignment, tactical decision, causal effect, or player value.

## The measurement problem

If the whole back line slides five metres left, a defender may travel a long way while barely changing position relative to the unit. If three defenders slide and one steps away from them, the individual change is hidden inside the shared shift.

The project therefore uses the other defending outfield players as a simple moving reference. For focal defender $d$,

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),
$$

where $\mathbf c_{-d}(t)$ is the centroid of the other available defending outfield players, excluding the goalkeeper. The accumulated path of $\mathbf r_d(t)$ answers a limited question: **how much did this defender move differently from the rest of the defensive unit?** It does not answer why.

![A shared defensive shift and an individual departure](figures/concepts/collective_translation_vs_focal_departure.png)

## What survived validation

The focal-relative path is the project’s strongest result:

- the definition and controls were frozen before held-out outcomes;
- it replicated from Metrica Sample Game 1 to held-out Sample Game 2;
- it then externally replicated across seven professional IDSSE matches from **one independent dataset/provider environment**, not seven providers;
- common translation cancelled, strict misaligned-reference controls passed, and all frozen smoothing/window sensitivities passed.

The supported claim remains geometric:

> **Focal-relative path externally replicated as a focal-versus-collective movement primitive across seven professional matches from an independent tracking dataset/provider environment under frozen criteria.**

It remains substantially associated with generic player activity and is not a validated tactical response.

## What failed—and why it matters

The project began with a more ambitious Structure / Track / Close / Recover state interpretation. Diagnostics showed that those ideas overlap, a simple fixed attacker-relative “Track” representation failed, and local stories changed when reasonable player relationships were selected prospectively.

Phase 3 then froze a reception-based validation design for relational reconfiguration. It produced **C**:

- only 46 of 315 reception candidates matched controls, versus 70% required support;
- shifted anchors inside the same possession reproduced or exceeded the apparent effects;
- pre-anchor activity matching removed the contrasts in a very small matched subset.

The lesson is central: active football passages can make generic movement look like meaningful structure. Receptions are useful clocks, not positive labels for defensive reconfiguration. Relational reconfiguration remains unvalidated.

![Why the reception-based route failed](figures/phase3/phase3_validation_failure.png)

## What prediction and opponent information added

After geometric replication, Phase 5A asked whether future focal-relative path was statistically predictable from pre-interval context. It produced **A — contextual expectation feasible**:

- median held-out MAE improved from 2.666 m to 2.114 m in the best simple model;
- every contextual model improved all seven held-out matches versus the unconditional baseline;
- almost 90% of the total improvement was already supplied by the focal defender’s recent movement;
- collective, ball, and spatial additions were small and directionally consistent, but not materially incremental under the frozen rule.

Phase 5B then added prospectively selected opponent geometry. It produced **B — mixed/partial**: the best opponent model improved median MAE by only 0.43%, improved six of seven matches, and did not show that nearest opponents were materially more informative than matched nonlocal opponents. This is a small predictive association, not tactical response or attacker attribution.

## Why the project moved upstream again

Two post-5B audits exposed a timing problem.

First, signed focal-relative displacement retained direction that scalar path magnitude loses. But constant-velocity continuation innovation did not cleanly identify response onset: neutral windows overlapped historical examples, and movement of later interest was often already developing inside the preceding two seconds.

Second, the project tested whether an attacker’s own trajectory could be broken into finite movement efforts without looking at defenders or outcomes. The outcome-blind speed-valley audit produced **B — mixed**:

- 38,651 candidate movement-effort episodes;
- 95.78% peaked below the 5.5 m/s high-speed comparator;
- 15,845 (41.00%) combined that lower peak with at least 3 m displacement;
- median displacement/path was 0.987;
- 42.22% met a predeclared fragmentation diagnostic;
- only 1.97% met a merging/direction-change diagnostic;
- a retained 56.30 m/s maximum was subsequently traced to an identity/trajectory-continuity failure rather than ordinary movement or smoothing alone.

The basic attacker-only approach survives, but the current valley rule must not be carried unchanged into later response sampling. A frozen prominence refinement reduced fragmentation sharply but produced 35.88%–69.03% merging/direction failures against a 3.97% safety cap. The result is **B**, no prominence was selected, and Game 2 remains unopened.

## Current frontier

The evidence hierarchy is:

```text
football question
        ↓
measurable attacking movement
        ↓
measurable defensive movement
        ↓
defender movement relative to the collective
        ↓
movement magnitude + signed geometric change
        ↓
contextual expectation
        ↓
opponent association
        ↓
tactical interpretation
        ↓
attacker attribution
        ↓
attacking value
```

Every arrow is conditional. The current methodological frontier is approximately:

> **Can attacking movement and defensive geometric change be represented as defensible finite units before testing their relationship?**

The project has not reached tactical interpretation, attacker attribution, causal influence, gravity, or off-ball value.

## Potential applications—not current products

If later semantic and contextual validation succeeds, the measurement foundation could support:

- team defensive-style profiles: how often defenders break from, hold with, or recover toward the unit;
- individual defensive-style profiles without immediately calling tendencies good or bad;
- opponent- or zone-specific comparisons;
- scouting and recruitment descriptions of defensive tendencies;
- automatic surfacing of candidate moments for match analysts;
- video indexing of unusual defensive adjustments;
- coaching feedback only after tactical interpretation is independently validated.

The repository does **not** currently evaluate defensive quality, identify correct decisions, automatically label pinning/dragging/tracking, prescribe coaching actions, or measure attacker value.

## Evidence and reproducibility

The project preserves prospective protocols, machine-readable configs, executed notebooks, negative controls, saved results, and failed approaches. The shortest authoritative guide is the [claim-status ledger](docs/claim_status.md).

Data roles:

- Metrica Sample Game 1 — development and historical diagnostics;
- Metrica Sample Game 2 — completed held-out validation;
- seven IDSSE matches — completed external replication and predictive tests in one additional provider environment;
- Metrica Sample Game 3 — untouched and not part of the current evidence.

Start with the [documentation guide](docs/README.md) or the football-first [project explainer](docs/project_explainer.md). Technical reproduction instructions are in [docs/reproducibility.md](docs/reproducibility.md).

## Repository map

```text
config/      frozen protocols and predeclared exploratory rules
docs/        current explanations, claim controls, results, and audit trail
figures/     documentation and result figures
notebooks/   executed historical diagnostics and governed analyses
outputs/     machine-readable derived results
references/  bibliography and provenance
src/         reproducible analysis implementations
data/        ignored local raw data
```

## Submission horizon

The 2027 MIT Sloan Sports Analytics Conference abstract deadline is **October 1, 2026, 11:59 p.m. Eastern**. The deadline requires a coherent evidence story, not completion of the ultimate gravity/value vision. See the [research roadmap](docs/research_roadmap.md) and [Sloan-readiness audit](docs/sloan_readiness.md).

## License

Code and documentation are released under the [MIT License](LICENSE). Provider data remain subject to their source terms.
