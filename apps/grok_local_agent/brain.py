from datetime import datetime, timezone
import json
import re

from .config import AGENT_NAME, AGENT_VERSION, STATE_DIR
from . import tools as T

HELP = f"""{AGENT_NAME} {AGENT_VERSION}
ایجنت محلی هوشمند. ChatGPT / apps/local_agent قفل است.
دستورها: کمک، کی هستی، خلاصه، فهرست، بخوان، جستجو، پیدا کن متن، یادداشت، یادداشت‌ها، git، ایندکس
"""


def _n(s: str) -> str:
    return " ".join(s.lower().replace("\u200c", " ").split())


def _mem(user: str, reply: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "memory.json"
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({"t": datetime.now(timezone.utc).isoformat(), "u": user[:400], "r": reply[:400]})
    path.write_text(json.dumps(data[-40:], ensure_ascii=False, indent=2), encoding="utf-8")


def _has(key: str, *words: str) -> bool:
    return any(w in key for w in words)


def reply(message: str) -> dict:
    text = message.strip()
    key = _n(text)
    used: list[str] = []
    out: list[str] = []
    path = T.extract_path(text)

    def add(name: str, value: str) -> None:
        used.append(name)
        out.append(value)

    if _has(key, "کمک", "help", "چی بلدی", "چه کار", "چیکار"):
        add("help", HELP)
    if _has(key, "کی هستی", "who are you", "اسمت", "سلامت", "health"):
        add("id", f"من {AGENT_NAME} هستم، نسخه {AGENT_VERSION}. ایجنت محلی. اصلی روی 8765 را تغییر نمی‌دهم.")
    if _has(key, "ایندکس", "index", "ساختار"):
        add("index", T.index_top())
    if _has(key, "خلاصه", "overview", "وضعیت پروژه") and not _has(key, "خلاصه فایل"):
        bits = [T.runtime()]
        try:
            bits.append("branch " + T.git_info("branch"))
        except Exception as exc:
            bits.append(str(exc))
        try:
            bits.append(T.git_info("status"))
        except Exception as exc:
            bits.append(str(exc))
        bits.append(T.list_dir())
        add("overview", "\n".join(bits))
    if _has(key, "یادداشت‌ها", "notes", "یادداشت ها"):
        add("notes", T.note_read())
    elif _has(key, "یادداشت", "note ") and len(text) > 6:
        payload = re.sub(r"^(یادداشت|note)\s*[:\-]?\s*", "", text, flags=re.I)
        add("note", T.note_write(payload))
    if _has(key, "پیدا کن متن", "grep", "در کد"):
        q = re.sub(r"^(پیدا کن متن|grep|search text)\s+", "", text, flags=re.I).strip() or "Farnaz"
        add("grep", T.search_text(q))
    elif _has(key, "جستجو", "find", "search", "پیدا"):
        q = re.sub(r"^(جستجو|find|search|پیدا کن)\s+", "", text, flags=re.I).strip() or "farnaz"
        add("find", T.search_names(q))
    if _has(key, "خلاصه فایل", "summarize"):
        add("sum", T.summarize(path or "apps/grok_local_agent/brain.py"))
    if _has(key, "git status", "وضعیت گیت") or key == "git":
        try:
            add("git", T.git_info("status"))
        except Exception as exc:
            add("git", str(exc))
    if _has(key, "branch", "شاخه"):
        try:
            add("branch", T.git_info("branch"))
        except Exception as exc:
            add("branch", str(exc))
    if "diff" in key:
        try:
            add("diff", T.git_info("diff"))
        except Exception as exc:
            add("diff", str(exc))
    if _has(key, "بخوان", "read ", "cat "):
        add("read", T.read(path or "apps/grok_local_agent/brain.py"))
    if _has(key, "list", "فهرست", "ls", "dir"):
        add("list", T.list_dir(path or "apps/grok_local_agent"))
    if _has(key, "workspace", "پروژه"):
        add("ws", T.runtime())

    if not out:
        if path and not T.protected(path):
            target = T.PROJECT_ROOT / path
            if target.exists():
                add("auto", T.list_dir(path) if target.is_dir() else T.summarize(path))
        if not out:
            add("reason", HELP + "\n\n" + T.search_names(key.split()[0] if key else "farnaz"))

    content = "\n\n".join(out)
    try:
        _mem(text, content)
    except Exception:
        pass
    return {
        "model": "farnaz-v0.8-offline",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "tools": used,
        "content": content,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
