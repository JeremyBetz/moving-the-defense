# Explaining the Project

This document is a verbal guide for explaining the work accurately to a technically literate soccer audience.

## 1. What originally motivated the project?

The original idea was that attackers influence defenders even when they do not receive the ball. A checked run, rotation, or threatening position may cause defensive movement that conventional event data misses. The first framing tried to describe defenders as moving through Structure, Track, Close, and Recover states.

## 2. What does “asking questions” mean?

It is soccer shorthand for posing a credible tactical problem. A winger holding width, a striker threatening depth, or a midfielder appearing between lines may require some defensive response. “Question” is theoretical language; the data do not reveal whether a defender consciously recognized it.

## 3. Why can we not measure defensive cognition directly?

Tracking gives coordinates. It does not record instructions, gaze, communication, intention, attention, recognition, or responsibility. We can calculate movement consistent with an interpretation, but we cannot equate the calculation with the hidden mental or tactical process.

## 4. What does tracking data give us?

At 25 Hz, the Metrica files provide anonymized player and ball positions plus event timestamps. After converting normalized coordinates to 105 × 68 m, we can calculate trajectories, distances, relative positions, centroids, paths, and velocity components. Missing ball and player coordinates remain explicit; nothing is interpolated where a protocol prohibits it.

## 5. Why are reference frames important?

A defender can travel 20 m on the pitch while maintaining nearly the same position relative to the defensive block. Raw coordinates describe absolute movement; a moving reference describes movement relative to something else. The same trajectory can therefore look like large translation in one frame and little departure in another.

![Raw and collective-relative motion](../figures/concepts/raw_vs_collective_relative.png)

## 6. What is collective translation?

Collective translation is shared movement of the defending group. A simple baseline is the centroid of the defending outfield players. For focal defender $d$, the leave-one-out centroid is

$$
\mathbf c_{-d}(t)=\frac{1}{N-1}\sum_{j\neq d}\mathbf x_j(t).
$$

It is useful but not “the structure.” Opposing movements can cancel, and a mean cannot preserve local spacing, rotation, opponents, or ball context.

## 7. What is focal departure?

Focal departure is the movement of one defender relative to that leave-one-out collective baseline:

$$
\mathbf r_d(t)=\mathbf x_d(t)-\mathbf c_{-d}(t).
$$

Phase 4 proposes the path length of $\mathbf r_d(t)$ over a five-second interval as the primary magnitude. It measures accumulated relative motion, including leaving and returning. It does not say why the defender moved differently.

## 8. Why did the original Track concept fail?

The simple proposal was that a defender following an opponent should have a stable attacker-relative x/y vector. In the visually strongest Game 1 Track candidate, that vector was not more stable than the collective-relative alternative. Movement coupling and opponent geometry may capture other aspects, but fixed Cartesian stability is not a general Track primitive.

## 9. Why did local compression become local deformation?

Some selected defenders clearly converged in one interior-threat sequence. Later prospective selection showed that different reasonable local memberships contained contraction, expansion, and mixed anisotropic change. “Deformation” accurately includes shrinking, stretching, rotation, and reordering; “compression” is only one subtype.

![Local membership sensitivity](../figures/concepts/local_membership_sensitivity.png)

## 10. What did Phase 3 test?

Phase 3 froze a reception-anchored matched design before viewing outcomes. Receptions were candidate clocks, ordinary open-play pseudo-anchors were controls, and typed collective, focal, local, opponent, ball, and generic-activity descriptors stayed separate.

## 11. Why did Phase 3 fail?

Only 46 of 315 candidates matched, far below the frozen 70% support threshold. Reception windows showed more movement, but shifted anchors inside the same possession reproduced or exceeded the main apparent effects. When the sparse sensitivity also matched pre-anchor activity, the contrasts disappeared. The frozen conclusion was C.

## 12. Why is that failure useful?

It rules out a convenient shortcut: receptions cannot be treated as positive reconfiguration cases. It also shows that generic passage activity must be central in future designs and that one match cannot support strict contextual matching.

## 13. Why is Game 2 held out?

If the metric or thresholds change after looking at Game 2 outcomes, the second match becomes another development sample. Freezing the protocol first creates a genuine chance for failure and makes replication interpretable.

## 14. What exactly did Phase 4 test?

It sampled deterministic non-overlapping five-second intervals, calculated focal-relative path for every eligible outfield defender, characterized Game 1 distributions and activity relationships, and tested them once in Game 2. Events provided possession/context, not positive labels.

## 15. What did Phase 4B establish?

The geometric quantity replicated: all 9/9 frozen activity cells passed, directions were stable, common translation cancelled, misaligned references produced much larger paths, and all frozen sensitivities preserved the qualitative result. Focal departure remained positively associated with generic activity and no activity-free effect was estimated.

## 16. What remains weak or unsupported?

The result spans only two same-provider sample matches and still may mean little beyond “this defender moved differently from teammates.” It does not establish pinning, dragging, tracking, covering, handoffs, tactical response, relational reconfiguration, responsibility, quality, gravity, or value.

## 17. How far are we from defensive reconfiguration claims?

At least one major empirical layer away. Focal departure now validates narrowly as a primitive, but it still needs contextual or semantic interpretation and integration with other validated scales. The umbrella construct already failed one prospective validation design.

## 18. How far are we from gravity or off-ball value?

Several conditional layers away. Gravity requires attacker attribution and an expected-response baseline; value additionally requires downstream soccer consequences. A reproducible defensive movement quantity would not by itself establish either.

## 19. What is the post-validation research question?

The single formal question is: **How can tracking data measure defensive responses to attacking movement in open-play football?** The motivating football question is: **When an attacker does not receive the ball, can we measure what they made the defense do?** A downstream question asks whether concepts such as pinning, dragging, tracking, covering, handing off, and stretching can eventually be translated into validated tracking patterns. The program separates football language, tracking measurements, and theoretical mechanisms. Association is not attribution, and attribution is not causation.

## A useful one-minute summary

The project started by asking whether attackers cause defenders to switch among tactical states. Diagnostics showed that states overlap, simple Track failed, and local stories depend on reference choice. A reception-based validation mostly detected active passages. Phase 4 then narrowed to one primitive and found that focal-relative path replicated across Games 1 and 2 while remaining activity-associated. Only after that test closed did the project broaden toward translating football concepts such as pinning, dragging, covering, and passing on into separately validated defensive-response signatures. None of those tactical concepts is established yet.
