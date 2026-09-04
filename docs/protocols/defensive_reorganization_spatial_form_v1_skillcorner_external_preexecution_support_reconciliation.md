# SkillCorner Spatial Form v1 — pre-execution support reconciliation

**Status:** frozen before any SkillCorner Spatial Form target, coefficient,
interval, model, or classification was constructed or read.

**Date:** 2026-09-04  
**Starting commit:** `1ad05209209700a5b49b1a9164008f840dad20ba`

## Scope

This is a mechanical implementation reconciliation, not a scientific protocol
amendment. The authoritative external protocol and configuration remain byte
unchanged:

| Artifact | SHA-256 |
|---|---|
| `docs/protocols/defensive_reorganization_spatial_form_v1_skillcorner_external.md` | `9d863157e9bf938b4e13d216f73c5b56057d9c59f34a86b47dac20a4d9d9f80e` |
| `config/defensive_reorganization_spatial_form_v1_skillcorner_external.json` | `7b1537235dd6966b9ade55a091c3688635e8cdf586673f45fa0b5aa64d50a79e` |
| `config/defensive_reorganization_spatial_form_v1_skillcorner_external_hashes.json` | `b24b0ffda4a96052851100c28254799cf7099f76b225aabb3597d8bb555f2f73` |

The pre-outcome compatibility audit described its support counts as eligible
for mechanical correction and refreeze before any coefficient could be read.
The execution preflight found such a discrepancy: its original support audit
ordered D1--D7 in native, unscaled coordinates. The frozen protocol requires
those ranks after match-specific conversion to the canonical 105 by 68 m
pitch. Length scaling differs slightly across the release (104--106 m), so a
small number of close rank identities and resulting identity-QC rows differ.

The governed implementation therefore applies the already-frozen canonical
coordinate transform *before* D-rank ordering in both support and outcome
construction. This restores the protocol's stated semantics. It changes no
window, threshold, transform, target, covariate, model, bootstrap, quality
rule, or classification rule.

## Corrected outcome-blind support inventory

All nine formal matches passed full native-versus-Kloppy equivalence before
this reconciliation. The following canonical-rank support table is outcome
blind. It uses only roster/support, coordinates, status flags, ball-in-play,
possession-at-anchor, and the frozen identity/quality gates.

| Match | Retained anchors | Primary rows | Majority-detected rows |
|---|---:|---:|---:|
| 1886347 | 630 | 5,670 | 1,529 |
| 1899585 | 565 | 5,083 | 1,068 |
| 1925299 | 730 | 6,570 | 1,305 |
| 1996435 | 663 | 5,967 | 2,559 |
| 2006229 | 644 | 5,795 | 2,278 |
| 2011166 | 503 | 4,522 | 625 |
| 2013725 | 608 | 5,471 | 942 |
| 2015213 | 572 | 5,143 | 803 |
| 2017461 | 543 | 4,886 | 701 |
| **Total** | **5,458** | **49,107** | **11,810** |

The formally excluded `1953632` release entry remains excluded unchanged.

## Firewall

At this reconciliation point no SkillCorner response target, localized
defender-relative path, coefficient, interval, bootstrap, contrast, or status
has been constructed or inspected. DRD residuals and Metrica Game 3 remain
unopened. The next permitted computation is the unchanged governed external
execution using this canonical-rank support construction.
