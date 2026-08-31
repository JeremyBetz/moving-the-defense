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
- Outcome-blind movement-segmentation audit: [`config/post5b_movement_segmentation_audit_rules.json`](../config/post5b_movement_segmentation_audit_rules.json), exploratory predeclared rules rather than a frozen validation protocol.
- Continuous attacker movement: [`docs/protocols/attacking_continuous_movement_v1.md`](protocols/attacking_continuous_movement_v1.md), version 1.0; [Game 1 result](results/attacking_continuous_movement_game1_v1.md). Reproduce the governed development execution with:

```bash
MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python src/attacking_continuous_movement_game1_v1.py
.venv/bin/python -m unittest tests.test_attacking_continuous_movement_v1
```

For the required independent check, rerun with `--output` to a separate directory, then use `--verify-against` from the governed output directory. Complete support, feature, frequency-comparison, fixture, summary, provenance, and hash artifacts are under `outputs/attacking_continuous_movement_game1_v1/`.

- Held-out continuous attacker movement: [`docs/protocols/attacking_continuous_movement_game2_heldout_v1.md`](protocols/attacking_continuous_movement_game2_heldout_v1.md), frozen before any Game 2 access. Its mandatory first pass is trajectory-support QC and registry freeze only; no Game 2 feature implementation or result artifact exists.

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

## Known reproducibility limitations

- There is no one-command end-to-end workflow or continuous integration check.
- Requirements are bounded but not fully locked across platforms.
- Several large derived CSVs are committed for auditability; a future archive policy should preserve hashes and provenance before moving them.
- Two preflight/result attrition pairs are byte-identical because the governed sample did not change; they are retained as phase-specific evidence rather than deduplicated post hoc.
- The movement-segmentation audit retained a 56.30 m/s maximum. A later outcome-blind audit traced it to identity/trajectory discontinuity and froze only support-rule directions, not a numeric filter. The separate prominence-refinement protocol subsequently executed once and classified B; it did not repair or exclude tracking discontinuities in the primary analysis.
- The prominence-refinement execution is governed by [`config/post5b_attacking_movement_prominence_refinement_rules.json`](../config/post5b_attacking_movement_prominence_refinement_rules.json), implemented in `src/post5b_attacking_movement_prominence_refinement.py`, and reported in [`post5b_attacking_movement_prominence_refinement_results.md`](post5b_attacking_movement_prominence_refinement_results.md). Its B result selects no threshold and does not authorize Game 2 execution.
- Directional segmentation v1 is governed by [`protocols/attacking_directional_segmentation_v1.md`](protocols/attacking_directional_segmentation_v1.md), implemented in `src/attacking_directional_segmentation_game1_v1.py`, and reported in [`results/attacking_directional_segmentation_game1_v1.md`](results/attacking_directional_segmentation_game1_v1.md). Its compressed CSV outputs are deterministic and can be read directly by pandas. The Game 1 result is B and does not authorize Game 2 execution.
