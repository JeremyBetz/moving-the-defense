# Game 1 Event-Ordering Compatibility Audit

**Status:** frozen before detailed malformed-record inspection  
**Frozen:** 2026-09-28  
**Starting commit:** `0ef0323169f86f0946ea942483cd21259009dfbb`

## Purpose and boundary

This audit asks why the unchanged possession normalizer rejects Metrica Sample
Game 1 because a recorded event end precedes its start, and whether a narrow,
prospective compatibility rule is scientifically defensible. It is an
outcome-blind source-compatibility audit, not possession reconstruction or a
scientific analysis.

Authorized inputs are the public Game 1 event source, Game 1 tracking timestamps
only when needed to reconcile event starts, the current event normalizer and
possession adapter, and public Metrica source documentation. The audit must not
construct possession states, relational-reorganization scores, event-score
joins, ball-alignment quantities, rapid candidates, or visual clips. Game 3,
IDSSE, SkillCorner, and protected outcomes remain closed. Event types and
subtypes may be summarized only as source-encoding categories, not interpreted
as outcomes.

The source file is read-only. The audit may not swap starts and ends, clamp or
take absolute durations, substitute zero duration, drop malformed events, or
replace the Games 1-2 reference design with Game 2 alone.

## Frozen questions

The audit answers only:

1. How many Game 1 records have `End Time [s] < Start Time [s]`?
2. Are anomalies isolated or repeated, concentrated by type, subtype, or
   period, or consistent with a provider encoding pattern?
3. Are Start Time and Start Frame finite, provider-ordered, and uniquely
   reconcilable to the native period clock?
4. Which possession operations consume Start fields, End Frame, or End Time?
5. Does provider documentation explicitly define the raw Start/End fields, and
   what remains project inference?

Time and frame ordering are assessed separately. The audit must report both
`End Time < Start Time` and `End Frame < Start Frame`; agreement between them is
evidence, not an assumption.

## Aggregate diagnostics

The committed package contains only:

- total event count and malformed count/rate;
- anomaly counts by period, event type, and subtype;
- negative-duration minimum, NumPy-linear P25, median, P75, and maximum;
- Start-field finiteness, ordering, uniqueness, and tracking-clock support;
- a field/schema summary and possession dependency matrix;
- the classification, QC, provenance, and hashes.

No raw offending rows, event timestamps, frame IDs, coordinates, player/team
identifiers, possession states, or event-score joins may be serialized.
Detailed offending records may be inspected locally only after this protocol is
committed.

## Frozen dependency questions

Static tracing must cover PASS, RECOVERY, SET PIECE, SHOT, BALL LOST,
CHALLENGE, BALL OUT, FAULT RECEIVED, CARD, goal/shot OUT subtypes,
FORCED-END HALF, restart handling, and period boundaries. For each operation,
the report states whether Start and End are required and why.

The pre-audit implementation trace to verify is that Start fields drive event
ordering and ordinary possession/restart logic; `End Frame` is additionally
used to open dead ball for SHOT records containing `GOAL` or `OUT`; and
`End Time [s]` is validated but not otherwise consumed.

## Classification rule

Exactly one classification is emitted:

- **A — START-TIME-ONLY COMPATIBILITY JUSTIFIED:** documented or strongly
  evidenced semantics and the dependency trace show that no possession
  operation requires an End field. Malformed End metadata remains visible.
- **B — EVENT-TYPE-SPECIFIC COMPATIBILITY JUSTIFIED:** Start integrity passes;
  End is required only for explicitly identified event classes; every required
  endpoint is valid; and malformed unused End metadata can remain visible
  without affecting possession results.
- **C — STRICT BLOCK REQUIRED:** any Start field fails integrity or
  reconciliation, a malformed required endpoint affects possession logic, or a
  deterministic compatibility rule would change event ordering or support.
- **D — SOURCE SEMANTICS INSUFFICIENT / AMBIGUOUS:** available provider/source
  evidence cannot establish safely whether the malformed field is irrelevant.

A or B is permitted only when the rule:

- follows documented or strongly evidenced source semantics;
- is outcome-independent and deterministic;
- applies identically to Games 1 and 2;
- preserves provider Start ordering and all source values;
- leaves every anomaly detectable in QC; and
- does not make possession results depend on a malformed field except where an
  explicitly documented event class requires it.

No scientific or visual result may influence classification.

## Prospective implementation tests

If A or B is justified, the result report must freeze tests for a later,
separately authorized implementation. At minimum they cover unchanged valid
events, tolerance only for an unused malformed endpoint allowed by the rule,
blocking of malformed required endpoints, blocking of Start disorder,
simultaneous conflicting ownership, period contradictions, unchanged Game 2
behavior, and persistent QC reporting of malformed source metadata.

This audit does not implement that compatibility rule and does not resume the
ball-alignment execution.

## Protected working-state identities

The following untracked work must remain unedited and uncommitted:

| Path | SHA-256 at audit freeze |
|---|---|
| `src/ball_alignment_reorganization_review.py` | `20a4a3e043ad82b0d135c438792cc3f9a72f18c9e3ac4917a397d372cae18817` |
| `src/run_ball_alignment_reorganization_review.py` | `ddd18cab76b7e722fed6be37d653248d372076a21b0622790cb9e94a803a72c3` |
| `tests/test_ball_alignment_reorganization_review.py` | `d2ee4e2dc8bfa64fac515d57319d65322fffb06dc42adf9e5547e8a36ead2cca` |

Candidate V1, governed Figures 1-2, the production scorer, historical v1/v2/v3
application packages, and the ball-alignment freeze remain byte-identical.
