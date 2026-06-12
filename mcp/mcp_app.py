"""The single FastMCP instance. All tool modules import `mcp` from here."""
import os
from fastmcp import FastMCP

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "Ravimus MCP")
mcp = FastMCP(SERVER_NAME)
