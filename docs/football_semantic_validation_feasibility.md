# Football-semantic validation feasibility

**Status:** design feasibility only; no protocol is frozen and no empirical
passage has been selected.

**Purpose:** test whether passages ordered by the project's closed geometric
measurement correspond to distinctions that independent football practitioners
can recognize and describe. This is semantic/practitioner validation of an
observable tracking construct. It is not a test of attacking value, causal
influence, tactical success, player quality, gravity, marking assignment, or
whether agreement makes the metric “correct.”

## Recommendation

Use a blinded, fully crossed paired-comparison study with **five independent
football practitioners reviewing 15 matched pairs (30 unique passages)**. Each
pair should contain one passage with higher and one with lower observed
localized defensive reorganization, selected deterministically from the closed
Metrica Games 1–2 measurement registry after matching on attacker movement and
starting geometry. Reviewers see standardized tracking animations only, with no
metric values, proximity ranks, centroid, arrows, hypotheses, or high/low
labels.

The primary question asks which passage shows more local defensive adjustment
relative to the rest of the defensive unit. A single secondary question asks
whether each passage would be worth flagging for tactical/video review. This
design tests recognizable ordering and prospective analyst usefulness while
keeping football interpretation separate from value.

This is feasible as a small pilot, not a definitive validation sample. It should
advance only after a written institutional human-subjects/ethics determination
and a passage-construction protocol are complete.

## Why paired comparison

A five-point absolute scale asks different reviewers to calibrate “a lot” in
the same way. A matched pair instead asks for a direct visual distinction while
holding major geometric alternatives approximately constant. It is therefore
the cleaner primary design.

The alternative monotonic-rating design is useful only as a secondary
sensitivity: it is more vulnerable to reviewer-specific scale use, requires a
larger sample, and makes the small reviewer pool more consequential. Absolute
ratings should not replace the primary paired judgment.

## Ethics and human-subjects action

The planned activity asks living people to provide judgments for research and
publication through direct interaction. Under the Common Rule definition,
interaction for research can make reviewers human subjects even when the task
is minimal risk and the investigator is a student. The likely route may be an
exempt survey/interview determination, but that is an institutional
determination—not an assumption the project should make independently.

**Required action before recruitment or pilot ratings:**

1. Send the university Human Research Protection Program/IRB a written
   determination request describing this as an independent student project
   intended for publication.
2. Include the exact animations, reviewer instructions, questions, recruitment
   text, consent language, compensation if any, minimal metadata, storage plan,
   and planned public reporting.
3. Obtain written confirmation of one of: not-human-subjects research, exempt
   human-subjects research, or approval under the institution's required review
   route.
4. If the university declines jurisdiction because the project is independent,
   retain that written decision and ask what external ethics review or
   publication-facing documentation is appropriate. Do not treat
   non-jurisdiction as self-issued exemption.
5. Collect no ratings until the determination and any required consent process
   are complete.

