"""Pipedrive deal tools."""
from mcp_app import mcp
from lib import pipedrive_client as pc


@mcp.tool
def pipedrive_get_deal(deal_id: int) -> dict:
    """Get one deal by id, including custom fields."""
    return pc.get(f"deals/{deal_id}")


@mcp.tool
def pipedrive_list_deals(stage_id: int | None = None,
                         status: str | None = None,
                         limit: int = 100) -> dict:
    """List deals, optionally filtered by stage_id and status (open/won/lost)."""
    return pc.get("deals", {"stage_id": stage_id, "status": status, "limit": limit})
