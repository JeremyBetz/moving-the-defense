# Post-5B Outcome-Blind Attacking Movement Segmentation Audit

## Purpose and firewall

This exploratory Sample Game 1 audit asks whether an attacking player's own tracking trajectory can be divided into finite, geometrically interpretable **movement-effort episodes** without using defenders or downstream outcomes. It does not test defensive response, attacker influence, tactical run type, or value.

Segmentation used only each player's own x/y coordinates, period/time, and global `BALL OUT`/`SET PIECE` exclusions. No defender coordinate, defensive centroid, nearest defender, focal-relative measure, pass/reception/shot outcome, or defensive-response outcome entered construction, evaluation, or visual selection. All supported outfield players from both teams were included; the audit does not condition episodes on possession and therefore uses “attacking player” as the future analytic role, not a claim that every interval occurred while that player's team attacked.

## Prospectively fixed exploratory rules

Rules were recorded in [`config/post5b_movement_segmentation_audit_rules.json`](../config/post5b_movement_segmentation_audit_rules.json) before outputs were reviewed. They are exploratory implementation choices, not a frozen validation protocol.

- **Coordinates and smoothing:** 25 Hz normalized Metrica coordinates were converted to 105 x 68 m. Player x and y were smoothed with a centered seven-frame (0.28 s) rolling mean requiring all seven samples. Velocity is the consecutive-frame difference of the smoothed coordinates divided by elapsed time. Missing support, period changes, `BALL OUT` intervals, and `SET PIECE` events form hard boundaries; no interpolation is used.
- **Method A — speed valleys:** a valley is a maximal flat run no higher than its immediate neighboring values and strictly lower than at least one. Its midpoint is the candidate time. Candidates less than 1.0 s apart are consolidated by retaining the lower-speed candidate (earlier candidate breaks exact ties). Consecutive retained valleys define episodes; intervals shorter than 1.0 s are excluded for numerical stability. Peak speed is never an inclusion rule.
- **Method B — high-speed comparator:** contiguous own-player speed at or above 5.5 m/s for at least 1.0 s, with the same 5.5 m/s termination threshold and no acceleration condition. This is a simplified literature/provider-inspired comparator, not an exact reproduction of a proprietary run detector.
- **Method C — fixed windows:** non-overlapping 4.0 s grids beginning at the first tracking time in each period. Only complete eligible windows are retained.

The descriptive diagnostic cutoffs were also fixed before review: short <=1.5 s, tiny path <=1 m, tiny displacement <=0.5 m, long >=8 s, displacement/path <=0.5, and a direction-change flag requiring path >=3 m and absolute heading change >=180 degrees. Heading increments use only consecutive segments with speed >=0.5 m/s.

## Sample and results

All 26 supported non-goalkeepers (13 per team, including substitutes) yielded episodes. Method A produced **38,651** episodes.

| Quantity | Median | IQR | Range |
|---|---:|---:|---:|
| Duration | 1.88 s | 1.32–2.76 s | 1.00–51.16 s |
| Path | 2.65 m | 1.32–5.65 m | 0.008–63.29 m |
| Net displacement | 2.58 m | 1.30–5.47 m | 0.001–61.53 m |
| Peak speed | 1.66 m/s | 1.09–3.20 m/s | 0.009–56.30 m/s |

The physically implausible 56.30 m/s maximum is retained as a tracking-data-quality warning rather than silently filtered. A separate, prospective tracking-support/QC investigation is required before formal segmentation validation. No clipping, winsorization, maximum-speed rule, or post-outcome cleaning was introduced. Tracking-data validity and segmentation design are separate methodological issues.

### Lower-speed retention and directional geometry

**95.78%** of Method A episodes peaked below 5.5 m/s. **15,845 (41.00%)** both peaked below 5.5 m/s and displaced the player at least 3 m. Method B found 720 high-speed runs; **96.72%** of Method A episodes had no temporal overlap with one. Valley segmentation therefore retains a large lower-speed movement domain that a run-only comparator removes. This says nothing about its tactical value.

Signed x/y displacement preserves distinctions hidden by path magnitude. For example, episodes near 5 m path include predominantly longitudinal, predominantly lateral, and diagonally opposed changes. Median displacement/path was 0.987, so most episodes were directionally coherent in net geometry even though similar scalar paths had different signed directions.

### Fragmentation

The main weakness is over-fragmentation under the fixed rule:

- 13,693 episodes (35.43%) lasted <=1.5 s;
- 6,694 (17.32%) had <=1 m path;
- 3,698 (9.57%) had <=0.5 m displacement;
- 16,320 (42.22%) met at least one predeclared fragmentation diagnostic.

