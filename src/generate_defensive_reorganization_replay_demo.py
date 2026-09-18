"""Generate the approved local Metrica Game 2 replay demonstration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import matplotlib.pyplot as plt
import numpy as np

from defensive_reorganization_replay import (
    DefenderRelativePathSpec,
    score_trailing_defender_relative_path,
)
from defensive_reorganization_replay_visualization import (
    DEFAULT_SCORE_VMAX_M,
    animate_defensive_reorganization,
    plot_defensive_reorganization_diagnostic,
)
from tracking_animation import TrackingClipSpec, export_animation
from tracking_animation_metrica_demo import DEMO_SPEC, ROOT, load_demo_tracking


DISPLAY_SPEC = TrackingClipSpec(
    match_id=DEMO_SPEC.match_id,
    period=1,
    anchor_time_s=2336.04,
    start_time_s=2326.04,
    end_time_s=2346.04,
    focal_player_key=DEMO_SPEC.focal_player_key,
    attacking_team_key=DEMO_SPEC.attacking_team_key,
    defending_team_key=DEMO_SPEC.defending_team_key,
    defender_ranks=None,
)

RAW_SUPPORT_SPEC = TrackingClipSpec(
    match_id=DEMO_SPEC.match_id,
    period=1,
    anchor_time_s=2336.04,
    start_time_s=2323.92,
    end_time_s=2346.16,
    focal_player_key=DEMO_SPEC.focal_player_key,
    attacking_team_key=DEMO_SPEC.attacking_team_key,
    defending_team_key=DEMO_SPEC.defending_team_key,
    defender_ranks=None,
)

EXPECTED_DEMO_QA = {
    "native_frame_count": 501,
    "displayed_frame_count": 251,
    "elapsed_duration_s": 20.0,
    "saturation_count": 134,
    "frames_at_least_1_saturated": 97,
    "frames_at_least_2_saturated": 37,
    "frames_at_least_5_saturated": 0,
    "team_mean_saturation_count": 0,
}


def load_approved_scored_demo(root: Path = ROOT):
    """Load only approved public tracking support and compute the committed score."""
    tracking = load_demo_tracking(root=root, spec=RAW_SUPPORT_SPEC)
    approved_defenders = set(DEMO_SPEC.defender_ranks or {})
    is_other_defender = tracking["team_key"].eq(DEMO_SPEC.defending_team_key) & ~tracking[
        "player_key"
    ].isin(approved_defenders)
    tracking = tracking.loc[~is_other_defender].reset_index(drop=True)
    scores = score_trailing_defender_relative_path(
        tracking,
        DefenderRelativePathSpec(
            defending_team_key=DEMO_SPEC.defending_team_key,
            source_fps=25.0,
            window_seconds=2.0,
            smoothing_frames=7,
        ),
    )
    return tracking, scores


def generate_demo(output_dir: Path, root: Path = ROOT) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tracking, scores = load_approved_scored_demo(root)
    diagnostic = plot_defensive_reorganization_diagnostic(
        tracking, scores, DISPLAY_SPEC, selected_time_s=DISPLAY_SPEC.anchor_time_s
    )
    png = output_dir / "metrica_game2_defensive_reorganization_diagnostic.png"
    pdf = output_dir / "metrica_game2_defensive_reorganization_diagnostic.pdf"
    diagnostic.savefig(png, dpi=150, bbox_inches="tight", metadata={"Software": "moving-the-defense"})
    diagnostic.savefig(pdf, bbox_inches="tight", metadata={"Creator": "moving-the-defense"})
    plt.close(diagnostic)

    bundle = animate_defensive_reorganization(tracking, scores, DISPLAY_SPEC)
    expected_native = int(round(bundle.elapsed_duration_s * bundle.source_fps)) + 1
    if bundle.native_frame_count != expected_native:
        raise RuntimeError("display frame count disagrees with timestamps and source cadence")
    gif = output_dir / "metrica_game2_defensive_reorganization.gif"
    started = time.monotonic()
    export_animation(bundle, gif)
    render_seconds = time.monotonic() - started
    metadata = dict(bundle.animation._reorganization_metadata)
    result = {
        "diagnostic_png": str(png),
        "diagnostic_pdf": str(pdf),
        "gif": str(gif),
        "native_frame_count": bundle.native_frame_count,
        "displayed_frame_count": bundle.displayed_frame_count,
        "source_fps": bundle.source_fps,
        "playback_fps": bundle.playback_fps,
        "elapsed_duration_s": bundle.elapsed_duration_s,
        "playback_duration_s": bundle.playback_duration_s,
        "render_seconds": render_seconds,
        "gif_bytes": gif.stat().st_size,
        "saturation_count": metadata["saturation_count"],
        "frames_at_least_1_saturated": metadata["frames_at_least_1_saturated"],
        "frames_at_least_2_saturated": metadata["frames_at_least_2_saturated"],
        "frames_at_least_5_saturated": metadata["frames_at_least_5_saturated"],
        "team_mean_saturation_count": metadata["team_mean_saturation_count"],
        "score_vmax_m": metadata["score_vmax_m"],
        "unsupported_score_frame_count": metadata["unsupported_score_frame_count"],
    }
    for key, expected in EXPECTED_DEMO_QA.items():
        if not np.isclose(result[key], expected, atol=1e-9, rtol=0):
            raise RuntimeError(f"demo QA mismatch for {key}: {result[key]} != {expected}")
    if result["score_vmax_m"] != DEFAULT_SCORE_VMAX_M:
        raise RuntimeError("demo did not use the frozen 6.25 m display ceiling")
    bundle.animation._draw_was_started = True
    plt.close(bundle.figure)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/tmp/moving_the_defense_replay_demo"),
        help="Local untracked output directory",
    )
    args = parser.parse_args()
    print(json.dumps(generate_demo(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
