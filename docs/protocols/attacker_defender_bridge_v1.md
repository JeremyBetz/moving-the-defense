# Attacker-to-Defender Bridge Protocol v1.0

**Protocol status:** frozen before bridge execution

**Freeze date:** 2026-08-31

**Classification:** **A — BRIDGE PROTOCOL READY**

**Scientific boundary:** observational attacker movement → subsequent defensive geometry. No assignment, intention, causation, tactical success, gravity, or value.

## 1. Purpose

Moving the Defense has validated two separate measurement components: continuous attacker-only geometry across both Metrica sample matches, and focal-defender movement relative to the contemporaneous defending unit across Metrica and IDSSE. This protocol freezes the first simple test connecting those components. It does not execute that test.

The bridge is deliberately narrower than the football ideas that motivate it. Tracking shows where players moved. It does not reveal who was responsible for whom or why a player moved.

## 2. Primary scientific question

> **Conditional on strictly earlier defensive context, is greater observed attacking movement over the preceding two seconds associated with greater subsequent focal-relative movement among the three spatially nearest defending outfield players?**

The temporal roles are distinct:

- **Exposure:** one attacker's own frozen movement geometry during $[t-2,t]$.
- **Outcome:** the following focal-relative movement of a defender set during $[t,t+h]$.
- **Context:** defensive movement during $[t-4,t-2]$, before the attacker exposure begins.

No response-interval information may define the exposure, select defenders, change support, or select an observation.

## 3. Inference boundary

The protocol estimates temporal geometric association. It does not observe marking assignment, tactical instruction, player intention, decision-making, responsibility, success, defensive quality, or attacker value. “Local” means spatially near under a frozen rule, not tactically assigned.

The inference ladder remains:

```text
attacker movement → subsequent defensive geometric change
                  ≠ responsibility → causation → value
```

## 4. Prerequisite measurements

### 4.1 Attacker geometry

Use continuous attacker movement v1 unchanged: centred seven-frame mean at native 25 Hz, canonical fixed-pitch coordinates, 2 s primary window, and `delta_x_m`, `delta_y_m`, `path_length_m`, `straightness`, and `straightness_valid`. The representation classified A on development Game 1 and prospectively held-out Game 2.

### 4.2 Defensive geometry

For focal defender $d$, let

$$
\mathbf c_{-d}(s)=\frac{1}{N-1}\sum_{j\in D,\,j\ne d}\mathbf x_j(s),
\qquad
\mathbf r_d(s)=\mathbf x_d(s)-\mathbf c_{-d}(s),
$$

where $D$ is the complete supported defending-outfield set and the goalkeeper is excluded. For interval $[u,v]$,

$$
P_{\mathrm{rel}}(d;u,v)=
\sum_{i:u<s_i\le v}\|\mathbf r_d(s_i)-\mathbf r_d(s_{i-1})\|_2.
$$

This is the validated focal-versus-collective movement primitive. It says how much one defender moved differently from the rest of the defending outfield unit, not why.

Use the established native-25-Hz defensive implementation: canonical 105 × 68 m fixed-pitch coordinates; centred seven-frame arithmetic means calculated only on complete consecutive support; ten defending outfield players; and no interpolation, padding, partial smoother, direction normalization, or missing-player centroid. Compute each focal reference from the other nine smoothed defending outfield trajectories. Because the mean and centred arithmetic smoother are linear, this is numerically equivalent to smoothing their complete raw centroid, subject to the frozen tolerance. Sum all consecutive 0.04 s focal-relative steps including both interval endpoints: 25 steps at 1 s, 50 at 2 s, and 100 at 4 s.

## 5. Dataset roles and execution order

- **Metrica Sample Game 1:** bridge development execution, implementation diagnostics, and football-readable visualization.
- **Metrica Sample Game 2:** prospectively bridge-held-out replication after this protocol is committed. It is not a pristine dataset generally: it has already supported defensive measurement validation and attacker-representation validation. No attacker-to-defender association has been inspected, so it remains conditionally held out for this new relationship.
- **Metrica Sample Game 3:** untouched and not designated for this bridge.
- **IDSSE:** no bridge execution under v1. Its defensive primitive has replicated there, but the attacker representation lacks a prospectively validated native-frequency cross-provider implementation.

