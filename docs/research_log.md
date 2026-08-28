# Research Log

## 2026-08-28 — Initial Project Definition

### Motivation

Explore whether off-ball influence in soccer can be quantified through the defensive adjustments induced by attacking movement.

The broader tactical idea is that attacking teams create problems for defenders to solve. Some movements may require little attacking effort while forcing substantial defensive reorganization.

Tracking data cannot directly measure cognition, so the initial observable target will be defensive movement and structural adjustment.

### Initial Behavioral Framework

Four hypothesized defensive movement regimes:

1. Structure
2. Track
3. Close
4. Recover

Working cycle:

**Structure → Track → Close → Recover → Structure**

These are not assumed ground-truth labels.

### Core Reference-Frame Idea

Instead of manually labeling tactical behavior first, compare a defender's movement against competing explanations:

- movement with team structure,
- movement with an opponent,
- movement toward an opponent or ball,
- movement toward an expected structural position.

The central question becomes:

**Which reference frame best explains the defender's movement?**

### Important Distinction

Tracking and closing must not be conflated.

Tracking:
- maintain an opponent-relative relationship.

Closing:
- actively reduce distance to a threat.

Recovery:
- actively reduce displacement from expected defensive structure.

### Potential Longer-Term Concepts

- defensive adjustment,
- structural disruption,
- recovery burden,
- attacker gravity,
- off-ball movement value,
- defensive positional economy.

### Methodological Constraint

Do not introduce modeling methods that cannot be clearly explained and interrogated.

### Next Steps

1. Conduct focused literature review.
2. Identify closest existing methods and research gap.
3. Compare available public tracking datasets.
4. Formalize candidate measurable quantities.
5. Only then begin exploratory tracking analysis.
