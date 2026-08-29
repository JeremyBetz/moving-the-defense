# Phase 4C IDSSE Outcome-Blind Mapping Audit

## Status and firewall

This audit was completed after Phase 4C protocol v1.0 was frozen and before any focal-relative coordinate or path was constructed. The mapping stage inspected only provider schema, raw coordinate presence, timing, identities, goalkeeper metadata, possession/open-play event fields, substitutions, ball observations, interval membership, and frozen support counts. It did not calculate focal-relative paths, distributions, activity relationships, misaligned-reference outcomes, sensitivities, or high/low examples.

The official seven-match IDSSE release was obtained from the public mirror of the DFL-authorized CC BY 4.0 dataset accompanying Bassek et al. (2025). Raw XML files remain under ignored `data/idsse_raw/`; SHA-256 checksums are recorded in `outputs/phase4c/input_checksums.csv`.

## Provider mapping

| Requirement | IDSSE field / rule | Decision | Rationale |
|---|---|---|---|
| Match identity | filename and `General.MatchId` / tracking `MetaData.MatchId` | **A — direct mapping** | Stable DFL match identifier agrees across the three feeds. |
| Team identity | `General.HomeTeamId`, `General.GuestTeamId`, `Team.TeamId`, tracking `FrameSet.TeamId` | **A** | Explicit provider IDs; no name matching. |
| Player identity | metadata `Player.PersonId`, tracking `FrameSet.PersonId` | **A** | Stable provider IDs join team sheets to trajectories. |
| Goalkeeper | metadata `Player.PlayingPosition == "TW"` | **A** | Explicit goalkeeper position; goalkeeper is excluded from every defending-outfield set. |
| Period | tracking `FrameSet.GameSection`; period-opening event `KickOff.GameSection` | **A** | `firstHalf` and `secondHalf` are explicit. |
| Timestamp | ISO-8601 `Frame.T` and `Event.EventTime`, converted to UTC nanoseconds | **A** | Feeds are synchronized in absolute time despite different displayed offsets. |
| Sampling | consecutive tracking timestamps differ by 40 ms | **A** | 25 Hz in all matches. |
| Pitch and coordinates | `Environment.PitchX/PitchY`, tracking `PitchSize.X/Y`, raw `Frame.X/Y` | **A** | Every match reports 105×68 m. Coordinates are already metric and centered approximately at (0,0); no orientation normalization is applied. |
| Coordinate validity | entity has a frame with finite raw `X` and `Y` | **B — implementation clarification** | Absent entity frames are missing. Provider `M` is match minute, not measurement validity; interpreting `M==1` as quality would be erroneous. No interpolation is used. |
| Ball | tracking `FrameSet.TeamId == "BALL"`; finite raw `X/Y` throughout interval | **A/B** | Explicit ball entity is direct; finite-coordinate validity is the same clarification as above. |
| Substitutions / availability | metadata team sheet, event `Substitution`, and actual frame presence | **A** | Fixed membership is determined from complete raw presence over each interval; substitutions are also retained for audit. |
| Possession team | latest event-carried team, updated by `Play`, `OtherBallAction`, `ShotAtGoal`, `BallClaiming`, and possession-changing `TacklingGame` | **B** | Deterministic provider translation of the inherited latest-possession-bearing-event logic. Tackle winner is used only when `PossessionChange=true`; otherwise loser team retains possession. |
| Open play / restart | `Play.FromOpenPlay`; explicit `KickOff`, `ThrowIn`, `GoalKick`, `FreeKick`, `CornerKick`, `Penalty`, `RefereeBall`, `Offside`, and `FinalWhistle` set non-open state | **B** | Provider vocabulary preserves the inherited football condition. A later `Play.FromOpenPlay=true` resumes open state. |
| Interval grid | per half, half-open 5-second UTC grids from the period kickoff; first grid boundary not before tracking begins; exactly 125 regular frames | **B** | Implements elapsed-period multiples when provider frames begin a fraction of a second after kickoff. No frame resampling or padding. |
| Defending team | the other metadata team from the unique event-defined attacking team | **A** | Deterministic two-team complement. |
| Fixed focal/reference membership | all defending outfield players with finite coordinates at every one of 125 frames; require at least nine; every complete member becomes focal | **A** | Direct implementation of the frozen construct and eligibility rule. |

No **C — material protocol issue** was found. These mappings do not alter the construct, eligibility principle, reference, numerical criteria, controls, or classification.

## Outcome-blind support

| Match | Eligible intervals | Team 1 / Team 2 defending intervals | Focal defenders with ≥25 intervals | Usable |
|---|---:|---:|---:|---|
| J03WMX | 695 | 432 / 263 | 27 | Yes |
| J03WN1 | 574 | 316 / 258 | 22 | Yes |
| J03WOH | 612 | 260 / 352 | 25 | Yes |
| J03WOY | 635 | 331 / 304 | 27 | Yes |
| J03WPY | 708 | 447 / 261 | 29 | Yes |
| J03WQQ | 640 | 275 / 365 | 28 | Yes |
| J03WR9 | 656 | 412 / 244 | 27 | Yes |

All seven matches exceed 100 eligible intervals, both defending teams exceed 40 intervals, and at least eight focal defenders exceed 25 intervals. The behavioral execution gate therefore passes. Detailed interval-level exclusions and focal counts are in `outputs/phase4c/mapping_interval_support.csv` and `outputs/phase4c/mapping_support_summary.json`.

## Frozen implementation audit before outcomes

- focal coordinate is raw focal x/y minus the contemporaneous mean x/y of the other fixed complete defending outfield players;
- focal defender and goalkeeper are excluded from the reference;
- membership is fixed within each interval;
- centered rolling means operate separately on x/y with 5/7/9 frames, no padding and no interpolation;
- path accumulation uses successive finite smoothed x/y positions in physical metres;
- focal absolute, full defending-outfield centroid, summed defender, and ball paths remain separate;
- temporally misaligned references are selected within match, period, defending team, and stable-rank full-centroid activity bin using the frozen temporal and tie rules;
- common translation, 10,000 interval-cluster bootstrap resamples, seed `20260830`, activity roles, sensitivity rules, and A/B/C/P precedence are copied unchanged from protocol v1.0.

The machine-readable companion is `config/phase4c_idsse_implementation.json`. If code, this note, that config, or the frozen protocol disagree, execution must stop rather than choose an outcome-favorable interpretation.
