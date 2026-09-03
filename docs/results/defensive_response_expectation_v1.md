# Defensive Response Expectation v1 — Results

**Formal status:** `NOT SUPPORTED`

**Frozen protocol:** [`defensive_response_expectation_v1.md`](../protocols/defensive_response_expectation_v1.md)

**Frozen configuration:** [`defensive_response_expectation_v1.json`](../../config/defensive_response_expectation_v1.json)

## Question and boundary

This seven-match IDSSE execution asked whether allowing the defending side within each match to have an intercept and concurrent-attacker-path slope deviation improved temporally blocked heldout prediction of the observed D2–D3-minus-D4–D7 attacker-aligned defender-relative velocity response. The classification concerns only a **match-specific defensive-response increment**. It cannot establish stable team identity, tactical style, assignment, causal attacker influence, gravity, or value.

## Sample and validation

The common feature sample retained all 73,852 outcome-eligible anchors. Five contiguous fold groups and a one-block embargo produced 73,552 heldout predictions per model; 300 `J03WN1` observations from the sparse second defending side did not meet the frozen fold-support rule. Every other match retained all eligible anchors.

| Match | Eligible anchors | Heldout rows | Defending-side counts |
|---|---:|---:|---|
| J03WMX | 12,335 | 12,335 | 7,261 / 5,074 |
| J03WN1 | 4,874 | 4,574 | 300 / 4,574 |
| J03WOH | 11,248 | 11,248 | 6,108 / 5,140 |
| J03WOY | 11,519 | 11,519 | 5,611 / 5,908 |
| J03WPY | 12,397 | 12,397 | 7,501 / 4,896 |
| J03WQQ | 9,961 | 9,961 | 3,570 / 6,391 |
| J03WR9 | 11,518 | 11,518 | 6,930 / 4,588 |

Coordinates stayed in fixed-pitch metres. The goalward longitudinal sign was registered deterministically from the opposing goalkeeper's median fixed-pitch x within each period. In fold 0, the unsupported `J03WN1` side columns had zero training variance and were removed from training and heldout matrices exactly under the frozen zero-variance rule.

## Heldout performance

| Model | Macro MAE (m/s) | Weighted MAE (m/s) | RMSE (m/s) |
|---|---:|---:|---:|
| E0 | 0.729262 | 0.729223 | 0.987964 |
| E1 | 0.725360 | 0.725304 | 0.981156 |
| E2a | 0.725647 | 0.725555 | 0.981294 |
| E2b | 0.725807 | 0.725701 | 0.981428 |

E1 improved on E0 by 0.003902 m/s, or 0.5350%, and did so in all seven matches. E2a worsened E1 by 0.000287 m/s (−0.0396%) and improved one match. The primary E2b comparison worsened E1 by 0.000447 m/s (−0.0616%) and improved **zero of seven** matches.

| Match | E1 MAE − E2b MAE (m/s) |
|---|---:|
| J03WMX | −0.000147 |
| J03WN1 | −0.000878 |
| J03WOH | −0.000190 |
| J03WOY | −0.000008 |
| J03WPY | −0.000572 |
| J03WQQ | −0.000797 |
| J03WR9 | −0.000534 |

The paired hierarchical bootstrap produced 2,000 valid replicates. Its 95% interval for absolute E1-minus-E2b MAE improvement was **[−0.000785, −0.000122] m/s**; the relative interval was **[−0.1094%, −0.0167%]**.

## Shifted-label control and classification

The observed E2b improvement was −0.0616%. The 95th percentile of 200 valid deterministic shifted-label controls was −0.0163%, so the observed result did not pass the frozen control. Thirty-eight algebraically invalid label draws were rejected only because the frozen design was not full rank; 200 valid controls were obtained from 238 deterministic attempts. No draw was rejected using model performance.

Every frozen support gate failed except bootstrap validity: macro improvement was not positive, no match improved, the 3% threshold failed, the paired interval was not positive, and the control failed. The exact frozen formal classification is therefore:

> **NOT SUPPORTED**

Movement and modeled spatial context predicted the observed response slightly better than the frozen match-side increment. Current evidence does not support a material match-specific defensive-response component in this seven-match schedule.

## Nonclassifying checks

The expanding early-to-later check also favored E1: E1 macro MAE was 0.719552 m/s and E2b was 0.720028 m/s, a −0.0662% E2b increment. The repeated-team check for `DFL-CLU-00000P` produced positive path-deviation estimates in all five leave-one-match-out folds (0.0103–0.0188), but this is a secondary, model-dependent descriptive pattern. One repeated team cannot establish a stable team signature and cannot rescue the failed primary classification.

The saved E1 residual descriptions mean only more or less attacker-aligned local defensive response than predicted by the frozen spatial-context model. They are not disruption, influence, tactical surprise, gravity, or value.

## Reproduction and publication boundary

All ten compact governed outputs reproduced byte-for-byte in an independent complete rerun. The local detailed prediction source and heldout prediction Parquets are ignored and are not published because they contain provider-linked observation identifiers and times. Their regeneration path and the closed IDSSE input hash are recorded in the manifest and result bundle. Metrica Sample Game 3 was not accessed.

Machine-readable results are under [`outputs/defensive_response_expectation_v1/`](../../outputs/defensive_response_expectation_v1/).