Some one-second intervals are coherent movements, but deterministic figures also show tiny near-stationary pieces. The minimum-separation rule therefore does not by itself produce uniformly useful analytic units.

The dominant fragmentation pattern suggests that a future outcome-blind refinement should investigate whether local speed minima require additional evidence of a substantive valley, such as prominence/depth relative to surrounding movement, before being retained as episode boundaries. This is a prospective design implication, not an accepted rule: no prominence threshold, valley-depth threshold, new temporal separation, or hysteresis parameter is selected here.

### Merging and direction change

Only 141 episodes (0.36%) lasted >=8 s, 268 (0.69%) had displacement/path <=0.5, and 424 (1.10%) met the predeclared direction-change flag. In total, 763 (1.97%) met a merging/direction diagnostic. These are less common than fragmentation but include clear loops, reversals, and multiple directional legs without an internal retained speed valley. The 51.16 s episode is the clearest neutral counterexample to treating every valley interval as a compact effort.

### Fixed-window comparison

Fixed 4 s windows were temporally arbitrary relative to player movement: **51.84%** of Method A episodes were split by a fixed boundary, while **92.84%** of retained fixed windows contained parts of multiple Method A episodes. The median Method A start was 1.0 s from its nearest fixed-grid boundary. This supports movement-defined timing as informative, but it does not establish that the chosen valley rule is adequate.

## Deterministic visual audit

The primary sample comprises 16 evenly spaced episode indices after chronological sorting. It includes both teams, both halves, duration/speed variation, coherent trajectories, and tiny near-stationary fragments without manual aesthetic selection. Objective extremes additionally show the shortest, longest, highest-heading-change, lowest-peak-speed episode with >=3 m displacement, and first high-speed overlap.

The strongest representative support is Away Player 24, 380.20–385.04 s: a coherent 4.84 s, 13.65 m path with 13.53 m displacement and a valley-bounded acceleration/deceleration shape. The strongest deterministic counterexample is Home Player 6, 95.32–146.48 s: a 51.16 s interval, far too long to assume one finite effort. The most important aggregate failure is fragmentation, not merging: 42.22% meet a predeclared fragmentation diagnostic.

## Classification

**B — mixed.** The basic attacker-only approach survives: finite temporal units can be constructed independently of defensive behavior and tactical outcomes, and the result remains promising enough for outcome-blind refinement. Speed valleys preserve signed geometry and substantial lower-speed movement. However, the predeclared rule creates many very short or tiny fragments, while a substantially smaller set merges long or multi-leg movements. Over-fragmentation—not direction-change splitting—is the primary refinement problem. This implementation is not ready to define later defensive-response samples unchanged.

Supported claim:

> **Outcome-blind speed-valley segmentation provides reproducible finite descriptions of an attacking player's own movement and retains substantial lower-speed geometry that a high-speed-run comparator omits, but the tested rule has meaningful fragmentation and occasional direction-change/merging failures that require outcome-blind refinement before validation.**

It does **not** establish defensive response, attacker association or causation, marking, assignment, responsibility, attention, pinning, dragging, tracking, covering, handoffs, tactical run type, tactical success, relational reconfiguration, gravity, or off-ball value. A movement episode is only a reproducibly segmented portion of one player's motion.

## Provenance

Speed-based physical-effort/run segmentation is prior art. Llana et al. (2022) describe rolling-smoothed speed, valley-to-valley run sections, and a 21 km/h high-intensity descriptor. FIFA's training-methodology overview places globally used high-speed running thresholds in the 5.5–7.0 m/s range. This audit adapts those ideas to outcome-independent attacking movement episodes as possible future temporal units. It does not claim novelty for speed valleys or movement-episode analysis. Any later contribution would require a validated bridge from attacker episode to defensive geometry, contextual expectation, opponent association, and only then football interpretation.

## Artifacts

- Executable analysis: [`src/post5b_attacking_movement_segmentation_audit.py`](../src/post5b_attacking_movement_segmentation_audit.py)
- Review notebook: [`notebooks/post5b_attacking_movement_segmentation_audit.ipynb`](../notebooks/post5b_attacking_movement_segmentation_audit.ipynb)
- Machine-readable results: [`outputs/post5b_movement_segmentation_audit/`](../outputs/post5b_movement_segmentation_audit/)
- Figures: [`figures/post5b_movement_segmentation_audit/`](../figures/post5b_movement_segmentation_audit/)
