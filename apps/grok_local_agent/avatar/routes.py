"""HTTP surface for the desktop panel. Does not implement intelligence."""
from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import speech_input
from .avatar_engine import identity, set_portrait
from .avatar_state import State, get_state, set_hidden, set_muted, set_state
from .settings import load as load_settings, save as save_settings
from .voice_engine import VoiceEngine

STATIC = Path(__file__).resolve().parent.parent / "static"
VOICE = VoiceEngine()


class SpeakBody(BaseModel):
    text: str
    lang: str | None = None


class StateBody(BaseModel):
    state: str
    detail: str = ""


class ConfigBody(BaseModel):
    volume: float | None = None
    muted: bool | None = None
    hidden: bool | None = None
    lang: str | None = None
    x: int | None = None
    y: int | None = None
    minimized: bool | None = None
    portrait_path: str | None = None
    allow_browser_stt: bool | None = None


class PttBody(BaseModel):
    backend: str = "client"


def mount(app, require_token):
    @app.get("/avatar/face.svg")
    def face_svg():
        return FileResponse(STATIC / "face.svg", media_type="image/svg+xml")

    @app.get("/avatar/desktop.css")
    def desktop_css():
        return FileResponse(STATIC / "desktop.css", media_type="text/css")

    @app.get("/avatar/desktop.js")
    def desktop_js():
        return FileResponse(STATIC / "desktop.js", media_type="text/javascript")

    @app.get("/avatar/state")
    def avatar_state(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return {**get_state(), **identity(), "mic": speech_input.status()}

    @app.post("/avatar/state")
    def avatar_set_state(body: StateBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        try:
            return set_state(body.state, body.detail)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/avatar/speak")
    def avatar_speak(body: SpeakBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        set_state(State.SPEAKING, body.text[:80])
        result = VOICE.speak(body.text, body.lang)
        if get_state().get("muted") or result.get("backend") == "muted":
            set_state(State.IDLE)
        return result

    @app.post("/avatar/stop")
    def avatar_stop(authorization: str | None = Header(default=None)):
        require_token(authorization)
        VOICE.interrupt()
        speech_input.stop_ptt()
        return set_state(State.IDLE, "stopped")

    @app.post("/avatar/ptt/start")
    def ptt_start(body: PttBody | None = None, authorization: str | None = Header(default=None)):
        require_token(authorization)
        backend = body.backend if body else "client"
        return speech_input.start_ptt(backend)

    @app.post("/avatar/ptt/stop")
    def ptt_stop(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return speech_input.stop_ptt()

    @app.get("/avatar/config")
    def avatar_config(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return {**load_settings(), "identity": identity(), "tts_backends": VOICE.list_backends()}

    @app.post("/avatar/config")
    def avatar_config_set(body: ConfigBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        patch = body.model_dump(exclude_none=True)
        if "portrait_path" in patch:
            try:
                set_portrait(patch["portrait_path"] or None)
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            patch.pop("portrait_path", None)
        saved = save_settings(patch)
        if "hidden" in patch:
            set_hidden(bool(patch["hidden"]))
        if "muted" in patch:
            set_muted(bool(patch["muted"]))
        return saved
