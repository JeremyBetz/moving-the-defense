# UnravelSports Interoperability Audit

**Classification:** **B — useful interoperability/reference layer, but no governed pipeline integration yet**

**Tested package:** UnravelSports 1.2.1 on Python 3.13.15, with Kloppy 3.19.0, Polars 1.44.1, and SciPy 1.18.1

**Data boundary:** Kloppy `limit=250` from Metrica Sample Game 1 and IDSSE/Sportec `J03WMX`, yielding 249 and 250 frames respectively; no other match and no defensive outcome

## 1. Purpose

This audit asks whether UnravelSports can sit above or beside the governed Moving the Defense ingestion architecture without silently changing its meaning:

> raw provider data → Kloppy → governed provider adapter → canonical Polars table + provenance → project-owned football measurement

It is an infrastructure comparison, not a football experiment. The canonical contract remains authoritative. No historical loader, output, protocol, threshold, measurement, or claim changes.

## 2. Version, compatibility, dependencies, and license

UnravelSports 1.2.1 declares Python `>=3.11`, Kloppy `>=3.18.0`, Polars `>=1.35.0`, and SciPy `>=1.0.0`. It installed cleanly into the existing Python 3.13.15 environment. Because Kloppy and Polars were already present, the only additional runtime package was SciPy 1.18.1. Optional test/graph extras—including PyTorch, PyTorch Geometric, TensorFlow, Keras, and Spektral—were not installed.

