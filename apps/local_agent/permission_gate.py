from pathlib import Path

from .config import PROJECT_ROOT


ALLOWED_OPERATIONS = {
    "read_file",
    "write_file",
    "list_files",
    "make_directory",
    "move_path",
    "delete_path",
    "git_status",
    "git_branch",
    "git_diff",
    "git_add_all",
    "git_commit",
    "python_version",
}


PROTECTED_PATHS = {
    ".git",
    ".venv",
    ".warlock",
}


def resolve_project_path(relative_path: str) -> Path:
    candidate = (PROJECT_ROOT / relative_path).resolve()
    project_root = PROJECT_ROOT.resolve()

    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise PermissionError(
            "Path is outside the project workspace"
        ) from exc

    return candidate


def authorize_operation(operation: str) -> None:
    if operation not in ALLOWED_OPERATIONS:
        raise PermissionError(
            f"Operation not allowed: {operation}"
        )


def authorize_path(
    relative_path: str,
    *,
    allow_protected: bool = False,
) -> Path:
    target = resolve_project_path(relative_path)

    if allow_protected:
        return target

    project_root = PROJECT_ROOT.resolve()
    relative = target.relative_to(project_root)

    if not relative.parts:
        raise PermissionError(
            "Project root is protected"
        )

    if relative.parts[0] in PROTECTED_PATHS:
        raise PermissionError(
            f"Protected path: {relative.parts[0]}"
        )

    return target