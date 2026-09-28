# Attacker-Linked Off-Ball Reorganization Review v1

**Status:** frozen before attacker-link reference construction or candidate inspection

**Frozen:** 2026-09-28

**Starting commit:** `a3c3ac99a3f119fed317aea7df4eb448a7e43fee`

## Purpose and boundary

This descriptive application review asks whether trajectory-clean,
possession-valid, open-play, low-ballward rapid defensive reorganizations occur
alongside substantial movement by off-ball attackers and strong, predeclared
attacker–defender spatial links. It does not alter the production score, rapid
threshold, possession state, trajectory QC, ball-alignment geometry, or any
scientific result.

“Linked” means only that the frozen movement and geometry rules co-occur. It
does not establish causation, defensive reaction, marking responsibility,
attacker influence, space creation, tactical success, intent, quality, or value.

## Population and timing

The reference population is the existing Metrica Sample Games 1–2 set of
trajectory-clean, possession-valid, open-play, renderable, alignment-supported
low-ballward rapid episodes. The public candidate population is the Game 2
subset. Low-ballward retains the closed condition `team_B <= reference P25`.

All new geometry uses the centered seven-frame mean at 25 Hz over `[t-2,t]`,
with complete raw support `[t-2.12,t+0.12]`. Require exactly ten stable attacking
outfield identities, ten stable defending outfield identities, and complete ball
coordinates. Missing, duplicate, nonfinite, cadence-broken, or period-crossing
support fails closed. No interpolation or partial-team calculation is allowed.

## Off-ball attacker and movement

At each of the 51 smoothed frames, the ball-nearest attacking outfielder is
excluded. Exact distance ties resolve by ascending canonical player key. An
attacker is eligible when off-ball on at least 41 of 51 frames
(`off_ball_fraction >= 0.80`). This is a geometric proxy, not observed ball
possession or a tactical run label.

For every eligible attacker report:

- accumulated absolute path over the 50 increments (primary);
- endpoint net displacement; and
- accumulated path of the attacker-minus-ball vector.

No attacking-centroid measure is included in v1.

## Defender contributors and pair geometry

Reuse the ten stored defender-relative path contributions at `t` exactly.
Order them descending, breaking ties by ascending canonical defender key. The
top three define strong-link eligibility. Defenders strictly above the
ten-player median are retained only for secondary description.

For every eligible attacker and defender calculate start, end, and minimum
distance; signed and absolute end-minus-start distance; accumulated path of the
defender-minus-attacker vector; and cosine coherence between attacker absolute
net movement and defender net displacement relative to the other nine
defenders. Coherence is undefined when either vector norm is at or below
`1e-12 m`.

## Reference thresholds and link rule

Before exposing any Game 2 pair identities or diagnostics, pool:

- attacker paths across all eligible off-ball attackers in the Games 1–2
  reference episodes; and
- relative-vector paths across every eligible attacker × top-three contributor
  pair in those episodes.

Freeze NumPy-linear P75 for each distribution in a hash-bound threshold gate.

An attacker–defender pair is strongly linked only when the attacker is eligible,
attacker path is at least attacker-path P75, the defender is a top-three
contributor, and at least one holds:

- minimum distance is at most `8.0 m`;
- absolute distance change is at least `3.0 m`; or
- relative-vector path is at least its reference P75.

Count unique pairs. Zero links is `none`, one or two is `localized`, and three
or more is `distributed`.

## Rankings and publication

Produce three deterministic Game 2 rankings:

1. rapid magnitude descending, then period, time, and team;
2. maximum eligible attacker path descending, then rapid magnitude, period,
   time, and team; and
3. strong-link count descending, then rapid magnitude, period, time, and team.

Public selection retains the highest rapid-magnitude distributed episode, then
the highest localized episode, then optionally the highest no-link episode.
Absent categories remain absent; appearance cannot trigger substitution.

Public players receive episode-local labels only: attackers ordered by path and
defenders ordered by contribution. Provider identities, coordinates, raw frame
rows, and pair tables remain local. The package may publish aggregate reference
summaries, one compact episode audit, selected diagnostics, and at most three
GIFs. Historical v1–v4 packages remain byte-identical.

## Closure

Construct the anonymous reference gate first, then evaluate candidates, select
examples, and render. Repeat mechanically in an isolated destination and require
byte-identical governed outputs before promotion. Preserve null or sparse
results without changing thresholds, categories, or clips.

