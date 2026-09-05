# Reproduce the current paper

This is the short, human-first path for reproducing the current paper,
*Off-Ball Movement Direction and Localized Defensive Reorganization in
Football*. It assumes that you have the required data access. For protocol
history, every negative branch, and machine-oriented provenance, use the
[technical reproducibility guide](docs/reproducibility.md) instead.

## What this reproduces

- the time-ordered localized defensive-reorganization result in Metrica and
  its seven-match IDSSE replication;
- the IDSSE starting-context results for attacker--unit goalward position and
  attacker--ball distance;
- the IDSSE outward-versus-goalward movement-direction analysis;
- its SkillCorner Open Data directional replication; and
- the paper's Figure 1 temporal measurement figure, Figure 2 directional
  replication figure, and retained context/directional supplementary figures.

It does **not** require reproducing historical segmentation, opportunity,
coverage, expectation, or other mixed/negative branches. Those are preserved
for scientific provenance, not as prerequisites for the paper.

## Data you need

| Dataset | Why needed | Where to obtain | Expected local location | Redistributed here? | Notes |
|---|---|---|---|---|---|
| Metrica Sample Games 1--2 | Within-provider temporal result and flagship Figure 1 passage | [Metrica sample data](https://github.com/metrica-sports/sample-data) | `data/metrica_sample_game_1/`, `data/metrica_sample_game_2/` | No | Public sample data. Use Games 1--2 only; Game 3 is outside this paper. |
| IDSSE / DFL XML | Seven-match temporal, context, and movement-direction analyses | [IDSSE/DFL Figshare dataset](https://doi.org/10.6084/m9.figshare.28196177.v1) | `data/idsse_raw/` | No | Public CC BY 4.0 research release. Download the required XML files locally; this repository does not duplicate raw files or detailed generated intermediates. |
| SkillCorner Open Data | Nine-match external directional replication | [SkillCorner Open Data](https://github.com/SkillCorner/opendata) | `data/skillcorner_opendata/` | No | Public MIT-licensed source, but this repository deliberately keeps raw provider files and row-level derivatives local. Each formal match needs `<id>_match.json`, `<id>_tracking_extrapolated.jsonl`, and `<id>_phases_of_play.csv`. |

Raw tracking, player/frame rows, and detailed provider-derived ledgers are not
committed. The repository does include source, frozen protocols/configurations,
compact aggregate results, figures, and hash ledgers. Download the public
IDSSE/DFL release from its canonical source and place the required files under
`data/idsse_raw/`; the repository deliberately does not duplicate upstream raw
files or locally generated detailed intermediates. A reader can inspect the
published paper artifacts and their governed summaries without a local data copy.

## Environment

The governed executions were audited with Python **3.13.15**. From a clean
clone, create the lightweight environment used by the repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-phase0.txt
```

Equivalent `uv` setup:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-phase0.txt
```

Use a writable Matplotlib cache while running figures:

```bash
export MPLCONFIGDIR=/tmp/moving-the-defense-mpl
```

No secret environment variable or automatic data download is used. The
optional `jupyter`, `pytest`, and `uv` command-line tools are conveniences; the
paper scripts run through `.venv/bin/python`.

## Repository layout

| Location | What a reproducer needs it for |
|---|---|
| `src/` | Governed implementations and figure generators. |
| `config/` | Frozen machine-readable rules and hash ledgers. |
| `docs/protocols/` | Exact scientific definitions and execution boundaries. |
| `outputs/` | Compact governed results, manifests, and final hashes. |
| `figures/` and `docs/figures/` | Regenerated supplementary and manuscript figures. |
| `tests/` | Focused implementation and contract checks. |

For the complete scientific audit trail, see
[claim status](docs/claim_status.md), [research log](docs/research_log.md), and
[roadmap](docs/research_roadmap.md). They are useful context, but not required
reading for the linear paper path below.

## Paper-to-code map

| Paper result | Entry point | Frozen source | Compact output | Paper figure/table | Expected headline value |
|---|---|---|---|---|---|
| Temporal result, Metrica | `src/spatial_defensive_response_footprint_game1_v1.py`, then `src/spatial_defensive_response_footprint_game2_final_v1.py` | [`footprint protocol`](docs/protocols/spatial_defensive_response_footprint_v1.md) | `outputs/spatial_defensive_response_footprint_game2_final_v1/pooled_regional.csv` | Flagship Figure 1, Panel B/C | Near-minus-middle `0.05029` [0.03433, 0.06858]; paired excess `0.02912` [0.01410, 0.04526] |
| Temporal result, IDSSE | `src/spatial_defensive_response_footprint_idsse_v1.py` | [`external protocol`](docs/protocols/spatial_defensive_response_footprint_v1_idsse_external_replication.md) | `outputs/spatial_defensive_response_footprint_idsse_v1/coefficient_intervals.csv` | Flagship Figure 1, Panel B/C | `0.06115` [0.05579, 0.06681]; paired excess `0.02455` [0.01932, 0.02985] |
| Context H1/H2, IDSSE | `src/defensive_reorganization_context_v1.py` | [`Context v1 protocol`](docs/protocols/defensive_reorganization_context_v1.md) | `outputs/defensive_reorganization_context_v1/result.json` | Table 1; supplementary context figure | H1 `-0.010161` [−0.011805, −0.008499]; H2 `-0.007533` [−0.008864, −0.006245] |
| Movement-direction analysis, IDSSE | `src/defensive_reorganization_spatial_value_v1.py` | [`directional-analysis protocol`](docs/protocols/defensive_reorganization_spatial_value_v1.md) | `outputs/defensive_reorganization_spatial_value_v1/result.json` | Table 1; supplementary directional figure | Outward minus goalward `0.056856` [0.051358, 0.062430] |
| Directional replication, SkillCorner | `src/defensive_reorganization_spatial_form_skillcorner_external.py` | [`SkillCorner protocol`](docs/protocols/defensive_reorganization_spatial_form_v1_skillcorner_external.md) | `outputs/defensive_reorganization_spatial_form_v1_skillcorner_external/result.json` | Table 1 / external-replication text | Outward minus goalward `0.048883` [0.042940, 0.054707] |
| Figure 1 — Time-ordered localized defensive reorganization | `src/generate_temporal_footprint_flagship.py` | Closed compact temporal outputs plus one deterministic Game 2 passage | `docs/figures/sloan/temporal_footprint_flagship.svg` | Figure 1 | Uses the closed values above plus one deterministic Game 2 passage |
| Figure 2 — Directional replication | `src/generate_directional_replication_figure.py` | Closed compact aggregate directional inputs only | `docs/figures/sloan/directional_replication.{svg,png,pdf}` | Figure 2 | IDSSE `0.056856` [0.051358, 0.062430], 7/7 positive; SkillCorner `0.048883` [0.042940, 0.054707], 9/9 positive; no cross-provider pooled estimate |

Intervals are pre-specified bootstrap intervals. Exact byte identity is expected for
the compact files when the same data release, Python/package environment, and
deterministic execution path are used. On another compatible platform, first
compare the reported values to the precisions shown above, then consult the
output `final_hashes.json` and the technical guide before treating a small
serialization difference as a scientific discrepancy.

## Linear full-reproduction order

The historic governed scripts deliberately fail rather than overwrite closed
result folders. Do the full path in a **disposable clone or worktree**, keeping
the published checkout intact. Before a script that uses a fixed output path,
move that output and its matching figure folder out of the disposable clone;
do not delete or alter the published results in your working copy.

In that disposable clone, this one-time preparation keeps the published compact
artifacts outside the paths that the fixed-output scripts protect:

```bash
mkdir -p ../moving-the-defense-paper-baseline
mv outputs/spatial_defensive_response_footprint_game1_v1 \
   outputs/spatial_defensive_response_footprint_game2_final_v1 \
   outputs/defensive_reorganization_context_v1 \
   outputs/defensive_reorganization_spatial_value_v1 \
   ../moving-the-defense-paper-baseline/
mv figures/spatial_defensive_response_footprint_game1_v1 \
   figures/spatial_defensive_response_footprint_game2_final_v1 \
   figures/defensive_reorganization_context_v1 \
   figures/defensive_reorganization_spatial_value_v1 \
   ../moving-the-defense-paper-baseline/
```

1. **Prepare and verify data** — copy the three data sources above into their
   stated locations. Runtime: **seconds** for a directory check.

   ```bash
   find data/metrica_sample_game_1 data/metrica_sample_game_2 data/idsse_raw data/skillcorner_opendata -maxdepth 1 -type f | head
   ```

2. **Run ingestion/provider gates** — this validates the IDSSE seven-match
   provider-equivalence gate before fitting the temporal result. Runtime:
   **minutes**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl PYTHONPATH=src .venv/bin/python \
     src/spatial_defensive_response_footprint_idsse_v1.py --equivalence-only
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/defensive_reorganization_spatial_form_skillcorner_external.py \
     --data-dir data/skillcorner_opendata --preflight-only
   ```

3. **Reproduce the temporal result** — first run Metrica Game 1 and then the
   protected Game 2/pooled script in the disposable clone. Then stage the
   seven IDSSE matches and fit the frozen external model. Runtime: **long**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/spatial_defensive_response_footprint_game1_v1.py
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/spatial_defensive_response_footprint_game2_final_v1.py

   for match in J03WMX J03WN1 J03WOH J03WOY J03WPY J03WQQ J03WR9; do
     MPLCONFIGDIR=/tmp/moving-the-defense-mpl PYTHONPATH=src .venv/bin/python \
       src/spatial_defensive_response_footprint_idsse_v1.py \
       --output outputs/.paper_temporal_idsse --stage-match "$match"
   done
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl PYTHONPATH=src .venv/bin/python \
     src/spatial_defensive_response_footprint_idsse_v1.py \
     --output outputs/.paper_temporal_idsse
   ```

   Expect the Metrica and IDSSE values in the map above. The IDSSE execution
   writes `outputs/.paper_temporal_idsse/`; use its `governed_hashes.json` to
   compare with the published output rather than replacing it.

4. **Reproduce Context v1** — after moving the closed Context output/figure
   folders aside in the disposable clone, run the frozen seven-match analysis.
   Runtime: **tens of minutes**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/defensive_reorganization_context_v1.py
   ```

   Expect the two H1/H2 estimates in the map. The result and supplementary
   figure are written to `outputs/defensive_reorganization_context_v1/` and
   `figures/defensive_reorganization_context_v1/`.

5. **Reproduce the IDSSE movement-direction analysis** — after moving its closed compact
   output/figure folders aside, execute the frozen model. Runtime: **tens of
   minutes**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/defensive_reorganization_spatial_value_v1.py
   ```

   Expect outward-minus-goalward `0.056856` [0.051358, 0.062430].

6. **Reproduce the SkillCorner directional replication** — use a new output path
   for an isolated rerun. Runtime: **long**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/defensive_reorganization_spatial_form_skillcorner_external.py \
     --data-dir data/skillcorner_opendata \
     --output outputs/.paper_skillcorner_spatial_form \
     --reproduction-run
   ```

   Expect outward-minus-goalward `0.048883` [0.042940, 0.054707]. Compare the
   local compact hash ledger with the published result; do not commit raw or
   row-level outputs.

7. **Regenerate paper figures/tables** — after the temporal Metrica outputs
   are present, regenerate Figure 1. Figure 2 uses only closed compact
   aggregate inputs and therefore does not require provider row-level data.
   Runtime: **seconds to minutes**.

   ```bash
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/generate_temporal_footprint_flagship.py
   MPLCONFIGDIR=/tmp/moving-the-defense-mpl .venv/bin/python \
     src/generate_directional_replication_figure.py
   ```

   This writes `docs/figures/sloan/temporal_footprint_flagship.{svg,png,pdf}`.
   Figure 2 writes `docs/figures/sloan/directional_replication.{svg,png,pdf}`.
   The Context and historical internal source scripts in steps 4--5 regenerate
   their own supplementary figures. Table values are read from the compact
   result files listed above.

## Fast paper-artifact path

There is no data-free command that regenerates **every** paper figure: the
flagship figure intentionally reads a small deterministic Metrica Game 2 slice
for its illustrative panel. Without provider data, use the committed compact
outputs, manuscript, and versioned figures to inspect the paper package; do
not treat that as a full data-to-result rerun. The fastest useful check is:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
for path in [
    'outputs/spatial_defensive_response_footprint_idsse_v1/final_results.json',
    'outputs/defensive_reorganization_context_v1/result.json',
    'outputs/defensive_reorganization_spatial_value_v1/result.json',
    'outputs/defensive_reorganization_spatial_form_v1_skillcorner_external/result.json',
]:
    value = json.loads(Path(path).read_text())
    print(path, value.get('status') or value.get('classification') or 'closed')
PY
```

This verifies the available compact paper records, but it is not scientific
reproduction. A lightweight one-command wrapper is intentionally **not** added:
the existing governed scripts have distinct fail-closed output policies and
data/provider gates, so a wrapper would hide rather than simplify those
boundaries.

## Human-friendly method summary

The paper first measures an attacker's movement over a fixed earlier interval.
It then measures each defender's later movement relative to the other defending
outfield players, so a shared block shift is separated from movement within the
defensive unit. Defenders are ranked by start-time distance to the attacker;
the paper compares the nearby three with the middle four without claiming that
any defender was assigned to the attacker. A reverse-time comparison asks
whether the correctly ordered association exceeds retained background temporal
structure. Separate models describe starting ball/block context and whether
goalward versus outward movement is associated with different observable
geometric scales. See the frozen protocols for every timing, support, and
bootstrap definition.

## If your reproduction does not match

- Confirm the commit: the published paper state is the commit named in the
  repository release or `git rev-parse HEAD` for this checkout.
- Check data locations and exact provider filenames first; IDSSE and
  SkillCorner loaders fail closed when one expected file is absent.
- Confirm the correct provider release and Python/dependency environment.
- Do not use a partial or unsupported player/ball registry as a substitute for
  the governed support gate.
- Use a disposable clone when a script refuses to overwrite an existing
  compact result folder; that refusal protects the closed artifact.
- Compare `manifest.json`, `governed_hashes.json`, and `final_hashes.json`
  before changing code or interpreting a mismatch.

For provider-equivalence detail, hash identities, byte-level reruns, or a
historical result not listed here, return to
[docs/reproducibility.md](docs/reproducibility.md).

## Reproduction checklist

- [ ] Correct commit checked out
- [ ] Environment installed
- [ ] Metrica Games 1--2 available
- [ ] IDSSE data available
- [ ] SkillCorner data available
- [ ] Provider gates pass
- [ ] Temporal result matches
- [ ] Context result matches
- [ ] IDSSE movement-direction result matches
- [ ] SkillCorner replication matches
- [ ] Figures regenerate
