# Defensive Reorganization Spatial Form v1 — SkillCorner external replication

**Status:** frozen prospectively; protected SkillCorner spatial-form outcome unobserved

**Freeze date:** 2026-09-04

**Starting commit:** `b9760207ebe4e59b14a6ff9b3302fda86a29dddb`

**Parent protocol:** [Defensive Reorganization Spatial Form v1](defensive_reorganization_spatial_value_v1.md)

## 1. Question and boundary

The one external question is unchanged:

> Conditional on equal attacker path magnitude and the frozen starting context,
> is outward attacker displacement associated with greater subsequent localized
> defender-relative reorganization than goalward displacement in SkillCorner
> tracking data?

The sole primary estimand is

$$
\Delta_{O-G}=\beta_{outward}-\beta_{goalward}.
$$

The prospectively expected sign is positive because the closed IDSSE result was
`OUTWARD GREATER`. Exact magnitude replication is not required. This protocol
does not reopen the static-versus-dynamic comparison and does not inspect DRD,
players, teams, alternate directions, ranks, windows, lags, tactics, gravity,
or value.

## 2. Release and formal match set

Use only the official `SkillCorner/opendata` release at Git commit
`c1e17a0cc3e07e1774b52d929c1a0b85115143fc`. It contains ten 2024/25
Australian A-League tracking matches at 10 Hz.

Match `1953632` is excluded prospectively because its top-level provider status
is `not_started` despite the presence of complete two-period files. No result
was inspected when this provider-metadata conflict was found. The formal match
set is therefore:

`1886347`, `1899585`, `1925299`, `1996435`, `2006229`, `2011166`,
`2013725`, `2015213`, and `2017461`.

At least eight of these nine matches must pass all outcome-blind provider,
identity, support, equivalence, and design-rank gates. Otherwise the external
study is `INVALID`. A passing match is never selected by its coefficient.

## 3. Native source, Kloppy, and publication

The native SkillCorner JSONL is authoritative for raw frame IDs, timestamps,
coordinates, `is_detected`, image-coverage metadata, possession-player fields,
and provider support. Kloppy 3.19.0 is the community ingestion layer for roster,
pitch, frame, player/team, ball, and possession-team objects, but its current
SkillCorner deserializer drops `is_detected`, image projection, and possession
player ID. The provider adapter must merge native support metadata by exact
frame and player ID; it may not infer or replace those fields.

Before outcome construction, every formal match must pass a full native-versus-
Kloppy equivalence gate for frame, period, timestamp, player/team identity,
goalkeeper identity, player and ball coordinates, possession team, and pitch
dimensions. Required tolerances are `1e-9 s` for period time, `1e-12 m` for
native coordinates, `1e-5 m` after canonical conversion, and exact equality for
discrete identities and masks.

The open-data repository uses the MIT License and requests SkillCorner credit.
Moving the Defense nevertheless publishes no raw tracking, frame/player table,
anchor-level sample, or other reconstructive derivative. Only source, tests,
protocols, hashes, aggregate match support, and compact result summaries may be
committed. Preserve the SkillCorner copyright and MIT notice in acquisition
documentation.

## 4. Time, cadence, and smoothing

Use native 10 Hz frames. Preserve physical intervals exactly:

- prior attacker path: `[t-4,t-2]`;
- attacker exposure: `[t-2,t]`;
- defender response: `[t,t+2]`; and
- anchor grid: period origin plus `4 + 4k` seconds.

Endpoints are included. Paths sum Euclidean differences between consecutive
smoothed native-time positions, once per 0.1 s. No interpolation, resampling,
or IDSSE frame counts are allowed.

The IDSSE centred seven-frame smoother has 0.28 s nominal physical support.
The nearest odd native SkillCorner window is frozen prospectively as the
centred three-frame arithmetic mean (0.30 s nominal support, one raw frame on
each side). Every raw point must be present; edge or partial smoothing is
prohibited. This is the sole cadence-specific adaptation.

The provider timestamp and `(frame_id-period_start_frame)/10` clocks must agree
within `1e-9 s`. Period 2 provider time is made period-relative by subtracting
45 minutes. Any cadence gap inside a required window excludes that observation.

## 5. Coordinates and direction

Native coordinates are centred metres with x along pitch length and y along
pitch width. Scale independently about `(0,0)` to the governed 105 by 68 m
canonical pitch:

$$
x_c=x\,105/L,\qquad y_c=y\,68/W,
$$

using each match's provider pitch dimensions. Do not clip off-pitch values.

For each period/team, derive goalward sign from the provider's frozen
`home_team_side` field. Multiply x by that sign. Then reflect the entire frame
in y only when the focal attacker's canonical y at `t-2` is negative. Exact
zero is not reflected. The focal attacker therefore starts at nonnegative y;
positive `y(t)-y(t-2)` is outward from the centre line. The reflection is fixed
at `t-2` and never depends on future movement or the result.

## 6. Identity and active-roster support

Derive current players from provider metadata `playing_time.total.start_frame`
and `end_frame`, with the provider player-role ID `0` identifying goalkeepers.
The metadata supplies 22 starters and substitution intervals in every formal
match; no dismissals are reported. Coordinate presence never defines roster
membership.

At every required raw frame, the expected and observed active outfield sets
must be exactly equal for both teams, with exactly ten players per side.
Windows crossing substitutions or any reduced/ambiguous active set fail.
Unknown, duplicated, or roster-inconsistent player IDs fail closed.

