"""Local preset brain. No API."""
from __future__ import annotations

import json
from pathlib import Path

PRESET_PATH = Path(__file__).resolve().parents[1] / "shared" / "presets.json"
NAMES = ("THALL", "DJENT", "DOOM", "BLACK_METAL", "CLEAN_AMBIENT", "MODERN_METAL")


def load() -> dict:
    return json.loads(PRESET_PATH.read_text(encoding="utf-8"))


def cards() -> list[dict]:
    data = load()
    out = [{
        "id": "preset-law",
        "topic": "preset",
        "tags": "preset brain thall djent doom free oss",
        "fact": data.get("law", "") + " Chain: " + data.get("chain", ""),
    }]
    for name, bank in data.get("banks", {}).items():
        tags = f"preset {name.lower().replace('_', ' ')} tone dsp gate oversample"
        fact = (
            f"{name} ({bank.get('family')}): "
            f"LowCut {bank.get('low_cut_hz')}Hz TIGHT {bank.get('tight')} "
            f"BODY {bank.get('body')}@{bank.get('body_freq_hz')}Hz "
            f"GAIN {bank.get('gain')} MORPH {bank.get('morph')} "
            f"BITE {bank.get('bite')}@{bank.get('bite_freq_hz')}Hz "
            f"AIR {bank.get('air')} GATE {bank.get('gate')} SPACE {bank.get('space')} "
            f"OS {bank.get('oversample')}. {bank.get('target')}. "
            f"Gate: {bank.get('gate_behavior')}. {bank.get('gain_structure')}."
        )
        out.append({"id": "preset-" + name.lower(), "topic": "preset", "tags": tags, "fact": fact})
    return out


def get(name: str) -> dict | None:
    key = (name or "").strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {"BLACK": "BLACK_METAL", "AMBIENT": "CLEAN_AMBIENT", "CLEAN": "CLEAN_AMBIENT", "MODERN": "MODERN_METAL"}
    key = aliases.get(key, key)
    return load().get("banks", {}).get(key)


def dump(name: str | None = None) -> str:
    if name:
        bank = get(name)
        if not bank:
            return "unknown preset. banks: " + ", ".join(NAMES)
        return json.dumps({name.upper(): bank}, indent=2)
    data = load()
    lines = [data.get("law", ""), data.get("chain", "")]
    for n, b in data.get("banks", {}).items():
        lines.append(f"{n}: {b.get('family')} · GATE {b.get('gate')} · GAIN {b.get('gain')} · OS {b.get('oversample')}")
    return "\n".join(lines)