No specification, threshold, linkage rule, model, figure selection, or interpretation may change after Game 1 bridge results are viewed. Game 2 may be opened for bridge execution only after the Game 1 implementation passes hard QC under this committed protocol. A Game 1 result cannot tune Game 2.

## 6. Observational unit and sampling cadence

The primary unit is one eligible `(match, period, t, attacker)` observation. Multiple attacking outfield players at the same $t$ remain separate observations; their shared time and defensive context are preserved in uncertainty blocks rather than treated as independent.

Primary endpoint times use a **nonoverlapping four-second cadence**:

$$
t_{p,k}=o_p+4+4k,\qquad k=0,1,2,\ldots,
$$

where $o_p$ is the first canonical `time_period_s` in period $p$. Thus the strictly prior context $[t-4,t-2]$, attacker exposure $[t-2,t]$, and primary response $[t,t+2]$ fit in the period. Consecutive primary exposure-plus-response spans for the same player meet only at their boundary and share no path step. The phase offset is fixed by the period origin and is not selected from results.

The dense 0.20 s attacker grid may be used only for geometric illustration of an already selected primary observation, never as naïvely independent inferential data or to move endpoints.

## 7. Temporal ordering

- Strictly prior defensive context: $[t-4,t-2]$.
- Primary attacker exposure: $[t-2,t]$.
- Primary defensive response: $[t,t+2]$.
- Secondary response-horizon sensitivities: $[t,t+1]$ and $[t,t+4]$ only.

The two-second response is primary because it matches the validated primary attacker duration, is physically interpretable, and avoids horizon search. The one- and four-second results are robustness descriptions; they cannot replace the primary result or select an “optimal” lag. No onset detection, post-hoc alignment, or additional horizon is permitted.

## 8. Attacker exposure

The primary exposure is

$$
X_a(t)=P_a(t;2\ \mathrm{s}),
$$

the frozen `path_length_m` of attacker $a$ over $[t-2,t]$, reported in metres. This asks whether the amount of attacker travel is associated with subsequent local defensive adjustment. It does not test a run direction, movement type, purpose, threat, or quality.

The already frozen `delta_x_m`, `delta_y_m`, `straightness`, and `straightness_valid` are retained as separate secondary descriptive quantities. They may not be combined into a score, embedding, PCA component, learned exposure, or selection rule.

## 9. Attacking-team and defender linkage

At $t$, define the attacking team using the existing Metrica convention: take the team on the latest event of type `PASS`, `RECOVERY`, `SET PIECE`, or `SHOT` whose period matches and whose start time is at or before $t$ within $10^{-9}$ s, ordered by period, event start time, and start frame. The observation is eligible only when that event and team exist. This event state identifies team context only; it does not label an action or outcome.

Every supported outfielder on that team is a candidate attacker. Players are not selected by event involvement, reception, pass target, speed, path magnitude, visual interest, or subsequent outcome.

The opposing complete outfield set is the defending team. At the exact endpoint $t$, order its ten supported outfield players by Euclidean attacker-defender distance in canonical metres, breaking exact ties by canonical `player_key`.

- **Primary local set $L_3(a,t)$:** the first three defenders.
- **Descriptive nearest comparator:** rank one only, explicitly “nearest defender at $t$,” never “marker” or “assigned defender.”
- **Matched nonlocal control $F_3(a,t)$:** the last three defenders, ordered farthest first.

Set membership is fixed at $t$ for every baseline, outcome, sensitivity, and control calculation. It may not change with future proximity or movement. $K=3$ is not optimized: it preserves a local neighborhood without asserting one true matchup and permits a dimension-matched farthest-three control.

## 10. Primary defensive outcome and local aggregation

For response horizon $h$, the primary local outcome is

$$
Y_{\mathrm{local}}(a,t;h)=
\frac{1}{3}\sum_{d\in L_3(a,t)}P_{\mathrm{rel}}(d;t,t+h).
$$

The primary value uses $h=2$ s and is interpreted as the mean amount by which the three nearby defenders moved differently from their respective contemporaneous defending-unit references. Individual paths remain descriptive output.

