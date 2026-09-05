# Off-Ball Movement Direction and Localized Defensive Reorganization in Football

> **Internal manuscript skeleton — argument architecture, not submission prose.**
> This document organizes closed results; it does not add claims, results, or protocol choices.

## Abstract

**Introduction.** Off-ball movement can coincide either with a whole defensive
unit shifting or with defenders changing position within that unit; tracking
analyses need to distinguish them. Outward attacker movement was more strongly
associated with localized internal defensive reorganization than equivalently
modelled goalward movement, showing that reorganization is not simply aligned
with movement toward goal.

**Methods.** Using fixed windows, we measured attacker movement before each
defender's response path relative to the other defending outfield players,
separating local reorganization from shared translation. Start-fixed proximity
ranks compared the three nearest defenders with four middle-ranked defenders
without inferred marking assignments. We developed and held out the temporal
design in Metrica, tested it externally across seven IDSSE matches, replicated
directional form in nine SkillCorner matches, and included a reverse-time
comparison.

**Results.** In pooled Metrica, the pre-specified near-minus-middle association
was 0.05029 m/m (97.5% interval [0.03433, 0.06858]); its paired
forward-minus-reverse excess was 0.02912 [0.01410, 0.04526]. The development
and protected heldout estimates were both positive (0.04559 and 0.08553 m/m).
Across Metrica, frozen 1-, 2-, and 4-second horizons were positive (0.02916,
0.05029, and 0.07566 m/m), and the predeclared trim retained 88.74% of primary
magnitude. Across seven IDSSE matches, the corresponding association was
0.06115 m/m (95% CI [0.05579, 0.06681]) and the forward-minus-reverse excess
was 0.02455 [0.01932, 0.02985]. All seven primary and paired-excess estimates
were positive; 1-, 2-, and 4-second horizons were likewise positive (0.03536,
0.06115, and 0.09549 m/m), although reverse-time structure itself remained
positive. The IDSSE trim retained 95.35% of primary magnitude. The
outward-versus-goalward directional difference replicated across independent
tracking environments: conditional on
equal path magnitude and frozen starting geometry, outward minus goalward
movement was 0.056856 m/m [0.051358, 0.062430] in IDSSE, positive in all 7/7
match and leave-one-match-out fits, and 0.048883 m/m [0.042940, 0.054707] in
SkillCorner, positive in all 9/9 match and leave-one-match-out fits.
SkillCorner's trim retained 90.19% of rows, and a majority-directly-detected
sensitivity estimated 0.046780 m/m. All governed bootstrap families had
2,000 valid replicates each; the two external environments used separate
frozen models, interval conventions, and checks and were not pooled across
providers. In IDSSE, 5 m outward rather than goalward displacement corresponded
to approximately 0.284 m more subsequent localized defender-relative
reorganization. Thus reorganization was not simply aligned with movement
toward goal. Goalward movement instead had a secondary, nonclassifying
2.962709 m [2.870720, 3.048322] collective-translation association, while the
proposed inward-versus-outward narrowing mechanism was not established.

**Conclusion.** This is not a new centroid or tracking primitive, but a
prospectively tested and externally replicated temporal measure of internal
defensive reorganization with a replicated directional difference. It can
distinguish shared defensive shifts from localized internal reorganization and
surface passages for video analysis. It does not automatically assign tactical
labels. These are observational geometric associations, not estimates of causal
influence or attacking value.

## 1. Introduction

### 1.1 The football problem

Much of football's tactical language concerns movement away from the ball. An
attacker may be said to pull a defender, stretch a line, or make the defence
adjust. These descriptions are meaningful to analysts, but they are difficult
to translate into tracking-data measurements without adding assumptions that the
data do not directly identify. Player tracking records where players move; it
does not directly reveal defensive assignments, tactical instruction, or why a
particular defender changed position.

One source of difficulty is that absolute defender movement combines different
geometries. A defensive unit can slide together toward the ball or toward one
side of the pitch, producing substantial movement by every defender while
largely preserving internal relationships. In another passage, a defender can
move differently from the unit around them, even if the unit's overall movement
is modest. The first pattern is a shared defensive shift. The second is a more
localized internal reorganization. Both may occur together, and neither is
inherently good, bad, intentional, or caused by a single attacker. Yet
distinguishing them is necessary before using tracking data to ask more
substantive questions about off-ball movement.

This distinction matters particularly for attacking movement direction. Football
analysis often privileges movement toward goal because it is naturally linked to
progression and shooting opportunity. However, movement that changes width or
moves away from the pitch centreline may be associated with a different local
defensive geometry even when it is not as goal-directed. A useful measurement
should therefore avoid treating raw displacement, movement toward goal, and
internal defensive change as interchangeable quantities.

The practical question is not whether a tracking system can describe a player
path. It can. The harder question is what comparison makes that path meaningful
for the defensive unit that surrounds it. Comparing only an attacker with their
nearest opponent risks conflating a local relation with the team's shared shift;
comparing only whole-team centroids can hide substantial movement within the
unit. We therefore retain both levels of description and ask a deliberately
narrower question about their time-ordered association.

That distinction also gives the measurement a practical role: it can flag a
passage for later football review without deciding what that passage means.

### 1.2 Measurement problem and research questions

