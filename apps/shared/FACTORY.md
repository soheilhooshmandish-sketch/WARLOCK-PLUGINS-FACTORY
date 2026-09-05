# WARLOCK Plugin Factory

```
FARNAZ → DSP spec → DPF → CMAKE → CLANG → VST3 → PLUGINVAL → TEST → CPACK → NSIS
```

Default framework: **DPF**. iPlug2 is secondary. JUCE is legacy (existing THALL only).

Farnaz will **not** download or install CMake, LLVM, DPF, pluginval, or NSIS without explicit permission.

## Tool roles

| Tool | Role |
|---|---|
| Python, Git, CMake, Clang, DPF, pluginval, CPack, NSIS | REQUIRED for the vertical slice |
| g++ | FALLBACK compiler |
| Ninja, FFmpeg, SciPy, pyloudnorm | OPTIONAL |
| iPlug2 | FALLBACK framework |
| JUCE | DEVELOPMENT-ONLY / legacy THALL |

## Probe plugin

First proof is **WARLOCK Probe** (gain only). Not THALL.

```
python -m apps.grok_local_agent.factory tools
python -m apps.grok_local_agent.factory create
python -m apps.grok_local_agent.factory build
```

Safe/read commands run without extra grants. Build/validate/package need BUILD permission and the real toolchain.
