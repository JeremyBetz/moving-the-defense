# Continuous Attacking Movement — Game 2 Stage-A Support Result

**Protocol:** [held-out Game 2 continuous-representation v1](../protocols/attacking_continuous_movement_game2_heldout_v1.md)

**Execution date:** 2026-08-31

**Classification:** **STAGE A READY**

**Boundary:** raw trajectory support only; no smoothing, continuous attacker feature, frequency diagnostic, defender/outcome inspection, or attacker-to-defender bridge

## 1. Purpose and chronology

The Stage-A question was:

> Can Game 2 raw canonical trajectory support be governed completely and reproducibly under the prospectively frozen universal, hard-link, and exact-duplication rules before any continuous attacker-movement feature is computed?

This was the first authorized opening of Metrica Sample Game 2 for the continuous attacker-movement held-out replication. Before access, the protocol had frozen the canonical ingestion route, raw support rules, $>20.0$ m/s hard-link rule, five-frame exact same-team duplication rule, bounded-segment handling, registry construction, and READY/BLOCKED criteria. No Game 2 continuous-movement feature existed before this audit.

The audit used only raw tracking support. It stopped before centred smoothing, 1/2/4 s windows, signed displacement, path, straightness, or 25→10 Hz comparison. The validity registry and support segments below are now frozen for a later representation pass.

## 2. Canonical ingestion and provenance

The governed path was:

> raw Metrica tracking CSVs → Kloppy 3.19.0 → Moving the Defense Metrica adapter 1.0.0 → canonical tracking contract 1.0.0

| Property | Result |
|---|---:|
| Canonical match | `metrica:sample-game-2` |
| Teams | `metrica:Home`, `metrica:Away` |
| Periods | 1, 2 |
| Provider frames | 141,156 |
| Canonical logical rows, including players and ball | 3,811,212 |
| Rostered outfield identities | 24 |
| Outfield player-periods | 48 |
| Pitch | 105 × 68 m |
| Coordinates | centred fixed pitch; +x right, +y up |
| Goalkeepers excluded through metadata | Home 11, Away 25 |

The raw match clock comes from Metrica `Time [s]`; period-relative time comes from Kloppy. Provider frames remain global integer identities serialized as canonical strings. No direction normalization, interpolation, clipping, possession inference, or event join occurred.

The two tracking inputs and SHA-256 hashes are preserved in [`canonical_provenance.json`](../../outputs/attacking_continuous_movement_game2_stage_a/canonical_provenance.json). Their hashes are `3f9990ac…64694` (Home) and `aa639f40…3718b` (Away). The sidecar also preserves reversible team/player maps, orientation metadata, transformation rules, pitch dimensions, dependency versions, and support semantics.

## 3. Raw support inventory

The canonical adapter emits explicit null rows for rostered players who are not observed. Counts below precede the hard-link and duplication registry.

| Team | Canonical outfield rows | Observed/coordinate-valid | Universal invalid or unsupported | Finite out-of-bounds retained |
|---|---:|---:|---:|---:|
| Away | 1,552,716 | 1,411,561 | 141,155 | 8,535 |
| Home | 1,835,028 | 1,411,563 | 423,465 | 9,585 |
| **Total** | **3,387,744** | **2,823,124** | **564,620** | **18,120** |

All 564,620 unsupported rows were absent and coordinate-invalid under the canonical provider semantics; there were no internal unsupported gaps between a player's first and last observed rows. Four player-periods started after the period start and four ended before the period end. Those deterministic boundaries describe provider-observed entry/exit only, without tactical or substitution-event interpretation. There was no disappearance/reappearance inside an observed span. Exact player-period first/last frames, clocks, presence counts, coordinate counts, and boundary inventory are in [`raw_support_inventory.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/raw_support_inventory.csv).

Finite out-of-bounds values remain supported, as prospectively required. They were counted rather than clipped or reclassified.

## 4. Frame/time and coordinate integrity

Canonical schema, row-key uniqueness, frame ordering, period membership, provider-frame succession, and both clocks passed. No duplicate/reversed timestamp or unexplained frame/time increment was found within a player-period. The explicitly empty [`frame_time_continuity.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/frame_time_continuity.csv) records that result with its governed schema.

Missing/nonfinite/provider-invalid coordinates were handled only through the universal support registry. No coordinate was repaired or interpolated, and no valid row crossed a missing, period, entry/exit, or continuity boundary.

## 5. Frozen hard raw-link audit

For consecutive valid observed rows on the expected 0.04 s link, the audit calculated only

$$
v_i^{raw}=\frac{\|\mathbf p_i-\mathbf p_{i-1}\|_2}{\Delta t_i}.
$$

There were 1,408 report-only links above 10 m/s and **497 hard links strictly above 20.0 m/s**. Equality would not have flagged. Both teams, 19 players, and 29 player-periods were affected. The maximum was **182.04742033361183 m/s**: Away 15, period 2, frame 67,964 at 2,718.56 s to frame 67,965 at 2,718.60 s, 7.281896813337849 m over the recorded 0.0399999999999636 s. These are trajectory-integrity diagnostics, not physiological or football-performance claims.

The complete link-level record—including players, frames, times, component differences, distance, elapsed time, and speed—is [`raw_link_diagnostics.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/raw_link_diagnostics.csv). Frozen endpoint and bounded-segment handling produced 29 hard-jump registry intervals:

