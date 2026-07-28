"""Microsoft Graph app-only (client-credentials) client: token, sendMail,
inbox delta read, calendar free-slot search + booking. Sender/organizer
mailbox = GRAPH_SENDER; offered availability = GRAPH_CALENDAR_USER."""
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

_GRAPH = "https://graph.microsoft.com/v1.0"
_token_cache = {"value": None, "exp": 0.0}


def _env(name: str) -> str:
    return os.getenv(name, "")


def get_token() -> dict:
    """Return {'token': ...} or {'error': ...}. Caches until ~60s before expiry."""
    if _token_cache["value"] and time.time() < _token_cache["exp"] - 60:
        return {"token": _token_cache["value"]}
    tenant, client, secret = _env("GRAPH_TENANT_ID"), _env("GRAPH_CLIENT_ID"), _env("GRAPH_CLIENT_SECRET")
    if not (tenant and client and secret):
        return {"error": "GRAPH_TENANT_ID/CLIENT_ID/CLIENT_SECRET not all set"}
    data = urllib.parse.urlencode({
        "client_id": client, "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
            tok = json.loads(r.read().decode())
        _token_cache["value"] = tok["access_token"]
        _token_cache["exp"] = time.time() + tok.get("expires_in", 3600)
        return {"token": tok["access_token"]}
    except urllib.error.HTTPError as e:
        return {"error": f"token HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def _auth_headers() -> dict | None:
    t = get_token()
    if "error" in t:
        return None
    return {"Authorization": f"Bearer {t['token']}", "Content-Type": "application/json"}


def file_attachment(path: str) -> dict:
    """Graph fileAttachment entry (base64 contentBytes) for a local file."""
    import base64
    import mimetypes
    p = Path(path)
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return {"@odata.type": "#microsoft.graph.fileAttachment",
            "name": p.name, "contentType": ctype,
            "contentBytes": base64.b64encode(p.read_bytes()).decode()}


def send_mail(to: str, subject: str, body_html: str,
              attachments: list | None = None) -> dict:
    """Send mail as GRAPH_SENDER. `attachments` = local file paths, embedded
    as base64 fileAttachments (sendMail size cap ~3 MB total — labels are
    tens of kB). Returns {'sent': True} or {'error': ...}."""
    sender = _env("GRAPH_SENDER")
    headers = _auth_headers()
    if headers is None:
        return get_token()  # carries the error
    message = {"subject": subject,
               "body": {"contentType": "HTML", "content": body_html},
               "toRecipients": [{"emailAddress": {"address": to}}]}
    if attachments:
        try:
            message["attachments"] = [file_attachment(a) for a in attachments]
        except OSError as e:
            return {"error": f"attachment unreadable: {e}"}
    msg = {"message": message, "saveToSentItems": True}
    url = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/sendMail"
    req = urllib.request.Request(url, data=json.dumps(msg).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"sent": True, "status": r.status}
    except urllib.error.HTTPError as e:
        return {"error": f"sendMail HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def list_new_messages(folder: str = "inbox") -> dict:
    """Read new messages via the delta endpoint. Persists the deltaLink to
    GRAPH_DELTA_PATH so each call returns only messages since the last call."""
    sender = _env("GRAPH_SENDER")
    delta_path = Path(_env("GRAPH_DELTA_PATH") or "./data/graph_delta.json")
    headers = _auth_headers()
    if headers is None:
        return get_token()
    initial = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/mailFolders/{folder}/messages/delta"
    if delta_path.exists():
        url = json.loads(delta_path.read_text()).get("deltaLink") or initial
    else:
        url = initial
    messages = []
    try:
        while url:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=30) as r:
                page = json.loads(r.read().decode())
            messages.extend(page.get("value", []))
            if "@odata.nextLink" in page:
                url = page["@odata.nextLink"]
            else:
                delta_path.parent.mkdir(parents=True, exist_ok=True)
                delta_path.write_text(json.dumps({"deltaLink": page.get("@odata.deltaLink")}))
                url = None
        return {"messages": [
            {"id": m.get("id"), "from": (m.get("from") or {}).get("emailAddress", {}).get("address"),
             "subject": m.get("subject"), "received": m.get("receivedDateTime"),
             "preview": m.get("bodyPreview")}
            for m in messages]}
    except urllib.error.HTTPError as e:
        return {"error": f"delta HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


# --- Calendar (getSchedule + event booking) --------------------------------
# getSchedule is used deliberately: findMeetingTimes is delegated-only and
# silently unusable with app-only client-credentials auth.
#
# Organizer-calendar model: all Graph calls anchor on the agent mailbox
# (GRAPH_SENDER = ravimus@) — events are created on ITS calendar, inviting
# both GRAPH_CALENDAR_USER (whose availability is offered) and the lead.
# The app therefore never writes the human's mailbox (ApplicationAccessPolicy
# only needs to cover the agent mailbox); free/busy of GRAPH_CALENDAR_USER
# arrives via getSchedule's org-default sharing.

_BLOCKING = {"busy", "tentative", "oof"}
_DAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
         "friday": 4, "saturday": 5, "sunday": 6}


def _call(method: str, path: str, body: dict | None = None) -> dict:
    """Authenticated Graph call. Returns parsed JSON or {'error': ...}."""
    headers = _auth_headers()
    if headers is None:
        return get_token()  # carries the error
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{_GRAPH}{path}", data=data,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {"status": r.status}
    except urllib.error.HTTPError as e:
        return {"error": f"Graph HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def _parse_dt(s: str):
    """Parse a Graph/ISO datetime as UTC-aware. Graph emits 7 fractional
    digits, which fromisoformat rejects — truncate to 6."""
    from datetime import datetime, timezone
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1]
    if "." in s:
        head, frac = s.split(".", 1)
        s = f"{head}.{frac[:6]}"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_dt(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _wh_tz(working_hours: dict):
    """Resolve the workingHours timezone. UTC and IANA names resolve exactly;
    Windows names (e.g. 'FLE Standard Time') fall back to UTC — documented."""
    from datetime import timezone
    name = ((working_hours.get("timeZone") or {}).get("name") or "UTC")
    if name.upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def _pick_schedule(res: dict, schedule_id: str) -> dict:
    """The value[] entry whose scheduleId matches (case-insensitive);
    falls back to the first entry (we only ever request one schedule)."""
    entries = res.get("value") or [{}]
    for entry in entries:
        if (entry.get("scheduleId") or "").lower() == schedule_id.lower():
            return entry
    return entries[0]


def _working_intervals(working_hours: dict | None, win_start, win_end) -> list:
    """UTC intervals inside [win_start, win_end] allowed by workingHours.
    No workingHours -> the whole window is allowed."""
    from datetime import datetime, time as dtime, timedelta
    if not working_hours or not working_hours.get("startTime"):
        return [(win_start, win_end)]
    days = {_DAYS[d.lower()] for d in working_hours.get("daysOfWeek", [])
            if d.lower() in _DAYS}
    tz = _wh_tz(working_hours)
    start_t = dtime.fromisoformat(working_hours["startTime"].split(".")[0])
    end_t = dtime.fromisoformat(working_hours["endTime"].split(".")[0])
    out = []
    day = win_start.astimezone(tz).date() - timedelta(days=1)  # tz-shift margin
    last = win_end.astimezone(tz).date() + timedelta(days=1)
    while day <= last:
        if day.weekday() in days:
            from datetime import timezone as _tzmod
            s = datetime.combine(day, start_t, tzinfo=tz).astimezone(_tzmod.utc)
            e = datetime.combine(day, end_t, tzinfo=tz).astimezone(_tzmod.utc)
            s, e = max(s, win_start), min(e, win_end)
            if s < e:
                out.append((s, e))
        day += timedelta(days=1)
    return out


def _merge_busy(items: list, win_start, win_end) -> list:
    """Merged, sorted UTC busy intervals (busy/tentative/oof) clipped to the
    window."""
    spans = []
    for it in items:
        if (it.get("status") or "busy") not in _BLOCKING:
            continue
        s = max(_parse_dt(it["start"]["dateTime"]), win_start)
        e = min(_parse_dt(it["end"]["dateTime"]), win_end)
        if s < e:
            spans.append((s, e))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _subtract(intervals: list, busy: list) -> list:
    """Subtract merged busy spans from allowed intervals."""
    free = []
    for s, e in intervals:
        cur = s
        for bs, be in busy:
            if be <= cur or bs >= e:
                continue
            if bs > cur:
                free.append((cur, bs))
            cur = max(cur, be)
        if cur < e:
            free.append((cur, e))
    return free


def get_free_slots(date_from: str, date_to: str, duration_minutes: int = 20,
                   max_slots: int = 20) -> dict:
    """Free meeting slots of `duration_minutes` for GRAPH_CALENDAR_USER within
    [date_from, date_to] (ISO-8601 UTC). Uses POST /calendar/getSchedule
    (app-only-safe; findMeetingTimes is delegated-only), then computes free
    windows locally: busy/tentative/oof blocks are subtracted and, when the
    response carries workingHours, slots are offered only inside them.
    Returns {'slots': [{'start': ..., 'end': ...}, ...], 'count': N}
    (capped at max_slots) or {'error': ...}. The call anchors on the
    ORGANIZER mailbox (GRAPH_SENDER) and queries GRAPH_CALENDAR_USER's
    schedule — the app needs no rights on the human's mailbox."""
    from datetime import timedelta
    sender, calendar_user = _env("GRAPH_SENDER"), _env("GRAPH_CALENDAR_USER")
    if not (sender and calendar_user):
        return {"error": "GRAPH_SENDER/GRAPH_CALENDAR_USER not all set"}
    interval = max(5, min(1440, int(duration_minutes)))  # Graph bounds
    body = {"schedules": [calendar_user],
            "startTime": {"dateTime": date_from, "timeZone": "UTC"},
            "endTime": {"dateTime": date_to, "timeZone": "UTC"},
            "availabilityViewInterval": interval}
    res = _call("POST", f"/users/{urllib.parse.quote(sender)}"
                        "/calendar/getSchedule", body)
    if "error" in res:
        return res
    entry = _pick_schedule(res, calendar_user)
    win_start, win_end = _parse_dt(date_from), _parse_dt(date_to)
    allowed = _working_intervals(entry.get("workingHours"), win_start, win_end)
    busy = _merge_busy(entry.get("scheduleItems", []), win_start, win_end)
    dur = timedelta(minutes=int(duration_minutes))
    slots = []
    for s, e in _subtract(allowed, busy):
        cur = s
        while cur + dur <= e and len(slots) < max_slots:
            slots.append({"start": _fmt_dt(cur), "end": _fmt_dt(cur + dur)})
            cur += dur
        if len(slots) >= max_slots:
            break
    return {"slots": slots, "count": len(slots)}


def _window_is_free(sender: str, calendar_user: str,
                    start: str, end: str) -> dict:
    """Re-check calendar_user's [start, end] via getSchedule (anchored on the
    organizer mailbox). {'free': bool} or {'error': ...}."""
    body = {"schedules": [calendar_user],
            "startTime": {"dateTime": start, "timeZone": "UTC"},
            "endTime": {"dateTime": end, "timeZone": "UTC"},
            "availabilityViewInterval": 5}
    res = _call("POST", f"/users/{urllib.parse.quote(sender)}"
                        "/calendar/getSchedule", body)
    if "error" in res:
        return res
    entry = _pick_schedule(res, calendar_user)
    busy = _merge_busy(entry.get("scheduleItems", []),
                       _parse_dt(start), _parse_dt(end))
    return {"free": not busy}


def book_slot(start: str, end: str, attendee_email: str, subject: str,
              body_text: str = "") -> dict:
    """Create a Teams meeting on the ORGANIZER's calendar (GRAPH_SENDER) and
    invite both GRAPH_CALENDAR_USER and `attendee_email` as required attendees
    (Graph sends the invitations automatically). Double-booking against
    GRAPH_CALENDAR_USER's free/busy is prevented by an exclusive flock
    (GRAPH_BOOK_LOCK_PATH, default ./cache/calendar-book.lock) held around a
    getSchedule re-check + POST: if the window is no longer free (tentative
    counts — covering not-yet-accepted invites), returns
    {'error': 'slot_taken'} without creating anything."""
    import fcntl
    sender, calendar_user = _env("GRAPH_SENDER"), _env("GRAPH_CALENDAR_USER")
    if not (sender and calendar_user):
        return {"error": "GRAPH_SENDER/GRAPH_CALENDAR_USER not all set"}
    lock_path = Path(_env("GRAPH_BOOK_LOCK_PATH") or "./cache/calendar-book.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            check = _window_is_free(sender, calendar_user, start, end)
            if "error" in check:
                return check
            if not check["free"]:
                return {"error": "slot_taken", "start": start, "end": end}
            event = {"subject": subject,
                     "body": {"contentType": "Text", "content": body_text},
                     "start": {"dateTime": start, "timeZone": "UTC"},
                     "end": {"dateTime": end, "timeZone": "UTC"},
                     "attendees": [{"emailAddress": {"address": calendar_user},
                                    "type": "required"},
                                   {"emailAddress": {"address": attendee_email},
                                    "type": "required"}],
                     "isOnlineMeeting": True,
                     "onlineMeetingProvider": "teamsForBusiness"}
            res = _call("POST", f"/users/{urllib.parse.quote(sender)}"
                                "/events", event)
            if "error" in res:
                return res
            return {"booked": True, "event_id": res.get("id"),
                    "start": start, "end": end}
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
