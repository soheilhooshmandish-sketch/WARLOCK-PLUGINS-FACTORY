"""VST3 validation without a DAW host. Honest about what we cannot load."""
from __future__ import annotations

from pathlib import Path

from .config import PROJECT_ROOT


def inspect(path: str | None = None) -> dict:
    root = Path(path) if path else PROJECT_ROOT / "native"
    hits = list(root.rglob("*.vst3"))[:20] if root.exists() else []
    reports = []
    for p in hits:
        bundle = p if p.is_dir() else p.parent
        size = sum(f.stat().st_size for f in (bundle.rglob("*") if bundle.exists() else []) if f.is_file())
        reports.append({
            "path": str(p.relative_to(PROJECT_ROOT)) if PROJECT_ROOT in p.parents else str(p),
            "bytes": size,
            "has_moduleinfo": (bundle / "Contents" / "moduleinfo.json").exists() or (bundle / "moduleinfo.json").exists(),
            "load_test": "not-run",
            "note": "No in-process VST host here. Load/automation/CPU must be checked in a validator (pluginval) or DAW after BUILD grant.",
        })
    return {
        "ok": True,
        "count": len(reports),
        "plugins": reports,
        "pluginval": "optional OSS: https://github.com/Tracktion/pluginval — not bundled.",
    }
