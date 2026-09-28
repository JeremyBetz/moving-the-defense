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
event. Exact metric values, changes, contributor identities, traces, and diagnostics
remain in the analyst appendix. Missing context is labeled unavailable rather
than inferred. Event-first GIFs use the same plain “within-unit movement”
language and hide the numeric team meter; the renderer's technical default and
the detailed analyst view remain unchanged. In the coach-facing replay, warmer
defenders are described as having moved more relative to their teammates.

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

## Pooled-reference full-match scanner

### Current analyst facade

For first use, prefer the compact facade over manually joining historical
research-stage modules:

```python
from match_reorganization_review import analyze_match_reorganization

review = analyze_match_reorganization(
    ball_alignment_episode_records,
    attacker_linked_episode_records,
)

review.rapid_episodes
review.integrity_clean
review.low_ballward
review.high_ballward
review.attacker_linked
review.representative_examples  # valid and integrity-clean only
review.diagnostic_examples      # valid special/context contrasts
review.rejected_examples        # failed support or integrity
```

The facade only composes frozen fields. It does not calculate a new score,
relax a gate or select by timestamp. Current timestamps are regression-test
expectations, never production selection rules.

```bash
.venv/bin/python src/run_match_reorganization_demo.py \
  --game 2 --data-root data \
  --output-dir /tmp/moving_the_defense_match_demo --no-media
```

The command validates closed package hashes and writes four separate CSV queues
plus a summary. Use `--render-media` to copy valid and diagnostic governed
media; rejected media are never copied as defaults. This fast path does not
rerun the historical pipelines. The commands below remain the full public-data
reproduction routes.

`src/defensive_reorganization_match_review.py` adds a separate opt-in application
layer without changing `discover_moments(...)` or the event-review dashboard.
Its `PooledScoreReference` stores sorted raw player, team, and one-second-change
reference arrays in memory. Player and team empirical percentiles are always
separate and use `searchsorted(..., side="right") / N`.

### First successful review

The CLI is the complete end-to-end reference workflow for the public Metrica
case study. Run it from the repository root after placing the public Sample
Games 1 and 2 files in the documented ignored data directories:

```bash
.venv/bin/python src/run_full_match_application_case_study.py \
  --output-dir /tmp/moving_the_defense_full_match_case_study
```

The Python API is the normalized-data integration interface. The complete
equivalent path is necessarily more explicit: normalize each provider file,
score the pooled reference population, analyze Game 2, align events, render one
selected window, and export local tables.

```python
from pathlib import Path

import pandas as pd

from defensive_reorganization_application import score_stable_runs
from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    align_events_to_reference,
    analyze_match_with_reference,
    build_pooled_reference,
    export_application_tables,
    render_reorganization_window,
)
from run_metrica_game2_application import (
    GOALKEEPERS,
    load_ball,
    load_normalized_team,
    load_shots,
    metrica_sample_preset,
)

population = {}
game2_tracking = {}
for game in (1, 2):
    preset = metrica_sample_preset(game)
    for team, filename in sorted(preset.team_files.items()):
        tracking = load_normalized_team(
            preset.data_dir / filename,
            team,
            match_id=preset.match_id,
        )
        population[f"game{game}:{team}"] = score_stable_runs(
            tracking,
            defending_team_key=team,
            source_fps=25.0,
            smoothing_frames=7,
            window_seconds=2.0,
            excluded_player_keys=(GOALKEEPERS[team],),
        )
        if game == 2:
            game2_tracking[team] = tracking

reference = build_pooled_reference(population, source_fps=25.0)
normalized_tracking = pd.concat(game2_tracking.values(), ignore_index=True)
analysis = analyze_match_with_reference(
    normalized_tracking,
    defending_team_keys=("metrica:Home", "metrica:Away"),
    reference=reference,
    smoothing_frames=7,
    excluded_player_keys={
        team: (GOALKEEPERS[team],) for team in game2_tracking
    },
    moment_spec=ReferenceMomentSpec(),
)
moments = analysis.selected_moments

preset = metrica_sample_preset(2)
shots = load_shots(preset.data_dir / preset.events_file, match_id=preset.match_id)
events = align_events_to_reference(
    shots,
    analysis,
    reference,
    defending_team_by_attacking_team={
        "metrica:Home": "metrica:Away",
        "metrica:Away": "metrica:Home",
    },
)

tracking_with_ball = pd.concat(
    [
        normalized_tracking,
        load_ball(
            preset.data_dir / preset.team_files["metrica:Home"],
            match_id=preset.match_id,
        ),
    ],
    ignore_index=True,
)
selected = moments.iloc[0]
render_reorganization_window(
    tracking_with_ball,
    analysis.scores_by_team[str(selected.team_key)],
    selected,
    Path("/tmp/mtd_first_review/media"),
    stem="selected_window",
    render_gif=False,
)
export_application_tables(
    analysis,
    Path("/tmp/mtd_first_review/tables"),
    formats=("csv",),
)
```