The mean is frozen. Median, maximum, minimum, strongest responder, future-nearest defender, outcome-weighted assignment, and any future-informed aggregation are prohibited.

The nonlocal outcome uses the identical mean over $F_3(a,t)$.

## 11. Strictly prior defensive context

The primary baseline is separated from the attacker exposure:

$$
B_{\mathrm{local}}(a,t)=
\frac{1}{3}\sum_{d\in L_3(a,t)}P_{\mathrm{rel}}(d;t-4,t-2).
$$

This strictly earlier window is selected prospectively because Phase 5A showed recent focal movement dominates prediction, while using $[t-2,t]$ would be concurrent with the attacker exposure and could adjust away developing movement already associated with that exposure.

One additional sparse control is retained:

$$
C_D(t)=\sum_{i:t-4<s_i\le t-2}
\|\mathbf c_D(s_i)-\mathbf c_D(s_{i-1})\|_2,
$$

the full defending-outfield centroid path over the same strictly prior interval. It represents recent movement of the defensive unit. No ball term, spatial-position term, opponent feature beyond the focal attacker exposure, or significance-selected covariate enters the primary model. Ball and spatial additions were smaller in Phase 5A, and the first bridge prioritizes a sparse falsifiable specification.

## 12. Support and open-play eligibility

An observation is eligible only if:

1. attacker, all ten defending outfield players, and every raw sample required by smoothing and geometry have valid canonical support for the complete primary span $[t-4,t+2]$;
2. all identities remain the same complete outfield sets across that span;
3. the attacker has a valid frozen 2 s continuous observation ending exactly at $t$;
4. every local/nonlocal baseline and primary outcome is computable without interpolation, partial windows, period crossing, or support crossing;
5. $t$ and every required endpoint match canonical frames exactly under the established tolerance;
6. an event-established possession team is known at $t$ and identifies the candidate attacker's team;
7. no restart event occurs in $[t-4,t+2)$, using the frozen Phase 4 event rule: event type `SET PIECE` or `BALL OUT`, or subtype `CORNER KICK`, `FREE KICK`, `GOAL KICK`, `KICK OFF`, `THROW IN`, `OFFSIDE`, or `END HALF`; and
8. no period boundary occurs inside $[t-4,t+2]$.

For the four-second response sensitivity only, complete support and the global restart/ball-out exclusion extend through $t+4$; sensitivity eligibility is reported separately and may not remove rows from the primary sample.

Possession continuity is **not** required before or after $t$. Requiring the same possession through the response would condition on a post-exposure variable potentially affected by play. Pass completion, reception, shot, chance creation, possession retention/loss, defensive success, and later event outcomes are never eligibility conditions. Ball coordinates are not required because the primary model contains no ball measurement.

Global stoppage exclusions provide interpretable open-play support; they do not select tactically successful observations.

## 13. Dependence and uncertainty

Primary coefficients are ordinary least-squares descriptive association estimates in raw metres. Main uncertainty uses a deterministic **block bootstrap at the match-period-time level**:

- nonoverlapping 60 s blocks anchored at each period origin;
- retain all simultaneous attackers and all linked defenders within a sampled block;
- sample blocks with replacement within each match-period until the original block count is reached;
- 2,000 replicates with seed `20260831`;
- percentile 95% intervals; and
- no frame-, player-, or row-level independent bootstrap.

Report Game 1 and Game 2 coefficients separately and a pooled descriptive estimate with match indicator. With only two Metrica matches, match-level asymptotics and p-value-heavy claims are prohibited. Bootstrap intervals describe stability under the frozen block scheme; they do not establish causality.

## 14. Primary estimand and model

Fit separately by match:

$$
Y_{\mathrm{local}}(a,t;2)=
\beta_0+\beta_1X_a(t)+\beta_2B_{\mathrm{local}}(a,t)
+\beta_3C_D(t)+\varepsilon.
$$

For the pooled descriptive fit, add one binary match indicator and no interactions. No standardization replaces raw units.

The primary estimand is $\beta_1$: the change in expected subsequent mean local focal-relative path, in metres, associated with one additional metre of attacker path during the preceding two seconds, conditional on the frozen strictly prior defensive context. It is an observational association coefficient—not a causal effect, reaction probability, responsibility estimate, or attacker value.

