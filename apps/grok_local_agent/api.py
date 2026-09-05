import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT
from .grok_client import GrokClientError, chat as grok_chat


app = FastAPI(title=AGENT_NAME, version=AGENT_VERSION)


class GrokChatRequest(BaseModel):
    message: str
    model: str | None = None


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
    return {
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "status": "healthy",
        "port": 8766,
    }


@app.get("/workspace")
def workspace(authorization: str | None = Header(default=None)):
    require_token(authorization)
    return {
        "workspace": str(PROJECT_ROOT),
        "exists": PROJECT_ROOT.exists(),
    }


@app.post("/grok/chat")
def grok_chat_route(
    request: GrokChatRequest,
    authorization: str | None = Header(default=None),
):
    require_token(authorization)
    try:
        return grok_chat(request.message, request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except GrokClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Grok request failed")
