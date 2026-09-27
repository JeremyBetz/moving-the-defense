# Case study: event-first defensive-unit review

## The analyst question

**What defensive reorganization happened around shots and goals?**

The workflow starts with recorded football events, not metric extremes. For
each supported shot or goal, it opens a fixed ten-second window, summarizes the
existing trailing two-second defender-relative score before, at, and after the
event, and ranks windows by their local maximum. The ranked result is a review
queue—not a claim that the movement caused the event or identifies a tactic.

## Deterministic public examples

The same predeclared query was run without manual swapping on public Metrica
Sample Games 1 and 2. It required complete score support, complete ball support,
and the existing visual-suitability checks. Game 1 returned two review windows:

1. Away shot at period 1, 778.80 s (12:59), Home defending: local maximum
   5.16 m at 0.68 s after the shot; post-minus-pre change −0.65 m.
2. Away shot at period 2, 3010.48 s (50:10), Home defending: local maximum
   4.61 m at 1.08 s before the shot; post-minus-pre change +0.93 m.

Game 2 returned one suitable review window:

1. Home shot at period 1, 2243.16 s (37:23), Away defending: local maximum
   3.45 m at 3.32 s before the shot; post-minus-pre change −0.80 m.

These values describe mean trailing movement within the defending unit. They do
not grade the defence, explain the shot, or imply that larger values are better.
Fewer returned windows is a valid result of the frozen support/suitability gates.
Together, the examples form three timing profiles: a peak just after a shot, a
peak immediately before a shot, and a peak earlier in the attacking sequence.
That contrast is why signed time-to-peak is displayed rather than describing
every window as a defensive reaction.

## How the review proceeds

The ranked CSV/JSON table answers where to look first. Each selected window then
receives a ten-second GIF, sparse event-review card, and analyst trace. The card
shows the event outcome, score state, physical location and orientation,
preceding event, rank basis, and signed peak timing. It also contains the
explicitly human question:

> Which defenders changed position most around the shot, and was the unit still
> reorganizing afterward?

An analyst next opens the original match video, records relevant context, and
writes any coaching question in their own words. The software does not label
counter-pressing, defensive intent, quality, tactical success, or player value.
The detailed trace, event context, player contributions, CSV, and Parquet files
remain an analyst appendix rather than coach-facing output.

Metrica possession context is only a last-recorded-event proxy, not a true
provider possession state. Transition-like event anchors can narrow review
candidates, but cannot classify counter-pressing or other tactical intent.

## Minimal use

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
ranked_windows = result.windows
```

The public Metrica runner performs normalization, scoring, suitability checks,
ranking, export, and optional rendering:

```bash
.venv/bin/python src/run_metrica_game2_application.py \
  --game 2 \
  --output-dir /tmp/mtd_game2_event_review \
  --render-selected
```

## Audit and metric demonstration

High movement, rapid increase, and low trailing movement under an attacking-
activity gate remain useful for validating and demonstrating the score's
extremes. They are not the default analyst workflow. To render those examples,
use the explicit `--discovery-audit` option. The reviewed Game 2 audit retains
its fixed 14:05 high, 5:36 rapid-increase, and 83:59 low-under-activity passages.
Any counter-pressing interpretation remains a human review hypothesis, not an
automated category.

## Interpretation boundary

The score is accumulated movement relative to the other nine defenders over
trailing `[t−2,t]`, using the committed retrospective smoother. Event windows
do not create a new estimator. This workflow can support deterministic passage
retrieval and review. It does not establish marking, causation, tactics,
defensive quality, success, effectiveness, or value.
