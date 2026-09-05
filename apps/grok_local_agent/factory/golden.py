"""Python model of Factory Test DSP. This is NOT a VST render."""
from __future__ import annotations

import math


def process(samples: list[float], gain: float = 1.0, output: float = 1.0, bypass: bool = False) -> dict:
    out = []
    sg = so = 1.0
    a = 0.05
    bad = False
    for x in samples:
        sg += a * (gain - sg)
        so += a * (output - so)
        y = x if bypass else math.tanh(x * sg) * so
        if not math.isfinite(y):
            y = 0.0
            bad = True
        out.append(y)
    peak = max((abs(v) for v in out), default=0.0)
    return {
        "ok": not bad and peak < 8.0,
        "n": len(out),
        "peak": round(peak, 6),
        "nan_or_inf": bad,
        "source": "python-model",
        "note": "Not pluginval. Not a host render.",
        "samples": out,
    }
