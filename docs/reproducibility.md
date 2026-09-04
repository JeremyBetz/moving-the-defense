# Moving the Defense — Reproducibility Guide

**Repository:** [`moving-the-defense`](https://github.com/JeremyBetz/moving-the-defense)

**Project:** *Measuring Defensive Responses to Attacking Movement in Football*

## Experimental Kloppy equivalence gate

Kloppy is pinned at 3.19.0 for the isolated Metrica Game 1 equivalence experiment. With the existing raw Sample Game 1 files in `data/metrica_sample_game_1/`, reproduce it with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python src/kloppy_metrica_equivalence.py
.venv/bin/python -m unittest tests.test_kloppy_metrica_adapter
```

The experiment writes only to `outputs/kloppy_metrica_equivalence/`. Its [B result and adapter rules](kloppy_metrica_equivalence.md) do not replace the current Metrica loader or authorize scientific reruns through Kloppy.

## Governed canonical tracking architecture

[Canonical tracking contract v1.0.0](canonical_tracking_contract.md) governs new analyses using Kloppy 3.19.0 and Polars 1.44.1. It does not replace historical loaders. With Metrica Game 1 and IDSSE `J03WMX` raw files already present, reproduce the cross-provider contract gate with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python src/canonical_tracking_contract_audit.py
.venv/bin/python -m unittest tests.test_canonical_tracking_contract
```

The full logical tables are validated in consecutive Polars chunks. Only bounded schema samples, provenance sidecars, invariant summaries, and downstream equivalence results are committed under `outputs/canonical_tracking_contract/`.

## UnravelSports interoperability audit

UnravelSports 1.2.1 is pinned for the bounded, non-governed [interoperability audit](unravelsports_interoperability.md). It adds SciPy at runtime; graph/deep-learning extras are not required or installed. With only Metrica Game 1 and IDSSE `J03WMX` present, reproduce the `limit=250` comparison with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python src/unravelsports_interoperability_audit.py
.venv/bin/python -m unittest tests.test_unravelsports_compat
```

The audit writes only to `outputs/unravelsports_interoperability/`. It does not authorize using UnravelSports inference, filtering, kinematics, pressing, EFPI, or graph tooling in a governed scientific pipeline.

## Environment

The current local checkpoint was audited under Python 3.13.15. The bounded requirements are intentionally lightweight rather than a platform-specific lockfile; exact package versions used by governed executions are recorded in their manifests where applicable.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-phase0.txt
jupyter notebook
```

An equivalent `uv` setup is:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-phase0.txt
```

Python, pandas, NumPy, Polars, Kloppy, UnravelSports, SciPy, Matplotlib, Jupyter, nbclient, and ipykernel cover the tracked source implementations and documentation figures. XML parsing uses the Python standard library. The local environment is ignored by Git.

## Raw data

Download Metrica Sample Games 1 and 2 from <https://github.com/metrica-sports/sample-data> and place the three CSVs for each match under:

```text
data/metrica_sample_game_1/
data/metrica_sample_game_2/
```

`data/*` is ignored and `data/.gitkeep` is retained. Sample Game 2 SHA-256 checksums are recorded in [`config/phase4a_focal_departure_validation_protocol.json`](../config/phase4a_focal_departure_validation_protocol.json). The 21 IDSSE XML files used for completed external replication belong under ignored `data/idsse_raw/`; their governed mapping and hashes are recorded in Phase 4C artifacts. Metrica Sample Game 3 is not part of the current evidence and must not be added to a reproduction run.

## Coordinate and time conventions

- Source coordinates are nominally normalized and may slightly exceed $[0,1]$.
- Physical calculations use 105 × 68 m without clipping.
- Phase 0 and explicitly raw diagnostics retain source coordinates first.
- Tracking is 25 Hz; time and frame counters are global across periods in these files.
- Phase 4 intervals are half-open $[t,t+5)$ with exactly 125 frames.
- Goalkeepers are excluded as Home11 and Away25 under the frozen Metrica protocol.

## Missingness and smoothing

- No protocol silently imputes or interpolates missing coordinates.
- Earlier derivative diagnostics use centered 5/7/9-frame rolling-position means and document edge behavior.
- Phase 4 uses a centered seven-frame mean within each interval, omits the first/last three frames from path accumulation, and freezes 5/9-frame sensitivity.
- Phase 4 requires a complete ball path and at least nine complete defending outfield players throughout an interval.

## Protocol sources of truth

- Phase 3: [`config/phase3a_validation_protocol.json`](../config/phase3a_validation_protocol.json), version 1.1, seed `20260828`.
- Phase 4: [`config/phase4a_focal_departure_validation_protocol.json`](../config/phase4a_focal_departure_validation_protocol.json), version 1.0, seed `20260829`.
- Phase 4C: [`config/phase4c_external_replication_protocol.json`](../config/phase4c_external_replication_protocol.json) plus provider mapping in [`config/phase4c_idsse_implementation.json`](../config/phase4c_idsse_implementation.json).
- Phase 5A: [`config/phase5a_contextual_expectation_protocol.json`](../config/phase5a_contextual_expectation_protocol.json).
- Phase 5B: [`config/phase5b_opponent_relational_increment_protocol.json`](../config/phase5b_opponent_relational_increment_protocol.json).
- Defensive Coverage Redistribution v1 is preserved as a [rejected pre-execution design](protocols/defensive_coverage_redistribution_v1_rejection.md); its frozen protocol/configuration remain unchanged and no empirical result exists. V2 is governed by its [protocol](protocols/defensive_coverage_redistribution_v2.md), [`config/defensive_coverage_redistribution_v2.json`](../config/defensive_coverage_redistribution_v2.json), [supersession audit](defensive_coverage_redistribution_v2_methodology.md), and [Game 1 invalid closure](results/defensive_coverage_redistribution_game1_v2.md). It retained 281 period-1 anchors but no period-2 anchors, leaving the mandatory period-2 indicator constant and the frozen model rank-deficient; no outcome coefficient was estimated. Reproduce the v1 algebra check and v2 pure synthetic gates with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-coverage .venv/bin/python -m pytest -q tests/test_defensive_coverage_redistribution_v1.py tests/test_defensive_coverage_redistribution_v2.py
MPLCONFIGDIR=/tmp/moving-the-defense-coverage .venv/bin/python src/generate_defensive_coverage_redistribution_v1_figure.py
```

The governed V2 closure can be reproduced without changing any scientific rule:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-coverage .venv/bin/python src/defensive_coverage_redistribution_game1_v2.py --reproduce
```

V2 remains INVALID before estimation. The [v3 protocol](protocols/defensive_coverage_redistribution_v3.md)
changed only exact omission of its explicitly designated constant nuisance
indicator. The [v3 Game 1 result](results/defensive_coverage_redistribution_game1_v3.md)
is a valid period-1-only **MIXED** development result; it uses the same 281
anchors, omits only `period_2_indicator`, and commits compact governed output
artifacts while retaining provider-linked rows locally. The frozen governance
test remains a historical pre-execution assertion; use the estimability and
result checks below after the authorized execution:

```bash
.venv/bin/python -m pytest -q tests/test_defensive_coverage_redistribution_v3_estimability.py tests/test_defensive_coverage_redistribution_game1_v3.py
```

Reproduce the governed v3 result and its independent deterministic rerun with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-coverage .venv/bin/python src/defensive_coverage_redistribution_game1_v3.py --reproduce
```

- Outcome-blind movement-segmentation audit: [`config/post5b_movement_segmentation_audit_rules.json`](../config/post5b_movement_segmentation_audit_rules.json), exploratory predeclared rules rather than a frozen validation protocol.
- Continuous attacker movement: [`docs/protocols/attacking_continuous_movement_v1.md`](protocols/attacking_continuous_movement_v1.md), version 1.0; [Game 1 result](results/attacking_continuous_movement_game1_v1.md). Reproduce the governed development execution with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python src/attacking_continuous_movement_game1_v1.py
.venv/bin/python -m unittest tests.test_attacking_continuous_movement_v1
```

For the required independent check, rerun with `--output` to a separate directory, then use `--verify-against` from the governed output directory. Complete support, feature, frequency-comparison, fixture, summary, provenance, and hash artifacts are under `outputs/attacking_continuous_movement_game1_v1/`.

- Held-out continuous attacker movement: [`docs/protocols/attacking_continuous_movement_game2_heldout_v1.md`](protocols/attacking_continuous_movement_game2_heldout_v1.md), frozen before Game 2 access. Its mandatory [Stage-A trajectory-support result](results/attacking_continuous_movement_game2_stage_a.md) is READY, and the [held-out representation result](results/attacking_continuous_movement_game2_v1.md) is A. Reproduce the support registry and its independent byte-level check with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-stage-a .venv/bin/python src/attacking_continuous_movement_game2_stage_a.py
.venv/bin/python -m unittest tests.test_attacking_continuous_movement_game2_stage_a
```

Governed provenance, raw-support inventory, diagnostic triggers, registry, support segments, hashes, and reproduction verification are under `outputs/attacking_continuous_movement_game2_stage_a/`.

Then reproduce the continuous representation and tests with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-game2-v1 .venv/bin/python src/attacking_continuous_movement_game2_v1.py
.venv/bin/python -m unittest tests.test_attacking_continuous_movement_game2_v1
```

For the independent check, rerun with `--output` to a separate directory and call the governed output with `--verify-against`. The 19 governed outputs must match byte-for-byte. Feature, support-linkage, 25/10 Hz comparison, mathematical-QC, fixture, invariance, provenance, hash, reproduction, and final-classification artifacts are under `outputs/attacking_continuous_movement_game2_v1/`.

- First attacker-to-defender bridge: [`docs/protocols/attacker_defender_bridge_v1.md`](protocols/attacker_defender_bridge_v1.md), frozen before any bridge observation or association was computed. Its [Game 1 development result](results/attacker_defender_bridge_game1_v1.md) is COHERENT. Reproduce the governed Game 1 execution with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-bridge .venv/bin/python src/attacker_defender_bridge_game1_v1.py
.venv/bin/python -m unittest tests.test_attacker_defender_bridge_game1_v1 tests.test_attacking_continuous_movement_v1 tests.test_canonical_tracking_contract
```

For the required independent check, rerun with `--output` and `--figures` pointing to temporary locations, then call the governed output with `--verify-against`. Fifteen governed pre-reproduction files must match byte-for-byte. The saved `hard_qc.csv` records 24 execution-contract checks; final results, linkage, observations, bootstrap summaries, inheritance, manifests, and hashes are under `outputs/attacker_defender_bridge_game1_v1/`. That execution froze `game2_inheritance.json` before Game 2 bridge access. Game 3 and external-provider bridge data remained unauthorized.

The unchanged held-out Game 2 and pooled execution has now completed as [FINAL BRIDGE A](results/attacker_defender_bridge_game2_v1.md). With the frozen Game 2 Stage-A support and attacker outputs present, reproduce it with:

```bash
MPLCONFIGDIR=/tmp/moving-defense-bridge-game2 .venv/bin/python src/attacker_defender_bridge_game2_v1.py
.venv/bin/python -m unittest tests.test_attacker_defender_bridge_game2_v1 tests.test_attacker_defender_bridge_game1_v1
```

For deterministic verification, rerun to temporary output/figure paths and use `--verify-against`. Sixteen governed pre-reproduction files must match byte-for-byte. `outputs/attacker_defender_bridge_game2_v1/` contains the Game 2 sample/linkage, model and bootstrap tables, pooled models/comparisons, 32-row hard audit, final criteria, provenance, reproduction record, and hash ledgers. The inherited threshold is exactly 12.198443079831405 m. Game 3 and external-provider bridge execution remain unauthorized.

- Spatial defensive-response footprint Game 1: [`docs/protocols/spatial_defensive_response_footprint_v1.md`](protocols/spatial_defensive_response_footprint_v1.md), frozen before any footprint coefficient was computed. The [Game 1 result](results/spatial_defensive_response_footprint_game1_v1.md) is DEVELOPMENT COHERENT. Reproduce it with:

```bash
MPLCONFIGDIR=/tmp/moving-defense-footprint .venv/bin/python src/spatial_defensive_response_footprint_game1_v1.py
.venv/bin/python -m unittest tests.test_spatial_defensive_response_footprint_game1_v1 tests.test_attacker_defender_bridge_game1_v1
```

For deterministic verification, rerun with `--output` and `--figures` pointing to temporary locations, then call the governed output with `--verify-against`. All 24 governed pre-reproduction Game 1 files must match byte-for-byte. Outputs include the complete anchor/rank linkage, coefficient and contrast tables, rank-distance diagnostics, fixed metric bands, temporal placebo, inherited consistency check, trimming/horizon sensitivities, 28-row hard-QC ledger, provenance, reproduction record, and hashes.

Before Game 2 footprint execution, the [prospective held-out execution clarification](protocols/spatial_defensive_response_footprint_v1_execution_clarification.md) resolved a reporting gap without changing either frozen scientific artifact. Game 2 receives no standalone coherent/mixed/invalid status: its complete governed outputs must first be saved, hashed, and reproduced, followed by the already-authorized pooled execution, before the original Final Footprint A/B/C rules are applied. The clarification SHA-256 is `60678b0f90128c5905ed2535a81aab37b562fe8a6b8aa6a9c9ff1f7642dcf37e`.

The held-out and pooled sequence is now complete at [FINAL FOOTPRINT A](results/spatial_defensive_response_footprint_final_v1.md). Reproduce it with:

```bash
MPLCONFIGDIR=/tmp/moving-defense-footprint-final .venv/bin/python src/spatial_defensive_response_footprint_game2_final_v1.py
```

For independent verification, run the same source with temporary `--output` and `--figures` paths, then invoke the governed primary output with `--verify-against <temporary-output>`. The closed execution reproduced 31/31 governed files byte-for-byte. Game 3 remains unauthorized and untouched.

Local defensive response form v1 is frozen at protocol SHA-256 `958c8aa80fe9ea43358c32a42a6be2eea7a41e7f727e23ff137eb3079ee80428` and configuration SHA-256 `b120f19c13b86f47f5b73311a4509cbd5de5f95fbaa1369f95dc061c998b8053`. Its [Game 1 development result](results/local_defensive_response_form_game1_v1.md) is coherent. Reproduce it with:

```bash
MPLCONFIGDIR=/tmp/moving-defense-response-form .venv/bin/python src/local_defensive_response_form_game1_v1.py
.venv/bin/python -m unittest tests.test_local_defensive_response_form_v1 tests.test_local_defensive_response_form_game1_v1
```

The command reads Sample Game 1 and the closed footprint registry, writes `outputs/local_defensive_response_form_game1_v1/`, and does not access Game 2 response-form quantities or Game 3.

The Tier-3 Game 2 and pooled execution is closed at [FINAL RESPONSE FORM B](results/local_defensive_response_form_final_v1.md). Reproduce its stages with:

```bash
MPLCONFIGDIR=/tmp/moving-defense-response-form-final .venv/bin/python src/local_defensive_response_form_game2_final_v1.py --stage game2
MPLCONFIGDIR=/tmp/moving-defense-response-form-final .venv/bin/python src/local_defensive_response_form_game2_final_v1.py --stage pooled
```

Game 2 must be serialized, hashed, and independently reproduced before the pooled stage. The closed execution reproduced 12/12 Game 2 and 10/10 pooled governed files byte-for-byte. The pooled addendum hashes are `1ba4e198...e23cf794` and `70f0d6ad...b8a9c813`. Game 3 remains unauthorized and untouched.

Where a machine-readable config is listed, documentation explains the rules and the config governs execution. The continuous attacker-movement v1 freeze is currently governed directly by its protocol document; an implementation may transcribe it to config only through a pre-execution exact-consistency check. If prose and config conflict, stop and resolve the literal inconsistency before outcomes.

## Development/test separation

Sample Game 1 is development/history. Sample Game 2 completed the first held-out focal-departure validation. Seven IDSSE matches then completed external replication and the Phase 5A/5B predictive tests in one additional provider environment. Historical pre-outcome firewalls remain binding records of how those results were produced; they are not current claims that completed outcomes remain uninspected.

## Execution order

For historical reconstruction, execute notebooks in filename phase order. Each notebook is intentionally scoped and many reuse fixed cases. For governed reproduction, run the matching source implementation and protocol rather than assuming every notebook is a standalone pipeline.

The historical Phase 4 sequence was:

1. verify Game 2 checksums;
2. read the Phase 4 JSON and protocol;
3. reproduce outcome-blind support counts;
4. stop if any frozen support condition fails;
5. execute held-out outcomes only after the recorded authorization;
6. preserve all frozen sensitivities and falsification results.

## Phase 4B held-out execution

Run the outcome-blind firewall without constructing focal-relative outcomes:

```bash
python src/phase4b_focal_departure_validation.py --precheck
```

After authorization, reproduce the complete frozen analysis and machine-readable outputs with:

```bash
python src/phase4b_focal_departure_validation.py
```

The executed narrative artifact is [`notebooks/phase4b_focal_departure_heldout_validation.ipynb`](../notebooks/phase4b_focal_departure_heldout_validation.ipynb); detailed results are in [`docs/phase4b_focal_departure_validation_results.md`](phase4b_focal_departure_validation_results.md). The analysis writes derived tables to `outputs/phase4b/` and figures to `figures/phase4b/`.

## Phase 4C external replication

Frozen protocol v1.0 is [`docs/phase4c_external_replication_protocol.md`](phase4c_external_replication_protocol.md), with machine-readable rules in [`config/phase4c_external_replication_protocol.json`](../config/phase4c_external_replication_protocol.json). The completed outcome-blind provider mapping is documented in [`docs/phase4c_idsse_mapping_audit.md`](phase4c_idsse_mapping_audit.md) and [`config/phase4c_idsse_implementation.json`](../config/phase4c_idsse_implementation.json). Detailed results are in [`docs/phase4c_external_replication_results.md`](phase4c_external_replication_results.md).

Place the 21 raw IDSSE XML files under ignored `data/idsse_raw/`. Then reproduce mapping/support and the frozen execution separately:

```bash
python src/phase4c_idsse_external_replication.py --stage mapping
python src/phase4c_idsse_external_replication.py --stage execute
```

The first command does not construct focal-relative outcomes. The second writes machine-readable tables to `outputs/phase4c/` and figures to `figures/phase4c/`. The narrative notebook is [`notebooks/phase4c_idsse_external_replication.ipynb`](../notebooks/phase4c_idsse_external_replication.ipynb).

## Phase 5A contextual expectation

Frozen protocol v1.0 is [`docs/phase5a_contextual_expectation_protocol.md`](phase5a_contextual_expectation_protocol.md), with machine-readable rules in [`config/phase5a_contextual_expectation_protocol.json`](../config/phase5a_contextual_expectation_protocol.json). The implementation uses NumPy's standard Ridge solution and requires only the existing Phase 4C IDSSE raw files/caches.

Run the target-free support/leakage preflight first, inspect its gate, and execute separately:

```bash
MPLCONFIGDIR=/tmp/phase5a-mpl .venv/bin/python src/phase5a_contextual_expectation_feasibility.py preflight
MPLCONFIGDIR=/tmp/phase5a-mpl .venv/bin/python src/phase5a_contextual_expectation_feasibility.py execute
```

The execution writes machine-readable outputs under `outputs/phase5a/` and figures under `figures/phase5a/`. The narrative artifacts are the [executed notebook](../notebooks/phase5a_contextual_expectation_feasibility.ipynb) and [results report](phase5a_contextual_expectation_results.md). The execution manifest records frozen protocol hashes and implementation clarifications.

## Phase 5B opponent-relational increment

Frozen protocol v1.0 is [`docs/phase5b_opponent_relational_increment_protocol.md`](phase5b_opponent_relational_increment_protocol.md), with machine-readable rules in [`config/phase5b_opponent_relational_increment_protocol.json`](../config/phase5b_opponent_relational_increment_protocol.json). Reproduce its outcome-blind preflight and governed execution separately:

```bash
MPLCONFIGDIR=/tmp/phase5b-mpl .venv/bin/python src/phase5b_opponent_relational_increment.py preflight
MPLCONFIGDIR=/tmp/phase5b-mpl .venv/bin/python src/phase5b_opponent_relational_increment.py execute
```

The execution writes machine-readable outputs under `outputs/phase5b/` and figures under `figures/phase5b/`. The [executed reporting notebook](../notebooks/phase5b_opponent_relational_increment.ipynb) reads those saved outputs without refitting; the detailed [results report](phase5b_opponent_relational_increment_results.md) preserves the claim boundary. The manifest records all governing hashes and confirms that Metrica Game 3 was not accessed.

Documentation figures can be regenerated with:

```bash
python figures/generate_documentation_figures.py
```

That script reads Game 1 only for empirical figures.

## Post-5B measurement audits

The direction/onset and movement-segmentation audits are exploratory, saved-result analyses rather than frozen validation phases:

```bash
MPLCONFIGDIR=/tmp/post5b-mpl .venv/bin/python src/post5b_measurement_audit_direction_onset.py
MPLCONFIGDIR=/tmp/post5b-mpl .venv/bin/python src/post5b_attacking_movement_segmentation_audit.py
```

Their reports, executed notebooks, figures, and machine-readable outputs are under matching `post5b_*` paths. The segmentation audit manifest hashes its source, rules, and Game 1 inputs. Reproducing it requires Game 1 only and must not introduce defender coordinates or defensive outcomes.

### Attacker Movement Episode v2

The immutable Game 1 rule is governed by [`protocols/attacker_movement_episode_v2.md`](protocols/attacker_movement_episode_v2.md) and `config/attacker_movement_episode_v2.json`. Heldout Game 2 additionally requires the prospectively frozen [`protocols/attacker_movement_episode_v2_game2_replication.md`](protocols/attacker_movement_episode_v2_game2_replication.md), its matching configuration, and the closed attacker-only Stage A support registry.

```bash
MPLCONFIGDIR=/tmp/attacker-episode-v2 .venv/bin/python src/attacker_movement_episode_v2_game2.py
MPLCONFIGDIR=/tmp/attacker-episode-v2 .venv/bin/python src/attacker_movement_episode_v2_game2.py --reproduce
```

The [Game 2 report](results/attacker_movement_episode_v2_game2.md) records a **MIXED** heldout replication. All 10 governed outputs reproduced byte-for-byte. The command reads Game 2 attacker trajectories, global stoppage clocks, and frozen Stage A support only; it does not read defenders or defensive outcomes.

## Local defensive deformation v1

The frozen construct is governed by [`docs/protocols/local_defensive_deformation_v1.md`](protocols/local_defensive_deformation_v1.md) and `config/local_defensive_deformation_v1.json`. Game 2 additionally requires the prospectively frozen [held-out addendum](protocols/local_defensive_deformation_v1_game2_replication.md) and `config/local_defensive_deformation_v1_game2_replication.json`.

Reproduce the closed executions separately:

```bash
.venv/bin/python src/local_defensive_deformation_game1_v1.py
.venv/bin/python src/local_defensive_deformation_game2_v1.py
```

The [Game 1 report](results/local_defensive_deformation_game1_v1.md) records development coherence. The [Game 2 report](results/local_defensive_deformation_game2_v1.md) records a standalone-unclassified held-out result. Its governed outputs are under `outputs/local_defensive_deformation_game2_v1/`; an independent run reproduced all 13 governed files byte-for-byte. No pooled deformation analysis is authorized by the held-out addendum.

## Opportunity Redistribution v1 — Game 1 development

The scientific design is frozen in [`protocols/opportunity_redistribution_v1.md`](protocols/opportunity_redistribution_v1.md) and `config/opportunity_redistribution_v1.json`. Reproduce the closed negative result with:

```bash
MPLCONFIGDIR=/tmp/mtd-opportunity .venv/bin/python src/opportunity_redistribution_game1_v1.py
MPLCONFIGDIR=/tmp/mtd-opportunity .venv/bin/python src/opportunity_redistribution_game1_v1.py --reproduce
```

The [result report](results/opportunity_redistribution_game1_v1.md) and `outputs/opportunity_redistribution_game1_v1/` record the six-column rank-6 fit, all 2,000 bootstrap replicates, exclusions, frozen robustness checks, and byte-identical reproduction. The script reads Metrica Sample Game 1 only. Game 2, Game 3, and IDSSE are outside this execution.

## Concurrent geometry v1 — IDSSE external replication

The [external protocol](protocols/concurrent_attacker_defensive_geometry_v1_idsse_replication.md), configuration, and provider-equivalence note govern the seven-match Tier 3 execution. Raw IDSSE files and the established cache/adapter structure are required. Reproduce the complete execution and compare it with the authoritative outputs using:

```bash
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/concurrent_attacker_defensive_geometry_idsse_v1.py --output outputs/.concurrent_attacker_defensive_geometry_idsse_v1_rerun
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/concurrent_attacker_defensive_geometry_idsse_v1.py --output outputs/concurrent_attacker_defensive_geometry_idsse_v1 --verify-against outputs/.concurrent_attacker_defensive_geometry_idsse_v1_rerun
```

The first command reruns the full provider-equivalence gate and scientific execution. The second records byte identity against the closed result. The [result report](results/concurrent_attacker_defensive_geometry_idsse_v1.md) and `outputs/concurrent_attacker_defensive_geometry_idsse_v1/` contain the governed evidence. Game 3 and opportunity outcomes are outside this execution.

## Temporal spatial footprint v1 — IDSSE external replication

The [frozen external protocol](protocols/spatial_defensive_response_footprint_v1_idsse_external_replication.md), configuration, hash ledger, and [provider-equivalence specification](spatial_defensive_response_footprint_v1_idsse_equivalence.md) governed the final planned time-ordered external bridge test. Its [seven-match IDSSE result](results/spatial_defensive_response_footprint_idsse_v1.md) is **SUPPORTED** and commits only compact governed outputs under `outputs/spatial_defensive_response_footprint_idsse_v1/`; provider-derived rows and local staging remain ignored. Reproduce each match's outcome-blind reconstruction in an isolated process, then the staged fit and its independent rerun:

```bash
for match in J03WMX J03WN1 J03WOH J03WOY J03WPY J03WQQ J03WR9; do
  MPLCONFIGDIR=/tmp/moving-defense-footprint PYTHONPATH=src .venv/bin/python \
    src/spatial_defensive_response_footprint_idsse_v1.py \
    --output outputs/spatial_defensive_response_footprint_idsse_v1 --stage-match "$match"
done
MPLCONFIGDIR=/tmp/moving-defense-footprint PYTHONPATH=src .venv/bin/python \
  src/spatial_defensive_response_footprint_idsse_v1.py
```

The memory-bounded staging reconstructs exactly the frozen native inputs; it
does not change the 25 Hz cadence, seven-frame support, fixed 2-second
preceding exposure/subsequent response, near/middle ranks, reverse-time
control, or transported trim threshold. Independently repeat the commands in
an ignored output directory and use `--verify-against` to require byte-identical
governed outputs. The execution used only the seven governed IDSSE matches and
did not access Metrica Sample Game 3.

## Concurrent Defensive Coordination Form v1 — IDSSE external replication

The original [protocol](protocols/concurrent_defensive_coordination_form_v1.md), configuration, and [prospective IDSSE status clarification](protocols/concurrent_defensive_coordination_form_v1_idsse_replication.md) govern the seven-match execution. Reproduce two independent complete executions with:

```bash
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/concurrent_defensive_coordination_form_idsse_v1.py --output /tmp/mtd-coordination-idsse-run1
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/concurrent_defensive_coordination_form_idsse_v1.py --output /tmp/mtd-coordination-idsse-run2
MPLCONFIGDIR=/tmp/mtd-mpl .venv/bin/python src/concurrent_defensive_coordination_form_idsse_v1.py --output /tmp/mtd-coordination-idsse-run1 --verify-against /tmp/mtd-coordination-idsse-run2
```

The [result report](results/concurrent_defensive_coordination_form_idsse_v1.md) and `outputs/concurrent_defensive_coordination_form_idsse_v1/` record the supported external result, provider-equivalence gates, exclusions, rank coefficients, manifest, hashes, and reproduction comparison. The 89,719,630-byte observation-level Parquet is intentionally not redistributed: it contains provider-linked identifiers, anchor times, distances, and derived movement measurements. A licensed-data holder can regenerate it deterministically; its authoritative SHA-256, `8a580a2d079fa248a1e8e64578b975b52e9fe790c595a6d16e37811c4a43e8d0`, remains in `governed_hashes.json`. Compact aggregate outputs are sufficient to inspect the reported result. The execution uses only the seven governed IDSSE matches and does not inspect Metrica Sample Game 3.

## Defensive Response Expectation v1

The [frozen protocol](protocols/defensive_response_expectation_v1.md), configuration, and [result report](results/defensive_response_expectation_v1.md) govern the seven-match execution. It requires the closed local IDSSE coordination-form observation ledger; that provider-linked input remains ignored. Reproduce the complete execution and independent comparison with:

```bash
MPLCONFIGDIR=/tmp/mtd-mpl OPENBLAS_NUM_THREADS=1 .venv/bin/python src/defensive_response_expectation_v1.py --output outputs/defensive_response_expectation_v1
MPLCONFIGDIR=/tmp/mtd-mpl OPENBLAS_NUM_THREADS=1 .venv/bin/python src/defensive_response_expectation_v1.py --output outputs/.defensive_response_expectation_v1_rerun --clean-output
.venv/bin/python src/defensive_response_expectation_v1.py --output outputs/defensive_response_expectation_v1 --verify-against outputs/.defensive_response_expectation_v1_rerun
```

The ten compact governed outputs reproduce byte-for-byte. `prediction_source_rows.parquet` and `prediction_rows.parquet` remain local-only; compact errors, bootstrap/control results, provenance, and hashes are publishable. The execution does not access Metrica Sample Game 3.

## Defensive Reorganization Departure v1

The [frozen protocol](protocols/defensive_reorganization_departure_v1.md) and
[result](results/defensive_reorganization_departure_v1.md) govern the compact
seven-match IDSSE application check. The execution stopped before fitting at
the frozen common-sample gate because `J03WN1` retained 782 rather than 1,000
off-ball rows. Reproduce its eligibility ledger and byte-identical compact
result with:

```bash
MPLCONFIGDIR=/tmp/mtd-drd OPENBLAS_NUM_THREADS=1 .venv/bin/python src/defensive_reorganization_departure_v1.py --output outputs/defensive_reorganization_departure_v1
MPLCONFIGDIR=/tmp/mtd-drd OPENBLAS_NUM_THREADS=1 .venv/bin/python src/defensive_reorganization_departure_v1.py --output outputs/.defensive_reorganization_departure_v1_rerun
.venv/bin/python src/defensive_reorganization_departure_v1.py --output outputs/defensive_reorganization_departure_v1 --verify-against outputs/.defensive_reorganization_departure_v1_rerun
```

No prediction ledger is created: the frozen support gate stops before model
fitting. The provider-linked observation-level eligibility ledger remains
local-only; its governed SHA-256 is retained in the compact final hash ledger.
The execution does not access Metrica Sample Game 3.

## Known reproducibility limitations

- There is no one-command end-to-end workflow or continuous integration check.
- Requirements are bounded but not fully locked across platforms.
- Several large derived CSVs are committed for auditability; a future archive policy should preserve hashes and provenance before moving them.
- Two preflight/result attrition pairs are byte-identical because the governed sample did not change; they are retained as phase-specific evidence rather than deduplicated post hoc.
- The movement-segmentation audit retained a 56.30 m/s maximum. A later outcome-blind audit traced it to identity/trajectory discontinuity and froze only support-rule directions, not a numeric filter. The separate prominence-refinement protocol subsequently executed once and classified B; it did not repair or exclude tracking discontinuities in the primary analysis.
- The prominence-refinement execution is governed by [`config/post5b_attacking_movement_prominence_refinement_rules.json`](../config/post5b_attacking_movement_prominence_refinement_rules.json), implemented in `src/post5b_attacking_movement_prominence_refinement.py`, and reported in [`post5b_attacking_movement_prominence_refinement_results.md`](post5b_attacking_movement_prominence_refinement_results.md). Its B result selects no threshold and does not authorize Game 2 execution.
- Directional segmentation v1 is governed by [`protocols/attacking_directional_segmentation_v1.md`](protocols/attacking_directional_segmentation_v1.md), implemented in `src/attacking_directional_segmentation_game1_v1.py`, and reported in [`results/attacking_directional_segmentation_game1_v1.md`](results/attacking_directional_segmentation_game1_v1.md). Its compressed CSV outputs are deterministic and can be read directly by pandas. The Game 1 result is B and does not authorize Game 2 execution.
