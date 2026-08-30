# Phase 5B Opponent-Relational Predictive Increment Results

> **Result: B — mixed/partial.** Under frozen protocol v1.0, prospectively selected opponent information produced small held-out predictive improvements beyond the Phase 5A B4 baseline, but the improvements were not material and did not support a tactical or attacker-specific interpretation.

## Protocol compliance and support

Execution used the seven frozen IDSSE matches, the unchanged Phase 4 target, and the exact Phase 5A B4 baseline refitted on the Phase 5B common sample. Opponents were selected once at the prediction cutoff, ordered by exact cutoff distance with provider player ID as the deterministic tie-break, and kept fixed through the history. No later movement affected selection or ordering.

The primary common sample contains 44,752 observations from 44,767 Phase 5A observations (99.97%). The maximum difference from the saved Phase 4 target is $1.28\times10^{-12}$ m. Every model used seven outer leave-one-match-out folds, six inner training-match folds, training-only preprocessing, population SD (`ddof=0`), and the Phase 5A NumPy Ridge implementation. Every actual fit used the direct solver; the deterministic pseudoinverse fallback was not invoked. Protocol/config/source hashes and the non-material implementation clarifications are recorded in the [execution manifest](../outputs/phase5b/execution_manifest.json).

| Match | Phase 5A B4 | $K=3$ selectable | A1–A3 history complete | Final primary |
|---|---:|---:|---:|---:|
| J03WMX | 6,948 | 6,948 | 6,946 | 6,946 |
| J03WN1 | 5,436 | 5,436 | 5,434 | 5,434 |
| J03WOH | 6,115 | 6,115 | 6,115 | 6,115 |
| J03WOY | 6,342 | 6,342 | 6,342 | 6,342 |
| J03WPY | 7,074 | 7,074 | 7,070 | 7,070 |
| J03WQQ | 6,296 | 6,296 | 6,289 | 6,289 |
| J03WR9 | 6,556 | 6,556 | 6,556 | 6,556 |
| **Overall** | **44,767** | **44,767** | **44,752** | **44,752** |

## Primary held-out MAE

| Match | B4 | B5 | B6 | B7 |
|---|---:|---:|---:|---:|
| J03WMX | 2.1142 | 2.1114 | 2.1094 | 2.1048 |
| J03WN1 | 1.9186 | 1.9124 | 1.9131 | 1.9142 |
| J03WOH | 2.1107 | 2.0934 | 2.0974 | 2.0927 |
| J03WOY | 2.1210 | 2.1096 | 2.1143 | 2.1078 |
| J03WPY | 2.0739 | 2.0780 | 2.0769 | 2.0745 |
| J03WQQ | 2.2328 | 2.2231 | 2.2214 | 2.2233 |
| J03WR9 | 2.1319 | 2.1282 | 2.1276 | 2.1268 |

All values are metres.

| Model | Median MAE | Range | IQR | Median improvement vs B4 | Matches improved | ≥10% worsenings |
|---|---:|---:|---:|---:|---:|---:|
| B4 | 2.1142 | 1.9186–2.2328 | 0.0341 | 0.000% | — | 0 |
| B5 | 2.1096 | 1.9124–2.2231 | 0.0341 | 0.323% | 6/7 | 0 |
| B6 | 2.1094 | 1.9131–2.2214 | 0.0338 | 0.290% | 6/7 | 0 |
| **B7** | **2.1048** | **1.9142–2.2233** | **0.0337** | **0.426%** | **6/7** | **0** |

B7 is the technical best simple model because it has the lowest median held-out MAE. This does not make every opponent feature family scientifically material.

## Adjacent materiality and classification

| Step | Median improvement | Matches improved | Frozen 3% materiality |
|---|---:|---:|---|
| B4→B5 | 0.323% | 6/7 | Fail |
| B5→B6 | 0.026% | 4/7 | Fail |
| B6→B7 | 0.117% | 5/7 | Fail |

Category A fails because no B5–B7 model reaches the frozen 5% median improvement requirement versus B4. Category C fails because all three opponent models improve six of seven matches, exceeding its maximum of three directionally improved matches, although none reaches a 2% median gain. The mechanically determined result is therefore **B — mixed/partial**.

The B7 improvement versus B4 by match is +0.443%, +0.229%, +0.853%, +0.623%, −0.028%, +0.426%, and +0.241% in the table order above. These are small effects.

## Ridge selection

