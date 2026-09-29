# Project 1 demo human-usefulness review v1

**Review date:** 2026-09-28
**Starting HEAD:** `decfaa397261e718c72c24d8abfa79ff07a99cfb`
**Scope:** analyst-facing review only; no scientific or application behavior changed

## Review basis

The documented Game 2 demo completed successfully in both modes:

- no media: `/tmp/p1_demo_review_nomedia`;
- media: `/tmp/p1_demo_review_media`.

Both modes produced the same 25 rapid episodes, two representative examples,
two diagnostic examples and one rejected example. Their four CSV files were
byte-identical across modes. The media run copied ten governed files for the
four valid examples. Every static diagnostic and every complete GIF loop was
reviewed. The historical `1734.72 s` GIF was inspected only as a rejected-QC
reference; it is not copied into the current valid/diagnostic media package.

This review assumes a football analyst who understands tracking data but has
not followed the research history. The application remains a descriptive
review tool. It does not identify tactics, marking, cause, defensive quality,
success or player value.

## Overall finding

The demo can locate passages worth watching and can separate valid, special
context and rejected examples. Its current first-use surface does not yet make
all of that understanding immediate. The strongest gap is navigation: even in
the media run, every table row says `media_status=not_requested` and has empty
`static_path` and `gif_path` fields. The media exist, but the analyst must match
filenames and timestamps manually.

The example logic itself is credible. The two representative passages are
physically plausible and meaningfully different, while the diagnostics explain
why context and downstream checks matter. The remaining work is a bounded
presentation and information-hierarchy pass, not a new selection exercise.

## Representative example: Home P2 5355.64

**Rating: USABLE BUT AMBIGUOUS**

- **Physical plausibility:** Yes. Player motion is continuous and the passage
  has clean trajectory status, established defending context and complete ball
  and attacker-link support.
- **Visible reorganization:** Present, particularly in the warm defender
  markers and short trails, but not instantly legible as a *rapid increase*.
  The attacker-linked GIF covers only `t-2.00` to `t=0.00` and ends as the
  selected moment arrives. It provides no post-moment context or score trace.
- **Not simply ballward:** The reported ballward share is `0.168` and signed
  alignment is `-0.313`. The ball remains spatially separate from several
  visible defender movements, but the low-ballward interpretation still
  depends on the title/value rather than being unmistakable by eye.
- **Off-ball movement:** Meaningful attacker movement is visible through blue
  trails. The maximum eligible attacker path is `8.96 m`, although that value
  is available only in the table, not the media.
- **Links:** Two thin links provide a useful localized relationship without
  overwhelming the pitch. They remain descriptive geometric links, not marking
  assignments.
- **Relative value:** It is a better primary illustration than `4443.16 s`.
  The pitch is less congested, the two-link pattern is traceable, and it is not
  dominated by a goalkeeper-distribution reset.
- **Analyst comprehension:** With a one-sentence glossary and a compact context
  card, an analyst would understand why it was surfaced. The current GIF alone
  does not fully explain the trigger, reference percentile, defending context,
  or leading defender contributions.

The table identifies this as open play, continuously out of possession for
`5.36 s`, trajectory clean, low ballward, and localized attacker-linked. Its
reference percentile is only about `58%`, which is not contradictory: selection
is based on the one-second rise (`+0.79 m`), not on an extreme absolute level.
That distinction should be stated prominently in the analyst view.

## High-ballward contrast: Home P1 336.76

**Rating: USABLE**

- The passage is trajectory clean, in established defending context and
  classified as open play.
- It supplies a strong numerical contrast: team reorganization `6.46 m`,
  one-second increase `+1.42 m`, reference percentile above `99.9%`, ballward
  share `0.730`, and signed alignment `+0.687`.
- The ten-second GIF is much easier to orient within than the two-second
  attacker-linked clip. The selected moment is centered and the team meter and
  color scale make the rise visible.
- Movement toward the ball is plausible on inspection but not self-explanatory.
  The GIF shows the ball as a small white marker without a ball trail or an
  explicit direction cue. A new analyst is likely to understand the contrast
  from the diagnostic title and values rather than from motion alone.
- Together, `336.76 s` and `5355.64 s` communicate the intended point: two
  passages can both show rapid within-unit movement while differing strongly in
  their orientation relative to the ball. The pair is useful after a brief
  explanation, but not yet a self-teaching visual pair.

The row contains ball-alignment values but its
`ball_alignment_support_status` is blank. That is an output-contract problem,
not a scientific ambiguity: a visible value should be accompanied by the
explicit support state that authorized its interpretation.

## Special-context diagnostic: Home P2 4443.16

