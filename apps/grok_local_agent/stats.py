from collections import Counter
from pathlib import Path

from .config import PROJECT_ROOT, SKIP_DIRS
from .tools import protected


def file_types() -> str:
    counts: Counter[str] = Counter()
    for p in PROJECT_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if protected(rel):
            continue
        counts[p.suffix.lower() or "(none)"] += 1
    top = counts.most_common(12)
    return "types\n" + "\n".join(f"{ext:10} {n}" for ext, n in top)


def lock_ok() -> str:
    root = PROJECT_ROOT / "apps" / "local_agent"
    if not root.exists():
        return "WARNING: original agent folder missing"
    names = sorted(p.name for p in root.glob("*.py"))
    return "lock OK apps/local_agent\n" + ", ".join(names)
