# WARLOCK mix-ready tone system

PluginSpec parameter IDs never change. Genre is **energy + mix slot**, not a new DSP chain.

```
artistic intent → energy vector → bank values → same THALL chain → TRIM → mix slot
```

## Energy axes (0–100)

| axis | meaning |
|---|---|
| attack | pick / chug transient |
| density | how full the mid is |
| frost | cold treble wall (black) |
| sludge | slow low-mid mass (doom) |
| chainsaw | HM-2 / death grind |
| sag | fuzz compression / stoner |
| hiss | intentional air noise |
| sustain | un-gated tail |

Solo loudness is not an axis.

## Mix law

1. Trim after the chain. MASTER is mix, GAIN is saturation.
2. Plugin `LOW_CUT` is tone. Bus HPF is arrangement.
3. Kick / bass own the floor unless the bank says share (doom/stoner).
4. Dual guitar must survive mono for THALL, DJENT, DEATH. Black/stoner may collapse.
5. A/B only after loudness match. Approximate RMS is not LUFS.

## Genre pockets

- **THALL / DJENT / MODERN_METAL** — percussive, tight dual, gate is a drum.
- **DEATH_METAL** — Florida/brutal: kick-visible chug, 2.5 kHz bite, not black hiss.
- **DEATH_HM2** — Stockholm: 850 Hz + 1.4 kHz bump is the song; bass must leave that hole.
- **BLACK_METAL** — blizzard; hiss is the point; bass below 150 Hz.
- **DOOM** — mass, open gate, BODY at 90 Hz, drums ride on top.
- **STONER** — sag and room; almost no gate; not ambient pad.
- **CLEAN_AMBIENT** — bed, GATE=0, widest, felt not seen.

Same chain. Wrong bank = wrong energy, even if it still distorts.
