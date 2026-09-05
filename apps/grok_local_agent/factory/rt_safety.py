"""Static scan of generated DSP. Heuristic, not a proof of realtime safety."""
from __future__ import annotations

import re
from pathlib import Path

BANNED = [
    r"\bfopen\s*\(", r"\bifstream\b", r"\bofstream\b", r"\bsystem\s*\(",
    r"\bsleep\s*\(", r"\bSleep\s*\(", r"\bstd::thread\b", r"\bnew\s+",
    r"\bmalloc\s*\(", r"\brealloc\s*\(", r"\bprintf\s*\(", r"\bcout\b",
    r"\bsocket\s*\(", r"\bconnect\s*\(", r"\bPy_", r"\bpopen\s*\(",
]


def scan(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    # Only inspect run() body if present
    m = re.search(r"void run\s*\((.*?)\)\s*\{(.*)\n    \}", text, re.S)
    body = m.group(2) if m else text
    hits = []
    for pat in BANNED:
        if re.search(pat, body):
            hits.append(pat)
    return {
        "ok": not hits,
        "hits": hits,
        "path": str(path),
        "note": "Scan is heuristic. Passing is not a formal RT proof.",
    }
