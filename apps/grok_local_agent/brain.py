from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT, PROTECTED_PATHS, STATE_DIR

HELP = """فرناز 0.6.0 — ایجنت محلی هوشمند (آفلاین)
قفل: apps/local_agent و ایجنت ChatGPT روی 8765

نمونه دستور:
کی هستی | کمک | خلاصه
فهرست apps/grok_local_agent
بخوان apps/grok_local_agent/brain.py
جستجو grok_client
خلاصه فایل apps/grok_local_agent/api.py
git status | branch | diff
"""


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _is_protected(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    return any(p == g or p.startswith(g + "/") for g in PROTECTED_PATHS)


def _extract_path(text: str) -> str | None:
    match = re.search(r"([\w./\\-]+\.[a-zA-Z0-9]+|[\w./\\-]+/[\w./\\-]+)", text)
    if not match:
        return None
    return match.group(1).replace("\\", "/")


def _remember(user: str, reply: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "memory.json"
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({"t": datetime.now(timezone.utc).isoformat(), "user": user[:500], "reply": reply[:500]})
    path.write_text(json.dumps(data[-20:], ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_list(path: str) -> str:
    if _is_protected(path):
        return f"قفل: {path}"
    try:
        files = list_files(path)
        return f"{path} ({len(files)})\n" + "\n".join(files[:120])
    except Exception as exc:
        return f"list failed: {exc}"


def _safe_read(path: str) -> str:
    if _is_protected(path):
        return f"قفل: {path}"
    try:
        content = read_file(path)
        return content[:5000] + ("\n…truncated" if len(content) > 5000 else "")
    except Exception as exc:
        return f"read failed: {exc}"


def _search_name(query: str) -> str:
    hits = []
    q = query.lower()
    for p in PROJECT_ROOT.rglob("*"):
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if _is_protected(rel):
            continue
        if q in p.name.lower():
            hits.append(rel)
        if len(hits) >= 40:
            break
    return "\n".join(hits) or "چیزی پیدا نشد."


def _summarize_file(path: str) -> str:
    raw = _safe_read(path)
    if raw.startswith("قفل") or raw.startswith("read failed"):
        return raw
    defs = re.findall(r"^(def |class |async def )(.+)$", raw, re.M)
    lines = raw.splitlines()
    head = "\n".join(lines[:25])
    names = ", ".join((a + b).strip()[:80] for a, b in defs[:20]) or "(no defs)"
    return f"{path}  lines={len(lines)}\nsymbols: {names}\n\n{head}"


def _overview() -> str:
    bits = [
        f"{AGENT_NAME} {AGENT_VERSION} @8766",
        f"python {sys.version.split()[0]}",
        str(PROJECT_ROOT),
    ]
    try:
        bits.append("branch " + git_branch())
    except Exception as exc:
        bits.append(str(exc))
    try:
        bits.append(git_status() or "git clean")
    except Exception as exc:
        bits.append(str(exc))
    bits.append(_safe_list("apps/grok_local_agent"))
    return "\n".join(bits)


def reply(message: str) -> dict:
    text = message.strip()
    key = _norm(text)
    used: list[str] = []
    chunks: list[str] = []

    if any(w in key for w in ("help", "کمک", "چه کار", "چیکار", "توان")):
        used.append("help")
        chunks.append(HELP)
    if any(w in key for w in ("کی هستی", "who are you", "اسم", "سلامت", "health")):
        used.append("identity")
        chunks.append(f"من {AGENT_NAME} هستم، نسخه {AGENT_VERSION}. ایجنت اصلی را تغییر نمی‌دهم.")
    if any(w in key for w in ("overview", "خلاصه", "وضعیت پروژه")) and "خلاصه فایل" not in key:
        used.append("overview")
        chunks.append(_overview())
    if any(w in key for w in ("workspace", "پروژه", "کجا")):
        used.append("workspace")
        chunks.append(str(PROJECT_ROOT))
    if "جستجو" in key or key.startswith("find ") or key.startswith("search "):
        q = re.sub(r"^(جستجو|find|search)\s+", "", text, flags=re.I).strip()
        used.append("search")
        chunks.append(_search_name(q or "grok"))
    if "خلاصه فایل" in key or key.startswith("summarize "):
        path = _extract_path(text) or "apps/grok_local_agent/brain.py"
        used.append("summarize")
        chunks.append(_summarize_file(path))
    if any(w in key for w in ("git status",)) or key in {"git", "وضعیت گیت"}:
        used.append("git_status")
        try:
            chunks.append(git_status() or "clean")
        except Exception as exc:
            chunks.append(str(exc))
    if "branch" in key or "شاخه" in key:
        used.append("git_branch")
        try:
            chunks.append(git_branch())
        except Exception as exc:
            chunks.append(str(exc))
    if "diff" in key:
        used.append("git_diff")
        try:
            chunks.append(git_diff() or "no diff")
        except Exception as exc:
            chunks.append(str(exc))
    if any(w in key for w in ("بخوان", "read ", "cat ")):
        path = _extract_path(text) or "apps/grok_local_agent/brain.py"
        used.append("read_file")
        chunks.append(_safe_read(path))
    if any(w in key for w in ("list", "فهرست", "ls", "dir")) or ("فایل" in key and "خلاصه فایل" not in key):
        path = _extract_path(text) or "apps/grok_local_agent"
        used.append("list_files")
        chunks.append(_safe_list(path))

    if not chunks:
        path = _extract_path(text)
        if path and not _is_protected(path):
            target = PROJECT_ROOT / path
            if target.exists():
                used.append("auto")
                chunks.append(_safe_list(path) if target.is_dir() else _summarize_file(path))
        if not chunks:
            used.append("fallback")
            chunks.append(f"{AGENT_NAME} پیام را گرفت.\n{text}\n\n{HELP}")

    content = "\n\n".join(chunks)
    try:
        _remember(text, content)
    except Exception:
        pass
    return {
        "model": "farnaz-super-offline",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "tools": used,
        "content": content,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