Those local tables can contain detailed player/time rows and must remain
untracked. Other providers enter at `normalized_tracking`; the scorer and
application layer do not accept raw provider objects.

```python
from defensive_reorganization_match_review import (
    ReferenceMomentSpec,
    analyze_match_with_reference,
    align_events_to_reference,
    build_pooled_reference,
    render_reorganization_window,
)

reference = build_pooled_reference(
    reference_scores_by_game_team,
    source_fps=25.0,
)
analysis = analyze_match_with_reference(
    normalized_tracking,
    defending_team_keys=("metrica:Home", "metrica:Away"),
    reference=reference,
    smoothing_frames=7,
    excluded_player_keys=goalkeepers,
    moment_spec=ReferenceMomentSpec(),
)
events = align_events_to_reference(
    normalized_shots,
    analysis,
    reference,
    defending_team_by_attacking_team=opponents,
)
```

The frozen case-study defaults use pooled team P95/P05 thresholds, pooled P95
for exact same-run one-second increases, one continuous second for high/low
episodes, two selections per category, and five seconds of complete rendering
context on each side. Category overlaps remain in the result.

### Possession-aware defensive review

`find_reorganization_windows(...)` remains the possession-agnostic raw scanner.
For Metrica events, the opt-in contextual layer reconstructs a conservative
native-frame state and applies the same frozen thresholds only after the scored
team has been continuously out of possession for two seconds:

```python
from possession_aware_defensive_review import (
    DefensiveReviewEligibilitySpec,
    build_metrica_possession_context,
    find_defensive_review_windows,
)

eligibility = DefensiveReviewEligibilitySpec(
    continuous_out_of_possession_seconds=2.0,
    transition_radius_seconds=2.0,
)
possession = build_metrica_possession_context(
    metrica_event_rows,
    normalized_tracking,
    match_id="metrica_sample_game_2",
    source_fps=25.0,
    spec=eligibility,
)
review = find_defensive_review_windows(
    analysis.scores_by_team,
    reference,
    possession,
    eligibility_spec=eligibility,
    historical_selected=analysis.selected_moments,
)
```

`review.moments` contains the high, low, and rapid passages that pass the
opponent-possession buffer; `review.selected_moments` contains the frozen
two-per-category review queue. `review.transition_moments` is a separate
descriptive view around direct event-derived possession changes, and
`review.historical_selection_audit` explains how an earlier ungated selection
is now classified. Ineligible frames split clusters; rapid changes require both
endpoints in the same eligible state run. No proximity or ball-location logic
fills ambiguous possession.

The native-frame possession table is detailed local working data and must remain
untracked. Its states are derived from Metrica events under the frozen rules;
they are not provider-ground-truth possession and do not alter the score.

Event alignment selects the nearest supported frame in the same period only
within half a native frame. It returns descriptive current, preceding 2/5/10
second, and exact one-/two-second change fields. Incomplete same-run windows are
missing rather than shortened or interpolated.

`export_application_tables(...)` can write local CSV/Parquet analyst tables.
`render_reorganization_window(...)` renders any supported selected interval
through the existing 0–6.25 m visualization without changing renderer defaults.
Detailed player/time exports are not public artifacts.

Reproduce the committed Game 2 application case study with:

```bash
.venv/bin/python src/run_possession_aware_defensive_review.py \
  --output-dir /tmp/moving_the_defense_possession_aware_review
```

Add `--no-media` for the faster state and selection check. The historical
ungated v1 command remains available as
`src/run_full_match_application_case_study.py`.

