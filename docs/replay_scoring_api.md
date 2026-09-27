# Defender-relative replay scoring API

The replay scoring API is a thin, local JSON boundary around the approved
retrospective scorer in `src/defensive_reorganization_replay.py`. It does not
host a service, load provider files, or introduce a new metric.

## Contract

One request contains exactly:

```json
{
  "schema_version": "1.0",
  "spec": {
    "defending_team_key": "Away",
    "source_fps": 25.0,
    "window_seconds": 2.0,
    "smoothing_frames": 7,
    "smoothing_method": "centered_mean"
  },
  "tracking": []
}
```

`tracking` uses the normalized long-format schema documented by the replay
renderer: match, period, provider frame, match time, entity/team/player keys,
metre coordinates, coordinate-valid flag, and constant 105 × 68 m pitch
dimensions. Raw Metrica, SkillCorner, IDSSE, or Kloppy objects must be adapted
before reaching this boundary.

The response contains the documented player-score and team-score tables plus
scorer metadata. Unsupported numeric scores are JSON `null`. The API never
returns input coordinates, discovers response fields, infers possession or
marking, interpolates support, or normalizes raw metre values.

Run it locally with:

```bash
.venv/bin/python src/defensive_reorganization_replay_api.py request.json \
  --output response.json
```

Omit `--output` to write the response to standard output, or pass `-` as the
request path to read from standard input.

For Python workflows, `score_match(...)` in
`src/defensive_reorganization_application.py` adds an optional time range while
retaining the necessary support outside that range. `export_scores(...)` writes
the player and team timelines as CSV and Parquet plus JSON metadata.

`discover_moments(...)` identifies three descriptive passage types from the
supported team timeline: upper-tail intensity, lower-tail intensity, and large
positive frame-to-frame changes. Adjacent candidate frames are grouped before
selection so one episode is not returned repeatedly. Each row includes its
within-match percentile and the leading player-score contributors. Selection
is geometry-only and occurs before manual viewing.

Final clip selection applies a symmetric six-second interior-support guard at
period, roster-run, substitution, and support-gap boundaries. Six seconds
covers the trailing two-second score, three seconds of visual context on either
side of a selected peak, and the centered-smoother edge with a conservative
margin. Boundary candidates remain in `moment_audit.csv` with their distances
and flags, but cannot be selected for the public clip set.

## Notebook-first full-match workflow

The high-level application call keeps the ordinary notebook decision surface
small. The caller supplies normalized tracking, the two team keys, provider
cadence/smoothing, and any known goalkeeper exclusions. Optional normalized
events use the columns documented by `align_events(...)`.

```python
from defensive_reorganization_application import MatchApplicationConfig, analyze_match

config = MatchApplicationConfig(source_fps=25.0, smoothing_frames=7)
result = analyze_match(
    normalized_tracking,
    defending_team_keys=("metrica:Home", "metrica:Away"),
    excluded_player_keys={
        "metrica:Home": ("metrica:Home:11",),
        "metrica:Away": ("metrica:Away:25",),
    },
    events=normalized_events,
    config=config,
    output_dir="/tmp/moving_the_defense_match_application",
    render_selected=False,
)
```

One call scores both defending teams, splits support at cadence/roster/missing
coordinate boundaries, aligns supplied events, and exports score timelines plus
compact audit tables. Category discovery is retained as an audit facility, not
the default analyst workflow. The default
policy—trailing two-second window, six-second boundary guard, one-second
clustering adjacency, two clips per category, 2/5/10-second event windows,
fixed 6.25 m display ceiling—is recorded in `application_metadata.json`.

The public question-first boundary is `EventWindowQuery`:

```python
from defensive_reorganization_application import EventWindowQuery, query_event_windows

query = EventWindowQuery(
    defending_team_key="metrica:Home",
    attacking_team_key="metrica:Away",
    event_types=("SHOT", "GOAL"),
    pre_seconds=5.0,
    post_seconds=5.0,
    rank_by="maximum_score",
    limit=3,
)
result = query_event_windows(normalized_events, home_scores, query)
```

