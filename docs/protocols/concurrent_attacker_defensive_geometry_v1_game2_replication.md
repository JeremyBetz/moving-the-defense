# Concurrent Attacker–Defensive Geometry v1 — Game 2 Replication Governance

**Status:** **FROZEN BEFORE ANY GAME 2 CONCURRENT-GEOMETRY RESULT**

**Freeze date:** 2026-09-02

**Starting commit:** `cf411c6171362ac59c523f372b388aea4b7841a3`

**Execution tier:** Tier 3 heldout replication

## 1. Firewall and closed development context

This addendum was frozen after Game 1 closed as **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT** and before any Game 2 concurrent-geometry sample, coefficient, interval, robustness result, directional output, or deformation result was generated or inspected. Game 3 and IDSSE remain untouched for this construct; no opportunity-redistribution result exists.

The authoritative Game 1 identities are:

- protocol SHA-256 `1382e97f401eafc2101f2d77ef2b7158e48500ce7df6b01d4db450f2ba1b8f32`;
- configuration SHA-256 `5b37211295297fe4350c394500da27e72040aefcc7f4806b1c779a390a9c692d`; and
- result SHA-256 `cd782fcf31b1822e397297278f43b82dcb9ce270318786c1db8c3d57d52e0da0`.

Game 1's primary near-minus-middle estimate was 0.026667 [0.011343, 0.044866], and trimming retained 91.71%. Its rank curve was not monotonic: D1 was descriptively elevated, every rank coefficient was positive, and far exceeded middle descriptively. Secondary deformation near-minus-middle was 0.013535 [0.004249, 0.024282]. These observations motivate replication but create no new gate.

## 2. Heldout questions

Primary:

> On Metrica Sample Game 2, does the exact prospectively frozen concurrent geometry design reproduce a positive near-minus-middle association between concurrent attacker path and focal-relative defender path under the same pre-interval context model?

Secondary: does concurrent endpoint defensive deformation show the same-direction spatial localization descriptively/supportively?

Neither question establishes temporal ordering, reaction, causation, or tactical meaning.

## 3. Immutable scientific inheritance

Apply [Concurrent Attacker–Defensive Geometry v1](concurrent_attacker_defensive_geometry_v1.md) literally:

- centred seven-frame 25 Hz positions in canonical 105 × 68 m fixed-pitch coordinates;
- pre-context $[t-2,t)$ and concurrent interval $[t,t+2)$ with the original exact endpoint/increment convention;
- period-origin anchors $t=origin+2+4k$;
- concurrent attacker path as continuous exposure;
- concurrent focal-relative path as primary outcome;
- concurrent endpoint RMS focal-to-nine-teammate distance change as secondary outcome;
- D1–D10 ranked at $t$ by Euclidean distance with ascending canonical-ID tie-break, held fixed thereafter;
- near D1–D3, middle D4–D7, descriptive far D8–D10;
- all supported attacking outfield players, grouped simultaneous attackers, and exactly ten unique defending outfield players;
- goalkeeper exclusion, complete support, no interpolation, and inherited open-play/restart rules; and
- no possession-continuity requirement after $t$.

The exact 72-column float64 stacked rank-specific OLS and column order remain unchanged. Every point and bootstrap OLS fit must use `numpy.linalg.lstsq(..., rcond=None)`. Covariates remain prior focal-relative path, defensive-centroid path, mean absolute path of the other nine defenders, attacker path, anchor distance, period indicator, and attacking-team indicator. No ball variable, focal absolute path, concurrent global activity, interaction, nonlinear term, regularization, weighting change, or alternate model is permitted.

The sole primary estimand remains

$$\Delta_{NM}=\overline\beta_{D1:D3}-\overline\beta_{D4:D7}.$$

Use the frozen two-sided 95% percentile interval. D1-specific, near-versus-far, monotonicity, and rank-trend tests are prohibited. D1-largest, concentration at D1, far-versus-middle, and monotonic-shape observations may be reported descriptively only after Game 2 closes.

## 4. Game 2 dataset mechanics frozen before results

Use the closed Game 2 canonical ingestion and Stage-A support registry rather than rediscovering support:

- canonical match `metrica:sample-game-2`;
- raw 25 Hz provider frames and period-relative clock, exact-frame tolerance $10^{-9}$ s;
- centred origin, +x right, +y up, fixed pitch frame, with no attacking-direction normalization;
- canonical IDs from the governed Metrica adapter;
- goalkeeper metadata Home 11 and Away 25;
- closed `trajectory_validity_registry.csv` and `valid_support_segments.csv` exactly as hashed in the configuration;
- the Game 2 event file only for the inherited possession-at-anchor and restart/ball-out logic;
- possession types `PASS`, `RECOVERY`, `SET PIECE`, `SHOT`;
- restart types `SET PIECE`, `BALL OUT` and inherited restart subtypes;
- complete four-second support around the anchor within one frozen support segment;
- exact period-origin four-second grid; and
- deterministic exclusions serialized by the same categories as Game 1.

