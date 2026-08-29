# Phase 4A Focal-Departure Validation Protocol

## Status

Protocol version **1.0** is fully specified but not executed. The machine-readable source of truth is `config/phase4a_focal_departure_validation_protocol.json`. Phase 4A inspected only data provenance, schema, missingness, eligibility, activity-conditioning variables, and support. No focal-relative outcome was calculated for held-out Sample Game 2.

## Target and limits

The narrowed target is **focal departure from collective defensive motion**:

> Focal departure is the extent to which an individual defender's movement differs from the contemporaneous collective motion of the remaining defending outfield players.

For focal defender $d$,

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),
$$

where $\mathbf c_{-d}(t)$ is the centroid of the other available defending outfield players.

This wording is provisional. The primitive is geometric, behavioral, reference-relative, and continuous. It is not inherently good or bad and does not imply opponent response, responsibility, attention, tactical error, or relational reconfiguration. A large value can arise from pressing, covering, ball response, recovery, role behavior, transition, general activity, or data artifacts.

The focal primitive is selected on conceptual grounds established before Phase 4: leave-one-out referencing separates collective translation from relative movement; focal descriptions survived prospective relationship selection better than local-compression accounts; local deformation was common and membership-sensitive; opponent semantics remained weak; and Phase 3B made general activity a mandatory alternative explanation. It is not selected because the historical 590–598s example looked compelling.

## Data and held-out separation

- **Development/history:** Metrica Sample Game 1.
- **First held-out validation:** Metrica Sample Game 2.
- **Source:** Metrica Sports public `sample-data` repository.
- **Raw storage:** `data/metrica_sample_game_2/`, excluded by `.gitignore`.

Sample Game 2 contains the same three-file structure as Game 1, the same three-row tracking header, the same normalized coordinate convention, matching event columns, 25 Hz tracking, global frame/time counters, Home/Away player slots, ball fields, and two periods. It has 141,156 tracking frames after joining Home and Away and 1,935 events. Home IDs are 11, 1–10, and 12–14; Away IDs are 25, 15–24, and 26. The frozen Home11/Away25 goalkeeper exclusions are present and schema-compatible. Event types are the same broad vocabulary needed here: `PASS`, `RECOVERY`, `SET PIECE`, `SHOT`, `BALL LOST`, `BALL OUT`, `CHALLENGE`, `FAULT RECEIVED`, and `CARD`. Coordinate values range approximately from −0.05 to 1.05, so physical conversion does not silently clip them.

Checksums are frozen in the JSON configuration. Game 2 remains held out: schema and conditioning/support quantities were inspected, but $\mathbf r_d(t)$, its path, endpoint changes, distributions, examples, and contextual relationships were not calculated.

## Sampling and eligibility

Sampling is independent of event outcomes. Each period is partitioned on a non-overlapping five-second elapsed-match grid. A primary interval is half-open $[t,t+5)$ and contains exactly 125 tracking frames. Five seconds is frozen because it matches the prior primary diagnostic scale, can contain coordinated movement, and is short relative to many uninterrupted possessions—not because it optimizes focal separation. Four- and six-second intervals are frozen sensitivities.

An interval must:

- remain within one period;
- have one event-defined possession team throughout, using the latest `PASS`, `RECOVERY`, `SET PIECE`, or `SHOT` at interval start;
- contain no possession-team change, restart, `SET PIECE`, or `BALL OUT`;
- contain a complete tracked ball path;
- contain at least nine non-goalkeeper defending outfield players with complete x/y throughout.

The complete outfield set is fixed within the interval. Each member becomes one focal observation. Events define possession/context and exclusions only; they do not label focal departure.

## Representation and primary quantity

Coordinates convert to 105×68 m without orientation flipping. Positions are smoothed separately in x and y with the established centered seven-frame rolling mean. Smoothing occurs within each interval, uses no interpolation or padding, and omits the first/last three frames from path accumulation. Five- and nine-frame windows are frozen sensitivities.

The primary quantity is **focal-relative path length**:

$$
P^{rel}_d=\sum_t \left\|\mathbf r_d(t)-\mathbf r_d(t-1)\right\|.
$$

It is accepted as primary for a reason independent of the Phase 3B result: departure is accumulated movement relative to a moving collective baseline, and endpoint vectors can cancel when a defender leaves and returns. Net x/y change, net relative displacement, focal absolute path, and collective paths remain separate secondary quantities.

$P^{rel}_d$ is still only **departure magnitude**, not **meaningful focal departure**. It may measure focal activity remaining after translation subtraction. Its usefulness depends on reproducibility, conditioning, negative controls, sensitivities, and soccer interpretation. No ratio or composite focal-departure score is defined.

