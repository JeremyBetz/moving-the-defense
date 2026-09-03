# Concurrent Defensive Coordination Form v1 — IDSSE External Replication

## Formal status

**IDSSE COORDINATION FORM EXTERNAL REPLICATION SUPPORTED**

The [external-replication clarification](../protocols/concurrent_defensive_coordination_form_v1_idsse_replication.md) was frozen and hashed before any protected IDSSE coefficient was computed. It introduced no pooled estimator and changed none of the [original protocol](../protocols/concurrent_defensive_coordination_form_v1.md) or configuration settings. All seven governed matches individually met the prospective `SUPPORTED` rule.

## Provider and implementation gate

The established IDSSE native/Kloppy equivalence layer reproduced provider frames, timestamps, observed player-coordinate null masks, player/team/goalkeeper rosters, and shared event context in all seven matches. Maximum coordinate disagreement was **0.000001831 m**, below the frozen **0.00001 m** tolerance. Ball null-mask equality remained descriptive and was not required because the frozen coordination form does not use the ball.

The IDSSE implementation retained metres, seconds, physical 1.0 Hz and 1.5 Hz filtering at 25 Hz, period-local continuous support, goalkeeper exclusion, complete ten-defender rank vectors, focal-relative velocity, the frozen 72-column model ordering, and grouped 60-second block resampling.

## Samples and primary external evidence

| Match | Observations | Anchors | Rank rows | Primary D2–D3 minus D4–D7 | 95% interval | Valid bootstraps | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| J03WMX | 12,335 | 1,235 | 123,350 | 0.03317 | [0.01999, 0.04661] | 2,000 | SUPPORTED |
| J03WN1 | 4,874 | 532 | 48,740 | 0.05165 | [0.03451, 0.06913] | 1,995 | SUPPORTED |
| J03WOH | 11,248 | 1,126 | 112,480 | 0.03822 | [0.02706, 0.04915] | 2,000 | SUPPORTED |
| J03WOY | 11,519 | 1,154 | 115,190 | 0.03354 | [0.02165, 0.04748] | 2,000 | SUPPORTED |
| J03WPY | 12,397 | 1,241 | 123,970 | 0.03697 | [0.02490, 0.04965] | 2,000 | SUPPORTED |
| J03WQQ | 9,961 | 1,021 | 99,610 | 0.04205 | [0.02841, 0.05555] | 2,000 | SUPPORTED |
| J03WR9 | 11,518 | 1,152 | 115,180 | 0.03663 | [0.02408, 0.05237] | 2,000 | SUPPORTED |

Units are m/s. The seven primary estimates were all positive, ranging from **0.03317 to 0.05165 m/s**, and every frozen interval was strictly above zero.

## D1–D10 profiles

| Match | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| J03WMX | 0.09967 | 0.03640 | 0.01774 | 0.00763 | 0.01086 | -0.02119 | -0.02171 | -0.03065 | -0.03557 | -0.03747 |
| J03WN1 | 0.13512 | 0.04153 | 0.04006 | -0.00446 | -0.00022 | -0.01541 | -0.02333 | -0.03144 | -0.04441 | -0.05311 |
| J03WOH | 0.11764 | 0.04132 | 0.02213 | 0.01372 | -0.01349 | -0.01011 | -0.01608 | -0.02865 | -0.03116 | -0.04527 |
| J03WOY | 0.10525 | 0.03521 | 0.01449 | -0.00299 | 0.00224 | -0.01398 | -0.02005 | -0.02661 | -0.02855 | -0.02454 |
| J03WPY | 0.10690 | 0.03737 | 0.01571 | 0.00312 | -0.02107 | -0.00838 | -0.01539 | -0.03207 | -0.01828 | -0.02404 |
| J03WQQ | 0.11459 | 0.03623 | 0.02096 | -0.00073 | -0.00627 | -0.02275 | -0.02407 | -0.03280 | -0.02982 | -0.03014 |
| J03WR9 | 0.10793 | 0.02714 | 0.02171 | -0.00301 | -0.01377 | -0.01204 | -0.02001 | -0.03379 | -0.01845 | -0.02087 |