**Recommended role: advanced example**

This is a valid, trajectory-clean, low-ballward, distributed attacker-linked
passage. It is useful precisely because it demonstrates that a numerically
strong rapid episode can arise around a goalkeeper distribution and shape
reset. The current demo does not label that football context in the table,
title or GIF. An analyst could therefore mistake it for the primary intended
open-play phenomenon.

The attacker-linked view contains 12 strong-link lines in a congested defensive
third. Those lines dominate the graphic and make individual relationships hard
to follow. The separate ball-alignment diagnostic is more useful for inspecting
the score trajectory and context than the distributed-link GIF.

Keep the passage visible after the representative pair, with an explicit
`Goalkeeper distribution / shape reset` context label and a short explanation
of why it is diagnostically valuable. It should not be a default first example
or be presented without that qualifier.

## No-link diagnostic: Home P1 978.32

This is a useful method-QA contrast, but not a necessary default analyst
example. It is trajectory clean, low ballward, attacker-link supported, and has
zero strong links despite a `+0.89 m` one-second rise. It demonstrates that the
attacker-link layer does not automatically attach off-ball relationships to
every rapid passage.

The absence of link lines is visually clear. The reason the geometry fails the
frozen link criteria is not visible, however, and the current media does not
show the relevant thresholds. A normal analyst gains little from the clip
without that explanation. Retain it in a method-QA or “why no link?” section
rather than the main review queue.

## Rejected trajectory example: Home P1 1734.72

**Rating: NEEDS BETTER LABELING**

- It is correctly excluded from both representative and diagnostic queues and
  appears only in `rejected_examples.csv`.
- The table gives a clear machine reason:
  `trajectory_integrity_failed`, `impossible_native_speed`, with six impossible
  native-speed transitions.
- The historical GIF itself contains no rejection banner or failure marker. At
  normal playback the impossible movement is not reliably obvious to a new
  analyst; the clip looks like an ordinary valid replay unless the viewer
  already knows what to inspect.
- The current demo deliberately does not copy rejected media, so it does not yet
  teach the QC lesson visually. A future rejected-example view should be
  unmistakably separated from normal review and annotate the affected moment or
  trajectory. It must never become a valid/default render.

## Episode-table UX

The queue separation is the strongest part of the current contract. The 38-column
CSV is not yet an effective primary analyst table. It combines historical ranks,
duplicate attacker fields, internal support/QC fields and serialized lists. Some
rows contain valid ball-alignment values but a blank support status; media paths
remain blank after media copying; and leading defender contributions are absent
for `5355.64 s` even though they are one of the analyst questions the facade is
meant to answer. Blank values are therefore not consistently distinguishable
from unsupported or not evaluated.

Recommended first-view display labels are:

| Current/API concept | Analyst display label |
|---|---|
| `relational_reorganization_m` / `team_score_m` | Team reorganization — trailing 2 s (m) |
| `rapid_delta_m` / `one_second_change_m` | Increase from 1 s earlier (m) |
| `reference_percentile` | Games 1–2 reference percentile |
| `possession_state` | Possession context |
| `defensive_eligible` | Defensive-review eligible |
| `integrity_status` | Tracking integrity |
| `ballward_share` | Share of movement directed toward the ball |
| `signed_alignment` | Ball-alignment index (signed) |
| `ballward_stratum` | Movement orientation |
| `max_off_ball_path` | Longest eligible off-ball attacker path — trailing 2 s (m) |
| `strong_link_count` | Attacker–defender geometric links |
| `linkage_category` | Attacker-link pattern |
| `top_defender_contributors` | Leading defender-relative paths (m) |

The first-view table should contain only identity/time, selection class, raw
level, one-second increase, percentile, possession/eligibility, integrity,
ball orientation, attacker-link summary, leading defender paths, and a direct
media action. Historical ranks, raw component fields, threshold diagnostics and
serialized shares belong in an expandable analyst appendix. Every unavailable
field should display an explicit state such as `unsupported`, `not evaluated`,
or `not available`, never an unexplained blank.

## Media UX

What an analyst should notice first is the defender movement that increased
relative to the rest of the unit, followed by whether that movement follows the
ball and whether an off-ball attacker moves alongside it.

Current strengths:

- attacking and defending teams are readily distinguishable;
- the ball is generally visible as a white marker;
- defender color and the fixed metre scale make within-unit movement intensity
  visible;
- the ten-second ball-alignment replay centers the selected moment effectively;
- the localized two-link example is visually manageable;
- the scientific boundary is present in the standard replay footer.

Current weaknesses:

- the attacker-linked two-second GIFs end at the selected moment and loop
  abruptly, leaving no post-moment context;
