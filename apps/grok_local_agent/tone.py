"""Auto Tone A/B/C from guitar analysis + preset brain. JUCE-ready JSON."""
from __future__ import annotations

import json
from pathlib import Path

from .audio_lab import analyze
from .config import STATE_DIR
from .presets import get


def _n01(x, lo=0, hi=100) -> float:
    return round(max(0.0, min(1.0, (float(x) - lo) / (hi - lo))), 3)


def _from_bank(name: str) -> dict:
    bank = get(name) or get("THALL") or {}
    return {
        "GAIN": _n01(bank.get("gain", 40)),
        "TIGHT": _n01(bank.get("tight", 70)),
        "BODY": _n01(bank.get("body", 55)),
        "MORPH": _n01(bank.get("morph", 40)),
        "GATE": _n01(bank.get("gate", 55)),
        "BITE": _n01(bank.get("bite", 48)),
        "AIR": _n01(bank.get("air", 35)),
    }


def _tweak(base: dict, analysis: dict, flavor: str) -> dict:
    p = dict(base)
    notes = " ".join(analysis.get("notes") or []).lower()
    if "low-end" in notes:
        p["TIGHT"] = min(1.0, p["TIGHT"] + 0.08)
        p["BODY"] = max(0.0, p["BODY"] - 0.05)
    if "mud" in notes:
        p["BODY"] = max(0.0, p["BODY"] - 0.07)
    if "attack" in notes or "bite" in notes:
        p["BITE"] = min(1.0, p["BITE"] + 0.08)
    if "noise" in notes:
        p["GATE"] = min(1.0, p["GATE"] + 0.1)
    if "peaks hot" in notes:
        p["GAIN"] = max(0.0, p["GAIN"] - 0.08)
    if flavor == "A":
        p["TIGHT"] = min(1.0, p["TIGHT"] + 0.06)
        p["GATE"] = min(1.0, p["GATE"] + 0.05)
        p["label"] = "tight chug"
    elif flavor == "B":
        p["label"] = "balanced mix"
    else:
        p["MORPH"] = min(1.0, p["MORPH"] + 0.12)
        p["AIR"] = min(1.0, p["AIR"] + 0.08)
        p["GATE"] = max(0.0, p["GATE"] - 0.08)
        p["label"] = "open / ambient-lean"
    for k, v in list(p.items()):
        if k != "label" and isinstance(v, (int, float)):
            p[k] = round(float(v), 3)
    return p


def propose(wav_path: str | None = None, family: str = "THALL") -> dict:
    analysis = analyze(wav_path) if wav_path else {"ok": True, "notes": ["no wav — using preset brain only"]}
    if wav_path and not analysis.get("ok"):
        return analysis
    base = _from_bank(family)
    tones = {k: _tweak(base, analysis, k) for k in ("A", "B", "C")}
    target_lufs = analysis.get("lufs_approx")
    return {
        "ok": True,
        "family": family,
        "analysis": analysis,
        "loudness_match": {
            "target_lufs_approx": target_lufs,
            "rule": "Compare A/B/C at the same LUFS. Louder is not better.",
        },
        "tones": tones,
        "juce": {k: {p: v for p, v in tones[k].items() if p != "label"} for k in tones},
    }


def export_juce(tones: dict, stem: str = "thall_auto") -> dict:
    out_dir = STATE_DIR / "presets"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, params in (tones.get("juce") or tones).items():
        path = out_dir / f"{stem}_{key.lower()}.json"
        payload = {"plugin": "THALL", "source": "farnaz-auto-tone", "params": params}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(str(path))
    return {"ok": True, "files": written}
