# Kloppy–IDSSE/Sportec Equivalence Experiment

**Status:** completed infrastructure experiment; **B — mostly compatible, explicit provider rules remain**

**Architecture decision:** **NOT READY** to promote `Kloppy → Moving the Defense adapter → canonical Polars representation` as the default ingestion architecture for new analyses.

**Scope:** one already-used Phase 4C match, `J03WMX`, only. No historical loader, frozen protocol, existing Phase 4C result, notebook, or scientific claim changed. Metrica Game 3 and UnravelSports were not accessed.

## 1. Purpose

This is the IDSSE/Sportec counterpart to the [Metrica Game 1 equivalence experiment](kloppy_metrica_equivalence.md). It asks whether Kloppy 3.19.0 can load one professional-match provider feed while preserving the support and geometry used by the frozen Phase 4C analysis. It is an equivalence experiment, not a migration.

The result is B because the continuous scientific quantities reproduce, but Kloppy alone does not preserve every governed provider field. Absolute UTC timestamps and the provider ball-object identity require a raw provenance sidecar; explicit null rows must be reconstructed; and a single cross-provider contract for coordinate origin and time meaning has not yet been frozen. These are material architecture concerns even though the tested Phase 4C measurement is numerically stable.

## 2. Selected match and provenance

`J03WMX` is the first canonical match in the frozen Phase 4C match order: 1. FC Köln versus FC Bayern München, provider match ID `DFL-MAT-J03WMX`.

Raw DFL/Sportec XML inputs:

- `DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml`;
- `DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml`;
- `DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml`.

The experiment uses local files already used by Phase 4C. Kloppy loads match information and raw observed positions with `sportec.load_tracking(..., coordinates="sportec", only_alive=False)`. Existing Phase 4C event-state logic remains unchanged and reads the same event XML; Kloppy event semantics were not substituted.

Exact input and source hashes are recorded in [`equivalence_result.json`](../outputs/kloppy_idsse_equivalence/equivalence_result.json).

## 3. Representations

### Current Phase 4C representation

The governed loader stores provider frame IDs, absolute UTC nanoseconds, and metre coordinates in period arrays. Coordinates are centred on the pitch, x in [−52.5, 52.5] and y in [−34, 34], with no orientation normalization. Player presence is an explicit finite-coordinate mask. The cache stores coordinates as float32, while scientific calculations convert them to float64.

### Kloppy representation and adapter

Kloppy returns a `TrackingDataset` with Sportec metre coordinates, provider team/player IDs, 25 Hz metadata, an inferred match orientation of `away-home`, active players per frame, ball coordinates, ball state, and ball-owning team. Goalkeeper identity is available through player position metadata.

[`kloppy_idsse_adapter.py`](../src/infrastructure/kloppy_idsse_adapter.py) shares the 14-column canonical core introduced by the Metrica adapter and appends four IDSSE fields: raw UTC nanoseconds, period label, ball state, and ball-owning team. Its complete logical long table contains 5,984,647 rows—40 rostered players plus one ball row for each frame—and is streamed. Only a three-frame schema sample is committed.

The adapter emits explicit null rows for inactive or unsupported roster players. It does not interpolate or infer a tactical field.

## 4. Structural equivalence

| Check | Current Phase 4C | Kloppy adapter | Result |
|---|---:|---:|---|
| Total frames | 145,967 | 145,967 | Exact |
| First-half frames | 70,708 | 70,708 | Exact |
| Second-half frames | 75,259 | 75,259 | Exact |
| First-half frame range | 10,000–80,707 | 10,000–80,707 | Exact |
| Second-half frame range | 100,000–175,258 | 100,000–175,258 | Exact |
| Sampling frequency | 25 Hz | 25 Hz | Exact |
| Player IDs/team mapping | 40 roster players | 40 roster players | Exact |
| Goalkeepers | `DFL-OBJ-0002DR`, `DFL-OBJ-0002HE` | Same | Exact |
| Player-presence masks | — | — | Exact for every player/period |
| Ball-presence masks | complete | complete | Exact |
| Ball state | raw `BallStatus` | alive/dead | Exact |
| Ball possession code/team | raw 1/2 | home/away team | Exact |

Kloppy includes 22 active players on each frame and changes identities as substitutions occur. The adapter expands those observations against the fixed 40-player metadata roster. These reconstructed masks match the current pipeline exactly, so no substitution or inactive-player difference was observed.

## 5. Time, orientation, and provider metadata

Raw `Frame.T` values and current Phase 4C timestamps match exactly after the adapter reads UTC nanoseconds from the provider ball frames. Kloppy’s own `Frame.timestamp` is different by design: it is derived from frame number and period metadata, begins at 0.00 s in each half, and ends at 2,828.28 s and 3,010.32 s. It does not preserve raw absolute `Frame.T` as a separate field. Both clocks are therefore exposed; one is not silently substituted for the other.

Kloppy preserves provider player and team IDs directly. It does not expose the provider ball object ID `DFL-OBJ-0000XT`; that identity remains in the raw sidecar. Raw provider attributes such as match minute, acceleration, direction, and every XML serialization detail are not part of the canonical analysis table. They remain provenance-sidecar fields if a future question needs them.

The native Sportec coordinate system and the existing Phase 4C system are both centred 105 × 68 m coordinates. Kloppy reports `away-home` orientation from the opening geometry. Phase 4C performs no orientation normalization, and the adapter likewise performs none.

## 6. Coordinate and support equivalence

Every player and ball missingness mask matched. The largest coordinate difference was $1.8311\times10^{-6}$ m, arising from the current cache’s float32 storage versus Kloppy’s float64 parsing of the same two-decimal provider coordinates.

