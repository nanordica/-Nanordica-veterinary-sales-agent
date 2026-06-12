"""Mail tools (MS Graph). mail_send enforces all guardrails from the Pipedrive
deal's JSON state (single source of truth) and writes the send back to the deal."""
import os
from datetime import datetime, timezone

from mcp_app import mcp
from lib import pipedrive_client as pc
from lib import graph_client as gc
from lib import deal_state
from lib.guardrails import evaluate_send_guardrails
from lib.dryrun import is_dry_run, dry_log


@mcp.tool
def mail_check_config() -> dict:
    """Report whether Graph credentials and sender are set (no send)."""
    return {"tenant_set": bool(os.getenv("GRAPH_TENANT_ID")),
            "client_set": bool(os.getenv("GRAPH_CLIENT_ID")),
            "secret_set": bool(os.getenv("GRAPH_CLIENT_SECRET")),
            "sender": os.getenv("GRAPH_SENDER", "")}


@mcp.tool
def mail_send(deal_id: int, to: str, subject: str, body_html: str) -> dict:
    """Send an email to a lead. Enforces, from the Pipedrive deal's JSON state:
    email match, opt-out, <=1 mail/24h, <=5 mails total. On success, updates
    last_contact_at + emails_sent in the deal state and logs a note."""
    raw = pc.get(f"deals/{deal_id}")
    data = raw.get("data")
    if not isinstance(data, dict):
        return {"error": f"deal {deal_id} not found"}
    state = deal_state.read_state(data)
    if deal_state.state_key() is None:
        return {"error": "state field key unknown; run pipedrive_setup first"}

    now = datetime.now(timezone.utc)
    # MAIL_ALLOWLIST (komaga eraldatud aadressid): faasis 2 tohib
    # saata AINULT neile. Tühi/seadmata = piirang puudub (faas 3).
    allowlist_env = os.getenv("MAIL_ALLOWLIST", "").strip()
    allowlist = allowlist_env.split(",") if allowlist_env else None
    refusal = evaluate_send_guardrails(state, to, now, allowlist=allowlist)
    if refusal:
        return {"refused": refusal, "deal_id": deal_id}

    if is_dry_run():
        return dry_log("mail_send", deal_id=deal_id, to=to, subject=subject)

    result = gc.send_mail(to, subject, body_html)
    if "error" in result:
        return result

    # last_contact_at + emails_sent BEFORE the note so a note failure can't resend.
    try:
        sent = int(float(state.get("emails_sent") or 0))
    except (TypeError, ValueError):
        sent = 0
    merged = {**state, "last_contact_at": now.isoformat(), "emails_sent": sent + 1}
    pc.put(f"deals/{deal_id}", deal_state.encode_state(merged))
    pc.post("notes", {"deal_id": deal_id,
                      "content": f"<b>Sent:</b> {subject}<br>{body_html}"})
    return {"sent": True, "deal_id": deal_id, "emails_sent": sent + 1}


@mcp.tool
def mail_list_new_messages(folder: str = "inbox") -> dict:
    """List messages received since the last call (Graph delta cursor)."""
    return gc.list_new_messages(folder)
