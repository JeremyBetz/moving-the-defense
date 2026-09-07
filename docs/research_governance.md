# Current Research Governance and Firewalls

**Status:** authoritative current-facing operational record

**Established:** 2026-09-06

**Starting scientific checkpoint:** `57644b3205ead6ef7ede76aa15c3f23b28c2af8e`

This document records temporary research boundaries that may change after an
explicit, prospectively documented human decision. Permanent scientific and
engineering rules live in the root `AGENTS.md`; completed claim status lives in
the [claim-status ledger](claim_status.md). Frozen protocols remain authoritative
for individual analyses.

## Current protected boundaries

| Boundary | Current status | Required authorization to change it |
|---|---|---|
| Metrica Sample Game 3 | Untouched and outside [current paper reproduction](../REPRODUCE.md) | A prospectively approved scientific plan and any required frozen protocol before access |
| SkillCorner response-mode outcomes | Unopened; the [IDSSE response-mode result](results/defensive_response_mode_v1.md) is MIXED and does not authorize transport | A separately motivated and approved design; not a repair of the mixed result |
| Defensive Reorganization Departure residuals and retrieval | Unopened after [DRD v2](results/defensive_reorganization_departure_v2.md) classified MIXED | A separately motivated and approved design that does not alter the closed v2 result |
| Closed negative, mixed, rejected, or invalid branches | Closed as recorded in the [claim ledger](claim_status.md) | Independent football/scientific rationale, planning, and explicit approval before a new version or dataset is opened |

These are operational firewalls, not claims that previously completed authorized
outcomes remain uninspected. Historical pre-execution firewalls retain their
recorded meaning in the research log and governed artifacts.

## Current paper boundary

The public paper path is the one documented in [REPRODUCE.md](../REPRODUCE.md).
Its current entry points may read the authorized Metrica Games 1–2, seven-match
IDSSE, and nine-match SkillCorner Spatial Form inputs described there. They must
not acquire dependencies on:

- Metrica Game 3;
- DRD prediction residuals, retrieval passages, or player rankings; or
- SkillCorner response-mode outcomes.

Static repository checks can detect direct path or dependency regressions, but
they do not replace prospective protocol governance or prove that data was never
opened outside repository code.

`src/repository_policy.py` provides two bounded checks: a static import/read-path
check for the configured paper entry points, and a Git-diff check for changed
provider/publication artifacts. They inspect only configured code paths and
changed files. Blocking findings fail the relevant guard. An unresolved dynamic
read path is a visible nonblocking warning: it means the path was not statically
resolved, not that it is safe. These checks supplement review; neither can prove
non-access to a protected dataset or establish publication approval from its
metadata alone.

## Publication boundary

- Raw provider files stay under ignored local `data/` paths.
- New reconstructive provider-linked row tables, prediction/residual tables, and
  detailed eligibility ledgers require explicit publication approval.
- Existing tracked historical artifacts are grandfathered and remain part of the
  scientific audit trail.
- New public outputs should normally be compact governed summaries with units,
  provenance, and hashes.

## Changing a firewall

A firewall changes only through an explicit human decision recorded before the
protected outcome is inspected. The update must state the scientific rationale,
authorized data, applicable protocol/configuration, starting checkpoint, and
whether the change is development, heldout, external, or final execution. A task
prompt's temporary permission does not silently rewrite this document; update the
record when the decision is intended to persist.

## Scoped historical checkpoint helper

`config/execution_governance_checkpoint.json` preserves the Local Defensive
Response Form closure at `FINAL RESPONSE FORM B`. It is a valid scoped historical
checkpoint for hash verification, not the current global project-state ledger.
Use `docs/claim_status.md` and this document for current project status.
