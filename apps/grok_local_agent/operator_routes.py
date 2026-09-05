from fastapi import Header
from pydantic import BaseModel

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


class TypeBody(BaseModel):
    text: str


class LaunchBody(BaseModel):
    app: str


class WorkflowBody(BaseModel):
    steps: list[dict]


def mount(app, require_token):
    @app.get("/operator")
    def operator_status(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return status()

    @app.post("/operator/grant")
    def operator_grant(body: GrantBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return grant(body.capability, body.minutes, body.confirm)

    @app.post("/operator/revoke")
    def operator_revoke(body: RevokeBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return revoke(body.capability)

    @app.post("/operator/see")
    def operator_see(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return see()

    @app.get("/operator/apps")
    def operator_apps(authorization: str | None = Header(default=None)):
        require_token(authorization)
        return apps()

    @app.post("/operator/click")
    def operator_click(body: ClickBody, authorization: str | None = Header(default=None)):
        require_token(authorization)
        return click(body.x, body.y, body.button)

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