Player-to-team geometry, relative phase, and collective coordination are
established parts of football-tracking research. They provide a useful
measurement substrate, but they do not by themselves define a local defensive
response to attacking movement. This paper operationalizes a narrower,
observable estimand: subsequent movement by a defender relative to the other
defending outfield players after a fixed interval of off-ball attacker movement.
The analysis does not require a marking assignment or a downstream value model.
Instead, it asks whether initially nearby defenders show a different
defender-relative association from a pre-specified middle-distance reference.

The temporal ordering is deliberate. Attacker movement is measured in a
pre-specified interval before the defender outcome, and defender proximity is
fixed at the interval boundary before the later movement is observed. These
start-fixed proximity ranks are a localization safeguard: they prevent the
analysis from selecting defenders because their subsequent movement happened to
look interesting. They do not identify a marker, responsibility, or tactical
role.

The paper addresses three questions. First, is preceding off-ball attacker
movement associated with subsequent defender movement relative to the defensive
unit, more strongly among start-near than middle-ranked defenders? Second, does
this association differ by attacker movement direction, particularly for
movement outward from the pitch centreline versus movement toward goal? Third,
how does observed starting geometry characterize where the localized association
is larger or smaller? These are questions about observable geometric
associations. They are not tests of attacker causation, tactical correctness,
or attacking value.

### 1.3 Contribution and boundary

The contribution is a prospectively tested defender-relative temporal
measurement rather than a new centroid primitive. We use established
player-to-team geometry to define a specific local-response estimand, preserve
proximity localization from before the response interval, and test the design
through protected Metrica holdout, a paired reverse-time comparison, and
external analysis in independent tracking environments. The main empirical
contribution is a replicated outward-versus-goalward difference in the
movement-direction association: conditional on path magnitude and starting
geometry, outward movement was associated with stronger subsequent localized
defender-relative reorganization than goalward movement in separate IDSSE and
SkillCorner analyses.

This result does not mean that outward movement is always tactically preferable,
that it forced defenders to move, or that it generated value. It provides a
more limited measurement statement: comparable movement directions were not
associated with the same localized defensive geometry. By keeping the estimand
observable and the validation sequence explicit, the paper separates a useful
tracking-data measurement from later questions of football interpretation,
attacker attribution, and value.

## 2. Related work

### 2.1 Collective defensive geometry and player-team synchronization

Tracking research has long described football teams through centroids, width,
depth, surface area, interpersonal distances, and related measures of collective
organization. Sampaio and Maçãs (2012) used player distance to the team centre
and relative phase to study tactical behaviour. Duarte, Araújo, and Correia
(2013) examined team-team and player-team synchrony in professional football,
while Moura et al. (2016) used cross-correlation and vector coding to describe
coordination in the spread of opposing teams. Carrilho et al. (2020) likewise
used optical tracking to study player and team synchronization through
player-ball-goal geometry.

These studies establish player-relative-to-team geometry and temporal
coordination as important measurement families. The present analysis uses that
substrate rather than claiming to introduce it. Its leave-one-out defensive-unit
reference is intended to preserve the defensive unit's shared movement as
context while expressing the focal defender's movement relative to teammates.
The question is therefore narrower than whether collective coordination exists:
it is whether a prospectively defined attacker interval is associated with later
localized defender-relative movement.

### 2.2 Attacker-defender pressure, dyads, and assignments

A second literature studies the spatial relations between opponents. Herold et
al. (2022) provide the closest direct off-ball precedent. They used
expert-annotated deep runs and changes of direction to examine how a
time-varying defensive-pressure measure changed over high-intensity off-ball
actions. Their target was individual pressure and separation, rather than
movement relative to a defending unit, but the study demonstrates that off-ball
actions can be connected to evolving defensive geometry.

Dyadic work provides a complementary view. Caetano et al. (2023) characterized
lateral and longitudinal coordination between nearest opposing players during
official-match attacks. Earlier nearest-opponent alignment work also shows that
direction and distance can organize attacker-defender interactions (Narizuka &
Yamazaki, 2016). Other approaches model defensive relationships more
explicitly. Calero-Sanz et al. (2026) construct marking networks from proximity
and directional alignment, whereas Groom et al. (2026) infer time-resolved
defensive roles and assignments. Such approaches address important questions
about who is related to whom, but they require either constructed marking
relationships or latent-role modelling.

The present paper does not attempt to replace these methods. It uses
start-fixed proximity ranks as an assignment-free localization device. Nearby
and middle-ranked defenders are compared because their positions relative to the
attacker are fixed before the outcome interval, not because they are assumed to
be markers, cover defenders, or otherwise responsible for that attacker.

### 2.3 Off-ball movement, space, trajectories, and value

Off-ball research has also approached attacking movement through space,
availability, trajectory representation, and value. Fernández and Bornn (2018)
developed a pitch-control framework for spatial occupation and generation,
including the space that may be opened when an attacker attracts opponents.
Related space/control and receiver-availability work evaluates where a player
can receive the ball or which parts of the pitch are controllable. These are
important downstream questions, but generated space, receiver availability, and
attacking value are not equivalent to subsequent defender movement relative to a
defensive unit.

