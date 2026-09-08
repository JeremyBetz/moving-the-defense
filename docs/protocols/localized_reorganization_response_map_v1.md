# Localized Reorganization Response Map v1

**Status:** **FROZEN PRE-RESPONSE IMPLEMENTATION; RESPONSE ACCESS NOT YET AUTHORIZED**

**Freeze date:** 2026-09-07
**Starting commit:** `079fbd49c8756c71cc2db200b7a80aa7beb4fede`
**Execution tier after authorization:** Tier 2

**Pre-access closure hardening:** deterministic reproduction, no-overwrite, and
final-ledger mechanics were clarified before any response access. They do not
change the estimand, sample, mask, bandwidth, weighting, or display scale.

## Purpose and firewall

This protocol governs one descriptive IDSSE-only visualization of the already
governed two-second localized defensive-reorganization outcome. It does not
define a new response, fit a model, test a hypothesis, or alter a scientific
claim. The protected registry and `response_2s_m` remain unread until an
explicit later execution authorization names this frozen protocol.

The map may not be used to claim causation, tactical preference, disruption,
space creation, gravity, value, or recommended attacker locations.

## Frozen population, location, and outcome

Use exactly the seven governed IDSSE matches, in this order:
`J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, `J03WR9`.
The anchor population is the complete governed temporal-footprint population:
72,316 attacker-anchor observations, each with one fixed D1--D10 vector.

For anchor \(i\) in match \(m\), use the centred-seven-frame attacker position
at \(t-2\) seconds, with

\[
x_{plot}=s_{attack}x_{provider},\qquad y_{plot}=y_{provider}.
\]

Physical provider y is not reflected. Plotted left means deeper and plotted
right means goalward; vertical position is provider physical lateral position,
not a player-relative tactical-side label.

The sole permitted outcome field is governed `response_2s_m`, the
focal-relative defender path over \([t,t+2]\) in metres. For every complete
anchor,

\[
Y_{im}=\frac{1}{3}\sum_{r=1}^{3}R_{imr}
-\frac{1}{4}\sum_{r=4}^{7}R_{imr},
\]

where \(R_{imr}=\texttt{response\_2s\_m}\) at fixed rank \(r\). D8--D10,
other response horizons, path fields, predictions, residuals, and all other
outcomes are prohibited.

## Frozen spatial estimator

Evaluate legal 1 m grid centres on a 105 by 68 m pitch. Use a Gaussian kernel
with radius truncated at \(2h\), primary \(h=7.5\) m, and fixed sensitivities
\(h=5\) and \(10\) m. Let \(z_{im}\) be the native retained attacker start
coordinate and \(g\) a grid location:

\[
w_{imh}(g)=\mathbf1\{\lVert z_{im}-g\rVert\le2h\}
\exp\left[-\frac{\lVert z_{im}-g\rVert^2}{2h^2}\right].
\]

Compute one ordinary weighted local mean within each match,

\[
\mu_{mh}(g)=\frac{\sum_i w_{imh}(g)Y_{im}}{\sum_i w_{imh}(g)},
\]

then average the seven match means equally:

\[
\mu_h(g)=\frac{1}{7}\sum_{m=1}^{7}\mu_{mh}(g).
\]

This is not a row-pooled estimator. Native out-of-pitch anchors remain in
kernel calculations; they are never clipped, reflected, excluded, or
boundary-corrected. Only legal-pitch grid locations are evaluated or rendered.

## Frozen support and missingness policy

Use the saved response-blind Conservative mask separately for each bandwidth:
6,373 valid cells at 5 m, 6,979 at 7.5 m, and 7,132 at 10 m. A cell that fails
its saved mask receives no response value and is not rendered. Cross-bandwidth
description is limited to the response-blind common 6,373-cell intersection.

Execution is invalid, rather than complete-case filtered, if a required D1--D7
response is missing or nonfinite, rank identity is incomplete or duplicated,
the response identity join is incomplete, a displayed cell has a nonpositive
or nonfinite denominator in any match, a saved support mask differs, the input
hash differs, or the selected response field differs.

## Shared colour scale

For match \(m\) with \(n_m\) eligible anchors, give each anchor weight
\(1/(7n_m)\). Sort the observed \(|Y_{im}|\) values ascending, with
`observation_id` only as a deterministic tie order. Set \(L\) to the smallest
observed \(|Y_{im}|\) whose cumulative weight is at least 0.95. This is a
weighted inverse empirical CDF: no interpolation and no rounding before
selection.

All panels use \([-L,L]\). The raw aggregate surface is never clipped; only
display values may saturate, and each panel reports saturation counts with an
explicit colorbar/caption disclosure. If \(L=0\) with any nonzero surface
value, execution is invalid. If \(L=0\) and every surface value is zero, the
execution is valid but uninformative and renders a neutral map.

## Outputs, figure, and interpretation

The only public result files may be the frozen compact CSV/JSON package and a
three-panel PNG/SVG figure. No output may contain anchor rows, identities,
timestamps, rank rows, coordinates, per-match surfaces, or row-level \(Y\).

The primary authoritative output and figure destinations must not already
exist. Execution fails closed rather than overwriting them, with the operator
directed to use a clean/disposable environment or an explicitly isolated
reproduction destination. Both the primary calculation and an independent
rerun are first generated in isolated temporary roots. Their aggregate CSV/JSON
outputs and PNG/SVG figures must be byte-identical under the current platform
policy before the primary package is promoted to its authoritative paths.

`reproduction.json` records only explicitly labeled primary and independent
rerun **pre-closure staging** identities, their equality outcome, the frozen
identities, authorization reference, and compact runtime metadata. It does not
claim that a staging manifest hash is an authoritative final-file hash.
`final_hashes.json` is the sole authority for the closed authoritative CSV/JSON
package and PNG/SVG figures, while excluding its own recursive hash.

After staging comparison and final-ledger creation, promotion is ordered PNG,
SVG, then finalized output directory last. Thus an authoritative valid-status
manifest cannot appear before both figures. The final ledger is re-read and
validated against the promoted authoritative paths before success returns.

Panel A is the primary 7.5 m surface, Panel B the 5 m sensitivity, and Panel C
the 10 m sensitivity. Rendering is cell-based with no spatial interpolation,
a shared symmetric scale, and clearly gray failed-mask cells. No confidence,
significance, or tactical overlays are permitted.

Colorbar extensions are derived from actual display saturation: neither, max,
min, or both for no clipping, positive-only, negative-only, or two-sided
clipping respectively. Each panel and the figure footer disclose the observed
negative/positive saturation counts.

There is no `SUPPORTED`, `MIXED`, or `NOT SUPPORTED` classification. A valid
execution is `DESCRIPTIVE RESPONSE MAP EXECUTED — QC PASSED`; a mechanical
failure is `DESCRIPTIVE RESPONSE MAP INVALID`. A weak, flat, or
bandwidth-sensitive map is valid descriptive evidence, not an execution
failure. The default destination is repository/future-full-paper material, not
the current Sloan manuscript or its two-figure package.

## Stop rule and closure

After the first authorized execution, inspect only the three frozen surfaces
and the compact summaries/QC. Do not change bandwidth, mask, scale, zones,
weighting, estimator, response field, or diagnostics. Do not create individual
match or leave-one-match-out surfaces. Any follow-up requires a new
prospective plan and explicit approval.

Tier-2 closure requires frozen-input verification, deterministic rerun,
aggregate-schema validation, publication-boundary checks, hashes, a concise
result report, and explicit human authorization before response access. The
authorization reference recorded by the command is provenance only; it does
not independently prove authorization.
