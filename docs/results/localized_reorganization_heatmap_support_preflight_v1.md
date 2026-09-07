# Localized Reorganization Heatmap — Support Preflight v1

**Status:** response-blind support characterization; no response surface or response field was read.

## Bounded alternatives

| Profile | h (m) | Cells | Coverage | Match coverage range | Mean raw / unique anchors | Min blocks / Kish row-weight concentration | Max nearest (m) | Mass balance | Edge: touch / goal / centre / penalty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basic | 2.5 | 5412 | 75.798% | 78.529%–93.529% | 974.2 / 864.2 | 5 / 10.01 | 2.50 | 0.449 | 30.952% / 0.000% / 100.000% / 65.541% |
| basic | 5 | 6795 | 95.168% | 95.980%–99.678% | 3180.1 / 2057.8 | 3 / 10.03 | 5.00 | 0.435 | 77.143% / 49.265% / 100.000% / 97.973% |
| basic | 7.5 | 7106 | 99.524% | 99.650%–100.000% | 6680.4 / 2998.4 | 4 / 10.00 | 7.42 | 0.441 | 95.714% / 88.235% / 100.000% / 100.000% |
| basic | 10 | 7140 | 100.000% | 100.000%–100.000% | 11413.5 / 3812.8 | 7 / 16.21 | 8.99 | 0.449 | 100.000% / 100.000% / 100.000% / 100.000% |
| basic | 12.5 | 7140 | 100.000% | 100.000%–100.000% | 17088.7 / 4546.4 | 16 / 37.71 | 8.99 | 0.454 | 100.000% / 100.000% / 100.000% / 100.000% |
| basic | 15 | 7140 | 100.000% | 100.000%–100.000% | 23406.1 / 5181.1 | 28 / 78.78 | 8.99 | 0.458 | 100.000% / 100.000% / 100.000% / 100.000% |
| conservative | 2.5 | 4443 | 62.227% | 64.328%–85.490% | 1096.6 / 974.6 | 9 / 20.03 | 2.48 | 0.465 | 10.000% / 0.000% / 97.059% / 43.243% |
| conservative | 5 | 6373 | 89.258% | 90.308%–99.188% | 3361.9 / 2174.8 | 8 / 20.01 | 4.87 | 0.442 | 62.857% / 18.382% / 100.000% / 84.459% |
| conservative | 7.5 | 6979 | 97.745% | 97.843%–100.000% | 6790.3 / 3046.6 | 7 / 20.05 | 7.42 | 0.444 | 86.667% / 72.794% / 100.000% / 100.000% |
| conservative | 10 | 7132 | 99.888% | 99.888%–100.000% | 11425.3 / 3816.6 | 8 / 20.06 | 8.99 | 0.450 | 97.619% / 96.324% / 100.000% / 100.000% |
| conservative | 12.5 | 7140 | 100.000% | 100.000%–100.000% | 17088.7 / 4546.4 | 16 / 37.71 | 8.99 | 0.454 | 100.000% / 100.000% / 100.000% / 100.000% |
| conservative | 15 | 7140 | 100.000% | 100.000%–100.000% | 23406.1 / 5181.1 | 28 / 78.78 | 8.99 | 0.458 | 100.000% / 100.000% / 100.000% / 100.000% |

## Support-only recommendation

Response-blind human selection: Conservative h=7.5 m balances locality with seven-match support in the reviewed bounded frontier. It was not selected by a prospectively frozen automatic rule. Human approval freezes it for the future descriptive response-map stage; this execution remains support-only.

{
  "bandwidth_m": 7.5,
  "common_support_fraction": 0.9774509803921568,
  "description": "Human review selected this option after response-blind support inspection. It was not selected by a prospectively frozen automatic rule, and response values remained unseen when selected. It is frozen only for the future descriptive response-map stage; this support-only execution did not render a response surface.",
  "profile": "conservative",
  "recommended": true,
  "status": "HUMAN_APPROVED_FUTURE_RESPONSE_MAP_CHOICE"
}

## Boundary

This report used only governed observation identity/support fields and in-memory `t-2 s` attacker coordinates. It did not read or construct a response, a near-minus-middle outcome, a coefficient, or a response-colored surface. The future response-map specification is frozen separately and still has not been executed. Native coordinates were retained without clipping or exclusion: 586 of 72,316 anchors (0.810%) lay outside the nominal pitch rectangle, while kernels were evaluated only at legal-pitch grid cells.

Correcting period-aware 60-second block identity did not change any candidate support-pass cell or mask; it corrects reported temporal-block counts without changing the underlying eligible anchor population.

Kish row-weight concentration counts describe local kernel-weight concentration, not independent observations; simultaneous attackers can increase them. Unique-time-anchor and period-aware 60-second-block counts provide separate temporal-support diagnostics.

## Provenance

- protocol SHA-256: `050152e1a1c598cd8fcb985f70cd958b3ba4e9d17dca52db814561f979c65472`
- configuration SHA-256: `3fe8f0b88d07833abc534706734480cbd1a4396d0c6aada0f8d24cf6503fd1fd`
- source SHA-256: `d64f1e66a4ca65297133bbd11d4440cfb9c0b1b8fbc228c058a1f68b873cdf31`
- support-grid SHA-256: `dccd54618018e6dd1bee8f136f9a2b0eef0f3384b73a502b931a6719f0ad25fc`
