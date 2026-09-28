# Game 1 Event-Ordering Compatibility Audit

**Status:** closed aggregate-only source compatibility audit  
**Classification:** **B — EVENT-TYPE-SPECIFIC COMPATIBILITY JUSTIFIED**  
**Freeze commit:** `42326b440fcec5de45ee8977dd97eae0e40a88be`

## Purpose and access boundary

This audit investigated the single source-ordering failure that blocked the
already-frozen ball-alignment review. It read only the public Metrica Sample
Game 1 event metadata and the Home/Away native tracking clocks needed to check
event Start fields. It did not construct possession states, calculate
relational-reorganization scores, join scores to events, rank passages, inspect
ball alignment, or render media.

The malformed source record was preserved exactly. No endpoint was swapped,
clamped, replaced, dropped, or otherwise repaired.

## Source semantics

Metrica's public sample-data README says the tracking and event data are
synchronized and points to its event-definition document. That document
defines event types, subtypes, and possession terminology. In particular, it
defines a SET PIECE as bringing the ball back into play. It does **not** define
the raw CSV semantics of `Start Frame`, `Start Time [s]`, `End Frame`, or
`End Time [s]`.

Accordingly, this audit treats the football event definitions and stated source
synchronization as documented facts. The interpretation of individual CSV
time fields is identified as source-pattern evidence or project implementation
dependency, not provider-documented fact. The retrieved event-definition PDF
had SHA-256
`5afb1ee34931447223ef8b9dc6a30b827fd0ba57ac9b6e2d7125ee87b083a866`.

## Aggregate anomaly result

Game 1 contains **1,745** event records. Exactly **one** record has both an End
Time earlier than its Start Time and an End Frame earlier than its Start Frame:
**1/1,745 = 0.0573066%**.

The anomaly is confined to period 1 and the `SET PIECE / KICK OFF` source
category. Its recorded duration difference is `-0.04 s`; because it is the
only anomaly, the minimum, P25, median, P75, and maximum are all `-0.04 s`.
No identifying timestamp or frame is published.

The source pattern is consistent with a match-opening boundary record: the
event Start maps exactly to the first supported native tracking frame, whereas
its End precedes tracking support. This is strong source-pattern evidence, not
an assertion that Metrica formally documents a sentinel convention.

## Start integrity

- All 1,745 Start Frames are finite whole values.
- All Start Times are finite.
- Start Frame and Start Time are nondecreasing in provider row order within
  both periods.
- Home and Away tracking clocks are identical.
- Every event Start Frame maps to exactly one native tracking time.
- Every event Start Time equals its native tracking time exactly; the maximum
  absolute mismatch is `0.0 s`.

The Start path therefore passes the frozen integrity and reconciliation gate.

## Possession dependency result

| Possession operation | Needs Start | Needs End Frame | Needs End Time | Current behavior |
|---|---:|---:|---:|---|
| PASS establishment/change | yes | no | no | evaluated at Start |
| RECOVERY establishment/change | yes | no | no | evaluated at Start |
| SET PIECE restart | yes | no | no | restart and pending owner use Start |
| SHOT possession evidence | yes | no | no | evidence uses Start |
| BALL LOST ambiguity | yes | no | no | ambiguity begins at Start |
| CHALLENGE | yes | no | no | inspected at Start; does not establish possession |
| BALL OUT | yes | no | no | dead ball opens at Start |
| FAULT RECEIVED | yes | no | no | dead ball opens at Start |
| CARD | yes | no | no | dead ball opens at Start |
| SHOT with GOAL/OUT subtype | yes | **yes** | no | dead ball opens at End Frame |
| FORCED-END HALF | yes | no | no | state change uses Start |
| Restart-frame handling | yes | no | no | SET PIECE Start is dead; possession begins next frame |
| Period boundary | yes | no | no | state resets from the native period clock |

The unchanged implementation validates End Time globally but never otherwise
consumes it. `End Frame` is consumed only for SHOT records whose subtype
contains `GOAL` or `OUT`. Game 1 contains 15 such endpoint-dependent records;
all 15 have ordered End Time and End Frame values, and every required End Frame
is present in native tracking.

The malformed KICK OFF End therefore does not affect any required possession
operation. A start-time-only classification is not appropriate because one
explicit event class does require End Frame.

## Prospective compatibility rule

For both Metrica Sample Games 1 and 2:

1. Every event must retain a finite whole Start Frame, finite Start Time,
   nondecreasing provider ordering, exact native-clock reconciliation, and the
   existing simultaneous-ownership conflict checks.
2. SHOT records whose subtype contains `GOAL` or `OUT` must additionally have
   finite, ordered End Frame and End Time values, and their End Frame must
   reconcile to native tracking.
3. Other event classes do not use End fields for possession reconstruction.
   Their raw End metadata is preserved and any reversal remains reported in
   QC, but an unused reversal does not reject reconstruction.
4. No value is swapped, clamped, absolutized, replaced, or dropped.

This rule is deterministic, outcome-independent, and based on the unchanged
operation dependency rather than the eventual possession or ball-alignment
result.

## Required implementation tests

A separate bounded implementation must demonstrate:

- unchanged handling of valid Start/End records;
- tolerance only for malformed unused End fields permitted by the frozen rule;
- blocking of malformed required SHOT GOAL/OUT endpoints;
- blocking of nonfinite, non-whole, disordered, or unreconciled Starts;
- unchanged blocking of conflicting simultaneous ownership;
- unchanged blocking of period-boundary contradictions;
- unchanged Game 2 behavior;
- visible aggregate QC for every tolerated malformed source endpoint; and
- no mutation of caller input or provider files.

## Interpretation and next gate

This is a source-compatibility finding, not a football result. It does not
authorize possession reconstruction or resume the ball-alignment review by
itself. The next bounded task is to implement and independently test this exact
event-type-specific rule, then resume the already-frozen ball-alignment
execution only after those checks pass.
