# Measuring Localized Defensive Reorganization Associated with Off-Ball Movement in Football

*Working paper from the `moving-the-defense` repository.*

Off-ball movement can coincide with defenders moving differently from the
defensive unit as a whole. Across Metrica and IDSSE tracking data, preceding
attacker movement was associated with stronger later localized
defender-relative movement among the three nearest defenders than among a
middle-ranked group. More surprisingly, outward movement was associated with
greater localized defensive reorganization than equivalently modelled goalward
movement—and that directional pattern replicated again in SkillCorner Open
Data.

The paper asks how this association varies with an attacker's starting geometry
and movement direction.

This is an observational measurement, not a causal or value claim. It can help
analysts surface passages where attacker movement is followed by localized
internal defensive change for later video review.

> **Reproduce the paper:** begin with [REPRODUCE.md](REPRODUCE.md), the
> human-first data-to-figure guide. The
> [technical reproducibility guide](docs/reproducibility.md) contains full
> protocol and audit detail.

## The football problem

A defender may move because the whole defensive unit shifts, or because that
defender changes position relative to the unit. Raw displacement blends those
geometries together. This project measures each defender's movement relative to
the contemporaneous movement of the other defending outfield players, so a
shared collective shift can be distinguished from local movement within the
unit. Defenders are grouped by their start-time proximity to the moving
attacker; “near-minus-middle” means the difference between the three nearest
and four middle-ranked defenders.

![Time-ordered localized defensive-reorganization evidence](docs/figures/sloan/temporal_footprint_flagship.svg)

*Panel A is a real, deterministic heldout Metrica Game 2 passage. The defensive
unit shifts goalward and laterally; D2 and D3 move less goalward than their
unit reference, whereas D1 moves more goalward. Panels B–C show the replicated
time-ordered evidence. The example does not assign marking or cause.*

## What we found

### 1. Time-ordered localized reorganization

Preceding attacker movement was associated with greater subsequent defender
movement relative to the defensive unit among the nearest defenders than the
middle group. Here, **m/m** means metres of additional defender-relative
movement per metre of attacker movement.

| Environment | Near-minus-middle association | Interval |
|---|---:|---:|
| Metrica Games 1–2, pooled | 0.05029 m/m | [0.03433, 0.06858] |
| IDSSE, seven matches | 0.06115 m/m | [0.05579, 0.06681] |
| IDSSE forward-minus-reverse difference | 0.02455 m/m | [0.01932, 0.02985] |

All seven IDSSE primary estimates and all seven forward-minus-reverse
differences were positive. Reverse-time structure also remained positive: the
evidence is that the correctly ordered association exceeded the reverse-time
comparison, not that shared temporal structure disappeared.

### 2. Outward movement produced a different geometric response than goalward movement

At equal movement magnitude and comparable predeclared starting geometry,
outward attacker displacement was associated with greater subsequent localized
defender-relative reorganization than goalward displacement.

| Environment | Outward minus goalward | 95% CI | Direction consistency |
|---|---:|---:|---|
| IDSSE | 0.056856 m/m | [0.051358, 0.062430] | 7/7 match; 7/7 leave-one-match-out positive |
| SkillCorner Open Data | 0.048883 m/m | [0.042940, 0.054707] | 9/9 match; 9/9 leave-one-match-out positive |

The frozen IDSSE illustration corresponds to approximately **0.284 m** more
subsequent localized defender-relative reorganization for a 5 m outward rather
than 5 m goalward displacement, under equal path magnitude and context.
Defensive reorganization was therefore not simply aligned with movement toward
goal. This does not mean outward movement is better, more valuable, or a
preferred tactical action.

![Outward-versus-goalward movement-direction result](figures/defensive_reorganization_spatial_value_v1/spatial_form.png)

*Left: frozen 5 m canonical movement descriptions. Right: all seven IDSSE
match-specific outward-minus-goalward contrasts are positive. No cross-provider
pooled estimate was created.*

### 3. Starting geometry matters

Localized reorganization tended to be larger when attackers started closer to
the ball and less far goalward relative to the defensive unit.

| Starting relationship | Association | 97.5% CI |
|---|---:|---:|
| Attacker goalward position relative to the unit | −0.010161 m/m | [−0.011805, −0.008499] |
| Attacker–ball distance | −0.007533 m/m | [−0.008864, −0.006245] |

Both relationships had the same direction in all 7/7 match and
leave-one-match-out fits, and passed their predeclared trims. They characterize
where the observed geometry was larger; they do not explain why defenders moved.

## What this could be used for

The method can surface off-ball movements followed by strong measured
reorganization within the defensive unit, distinguish those changes from a
shared defensive shift, and give analysts a structured set of passages for
video review. It does not automatically assign tactical labels, rank players,
or measure value.

The contribution is not a new centroid or generic tracking primitive. It is a
prospectively validated temporal measurement of internal defensive
reorganization, combined with a replicated finding that outward and goalward
off-ball movement are associated with different defensive geometry across
multiple tracking environments—without requiring inferred marking assignments
or a value model.

## What the follow-up does and does not explain

Goalward movement showed a strong **secondary, nonclassifying** association with
collective defensive translation: the frozen 5 m goalward-versus-outward
contrast was 2.962709 m [2.870720, 3.048322], positive in 7/7 match and 7/7
leave-one-match-out fits.

The proposed inward-versus-outward narrowing mechanism was **MIXED**:
0.134003 m [−0.006622, 0.273430], with 5/7 positive match contrasts. Different
geometric response scales are visible, but the mechanism behind the directional
asymmetry remains unresolved.

## What the evidence does not establish

The evidence does not establish attacker causation or influence; defender
attention, marking, assignment, or responsibility; tactical success; space
creation; player quality; gravity; or off-ball value.

A direct consequence test was negative: Opportunity Redistribution in Metrica
Game 1 estimated `beta_D = -0.02407` [−0.09392, 0.04776]. Under that test,
localized defensive reorganization did not imply improved nearby teammate
separation. A context-adjusted retrieval model also remained **MIXED** after
missing its predeclared application threshold. Negative and mixed findings are
retained in the [claim-status ledger](docs/claim_status.md) and
[research log](docs/research_log.md), not tuned away.

## Data and external validation

| Data source | Role |
|---|---|
| Metrica Sample Game 1 | Open/public development environment |
| Metrica Sample Game 2 | Open/public heldout validation and real explanatory example |
| IDSSE / DFL XML | Seven-match external validation; authorized/provider access required |
| SkillCorner Open Data | Open third, broadcast-derived environment for directional replication |
| Metrica Sample Game 3 | Untouched |

Under the repository’s conservative publication policy, raw provider files,
row-level data, and reconstructive provider-derived tables are not committed.
Compact governed results, code, figures, protocols, configurations, and
provenance ledgers are public.

## Reproduce, audit, or continue

| Goal | Start here |
|---|---|
| **Reproduce the paper** | [REPRODUCE.md](REPRODUCE.md) |
| **Audit research history and claim limits** | [Claim-status ledger](docs/claim_status.md) and [research log](docs/research_log.md) |
| **Continue the research** | [Research roadmap](docs/research_roadmap.md) |
| Understand the football question | [Project explainer](docs/project_explainer.md) |
| Inspect protocols and results | [Documentation guide](docs/README.md) |

## Current frontier

The next scientific challenge is semantic and applied: determine what these
replicated geometric patterns correspond to in football practice and how
analysts should use them without converting observable reorganization into
unsupported claims of influence or value. Artificial-transition work is a
post-Sloan extension, not a current mechanism search.

Figure sources use closed governed artifacts. Code and documentation are
released under the [MIT License](LICENSE).