The reference percentile is descriptive calibration context—not DRS,
probability, prediction, quality, tactics, or value. See the
[case study](match_application_case_study.md) and its
[possession protocol](protocols/possession_aware_defensive_review_v1.md).

### Rapid-change-first review queue

For defensive review, the recommended question is when the unit's raw team
score rose much more strongly than one second earlier. This layer consumes the
existing possession-aware result and unchanged score packages:

```python
from rapid_change_defensive_review import (
    RapidReviewPrioritySpec,
    find_rapid_reorganization_windows,
)

rapid = find_rapid_reorganization_windows(
    review,
    analysis.scores_by_team,
    events=normalized_events,
    spec=RapidReviewPrioritySpec(),
)
queue = rapid.review_set       # frozen top-six audit
examples = rapid.public_examples
```

`queue` ranks the six largest eligible one-second increases. Both endpoints
must be in the same uninterrupted out-of-possession state run; ambiguous and
restart-adjacent passages fail closed. Context and anonymized contribution
patterns organize human review but do not explain cause or classify tactics.
`rapid.decrease_diagnostics` is a secondary local-only inspection table.
Sustained high/low outputs in `review` remain unchanged and serve
extreme-state inspection rather than the primary queue.

Run the complete public Game 2 workflow with:

```bash
.venv/bin/python src/run_rapid_change_defensive_review.py \
  --output-dir /tmp/moving_the_defense_rapid_change_review
```

The public package contains only its aggregate audit, timeline and
deterministically selected examples. All-six review media and decrease media
remain local. See the
[rapid-change protocol](protocols/rapid_change_first_defensive_review_v1.md).

### Trajectory integrity and ball alignment

The optional review layer in `src/ball_alignment_reorganization_review.py`
keeps the production score and rapid ordering unchanged. It first checks the
complete native-frame support for impossible movement and a narrowly defined
identity-swap signature. It then decomposes each defender-relative increment
against the contemporaneous player-to-ball direction.

```python
from ball_alignment_reorganization_review import (
    TrajectoryIntegritySpec,
    audit_native_trajectory_integrity,
    compute_ball_alignment_at_time,
)

spec = TrajectoryIntegritySpec()
integrity = audit_native_trajectory_integrity(
    defending_tracking,
    defending_scores,
    match_id=match_id,
    period=period,
    team_key=defending_team_key,
    peak_time_s=peak_time_s,
    spec=spec,
)
alignment = compute_ball_alignment_at_time(
    defending_tracking,
    ball_tracking,
    defending_scores,
    match_id=match_id,
    period=period,
    team_key=defending_team_key,
    time_s=peak_time_s,
    spec=spec,
)
```

`alignment.team_ballward_projection_share` is the positive projection toward
the ball divided by total defender-relative path; `team_signed_alignment`
retains toward-versus-away direction. Both are path-weighted team summaries.
They describe movement geometry and do not classify tactics, quality, cause,
effectiveness, or value. The frozen Games 1–2 review can be reproduced locally
with:

```bash
.venv/bin/python src/run_ball_alignment_reorganization_review.py \
  --output-dir /tmp/moving_the_defense_ball_alignment_review
```

The public package contains only the aggregate audit, comparison, and
deterministically selected low/high examples. Detailed candidate media and
decompositions remain local. See the
[frozen protocol](protocols/ball_alignment_reorganization_review_v1.md) and
[closed result](results/ball_alignment_reorganization_review_v1.md).

### Attacker-linked off-ball review

`src/attacker_linked_reorganization_review.py` adds a provider-neutral,
descriptive layer after the existing rapid, possession, trajectory-integrity
and ball-alignment gates. It accepts normalized attacker, defender and ball
tracking plus the already classified low-ballward episodes; provider loading
remains in `src/run_attacker_linked_reorganization_review.py`.

```python
from attacker_linked_reorganization_review import (
    AttackerLinkedReviewSpec,
    classify_episode_links,
    derive_reference_thresholds,
    rank_attacker_linked_episodes,
    summarize_off_ball_attackers,
    summarize_pair_geometry,
)

spec = AttackerLinkedReviewSpec()
attackers = summarize_off_ball_attackers(attacker_xy, ball_xy, attacker_keys, spec=spec)
pairs = summarize_pair_geometry(
    attacker_xy,
    defender_xy,
    attacker_keys,
    defender_keys,
    defender_relative_paths_m,
    attackers,
    spec=spec,
)
thresholds = derive_reference_thresholds(reference_attacker_paths, reference_pair_paths)
episode = classify_episode_links(attackers, pairs, thresholds, spec=spec)
ranked = rank_attacker_linked_episodes(episode_table)
```

