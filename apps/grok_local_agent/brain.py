from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT, PROTECTED_PATHS, SKIP_DIRS, STATE_DIR

HELP = """فرناز 0.7.0 — ایجنت محلی هوشمند
قفل دائمی: apps/local_agent و ChatGPT روی 8765

بپرسید: کی هستی، کمک، خلاصه، فهرست، بخوان، جستجو، پیدا کن متن، git، چی بلدی
"""


def _n(text: str) -> str:
    return " ".join(text.lower().replace("‌", " ").split())


def _protected(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    return any(p == g or p.startswith(g + "/") for g in PROTECTED_PATHS)


def _path_in(text: str) -> str | None:
    m = re.search(r"([\w./\\-]+\.[A-Za-z0-9]+|[\w./\\-]+/[\w./\\-]+)", text)
    return m.group(1).replace("\\", "/") if m else None


def _skip(p: Path) -> bool:
    return any(part in SKIP_DIRS for part in p.parts)


def _remember(user: str, reply: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "memory.json"
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({"t": datetime.now(timezone.utc).isoformat(), "user": user[:400], "reply": reply[:400]})
    path.write_text(json.dumps(data[-30:], ensure_ascii=False, indent=2), encoding="utf-8")


def _list(path: str) -> str:
    if _protected(path):
        return f"قفل است: {path}"
    try:
        files = list_files(path)
        return f"{path} ({len(files)})\n" + "\n".join(files[:150])
    except Exception as exc:
        return str(exc)


def _read(path: str) -> str:
    if _protected(path):
        return f"قفل است: {path}"
    try:
        c = read_file(path)
        return c[:6000] + ("\n…" if len(c) > 6000 else "")
    except Exception as exc:
        return str(exc)


def _search_names(q: str) -> str:
    hits = []
    ql = q.lower()
    for p in PROJECT_ROOT.rglob("*"):
        if _skip(p):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if _protected(rel):
            continue
        if ql in p.name.lower():
            hits.append(rel)
        if len(hits) >= 50:
            break
    return "\n".join(hits) or "نتیجه‌ای نبود."


def _search_text(q: str) -> str:
    if len(q) < 2:
        return "عبارت کوتاه است."
    hits = []
    ql = q.lower()
    for p in PROJECT_ROOT.rglob("*.py"):
        if _skip(p):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if _protected(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if ql in text.lower():
            line = next((ln.strip() for ln in text.splitlines() if ql in ln.lower()), "")
            hits.append(f"{rel}: {line[:140]}")
        if len(hits) >= 25:
            break
    return "\n".join(hits) or "در متن پیدا نشد."


def _summarize(path: str) -> str:
    raw = _read(path)
    if raw.startswith("قفل") or "failed" in raw.lower():
        return raw
    defs = re.findall(r"^(?:async def|def|class)\s+\w+", raw, re.M)
    return f"{path}  {len(raw.splitlines())} lines\n" + ", ".join(defs[:25])


def _overview() -> str:
    rows = [f"{AGENT_NAME} {AGENT_VERSION} :8766", f"py {sys.version.split()[0]}", str(PROJECT_ROOT)]
    for fn, label in ((git_branch, "branch"), (git_status, "git")):
        try:
            rows.append(f"{label}: {fn() or 'ok'}")
        except Exception as exc:
            rows.append(f"{label}: {exc}")
    rows.append(_list("apps/grok_local_agent"))
    return "\n".join(rows)


def _score(key: str, words: tuple[str, ...]) -> int:
    return sum(1 for w in words if w in key)


def reply(message: str) -> dict:
    text = message.strip()
    key = _n(text)
    used: list[str] = []
    chunks: list[str] = []
    path = _path_in(text)

    checks = [
        (("help", "کمک", "چی بلدی", "چه کار", "چیکار", "توان"), "help", lambda: HELP),
        (("کی هستی", "who are you", "اسمت", "سلامت", "health"), "identity",
         lambda: f"من {AGENT_NAME} هستم، نسخه {AGENT_VERSION}. ایجنت محلی هوشمند. ChatGPT روی 8765 قفل است."),
        (("overview", "خلاصه", "وضعیت پروژه"), "overview", _overview),
        (("workspace", "پروژه کجاست", "کجا هست"), "workspace", lambda: str(PROJECT_ROOT)),
    ]
    for words, name, fn in checks:
        if _score(key, words):
            if name == "overview" and "خلاصه فایل" in key:
                continue
            used.append(name)
            chunks.append(fn())

    if _score(key, ("پیدا کن متن", "search text", "در کد", "grep")):
        q = re.sub(r"^(پیدا کن متن|search text|grep)\s+", "", text, flags=re.I).strip() or "Farnaz"
        used.append("content-search")
        chunks.append(_search_text(q))
    elif _score(key, ("جستجو", "find", "search", "پیدا")):
        q = re.sub(r"^(جستجو|find|search|پیدا کن)\s+", "", text, flags=re.I).strip()
        used.append("name-search")
        chunks.append(_search_names(q or "farnaz"))

    if _score(key, ("خلاصه فایل", "summarize")):
        used.append("summarize")
        chunks.append(_summarize(path or "apps/grok_local_agent/brain.py"))
    if _score(key, ("git status", "وضعیت گیت")) or key == "git":
        used.append("git_status")
        try:
            chunks.append(git_status() or "clean")
        except Exception as exc:
            chunks.append(str(exc))
    if _score(key, ("branch", "شاخه")):
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
    if _score(key, ("بخوان", "read ", "cat ")):
        used.append("read")
        chunks.append(_read(path or "apps/grok_local_agent/brain.py"))
    if _score(key, ("list", "فهرست", "ls", "dir")):
        used.append("list")
        chunks.append(_list(path or "apps/grok_local_agent"))

    if not chunks:
        if path and not _protected(path):
            target = PROJECT_ROOT / path
            if target.exists():
                used.append("auto")
                chunks.append(_list(path) if target.is_dir() else _summarize(path))
        if not chunks:
            used.append("reason")
            extra = _search_names(key.split()[0]) if key else ""
            chunks.append(f"{AGENT_NAME} درخواست را تحلیل کرد.\n{text}\n\n{HELP}\n\n{extra}")

    content = "\n\n".join(chunks)
    try:
        _remember(text, content)
    except Exception:
        pass
    return {
        "model": "farnaz-v0.7-offline",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "tools": used,
        "content": content,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
