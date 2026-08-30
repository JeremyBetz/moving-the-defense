# Post-5B attacking-movement prominence-refinement protocol

**Version:** 1.0
**Status:** frozen before refined segmentation execution
**Scope:** protocol design only; no refined episode has been constructed or inspected

> **Execution status:** this document preserves the pre-execution design. It subsequently executed once on Game 1 and classified **B**, with no selected prominence and no Game 2 execution. See the [results](post5b_attacking_movement_prominence_refinement_results.md).

The machine-readable source of truth is [`config/post5b_attacking_movement_prominence_refinement_rules.json`](../config/post5b_attacking_movement_prominence_refinement_rules.json).

## 1. Scientific question

> **Can the existing attacker-only speed-valley segmentation be refined using valley prominence so that meaningful over-fragmentation is reduced without materially increasing merging/direction failures or collapsing lower-speed movement coverage?**

This remains a movement-segmentation question. It does not classify tactical movements or test defensive response, attacker influence, gravity, or value.

## 2. Why prominence, and why not direction splitting?

The historical Game 1 audit classified the basic speed-valley method **B — mixed**. It produced 38,651 episodes, with 42.22% meeting at least one fragmentation diagnostic but only 1.97% meeting a merging/direction diagnostic. The dominant observed problem is therefore weak valleys creating too many short or tiny episodes.

Prominence directly tests the strength of a candidate slowdown while preserving the valley-to-valley architecture. A small fluctuation such as 4.0 → 3.8 → 4.1 m/s should have low prominence; a slowdown such as 4.0 → 1.2 → 4.3 m/s should have much greater prominence. Direction splitting targets the smaller secondary failure, would add another construct and parameter family, and is excluded from this one-refinement test.

## 3. Provenance and novelty boundary

Llana et al. (2022), already recorded in the [literature review](literature_review.md) and [bibliography](../references/bibliography.md), provide football precedent for smoothed player speed, valley-to-valley physical-effort sections, and peak-speed description. Standard signal processing supplies topographic prominence as a general measure of extremum strength. No verified football-specific prominence threshold has been identified. The numerical ladder below is a bounded development choice, not imported football truth, and neither valley segmentation nor prominence is claimed as novel.

## 4. Development and validation separation

Metrica Sample Game 1 is the development environment. Repository history and current documentation contain no Game 2 attacking-movement segmentation, prominence calculation, refined episode count, or refinement result. Game 2's earlier use for Phase 4 defender-relative geometric validation is a different outcome and does not contaminate this question.

**Contamination/readiness judgment: A — Game 2 is untouched for this specific segmentation outcome and remains eligible as held-out validation.**

No Game 2 tracking or segmentation output was inspected while writing this protocol. Sample Game 3 remains untouched.

## 5. Historical method held fixed

The no-prominence branch must reproduce the saved Method A result exactly:

- centered seven-frame x/y position means with complete support;
- speed from consecutive smoothed positions and observed time difference;
- plateau-aware local minima and plateau midpoint;
- candidates within 1.0 s consolidated by lower speed, with earlier time on an exact tie;
- consecutive retained valleys define episodes;
- 1.0 s minimum episode duration;
- no peak-speed inclusion threshold;
- the same period, unsupported-coordinate, `BALL OUT`, and `SET PIECE` boundaries.

## 6. Exact prominence definition

For a historical candidate valley at index $i$, let $v_i$ be smoothed speed and apply standard topographic peak prominence to the inverted signal $-v$. For an exact speed-domain statement, find the nearest strictly deeper speed valley on each side, using the eligible-block edge when none exists. Let $L_i$ and $R_i$ be the maximum speeds encountered from $i$ through those left and right limits. Then:

$$P_i=\min(L_i,R_i)-v_i.$$

Prominence is measured in **m/s**. The full eligible block is the search scope; there is no additional local-window parameter. Plateau minima retain the historical midpoint. A candidate passes when its prominence is greater than or equal to the configured threshold.

For each nonzero branch, operations occur in this order:

1. construct the historical plateau-aware candidates;
2. compute prominence within the eligible block;
3. remove candidates below the threshold;
4. apply the historical 1.0 s consolidation to the remaining candidates;
5. create consecutive-valley episodes and apply the historical 1.0 s numerical-stability minimum.

The later implementation must be deterministic and mathematically equivalent to standard peak prominence. SciPy is not currently an explicit dependency, so this protocol does not silently add it.

## 7. Closed candidate ladder

| Candidate | Prominence |
|---|---:|
| Historical baseline | 0.00 m/s |
| Modest filter | 0.25 m/s |
| Intermediate filter | 0.50 m/s |
| Stronger filter | 1.00 m/s |

This ladder was fixed before any refined output. It will not be extended after execution.

## 8. Development criteria

### Fragmentation success

Use the historical definitions of short duration, tiny path, tiny displacement, and `diag_fragmentation_any` unchanged.

$$F(P)=100\frac{N_P(\text{diag\_fragmentation\_any})}{N_P(\text{all episodes})}.$$

A candidate passes only when the relative reduction from the documented 42.22% operational baseline is at least 20%. The frozen operational cap is:

$$F(P)\leq 33.776\%.$$

