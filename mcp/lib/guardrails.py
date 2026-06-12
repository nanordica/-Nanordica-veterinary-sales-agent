"""Pure send-guardrail decision over a deal's fields. Returns a refusal
reason string, or None if sending is allowed. All state comes from Pipedrive."""
from datetime import datetime, timezone

MAX_EMAILS = 5
MIN_HOURS_BETWEEN = 24


def _parse_dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def evaluate_send_guardrails(deal: dict, to: str, now: datetime,
                             allowlist: list[str] | None = None) -> str | None:
    """Return None if allowed; else a reason:
    not_in_allowlist | email_mismatch | opt_out | too_soon | max_emails.

    `allowlist`: when set (phase 2, synthetic lead), only these
    addresses may receive mail at all — every other recipient is
    refused regardless of the other checks. None = no restriction."""
    if allowlist is not None:
        allowed = {a.strip().lower() for a in allowlist if a.strip()}
        if to.strip().lower() not in allowed:
            return "not_in_allowlist"
    if str(deal.get("email", "")).strip().lower() != to.strip().lower():
        return "email_mismatch"
    if str(deal.get("lost_reason") or "").strip().lower() == "opt-out":
        return "opt_out"
    try:
        sent = int(float(deal.get("emails_sent") or 0))
    except (TypeError, ValueError):
        sent = 0
    if sent >= MAX_EMAILS:
        return "max_emails"
    last = _parse_dt(deal.get("last_contact_at"))
    if last is not None and (now - last).total_seconds() < MIN_HOURS_BETWEEN * 3600:
        return "too_soon"
    return None
