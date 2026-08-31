# Moving the Defense — Open Football Analytics Ecosystem Alignment

**Status:** architecture audit complete; the first bounded Kloppy/Metrica equivalence experiment subsequently produced B — explicit adapter required, with no loader migration

**Repository checkpoint:** naming checkpoint `5d05cf6`

**Audit date:** 2026-08-30

## 1. Ecosystem philosophy

Moving the Defense should use established community software for routine football-data plumbing and preserve custom code where the scientific contribution and evidentiary commitments live.

The governing boundary is:

> **Community infrastructure → stable project adapter → project-specific measurement → frozen research design.**

Provider parsing, coordinate metadata, standard pitch drawing, and dataframe interchange are not research contributions. Conversely, a library function with a similar name is not a scientific substitute for a construct that has already been prospectively defined and validated. In particular, no ecosystem component reviewed here replaces focal-relative defensive movement, the attacking-movement segmentation audit trail, tracking-support QC, frozen thresholds, held-out logic, negative controls, or the claim-status ladder.

The original six-package environment was deliberately small: NumPy, Pandas, Matplotlib, Jupyter, nbclient, and ipykernel. Kloppy 3.19.0 is now the sole ecosystem dependency added for the isolated equivalence gate. The repository has no package metadata beyond [`requirements-phase0.txt`](../requirements-phase0.txt) and no lockfile. Later governed scripts import earlier scripts directly, which preserves provenance but also couples provider parsing, canonical representation, measurement, and analysis.

The first implementation gate is now recorded in the [Kloppy–Metrica Game 1 equivalence report](kloppy_metrica_equivalence.md). Kloppy 3.19.0 reproduced Game 1 support and continuous Phase 4 geometry within numerical precision only after explicit y-axis, timestamp, identity, goalkeeper, and null-row adaptation. Independently regenerated negative-control pairing also exposed sensitivity at a frozen activity cut. The result does not authorize migration.

The second gate, [Kloppy–IDSSE/Sportec match J03WMX](kloppy_idsse_equivalence.md), also produced B. All frames, presence masks, identities, 695 eligible intervals, 6,949 focal outcomes, activity relationships, and controls reproduced within the expected float32/float64 precision difference. However, absolute UTC time and the provider ball ID require a raw sidecar, while cross-provider clock and coordinate-origin semantics still need a governed canonical contract. The proposed default Kloppy→adapter→canonical Polars architecture therefore remains **NOT READY**.

Those blockers are now resolved prospectively by [canonical tracking contract v1.0.0](canonical_tracking_contract.md). Complete Metrica Game 1 and IDSSE `J03WMX` logical tables passed one explicit Polars schema and provider-independent invariants, while bounded historical focal-relative/control quantities remained equivalent. The Kloppy→governed adapter→canonical Polars architecture is therefore **READY for new analyses**. Historical loaders and governed results are not migrated or rewritten.

The subsequent [UnravelSports interoperability audit](unravelsports_interoperability.md) produced **B**. UnravelSports 1.2.1 is useful as a reference/optional layer, and a thin row-preserving compatibility view is safe to integrate. Its full `KloppyPolarsDataset` is not canonical because it changes orientation, removes unsupported rows, derives and caps kinematics, and may infer possession, ball carrier, and goalkeeper identity. No governed measurement or historical pipeline was replaced.

## 2. Current architecture

The current pipeline has three main paths:

1. **Metrica CSV path.** `phase4b_focal_departure_validation.py` and three post-5B sources independently parse the two tracking CSVs, flatten two header rows, merge teams, scale normalized coordinates to 105 × 68 m, and reconstruct player/ball columns. Earlier notebooks contain related versions.
2. **IDSSE/Sportec XML path.** `phase4c_idsse_external_replication.py` parses metadata, events, and positional XML, constructs period arrays and validity masks, saves a custom cache, and supplies Phase 5A/5B.
3. **Scientific path.** NumPy/Pandas routines apply frozen completeness rules, smoothing, leave-one-out centroids, focal-relative paths, negative controls, predictive models, and audit classifications. These routines are scientifically authoritative for completed results.

