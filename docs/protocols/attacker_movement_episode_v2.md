# Attacker Movement Episode v2 — Game 1 Development Protocol

**Status:** frozen prospectively before v2 Game 1 execution

**Freeze date:** 2026-09-01

**Starting commit:** `515b1a95c8fd5a4d0b5aadc9978597d71e023d52`

**Execution tier:** Tier 1

The machine-readable source of truth is [`config/attacker_movement_episode_v2.json`](../../config/attacker_movement_episode_v2.json).

## 1. Question and construct

Can an attacker's own two-dimensional trajectory be divided into finite, interpretable movement episodes without using defenders, ball outcomes, or downstream tactical outcomes, while improving the closed speed-valley fragmentation/merging trade-off?

An **attacker movement episode** is a finite interval describing a coherent portion of one player's own observed 2D movement trajectory. It is not a tactical run, decoy, overlap, underlap, drag, pin, threat, influence, defensive response, success, value, intent, decision, reaction, or responsibility.

## 2. Firewall and closed inheritance

Game 1 only. Use the closed attacker-only sample, 105 × 68 m conversion, 25 Hz clock, centred seven-frame position mean, consecutive-position velocity, no interpolation, period/support boundaries, and inherited global `BALL OUT`/`SET PIECE` exclusions. Use all supported outfield identities and no possession filter. Do not read any defender-derived, bridge, footprint, response-form, deformation, Game 2, Game 3, or IDSSE artifact during execution.

Candidate A must reproduce the historical 38,651 speed-valley episodes and saved diagnostics exactly within $10^{-9}$ numerical tolerance. The closed prominence ladder is historical context only: no prominence value is reused, extended, or tuned.

The confirmed Home 10 period-1 discontinuity at raw frames 2911–2945 is a hard support break for v2. Candidate B may not create an episode whose required smoothed support crosses it. Candidate A remains the exact historical comparator and separately reports the corresponding support sensitivity; this preserves the historical record while preventing v2 from treating an accepted discontinuity as movement.

## 3. Direction and episode geometry

For consecutive velocity vectors,

$$
\theta_k=\arccos\left[\operatorname{clip}\left(
\frac{\mathbf v_k\cdot\mathbf v_{k+1}}
{\|\mathbf v_k\|\|\mathbf v_{k+1}\|},-1,1\right)\right].
$$

The division floor is $10^{-9}$ m/s; a vector at or below it has undefined heading and contributes no angle. This is a numerical guard, not a football threshold. For reported/candidate turning, inherit the historical reliability rule requiring both velocity magnitudes to be at least 0.50 m/s. Episode path $L$, displacement $D$, directness $Q=D/L$ for $L>10^{-9}$ m, and cumulative absolute turning $T=\sum\theta_k$ are retained separately. Low $Q$ is descriptive, not automatically invalid.

## 4. Candidate A — closed baseline

Reproduce exactly: plateau-aware speed minima; plateau midpoint; chronological 1.0 s consolidation retaining the lower-speed candidate (earlier exact tie); consecutive retained valleys as episodes; 1.0 s minimum; no speed inclusion threshold.

## 5. Candidate B — direction-aware boundary consolidation

Candidate B is one fixed algorithm:

1. Construct Candidate A retained valleys.
2. Restrict v2 coverage to between the first and last retained baseline valley in each eligible block.
3. At every possible internal frame, form a preceding and following 0.48 s mean-velocity vector from 12 consecutive 25 Hz steps on each side. A direction candidate requires both vector magnitudes to be at least 0.50 m/s and their angle to be at least 45°.
4. Collapse each maximal consecutive run of qualifying frames to the frame with greatest angle; use the earlier frame on an exact tie. Consolidate direction candidates within 1.0 s by the same greatest-angle/earlier-tie rule.
5. Combine direction candidates with historical valley boundaries. When candidates lie within 1.0 s, retain a direction candidate over a speed valley; between direction candidates retain the greater angle/earlier tie; between speed valleys retain the historical lower-speed/earlier-tie choice.
6. Direction candidates are protected. Repeatedly scan remaining unprotected speed-valley boundaries chronologically. Remove a boundary only when the union between its immediately adjacent retained boundaries has $Q\ge0.95$ and $T<45°$. Repeat to a fixed point.
7. Consecutive final boundaries define episodes. Require at least 1.0 s and reject an episode crossing the frozen Home 10 support break.

