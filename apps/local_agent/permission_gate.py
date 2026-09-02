from pathlib import Path

from .config import PROJECT_ROOT


ALLOWED_OPERATIONS = {
    "read_file",
    "write_file",
    "list_files",
    "git_status",
    "git_branch",
    "python_version",
}


def resolve_project_path(relative_path: str) -> Path:
    candidate = (PROJECT_ROOT / relative_path).resolve()
    project_root = PROJECT_ROOT.resolve()

    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise PermissionError("Path is outside the project workspace") from exc

    return candidate


def authorize_operation(operation: str) -> None:
    if operation not in ALLOWED_OPERATIONS:
        raise PermissionError(f"Operation not allowed: {operation}")


def authorize_path(relative_path: str) -> Path:
    return resolve_project_path(relative_path)