Plotting is primarily direct Matplotlib. Pitch dimensions, orientation decisions, temporal conversion, smoothing, path length, hashing, and statistical helpers recur across scripts and notebooks.

## 3. Component audit

Classification meanings: **ADOPT** means community tooling can replace future plumbing after equivalence; **INTEGRATE** means place it under or beside a stable project interface; **RETAIN CUSTOM** protects project-specific science; **INVESTIGATE** requires a bounded equivalence or utility test; **DO NOT USE** means there is no current benefit sufficient to justify another abstraction.

| Current component | Current location | What it does | Relevant library | Community-standard alternative | Classification | Migration risk | Scientific dependency | Recommendation |
|---|---|---|---|---|---|---|---|---|
| Repeated Metrica CSV readers | `src/phase4b_*`, three post-5B sources, historical notebooks | Flatten headers; identify players/ball; merge teams | Kloppy | `kloppy.metrica` tracking/event loaders | **ADOPT** | Medium: column, timestamp, missingness, and orientation semantics | Feeds validated Phase 4 and segmentation results | Use Kloppy for new ingestion only after the full equivalence suite; never rewrite historical artifacts in place. |
| IDSSE/Sportec XML parser | `src/phase4c_idsse_external_replication.py` | Parses metadata, events, positions, validity, periods, IDs, and caches | Kloppy | `kloppy.sportec.load_tracking/load_event` or open IDSSE loaders | **INTEGRATE** | High: absolute timestamps, validity flags, goalkeeper identity, cache shape, and event-state logic | Foundation of external replication and Phase 5A/5B | Build an adapter beside the parser; retire parsing only after exact identity/mask and downstream equivalence. |
| Raw-provider archival fields | Phase 4C manifests and caches | Preserves input hashes, provider IDs, raw timing, provenance | Kloppy plus project sidecar | Kloppy metadata with raw-file/hash sidecar | **INTEGRATE** | High if normalized objects discard provider-specific fields | Required for auditability | Keep immutable raw files/hashes and a project provenance sidecar even if Kloppy becomes the loader. |
| Coordinate conversion | Repeated `* 105`, `* 68`; Phase 4C provider mapping | Converts provider coordinates to physical pitch units | Kloppy | Explicit `CoordinateSystem` transformation | **INTEGRATE** | High: origin, y direction, pitch size, and orientation can silently change signs | Every geometric result | First load in provider/raw orientation; transform explicitly; record both source and target systems. |
| Playing direction | `phase5a.period_orientation`, notebooks | Infers own-goal direction, standardizes x where required | Kloppy | Metadata `Orientation` and explicit transformations | **INVESTIGATE** | High: inference and period flips affect signed features | Phase 5A/5B directional context | Compare Kloppy metadata with frozen goalkeeper-based inference; do not silently replace it. |
| Pitch dimensions | Constants/configs across sources | Defines 105 × 68 m physical space | Kloppy, mplsoccer | Dataset metadata plus explicit analysis pitch | **INTEGRATE** | Medium: provider dimensions may differ from frozen 105 × 68 m | All physical-unit outputs | Preserve 105 × 68 m as the governed analysis target; use metadata to document source dimensions. |
| Team/player/goalkeeper metadata | Metrica column names; Phase 4C `Player` parser | Maps IDs, teams, positions, goalkeeper exclusions | Kloppy | Standard `Team`, `Player`, lineup, `PositionType` metadata | **INTEGRATE** | High: substitutions and goalkeeper inference can alter eligible sets | Leave-one-out reference membership | Preserve provider IDs as strings; verify goalkeeper and on-pitch membership exactly. |
| Frame/time representation | Metrica `Frame`/`Time [s]`; Phase 4C nanoseconds | Aligns 25 Hz frames, periods, events, and windows | Kloppy | `Frame`, `Time`, `Period`, `frame_id`, `metadata.frame_rate` | **INTEGRATE** | High: period-relative versus absolute time and endpoint rules | Frozen half-open windows and history cutoffs | Canonical adapter must expose raw frame ID, raw timestamp, period-relative seconds, and source time basis. |
| Event/tracking synchronization | Metrica joins and Phase 4C `event_state_at_intervals` | Determines open play, possession, and interval eligibility | Kloppy | Standard event/tracking datasets and frame-linked metadata where available | **INVESTIGATE** | High: event semantics and boundary matching are protocol-sensitive | Phase 3/4 sample construction | Test synchronization separately; do not replace frozen event-state logic without exact candidate equivalence. |
| Wide/long dataframe conversion | Custom wide Pandas and array dictionaries | Supplies vectorized analysis shapes | Kloppy, Polars, UnravelSports | Kloppy `to_df(engine="polars")`; optional `KloppyPolarsDataset` | **ADOPT** for new infrastructure | Medium: ordering, nulls, types, and inferred fields | Scientific code expects exact arrays/columns | Define a canonical long Polars table, then a deterministic compatibility adapter to governed NumPy/Pandas shapes. |
| Repeated smoothing/velocity/path helpers | Phase 4–5 and post-5B sources | Implements frozen centered/trailing means, finite differences, paths | UnravelSports, floodlight | General kinematic preprocessing | **RETAIN CUSTOM** for governed work | Very high: filters and edge handling change results | Validated constructs and sensitivities | Community kinematics may be compared in future exploration, never substituted into frozen executions. |
| Generic future kinematics | Not yet separated from analyses | Would support non-governed exploratory football tracking | UnravelSports, floodlight | Savitzky–Golay/low-pass velocity and acceleration tooling | **INVESTIGATE** | Medium: outlier filtering and inferred possession are bundled | None yet | Evaluate only in a sandbox with raw coordinates retained and transformations logged. |
| Focal leave-one-out centroid/path | Phase 4B/4C, Phase 5A/5B | Measures one defender differently from the remaining defending outfield unit | No direct replacement | Project construct using basic geometry | **RETAIN CUSTOM** | Critical | Externally replicated geometric primitive | Keep definition, exclusions, smoothing, controls, and tests project-owned. |
| Directional focal-relative complement | Post-5B direction/onset audit | Retains signed x/y change omitted by scalar path | No direct replacement | Project descriptive representation | **RETAIN CUSTOM** | Critical | Claim-bounded descriptive result | Preserve without tactical interpretation. |
| Attacking movement segmentation | Post-5B segmentation/prominence sources | Tests outcome-blind finite attacking movement units | No direct replacement | Project research logic informed by prior literature | **RETAIN CUSTOM** | Critical | Mixed/negative audit trail | Do not tune or replace during infrastructure migration. |
| Tracking-support/identity QC | `post5b_tracking_support_qc_audit.py` | Diagnoses continuity, colocation, and identity failures | No reviewed exact equivalent | Project QC with possible future community interface | **RETAIN CUSTOM** | High | Protects valid trajectory support | Extract only after broader validation; keep provider evidence and nonclaims. |
| Pitch drawing and trajectory figures | Many notebooks and source plotting functions | Draws rectangles, players, paths, and diagnostic panels | mplsoccer | `Pitch`, `VerticalPitch`, `Standardizer` | **ADOPT** for new figures | Low–medium: orientation and existing figure hashes | Documentation, not numerical results | Use mplsoccer for new football-facing pitch panels; do not regenerate frozen figures solely for style. |
| Formation/position utilities | No accepted project primitive | Potential role/shape context | UnravelSports EFPI; mplsoccer formations | EFPI/template matching or plotting positions | **INVESTIGATE** | High: inferred roles could leak semantics | Current protocols avoid role inference | Consider only as a separately validated contextual feature, not a replacement for references. |
| Pressing intensity | None | Models time-to-intercept/probability matrices | UnravelSports | `PressingIntensity` | **DO NOT USE** now | High: adds reaction and interception assumptions | Outside current inference level | Revisit only for a prospectively justified football question. |
| Graph/GNN tooling | None | Converts frames to graphs and trains models | UnravelSports | Graph converter/model stack | **DO NOT USE** | Very high complexity and interpretability risk | Explicitly outside current research | Do not add merely because the package provides it. |
| Event action/value representation | Raw Metrica/Sportec events only | Provides clocks, exclusions, and possession context | socceraction | SPADL/atomic-SPADL, xT, VAEP | **DO NOT USE** now; **INVESTIGATE** later | High: changes the question from tracking geometry to action/value | Value is beyond the current ladder | Consider SPADL only when a later event-context or value protocol exists; do not add xT/VAEP now. |
| Alternative canonical sports objects | None | Could represent XY, Events, Pitch, filters | floodlight | `XY`, `Events`, `Pitch`, transforms, IDSSE loader | **DO NOT USE** as a second canonical layer | High duplication with Kloppy | None | Avoid competing abstractions; investigate isolated QC/filter routines only if Kloppy/UnravelSports lack them. |
| Hashes, manifests, frozen config, controls, classifications | All governed sources/configs/outputs | Preserves prospective design and result provenance | None | Project research-design infrastructure | **RETAIN CUSTOM** | Critical | Entire evidence hierarchy | Keep immutable and versioned; community loaders must report their versions and transformation manifests into this layer. |