Queries may use event types and/or explicit `(period, time)` timestamps. Ranking
is limited to the existing anchor score, window maximum, post-minus-pre change,
or time to peak. The result includes pre/anchor/post values, local maximum,
time to peak, leading player contributors, support/suitability, deterministic
rank, and explicit no-result reasons. These are existing score summaries, not a
new estimator. A future dashboard can consume the table without changing the
measurement API.

The Metrica adapter enriches selected event windows with provider-recorded
outcome/subtype, deterministic score state, physical event location, safely
inferred attacking orientation, and the immediately preceding same-period
event with signed offset. The coach-facing card uses plain “within-unit
movement” and prominently says whether the maximum occurred before or after the
event. Exact metric values, contributor identities, traces, and diagnostics
remain in the analyst appendix. Missing context is labeled unavailable rather
than inferred.

Analyst cards report adjacent-event offsets and whether each event falls inside
the replay, shirt-number display labels, the safely inferred physical attacking
direction, a ball start-to-end arrow, and compact endpoint shape summaries.
Raw provider keys and physical-coordinate fields remain in audit metadata.

The Game 2 preset does not promote a low defensive-movement passage merely
because its score is small. A low-trailing-movement candidate must retain the
attacking possession proxy and pass at least two of four transparent on-ball
checks over the same ten-second review window: 15 m ball path, 10 m endpoint
change, 5 m directed progression, or two recorded attacking actions. Attacking
centroid and shape changes are reported as additional context but cannot make
an otherwise inert passage eligible. These thresholds organize analyst review;
they are not a validated attacking-activity metric.

The workflow fails rather than guessing if it does not receive exactly two
team keys, cannot form a stable ten-outfielder run, is asked to render without
an output directory, or lacks complete clip support. Goalkeeper exclusions are
provider-adapter knowledge and therefore remain explicit caller inputs.

Candidate selection alone is not permission to publish a clip. The public
Metrica runner adds provider-aware visual-suitability checks before rendering:
complete ball support, no dead-ball/restart overlap, no out-of-pitch player
coordinates, and no player speed above 15 m/s within the ten-second clip. These
checks remove obvious provider discontinuities and restart setups; they do not
validate tactical meaning. Other provider adapters must supply an equivalent
event/ball suitability layer rather than silently inheriting Metrica labels.

For public Metrica Sample Games 1 and 2, the preset resolves normalization,
team identities, goalkeepers, 25 Hz cadence, seven-frame smoothing, events,
ten-second analyst clips, context matching, and suitability gates from the game
number plus optional input/output paths. Automatic selection is the default;
the reviewed Game 2 case-study identities require an explicit option.

```python
from run_metrica_game2_application import analyze_metrica_sample_match

case = analyze_metrica_sample_match(
    1,
    data_dir="data/metrica_sample_game_1",
    output_dir="/tmp/mtd_game1_analyst_case",
    render_selected=True,
)
```

The lower-level normalized API remains the provider-neutral integration
boundary. A missing low-trailing-movement example is valid and does not relax the
activity gate.

The bounded public Game 2 application can be reproduced locally with:

```bash
.venv/bin/python src/run_metrica_game2_application.py \
  --game 2 \
  --reviewed-game2-case-study \
  --output-dir /tmp/moving_the_defense_game2_application \
  --render-selected
```

It scores maximal stable-roster runs for both teams, exports local Parquet
timelines, selects moments, and aligns every recorded shot. The command does
not publish its tracking-derived outputs.
Use `--game 1` without `--reviewed-game2-case-study` for automatic Game 1
selection.

Every run writes `event_window_review_summary.md` plus ranked event-window CSV
and JSON files. Rendered runs add sparse event-review cards, GIFs, and traces.
Metric traces, event details, player contributions, CSV, and Parquet outputs
remain analyst appendix material. `match_review_summary.md` and category cards
belong to the explicit discovery/audit mode. These artifacts support
deterministic passage retrieval for review, not tactical classification,
defensive quality, causation, success, or value.

## Meaning and limits

For each defender, the value is accumulated movement relative to the other
nine defenders over trailing `[t−2,t]`. The team value is the arithmetic mean
of all ten supported defenders. Both are expressed in metres.

The centered smoother requires future raw support relative to the displayed
frame, so this is a retrospective analyst tool—not a live detector. The API
does not measure defensive quality, tactical correctness, attacker influence,
marking responsibility, causation, or value.
