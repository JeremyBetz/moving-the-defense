# Phase 4B Held-Out Focal-Departure Validation

## Scope and outcome

Phase 4B executed protocol v1.0 without changing the primitive, sample, eligibility, activity cuts, windows, smoothing, controls, or sensitivities. Metrica Sample Game 1 remained development/history and Sample Game 2 was inspected once as the held-out match after the outcome-blind firewall passed.

The result is positive at a deliberately narrow level: **focal-relative path is a reproducible geometric primitive under the frozen tests**. This does not validate meaningful defensive reconfiguration. It does not identify an opponent response, responsibility, attention, tactical intent, tactical error, quality, or attacking value.

## Outcome-blind firewall

Checksums and schema matched the frozen configuration. The five-second grid reproduced 1,158/1,127 intervals in Games 1/2. Eligibility reproduced 422/407 intervals and 4,220/4,070 defender-interval observations. Game 1 attrition was 273 possession changes, 413 incomplete ball intervals, 43 restarts, and seven intervals without prior possession; Game 2 attrition was 256, 421, 43, and zero. Defending-team support was 198 Away/224 Home in Game 1 and 217 Away/190 Home in Game 2. The smallest frozen 3×3 cell contained 74/75 observations, 25/21 defenders met the 50-interval secondary minimum, and misaligned-reference support reproduced 378/366 intervals.

All four Game-1-derived activity cuts reproduced exactly. The focal-observation terciles use the frozen linear quantiles; the three interval-level cuts correspond to the frozen nearest observed order statistics. This interpolation convention was recovered from the already-frozen values before any Game 2 focal-relative outcome was constructed.

### Pre-outcome implementation-resolution audit

The protocol freezes exact cut values and makes the configuration authoritative, but does not name quantile interpolation methods. Recomputing the Game 1 conditioning quantities before outcome construction showed that the focal-observation cuts exactly equal linear terciles over 4,220 focal observations, whereas the centroid, aggregate-defender, and ball cuts exactly equal nearest observed tercile order statistics over 422 intervals. Using those methods is therefore reproduction of the frozen constants, not selection based on Game 2 and not a protocol change. No Game 2 focal-relative coordinate, path, distribution, cell result, or contextual relationship had been constructed when this was resolved.

The phrase “0.5 pooled within-cell IQR” also lacks a named pooling formula. Before held-out outcomes were constructed, it was operationalized as the IQR of the combined Game 1 and Game 2 observations inside each already-frozen activity cell. This is the most literal empirical-distribution reading of “pooled within-cell IQR”: pool the two within-cell samples, then calculate their IQR. It necessarily uses Game 2 outcomes to evaluate the prospectively frozen cross-match compatibility criterion, just as the Game-2-minus-Game-1 median difference does; it does not use those outcomes to choose the cell definitions, multiplier, required cell count, or pooling rule. It is therefore an implementation clarification, not an outcome-tuned threshold or protocol deviation. Because IQR has no unique canonical pooled estimator, this clarification is recorded explicitly and no alternative definition was tested against Game 2.

## Primary distribution and frozen replication

The five-second, seven-frame focal-relative path distribution was similar across matches:

| Match | n | p10 | p25 | median | p75 | p90 | IQR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Game 1 | 4,220 | 2.509 m | 3.735 m | 5.489 m | 8.138 m | 11.299 m | 4.404 m |
| Game 2 | 4,070 | 2.805 m | 3.890 m | 5.653 m | 8.136 m | 10.885 m | 4.246 m |

All nine frozen focal-absolute-path × full-centroid-path cells met the compatibility rule; seven were required. Absolute Game-2-minus-Game-1 cell-median differences ranged from 0.005 to 0.837 m and were no greater than half the pooled within-cell IQR in every cell. Interval-cluster bootstrap intervals are reported in the executed outputs. The largest point difference occurred in the high-focal/middle-collective cell (−0.837 m; bootstrap 95% interval −1.562 to 0.001 m), which still met the frozen effect-size rule.

The separately reported activity relationships retained their direction:

| Activity quantity | Game 1 Spearman $\rho$ | Game 2 Spearman $\rho$ |
|---|---:|---:|
| Focal absolute path | 0.541 | 0.462 |
| Full defending-outfield centroid path | 0.340 | 0.241 |
| Sum of defending-outfield paths | 0.409 | 0.333 |
| Ball path | 0.315 | 0.185 |

Period, possession-team, defending-team, aggregate-activity, ball-activity, within-interval, and eligible-defender summaries are retained as separate descriptive tables. They show context and player heterogeneity, not roles or tactical effects.

## Generic activity: what the test does and does not establish

Focal-relative path is positively related to every frozen activity quantity, so ordinary passage activity remains a strong alternative explanation. It is not almost completely determined by focal absolute path under the frozen falsifier: $\rho=0.541$ in Game 1 and $0.462$ in Game 2, far below the pre-specified $|\rho|\geq0.95$ condition. The 3×3 conditional pattern and the separate activity relationships also reproduced without sign reversal.

Under these frozen descriptive tests, the quantity therefore contains reproducible variation not reducible to any one reported activity scalar. Focal departure is not equivalent to generic activity, but it remains substantially associated with generic activity. That is weaker than an activity-free effect: no residual model, causal adjustment, or tactical comparator was specified. The correct claim is reproducible focal-versus-collective geometry with stable activity-context structure, not meaningful movement beyond all forms of generic activity.

## Negative controls

Applying one observed collective translation trajectory identically to defenders at fixed relative positions produced a maximum focal-relative path of $1.3\times10^{-12}$ m, passing the numerical invariance check.

The similarly active but temporally misaligned collective reference greatly increased relative path. Median contemporaneous/misaligned values were 5.396/12.058 m in Game 1 and 5.640/13.705 m in Game 2. The misaligned value was larger for 86.7% and 92.5% of supported observations, respectively; median paired increases were 5.344 and 6.894 m. This supports the narrower conclusion that contemporaneous focal-versus-collective geometry contains information beyond movement magnitudes alone. The control is not a tactical null and does not establish coordination, synchronization, responsibility, defensive organization, or other tactical meaning.

## Frozen sensitivities

All nine 4/5/6-second × 5/7/9-frame settings preserved the qualitative result. Game 2 medians remained modestly above Game 1 medians at every setting. Focal-absolute-path correlations remained positive and moderate: 0.506–0.585 in Game 1 and 0.435–0.472 in Game 2. Wider smoothing windows reduced path magnitudes slightly without changing the conclusion.

## Claim boundary

Phase 4B establishes that accumulated movement relative to the leave-one-out defending-outfield centroid is reproducible across these two sample matches and is not mathematically equivalent to focal absolute activity or shared translation. It remains a geometric measurement under validation beyond this dataset. Phase 4B does **not** validate defensive relational reconfiguration, opponent induction, semantic defensive response, tactical quality, gravity, or off-ball value.

## Reproducible artifacts

The executed notebook is `notebooks/phase4b_focal_departure_heldout_validation.ipynb`. The implementation is `src/phase4b_focal_departure_validation.py`. Machine-readable tables are under `outputs/phase4b/`; figures are under `figures/phase4b/`.