## 4. Kloppy assessment

Kloppy is the strongest candidate for the provider-normalization boundary. Its official provider table includes both event and tracking support for **Metrica** and **Sportec**, and its Sportec loader explicitly supports the seven open IDSSE matches already used here. It also supports relevant future tracking providers including PFF, Second Spectrum, Signality, SkillCorner, Stats Perform, Tracab, and Hawkeye 2D, with provider-specific limitations documented by Kloppy. See the [official provider matrix](https://github.com/PySport/kloppy#supported-data-providers), [Metrica tracking example](https://kloppy.pysport.org/user-guide/concepts/tracking-data/), and [Sportec/IDSSE loader](https://kloppy.pysport.org/user-guide/loading-data/sportec/).

### Representation and coordinates

Kloppy loads tracking into an object-oriented `TrackingDataset` containing `Frame` objects. Frames expose period-aware time, `frame_id`, player coordinates, ball coordinates, ball state, and ball-owning team where available. Metadata describes teams/lineups, periods, frame rate, provider, orientation, and coordinate system. The default `KloppyCoordinateSystem` is a unit square with x left-to-right and y bottom-to-top; explicit transformations can retain or convert to provider systems and orientations. Kloppy can export directly to Pandas or Polars. These capabilities are documented in its [tracking model](https://kloppy.pysport.org/user-guide/concepts/tracking-data/), [domain metadata](https://kloppy.pysport.org/reference/domain/models/), [coordinate transformations](https://kloppy.pysport.org/user-guide/transformations/coordinates/), and [dataframe export guide](https://kloppy.pysport.org/user-guide/getting-started/).

That normalization is useful but is also the principal migration risk. Moving the Defense currently relies on:

- Metrica's global `Frame` and `Time [s]` columns;
- IDSSE absolute provider timestamps represented as nanoseconds plus period kickoffs;
- provider IDs and explicit validity masks;
- frozen 105 × 68 m scaling;
- precise half-open interval membership;
- goalkeeper and on-pitch membership decisions.

Kloppy can represent frame numbers, period time, IDs, teams, lineups, ball state, possession where supplied, provider, and orientation. It should not yet be assumed to preserve the *raw serialization* of absolute timestamps, every provider-specific validity attribute, or every auxiliary XML field. The future adapter must therefore retain a raw provenance sidecar and verify these fields rather than treating a successful load as equivalence.

### Direct Polars versus UnravelSports

Kloppy already supports direct `to_df(engine="polars")`. That is the preferable minimal bridge when the need is only a canonical table. UnravelSports' `KloppyPolarsDataset` is a richer processing layer: it converts to a long Polars representation, standardizes coordinates to a Second Spectrum-style system, derives velocity/acceleration, may filter extreme kinematics, may infer ball carrier/possession, can infer goalkeepers, and can orient to the ball-owning team. Those additions are valuable conveniences but are not neutral for this project. Use direct Kloppy→Polars first; investigate UnravelSports only for explicitly requested derived infrastructure.

### Deletion candidates after equivalence—not before

If equivalence is demonstrated, future code could delete duplicated Metrica header flattening and file merging from `phase4b_focal_departure_validation.py`, `post5b_attacking_movement_segmentation_audit.py`, `post5b_measurement_audit_direction_onset.py`, and `post5b_tracking_support_qc_audit.py`. The bespoke Phase 4C XML parser and cache may eventually become a compatibility/provenance adapter over Kloppy Sportec data, but it should be the **last** loader retired because Phase 4C–5B depend on its exact timestamp, validity, event-state, and identity behavior. Historical committed sources remain part of the audit trail even after a new loader exists.

## 5. UnravelSports assessment

UnravelSports is best treated as an optional layer above Kloppy, not the provider source of truth. Its official documentation describes a `KloppyPolarsDataset` with period/timestamp/frame IDs, player/team IDs, positions, derived velocity and acceleration, ball state, ball-owning team, ball carrier, position name, and game ID. Its conversion pipeline also standardizes coordinates, optionally smooths derivatives, filters kinematic outliers, infers missing possession/ball carrier, infers goalkeeper position, and can reorient play. See the [dataset API](https://unravelsports.readthedocs.io/en/latest/api/soccer/dataset.html) and [project repository](https://github.com/UnravelSports/unravelsports).

| Component | Classification | Reason for Moving the Defense |
|---|---|---|
| `KloppyPolarsDataset` long-table bridge | **INVESTIGATE / INTEGRATE selectively** | Convenient and football-aware, but it bundles transformations and inference. Direct Kloppy→Polars is safer for the first equivalence pass. |
| Velocity/acceleration derivation | **INVESTIGATE** | Useful for future non-governed exploration; it cannot replace frozen centered/trailing smoothing, edge handling, missingness, or finite differences. |
| Kinematic outlier filtering | **DO NOT USE** in governed paths | The project deliberately retained and diagnosed a 56.30 m/s discontinuity. Silent filtering would erase evidence and change support. |
| Ball carrier/possession inference | **DO NOT USE** by default | Threshold inference is uncertain in contested situations and cannot replace provider/event possession in frozen sample logic. |
| Goalkeeper inference | **INVESTIGATE** only as a QC cross-check | Goalkeeper identity determines the defensive reference set; metadata identity remains primary. |
| Orientation normalization | **INVESTIGATE** | Ball-owning-team orientation is useful for later work but would alter signed coordinates and cannot replace frozen period orientation. |
| Pressing intensity | **DO NOT USE** now | Time-to-intercept and reaction assumptions answer a different question and add an unvalidated model layer. |
| EFPI formation/position identification | **INVESTIGATE** later | Potential context, but inferred formation/roles are neither needed nor validated for current constructs. |
| Graph conversion and GNN tools | **DO NOT USE** | No current scientific need; conflicts with interpretability and explicit scope. |

UnravelSports does **not** replace focal-relative defensive movement. Its dataframe and kinematic layers describe objects and derivatives. The project primitive excludes the focal defender and goalkeeper from a contemporaneous defending-outfield centroid, applies frozen support/smoothing rules, accumulates the two-dimensional relative path, and was tested with translation, misalignment, activity, sensitivity, held-out, and cross-provider controls. Similar inputs do not imply equivalent estimands or validation.

## 6. Other ecosystem tools

### mplsoccer — adopt for new football-facing pitch figures

`mplsoccer` supplies football pitch types, consistent dimensions/orientation, standardization, scatter/line/arrow helpers, formations, grids, Voronoi/Delaunay, and animation support. It is the clearest low-risk adoption. New trajectory and snapshot figures should use a small project wrapper around `Pitch`/`VerticalPitch` so visual orientation, colors, units, and captions are consistent. Existing validated or explanatory figures should not be regenerated merely to change style. See the [official repository](https://github.com/andrewRowlinson/mplsoccer) and [pitch gallery](https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_plots/).

### socceraction — later event semantics/value, not current infrastructure

`socceraction` standardizes on-ball event streams into SPADL/atomic-SPADL and implements xT, VAEP, and Atomic-VAEP. It is relevant only if a later frozen protocol needs provider-independent on-ball action context or downstream value. The current project is deliberately below tactical attribution and value, and its tracking temporal units must not be defined by later outcomes. Classification: **DO NOT USE now; INVESTIGATE later for event representation, not for current tracking geometry**. See the [official repository](https://github.com/ML-KULeuven/socceraction).

### floodlight — useful reference, not a second canonical abstraction

Floodlight offers provider-independent `XY`, `Events`, `Pitch`, transformations, filters, plotting, centroids, distances, velocities, accelerations, space control, and an IDSSE dataset interface. That overlap is real, but adopting both Kloppy and Floodlight as canonical layers would duplicate coordinate, metadata, and object semantics. Classification: **DO NOT USE as the main representation**. Its low-pass filtering, trajectory manipulation, or IDSSE parser may be useful as independent equivalence/QC comparators if a specific gap remains. See the [official repository](https://github.com/floodlight-sports/floodlight).

### Polars — integrate at ingestion and large-table boundaries

Polars fits naturally for long tracking tables, provider-normalized ingestion, joins, grouped completeness summaries, and lazy scans of future multi-match data. It should not trigger a wholesale notebook rewrite. Pandas remains appropriate for committed exploratory notebooks, compact result tables, and protocol code whose outputs are already frozen; NumPy remains appropriate for explicit trajectories, smoothing, geometry, and closed-form models. A future adapter should return Polars at the canonical storage boundary and explicit NumPy arrays/Pandas frames at governed compatibility boundaries. See the [official Polars repository](https://github.com/pola-rs/polars).

## 7. Scientific preservation map

### A. Community infrastructure

- provider loading for Metrica and Sportec/IDSSE;
- provider/team/player/period/frame metadata;
- coordinate-system descriptions and explicit transforms;
- ball coordinates/state and provider possession when present;
- canonical long dataframe conversion;
- standard football pitch plotting;
- optional generic kinematics for future non-governed work.

### B. Moving the Defense measurement

- defending-outfield membership and leave-one-out centroid;
- focal-relative x/y trajectory and accumulated path;
- signed focal-relative displacement complement;
- exact smoothing, support, missingness, and interval semantics;
- attacking movement segmentation and its preserved mixed/negative refinements;
- trajectory-continuity and identity-support QC;
- opponent-geometry representations already tested.

### C. Moving the Defense research design

- frozen protocol/config artifacts and hashes;
- development, held-out, and external-replication roles;
- common-sample and leakage rules;
- translation, misalignment, shifted-time, locality, and other negative controls;
- materiality criteria, A/B/C classifications, and stopping rules;
- claim ledger, inference ladder, nonclaims, and historical audit trail.

Community code may supply A. It may not silently redefine B or C.

## 8. Proposed future architecture

```text
immutable provider files + hashes
        │
        ▼
Kloppy provider loaders (raw/provider orientation first)
        │
        ├── raw/provenance sidecar
        │   provider IDs, source timestamps, validity fields, file hashes,
        │   Kloppy/package versions, coordinate/orientation transforms
        ▼
Moving the Defense canonical adapter
        │
        ├── long Polars table for storage/interchange
        ├── explicit source and 105 × 68 m coordinate columns
        ├── raw frame/time plus period-relative time
        └── deterministic compatibility views for NumPy/Pandas
        ▼
project-owned measurement layer
        │ focal-relative geometry, signed change, support QC,
        │ segmentation research, exact frozen smoothing
        ▼
project-owned protocol/validation layer
        │ samples, controls, held-out logic, classifications, manifests
        ▼
presentation layer
        └── mplsoccer for new pitch figures; Matplotlib/statistical panels
```

UnravelSports sits beside the canonical adapter as an optional derived-feature comparator, not inside the first equivalence-critical path. Socceraction is a later optional event/action branch. Floodlight is an independent comparator only, not another source of truth.

## 9. Numerical-equivalence migration plan

No loader migration is complete until one already-used Metrica match and one already-used IDSSE/Sportec match pass a versioned equivalence harness.

### Frozen comparison fixtures

- **Metrica:** Sample Game 1, using existing ignored raw files and a fixed set of frames spanning both periods, missingness, ball rows, substitutions/support changes, and frozen Phase 4/post-5B windows.
- **IDSSE/Sportec:** one of the seven existing Phase 4C matches chosen before reading comparison results, with fixed period starts, events, validity gaps, players, and Phase 4C focal windows.
- The current pipeline is path A; Kloppy plus the proposed adapter is path B.

### Required comparisons

| Field/result | Expected comparison | Proposed tolerance |
|---|---|---|
| Raw file hashes | Exact | Byte equality |
| Period IDs and order | Exact | Equality |
| Frame IDs and order | Exact after documented string/type normalization | Equality; no dropped/duplicated frames |
| Player/team/provider IDs | Exact | Equality after a frozen reversible mapping only |
| Goalkeeper and on-pitch membership | Exact | Equality per tested frame/window |
| Period boundaries | Exact frame membership | Same first/last frame; time difference ≤1 microsecond after common conversion |
| Raw/provider timestamps | Exact where Kloppy exposes them | Equality; otherwise adapter must preserve them from a sidecar before approval |
| Period-relative timestamps | Numerically equivalent | ≤1 microsecond |
| Raw Metrica normalized coordinates | Numerically equivalent without orientation transform | ≤1e-9 normalized units |
| Raw IDSSE physical coordinates | Numerically equivalent without orientation transform | ≤1e-6 m |
| Canonical 105 × 68 m coordinates | Numerically equivalent | ≤1e-6 m per component |
| Orientation/sign | Exact transform identity | Same transform matrix/period/team; no implicit flip |
| Ball coordinates/state | Exact mask/state; numeric tolerance as above | Mask equality and coordinate tolerance |
| Possession/team state | Exact when provider-supplied | Equality; inferred values must be separated and cannot satisfy this gate |
| Missing/validity masks | Exact | Boolean equality for every object/frame |
| Event-to-frame synchronization | Exact candidate/frame assignment | Same frame and half-open interval membership |
| Selected focal-relative x/y | Numerically equivalent | ≤1e-6 m per component |
| Selected focal-relative path | Numerically equivalent under the existing project measurement | Absolute difference ≤1e-5 m |
| Frozen eligible/sample keys | Exact | Set and order equality where order is governed |

The first equivalence run must use no orientation normalization, kinematic filtering, possession inference, interpolation, or missing-value filling. A second explicitly named transformation test may compare Kloppy's normalized coordinates against a hand-computed expected transform. Differences must be classified as parser defect, metadata mismatch, intended representation difference, or unresolved; they must not be averaged away.

The harness should write package versions, inputs, transform settings, maximum errors, mismatch keys, and pass/fail decisions to machine-readable output. It must not overwrite historical outputs or claim that numerical equivalence validates football meaning.

## 10. Contribution-back opportunities

| Candidate | Assessment | Why |
|---|---|---|
| Trajectory continuity and identity QC | **Potentially upstream contribution; needs more validation first** | Provider-aware duplicate/near-coincident traces, restoration jumps, and support evidence could complement loader validation without imposing tactical semantics. |
| Provider-agnostic tracking-support validation | **Potentially standalone module; needs more validation first** | Explicit masks, continuity evidence, frame/time checks, and provenance manifests are broadly useful across providers. |
| Kloppy equivalence fixtures for open Metrica/IDSSE | **Potentially upstream contribution** | Small regression fixtures or documented edge cases could improve provider adapters after issues are reproduced independently. |
| Cross-provider validated focal-relative geometry | **Too project-specific now; potentially standalone later** | The primitive is simple, but its reference membership, controls, and claim boundaries are the scientific contribution and need broader use before extraction. |
| Outcome-blind attacking movement segmentation | **Needs more validation first** | Current method and prominence refinement are both B; exporting now would prematurely bless an unresolved temporal unit. |
| Defensive-response primitives | **Too project-specific / needs much more validation** | Tactical response and attacker attribution remain unvalidated. |
| Protocol/negative-control templates | **Potentially standalone methodological examples** | Frozen configs, hashes, stopping rules, and control logic may be reusable without exporting empirical claims. |

No package, pull request, or upstream issue is opened in this pass.

## 11. Licensing and dependency notes

| Project | License | Dependency implication |
|---|---|---|
| Moving the Defense | MIT | Current project license; dependency notices remain separate and must be retained as required. |
| [Kloppy](https://github.com/PySport/kloppy) | BSD 3-Clause | Permissive; preserve copyright/license notices when redistributing covered source or substantial copies. |
| [UnravelSports](https://github.com/UnravelSports/unravelsports) | Mozilla Public License 2.0 | File-level copyleft applies to modifications of MPL-covered source files distributed by the project. Ordinary use as an imported dependency does not make unrelated Moving the Defense files MPL, but notices and license terms still apply. |
| [mplsoccer](https://github.com/andrewRowlinson/mplsoccer) | MIT | Permissive; retain license/copyright notice with redistributed source copies. |
| [socceraction](https://github.com/ML-KULeuven/socceraction) | MIT | Permissive; citation is encouraged by the project. Its provider data terms remain separate from package licensing. |
| [floodlight](https://github.com/floodlight-sports/floodlight) | MIT | Permissive; retain notices with redistributed source copies. |
| [Polars](https://github.com/pola-rs/polars) | MIT | Permissive; retain notices with redistributed source copies. |

Importing a package as a declared dependency is different from copying or modifying its source. This project should depend on released packages, pin versions for governed executions, record transitive licenses, and avoid vendoring. If third-party code is ever adapted rather than imported, the exact source, version, license, attribution, and modification history must be preserved. Dataset licenses and commercial-provider agreements are independent of software licenses. This is an engineering summary, not legal advice.

Compatibility must be checked in an isolated environment before adoption. The audited repository uses Python 3.13.15; `socceraction` 1.5.3 declares Python below 3.13 and therefore cannot enter the current environment without a separate compatible environment or a future upstream release. Floodlight 1.2.0 declares Python 3.10–3.13, and current mplsoccer requires Python 3.10+. Kloppy and UnravelSports versions and transitive requirements must be pinned at the time of an equivalence experiment; the reviewed UnravelSports documentation and repository metadata are not fully version-aligned, which is another reason not to add it to the first ingestion gate.

## 12. Recommended migration order

1. **Create the equivalence harness before changing ingestion.** Freeze fixtures, field mappings, tolerances, and downstream focal-relative comparisons.
2. **Add Kloppy in an isolated optional environment.** Load Metrica Game 1 and one predeclared IDSSE match without transformations; write no replacement outputs.
3. **Define the thin canonical adapter and provenance sidecar.** Prefer direct Kloppy→Polars; preserve raw IDs/times/masks and explicit 105 × 68 m transforms.
4. **Pass Metrica equivalence.** Only then use the adapter for new Metrica work; historical sources stay untouched.
5. **Pass IDSSE equivalence.** Retire bespoke XML plumbing only after all Phase 4C/5A/5B sample keys and focal-relative quantities match.
6. **Adopt mplsoccer for new pitch figures.** This can proceed independently because it does not alter numerical artifacts.
7. **Evaluate UnravelSports components one at a time.** Directly compare kinematics/orientation/inference against explicit project choices; keep them out of governed paths until separately accepted.
8. **Revisit socceraction or floodlight only after a concrete protocol needs them.** Do not accumulate ecosystem dependencies speculatively.

The highest-value first migration is therefore **a Kloppy-backed, equivalence-tested Metrica ingestion adapter with direct Polars export and a raw provenance sidecar**. It removes repeated plumbing while keeping the scientific layer unchanged.

## 13. Explicitly not changing yet

- no dependency is added in this audit;
- no Kloppy, UnravelSports, Polars, mplsoccer, socceraction, or floodlight migration is executed;
- no notebook or historical source is rewritten;
- no raw, cached, result, figure, or machine-readable scientific artifact is regenerated;
- no frozen protocol, threshold, sample, control, or classification changes;
- no focal-relative measurement, smoothing, interval, missingness, or goalkeeper rule changes;
- no tracking discontinuity is filtered or repaired;
- no direction split or attacking-segmentation tuning occurs;
- no GNN, graph model, pressing model, formation inference, xT, VAEP, gravity, or value model is introduced;
- no Metrica Game 3 access and no new research experiment.

This audit recommends infrastructure boundaries and tests. It does not alter the evidence hierarchy or scientific claims.
