# Spatial Defensive-Response Footprint v1 — Game 2 Held-Out Result

**Status:** governed held-out measurements, **descriptively unclassified**. The frozen protocol does not define a standalone Game 2 coherent/mixed/invalid status.

## Result

Untouched Metrica Sample Game 2 reproduced the Game 1 spatial distinction under the unchanged protocol. The association between preceding attacker path and subsequent defender-relative path was $N=0.14967$ m/m for D1–D3, $M=0.06415$ for D4–D7, and $F=0.05853$ for D8–D10. The frozen near-minus-middle contrast was $\Delta_{NM}=0.08553$, 97.5% interval [0.02917, 0.15786]; middle-minus-far was $\Delta_{MF}=0.00562$, interval [-0.03782, 0.03612]. These are observational geometric associations, not evidence of assignment, tactics, influence, or causation.

## Firewall and chronology

The authorized execution began from commit `0670729195fcdc3850e3a7ee186344a6f3fb4913` with a clean, synchronized tree. The protocol, configuration, and prospective execution-clarification SHA-256 values were respectively `649c40c551d880f5204f6ccca7e37cf219660c4a5fdea590e0b73b6377534458`, `b784b3839146a424acd427a0f1d99959f3ef547039743d30ce90e39f9e557c9c`, and `60678b0f90128c5905ed2535a81aab37b562fe8a6b8aa6a9c9ff1f7642dcf37e`. Closed bridge and Game 1 footprint artifacts were unchanged; no Game 2 footprint output existed; Game 3 was not accessed.

Game 2 outputs were saved and hashed before Game 1 comparison or pooled construction. The first result observation exposed missing pre-required reporting artifacts: rank-level placebo, paired-placebo, near/far reconstruction, prescribed robustness, and complete hard-QC serialization. Adding those artifacts changed no sample, estimate, model, metric, threshold, contrast, bootstrap rule, control, horizon, or classification criterion. The complete sequence was then regenerated and independently reproduced.

## Sample

- 1,087 eligible attacker-anchor observations at 115 unique times; 10,870 complete defender rows.
- Period counts: 849 in period 1 and 238 in period 2.
- Attacking-team counts: Home 697; Away 390.
- Simultaneous attackers: median 10, IQR 1, range 7–10.
- Four-second support: 1,070 anchors.
- Every anchor contained D1–D10 exactly once; ten unique defending outfield players were retained and goalkeepers were excluded.
- Exclusion ledger: 5,635 unavailable attacker exposures; 39 unavailable full attacker-support cases; 7,643 incomplete ten-defender cases; 2,563 restart/ball-out-span cases. Categories occur at governed candidate units and are not one additive attrition denominator.

## Rank-distance geometry and primary coefficients

| Rank | Median distance (m) | IQR | p10–p90 | Adjacent overlap | Coefficient (m/m) | 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| D1 | 5.84 | 5.50 | 2.19–12.91 | 0.591 | 0.18711 | [0.15289, 0.23947] |
| D2 | 11.09 | 7.52 | 5.69–18.95 | 0.743 | 0.16860 | [0.10970, 0.22925] |
| D3 | 14.82 | 8.76 | 8.76–24.51 | 0.825 | 0.09331 | [0.02849, 0.17226] |
| D4 | 18.25 | 9.69 | 10.70–27.52 | 0.807 | 0.08376 | [0.02041, 0.14801] |
| D5 | 21.15 | 9.86 | 13.21–30.63 | 0.822 | 0.06757 | [0.01472, 0.12264] |
| D6 | 24.31 | 10.52 | 15.67–34.24 | 0.830 | 0.06695 | [0.02191, 0.10962] |
| D7 | 27.35 | 10.61 | 18.30–36.89 | 0.826 | 0.03830 | [-0.03994, 0.11883] |
| D8 | 30.67 | 10.82 | 20.61–39.83 | 0.826 | 0.05421 | [-0.01030, 0.11546] |
| D9 | 34.05 | 12.23 | 23.06–44.30 | 0.816 | 0.05899 | [-0.01295, 0.16252] |
| D10 | 37.89 | 12.16 | 25.40–49.24 | — | 0.06238 | [-0.04150, 0.17667] |

Every interval used 2,000/2,000 valid grouped bootstrap replicates.

## Frozen contrasts and controls

| Estimand | Estimate | Frozen 97.5% interval | Contrast result |
|---|---:|---:|---:|
| D1–D3 ($N$) | 0.14967 | [0.09505, 0.21466] | descriptive |
| D4–D7 ($M$) | 0.06415 | [0.00843, 0.12547] | descriptive |
| D8–D10 ($F$) | 0.05853 | [-0.01342, 0.14682] | descriptive |
| $\Delta_{NM}$ | **0.08553** | **[0.02917, 0.15786]** | **PASS** |
| $\Delta_{MF}$ | 0.00562 | [-0.03782, 0.03612] | FAIL |

The reverse-time placebo gave $\Delta_{NM}=0.05476$ [0.01166, 0.09328] and $\Delta_{MF}=0.01687$ [-0.02889, 0.06545]. Paired primary-minus-placebo values were 0.03077 [-0.01446, 0.07465] and -0.01125 [-0.06372, 0.03115]. The placebo is diagnostic and nonclassifying.

The inherited bridge reconstructed local and far coefficients of 0.1342219874 and 0.0647562685, with local-minus-far 0.0694657189. Maximum discrepancy from the governed bridge values was zero at the $10^{-12}$ tolerance.

The frozen 12.198443 m extreme-exposure threshold excluded 4/1,087 anchors (0.368%). Trimmed $\Delta_{NM}=0.08760$ [0.02599, 0.16094] retained sign and 102.42% of magnitude: PASS. Horizon $\Delta_{NM}$ values were 0.04346, 0.08553, and 0.17261 at 1, 2, and 4 seconds; the sign rule passed. Corresponding $\Delta_{MF}$ values were 0.00988, 0.00562, and 0.01029 and also passed the sign rule.

The fixed metric-distance coefficients were 0.17118, 0.10943, 0.08305, 0.05627, -0.01095, and -0.05695 m/m for [0,10), [10,20), [20,30), [30,40), [40,50), and [50,∞) m. This complement is descriptive and nonclassifying.

## Validity and closure

All 28/28 hard scientific checks passed after deterministic reproduction. All governed bootstrap tables contained 2,000/2,000 valid replicates. The Game 2 closure ledger is `outputs/spatial_defensive_response_footprint_game2_final_v1/game2_closed_hashes.json`; its SHA-256 is `c39c59a4c20ff3bdc066df8fcaacf22561c921294495b66866e4929cce588c25`.

The Game 2 result is intentionally not assigned a standalone status. Its role in the final decision is governed only by the [pooled/final report](spatial_defensive_response_footprint_final_v1.md).
