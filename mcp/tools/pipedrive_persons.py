"""Pipedrive person tools."""
from mcp_app import mcp
from lib import pipedrive_client as pc
from lib.dryrun import is_dry_run, dry_log


@mcp.tool
def pipedrive_search_persons(term: str, fields: str = "email") -> dict:
    """Search persons by term in the given fields (default email).
    Used to bind an inbound email or order to its deal."""
    return pc.get("persons/search", {"term": term, "fields": fields})


@mcp.tool
def pipedrive_create_person(name: str, email: str) -> dict:
    """Create a person with a primary email."""
    body = {"name": name, "email": [{"value": email, "primary": True}]}
    if is_dry_run():
        return dry_log("pipedrive_create_person", body=body)
    return pc.post("persons", body)


@mcp.tool
def pipedrive_update_person(person_id: int, fields: dict) -> dict:
    """Update native person fields (e.g. name, phone)."""
    if is_dry_run():
        return dry_log("pipedrive_update_person", person_id=person_id, body=fields)
    return pc.put(f"persons/{person_id}", fields)
