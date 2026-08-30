# Phase 5A Contextual-Expectation Feasibility Results

> **Result: A — contextual expectation feasible.** This is a predictive result for a geometric target under frozen protocol v1.0. It does not validate tactical defensive response or give the residual tactical meaning.

## Protocol compliance and support

Execution used the seven frozen IDSSE matches and the exact Phase 4 target. The 44,767 primary common-sample observations reproduced the existing Phase 4C focal-relative paths with maximum absolute difference $1.28\times10^{-12}$ m. Every sample passed the raw-time firewall, 125/119/118 target counts, 50/44/43 history counts, and minimum history-reference membership. The protocol and config hashes are recorded in the [execution manifest](../outputs/phase5a/execution_manifest.json).

The orientation fallback uses each team's goalkeeper median x during the first 50 observed regular frames of the period. This directly implements the frozen config's “first 2 seconds of period tracking” rule; an initial attempt to use the event kickoff timestamp found no frames in one match and stopped before target construction. Population SD (`ddof=0`) and NumPy's standard Ridge linear solve, with deterministic pseudoinverse fallback, are non-material implementation clarifications recorded before outcomes. Every fitted model used the direct solver.

### Primary common-sample attrition

| Match | Phase 4 eligible | Complete 2 s history | Complete ball history | Final B4/common | Retention |
|---|---:|---:|---:|---:|---:|
| J03WMX | 6,949 | 6,948 | 6,948 | 6,948 | 99.99% |
| J03WN1 | 5,436 | 5,436 | 5,436 | 5,436 | 100.00% |
| J03WOH | 6,116 | 6,115 | 6,115 | 6,115 | 99.98% |
| J03WOY | 6,345 | 6,342 | 6,342 | 6,342 | 99.95% |
| J03WPY | 7,077 | 7,074 | 7,074 | 7,074 | 99.96% |
| J03WQQ | 6,298 | 6,296 | 6,296 | 6,296 | 99.97% |
| J03WR9 | 6,558 | 6,556 | 6,556 | 6,556 | 99.97% |
| **Overall** | **44,779** | **44,767** | **44,767** | **44,767** | **99.97%** |

Team-level counts are retained in [`primary_attrition.csv`](../outputs/phase5a/primary_attrition.csv).

## Primary held-out performance

### MAE by held-out match

| Match | B0 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|---:|
| J03WMX | 2.730 | 2.159 | 2.129 | 2.119 | 2.114 |
| J03WN1 | 2.491 | 2.029 | 1.941 | 1.926 | 1.918 |
| J03WOH | 2.658 | 2.162 | 2.124 | 2.112 | 2.111 |
| J03WOY | 2.666 | 2.200 | 2.158 | 2.126 | 2.121 |
| J03WPY | 2.674 | 2.165 | 2.112 | 2.085 | 2.073 |
| J03WQQ | 2.803 | 2.280 | 2.250 | 2.238 | 2.233 |
| J03WR9 | 2.615 | 2.182 | 2.156 | 2.138 | 2.132 |

All values are metres. Full MAE, median absolute error, RMSE, $R^2$, alpha, and observation counts are in [`heldout_model_metrics.csv`](../outputs/phase5a/heldout_model_metrics.csv).

### Across-match summary

| Model | Median MAE | Range | IQR | Median improvement vs B0 | Matches improved | ≥10% worsenings |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 2.666 | 2.491–2.803 | 0.066 | 0.0% | 0/7 | 0 |
| B1 | 2.165 | 2.029–2.280 | 0.030 | 18.64% | 7/7 | 0 |
| B2 | 2.129 | 1.941–2.250 | 0.039 | 20.09% | 7/7 | 0 |
| B3 | 2.119 | 1.926–2.238 | 0.033 | 20.54% | 7/7 | 0 |
| **B4** | **2.114** | **1.918–2.233** | **0.034** | **20.58%** | **7/7** | **0** |

B4 has the lowest median MAE and is therefore the frozen best simple level. B1–B4 all meet category A versus B0. The classification does **not** mean every feature family contributes materially.

## Adjacent ladder increments

| Step | Median improvement | Matches improved | ≥10% worsenings | Frozen materiality |
|---|---:|---:|---:|---|
| B0→B1 | 18.64% | 7/7 | 0 | **Pass** |
| B1→B2 | 1.78% | 7/7 | 0 | Fail |
| B2→B3 | 0.75% | 7/7 | 0 | Fail |
| B3→B4 | 0.25% | 7/7 | 0 | Fail |

