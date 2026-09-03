# Defensive Coverage Redistribution v1 — Prospective Rejection Record

**Status:** rejected before empirical execution

**Decision date:** 2026-09-03

**Decision checkpoint:** `c3346602f706dedab237a0b2c4148485e5f31ade`

The frozen [v1 protocol](defensive_coverage_redistribution_v1.md) and
[configuration](../../config/defensive_coverage_redistribution_v1.json) remain
unchanged as the scientific record. No Game 1 coverage outcome, coefficient,
interval, sample, or empirical figure was computed or inspected under v1.
Metrica Sample Games 2 and 3 and IDSSE coverage outcomes also remained unopened.

## Identification defect

V1 defined, for every focal attacker $a$, an optimized coverage cost over the
other nine attackers and then demeaned those focal-perspective outcomes within
the common anchor. Under stable one-to-one pairings, let $\Delta c_j$ be each
attacker's matched-distance change. Then

$$
Y_a=\frac{1}{9}\sum_{j\ne a}\Delta c_j
$$

and the frozen transformation implies

$$
Y_a-\overline Y
=-\frac{\Delta c_a-\overline{\Delta c}}{9}.
$$

The intended outcome for the other nine attackers can therefore collapse
exactly into the negative marginal matching-cost change of the excluded focal
attacker. A positive focal-response coefficient can arise even when the focal
perspective's raw other-nine coverage cost is unchanged. Grouped resampling,
the focal-label permutation, and the frozen robustness checks cannot repair a
misidentified estimand.

This is a pre-execution construct-identification failure, not an empirical null,
an inference defect, or a reason to tune v1. The design is superseded by the
[v2 protocol](defensive_coverage_redistribution_v2.md), which uses one physical
anchor-level unit, one start-defined reference attacker, one fixed elsewhere
set, and no within-anchor repeated-focal demeaning.
