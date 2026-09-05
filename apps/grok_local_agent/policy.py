"""Safety layer. Original ChatGPT agent is never a write target."""

from .config import PROTECTED_PATHS

FORBIDDEN_TOOLS = {"git_add_all", "git_commit", "delete_path", "write_original"}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_locked(path: str) -> bool:
    p = normalize_path(path)
    return any(p == g or p.startswith(g + "/") for g in PROTECTED_PATHS)


def allow_tool(name: str) -> bool:
    return name not in FORBIDDEN_TOOLS


def guard_path(path: str) -> str | None:
    if is_locked(path):
        return f"POLICY DENY: {path} is the original ChatGPT agent"
    return None
