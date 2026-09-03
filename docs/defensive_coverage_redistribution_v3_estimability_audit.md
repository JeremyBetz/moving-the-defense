# Defensive Coverage Redistribution v3 — Prospective Estimability Audit

**Audit date:** 2026-09-03

**Starting checkpoint:** `a4b4a9ab301651c97aab5c024e6254b89a406f57`

**Verdict:** **A — PROSPECTIVE V3 WITH CONSTANT-NUISANCE OMISSION IS PRINCIPLED**

## Outcome-blind support diagnosis

V2 retained 281 eligible anchors, all in period 1. Period 2 contained 737
candidate anchors after grid/window construction. Before player support was
checked, 58 were excluded for restart/ball-out spans, 51 for an opposing
possession-defining event, and 9 for no possession team. Of the remaining 619,
501 first failed the complete-ten-attacker check and 118 first failed the
complete-ten-defender check. The recorded attacker availability was nine at
499 anchors and eight at two; recorded defender availability was nine at 118.

This is the legitimate result of the frozen support rules, not a coding defect.
The inherited outcome-blind trajectory registry invalidates Home 3 and Away 22
for all of period 2 because of unresolved discontinuities near provider frames
71,279 and 71,287. One outfield identity per team is therefore unavailable
throughout the period. Because v2 requires all ten attacking and all ten
defending outfield players simultaneously, no period-2 anchor can qualify. The
implementation records only the first support failure, so the 501/118 split
does not mean the opposite side had ten valid players.

The recorded attacker failures comprise 129 Away-attacking anchors and 372
Home-attacking anchors; 370 of the latter had nine available attackers and two
had eight. The 118 recorded defender failures occurred when Away had ten
supported attackers but Home still had only nine supported defenders. A
separate outcome-blind support check, used only to diagnose the waterfall,
found that 613 of the 619 event-passing anchors would have had raw complete
ten-versus-ten support without the two whole-period registry invalidations.
The other six also crossed an ordinary entry/exit or support transition. No
scientific eligibility rule is changed by that diagnostic.

No period-2 anchor reached the later ball-support or reference-selection
checks. Therefore zero recorded period-2 ball exclusions is not evidence that
ball support would have passed; it is simply downstream of the decisive player-
support failure. The anchor grid itself produced no recorded exact-frame or
period-edge failure. Substitution/roster handling did not restore simultaneous
complete support. Away substitutions produced ten supported attackers at 118
anchors, but Home still had only nine supported defenders; no event-eligible
anchor had ten supported outfield players on both sides at once.

The immediate cause is Game-1-specific: the registry explicitly says these are
development support decisions, not a provider-general validity rule. The same
problem is nevertheless possible wherever complete-set eligibility meets a
provider/period with one unsupported outfield identity. Existing outcome-blind
Game 2 and IDSSE support metadata includes supported second-period/second-half
windows, so it does not imply the same whole-period collapse. Their separate
registries can still create local attrition, and the coverage construct's
additional all-ten-attacker condition has not been preflighted there. No Game 2
or IDSSE coverage outcome was inspected, so future coverage feasibility remains
unknown until a separately authorized metadata check.

## Role of the period indicator and linear algebra

$P_2$ is category **C: a non-scientific nuisance indicator intended only to
absorb a period-level mean difference**. It is not the response, the primary
predictor, a classifying contrast, or a required within-period source of
identification for $\beta_D$.

Let $X=[X_s\;p]$, where $X_s$ contains the intercept and all scientific
columns. If the eligible sample is period 1 only, $p=0$, so
$\mathcal C(X)=\mathcal C(X_s)$ and $\operatorname{rank}(X)=
\operatorname{rank}(X_s)<\dim(X)$. Removing $p$ leaves exactly the same least-
squares projection, fitted values, residuals, and identifiable coefficients in
$X_s$, including $\beta_D$. If a nuisance dummy is constant one, it duplicates
the intercept; removing the dummy likewise preserves the column space, while
the arbitrary intercept/dummy coefficient split was never identified.