Only recent focal movement adds material predictive information under the frozen adjacent-step rule. B1 accounts for a median 89.7% of the full B0→B4 absolute MAE reduction across matches. Collective, ball, and spatial additions are directionally consistent but below the prospectively frozen 3% materiality requirement; they cannot be described as material contributors.

## Ridge selection

| Held-out match | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| J03WMX | 0.1 | 10 | 0.1 | 100 |
| J03WN1 | 0.1 | 10 | 0.1 | 0.1 |
| J03WOH | 0.1 | 100 | 0.1 | 10 |
| J03WOY | 0.1 | 1 | 0.1 | 100 |
| J03WPY | 0.1 | 100 | 0.1 | 0.1 |
| J03WQQ | 0.1 | 100 | 1 | 100 |
| J03WR9 | 0.1 | 100 | 1 | 100 |

All outer and inner fits removed zero constant features and used the direct linear solver. Inner-fold MAEs and selected alphas are retained machine-readably.

## Calibration and residual diagnostics

For B4, held-out calibration slopes range from 0.882 to 1.084, with median 0.999. Match mean residuals range from −0.134 to +0.059 m. Training-side cross-fitted prediction quantiles supplied every bin edge; held-out outcomes never defined bins.

Residual Spearman relationships with the prospectively named activity/spatial variables are small overall: focal recent activity +0.014, leave-one-out centroid activity −0.015, other-defender mean activity −0.022, ball activity −0.021, focal depth +0.002, focal lateral distance −0.009, and prediction magnitude +0.003. The fitted B4 residual therefore showed little remaining monotonic association with the pre-specified pre-cutoff activity and spatial diagnostics. This does not make it activity-independent, activity-free, an activity-controlled response, or unexplained by movement generally. Residual distributions retain skew, large errors, player/team heterogeneity, omitted-variable risk, and model misspecification; player summaries include small-sample players and are diagnostic rather than stable effects.

## One-second sensitivity

The frozen one-second analysis also classifies A and selects B4. Median B4 MAE is 2.048 m versus 2.114 m for the primary two-second specification. B0→B1 is again the only material adjacent step (21.46%); B1→B2, B2→B3, and B3→B4 remain below 3%. The conclusion therefore does not depend on the two-second history, although the shorter history predicts somewhat better. The primary classification remains the two-second result.

## Evidence balance and claim boundary

The strongest supporting evidence is the consistent match-heldout reduction: every B1–B4 model improves on B0 in all seven matches, with no ≥10% worsening, and the primary B4 median reduction is 20.58%.

The strongest counterevidence is that recent focal motion alone supplies nearly all useful improvement. The frozen collective, ball, and spatial increments are individually non-material; the observed-versus-predicted distribution retains substantial dispersion and outliers; and diagnostic residual group heterogeneity remains. Phase 5A therefore establishes contextual predictability in the broad frozen sense, not a rich contextual or tactical expectation model.

The maximum supported claim is:

> **Future focal-relative path contains reproducibly predictable structure from pre-interval observable context.**

Within the ladder, the supported decomposition is narrower:

> **Most useful predictive information in the tested ladder was already contained in the focal defender's recent movement.**

Phase 5A does not validate correct tactical position or trajectory, tactical defensive response, responsibility, attention, decision-making, relational reconfiguration, attacker association, pinning, dragging, tracking, covering, handoffs, causation, defensive quality, gravity, or off-ball value. Statistically expected is not tactically expected; prediction residual is not tactical error; unexpected focal departure is not attacker-induced response.

## Inference-ladder position

The governing ladder remains:

**physical movement → collective defensive movement → individual/local behavior relative to collective movement → contextual expectation → defensive response → attacker association → attribution → attacking value**

Phase 4 externally validated the third level as geometry. Phase 5A supplies feasibility evidence for the fourth level, contextual expectation, within one IDSSE provider/data environment. It does not establish a definitive contextual-expectation metric externally validated across providers, and it does not establish the fifth level, defensive response.

## Figures

- [Held-out MAE by match](../figures/phase5a/heldout_mae_by_match.png)
- [Adjacent improvements](../figures/phase5a/adjacent_improvement.png)
- [Observed versus predicted](../figures/phase5a/observed_vs_predicted_best.png)
- [Residuals by match](../figures/phase5a/residuals_by_match.png)
- [History sensitivity](../figures/phase5a/history_sensitivity.png)
