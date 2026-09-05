# WARLOCK Plugin Factory

```
FARNAZ → AUDIO → DSP → PLUGINSPEC → DPF → CMAKE → CLANG → VST3 → PLUGINVAL → TEST → CPACK → NSIS
```

Default: **DPF**. iPlug2 secondary. JUCE legacy (THALL only, no auto-migrate).

Finished VST3 must run with **no** Farnaz, Grok, ChatGPT, Python, or internet.

`farnaz doctor` inspects; it does not install.

Release requires all gates:
BUILD + PLUGINVAL + AUDIO (hosted, not Python model) + REGRESSION + LICENSE + PACKAGE.

Python golden DSP is a model, **not** AUDIO_TEST_PASS.


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