Do not reuse older footprint anchors: this concurrent protocol has its own prospectively fixed anchor offset and required span. Dataset-specific ambiguity may be resolved only from provider metadata and already-governed project conventions, never from the heldout outcome.

## 5. Resampling, trimming, and secondary outputs

Use 2,000 period-origin 60-second block replicates, retain terminal partial blocks, group complete D1–D10 vectors and simultaneous attackers, and require at least 1,900 valid replicates. Initialize `Generator(PCG64(SeedSequence(20260831).spawn(2)[1]))` freshly for each governed family. Primary, secondary, and trim families use identical draws.

The frozen extreme-exposure analysis removes complete anchors with concurrent attacker path above `12.198443079831405` m. Do not calculate a Game 2 percentile. Report excluded count/share, trimmed contrast and interval, sign, and retained magnitude.

Secondary deformation is:

- **SUPPORTIVE** if its near-minus-middle point estimate is positive and its 95% interval is strictly above zero;
- **DIRECTIONALLY SUPPORTIVE** if its point estimate is positive but its interval is not strictly above zero; and
- **NON-SUPPORTIVE** if its point estimate is nonpositive.

It cannot determine primary replication status. Parallel, orthogonal, and radial focal-relative displacement remain descriptive only. The shifted-time temporal control remains omitted because the estimand is intentionally concurrent.

## 6. Frozen Game 2 status

Evaluate in this order:

1. **GAME 2 CONCURRENT GEOMETRY REPLICATION INVALID** if governance, implementation, data/support, solver, or construct-validity hard QC fails.
2. **GAME 2 CONCURRENT GEOMETRY REPLICATION NOT SUPPORTED** if execution is valid and primary $\Delta_{NM}\le0$.
3. **GAME 2 CONCURRENT GEOMETRY REPLICATION SUPPORTED** if execution is valid and all hold:
   - primary $\Delta_{NM}>0$;
   - its 95% interval is strictly above zero;
   - trimmed $\Delta_{NM}>0$; and
   - trimming retains at least 50% of the untrimmed absolute magnitude.
4. **GAME 2 CONCURRENT GEOMETRY REPLICATION MIXED** for every other valid positive primary estimate.

A null or negative result is not INVALID. Positive coefficients at all ranks without positive near-minus-middle localization cannot qualify as SUPPORTED. No effect-size, D1, far, secondary, or shape gate exists.

## 7. Tier 3 closure and hard QC

Before Game 1 comparison, serialize and hash every governed Game 2 artifact, independently rerun the complete execution, and require byte-identical governed outputs. Verify at minimum: all frozen hashes; closed Stage-A support; no Game 3/IDSSE/opportunity access; unique observation IDs; exactly ten unique outfield defenders and D1–D10 once; goalkeeper/focal exclusion; exact ties and distance order; fixed ranks; complete temporal support; no interpolation; finite canonical geometry; full-rank 72-column designs; `lstsq` compliance for every fit; grouped block draws; bootstrap validity; deterministic serialization; and translation/rotation/reflection invariance.

Only after closure may Game 2 be compared descriptively with Game 1. No pooled analysis or final two-game classification is authorized by this addendum.

## 8. Prospective project decision

- If **SUPPORTED**, stop refining concurrent defensive geometry and move next to a separately governed Opportunity Redistribution design stage; do not immediately run IDSSE.
- If **MIXED**, assess whether repeated spatial structure is sufficient to justify downstream opportunity work without automatically tuning this model.
- If **NOT SUPPORTED**, stop and interpret the cross-game inconsistency before building opportunity redistribution on this construct.
- If **INVALID**, resolve validity prospectively before scientific interpretation.

## 9. Claim boundary

If supported, the maximum statement is: **Across the two Metrica sample matches, greater attacker movement within fixed two-second intervals was associated with a stronger concurrent focal-relative defender-movement coefficient among near than middle defender ranks after conditioning on the prospectively specified pre-interval movement context.**

This remains within-provider observational geometry. It cannot establish causation, reaction, latency, influence, attention, responsibility, assignment, marking, tracking, pinning, dragging, covering, handoff, defensive error, space or opportunity creation, tactical success, attacking value, gravity, cross-provider generality, or elimination of all common-motion confounding.