| Player | Period | Inclusive provider-frame interval(s) |
|---|---:|---|
| Away 15 | 1 | 12–58,030 |
| Away 15 | 2 | 67,959–134,795 |
| Away 17 | 1 | 6–44,338 |
| Away 18 | 2 | 117,263–117,264 |
| Away 19 | 2 | 67,957–67,958 |
| Away 20 | 1 | 6–33,427 |
| Away 20 | 2 | 67,947–113,119 |
| Away 21 | 1 | 6–7 |
| Away 22 | 1 | 6–7 |
| Away 24 | 1 | 32,222–32,223 |
| Away 24 | 2 | 67,947–67,948 |
| Home 1 | 1 | 34,925–34,926 |
| Home 10 | 1 | 6–27,359 |
| Home 10 | 2 | 67,947–100,069 |
| Home 12 | 2 | 115,183–131,293 |
| Home 13 | 2 | 112,742–112,745 |
| Home 2 | 1 | 46,120–53,603 |
| Home 2 | 2 | 67,947–120,313 |
| Home 4 | 1 | 12,980–59,568 |
| Home 4 | 2 | 67,947–86,009 |
| Home 5 | 1 | 22–54,272 |
| Home 5 | 2 | 81,476–139,997 |
| Home 6 | 1 | 346–27,550 |
| Home 7 | 1 | 6–7 |
| Home 7 | 2 | 67,963–140,121 |
| Home 8 | 1 | 6–12,970 |
| Home 8 | 2 | 67,947–95,744 |
| Home 9 | 1 | 6–19,428 |
| Home 9 | 2 | 67,949–74,616 |

Those sometimes-long intervals contain 726,886 unique raw rows before overlap with the duplication rule. They are the mechanical consequence of the predeclared rule: consecutive hard links within one continuous observed trace bound invalid support between them. They were not shortened after inspection, and no unusual trajectory at or below 20 m/s was manually excluded.

## 6. Exact-coordinate duplication audit

The audit found 176 maximal exact-coordinate runs across all player pairs. **Fifty-seven** were same-team runs lasting at least five consecutive frames and therefore qualified for exclusion: 2 Away-period-1, 9 Away-period-2, 11 Home-period-1, and 35 Home-period-2 events. They involved 31 distinct identity pairs, 22 players, and 31 player-periods. Qualifying run length had minimum 5, median 43, and maximum 328 consecutive frames. Cross-team equality and shorter same-team runs were reported but remained supported under v1.

Every event's identities, inclusive frames/clocks, duration, team relationship, and qualification status are in [`exact_coordinate_duplication_runs.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/exact_coordinate_duplication_runs.csv). Applying the rule to both identities produced 6,419 unique player-rows before cross-rule overlap; merging only overlapping/touching intervals with the same rule produced 97 registry intervals. No marking, role, identity-correction, or tactical inference selected which player was “right.”

## 7. Frozen validity registry and support segments

The final registry contains **138 intervals**:

| Frozen rule | Registry intervals |
|---|---:|
| Universal invalid/unsupported rows | 12 |
| Hard raw jump, including bounded segments | 29 |
| Sustained exact same-team duplication | 97 |

The registry is [`trajectory_validity_registry.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/trajectory_validity_registry.csv). Each row records match, team, player, period, inclusive frames and clocks, rule, diagnostic IDs, deterministic explanation, and provenance. Complete accounting is:

$$
3{,}387{,}744
-564{,}620
-726{,}886
-6{,}419
+3{,}209
=2{,}093{,}028.
$$

The positive term restores the 3,209 rows shared by hard-jump and duplication exclusions so they are subtracted once. Universal invalid support overlaps neither governed trajectory rule, and no row belongs to all three categories. The final invalid union is **1,294,716 rows**.

The complement contains **2,093,028 valid raw outfield rows** in **134 support segments**: 1,163,019 rows/49 segments for Away and 930,009 rows/85 segments for Home. The 134 segments are the maximal runs remaining after period/entry/exit, universal-support, hard-jump, and duplication boundaries are applied. They are trajectory-support segments—not attacking-movement episodes or football actions. [`valid_support_segments.csv`](../../outputs/attacking_continuous_movement_game2_stage_a/valid_support_segments.csv) freezes exact inclusive frames/clocks, counts, and boundary reasons. A later representation execution must consume this artifact rather than rediscover support.

## 8. Deterministic reproduction and hard QC

An independent execution rebuilt ten governed provenance/QC/registry/support artifacts in a temporary directory. Every file was byte-identical; hashes and comparison are in [`governed_output_hashes.json`](../../outputs/attacking_continuous_movement_game2_stage_a/governed_output_hashes.json) and [`reproduction_verification.json`](../../outputs/attacking_continuous_movement_game2_stage_a/reproduction_verification.json).

Hard QC passed:

- every raw row received one deterministic valid/invalid status;
- no excluded row appears inside a valid segment;
- no hard link survives inside a valid segment;
- no qualifying same-team duplicate survives contrary to the frozen rule;
- canonical keys, player identities, periods, clocks, coordinates, and registry fields passed;
- no interpolation, clipping, smoothing, feature calculation, frequency comparison, event/outcome access, or Game 3 access occurred.

There is no unresolved support/identity/schema ambiguity under the frozen protocol.

## 9. Stage-A classification and claim boundary

The mechanical classification is **STAGE A READY**.

The maximum current claim is:

> Game 2 raw trajectory support has passed the prospectively frozen pre-result integrity audit, and its validity registry/support segments were frozen before continuous attacker-movement features were computed.

This does **not** mean the continuous representation has replicated. The substantial support defects are neither evidence for nor evidence against that representation. Stage A says nothing about Game 2 feature values, numerical/frequency robustness, native 10 Hz or cross-provider equivalence, football universality, tactical validity, defenders, defensive response, opponent association, attacker influence, causation, gravity, or off-ball value.

A later pass is authorized to execute the unchanged continuous representation on Game 2 using this committed registry and support-segment artifact. It may not revise Stage-A exclusions. Game 3 remains untouched.