D1 was largest in every IDSSE match, D2 and D3 were individually positive in every match, and middle/far ranks were often negative. These are bounded post-classification descriptions, not additional criteria or evidence of a defensive tactic.

## Frozen sensitivities, benchmark, and secondary quantities

| Match | 1.5 Hz primary [95% interval] | D1 minus D4–D7 [95% interval] | Absolute | Cross-axis | Deformation | Raw/secant | Seven-frame |
|---|---:|---:|---:|---:|---:|---:|---:|
| J03WMX | 0.03325 [0.02005, 0.04667] | 0.10577 [0.08723, 0.12636] | 0.03053 | 0.00633 | 0.01138 | 0.03343 | 0.03315 |
| J03WN1 | 0.05153 [0.03455, 0.06888] | 0.14597 [0.11795, 0.17333] | 0.04663 | 0.00430 | 0.00817 | 0.05180 | 0.05148 |
| J03WOH | 0.03783 [0.02670, 0.04877] | 0.12413 [0.10584, 0.14190] | 0.03507 | 0.00557 | 0.01173 | 0.03828 | 0.03809 |
| J03WOY | 0.03299 [0.02131, 0.04729] | 0.11394 [0.08780, 0.14251] | 0.03158 | 0.00083 | 0.00585 | 0.03539 | 0.03518 |
| J03WPY | 0.03619 [0.02368, 0.04901] | 0.11733 [0.09889, 0.13745] | 0.03404 | 0.00149 | 0.00669 | 0.02174 | 0.03674 |
| J03WQQ | 0.04171 [0.02802, 0.05517] | 0.12804 [0.10887, 0.14923] | 0.03793 | 0.01057 | 0.00745 | 0.04159 | 0.04203 |
| J03WR9 | 0.03603 [0.02324, 0.05245] | 0.12014 [0.08271, 0.16000] | 0.03401 | 0.00714 | 0.01869 | 0.03856 | 0.03827 |

All 1.5 Hz point estimates were positive with intervals strictly above zero. D1 is a benchmark only; the absolute-coordinate, cross-axis, deformation, raw/secant, and seven-frame quantities are descriptive and did not determine or rescue any status.

## Bounded comparison with Metrica

The seven IDSSE primary estimates were less variable than the two Metrica development/replication estimates: Metrica Game 1 was **0.04045 [0.02366, 0.05538]**, while Game 2 was **0.04587 [-0.01056, 0.09260]**. IDSSE rank profiles were consistently positive at D1–D3 and mostly negative thereafter; this was more orderly than Metrica Game 2's irregular profile. The provider environments, samples, and uncertainty differ, so this is not a pooled nine-match estimate or a magnitude-equivalence claim.

## Interpretation boundary

The frozen attacker-aligned defender-relative movement construct was externally supported across all seven governed IDSSE matches. Observationally, the association between attacker movement and within-unit defender movement in the attacker's direction was stronger for D2–D3 than D4–D7 after the frozen pre-interval conditioning.

This does not establish tracking, marking, attention, reaction, responsibility, attacker influence, causation, tactics, disruption, space creation, gravity, or attacking value. Match-profile differences are descriptive and must not be interpreted as team-response archetypes.

## Reproducibility

All seven provider-equivalence gates and hard-QC assertions passed. Every retained focal observation had a complete vector of ten unique defending outfield players. At least 1,995 of 2,000 paired block bootstraps were valid per match. An independent complete rerun reproduced all six governed machine-readable outputs byte-for-byte. Metrica Sample Game 3 was not inspected.

The complete observation-level Parquet reproduced at **89,719,630 bytes**, SHA-256 `8a580a2d079fa248a1e8e64578b975b52e9fe790c595a6d16e37811c4a43e8d0`. It is intentionally excluded from the public repository because redistribution permission for this provider-linked derivative is not established and the compact results suffice for public inspection. It remains locally reproducible for holders of the licensed source data; omitting it changes no result, ledger entry, or scientific hash.

See the [machine-readable output directory](../../outputs/concurrent_defensive_coordination_form_idsse_v1/), [implementation](../../src/concurrent_defensive_coordination_form_idsse_v1.py), and [presentation figure](../../figures/concurrent_defensive_coordination_form_idsse_v1/external_replication.png).
