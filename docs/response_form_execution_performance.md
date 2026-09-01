# Local Defensive Response Form v1 — Execution Performance

**Scope:** implementation efficiency only

**Scientific status:** `FINAL RESPONSE FORM B` remains closed and unchanged

## Measured bottleneck

A deterministic 12-fit pooled benchmark used closed response-form rows and the frozen block sampler. Each sampled fit contained approximately 88,688 defender rows and the governed 41-column design.

| Operation | Calls | Cumulative time | Approximate share |
|---|---:|---:|---:|
| `np.linalg.lstsq` | 12 | 0.310 s | 34% |
| Separate `np.linalg.matrix_rank` SVD | 12 | 0.284 s | 32% |
| Rebuilding the pooled design matrix | 12 | 0.303 s | 34% |
| Total fit path | 12 | 0.899 s | 100% |

The separate rank check was redundant: `np.linalg.lstsq` already returns the fitted matrix rank from the same governed least-squares operation. Across the six frozen pooled families, the implementation performs 14,000 model fits per execution (one fit per replicate for five families and two paired fits per replicate). Independent reproduction doubles that work. Game 2 uses the same duplicate-decomposition pattern within ten separate rank fits.

Block resampling, dataframe indexing, and serialization were not leading costs in this controlled profile. Repeated pooled design construction remains the largest obvious invariant overhead after this pass.

## Retained optimization

The execution now checks the rank returned by the existing `np.linalg.lstsq` call instead of first running `np.linalg.matrix_rank`. Inputs, row order, design columns, estimator, `rcond`, bootstrap draws, seeds, weighting, controls, intervals, and scientific criteria are unchanged.

The same change applies to the ten-rank Game 1/Game 2 fit helper and the pooled 41-column fit helper. It removes one decomposition per fitted model without changing the least-squares call that supplies governed coefficients.

## Benchmark and identity evidence

| Benchmark | Before | After | Result |
|---|---:|---:|---:|
| 12 representative pooled fits | 0.899 s | 0.604 s | 32.8% lower elapsed time; 1.49× fit throughput |
| Full optimized Game 2 oracle run | — | completed | 12/12 governed files byte-identical |
| Full optimized pooled oracle run | — | 822 s | 10/10 governed files byte-identical |

No full unoptimized end-to-end rerun was performed solely to manufacture a headline comparison. The 822-second measurement therefore has no directly measured full-run baseline in this pass.

Focused tests also compare optimized coefficients with the historical `matrix_rank`-then-`lstsq` path using exact array equality. Historical Game 1, Game 2, pooled, reproduction, and Final B artifacts were not regenerated or modified.

## Remaining opportunities

### High value, low scientific risk

Precompute the invariant full-sample design matrix, outcomes, anchor-to-row positions, and block-to-anchor indices once per sample family. Bootstrap replicates could then select NumPy row indices without rebuilding pandas objects or re-encoding the 41-column rank structure. This should be attempted next, but exact row order and byte-identical oracle outputs must remain mandatory.

### Medium risk

Run independent bootstrap families in separate processes with fixed child-seed ownership and controlled BLAS threads. This could reduce wall time, but adds operational complexity and must demonstrate serial/parallel byte identity and stable output ordering.

### High numerical-identity risk

Replacing `lstsq` with accumulated normal equations, cached factorizations, alternative solvers, or reordered reductions may be statistically equivalent but can change floating-point bytes. These are not recommended for the closed machinery without an explicitly authorized numerical-policy change.

## Recommended next performance pass

1. Profile design construction, row selection, and block-index assembly separately on fixed oracle draws.
2. Introduce one array/index cache at a time.
3. Compare coefficients, intervals, serialization order, and governed hashes with closed outputs.
4. Retain only byte-identical changes with measured benefit.
5. Keep historical outputs unchanged and use optimized machinery only prospectively.
6. Evaluate process-level family parallelism only after single-process allocation overhead is removed.