Trajectory research offers further representations without supplying a single
tactical interpretation. Beernaerts et al. (2020), for example, used relative
movement descriptions to recognize recurring spatial patterns. Run detection and
movement-effort methods likewise describe paths, speed, or direction, but an
observed path does not by itself identify a decoy run, overlap, check, or other
football action. Esposito et al.'s (2026) scoping review of elite off-ball
tracking research emphasizes this broader methodological diversity, including
heterogeneous definitions and limited integration of opponents and context.

Accordingly, the present paper treats attacker path and signed displacement as
geometric exposures. It does not infer that a movement generated space, changed
a defender's assignment, or produced attacking value.

### 2.4 Temporal disruption and directional movement

Temporal ordering is also established in adjacent work. Moura et al. (2016)
reported short lags in coordinated team spread. Forcher, Kempe, and colleagues
(2021) evaluated D-Def, a pass-triggered measure of changes in team and line
centroids, area, and spread during the seconds after a pass. Herold et al.
(2022) followed pressure trajectories through off-ball actions. These studies
show that delayed defensive change can be measured, but they use collective
disruption or pressure rather than a localized defender-relative outcome.

Directional coordination is likewise not new. Caetano et al. (2023) separated
lateral and longitudinal components of nearest-opponent coordination, and
Narizuka and Yamazaki (2025) decomposed goal- and opponent-oriented components
in a model of on-ball dribbling against the nearest defender. Those analyses
differ from the present question in their dyadic and on-ball focus. They do,
however, make clear that the current paper cannot claim novelty for temporal
response or directional coordination in general.

What is specific here is the combination of a pre-specified attacker interval,
a subsequent non-overlapping defender-relative interval, start-fixed
localization, a paired reverse-time comparison, and replication across
independent tracking environments. The reviewed literature did not identify a
direct controlled comparison of outward and goalward off-ball movement against
this kind of subsequent localized internal defensive outcome.

### 2.5 Precise gap

Existing tracking research has characterized collective defensive shape,
player-team synchronization, pressure, inferred marking relationships,
trajectories, and space/value outcomes. Less attention has been given to a
transparent, assignment-free estimand linking a pre-specified attacking movement
interval to subsequent defender movement relative to the defensive unit,
localized using relationships fixed before response. The reviewed literature
also did not identify a direct controlled outward-versus-goalward comparison
against this kind of subsequent localized defender-relative outcome. These are
bounded distinctions from adjacent work, not claims that related methods or
football questions have not previously been studied.

## 3. Data

### 3.1 Metrica development and protected holdout

The temporal measurement was developed using Metrica Sample Game 1 and tested
without revision in Metrica Sample Game 2. These openly available sample
matches provide synchronized player and ball tracking with event context. The
analysis retained only supported open-play intervals after applying the
pre-specified coordinate, cadence, restart, and ball-out rules. Positions were
represented in standardized metric pitch coordinates.

Game 1 served as the development environment for the temporal design, while
Game 2 served as a protected within-provider holdout. The latter also provides
the paper's explanatory match-level example because it was not used to develop
the primary temporal analysis. The two matches are transparent samples rather
than a representative population of football. Metrica Sample Game 3 was not
used in development, validation, or illustration.

### 3.2 IDSSE / DFL external validation

The principal external temporal analysis used seven complete professional
matches from the IDSSE/DFL tracking environment, accessed under authorized
provider terms. This environment tested whether the already specified temporal
measurement and its time-ordered association transported beyond the Metrica
sample. It also supplied the primary external analysis of starting-context
characteristics and the movement-direction comparison.

The seven matches are independent external matches, not seven provider
replications or a league-wide population estimate. The aim was replication of a
pre-specified measurement in a distinct tracking environment, with its own
provider-compatible support and inference procedures.

### 3.3 SkillCorner Open Data directional replication

A separate directional replication used nine usable 2024/25 A-League matches
from SkillCorner Open Data. This broadcast-derived tracking environment was used
only for the outward-versus-goalward comparison. Pre-specified compatibility
rules handled provider status and extrapolation information before modelling.

SkillCorner and IDSSE were analysed separately. Their results were not pooled
across providers because the environments retain different data-generating and
provider-processing conditions, as well as separate pre-specified models,
interval conventions, and support checks.

### 3.4 Availability and publication scope

Metrica and SkillCorner data are available under their respective open-data
terms. IDSSE data require authorized provider access. The public repository
contains implementation, protocols, compact governed summaries, figure
artifacts, and reproducibility guidance. To respect the project's conservative
publication boundary and provider terms, it does not commit row-level,
reconstructive, or other detailed provider-derived tracking tables. Full
coordinate handling, eligibility, support, and implementation details are
available in the supplement and repository documentation.

## 4. Methods

### 4.1 Analysis unit and attacker movement

The analysis unit was a supported attacker-time anchor during open play. Each
anchor defined three consecutive two-second intervals: a context interval
([t-4,t-2]), an attacker-exposure interval ([t-2,t]), and a subsequent
defender-response interval ([t,t+2]). The separation between exposure and
outcome is central to the estimand. Attacker movement is treated as an observed
exposure, not as a causal treatment or a tactical label.

For each eligible attacker and anchor, we calculated path length and signed
displacement from the attacker's standardized tracking coordinates during the
exposure interval. Eligibility required complete temporal support under the
pre-specified cadence and endpoint rules and excluded restarts, ball-out
intervals, and unsupported player tracking. These restrictions define a
reproducible measurement sample; they do not imply that every retained interval
is a run, a threat, or a meaningful attacking action.

