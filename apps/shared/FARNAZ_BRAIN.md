# Farnaz brain - shared with ChatGPT

ChatGPT agent (port 8765) may **read** this file. Do not rewrite `apps/local_agent`.

Path: `apps/shared/FARNAZ_BRAIN.md`
JSON: `apps/shared/farnaz_brain.json`

## How ChatGPT uses it

Read `apps/shared/farnaz_brain.json` (or this markdown) before answering DSP, Thall, oversample, ADAA, gate, space/IR, frequency-domain, or lab layout questions.

## DSP chain

Input -> Highpass (Low Cut + TIGHT) -> Tight highshelf -> Body peaking -> Drive gain -> tanh waveshaper (MORPH) -> Bite peaking -> Air shelf -> Gate -> Dry / Delay / Reverb -> Engage bypass -> Stereo/Mono -> Master + Trim.

Filters **before** the shaper. Bite **after**. Never put the shaper first.

## Waveshaping

- `y = f(x)` per sample.
- Symmetric tanh -> odd harmonics (modern).
- Asymmetric tanh (x1.2 on +, x0.82 on -) -> even + odd (tube-like).
- `amount = 1.4 + GAIN^2 * 22`
- Drive before table: `0.72 + GAIN^2 * 5.8`
- MORPH crossfades modern <-> asymmetric.

## Oversampling

Upsample xL -> nonlinearity -> lowpass -> downsample. Default **4x** on the shaper only. 2x or OFF available. Harder clip needs higher L.

## ADAA (native VST, not the browser shaper)

Parker / Zavalishin / Le Bivic, DAFx-16.

`y = (F(x[n]) - F(x[n-1])) / (x[n] - x[n-1])` with `F' = f`.
If `|dx| < eps` use `f(x)`.
tanh: `F = ln(cosh)`. Cheap cousin: `f = x/sqrt(1+x^2)`, `F = sqrt(1+x^2)`.
Best with **ADAA + 2x** oversample. Adds 1 sample delay.

### ADAA numerical stability (native)

- `eps` relative: `1e-6 * (1+|x|+|x1|)`. Never divide by raw 0.
- If `|dx| < eps` use `0.5*(f(x)+f(x1))`.
- Stable `ln(cosh x) = |x| + log1p(exp(-2|x|)) - ln(2)`. Raw `log(cosh)` overflows.
- Asymmetric branch: `f=tanh(a x)` → `F=ln_cosh(a x)/a`. Clamp `a`.
- MORPH = two ADAA results blended, not two `f` then one `F`.
- Denormal: if `|x1| < 1e-30` set 0. Non-finite sample → 0 and reset state.
- `NUMERICAL_SAFETY` stays NOT_RUN until tests exist. Factory Test has tanh + isfinite only, no ADAA yet.

### Alternative clips (do not silently replace tanh)

| f | F | use |
|---|---|---|
| tanh | ln_cosh | THALL default |
| x/√(1+x²) | √(1+x²) | ECO cousin |
| x/(1+|x|) | |x|-ln(1+|x|) | utility, not brand |
| atan (scaled) | x atan x − ½ ln(1+x²) | darker, more CPU |
| cubic | piecewise polynomial | simple Factory, not MORPH |

Symmetric → odd. Asymmetric scale → even. Recalibrate GAIN² and approve golden if you switch family.

https://dafx16.vutbr.cz/dafxpapers/20-DAFx-16_paper_41-PN.pdf
https://vicanek.de/articles/AADistortion.pdf

## Gate

Sample-wise worklet: peak magnitude, exp envelope (~1.5 ms attack, 55-185 ms release from GATE), threshold `0.00008 + 0.0085*GATE^2`, close at `0.58*threshold`, gain `g^2(3-2g)`. GATE~0 stays open.

## Space

Delay `75ms + MORPH*280ms`. Reverb wet `SPACE^1.4 * 0.34`. MORPH tints shaper **and** stretches delay.

SPACE = delay then optional **partitioned convolution IR after the gate**. Never IR before the shaper.

### Frequency domain vs time

