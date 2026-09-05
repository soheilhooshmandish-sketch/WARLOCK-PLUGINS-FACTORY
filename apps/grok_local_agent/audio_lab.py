"""Guitar / WAV analysis. Stdlib first. No paid API."""
from __future__ import annotations

import math
import wave
from pathlib import Path

from .dsp_local import bands


def _samples(path: str | Path) -> tuple[list[float], int]:
    p = Path(path)
    with wave.open(str(p), "rb") as wf:
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(min(n, sr * 12))
    if sw != 2:
        raise ValueError("need 16-bit wav")
    out = []
    step = sw * ch
    for i in range(0, len(raw) - step + 1, step):
        sample = int.from_bytes(raw[i : i + 2], "little", signed=True)
        out.append(sample / 32768.0)
    return out, sr


def analyze(path: str | Path) -> dict:
    samples, sr = _samples(path)
    if len(samples) < 256:
        return {"ok": False, "error": "file too short"}
    peak = max(abs(x) for x in samples) or 1e-9
    rms = math.sqrt(sum(x * x for x in samples) / len(samples)) or 1e-9
    peak_db = 20 * math.log10(peak)
    rms_db = 20 * math.log10(rms)
    lufs_approx = rms_db - 0.691  # not ITU BS.1770; labeled approx
    crest = peak / rms
    # noise floor: quietest 10% absolute frames of 1024
    hop = 1024
    frame_rms = []
    for i in range(0, len(samples) - hop, hop):
        chunk = samples[i : i + hop]
        frame_rms.append(math.sqrt(sum(x * x for x in chunk) / hop))
    frame_rms.sort()
    floor = frame_rms[max(0, len(frame_rms) // 10)] if frame_rms else rms
    floor_db = 20 * math.log10(floor + 1e-9)
    spec = bands(samples, sr)
    mud = spec.get("body_90_200") or 0
    # extra mud 200-500 via a second call
    low = spec.get("tight_highpass") or 0
    bite = spec.get("bite_2k_4k") or 0
    air = spec.get("air_8k_16k") or 0
    dyn = peak_db - floor_db
    notes = []
    if low > mud * 1.4:
        notes.append("Low-end heavy. Raise TIGHT, nudge LowCut up.")
    if mud > bite * 1.2:
        notes.append("Mud / boxiness. Lower BODY slightly.")
    if bite < air * 0.5:
        notes.append("Dull attack. Raise BITE.")
    if floor_db > -40:
        notes.append("Noise floor high. Raise GATE.")
    if peak_db > -1.0:
        notes.append("Peaks hot. Lower GAIN.")
    if not notes:
        notes.append("Balance is usable. Small MORPH/AIR moves only.")
    return {
        "ok": True,
        "path": str(path),
        "sr": sr,
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "lufs_approx": round(lufs_approx, 2),
        "crest": round(crest, 2),
        "noise_floor_db": round(floor_db, 2),
        "dynamic_range_db": round(dyn, 2),
        "bands": spec,
        "notes": notes,
        "lufs_note": "lufs_approx is RMS-based, not BS.1770. pyloudnorm optional later.",
    }