The same standardized orientation was used to make signed movement comparable
within each analysis environment. This permits path magnitude and the two signed
displacement components to be separated rather than treating all movement of
the same length as geometrically equivalent. The outcome interval begins only
after the exposure interval ends, so a defender's later movement is not used to
construct the attacker's movement quantity.

### 4.2 Defender-relative representation

For each focal defender \(d\), position was expressed relative to the other
nine defending outfield players,

\[
\mathbf r_d(t)=\mathbf x_d(t)-\frac{1}{9}\sum_{j\ne d}\mathbf x_j(t),
\]

where \(\mathbf x_d(t)\) is the focal defender's position. The primary local
outcome was accumulated path in \(\mathbf r_d(t)\) over the response interval.
This outcome describes how much the defender moved relative to the defensive
unit. It therefore reduces the contribution of a shared translation without
assuming that collective translation is unimportant or absent.

The leave-one-out reference is a transparent form of centroid-relative
geometry. If \(\mathbf c\) is the centroid of all ten defending outfield
players and \(\mathbf c_{-d}\) is the centroid excluding defender \(d\), then

\[
\mathbf x_d-\mathbf c_{-d}=\tfrac{10}{9}(\mathbf x_d-\mathbf c).
\]

For a complete ten-defender set, leave-one-out centering is consequently a
constant rescaling of ordinary centroid-relative position. It cannot create a
near-versus-middle rank pattern mechanically. Its practical benefit is that the
reference is explicitly the defender's teammates rather than a group including
the focal defender.

### 4.3 Temporal ordering and start-fixed proximity groups

At the response boundary \(t\), all ten defending outfield players were ranked
by their Euclidean distance from the focal attacker. The resulting ranks were
held fixed for the following response interval. The primary local group was the
three nearest defenders (D1–D3); the pre-specified reference group was the four
middle-ranked defenders (D4–D7). The three farthest defenders (D8–D10) were
retained for descriptive rank profiles rather than the primary contrast.

This design makes proximity a property of the observed starting geometry, not a
property selected after defenders have moved. It reduces post-response selection
while retaining the complete defensive block for the leave-one-out reference.
The ranks are not inferred marking assignments: a nearby defender may be
screening space, holding a line, covering another player, or moving for reasons
not observed in the available variables. The comparison is therefore local
versus middle-distance geometry, not a comparison of responsible versus
non-responsible defenders.

Rank groups were intentionally used as a transparent local-versus-reference
comparison rather than as a claim that a fixed metric radius has the same
meaning in every passage. They preserve all ten outfield defenders in the
representation, accommodate variation in local defensive density, and leave the
full D1–D10 profile available for inspection. They do not remove possible shared
context between attackers and defenders; that concern motivates the temporal
comparison and the stated inference boundary rather than an assignment
interpretation of rank.

### 4.4 Primary temporal association and reverse-time comparison

The primary temporal models estimated the association between attacker path
during \([t-2,t]\) and focal defender-relative path during \([t,t+2]\), with
separate terms by start-fixed defender rank. Models conditioned on
pre-interval movement and spatial context only; they did not use future
information to define the exposure or select defenders. The headline quantity
was the pre-specified near-minus-middle contrast: the difference between the
attacker-path association for D1–D3 and the corresponding association for
D4–D7.

A positive contrast would indicate that greater preceding attacker movement was
associated with more subsequent defender-relative movement among nearby ranks
than among the middle-distance reference ranks. It would not establish that the
attacker caused that movement, that nearby defenders were assigned to the
attacker, or that the movement was tactically successful.

To assess time ordering against background structure in continuous play, we
used a paired reverse-time comparison constructed with the same measurement
logic in the opposite temporal order. The relevant check was whether the
forward-time near-minus-middle association exceeded its paired reverse-time
counterpart. Reverse-time estimates were not expected to be zero: football
movement contains persistence and shared context in either direction. The
comparison therefore tests an ordered excess, not the absence of geometric
structure in the control.

### 4.5 Movement-direction analysis

The directional analysis decomposed attacker displacement into the pre-specified
goalward/away-from-goal axis and outward/inward axis. Outward movement means
movement away from the pitch centreline under the standardized orientation; it
does not mean movement away from goal. The primary directional contrast compared
outward with goalward displacement while conditioning on attacker path magnitude
and the specified starting geometry. This asks whether movements of comparable
overall size, beginning in comparable observed contexts, were associated with
different subsequent localized defender-relative movement.

IDSSE was the primary directional environment. SkillCorner provided a separate
external replication using provider-compatible support, status, and
extrapolation rules specified before the directional outcome was examined. The
two environments used separate models and inference procedures and were not
pooled. Signed directions remain geometric descriptors: they do not label a run
type, identify a tactical intention, or determine whether an attacker caused a
defensive action.

The directional comparison is not a contest between two mutually exclusive
football actions. A two-dimensional path can contain both goalward and outward
components. The model therefore compares their conditional associations while
holding the observed path magnitude and specified starting geometry in view. It
is designed to ask whether the direction of a comparable movement is associated
with a different local defender-relative pattern, not whether one named action
is intrinsically more valuable than another.