This recommendation follows the U.S. Office for Human Research Protections'
[human-subject definition](https://www.hhs.gov/ohrp/education-and-outreach/online-education/human-research-protection-training/lesson-2-what-is-human-subjects-research/index.html),
its recommendation against unsupported investigator-only
[exemption determinations](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/faq/exempt-research-determination/index.html),
and its [informed-consent guidance](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/informed-consent/index.html).
Institutional and local rules may be stricter.

Collect only:

- pseudonymous reviewer ID;
- primary role: coach, analyst, player, or other practitioner;
- football-experience band: 3–5, 6–10, or more than 10 years;
- analysis-experience band;
- broad voluntary coaching-licence band; and
- prior familiarity with tracking animations: none, some, or frequent.

Do not publish names, employers, clubs, exact licence identifiers, contact
details, free-text biographies, or combinations that make a reviewer readily
identifiable. Keep recruitment/consent records separate from coded ratings.
Quotes require separate explicit consent and are not part of the recommended
primary study.

## Reviewer population

Recruit five adults who are independent of the project and have not seen its
metric categories or hypotheses. Each should meet at least one predeclared
expertise route:

- at least three years in a football coaching or analysis role;
- a recognized intermediate-or-higher coaching qualification plus current
  practical involvement; or
- at least five years of tactically engaged playing/coaching experience with
  demonstrated video-analysis familiarity.

Aim for more than one role type and avoid taking all reviewers from one club or
shared staff. Expertise rules establish a relevant judgment population; they do
not imply that one tactical interpretation is objectively correct.

Five reviewers provide an odd-number majority, permit fully crossed agreement
assessment, and keep the task recruitable. Three would make agreement unstable
and a single dissent decisive. More than five would improve precision but is
unlikely to be the highest-value use of pre-Sloan time.

## Dataset and viewing format

### Recommended data source: Metrica Sample Games 1–2

Use the two already-closed Metrica matches because:

- the temporal localized-reorganization measurement is closed for both;
- the sample tracking is public and reproducible;
- pitch animations can be shared without exposing restricted IDSSE derivatives;
- Game 2 supplies a genuine heldout source; and
- no synchronized match video is required.

Do not use Metrica Game 3. Do not use DRD residuals. Do not use SkillCorner
response-mode outcomes. IDSSE would offer more matches but creates access and
redistribution constraints. SkillCorner is valuable external evidence for the
movement-direction result, but it is not needed to test the basic semantic
ordering and broadcast-derived animations may add tracking-support differences.

Use **one standardized tracking-animation format**, not video plus overlays.
Broadcast video introduces editorial camera choices, licensing, and unavailable
synchronization across the main datasets. Tracking-only animation tests whether
the geometry itself is football-readable.

### Animation standard

Each animation should:

- show a neutral pitch and all fully supported players plus the ball;
- use stable anonymous team colors and no team, match, score, or clock identity;
- highlight the focal attacker with a neutral ring;
- show attacking direction with a fixed pitch-edge arrow;
- use native standardized pitch coordinates and real-time playback;
- show no defender ranks, centroid, relationship lines, metric values, path
  values, high/low labels, or model categories; and
- use identical size, colors, frame rate, trail policy, and encoding.

A short focal-attacker trail should be omitted in the primary presentation
because it selectively emphasizes the exposure. If later judged necessary for
basic orientation, that decision must be made before pair construction and
applied identically to all passages.

## Passage duration and presentation

Use a **six-second window from anchor −3 s to anchor +3 s**:

- −3 to −2 s: one second of football context;
- −2 to 0 s: the closed attacker-movement interval;
- 0 to +2 s: the closed subsequent defender interval; and
- +2 to +3 s: one second of follow-through.

Play each passage twice automatically at 1× speed, separated by a 0.5-second
neutral screen. Show Passage A and Passage B sequentially, not simultaneously.
Randomize pair order and A/B assignment independently for each reviewer with a
saved seed. Do not identify the anchor transition on screen.

This window gives shape context while limiting downstream play. Fifteen pairs
produce about six minutes of raw first-pass footage and roughly 20–25 minutes
including replay, questions, instructions, and breaks.

## Prospective passage construction

No passage may be chosen by visual appeal. Passage construction should use only
the closed Metrica measurement registry, predeclared matching variables, and
support/QC fields. The future protocol should define the following before any
animation is viewed.

### Passage-level measurement

For each eligible anchor, define observed localized defensive reorganization as
the mean closed defender-relative path for D1–D3 minus the mean for D4–D7 over
the established subsequent interval. This is a direct passage-level description
of the closed geometric outcome—not a DRD residual, model prediction, tactical
label, or causal effect.

### Candidate pools

Within each match-period and broad attacker-movement-direction stratum, create:

- a high pool from the upper quartile of the passage-level measure; and
- a low pool from the lower quartile.

Quartiles are deterministic diagnostic strata, not claims that the construct has
a natural high/low threshold. If the final protocol uses different quantiles,
that choice must be justified and frozen before passage identities or animations
are inspected.

### Matching hierarchy

Match one high passage to one low passage using this order:

1. exact match and period;
2. exact broad movement-direction stratum;
3. similar attacker path magnitude;
4. similar attacker–ball distance at movement start;
5. similar attacker goalward position relative to the defensive unit;
6. same attacking side where feasible; and
7. maximum separation in the closed passage-level measurement only after
   matching quality is satisfied.

The protocol must predeclare scaling, calipers, optimization/tie-breaking, and
what happens when fewer than 15 valid pairs exist. No passage may be swapped
after viewing. A preferable deterministic implementation is optimal
minimum-distance matching on robustly standardized matching variables, followed
by a fixed outcome-separation priority and stable observation-ID tie-break.

Additional independence rules should require:

- 30 unique passages and unique anchor times;
- no overlapping six-second windows;
- no two passages from the same pair sharing a defensive state;
- a predeclared cap on passages per focal attacker; and
- approximate allocation across Games 1 and 2, subject to valid matching.

The proposed 2×2 outward/goalward-by-high/low presentation is not recommended as
the primary design. Exact or close direction matching within pairs already
separates movement direction from the measured response and preserves more
matching flexibility. Direction can be balanced descriptively across pairs.

### Outcome-blind visual QC

Visual QC must be rules-based and performed without metric category visible.
Before selection, require continuous focal-attacker, defending-outfield, ball,
period, and timing support across the six-second window. Decide prospectively
whether complete 22-player support is mandatory or whether all supported
players are displayed. Reject only objective faults such as missing required
objects, identity discontinuity, impossible coordinate jumps under a separately
frozen tracking-QC rule, or render failure.

Keep an exclusion ledger. If a selected passage fails, replace it only by the
next deterministic match from the original algorithm; never hand-pick a cleaner
clip.

## Blinding and neutral instructions

Reviewers must not see metric values, high/low status, coefficients, model
predictions, hypotheses, or the outward/goalward result. File names and passage
IDs must not encode condition. The person administering ratings should use a
fixed script and, where practical, remain blind to pair order.

### Draft reviewer instruction

> You will review pairs of short football tracking animations. One attacking
> player is highlighted to help you follow the same type of passage in each
> clip. Focus only on movement you can see, especially whether defenders near
> that attacker change position relative to the rest of the defensive unit.
> There is no requested tactical explanation and no judgment of whether the
> movement was good, successful, or caused by the highlighted player. For each
> pair, choose the passage that shows more local defensive adjustment. If the
> distinction is difficult, still make the closer choice and record low
> confidence. You will also rate whether each passage would be worth flagging
> for later tactical/video review.

After all ratings are locked, provide a short debrief explaining the high/low
construction, the study hypothesis, and the limits of interpretation.

## Questions and rating format

### Primary semantic-validity question

> Which passage shows more change in the positions of defenders near the
> highlighted attacker relative to the rest of the defensive unit?

Response: forced choice **A** or **B**, followed by confidence
**low / medium / high**. Confidence is descriptive and nonclassifying. A forced
choice supports a clean chance reference; low confidence preserves ambiguity
without turning “unclear” into an unplanned third outcome.

### Secondary application question

For each passage separately:

> How useful would it be to flag this passage for later tactical/video review of
> the highlighted off-ball movement?

Response: **1 (not useful to flag) to 5 (very useful to flag)**. This tests
workflow relevance, not attacking quality or value. Its status cannot rescue a
failed primary semantic result.

Optional noninferential descriptors—“mainly collective shift,” “mainly local
change,” “both,” or “unclear”—may help explain disagreements, but should not
become additional confirmatory outcomes.

## Analysis and agreement

### Primary estimand

For each pair, determine whether a majority of reviewers selected the passage
with higher closed measured reorganization. The primary estimand is the
proportion of pairs for which that majority selected the higher passage.

With 15 independent pair units, 12 or more higher-passage majorities are needed
for a one-sided exact binomial probability below 0.05 against 50% (12/15 gives
0.0176). This small design has limited sensitivity: under a true pair-level
majority probability of 0.75, the probability of reaching 12/15 is about 46%;
at 0.80 it is about 65%. A null result would therefore constrain semantic
validity but would not prove the geometry is meaningless.

Report:

- pair-majority proportion and exact two-sided 95% interval;
- one-sided exact test against 0.50;
- each reviewer's accuracy descriptively;
- unanimous and 4/5 pair agreement; and
- a predeclared crossed reviewer/pair sensitivity, such as a logistic mixed
  model with random intercepts for reviewer and pair, only if estimable.

The pair—not each reviewer-passage response—is the primary inferential unit.
Do not treat 75 judgments as independent.

### Agreement

Use nominal **Krippendorff's alpha** on canonical passage choices within each
pair, with a pair-resampling interval, plus raw agreement. Alpha handles
multiple reviewers and missing ratings. The interpretation convention should be
predeclared:

- **adequate:** alpha at least 0.800;
- **mixed/tentative:** 0.667 to below 0.800;
- **inadequate:** below 0.667.

These are conventional reliability guidance, not laws of football semantics.
See the University of Pennsylvania
[Krippendorff alpha resources](https://www.asc.upenn.edu/krippendorffs-alpha-reliability).
Low agreement may reveal genuine ambiguity rather than reviewer failure.

### Primary semantic classification

The exact rules below are recommended but **not frozen** pending ethics review
and a dry review of the rating instrument without empirical passages.

- **SUPPORTED:** execution valid; at least 12/15 pair majorities select the
  higher-measured passage; exact one-sided p < 0.05; alpha at least 0.800; and
  at least 4/5 reviewers individually select the higher passage in more than
  half of pairs.
- **MIXED:** execution valid and the overall direction favors the
  higher-measured passage, but one or more precision, agreement, or
  reviewer-consistency conditions for SUPPORTED fail.
- **NOT SUPPORTED:** execution valid, the pair-majority proportion is at or
  below 0.50, or there is no reproducible direction across reviewers.
- **INVALID:** required ethics/consent conditions were not satisfied; fewer than
  four eligible reviewers or fewer than 12 valid pairs completed; required
  blinding failed; more than 10% of primary judgments are missing; or a
  predeclared animation/support QC failure prevents interpretation.

Do not tune the measurement, matching, thresholds, or display after ratings.

### Secondary application classification

Analyze the 1–5 flagging rating with an ordinal mixed model containing the
predeclared high-versus-low passage indicator and random intercepts for reviewer
and pair, if estimable. Otherwise report paired reviewer differences with a
two-way reviewer/pair bootstrap.

- **SUPPORTED:** positive high-versus-low association with interval above zero
  and the same direction for at least 4/5 reviewers.
- **MIXED:** positive estimate but incomplete interval or reviewer consistency.
- **NOT SUPPORTED:** no positive association.
- **INVALID:** the study itself is invalid or the model is not estimable.

This application status is separate and subordinate to semantic validity.

## Sample-size and burden assessment

The recommended 30 passages/15 pairs and five reviewers are the largest design
within the suggested range while remaining practical. It supplies 75 binary
judgments but only 15 primary pair units. It can detect a strong, coherent
semantic distinction; it is underpowered for a modest one. Its chief scientific
value is a prospectively controlled feasibility result with honest
uncertainty—not a population-wide estimate of expert consensus.

A 20-passage/10-pair design would require 9/10 correct pair majorities for a
one-sided exact result below 0.05 and would have only about 24% probability of
doing so when the true pair-level majority probability is 0.75. It is too
fragile for the primary plan. Three reviewers also provide too little
reliability information. Five reviewers and 15 pairs are therefore recommended.

## Pre-Sloan feasibility

As of early September 2026, completion before October 1 is **conditional and
not reliably schedulable**:

- materials and a nonempirical implementation plan: approximately 3–5 working
  days;
- institutional determination: potentially several days to several weeks;
- recruitment and five complete reviews: approximately 5–10 working days after
  approval;
- locked analysis, QC, and write-up: approximately 2–4 working days.

Proceed before Sloan only if the written ethics determination arrives promptly,
the required materials are approved without major revision, and five reviewers
can be scheduled without compromising independence. Do not bypass review to
meet the deadline. The current geometric paper remains coherent without this
study.

## Fallback: structured practitioner case review

If formal multi-reviewer validation cannot be completed, use a clearly labeled
**structured practitioner case review**:

- one or two independent football experts;
- deterministic, outcome-blind passage selection under the same matching and
  display rules;
- the same neutral observable-geometry prompts;
- a structured summary of agreements, disagreements, and football descriptions;
- no inferential test, agreement coefficient, semantic-validity status, or
  claim that the metric was validated.

This still requires the institution to determine the applicable ethics and
consent route if judgments will be collected and published. Its permitted claim
is only that deterministic examples show how the measurement can structure
expert review.

## Expected value

### Scientific value

A SUPPORTED formal study would add passage-level semantic evidence: the closed
geometric ordering corresponds to independent expert judgments of local
defensive adjustment. MIXED or NOT SUPPORTED would be equally informative,
showing that geometric replication does not automatically produce shared
football semantics. No outcome would establish mechanism, causation, tactics,
or value.

### Sloan application value

- **Formal blinded study:** material upgrade. It directly answers the likely
  reviewer question, “Can football practitioners see the distinction?”
- **Structured case review:** modest communication upgrade. It demonstrates an
  analyst workflow but is not validation.
- **No semantic study:** acceptable. The submission remains a rigorous
  measurement-and-replication paper with semantic validation named as future
  work.

### Expected Codex cost

- feasibility/protocol drafting after ethics direction: low;
- deterministic matching and blinded animation generator: medium;
- rating-form export, randomization manifest, and QC: low to medium;
- analysis and reproducibility package after ratings: medium;
- human recruitment, consent, scheduling, and institutional review: outside
  Codex and likely the dominant calendar cost.

## Freeze decision

**No protocol or configuration is frozen in this pass.**

The scientific design is sufficiently clear to recommend, but the ethics path
has not been determined by the relevant institution, complete-animation support
has not been checked without selecting passages, and exact matching/caliper
rules have not undergone prospective feasibility review. Freezing now would
either guess at institutional requirements or risk an infeasible pair
construction.

The next authorized action should be an ethics/determination package and a
strictly outcome-blind implementation-feasibility check of support and matching
capacity. Neither should inspect animations or passage identities. Only after
those gates pass should a versioned protocol/configuration be frozen.

## Pass firewall

This feasibility design:

- selected no empirical passage;
- inspected no high/low passage identity or animation;
- collected no reviewer rating;
- computed no new scientific result;
- did not inspect DRD residuals;
- did not inspect SkillCorner response-mode outcomes; and
- did not inspect Metrica Game 3.
