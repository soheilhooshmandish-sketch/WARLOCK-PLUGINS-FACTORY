import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .audit import write_audit
from .command_gateway import run_allowed
from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT
from .git_worker import (
    git_add_all,
    git_branch,
    git_commit,
    git_diff,
    git_status,
)
from .workspace_worker import (
    delete_path,
    list_files,
    make_directory,
    move_path,
    read_file,
    write_file,
)


app = FastAPI(
    title=AGENT_NAME,
    version=AGENT_VERSION,
)


class CommandRequest(BaseModel):
    command: str


class PathRequest(BaseModel):
    path: str = "."


class WriteFileRequest(BaseModel):
    path: str
    content: str


class MovePathRequest(BaseModel):
    source: str
    destination: str


class GitCommitRequest(BaseModel):
    message: str


def require_token(authorization: str | None) -> None:
    expected_token = os.getenv("WARLOCK_AGENT_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="Agent token is not configured",
        )

    if authorization != f"Bearer {expected_token}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )


@app.get("/health")
def health():
    return {
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "status": "healthy",
    }


@app.get("/workspace")
def workspace(authorization: str | None = Header(default=None)):
    require_token(authorization)

    return {
        "workspace": str(PROJECT_ROOT),
        "exists": PROJECT_ROOT.exists(),
    }


@app.post("/command")
def command(
    request: CommandRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit(
        "command_request",
        "received",
        {"command": request.command},
    )

    try:
        output = run_allowed(request.command)
    except PermissionError:
        write_audit(
            "command_request",
            "denied",
            {"command": request.command},
        )
        raise HTTPException(
            status_code=403,
            detail="Command not allowed",
        )
    except Exception:
        write_audit(
            "command_request",
            "failed",
            {"command": request.command},
        )
        raise HTTPException(
            status_code=500,
            detail="Command execution failed",
        )

    write_audit(
        "command_request",
        "success",
        {"command": request.command},
    )

    return {
        "command": request.command,
        "output": output,
    }


@app.post("/files/list")
def files_list(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    try:
        files = list_files(request.path)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Path not found")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail="Path is not a directory")

    return {
        "path": request.path,
        "files": files,
    }


@app.post("/files/read")
def files_read(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit(
        "file_read",
        "received",
        {"path": request.path},
    )

    try:
        content = read_file(request.path)
    except PermissionError:
        write_audit("file_read", "denied", {"path": request.path})
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except IsADirectoryError:
        raise HTTPException(status_code=400, detail="Path is a directory")

    write_audit(
        "file_read",
        "success",
        {"path": request.path},
    )

    return {
        "path": request.path,
        "content": content,
    }


@app.post("/files/write")
def files_write(
    request: WriteFileRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit(
        "file_write",
        "received",
        {"path": request.path},
    )

    try:
        result = write_file(
            request.path,
            request.content,
        )
    except PermissionError:
        write_audit("file_write", "denied", {"path": request.path})
        raise HTTPException(status_code=403, detail="Path not allowed")

    write_audit(
        "file_write",
        "success",
        {"path": request.path},
    )

    return result


@app.post("/files/mkdir")
def files_mkdir(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("mkdir", "received", {"path": request.path})

    try:
        result = make_directory(request.path)
    except PermissionError:
        write_audit("mkdir", "denied", {"path": request.path})
        raise HTTPException(status_code=403, detail="Path not allowed")

    write_audit("mkdir", "success", {"path": request.path})
    return result


@app.post("/files/move")
def files_move(
    request: MovePathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    details = {
        "source": request.source,
        "destination": request.destination,
    }

    write_audit("move", "received", details)

    try:
        result = move_path(
            request.source,
            request.destination,
        )
    except PermissionError:
        write_audit("move", "denied", details)
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        write_audit("move", "failed", details)
        raise HTTPException(status_code=404, detail="Source not found")

    write_audit("move", "success", details)
    return result


@app.post("/files/delete")
def files_delete(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("delete", "received", {"path": request.path})

    try:
        result = delete_path(request.path)
    except PermissionError:
        write_audit("delete", "denied", {"path": request.path})
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        write_audit("delete", "failed", {"path": request.path})
        raise HTTPException(status_code=404, detail="Path not found")

    write_audit("delete", "success", {"path": request.path})
    return result


@app.get("/git/status")
def api_git_status(
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("git_status", "received")

    try:
        output = git_status()
    except Exception:
        write_audit("git_status", "failed")
        raise HTTPException(
            status_code=500,
            detail="Git status failed",
        )

    write_audit("git_status", "success")
    return {"output": output}


@app.get("/git/branch")
def api_git_branch(
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("git_branch", "received")

    try:
        output = git_branch()
    except Exception:
        write_audit("git_branch", "failed")
        raise HTTPException(
            status_code=500,
            detail="Git branch failed",
        )

    write_audit("git_branch", "success")
    return {"output": output}


@app.get("/git/diff")
def api_git_diff(
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("git_diff", "received")

    try:
        output = git_diff()
    except Exception:
        write_audit("git_diff", "failed")
        raise HTTPException(
            status_code=500,
            detail="Git diff failed",
        )

    write_audit("git_diff", "success")
    return {"output": output}


@app.post("/git/add")
def api_git_add(
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    write_audit("git_add_all", "received")

    try:
        output = git_add_all()
    except Exception:
        write_audit("git_add_all", "failed")
        raise HTTPException(
            status_code=500,
            detail="Git add failed",
        )

    write_audit("git_add_all", "success")
    return {"output": output}


@app.post("/git/commit")
def api_git_commit(
    request: GitCommitRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)

    details = {"message": request.message}
    write_audit("git_commit", "received", details)

    try:
        output = git_commit(request.message)
    except ValueError as exc:
        write_audit("git_commit", "denied", details)
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except Exception:
        write_audit("git_commit", "failed", details)
        raise HTTPException(
            status_code=500,
            detail="Git commit failed",
        )

    write_audit("git_commit", "success", details)
    return {"output": output}