### 4.6 Starting-context characterization

Separate models characterized heterogeneity in the temporal association using
two observed quantities at the start of the exposure interval: the attacker's
goalward position relative to the defensive-unit centroid and the attacker's
distance from the ball. The first locates the attacker relative to the unit's
depth; the second locates the attacker relative to the immediate ball context.

These analyses answer a descriptive “when” question: in what observed starting
geometry was the local temporal association larger or smaller? They do not
identify why that geometry occurred, whether it reflected a tactical plan, or a
complete set of situational influences. The context models were therefore kept
separate from the primary temporal and directional estimands.

### 4.7 Response-scale follow-up

Defensive movement can be represented at several scales. In addition to the
established local defender-relative outcome, follow-up analyses retained
defensive-unit centroid translation and pitch-axis width as separate outcomes.
Centroid translation captures a shared collective shift that the local outcome
largely removes. Width reduction tests one specific proposed geometric
mechanism: whether a directional difference in local reorganization is
accompanied by a narrowing of the defensive unit.

These follow-ups were secondary and nonclassifying. They were not combined into
a composite response score, and the analysis did not allocate observed movement
into exclusive local and collective shares. In particular, a collective shift
can coexist with local reorganization, and a width result alone would not
establish a tactical mechanism.

### 4.8 Validation and inference

The temporal measurement was developed in Metrica Game 1 and evaluated without
revision in protected Metrica Game 2. The external IDSSE analysis tested the
time-ordered association in a distinct tracking environment. The SkillCorner
analysis then tested the directional comparison separately. Across these stages,
the central analysis rules and result sequence were specified before protected
outcomes were inspected; this is described here as prospective testing, not
external preregistration.

Uncertainty was quantified with the pre-specified grouped block-bootstrap
procedures appropriate to the temporal dependence of tracking observations.
Robustness checks included the paired reverse-time comparison, alternative
pre-specified response horizons, movement trimming, complete-support checks,
and match-level or leave-one-match-out sign checks where applicable. Coordinate,
support, invariance, provider-compatibility, and reproducibility checks are
reported in the supplement and repository materials. The resulting intervals
and replications describe observational associations under provider-specific
inference; they do not supply a pooled cross-provider effect or a causal
estimate.

The validation sequence also distinguishes development, protected testing, and
external transport. Metrica Game 1 was used to establish the temporal
measurement; Metrica Game 2 tested that unchanged analysis within the same
sample-data setting. IDSSE then evaluated the temporal association in a
separate professional tracking environment. SkillCorner was reserved for the
directional replication and was analysed under its own compatibility rules.
This staged design strengthens the measurement evidence without converting
agreement across data environments into proof of a common causal mechanism.

## 5. Results

### 5.1 Time-ordered localized defensive reorganization

The first result concerns whether attacker movement was associated with later
defender movement relative to the defensive unit more strongly among the three
start-nearest defenders than among the four middle-ranked defenders. In pooled
Metrica, this near-minus-middle association was 0.05029 m/m (97.5% interval
[0.03433, 0.06858]). Here, m/m expresses the modeled difference in subsequent
defender-relative path associated with one additional metre of preceding
attacker path. The positive estimate was present in both the development and
protected heldout matches (0.04559 and 0.08553 m/m, respectively).

The same time-ordered pattern appeared in the external IDSSE analysis. The
near-minus-middle estimate was 0.06115 m/m (95% CI [0.05579, 0.06681]), with a
positive primary estimate in all 7/7 matches. The paired forward-minus-reverse
excess was 0.02455 m/m [0.01932, 0.02985], also positive in all 7/7 match-level
estimates. Thus, the forward-time association was stronger than its paired
reverse-time counterpart under the pre-specified comparison.

The reverse-time association itself remained positive. The control therefore
did not imply an absence of movement structure in the opposite ordering;
rather, it showed that continuous football movement contains shared and
persistent geometry in both directions. The relevant evidence is the paired
forward-time excess, not a null control. The direction of the primary estimate
also remained positive in the pre-specified duration and trimming checks.

Taken together, these estimates locate the pattern in defender-relative rather
than absolute movement and retain the temporal ordering specified in the design.

Figure 1 combines a real protected-holdout Metrica passage with the population
estimate and its forward-versus-reverse qualification. The passage is intended
to make the measurement legible: individual defenders need not move in one
common direction for their movement relative to the unit to differ from a
shared defensive shift. It is an explanatory example, not evidence that a
single attacker caused the observed movement.

### 5.2 Movement direction: outward-versus-goalward difference

The central empirical result was a replicated outward-versus-goalward difference
in the movement-direction association. The directional models compared signed
attacker displacement components conditional on overall path magnitude and the
pre-specified starting geometry. Outward movement denotes movement away from the
pitch centreline under the standardized orientation; it is not another term for
movement away from goal.

In IDSSE, outward minus goalward displacement was associated with 0.056856 m/m
more subsequent localized defender-relative reorganization (95% CI [0.051358,
0.062430]). The contrast was positive in all 7/7 match-specific fits and all
7/7 leave-one-match-out fits. Expressed on the observed scale, a 5 m comparison
of outward rather than goalward movement corresponded to approximately 0.284 m
more subsequent localized defender-relative reorganization under the
pre-specified model. This is a descriptive translation of the model contrast,
not an estimate of the movement that an individual attacker caused.