UnravelSports is licensed under [MPL-2.0](https://github.com/UnravelSports/unravelsports/blob/main/LICENSE). Importing the package as a dependency does not copy its source into this repository. If an MPL-covered source file were modified and distributed, the MPL notice and source-availability obligations would apply to that file. This project neither copies nor modifies third-party source.

Primary references are the [official repository](https://github.com/UnravelSports/unravelsports), [dataset API](https://unravelsports.readthedocs.io/en/latest/api/soccer/dataset.html), and [model API](https://unravelsports.readthedocs.io/en/latest/api/soccer/models.html).

## 3. Current API/components reviewed

| Component | What it does | Decision | Reason |
|---|---|---|---|
| `KloppyPolarsDataset` | Transforms a Kloppy tracking dataset into long Polars data with positions, kinematics, possession/carrier, and position metadata | **REFERENCE ONLY** | Useful reference representation, but conversion bundles orientation, inference, filtering, null-row removal, and derived fields. |
| Canonical compatibility view | Renames governed canonical columns into a conservative Unravel-shaped table | **INTEGRATE** | Safe, row-preserving, and noninferential; useful for inspection/export, though current Unravel model classes still require their own dataset wrapper. |
| Velocity/acceleration | First differences; optional Savitzky–Golay smoothing; scalar outlier caps | **REFERENCE ONLY** | Shared complete-row velocity matched here, but defaults and support behavior do not match every governed use. |
| Pressing intensity | Frame-level time/probability-to-intercept matrices | **DEFER** | Adds interception, reaction-time, speed, possession, and probability assumptions not needed by the current research question. |
| EFPI | Template/assignment-based formation and contextual position identification | **DEFER** | Potential later structural context, but it infers spatial formation positions and does not replace a validated movement primitive. |
| Graph conversion/training | Converts frames to graph samples and supports GNN workflows | **DO NOT USE** | No present scientific need; substantial dependency and interpretability cost. |
| Object/team/player helpers | Player/team lookups and standardized object metadata | **REFERENCE ONLY** | Convenient but canonical namespaced identities and goalkeeper provenance remain authoritative. |

## 4. Kloppy → Polars interoperability

The comparison deliberately disabled possession-based orientation and compared the same bounded Kloppy datasets:

1. Kloppy → Moving the Defense adapter → canonical Polars;
2. Kloppy → `KloppyPolarsDataset`, with `orient_ball_owning=False`.

The representations are not directly interchangeable.

| Provider | Canonical rows | Canonical valid-coordinate rows | UnravelSports rows | Shared rows | Raw max coordinate difference | Difference after explicit axis mapping |
|---|---:|---:|---:|---:|---:|---:|
| Metrica | 7,221 | 5,727 | 5,727 | 5,727 | 65.343 m | $1.42\times10^{-14}$ m |
| IDSSE/Sportec | 10,250 | 5,750 | 5,750 | 5,750 | 98.940 m | $1.78\times10^{-14}$ m |

The large raw differences are orientation differences, not measurement error. UnravelSports transforms to a Second Spectrum coordinate system and `STATIC_HOME_AWAY` orientation. Returning to the governed fixed frame required `(x,+; y,-)` for this Metrica sample and `(x,-; y,-)` for this IDSSE sample. These mappings must be explicit and provider-tested; they cannot be assumed from matching units.

### Membership, identity, metadata, ball, and support

- The canonical table retains every metadata-roster player plus one ball row per frame. UnravelSports removes rows with null x/y. `J03WMX`, for example, has 41 canonical rows per frame but 23 UnravelSports rows in this opening sample.
- Canonical player/team keys are provider-namespaced and reversible. UnravelSports retains provider IDs directly and uses `ball` as its synthetic ball identity.
- Canonical frame IDs are strings to prevent coercion; UnravelSports uses integer frame IDs here. Both use period-relative duration timestamps, but UnravelSports does not retain the governed match-global clock or raw IDSSE UTC sidecar.
- UnravelSports has no canonical equivalents for `is_present`, `coordinate_valid`, or `support_state`; unsupported rows are dropped rather than described.
- Metrica provides no governed possession. UnravelSports warned and inferred possession/ball carrier from ball distance; its implementation removes rows lacking an inferred/provider owning team. That inference and filtering are prohibited in canonical ingestion.
- IDSSE provider possession and ball state are carried into UnravelSports, but raw provider ball identity and full project provenance are not part of the long table.
- Metrica lacks position metadata, so UnravelSports may infer goalkeepers. Canonical goalkeeper identity instead comes from governed provenance.
- Ordering and dtypes differ. They are representational choices, not evidence that either table is canonical for the other project.

## 5. Canonical-contract compatibility

UnravelSports can work in three positions, with different consequences:

1. **Directly from Kloppy:** technically works, but invokes its full transform/inference/filter pipeline. Appropriate only for isolated reference utilities.
2. **Directly from canonical Polars:** current `PressingIntensity`, `EFPI`, and graph APIs require a `KloppyPolarsDataset`, so direct consumption is not supported.
3. **Through a thin compatibility view:** the new `canonical_to_unravel_reference_view` maps canonical names into familiar columns while retaining namespaced IDs, null rows, provider possession only, and fixed coordinates. It intentionally omits inferred carrier, roles, kinematics, and models.

The preferred direction is therefore:

> canonical Moving the Defense table → thin, declared compatibility view → bounded optional/reference utility

The reverse direction must not redefine the canonical table. The compatibility view is an integration seam, not a second canonical data model and not a promise that every UnravelSports model can consume it unchanged.

## 6. Kinematics comparison

The bounded comparison used:

- **project rule:** centered seven-frame rolling mean of x/y position, followed by backward first difference divided by observed time difference;
- **UnravelSports default:** backward position difference, followed by a seven-frame, first-order Savitzky–Golay filter on velocity; acceleration is then differenced; scalar speed and acceleration are capped at configured maxima.

After the same explicit axis mapping, shared finite player rows agreed closely:

| Provider | Shared finite rows | Velocity-component MAE | Maximum component difference | Speed correlation |
|---|---:|---:|---:|---:|
| Metrica | 5,324 | $3.70\times10^{-14}$ m/s | $3.55\times10^{-13}$ m/s | 1.000 |
| IDSSE/Sportec | 5,346 | $4.39\times10^{-14}$ m/s | $4.82\times10^{-13}$ m/s | 1.000 |

This shows numerical equivalence for the shared complete interior rows in this sample because these two linear seven-frame operations coincide there. It does **not** make UnravelSports an exact governed substitute. It initializes derivatives at group edges, drops null-coordinate rows before final output, caps scalar speed at 12 m/s and acceleration at 6 m/s² for players, applies different ball smoothing, derives acceleration, and bundles possession/orientation behavior. No cap was reached in this bounded opening sample, so the cap behavior was not validated here. Project rules remain authoritative wherever frozen.

## 7. Pressing-intensity assessment

`PressingIntensity` produces time-to-intercept and probability-to-intercept matrices between attacking and defending objects. It uses positions and velocities plus configurable assumptions including reaction time, maximum speed, time horizon, sigmoid steepness, team/ball handling, and possession-defined orientation. Possession is therefore operationally important; when unavailable upstream, the dataset wrapper may infer it.

This may later provide a comparison for a specifically justified pressure/coverage question. It is not a neutral preprocessing utility and has no immediate role in measuring how a defender moved differently from the defensive unit. **Decision: DEFER.**

## 8. EFPI assessment

EFPI matches player spatial distributions to formation templates through linear assignment. It can operate per frame, possession, period, or time window; it returns formation and spatial position assignments, may average within intervals, filters frames with fewer than ten outfield players, and offers a change threshold for temporally aggregated fits.

EFPI addresses formation/template position, not focal-versus-collective movement. It does not replace the leave-one-out defending-outfield centroid, focal-relative path, directional complement, or support rules. It could later become a separately validated contextual descriptor, but role/position inference would raise new leakage, selection, and interpretation questions. **Decision: DEFER.**

## 9. Graph-tooling assessment

`SoccerGraphConverter` creates player/ball nodes, configurable edges and features, graph IDs, labels, and train/validation/test inputs for PyTorch Geometric or Spektral workflows. These tools are substantial modeling infrastructure, not an ingestion requirement. No graph or GNN question is currently authorized, and optional graph dependencies were not installed. **Decision: DO NOT USE.**

## 10. Scientific boundary

| UnravelSports component | Football concept | Inputs | Outputs | Potential use | Overlap with current construct | Status | Scientific risk |
|---|---|---|---|---|---|---|---|
| Dataset wrapper | Standard tracking table | Kloppy tracking | Long Polars plus inferred/derived fields | Reference interoperability | Infrastructure only | **REFERENCE ONLY** | Silent orientation, possession, row, and support changes |
| Compatibility view | Interchange | Canonical Polars | Loss-aware familiar columns | Optional exports/tests | No measurement overlap | **INTEGRATE** | Consumers may assume missing derived fields |
| Kinematics | Player/ball motion | Positions and time | velocity, speed, acceleration | Non-governed exploration/reference | Similar arithmetic, different policy envelope | **REFERENCE ONLY** | Filtering, edges, missingness, and inference can alter samples |
| Pressing intensity | Pressure/interception | positions, velocity, possession, assumptions | TTI/PTI matrices | Possible later comparator | Does not replace focal-relative movement | **DEFER** | Model assumptions could be mistaken for observed response |
| EFPI | Formation/spatial position | team configurations | template formation/position | Possible later context | Does not replace centroid/path | **DEFER** | Inferred role/shape may be treated as ground truth |
| Graph tooling | Relational model representation | processed frames, features, labels | graphs/model inputs | None now | No validated construct replaced | **DO NOT USE** | Complexity, leakage, and interpretability |

Moving the Defense continues to own focal-relative defensive movement, leave-one-out reference logic, directional complements, segmentation history, tracking-support QC, frozen protocols, negative controls, held-out/external validation, and claim boundaries. Similar library geometry is not scientific equivalence.

## 11. What to adopt now

Adopt only the thin, project-owned compatibility view as an explicit interoperability seam. Keep UnravelSports pinned so this audit is reproducible, but do not place its dataset wrapper in the governed ingestion path. Its source and docs are useful reference implementations for Polars football tooling.

## 12. What to defer

- governed replacement of any kinematics;
- pressing intensity;
- EFPI or inferred formation/position context;
- ball-carrier or possession inference;
- goalkeeper inference;
- possession-oriented coordinates;
- graph conversion, graph models, and deep-learning dependencies.

## 13. What might become useful later

An explicitly parameterized kinematic utility could be reconsidered for new exploratory work after missingness, edges, caps, balls, and discontinuities are tested prospectively. EFPI could be evaluated as contextual metadata only after a research question requires formation context. Pressing intensity could serve as a published model comparator if a later protocol studies pressure rather than treating it as observed truth.

## 14. Contribution/upstream opportunities

- A public canonical-to-Unravel compatibility protocol could help users see where provider IDs, support rows, clocks, and orientations change. **Potentially upstream after more providers are tested.**
- Explicit switches to disable carrier/possession inference, row dropping, scalar caps, and all coordinate orientation would improve loss-aware interoperability. **Potential upstream issue/contribution.**
- Accepting a documented long Polars input independent of `KloppyPolarsDataset` could make individual utilities more reusable. **Potential upstream design discussion.**
- Moving the Defense tracking-support states and provenance sidecars require broader validation before any standalone contribution.
- Focal-relative measurement, segmentation, controls, and validation logic remain project-specific research rather than utility patches.

## 15. Recommendation

Overall classification is **B**. UnravelSports is credible, lightweight at runtime, and valuable as a reference/optional football analytics layer. Its current wrapper is intentionally opinionated and therefore not a lossless canonical bridge. Keep the governed architecture unchanged; use the canonical compatibility view for bounded inspection, retain UnravelSports for reproducible comparisons, and require a new prospective validation before any individual utility enters a scientific pipeline.
