# Reproducibility Guide

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-phase0.txt
jupyter notebook
```

Python, pandas, NumPy, Matplotlib, Jupyter, nbclient, and ipykernel are sufficient for the current notebooks and documentation figures. The local environment is ignored by Git.

## Raw data

Download Metrica Sample Games 1 and 2 from <https://github.com/metrica-sports/sample-data> and place the three CSVs for each match under:

```text
data/metrica_sample_game_1/
data/metrica_sample_game_2/
```

`data/*` is ignored and `data/.gitkeep` is retained. Sample Game 2 SHA-256 checksums are recorded in [`config/phase4a_focal_departure_validation_protocol.json`](../config/phase4a_focal_departure_validation_protocol.json).

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

Documentation explains the rules; configs govern execution. If prose and config conflict, stop and resolve the literal inconsistency before outcomes.

## Development/test separation

Sample Game 1 is development/history. Sample Game 2 is the first held-out focal-departure validation match. Schema, missingness, eligibility, and conditioning-only support may be inspected before execution. Do not calculate or visualize Game 2 focal-relative coordinates, paths, distributions, examples, or contextual relationships until Phase 4B is explicitly authorized.

## Execution order

For historical reconstruction, execute notebooks in filename phase order. Each notebook is intentionally scoped and many reuse fixed cases. For current work:

1. verify Game 2 checksums;
2. read the Phase 4 JSON and protocol;
3. reproduce outcome-blind support counts;
4. stop if any frozen support condition fails;
5. execute held-out outcomes only after authorization;
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
