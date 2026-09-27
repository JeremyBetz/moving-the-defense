# Event-review product demo

## Product proposition

The application helps an analyst move from a football event to a short list of
defensive passages worth watching:

> Prepare a match once, review event-linked candidates, curate a small number
> of passages, and hand a coach or analyst a portable clip pack.

The movement measure organizes attention. The analyst supplies football meaning.
The product never labels a tactic, intent, responsibility, quality, cause,
success, or player value.

## End product

The exported ZIP is the primary deliverable. After extraction it contains:

- `index.html`: a short coach-facing sequence of selected passages;
- `media/`: the corresponding context cards and tracking replays, plus the
  detailed analyst views;
- `manifest.json`: the selection order, passage identity, source package, and
  interpretation boundary.

The HTML can be opened locally without the application. It is deliberately
closer to a themed clip playlist or presentation than to a technical dashboard.
The manifest and detailed views preserve an analyst-facing audit trail.

## Workflow

1. **Frame the question.** Select the match, defending perspective, recorded
   football moment (shots, goals, or possession changes), time around the
   moment, and review order.
2. **Prepare the match once.** The application checks the tracking coverage,
   measures movement for both teams, and prepares the passages that can be
   reviewed reliably. No replay is rendered during preparation. A persistent
   preparation panel explains that the first run can take a few minutes,
   refreshes automatically, and disables repeated submission. A second request
   for the same match never starts duplicate preparation.
3. **Explore quickly.** Team, event, time-window, ordering, and result-count
   changes reuse the prepared match rather than measuring it again.
4. **Review quickly.** Reopening the same choices returns immediately. The queue
   supplies factual match context and says plainly when no passage qualifies.
5. **Render deliberately.** Only the passage opened by the analyst is rendered.
   Its media are saved for reuse; repeated viewing does not reprocess the match.
6. **Curate.** The analyst keeps only passages that support the intended human
   discussion. Software rank is review order, not an automated recommendation.
7. **Export.** Selected rendered passages become a portable review-pack ZIP.

## Run the demo

The public Metrica Sample Games 1 and 2 files must be present under the existing
ignored `data/metrica_sample_game_1/` and `data/metrica_sample_game_2/` paths.

```bash
.venv/bin/python src/event_review_dashboard.py \
  --output-root /tmp/moving_the_defense_dashboard
```

Open `http://127.0.0.1:8765`. For a concise portfolio demonstration:

1. prepare Game 1, both defending perspectives, and choose shots and goals or
   possession changes;
2. explain that the match is prepared once and later choices return quickly;
3. open the first candidate and render only that replay;
4. keep one or two rendered passages;
5. export the ZIP and open its `index.html`;
6. open the analyst appendix to show the trace and method boundary.

## What this demonstrates

### Football analysis

- starts from a recognizable football question rather than a numerical extreme;
- combines recorded event context, player movement, and human video review;
- separates coach-facing communication from analyst-facing technical detail;
- preserves valid no-results and avoids automatic tactical interpretation.

Possession changes are identified from the recorded event sequence, not from
the movement score. PASS, RECOVERY, SET PIECE, and SHOT events maintain the
event-derived possession clock; a team change at PASS, RECOVERY, or SHOT is a
review anchor. SET PIECE changes update that clock but are not anchors.
CHALLENGE and BALL LOST do not establish possession by themselves. The product
therefore uses “Possession lost” from the defending perspective and does not
claim a forced turnover, press win, or transition quality.

### Data and scientific practice

- deterministic scoring with explicit timing and units;
- fail-closed support, identity, cadence, and visual-suitability checks;
- unchanged scientific computation beneath the product layer;
- clear boundaries between descriptive geometry and causal/tactical claims.

### Product and software engineering

- expensive match preparation separated from interactive review;
- reusable cache, lazy media rendering, progress states, and duplicate-job locks;
- portable export rather than dependence on a running local server;
- path-confined artifact serving, synthetic tests, and dependency-light design.

## Deliberate limitations

This is a local portfolio prototype, not production club software. It has no
authentication, deployment, background worker, persistent user database,
broadcast-video integration, collaborative annotations, or coach feedback
study. GIFs stand in for rights-cleared match video. The usefulness of the
review workflow has not been validated with practitioners.

Those omissions are visible product decisions, not hidden capabilities.
