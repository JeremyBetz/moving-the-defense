# IDSSE Provider Equivalence for Concurrent Geometry v1

**Status:** prospective adapter specification; no concurrent-geometry IDSSE outcome inspected

The external replication keeps the football measurement fixed and confines provider differences to ingestion. The established path is:

```text
IDSSE/Sportec XML
    → Kloppy IDSSE adapter + raw timestamp sidecar
    → canonical fixed-pitch tracking contract
    → unchanged Concurrent Attacker–Defensive Geometry v1 construction
```

## Representation mapping

| Scientific requirement | IDSSE implementation | Equivalence condition |
|---|---|---|
| 25 Hz physical trajectory | Native `Frame.X`, `Frame.Y` in metres | Exact cadence and finite observed coordinates |
| Fixed pitch | Centred 105 × 68 m, +x right, +y up | No attacking-direction normalization |
| Period clock | Raw UTC `Frame.T` plus period-opening `KickOff` | Exact period/frame/time identity |
| Player/team identity | Provider `PersonId` / `TeamId`, retained canonically | Exact reversible IDs |
| Goalkeeper exclusion | `PlayingPosition == TW` | Match metadata and adapter agree |
| Complete support | Explicit observed/null roster rows | Exact masks; no interpolation or padding |
| Possession/open play | Existing event-clock state machine | Exact anchor state; no outcome-dependent filtering |
| Simultaneous attackers | Shared anchor/block identity | Entire anchor retained in one bootstrap unit |

The centered seven-frame smoother is unchanged. A used endpoint requires its full seven raw frames; $t-2$ through $t+2$ contains 101 smoothed positions and 100 increments. An anchor is retained only when the focal attacker and all ten defending outfield players have complete raw support, including the three smoothing frames beyond both outer endpoints.

## Mandatory pre-outcome equivalence gate

Run the current provider-native IDSSE representation and the canonical adapter on each of the seven governed matches before fitting an outcome model. Require exact equality for discrete identities, masks, context state, sample keys, and rank membership. Require maximum discrepancies of $10^{-5}$ m for coordinates, $10^{-4}$ m for derived components, and $10^{-3}$ m for paths.

The existing J03WMX adapter audit supports the architecture but does not waive the seven-match gate. Any mismatch must be resolved without inspecting concurrent-geometry outcomes. If scientifically equivalent construction cannot be established for every governed match, the external replication is **INVALID**; a difficult match cannot be silently excluded.

Provider adaptation does not authorize alternate coordinates, resampling, interpolation, smoothing, support relaxation, rank rules, predictors, or football semantics.
