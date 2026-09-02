# Concurrent Defensive Coordination Form v1 — Game 2 Replication Clarification

**Status:** frozen prospectively before any Game 2 coordination-form result

**Date:** 2026-09-02

**Starting commit:** `55c3b27fcc1cead8595ec7e2d8e2ae43bca0ee76`

**Original protocol SHA-256:** `3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032`

**Original configuration SHA-256:** `d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3`

## Prospective firewall and scope

No Metrica Sample Game 2 coordination-form sample, coefficient, interval, sensitivity, secondary result, or status had been computed or inspected when this clarification was frozen. IDSSE coordination-form results remained uncomputed, and Metrica Sample Game 3 remained untouched.

This clarification changes no outcome, exposure, sample, support rule, filter, window, ranking, covariate, model, bootstrap, sensitivity, or estimand. The original protocol and configuration remain byte-identical and scientifically authoritative. This artifact closes only the heldout-replication status terminology before Game 2 observation.

## Frozen Game 2 primary estimand

The sole classification-driving estimand remains the `AARD_vel` contrast

$$
\operatorname{mean}(D2,D3)-\operatorname{mean}(D4,D5,D6,D7).
$$

## Frozen heldout-replication statuses

- **GAME 2 COORDINATION FORM REPLICATION INVALID:** execution or hard-QC failure prevents valid inference, or fewer than 1,900 paired-valid bootstrap replicates are available.
- **GAME 2 COORDINATION FORM REPLICATION NOT SUPPORTED:** execution is valid and the primary 1.0 Hz estimate is less than or equal to zero.
- **GAME 2 COORDINATION FORM REPLICATION SUPPORTED:** execution is valid, the primary 1.0 Hz estimate is positive, its two-sided 95% block-bootstrap percentile interval is strictly above zero, and the frozen 1.5 Hz sensitivity point estimate is positive.
- **GAME 2 COORDINATION FORM REPLICATION MIXED:** every other valid case with a positive primary 1.0 Hz estimate.

The status does not require equality with Game 1, confidence-interval overlap, a particular D1–D10 profile, D1 to be largest, or remote ranks to be negative. Secondary geometry cannot rescue or upgrade the primary classification.

## Post-classification comparison

Only after Game 2 is classified may its magnitude, interval, D1 benchmark, individual ranks, cross-axis result, deformation context, absolute-coordinate comparator, and preprocessing comparators be compared descriptively with Game 1. None is an additional replication criterion.

This clarification introduces no new scientific decision rule beyond the prospectively specified heldout status mapping above.
