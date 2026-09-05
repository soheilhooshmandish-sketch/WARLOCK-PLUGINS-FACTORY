"""Validate PluginSpec before any production C++ or build."""
from __future__ import annotations

from .spec import PluginSpec, probe_spec

FRAMEWORKS = {"DPF", "iPlug2", "LegacyJUCE"}
FORMATS = {"VST3", "CLAP", "Standalone"}
RATES = {44100, 48000, 88200, 96000, 192000}


def validate(spec: PluginSpec | dict | None = None) -> dict:
    spec = spec or probe_spec()
    if isinstance(spec, dict):
        errors = ["raw dict is not a PluginSpec object — wrap it first"]
        return {"status": "INVALID", "ok": False, "errors": errors}
    errors: list[str] = []
    if getattr(spec, "schema_version", 1) != 1:
        errors.append("unsupported schema_version")
    if not getattr(spec, "plugin_id", ""):
        errors.append("missing plugin_id")
    if not spec.plugin.strip():
        errors.append("empty name")
    if spec.framework not in FRAMEWORKS:
        errors.append(f"unsupported framework: {spec.framework}")
    if spec.framework != "DPF" and spec.template != "legacy":
        errors.append("new factory plugins must use DPF")
    if not spec.formats or "VST3" not in spec.formats:
        errors.append("VST3 is the first production target")
    ids = [p.id for p in spec.parameters]
    if len(ids) != len(set(ids)):
        errors.append("duplicate parameter id")
    for p in spec.parameters:
        if p.min > p.max:
            errors.append(f"{p.id}: min > max")
        if not (p.min <= p.default <= p.max):
            errors.append(f"{p.id}: default outside range")
        if not p.id.strip():
            errors.append("empty parameter id")
    ch = getattr(spec, "inputs", 2)
    if ch not in {1, 2}:
        errors.append("invalid channel layout")
    os_ = spec.oversampling
    if os_ not in {1, 2, 4, 8}:
        errors.append("invalid oversampling")
    if not spec.version.strip():
        errors.append("invalid version")
    return {
        "status": "VALID" if not errors else "INVALID",
        "ok": not errors,
        "errors": errors,
        "plugin_id": getattr(spec, "plugin_id", None),
    }
