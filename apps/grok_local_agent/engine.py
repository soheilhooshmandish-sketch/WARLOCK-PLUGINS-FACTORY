from pathlib import Path
import re

from . import inspect_self as S
from . import stats as ST
from . import tools as T
from .ast_summary import summarize_python
from .autogen_team import run_autogen
from .brain import answer as brain_answer
from .config import MAX_REASON_STEPS, PROJECT_ROOT, SKIP_DIRS
from .knowledge import FACTS
from .orchestrator import conductor
from .peers import fleet
from .recall import last as recall_last
from .selector import run_selector
from .selfmap import api_routes
from .sources import list_sources


def _has(key: str, *words: str) -> bool:
    return any(w in key for w in words)


def count_py() -> str:
    n = 0
    for p in PROJECT_ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if T.protected(rel):
            continue
        n += 1
    return f"python files (unlocked): {n}"


def recent() -> str:
    files = []
    for p in PROJECT_ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if T.protected(rel):
            continue
        files.append((p.stat().st_mtime, rel))
    files.sort(reverse=True)
    return "recent:\n" + "\n".join(rel for _, rel in files[:12])


def todos() -> str:
    return T.search_text("TODO") + "\n" + T.search_text("FIXME")


def plan(text: str) -> list[tuple[str, callable]]:
    key = " ".join(text.lower().replace("\u200c", " ").split())
    path = T.extract_path(text)
    steps: list[tuple[str, callable]] = []

    def add(name, fn):
        if name not in {n for n, _ in steps}:
            steps.append((name, fn))

    if _has(key, "کمک", "help", "چی بلدی", "چه کار", "چیکار"):
        add("help", lambda: FACTS)
    brain_keys = (
        "interrupt", "checkpointer", "reducer", "add_messages", "selector",
        "candidate", "hitl", "crewai", "langgraph", "autogen", "oversight",
        "pele", "xai", "grok-4", "mcp", "tool", "function", "fastapi", "uvicorn",
        "توضیح", "explain", "چیست", "یعنی", "how does", "what is", "versioning",
        "messagesstate", "command", "resume",
    )
    if _has(key, *brain_keys):
        add("brain", lambda: brain_answer(text))
    if _has(key, "منبع", "منابع", "source", "sources", "citation", "docs"):
        topic = None
        for t in ("autogen", "crewai", "langgraph", "xai", "oversight", "mcp", "tools", "fastapi"):
            if t in key:
                topic = t
                break
        add("sources", lambda: list_sources(topic))
    if _has(key, "autogen", "roundrobin", "groupchat") and "selector" not in key and "explain" not in key and "توضیح" not in key:
        add("autogen", lambda: run_autogen(text))
    if _has(key, "selector", "انتخابگر", "@scout", "@analyst", "@reviewer", "@fleet") and "explain" not in key:
        strategy = "mention" if "@" in text else ("roundrobin" if "round" in key else "keyword")
        add("selector", lambda: run_selector(text, strategy))
    if _has(key, "ارکستر", "orchestrat", "fleet", "چند ایجنت", "multi-agent", "agents"):
        add("orchestrate", lambda: conductor(text))
    if _has(key, "ناوگان", "peer", "8765", "8766"):
        add("fleet", fleet)
    if _has(key, "کی هستی", "who are you", "اسمت", "سلامت", "health"):
        add("id", lambda: FACTS)
        add("syntax", S.syntax)
        add("lock", ST.lock_ok)
    if _has(key, "ماژول", "module", "inventory", "خودت"):
        add("inventory", S.inventory)
        add("syntax", S.syntax)
        add("imports", S.imports)
    if _has(key, "syntax", "خطا"):
        add("syntax", S.syntax)
    if _has(key, "مسیرها", "routes", "endpoint"):
        add("routes", api_routes)
    if _has(key, "ایندکس", "index", "ساختار"):
        add("index", T.index_top)
        add("types", ST.file_types)
    if _has(key, "آمار", "stats", "types"):
        add("types", ST.file_types)
        add("count", count_py)
    if _has(key, "قفل", "lock", "chatgpt"):
        add("lock", ST.lock_ok)
    if _has(key, "یادآوری", "recall", "قبلی"):
        add("recall", lambda: recall_last(5))
    if _has(key, "خلاصه", "overview", "وضعیت") and not _has(key, "خلاصه فایل"):
        add("runtime", T.runtime)
        add("list-self", lambda: T.list_dir("apps/grok_local_agent"))
        add("count", count_py)
        add("syntax", S.syntax)
        add("lock", ST.lock_ok)
    if _has(key, "یادداشت‌ها", "notes"):
        add("notes", T.note_read)
    elif _has(key, "یادداشت", "note ") and len(text) > 6:
        payload = re.sub(r"^(یادداشت|note)\s*[:\-]?\s*", "", text, flags=re.I)
        add("note", lambda p=payload: T.note_write(p))
    if _has(key, "پیدا کن متن", "grep", "در کد"):
        q = re.sub(r"^(پیدا کن متن|grep|search text)\s+", "", text, flags=re.I).strip() or "Farnaz"
        add("grep", lambda q=q: T.search_text(q))
    elif _has(key, "جستجو", "find", "search", "پیدا"):
        q = re.sub(r"^(جستجو|find|search|پیدا کن)\s+", "", text, flags=re.I).strip() or "farnaz"
        add("find", lambda q=q: T.search_names(q))
    if _has(key, "خلاصه فایل", "summarize", "ast"):
        target = path or "apps/grok_local_agent/engine.py"
        add("ast", lambda t=target: summarize_python(t) if t.endswith(".py") else T.summarize(t))
    if _has(key, "git", "وضعیت گیت", "branch", "شاخه", "diff"):
        if _has(key, "branch", "شاخه"):
            add("branch", lambda: T.git_info("branch"))
        elif "diff" in key:
            add("diff", lambda: T.git_info("diff"))
        else:
            add("git", lambda: T.git_info("status"))
    if _has(key, "بخوان", "read ", "cat "):
        add("read", lambda: T.read(path or "apps/grok_local_agent/engine.py"))
    if _has(key, "list", "فهرست", "ls", "dir"):
        add("list", lambda: T.list_dir(path or "apps/grok_local_agent"))
    if _has(key, "todo", "کار باز"):
        add("todo", todos)
    if _has(key, "recent", "اخیر"):
        add("recent", recent)
    if _has(key, "workspace", "پروژه"):
        add("ws", T.runtime)

    if not steps:
        add("brain", lambda: brain_answer(text))
        add("facts", lambda: FACTS)
        add("lock", ST.lock_ok)
        add("syntax", S.syntax)
        add("inventory", S.inventory)
        add("index", T.index_top)
        add("recall", lambda: recall_last(3))
        words = [w for w in key.split() if len(w) > 3][:3]
        if words:
            add("find", lambda: T.search_names(words[0]))
            add("grep", lambda: T.search_text(words[0]))
        if path and not T.protected(path):
            target = PROJECT_ROOT / path
            if target.exists():
                add("inspect", lambda: T.list_dir(path) if target.is_dir() else (
                    summarize_python(path) if path.endswith(".py") else T.read(path)
                ))
    return steps[:MAX_REASON_STEPS]


def run(text: str) -> tuple[list[str], list[str]]:
    used = []
    chunks = []
    for name, fn in plan(text):
        try:
            chunks.append(str(fn()))
            used.append(name)
        except Exception as exc:
            used.append(name + "!")
            chunks.append(f"{name}: {exc}")
    return used, chunks
