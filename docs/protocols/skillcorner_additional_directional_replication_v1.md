# Additional SkillCorner Directional Replication v1

**Status:** frozen prospectively; response execution not authorized

**Freeze date:** 2026-09-17

## 1. Question and lineage

This protocol freezes one additional-provider-population test of the already
governed Project 1 directional estimand:

> In ten independently reacquired, nonoverlapping SkillCorner matches, is
> outward off-ball displacement more strongly associated with subsequent
> localized defender-relative reorganization than equivalently modelled
> goalward displacement?

The ten matches were prospectively frozen as a nonoverlapping Project 1
replication population after independent reacquisition and response-blind
compatibility checking. Project 1 had not previously evaluated its frozen
directional response on these matches. Global prior exposure outside this
project is not claimed to be absent.

This is a prospective replication in a new Project 1 population from an
already-used provider environment. It is not an untouched-dataset claim and
does not pool providers.

## 2. Frozen population and source

Use only official SkillCorner Open Data at commit
`02a396ffd09b283c9f092fdedeff11da6d535b66` and tree
`44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`. The exact formal population is:

`1874553`, `1927964`, `1959846`, `1986691`, `1996436`, `2006363`,
`2007448`, `2007721`, `2010085`, and `2016236`.

All ten must remain present. The nine earlier Project 1 matches (`1886347`,
`1899585`, `1925299`, `1996435`, `2006229`, `2011166`, `2013725`,
`2015213`, `2017461`) and the provider-status exclusion `1953632` are
prohibited. No match may be substituted or removed after response access.

Population and source identity are bound to the committed support preflight:

- protocol SHA-256 `34f6ea94ae14a2bd990214496dcbe0db7fbec6de434f830a5e654aa75be9f0b3`;
- configuration SHA-256 `b5237ba47ebb254df5cbf9d7f4004dab0469aacab55c54e645ef7e1772f63452`;
- inventory SHA-256 `cd53a11c3f58a12f0bb808a3cf7600e1dc82ceb09a3e7703a6447716cc08a3e5`;
- manifest SHA-256 `f4b5a586dcb4c95a0d73373962d46aa54f6db9f4204b87a1fdacb5e27e86ba46`;
- source ledger SHA-256 `101a85a2f27ac50bfabae3059daf8df2fb39825accc528666348ba22a927aae1`; and
- final hash ledger SHA-256 `640cabf5ccb8759803393370027c020bcfa8d6b018e16dd74b6bf05facab6851`.

## 3. Scientific authority

Scientific construction is unchanged from the frozen SkillCorner directional
protocol, configuration, and implementation:

- `docs/protocols/defensive_reorganization_spatial_form_v1_skillcorner_external.md`;
- `config/defensive_reorganization_spatial_form_v1_skillcorner_external.json`; and
- `src/defensive_reorganization_spatial_form_skillcorner_external.py`.

The target is mean D1--D3 minus mean D4--D7 accumulated leave-one-out
defender-relative path over `[t,t+2]`, with defender ranks fixed at the anchor.
Attacker windows remain `[t-4,t-2]` and `[t-2,t]`. Native 10 Hz positions use
the centred three-frame smoother, canonical 105 by 68 metre scaling, goalward
x, and start-fixed focal-side y reflection. Eligibility, roster, possession,
phase, ball, detection, identity and support rules are unchanged.

The exact nine-column adjusted equal-total-match-weight OLS is unchanged. The
sole primary estimand is

$$\Delta_{O-G}=\beta_{outward}-\beta_{goalward}.$$

No cross-provider pooling, model search, alternative covariate, threshold,
window, representation or result-driven exclusion is allowed.

## 4. Inference and robustness

Use 2,000 deterministic paired PCG64 bootstrap draws with seed `20260905`.
Resample complete 60-second blocks independently within match and period,
preserve all simultaneous anchor rows, retain all ten matches, and calculate a
two-sided 95% percentile interval. At least 1,900 finite full-rank draws are
required.

Report the primary macro contrast and interval, ten match-specific contrasts,
ten leave-one-match-out contrasts, the inherited joint-displacement trim, and
the inherited majority-detected quality sensitivity. Their definitions and
magnitude-retention gates remain exactly those in the scientific authority.

## 5. Ordered classification

Evaluate in this order:

1. **INVALID:** any identity, source, support, estimability, inference,
   reproduction or package failure.
2. **SUPPORTED:** the macro contrast is positive; its interval is strictly
   positive; at least 7 of 10 match contrasts are positive; all ten
   leave-one-match-out contrasts are positive; and the inherited trim and
   quality gates pass.
3. **MIXED:** the macro contrast is positive but one or more preceding support
   gates fail.
4. **NOT SUPPORTED:** every other valid result, including a nonpositive macro
   contrast.

A mixed, null, negative or invalid result is preserved. No result authorizes
retuning or a replacement analysis.

## 6. Publication and stopping boundary

Only compact aggregate results, counts, QC, provenance and hashes may be
serialized. Provider rows, observation identifiers, timestamps, coordinates,
rank rows, individual responses, predictions, residuals and match surfaces are
prohibited.

Animation, API work, Game 3, DRD, SkillCorner response-mode outcomes, and any
new representation are outside this protocol. Execution requires a separate,
explicit human authorization reference and a clean hash-verified frozen
package. This freeze does not authorize response access.

The maximum positive interpretation is an observational association in these
ten matches. It does not establish causation, marking, intent, tactical value,
space creation, or universal provider transport.
