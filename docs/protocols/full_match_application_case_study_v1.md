# Full-Match Application Case Study v1

**Status:** frozen before event-aligned execution  
**Frozen:** 2026-09-27  
**Starting application commit:** `6a614cb561c202f389d40b3d047584a5cca946ec`

## Purpose and boundary

This protocol governs one descriptive analyst-workflow demonstration on public
Metrica Sample Game 2. It does not change or validate the underlying scientific
measurement. Raw trailing two-second defender-relative path in metres remains
authoritative. Reference percentiles are descriptive calibration context, not a
bounded score, probability, prediction, tactical assessment, or value measure.

The DRS experiment is outside this protocol and must not be imported or merged.
Metrica Sample Game 3, protected outcomes, manuscript claims, Candidate V1, and
the governed submission figures remain outside scope.

## Frozen reference population

The reference population is the already-authorized display-scale population:
both teams and both periods from public Metrica Sample Games 1 and 2, split into
the same 18 maximal regular-cadence runs with ten stable, finite outfield-player
identities. The provider cadence is 25 Hz. Scoring uses the unchanged centered
seven-frame smoother and trailing two-second accumulated leave-one-out
defender-relative path. The team score is the arithmetic mean of all ten
supported player scores.

Player and team reference distributions remain separate. For sorted reference
values, a reference percentile is
`searchsorted(reference, value, side="right") / N`. Reference arrays may exist
only in memory or ignored temporary storage; only aggregate summaries and
thresholds may be published.

## Frozen case-study match and event taxonomy

The case-study match is Metrica Sample Game 2. It was selected for public-data
completeness and existing application support, not because it is an untouched
scientific holdout. If its event/tracking synchronization fails the frozen
checks, execution stops rather than substituting another match.

The event taxonomy is limited to shots, goals, and shots on target. A shot is on
target only when its normalized Metrica subtype contains `GOAL`, `ON TARGET`, or
`SAVED`. `BLOCK` and `OFF TARGET` do not qualify. If the source cannot support
this rule consistently, the execution is invalid.

## Frozen moment rules

- **High:** supported Game 2 team frames at or above the pooled reference-team
  P95. An episode must remain qualifying for at least 1.00 continuous second.
- **Low:** supported Game 2 team frames at or below the pooled reference-team
  P05. An episode must remain qualifying for at least 1.00 continuous second.
- **Rapid increase:** the current team score minus the exact score one second
  earlier within the same stable run. Candidates must be at or above the pooled
  P95 of all finite one-second changes in the reference population.

Qualifying native frames cluster only when consecutive at the 25 Hz cadence and
within the same match, team, period, and stable run. High episodes rank by raw
peak score, low episodes by raw minimum score, and rapid episodes by largest
positive one-second change. Ties resolve by lexical match/team, period, then
earliest time.

Select at most two episodes per category. Cross-category overlap is preserved
and recorded rather than replaced. Public media selection additionally requires
complete five-second pre/post rendering support inside the same stable run. If
fewer than two episodes qualify, publish fewer; never relax a rule.

## Event alignment and context

An event matches the nearest supported native frame in the same period only
when the absolute difference is at most half a 25 Hz frame, plus `1e-7` seconds
of numerical tolerance. Equal-distance ties select the earlier frame. Other
events remain unmatched.

For a matched event, report the current raw team score and team reference
percentile. For complete preceding 2, 5, and 10 second windows, report mean raw
score, maximum raw score, and the maximum reference percentile. Report exact
one- and two-second changes only when those native frames exist in the same
stable run. Missing support remains missing; there is no interpolation or future
leakage.

## Publication and interpretation

The public case study may contain compact aggregate distributions, episode
summaries, an event table, one timeline, six deterministic static diagnostic
slots, and at most three unique GIFs representing the top high, low, and rapid
episodes. If categories select the same interval, reuse the artifact and retain
all category labels.

Do not publish raw tracking, player-time score tables, coordinates, detailed
eligibility ledgers, or provider-linked exports. Local CSV/Parquet exports remain
ignored analyst artifacts.

Allowed interpretation is retrospective observable geometry: defenders moved
more or less relative to the other nine defenders, the team mean rose or fell,
and an event occurred before, during, or after a passage. This protocol does not
establish causation, prediction, defensive quality, tactical intent, marking,
space creation, player value, or event effectiveness.
