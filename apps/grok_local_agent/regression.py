"""DSP safety on synthetic signals. Does not change WARLOCK topology."""
from __future__ import annotations

import math

from .dsp_local import bands


def _stats(samples: list[float]) -> dict:
    if not samples:
        return {"ok": False, "error": "empty"}
    peak = max(abs(x) for x in samples)
    mean = sum(samples) / len(samples)
    bad = any(math.isnan(x) or math.isinf(x) for x in samples)
    return {
        "ok": not bad and peak < 8.0,
        "n": len(samples),
        "peak": round(peak, 5),
        "dc": round(mean, 6),
        "nan_or_inf": bad,
        "clip_guess": peak >= 0.999,
    }


def suite() -> dict:
    n = 2048
    silence = [0.0] * n
    sine = [0.2 * math.sin(2 * math.pi * 440 * i / 48000) for i in range(n)]
    hot = [math.tanh(3 * math.sin(2 * math.pi * 110 * i / 48000)) for i in range(n)]
    cases = {
        "silence": _stats(silence),
        "sine_440": _stats(sine),
        "hot_tanh": _stats(hot),
    }
    cases["sine_440"]["bands"] = bands(sine, 48000)
    passed = all(v.get("ok") for v in cases.values())
    return {
        "ok": passed,
        "cases": cases,
        "note": "Analyzer only. Native VST not loaded. No DSP chain reorder.",
    }
