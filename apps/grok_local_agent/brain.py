from datetime import datetime, timezone
from pathlib import Path
import re
import sys

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT, PROTECTED_PATHS

HELP = """من فرناز هستم، ایجنت محلی هوشمند روی پورت 8766.
ایجنت اصلی ChatGPT روی 8765 را تغییر نمی‌دهم و apps/local_agent قفل است.

می‌توانید بپرسید:
- کی هستی / سلامت
- پروژه / workspace
- فهرست apps/grok_local_agent
- بخوان apps/grok_local_agent/brain.py
- git status / branch / diff
- خلاصه / overview
- کمک
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


def _safe_list(path: str) -> str:
    if _is_protected(path):
        return f"قفل: {path} (ایجنت اصلی)"
    try:
        files = list_files(path)
        return f"{path} ({len(files)} items)\n" + "\n".join(files[:100])
    except Exception as exc:
        return f"list failed: {exc}"


def _safe_read(path: str) -> str:
    if _is_protected(path):
        return f"قفل: {path} (ایجنت اصلی)"
    try:
        content = read_file(path)
        if len(content) > 4000:
            return content[:4000] + "\n…truncated"
        return content
    except Exception as exc:
        return f"read failed: {exc}"


def _overview() -> str:
    parts = [
        f"{AGENT_NAME} {AGENT_VERSION}  port 8766  workspace={PROJECT_ROOT}",
        f"python {sys.version.split()[0]}",
    ]
    try:
        parts.append("branch: " + git_branch())
    except Exception as exc:
        parts.append(f"branch: {exc}")
    try:
        status = git_status() or "clean"
        parts.append("git:\n" + status)
    except Exception as exc:
        parts.append(f"git: {exc}")
    parts.append(_safe_list("apps/grok_local_agent"))
    return "\n\n".join(parts)


def reply(message: str) -> dict:
    text = message.strip()
    key = _norm(text)
    used: list[str] = []
    chunks: list[str] = []

    if any(w in key for w in ("help", "کمک", "دستور")):
        used.append("help")
        chunks.append(HELP)
    if any(w in key for w in ("کی هستی", "who are you", "اسم", "سلامت", "health")):
        used.append("identity")
        chunks.append(
            f"من {AGENT_NAME} هستم. نسخه {AGENT_VERSION}. ایجنت گروک محلی. "
            "ChatGPT روی 8765 را لمس نمی‌کنم."
        )
    if any(w in key for w in ("overview", "خلاصه", "وضعیت پروژه", "super", "smart")):
        used.append("overview")
        chunks.append(_overview())
    if any(w in key for w in ("workspace", "پروژه", "کجا")):
        used.append("workspace")
        chunks.append(str(PROJECT_ROOT))
    if any(w in key for w in ("git status", "وضعیت گیت")) or key == "git":
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
    if any(w in key for w in ("list", "فهرست", "ls", "dir", "فایل")):
        path = _extract_path(text) or "apps/grok_local_agent"
        used.append("list_files")
        chunks.append(_safe_list(path))

    if not chunks:
        used.append("plan")
        path = _extract_path(text)
        if path and Path(PROJECT_ROOT, path).exists() and not _is_protected(path):
            used.append("auto-inspect")
            target = Path(PROJECT_ROOT, path)
            if target.is_dir():
                chunks.append(_safe_list(path))
            else:
                chunks.append(_safe_read(path))
        else:
            chunks.append(
                f"{AGENT_NAME}: درخواست را فهمیدم ولی ابزار دقیق مشخص نشد.\n"
                f"متن: {text}\n\n{HELP}"
            )

    return {
        "model": "farnaz-super-offline",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "tools": used,
        "content": "\n\n".join(chunks),
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