The nearest attacker to the ball at each frame is treated as on ball; exact
ties use canonical key order. An attacker must be off ball for at least 41 of
51 smoothed frames. A strong link additionally requires an attacker path at or
above the frozen reference P75, a top-three defender contributor, and one of
the frozen distance, distance-change, or relative-vector-path conditions.
“Linked” therefore means concurrent geometric criteria only—not marking,
attacker influence, tactical effectiveness, space creation, or value.

Reproduce the aggregate-only public application package with:

```bash
.venv/bin/python src/run_attacker_linked_reorganization_review.py \
  --output-dir /tmp/moving_the_defense_attacker_linked_review
```

The runner freezes anonymous Games 1–2 reference thresholds before evaluating
Game 2, publishes only episode-local labels and compact aggregate artifacts,
and retains provider identities and detailed pair rows locally. See the
[protocol](protocols/attacker_linked_off_ball_reorganization_review_v1.md) and
[closed result](results/attacker_linked_off_ball_reorganization_review_v1.md).

Every run writes `event_window_review_summary.md` plus ranked event-window CSV
and JSON files. Rendered runs add sparse event-review cards, GIFs, and traces.
Metric traces, event details, player contributions, CSV, and Parquet outputs
remain analyst appendix material. `match_review_summary.md` and category cards
belong to the explicit discovery/audit mode. These artifacts support
deterministic passage retrieval for review, not tactical classification,
defensive quality, causation, success, or value.

## Local event-review product demo

`src/event_review_dashboard.py` is a thin, dependency-free browser layer over
`EventWindowQuery` and the Metrica match runner. It does not define a score or
own query logic. The default Event Review view lets an analyst choose Sample
Game 1 or 2, a defending perspective, shots/goals or event-derived possession
changes, bounded two-, three-, or five-second context, one of the existing rank
fields, and a result limit.

```bash
.venv/bin/python src/event_review_dashboard.py \
  --output-root /tmp/moving_the_defense_dashboard
```

The application prepares each match once but deliberately renders no media at
that stage. Preparation runs in the background with visible status and prevents
duplicate work. The browser immediately disables the preparation button and
shows an automatically refreshing progress panel; concurrent requests for the
same match do not start another preparation job. Later team, event, time-window, review-order, and result-count
choices reuse the prepared match. Opening a candidate renders only that passage.
Rendered passages can be retained and exported as a
portable ZIP containing a coach-facing HTML sequence, local media, and a compact
audit manifest.

The review table exposes factual event context. The selected football card and
GIF appear before a collapsed analyst appendix containing the exact trace and
technical diagnostic. If no complete, viewable passage matches the choices, the
dashboard says so without relaxing its rules. The local dashboard is intentionally
limited to event review. The separate command-line audit retains the existing
high/rapid/conditional-low checks. See
the [product-demo guide](event_review_product_demo.md) for the end-to-end user
journey and portfolio demonstration.

The possession-change option follows the repository's existing recorded-event
clock. PASS, RECOVERY, SET PIECE, and SHOT events update possession; only a team
change at PASS, RECOVERY, or SHOT becomes a review anchor. SET PIECE is excluded
as a restart anchor, while CHALLENGE and BALL LOST never infer possession on
their own. The selected defending perspective is labelled “Possession lost.”
This is an event-derived review boundary, not a claim about pressure, intent,
forced turnovers, or tactical success.

The server binds to `127.0.0.1` by default, fetches nothing externally, and
serves artifacts only from the configured output root. It adds no authentication,
telemetry, deployment, provider adapter, or tactical inference. Runtime output
remains local and untracked.

## Meaning and limits

For each defender, the value is accumulated movement relative to the other
nine defenders over trailing `[t−2,t]`. The team value is the arithmetic mean
of all ten supported defenders. Both are expressed in metres.

The centered smoother requires future raw support relative to the displayed
frame, so this is a retrospective analyst tool—not a live detector. The API
does not measure defensive quality, tactical correctness, attacker influence,
marking responsibility, causation, or value.
