"""Golden audio compare. Python model is NOT a host VST render."""
from __future__ import annotations

import json
import math
from pathlib import Path

from ..config import PROJECT_ROOT
from .golden import process

REF_DIR = PROJECT_ROOT / "apps" / "grok_local_agent" / "factory" / "golden_refs"


def _metrics(samples: list[float]) -> dict:
    if not samples:
        return {"peak": 0.0, "rms": 0.0, "dc": 0.0, "n": 0, "clip": False}
    n = len(samples)
    peak = max(abs(x) for x in samples)
    mean = sum(samples) / n
    rms = math.sqrt(sum(x * x for x in samples) / n)
    return {
        "peak": round(peak, 6),
        "rms": round(rms, 6),
        "dc": round(mean, 6),
        "n": n,
        "clip": peak >= 0.999,
        "loudness_approx_rms_db": round(20 * math.log10(max(rms, 1e-12)), 3),
        "loudness_label": "approximate RMS dB — not LUFS",
    }


def _diff(a: dict, b: dict) -> dict:
    return {
        "peak": abs(a["peak"] - b["peak"]),
        "rms": abs(a["rms"] - b["rms"]),
        "dc": abs(a["dc"] - b["dc"]),
        "n": abs(a["n"] - b["n"]),
    }


def compare(new_samples: list[float], ref_name: str = "factory_test",
            tol: dict | None = None, expected_change: bool = False) -> dict:
    tol = tol or {"peak": 0.02, "rms": 0.02, "dc": 0.01, "n": 0}
    ref_path = REF_DIR / f"{ref_name}.json"
    new_m = _metrics(new_samples)
    if not ref_path.exists():
        return {
            "status": "FAIL",
            "ok": False,
            "reason": "no approved golden reference",
            "ref": str(ref_path),
            "new": new_m,
            "note": "Will not silently create a baseline.",
        }
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    ref_m = ref.get("metrics") or _metrics(ref.get("samples") or [])
    d = _diff(ref_m, new_m)
    over = {k: v for k, v in d.items() if v > tol.get(k, 0)}
    if not over:
        status = "PASS"
    elif expected_change:
        status = "EXPECTED_CHANGE"
    else:
        status = "UNEXPECTED_CHANGE" if max(over.values()) < 0.2 else "FAIL"
    return {
        "status": status,
        "ok": status in {"PASS", "EXPECTED_CHANGE", "WARNING"},
        "diff": d,
        "over_tolerance": over,
        "new": new_m,
        "source": "python-model",
        "note": "Not pluginval. Not a DAW render.",
    }


def approve_baseline(samples: list[float], ref_name: str, reason: str) -> dict:
    """Explicit approval only. Never called by compare()."""
    REF_DIR.mkdir(parents=True, exist_ok=True)
    path = REF_DIR / f"{ref_name}.json"
    payload = {"reason": reason, "metrics": _metrics(samples), "n": len(samples)}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path), "explicit": True}


def factory_test_vector() -> list[float]:
    # Deterministic 48k-ish sine, 256 samples.
    return [math.sin(2 * math.pi * 440 * i / 48000) for i in range(256)]