### Merging/direction safety

Use the historical long-duration, low displacement/path, direction-change, and `diag_merging_any` definitions unchanged:

$$M(P)=100\frac{N_P(\text{diag\_merging\_any})}{N_P(\text{all episodes})}.$$

Both proposed safety statements reduce to the stricter frozen requirement:

$$M(P)\leq 3.97\%.$$

### Lower-speed coverage protection

The historical 41.00% is **not** the share among episodes displacing at least 3 m. It is the joint share of all Method A episodes that both peak below 5.5 m/s and displace at least 3 m. Reinterpreting its denominator would be invalid.

The prospective metric therefore retains the all-episode denominator:

$$L(P)=\frac{N_P(\text{peak speed}<5.5\ \text{m/s and displacement}\geq3\ \text{m})}{N_P(\text{all episodes})}.$$

The saved exact baseline is 0.4099505834260433. A candidate may lose no more than 10% relatively:

$$L(P)\geq0.368955525083439\quad(36.8955525083439\%).$$

A conditional share among episodes displacing at least 3 m may be reported descriptively, but it cannot replace this criterion.

## 9. Selection and classification

A nonzero candidate is eligible only if it passes fragmentation, merging/direction safety, lower-speed coverage, and every implementation/QC requirement. If none qualifies, select none. If one qualifies, select it. If several qualify, select the **lowest nonzero prominence**, making the smallest intervention in the historical method.

Quantitative criteria plus objective implementation/QC validity determine selection and classification completely. The deterministic visual audit is descriptive: it cannot rescue a failed criterion, reject a candidate because another threshold looks better, change selection based on football aesthetics, or trigger threshold tuning.

- **A:** at least one nonzero candidate passes the complete quantitative and implementation/QC package.
- **B:** at least one candidate achieves the required 20% fragmentation reduction, but none passes the complete quantitative and implementation/QC package.
- **C:** no candidate achieves the required fragmentation reduction, or the refinement is unstable, uninterpretable, or fails implementation QC.

Visual review may invalidate execution only by exposing an objective implementation/QC inconsistency—for example, a plotted boundary absent from the documented algorithm, plotted values disagreeing with machine-readable output, a reported qualifying valley failing the implemented prominence rule, mismatched timestamps/player identities, or another reproducibility defect. Such a finding is recorded as implementation QC failure rather than a subjective segmentation judgment.

## 10. Deterministic visual audit

The sample is selected from the historical Game 1 Method A table before refined results:

1. in every team × period stratum, order episodes by start time, numeric player ID, start frame, then end frame;
2. for a stratum containing $n$ rows, select zero-based indices $\lfloor(n-1)q+0.5\rfloor$ for $q\in\{1/6,3/6,5/6\}$;
3. in each stratum, add the earliest historical fragmentation example under the same tie order;
4. in each stratum, add the longest historical merging/direction-risk example, breaking ties by start time, player, and frames;
5. take the union by historical episode ID and retain all reason labels.

After execution, plots may show only the player's trajectory and speed with historical versus selected-prominence boundaries. No defensive player, event outcome, or manually chosen example may be added. Visual appearance has no selection or classification role unless it reveals an objective implementation/QC defect.

## 11. Tracking-support treatment

No automatic numeric support rule has been frozen, so the primary Game 1 comparison preserves the historical scope. It must not silently clip, repair, or exclude an interval.

The confirmed Home 10 period-1 support issue is handled only as a separate diagnostic sensitivity: report primary metrics unchanged, then separately exclude episodes whose required raw/smoothing support intersects frames 2911–2945. The larger Home 3 and Away 22 maxima remain descriptive flags, not automatic exclusions. Prominence is not a remedy for tracking discontinuity.

The governing architecture is:

> raw tracking support → trustworthy player trajectory → attacking movement segmentation → defensive geometric relationship testing

## 12. Outcome firewall

Development may use only player-own movement geometry, time/frame/period support, the existing global open-play boundaries, and the frozen segmentation diagnostics. It may not use defender coordinates as outcomes, focal-relative defensive change, receptions, tackles, passes, shots, expected value, tactical annotations, bridge results, or Sample Game 3.

## 13. Held-out Game 2 plan

Only a Game 1 **A** result advances. The least-restrictive eligible rule must be frozen before any Game 2 segmentation output is constructed. Game 2 receives no retuning.

Held-out validation asks whether:

- fragmentation decreases relative to Game 2's historical no-prominence branch;
- merging/direction remains at or below 3.97%;
- the all-episode lower-speed/≥3 m joint share remains at least 90% of Game 2's no-prominence share;
- the same deterministic visual audit remains coherent.

## 14. Anti-tuning stopping rule

After this closed prominence ladder, do not add direction splitting, another refinement, changed duration thresholds, changed valley spacing, or changed smoothing because a criterion is narrowly missed. If prominence fails, stop and reassess the segmentation construct conceptually before another implementation.

## 15. Result status and nonclaims

At freeze time, no refined segmentation had been executed. The protocol itself created no result table, episode count, selected threshold, validated support filter, tactical movement construct, defensive response, attacker influence, gravity, or value. The later governed result is recorded separately.
