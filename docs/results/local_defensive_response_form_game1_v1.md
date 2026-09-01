# Local Defensive Response Form v1 — Game 1 Development Result

**Status:** **GAME 1 RESPONSE FORM DEVELOPMENT COHERENT**

This is the first empirical execution of the [frozen protocol](../protocols/local_defensive_response_form_v1.md). It asks whether defender movement relative to the defensive unit has signed geometric structure along the preceding attacker movement direction. It does not label tracking, marking, reaction, intent, influence, or causation.

## Firewall and sample

The protocol/configuration hashes matched `958c8aa8...9ee80428` and `b120f19c...998b8053`. Closed footprint artifacts were unchanged. Game 2 response-form quantities and Game 3 were not accessed.

The inherited footprint registry contained 7,823 eligible attacker-anchor observations at 804 unique times. Four exact-zero/near-zero attacker displacement axes were excluded under the machine-derived rule, leaving 7,819 anchors (99.9489%), 78,190 complete defender rows, and all D1–D10 ranks exactly once. Period counts were 5,932 and 1,887; attacking-team counts were 4,479 Home and 3,340 Away. Simultaneous attackers had median 10, IQR 9–10, and range 7–10.

Inherited exclusions were: attacker exposure unavailable 4,198; attacker full support unavailable 8; complete ten-defender set unavailable 3,974; restart/ball-out 2,717; and no-possession endpoint 8. The response-form stage added only four invalid-axis exclusions. The paired-control common sample retained 7,818 anchors; the four-second sensitivity retained 7,327.

## Primary attacker-direction result

Coefficients are metres of signed focal-relative endpoint displacement per metre of preceding attacker path. Intervals are frozen 97.5% block-bootstrap intervals; every estimate had 2,000/2,000 valid replicates.

| Rank | Estimate | 97.5% interval |
|---:|---:|---:|
| D1 | 0.16245 | [0.13056, 0.19735] |
| D2 | 0.05292 | [0.02179, 0.08841] |
| D3 | 0.03584 | [0.00944, 0.06213] |
| D4 | 0.01962 | [-0.00918, 0.05181] |
| D5 | -0.01025 | [-0.03550, 0.01306] |
| D6 | -0.01482 | [-0.04335, 0.01446] |
| D7 | -0.04386 | [-0.06816, -0.01978] |
| D8 | -0.04858 | [-0.07788, -0.01874] |
| D9 | -0.06471 | [-0.10404, -0.03149] |
| D10 | -0.08442 | [-0.12109, -0.05094] |

Frozen regions were near 0.08374 [0.06491, 0.10513], middle -0.01233 [-0.02210, -0.00234], and descriptive far -0.06590 [-0.08731, -0.04638]. The sole primary contrast was:

> **Near minus middle: 0.09606 m/m, 97.5% interval [0.07220, 0.12295].**

The curve is irregular and was not smoothed or forced to be monotonic.

## Temporal control and robustness

The frozen temporal-control near-minus-middle estimate was 0.05512 [0.03290, 0.08036]. On the fixed common sample, primary minus control was **0.04085 [0.01784, 0.06436]**, passing the same-direction exclusion rule. The control itself retained directional structure; the qualifying result is the paired difference, not absence of shared/temporally symmetric movement.

Trimming at the inherited 12.198443 m exposure threshold excluded 79 anchors (1.0104%), retained 7,740, and gave near-minus-middle 0.08573 [0.05674, 0.11529]. Sign was retained and magnitude retention was 89.25%.

The frozen one-, two-, and four-second near-minus-middle estimates were respectively 0.06064 [0.04686, 0.07559], 0.09606 [0.07220, 0.12295], and 0.08680 [0.04859, 0.13083]. Neither sensitivity reversed the primary sign. These are cumulative-window checks, not reaction persistence.

## Secondary geometry

Median near/middle/far focal-relative paths were 1.985/1.956/2.010 m; net displacements were 1.835/1.814/1.874 m. Median orthogonal components were 0.0077/-0.0019/-0.0099 m; radial components were 0.0379/0.0450/0.1603 m; and alignment cosines were 0.1189/-0.0371/-0.1630. Sixteen of 78,190 radial rows had an undefined response-start radial axis. These quantities are descriptive and did not classify the result.

Median absolute defender movement was 2.776/2.824/2.753 m across near/middle/far; median leave-one-out centroid movement was 2.195/2.191/2.217 m. Their difference produces the focal-relative endpoint vector, but v1 defines no “hold” or “pin” category and no causal interpretation.

## Frozen criteria

| Criterion | Result |
|---|---|
| Valid execution, hard QC, reproduction, bootstrap support | PASS |
| Primary-axis retention ≥80% | PASS (99.9489%) |
| Primary near-minus-middle interval excludes zero | PASS |
| Paired primary-minus-control interval excludes zero in the same direction | PASS |
| Trim retains sign and ≥50% magnitude | PASS (89.25%) |
| One- and four-second estimates not both opposite the two-second sign | PASS |

Therefore the exact status is **GAME 1 RESPONSE FORM DEVELOPMENT COHERENT**. Under the frozen governance this permits, but does not execute, a later unchanged Game 2 response-form replication.

## Claim boundary and reproducibility

Strongest permitted Game 1 claim:

> In Metrica Sample Game 1 under the frozen observational protocol, attacker-direction-aligned defender-relative movement showed positive near-versus-middle directional structure beyond the paired temporal control.

In plain football geometry, the nearest defenders' movement relative to the rest of their defensive unit contained more movement in the attacker's preceding direction than did the middle-ranked defenders. This does not establish tracking, following, marking, pinning, assignment, reaction, attention, influence, causation, space creation, gravity, or value.

An independent full execution reproduced all 13 governed machine-readable outputs byte-for-byte and the same classification. See [`outputs/local_defensive_response_form_game1_v1/`](../../outputs/local_defensive_response_form_game1_v1/) and the [predeclared figure](../../figures/local_defensive_response_form_game1_v1/response_form_result_template.png).
