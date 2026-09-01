# Spatial Defensive-Response Footprint v1 — Held-Out Execution Clarification

**Status:** **FROZEN BEFORE GAME 2 FOOTPRINT OBSERVATION**

**Clarification date:** 2026-09-01

**Starting commit:** `80be8c3e3c7d1805ea735ba69bc17220884443ee`

**Scientific effect:** none. This clarification changes sequencing and reporting semantics only. It changes no metric, sample, model, threshold, contrast, bootstrap, interval, control, robustness rule, horizon, or Final Footprint A/B/C criterion.

## 1. Prospective firewall

Before this clarification was written and frozen:

- no Metrica Sample Game 2 spatial-footprint result had been computed or inspected;
- no pooled spatial-footprint result had been computed or inspected;
- no Game 2 spatial-footprint output or figure existed;
- Metrica Sample Game 3 remained untouched; and
- the closed Game 1 footprint result remained `GAME 1 FOOTPRINT DEVELOPMENT COHERENT`.

The authoritative scientific artifacts remained unchanged:

- `docs/protocols/spatial_defensive_response_footprint_v1.md`: SHA-256 `649c40c551d880f5204f6ccca7e37cf219660c4a5fdea590e0b73b6377534458`;
- `config/spatial_defensive_response_footprint_v1.json`: SHA-256 `b784b3839146a424acd427a0f1d99959f3ef547039743d30ce90e39f9e557c9c`.

## 2. Governance gap

The frozen protocol defines:

1. Game 1 development classifications:
   - `GAME 1 FOOTPRINT DEVELOPMENT COHERENT`;
   - `GAME 1 FOOTPRINT DEVELOPMENT MIXED`;
   - `GAME 1 FOOTPRINT DEVELOPMENT INVALID`.
2. `FINAL FOOTPRINT A`, `FINAL FOOTPRINT B`, and `FINAL FOOTPRINT C` after the authorized Game 1, Game 2, and pooled sequence.

It does **not** define a separate Game 2 coherent/mixed/invalid scientific classification. Consequently:

- no Game 2-only coherent/mixed/invalid status may be invented;
- the Game 1 development gates may not be silently reused as Game 2 classification gates;
- Game 2 quantities remain individually descriptive and unclassified until they enter the already-frozen Final Footprint evaluation; and
- Final Footprint A/B/C may be assigned only after the required Game 2 and pooled executions are complete, valid, saved, hashed, and reproduced.

## 3. Clarified execution sequence

1. Execute Game 2 with the exact frozen Game 1 footprint implementation and every frozen scientific rule unchanged.
2. Produce the complete governed Game 2 result set already required by v1:
   - sample and exclusion ledger;
   - D1–D10 rank-distance diagnostics;
   - primary coefficients and frozen intervals;
   - D1–D3, D4–D7, and D8–D10 regional estimates;
   - the frozen classifying contrasts;
   - inherited near/far consistency;
   - temporal placebo;
   - metric-distance complement;
   - extreme-exposure robustness;
   - frozen horizons;
   - hard QC; and
   - deterministic reproduction.
3. Save, hash, and independently reproduce every governed Game 2 output before comparing Game 2 descriptively with Game 1.
4. Do not give Game 2 a standalone coherent/mixed/invalid scientific classification.
5. After Game 2 is closed, execute the already-authorized pooled footprint analysis exactly as specified by the original frozen protocol.
6. Only then assign `FINAL FOOTPRINT A`, `FINAL FOOTPRINT B`, or `FINAL FOOTPRINT C` using the original criteria.

No new decision rule is introduced. This clarification resolves only when classification occurs and how the held-out match is reported between execution and the final pooled step.

## 4. Non-amendment statement

This document is not a scientific-protocol amendment. The authoritative v1 protocol and machine-readable configuration retain their original hashes. If a later implementation conflicts with them, execution must stop; this clarification cannot be used to repair, tune, or reinterpret a scientific result.
