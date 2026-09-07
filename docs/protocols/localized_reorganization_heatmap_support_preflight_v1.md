# Localized Reorganization Heatmap — Response-Blind Support Preflight v1

**Status:** support-only preflight executed; future response-map specification human-approved before response access
**Date:** 2026-09-07

## Purpose and firewall

This preflight asks only where the already-governed seven-match IDSSE temporal
footprint population has enough spatial support for a future descriptive map.
It does not read, construct, join, summarize, model, or render
`response_2s_m`, the near-minus-middle outcome, any coefficient, or any other
defensive-response outcome.

It is therefore not a new empirical result. The support-only execution did not
render a response surface. After reviewing its response-blind support report,
human approval froze the separate future response-map choices below; no response
values were read or constructed at selection.

The seven existing IDSSE match identifiers and their governed observation IDs
are used only to reconstruct each focal attacker's start coordinate at
`t-2 s`. Metrica Sample Game 3, SkillCorner response-mode material, and DRD
residual/retrieval material are outside this preflight.

## Coordinate and support construction

For each governed attacker-anchor observation, reconstruct in memory the
centred-seven-frame, complete-support attacker position at `t-2 s`, using the
same 25 Hz native IDSSE coordinate support as the closed footprint. The plotted
coordinate is

\[
x_{plot}=s_{attack}x_{provider}, \qquad y_{plot}=y_{provider}.
\]

`s_attack` is the established goalkeeper-derived attacking-direction sign.
There is no lateral reflection. Thus the horizontal axis means deeper/own-goal
direction (left) to goalward direction (right); vertical position remains the
provider's physical side of the pitch and is not a tactical left/right or
inward/outward label. This avoids resolving the separate exact-centreline
lateral-direction convention.

The coordinate table is held only in memory, match by match. It is never
serialized, including as an ignored staging artifact.

Provider-native observed player positions are not clipped to the nominal pitch
rectangle. The preflight requires finite coordinates and reports the aggregate
count outside that rectangle; this is a tracking-support description, not a
coordinate transformation or a data-quality exclusion.

## Bounded alternatives

Evaluate 1 m cell centres over the 105 by 68 m pitch, exactly six Gaussian
bandwidths (`2.5`, `5`, `7.5`, `10`, `12.5`, `15` m), and a kernel neighborhood
truncated at `2h`.

At every cell and bandwidth, evaluate exactly two profiles:

| Profile | Requirements in every one of seven matches |
|---|---|
| Basic | nearest anchor within `h`; at least 2 distinct period-aware 60-second blocks; Kish row-weight concentration count at least 10 |
| Conservative | Basic plus at least 4 period-aware blocks and Kish row-weight concentration count at least 20 |

The all-seven-match requirement, temporal diversity, local nearest-anchor
coverage, and local weight concentration are nonnegotiable support concepts.
The two numerical profiles are deliberately small, interpretable alternatives,
not a search for attractive map coverage.

For every alternative, report pitch/common-support coverage, raw and unique
time-anchor support, per-match balance, block counts, nearest distances,
kernel mass, Kish row-weight concentration counts, and support at touchlines, goal lines, the centre
line, and penalty-area boundaries. Smaller bandwidths preserve locality while
usually reducing common support; larger ones increase coverage while broadening
any future display.

The bandwidth grid and profile thresholds were specified before response access.
An earlier automatic recommendation rule was added after the first support
output and is therefore not retained as prospective selection evidence. The
current `h=7.5 m`, Conservative choice was selected by response-blind human
review from the bounded support trade-off only—not by a prospectively frozen
automatic rule. It is now frozen for the future descriptive response-map stage;
the already-executed support-only result remains distinct from that future map.

## Human-approved future response-map specification

The following visualization choices are frozen before response access:

- IDSSE only, using all seven governed matches; attacker location is the
  smoothed `t-2 s` position on the existing goalward x / physical-y coordinate
  frame, $x_{plot}=s_{attack}x_{provider}$ and $y_{plot}=y_{provider}$.
- The descriptive colour quantity is
  $Y_m=\operatorname{mean}(\mathrm{response\_2s\_m}_{D1:D3})-
  \operatorname{mean}(\mathrm{response\_2s\_m}_{D4:D7})$, in metres.
- At each grid cell, form one truncated-Gaussian local mean per match and then
  average the seven match means equally. The primary bandwidth is `7.5 m`, with
  `5.0 m` and `10.0 m` sensitivities; every displayed cell must pass the current
  Conservative profile in all seven matches on the existing 1 m grid.
- Retain native out-of-pitch attacker coordinates in kernels; evaluate and
  render only legal-pitch grid cells, with no clipping or exclusion.
- Use no local regression coefficient, GAM/spline response model, local
  hypothesis test, or significance map. The surface is descriptive; an absent,
  weak, or bandwidth-unstable pattern is accepted without changing the smoother.
- Define one shared symmetric colour range $[-L,L]$, where $L$ is the weighted
  95th percentile of $|Y_m|$ across one governed anchor-level $Y_m$ per
  observation after assigning each match total weight $1/7$. Use this same limit
  for primary and sensitivity surfaces and mark any saturation explicitly.

Physical provider y remains unreflected, so this map neither uses nor resolves
the separate exact-centreline outward-direction ambiguity.

Kish row-weight concentration counts describe how concentrated local kernel
weights are; they are not independent-observation counts, and simultaneous
attackers can increase them. Unique-time-anchor and period-aware 60-second-block
counts provide separate temporal-support diagnostics.

## Aggregate-publication rule

The only grid artifact is `support_grid.parquet`, one aggregate row per grid
cell × bandwidth × profile. Its schema is allowlisted in the accompanying
configuration and excludes observation/player/team/time/block identifiers,
individual coordinates, and all response/path/rank fields. A hard QC check and
synthetic test fail closed on a schema violation. The aggregate artifact must
remain below 10 MiB and is checked by the repository changed-artifact guard.

## Interpretation boundary

Support is not response magnitude, association, causation, tactical meaning,
space creation, or attacking value. This preflight only describes whether a
future descriptive visualization could avoid visibly single-match, temporally
concentrated, or sparse spatial regions.
