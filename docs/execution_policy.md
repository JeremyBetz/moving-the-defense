# Tiered Research Execution Policy

**Status:** authoritative operational-governance policy

**Adopted:** 2026-09-01

**Scientific checkpoint at adoption:** `a3f11712cf9e8323cee3f275b5e402cf168cd6d9` — **GAME 1 RESPONSE FORM DEVELOPMENT COHERENT**

## Purpose

This policy reduces routine execution and documentation cost by matching operational closure to the evidentiary stage. It does **not** relax scientific rules. A prospectively frozen protocol still controls the sample, estimand, model, controls, resampling, thresholds, classification, and claims.

The default progression is:

```text
Tier 1: execute a development question cheaply
    ↓ promote only when warranted
Tier 2: close a scientifically useful milestone

Tier 3: maximum rigor from the start for heldout/final evidence
```

## Tier 1 — Development execution

Use Tier 1 for an explicitly authorized development dataset unless the frozen protocol requires more.

Required:

1. verify protocol/configuration hashes and the data firewall;
2. execute only the prospectively frozen analysis;
3. compute the required estimand, controls, robustness, and classification;
4. run focused unit and scientific-validity tests;
5. save a machine-readable result and minimal provenance record;
6. return the governed status and stop.

Normally deferred:

- independent full rerun;
- repository-wide test suite;
- broad README, roadmap, Sloan, and claim-ledger updates;
- polished publication figures;
- a complete artifact hash ledger; and
- commit/push solely to inspect the development result.

A Tier 1 result is informative but **not a closed repository milestone**. Negative or mixed results may stop with a minimal result record unless their scientific importance warrants Tier 2. Tier 1 never authorizes changing a frozen rule.

## Tier 2 — Milestone closure

Tier 2 promotes an already-computed result into the durable scientific record.

Required:

1. reverify the firewall and every frozen hash;
2. complete independent deterministic reproduction where applicable;
3. run full relevant QC and repository-wide tests when shared code changed;
4. serialize governed outputs and generate predeclared/governed figures;
5. complete result, reproduction, and hash ledgers;
6. update current-state documentation, claim status, research log, roadmap, and Sloan readiness as appropriate;
7. commit and push; and
8. verify a clean, synchronized repository.

Use Tier 2 when a development result meets its frozen success/coherence rule, a negative/mixed result materially changes the research direction, shared infrastructure changed materially, or a paper-facing milestone is being closed. Tier 2 cannot repair or upgrade a result by changing its scientific definition.

## Tier 3 — Heldout or final execution

Tier 3 is mandatory for untouched or estimand-heldout evidence, external replication, pooled final classifications, and paper-critical results. It applies maximum rigor from the start:

1. record the pre-execution firewall and frozen hashes;
2. construct the exact governed sample with no post-result tuning;
3. serialize heldout results before downstream comparison where required;
4. run every frozen control and robustness check;
5. complete hard QC, independent deterministic reproduction, and artifact hashing;
6. complete result and current-state documentation;
7. commit and push; and
8. verify clean synchronization.

Heldout evidence cannot use Tier 1 for convenience.

## Precedence rules

1. A frozen scientific protocol overrides this generic policy.
2. The tier controls operational rigor and cost—not scientific estimands.
3. Tiering never changes eligibility, time windows, ranks, thresholds, controls, bootstrap counts, models, success rules, or claim boundaries.
4. Tier 2 closure cannot change a scientific rule after seeing the result.
5. Heldout data cannot be downgraded to Tier 1.
6. If a protocol requires more than its nominal tier, the stronger protocol requirement wins.
7. Any hash, firewall, support, leakage, or validity failure stops execution at every tier.

## Escalation and closure

A result becomes scientifically closed only after the applicable frozen scientific decision has been recorded and Tier 2 or Tier 3 closure is complete. Escalation from Tier 1 to Tier 2 preserves the original computed result and rules; it adds reproduction, QC, documentation, and version-control closure. It does not rerun a different analysis.

Tier 1 should escalate when the result is coherent/successful, scientifically consequential despite failure, dependent on materially changed shared infrastructure, or needed for a paper-facing claim. Otherwise it may remain an explicitly provisional development record.

## Project examples

- **New Game 1 construct:** execute under Tier 1. If mixed and not direction-changing, stop cheaply. If coherent, promote under Tier 2.
- **Completed Game 1 Local Defensive Response Form v1:** it was executed with effectively Tier 3-like rigor and is already closed. This policy does not alter its status.
- **Future Game 2 Local Defensive Response Form v1:** it is the prospectively governed internal-replication step and must use Tier 3. It remains unexecuted.
- **Exploratory secondary-geometry decomposition on Game 1:** use Tier 1 unless its frozen protocol explicitly requires more.

## Reusable read-only helpers

The helper at `src/research_execution_governance.py` centralizes recurring mechanical checks without importing or changing scientific pipelines:

```bash
# Verify the current scientific checkpoint and forbidden heldout outputs
.venv/bin/python src/research_execution_governance.py verify-checkpoint

# Verify an analysis-specific artifact ledger
.venv/bin/python src/research_execution_governance.py verify-ledger \
  outputs/local_defensive_response_form_game1_v1 \
  outputs/local_defensive_response_form_game1_v1/final_hashes.json

# Report branch cleanliness, remote, and ahead/behind state
.venv/bin/python src/research_execution_governance.py repo-state
```

The checkpoint manifest is `config/execution_governance_checkpoint.json`. It is a convenience firewall, not a replacement for an analysis protocol. Focused and full test commands remain analysis-specific so a generic wrapper cannot silently select an incomplete scientific test set.

## Prompt economy

Future prompts may use these forms:

> Execute `[protocol]` on `[authorized development data]` under Tier 1 of `docs/execution_policy.md`. The frozen protocol controls all scientific definitions. Return the governed result and stop before milestone closure.

> Promote the completed result under Tier 2 of `docs/execution_policy.md`.

> Execute the frozen heldout/final protocol under Tier 3 of `docs/execution_policy.md`.

The prompt must still identify the protocol, authorized data, starting checkpoint, and any protocol-specific firewall. The policy supplies the generic operational requirements.

## Relationship to history

This policy is prospective. Historical executions retain their recorded rigor and status; no pipeline, result, or audit trail is reclassified or rewritten. Frozen artifacts remain authoritative, and completed negative or mixed findings remain part of the scientific record.
