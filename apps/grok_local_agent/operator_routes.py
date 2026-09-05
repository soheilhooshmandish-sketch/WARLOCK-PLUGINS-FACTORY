from fastapi import Header
from pydantic import BaseModel

from .builder import build, suggest_fix
from .jobs import create as job_create, current as job_current, update as job_update
from .killswitch import halt, halted, resume
from .levels import describe as levels_describe, grant_level
from .operator import (
    apps,
    click,
    grant,
    launch,
    revoke,
    see,
    status,
    type_text,
    workflow,
)
from .plugin_val import inspect as plugin_inspect
from .smart_ui import click_named
from .tone import export_juce, propose
from .vision import scene


class GrantBody(BaseModel):
    capability: str
    minutes: int = 30
    confirm: bool = False


class RevokeBody(BaseModel):
    capability: str | None = None


class ClickBody(BaseModel):
    x: int
    y: int
    button: str = "left"


class NamedClickBody(BaseModel):
    name: str


class TypeBody(BaseModel):
    text: str


class LaunchBody(BaseModel):
    app: str


class WorkflowBody(BaseModel):
    steps: list[dict]


class LevelBody(BaseModel):
    level: str
    minutes: int = 30
    confirm: bool = False


class ToneBody(BaseModel):
    wav: str | None = None
    family: str = "THALL"


class JobBody(BaseModel):
    title: str = "Thall"
    notes: str = ""
    id: str | None = None
    stage: str | None = None


def mount(app, require_token):
    @app.get("/operator")
    def operator_status(authorization: str | None = Header(default=None)):
        require_token(authorization)
        st = status()
        st["halted"] = halted()
        st["levels"] = levels_describe()["levels"]
        st["job"] = (job_current().get("jobs") or [None])[0]
        return st

    @app.post("/operator/grant")
    def operator_grant(body: GrantBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return grant(body.capability, body.minutes, body.confirm)

    @app.post("/operator/level")
    def operator_level(body: LevelBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return grant_level(body.level, body.minutes, body.confirm)

    @app.post("/operator/revoke")
    def operator_revoke(body: RevokeBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return revoke(body.capability)

    @app.post("/operator/stop")
    def operator_stop(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return halt("api")

    @app.post("/operator/resume")
    def operator_resume(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return resume()

    @app.post("/operator/see")
    def operator_see(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return see()

    @app.get("/operator/vision")
    def operator_vision(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return scene()

    @app.get("/operator/apps")
    def operator_apps(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return apps()

    @app.post("/operator/click")
    def operator_click(body: ClickBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return click(body.x, body.y, body.button)

    @app.post("/operator/click_named")
    def operator_click_named(body: NamedClickBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return click_named(body.name)

    @app.post("/operator/type")
    def operator_type(body: TypeBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return type_text(body.text)

    @app.post("/operator/launch")
    def operator_launch(body: LaunchBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return launch(body.app)

    @app.post("/operator/workflow")
    def operator_workflow(body: WorkflowBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return workflow(body.steps)

    @app.post("/operator/tone")
    def operator_tone(body: ToneBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        prop = propose(body.wav, body.family)
        if prop.get("ok"):
            prop["export"] = export_juce(prop)
        return prop

    @app.post("/operator/build")
    def operator_build(authorization: str | None = Header(default=None)):
        require_token(authorization)
        result = build()
        issues = (result.get("build") or {}).get("issues") or []
        result["suggestions"] = suggest_fix(issues)
        return result

    @app.get("/operator/plugins")
    def operator_plugins(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return plugin_inspect()

    @app.get("/operator/jobs")
    def operator_jobs(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return job_current()

    @app.post("/operator/jobs")
    def operator_jobs_set(body: JobBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        if body.id:
            return job_update(body.id, body.stage, body.notes or None)
        return job_create(body.title, body.notes)
