# Concurrent Defensive Coordination Form v1 — Game 2 Replication

## Formal status

**GAME 2 COORDINATION FORM REPLICATION MIXED**

The [heldout status rule](../protocols/concurrent_defensive_coordination_form_v1_game2_replication.md) was frozen and hashed before any Game 2 coordination-form result was computed. It changed no scientific setting from the [original protocol](../protocols/concurrent_defensive_coordination_form_v1.md).

## Sample

- Eligible focal observations: **1,143** (**11,430** defender-rank rows)
- Unique anchor times: **123**
- Period 1 / period 2 observations: **887 / 256**
- Exclusions: attacker continuous edge support **6,078**; complete ten-defender continuous edge support **8,097**; restart/ball-out span **1,711**; numerical zero attacker path **12**

Every retained observation contained ten unique defending outfield players and one fixed D1–D10 vector, complete physical edge support, finite model rows and outcomes, and no interpolation.

## Frozen replication evidence

| Rank | 1.0 Hz coefficient | 1.5 Hz sensitivity |
|---:|---:|---:|
| D1 | 0.07305 | 0.07256 |
| D2 | 0.09093 | 0.09226 |
| D3 | -0.01787 | -0.01852 |
| D4 | -0.03037 | -0.03008 |
| D5 | -0.01438 | -0.01458 |
| D6 | -0.01685 | -0.01742 |
| D7 | 0.02420 | 0.02385 |
| D8 | -0.01424 | -0.01447 |
| D9 | 0.00120 | 0.00139 |
| D10 | -0.01213 | -0.01159 |

At 1.0 Hz, mean D2–D3 was **0.03653**, mean D4–D7 was **-0.00935**, and the frozen primary contrast was **0.04587**, with 95% paired block-bootstrap interval **[-0.01056, 0.09260]**. All **2,000** paired bootstrap replicates were valid. The 1.5 Hz primary contrast was **0.04643**, with interval **[-0.01038, 0.09358]**.

The execution was valid, the primary point estimate was positive, and the 1.5 Hz sensitivity point estimate was positive. The primary 95% interval was not strictly above zero. The prospectively frozen status is therefore **MIXED**.

The nonclassifying D1-minus-D4–D7 benchmark was **0.08240**, with interval **[0.03771, 0.12860]**.

## Frozen secondary descriptions

- Absolute-coordinate aligned D2–D3-minus-D4–D7: **0.04208**
- Cross-axis contrast: **0.00773**
- Descriptive deformation contrast: **0.02344**
- Raw/secant comparator: **0.04559**
- Historical seven-frame comparator: **0.04618**

Eight observations (80 rank rows) had comparator-specific zero paths and were omitted only from the nonclassifying raw and seven-frame fits. The frozen primary and sensitivity sample was unchanged.

## Post-classification Game 1 comparison

The Game 2 primary point estimate was about **1.13 times** the Game 1 estimate (0.04587 versus 0.04045), but its interval was much wider and crossed zero. The D1 benchmark was smaller than in Game 1 (0.08240 versus 0.10765). D1 was not the largest Game 2 rank coefficient: D2 was larger. D2 was positive while D3 was negative, so the positive D2–D3 mean did not reflect two individually positive ranks. Middle and far ranks were irregular rather than monotonic. Absolute-coordinate, raw, seven-frame, cross-axis, and deformation contrasts were positive descriptively. None of these comparisons changed the frozen **MIXED** status.

## Interpretation boundary

The heldout point direction replicated, but interval support did not fully satisfy the prospective replication criterion. Within Game 2, the estimated attacker-aligned defender-relative velocity contrast was positive for D2–D3 versus D4–D7, but the data remain compatible with no contrast under the frozen interval procedure.

This remains observational geometry. It does not establish causal defender response, reaction latency, attention, marking, assignment, responsibility, attacker-induced movement, tactical success, space creation, gravity, or attacking value. IDSSE coordination-form outcomes and Metrica Sample Game 3 were not inspected.

## Reproducibility

An independent complete rerun reproduced all eight governed outputs byte-for-byte. All 15 hard-QC assertions passed. Final result SHA-256: `11ad4804933995b08928f548d44053889d081378eb7390fafd4bf3b53824d52a`. Observation table SHA-256: `95a26f51241730afd383c83a81866baad3fb88baf2025b62ab0cd6f9f0881456`.
