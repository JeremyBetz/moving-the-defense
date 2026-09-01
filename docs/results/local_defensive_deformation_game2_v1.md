# Local Defensive Deformation v1 — Game 2 Held-out Replication

## Status

> **GAME 2 HELDOUT REPLICATION — STANDALONE UNCLASSIFIED**

This Tier-3 execution applied the unchanged Game 1 construct to Metrica Sample Game 2. The governed outputs were saved and hashed, then independently reproduced before Game 1 was reopened for comparison. The prospective addendum defines no standalone Game 2 coherent/mixed/negative status, and no pooled deformation analysis was run.

## Sample and model

The closed Game 2 footprint inventory supplied 1,087 eligible attacker anchors at 115 unique anchor times and 10,870 complete D1–D10 defender rows. Period 1 contributed 849 anchors and period 2 contributed 238; Home and Away contributed 697 and 390. Each anchor retained ten unique defending outfield players with inherited goalkeeper exclusion and complete, uninterpolated support. The four-second subset contained 1,070 anchors. Simultaneous attackers per time had median 10, IQR 9–10, and range 7–10.

Every model used the frozen raw-metre design: intercept, attacker path, focal prior endpoint deformation, and whole-unit prior endpoint deformation.

## Primary result

| Rank | Attacker-path coefficient (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| D1 | 0.13394 | [0.09577, 0.17502] |
| D2 | 0.11647 | [0.05703, 0.16937] |
| D3 | 0.09945 | [0.05382, 0.15072] |
| D4 | 0.08974 | [0.04893, 0.13307] |
| D5 | 0.08517 | [0.04650, 0.12633] |
| D6 | 0.08476 | [0.03726, 0.12788] |
| D7 | 0.08301 | [0.03326, 0.12615] |
| D8 | 0.08032 | [0.03478, 0.11736] |
| D9 | 0.08351 | [0.02711, 0.14267] |
| D10 | 0.07234 | [0.01094, 0.12749] |

| Region/contrast | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| Near D1–D3 | 0.11662 | [0.07162, 0.15475] |
| Middle D4–D7 | 0.08567 | [0.04398, 0.12355] |
| Far D8–D10, descriptive | 0.07873 | [0.03356, 0.12119] |
| Primary near minus middle | 0.03095 | [0.01148, 0.05483] |
| Temporal-control near minus middle | 0.03837 | [0.02628, 0.05152] |
| Paired primary minus control | -0.00742 | [-0.02143, 0.00777] |

The positive primary near-minus-middle contrast and its interval replicated the Game 1 direction. The temporal control was also positive and larger in point estimate; consequently, the prospectively paired primary-minus-control excess was negative and its interval included zero. The timing-specific paired evidence from Game 1 therefore did not replicate in Game 2.

## Robustness and secondary geometry

The four-second near-minus-middle estimate was 0.03844 [-0.00046, 0.08689], preserving the positive point-estimate sign without excluding zero. The frozen 12.198443 m exposure trim removed 4 anchors (0.368%), producing 0.03215 [0.01247, 0.05590] and retaining 103.88% of the untrimmed magnitude.

The descriptive relational-path contrast was 0.03487 [0.01673, 0.05811]. Median endpoint deformation by rank ranged from 2.049 to 2.186 m; relational path ranged from 2.259 to 2.436 m. Signed mean spacing change was negative at every rank (approximately -0.375 to -0.008 m), while median whole-unit endpoint deformation was 2.467 m. These secondary quantities do not classify replication and do not supply tactical meaning.

## Descriptive comparison with Game 1

Both matches showed positive primary near-minus-middle estimates with strictly positive frozen intervals: Game 1 0.02297 [0.01434, 0.03235], Game 2 0.03095 [0.01148, 0.05483]. Both retained positive four-second and trimmed point estimates, and both had positive secondary relational-path contrasts. Their timing-specific paired results differed: Game 1 primary exceeded its temporal control by 0.01162 [0.00231, 0.02047], whereas Game 2 primary minus control was -0.00742 [-0.02143, 0.00777]. The rank patterns were broadly near-high in both matches without requiring monotonicity.

## QC and claim boundary

All 13 hard checks passed. Each of six bootstrap families had 2,000/2,000 valid replicates. An independent complete execution reproduced all 13 governed files byte-for-byte. Frozen protocol, configuration, Game 1 result, closed footprint inputs, and held-out governance hashes passed; Game 3 was not accessed and pooled deformation was not executed.

The strongest permitted held-out statement is:

> In Metrica Sample Game 2, greater preceding attacker movement was associated with greater subsequent defender-to-defender relational change among near defender ranks than among middle ranks, but this near-versus-middle distinction did not exceed the prospectively paired temporal control.

In plain football language, the defenders nearest the attacker showed a stronger spacing-change association than the middle-ranked defenders, but a similar or stronger pattern was already present under the shifted-time control. This is observational geometry. It does not establish causation, reaction, manipulation, stretching, dragging, pinning, tracking, marking, covering, handoff, responsibility, attention, tactical intent, successful space creation, gravity, or attacking value.

Machine-readable Tier-3 outputs are in `outputs/local_defensive_deformation_game2_v1/`.
