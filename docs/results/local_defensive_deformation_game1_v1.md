# Local Defensive Deformation v1 — Game 1 Development Result

## Status

> **GAME 1 DEFORMATION DEVELOPMENT COHERENT**

This is a Tier-1 development result on Metrica Sample Game 1. It is not held-out evidence and does not authorize Game 2 execution.

## Sample and model

The frozen footprint inventory supplied 7,823 attacker anchors, 804 unique anchor times, and 78,230 complete D1–D10 defender rows. The four-second subset contained 7,328 anchors. All models used the frozen raw-metre design: intercept, attacker path, focal prior endpoint deformation, and whole-unit prior endpoint deformation.

## Primary result

| Rank | Attacker-path coefficient (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| D1 | 0.13907 | [0.11439, 0.16524] |
| D2 | 0.11236 | [0.08905, 0.13567] |
| D3 | 0.10469 | [0.08455, 0.12550] |
| D4 | 0.10455 | [0.08046, 0.12945] |
| D5 | 0.08940 | [0.06691, 0.11211] |
| D6 | 0.09616 | [0.06890, 0.12114] |
| D7 | 0.09282 | [0.06618, 0.12032] |
| D8 | 0.08834 | [0.06254, 0.11555] |
| D9 | 0.09608 | [0.07178, 0.12055] |
| D10 | 0.10117 | [0.07609, 0.12723] |

| Region/contrast | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| Near D1–D3 | 0.11871 | [0.09751, 0.14114] |
| Middle D4–D7 | 0.09573 | [0.07356, 0.11852] |
| Far D8–D10, descriptive | 0.09520 | [0.07207, 0.11945] |
| Primary near minus middle | 0.02297 | [0.01434, 0.03235] |
| Temporal-control near minus middle | 0.01135 | [0.00443, 0.01869] |
| Paired primary minus control | 0.01162 | [0.00231, 0.02047] |

The temporal control retained positive structure. The timing-specific evidence is the prospectively frozen paired excess, whose interval was strictly positive.

## Robustness and secondary geometry

The four-second near-minus-middle estimate was 0.02653 [0.00994, 0.04332]. The frozen exposure trim removed 79 anchors (1.010%), producing 0.01994 [0.00957, 0.03045] and retaining 86.81% of the primary magnitude.

The secondary relational-path contrast was 0.02540 [0.01693, 0.03475], so it did not materially oppose the endpoint result. Median endpoint deformation by rank ranged from 2.181 to 2.237 m; relational path ranged from 2.389 to 2.439 m. Signed mean spacing changes were small and mixed (approximately -0.103 to +0.072 m), showing that the RMS result is relational change rather than uniform expansion. Median whole-unit endpoint deformation was 2.418 m.

## QC clarification

The first result serialization incorrectly applied a blanket finite-value check to null four-second values on anchors prospectively ineligible for four-second support. The frozen protocol defines that sensitivity on a separate complete subset. The check was corrected to require finite primary quantities for every row and finite four-second quantities wherever present. No scientific sample, outcome, estimate, bootstrap, threshold, or decision rule changed.

All 13 hard checks passed. Each of six bootstrap families had 2,000/2,000 valid replicates. Synthetic common translation, rotation, reflection, uniform scaling, and local-displacement tests passed.

## Claim boundary

The strongest permitted development claim is:

> In Metrica Sample Game 1, greater preceding attacker movement was associated with greater subsequent change in defender-to-defender spacing relationships among near defender ranks than among middle ranks, beyond the frozen recent-relational-activity covariates and paired temporal control.

In plain football language, nearby defenders' internal spacing changed somewhat more with larger preceding attacker movements than did the middle-ranked defenders' spacing. This does not show that the attacker caused, manipulated, stretched, dragged, pinned, or tactically disrupted the defence.

Machine-readable Tier-1 outputs are in `outputs/local_defensive_deformation_game1_v1/`.
