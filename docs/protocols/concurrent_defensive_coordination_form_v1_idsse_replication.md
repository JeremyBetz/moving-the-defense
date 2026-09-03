# Concurrent Defensive Coordination Form v1 — IDSSE External Replication Clarification

**Status:** frozen prospectively before any IDSSE coordination-form coefficient

**Date:** 2026-09-02

**Starting commit:** `c22a9c2e6a8117dc3528e45207cddba5073ad1ef`

**Original protocol SHA-256:** `3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032`

**Original configuration SHA-256:** `d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3`

## Firewall and scope

No IDSSE coordination-form sample, coefficient, interval, sensitivity, secondary result, or status had been computed or inspected when this clarification was frozen. Metrica Sample Game 3 remained untouched.

This clarification changes no outcome, exposure, sample, support rule, filter, window, ranking, covariate, model, bootstrap, sensitivity, or estimand. The original protocol and configuration remain byte-identical and scientifically authoritative.

The governed match set is exactly `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, and `J03WR9`.

## Match-level statuses

The sole classification-driving estimand remains $\operatorname{mean}(D2,D3)-\operatorname{mean}(D4,D5,D6,D7)$ for `AARD_vel`.

- **INVALID:** execution/QC prevents valid inference or fewer than 1,900 paired-valid bootstraps.
- **NOT SUPPORTED:** valid primary 1.0 Hz estimate is at or below zero.
- **SUPPORTED:** valid primary 1.0 Hz estimate is positive, its two-sided 95% block-bootstrap percentile interval is strictly above zero, and the 1.5 Hz sensitivity point estimate is positive.
- **MIXED:** every other valid positive primary estimate.

## Seven-match external status

No pooled coordination-form estimator was prospectively defined, so none will be introduced in this execution.

- **IDSSE COORDINATION FORM EXTERNAL REPLICATION INVALID:** any governed match is invalid.
- **IDSSE COORDINATION FORM EXTERNAL REPLICATION SUPPORTED:** all seven governed matches are individually supported.
- **IDSSE COORDINATION FORM EXTERNAL REPLICATION NOT SUPPORTED:** at least four valid match-level primary 1.0 Hz estimates are at or below zero.
- **IDSSE COORDINATION FORM EXTERNAL REPLICATION MIXED:** every other valid seven-match result.

The summary rule does not require magnitude equality, confidence-interval overlap with Metrica, monotonic ranks, D1 dominance, individually positive D2 and D3, negative remote ranks, or null secondary quantities. Secondary quantities cannot rescue a status.

Only after all statuses are assigned may rank profiles and Metrica results be compared descriptively.
