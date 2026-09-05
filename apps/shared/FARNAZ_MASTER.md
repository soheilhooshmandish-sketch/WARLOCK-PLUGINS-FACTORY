# FARNAZ MASTER RULE

This file is the operating law. Every later upgrade must obey it.

Base at write time: **4.5.0** `4b2ea2bc24f7a94fc9fe106e303d6a1d240ecb81`

## Four laws

1. **BACKUP → MODIFY → TEST → VERIFY → COMMIT.** If verify fails: STOP, REPORT, FIX or ROLLBACK.
2. **Never touch `apps/local_agent`.** Port 8765 stays the ChatGPT agent. Farnaz is `apps/grok_local_agent` :8766.
3. **Free / Local first.** Paid APIs are optional. Farnaz must start without them.
4. **Do not claim success without a real test.** Code existing is not done.

## One intelligence

Brain = intelligence. Avatar = face. Voice = speech. Operator = hands. Vision = eyes. Mic = ears. Memory = continuity.

Loop:

PERCEIVE → UNDERSTAND → PLAN → PERMISSION → BACKUP IF MODIFY → ACT → OBSERVE → VERIFY → CHECKPOINT → REPORT

Never replace this with blind clicking.

## Preserve (do not rewrite)

- `apps/grok_local_agent/*` working modules (operator, windows, brain, biz, dsp, presets, avatar, vision, smart_ui, tone, jobs, killswitch, levels, builder)
- `apps/shared/` brain, presets, architecture
- Default-deny grants: see, apps, click, type, launch, workflow
- DSP chain: HP/TIGHT → Tight shelf → Body → Drive → tanh(MORPH) → Bite → Air → Gate → Delay/Reverb → Trim
- Secret typing deny, emergency stop, SQLite checkpoints

## Do not

- Rebuild Farnaz from scratch
- Merge into the ChatGPT agent
- Bind 0.0.0.0
- Upload mic/screenshots by default
- Auto-publish a VST
- Reorder the DSP chain without tests
- Keep heavy models running while FL Studio is recording
