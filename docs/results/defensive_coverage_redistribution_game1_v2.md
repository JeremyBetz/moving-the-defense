# Defensive Coverage Redistribution v2 — Game 1 development closure

**Status: INVALID before outcome-model estimation**

V2 was executed exactly as frozen on Metrica Sample Game 1 after its
pre-execution v1 supersession review. The eligibility pipeline retained 281
one-row anchors, all in period 1. Every retained row had a unique
ball-nearest geometric reference attacker, complete ten-by-ten outfield
geometry, and full ball support. The 281 anchors were reproduced byte for byte
in an independent rerun.

The frozen raw-unit model requires an intercept and a period-2 indicator, with
full column rank mandatory. Because no period-2 anchor survived the unchanged
complete-ten-outfield support rule, the period-2 indicator was constant and
the 12-column design had rank 11. The solver therefore stopped before any
$\beta_D$, bootstrap interval, direction-null result, robustness result, or
coverage-outcome conclusion was produced.

This is an execution-validity failure under the frozen protocol, not a
negative or positive result about matching geometry. Removing the period-2
column, weakening support, or otherwise repairing the design would be a new
prospective protocol—not a permissible execution adjustment. Game 2, Game 3,
and IDSSE coverage outcomes remain unopened.

The governed local artifacts and hashes are in
[`outputs/defensive_coverage_redistribution_game1_v2`](../../outputs/defensive_coverage_redistribution_game1_v2/).
Provider-linked anchor and observation tables are intentionally regenerated
locally rather than committed.
