from datetime import datetime, timezone

from apps.local_agent.git_worker import git_branch, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT, PROTECTED_PATHS


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _is_protected(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    return any(p == g or p.startswith(g + "/") for g in PROTECTED_PATHS)


def reply(message: str) -> dict:
    text = message.strip()
    key = _norm(text)
    used = []
    body = ""

    if any(w in key for w in ("health", "سلامت", "کی هستی", "who are you", "اسم")):
        used.append("identity")
        body = (
            f"من {AGENT_NAME} هستم، ایجنت محلی Warlock روی پورت 8766، نسخه {AGENT_VERSION}. "
            "ایجنت اصلی ChatGPT روی 8765 را تغییر نمی‌دهم."
        )
    elif any(w in key for w in ("git status", "وضعیت گیت", "git")):
        used.append("git_status")
        body = git_status()
    elif any(w in key for w in ("branch", "شاخه")):
        used.append("git_branch")
        body = git_branch()
    elif key.startswith("read ") or key.startswith("بخوان ") or "read file" in key:
        path = text.split(maxsplit=1)[-1].replace("بخوان", "").strip()
        if _is_protected(path):
            body = "این مسیر قفل است (ایجنت اصلی ChatGPT)."
        else:
            used.append("read_file")
            body = read_file(path)
    elif any(w in key for w in ("list", "فهرست", "فایل", "ls", "dir")):
        path = "apps/grok_local_agent"
        parts = text.split()
        for part in parts:
            if "/" in part or part.endswith(".py"):
                path = part
                break
        if _is_protected(path):
            body = "این مسیر قفل است (ایجنت اصلی ChatGPT)."
        else:
            used.append("list_files")
            files = list_files(path)
            body = f"{path}\n" + "\n".join(files[:80])
    elif any(w in key for w in ("workspace", "پروژه", "کجا")):
        used.append("workspace")
        body = str(PROJECT_ROOT)
    else:
        used.append("reason")
        body = (
            f"{AGENT_NAME}: پیام را فهمیدم. در حالت آفلاین می‌توانم سلامت، فهرست فایل، خواندن فایل، "
            f"git status و branch را انجام بدهم. مسیر apps/local_agent قفل است.\n"
            f"درخواست شما: {text}"
        )

    return {
        "model": "farnaz-offline-brain",
        "mode": "offline",
        "agent": AGENT_NAME,
        "tools": used,
        "content": body,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
