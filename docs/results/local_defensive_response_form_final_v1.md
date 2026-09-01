# Local Defensive Response Form v1 — Pooled and Final Result

## Final classification

> **FINAL RESPONSE FORM B**

All Game 1, Game 2, and pooled executions were valid and reproducible, and every primary near-minus-middle interval excluded zero with the same positive sign. Final A nevertheless failed because the Game 2 paired primary-minus-temporal-control interval crossed zero.

## Pooled result

The observation-weighted pooled sample contained 8,885 anchors (7,819 Game 1; 1,066 Game 2), 88,850 defender rows, 8,881 common primary/control anchors, and 8,376 four-second anchors. The governed 41-column model used ten rank-specific intercept/exposure/prior-parallel/prior-centroid blocks and one common additive Game 2 indicator, with no interactions.

| Rank | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| D1 | 0.15680 | [0.12307, 0.18940] |
| D2 | 0.05714 | [0.02887, 0.08764] |
| D3 | 0.03346 | [0.00853, 0.05896] |
| D4 | 0.01983 | [-0.00784, 0.04885] |
| D5 | -0.01301 | [-0.03830, 0.01020] |
| D6 | -0.01203 | [-0.04048, 0.01295] |
| D7 | -0.04694 | [-0.06730, -0.02511] |
| D8 | -0.04718 | [-0.07468, -0.01745] |
| D9 | -0.06092 | [-0.09600, -0.02831] |
| D10 | -0.08495 | [-0.11761, -0.05524] |

| Region/contrast | Estimate (m/m) | Frozen 97.5% interval |
|---|---:|---:|
| Near D1–D3 | 0.08247 | [0.06353, 0.10128] |
| Middle D4–D7 | -0.01304 | [-0.02291, -0.00383] |
| Far D8–D10 (descriptive) | -0.06435 | [-0.08429, -0.04498] |
| Primary near minus middle | 0.09550 | [0.07199, 0.12048] |
| Temporal-control near minus middle | 0.05348 | [0.03180, 0.07783] |
| Paired primary minus control | 0.04192 | [0.01783, 0.06581] |

The temporal control retained directional structure. The qualifying pooled evidence is the prospectively frozen paired excess, not an absence of structure in the control.

Trimming retained the positive sign and 89.12% of the full contrast magnitude (0.08512 versus 0.09550). Horizon estimates were positive at 1 s (0.05963), 2 s (0.09550), and 4 s (0.08977). All six pooled bootstrap families produced 2,000/2,000 valid replicates, and 10/10 governed pooled files reproduced byte-for-byte.

## Frozen criteria

| Final A condition | Result |
|---|---|
| Valid/reproducible Game 1, Game 2, pooled executions | PASS |
| At least 80% attacker-axis retention in both matches | PASS |
| Primary near-minus-middle intervals exclude zero with same sign in all three | PASS |
| Paired excess intervals exclude zero with same sign in all three | **FAIL** — Game 2 interval crosses zero |
| Pooled trim sign and magnitude rule | PASS |
| Pooled horizon-sign rule | PASS |

Because execution remained valid but one scientific condition failed, the frozen decision tree yields **FINAL RESPONSE FORM B**.

## Strongest permitted claim

Across two Metrica sample matches, greater attacker movement was observationally associated with a more positive subsequent defender-relative displacement along the attacker's preceding movement direction among near defender ranks than among middle ranks. The pooled paired excess over the temporal control was positive, but the analogous Game 2 interval crossed zero; directional localization beyond that control therefore did not fully replicate under the frozen Final A rule.

In plain football language: the defenders nearest the moving attacker tended to move more in the same pitch direction than defenders farther into the unit, but the held-out match did not clearly separate that pattern from the predeclared shifted-time comparison.

This does not establish reaction, causation, influence, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoffs, tactical success, player quality, fatigue, gravity, or off-ball value.

Machine-readable outputs are in `outputs/local_defensive_response_form_pooled_final_v1/`.
