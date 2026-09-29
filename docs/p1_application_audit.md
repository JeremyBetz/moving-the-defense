# Project 1 application audit

**Audit date:** 2026-09-28
**Scope:** application and public-demo layers only
**Frozen scope:** [post-submission audit protocol](protocols/p1_post_submission_audit_v1.md)

## Outcome

The scientific core and submission path are coherent and unchanged. The
application layers are individually tested and reproducible, but the public
workflow exposes their research history more clearly than their current order
of use. The principal analyst-facing defect is that the historical rapid-review
page still presents its old Rank 1 as a normal example even though the later
native-trajectory audit rejected it.

No incorrect scientific calculation was found. The required repair is to
compose the existing layers, surface support states explicitly, and keep valid,
special-context and rejected examples structurally separate.

## Component map

| Component | Purpose | Status | Normal analyst surface? | Main limitation |
|---|---|---|---|---|
| `defensive_reorganization_replay` | Trailing player and team relational-movement scores | **KEEP / authoritative measurement** | Yes, through a facade | Retrospective geometry, not tactics or a live detector |
| `defensive_reorganization_match_review` | Pooled reference, full-match scan and event alignment | **KEEP** | Yes | Possession agnostic until context is added |
| `possession_aware_defensive_review` | Conservative event-derived defending context | **KEEP** | Yes | Context is inferred from recorded events, not provider ground truth |
| `rapid_change_defensive_review` | Frozen rapid-rise retrieval | **KEEP** | Yes | Historical selection predates trajectory QC |
| `ball_alignment_reorganization_review` | Native-trajectory QC and movement orientation to the ball | **KEEP** | Yes | Ball alignment is descriptive and can be unsupported |
| `attacker_linked_reorganization_review` | Off-ball attacker co-occurrence geometry | **KEEP** | Yes, after upstream gates | “Linked” does not mean marking or cause |
| Replay/rendering modules | Static and GIF review media | **KEEP** | Yes | Media must display support and context faithfully |
| v1–v5 runners and public packages | Frozen application chronology and evidence | **HISTORICAL** | Linked as provenance | Must not be overwritten or treated as one current API |
| Event-review dashboard | Event-first preparation, filtering, lazy rendering and review packs | **SEPARATE WORKFLOW** | Yes, as an event-first product demo | It is not the rapid-change pipeline |
| Direct v3 public-example queue | Original rapid examples | **DEPRECATE AS DEFAULT** | Historical only | Old Rank 1 later failed trajectory integrity |

Nothing is classified safe to remove now. Historical filenames, runners and
packages remain necessary provenance or documented reproduction entry points.

## Triage

### P0

None found. Frozen calculations, thresholds, cohorts and paper artifacts agree
with their governed records.

### P1

1. **Invalid historical example remains prominent.** Home P1 `1734.72 s` is
   embedded as the leading rapid example even though the later audit found six
   native transitions above 15 m/s. It must remain preserved but be presented
   only as a rejected QC example.
2. **No unified current result contract.** A user must manually join raw scan,
   possession, rapid, integrity, ball and attacker outputs. This makes it easy
   to display an episode before its downstream support status is known.
3. **Unsupported values are not uniformly explicit.** Historical tables use
   nulls for unsupported ball alignment; a current analyst object needs a
   separate support/status field so null cannot be read as zero.

### P2

- README and API guide repeat several research-stage commands before providing
  a single current path.
- The case-study title says “Defensive Reorganization” while its opening raw
  scan is possession agnostic.
- Valid special context, representative examples and rejected examples are
  discussed serially but not structurally separated.
- The event-first dashboard and rapid-review workflow are both useful, but the
  relationship between them is easy to miss.

### P3

- Provider-neutral adapters beyond the existing normalized table boundary.
- A standalone deployed interface, authentication and persistent package index.
- Broader human review and usefulness validation.
- Any new scientific context, matched comparison or cross-provider application.

## Terminology findings

Current boundaries are generally careful, but application-facing navigation
should use this hierarchy consistently:

1. **Team relational reorganization** for the raw possession-agnostic score.
2. **Defensive reorganization** only after the defending context gate.
3. **Rapid defensive reorganization** for the frozen one-second increase under
   that context.
4. **Ball alignment** for descriptive movement orientation.
5. **Attacker-linked review** for concurrent geometric criteria only.

Words such as manipulation, reaction, marking, disruption, quality, success
and cause are acceptable only inside explicit exclusions or historical
scientific names. They must not label an application result.

## Example-library audit

| Existing example | Classification | Current-facing treatment |
|---|---|---|
| Home P1 `1734.72 s` | **DATA-INTEGRITY FAILURE** | Rejected QC example only; never a valid default |
| Home P1 `14.40 s` | **DATA-INTEGRITY FAILURE** | Historical audit only |
| Home P2 `4443.16 s` | **VALID BUT SPECIAL CONTEXT** | Goalkeeper-distribution diagnostic; preserve its low-ballward and distributed-link findings |
| Home P1 `336.76 s` | **GOOD REPRESENTATIVE EXAMPLE** | Clean high-ballward contrast |
| Home P2 `5355.64 s` | **GOOD REPRESENTATIVE EXAMPLE** | Clean low-ballward, localized attacker-linked example; do not call it ordinary without a frozen ordinary-context field |
| Home P1 `978.32 s` | **DIAGNOSTIC / NEGATIVE EXAMPLE** | Clean no-link contrast |
| v1/v2 high/low media | **SUPERSEDED / HISTORICAL** | Distribution and possession-gating provenance only |

The classifications above describe current presentation roles. Production
selection must derive them from frozen status/category fields and deterministic
ranking; timestamps are regression expectations, not selection rules.

## Analyst journey

The current recommended order is:

`analyze match → retrieve rapid defensive reorganization → trajectory QC →`
`possession/context → ball alignment → attacker context → render clip`

The raw score remains authoritative throughout. Later layers add review context;
they do not revise the score or explain why the movement occurred.

The event-first dashboard remains a complementary workflow for starting from
shots, goals or recorded possession changes. It should not silently substitute
for the rapid-change queue.

## Public-story boundary

The repository’s scientific story remains:

`football question → governed measurement → replicated directional evidence`

The analyst application follows as exploratory implementation:

`raw score → rapid retrieval → possession and integrity gates → descriptive`
`ball and attacker context → human review`

Only the first chain is paper evidence. The second demonstrates a disciplined
analyst workflow whose football interpretation and usefulness remain
unvalidated.
