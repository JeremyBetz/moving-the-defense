# Post-5B Measurement Audit A: Direction and Response Onset

> **Audit result: B — mixed.** Directional displacement preserves geometric distinctions that scalar path magnitude cannot retain. Constant-velocity continuation innovation is visually interpretable in some anchors, but overlaps substantially with deterministic neutral windows, is sometimes activity-associated, and often rises after the focal movement is already visible in the preceding two seconds. No response-onset detector or tactical response measure is established.

## Purpose and boundary

Phase 5B found only a tiny, non-material opponent-information increment beyond Phase 5A B4. This audit examines two possible measurement limitations without changing the validated focal-relative path primitive:

1. recent focal movement may already contain the beginning of the geometric movement before a prediction cutoff;
2. five-second scalar path magnitude may collapse movements that differ in direction or temporal development.

The established primitive retains its original role—**how much** the focal defender moved relative to the contemporaneous leave-one-out collective. Directional displacement asks **what geometric direction** the net relative movement took. Continuation innovation asks whether short-horizon movement departed from a transparent pre-candidate motion continuation. None has tactical, opponent, assignment, or causal semantics here.

## Human-reviewed measurement disposition

- **Keep:** directional focal-relative displacement as a complementary descriptive representation.
- **Keep:** scalar focal-relative path as the validated movement-magnitude primitive.
- **Do not keep as validated:** constant-velocity continuation innovation as a response-onset measure.
- **Do not tune from this audit:** innovation thresholds, horizons, persistence rules, or candidate-time placement.

Several historically interesting movements were already developing within a Phase 5A-style two-second history window. Pre-cutoff focal motion can therefore contain developing movement of later interest. As a research implication—not an established result—a future defensive-response representation may need to describe geometric change across a finite interval rather than require one universal response-onset instant.

## Fixed audit sample

The seven historical Sample Game 1 windows were reused without searching for favorable examples:

| Window | Defending team / focal | Candidate $\tau$ |
|---|---|---:|
| 1888–1896 coordinated collective movement | Home 2 | 1892.00 s |
| 590–598 apparent focal excursion | Home 2 | 594.00 s |
| 550.76–555.76 tackle/engagement | Away 16 | 550.76 s |
| 1228.12–1232.12 interior-threat anchor | Away 19 | 1230.12 s |
| 1229.28–1234.28 accommodation sequence | Away 19 | 1232.28 s |
| 3679.88–3684.88 collective-translation contrast | Home 8 | 3682.88 s |
| 4195.04–4199.04 heterogeneous negative | Away 16 | 4197.04 s |

### Deterministic neutral-window rule

Before viewing audit geometry, the comparison rule was fixed as:

- eight-second windows beginning every 300 seconds from 300 through 5700 seconds;
- exclude period crossings and overlaps with the seven anchor windows;
- exclude any window with a `SET PIECE` or `BALL OUT` event from two seconds before its start through its end;
- alternate Home/Away by the original grid index;
- select the lowest numeric non-goalkeeper player ID with complete focal and leave-one-out support;
- never use movement magnitude or visual interest.

This retained 14 windows: 300–308, 600–608, 900–908, 1200–1208, 1500–1508, 2100–2108, 2700–2708, 3000–3008, 3300–3308, 3600–3608, 3900–3908, 4200–4208, 4500–4508, and 5100–5108 seconds. The complete inclusion audit is machine-readable.

## Representations

### A. Existing scalar path

For the unchanged leave-one-out relative position

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t),
$$

the existing centered seven-frame interval construction supplies

$$
P=\sum_i \left\|\mathbf r_d(t_i)-\mathbf r_d(t_{i-1})\right\|.
$$

It remains a validated descriptive primitive and is not replaced.

### B. Directional displacement

For each fixed interval,

$$
\Delta\mathbf r=\mathbf r_d(t_1)-\mathbf r_d(t_0)
$$

is retained as longitudinal $\Delta r_x$, lateral $\Delta r_y$, magnitude $\|\Delta\mathbf r\|$, and visualization-only angle when the magnitude exceeds $10^{-9}$ m. The full signed relative-increment sequence is preserved in the time-series artifact. No tactical direction labels are assigned.

### C. Constant-velocity continuation innovation

Raw focal and leave-one-out centroid positions are converted to the documented 105 × 68 m pitch. A trailing causal seven-frame mean is calculated without interpolation. At each candidate time $\tau$, terminal relative velocity is the last one-frame difference of the causal-smoothed relative trajectory divided by the observed frame interval. For predeclared horizons $h\in\{0.4,0.8,1.2\}$ s,

$$
\widehat{\mathbf r}_d(\tau+h)=\mathbf r_d(\tau)+\mathbf v_{rel}(\tau)h,
$$

$$
\mathbf e(\tau+h)=\mathbf r_d(\tau+h)-\widehat{\mathbf r}_d(\tau+h).
$$

The audit retains innovation x, y, magnitude, unit-vector coherence across the three horizons, and forward five-frame directional coherence for the 0.8-second innovation. These are descriptive quantities, not thresholds or onset labels. Constant velocity is used because it is transparent, deterministic, pre-candidate-only, and exposes directional departure; it is not claimed to be tactically correct expectation.

## Scalar versus directional findings

| Anchor | Relative path | $\Delta r_x$ | $\Delta r_y$ | Net displacement | Path/net ratio |
|---|---:|---:|---:|---:|---:|
| 1888 translation | 5.057 | +1.118 | −1.566 | 1.924 | 2.628 |
| 590 excursion | 12.050 | +7.518 | +0.738 | 7.554 | 1.595 |
| 550 tackle | 15.770 | +6.371 | −12.071 | 13.649 | 1.155 |
| 1230 interior | 13.533 | +3.293 | −11.938 | 12.384 | 1.093 |
| 1232 accommodation | 16.492 | +5.601 | −10.275 | 11.703 | 1.409 |
| 3682 translation contrast | 12.198 | −11.661 | +1.293 | 11.733 | 1.040 |
| 4197 negative | 1.036 | −0.472 | −0.016 | 0.472 | 2.194 |

