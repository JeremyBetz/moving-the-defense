# Local Defensive Response Form v1 — Game 2 Replication

**Execution:** Tier 3, frozen protocol/configuration unchanged

**Status:** standalone descriptive; the protocol defines no Game 2-only classification

**Game 3:** untouched

Game 2 retained 1,066 of 1,087 inherited anchors (98.0681%), representing 115 unique anchor times and 10,660 complete D1–D10 defender rows. All six bootstrap families produced 2,000/2,000 valid replicates. The complete governed result reproduced 12/12 files byte-for-byte before any Game 1 comparison or pooled execution.

## Primary directional result

| Rank | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| D1 | 0.11528 | [0.03825, 0.21249] |
| D2 | 0.09196 | [0.02557, 0.16790] |
| D3 | 0.01396 | [-0.06373, 0.07025] |
| D4 | 0.02445 | [-0.06999, 0.11899] |
| D5 | -0.02974 | [-0.11502, 0.04445] |
| D6 | 0.01250 | [-0.05670, 0.10197] |
| D7 | -0.06956 | [-0.11862, 0.00820] |
| D8 | -0.03660 | [-0.13351, 0.07714] |
| D9 | -0.03582 | [-0.09816, 0.05175] |
| D10 | -0.09366 | [-0.13269, -0.06312] |

| Region/contrast | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| Near D1–D3 | 0.07374 | [0.02948, 0.10604] |
| Middle D4–D7 | -0.01559 | [-0.04551, 0.01610] |
| Far D8–D10 (descriptive) | -0.05536 | [-0.09151, -0.02199] |
| Primary near minus middle | 0.08932 | [0.02490, 0.15094] |
| Temporal-control near minus middle | 0.03935 | [-0.04350, 0.11074] |
| Paired primary minus control | 0.04980 | [-0.03936, 0.15903] |

The primary contrast was positive and its interval excluded zero. The paired excess had the same positive point-estimate direction but its interval crossed zero. This failed one condition required later for Final A; it is not a standalone Game 2 status.

## Robustness and secondary geometry

Top-1%-threshold trimming retained 88.06% of the primary contrast magnitude (0.07866 versus 0.08932) and its sign. Near-minus-middle remained positive at 1 s (0.05109), 2 s (0.08932), and 4 s (0.10653), although the four-second interval crossed zero. The frozen sign rule passed.

Prospectively declared path, net, orthogonal, radial, cosine, absolute-defender, and defensive-unit-centroid summaries are preserved in `secondary_geometry_by_rank.csv`. They are descriptive and were not used to classify the result.

## Claim boundary

Game 2 shows a positive observational association between preceding attacker path and subsequent defender movement relative to the unit along the attacker's preceding movement direction, with a stronger near than middle point estimate. It does not establish causation, reaction, influence, marking, assignment, responsibility, attention, tactical success, gravity, or value.

Machine-readable outputs are in `outputs/local_defensive_response_form_game2_final_v1/`.
