# Defensive Reorganization Departure v1 — Methodology Note

**Status:** prospective design note; no DRD result has been computed.

## Why this application is bounded

The project can already measure how much a defender moves differently from the
rest of the defensive unit and has externally replicated a time-ordered
near-versus-middle localization pattern. It has not shown that such movement is
caused by an attacker or has tactical value. DRD therefore asks a narrower
application question: can ordinary localized reorganization be predicted from
an attacker's own movement and pre-response geometry well enough to retrieve
unusual passages for review?

The direct target is the observed mean D1–D3 focal-relative path minus mean
D4–D7 focal-relative path over the subsequent two seconds. Modelling this
anchor-level geometry avoids turning fitted historical rank coefficients into
new pseudo-observations. Keeping the near and middle components beside the
contrast prevents one scalar from hiding how it arose.

## Why these features

E0 contains only current and prior attacker path. It represents the simplest
movement-only expectation. E1 adds three compact families with direct football
readings:

- signed goalward and outward/inward movement;
- starting position and defensive-unit size; and
- attacker/ball/unit geometry.

No role, run label, assignment, pitch-control value, event outcome, player
identity, or learned embedding enters. The mirrored lateral frame preserves a
signed continuous quantity while treating equivalent left/right starting
locations symmetrically.

The operational off-ball rule excludes the unique attacker nearest the ball at
the anchor. It is a provider-compatible proximity proxy, not observed
ball-carrier identity. This is preferable to inventing a distance threshold or
requiring an event actor at fixed tracking anchors.

## Why prediction must pass before retrieval

Out-of-fold residualization is established statistical infrastructure, not a
novel proof of influence. A passage is useful only if context materially and
consistently improves heldout prediction beyond movement amount. The frozen
3%, six-of-seven, no-10%-worsening, and family-ablation gates deliberately make
retrieval conditional. Examples cannot rescue a weak model.

Even after a supported model, DRD is only observed minus fitted expectation.
The deterministic board avoids the largest 1% of residuals, requires stability
to training-match deletion, suppresses temporal neighbors, and pairs high
departures with near-expected passages from the same match and broad movement/
geometry cell. These safeguards limit numerical and presentation cherry-picks;
they do not validate tactical meaning.

## Development and transport roles

The seven IDSSE matches are the primary nested leave-match-out environment.
Metrica Games 1–2 are already-used secondary transport settings, never tuning
data. SkillCorner remains conditional on a separate outcome-blind support gate
and a later frozen external protocol. Metrica Sample Game 3 remains untouched.

The governed scientific definition is the [v1 protocol](protocols/defensive_reorganization_departure_v1.md)
and its [machine-readable configuration](../config/defensive_reorganization_departure_v1.json).
