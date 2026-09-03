# Defensive Coverage Redistribution v2 — Prospective Supersession Record

**Status:** v2 closed INVALID; v3 frozen before any v3 outcome-model execution

**Decision date:** 2026-09-03

**Decision checkpoint:** `a4b4a9ab301651c97aab5c024e6254b89a406f57`

The frozen [v2 protocol](defensive_coverage_redistribution_v2.md),
[configuration](../../config/defensive_coverage_redistribution_v2.json), and
[invalid Game 1 closure](../results/defensive_coverage_redistribution_game1_v2.md)
remain unchanged. V2 retained 281 period-1 anchors and no period-2 anchors.
Its required period-2 indicator was constant zero, so the nominal design had
rank 11/12 and stopped before estimating $\beta_D$, an interval, the direction
null, or any robustness result.

The [estimability audit](../defensive_coverage_redistribution_v3_estimability_audit.md)
shows that an explicitly predesignated constant nuisance dummy adds no column-
space information. Omitting it preserves the fitted values, residuals, and all
identifiable scientific coefficients of the equivalent one-period model.
This does not permit dropping a scientific term or resolving any other exact
or near-collinearity after inspecting results.

The [v3 protocol](defensive_coverage_redistribution_v3.md) therefore changes
only the deterministic handling of an exactly constant, explicitly designated
non-scientific nuisance indicator. All sample, construct, timing, outcome,
predictor, covariate, control, resampling, classification, and claim-boundary
rules remain inherited from v2. No v3 empirical outcome was computed or
inspected before this supersession was frozen. Games 2 and 3 and IDSSE coverage
outcomes remain unopened.
