"""Pipedrive person tools."""
from mcp_app import mcp
from lib import pipedrive_client as pc


@mcp.tool
def pipedrive_search_persons(term: str, fields: str = "email") -> dict:
    """Search persons by term in the given fields (default email).
    Used to bind an inbound email or order to its deal."""
    return pc.get("persons/search", {"term": term, "fields": fields})
