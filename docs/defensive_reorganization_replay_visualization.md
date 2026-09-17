# Defender-relative replay visualization

This visualization consumes the committed trailing defender-relative score from
`src/defensive_reorganization_replay.py`. It is a **retrospective analyst
replay**, not a live detector or an inferential response calculation.

For each defender, the displayed value is accumulated movement relative to the
other nine defenders over the trailing interval `[t−2,t]`, in metres. The
centered smoother also requires raw tracking after the displayed time: 0.12 s
for the approved 25 Hz/seven-frame Metrica convention and 0.10 s for the 10
Hz/three-frame convention.

Defender marker fill uses a fixed `cividis` scale from 0 to 4 m. Values above 4
m saturate visually but remain unchanged in the score table. An unsupported
score is shown as a hollow gray marker; an invalid current coordinate hides the
player. The team meter is the arithmetic mean of all ten player scores and is
available only when all ten are supported.

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

The command writes a static PNG/PDF and a GIF. These files are local explanatory
artifacts, not additional scientific evidence or automatically approved public
assets.
