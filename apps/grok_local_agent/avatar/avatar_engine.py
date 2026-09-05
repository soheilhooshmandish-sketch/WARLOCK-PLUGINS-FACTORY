"""Persistent 2D identity. Portrait can change without touching the brain."""
from __future__ import annotations

from pathlib import Path

from .settings import load as load_settings, save as save_settings

NAME = "Farnaz"
IDENTITY_ID = "farnaz-v1"
DEFAULT_PORTRAIT = "face.svg"


def identity() -> dict:
    s = load_settings()
    portrait = s.get("portrait_path") or DEFAULT_PORTRAIT
    return {
        "name": NAME,
        "identity_id": IDENTITY_ID,
        "portrait": portrait,
        "custom_portrait": bool(s.get("portrait_path")),
        "note": "One face. Not generated per session. Swap portrait_path only.",
        "hidden": bool(s.get("hidden")),
        "volume": float(s.get("volume", 0.85)),
        "lang": s.get("lang") or "auto",
    }


def set_portrait(path: str | None) -> dict:
    s = load_settings()
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        s["portrait_path"] = str(p)
    else:
        s.pop("portrait_path", None)
    save_settings(s)
    return identity()
