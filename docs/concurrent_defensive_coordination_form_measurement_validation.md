# Concurrent Defensive Coordination Form v1 — measurement validation

**Status: design-stage measurement validation; no match-level defensive-response result computed.**

## Football question

When an attacker changes direction during a movement, does a nearby defender's movement relative to the rest of the defensive unit change in the same local direction? This asks about concurrent tracking geometry. It does not identify following, marking, responsibility, reaction, influence, or tactical success.

## Why the first formula was superseded

The first design used displacement increments:

$$
\operatorname{AARD}^{\mathrm{disp}}_d=
\frac{\sum_k \Delta\mathbf r_{d,k}\cdot\Delta\mathbf A_k}
{\sum_k\lVert\Delta\mathbf A_k\rVert_2}.
$$

For constant continuous velocities sampled every $\Delta t$, each numerator term is proportional to $\Delta t^2$, while each denominator term is proportional to $\Delta t$. The ratio is therefore proportional to $\Delta t$. The same underlying constant aligned trajectory produced 0.048 m at 10 Hz and 0.0192 m at 25 Hz, exactly the expected factor of 2.5. Opposite, smooth-speed, and curved fixtures showed the same sampling dependence. This displacement form is retained in code only as an explicit audit comparator; it is not the future primary.

## Candidate velocity measurement

Let the attacker's position be $\mathbf A(t)$, focal defender position be $\mathbf x_d(t)$, and the centroid of the other nine defending outfield players be $\mathbf c_{-d}(t)$. Define

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),\qquad
\Delta\mathbf A_k=\mathbf A_{k+1}-\mathbf A_k,\qquad
\Delta\mathbf r_{d,k}=\mathbf r_{d,k+1}-\mathbf r_{d,k}.
$$

Let interval velocities be the exact secants $\mathbf v_{A,k}=\Delta\mathbf A_k/\Delta t_k$ and $\mathbf v_{r_d,k}=\Delta\mathbf r_{d,k}/\Delta t_k$. For an interval with nonzero attacker path, the candidate **attacker-aligned relative velocity** is

$$
\operatorname{AARD}^{\mathrm{vel}}_d=
\frac{\sum_k (\mathbf v_{r_d,k}\cdot\mathbf v_{A,k})\Delta t_k}
{\sum_k\lVert\mathbf v_{A,k}\rVert_2\Delta t_k}.
$$

This is the discrete approximation to the corresponding continuous-time integral. Its unit is metres per second. It is an attacker-path-weighted mean defender-relative velocity projected onto the attacker's local movement direction. Positive means the relative velocity tends to point with the attacker's local velocity; negative means it tends to oppose it; near zero may reflect perpendicular movement, no relative movement, cancellation, or weak coordination. None of those signs has tactical semantics by itself.

The **absolute aligned comparator** replaces $\mathbf v_{r_d,k}$ with the defender's absolute pitch velocity. It exposes alignment caused by a shared defensive shift that the leave-one-out reference removes.

The secondary cross-trajectory magnitude is

$$
\operatorname{CROSS}^{\mathrm{vel}}_d=
\frac{\sum_k\left|v_{r_d,k,x}v_{A,k,y}-
v_{r_d,k,y}v_{A,k,x}\right|\Delta t_k}
{\sum_k\lVert\mathbf v_{A,k}\rVert_2\Delta t_k}.
$$

It is nonnegative and measured in metres per second. It describes relative velocity normal to the attacker's local path; it cannot rescue an unsupported primary aligned result. A signed left/right interpretation is not introduced.

Stationary attacker increments contribute zero to both numerator and denominator and therefore receive no artificial direction. If total attacker path is at or below the documented numerical-zero tolerance, all aligned/cross quantities are undefined. Missing coordinates invalidate required support; they are not interpolated.

## Preprocessing comparison

Historical project measurements use a centred seven-frame arithmetic mean. Its physical support is 0.28 seconds at 25 Hz but 0.70 seconds at 10 Hz, so it is not provider-time-equivalent.