- Time: tanh, ADAA, gate, IIR LOW CUT / TIGHT / BODY / BITE / AIR.
- Frequency: partitioned IR, Audio Lab analysis (offline).
- Do not waveshape inside STFT. Oversample is still time-domain (upsample → ADAA → downsample).
- IIR minimum-phase for live guitar. Linear-phase FIR/STFT must report latency.

### Overlap-save (linear convolution via FFT)

Circular FFT multiply wraps. Overlap-save prevents wrap:

1. IR length M. FFT size N ≥ 2M (typically next pow2, N ≥ L+M-1).
2. Keep last M-1 samples from previous block as prefix.
3. FFT the window of N samples, multiply by precomputed H(f), IFFT.
4. **Discard the first M-1 samples** (aliased). Keep the next L samples. That is the linear result.
5. Advance input by L. Latency of one-shot OLS = hop L (plus host buffer).

Overlap-add instead keeps tails and adds them. Same linear result if hop/window are consistent. WARLOCK SPACE prefers overlap-save / uniform-partition for IR.

### Partitioned IR (realtime)

Long IR cannot be one FFT per buffer. Split h into partitions:

- First partition small (64–256) → low latency, more CPU.
- Later partitions larger → cheap tail.
- Precompute H_k(f) off-thread. No fopen/malloc in `run()`.
- IR swap: atomic pointer or crossfade. NaN/DC-check IR on load.
- Report latency = first partition. Do not claim 0 ms.
- Unknown IR license = REVIEW_REQUIRED. Do not ship proprietary IR inside the VST.

Cab IR ≠ hall IR. Cab fights AIR/BITE; hall is SPACE.

## Lab UI

Menus top, tools left, program page left-wide, canvas center, inspect + Farnaz right. SOUND: RECORD/DEMO/MORPH primary. Chat: SEND is the only loud action. Farnaz icon bottom-left.


## Desktop Operator

Farnaz on Windows (127.0.0.1:8766) can become a desktop operator. Default is DENY.

Capabilities (grant with confirm=true, 1-120 minutes):

- see — screenshot of this machine, saved locally
- apps — visible window titles
- click — mouse click at x,y
- type — short safe text, no secrets
- launch — notepad / calc / explorer / paint
- workflow — up to 8 steps of the above

## Farnaz 4.5 desktop lab

Priority stack (local, no paid API):

1. Vision = UI Automation + window titles + screenshot (not a cloud VLM).
2. Smart click = find control by name ("Build"), then existing click().
3. Voice/PTT/avatar already on /desktop.
4. Audio analysis = peak/RMS/LUFS-approx/bands → Auto Tone A/B/C.
5. JUCE preset JSON in agent state/presets.
6. Build reads compiler errors; will not auto-edit without MODIFY.
7. Jobs persist stages: start → analyze → design → build → test → confirm → done.
8. Backup → change → test → commit. Emergency STOP freezes click/type/workflow/build.
9. Secrets never typed. apps/local_agent never written.

## Factory 4.7

DPF is default for NEW plugins. THALL stays JUCE until the probe slice is proven.
Farnaz does not download CMake, Clang, DPF, pluginval, or NSIS.
First proof plugin is WARLOCK Probe (gain), not THALL.



Desktop panel: http://127.0.0.1:8766/desktop
States: idle, listening, thinking, speaking, working, success, warning, error.
Push-to-talk only. Mic is never always-on.
TTS is local-first (SAPI / espeak / pyttsx3). Browser speech is fallback.


## Free / Open-Source First

Farnaz Local Brain → free tools → DSP engine → JUCE → VST3.

Paid APIs are optional. Preset banks live in `apps/shared/presets.json`:
THALL, DJENT, DOOM, BLACK_METAL, DEATH_METAL, DEATH_HM2, STONER, CLEAN_AMBIENT, MODERN_METAL.
Each bank has DSP targets, energy vector (attack/density/frost/sludge/chainsaw/sag/hiss/sustain), and mix slot.
Mix law: `apps/shared/MIX_READY.md`. Parameter IDs stay stable. Loudness is not energy.
Memory is SQLite. Backup is Git. Permission is the operator grant layer.

