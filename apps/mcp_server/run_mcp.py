from .server import mcp


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8790,
        path="/mcp",
        stateless=True,
        json_response=True,
    )
