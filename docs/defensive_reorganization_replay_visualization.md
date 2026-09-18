# Defender-relative replay visualization

This visualization consumes the committed trailing defender-relative score from
`src/defensive_reorganization_replay.py`. It is a **retrospective analyst
replay**, not a live detector or an inferential response calculation.

For each defender, the displayed value is accumulated movement relative to the
other nine defenders over the trailing interval `[t−2,t]`, in metres. The
centered smoother also requires raw tracking after the displayed time: 0.12 s
for the approved 25 Hz/seven-frame Metrica convention and 0.10 s for the 10
Hz/three-frame convention.

Defender marker fill uses the prospectively audited fixed `cividis` scale from
0 to 6.25 m. Values above 6.25 m saturate visually but remain unchanged in the
score table. The ceiling was selected as the lowest passing candidate in the
[response-free display-scale audit v2](results/defensive_reorganization_replay_display_scale_v2.md).
Attacking players use a fixed black fill and never enter the heat scale. Defender
and attacker trails remain neutral gray and black respectively; marker fill is
the primary score cue. An unsupported defender score is shown as a hollow gray
marker; an invalid current coordinate hides the player. The ball remains white
with a dark outline. The team meter is the arithmetic mean of all ten player
scores and is available only when all ten are supported.

Higher values mean more accumulated movement relative to the defensive unit.
They do not mean better or worse defending and do not establish causation,
marking, tactical effectiveness, attacker influence, or value. The uniform
pitch background is never a spatial heat field.

The approved local demonstration uses public Metrica Sample Game 2, period 1,
the fixed anchor at 2336.04 s, and the display interval 2326.04–2346.04 s. It can
be generated locally without writing media into the repository:

```bash
.venv/bin/python src/generate_defensive_reorganization_replay_demo.py \
  --output-dir /tmp/moving_the_defense_replay_demo
```

The command writes a static PNG/PDF and a GIF. The reviewed public rendering is
stored under `figures/presentation/defender_relative_replay/`; regeneration does
not create additional scientific evidence.

The complete public workflow is:

```text
normalized long-format tracking
    -> score_trailing_defender_relative_path(...)
    -> animate_defensive_reorganization(...)
```

Scores are raw metres over `[t−2,t]`. The centered smoother requires 0.12 s of
future raw tracking at 25 Hz, so this remains retrospective analyst playback,
not a live detector. Missing support invalidates all ten defender scores and the
team mean for that frame; no partial-team repair or interpolation is performed.
