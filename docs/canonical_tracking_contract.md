# Moving the Defense Canonical Tracking Contract

**Contract version:** 1.0.0

**Adapter version:** 1.0.0

**Status:** governed architecture for **new analyses**
**Evidence base:** Metrica Sample Game 1 and IDSSE/Sportec `J03WMX` Kloppy equivalence experiments

This contract governs infrastructure, not football interpretation. It does not change a historical loader, frozen protocol, validated measurement, output, or claim. Historical analyses remain reproducible through their original code paths.

## 1. Purpose and boundary

The canonical layer gives new work one stable path:

> raw provider data → Kloppy 3.19.0 → provider adapter → canonical Polars table + provenance sidecar → project-owned measurement

Community tooling handles parsing and standard data objects. Provider adapters make semantic differences explicit. Moving the Defense continues to own tracking-support rules, smoothing, leave-one-out defensive references, focal-relative geometry, controls, thresholds, validation design, and claim boundaries.

The canonical table is logically one long table. It may be emitted in consecutive schema-identical Polars chunks so a full match need not be materialized in memory.

## 2. Canonical Polars schema

| Field | Polars dtype | Nullability / meaning |
|---|---|---|
| `match_id` | `String` | Non-null canonical match key, namespaced by provider |
| `period` | `UInt8` | Non-null positive period number |
| `frame_id_provider` | `String` | Non-null raw/provider frame identifier; string prevents numeric coercion |
| `time_period_s` | `Float64` | Non-null elapsed seconds from the governed period origin |
| `time_match_s` | `Float64` | Non-null strictly increasing elapsed tracking time across periods, halftime excluded |
| `entity_type` | `String` | `player` or `ball` |
| `team_key` | `String` | Canonical reversible team key; null for ball |
| `player_key` | `String` | Canonical reversible player key; null for ball |
| `is_goalkeeper` | `Boolean` | Non-null; source recorded in provenance |
| `x_m` | `Float64` | Nullable canonical x coordinate in metres |
| `y_m` | `Float64` | Nullable canonical y coordinate in metres |
| `z_m` | `Float64` | Nullable height in metres when explicitly available |
| `is_present` | `Boolean` | Whether the provider/Kloppy frame contains the entity object |
| `coordinate_valid` | `Boolean` | Whether finite x/y coordinates are available |
| `support_state` | `String` | Explicit support classification described below |
| `ball_state` | `String` | `alive`, `dead`, or `unknown` on ball rows; null on player rows |
| `possession_team_key` | `String` | Explicit provider possession team on ball rows; otherwise null |
| `pitch_length_m` | `Float64` | Non-null pitch length used by the canonical transform |
| `pitch_width_m` | `Float64` | Non-null pitch width used by the canonical transform |

Provider IDs, absolute timestamps, and transformation metadata are not duplicated across millions of rows; their reversible mappings and sources live in the provenance sidecar.

## 3. Time contract

Five concepts remain distinct:

1. **Provider/raw timestamp.** The literal provider timestamp, if supplied. Its original type and unit are retained through the raw source plus sidecar metadata. Absolute UTC is optional provenance, not a canonical-table requirement.
2. **Provider/raw frame ID.** Preserved exactly as `frame_id_provider` and stored as `String`. No renumbering is permitted.
3. **Period number.** A positive integer in `period`. Period changes are explicit rows, never inferred from a clock discontinuity alone.
4. **Period-relative elapsed time.** `time_period_s`, in seconds, from a documented provider/adapter period origin. It must be nonnegative and strictly increasing within a period.
5. **Match-global elapsed time.** `time_match_s`, in seconds, strictly increasing across every retained frame. Period durations are accumulated without halftime gaps. It is an analysis clock, not necessarily the displayed football clock.

Metrica preserves raw `Time [s]` as `time_match_s` and Kloppy period time as `time_period_s`. IDSSE uses Kloppy’s frame-derived period time; the adapter accumulates actual tracked period durations for `time_match_s`. Raw IDSSE UTC nanoseconds remain available from `Frame.T`, keyed by period/frame in the hashed source, with their range and extraction rule recorded in provenance.

A missing provider concept remains null/unavailable in provenance. It must not be silently reconstructed and called raw. A derived clock is allowed only when its derivation is named in the sidecar transformation log.

## 4. Coordinate contract

Canonical coordinates use:

- physical units: metres;
- explicit per-row pitch dimensions;
- current governed analysis dimensions: 105 × 68 m;
- origin: pitch centre `(0, 0)`;
- +x: left-to-right in the fixed canonical pitch drawing;
- +y: bottom-to-top in the fixed canonical pitch drawing;
- frame: fixed for the match, never normalized by attacking team or period.

Playing direction and provider orientation are metadata, not coordinate transformations. A future analysis may create a separately named attacking-direction-normalized view, but it must retain the fixed-frame canonical source and log every flip. No adapter may silently change orientation at halftime or by possession.

Metrica’s normalized top-to-bottom y is converted through Kloppy’s bottom-to-top representation, centred, and scaled. Native Sportec centred metres already satisfy the contract, so x/y are unchanged. Coordinates outside nominal pitch bounds are retained and counted; they are not clipped because they may reflect valid off-pitch tracking or a support-quality issue requiring separate evaluation.

## 5. Entity identities

Canonical keys are reversible and namespaced:

- Metrica team: `metrica:{provider_team}`;
- Metrica player: `metrica:{provider_team}:{provider_player}`;
- Sportec team: `sportec:{provider_team_id}`;
- Sportec player: `sportec:{provider_player_id}`.

The provenance sidecar contains complete provider→canonical maps. No hash, integer recoding, or irreversible alias is allowed. `team_key` and `player_key` are required for player rows. The ball has neither; its provider object ID, where supplied, belongs in provenance.

