import subprocess

from .config import PROJECT_ROOT
from .permission_gate import authorize_operation


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )

    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(output or "Git command failed")

    return output


def git_status() -> str:
    authorize_operation("git_status")
    return _run_git(["status", "--short"])


def git_branch() -> str:
    authorize_operation("git_branch")
    return _run_git(["branch", "--show-current"])


def git_diff() -> str:
    authorize_operation("git_diff")
    return _run_git(["diff"])


def git_add_all() -> str:
    authorize_operation("git_add_all")
    return _run_git(["add", "--all"])


def git_commit(message: str) -> str:
    authorize_operation("git_commit")

    message = message.strip()

    if not message:
        raise ValueError("Commit message cannot be empty")

    if len(message) > 200:
        raise ValueError("Commit message is too long")

    return _run_git(["commit", "-m", message])