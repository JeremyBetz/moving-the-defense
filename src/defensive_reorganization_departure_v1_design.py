"""Outcome-free contract helpers for Defensive Reorganization Departure v1.

These helpers encode only algebra, deterministic selection conventions, and
the prospective decision tree.  They do not load tracking data or fit the
empirical IDSSE models.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np


NEAR = slice(0, 3)
MIDDLE = slice(3, 7)


def localized_response(rank_paths_m: Sequence[float]) -> tuple[float, float, float]:
    """Return near mean, middle mean, and near-minus-middle response in metres."""
    values = np.asarray(rank_paths_m, dtype=float)
    if values.shape != (10,) or not np.isfinite(values).all():
        raise ValueError("one finite D1-D10 path vector is required")
    near = float(values[NEAR].mean())
    middle = float(values[MIDDLE].mean())
    return near, middle, near - middle


def ball_nearest_attacker(
    attacker_positions: Mapping[str, Sequence[float]],
    ball_position: Sequence[float],
) -> str:
    """Select the unique geometric ball-nearest attacker with lexical tie-break."""
    ball = np.asarray(ball_position, dtype=float)
    if ball.shape != (2,) or not np.isfinite(ball).all():
        raise ValueError("one finite two-dimensional ball position is required")
    if len(attacker_positions) != 10:
        raise ValueError("exactly ten attacking outfield players are required")
    ranked: list[tuple[float, str]] = []
    for player, position in attacker_positions.items():
        xy = np.asarray(position, dtype=float)
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError("every attacking outfield position must be finite")
        ranked.append((float(np.linalg.norm(xy - ball)), str(player)))
    return min(ranked, key=lambda item: (item[0], item[1]))[1]


def attacking_frame(
    points_xy: Sequence[Sequence[float]],
    attack_sign_x: int,
    focal_start_y: float,
) -> np.ndarray:
    """Transform centred pitch coordinates to goalward/outward anchor axes.

    ``attack_sign_x`` is +1 when the attacking side moves toward canonical +x
    and -1 otherwise.  A 180-degree rotation first makes +x goalward.  A
    second reflection makes the focal attacker's movement-start lateral
    coordinate nonnegative, so positive lateral movement is outward and
    negative lateral movement is inward.  An exact centre-line start uses the
    unreflected (+y) convention.
    """
    if attack_sign_x not in (-1, 1):
        raise ValueError("attack_sign_x must be -1 or +1")
    points = np.asarray(points_xy, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError("finite n-by-2 points are required")
    rotated_focal_y = attack_sign_x * float(focal_start_y)
    lateral_mirror = 1.0 if rotated_focal_y >= 0.0 else -1.0
    return np.column_stack(
        [attack_sign_x * points[:, 0], lateral_mirror * attack_sign_x * points[:, 1]]
    )


def macro_mae(errors_by_match: Mapping[str, Sequence[float]]) -> float:
    """Return the equal-match mean of within-match mean absolute errors."""
    if not errors_by_match:
        raise ValueError("at least one match is required")
    values = []
    for errors in errors_by_match.values():
        array = np.asarray(errors, dtype=float)
        if array.ndim != 1 or len(array) == 0 or not np.isfinite(array).all():
            raise ValueError("each match requires finite one-dimensional errors")
        values.append(float(np.abs(array).mean()))
    return float(np.mean(values))


def leave_one_match_out(matches: Sequence[str]) -> list[tuple[tuple[str, ...], str]]:
    """Return deterministic whole-match outer folds in lexical match order."""
    ordered = tuple(sorted(str(match) for match in matches))
    if len(ordered) < 2 or len(set(ordered)) != len(ordered):
        raise ValueError("at least two unique match identifiers are required")
    return [(tuple(match for match in ordered if match != test), test) for test in ordered]


def select_alpha(alpha_scores: Mapping[float, float], tolerance_m: float = 1e-6) -> float:
    """Choose the largest alpha within the frozen tolerance of minimum MAE."""
    if not alpha_scores or tolerance_m < 0.0:
        raise ValueError("alpha scores and a nonnegative tolerance are required")
    clean = {float(alpha): float(score) for alpha, score in alpha_scores.items()}
    if any(alpha <= 0.0 for alpha in clean) or not np.isfinite(list(clean.values())).all():
        raise ValueError("positive alphas and finite scores are required")
    minimum = min(clean.values())
    return max(alpha for alpha, score in clean.items() if score <= minimum + tolerance_m)


def relative_improvement_percent(baseline_mae: float, model_mae: float) -> float:
    """Return 100 * (baseline - model) / baseline."""
    if not np.isfinite([baseline_mae, model_mae]).all() or baseline_mae <= 0.0:
        raise ValueError("finite MAEs with positive baseline are required")
    return float(100.0 * (baseline_mae - model_mae) / baseline_mae)


def family_is_stable(
    full_mae_by_match: Mapping[str, float],
    ablated_mae_by_match: Mapping[str, float],
) -> bool:
    """Apply the frozen >=1% macro and >=5/7 match ablation rule."""
    if set(full_mae_by_match) != set(ablated_mae_by_match) or len(full_mae_by_match) != 7:
        raise ValueError("identical seven-match keys are required")
    keys = sorted(full_mae_by_match)
    full = np.asarray([full_mae_by_match[key] for key in keys], dtype=float)
    ablated = np.asarray([ablated_mae_by_match[key] for key in keys], dtype=float)
    if not np.isfinite(full).all() or not np.isfinite(ablated).all() or np.any(ablated <= 0.0):
        raise ValueError("finite positive per-match MAEs are required")
    macro_full = float(full.mean())
    macro_ablated = float(ablated.mean())
    worsening = 100.0 * (macro_ablated - macro_full) / macro_full
    return bool(worsening >= 1.0 and int(np.sum(full < ablated)) >= 5)


def classify_application_foundation(
    e0_mae_by_match: Mapping[str, float],
    e1_mae_by_match: Mapping[str, float],
    stable_family_count: int,
    valid: bool = True,
) -> str:
    """Apply the frozen exhaustive DRD v1 application-foundation status tree."""
    if not valid:
        return "INVALID"
    if set(e0_mae_by_match) != set(e1_mae_by_match) or len(e0_mae_by_match) != 7:
        raise ValueError("identical seven-match keys are required")
    keys = sorted(e0_mae_by_match)
    e0 = np.asarray([e0_mae_by_match[key] for key in keys], dtype=float)
    e1 = np.asarray([e1_mae_by_match[key] for key in keys], dtype=float)
    if not np.isfinite(e0).all() or not np.isfinite(e1).all() or np.any(e0 <= 0.0):
        raise ValueError("finite MAEs with positive E0 values are required")
    macro_gain = relative_improvement_percent(float(e0.mean()), float(e1.mean()))
    improved = int(np.sum(e1 < e0))
    worsened_ten = int(np.sum((e1 - e0) / e0 >= 0.10))
    if macro_gain >= 3.0 and improved >= 6 and worsened_ten == 0 and stable_family_count >= 1:
        return "SUPPORTED"
    if macro_gain <= 0.0 or improved <= 3:
        return "NOT SUPPORTED"
    return "MIXED"


def drd(observed_m: Sequence[float], predicted_m: Sequence[float]) -> np.ndarray:
    """Return observed minus out-of-fold expected localized reorganization."""
    observed = np.asarray(observed_m, dtype=float)
    predicted = np.asarray(predicted_m, dtype=float)
    if observed.shape != predicted.shape or not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("finite equally shaped observed and predicted values are required")
    return observed - predicted
