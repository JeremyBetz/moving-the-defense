# Local Defensive Response Form Protocol v1.0

**Status:** **FROZEN / RESULTS UNOBSERVED**

**Freeze date:** 2026-09-01

**Starting commit:** `945f5921d6609f4246127419bba08c3bacd863a8`

**Scientific boundary:** geometric form of the already-established local observational response; no tactical label, assignment, intention, influence, or causation.

## 1. Football and measurement questions

Football question:

> When an attacker moves and nearby defenders subsequently move differently from the rest of the defensive unit, what geometric form does that movement take?

Primary measurement question:

> Across the already-fixed nearest defender region, does subsequent focal-relative defender movement contain a reproducible signed component along the preceding attacker's movement direction beyond the middle defender region and the frozen temporal control?

This phase does not retest whether a local response magnitude exists. **FINAL FOOTPRINT A is closed.** It preserves the validated focal-relative path and decomposes endpoint geometry alongside it.

## 2. Prior-art boundary

Attacker–defender relative phase, vector-coded dyadic coordination, velocity alignment, marking/proximity networks, pressure/separation models, two-dimensional defender-velocity prediction, pursuit-evasion models, and player-to-team coordination are established methodological neighbors. The [targeted provenance audit](../local_defensive_response_form_methodology.md) records their settings, temporal/spatial scales, transferable observables, and prohibited semantic transfers.

V1 does not claim invention of projections, radial coordinates, relative velocity, or collective-relative movement. It does not import “tracking,” “marking,” “pressure,” “anticipation,” “chasing,” or mechanistic pursuit semantics.

> **Football concept ≠ tracking measurement ≠ theoretical mechanism.**

## 3. Inherited sample, rank, and timing

Inherit the frozen spatial-footprint observation IDs, four-second endpoint cadence, attacking/defending team state, open-play exclusion, exact support, centred-seven-frame coordinates, complete ten-defender outfield set, goalkeeper exclusion, leave-one-out centroids, rank tie rule, simultaneous-attacker handling, and missingness/no-interpolation policy unchanged.

For anchor $t$:

- strictly prior defensive context: $[t-4,t-2]$;
- attacker exposure: $[t-2,t]$;
- primary defender response: $[t,t+2]$;
- sensitivity responses: $[t,t+1]$ and $[t,t+4]$;
- gap: exactly zero seconds; and
- ranks fixed once at $t$: near D1–D3, middle D4–D7, far D8–D10.

There is no onset detector, reaction-time interpretation, lag search, or post-result offset. The zero-gap, nonoverlapping exposure/response architecture is inherited because it already passed the bridge and footprint controls and because changing it would confound geometric form with a new timing construct.

## 4. Core positions and displacement

Let attacker, focal defender, and leave-one-out defending-outfield centroid positions be

$$
\mathbf a(s),\qquad \mathbf d(s),\qquad \mathbf c_{-d}(s),
$$

and retain

$$
\mathbf r_d(s)=\mathbf d(s)-\mathbf c_{-d}(s).
$$

The validated response magnitude remains the focal-relative path

$$
P_d=\sum_j\|\mathbf r_d(s_j)-\mathbf r_d(s_{j-1})\|_2
$$

over $[t,t+2]$. The new endpoint response vector is

$$
\Delta\mathbf r_d=\mathbf r_d(t+2)-\mathbf r_d(t)
=\Delta\mathbf d-\Delta\mathbf c_{-d}.
$$

Always retain $P_d$, $\|\Delta\mathbf r_d\|_2$, and $\Delta\mathbf r_d$ separately. Large path does not imply large net displacement or a large signed projection.

## 5. Numerical degeneracy policy

All vectors use canonical metres and Float64. Define one numerical—not empirical—threshold:

$$
\epsilon_v=64\,\epsilon_{64}\sqrt{105^2+68^2}
=1.7777205579859071\times10^{-12}\ \mathrm m.
$$

The scale is 64 Float64 ulps of the canonical pitch diagonal. It is not a football-motion threshold.

