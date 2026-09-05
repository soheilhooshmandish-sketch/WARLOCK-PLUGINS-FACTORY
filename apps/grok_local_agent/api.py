import os
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import (
    delete_path,
    list_files,
    make_directory,
    move_path,
    read_file,
    write_file,
)

from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION, PROJECT_ROOT, STATIC_DIR, offline_mode
from .grok_client import GrokClientError, chat as grok_chat


app = FastAPI(title=AGENT_NAME, version=AGENT_VERSION)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        ms = int((time.perf_counter() - started) * 1000)
        print(
            f"GROK {request.method} {request.url.path} "
            f"-> {response.status_code} ({ms}ms)"
        )
        return response


app.add_middleware(RequestLogMiddleware)


class GrokChatRequest(BaseModel):
    message: str
    model: str | None = None


class PathRequest(BaseModel):
    path: str = "."


class WriteFileRequest(BaseModel):
    path: str
    content: str


class MovePathRequest(BaseModel):
    source: str
    destination: str


def require_token(authorization: str | None) -> None:
    expected_token = os.getenv("WARLOCK_GROK_AGENT_TOKEN") or os.getenv(
        "WARLOCK_AGENT_TOKEN"
    )
    if not expected_token:
        raise HTTPException(status_code=500, detail="Agent token is not configured")
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _file_http_error(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail="Path not allowed") from exc
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Path not found") from exc
    if isinstance(exc, NotADirectoryError):
        raise HTTPException(status_code=400, detail="Path is not a directory") from exc
    if isinstance(exc, IsADirectoryError):
        raise HTTPException(status_code=400, detail="Path is a directory") from exc
    raise HTTPException(status_code=500, detail="File operation failed") from exc


@app.get("/")
def ui():
    page = Path(STATIC_DIR) / "index.html"
    return FileResponse(page)


@app.get("/health")
def health():
    key = (os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or "").strip()
    return {
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "status": "healthy",
        "port": AGENT_PORT,
        "original_agent_port": 8765,
        "role": "grok-only",
        "offline": offline_mode(),
        "xai_key_present": bool(key),
        "xai_key_prefix": key[:4] if key else None,
        "xai_key_length": len(key),
    }


@app.get("/workspace")
def workspace(authorization: str | None = Header(default=None)):
    require_token(authorization)
    return {
        "workspace": str(PROJECT_ROOT),
        "exists": PROJECT_ROOT.exists(),
    }


@app.post("/files/list")
def files_list(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        files = list_files(request.path)
        print(f"FILE list path={request.path} count={len(files)}")
        return {"path": request.path, "files": files}
    except Exception as exc:
        print(f"FILE list FAILED path={request.path} err={exc}")
        _file_http_error(exc)


@app.post("/files/read")
def files_read(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        content = read_file(request.path)
        print(f"FILE read path={request.path} bytes={len(content.encode('utf-8'))}")
        return {"path": request.path, "content": content}
    except Exception as exc:
        print(f"FILE read FAILED path={request.path} err={exc}")
        _file_http_error(exc)


@app.post("/files/write")
def files_write(
    request: WriteFileRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        result = write_file(request.path, request.content)
        print(f"FILE write path={request.path} status={result.get('status')}")
        return result
    except Exception as exc:
        print(f"FILE write FAILED path={request.path} err={exc}")
        _file_http_error(exc)


@app.post("/files/mkdir")
def files_mkdir(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        result = make_directory(request.path)
        print(f"FILE mkdir path={request.path}")
        return result
    except Exception as exc:
        print(f"FILE mkdir FAILED path={request.path} err={exc}")
        _file_http_error(exc)


@app.post("/files/move")
def files_move(
    request: MovePathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        result = move_path(request.source, request.destination)
        print(f"FILE move {request.source} -> {request.destination}")
        return result
    except Exception as exc:
        print(f"FILE move FAILED {request.source} -> {request.destination} err={exc}")
        _file_http_error(exc)


@app.post("/files/delete")
def files_delete(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        result = delete_path(request.path)
        print(f"FILE delete path={request.path}")
        return result
    except Exception as exc:
        print(f"FILE delete FAILED path={request.path} err={exc}")
        _file_http_error(exc)


@app.get("/git/status")
def api_git_status(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        output = git_status()
        print("GIT status ok")
        return {"output": output}
    except Exception as exc:
        print(f"GIT status FAILED err={exc}")
        raise HTTPException(status_code=500, detail="Git status failed") from exc


@app.get("/git/branch")
def api_git_branch(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        output = git_branch()
        print("GIT branch ok")
        return {"output": output}
    except Exception as exc:
        print(f"GIT branch FAILED err={exc}")
        raise HTTPException(status_code=500, detail="Git branch failed") from exc


@app.get("/git/diff")
def api_git_diff(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        output = git_diff()
        print("GIT diff ok")
        return {"output": output}
    except Exception as exc:
        print(f"GIT diff FAILED err={exc}")
        raise HTTPException(status_code=500, detail="Git diff failed") from exc


@app.post("/grok/chat")
def grok_chat_route(
    request: GrokChatRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        result = grok_chat(request.message, request.model)
        print(
            f"CHAT mode={result.get('mode')} model={result.get('model')} "
            f"chars={len(result.get('content') or '')}"
        )
        return result
    except ValueError as exc:
        print(f"CHAT ERROR 400: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except GrokClientError as exc:
        print(f"CHAT ERROR 502: {exc}")
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        print(f"CHAT ERROR 500: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Grok request failed")
