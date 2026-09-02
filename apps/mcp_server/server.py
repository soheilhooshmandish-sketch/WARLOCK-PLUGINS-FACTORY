import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


AGENT_URL = os.getenv("WARLOCK_AGENT_URL", "http://127.0.0.1:8765").rstrip("/")

mcp = FastMCP(
    "Warlock Plugins Factory",
    instructions=(
        "Operate only inside the Warlock Plugins Factory workspace. "
        "All writes and Git mutations are still enforced by the local "
        "agent Permission Gate and audit log. Never use these tools as "
        "a substitute for unrestricted shell access."
    ),
    host="127.0.0.1",
    port=8790,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def _token() -> str:
    token = os.getenv("WARLOCK_AGENT_TOKEN")
    if not token:
        raise RuntimeError("WARLOCK_AGENT_TOKEN is not configured")
    return token


def _request(method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
    response = httpx.request(
        method,
        f"{AGENT_URL}{path}",
        headers={"Authorization": f"Bearer {_token()}"},
        json=json,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def health() -> dict[str, Any]:
    """Check whether the Warlock Local Agent is healthy."""
    response = httpx.get(f"{AGENT_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def workspace() -> dict[str, Any]:
    """Return the confined project workspace reported by the local agent."""
    return _request("GET", "/workspace")


@mcp.tool()
def list_files(path: str = ".") -> dict[str, Any]:
    """List files inside an allowed project-relative directory."""
    return _request("POST", "/files/list", {"path": path})


@mcp.tool()
def read_file(path: str) -> dict[str, Any]:
    """Read one allowed project-relative text file."""
    return _request("POST", "/files/read", {"path": path})


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, Any]:
    """Create or replace an allowed project-relative text file."""
    return _request("POST", "/files/write", {"path": path, "content": content})


@mcp.tool()
def make_directory(path: str) -> dict[str, Any]:
    """Create an allowed project-relative directory."""
    return _request("POST", "/files/mkdir", {"path": path})


@mcp.tool()
def move_path(source: str, destination: str) -> dict[str, Any]:
    """Move or rename an allowed project-relative path."""
    return _request("POST", "/files/move", {"source": source, "destination": destination})


@mcp.tool()
def delete_path(path: str) -> dict[str, Any]:
    """Delete an allowed project-relative path. Protected paths remain blocked."""
    return _request("POST", "/files/delete", {"path": path})


@mcp.tool()
def git_status() -> dict[str, Any]:
    """Show Git working-tree status for the project."""
    return _request("GET", "/git/status")


@mcp.tool()
def git_branch() -> dict[str, Any]:
    """Show the current Git branch."""
    return _request("GET", "/git/branch")


@mcp.tool()
def git_diff() -> dict[str, Any]:
    """Show the current Git diff."""
    return _request("GET", "/git/diff")


@mcp.tool()
def git_add_all() -> dict[str, Any]:
    """Stage allowed project changes using the local agent Git worker."""
    return _request("POST", "/git/add")


@mcp.tool()
def git_commit(message: str) -> dict[str, Any]:
    """Commit staged changes with a non-empty commit message."""
    return _request("POST", "/git/commit", {"message": message})


# Stable ASGI entrypoint for uvicorn and the Windows Supervisor.
app = mcp.streamable_http_app()
