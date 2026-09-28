"""Descriptive attacker-linked geometry for low-ballward rapid review."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AttackerLinkedReviewSpec:
    source_fps: float = 25.0
    window_seconds: float = 2.0
    smoothing_frames: int = 7
    minimum_off_ball_fraction: float = 0.80
    minimum_off_ball_frames: int = 41
    minimum_distance_m: float = 8.0
    minimum_absolute_distance_change_m: float = 3.0
    zero_vector_tolerance_m: float = 1e-12

    def __post_init__(self) -> None:
        numeric = (
            self.source_fps, self.window_seconds, self.minimum_off_ball_fraction,
            self.minimum_distance_m, self.minimum_absolute_distance_change_m,
            self.zero_vector_tolerance_m,
        )
        if not np.isfinite(numeric).all() or min(numeric) <= 0:
            raise ValueError("attacker-link settings must be finite and positive")
        if self.source_fps != 25.0 or self.window_seconds != 2.0:
            raise ValueError("attacker-link timing differs from the freeze")
        if self.smoothing_frames != 7 or self.minimum_off_ball_frames != 41:
            raise ValueError("attacker-link support differs from the freeze")
        if self.minimum_off_ball_fraction != 0.80:
            raise ValueError("off-ball threshold differs from the freeze")
        if self.minimum_distance_m != 8.0 or self.minimum_absolute_distance_change_m != 3.0:
            raise ValueError("strong-link geometry differs from the freeze")

    @property
    def expected_positions(self) -> int:
        return int(round(self.window_seconds * self.source_fps)) + 1


@dataclass(frozen=True)
class LinkReferenceThresholds:
    attacker_path_p75_m: float
    relative_vector_path_p75_m: float
    attacker_count: int
    pair_count: int

    def __post_init__(self) -> None:
        values = (self.attacker_path_p75_m, self.relative_vector_path_p75_m)
        if not np.isfinite(values).all() or min(values) < 0:
            raise ValueError("reference thresholds must be finite and nonnegative")
        if self.attacker_count <= 0 or self.pair_count <= 0:
            raise ValueError("reference populations must be nonempty")


@dataclass(frozen=True)
class EpisodeLinkageResult:
    attacker_summary: pd.DataFrame
    pair_geometry: pd.DataFrame
    strong_links: pd.DataFrame
    category: str
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        for name in ("attacker_summary", "pair_geometry", "strong_links"):
            object.__setattr__(self, name, getattr(self, name).copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class AttackerLinkedReviewResult:
    rapid_ranking: pd.DataFrame
    movement_ranking: pd.DataFrame
    density_ranking: pd.DataFrame
    public_examples: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        for name in ("rapid_ranking", "movement_ranking", "density_ranking", "public_examples"):
            object.__setattr__(self, name, getattr(self, name).copy(deep=True))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _validate_cube(values: np.ndarray, keys: Sequence[str], label: str) -> tuple[np.ndarray, tuple[str, ...]]:
    array = np.asarray(values, dtype=float)
    canonical = tuple(map(str, keys))
    if array.ndim != 3 or array.shape[1:] != (10, 2):
        raise ValueError(f"{label} must have shape [frames, 10, 2]")
    if len(canonical) != 10 or len(set(canonical)) != 10:
        raise ValueError(f"{label} requires ten unique player keys")
    if not np.isfinite(array).all():
        raise ValueError(f"{label} must be complete and finite")
    return array, canonical


def summarize_off_ball_attackers(
    attacker_positions: np.ndarray,
    ball_positions: np.ndarray,
    attacker_keys: Sequence[str],
    *,
    spec: AttackerLinkedReviewSpec = AttackerLinkedReviewSpec(),
) -> pd.DataFrame:
    """Return attacker movement and framewise geometric off-ball eligibility."""
    attackers, keys = _validate_cube(attacker_positions, attacker_keys, "attacker positions")
    ball = np.asarray(ball_positions, dtype=float)
    if len(attackers) != spec.expected_positions:
        raise ValueError("attacker positions do not cover the frozen interval")
    if ball.shape != (len(attackers), 2) or not np.isfinite(ball).all():
        raise ValueError("ball positions must be complete and match the interval")
    distances = np.linalg.norm(attackers - ball[:, None, :], axis=2)
    key_order = np.asarray(keys, dtype=object)
    nearest = np.empty(len(attackers), dtype=int)
    for frame, row in enumerate(distances):
        nearest[frame] = int(np.lexsort((key_order, row))[0])
    off_ball_counts = len(attackers) - np.bincount(nearest, minlength=10)
    delta = np.diff(attackers, axis=0)
    path = np.linalg.norm(delta, axis=2).sum(axis=0)
    net = np.linalg.norm(attackers[-1] - attackers[0], axis=1)
    relative = attackers - ball[:, None, :]
    ball_relative_path = np.linalg.norm(np.diff(relative, axis=0), axis=2).sum(axis=0)
    rows = pd.DataFrame({
        "attacker_key": keys,
        "off_ball_frame_count": off_ball_counts.astype(int),
        "off_ball_fraction": off_ball_counts / float(len(attackers)),
        "attacker_path_m": path,
        "net_displacement_m": net,
        "attacker_minus_ball_path_m": ball_relative_path,
    })
    rows["off_ball_eligible"] = (
        rows["off_ball_fraction"].ge(spec.minimum_off_ball_fraction)
        & rows["off_ball_frame_count"].ge(spec.minimum_off_ball_frames)
    )
    return rows.sort_values("attacker_key", kind="mergesort").reset_index(drop=True)


def summarize_pair_geometry(
    attacker_positions: np.ndarray,
    defender_positions: np.ndarray,
    attacker_keys: Sequence[str],
    defender_keys: Sequence[str],
    defender_contributions_m: Sequence[float],
    attacker_summary: pd.DataFrame,
    *,
    spec: AttackerLinkedReviewSpec = AttackerLinkedReviewSpec(),
) -> pd.DataFrame:
    """Return complete attacker–defender geometry over the frozen interval."""
    attackers, akeys = _validate_cube(attacker_positions, attacker_keys, "attacker positions")
    defenders, dkeys = _validate_cube(defender_positions, defender_keys, "defender positions")
    if attackers.shape != defenders.shape or len(attackers) != spec.expected_positions:
        raise ValueError("attacker and defender support must match the frozen interval")
    contributions = np.asarray(defender_contributions_m, dtype=float)
    if contributions.shape != (10,) or not np.isfinite(contributions).all():
        raise ValueError("defender contributions must contain ten finite values")
    required = {"attacker_key", "off_ball_eligible", "attacker_path_m"}
    if not required.issubset(attacker_summary.columns):
        raise ValueError("attacker summary lacks required fields")
    ordered_defenders = sorted(range(10), key=lambda i: (-contributions[i], dkeys[i]))
    top_three = set(ordered_defenders[:3])
    median = float(np.median(contributions))
    total = defenders.sum(axis=1, keepdims=True)
    defender_relative = (10.0 * defenders - total) / 9.0
    attacker_lookup = attacker_summary.set_index("attacker_key")
    rows: list[dict[str, object]] = []
    for ai, attacker_key in enumerate(akeys):
        attacker_net = attackers[-1, ai] - attackers[0, ai]
        for di, defender_key in enumerate(dkeys):
            vector = defenders[:, di] - attackers[:, ai]
            distance = np.linalg.norm(vector, axis=1)
            defender_net = defender_relative[-1, di] - defender_relative[0, di]
            denom = float(np.linalg.norm(attacker_net) * np.linalg.norm(defender_net))
            coherence = (
                float(np.dot(attacker_net, defender_net) / denom)
                if denom > spec.zero_vector_tolerance_m else np.nan
            )
            signed_change = float(distance[-1] - distance[0])
            rows.append({
                "attacker_key": attacker_key,
                "defender_key": defender_key,
                "attacker_off_ball_eligible": bool(attacker_lookup.loc[attacker_key, "off_ball_eligible"]),
                "attacker_path_m": float(attacker_lookup.loc[attacker_key, "attacker_path_m"]),
                "defender_contribution_m": float(contributions[di]),
                "defender_top_three": di in top_three,
                "defender_above_median": bool(contributions[di] > median),
                "start_distance_m": float(distance[0]),
                "end_distance_m": float(distance[-1]),
                "signed_distance_change_m": signed_change,
                "absolute_distance_change_m": abs(signed_change),
                "minimum_distance_m": float(distance.min()),
                "relative_vector_path_m": float(np.linalg.norm(np.diff(vector, axis=0), axis=1).sum()),
                "movement_direction_coherence": coherence,
            })
    return pd.DataFrame(rows).sort_values(
        ["attacker_key", "defender_key"], kind="mergesort"
    ).reset_index(drop=True)


def derive_reference_thresholds(
    attacker_paths_m: Sequence[float], relative_vector_paths_m: Sequence[float]
) -> LinkReferenceThresholds:
    attackers = np.asarray(attacker_paths_m, dtype=float)
    pairs = np.asarray(relative_vector_paths_m, dtype=float)
    if attackers.size == 0 or pairs.size == 0 or not np.isfinite(attackers).all() or not np.isfinite(pairs).all():
        raise ValueError("reference arrays must be nonempty and finite")
    if np.any(attackers < 0) or np.any(pairs < 0):
        raise ValueError("reference paths cannot be negative")
    return LinkReferenceThresholds(
        float(np.quantile(attackers, 0.75, method="linear")),
        float(np.quantile(pairs, 0.75, method="linear")),
        int(attackers.size), int(pairs.size),
    )


def classify_episode_links(
    attacker_summary: pd.DataFrame,
    pair_geometry: pd.DataFrame,
    thresholds: LinkReferenceThresholds,
    *,
    spec: AttackerLinkedReviewSpec = AttackerLinkedReviewSpec(),
) -> EpisodeLinkageResult:
    attackers = attacker_summary.copy(deep=True)
    pairs = pair_geometry.copy(deep=True)
    pairs["attacker_high_movement"] = pairs["attacker_path_m"].ge(thresholds.attacker_path_p75_m)
    pairs["minimum_distance_trigger"] = pairs["minimum_distance_m"].le(spec.minimum_distance_m)
    pairs["distance_change_trigger"] = pairs["absolute_distance_change_m"].ge(
        spec.minimum_absolute_distance_change_m
    )
    pairs["relative_vector_trigger"] = pairs["relative_vector_path_m"].ge(
        thresholds.relative_vector_path_p75_m
    )
    pairs["strong_link"] = (
        pairs["attacker_off_ball_eligible"].astype(bool)
        & pairs["attacker_high_movement"].astype(bool)
        & pairs["defender_top_three"].astype(bool)
        & pairs[["minimum_distance_trigger", "distance_change_trigger", "relative_vector_trigger"]].any(axis=1)
    )
    strong = pairs.loc[pairs["strong_link"]].copy().reset_index(drop=True)
    count = int(len(strong))
    category = "none" if count == 0 else "localized" if count <= 2 else "distributed"
    eligible = attackers.loc[attackers["off_ball_eligible"]]
    metadata = {
        "eligible_off_ball_attacker_count": int(len(eligible)),
        "maximum_eligible_attacker_path_m": (
            float(eligible["attacker_path_m"].max()) if len(eligible) else np.nan
        ),
        "strong_link_count": count,
        "linked_defender_count": int(strong["defender_key"].nunique()) if count else 0,
        "category": category,
    }
    return EpisodeLinkageResult(attackers, pairs, strong, category, metadata)


def rank_attacker_linked_episodes(episodes: pd.DataFrame) -> AttackerLinkedReviewResult:
    required = {
        "one_second_change_m", "maximum_eligible_attacker_path_m", "strong_link_count",
        "linkage_category", "period", "peak_time_s", "team_key",
    }
    missing = required - set(episodes.columns)
    if missing:
        raise ValueError(f"episode table lacks: {sorted(missing)}")
    q = episodes.copy(deep=True)
    rapid = q.sort_values(
        ["one_second_change_m", "period", "peak_time_s", "team_key"],
        ascending=[False, True, True, True], kind="mergesort",
    ).reset_index(drop=True)
    rapid["rapid_rank"] = np.arange(1, len(rapid) + 1)
    movement = q.sort_values(
        ["maximum_eligible_attacker_path_m", "one_second_change_m", "period", "peak_time_s", "team_key"],
        ascending=[False, False, True, True, True], kind="mergesort", na_position="last",
    ).reset_index(drop=True)
    movement["movement_rank"] = np.arange(1, len(movement) + 1)
    density = q.sort_values(
        ["strong_link_count", "one_second_change_m", "period", "peak_time_s", "team_key"],
        ascending=[False, False, True, True, True], kind="mergesort",
    ).reset_index(drop=True)
    density["density_rank"] = np.arange(1, len(density) + 1)
    selected: list[pd.Series] = []
    reasons: list[str] = []
    for category, reason in (
        ("distributed", "top_distributed"),
        ("localized", "top_localized"),
        ("none", "top_none_contrast"),
    ):
        candidates = rapid.loc[rapid["linkage_category"].eq(category)]
        if not candidates.empty:
            selected.append(candidates.iloc[0]); reasons.append(reason)
    public = pd.DataFrame(selected).reset_index(drop=True) if selected else rapid.head(0)
    if not public.empty:
        public["public_selection_reason"] = reasons
        public["public_rank"] = np.arange(1, len(public) + 1)
    return AttackerLinkedReviewResult(
        rapid, movement, density, public,
        {"episode_count": int(len(q)), "selection_count": int(len(public))},
    )
