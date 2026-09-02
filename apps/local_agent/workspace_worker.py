from pathlib import Path

from .permission_gate import authorize_operation, authorize_path


def list_files(relative_path: str = ".") -> list[str]:
    authorize_operation("list_files")
    target = authorize_path(relative_path)

    if not target.exists():
        raise FileNotFoundError(relative_path)

    if not target.is_dir():
        raise NotADirectoryError(relative_path)

    return sorted(
        str(path.relative_to(target))
        for path in target.iterdir()
    )


def read_file(relative_path: str) -> str:
    authorize_operation("read_file")
    target = authorize_path(relative_path)

    if not target.exists():
        raise FileNotFoundError(relative_path)

    if not target.is_file():
        raise IsADirectoryError(relative_path)

    return target.read_text(
        encoding="utf-8",
        errors="replace",
    )


def write_file(relative_path: str, content: str) -> dict:
    authorize_operation("write_file")
    target = authorize_path(relative_path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return {
        "path": relative_path,
        "bytes": len(content.encode("utf-8")),
        "status": "written",
    }