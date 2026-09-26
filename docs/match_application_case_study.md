# Case study: three active passages for defensive-unit review

## The analyst question

When does a defence move substantially within its own shape, which defenders
contribute most, and which contrasting passages should be opened in video next?

This case study scans public Metrica Sample Game 2 and returns three distinct
review moments: high within-unit movement, low defensive response while the
attack remains active, and one non-overlapping rapid increase. The score is
trailing two-second movement relative to the other nine defenders. It retrieved
the passages; an analyst—not the metric—supplied any football interpretation.

## Three review moments

### 1. High movement · 14:05 · Home defending

Home led 1–0. Away was the last recorded possession team and the ball was in
the physical left third, attacking toward the physical right. The previous
Away pass was 1.3 seconds before the anchor and the next Home challenge was
2.8 seconds after it; both occur inside the replay. Across the view, the ball endpoint moved
25.7 m horizontally and 19.3 m laterally. Home's team score reached 5.66 m
(99.7th percentile). Players 8, 7, and 4 had the three largest individual
defender-relative paths. Defensive width changed from 55.5 m to 32.0 m, depth
from 39.4 m to 36.0 m, and the centroid shifted 4.0 m.

Why review it: this is the fixed reviewed high-movement reference. It is not a
claim that the defending was good, bad, or caused by the opponent, and it is
not presented as a fully matched pair with the conditional-low passage.

### 2. Rapid increase · 5:36 · Home defending

At 0–0, with Away as the last recorded possession team in the physical middle
third and attacking toward the physical right, Home's score rose into the
98.4th percentile. Away passes occur 0.3 seconds before and 0.8 seconds after
the anchor, both inside the replay. The ball endpoint changed 17.6 m;
defensive width changed from 64.0 m to 36.9 m, depth from 33.6 m to 27.1 m,
and the centroid shifted 11.2 m. Players 8, 7, and 1 contributed the largest
individual paths.

Why review it: the metric retrieved the strongest suitable non-overlapping
rapid increase. On visual review, an analyst may reasonably treat it as a
counter-pressing candidate. That interpretation is not an automatic tactical
classification and has not been independently validated.

### 3. Conditional low response · 83:59 · Home defending

Home led 3–2. Away held the possession proxy in the physical right third and
attacked toward the physical left. Across the ten-second window, the ball
travelled 64.1 m, moved 26.9 m in the attacking direction, and changed endpoint
by 37.4 m; two Away actions were recorded. Five of six transparent activity
components passed. Home's defender-relative team score nevertheless remained
1.12 m (4.9th percentile). Defensive width changed from 39.4 m to 42.7 m,
depth from 25.2 m to 35.4 m, and the centroid shifted 3.2 m. Players 9, 14, and
13 supplied the largest individual paths.

Why review it: this answers the useful low-response question—what unusually low
defensive relative movement looks like while the attack is still doing
something. It was selected only after passing an activity gate requiring the
attacking possession proxy and at least two of four on-ball components.

The generated analyst package contains a ten-second GIF, compact context card,
simplified analyst diagnostic, and technical appendix for each moment. Those
local artifacts are generated below the caller's chosen temporary output
directory in `selected_clips/` and are not committed provider-derived outputs.

The main analyst diagnostic shows only the team trace, anchor, replay frame,
and context. A separately named technical appendix retains all ten player
traces and saturation disclosure.

## What the comparison adds

The high passage was fixed first as the strongest suitable high candidate. The
conditional-low search then prioritized genuine attacking activity before
matching context. It matched the high passage on defending team and possession
proxy, but not period or physical field third. This tradeoff is explicit: a
perfect contextual match would have returned the visually inert passage the
activity gate was designed to reject.

The high passage combines substantial within-unit movement with large changes
in ball location and defensive width. The conditional-low passage shows active
ball progression with relatively little within-unit movement. The rapid-increase
passage identifies a separate episode in which the metric changes sharply.
These are review cues, not tactical categories.

## Supporting match scan

| Defending team | Stable runs | Supported frames | Median | 5th–95th percentile |
|---|---:|---:|---:|---:|
| Home | 5 | 140,873 | 2.52 m | 1.12–4.27 m |
| Away | 3 | 140,987 | 2.35 m | 0.97–4.15 m |

All 24 recorded shots, including five goals, were aligned descriptively to the
defending-team timeline. Goal percentiles ranged from 15.2% to 98.8%, evidence
against treating the score as a goal detector. The event table remains a local
review aid rather than a performance evaluation.

## Suitability and interpretation boundary

The fixed high and rapid-increase identities were selected in the earlier
review and are reproduced deterministically here. The conditional-low search
is automatic and occurs before viewing its candidates. Candidate episodes must
be at least eight seconds from support boundaries and their full ten-second replay
must have complete ball support, live-play event context, no restart/dead-ball
overlap, no out-of-pitch players, and no gross tracking discontinuity above
15 m/s. Episodes are deduplicated across public categories.

The possession field is a last-recorded-event proxy, not a provider possession
state. Physical thirds are not attack-normalized. Shape summaries are endpoint
descriptions. None of these fields identifies marking, intent, defensive
quality, causal influence, tactical effectiveness, or value.

## Run it with two paths

```python
from run_metrica_game2_application import analyze_metrica_game2

case = analyze_metrica_game2(
    data_dir="data/metrica_sample_game_2",
    output_dir="/tmp/mtd_game2_analyst_case",
    render_selected=True,
)
```

- [Provider-neutral scoring API](replay_scoring_api.md)
- [Visualization guide](defensive_reorganization_replay_visualization.md)
- [Output-free fixed-passage notebook](../notebooks/defender_relative_replay_demo.ipynb)