The directional result replicated in the separate SkillCorner analysis. In the
broadcast-derived tracking environment, the outward-minus-goalward estimate was
0.048883 m/m (95% CI [0.042940, 0.054707]). It was positive in all 9/9
match-specific and all 9/9 leave-one-match-out fits. SkillCorner was analysed as
an independent provider-specific replication under its own compatibility and
support rules; its estimate was not pooled with IDSSE.

The two estimates have the same conditional interpretation but arise from
separate models, samples, and provider-specific inference procedures. Their
similar positive direction is therefore replication evidence rather than a
claim that the environments have identical coordinates, player populations, or
underlying tactical conditions. In both environments, the directional contrast
remained a comparison of observed movement components within supported passages;
it was not a label for a run type and did not depend on an inferred marker or a
measured attacking outcome.

The result also differs from a simple description of where attackers travelled.
The models account for total path magnitude, so the outward-versus-goalward
contrast is not merely a statement that one direction involved longer paths.
Likewise, the starting-geometry terms ensure that the reported association is
not a comparison of all outward movements with all goalward movements regardless
of their observed initial locations. Those controls narrow the geometric
comparison; they do not eliminate unobserved football context.

Figure 2 presents the two external environments side by side. Their agreement
is notable because the result is directional, conditional, and measured from
subsequent defender-relative movement rather than from an outcome such as a
reception, pass, shot, or value estimate. The finding does not rank football
actions. It says that, among movements of comparable magnitude and observed
starting geometry, localized defensive reorganization was not simply aligned
with movement toward goal. The result does not establish that outward movement
is superior, that it dragged defenders, or that it created attacking value.

### 5.3 Starting context

Starting context characterized where the localized temporal association was
larger or smaller; it was not used to define a tactical class. The association
declined with the attacker's goalward position relative to the defensive unit
(−0.010161 m/m, 97.5% CI [−0.011805, −0.008499]). Thus, within the modeled
starting geometry, localized reorganization was larger when attackers began
less far goalward relative to the unit. The estimate had the same direction in
all 7/7 match-specific and 7/7 leave-one-match-out fits, and retained its
direction after the pre-specified trim.

The association also declined with attacker-ball distance (−0.007533 m/m,
97.5% CI [−0.008864, −0.006245]). Localized reorganization was therefore larger
when attackers began closer to the ball under this characterization. This
direction was likewise consistent in all 7/7 match-specific and 7/7
leave-one-match-out fits and under trimming. These results describe observed
context around the measurement. They do not identify between-the-lines
occupation, pressing triggers, decoy movement, or an optimal attacking
position.

The context findings remained secondary descriptive results: they characterize
the observed setting of the temporal association rather than its mechanism.

### 5.4 Response-scale boundary

The response-scale follow-up was secondary and nonclassifying. A 5 m
goalward-versus-outward contrast was associated with 2.962709 m of collective
defensive-centroid translation [2.870720, 3.048322], with positive estimates in
all 7/7 match-specific and 7/7 leave-one-match-out fits. Goalward movement thus
showed a strong descriptive association with a shared defensive shift, whereas
outward movement showed the stronger localized defender-relative association.

The proposed inward-versus-outward narrowing mechanism was not established.
Its width contrast was 0.134003 m [−0.006622, 0.273430], positive in 5/7
matches and therefore classified as MIXED. Goalward and outward movement can
coincide with different observable scales of defensive movement, but the
mechanism underlying the directional difference remains unresolved.

Because the local and collective outcomes were estimated separately, neither
result is a decomposition of total defensive movement into exclusive parts.

## 6. Discussion

### 6.1 What the temporal result establishes

The temporal analysis establishes a bounded measurement result. When attacker
movement was measured before the outcome interval, nearby defenders showed a
stronger subsequent association in defender-relative movement than the
middle-ranked reference group. Because focal position was expressed relative to
the rest of the defensive unit, this association is distinct from a simple
statement that defenders or teams moved a long way in absolute pitch
coordinates. The start-fixed rank construction further ensures that locality
was determined before the response interval, rather than chosen because a
defender's later movement appeared noteworthy.

The paired reverse-time comparison matters for interpreting that result. The
control retained directional structure, as is plausible in a continuous game in
which player motion, team shape, and ball context persist across neighbouring
intervals. The forward association nevertheless exceeded the matched
reverse-time association. This supports a time-ordered geometric association;
it does not identify a response latency or convert the association into a
causal reaction signal.

Player-to-team geometry is already an established tracking-data substrate
(Sampaio and Maçãs, 2012; Duarte, Araújo, and Correia, 2013; Carrilho et al.,
2020). Temporal coordination and defensive disruption have also been studied
(Moura et al., 2016; Forcher et al., 2021). The contribution here is narrower:
a prospectively ordered local-response estimand, proximity localization fixed
before later defender movement, and a validation design that includes protected
testing, a paired temporal control, and external replication. The result should
be read as evidence for that measurement construction, not as a general theory
of why defending players move.

### 6.2 Why the movement-direction difference matters