All distances are metres. Scalar path remains useful for total relative movement, but it cannot preserve axis, sign, cancellation, or curvature. The 550 anchor and deterministic neutral 3000–3008 window have similar paths (15.770 and 15.500 m) but opposite longitudinal displacements (+6.371 and −13.450 m). The 590 and 3682 anchors likewise have similar paths (12.050 and 12.198 m) but opposite dominant x directions. Direction therefore adds real geometric information without invalidating path magnitude.

## Innovation and temporal findings

At the fixed candidate times, anchor innovation magnitudes for 0.4/0.8/1.2 seconds are:

| Anchor | 0.4 s | 0.8 s | 1.2 s | Pre-$\tau$ 2 s relative path |
|---|---:|---:|---:|---:|
| 1888 translation | 0.042 | 0.118 | 0.206 | 1.105 |
| 590 excursion | 0.149 | 0.613 | 1.463 | 1.489 |
| 550 tackle | 0.395 | 1.350 | 2.571 | 3.829 |
| 1230 interior | 0.195 | 0.638 | 1.321 | 3.684 |
| 1232 accommodation | 0.288 | 1.255 | 2.850 | 9.903 |
| 3682 translation contrast | 0.187 | 0.684 | 1.274 | 6.259 |
| 4197 negative | 0.015 | 0.030 | 0.084 | 0.543 |

The innovation vectors are usually directionally coherent across horizons at the chosen times, but coherence alone is not specificity: continuous curved motion and ordinary neutral play can also produce it.

- **1888:** high focal and centroid activity coexist with small innovation around $\tau$; the larger relative departure appears later.
- **590:** the relative x trajectory is already changing before $\tau$ and reverses shortly afterward; innovation rises around this change but does not define a unique onset.
- **550:** directional change and substantial innovation are already visible before the event-time candidate; the hypothetical cutoff is late relative to movement development.
- **1230:** relative y curvature and rising innovation begin inside the preceding two seconds.
- **1232:** the movement is unmistakably underway throughout much of the preceding two seconds; $\tau$ is not an onset.
- **3682:** relative x changes continuously before and after $\tau$; innovation describes curvature but does not localize a new beginning.
- **4197:** innovation is minimal at $\tau$ and remains small; later activity does not turn this negative case into a strong localized departure.

Thus the conditioning concern is real in several anchors: a two-second history can already contain the movement whose later development is being summarized. The audit does not establish where a response began.

## Activity and collective-motion confounds

Innovation is not merely absolute activity. The 1888 window has 32.268 m focal absolute path and 31.590 m centroid path but only 0.118 m 0.8-second innovation at $\tau$. The 590 window has much less absolute activity (13.641 m) but 0.613 m innovation. This demonstrates that collective translation and continued movement can be geometrically separated from short-horizon relative departure.

However, innovation is not cleanly specific either. The neutral 5100–5108 window has 0.912 m 0.8-second innovation—larger than five of seven anchors—and neutral 4500–4508 reaches 0.338 m despite only 3.830 m focal absolute path. Ordinary active play can generate sizable continuation errors, while high-activity neutral 600–608 has only 0.135 m. These contrasts are useful diagnostically but prevent treating innovation magnitude as response onset.

## Evidence balance and classification

The strongest promising contrast is 1888 versus 590: shared high collective movement can yield small innovation, while a lower-activity focal-relative reversal yields a larger, directional innovation. The strongest counterexample is neutral 5100–5108, whose 0.912 m 0.8-second innovation exceeds most anchors without being selected for historical meaning.

The qualitative classification is **B — mixed**:

- directional displacement is a useful additional representation because it retains sign and axis information scalar path necessarily discards;
- constant-velocity innovation is interpretable in some fixed anchors and is not identical to absolute or collective activity;
- neutral overlap, continuous curvature, candidate-time dependence, and pre-cutoff movement make it insufficiently specific for a formal onset validation protocol.

A formal validation phase is **not yet justified**. The representation needs further outcome-blind refinement of candidate-time semantics and falsification against ordinary movement before freezing a validation design. No Phase 5C design is introduced here.

The exact supported claim is:

> **Directional focal-relative displacement preserves geometric distinctions that scalar focal-relative path magnitude collapses, but constant-velocity continuation innovation is only a mixed diagnostic because historically interesting and deterministic neutral windows overlap and several anchor departures are already visible in the preceding two seconds.**

This audit does not establish tactical response, attacker association, attacker causation, marking, assignment, responsibility, pinning, dragging, tracking, covering, handoffs, relational reconfiguration, tactical correctness, defensive quality, gravity, or off-ball value.

## Artifacts

- [Executed notebook](../notebooks/post5b_measurement_audit_direction_onset.ipynb)
- [Window summary](../outputs/post5b_measurement_audit_a/window_summary.csv)
- [Neutral selection audit](../outputs/post5b_measurement_audit_a/neutral_window_selection_audit.csv)
- [Anchor/neutral summary figure](../figures/post5b_measurement_audit_a/anchor_neutral_summary.png)
- [Directional displacement comparison](../figures/post5b_measurement_audit_a/directional_displacement_comparison.png)
- Per-anchor pitch, relative-space, innovation, activity, path-accumulation, and vector figures under `figures/post5b_measurement_audit_a/`
