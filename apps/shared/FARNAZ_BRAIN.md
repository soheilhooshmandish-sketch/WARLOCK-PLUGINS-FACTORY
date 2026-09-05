# Farnaz brain - shared with ChatGPT

ChatGPT agent (port 8765) may **read** this file. Do not rewrite `apps/local_agent`.

Path: `apps/shared/FARNAZ_BRAIN.md`
JSON: `apps/shared/farnaz_brain.json`

## How ChatGPT uses it

Read `apps/shared/farnaz_brain.json` (or this markdown) before answering DSP, Thall, oversample, ADAA, gate, or lab layout questions.

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

https://dafx16.vutbr.cz/dafxpapers/20-DAFx-16_paper_41-PN.pdf
https://vicanek.de/articles/AADistortion.pdf

## Gate

Sample-wise worklet: peak magnitude, exp envelope (~1.5 ms attack, 55-185 ms release from GATE), threshold `0.00008 + 0.0085*GATE^2`, close at `0.58*threshold`, gain `g^2(3-2g)`. GATE~0 stays open.

## Space

Delay `75ms + MORPH*280ms`. Reverb wet `SPACE^1.4 * 0.34`. MORPH tints shaper **and** stretches delay.

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

Never controls apps/local_agent. Never binds 0.0.0.0. Screenshot does not leave the PC.