- those GIFs have no period, match-clock timestamp, defending-team label,
  possession/integrity status, raw team level, percentile or score trace;
- attacker and defender labels are small, and the ball can be lost against
  white pitch markings;
- no ball trail or orientation cue makes “high ballward” visually self-evident;
- defender contribution is encoded indirectly by marker color, while the table
  does not consistently expose the same leading contributions;
- 12 simultaneous links at `4443.16 s` create substantial clutter;
- copied media are not linked from their queue rows and the two different
  `4443.16 s` diagnostics are not explained in the summary;
- rejected media lack rejection-specific visual grammar.

## Workflow friction

From a clone with data already available, the documented fast path requires
three conceptual actions: find the analyst-demo section, run one command, then
inspect four CSV queues plus `summary.json`. To answer “show me an interesting
defensive reorganization,” the user must then understand the queue roles,
decode technical columns, manually match a timestamp to a filename, and decide
which of duplicate-context media to open. The CLI help is concise and the
command is fast, but the output package does not explain itself as a navigable
review product.

The demo is therefore operationally easy to run but cognitively expensive to
use. A compact HTML/index page or equally direct table-to-media navigation would
remove most of the friction without changing any calculation.

## Analyst-value test

| Question | Answer | Reason |
|---|---|---|
| A. Find candidate moments for video review? | **YES** | The rapid queue is deterministic, fast to create, and separates representative, diagnostic and rejected passages. |
| B. Distinguish ball-oriented reorganization from structural movement elsewhere? | **PARTLY** | Frozen shares, signed alignment and strata support the distinction, but the visuals do not make it intuitive without explanation and support status is sometimes blank. |
| C. Identify co-occurring off-ball attacker movement? | **PARTLY** | Localized, distributed and no-link results are useful, but only on evaluated passages and the compact media omit thresholds and several context fields. |
| D. Prioritize passages for deeper tactical review? | **PARTLY** | The queues provide a defensible shortlist, but absent media links and an over-wide table slow first-use prioritization. Tactical interpretation still requires human video/context review. |
| E. Avoid mistaking the output for causal or tactical truth? | **YES** | The summary and media disclaimers are bounded, and the workflow reports geometry and support states rather than tactical conclusions. |

## Prioritized fixes

### P0 — correctness or misleading result

None found. The reviewed selections, score values and classifications agree
across both demo modes and with their closed source packages.

### P1 — blocks analyst understanding

1. Populate the actual media status and direct static/GIF paths in the media-run
   queues, or provide one generated review index. The current rows claim media
   was not requested even when it was copied.
2. Replace the 38-column first view with a compact analyst table and move
   implementation/history fields to an appendix.
3. Make every support state explicit. In particular, do not pair ball-alignment
   values with a blank `ball_alignment_support_status`, and do not leave missing
   contributor or attacker fields unexplained.
4. Label `4443.16 s` explicitly as a goalkeeper-distribution/shape-reset advanced
   diagnostic so it cannot be mistaken for the primary phenomenon.
5. If the rejected QC clip is exposed, add unmistakable rejection language and
   locate the integrity failure; otherwise keep it table-only. Never present the
   historical unlabelled GIF as a normal example.

### P2 — important UX improvement

1. Give the representative attacker-linked media enough pre/post context or a
   compact score trace to show why the selected instant is a rapid rise.
2. Add period, match clock, evaluated team, raw level, percentile, possession
   and integrity context consistently across selected media.
3. Explain the paired `5355.64`/`336.76` comparison in plain football language
   and add a restrained ball-orientation cue.
4. Reduce or stage the distributed-link overlay at `4443.16 s`; 12 lines are not
   individually readable.
5. Keep `978.32 s` as an optional method-QA contrast rather than a default normal
   analyst example.

### P3 — polish and deployment

1. Add a lightweight package landing page with queue counts, definitions and
   one-click media.
2. Use human-readable filenames or display titles while preserving governed
   source identities in metadata.
3. Provide playback controls or an MP4/WebM option for pausing and scrubbing;
   retain GIFs as portable previews.

## Decision

**READY FOR DEMO POLISH**

The core examples and workflow are useful. `5355.64 s` is a credible but not yet
self-explanatory representative, and `336.76 s` is a useful high-ballward
contrast. The main defects are information hierarchy, table-to-media navigation,
support-state presentation and clip annotation. They can be repaired without
changing the frozen metric, thresholds, context gates, or deterministic example
selection.

## Recommended next action

Run one bounded analyst-UX polish pass that creates a compact navigable review
index, fixes support/media-state presentation, and clarifies the existing five
examples without changing their selection or any scientific rule.
