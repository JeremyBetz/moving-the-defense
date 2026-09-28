# Attacker-linked off-ball reorganization review v1

Status: **closed descriptive application review** (2026-09-28).

## Question

After rapid defensive reorganization has passed the existing possession,
trajectory-integrity, open-play, rendering-support and low-ballward gates, what
substantial off-ball attacking movement occurs alongside spatially related
movement by the defenders contributing most to reorganization?

“Linked” means only that the prospectively frozen movement and geometry rules
were satisfied in the same trailing two-second interval. It does not mean
caused, marked, followed, influenced, created space, or produced a successful
tactical outcome.

## Frozen reference and thresholds

The aggregate-only reference used qualifying low-ballward open-play episodes
from public Metrica Sample Games 1 and 2. It contained 212 eligible off-ball
attacker summaries and 636 eligible off-ball-attacker × top-three-defender pair
summaries. NumPy-linear P75 thresholds were frozen before Game 2 candidate
identities were exposed:

- attacker trailing two-second path: **7.6988088115 m**;
- attacker–defender relative-vector path: **7.9814805498 m**.

There were no reference or Game 2 episode-support exclusions. The threshold
gate, output schemas and hashes are recorded in the
[public manifest](../../figures/presentation/attacker_linked_reorganization_review/manifest.json).

## Game 2 audit

Twelve Game 2 episodes met the unchanged upstream gates. Under the frozen
attacker-link rule, five were `distributed` (at least three unique strong
attacker–defender pairs), three were `localized` (one or two), and four had no
strong link. These categories describe co-occurring geometry, not defensive
organization quality.

The historical Home-period-2 passage at 4443.16 s remained the largest rapid
rise in this candidate set: **+1.733 m** over one second, with a raw team level
of **4.725 m**, low ballward share **0.158**, eight eligible off-ball attackers,
and 12 strong links across the three leading defender contributors. It was
therefore classified as distributed. Under the frozen rules, the passage
contains substantial off-ball association in addition to its ball-flight and
shape-reset context; this remains a descriptive co-occurrence, not an account
of why the defenders moved.

## Deterministic public examples

The public selection followed category and rapid-magnitude rules fixed before
inspection:

| Selection | Team / period / time | Rapid rise | Strong links | Category |
|---|---|---:|---:|---|
| Highest distributed | Home / 2 / 4443.16 s | +1.733 m | 12 | Distributed |
| Highest localized | Home / 2 / 5355.64 s | +0.791 m | 2 | Localized |
| Highest no-link contrast | Home / 1 / 978.32 s | +0.888 m | 0 | None |

Player labels are local to each episode and cannot be mapped through committed
artifacts to provider identities. The compact audit contains no coordinates or
attacker–defender pair rows.

## Reproducibility and boundary

The primary and isolated reproduction packages were byte-identical. The raw
defender scores, rapid ordering, possession state, trajectory checks and ball
alignment were not changed. This application layer does not validate marking
assignments, causal attacker influence, tactical intent or success, space
creation, player quality, or player value.