| Held-out match | B4 | B5 | B6 | B7 |
|---|---:|---:|---:|---:|
| J03WMX | 100 | 100 | 100 | 10 |
| J03WN1 | 0.1 | 0.1 | 0.1 | 0.1 |
| J03WOH | 10 | 10 | 1 | 0.1 |
| J03WOY | 100 | 100 | 100 | 10 |
| J03WPY | 0.1 | 0.1 | 0.1 | 0.1 |
| J03WQQ | 100 | 100 | 100 | 100 |
| J03WR9 | 100 | 10 | 100 | 100 |

## Representation and locality controls

On the same primary observations, the $K=1$ B7 median MAE is 2.1097 m versus 2.1048 m for $K=3$. The $K=3$ representation is better in five of seven matches, with a median per-match relative improvement of 0.298% and median absolute reduction of 0.0066 m. The broader fixed representation is slightly stronger, but the difference is very small.

The frozen locality control retains 44,729 observations. Local-versus-nonlocal median relative differences are −0.026% for B5, −0.050% for B6, and +0.035% for B7; local models win two, two, and four of seven matches, respectively. This provides no strong evidence that the small opponent-information increment is specifically local. In the ball-nearest proxy, A1, A2, and A3 are nearest the ball in 11.86%, 9.23%, and 8.70% of observations; none of the selected three is nearest in 70.21%.

## Calibration, residuals, and sensitivity

B7 held-out calibration slopes range from 0.896 to 1.071, with median 0.990. Match mean residuals range from −0.099 to +0.064 m. These describe predictive-model behavior, not tactical validation.

Overall residual Spearman correlations range from −0.029 to +0.046 across the frozen B4 prediction, movement, opponent, ball, and spatial diagnostics. The fitted B7 residual showed little remaining monotonic association with those pre-specified diagnostics. It is not activity-independent, a tactical error, an isolated tactical response, or an attacker-induced response. Residual distributions retain skew, large errors, group heterogeneity, omitted-variable risk, and model-misspecification risk.

The frozen one-second history sensitivity also classifies B and selects B7. Median MAE changes from 2.0483 m for B4 to 2.0302 m for B7, a 0.503% median improvement; all adjacent increments again fail the 3% materiality rule. The qualitative conclusion is therefore robust to the frozen history sensitivity.

## Evidence balance and claim boundary

The strongest supporting evidence is directional consistency: each opponent model improves six of seven held-out matches, no model has a ≥10% match-level worsening, and the frozen one-second sensitivity reaches the same category-B conclusion.

The strongest counterevidence is magnitude and specificity. Median gains are below 1%, no adjacent step is material, one match is marginally worse under B7, $K=3$ only narrowly outperforms $K=1$, and local attackers do not consistently outperform nonlocal attackers.

The principal scientific constraint is:

> **The tested nearest-opponent representation does not provide evidence that local opponent information is materially more predictive than nonlocal opponent information.**

This is a conclusion about the frozen A1–A3 versus matched-dimensional A4–A6 test, not a universal claim that local opponent relationships never matter in football.

The maximum supported claim is:

> **Prospectively selected opponent information shows a small, mixed held-out predictive association with future focal-relative movement beyond the tested non-opponent contextual baseline.**

This is limited evidence at the **opponent-information association** rung. It does not validate attacker causation, tactical defensive response, marking, assignment, responsibility, attention, pinning, dragging, tracking, covering, handoffs, relational reconfiguration, tactical correctness, defensive quality, gravity, or off-ball value. Geometric proximity is not a tactical relationship; predictive increment is not attribution.

## Forward-looking unresolved questions

Without choosing among them or defining a subsequent phase, the result leaves several possibilities unresolved:

1. recent focal movement may already contain the beginning of opponent-associated response before cutoff;
2. nearest-attacker selection may inadequately represent the relevant attacking relationships;
3. opponent information may operate through attacking-team-relative or space/ball-conditioned configuration rather than simple proximity;
4. the five-second scalar focal-relative-path target may discard tactical or directional structure;
5. the weak observed increment may reflect opponent information already mediated through collective or focal motion.

These are hypotheses for later design work, not explanations established by Phase 5B.

## Figures

- [Held-out MAE by match](../figures/phase5b/heldout_mae_by_match.png)
- [Adjacent improvements](../figures/phase5b/adjacent_improvements.png)
- [B7 calibration](../figures/phase5b/best_model_calibration.png)
- [B7 residual diagnostics](../figures/phase5b/best_model_residuals.png)
- [$K=3$ versus $K=1$](../figures/phase5b/k3_vs_k1.png)
- [Local versus nonlocal](../figures/phase5b/local_vs_nonlocal.png)