## Primary validation design

The selected approach is **distributional replication**. Game 1 will define the focal-relative distribution and its separately reported relationships with pre-frozen activity/context variables. Those relationships will then be tested once in untouched Game 2. This avoids pretending that an event supplies positive/negative labels.

The primary activity view is a 3×3 table defined by Game 1 terciles of focal absolute path and full defending-outfield centroid path. Aggregate defending-player path and ball path are inspected in separate frozen marginal terciles. Exact cut points are stored in the JSON and were calculated without focal-relative outcomes. Period, possession team, and defending team remain visible.

Report medians, IQRs, five fixed quantiles, separate Spearman relationships, the 3×3 cell summaries, and within-interval dispersion across defenders. Use a 10,000-resample interval-cluster bootstrap. Contemporaneous conditioning is descriptive: it does not estimate a causal activity-free effect.

Defender-within-team contrasts are a secondary diagnostic because defenders share the same passage, ball movement, and collective context. They remain vulnerable to position/role differences, so only defenders with at least 50 eligible intervals are shown and no role is inferred. Within-defender temporal contrasts are also secondary because substitution patterns produce uneven support.

## Outcome-blind readiness and stop rule

The protocol requires, per match:

- at least 300 eligible intervals;
- at least 3,000 defender-interval observations;
- at least 150 intervals for each defending team;
- at least 50 observations in every primary 3×3 activity cell;
- at least 50 intervals for a defender included in within-defender diagnostics.

Game 1 provides 422 intervals and 4,220 defender-intervals; defending-team counts are 198/224 and the smallest 3×3 cell has 74 observations. Attrition from 1,158 grid intervals is 273 possession changes, 413 incomplete ball paths, 43 restarts, and seven intervals without prior possession information. Game 2 provides 407 intervals and 4,070 defender-intervals; defending-team counts are 217/190 and the smallest cell has 75 observations. Attrition from 1,127 grid intervals is 256 possession changes, 421 incomplete ball paths, and 43 restarts. Twenty-five Game 1 defenders and 21 Game 2 defenders meet the within-defender minimum.

Both matches pass readiness. If these counts do not reproduce from the checksummed files at execution, stop without changing criteria.

## Negative controls

1. **Common-translation invariance:** apply one identical observed translation trajectory to all defenders from fixed relative starting positions. Focal-relative path must be zero to numerical tolerance. This verifies the geometry; it is not empirical evidence.
2. **Temporally misaligned collective reference:** replace the contemporaneous collective reference with the nearest eligible interval from the same period, defending team, and frozen collective-activity tercile, 10–120 seconds away. This preserves broadly similar collective activity while breaking contemporaneous alignment. It has outcome-blind support for 378/422 Game 1 intervals and 366/407 Game 2 intervals. It is a reference-alignment diagnostic, not a tactical null.

Player-identity permutation is rejected: because every eligible defender is already evaluated, permutation would mainly relabel the same distribution while destroying legitimate identity/role structure.

## Replication and falsification

Replication requires adequate held-out support, compatible distributional shapes and effect magnitudes, and no material reversal of separately reported activity relationships. At least seven of nine primary cells must have an absolute Game-2-minus-Game-1 median difference no greater than 0.5 pooled within-cell IQR; interval-cluster bootstrap uncertainty must also be reported. The qualitative conclusion must remain stable across 4/5/6-second and 5/7/9-frame sensitivities. Identical point estimates and statistical significance are not required.

Focal departure is not supported as an independent useful primitive if:

- focal-relative path is almost completely determined by focal absolute movement (frozen diagnostic: $|\rho|\geq0.95$ in both matches with no stable conditional variation);
- collective, aggregate, or ball activity explains all reproducible structure;
- Game 1 relationships fail or reverse in Game 2;
- identity or unobserved role prevents a match-replicating construct;
- missingness/substitution makes the reference unstable;
- conclusions depend materially on frozen interval or smoothing choices;
- the leave-one-out centroid behaves misleadingly under common rotation, compression, or asymmetry;
- the only defensible interpretation is “this defender moved differently.”

Mathematical reproducibility alone is insufficient. Failure should weaken the proposed route from focal geometry toward later relational interpretation; it must not trigger immediate metric replacement.

## Scope boundary

Phase 4 execution, when authorized, tests only the first possible link:

**focal departure → contextual/relational interpretation → possible reconfiguration → possible attacker attribution**

It does not test attacker-induced movement, attention, responsibility, question propagation, relational reconfiguration, gravity, off-ball value, tactical quality, causality, or a model/classifier.
