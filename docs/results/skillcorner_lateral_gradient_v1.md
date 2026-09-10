# SkillCorner Lateral Gradient v1

The IDSSE spatial pattern generated the hypothesis. This SkillCorner analysis tests that hypothesis prospectively in a provider environment already used previously for the directional study. It is not untouched-dataset replication or independent new dataset validation.

Frozen hypothesis: beta_lat > 0 for |y_c(t-2)| under match-intercept equal-total-match-weight OLS.

**Classification:** SUPPORTED

Primary beta_lat: 0.009809 m/m; 95% interval [0.008125, 0.011573].
Majority-detected beta_lat: 0.019631 m/m; 95% interval [0.016244, 0.023107]; sign: positive.
Positive match slopes: 9/9. Match slopes are descriptive, not independent replications.

## Leave-one-match-out estimates

- Omit 1886347: 0.010444 m/m (positive).
- Omit 1899585: 0.009767 m/m (positive).
- Omit 1925299: 0.009717 m/m (positive).
- Omit 1996435: 0.009186 m/m (positive).
- Omit 2006229: 0.009972 m/m (positive).
- Omit 2011166: 0.009670 m/m (positive).
- Omit 2013725: 0.010029 m/m (positive).
- Omit 2015213: 0.009581 m/m (positive).
- Omit 2017461: 0.009910 m/m (positive).

## Population and provenance

Primary observations: 49107; quality observations: 11810.
Valid paired bootstrap draws: 2000/2000.
Support manifest: `outputs/skillcorner_lateral_gradient_support_preflight_v1/manifest.json`; SHA-256 `e3f4df125e4516f25770583b458f73d1de0cd2ae05b7d60b811fdf3002c0ff52`.
Pinned source ledger: `outputs/skillcorner_lateral_gradient_support_preflight_v1/source_hashes.json`; SHA-256 `7bd20c0fe5b4a02f3dba6396791ead40f71c91c2b4b8cc4dd7a787ffcff64834`.
- Match 1886347: primary 5670; quality 1529.
- Match 1899585: primary 5083; quality 1068.
- Match 1925299: primary 6570; quality 1305.
- Match 1996435: primary 5967; quality 2559.
- Match 2006229: primary 5795; quality 2278.
- Match 2011166: primary 4522; quality 625.
- Match 2013725: primary 5471; quality 942.
- Match 2015213: primary 5143; quality 803.
- Match 2017461: primary 4886; quality 701.
- primary observation digest: `2dc4e404e2c462c54416ac122f9a33950ced22d5e5e2fe5dc6ca7760d892d018`.
- quality observation digest: `a81c9a16cae54ed0f4b45908265f9c91514eb3e3f9467cbbf9105812de9fb17b`.
- `config/skillcorner_lateral_gradient_support_preflight_v1.json`: `8a25438a31d954d0f0d3a43577ebc6b39f16af3e902625b2554ca9150c9d17fb`.
- `config/skillcorner_lateral_gradient_v1.json`: `94423a8e42526b985fa4331f9af8ea408d00244ca2a1869a2aa22742cbae1f4f`.
- `docs/protocols/skillcorner_lateral_gradient_support_preflight_v1.md`: `02303400884ad6054d4aed123e13186c9706c887d0a618319953f2563ba25b94`.
- `docs/protocols/skillcorner_lateral_gradient_v1.md`: `8423c5cd05b832d72061c3ea6884b8451655fa8768737ac0535ab0a7215dea1e`.
- `outputs/skillcorner_lateral_gradient_support_preflight_v1/manifest.json`: `e3f4df125e4516f25770583b458f73d1de0cd2ae05b7d60b811fdf3002c0ff52`.
- `outputs/skillcorner_lateral_gradient_support_preflight_v1/source_hashes.json`: `7bd20c0fe5b4a02f3dba6396791ead40f71c91c2b4b8cc4dd7a787ffcff64834`.
- `src/defensive_reorganization_spatial_form_skillcorner_external.py`: `933cfe4da4687f20473914d452e7c211e2a6ae955597400093af990e0f695f2c`.
- `src/defensive_reorganization_spatial_value_v1_design.py`: `b13bb0f5b394910eb72b68072243287c31bede88870399280dc4354cd8495156`.
- `src/infrastructure/skillcorner_spatial_form_adapter.py`: `78ff9af7adb795a71585061d677e4fd1c77d6e5eed90645217664ec8a9fd7246`.
- `src/skillcorner_lateral_gradient_support_preflight_v1.py`: `3df05634112a41edb1b7eba356a06b98573a7976950a9f188fc470dcf1adf931`.
- `src/skillcorner_lateral_gradient_v1.py`: `1bee4e4b5c7d7f6457d34bb549978fc657e647bb4d537b27f13fe987d5681627`.
- `tests/test_skillcorner_lateral_gradient_support_preflight_v1.py`: `25dadbe60c903cd597a3160e99948c75a1e28b9b4689e5d5e6643d032163c5cf`.
- `tests/test_skillcorner_lateral_gradient_v1.py`: `ebdf0fdcfe2fcc001763f76fe340de4bbdd4a3717a2f29971b66679c56dc642d`.

## Measurement and interpretation boundaries

Coordinates include detected and provider-extrapolated positions; direct-detection retention varies by match. The aggregate support audit did not establish coordinate accuracy. The majority-detected sensitivity is not ground truth.
The interval is conditional on these nine matches, the frozen 60-second block convention, and this measurement process. Finite out-of-pitch starts remain retained; the sparse tail beyond 34 m is not interpreted.
This is an observational spatial association, not causation, influence, marking, tactical effectiveness, or value. It does not validate the IDSSE heatmap itself. No post-result model, filter, or diagnostic changes are authorized.
