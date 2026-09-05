"""PluginSpec → framework generator. DPF default."""
from __future__ import annotations

from .frameworks import dpf_gen, iplug2_gen, juce_legacy
from .spec import PluginSpec


def generate(spec: PluginSpec, framework: str | None = None) -> dict:
    fw = (framework or spec.framework or "DPF").upper()
    if fw in {"JUCE", "LEGACYJUCE"}:
        return juce_legacy.generate(spec)
    if fw in {"IPLUG2", "IPLUG"}:
        return iplug2_gen.generate(spec)
    return dpf_gen.generate(spec)