- If $\|\Delta\mathbf a\|_2\le\epsilon_v$, the attacker-direction axis, parallel/orthogonal projections, and cosine are undefined. Remove the complete ten-defender anchor from the primary directional sample; retain it in the support ledger and in eligible radial/path descriptions.
- A zero focal-relative response is a valid zero parallel/orthogonal/radial projection when its required axis exists. Its cosine alone is undefined when $\|\Delta\mathbf r_d\|_2\le\epsilon_v$.
- If attacker and defender positions at $t$ are within $\epsilon_v$, radial projection is undefined for that defender row; do not jitter, impute, substitute rank direction, or delete other views.
- Primary directional eligibility must retain at least 80% of inherited footprint anchors. This coverage gate was frozen before response-form inspection and prevents an axis-defined construct from silently describing a small selected subset.

## 6. Primary attacker-direction decomposition

Define the exposure displacement and unit axis:

$$
\Delta\mathbf a=\mathbf a(t)-\mathbf a(t-2),\qquad
\widehat{\mathbf u}_a=\frac{\Delta\mathbf a}{\|\Delta\mathbf a\|_2}.
$$

The primary signed response is

$$
Z^{\parallel}_{id}=\Delta\mathbf r_d\cdot\widehat{\mathbf u}_a.
$$

Positive means the defender's unit-relative endpoint displacement contains a component in the attacker's preceding displacement direction; negative means the opposite. It is not tracking or following.

The signed left-normal component is descriptive:

$$
Z^{\perp}_{id}=\Delta\mathbf r_d\cdot
[-\widehat u_{a,y},\widehat u_{a,x}].
$$

It changes sign under mirror reflection by construction; its magnitude and all rotation-preserving identities must remain invariant.

## 7. Radial and alignment descriptions

Freeze the radial axis at response start $t$, using no subsequent outcome geometry:

$$
\widehat{\mathbf u}_{ad}(t)=
\frac{\mathbf a(t)-\mathbf d(t)}{\|\mathbf a(t)-\mathbf d(t)\|_2},\qquad
Z^{rad}_{id}=\Delta\mathbf r_d\cdot\widehat{\mathbf u}_{ad}(t).
$$

Positive is unit-relative movement toward the attacker's response-start position; negative is away. Do not call it closing or engaging.

Where both norms exceed $\epsilon_v$, report the descriptive alignment

$$
A_{id}=\frac{\Delta\mathbf r_d\cdot\Delta\mathbf a}
{\|\Delta\mathbf r_d\|_2\|\Delta\mathbf a\|_2}.
$$

Cosine is bounded and scale-free but unstable for negligible displacement; it cannot classify v1.

## 8. Absolute movement and unit movement

Retain separately over the response interval:

- defender absolute vector and magnitude, $\Delta\mathbf d$ and $\|\Delta\mathbf d\|_2$;
- leave-one-out centroid vector and magnitude, $\Delta\mathbf c_{-d}$ and $\|\Delta\mathbf c_{-d}\|_2$; and
- focal-relative vector and magnitude, $\Delta\mathbf r_d$ and $\|\Delta\mathbf r_d\|_2$.

The exact identity $\Delta\mathbf r_d=\Delta\mathbf d-\Delta\mathbf c_{-d}$ must hold within $10^{-12}$ m. These separate vectors can describe a stationary defender while the unit shifts, a defender/unit shared translation, or a defender departing in another direction. V1 creates no hold/pin category and no threshold between these geometries.

Local teammate compensation is deferred. Defining it would require a new teammate-selection or network rule whose validity cannot be borrowed from proximity alone.

## 9. Primary model and estimand

Let $X_i$ be the already-frozen attacker exposure path over $[t-2,t]$. Let $Q^{\parallel}_{ik}$ be defender $D_k$'s focal-relative endpoint displacement over $[t-4,t-2]$, projected onto the same exposure axis $\widehat{\mathbf u}_a$. Let $C_i$ be the inherited defending-outfield-centroid path over $[t-4,t-2]$.

Fit one stacked raw-metre OLS model:

$$
Z^{\parallel}_{ik}=\sum_{r=1}^{10}I(k=r)
(\alpha_r+\beta^{\parallel}_rX_i+\gamma_rQ^{\parallel}_{ik}+\eta_rC_i)+\varepsilon_{ik}.
$$

