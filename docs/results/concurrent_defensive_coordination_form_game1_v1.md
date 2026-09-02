# Concurrent Defensive Coordination Form v1 — Game 1 Development Result

## Status

**GAME 1 COORDINATION FORM DEVELOPMENT COHERENT**

This is the first governed execution of the [prospectively frozen protocol](../protocols/concurrent_defensive_coordination_form_v1.md) on Metrica Sample Game 1. Protocol SHA-256: `3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032`. Configuration SHA-256: `d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3`. Neither frozen artifact changed during execution.

## Sample and exclusions

- Eligible focal observations: **8,261** (**82,610** defender-rank rows)
- Unique anchor times: **849**
- Period 1 / period 2 observations: **6,276 / 1,985**
- Exclusions: attacker continuous edge support **4,451**; complete ten-defender continuous edge support **4,162**; restart/ball-out span **1,846**; unavailable possession team **9**

Every retained observation contains one fixed rank for each of ten unique defending outfield players, complete continuous support with the frozen two-second physical edge margin, and no interpolation.

## Primary result

| Rank | 1.0 Hz coefficient | 1.5 Hz sensitivity |
|---:|---:|---:|
| D1 | 0.09878 | 0.09801 |
| D2 | 0.03783 | 0.03732 |
| D3 | 0.02533 | 0.02533 |
| D4 | 0.00965 | 0.00953 |
| D5 | -0.00680 | -0.00684 |
| D6 | -0.02151 | -0.02138 |
| D7 | -0.01682 | -0.01685 |
| D8 | -0.03120 | -0.03083 |
| D9 | -0.03580 | -0.03543 |
| D10 | -0.02269 | -0.02226 |

At 1.0 Hz, mean D2–D3 was **0.03158**, mean D4–D7 was **-0.00887**, and the frozen primary contrast was **0.04045**, with 95% paired block-bootstrap interval **[0.02366, 0.05538]**. All **2,000** paired bootstrap replicates were valid. At 1.5 Hz, the corresponding contrast was **0.04021**, with interval **[0.02341, 0.05502]**. The nonclassifying D1-minus-D4–D7 benchmark was **0.10765**, with interval **[0.08352, 0.13219]**.

## Secondary geometry

The absolute-coordinate aligned comparator retained a positive D2–D3-minus-D4–D7 contrast (**0.03673**). The cross-axis contrast was **-0.00231**, and the descriptive deformation contrast was **-0.00294**. The raw/secant and historical seven-frame comparators produced primary-like contrasts of **0.03999** and **0.04032**. These are contextual descriptions, not classification evidence.

Four observations (40 rank rows) had zero paths that made the nonclassifying raw and seven-frame comparator outcomes undefined. Those rows were omitted only from those comparator fits; the frozen 1.0/1.5 Hz common sample and classification were unchanged. A positive-form naming correction to the access-firewall QC assertions fixed reporting logic only and changed no scientific value or rule.

## Frozen classification audit

| Criterion | Result |
|---|---|
| Execution and hard QC valid | PASS |
| At least 1,900 paired-valid bootstrap replicates | PASS — 2,000 |
| Primary 1.0 Hz contrast > 0 | PASS — 0.04045 |
| Primary 95% interval strictly > 0 | PASS — [0.02366, 0.05538] |
| 1.5 Hz primary estimate > 0 | PASS — 0.04021 |

The frozen result is therefore **GAME 1 COORDINATION FORM DEVELOPMENT COHERENT**.

## Interpretation boundary

Within this frozen Game 1 development analysis, attacker-aligned defender-relative velocity was more strongly associated with D2–D3 than with D4–D7, consistent with directional localization extending beyond the nearest defender. The substantially larger D1 benchmark also shows a strong nearest-defender component, so the result does not imply uniform coordination across nearby defenders.

This is observational concurrent geometry. It does not establish causation, reaction, attention, marking, assignment, responsibility, tactical success, space creation, gravity, or attacking value. Game 2, Game 3, and IDSSE coordination-form outcomes were not inspected.

## Reproducibility

An independent full rerun reproduced all eight governed machine-readable files byte-for-byte, and the governed hash ledger itself was byte-identical. All 14 hard-QC assertions passed. Result JSON SHA-256: `8c9bc473826966ee2999adf14fda9a30fe630a5a7c5830da261d5020737b985e`. Observation table SHA-256: `193f61ff74b392a919c8470a09081079c8cc3e2f6c20700e5cad1cd44b844be0`.
