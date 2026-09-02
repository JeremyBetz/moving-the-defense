# Attacker Movement Episode v2 — Game 2 Heldout Replication

**Status:** frozen prospectively before any Game 2 v2 result

**Freeze date:** 2026-09-01

**Starting commit:** `35e22081c2697be2b3773986c7745815bf2ce317`

**Execution tier:** Tier 3

This addendum governs only the untouched Metrica Sample Game 2 replication of the immutable v2 rule in [`attacker_movement_episode_v2.md`](attacker_movement_episode_v2.md). The machine-readable source of truth is [`config/attacker_movement_episode_v2_game2_replication.json`](../../config/attacker_movement_episode_v2_game2_replication.json).

## 1. Question and firewall

Does the exact frozen direction-aware attacker-only segmentation reproduce its Game 1 improvement in the fragmentation-versus-merging trade-off on Game 2 without sacrificing lower-speed movement coverage?

Only each outfield player's own trajectory and structural support enter segmentation. Defender coordinates, ball outcomes, event outcomes, footprint, response form, deformation, Game 3, and IDSSE are forbidden. Global `BALL OUT` and `SET PIECE` intervals may enter only as inherited open-play boundaries.

No Game 2 v2 result existed or had been inspected when this document was frozen.

## 2. Game 2 sample and support

- Use every non-goalkeeper player identity present in the canonical Metrica Sample Game 2 tracking data.
- Use the closed, independently reproduced Stage A support registry at `outputs/attacking_continuous_movement_game2_stage_a/` as the sole trajectory-continuity authority.
- Work separately by player, period, and frozen valid-support segment. No episode may cross a period, support-segment boundary, or inherited stoppage boundary.
- Coordinates are canonical 105 × 68 m physical pitch coordinates. Preserve the provider's frame number, period clock, and match clock.
- Sampling is 25 Hz. Apply the same centred seven-frame position mean used in Game 1, requiring all seven observed coordinates. Derive velocity from consecutive smoothed positions and their observed time difference.
- Do not interpolate, impute, clip, repair, rediscover, or revise trajectory support.
- Goalkeeper exclusion uses canonical goalkeeper metadata. No possession filter is used.

## 3. Immutable candidates and diagnostics

Candidate A and Candidate B are exactly those frozen in the Game 1 protocol and configuration. All segmentation constants, numerical boundary behavior, and diagnostics are inherited unchanged. Candidate C remains omitted. There is no maximum-duration rule.

Game 2 baseline and v2 diagnostics report episode count; duration, path, displacement, peak speed, directness $Q$, and cumulative absolute turning distributions; fragmentation; merging/direction; lower-speed meaningful-displacement coverage; and the long-duration tail.

## 4. Prospective heldout criteria

The exact inherited gates are:

- material fragmentation improvement: at least 20% relative reduction from Game 2 Candidate A;
- merging/direction safety: Candidate B rate at most 3.97%;
- lower-speed coverage: Candidate B share at least 36.8955525083439%;
- valid support, exact immutable implementation, deterministic reproduction, and no post-result tuning.

The 20% rule is the qualitative relative-improvement requirement used in Game 1, applied to the new match's own baseline rather than importing the Game 1 absolute fragmentation ceiling.

Status logic is frozen as follows:

- **GAME 2 ATTACKER EPISODE v2 REPLICATION SUPPORTED:** valid execution; all three numerical gates pass; objective audit checks pass; no scientific rule changed.
- **GAME 2 ATTACKER EPISODE v2 REPLICATION MIXED:** valid execution; the fragmentation reduction is at least 20%, but a safety, coverage, or objective audit requirement fails without constituting implementation invalidity.
- **GAME 2 ATTACKER EPISODE v2 REPLICATION NOT SUPPORTED:** valid execution but fragmentation improves by less than 20%, fragmentation does not improve, or merging/direction exceeds 3.97%.
- **GAME 2 ATTACKER EPISODE v2 REPLICATION INVALID:** support, implementation, governance, or construct validity failure only.

Long-episode count, share, maximum, and upper tail are prominent counterevidence but are not a new classification gate.

## 5. Frozen visual-audit selection

Cases are selected without v2 output and without defensive information:

1. eight chronological cases are centred on deterministic equally spaced quantiles of the chronologically sorted valid-support-segment midpoints, using a support-complete six-second display window when available;
2. the direct case is the first chronological support-complete four-second window with path at least 3 m and $Q\ge0.95$;
3. the direction-change case is the first chronological support-complete four-second window with path at least 3 m and cumulative reliable turning at least 90°;
4. the low-speed case is the first chronological support-complete four-second window with peak speed below 2 m/s and path at least 1 m;
5. the discontinuity case is the first chronological frozen Stage A invalid interval with an adjacent valid-support segment.

The first three trajectory rules use only the player's own smoothed trajectory and are evaluated before Candidate B is constructed. If no qualifying case exists, that absence is reported without replacement. Duplicate selections are retained and identified rather than substituted post hoc.

Objective audit checks require plotted boundaries to match serialized boundary rows, no episode to cross frozen invalid support, a qualifying direction-change case (if present) to contain at least one protected direction boundary, and a qualifying low-speed case (if present) to overlap at least one Candidate B episode. The direct case is descriptive because a legitimate direction boundary can coexist with high whole-window directness.

## 6. Serialization and reproduction

Serialize CSV and JSON with stable column ordering, sorted rows, UTF-8, newline termination, and deterministic float formatting inherited from the Game 1 implementation. Hash every governed output except the hash ledger itself. Re-run independently into a temporary directory and require every governed machine-readable output to be byte-identical. Figure bytes are not governed because renderer metadata can vary; figures must be regenerated and visually reviewed.

Only after Game 2 outputs are saved, hashed, and independently reproduced may the report compare Game 2 descriptively with the already-closed Game 1 result. No episode-level pooling or attacker–defender analysis is authorized.

## 7. Interpretation boundary

This replication can support an attacker-only movement segmentation statement. It cannot validate a tactical run detector, an optimal segmentation, a football run taxonomy, defensive response, causation, off-ball influence, or value.
