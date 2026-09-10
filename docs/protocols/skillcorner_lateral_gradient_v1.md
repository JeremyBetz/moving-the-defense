# SkillCorner Lateral Gradient v1 — Frozen Pre-Access Protocol

**Status:** FROZEN; RESPONSE ACCESS NOT AUTHORIZED

**Freeze date:** 2026-09-09

**Execution tier after separate authorization:** Tier 3 external replication

## Question and estimand

Within the nine governed SkillCorner matches, is a larger absolute lateral attacker starting position associated with larger subsequent localized near-minus-middle defender-relative reorganization?

The IDSSE spatial pattern generated the hypothesis. This SkillCorner analysis tests that hypothesis prospectively in a provider environment already used previously for the directional study. It is not untouched-dataset replication or independent new dataset validation, and does not validate the IDSSE heatmap itself.

For attacker-anchor observation (i) in match (m), the predictor is

\[
z_{im}=|y_c(t-2)|,
\]

where (y_c=68y/W) is the provider coordinate scaled to the canonical 68 m pitch width. The outcome is

\[
Y_{im}=\frac{1}{3}\sum_{d=D1}^{D3}P_{imd}-\frac{1}{4}\sum_{d=D4}^{D7}P_{imd},
\]

where (P) is accumulated leave-one-out defender-relative path over ([t,t+2]). The primary estimand, \(\beta_{lat}\), is metres of near-minus-middle accumulated path per metre of absolute lateral starting position. The directional hypothesis is \(\beta_{lat}>0\). A reported 10 m contrast is exactly (10\beta_{lat}); it is not a tactical-zone comparison and does not imply pointwise monotonicity.

## Population and frozen support identity

The population is exactly matches `1886347`, `1899585`, `1925299`, `1996435`, `2006229`, `2011166`, `2013725`, `2015213`, and `2017461`. Match `1953632` remains excluded. There is no minimum-eight fallback and no post-response match dropping.

Execution is bound to the committed support manifest and source ledger under `outputs/skillcorner_lateral_gradient_support_preflight_v1/`. It requires exact agreement with the primary and majority-detected observation digests, every per-match digest and count, all-match totals (49,107 primary; 11,810 quality), the nine-match population, and the 27 pinned source identities. Count agreement alone is insufficient. Any mismatch is `INVALID` and stops before model fitting.

## Response construction and field firewall

The response reuses the governed native SkillCorner construction: 10 Hz tracking, the centred three-frame smoother, defender ranks fixed at the anchor, D1–D3 versus D4–D7, and accumulated leave-one-out defender-relative path over ([t,t+2]). The current native/provider wrapper is authoritative; Kloppy remains equivalence evidence only. No alternate response, prediction, residual, provider stack, or inferred marking assignment is permitted.

Import, `--help`, and `--verify-freeze` are provider-response-free. Real response construction is reachable only through `--execute-response` with a nonempty authorization reference, exact frozen protocol/config/source/test hashes, exact support identity reconciliation, and exact pinned source identity. The reference is provenance metadata, not independent proof of human approval. This frozen implementation does not authorize execution.

## Model and sensitivity

The primary model is

\[
Y_{im}=\alpha_m+\beta_{lat}z_{im}+\epsilon_{im}
\]

and minimizes

\[
\sum_m\frac{1}{n_m}\sum_i(Y_{im}-\alpha_m-\beta_{lat}z_{im})^2.
\]

Thus each match receives equal total fitting weight; this is not the arithmetic mean of nine slopes, and matches with greater within-match lateral variation provide more slope information. No attacker path, longitudinal start, ball distance, direction, interaction, zone, or spline enters A1.

The majority-detected subset is a required measurement-quality sensitivity using its committed digest. It fits the identical model and inference. It is not a cleaner ground truth sample. Finite native starts beyond the nominal pitch remain unaltered and are neither clipped nor excluded; the sparse `|y|>34 m` tail is not interpreted and receives no edge sensitivity.

## Inference

Use 2,000 PCG64 draws with seed `20260909`. Resample nonempty 60-second blocks separately within match × period, preserving all simultaneous attacker perspectives in a selected block. Each valid draw preserves all nine matches, recalculates match weights, and fits full-rank primary and quality models with paired block multiplicities. At least 1,900 paired draws must be finite and full rank. The interval is the two-sided 95% percentile interval using NumPy's linear quantile convention.

Allowed outputs are the pooled primary estimate and interval, pooled quality estimate and interval, nine descriptive match slopes/signs, nine leave-one-match-out estimates, observation counts, and valid-draw counts. LOMO is influence analysis only; match slopes are not nine independent replications.

## Classification

- `INVALID`: source, digest, rank, bootstrap, reproduction, or package-QC failure.
- `SUPPORTED`: primary 95% lower bound is above zero, the quality-subset slope is positive, and all nine LOMO slopes are positive.
- `MIXED`: the primary slope is positive but one or more `SUPPORTED` conditions fail, including a positive estimate whose interval crosses zero.
- `NOT SUPPORTED`: the primary slope is nonpositive. A clearly negative interval is contrary evidence.

No `MIXED` or `NOT SUPPORTED` result may trigger A2, A3, alternate filters, a heatmap, or another provider.

## Publication, closure, and interpretation

Only the compact aggregate files named in the config may be published. Observation IDs, tracking coordinates, identities, timestamps, blocks, provider rows, row-level outcomes, predictions, and residuals may never be serialized by this analysis.

Primary and reproduction payloads are materialized in separate temporary destinations with identical frozen inputs. All governed machine-readable outputs and the deterministic report must be byte-identical. Exact structural validation checks schemas, cardinalities, nine-match identities, finite values, counts, classification, and frozen lineage; unknown nested fields are rejected. The shared equal-match OLS implementation is hash-bound without changing its behavior.

The validated staging package is promoted without final authority. Its manifest and QC retain the explicitly non-authoritative staging status while pending at final paths. Every authoritative artifact and the report are checked before `final_hashes.json` is atomically published last, then reread and validated again before success. This nonrecursive ledger is the sole final authority. If publication or subsequent validation fails, no final-valid marker may remain; pending aggregates may remain for diagnosis. Existing destinations are never overwritten.

Reproduction hashes describe pre-authority staging artifacts only. The actual report destination is recorded relative to the authoritative output directory, consistently in reproduction metadata and the final ledger, including custom destinations. Report validation cannot be omitted. The report exposes the approved primary and quality estimates/intervals, quality sign, match-sign count, nine LOMO estimates, classification, support counts/digests, valid-draw count, source and frozen dependency hashes, and measurement/interpretation limitations. It introduces no new analysis or diagnostic.

The primary tracking contains both detected and provider-extrapolated coordinates, and direct-detection retention varies by match. The support audit found no strong monotonic deterioration of aggregate quality with `|y|`; it did not prove coordinate accuracy. The interval is conditional on these nine matches and this measurement process. Results describe an observational spatial association, not causation, influence, marking, tactical effectiveness, or value.

The existing Sloan abstract and two-figure package remain unchanged by default. Any response access requires a separate independent pre-access review and explicit human authorization. Any manuscript use requires a later editorial decision.