The omission changes neither the sample nor the sample-specific scientific
estimand. With the same active columns and block draws, uncertainty for the
identifiable scientific coefficients is governed by the same projection and
unchanged bootstrap. The nominal parameter count falls to the actual estimable
rank; no scientific degree of freedom is removed. Researcher discretion is
limited by the explicit nuisance allowlist, exact binary constancy, one-time
pre-fit decision, and the rule that every other deficiency remains INVALID.

This does not generalize to a varying scientific column. Dropping one member
of an exact scientific collinearity changes the model's conditional estimand,
and near-collinearity is a stability issue rather than permission for model
selection. Both remain outside the omission rule.

## Model-column audit

The nominal design contains the intercept; primary predictor $D$; scientific
covariates $A,G_0,M_O,B,C,R,A_{pre},D_{pre},B_{pre}$; and nuisance indicator
$P_2$. Only $P_2$ is prospectively designated as non-scientific and eligible
for exact constant-column omission. No raw design column is itself a
classification decision; the fitted $\beta_D$ and its frozen controls enter the
decision tree. No response, scientific covariate, intercept, or classifying
quantity is eligible for omission.

## Development value and researcher discretion

The 281 anchors cover both attacking teams (115 Home, 166 Away) but only one
period of one development match. V2 set no independent minimum-period rule and
did not define two-period representation as part of the estimand. The sample
is therefore potentially useful for a development test once the mechanical
nuisance defect is removed, but any valid result must be labeled period-1-only
and cannot support second-half, substitution-state, match-wide, or external
generalization.

Freezing v3 after learning sample size and period composition is acceptable
only because those are outcome-blind support/estimability facts and no v2
$\beta_D$, interval, direction-null, or robustness result was observed. The
repository must retain v2's INVALID closure, disclose the chronology, limit
the amendment to a deterministic predesignated nuisance rule, and freeze it
before any v3 outcome-model execution. These conditions prevent effect-driven
model repair; they do not make Game 1 held out.

## Options considered

| Option | Assessment |
|---|---|
| A. V3 deterministic constant-nuisance omission | **Selected.** It preserves rows, scientific columns, column space, and $\beta_D$'s estimand while removing only a non-estimable nuisance term. |
| B. Abandon Game 1 | Defensible if two-period representation were independently required, but no such rule was frozen; it discards an otherwise usable development sample without solving the general nuisance problem. |
| C. Weaken support to recover period 2 | Rejected. The exclusions protect against unresolved trajectory discontinuities; changing them merely to gain rows lacks independent scientific justification. |
| D. Use another development dataset | Possible under a separately frozen provider/sample design, but it is unnecessary to repair this mechanical nuisance problem and would trade a known development sample for new provider/support choices. It remains an option if the period-1-only scope is judged scientifically insufficient later. |

Stopping the coverage branch now would also be defensible if the construct were
no longer worth pursuing, but it is not required by this estimability defect:
v1's identification failure was substantive, whereas v2's present obstacle has
an estimand-preserving prospective remedy.

## Core-audit follow-up

For ten defenders, if $c$ is the full-team centroid and $c_{-d}$ excludes
defender $d$, then

$$
x_d-c_{-d}=\frac{10}{9}(x_d-c).
$$

Leave-one-out centering therefore applies the same $10/9$ scale factor to every
rank and cannot by itself manufacture a near-minus-middle pattern. No empirical
test is needed to resolve that narrow algebraic concern.

Start-distance rank can still encode role, zone, depth, and activity. That is a
substantive core-sensitivity issue, not an estimability defect, and the v3
freeze does not repair it. A separately governed, coverage-outcome-blind audit
should precede authorization of v3 empirical execution so that any sensitivity
choice is not informed by the coverage result. It does not block freezing the
otherwise identical v3 model now.

## Decision

V3 freezes only deterministic omission of a predesignated nuisance indicator
that is exactly constant in the complete eligible primary sample. The active
columns are fixed once and reused everywhere. Scientific columns may never be
dropped; any remaining full-rank failure under the inherited estimator policy
is INVALID; near-collinearity does not authorize omission. No v3 empirical
execution occurred in this pass.
