# Moving the Defense — Agent Instructions

## Repository purpose

This repository develops and validates measurements of defensive reorganization
associated with off-ball movement in football tracking data.

- A football concept is not automatically a tracking measurement.
- A tracking measurement is not automatically a tactical or causal mechanism.
- `docs/claim_status.md` is the authority for current scientific claims.

## Before changing anything

1. Inspect the branch, working tree, relevant source, tests, and authoritative
   documentation before editing.
2. Preserve unrelated user work and historical scientific artifacts.
3. Read `docs/research_governance.md` before opening data or result paths.
4. Classify the work:
   - **Trivial:** an unambiguous typo, link, formatting, or exact path/title fix
     with no behavioral or scientific effect.
   - **Nontrivial:** any source, test, dependency, schema, figure, interface,
     automation, or multi-file behavior change. Plan before editing.
   - **Scientifically material:** any change to an estimand, outcome, control,
     sample, window, rank, smoothing, threshold, inference, classification, or
     protected-data boundary. Plan and obtain explicit human approval.

Executing an already-frozen protocol is permitted when the current user prompt
explicitly authorizes that execution and all applicable firewall and hash checks
pass. Any change to the frozen design still requires separate approval.

## Scientific invariants

- Frozen protocols and configurations override generic workflow instructions.
- Never change a scientific rule, result, or claim to obtain a preferred outcome.
- Preserve negative, mixed, rejected, and invalid findings in the audit trail.
- Stop on leakage, support, hash, estimability, or firewall ambiguity that could
  change a governed result.
- Do not turn observational geometry into causation, attention, assignment,
  tactics, player quality, gravity, or value without separate supporting evidence.
- Do not reopen a closed branch without an independently motivated, prospectively
  approved design.

## Data, protected outcomes, and publication

- Follow the current firewalls in `docs/research_governance.md`.
- Do not commit raw provider tracking data.
- Do not add reconstructive provider-linked row tables, predictions, residuals,
  or detailed eligibility ledgers without explicit publication approval.
- Preserve provider and licence attribution.
- Existing tracked historical artifacts are grandfathered scientific records;
  do not silently rewrite or delete them.
- Prefer compact, governed, publication-safe summaries with provenance and hashes.

## Implementation standards

- Inspect before editing and make the smallest coherent change.
- Avoid unrelated refactors and preserve public/reproduction interfaces unless
  their change is intentional and documented.
- Use existing repository conventions; do not migrate closed historical pipelines
  merely to modernize them.
- Fail closed instead of suppressing errors involving scientific validity,
  missing support, identity, hashes, or protected outputs.

## Tests

- Every behavior change requires relevant automated tests.
- Add a regression test for a bug fix when feasible.
- Prioritize scientific invariants over arbitrary line-coverage percentages.
- Keep ordinary tests synthetic and compact; mark tests that require local
  provider data with `provider_data`.
- Keep current-paper exact-value locks separate with `paper_release`.
- Do not weaken or delete an assertion merely to make the suite pass.
- Never report a check as passing unless it was actually run.

## Reproducibility and artifacts

- Do not overwrite closed governed outputs.
- Use temporary paths, disposable worktrees, or disposable clones for independent
  reproduction when a script protects its output directory.
- Preserve deterministic serialization, seeds, manifests, and hash ledgers.
- Document new entry points and reproduction-path changes.
- Full-data reruns follow the applicable tier in `docs/execution_policy.md`.

## Documentation and claims

- Reconcile current-facing prose with `docs/claim_status.md`.
- Update `REPRODUCE.md` or `docs/reproducibility.md` when a reproduction interface
  changes.
- Preserve historical filenames and wording when changing them would damage
  provenance; add current-facing clarification instead.

## Git and completion

- Review the complete diff and run relevant tests plus `git diff --check`.
- Commit only intended files in a focused commit.
- Push only when explicitly requested and after publication-boundary checks.
- Report starting and ending HEAD, tests run, files changed, scientific impact,
  and protected-data status.
- If a task requests a commit, stage and commit only the intended files. Never
  disturb unrelated user work; report any unrelated state that remains.

## Authoritative repository map

- Current claims and limitations: `docs/claim_status.md`
- Current research firewalls: `docs/research_governance.md`
- Execution rigor: `docs/execution_policy.md`
- Human paper reproduction: `REPRODUCE.md`
- Detailed technical reproduction: `docs/reproducibility.md`
- Current manuscript and supplement: `docs/manuscript_skeleton.md`,
  `docs/manuscript_supplement.md`
- Roadmap and chronology: `docs/research_roadmap.md`, `docs/research_log.md`
- Frozen scientific definitions: `docs/protocols/`
- Frozen machine-readable rules: `config/`
- Implementations and automated checks: `src/`, `tests/`
