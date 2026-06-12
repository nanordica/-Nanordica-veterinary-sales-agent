"""Pipedrive deal tools. All deal metadata lives in one JSON state field."""
from mcp_app import mcp
from lib import pipedrive_client as pc
from lib import deal_state
from lib.dryrun import is_dry_run, dry_log
from lib.field_map import resolve_stage_id


@mcp.tool
def pipedrive_get_deal(deal_id: int) -> dict:
    """Get one deal by id. Adds `_state` (parsed JSON state dict)."""
    res = pc.get(f"deals/{deal_id}")
    data = res.get("data")
    if isinstance(data, dict):
        res["_state"] = deal_state.read_state(data)
    return res


@mcp.tool
def pipedrive_list_deals(stage_id: int | None = None,
                         status: str | None = None,
                         limit: int = 100) -> dict:
    """List deals (optionally by stage_id/status). Each row gets `_state`."""
    res = pc.get("deals", {"stage_id": stage_id, "status": status, "limit": limit})
    rows = res.get("data")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                row["_state"] = deal_state.read_state(row)
    return res


@mcp.tool
def pipedrive_create_deal(person_id: int, title: str, stage: str,
                          data: dict | None = None) -> dict:
    """Create a deal for a person in a stage (by name). `data` -> JSON state."""
    stage_id = resolve_stage_id(stage)
    if stage_id is None:
        return {"error": f"unknown stage '{stage}'; run pipedrive_setup first"}
    if deal_state.state_key() is None:
        return {"error": "state field key unknown; run pipedrive_setup first"}
    body = {"person_id": person_id, "title": title, "stage_id": stage_id}
    body.update(deal_state.encode_state(data or {}))
    if is_dry_run():
        return dry_log("pipedrive_create_deal", body=body)
    return pc.post("deals", body)


@mcp.tool
def pipedrive_update_deal_data(deal_id: int, data: dict) -> dict:
    """Merge `data` into the deal's JSON state (read-modify-write)."""
    current = pc.get(f"deals/{deal_id}")
    cur_data = current.get("data")
    if not isinstance(cur_data, dict):
        return {"error": f"deal {deal_id} not found"}
    merged = {**deal_state.read_state(cur_data), **data}
    body = deal_state.encode_state(merged)
    if not body:
        return {"error": "state field key unknown; run pipedrive_setup first"}
    if is_dry_run():
        return dry_log("pipedrive_update_deal_data", deal_id=deal_id, merged=merged)
    return pc.put(f"deals/{deal_id}", body)


@mcp.tool
def pipedrive_move_deal_stage(deal_id: int, stage: str) -> dict:
    """Move a deal to a stage by friendly stage name (e.g. 'Contacted')."""
    stage_id = resolve_stage_id(stage)
    if stage_id is None:
        return {"error": f"unknown stage '{stage}'; run pipedrive_setup first"}
    if is_dry_run():
        return dry_log("pipedrive_move_deal_stage", deal_id=deal_id,
                       stage=stage, stage_id=stage_id)
    return pc.put(f"deals/{deal_id}", {"stage_id": stage_id})


@mcp.tool
def pipedrive_add_note(deal_id: int, content: str) -> dict:
    """Add a note to a deal (log correspondence / context)."""
    body = {"deal_id": deal_id, "content": content}
    if is_dry_run():
        return dry_log("pipedrive_add_note", body=body)
    return pc.post("notes", body)
