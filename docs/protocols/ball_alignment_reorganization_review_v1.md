# Ball-Alignment Reorganization Review v1

**Status:** frozen before ball-alignment calculation or replacement-candidate inspection  
**Frozen:** 2026-09-28  
**Starting commit:** `0ed898f230903c27c725302a3122d95da6b45b4b`

## Purpose and boundary

This response-free application diagnostic asks whether rapid defensive
relational reorganization is directed substantially toward the ball or occurs
elsewhere in the defensive structure. It also prevents gross raw-trajectory
discontinuities from being promoted as analyst examples. It does not change the
production score, rapid threshold, possession state machine, event alignment,
or any scientific result.

Metrica Sample Games 1 and 2, both teams and both periods, provide the same 18
stable-run reference population used by the closed application audits. Both
event sources are hash-bound because their frozen possession states determine
reference eligibility; Game 2 is the public review match. Events supply
possession/restart context only. Ball
direction comes from tracking coordinates, never events. Game 3, IDSSE,
SkillCorner, DRS work, protected outcomes, and causal/tactical interpretation
remain outside scope.

## Raw trajectory integrity

Integrity is evaluated on native, unsmoothed player coordinates at 25 Hz.

- A player transition is impossible when displacement divided by native frame
  interval is strictly greater than **15.0 m/s**. The threshold is application
  QC, not a football-performance threshold.
- A same-team two-player swap is suspected only when both identity-preserving
  implied speeds exceed 15.0 m/s, both cross-assigned implied speeds are at or
  below 15.0 m/s, and cross-assignment total displacement is no more than 25%
  of identity-preserving total displacement. Pair ordering is lexical and ties
  are resolved lexically. No identity is relabelled or repaired.
- Duplicates, missing/nonfinite coordinates, cadence breaks, identity changes,
  and existing scorer support failures fail closed. There is no interpolation.

For a one-second delta `score(t) - score(t-1s)`, both endpoints must be clean
over the union of their raw score support. With the frozen trailing two-second
window and centered seven-frame smoother, the union is `[t-3.12, t+0.12]` at
25 Hz, including every native transition whose two endpoints lie in that
closed interval. Any affected defender or invalid ten-player support marks the
episode `trajectory_integrity_failed`. Historical scores and selections remain
unchanged; only the current showcase gate changes.

## Ball-alignment geometry

Players and ball use the same centered seven-frame mean. For consecutive
smoothed frames, defender-relative increment `delta_r` is the exact increment
underlying the raw score. Player and ball positions are each evaluated at the
midpoint of their corresponding smoothed frames. The unit ball direction is
from player midpoint to ball midpoint. Zero/undefined ball distance or invalid
ball support makes the increment unsupported.

For one defender over the same trailing two-second score interval:

- raw path `L = sum(||delta_r||)`;
- signed alignment `A = sum(delta_r dot u_ball) / L`;
- positive ballward projection share
  `B = sum(max(delta_r dot u_ball, 0)) / L`;
- diagnostic awayward share
  `W = sum(max(-delta_r dot u_ball, 0)) / L`;
- diagnostic lateral index
  `Q = sum(||delta_r|| * abs(sin(theta))) / L`.

`L=0` yields an explicit `zero_path` status and undefined directional ratios.
Team `A` and `B` are ratios of path-weighted sums across all ten defenders and
all supported increments; percentages are not averaged. Player values remain
decomposable locally. `B`, `W`, and `Q` are separate summaries and do not sum
to one by definition.

## Reference strata and retrieval

The reference distribution contains `A` and `B` for rapid episodes that pass
the unchanged P95 rapid threshold (`0.6251746256690309 m`) and unchanged
possession eligibility in the full Games 1–2 stable-run population. Reference
P25/P75 use NumPy linear quantiles and are computed before Game 2 examples are
inspected.

- `low_ballward`: `B <= P25`;
- `mid_ballward`: `P25 < B < P75`;
- `high_ballward`: `B >= P75`.

The three deterministic rankings start from existing rapid candidates and
require unchanged possession/restart/render rules, clean trajectory integrity,
and complete ball alignment:

1. overall rapid, descending one-second raw increase;
2. low-ballward rapid under the same order;
3. high-ballward rapid under the same order.

Ties resolve by period, time, then team key. The public contrast selects the
highest-ranked clean low-ballward episode, the highest-ranked clean
high-ballward episode, and optionally the highest overall episode only when
distinct. Overlap is preserved; examples are never substituted for appearance.

## Publication and interpretation

The six historical v3 episodes receive a compact audit containing integrity
status/counts, unchanged raw scores/deltas, aggregate alignment, stratum,
anonymized contribution magnitudes/shares, and existing possession context.
Public output may contain one compact comparison, one low-ballward and one
high-ballward diagnostic, up to two GIFs, and an aggregate manifest. Raw rows,
coordinates, frame identities, player identities, and detailed support ledgers
remain local.

Allowed wording is descriptive: high-ballward means most measured relational
movement had a substantial component toward the ball; low-ballward means much
of it was not directed toward the ball. The diagnostic does not establish
attacker causation, manipulation, pressing, disruption, intent, defensive
quality, effectiveness, or value.