As a prospective identity-continuity guard, exclude an observation if its focal
attacker or any fixed D1--D7 defender moves more than 1.5 m between adjacent
native 0.1 s frames anywhere in its required interval. Exact 1.5 m passes.
This 15 m/s ceiling is tracking-identity QC, not a movement or response label;
it cannot be changed after outcomes.

## 7. Tracking status and stricter sensitivity

Detected-only complete-team support is not feasible: only 49 full primary
anchors across all ten released matches had every active outfielder detected
through the required window. The primary therefore uses the provider's official
detected-plus-extrapolated full-field positions, while requiring a non-null
Boolean `is_detected` status for every used player coordinate.

One stricter, predeclared quality sensitivity retains a row only when direct
detection covers at least 50% of construct-relevant frames separately for:

1. the focal attacker and ball over `[t-4,t]` plus smoother edge support; and
2. every fixed D1--D7 defender over `[t,t+2]` plus smoother edge support.

This majority-observed rule is not tuned for retention. The sensitivity must
remain full rank, have a strictly positive pooled contrast, and retain 50--150%
of the primary absolute contrast magnitude to pass the robustness gate.

## 8. Ball, open play, and focal attackers

Require valid ball coordinates over `[t-4,t]` plus smoother edge support.
Require the complete physical interval `[t-4,t+2]` to fall within the union of
official phase-file intervals, used only as a provider ball-in-play mask; phase
labels and tactical fields are prohibited. Require native possession group at
the anchor to identify the attacking team. Possession after the anchor is not
required.

At the anchor, find the unique nearest current attacking outfielder to the
smoothed ball by `(distance, canonical_player_id)` ordering. Exclude that player
from focal candidates. This is a geometric exclusion and is never called the
ball carrier. Every other supported current attacking outfielder creates one
candidate row; simultaneous focal attackers remain grouped.

## 9. Defender-relative representation and target

At the anchor, order the ten current defending outfield players by smoothed
Euclidean distance to the focal attacker, then exact canonical player ID. Fix
D1--D10 for the observation.

For rank `k`, accumulate the path over `[t,t+2]` of the defender relative to the
leave-one-out centroid of the other nine defenders. The unchanged target is

$$
Y_i=\frac{1}{3}\sum_{k=1}^{3}P_{ik}
-\frac{1}{4}\sum_{k=4}^{7}P_{ik}.
$$

No rank reassignment, goalkeeper, interpolation, role, assignment, event
outcome, D8--D10 target, or DRD quantity is allowed.

## 10. Unchanged model

Fit equal-match-weighted raw-unit OLS with match intercepts and the exact
continuous column order:

1. exposure path;
2. prior attacker path;
3. attacker-minus-unit goalward offset at `t-2`;
4. attacker-ball distance at `t-2`;
5. defending-unit width at `t-2`;
6. defending-unit depth at `t-2`;
7. ball-minus-unit goalward offset at `t-2`;
8. signed goalward displacement; and
9. signed outward displacement.

Use `numpy.linalg.lstsq(rcond=None)` and require full rank. No standardization,
regularization, interaction, nonlinear term, provider term, identity effect,
target scaling, clipping, or alternate representation is permitted.

## 11. Inference and robustness

Use 2,000 deterministic paired match-period 60-second block bootstrap
replicates with `PCG64` seed `20260905`. Resample blocks independently within
every represented match-period, retain nonempty terminal blocks, preserve all
matches and all rows sharing an anchor, use a two-sided 95% percentile interval,
and require at least 1,900 finite full-rank replicates.

Report pooled equal-match-weighted, match-specific, and leave-one-match-out
fits. Apply the unchanged within-match inclusive 2.5th--97.5th percentile joint
trim to goalward and outward displacement. It passes only with positive sign
and 50--150% absolute magnitude retention. The only additional robustness is
the stricter tracking-quality sensitivity in Section 7.

## 12. External classification

Evaluate in order:

1. **INVALID:** fewer than eight valid formal matches, or any frozen-hash,
   provider/equivalence, support, identity, time, geometry, rank, solver,
   bootstrap, reproduction, or hard-QC failure.
2. **SKILLCORNER SPATIAL FORM EXTERNAL REPLICATION SUPPORTED:** valid execution;
   pooled contrast strictly positive with its 95% interval strictly above zero;
   at least `ceil(0.70*M)` valid-match contrasts positive; every one of the `M`
   leave-one-match-out contrasts positive; unchanged trim passes; and stricter
   quality sensitivity passes. For nine valid matches the match threshold is
   seven; for eight it is six.
3. **MIXED:** valid, pooled contrast positive, but one or more uncertainty,
   match-consistency, leave-one-match-out, trim, or quality gates fail.
4. **NOT SUPPORTED:** every other valid result, including a nonpositive pooled
   contrast.

No result may change the match set, support rule, smoothing, thresholds,
covariates, inference, or classification. A mixed/not-supported result remains
secondary in the paper; Game 3 is not a rescue dataset.

## 13. Reporting and stopping rule

Report match/support counts before fitting, pooled and match/leave-one-out
coefficients, interval, 5 m translation, trim, quality sensitivity, bootstrap
validity, and all hard QC. Provider differences must be stated directly.

If supported, the maximum claim is:

> In a third broadcast-derived tracking environment, outward off-ball
> displacement remained more strongly associated with subsequent localized
> defender-relative reorganization than equivalently modeled goalward
> displacement.

This remains observational. Do not claim that outward movement is better,
valuable, causally influential, a corner-flag run, or that defenders were
dragged. Stop after the external result. Do not inspect DRD residuals, Game 3,
players, teams, other representations, or downstream value.