`is_goalkeeper` is a canonical convenience flag, but its source is mandatory provenance. Metrica uses the governed Home 11/Away 25 mapping. IDSSE uses Kloppy/provider position metadata verified against the frozen Phase 4C metadata.

## 6. Row and support model

Each frame contains exactly:

- one row for every player in the match metadata roster; and
- one ball row.

No row is silently dropped. No coordinate is interpolated or repaired.

`is_present` means the entity object is present in the adapted provider frame. `coordinate_valid` means finite x/y exist. The permitted `support_state` values are:

- `observed`: entity present with valid x/y;
- `provider_coordinate_missing`: entity row exists but coordinates are invalid, when distinguishable;
- `provider_entity_absent`: metadata roster entity is not present in the provider/Kloppy frame;
- `inactive_off_pitch`: provider explicitly states inactive/off-pitch;
- `ball_absent`: no valid ball observation;
- `not_observed_unspecified`: provider representation cannot distinguish inactivity, absence, and coordinate missingness.

The distinction is never invented. Metrica’s wide nulls cannot establish why a player is unobserved, so they use `not_observed_unspecified`. IDSSE’s object mapping supports `provider_entity_absent`, but this is not automatically interpreted as a substitution or tactical status. A future provider may use `inactive_off_pitch` only when that state is explicit.

## 7. Ball fields

Every frame has one logical ball row. Minimum governed fields are x/y, optional z, `is_present`, `coordinate_valid`, and `support_state`. `ball_state` and `possession_team_key` are populated only when supplied explicitly by the provider and semantically mapped without tactical inference.

IDSSE supplies x/y/z, alive/dead state, possession code/team, and a provider ball object ID. The object ID remains provenance. Metrica supplies x/y when observed but no governed ball state, possession team, or ball ID; those fields remain `unknown`/null. Nearest-player or event-derived possession is prohibited at ingestion.

## 8. Provenance sidecar

Every canonical dataset must have a JSON-serializable sidecar containing at least:

- contract and adapter versions;
- provider and provider match identity;
- canonical match identity;
- Kloppy version;
- source paths and SHA-256 hashes;
- original coordinate system;
- canonical coordinate system and exact transformation log;
- pitch dimensions;
- raw timestamp availability, unit, location, and extraction rule;
- time-period and time-match derivations;
- full reversible team and player maps;
- goalkeeper source;
- provider ball ID where available;
- ball-state and possession availability;
- support/null semantics;
- provider orientation metadata;
- whether attacking-direction normalization occurred;
- interpolation/repair declaration.

Provider-specific serialization fields—raw UTC timestamps, event schemas, XML attributes, speed/acceleration fields, lineup detail, and object IDs—remain in hashed raw sources or explicit sidecars. They are not forced into the generic table unless a later governed contract version promotes them.

## 9. Numerical and discrete-boundary policy

This policy applies prospectively to new analyses only.

### Exact invariants

Schema, dtypes, frame IDs, period membership, entity keys, team mapping, goalkeeper source, row counts, presence masks, coordinate-valid masks, and previously persisted sample/control identities require exact equality.

### Continuous quantities

Canonical coordinates are `Float64`. Every equivalence test must predeclare units and tolerances appropriate to source precision and the downstream quantity. The current gates use $10^{-5}$ m for provider-coordinate equivalence, $10^{-4}$ m for derived point components, and $10^{-3}$ m for paths/scalars. Tolerances establish equivalence; they must not silently round or modify stored values.

### Thresholds and discrete decisions

Every future threshold must freeze its value, unit, comparison operator, missingness behavior, and tie-break before outcomes. Computation uses canonical float64 without hidden epsilon. Values within the predeclared numerical-equivalence tolerance of a boundary are flagged as **boundary-sensitive**. The exact frozen operator still produces the deterministic primary assignment, but robustness reporting must show whether a tolerance-consistent perturbation changes membership or conclusions.

Derived interval, sample, pairing, and control IDs must be persisted. A loader migration must compare those exact identities rather than merely reproduce similar continuous inputs. Historical protocols are not retroactively changed; the Metrica control-pair sensitivity remains part of the evidence motivating this rule.

## 10. Contract audit result

Both complete logical tables passed the same schema and invariants:

| Provider | Frames | Logical rows | Rows/frame | Ball valid |
|---|---:|---:|---:|---:|
| Metrica Game 1 | 145,006 | 4,205,174 | 29 | 88,251 |
| IDSSE `J03WMX` | 145,967 | 5,984,647 | 41 | 145,967 |

The bounded frozen geometry checks passed:

| Provider | Max centroid-component difference | Max focal-relative-component difference | Focal-path difference | Control-path difference |
|---|---:|---:|---:|---:|
| Metrica | $7.11\times10^{-15}$ m | $1.07\times10^{-14}$ m | $4.88\times10^{-15}$ m | $2.66\times10^{-15}$ m |
| IDSSE | $2.85\times10^{-7}$ m | $3.86\times10^{-7}$ m | $4.58\times10^{-7}$ m | $1.77\times10^{-7}$ m |

## 11. Architecture decision and migration status

The architecture is **READY for new analyses**:

> Kloppy → governed provider adapter → canonical Polars table + provenance sidecar

Both tested providers satisfy one schema; provenance loss is controlled; support semantics are explicit; clocks and coordinates are governed; and bounded validated measurements remain equivalent.

This decision does **not** migrate historical analyses, authorize deleting old loaders, or establish equivalence for every provider/match. Historical code and artifacts remain frozen. New analyses should start from this architecture and add provider equivalence tests before treating an untested provider adapter as ready.
