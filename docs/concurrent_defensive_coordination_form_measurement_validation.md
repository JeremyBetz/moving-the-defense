# Concurrent Defensive Coordination Form v1 — measurement validation

**Status: design-stage measurement validation; no match-level defensive-response result computed.**

## Football question

When an attacker changes direction during a movement, does a nearby defender's movement relative to the rest of the defensive unit change in the same local direction? This asks about concurrent tracking geometry. It does not identify following, marking, responsibility, reaction, influence, or tactical success.

## Candidate measurement

Let the attacker's position be $\mathbf A(t)$, focal defender position be $\mathbf x_d(t)$, and the centroid of the other nine defending outfield players be $\mathbf c_{-d}(t)$. Define

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),\qquad
\Delta\mathbf A_k=\mathbf A_{k+1}-\mathbf A_k,\qquad
\Delta\mathbf r_{d,k}=\mathbf r_{d,k+1}-\mathbf r_{d,k}.
$$

For an interval with nonzero attacker path, the candidate **attacker-aligned relative displacement** is

$$
\operatorname{AARD}_d=
\frac{\sum_k \Delta\mathbf r_{d,k}\cdot\Delta\mathbf A_k}
{\sum_k\lVert\Delta\mathbf A_k\rVert_2}.
$$

Its unit is metres. It is a path-weighted mean of each defender-relative increment projected onto the attacker's local movement direction. Positive means the defender-relative increments tend to point with the attacker's local increments; negative means they tend to oppose them; near zero may reflect perpendicular movement, no relative movement, cancellation, or weak coordination. None of those signs has tactical semantics by itself.

The **absolute aligned comparator** replaces $\Delta\mathbf r_{d,k}$ with $\Delta\mathbf x_{d,k}$. It exposes alignment caused by a shared defensive shift that the leave-one-out reference removes.

The secondary cross-trajectory magnitude is

$$
\operatorname{AARD}^{\perp}_d=
\frac{\sum_k\left|\Delta r_{d,k,x}\Delta A_{k,y}-
\Delta r_{d,k,y}\Delta A_{k,x}\right|}
{\sum_k\lVert\Delta\mathbf A_k\rVert_2}.
$$

It is nonnegative and measured in metres. It describes relative movement normal to the attacker's local path; it cannot rescue an unsupported primary aligned result.

Stationary attacker increments contribute zero to both numerator and denominator and therefore receive no artificial direction. If total attacker path is at or below the documented numerical-zero tolerance, all aligned/cross quantities are undefined. Missing coordinates invalidate required support; they are not interpolated.

## Preprocessing comparison

Historical project measurements use a centred seven-frame arithmetic mean. Its physical support is 0.28 seconds at 25 Hz but 0.70 seconds at 10 Hz, so it is not provider-time-equivalent.

The draft primary candidate is a fourth-order zero-phase Butterworth low-pass at 1.0 Hz, applied separately to x/y over a complete continuous support block before analysis windows are extracted. SciPy's `sosfiltfilt` odd-reflection edge treatment is explicit. A block too short for filtering is invalid; no fabricated padding or coordinate interpolation is allowed. A 1.5 Hz Butterworth is the sole proposed filtering sensitivity. The historical seven-frame mean remains a comparison and no historical result changes.

Synthetic 10/25 Hz tests showed that the 1.0 Hz filter preserved a 0.3 Hz trajectory while attenuating added 3 Hz disturbance, and its reconstruction error was more consistent across sampling rates than the seven-frame mean. Both the 1.0 and 1.5 Hz candidates remained finite and preserved a constant trajectory through their reflected edges to numerical tolerance. This supports physical-time comparability and basic edge stability only. No real defender-rank coefficient, near/middle contrast, or scientific response outcome was inspected.

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

Ten focused tests passed, including these seven identities and three outcome-blind filtering checks. The source contains no provider loader, rank model, bootstrap, or empirical execution entrypoint.

## Measurement risks still open

- Zero-phase filtering is noncausal, though the proposed estimand describes a completed concurrent interval rather than online prediction.
- Filtering a full support block makes edge handling reproducible but requires a prospective rule for continuous-block construction and minimum usable distance from block edges before protocol freeze.
- The local-increment formula weights contributions by attacker step length; intervals dominated by one fast leg may downweight slower direction changes.
- Absolute cross magnitude removes left/right cancellation intentionally; a signed cross quantity would answer a different question.
- Leave-one-out centroids remove common translation but not rotation, deformation, or other shared local geometry.
- Sampling-rate equivalence has been checked synthetically, not empirically across providers for this new measure.

## Conclusion

The candidate measure is **measurement-ready for protocol review, not scientifically executed**. Its algebra behaves as intended and a physical-time filtering route is preferable to reusing a fixed frame count across 10/25 Hz. Continuous-block and edge eligibility must be frozen before any Game 1 coordination-form result is computed.