The primary coefficient vector is $\boldsymbol\beta^{\parallel}$. Define

$$
N_{\parallel}=\frac{\beta^{\parallel}_1+\beta^{\parallel}_2+\beta^{\parallel}_3}{3},\qquad
M_{\parallel}=\frac{\beta^{\parallel}_4+\cdots+\beta^{\parallel}_7}{4},
$$

and the sole primary spatial contrast

$$
\Delta^{\parallel}_{NM}=N_{\parallel}-M_{\parallel}.
$$

Use a two-sided 97.5% percentile interval, preserving the footprint's conservative adjacent-region family convention even though v1 has only one classifying form contrast. D8–D10, $F_{\parallel}$, and middle-minus-far are descriptive; far is not required to classify because Final Footprint A already located the replicated magnitude distinction at near versus middle.

No standardized outcome, absolute projection, squared projection, composite score, circular model, phase category, interaction search, or alternative rank cut is permitted.

## 10. Temporal control

Use exactly one classifying temporal misalignment control. At the same anchor and fixed ranks:

- use future attacker displacement/path on $[t,t+2]$ to define the placebo attacker axis/exposure;
- use earlier focal-relative defender displacement on $[t-2,t]$ as the placebo outcome;
- retain context from $[t-4,t-2]$; and
- require complete axis/support validity for both primary and placebo, forming one fixed common sample.

Fit the same stacked model and calculate placebo $\Delta^{\parallel}_{NM,pl}$. On the common sample, refit the primary and calculate the paired bootstrap difference

$$
\Delta^{\parallel}_{NM}-\Delta^{\parallel}_{NM,pl}.
$$

Its 97.5% interval is classifying. No other offset, random direction, attacker relabel, or phase shuffle is allowed. The control can reveal temporal symmetry/shared motion but cannot prove reaction or causation.

## 11. Secondary outputs

Report separately, without classification:

1. focal-relative path $P_d$ and net magnitude $\|\Delta\mathbf r_d\|_2$ by D1–D10 and region;
2. all $\beta^{\parallel}_k$, $N_{\parallel}$, $M_{\parallel}$, and descriptive $F_{\parallel}$;
3. signed/magnitude distributions for parallel and orthogonal projections;
4. radial projections by rank and region using the response-start axis;
5. alignment cosine where defined;
6. absolute defender, centroid, and focal-relative endpoint vectors/magnitudes; and
7. axis-degeneracy and radial-degeneracy ledgers.

No output combines path, projection, radial, orthogonal, or cosine into one score.

## 12. Bootstrap and robustness

Inherit the 60-second match-period block bootstrap: 2,000 replicates, minimum 1,900 valid, simultaneous attackers and all ten defender rows kept together, terminal partial blocks retained, and empirical percentile intervals. Use `SeedSequence(20260831).spawn(9)` with child 6 for Game 1, 7 for Game 2, and 8 for pooled execution. Reinitialize the applicable child for each separately governed sample family.

Robustness is frozen as:

- remove complete anchors above the inherited attacker-path threshold 12.198443079831405 m; a qualifying full-sample contrast must retain sign and at least 50% magnitude;
- refit 1 s and 4 s response horizons with the same exposure axis; they may not both reverse the 2 s sign; and
- report the response-start radial-axis alternative only as a separate secondary view—never as a sensitivity that can rescue the parallel primary.

## 13. Development and final governance

- **Game 1:** development for this new estimand. Prior Game 1 use is extensive.
- **Game 2:** not untouched globally; it is only *unobserved for this response-form estimand*. It may open only after a coherent Game 1 result and must then run unchanged as internal replication.
- **Game 3:** untouched, reserved for a later more consequential validation, and prohibited in v1.

Game 1 receives one of:

