"""Ravimus MCP — single-endpoint server.

Auto-discovers every flat .py in tools/ (each registers on the shared `mcp`
instance via `from mcp_app import mcp`) and serves them all at /mcp.
"""
import os
import sys
import logging
import importlib
from pathlib import Path

import uvicorn

from mcp_app import mcp, SERVER_NAME

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8765"))


@mcp.tool
def ping() -> str:
    """Health check - returns pong."""
    return "pong"


@mcp.tool
def server_info() -> dict:
    """Server name, transport, and endpoint."""
    return {"name": SERVER_NAME, "transport": "streamable-http",
            "host": HOST, "port": PORT, "endpoint": "/mcp"}


def load_tools() -> None:
    """Import every flat .py in tools/ so its @mcp.tool decorators run."""
    app_dir = Path(__file__).parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    tools_dir = app_dir / "tools"
    for file in sorted(tools_dir.glob("*.py")):
        if file.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"tools.{file.stem}")
            logger.info("Loaded tool module: tools.%s", file.stem)
        except Exception as e:
            logger.error("Failed to load tools.%s: %s", file.stem, e)


if __name__ == "__main__":
    load_tools()
    app = mcp.http_app(path="/mcp")
    logger.info("Starting %s on %s:%s/mcp", SERVER_NAME, HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT)