No covariate selection, regularization, machine learning, spline, tree, interaction search, weighting, or alternative estimator is permitted.

## 15. Secondary descriptive quantities and nonlinearity check

Report signed attacker x/y displacement, straightness where valid, individual local-defender outcomes, the nearest-defender outcome, and one-/four-second response sensitivities separately. None changes the primary classification.

For one descriptive figure, compute quartile boundaries of Game 1 attacker `path_length_m` on the eligible primary bridge sample, freeze those four bins after the complete protocol-bound Game 1 execution, and apply the same metre cut points unchanged to Game 2. Show outcome distributions and model-adjusted descriptive means without converting bins into tactical categories. The continuous model remains primary. No additional binning is allowed.

## 16. Negative and temporal controls

### 16.1 Nonlocal control

Refit the exact primary specification with $Y_{\mathrm{nonlocal}}$, the mean focal-relative response of $F_3(a,t)$. Use its own strictly prior farthest-three baseline and the same $C_D(t)$. Compare the attacker-path coefficients as

$$
\Delta\beta_{\mathrm{local-nonlocal}}
=\beta_{1,\mathrm{local}}-\beta_{1,\mathrm{nonlocal}}.
$$

This asks whether association is spatially local under the frozen geometry; it does not prove assignment.

### 16.2 Reverse-time placebo

Using the same endpoint and linkage at $t$, define earlier defensive geometry as $P_{\mathrm{rel}}(d;t-2,t)$ and future attacker path as $P_a(t+2;2\ \mathrm{s})$ over $[t,t+2]$. Fit the same covariates from $[t-4,t-2]$. The placebo coefficient tests whether a nominally future attacker path predicts earlier local defensive movement. Compare

$$
\Delta\beta_{\mathrm{primary-placebo}}
=\beta_{1,\mathrm{primary}}-\beta_{1,\mathrm{placebo}}.
$$

The placebo is diagnostic only. Passing it does not prove causal direction; failing it may indicate shared temporal movement or inadequate ordering. No alternative offset may be inspected.

## 17. Extreme-exposure and influence diagnostic

To test whether a tiny number of large attacker paths dominate the coefficient, repeat the primary and control fits after excluding observations above the **Game 1 eligible-sample 99th percentile** of attacker path. Freeze that numerical cut once from Game 1 and apply it unchanged to Game 2. This is a prespecified diagnostic, not a cleaned primary result. The full sample remains authoritative.

Report ordinary regression influence summaries without deleting other rows. No winsorization, clipping, robust-regression substitution, or post-result threshold is allowed.

## 18. Primary figures

1. **Geometry schematic:** attacker trail over $[t-2,t]$, the three local defenders selected at $t$, defending-unit context, and subsequent defender-relative trails. Use synthetic geometry or a deterministic Game 1 observation selected without outcome magnitude. No tactical label.
2. **Primary relationship:** attacker 2 s path versus subsequent mean local focal-relative path, with raw distribution and the frozen adjusted linear trend/blocked uncertainty.
3. **Control comparison:** local, farthest-three nonlocal, and reverse-time coefficients with uncertainty, plus a football-readable pitch key.

If a real example is shown, select the first fully eligible Game 1 observation in chronological `(period, t, attacker player_key)` order. It has no classification role. Use `mplsoccer` where appropriate.

## 19. Mechanical interpretation criteria

Hard QC must first pass: exact protocol/support hashes, unique observation IDs, complete eligible geometry, no period/support crossing, valid local/nonlocal disjoint sets, no future-informed linkage, finite model inputs/outputs, geometric invariants, deterministic reproduction, and unchanged frozen component implementations. A hard scientific failure classifies **C**.

Subject to hard QC, classify the initial bridge:

### A — supported first geometric bridge

All must hold:

1. $\beta_{1,\mathrm{local}}>0$ separately in Game 1 and Game 2, and the pooled 95% blocked-bootstrap interval excludes zero on the positive side;
2. $\Delta\beta_{\mathrm{local-nonlocal}}>0$ separately in both matches, and its pooled 95% interval excludes zero on the positive side;
3. $\Delta\beta_{\mathrm{primary-placebo}}>0$ separately in both matches, and its pooled 95% interval excludes zero on the positive side;
4. after the prespecified top-1% diagnostic exclusion, the primary coefficient remains positive in both matches and at least 50% of its full-sample magnitude in each;
5. the 1 s and 4 s response sensitivities do not both reverse the primary coefficient's sign in either match; and
6. all support, invariance, and deterministic checks pass.

