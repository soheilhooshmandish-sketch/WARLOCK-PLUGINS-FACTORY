"""iPlug2 adapter stub. Not feature-complete. Same PluginSpec as DPF."""
from __future__ import annotations

from ..spec import PluginSpec


def generate(spec: PluginSpec) -> dict:
    return {
        "ok": False,
        "framework": "iPlug2",
        "error": "adapter reserved — DPF is default. No iPlug2 generate until DPF slice is proven.",
        "spec": spec.plugin,
    }
