# Spatial Defensive-Response Footprint v1 — Pooled and Final Result

**Final classification:** **FINAL FOOTPRINT A**

## Result in one paragraph

The frozen spatial-footprint distinction replicated on untouched Metrica Sample Game 2 and in the prospectively specified pooled analysis. Across 8,910 attacker-anchor observations, the association between preceding attacker path and subsequent defender movement relative to the defensive unit was $N=0.11327$ m/m for D1–D3, $M=0.06298$ for D4–D7, and $F=0.06204$ for D8–D10. Near-minus-middle was $\Delta_{NM}=0.05029$, frozen 97.5% interval [0.03433, 0.06858], while middle-minus-far was null. The qualifying near-minus-middle contrast excluded zero in Game 1, Game 2, and pooled estimates, had the same positive sign, and passed pooled robustness; therefore it met every prospectively frozen Final A condition.

## Pooled footprint

| Rank | Coefficient (m/m) | 95% interval |
|---|---:|---:|
| D1 | 0.15890 | [0.13589, 0.18211] |
| D2 | 0.09839 | [0.07562, 0.12142] |
| D3 | 0.08252 | [0.06287, 0.10411] |
| D4 | 0.08529 | [0.06468, 0.10909] |
| D5 | 0.04963 | [0.03012, 0.06881] |
| D6 | 0.06099 | [0.03847, 0.08364] |
| D7 | 0.05602 | [0.03443, 0.07738] |
| D8 | 0.04794 | [0.02274, 0.07222] |
| D9 | 0.07142 | [0.04574, 0.10115] |
| D10 | 0.06676 | [0.03715, 0.09718] |

![Held-out and pooled rank footprint](../../figures/spatial_defensive_response_footprint_game2_final_v1/rank_footprint.png)

| Region/contrast | Estimate | Frozen 97.5% interval |
|---|---:|---:|
| D1–D3 ($N$) | 0.11327 | [0.09261, 0.13347] |
| D4–D7 ($M$) | 0.06298 | [0.04543, 0.08132] |
| D8–D10 ($F$) | 0.06204 | [0.03608, 0.08882] |
| $\Delta_{NM}$ | **0.05029** | **[0.03433, 0.06858]** |
| $\Delta_{MF}$ | 0.00095 | [-0.01906, 0.02145] |

Every interval used 2,000/2,000 valid match/period-block bootstrap replicates.

## Controls and robustness

The pooled reverse-time placebo was $\Delta_{NM}=0.02117$ [0.00936, 0.03332] and $\Delta_{MF}=0.01035$ [-0.00598, 0.02626]. Paired primary-minus-placebo was 0.02912 [0.01410, 0.04526] for $\Delta_{NM}$ and -0.00940 [-0.02471, 0.00591] for $\Delta_{MF}$. The placebo remains diagnostic rather than independently classifying.

The frozen trim excluded 83/8,910 anchors (0.932%). Trimmed $\Delta_{NM}=0.04463$ [0.02716, 0.06373], preserving sign and 88.74% of magnitude: PASS. Pooled horizon $\Delta_{NM}$ values were 0.02916, 0.05029, and 0.07566 at 1, 2, and 4 seconds; $\Delta_{MF}$ values were 0.00054, 0.00095, and 0.01220. Both passed the governed sign rule.

The pooled fixed-band complement declined descriptively from 0.12796 m/m at [0,10) m to 0.00422 at [50,∞) m, without imposing monotonicity or contributing to classification.

## Game 1 and Game 2

Both matches show the same stepped distinction: the nearest three ranks have a stronger attacker-path association than the middle four, while middle and far regions are similar. Game 1 $\Delta_{NM}=0.04559$ [0.02979, 0.06428]; untouched Game 2 $\Delta_{NM}=0.08553$ [0.02917, 0.15786]. Game 2 has wider intervals because its governed sample is smaller (1,087 versus 7,823 anchors). Rank-level shapes are irregular in both matches and do not establish smooth distance decay. The temporal placebo retains some spatial pattern in both; the paired primary-minus-placebo near-minus-middle result excludes zero pooled but not in Game 2 alone. These differences are reported directly and do not alter the frozen decision rule.

## Frozen Final A/B/C evaluation

| Contrast | Game 1 excludes zero | Game 2 excludes zero | Pooled excludes zero | Same nonzero sign | Pooled robustness | Qualifies Final A |
|---|---:|---:|---:|---:|---:|---:|
| $\Delta_{NM}$ | PASS | PASS | PASS | PASS | PASS | **YES** |
| $\Delta_{MF}$ | FAIL | FAIL | FAIL | PASS | PASS | NO |

At least one contrast—$\Delta_{NM}$—satisfies all original frozen Final A conditions. The resulting classification is exactly **FINAL FOOTPRINT A**. No Game 2-only status was created.

## Interpretation boundary

**Strongest permitted claim:**

> Across the two Metrica sample matches under the frozen observational protocol, greater preceding attacker movement was associated with greater subsequent defender movement relative to the defensive unit, and that association was reproducibly stronger across the three nearest defender ranks than across the four middle ranks.

In plain football language: when an attacker moved more during the governed exposure interval, nearby defenders subsequently tended to move differently from the rest of their defensive unit by a larger amount than middle-ranked defenders did. This is a reproducible spatial association, not an explanation of why anyone moved.

Game 1 supplied prospective development evidence; untouched Game 2 supplied the held-out match comparison; the pooled model estimated the shared two-match pattern with match adjustment. None establishes causation, influence, attention, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoffs, space creation, tactical success/failure, player quality, fatigue, energy efficiency, gravity, or off-ball value.

## Reproducibility and provenance

Game 2 governed outputs were saved and hashed before Game 1 comparison or pooled construction. After reporting-only serialization was completed, an independent full rerun reproduced all **31/31 governed files byte-for-byte**, including the final classification. Game 2 and pooled hard-QC ledgers each passed **28/28 checks**; all bootstrap validity counts were 2,000/2,000. Protocol, configuration, clarification, closed bridge, and Game 1 scientific hashes remained unchanged. Game 3 was not accessed.

Machine-readable results are under `outputs/spatial_defensive_response_footprint_game2_final_v1/`. The final-results SHA-256 is `239b0cad626b156bc0a91c6f8e1fb673e28330ad56f00deb8c3a9ecd4c169b85`; the final hash ledger records every governed artifact.
