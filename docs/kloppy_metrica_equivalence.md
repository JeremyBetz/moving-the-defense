# Kloppy–Metrica Game 1 Equivalence Experiment

**Status:** completed infrastructure experiment; **B — mostly compatible, explicit adapter required**

**Scope:** Metrica Sports Sample Game 1 only. This experiment did not replace the current loader, change a validated measurement, inspect another match, infer possession, interpolate tracking, or use UnravelSports.

## 1. Purpose

This experiment asks whether Kloppy can become a future provider-normalization layer without changing the geometric measurements already validated by Moving the Defense. It is an equivalence test, not a migration. The existing project loader and the experimental Kloppy path loaded the same raw files independently; project-owned Phase 4 smoothing and measurement code then processed both representations.

The result is **B**, rather than A, because equivalence depends on explicit project adapter rules. Kloppy 3.19.0 reverses the raw Metrica y-axis, uses period-relative timestamps, exposes different native team/player identifiers, and does not identify the Metrica goalkeepers through native position metadata. In addition, independently regenerating a frozen negative-control pairing from numerically equivalent Kloppy geometry exposed sensitivity at one activity-bin boundary. With the already-frozen control interval identities held constant, every tested downstream quantity passed its numerical tolerance.

## 2. Environment and raw provenance

- Kloppy: **3.19.0**, pinned in `requirements-phase0.txt`
- Provider: Metrica
- Match: Sample Game 1
- Frame rate: 25 Hz
- Project analysis pitch: 105 × 68 m
- Home tracking SHA-256: `0a3d0eff7785950379c587d3597b86a2d91c2492281b4652e1abb97c99b6b364`
- Away tracking SHA-256: `0a3df68a92af0290ede472e62de3b6489ddee29223da09bdf0cf76c8e0ab0618`

The authoritative machine-readable result, input hashes, source hashes, protocol hash, tolerances, and provenance are in [`equivalence_result.json`](../outputs/kloppy_metrica_equivalence/equivalence_result.json).

## 3. Two representations

### Current project pipeline

The current Phase 4 loader reads the two raw tracking CSVs, preserves provider `Period`, `Frame`, and global `Time [s]`, combines home/away player columns, and retains raw normalized Metrica coordinates and nulls. Existing Phase 4 functions then scale coordinates to 105 × 68 m, apply the frozen seven-frame smoothing, construct leave-one-out defending-outfield centroids, and calculate focal-relative outcomes.

### Experimental Kloppy adapter

[`kloppy_metrica_adapter.py`](../src/infrastructure/kloppy_metrica_adapter.py) loads the same files with `metrica.load_tracking_csv(..., coordinates="metrica")`. It exposes a canonical long schema with one explicit row per rostered player and ball per frame:

`period`, `frame_id`, `provider_time_s`, `kloppy_period_time_s`, `object_type`, `team_id`, `player_id`, `kloppy_player_id`, `is_goalkeeper`, `observed`, `x_norm`, `y_norm`, `x_m`, `y_m`.

The complete logical table contains 4,205,174 rows and is generated in chunks; only a five-frame schema sample is committed. A compatibility view reconstructs the existing wide project columns solely for this comparison. It is not a replacement loader.

## 4. Structural equivalence

| Check | Current | Kloppy adapter | Result |
|---|---:|---:|---|
| Frames | 145,006 | 145,006 | Exact |
| Period 1 frames | 71,268 | 71,268 | Exact |
| Period 2 frames | 73,738 | 73,738 | Exact |
| Provider frame IDs | — | — | Exact sequence |
| Provider global timestamps | — | — | Exact sequence after sidecar preservation |
| Period membership/boundaries | — | — | Exact |
| Roster IDs | 14 Home + 14 Away | 14 Home + 14 Away | Exact after reversible mapping |
| Observed ball frames | 88,251 | 88,251 | Exact |

Kloppy native team IDs are `home` and `away`; the adapter maps these to the project’s `Home` and `Away`. Kloppy native Metrica player IDs such as `home_1` are retained in `kloppy_player_id`, while the provider jersey-number identity used by the project is exposed separately and reversibly.

Kloppy reports every Metrica player position as unknown, so native goalkeeper identification is unavailable. The adapter therefore uses the existing frozen Game 1 identities, Home 11 and Away 25, and records that provenance explicitly. This rule must remain a provider metadata rule, not a new inference.

## 5. Coordinates, orientation, and time

Kloppy 3.19.0 reverses raw Metrica y during parsing even when the requested coordinate system is `metrica`. Before adaptation, the relationship is exact:

$$
y_{\mathrm{Kloppy}} = 1-y_{\mathrm{project\ raw}},
$$

with correlation −1.0 and zero maximum residual in the identity above. The adapter therefore applies the documented inverse `project_y_norm = 1 - kloppy_y_norm` before multiplying x by 105 m and y by 68 m. It does not orient coordinates by period or possession.

After adaptation, all valid coordinate comparisons passed a normalized tolerance of $10^{-12}$:

| Object/axis | Valid observations | Maximum absolute difference | Median | 99th percentile | Mismatches |
|---|---:|---:|---:|---:|---:|
| Player x | 3,190,138 | 0 | 0 | 0 | 0 |
| Player y | 3,190,138 | $1.11\times10^{-16}$ | 0 | $5.55\times10^{-17}$ | 0 |
| Ball x | 88,251 | 0 | 0 | 0 | 0 |
| Ball y | 88,251 | $1.11\times10^{-16}$ | 0 | $5.55\times10^{-17}$ | 0 |

