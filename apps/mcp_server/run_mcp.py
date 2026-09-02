import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "apps.mcp_server.server:app",
        host="127.0.0.1",
        port=8790,
        log_level="info",
    )