Across the two periods and both axes:

- median player-coordinate difference: $1.53\times10^{-7}$ to $3.05\times10^{-7}$ m;
- 99th-percentile player-coordinate difference: $1.37\times10^{-6}$ to $1.83\times10^{-6}$ m;
- median ball-coordinate difference: $3.05\times10^{-7}$ to $4.58\times10^{-7}$ m;
- maximum difference: $1.8311\times10^{-6}$ m;
- mismatches above the explicit $10^{-5}$ m representation tolerance: 0.

Kloppy did not interpolate, drop a provider ball frame, change an active-player mask, or change identity continuity in this match. See [`coordinate_equivalence.csv`](../outputs/kloppy_idsse_equivalence/coordinate_equivalence.csv).

## 7. Phase 4C scientific equivalence

Both tracking paths independently entered the existing Phase 4C sample construction, seven-frame centred smoothing, leave-one-out centroid, focal-relative path, activity summaries, and misaligned-control code.

Support was exact:

- 695 eligible five-second intervals in each path;
- identical interval IDs;
- 6,949 focal outcomes in each path;
- identical focal keys;
- all nine frozen Metrica activity cells populated in each path.

Maximum differences were:

| Quantity | Maximum absolute difference |
|---|---:|
| Leave-one-out centroid components | $7.77\times10^{-7}$ m |
| Focal-relative components | $2.28\times10^{-6}$ m |
| Focal-relative path | $6.81\times10^{-6}$ m |
| Focal absolute path | $1.01\times10^{-5}$ m |
| Aggregate defender path | $2.27\times10^{-5}$ m |
| Ball path | $3.07\times10^{-6}$ m |
| Frozen misaligned-control path | $5.20\times10^{-6}$ m |

All scalar differences were below $10^{-3}$ m, and all pointwise component differences were below $10^{-4}$ m.

The match-level values were preserved:

| Phase 4C quantity | Frozen/current | Kloppy | Absolute difference |
|---|---:|---:|---:|
| Median focal-relative path | 5.141800516 m | 5.141801486 m | $9.70\times10^{-7}$ m |
| IQR | 4.394554097 m | 4.394553798 m | $2.99\times10^{-7}$ m |
| Focal absolute Spearman rho | 0.710138274 | 0.710138344 | $6.94\times10^{-8}$ |
| Full-centroid rho | 0.522643317 | 0.522643237 | $8.08\times10^{-8}$ |
| Aggregate-defender rho | 0.588304908 | 0.588304846 | $6.26\times10^{-8}$ |
| Ball rho | 0.467133618 | 0.467133528 | $8.94\times10^{-8}$ |

The frozen misaligned control retained 658 supported intervals and 6,579 focal observations. Its paired median increase changed from 2.361592722 m to 2.361592767 m; the 0.773673811 greater/nonnegative fractions and pass classification were unchanged. Independently regenerated control identities were also identical—unlike the hard-cut sensitivity found in the Metrica experiment.

The freshly reconstructed current-pipeline outcomes match the committed Phase 4C outputs to a maximum of $2.84\times10^{-14}$ m, confirming that this audit compares against the validated historical result rather than an alternative reconstruction.

## 8. Cross-provider adapter assessment

The same long-table **schema shape** can represent Metrica and IDSSE, and project-owned focal-relative measurement can operate downstream without provider-specific scientific logic. The boundary is:

### A. Provider-specific ingestion rules

- Metrica: undo Kloppy’s y reversal; preserve provider global match seconds; map native compound IDs; supply governed goalkeeper identities.
- IDSSE: preserve raw UTC nanoseconds; retain the raw ball object ID separately; expand active-player maps to explicit roster null rows; retain centred-metre coordinates and provider ball fields.

### B. Canonical representation rules

- one explicit row per roster object/frame;
- stable provider team/player IDs plus any reversible adapter identity;
- explicit observed/null status;
- x/y in documented physical units and a separately documented normalized view;
- raw provider clock plus Kloppy period time;
- pitch, orientation, provider, version, and transformation provenance.

### C. Project-owned scientific measurement

Support eligibility, outfield/goalkeeper exclusions, smoothing, leave-one-out centroids, focal-relative position/path, controls, frozen thresholds, and claim boundaries remain project-owned and unchanged.

The following belong in a provenance sidecar rather than a minimal analysis table: raw input hashes and paths, provider serialization fields, raw ball object identity, raw UTC time for providers whose canonical clock is relative, source/target coordinate definitions, orientation derivation, roster/position metadata, and adapter/library versions.

## 9. Classification and architecture recommendation

**Classification: B — mostly compatible, explicit unresolved adapter/provider rules remain.** Kloppy is technically suitable beneath an IDSSE adapter, and the tested match preserves the validated Phase 4C result. It is not safe to use Kloppy directly without that adapter.

**Architecture: NOT READY** for default use in new analyses. Before promotion, the project must govern one canonical contract for:

1. raw versus analysis clocks, including nanosecond-safe absolute time;
2. coordinate origin/y-direction semantics across Metrica and centred Sportec metres;
3. required versus optional ball/provider fields;
4. explicit roster membership and null-row construction;
5. provider IDs that Kloppy abstracts away;
6. numerical boundary policy for any discrete governed selection;
7. a direct canonical Polars implementation and tests, which this pass intentionally did not add.

One provider-agnostic **interface** now works for Metrica and IDSSE geometry, but the canonical representation is not yet sufficiently specified to be the default architecture. Historical analyses must remain on their original loaders regardless of future promotion.
