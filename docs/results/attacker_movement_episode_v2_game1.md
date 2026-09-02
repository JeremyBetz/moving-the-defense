# Attacker Movement Episode v2 — Game 1 Development Result

## Status

> **GAME 1 ATTACKER EPISODE v2 DEVELOPMENT COHERENT**

This is a Tier-1 development result on Metrica Sample Game 1. It segments only the focal player's own 2D trajectory. It does not validate tactical runs, defensive response, attacker influence, or value, and it does not authorize Game 2 without separate prospective governance.

## Firewall and method

The [protocol](../protocols/attacker_movement_episode_v2.md) and configuration were committed at `8f79f11` before execution. Candidate A exactly reproduced the closed speed-valley baseline. Candidate B retained historical valleys, added sustained direction candidates from 0.48 s mean-velocity support on each side of a frame, protected changes of at least 45°, and repeatedly removed only unprotected valley boundaries whose union remained very direct ($Q\ge0.95$) with less than 45° cumulative turning. No prominence threshold was reused. The already-closed 2D velocity PELT result served as method precedent; no new Candidate C penalty was introduced.

The sample contained 26 outfield identities, 1,604 eligible player blocks, and 2,258,316 smoothed supported frames across both periods. No interpolation, clipping, ball variable, defender variable, outcome event, Game 2, Game 3, or IDSSE input entered execution.

## Baseline reproduction

Candidate A reproduced all 38,651 historical episodes, identities, and diagnostics. Maximum numerical difference was $7.11\times10^{-15}$.

| Diagnostic | Candidate A | Candidate B |
|---|---:|---:|
| Episodes | 38,651 | 31,965 |
| Fragmentation composite | 16,320 (42.2240%) | 9,193 (28.7596%) |
| Merging/direction composite | 763 (1.9741%) | 847 (2.6498%) |
| Duration $\le1.5$ s | 13,693 | 6,982 |
| Path $\le1$ m | 6,694 | 4,616 |
| Displacement $\le0.5$ m | 3,698 | 2,557 |
| Duration $\ge8$ s | 141 (0.3648%) | 288 (0.9010%) |
| $Q\le0.5$ | 268 | 235 |
| Path $\ge3$ m and turning $\ge180°$ | 424 | 380 |
| Lower-speed and displacement $\ge3$ m | 15,845 (40.9951%) | 15,551 (48.6501%) |
| No high-speed-comparator overlap | 96.7194% | 96.2803% |

Fragmentation fell by **31.8881% relative**, passing the frozen 33.776% cap. Merging/direction rose but remained below its frozen 3.97% safety cap. Lower-speed coverage increased by 18.6730% relative and passed its 36.8956% minimum. Candidate B retained 29,954 valley boundaries and 3,545 direction boundaries.

## Episode geometry

| Quantity | Candidate A median (IQR; range) | Candidate B median (IQR; range) |
|---|---|---|
| Duration | 1.88 s (1.32–2.76; 1.00–51.16) | 2.32 s (1.60–3.32; 1.00–51.12) |
| Path | 2.650 m (1.324–5.647; 0.008–63.292) | 3.394 m (1.569–6.951; 0.008–63.292) |
| Displacement | 2.576 m (1.297–5.468; 0.001–61.534) | 3.294 m (1.518–6.712; 0.001–61.534) |
| Peak speed | 1.664 m/s (1.085–3.202; 0.009–56.295) | 1.780 m/s (1.125–3.325; 0.010–27.887) |
| Directness $Q$ | 0.987 (0.962–0.997; 0.015–1.000) | 0.981 (0.956–0.993; 0.024–1.000) |
| Cumulative turning | 31.16° (13.05–61.82; 0–953.76) | 42.21° (26.80–70.19; 0–825.44) |

The lower median directness and greater median turning are expected consequences of retaining directionally richer intervals. They also show that v2 is not merely a fewer-episodes result.

## Frozen visual cases

- **Away 24, 380.20–385.04 s:** the original coherent interval remained exactly valley-bounded, with no added direction boundary. The trajectory remained one continuous, direct movement.
- **Home 6, 95.32–146.48 s:** v2 placed a 142.08° direction boundary at 95.36 s, satisfying the frozen check that the complete original interval no longer remained one episode. However, the following episode still lasted **51.12 s** (95.36–146.48 s). The pathological long-duration problem therefore substantially persisted rather than being solved.
- **Home 10, 116.44–117.68 s:** Candidate A preserves the historical discontinuity-containing interval for exact reproduction. Candidate B excluded every episode intersecting the prospectively frozen raw-support break at frames 2911–2945; no v2 episode crossed it.
- The eight deterministic chronological examples showed the frozen valley/direction rules without post-result selection. Several straight or gently curving baseline pieces merged, while visible direction boundaries were retained where the fixed 45° rule qualified.

The visual checks passed mechanically. Visual appeal did not determine classification.

## Classification and counterevidence

All frozen COHERENT conditions passed: valid execution, exact baseline reproduction, material fragmentation reduction, merging/direction below 3.97%, preserved lower-speed coverage, all three fixed-case checks, minimum duration, finite geometry, and support handling.

The strongest permitted claim is:

> A prospectively frozen direction-aware attacker-only segmentation reduced the severe fragmentation of the closed speed-valley baseline while remaining below the frozen merging/direction safety cap on development Game 1.

The strongest counterevidence is that long episodes increased from 141 to 288 and the maximum remained approximately 51 seconds. The composite safety gate passed because direction-complex and low-directness counts declined enough relative to the episode denominator, not because long merging disappeared. The Home 6 counterexample shows this directly. **COHERENT therefore means that the prospectively frozen development gates passed; it does not mean segmentation is solved, optimal, or ready for tactical interpretation.**

## QC and artifacts

All 11 hard checks passed. Focused synthetic angle, direction-candidate, support-break, frozen-constant, and firewall tests passed. A complete independent rerun reproduced all eight governed machine-readable outputs and the audit figure byte-for-byte.

Machine-readable outputs are in `outputs/attacker_movement_episode_v2_game1/`; the frozen visual audit is in `figures/attacker_movement_episode_v2_game1/`.

Unsupported interpretations include tactical run type, optimal boundaries, defender response, opponent influence, causation, drag, pin, stretch, success, gravity, and attacking value.
