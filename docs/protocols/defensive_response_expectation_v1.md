# Defensive Response Expectation v1

**Status:** frozen prospectively before protected prediction results

**Design date:** 2026-09-03

**Starting commit:** `7cba86a9bb05e513f357761bde149cb19f8dae0b`

## 1. Football question and boundary

Can the ordinary geometric defensive response to attacking movement be predicted from movement and spatial context, and does knowing which side is defending add material predictive information beyond those factors?

The observable object remains geometry. At most, this design can show that defensive-response geometry contains a repeatable **match-specific** component beyond the modeled movement and spatial context. It cannot identify tactical intent, marking assignments, man-oriented or zonal defending, attacker causation, disruption, quality, gravity, or value. “Team” identifies an observed defending side; it is not a tactical label.

## 2. Data and prospective claim level

Use exactly the seven governed IDSSE/Sportec matches `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, and `J03WR9`, through the validated Kloppy/provider adapter. Inherit the [Concurrent Defensive Coordination Form v1](concurrent_defensive_coordination_form_v1.md) support, filtering, ranking, restart, goalkeeper, complete-ten-defender, time, and no-interpolation rules. No new dataset and no Metrica Sample Game 3 access are allowed.

Ten unique defending-team IDs occur across 14 match-side appearances. Only `DFL-CLU-00000P` repeats, in five matches; the other nine appear once. The primary design therefore tests temporal repeatability of a defending side **within its match**, not stable team identity across matches. A separately declared, nonclassifying leave-one-match-out check uses the one repeated team. No general team-style claim is available from this schedule.

## 3. Unit and outcome

One row is one eligible focal-attacker anchor with one complete D1–D10 defender vector. The primary observed outcome is

$$
Y_i=\frac{AARD_{D2,i}+AARD_{D3,i}}{2}
-\frac{AARD_{D4,i}+AARD_{D5,i}+AARD_{D6,i}+AARD_{D7,i}}{4},
$$

in m/s, using the frozen 1.0 Hz attacker-aligned defender-relative velocity (`AARD_vel`). This is the observed local-versus-middle directional response underlying the externally replicated contrast. It is not a previously estimated coefficient and it does not use D1 to rescue or define the target.

Football interpretation: for the same attacker and fixed window, $Y_i$ describes whether movement within the defensive unit aligned with the attacker's direction more among D2–D3 than D4–D7. It does not say why anyone moved.

## 4. Eligibility and common sample

In addition to inherited coordination-form eligibility, require finite construction of every E0/E1/E2 feature and an observed ball coordinate at the anchor. Use the identical retained rows and folds for all model comparisons. No imputation or interpolation is allowed.

Each match must retain at least 1,000 common rows and at least 90% of otherwise outcome-eligible coordination-form rows. A defending side contributes to a fold only with at least 100 training rows and 25 test rows; otherwise its test rows are excluded identically from E0/E1/E2 and recorded. Falling below a match or retention gate makes execution invalid rather than motivating a changed feature set.

## 5. Coordinate conventions

All geometry remains in metres. Longitudinal signs are standardized by the governed period attacking-direction registry: positive points toward the attacking team's goalward direction. Lateral context uses absolute offset because left/right tactics are not modeled. Defensive depth is max-x minus min-x and width is max-y minus min-y over the ten defending outfield players at the anchor.

## 6. Frozen model ladder

All models include an intercept, six lexical treatment-coded match indicators, and seven match-specific period-2 indicators. Continuous columns are standardized from the training fold only using its mean and population standard deviation (`ddof=0`). A training-zero-variance column is removed identically from all models in that fold and logged. Ordinary least squares uses `numpy.linalg.lstsq`; no regularization, tuning, selection, or nonlinear model is allowed. Every training design must have full column rank.

### E0 — attacker movement

- concurrent attacker path;
- prior attacker path.

E0 asks how much response geometry is predictable simply from how much the attacker moved now and immediately beforehand.

### E1 — movement plus spatial/football context

Add exactly:

- mean D2–D3 and mean D4–D7 anchor distance;
- prior mean D2–D3 and mean D4–D7 focal-relative path;
- prior defensive-centroid path;
- prior mean absolute path of all ten defenders;
- attacker-minus-defensive-centroid longitudinal and absolute lateral position;
- defending-unit depth and width;
- ball-minus-defensive-centroid longitudinal and absolute lateral position.

E1 is the frozen expected-response model. It remains model-light: no formation, event sequence, pitch control, learned embedding, possession value, or role/assignment label enters.

The exploratory response residual is $Y_i-\widehat Y_{E1,i}$. Positive means more local attacker-aligned response than E1 predicted; negative means less. It is not disruption, influence, gravity, quality, or value.

### E2 — defending-side increment

`E2a` adds seven within-match defending-side intercept indicators to E1, one per match using the lexical first side as reference. `E2b`, the primary defense-specific model, additionally adds seven within-match defending-side-by-concurrent-attacker-path deviations. This is one intercept and one core movement slope contrast per match, not dozens of contextual interactions.

E2's primary comparison is E2b versus E1. E2a is a prespecified mechanism comparator; the better E2 variant is not selected after results.

## 7. Blocked validation

### Primary: leave-contiguous-block-group-out

Within each match, construct unique `(period, floor(time_period_s/60))` blocks, sort by period then block, and assign block index $i$ among $B$ blocks to fold $\min(\lfloor5i/B\rfloor,4)$. In each of five folds, test the corresponding contiguous temporal group and train on the other four groups pooled across all matches. Exclude from training the immediately adjacent 60-second block on each test boundary within the same period. All observations sharing an anchor remain together.

Each eligible observation is predicted once. This asks whether a match-side pattern learned in separated portions of the same match predicts another portion. It does not establish between-match team stability.

### Secondary: early-to-later

For test folds 1–4, train only on strictly earlier fold groups with the same one-block embargo. This expanding-window check is descriptive and nonclassifying.

### Secondary: repeated team

For `DFL-CLU-00000P`, leave out each of its five matches in turn, estimate that team's intercept and current-attacker-path deviation from the other four matches, and evaluate only its rows in the heldout match. One repeated team cannot support a general team claim; this check is nonclassifying regardless of direction.

## 8. Metrics and materiality

The primary metric is equal-match macro heldout MAE in m/s: compute MAE within each match, then average the seven match MAEs. Also report observation-weighted MAE, per-match MAE, and RMSE. For nested models report

$$
100\frac{MAE_{baseline}-MAE_{model}}{MAE_{baseline}}.
$$

Report E1 versus E0 descriptively. E2b versus E1 is the classification comparison.

A material E2 increment requires at least **3.0%** macro-MAE improvement and lower E2b MAE in at least **6 of 7** matches. Three percent matches the project's earlier prospectively frozen adjacent-step materiality scale; the match-direction rule prevents one match or sample size from driving the claim. This is a scientific materiality rule, not a universal football threshold.

## 9. Paired uncertainty

Create one heldout prediction ledger. Use 2,000 deterministic paired hierarchical bootstrap replicates with seed `20260903`: resample matches, then resample heldout match-period 60-second blocks within each selected match, preserving every observation sharing a block/anchor. For each replicate calculate the macro absolute-MAE improvement $MAE_{E1}-MAE_{E2b}$ and relative improvement. Use two-sided 95% percentile intervals and require at least 1,900 valid replicates. Never iid-resample rank rows or observations.

## 10. Negative control

Retain E2a as the intercept-only mechanism comparison. Separately generate 200 deterministic label controls with seed `20260904`. Within each match-period, circularly shift defending-side labels by a randomly selected nonzero number of 60-second blocks, preserving anchor groups and label frequency. Refit the unchanged E2b ladder and validation for every shift. The control passes only if observed E2b-versus-E1 relative improvement exceeds the 95th percentile of the shifted-label improvements. No control is selected after inspection.

## 11. Classification

- **INVALID:** hard-QC/fold failure; fewer than 1,900 valid bootstrap replicates; any match below 1,000 common rows; common retention below 90%; or a rank-deficient frozen training design.
- **NOT SUPPORTED:** valid E2b macro improvement is at or below zero, or no more than three of seven match MAEs improve.
- **SUPPORTED:** E2b improves at least six of seven match MAEs; macro relative improvement is at least 3.0%; the paired 95% interval for $MAE_{E1}-MAE_{E2b}$ is strictly above zero; and the shifted-label control passes.
- **MIXED:** every other valid result with positive macro improvement and at least four of seven improving matches.

The only formal status is for a **match-specific defensive-response component**. Stable team-specific identity cannot be classified from this schedule.

## 12. Secondary descriptions

After classification, report but do not classify: signed and absolute E1 residual distributions by match/side; broad longitudinal thirds; D1 response minus the D2–D3 mean; E2a versus E2b; early-to-later performance; and the repeated-team leave-one-match-out result. Do not cluster responses, name archetypes, or search match context.

## 13. Failure conditions and prohibitions

Stop invalid rather than alter the design if feature support, temporal folds, model rank, bootstrap support, or deterministic reproduction fails. Do not tune features, thresholds, interactions, regularization, folds, embargo, controls, or status logic after outcomes. No random forest, boosting, neural network, sequence model, automated feature selection, tactical annotation, event-value model, Game 3 access, or new dataset is permitted.

## 14. Planned governed outputs

Persist a manifest, sample and fold ledgers, heldout predictions, error tables, model comparisons, bootstrap results, shifted-label controls, secondary descriptions, hard QC, governed hashes, independent reproduction record, figures, and a bounded result report. Observation-level licensed-provider derivatives remain local-only under repository policy; publish compact aggregates and hashes.

All governed machine-readable outputs must reproduce byte-for-byte before closure.
