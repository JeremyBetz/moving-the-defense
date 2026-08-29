# Phase 3A Prospective Matched-Contrast Validation Protocol

## Frozen status

Protocol version **1.0**, random seed **20260828**. Design only; no validation outcomes inspected. The JSON configuration is the executable source of truth.

> Defensive relational reconfiguration is a coherent, temporally localized change in prospectively specified typed defensive geometric relationships that is not adequately described by the relevant pre-specified baseline motion alone.

The target is internal geometric discrimination, not tactical truth, semantic validity, attacker value, responsibility, or causality.

## Candidates and overlap

Primary anchors are open-play `PASS` events with nonmissing `To`; valid `End Frame`/`End Time` defines the reception anchor because Metrica has no separate completion flag. A tracked ball is required at that anchor. For the five-second window $[-2,+3]$, sort anchors chronologically, retain the earliest, suppress every later anchor whose window overlaps it, and resume after its end. Rebuild eligibility independently for the eight-second $[-3,+5]$ sensitivity. Tackle sensitivity uses event `Start Time` and an unambiguous event defender. Possession-change sensitivity uses the `Start Time` of the first possession-bearing event whose team differs from the preceding possession-bearing event in the same period, excluding restarts. Both reuse all frozen windows, spacing, controls, outputs, and statistics; tackles are not primary because they mechanically enrich convergence.

No window crosses a period boundary. Candidate focal selection is symmetric with controls: the defending outfield player nearest the tracked ball at the anchor. Receiver identity establishes eligibility/context only. Missing anchor ball means exclusion. Tackle sensitivity uses an unambiguous event-identified defender or excludes the event.

## Possession, restarts, and pseudo-anchors

Candidate possession is the PASS `Team`. At pseudo-anchor times, possession is the team from the most recent event at or before the anchor whose `Type` is `PASS`, `RECOVERY`, `SET PIECE`, or `SHOT`, propagated only within the period. Player proximity never determines possession.

Restart exclusions use literal event vocabulary: any `SET PIECE` or `BALL OUT`, plus subtypes `CORNER KICK`, `FREE KICK`, `GOAL KICK`, `KICK OFF`, `THROW IN`, `OFFSIDE`, and `END HALF`.

Control pseudo-anchors use every integer elapsed-match second represented in tracking; there is no random subsample. Eligibility requires open play, possession, a full same-period window, anchor ball, core references, absolute separation of at least 5.0 seconds from every eligible reception and restart, and no overlap with any retained candidate. Match candidates chronologically. After selecting a control, remove every pseudo-anchor whose window overlaps that control. Candidate/control and control/control overlap are forbidden. Reconstruct the pool for the eight-second sensitivity.

## Matching

Hierarchy: same period; possession team; open-play status; fixed 3×3 anchor ball zone; available defending-outfield count; elapsed-time difference no more than 300 seconds; smallest absolute time difference; earlier pseudo-anchor on exact tie; without replacement. Earlier candidates receive first access, a deterministic choice that may reduce later support.

Primary support is adequate only if at least 70% of retained candidates match. Below 70%, label the primary design poorly supported and do not loosen anything. The sensitivity additionally exact-matches fixed pre-anchor one-second movement bins: ball displacement `<2`, `2–5`, `>5` m; centroid displacement `<1`, `1–2.5`, `>2.5` m.

## Fixed identities and descriptors

At window start, `neighbor_1` and `neighbor_2` are the nearest and second-nearest teammates to focal; `opponent_1` and `opponent_2` are the nearest and second-nearest opponents. Identities never change. Local pairs are `focal_neighbor_1`, `focal_neighbor_2`, and `neighbor_1_neighbor_2`.

For x/y ordering reversal, compare signs of every trio pairwise coordinate difference at start and end. The indicator is one if any non-tied pair reverses sign. Absolute differences below $10^{-9}$ working units are ties; intermediate crossings are ignored.

Six Holm families are frozen:

- **Collective:** centroid x/y displacement, centroid path, directional coherence.
- **Focal:** leave-one-out-relative x/y change and path.
- **Local configuration:** three named pair changes, x/y spans, area, x/y reversal, and each fixed member’s centroid-relative x/y change.
- **Opponent relational:** opponent1/2 relative x/y and distance changes.
- **Ball/context:** ball displacement and focal-ball x/y.
- **Generic activity:** sum of defending-outfield physical path lengths.

Directional coherence is the magnitude of the mean normalized net-displacement vector of defending outfield players. Net displacement at or below $10^{-9}$ is omitted and the omitted count reported.

## Missingness

Core eligibility requires anchor ball; focal and two teammates/opponents; complete focal/local/opponent coordinates; and complete defending-outfield coordinates needed for the leave-one-out centroid throughout the window. Resolve before matching. No interpolation or imputation. Ball-family analysis uses only matched pairs with complete ball tracks in both windows and reports its own pair count; incomplete later ball data does not discard a pair from other families.

## Statistics and negative control

Report raw effects and 95% intervals primarily. Use 10,000 paired bootstrap resamples with replacement and deterministic child seeds from 20260828. Report median paired difference and $d_z=\bar d/s_d$; if $s_d=0$, $d_z$ is undefined. Continuous descriptors use two-sided exact sign flips when practical, otherwise 100,000 Monte Carlo draws. Binary reversals use an exact matched discordant-pair McNemar/binomial test. Holm correction is within each family only; no descriptor is dropped.

For each retained candidate, negative-control anchors are one-second-grid times within the same uninterrupted possession, at least 3.0 seconds from the true anchor, at least 5.0 seconds from every reception/restart, and satisfying full-window/open-play/completeness rules. Select uniformly with a deterministic candidate-specific child seed. If none exists, omit that negative-control pair without broadening. Recompute for eight seconds.

## Leakage audit and interpretation

Sampling, spacing, pseudo-anchor generation, matching, tie-breaking, exclusions, and missingness never use focal displacement, local deformation, opponent change, cross-scale correspondence, resulting ball/centroid motion, or resulting activity. Permitted geometry is anchor ball location, window-start identity selection, coarse anchor ball zone, and completeness.

- **A:** stable typed differences remain after matching and are not reproduced by generic activity or negative controls.
- **B:** some differences remain but are overlapping, event-dependent, reference-sensitive, or context-heavy.
- **C:** differences are absent, vanish after reasonable matching, or are reproduced by generic activity or negative controls.

Independent expert annotation is desirable later but not required for internal geometric validation.
