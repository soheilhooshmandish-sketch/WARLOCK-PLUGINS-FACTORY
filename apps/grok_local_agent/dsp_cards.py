"""Load shared Farnaz brain JSON. Used by Grok agent; ChatGPT may read the JSON directly."""

from __future__ import annotations

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "shared" / "farnaz_brain.json"


def _load() -> tuple[list[dict], list[dict], str]:
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    return data.get("cards") or [], data.get("sources") or [], data.get("dsp_brain") or ""


CARDS, SOURCES, DSP_BRAIN = _load()
