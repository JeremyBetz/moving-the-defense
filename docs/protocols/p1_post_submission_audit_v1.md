# Project 1 post-submission application audit v1

**Status:** frozen before application hardening  
**Frozen:** 2026-09-28  
**Starting HEAD:** `6ecab49d8a1b663f9d962ef218e78992b7a2d3d3`

## Purpose

Audit and harden the exploratory analyst application after completion of the
SSAC27 first-pass submission. This is application engineering and public
communication work, not a new scientific analysis.

## Immutable submission and scientific layer

The following files are immutable in this pass (SHA-256):

| Artifact | SHA-256 |
|---|---|
| Candidate V1 PDF | `3a8b5f45e0e5ae619877d7c5b162d0b65c2390885875fae76b0465c6fde7f867` |
| Manuscript | `1ebff91073f1b2a4a6a3763c50593933597ae4ee62215e7f01d5c8875c65d510` |
| Supplement | `06005d2e04a88ba2d1814f4b71eaa272f6e94a0bc9309bab8a5c6eea96022aa8` |
| Governed Figure 1 SVG | `a73f9287b3bfd2f5b618efa10f018530921dd9837b86a3e3b3427d87d4c989de` |
| Governed Figure 2 SVG | `4971093833234293dace4d63ca829a7ad6a12c1edf9206aaecd9154e720a75d1` |
| Production replay scorer | `6b5f33de5a034ae4000270e847ebcefe0164b1df1d21d4f3a7ed8adf9bd24a8a` |
| Additional SkillCorner replication final ledger | `43713a1e37aa1e28604486dac53a9f1b01503dfab67280d64af37c12ae34185b` |
| SkillCorner lateral-gradient final ledger | `86fe1d81ba94649d078556e383de7e5128d934f1082194d292d99ed06fc64525` |
| IDSSE response-map final ledger | `cdcc57f5ddad9761da4cc3dd9233e573d84325ecdcccd4be4251a04ba76d1dcc` |

Historical application packages are also immutable:

| Package | Manifest SHA-256 |
|---|---|
| Full-match scan v1 | `bd8680ff2e860823d6556fd8d6671b6ec1defa651c62f01b5dbd26f8c8be6fcd` |
| Possession-aware review v2 | `f695ed86990fbcfd7d92014802a83cab02aecaf5095259b1d4ae4b0aa34a9656` |
| Rapid-change review v3 | `9719e7e418c77834775976641e8661a2e79dce16e8a7d75a8ea0523ab2b1cabf` |
| Ball-alignment review v4 | `23d51e89e6eedf82bd1981515b28573ffcd686b2d422b818aa2beb0ee17bff0d` |
| Attacker-linked review v5 | `2c43c05604b682a69cfb543624ceaa8914f32423b4fa9d495f54d5ca2e24f713` |

## Authorized application work

- Audit code, tests, documentation, links, terminology, examples and UX.
- Add orchestration that calls existing frozen measurement and context layers.
- Clarify names and explicit unsupported states.
- Separate valid representative examples, valid special-context diagnostics and
  rejected examples.
- Derive examples only from existing frozen classifications and deterministic
  rankings. Timestamps may be regression expectations but never selection rules.
- Add regression tests and a deterministic public-Metrica demonstration command.

## Prohibited work

- New estimands, inference, thresholds, datasets or scientific claims.
- Game 3, DRS, protected outcomes or reopened closed branches.
- Tuning selections after viewing clips.
- Changing the production scorer, scientific configurations or paper results.
- Rewriting or deleting historical packages.
- Causal attacker-manipulation, marking, tactical-quality or value claims.

## Terminology

- **Team relational reorganization:** raw possession-agnostic measurement.
- **Defensive reorganization:** relational reorganization when context establishes
  that the evaluated team is defending.
- **Rapid defensive reorganization:** the frozen one-second increase in valid
  defensive context.
- **Ball alignment:** descriptive orientation relative to the ball.
- **Attacker-linked review:** descriptive geometric co-occurrence only.

## Stop conditions

Stop rather than repair if application hardening would require changing a
scientific quantity, threshold, population, context rule, protected-data
boundary or any immutable hash above. Invalid and unsupported episodes remain
visible as diagnostics but cannot enter the valid default queue.
