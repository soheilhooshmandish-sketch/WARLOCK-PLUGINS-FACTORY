import os

import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .gateway import create_gateway


app = FastAPI(
    title="Warlock Secure Gateway",
    version="0.2.0",
)


class CommitRequest(BaseModel):
    message: str


def require_cloudflare_access(
    cf_access_jwt_assertion: str | None,
) -> None:
    team_domain = os.getenv("WARLOCK_CF_TEAM_DOMAIN")
    audience = os.getenv("WARLOCK_CF_ACCESS_AUD")

    if not team_domain or not audience:
        raise HTTPException(
            status_code=500,
            detail="Cloudflare Access is not configured",
        )

    if not cf_access_jwt_assertion:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    issuer = f"https://{team_domain}"
    certs_url = f"{issuer}/cdn-cgi/access/certs"

    try:
        jwks_client = PyJWKClient(certs_url)
        signing_key = jwks_client.get_signing_key_from_jwt(
            cf_access_jwt_assertion
        )

        jwt.decode(
            cf_access_jwt_assertion,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )


@app.get("/health")
def health():
    return {
        "gateway": "warlock",
        "status": "healthy",
    }


@app.get("/agent/health")
def agent_health(
    cf_access_jwt_assertion: str | None = Header(
        default=None,
        alias="Cf-Access-Jwt-Assertion",
    ),
):
    require_cloudflare_access(cf_access_jwt_assertion)

    try:
        return create_gateway().health()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Local agent unavailable",
        )


@app.get("/git/status")
def git_status(
    cf_access_jwt_assertion: str | None = Header(
        default=None,
        alias="Cf-Access-Jwt-Assertion",
    ),
):
    require_cloudflare_access(cf_access_jwt_assertion)

    try:
        return create_gateway().git_status()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Local agent unavailable",
        )


@app.post("/files/read")
def read_file(
    path: str,
    cf_access_jwt_assertion: str | None = Header(
        default=None,
        alias="Cf-Access-Jwt-Assertion",
    ),
):
    require_cloudflare_access(cf_access_jwt_assertion)

    try:
        return create_gateway().read_file(path)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Local agent unavailable",
        )