The replicated directional difference is the paper's most distinctive empirical
finding. Football discourse often gives special weight to movement toward goal,
because goalward progression is connected to advancing the ball and eventually
to shooting opportunity. Yet the direction more strongly associated with later
localized defender-relative reorganization was outward movement—movement away
from the pitch centreline—not simply goalward movement. Under the specified
comparison, progression and localized defensive reorganization were therefore
different observable dimensions of off-ball movement.

This interpretation is deliberately narrower than a claim about a preferred
action. The analyses condition on path magnitude and starting geometry, but
they do not observe every tactical and game-state factor that may jointly shape
attacker and defender movement. Nor do they establish that an attacker forced a
defender to move. They show that comparable signed components of off-ball
movement were associated with different subsequent local defensive geometry.

The finding sits beside, rather than above, existing work on direction and
attacker-defender interaction. Caetano et al. (2023) separated lateral and
longitudinal components of coordination in opponent dyads, while Narizuka and
Yamazaki (2025) decomposed directional components in an on-ball
attacker-defender model. Pressure-oriented analyses follow a different
individual defensive outcome (Herold et al., 2022), and space/control or value
frameworks address whether and where actions expand opportunity (Fernández and
Bornn, 2018). The present paper asks a different question: how signed attacker
movement is associated with later movement by defenders relative to their own
unit.

The reviewed literature did not identify a direct controlled comparison of
outward and goalward off-ball movement against this subsequent localized
defender-relative estimand. That gap is specific and limited. Temporal response
and directional coordination are not new concepts, nor is cross-environment
validation a general innovation. The evidence is stronger because the
outward-versus-goalward difference replicated separately in IDSSE and
SkillCorner, independent tracking environments with different support and
processing conditions. They are corroborating replications, not ingredients of
a pooled cross-provider effect.

This distinction has a useful football-facing consequence. An analyst can keep
movement toward goal and movement across the pitch conceptually separate when
asking which passages may merit closer review. A movement's contribution to
progression is not the same thing as its observed association with internal
defensive reorganization. Whether either dimension reflects a named movement
such as an overlap, a decoy, a check, or a positional rotation remains a
question for video and tactical context, not for the present measurement alone.

### 6.3 Collective and localized defensive scales

The response-scale results help explain why absolute defender movement is an
insufficient starting point. Goalward attacker movement had a strong descriptive
association with collective defensive-centroid translation, whereas outward
movement had the stronger association with localized defender-relative
reorganization. These results concern different geometric scales. A defensive
unit can shift together and also deform internally; local and collective
movement are neither mutually exclusive categories nor fixed shares of a common
response.

This distinction should not be turned into a mechanism after the fact. The
pre-specified width analysis tested whether an inward-versus-outward narrowing
pattern could account for the directional result, and its MIXED status did not
provide sufficient evidence. Other changes in defensive geometry may be
possible, but they were not tested here as explanations. The appropriate
conclusion is therefore a boundary: the directional difference is visible at a
localized defender-relative scale, while the proposed narrowing mechanism
remains unresolved.

Collective and local measures can be useful complements in analysis, provided
they remain separate. A collective shift may be the dominant geometry of one
passage; in another, a defender's departure from the unit may be more salient.
Neither description assigns intent, responsibility, or defensive quality. The
present results provide a way to retain that distinction without reducing it to
a single composite score.

### 6.4 Starting geometry

The starting-context results characterize the conditions under which the local
temporal association was larger in the IDSSE analysis. It was larger when the
attacker began less far goalward relative to the defensive unit and closer to
the ball. These observed contextual relationships are compatible with the idea
that the same path may have different geometric meaning in different locations,
but they do not identify why an attacker started there or why the defensive unit
was arranged as observed.

This is an important distinction from pressure, availability, and ball-control
research. Those literatures may describe nearby football questions, but they do
not make ball proximity or relative depth a tactical label in this analysis.
The estimates are descriptive characterizations of association heterogeneity,
not evidence for an optimal starting position, a pressing trigger, or a
particular tactical template.

### 6.5 Analyst use

The measurement is best understood as a filtering and descriptive layer for
analyst review. It can distinguish a passage dominated by a shared defensive
shift from one in which defender movement relative to the unit is more
pronounced, then characterize the movement direction and starting geometry
associated with that measured pattern. An analyst could use those quantities to
surface passages for video review, where ball movement, teammates, opponents,
and the tactical phase can be assessed together.

That workflow is intentionally modest. It does not automatically label pinning,
dragging, tracking, covering, a handoff, or any other tactical concept. It does
not rank players, identify correct defensive decisions, or produce an attacking
value estimate. The Defensive Reorganization Departure application test did not
reach its formal threshold and is not the basis of the practical claim here.
Passage retrieval is plausible as an analyst workflow, but it has not yet been
independently validated for usefulness or semantic accuracy.

### 6.6 Limitations and interpretation boundaries

Several limitations determine the appropriate scope of the findings. First, the
design is observational. Temporal ordering and a paired reverse-time comparison
reduce some forms of ambiguity, but they cannot remove shared game context or
show that an attacker caused defenders to move. Start-fixed proximity ranks are
localization devices, not marking assignments; the analysis does not identify
responsibility, attention, instruction, or tactical intent. Independent human
semantic validation of what high measured reorganization corresponds to in
football language has not yet been completed.

