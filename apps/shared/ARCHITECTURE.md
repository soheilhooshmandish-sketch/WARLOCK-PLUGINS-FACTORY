# Farnaz architecture law — Free / Open-Source First

Farnaz must run **without a paid API**. Grok, ChatGPT, and Claude are optional helpers, never a dependency.

```
Farnaz Local Brain → free tools → DSP engine → JUCE → VST3
```

## Law

1. Knowledge lives in the repository (shared brain, presets, DSP cards). No network required to answer Thall / gate / ADAA / oversample / tone.
2. Desktop control is loopback-only (`127.0.0.1`) and **default-deny**. `apps/local_agent` is never a write target.
3. Prefer stdlib and OSS: Python, SQLite, Git, NumPy/SciPy, OpenCV, PyAutoGUI, librosa, FFmpeg, JUCE, CMake, CTest.
4. A missing optional package degrades; it does not crash Farnaz.
5. Never claim a VST3 was compiled unless CMake/CTest actually ran.
6. Paid model calls are opt-in (`WARLOCK_GROK_OFFLINE=0` **and** a valid `xai-` key). Core work stays local.

## Capability stack

| Capability | Free stack | Now |
|---|---|---|
| Desktop Vision | GDI screenshot; OpenCV later | wired (screenshot + grant `see`) |
| Mouse / Keyboard | Windows API; PyAutoGUI later | wired (grant `click` / `type`) |
| App detect | PowerShell window titles | wired (grant `apps`) |
| Audio analysis | NumPy/SciPy; librosa/pyloudnorm optional | local bands (stdlib FFT fallback) |
| DSP analysis | SciPy + WARLOCK DSP bible | local brain + preset bank |
| JUCE / VST3 | JUCE + CMake + Python | detect / report, no fake build |
| A/B render | FFmpeg + own DSP | detect ffmpeg |
| Memory / checkpoint | SQLite + JSON | wired |
| Backup / rollback | Git branches + commits | wired (read-only git) |
| Permission | Farnaz policy layer | wired (operator grants) |
| Build / test | CMake + VS Build Tools + CTest | detect |

## Preset brain (no API)

THALL, DJENT, DOOM, BLACK_METAL, CLEAN_AMBIENT, MODERN_METAL in `apps/shared/presets.json`.
