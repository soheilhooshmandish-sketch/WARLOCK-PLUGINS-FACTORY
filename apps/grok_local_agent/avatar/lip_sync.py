"""Lightweight visemes from text. Replaceable with a heavier model later."""
from __future__ import annotations

import math
import wave
from pathlib import Path

MOUTH = {
    "M": "m",
    "A": "a",
    "O": "o",
    "E": "e",
    "F": "f",
    "REST": "rest",
}

_A = set("اآعیََاaàáâäæ")
_O = set("وُoôöøuùúûü")
_E = set("eéèêëیِiíîïy")
_M = set("mbpپبم")
_F = set("fvف")


def detect_lang(text: str) -> str:
    fa = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    return "fa" if fa >= 2 else "en"


def visemes_from_text(text: str) -> list[dict]:
    clean = (text or "").strip()
    if not clean:
        return [{"t": 0, "mouth": "rest", "open": 0.0}]
    lang = detect_lang(clean)
    ms = 72 if lang == "fa" else 55
    frames = []
    t = 0
    for ch in clean[:800]:
        if ch.isspace():
            mouth, open_ = "rest", 0.05
            dur = ms
        elif ch in _M:
            mouth, open_ = "m", 0.0
            dur = ms
        elif ch in _O:
            mouth, open_ = "o", 0.85
            dur = int(ms * 1.25)
        elif ch in _A:
            mouth, open_ = "a", 0.9
            dur = int(ms * 1.2)
        elif ch in _E:
            mouth, open_ = "e", 0.55
            dur = ms
        elif ch in _F:
            mouth, open_ = "f", 0.25
            dur = ms
        elif ch.isalnum() or "\u0600" <= ch <= "\u06ff":
            mouth, open_ = "e", 0.35
            dur = ms
        else:
            mouth, open_ = "rest", 0.08
            dur = int(ms * 0.6)
        frames.append({"t": t, "mouth": mouth, "open": open_})
        t += dur
    frames.append({"t": t, "mouth": "rest", "open": 0.0})
    return frames


def visemes_from_wav(path: str | Path, hop_ms: int = 40) -> list[dict]:
    p = Path(path)
    with wave.open(str(p), "rb") as wf:
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    if sw != 2:
        return visemes_from_text("")
    hop = max(1, int(sr * hop_ms / 1000))
    frames = []
    total = len(raw) // (sw * ch)
    peak = 1
    rms_list = []
    for i in range(0, total, hop):
        acc = 0
        count = 0
        for s in range(i, min(i + hop, total)):
            idx = s * sw * ch
            sample = int.from_bytes(raw[idx : idx + 2], "little", signed=True)
            acc += sample * sample
            count += 1
        rms = math.sqrt(acc / max(count, 1))
        rms_list.append(rms)
        peak = max(peak, rms)
    t = 0
    for rms in rms_list:
        amp = min(1.0, rms / peak)
        if amp < 0.08:
            mouth, open_ = "rest", 0.0
        elif amp < 0.25:
            mouth, open_ = "m", 0.1
        elif amp < 0.45:
            mouth, open_ = "e", amp
        elif amp < 0.7:
            mouth, open_ = "a", amp
        else:
            mouth, open_ = "o", amp
        frames.append({"t": t, "mouth": mouth, "open": round(open_, 3)})
        t += hop_ms
    frames.append({"t": t, "mouth": "rest", "open": 0.0})
    return frames


def duration_ms(frames: list[dict]) -> int:
    if not frames:
        return 0
    return int(frames[-1]["t"])