These are prospective association/robustness gates, not football-effect thresholds.

### B — mixed or negative association evidence

Hard QC passes and the representation remains usable, but one or more A criteria fail. Examples include adjustment removing the association, local and nonlocal coefficients being similar, a comparable reverse-time pattern, match-specific signs, or extreme observations dominating. Preserve B without tuning.

### C — bridge implementation/measurement failure

Support cannot be consumed faithfully, prerequisite geometry changes, hard QC/invariance/deterministic reproduction fails, future information enters exposure/linkage, or substantial eligible geometry is mathematically unusable. Do not rescue C.

No coefficient-size threshold beyond sign, no p-value, and no Game-1-tuned gate may be introduced.

## 20. Claim ladder

The maximum A claim is:

> **Greater observed attacker movement is associated with greater subsequent local defensive movement relative to the defensive unit, beyond prespecified strictly prior defensive-motion context.**

Even A would not establish that the attacker caused movement, a defender marked or was responsible for that attacker, a tactical drag/pin/track/cover/handoff occurred, the defense was disrupted, or the attacker created gravity, quality, or value.

## 21. External-replication boundary

V1 is a within-provider Metrica bridge. IDSSE has validated the defensive primitive, but continuous attacker v1 has not been validated from native 10 Hz or across providers. The Metrica seven-frame 25 Hz smoother cannot be silently ported. External bridge replication requires a separately frozen attacker-representation compatibility protocol governing native frequency, smoothing support, coordinates, time, and missingness before any external bridge association is inspected.

## 22. Ambiguity audit

| Design item | Status | Resolution |
|---|---|---|
| Defender linkage | **FROZEN** | Three nearest defending outfield players at $t$; distance then canonical ID; membership fixed. |
| $K$ | **FROZEN** | $K=3$; no optimization or alternate $K$. |
| Local aggregation | **FROZEN** | Arithmetic mean of three individual focal-relative paths. |
| Temporal windows | **FROZEN** | Context $[t-4,t-2]$; exposure $[t-2,t]$; response 2 s primary, 1/4 s sensitivity. |
| Baseline timing | **FROZEN** | Strictly before exposure; concurrent $[t-2,t]$ defensive baseline prohibited as primary. |
| Possession conditioning | **FROZEN** | Possession team known at $t$ only; continuity through response not required. |
| Open-play/support conditioning | **FROZEN** | Complete canonical player support and global restart/ball-out exclusion; no event outcome selection. |
| Simultaneous attackers | **FROZEN** | Separate observations retained together in time blocks. |
| Repeated observations | **FROZEN** | Four-second period-anchored cadence; dense grid inferential use prohibited. |
| Shared defenders/context | **FROZEN** | Preserved within 60 s match-period bootstrap blocks. |
| Primary regression | **FROZEN** | Raw-metre OLS with attacker path, strict-prior local path, and strict-prior centroid path. |
| Nonlocal control | **FROZEN** | Three farthest defenders at $t$, matched aggregation and baseline. |
| Placebo timing | **FROZEN** | Future attacker $[t,t+2]$ versus earlier defender $[t-2,t]$; no offset search. |
| Dataset role | **FROZEN** | Game 1 development; Game 2 conditionally bridge-held-out; Game 3 untouched. |
| Cross-provider portability | **DEFERRED** | Requires a separate native-frequency attacker compatibility protocol. |
| Tactical assignment inference | **PROHIBITED** | Proximity is geometry only. |
| Causal language and attacker value | **PROHIBITED** | No bridge classification authorizes causation, gravity, or value. |

No item is blocking.

## 23. Execution authorization

The design is **A — BRIDGE PROTOCOL READY**. A later pass may implement synthetic fixtures and then execute Game 1 under this exact protocol. It may proceed to Game 2 only under the sequence in Section 5. This document authorizes no bridge computation in the protocol-design pass and does not authorize Game 3 or external-provider bridge access.
