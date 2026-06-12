"""Read-only Pipedrive field definitions and config diagnostics."""
import os
from mcp_app import mcp
from lib import pipedrive_client as pc


@mcp.tool
def pipedrive_check_config() -> dict:
    """Report whether Pipedrive token and domain are set (no API call)."""
    return {"token_set": bool(os.getenv("PIPEDRIVE_API_TOKEN")),
            "domain": os.getenv("PIPEDRIVE_DOMAIN", "")}


@mcp.tool
def pipedrive_get_deal_fields() -> dict:
    """All deal field definitions, including custom-field keys."""
    return pc.get("dealFields", {"limit": 500})


@mcp.tool
def pipedrive_get_person_fields() -> dict:
    """All person field definitions, including custom-field keys."""
    return pc.get("personFields", {"limit": 500})
