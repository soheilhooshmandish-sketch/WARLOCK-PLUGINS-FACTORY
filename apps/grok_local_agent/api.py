import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from apps.local_agent.git_worker import git_branch, git_diff, git_status
from apps.local_agent.workspace_worker import list_files, read_file

from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION, PROJECT_ROOT
from .grok_client import GrokClientError, chat as grok_chat


app = FastAPI(title=AGENT_NAME, version=AGENT_VERSION)


class GrokChatRequest(BaseModel):
    message: str
    model: str | None = None


class PathRequest(BaseModel):
    path: str = "."


def require_token(authorization: str | None) -> None:
    expected_token = os.getenv("WARLOCK_GROK_AGENT_TOKEN") or os.getenv(
        "WARLOCK_AGENT_TOKEN"
    )
    if not expected_token:
        raise HTTPException(status_code=500, detail="Agent token is not configured")
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


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
        return {"path": request.path, "files": list_files(request.path)}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Path not found")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail="Path is not a directory")


@app.post("/files/read")
def files_read(
    request: PathRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        return {"path": request.path, "content": read_file(request.path)}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Path not allowed")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except IsADirectoryError:
        raise HTTPException(status_code=400, detail="Path is a directory")


@app.get("/git/status")
def api_git_status(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        return {"output": git_status()}
    except Exception:
        raise HTTPException(status_code=500, detail="Git status failed")


@app.get("/git/branch")
def api_git_branch(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        return {"output": git_branch()}
    except Exception:
        raise HTTPException(status_code=500, detail="Git branch failed")


@app.get("/git/diff")
def api_git_diff(authorization: str | None = Header(default=None)):
    require_token(authorization)
    try:
        return {"output": git_diff()}
    except Exception:
        raise HTTPException(status_code=500, detail="Git diff failed")


@app.post("/grok/chat")
def grok_chat_route(
    request: GrokChatRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        return grok_chat(request.message, request.model)
    except ValueError as exc:
        print(f"GROK_CHAT_ERROR 400: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except GrokClientError as exc:
        print(f"GROK_CHAT_ERROR 502: {exc}")
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        print(f"GROK_CHAT_ERROR 500: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Grok request failed")
