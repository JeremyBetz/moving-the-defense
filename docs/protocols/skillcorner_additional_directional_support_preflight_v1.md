# SkillCorner additional directional replication — outcome-blind support preflight v1

**Status:** frozen before any response construction or directional outcome access

**Authorization:** user-approved independent reacquisition and compatibility audit, 2026-09-17

## Purpose and source

Independently inventory the official SkillCorner Open Data repository at commit
`02a396ffd09b283c9f092fdedeff11da6d535b66`, acquired directly from
`https://github.com/SkillCorner/opendata`. No sibling repository, prepared
dataset, partition, result, or output may enter this audit.

The release is associated with PySport Analytics Cup 2.0 and contains Australian
A-League 2024/25 material. The upstream root MIT licence permits use and
publication with its notice; SkillCorner requests attribution. Project policy is
narrower: raw files and reconstructive derivatives remain ignored. Permission
for public rasterized tracking animations is not treated as resolved here.

## Population and classification

The acquired release must contain exactly 20 match directories. Compare their
provider IDs with Project 1's committed authority only:

- nine existing formal matches;
- the previously excluded match `1953632`;
- ten nonoverlapping candidates;
- no unresolved IDs.

The ten candidates must be retained or rejected only by source identity and the
fixed compatibility checks below. No coefficient, response, rank, path, or
directional outcome may be constructed. Global non-exposure cannot be claimed
without inspecting other projects; the allowed description is “prospectively
frozen, nonoverlapping Project 1 replication population,” not “untouched.”

## Permitted fields and checks

Metadata projection is limited to match ID/status, pitch dimensions, team IDs,
team-period side, player/team/role identities, and playing intervals. Tracking
projection is limited to frame, period, timestamp, player identity/x/y/detection,
ball x/y/detection, and possession group. Phase projection is limited to interval
start/end. Fixture names, scores, events, targets, outcomes, Dynamic Events,
aggregates, and pose are excluded.

For every match, verify exact source bytes against the pinned Git tree and LFS
pointer, then check:

- both periods, contiguous native frame IDs, finite 10 Hz timestamps and exact
  frame-clock agreement within `1e-9 s`;
- finite positive pitch dimensions and centred-metre coordinate support;
- distinct home/away identities, roster identity uniqueness, goalkeeper roles,
  and playing intervals supporting substitutions;
- player/ball coordinates and Boolean `is_detected` support;
- possession group support, nonempty phase intervals, and team-period attacking
  direction;
- native/Kloppy identity, time, pitch, player/ball-coordinate and possession-team
  equivalence under the existing adapter tolerances.

Finite out-of-pitch coordinates are retained. No clipping, interpolation,
imputation, smoothing, rank construction, eligibility filtering, response path,
model fit, bootstrap, or visualization is authorized.

## Outputs and decision

Publish only aggregate per-match compatibility rows, source identities, QC,
manifest, hashes, and a compact report. Do not publish fixtures, dates, teams,
players, frames, timestamps, coordinates, observations, ranks, responses,
predictions, or residuals.

The preflight passes only if all ten nonoverlapping candidates have exact source
identity and every frozen compatibility check passes. A failure identifies the
specific fixed incompatibility and stops. Passing supports a later prospective
protocol using the current frozen directional metric on all ten candidates; it
does not authorize that execution.
