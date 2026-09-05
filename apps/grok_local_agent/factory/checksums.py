"""SHA-256 provenance. Never claim a hash for a missing artifact."""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256(path: Path) -> dict:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "artifact missing", "path": str(p)}
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return {"ok": True, "path": str(p), "sha256": h.hexdigest(), "bytes": p.stat().st_size}


def bundle(paths: list[Path], meta: dict | None = None) -> dict:
    items = [sha256(p) for p in paths]
    present = [i for i in items if i.get("ok")]
    return {
        "ok": bool(present) and all(i.get("ok") for i in items),
        "items": items,
        "meta": meta or {},
    }
