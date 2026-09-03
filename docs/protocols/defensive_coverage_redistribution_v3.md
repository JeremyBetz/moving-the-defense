# Defensive Coverage Redistribution v3 — Frozen Game 1 Development Protocol

**Status:** frozen prospectively before any coverage-model coefficient

**Freeze date:** 2026-09-03

**Starting checkpoint:** `a4b4a9ab301651c97aab5c024e6254b89a406f57`

**Supersedes:** [Defensive Coverage Redistribution v2](defensive_coverage_redistribution_v2.md), which remains closed **GAME 1 COVERAGE REDISTRIBUTION v2 DEVELOPMENT INVALID** because its mandatory period-2 indicator was constant and the nominal design had rank 11/12

## 1. Scope and authoritative inheritance

V3 changes exactly one pre-fit estimability rule. The complete scientific
design in the frozen [v2 protocol](defensive_coverage_redistribution_v2.md) and
[`config/defensive_coverage_redistribution_v2.json`](../../config/defensive_coverage_redistribution_v2.json)
is incorporated unchanged except where Sections 3–5 below explicitly govern
constant nuisance indicators and the corresponding full-rank check.

In particular, v3 does not change the Game 1 data, support registry,
eligibility, ten-versus-ten requirement, ball-nearest reference attacker,
fixed other-nine outcome, response predictor, timing, smoothing, model
covariates, raw-unit estimator, bootstrap, direction null, remote comparator,
movement trim, descriptive alternatives, synthetic gates, classification
thresholds, or claim boundary. Games 2 and 3 and IDSSE coverage outcomes remain
closed.

No v2 $\beta_D$, interval, null, robustness estimate, or outcome-model result
was observed. The v3 change follows the known outcome-blind sample fact that
281 eligible anchors all came from period 1.

## 2. Unchanged statistical unit, outcome, predictor, and model family

There remains exactly one row per eligible period/time anchor. The outcome is
the unchanged fixed-set matching-cost change

$$
Y=G_{else}(t+2)-G_{else}(t),
$$

and the sole primary predictor remains

$$
D=\overline{P^{rel}}_{D1:D3}-\overline{P^{rel}}_{D4:D7}.
$$

The nominal raw-unit model family remains

$$
Y=\alpha+\beta_A A+\beta_D D+\beta_GG_0+\beta_OM_O+
\beta_BB+\beta_CC+\beta_RR+\beta_{Apre}A_{pre}+
\beta_{Dpre}D_{pre}+\beta_{Bpre}B_{pre}+\beta_PP_2+\epsilon.
$$

The nominal column order is unchanged:

| Column | Role | Eligible for constant-nuisance omission? |
|---|---|---:|
| intercept | structural model term | No |
| $A$ | scientific covariate: concurrent reference-attacker path | No |
| $D$ | primary scientific predictor; fitted $\beta_D$ enters classification | No |
| $G_0$ | scientific covariate: initial elsewhere matching cost | No |
| $M_O$ | scientific covariate: mean other-attacker concurrent path | No |
| $B$ | scientific covariate: concurrent ball path | No |
| $C$ | scientific covariate: concurrent defending-centroid path | No |
| $R$ | scientific covariate: mean concurrent D1–D10 focal-relative path | No |
| $A_{pre}$ | scientific covariate: prior reference-attacker path | No |
| $D_{pre}$ | scientific covariate: prior fixed-rank response contrast | No |
| $B_{pre}$ | scientific covariate: prior ball path | No |
| $P_2$ | non-scientific nuisance indicator for a period-level mean difference | **Yes; the only v3-designated nuisance** |

## 3. Deterministic constant-nuisance rule

After the complete realized eligible primary sample is constructed, assemble
all twelve nominal columns without inspecting $Y$ or any predictor–outcome
association. Apply this rule once:

> A frozen nuisance indicator explicitly listed in the configuration as
> non-scientific is omitted if and only if it is exactly constant over the
> complete realized eligible primary sample. No scientific predictor,
> scientific covariate, response, classifying contrast, or structural
> intercept may be omitted under this rule.

For v3, `period_2_indicator` is the sole listed nuisance column. Exact
constancy means every constructed binary value is identical; no tolerance,
variance threshold, model fit, coefficient, outcome, or researcher judgment
enters the decision. Log the nominal columns, observed unique value for every
designated nuisance, omitted columns, and final active column order.

The active column set is then fixed. Do not re-evaluate or change it inside
bootstrap replicates, direction-null replicates, the remote comparator, the
movement trim, or any descriptive alternative.

## 4. Rank, collinearity, and numerical policy

Fit float64 `numpy.linalg.lstsq(..., rcond=None)` using the unchanged outcome,
rows, and active columns. The active design must have full column rank as
reported by that frozen estimator policy.

- A constant scientific predictor or covariate is not removable and makes the
  execution INVALID.
- Exact collinearity among varying active columns is not removable and makes
  the execution INVALID.
- Near-collinearity does not authorize omission. Report the unchanged singular
  values and condition number; any existing numerical/solver failure remains
  INVALID.
- Do not “drop columns until full rank.”

When $P_2$ is constant, its column is either zero or a scalar multiple of the
intercept and adds no column-space information. Omitting it preserves the
model's estimable fitted values, residuals, and all identifiable scientific
coefficients, including $\beta_D$. The unidentified split between the
intercept and a constant-one dummy has no scientific estimand in this design.

## 5. Unchanged inference and classification

Use the exact v2 bootstrap seed, period-block construction, 2,000 replicates,
minimum-valid count, direction null, controls, robustness rules, and
COHERENT/MIXED/NOT SUPPORTED/INVALID decision order. “Full rank” now refers to
the active design after the single deterministic rule in Section 3. No other
classification condition changes.

A valid Game 1 result must be labeled explicitly as a **period-1-only
development result**. The absence of period 2 is an external-validity and
representativeness limitation; it is not itself an execution-invalidity rule
once its non-informative nuisance indicator is handled as frozen here.

## 6. Firewall and stopping rule

This protocol is a prospective supersession, not an execution. Do not compute
or inspect a v3 coverage outcome, $\beta_D$, interval, null, robustness result,
or classification in the freeze pass. A later execution requires separate
authorization and must stop after Game 1. Game 2, Game 3, and IDSSE coverage
outcomes remain prohibited.

All v2 nonclaims remain unchanged. Even a coherent v3 result would remain a
concurrent matching-geometry association, not causation, influence, attention,
marking, responsibility, opportunity, space creation, tactical success,
gravity, or value.
