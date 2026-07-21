"""Calendar tools (MS Graph, app-only). Free-slot search via getSchedule
(findMeetingTimes is delegated-only and unusable app-only) and Teams-meeting
booking with a flock-serialized check-then-insert against double booking.
Target mailbox = GRAPH_CALENDAR_USER."""
import os

from mcp_app import mcp
from lib import graph_client as gc
from lib.dryrun import is_dry_run, dry_log


@mcp.tool
def calendar_check_config() -> dict:
    """Report whether Graph credentials and calendar user are set (no call)."""
    return {"tenant_set": bool(os.getenv("GRAPH_TENANT_ID")),
            "client_set": bool(os.getenv("GRAPH_CLIENT_ID")),
            "secret_set": bool(os.getenv("GRAPH_CLIENT_SECRET")),
            "calendar_user": os.getenv("GRAPH_CALENDAR_USER", "")}


@mcp.tool
def calendar_find_slots(date_from: str, date_to: str,
                        duration_minutes: int = 20) -> dict:
    """Free meeting slots for GRAPH_CALENDAR_USER within [date_from, date_to]
    (ISO-8601 UTC). Busy/tentative/oof blocks and the mailbox's working hours
    are respected. Returns {'slots': [{'start','end'}, ...], 'count': N}."""
    return gc.get_free_slots(date_from, date_to, duration_minutes)


@mcp.tool
def calendar_book_slot(deal_id: int, start: str, end: str,
                       attendee_email: str, subject: str,
                       body_text: str = "") -> dict:
    """Book a Teams meeting with a lead (invite is sent by Graph). The window
    is re-verified as free under an exclusive lock right before creation;
    {'error': 'slot_taken'} means someone got there first. `deal_id` is
    carried through for logging/note context (the tick layer writes Pipedrive)."""
    if is_dry_run():
        return dry_log("calendar_book_slot", deal_id=deal_id, start=start,
                       end=end, attendee_email=attendee_email,
                       subject=subject, body_text=body_text)
    res = gc.book_slot(start, end, attendee_email, subject, body_text)
    if "error" in res:
        return res
    return {**res, "deal_id": deal_id}