The 45° convention has football change-of-direction precedent (Kai et al., 2021; Reilly et al., 2021). The one-second local summary follows the time scale used in football direction/velocity descriptions. The $Q\ge0.95$, $T<45°$ redundant-boundary idea was declared before this experiment in the closed directional-segmentation protocol. These precedents motivate a development rule; they do not validate universal episode semantics.

## 6. Candidate C — omitted prospectively

No new generic change-point comparator will run. The project already froze and executed the relevant standard comparator: penalized two-dimensional $[v_x,v_y]$ PELT. It produced overwhelming minimum-duration fragmentation and frequency instability. Running a second penalty choice would add an arbitrary, outcome-informed comparator rather than answer the present bounded question. The closed result remains literature/method precedent only.

## 7. Diagnostics and criteria

Historical diagnostics remain exact:

- fragmentation: duration $\le1.5$ s, path $\le1$ m, displacement $\le0.5$ m; composite is their union;
- merging/direction: duration $\ge8$ s, $Q\le0.5$, or path $\ge3$ m and $T\ge180°$; composite is their union;
- lower-speed coverage: peak speed $<5.5$ m/s and displacement $\ge3$ m divided by all episodes.

New descriptive directional summaries report $Q$ and $T$. The same frozen historical caps classify v2:

- fragmentation at most 33.776% (at least 20% relative reduction from 42.22%);
- merging/direction at most 3.97%;
- lower-speed coverage at least 36.8955525083439%;
- exact baseline reproduction and all support/QC checks.

The frozen visual checks are objective and secondary to the numerical gates:

- Away 24, 380.20–385.04 s: no added direction boundary inside the historical episode, and one v2 episode contains that interval;
- Home 6, 95.32–146.48 s: at least one direction boundary lies inside the interval and no v2 episode spans the complete interval;
- Home 10, 116.44–117.68 s: no v2 episode crosses the frozen invalid support interval;
- eight additional chronological cases are fixed in the configuration.

Status logic:

- **COHERENT:** valid; all three numerical gates pass; all three fixed-case checks pass; no tuning.
- **MIXED:** valid and fragmentation improves materially, but a direction/merging, coverage, or fixed-case requirement fails; or the directional rule creates another material failure.
- **NEGATIVE:** valid but fragmentation does not improve materially or the overall fragmentation/merging trade-off is materially worse than baseline.
- **INVALID:** support, continuity, implementation, or construct failure only.

## 8. Outputs, interpretation, and stopping rule

Report candidate counts and duration/path/displacement/peak-speed/$Q$/$T$ distributions, historical diagnostics, lower-speed coverage, fixed visual cases, baseline equality, support handling, and exact status. Visual appeal cannot override a gate. No tactical labels are permitted.

After Game 1, stop. Do not inspect Game 2 or Game 3, calculate defensive geometry, tune constants, add cleanup, or begin an attacker–defender bridge.

## 9. Method provenance

- Llana et al. (2022): smoothed speed and valley-to-valley football effort sections.
- Kai et al. (2021), *PLOS ONE* 16:e0251292: football change-of-direction geometry and timing.
- Reilly et al. (2021): football tracking classification of changes exceeding 45°.
- Edelhoff, Signer, and Balkenhol (2016): turning angle, heading, speed, and path geometry as trajectory-segmentation signals.

These are precedents, not claims that Candidate B is established or novel.
