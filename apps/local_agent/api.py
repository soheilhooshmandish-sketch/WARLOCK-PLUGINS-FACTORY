import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT
from .command_gateway import run_allowed


app = FastAPI(
    title=AGENT_NAME,
    version=AGENT_VERSION,
)


class CommandRequest(BaseModel):
    command: str


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

    try:
        output = run_allowed(request.command)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Command not allowed",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Command execution failed",
        )

    return {
        "command": request.command,
        "output": output,
    }