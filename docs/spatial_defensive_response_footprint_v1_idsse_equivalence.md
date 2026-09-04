# IDSSE Provider Equivalence for the Temporal Spatial Footprint v1

**Status:** prospective adapter specification; no IDSSE temporal-footprint
association, coefficient, interval, sample count, or classification has been
computed or inspected.

The external replication preserves the closed Metrica football measurement and
uses the established provider path:

```text
IDSSE/Sportec XML
  → Kloppy IDSSE adapter + raw timestamp sidecar
  → canonical fixed-pitch tracking contract
  → unchanged time-ordered spatial-footprint construction
```

| Closed requirement | IDSSE implementation | Gate before outcome fitting |
|---|---|---|
| Fixed pitch | centred 105 × 68 m, +x right, +y up | coordinate difference <= 1e-5 m; no attacking-direction normalization |
| Time | raw UTC `Frame.T`, retained `Frame.N`, period origin = first observed provider frame | exact timestamp/frame/period identity; native 40 ms cadence |
| Seven-frame mean | centred arithmetic mean, full raw support only | same 0.28 s physical support; no partial window or interpolation |
| Strict timing | prior `[t-4,t-2]`, exposure `[t-2,t]`, response `[t,t+2]` | exact physical-time endpoints on `origin + 4 + 4k` |
| IDs and roster | provider PersonId/TeamId and PlayingPosition `TW` | exact reversible IDs, team assignment, goalkeeper flag, and masks |
| Support | explicit finite observed coordinates | exact observed/null mask agreement; complete attacker + ten defender support |
| Context | established IDSSE event-clock state machine | exact possession/open-play state and restart/ball-out decision |
| Ranks | anchor distance then canonical player key | exact D1–D10 membership and tie resolution |
| Derived geometry | native and canonical construction | components <= 1e-4 m; paths <= 1e-3 m |

The historical bridge source uses 25 Hz positions (`positions25`) and a
centred seven-frame mean. This differs from earlier project analyses that
deliberately used 10 Hz Metrica derivatives; those analyses are not this
bridge’s source of truth. Therefore the bridge transfers its physical
two-/four-second windows and seven-frame full-support mean only when IDSSE’s
actual native cadence passes the 25 Hz gate. A cadence mismatch is invalid for
this frozen external bridge rather than an invitation to silently change the
smoother.

Ball coordinates are not a predictor or outcome. The event clock uses raw UTC
for possession and global restart/ball-out exclusion; ball-object-key
differences remain a provenance-sidecar detail, not a construct substitution.
All equivalence work is mechanical and outcome-blind: it must finish before a
regression, bootstrap interval, or external status is calculated.
