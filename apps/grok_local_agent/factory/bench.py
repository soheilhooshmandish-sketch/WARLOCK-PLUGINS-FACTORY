"""Independent tests. Honest when we cannot load a VST3 host."""
from __future__ import annotations

from pathlib import Path


def run(vst3: Path | None) -> dict:
    if not vst3 or not Path(vst3).exists():
        return {
            "ok": False,
            "error": "no vst3 artifact",
            "tests": {"existence": False},
        }
    p = Path(vst3)
    size = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return {
        "ok": size > 0,
        "tests": {
            "existence": True,
            "bytes": size,
            "loading": "not-run",
            "nan": "not-run",
            "cpu": "not-run",
            "note": "Hosted audio/CPU tests need a real VST3 + pluginval/DAW. Not simulated.",
        },
    }