- **GAME 1 RESPONSE FORM DEVELOPMENT COHERENT:** hard QC/reproduction and bootstrap validity pass; primary-axis retention is at least 80%; $\Delta^{\parallel}_{NM}$ and the paired primary-minus-placebo contrast each have 97.5% intervals strictly excluding zero in the same direction; trim retains sign and at least 50% magnitude; and 1/4 s estimates are not both opposite the 2 s sign.
- **GAME 1 RESPONSE FORM DEVELOPMENT MIXED:** execution is valid/reproducible but any scientific-pattern or coverage condition fails. Stop; Game 2 remains unopened for this estimand.
- **GAME 1 RESPONSE FORM DEVELOPMENT INVALID:** any frozen-hash, support, leakage, identity, rank, axis, model, bootstrap, invariance, or deterministic-reproduction failure. Stop for a versioned prospective repair.

If and only if Game 1 is coherent, execute unchanged Game 2 and pooled analyses. Game 2 receives no standalone status. Then assign exactly one:

- **FINAL RESPONSE FORM A:** Game 1, Game 2, and pooled executions are valid/reproducible with at least 80% primary-axis retention; primary $\Delta^{\parallel}_{NM}$ intervals strictly exclude zero with the same sign in Game 1, Game 2, and pooled; paired primary-minus-placebo intervals strictly exclude zero with that same sign in all three; and pooled trim/horizon robustness passes.
- **FINAL RESPONSE FORM B:** all authorized executions are valid/reproducible, but one or more Final A scientific conditions fail.
- **FINAL RESPONSE FORM C:** Game 2 or pooled execution is scientifically invalid under hard rules.

No final status can be assigned before the authorized Game 2 and pooled sequence. No radial, orthogonal, cosine, far-region, visual, or post-hoc result can rescue A.

## 14. Falsification conditions

The primary idea is unhelpful or mixed if signed parallel structure is near zero/overlapping across near and middle, the temporal control reproduces it, signs disagree across matches, trimming/horizons reverse it, attacker-axis attrition exceeds the coverage gate, or the result cannot reproduce. Descriptively record whether projection magnitude merely scales with attacker displacement/path and whether radial conclusions depend on the frozen reference-time choice. Do not add an alternative axis after observing failure.

## 15. Hard QC

Future execution must verify inherited hashes and IDs; exact ten-player/rank vectors; goalkeeper/focal exclusion; support and temporal order; no interpolation; axis construction from exposure only; response-start radial geometry; exact endpoint-vector identity; numerical missingness rules; region identities; 80% coverage; grouped bootstrap; minimum valid replicates; translation/rotation/mirror behavior; non-tie player-ID relabeling; no Game 3 access; no tactical/outcome labels; and complete deterministic reproduction.

## 16. Claim boundaries

If successful, permitted terms are **attacker-direction-aligned defender-relative movement**, **attacker-radial defender-relative movement**, **orthogonal defender-relative movement**, **directional structure of local defensive response**, and **local geometric response form**.

Prohibited interpretations include tracking, following, marking, pinning, dragging, covering, handoff, assignment, responsibility, attention, tactical intent, reaction, causation, influence, space creation, gravity, and off-ball value.

## 17. Figures frozen before results

1. **Football-first vector cartoon:** synthetic pitch with attacker exposure arrow, defensive-unit shift arrow, absolute focal-defender arrow, resulting focal-relative arrow, parallel component, and orthogonal component. Caption must say geometry only.
2. **Result template:** fixed panels for D1–D10 parallel coefficients with intervals, near/middle/far regional estimates, the primary near-minus-middle contrast, and its temporal-control comparison. Axis order, colors, and panel inclusion cannot change based on results. Radial and magnitude views are separate secondary panels.

Use `mplsoccer` when available for pitch presentation; plotting choice cannot transform coordinates or estimates.

## 18. Freeze and execution prohibition

Authoritative configuration: `config/local_defensive_response_form_v1.json`. Synthetic definitions: `src/local_defensive_response_form_v1.py`. No provider loader or match execution entrypoint exists in this freeze pass. No Game 1/Game 2 response-form sample, coefficient, distribution, bootstrap, or figure may be computed until a separate authorized execution.

Protocol and configuration SHA-256 values are recorded in the research log and documentation index after final QC. Any substantive amendment requires a versioned, pre-result erratum.
