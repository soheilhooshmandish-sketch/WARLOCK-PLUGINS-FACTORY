from pathlib import Path
import re
import sys

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import PROJECT_ROOT, PROTECTED_PATHS, SKIP_DIRS, STATE_DIR


def protected(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    return any(p == g or p.startswith(g + "/") for g in PROTECTED_PATHS)


def skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def extract_path(text: str) -> str | None:
    m = re.search(r"([\w./\\-]+\.[A-Za-z0-9]+|[\w./\\-]+/[\w./\\-]+)", text)
    return m.group(1).replace("\\", "/") if m else None


def list_dir(path: str = "apps/grok_local_agent") -> str:
    if protected(path):
        return f"LOCKED {path}"
    files = list_files(path)
    return f"{path} ({len(files)})\n" + "\n".join(files[:200])


def read(path: str) -> str:
    if protected(path):
        return f"LOCKED {path}"
    data = read_file(path)
    return data[:8000] + ("\n…" if len(data) > 8000 else "")


def summarize(path: str) -> str:
    raw = read(path)
    if raw.startswith("LOCKED"):
        return raw
    defs = re.findall(r"^(?:async def|def|class)\s+\w+", raw, re.M)
    return f"{path} lines={len(raw.splitlines())}\n" + ", ".join(defs[:40])


def search_names(query: str, limit: int = 60) -> str:
    q = query.lower().strip()
    hits = []
    for p in PROJECT_ROOT.rglob("*"):
        if skip(p) or not p.is_file():
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if protected(rel):
            continue
        if q in p.name.lower() or q in rel.lower():
            hits.append(rel)
        if len(hits) >= limit:
            break
    return "\n".join(hits) or "no name matches"


def search_text(query: str, limit: int = 30) -> str:
    q = query.lower().strip()
    if len(q) < 2:
        return "query too short"
    hits = []
    for p in PROJECT_ROOT.rglob("*.py"):
        if skip(p):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if protected(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if q not in text.lower():
            continue
        line = next((ln.strip() for ln in text.splitlines() if q in ln.lower()), "")
        hits.append(f"{rel}: {line[:160]}")
        if len(hits) >= limit:
            break
    return "\n".join(hits) or "no text matches"


def index_top() -> str:
    rows = []
    for child in sorted(PROJECT_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if child.name.startswith(".") or child.name in SKIP_DIRS:
            continue
        rel = child.name
        if protected(rel):
            rows.append(f"{rel}/ LOCKED")
            continue
        mark = "/" if child.is_dir() else ""
        rows.append(rel + mark)
    return "\n".join(rows)


def note_write(text: str) -> str:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "notes.md"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text.strip() + "\n")
    return f"noted -> {path.relative_to(PROJECT_ROOT).as_posix()}"


def note_read() -> str:
    path = STATE_DIR / "notes.md"
    if not path.exists():
        return "no notes yet"
    return path.read_text(encoding="utf-8")[-4000:]


def git_info(kind: str) -> str:
    fn = {"status": git_status, "branch": git_branch, "diff": git_diff}[kind]
    return fn() or "ok"


def runtime() -> str:
    return f"python {sys.version.split()[0]} cwd={PROJECT_ROOT}"