The draft primary candidate is a fourth-order zero-phase Butterworth low-pass at 1.0 Hz, applied separately to x/y over a complete continuous support block before analysis windows are extracted. SciPy's `sosfiltfilt` odd-reflection edge treatment is explicit. A block too short for filtering is invalid; no fabricated padding or coordinate interpolation is allowed. A 1.5 Hz Butterworth is the sole proposed filtering sensitivity. The historical seven-frame mean remains a comparison and no historical result changes.

Synthetic 10/25/100 Hz tests showed that the 1.0 Hz filter preserved a 0.3 Hz trajectory while attenuating added 3 Hz disturbance, and its reconstruction error was more consistent across sampling rates than the seven-frame mean. Both the 1.0 and 1.5 Hz candidates remained finite and preserved a constant trajectory through their reflected edges to numerical tolerance.

Cross-frequency equivalence was declared as an absolute 10-versus-25 Hz difference no greater than 0.005 m/s **or** a relative difference no greater than 1%. Raw secant velocities, 1.0 Hz filtering, and 1.5 Hz filtering passed every aligned/cross fixture. Maximum absolute differences were respectively 0.0000575, 0.002568, and 0.000738 m/s. The centred seven-frame comparison failed the stop fixture (0.007937 m/s; 2.688%); seven frames smooth materially different physical durations at 10 and 25 Hz. This supports physical-time comparability and basic edge stability only. No real defender-rank coefficient, near/middle contrast, or scientific response outcome was inspected.

SciPy's fourth-order SOS design has two second-order sections. Its documented/default `sosfiltfilt` padding resolves to 15 samples for these filters, so a block must contain more than 15 samples to execute. For future scientific use, filtering must occur separately inside each continuously valid player/support block and must never cross halftime, invalid tracking gaps, unsupported-player blocks, or other discontinuities. Two-second windows must be extracted only from a single filtered block. Excluding at least the 15 reflected-edge samples from candidate anchors is the implementation-derived minimum, but whether to impose a common physical-time margin across providers remains a prospective freeze decision.

## Synthetic geometry tests

| Fixture | Required behavior | Result |
|---|---|---|
| A. Common defensive translation | absolute aligned positive; relative aligned zero | Pass |
| B. Focal relative movement with attacker | relative aligned positive | Pass |
| C. Focal relative movement opposite attacker | relative aligned negative | Pass |
| D. Perpendicular focal-relative movement | aligned zero; cross magnitude positive | Pass |
| E. Attacker stops | zero increments have no direction; all-stop interval undefined | Pass |
| F. Attacker turns and returns | local-increment form retains coordination despite endpoint cancellation | Pass |
| G. Added common defensive translation | relative aligned and cross quantities invariant | Pass |

Twelve focused tests passed, including these seven identities, explicit displacement-frequency scaling, velocity-frequency invariance, and three outcome-blind filtering checks. A deterministic synthetic audit covers straight, opposite, perpendicular, smoothly varying, stopped, curved, and collective-plus-local motion at 10, 25, and 100 Hz. The source contains no provider loader, rank model, bootstrap, or empirical execution entrypoint.

## Measurement risks still open

- Zero-phase filtering is noncausal, though the proposed estimand describes a completed concurrent interval rather than online prediction.
- Filtering a full support block makes edge handling reproducible, but a common physical-time edge margin versus the implementation-minimum 15 samples remains to be chosen prospectively.
- The local-increment formula weights contributions by attacker step length; intervals dominated by one fast leg may downweight slower direction changes.
- Absolute cross magnitude removes left/right cancellation intentionally; a signed cross quantity would answer a different question.
- Leave-one-out centroids remove common translation but not rotation, deformation, or other shared local geometry.
- Sampling-rate equivalence has been checked synthetically, not empirically across providers for this new measure.

## Conclusion

The velocity candidate is **measurement-ready for final protocol design, not scientifically executed**. It removes the displacement form's deterministic $\Delta t$ scaling, and the physical-time filters meet the synthetic 10/25 Hz equivalence rule. Before freeze, the protocol still must choose a provider-comparable edge margin, complete continuous-block construction, exact inference/multiplicity rules, and classification conditions. No Game 1 coordination-form result has been computed.
