"""Local DSP / audio analysis. NumPy if present, stdlib FFT otherwise. No API."""
from __future__ import annotations

import math


def _fft_mags(samples: list[float]) -> list[float]:
    try:
        import numpy as np
        spec = np.fft.rfft(np.asarray(samples, dtype=float))
        return np.abs(spec).tolist()
    except Exception:
        n = len(samples)
        n2 = n // 2
        out = []
        for k in range(n2):
            re = im = 0.0
            for t, x in enumerate(samples):
                ang = 2 * math.pi * k * t / n
                re += x * math.cos(ang)
                im -= x * math.sin(ang)
            out.append(math.hypot(re, im) / n)
        return out


def bands(samples: list[float], sr: int = 48000) -> dict:
    if len(samples) < 64:
        return {"error": "need >=64 samples"}
    mags = _fft_mags(samples[:4096] if len(samples) > 4096 else samples)
    n = len(mags)
    hz = sr / (2 * max(n - 1, 1))

    def energy(lo: float, hi: float) -> float:
        a = max(0, int(lo / hz))
        b = min(n, int(hi / hz) + 1)
        chunk = mags[a:b] or [0.0]
        return sum(chunk) / len(chunk)

    return {
        "backend": "numpy-or-stdlib",
        "sr": sr,
        "n": len(samples),
        "tight_highpass": round(energy(20, 160), 6),
        "body_90_200": round(energy(90, 200), 6),
        "bite_2k_4k": round(energy(2000, 4000), 6),
        "air_8k_16k": round(energy(8000, 16000), 6),
        "note": "Map these to TIGHT / BODY / BITE / AIR. No librosa required.",
    }


def sine_probe(preset: str = "THALL") -> dict:
    from .presets import get
    bank = get(preset) or get("THALL") or {}
    sr = 48000
    freq = float(bank.get("bite_freq_hz") or 1000)
    n = 2048
    samples = [math.sin(2 * math.pi * freq * i / sr) for i in range(n)]
    result = bands(samples, sr)
    result["preset"] = preset
    result["probe_hz"] = freq
    return result
