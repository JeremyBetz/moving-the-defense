"""Analyst-facing composition of the frozen match-review application layers.

This module does not calculate a new score or change any selection threshold.
It joins existing rapid, trajectory, ball-alignment and attacker-link records,
then separates valid examples from special diagnostics and rejected support.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


KEY = ("match_id", "team_key", "period", "peak_time_s")


def _copy(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.copy(deep=True).reset_index(drop=True)


@dataclass(frozen=True)
class MatchReorganizationReview:
    rapid_episodes: pd.DataFrame
    representative_examples: pd.DataFrame
    diagnostic_examples: pd.DataFrame
    rejected_examples: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        for name in (
            "rapid_episodes", "representative_examples", "diagnostic_examples",
            "rejected_examples",
        ):
            object.__setattr__(self, name, _copy(getattr(self, name)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        groups = [set(_keys(getattr(self, name))) for name in (
            "representative_examples", "diagnostic_examples", "rejected_examples"
        )]
        if any(groups[i] & groups[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError("example collections must be mutually exclusive")
        if not self.representative_examples.empty and not self.representative_examples[
            "trajectory_integrity_status"
        ].eq("trajectory_integrity_clean").all():
            raise ValueError("representative examples must be trajectory-integrity clean")

    @property
    def integrity_clean(self) -> pd.DataFrame:
        return _copy(self.rapid_episodes.loc[
            self.rapid_episodes["trajectory_integrity_status"].eq("trajectory_integrity_clean")
        ])

    @property
    def low_ballward(self) -> pd.DataFrame:
        return _copy(self.integrity_clean.loc[self.integrity_clean["ballward_stratum"].eq("low_ballward")])

    @property
    def high_ballward(self) -> pd.DataFrame:
        return _copy(self.integrity_clean.loc[self.integrity_clean["ballward_stratum"].eq("high_ballward")])

    @property
    def attacker_linked(self) -> pd.DataFrame:
        return _copy(self.integrity_clean.loc[self.integrity_clean["attacker_link_status"].eq("supported")])


def _keys(frame: pd.DataFrame) -> list[tuple[object, ...]]:
    if frame.empty:
        return []
    return [tuple(row) for row in frame.loc[:, KEY].itertuples(index=False, name=None)]


def _records_frame(records: Sequence[Mapping[str, object]] | pd.DataFrame) -> pd.DataFrame:
    return records.copy(deep=True) if isinstance(records, pd.DataFrame) else pd.DataFrame(list(records))


def _rank(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.sort_values(
        ["one_second_change_m", "period", "peak_time_s", "team_key"],
        ascending=[False, True, True, True], kind="mergesort",
    ).reset_index(drop=True)


def analyze_match_reorganization(
    ball_alignment_episodes: Sequence[Mapping[str, object]] | pd.DataFrame,
    attacker_linked_episodes: Sequence[Mapping[str, object]] | pd.DataFrame = (),
    *,
    metadata: Mapping[str, object] | None = None,
) -> MatchReorganizationReview:
    """Compose already-computed application records into one safe review object.

    Selection uses only frozen status/category fields. Timestamps are identities,
    never selection criteria except as deterministic tie-breakers.
    """
    ball = _records_frame(ball_alignment_episodes)
    required = {
        *KEY, "one_second_change_m", "team_score_m", "reference_percentile",
        "trajectory_integrity_status", "ballward_stratum",
    }
    missing = required - set(ball.columns)
    if missing:
        raise ValueError(f"ball-alignment episodes lack: {sorted(missing)}")
    if ball.duplicated(list(KEY)).any():
        raise ValueError("ball-alignment episode identities must be unique")
    links = _records_frame(attacker_linked_episodes)
    if not links.empty:
        link_required = {
            *KEY, "maximum_eligible_attacker_path_m", "strong_link_count",
            "linkage_category", "trajectory_integrity_status",
            "one_second_change_m", "team_score_m", "reference_percentile",
            "team_ballward_projection_share", "team_signed_ball_alignment",
        }
        missing = link_required - set(links.columns)
        if missing:
            raise ValueError(f"attacker-linked episodes lack: {sorted(missing)}")
        if links.duplicated(list(KEY)).any():
            raise ValueError("attacker-linked episode identities must be unique")
        # The frozen attacker-linked package is defined only on supported,
        # integrity-clean, low-ballward candidates. Add candidates that fall
        # outside the compact top-six ball manifest without inventing values.
        existing = set(_keys(ball))
        additions = links.loc[[tuple(row) not in existing for row in links.loc[:, KEY].itertuples(index=False, name=None)]].copy()
        if not additions.empty:
            additions["ballward_stratum"] = "low_ballward"
            additions["ball_alignment_support_status"] = "supported"
            ball = pd.concat([ball, additions], ignore_index=True, sort=False)
    q = ball.copy(deep=True)
    if "ball_alignment_support_status" not in q:
        q["ball_alignment_support_status"] = np.where(
            q["ballward_stratum"].eq("unsupported"), "unsupported", "supported"
        )
    impossible = (
        q["impossible_speed_count"]
        if "impossible_speed_count" in q else pd.Series(0, index=q.index)
    )
    q["trajectory_integrity_reason"] = np.where(
        q["trajectory_integrity_status"].eq("trajectory_integrity_clean"),
        "none",
        np.where(impossible.fillna(0).astype(float).gt(0),
                 "impossible_native_speed", "support_or_identity_failure"),
    )
    q["attacker_link_status"] = "not_evaluated"
    q["maximum_off_ball_attacker_path_m"] = np.nan
    q["strong_link_count"] = pd.array([pd.NA] * len(q), dtype="Int64")
    q["linkage_category"] = "not_evaluated"

    if not links.empty:
        lookup = links.set_index(list(KEY))
        for index, row in q.iterrows():
            key = tuple(row[name] for name in KEY)
            if key not in lookup.index:
                continue
            linked = lookup.loc[key]
            q.at[index, "attacker_link_status"] = "supported"
            q.at[index, "maximum_off_ball_attacker_path_m"] = float(linked.maximum_eligible_attacker_path_m)
            q.at[index, "strong_link_count"] = int(linked.strong_link_count)
            q.at[index, "linkage_category"] = str(linked.linkage_category)

    for name, default in (
        ("possession_state", "out_of_possession"),
        ("rapid_context", "not_evaluated"),
        ("continuous_out_of_possession_s", np.nan),
        ("team_ballward_projection_share", np.nan),
        ("team_signed_ball_alignment", np.nan),
        ("top_three_player_raw_paths_m", None),
    ):
        if name not in q:
            q[name] = [default] * len(q)
    q["media_status"] = "not_requested"
    q["static_path"] = None
    q["gif_path"] = None
    q = _rank(q)

    clean = q.loc[q.trajectory_integrity_status.eq("trajectory_integrity_clean")].copy()
    rejected = _rank(q.loc[~q.trajectory_integrity_status.eq("trajectory_integrity_clean")]).head(1)

    representative_parts: list[pd.DataFrame] = []
    localized_low = _rank(clean.loc[
        clean.ballward_stratum.eq("low_ballward")
        & clean.attacker_link_status.eq("supported")
        & clean.linkage_category.eq("localized")
    ])
    if not localized_low.empty:
        representative_parts.append(localized_low.head(1))
    high = _rank(clean.loc[clean.ballward_stratum.eq("high_ballward")])
    if not high.empty:
        representative_parts.append(high.head(1))
    representatives = (
        pd.concat(representative_parts, ignore_index=True).drop_duplicates(list(KEY))
        if representative_parts else q.head(0)
    )

    representative_keys = set(_keys(representatives))
    diagnostic_parts: list[pd.DataFrame] = []
    distributed_low = _rank(clean.loc[
        clean.ballward_stratum.eq("low_ballward")
        & clean.attacker_link_status.eq("supported")
        & clean.linkage_category.eq("distributed")
    ])
    if not distributed_low.empty:
        diagnostic_parts.append(distributed_low.head(1))
    no_link = _rank(clean.loc[
        clean.attacker_link_status.eq("supported") & clean.linkage_category.eq("none")
    ])
    if not no_link.empty:
        diagnostic_parts.append(no_link.head(1))
    diagnostics = (
        pd.concat(diagnostic_parts, ignore_index=True).drop_duplicates(list(KEY))
        if diagnostic_parts else q.head(0)
    )
    diagnostics = diagnostics.loc[[key not in representative_keys for key in _keys(diagnostics)]]

    return MatchReorganizationReview(
        q, representatives, diagnostics, rejected,
        {
            "measurement": "team relational reorganization",
            "selection": "frozen fields and deterministic magnitude/period/time/team ordering",
            "scientific_change": False,
            **dict(metadata or {}),
        },
    )