Second, the analysis does not establish a downstream attacking consequence. In
Opportunity Redistribution v1, greater focal-local defensive geometric change
was not associated with relatively improved nearest-defender separation for
other initially local attackers (\(\beta_D=-0.02407\), 95% bootstrap interval
[−0.09392, 0.04776]). That result is an interpretation boundary rather than a
metric to tune until positive: localized reorganization should not be equated
with demonstrated space creation, attacking value, or tactical success.

Third, the samples and tracking environments remain limited. Metrica provides
two open sample matches, while IDSSE supplies seven authorized professional
matches. SkillCorner uses broadcast-derived tracking and requires its own
provider-compatible support and extrapolation handling. The external estimates
were intentionally not pooled, and Metrica Game 3 was not used. These features
support a staged replication argument, not population-wide generalization or
provider interchangeability.

Finally, the mechanism remains incomplete. The width test was mixed, and the
local and collective response channels are not an exhaustive or orthogonal
description of defensive geometry. The observed directional difference is
therefore a well-specified association, not an explanation of how a defensive
unit reorganized in every passage.

### 6.7 Future work

The next steps should strengthen interpretation rather than add a new score.
One option is independent semantic and video-based validation of whether
analysts judge passages with different measured geometry as meaningfully
different; any such work remains a future direction rather than an active
reviewer study. Broader replication across teams, competitions, and tracking
systems would test the scope of the measurement, while richer video and
match-state context could support more careful football interpretation.

Downstream consequence or value models should be pursued only when grounded in
an independently motivated construct and after semantic validity is clearer.
Artificial-transition work is likewise a post-Sloan extension, not part of the
present evidence. The immediate task is to preserve a transparent measurement
layer that can be challenged, replicated, and used alongside—not instead of—an
analyst's football judgment.

## 7. Conclusion

This paper reports a reproducible temporal measurement of localized defensive
reorganization associated with preceding off-ball movement. Nearby defenders
showed a stronger subsequent defender-relative association than middle-ranked
defenders, and the time-ordered association replicated beyond the Metrica sample
in IDSSE. The main directional result also replicated across IDSSE and
SkillCorner: conditional on movement magnitude and observed starting geometry,
outward movement away from the pitch centreline was associated with stronger
subsequent localized defender-relative reorganization than goalward movement.

The results distinguish a shared defensive shift from internal movement within
the defensive unit. Goalward movement was more strongly associated with
collective translation, whereas outward movement showed the stronger localized
association. These are complementary observable scales, not a complete tactical
mechanism. The measure can help organize later video and football analysis, but
it does not establish attacker causation, marking responsibility, tactical
intent, defensive quality, space creation, or attacking value. Its concrete
contribution is a bounded, externally replicated way to describe where
off-ball movement and localized defensive geometry are associated over time.

## Supplement plan

- **S1 — Representation and eligibility:** coordinate contract; complete
  support; smoothing; endpoint, timing, tie, and numerical-boundary rules.
- **S2 — Full temporal results:** complete statistics, D1–D10 profiles,
  regional estimates, horizons, trimming, reverse-time/placebo results, and
  all match-level external estimates.
- **S3 — Validation and provenance:** Metrica holdout, provider-equivalence
  checks, bootstrap and reproducibility materials, hash ledgers, and
  regeneration pointers.
- **S4 — Additional geometry:** concurrent geometry/coordination, rank
  composition and synthetic audits, starting-context diagnostics, and the full
  response-scale follow-up.
- **S5 — Directional detail:** IDSSE and SkillCorner compatibility checks,
  separate provider-specific specifications, sensitivity results, and complete
  movement-direction tables.
- **S6 — Boundary findings:** Opportunity Redistribution, Defensive Coverage,
  Defensive Response Expectation, and other negative or mixed outcomes.
- **S7 — Additional visuals:** D1–D10, context, response-scale, robustness,
  and provider-equivalence figures. The comprehensive results table is
  supplementary for a two-slot Sloan package.

## Internal drafting decisions

- **Skeptical-reviewer guidance — Why is this not just another
  centroid-relative metric?** Centroid-relative geometry is the substrate. The
  contribution is the pre-specified attacker interval, subsequent
  non-overlapping defender interval, proximity fixed before response,
  near-versus-middle localization contrast, temporal controls, and external
  replication.
- **Skeptical-reviewer guidance — What did we learn about football?** Comparable
  movement directions were not associated with the same localized defensive
  geometry: outward movement showed a stronger subsequent localized association
  than goalward movement across independent tracking environments.
- Treat assignment-free geometry and the absence of a downstream value model as
  interpretability and scope choices, not inventions. Do not claim that all
  earlier work requires inferred marking assignments or a value model.

- Main paper: Figure 1 is the temporal flagship; Figure 2 is the
  outward-versus-goalward external replication. All other result visuals are
  supplementary unless venue rules require otherwise.
- Keep concurrent geometry/coordination to one contextual sentence in the main
  paper, if retained at all; its full result is supplementary because it shares
  the attacker and defender interval.
- Do not promote Opportunity Redistribution, Defensive Coverage, Defensive
  Response Expectation, segmentation, or construct-development branches into
  headline results. They remain boundary evidence in repository and supplement
  materials as specified above.
- Before polished prose: confirm target venue and word limit, author list,
  citation style, data-access language, and final figure typography.
