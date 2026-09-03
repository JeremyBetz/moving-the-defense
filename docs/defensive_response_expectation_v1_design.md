# Defensive Response Expectation v1 — Pre-execution Design Record

**Status:** design frozen; no protected E0/E1/E2 result computed

## Schedule audit

The metadata-only audit used match/team identifiers and eligible-observation IDs from already closed IDSSE infrastructure. It did not read coordination-form response columns.

| Match | Defending team | Existing coordination-form eligible observations |
|---|---|---:|
| J03WMX | DFL-CLU-000008 | 7,261 |
| J03WMX | DFL-CLU-00000G | 5,074 |
| J03WN1 | DFL-CLU-00000B | 300 |
| J03WN1 | DFL-CLU-00000S | 4,574 |
| J03WOH | DFL-CLU-00000P | 5,140 |
| J03WOH | DFL-CLU-000011 | 6,108 |
| J03WOY | DFL-CLU-00000P | 5,908 |
| J03WOY | DFL-CLU-00000Q | 5,611 |
| J03WPY | DFL-CLU-000005 | 7,501 |
| J03WPY | DFL-CLU-00000P | 4,896 |
| J03WQQ | DFL-CLU-00000H | 3,570 |
| J03WQQ | DFL-CLU-00000P | 6,391 |
| J03WR9 | DFL-CLU-00000I | 6,930 |
| J03WR9 | DFL-CLU-00000P | 4,588 |

There are 73,852 existing eligible focal-attacker observations before the new common-feature gate. `DFL-CLU-00000P` is the only repeated team, appearing in five matches. Nine teams appear once. `DFL-CLU-00000B` appears in only one temporal region of `J03WN1`; the frozen fold-support rule will exclude its unsupported test rows identically from every model rather than invent an effect.

## Consequence for the claim

The primary validation can test whether knowing the defending side improves prediction in temporally separated portions of the **same match**. It cannot show stable team identity across matches. The one repeated team's leave-one-match-out check is informative but nonclassifying and cannot generalize to the league.

## Chosen outcome and ladder

The outcome is the observed D2–D3-minus-D4–D7 AARD-velocity contrast, not its regression coefficient. It compresses the already-validated local-versus-middle directional geometry to one interpretable anchor-level response while avoiding a new rank-specific multivariate prediction problem.

- **E0:** concurrent and prior attacker path, plus common match/period nuisance indicators.
- **E1:** E0 plus frozen compact distance, prior defensive movement, unit shape, attacker-to-unit, and ball-to-unit geometry.
- **E2a:** E1 plus within-match defending-side intercepts.
- **E2b (primary):** E2a plus one defending-side deviation in the concurrent-attacker-path slope per match.

## Outcome-free readiness checks

Synthetic tests establish the exact local-minus-middle aggregation, deterministic contiguous-block folds, lexical treatment coding, nested full-rank design construction, and rejection of incomplete rank vectors. These checks use generated values only. No empirical response target, model error, residual, coefficient, or status was computed.

The remaining implementation must prove common-sample support, full training rank, fold support, grouping, and deterministic reproduction before any result can be valid. The [protocol](protocols/defensive_response_expectation_v1.md) and [configuration](../config/defensive_response_expectation_v1.json) are authoritative.