The largest physical-coordinate discrepancy is approximately $7.55\times10^{-15}$ m.

Kloppy timestamps are period-relative. Period 1 begins at 0.04 s in both representations, but Kloppy period 2 begins at 0.04 s while the provider global time is 2,850.76 s. The period-2 offset is therefore 2,850.72 s. The adapter preserves the raw global time by reading the provider frame/time fields as a structural sidecar; it exposes both clocks instead of silently substituting one for the other.

## 6. Missingness and support

Player and ball missingness masks were exact for every compared coordinate. Kloppy omits unsupported players from a frame’s coordinate mapping; the adapter restores an explicit row for every rostered player with `observed = false` and null coordinates. A missing ball is likewise emitted as an explicit null ball row. No interpolation or automatic repair is used.

The independent Phase 4 sample construction produced the same 422 eligible five-second intervals from 1,158 grid intervals, with identical interval IDs and identical attrition:

- possession change: 273;
- incomplete ball support: 413;
- restart: 43;
- no possession: 7;
- frame or membership failure: 0.

This establishes equivalence for Game 1 support under the tested adapter; it does not establish equivalence for another provider or match.

## 7. Downstream focal-relative equivalence

Both pipelines independently used the existing seven-frame smoothing and Phase 4 functions. The comparison covered 4,220 focal-player outcomes across all 422 eligible windows, plus 1,004,360 component observations for each pointwise representation.

| Quantity | Maximum absolute difference | 99th percentile | Tolerance | Mismatches |
|---|---:|---:|---:|---:|
| Leave-one-out centroid components | $2.13\times10^{-14}$ m | $7.11\times10^{-15}$ m | $10^{-9}$ m | 0 |
| Focal-relative components | $2.84\times10^{-14}$ m | $1.07\times10^{-14}$ m | $10^{-9}$ m | 0 |
| Focal-relative path | $3.42\times10^{-14}$ m | $1.42\times10^{-14}$ m | $10^{-8}$ m | 0 |
| Signed focal-relative x change | 0 m | 0 m | $10^{-8}$ m | 0 |
| Signed focal-relative y change | $2.13\times10^{-14}$ m | $1.42\times10^{-14}$ m | $10^{-8}$ m | 0 |
| Focal-relative net displacement | $1.98\times10^{-14}$ m | $1.15\times10^{-14}$ m | $10^{-8}$ m | 0 |
| Leave-one-out centroid path | $2.62\times10^{-14}$ m | $1.24\times10^{-14}$ m | $10^{-8}$ m | 0 |
| Frozen misaligned-control path | $2.91\times10^{-14}$ m | $1.60\times10^{-14}$ m | $10^{-8}$ m | 0 |

The selected 5.00 s, 590.00 s, and 4,195.00 s Phase 4 windows also passed for every focal defender. See [`selected_window_equivalence.csv`](../outputs/kloppy_metrica_equivalence/selected_window_equivalence.csv) and [`downstream_equivalence.csv`](../outputs/kloppy_metrica_equivalence/downstream_equivalence.csv).

## 8. Discrepancy: regenerated negative-control selection

The frozen negative-control identities were reused for the scientific equivalence comparison above. As an additional sensitivity, the deterministic pairing procedure was regenerated independently from each representation. Four interval-level pair assignments differed around 5,425–5,475 s in period 2. The resulting 30 differences among 3,780 finite focal control outcomes (0.794%) reached a maximum of 9.239 m.

This is not a coordinate or focal-relative measurement disagreement. Differences of approximately $10^{-14}$ m moved interval centroid paths across a frozen activity cut, which changed eligible control partners. The finding is still scientifically important: a future migration must either preserve frozen derived sample/control identities or define stable, prospectively governed boundary semantics. It must not silently regenerate governed controls and assume that numerically equivalent inputs guarantee identical discrete membership.

## 9. Equivalence definitions and classification

- **Exact equivalence:** identifiers, provider timestamps, periods, roster mappings, ball observation counts, missingness masks, eligible interval IDs, and attrition must match exactly.
- **Floating-point equivalence:** adapted coordinates and continuous downstream geometry must remain within the predeclared tolerances above.
- **Scientifically material disagreement:** support, sample membership, governed control identity, or validated downstream meaning changes beyond those tolerances.

The result is **B — mostly compatible but requires an explicit adapter or resolution of documented differences**. Kloppy is safe enough to continue evaluating as the future Metrica ingestion layer, but it is **not safe to adopt directly** and the existing canonical loader remains authoritative.

Required adapter rules are:

1. reverse Kloppy’s loaded Metrica y-axis back to the project raw convention;
2. preserve provider global frame/time fields alongside Kloppy’s period-relative clock;
3. retain native and project team/player IDs with explicit reversible mappings;
4. source goalkeeper identity from governed provider/project metadata rather than Kloppy’s unknown position field;
5. emit explicit null rows for unsupported player and ball observations without interpolation;
6. retain the governed 105 × 68 m analysis pitch and record orientation rather than applying implicit possession orientation;
7. preserve frozen sample/control identities, or separately govern numerical boundary behavior, before any scientific rerun.

No current loader, frozen protocol, result, notebook, or validated output was changed by this experiment.
