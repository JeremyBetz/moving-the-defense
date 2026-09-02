# Attacker Movement Episode v2 — Game 2 Heldout Replication

**Status:** **GAME 2 ATTACKER EPISODE v2 REPLICATION MIXED**

**Execution tier:** Tier 3

**Prospective governance:** [`attacker_movement_episode_v2_game2_replication.md`](../protocols/attacker_movement_episode_v2_game2_replication.md)

## Result in plain language

On untouched Metrica Sample Game 2, the exact frozen direction-aware attacker-only rule reproduced the intended numerical trade-off: fragmentation fell materially, merging/direction stayed below its safety cap, and lower-speed movement coverage remained above its floor. The full heldout status is nevertheless **MIXED**, not supported, because the prospectively selected direction-change audit window contained no protected direction boundary. The numerical result therefore generalizes better than the predeclared boundary-level interpretation check.

This is movement geometry only. It is not a tactical run detector, an optimal segmentation, defensive response, influence, or value.

## Firewall and sample

The pre-result governance commit was `06e8d26`. Frozen Game 1 hashes matched exactly: protocol `5d3b1863...9a7b24`, configuration `f42142f0...3a19a`, result `261e092f...bebd7`, and ledger `d10d5415...a4adc`. No Game 2 v2 output existed before that freeze.

The execution consumed the closed attacker-only Game 2 Stage A support registry without rediscovery or revision: 2,093,028 valid raw player rows in 134 support segments. After inherited stoppage boundaries, centred seven-frame smoothing, and the first velocity row, the sample contained 24 outfield identities, 44 player-periods, 1,290 open-play support blocks, and 1,688,267 supported frames. No interpolation, defender coordinate, defensive outcome, Game 3, IDSSE, or pooled analysis entered.

## Candidate A baseline

Candidate A produced 29,679 episodes.

| Quantity | Minimum | Q1 | Median | Q3 | Maximum |
|---|---:|---:|---:|---:|---:|
| Duration (s) | 1.00 | 1.28 | 1.84 | 2.68 | 33.60 |
| Path (m) | 0.005 | 1.384 | 2.655 | 5.283 | 58.550 |
| Displacement (m) | 0.005 | 1.347 | 2.586 | 5.139 | 55.058 |
| Peak speed (m/s) | 0.007 | 1.148 | 1.691 | 3.140 | 18.159 |
| Directness $Q$ | 0.058 | 0.962 | 0.987 | 0.997 | 1.000 |
| Turning (degrees) | 0.0 | 16.05 | 34.33 | 64.12 | 921.00 |

Baseline fragmentation was 12,597/29,679 = **42.4442%**. Merging/direction was 619/29,679 = **2.0856%**. Lower-speed meaningful-displacement coverage was 12,210/29,679 = **41.1402%**. Long episodes numbered 87 (**0.2931%**), with a 33.60 s maximum.

## Candidate B v2

Candidate B produced 25,579 episodes.

| Quantity | Minimum | Q1 | Median | Q3 | Maximum |
|---|---:|---:|---:|---:|---:|
| Duration (s) | 1.00 | 1.52 | 2.20 | 3.12 | 33.60 |
| Path (m) | 0.008 | 1.530 | 3.168 | 6.243 | 65.252 |
| Displacement (m) | 0.006 | 1.485 | 3.082 | 6.040 | 65.250 |
| Peak speed (m/s) | 0.007 | 1.158 | 1.752 | 3.210 | 18.159 |
| Directness $Q$ | 0.024 | 0.957 | 0.982 | 0.994 | 1.000 |
| Turning (degrees) | 0.0 | 27.64 | 42.84 | 70.74 | 757.09 |

Fragmentation was 7,950/25,579 = **31.0802%**, a **26.7739% relative reduction** from the Game 2 baseline and a pass against the frozen 20% gate. Merging/direction was 632/25,579 = **2.4708%**, passing the **3.97%** cap. Lower-speed meaningful-displacement coverage was 12,011/25,579 = **46.9565%**, passing the **36.8956%** floor.

Long episodes increased from 87 to 134 and from 0.2931% to **0.5239%**; the maximum remained 33.60 s. This known tail remains counterevidence even though it is not a post-hoc failure gate.

## Frozen visual audit

The audit set contained eight equally spaced chronological support cases, plus the first qualifying direct, direction-change, and low-speed own-trajectory windows and the first frozen Stage A discontinuity. It was selected before Candidate B construction. The serialized figure contains only attacker path, speed, heading, and Candidate B boundaries.

The low-speed window overlapped a Candidate B episode, the frozen discontinuity was not crossed, and serialized boundaries were unique. The direction-change window (Away 16, 10.24–14.24 s; path 7.09 m; $Q=0.964$; cumulative reliable turning 105.54°) contained **zero** protected direction boundaries. That prospectively declared objective check failed. It shows that cumulative four-second turning and the v2 sustained pre/post direction-boundary definition are not interchangeable.

## Mechanical classification

| Frozen condition | Result |
|---|---|
| Valid frozen support and implementation | PASS |
| Fragmentation relative reduction ≥20% | PASS: 26.7739% |
| Merging/direction ≤3.97% | PASS: 2.4708% |
| Lower-speed coverage ≥36.8956% | PASS: 46.9565% |
| Objective frozen audit checks | **FAIL** |
| No post-result tuning | PASS |

Under the predeclared decision tree, that combination yields exactly:

> **GAME 2 ATTACKER EPISODE v2 REPLICATION MIXED**

## Post-closure comparison with Game 1

| Quantity | Game 1 v2 | Game 2 v2 |
|---|---:|---:|
| Fragmentation | 28.7596% | 31.0802% |
| Relative fragmentation reduction | 31.8881% | 26.7739% |
| Merging/direction | 2.6498% | 2.4708% |
| Lower-speed coverage | 48.6501% | 46.9565% |
| Median $Q$ | 0.9810 | 0.9820 |
| Median turning | 42.21° | 42.84° |
| Long episodes | 288/31,965 (0.9010%) | 134/25,579 (0.5239%) |
| Maximum duration | 51.12 s | 33.60 s |

The numerical fragmentation/merging/coverage trade-off, median directness, and median turning reproduced closely. The Game 1 fixed-case success did not reproduce under the separate prospectively selected Game 2 direction audit. Long episodes persisted in both matches but were less prevalent and shorter-tailed in Game 2.

## Reproduction and hashes

All **10/10 governed outputs** reproduced byte-for-byte in an independent execution. The governed result hash is `37ef7dde32b1b1bc8305994b75265143dbeda91349d35c32e74e773ae7d69ad3`; the complete file ledger is [`hashes.json`](../../outputs/attacker_movement_episode_v2_game2/hashes.json), and detailed comparisons are in [`reproduction_verification.json`](../../outputs/attacker_movement_episode_v2_game2/reproduction_verification.json).

## Claim boundary

**Supported:** on heldout Game 2, the exact frozen v2 rule materially reduced the historical baseline's fragmentation while keeping the predefined merging/direction diagnostic within its safety bound and preserving lower-speed movement coverage. Across the two Metrica sample matches, those numerical properties were similar.

**Not supported:** complete heldout replication of every predeclared audit requirement; validated tactical runs; optimal or solved segmentation; defender response; attacker influence or causation; tactical movement type; gravity; off-ball value; Game 3, IDSSE, or cross-provider generality.
