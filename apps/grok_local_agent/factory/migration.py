"""Preset / parameter identity. Names may change; IDs must not."""
from __future__ import annotations

from .spec import PluginSpec, probe_spec


def migrate(preset: dict, spec: PluginSpec | None = None) -> dict:
    spec = spec or probe_spec()
    ids = {p.id: p for p in spec.parameters}
    src = dict(preset.get("params") or preset.get("parameters") or preset)
    out = {}
    unknown = []
    missing = []
    for pid, param in ids.items():
        if pid in src:
            try:
                val = float(src[pid])
            except (TypeError, ValueError):
                val = param.default
            out[pid] = max(param.min, min(param.max, val))
        else:
            out[pid] = param.default
            missing.append(pid)
    for k in src:
        if k not in ids:
            unknown.append(k)
    incompatible = bool(unknown) and preset.get("schema_version") not in {None, "0.1.0", spec.version}
    return {
        "ok": not incompatible,
        "params": out,
        "missing_filled": missing,
        "unknown_ignored": unknown,
        "incompatible": incompatible,
        "note": "Changing a knob label does not change parameter_id.",
    }
