# Ravimus MCP

Single-endpoint local MCP server for the Ravimus lead pipeline. Exposes a
narrow, guarded set of Pipedrive / MS Graph / Wix operations at
`http://localhost:8765/mcp`. All lead state lives in Pipedrive; a `DRY_RUN`
switch makes every write a no-op that logs intent.

## Run

```bash
cp .env.example .env   # fill in secrets (gitignored)
pip install -r requirements.txt
python server.py
# or: docker compose up -d
```

## First-time provisioning

```bash
python -m scripts.pipedrive_setup   # preview with DRY_RUN=1 (default)
DRY_RUN=0 python -m scripts.pipedrive_setup   # create pipeline + stages + fields
```

Writes `data/field_keys.json` (friendly-name -> Pipedrive key + stage ids),
used by every tool. Re-running creates nothing (idempotent).

## Tools

Single endpoint: `http://localhost:8765/mcp`

### Utility

| Tool | Description |
|---|---|
| `ping` | Health check — returns `"pong"`. |
| `server_info` | Server name, transport, host, port, endpoint. |

### Pipedrive — deals (`pipedrive_deals.py`)

All deal metadata lives in **one** Pipedrive `text` custom field
`ravimus_hackathon_data` (a JSON object). Tools that read a deal add a
`_state` key with the parsed dict. The pipeline is `ravimus-hackathon`.
Stages are referenced by friendly name (e.g. `"Contacted"`); stage IDs are
resolved from `data/field_keys.json` (written by `pipedrive_setup`).

| Tool | Signature | Description |
|---|---|---|
| `pipedrive_get_deal` | `(deal_id: int)` | Get one deal by id. Adds `_state`. |
| `pipedrive_list_deals` | `(stage_id?, status?, limit=100)` | List deals; each row gets `_state`. |
| `pipedrive_create_deal` | `(person_id: int, title: str, stage: str, data?: dict)` | Create a deal in a stage by name; `data` becomes the JSON state. |
| `pipedrive_update_deal_data` | `(deal_id: int, data: dict)` | Merge `data` into the deal's JSON state (read-modify-write). |
| `pipedrive_move_deal_stage` | `(deal_id: int, stage: str)` | Move a deal to a stage by friendly name. |
| `pipedrive_add_note` | `(deal_id: int, content: str)` | Add a note to a deal. |

### Pipedrive — persons (`pipedrive_persons.py`)

| Tool | Signature | Description |
|---|---|---|
| `pipedrive_search_persons` | `(term: str, fields="email")` | Search persons; used to bind an inbound email or order to a deal. |
| `pipedrive_create_person` | `(name: str, email: str)` | Create a person with a primary email. |
| `pipedrive_update_person` | `(person_id: int, fields: dict)` | Update native person fields (name, phone, etc.). |

### Pipedrive — fields & config (`pipedrive_fields.py`)

| Tool | Signature | Description |
|---|---|---|
| `pipedrive_check_config` | `()` | Report whether token and domain are set (no API call). |
| `pipedrive_get_deal_fields` | `()` | All deal field definitions, including custom-field keys. |
| `pipedrive_get_person_fields` | `()` | All person field definitions. |

### Mail — MS Graph (`mail.py`)

| Tool | Signature | Description |
|---|---|---|
| `mail_check_config` | `()` | Report whether Graph credentials and sender are set (no send). |
| `mail_send` | `(deal_id: int, to: str, subject: str, body_html: str)` | Send an email with guardrails enforced from Pipedrive deal state (see below). |
| `mail_list_new_messages` | `(folder="inbox")` | List messages received since the last call (Graph delta cursor). |

### Wix (`wix.py`)

Auth uses raw `Authorization` header + `wix-site-id` only.

| Tool | Signature | Description |
|---|---|---|
| `wix_check_config` | `()` | Report whether Wix key, account, and site are set (no API call). |
| `wix_list_orders` | `(since?: str, limit=50)` | List recent store orders, optionally filtered by `since` (ISO-8601). |
| `wix_create_coupon` | `(name: str, code: str, percent_off=100, usage_limit=1)` | Create a personal coupon (DRY_RUN-guarded). |
| `wix_check_coupon_usage` | `(code: str)` | Check how many times a coupon code has been used. |
| `wix_get_click_events` | `(utm_content?: str, since?: str, limit=100)` | List Academy-link click events from the `clickEvents` Wix Data collection (written by the site's masterPage.js Velo snippet). Filter by exact `utm_content` hash and/or `since` (ISO-8601). Newest first, read-only. Requires the **Wix Data – Read Data Items** permission on the API key. |

### Calendar (`calendar.py`)

Free-slot search + Teams-meeting booking, app-only, using the
**organizer-calendar model**: every Graph call anchors on the agent mailbox
(`GRAPH_SENDER`, e.g. `ravimus@`). Free/busy offered is
`GRAPH_CALENDAR_USER`'s (the human's), queried via getSchedule; the event
is created on the **agent's own calendar**, inviting both
`GRAPH_CALENDAR_USER` and the lead as required attendees. Two benefits:

- the Exchange `ApplicationAccessPolicy` group needs **only** the agent
  mailbox — the app never writes the human's mailbox (his free/busy comes
  via org-default calendar sharing);
- the agent calendar is the system of record, and the human
  accepts/declines invites normally.

Known limitation: a decline is not auto-detected yet (future tick
enhancement polling the event's `responseStatus`).

Uses `POST /calendar/getSchedule` deliberately — `findMeetingTimes` is
**delegated-only** and silently unusable with app-only client-credentials
auth. Free windows are computed locally: busy/tentative/oof blocks are
subtracted and, when the response carries `workingHours`, slots are offered
only inside them (mailbox timezones with non-IANA Windows names fall back
to UTC).

| Tool | Signature | Description |
|---|---|---|
| `calendar_check_config` | `()` | Report whether Graph credentials and calendar user are set (no call). |
| `calendar_find_slots` | `(date_from: str, date_to: str, duration_minutes=20)` | Free slots (ISO-8601 UTC window). Returns `{"slots": [{"start", "end"}, ...], "count": N}`, capped at 20. |
| `calendar_book_slot` | `(deal_id: int, start: str, end: str, attendee_email: str, subject: str, body_text="")` | Book a Teams meeting on the agent's calendar, inviting `GRAPH_CALENDAR_USER` + the lead; Graph sends the invites. DRY_RUN-guarded. `deal_id` is logging/note context only. |

**No-double-book strategy:** `book_slot` takes an exclusive `flock` on
`GRAPH_BOOK_LOCK_PATH` (default `./cache/calendar-book.lock`) for the whole
check-then-insert: `GRAPH_CALENDAR_USER`'s window is re-verified as free
via `getSchedule` immediately before the `POST /events`, inside the lock
(tentative blocks too, which also covers not-yet-accepted invites). If it
is no longer free, the tool returns `{"error": "slot_taken"}` and creates
nothing.

**Azure scopes (application permissions, admin consent required):**
`Calendars.Read` (getSchedule), `Calendars.ReadWrite` (event creation);
`MailboxSettings.Read` optional. Recommended: an Exchange
`ApplicationAccessPolicy` limiting the app registration to the **agent
mailbox only** (`GRAPH_SENDER`) — the organizer model needs no rights on
the human's mailbox.

**Live smoke test** (after granting scopes):
`python -m scripts.smoke_calendar` prints tomorrow's free slots (read-only);
add `--book --start ... --end ... --attendee ...` to create a real event.

### Omniva (`omniva.py`)

Physical sample dispatch to Latvian vets via Omniva parcel machines
(OMX REST API, `https://omx.omniva.eu/api/v01/omx`, HTTP Basic auth).
Pickup points come from the public `https://www.omniva.ee/locations.json`
feed (no auth, EE+LV+LT; cached in-process for 24 h).

| Tool | Signature | Description |
|---|---|---|
| `omniva_check_config` | `()` | Report whether customer code, username, and password are set (no API call). |
| `omniva_list_pickup_points` | `(country="LV", query?: str, limit=20)` | Search pickup points; returned `zip` is the `pickup_point_id` for shipment registration. |
| `omniva_create_shipment` | `(deal_id: int, receiver_name, receiver_phone, pickup_point_id, receiver_email?)` | Register a parcel-machine sample shipment (DRY_RUN-guarded). Mobile phone mandatory — arrival SMS carries the door code. `deal_id` is context only. |
| `omniva_get_label` | `(barcode: str)` | Fetch the label PDF to `cache/labels/<barcode>.pdf`, return the path (DRY_RUN-guarded: authenticated call + file write). |
| `omniva_track` | `(barcode: str)` | Tracking events for a barcode (read-only). |

**No public sandbox exists** — the first live test must be a real (cheap)
shipment. Keep `DRY_RUN=1` until then; the dry-run log shows the exact
would-be registration.

## Guardrails (`mail_send`)

`mail_send` reads the deal's `_state` from Pipedrive and refuses when:

- recipient `to` does not match `deal.email`
- `lost_reason == "opt-out"` (opt-out is modelled as a Lost deal in Pipedrive — there is no separate opt-out tool)
- `last_contact_at` is less than 24 hours ago
- `emails_sent >= 5`

On success, `last_contact_at` and `emails_sent` are written back to the deal
state and a note is logged.

## DRY_RUN

`DRY_RUN=1` (the default when unset) logs every write and skips the external
API call. `DRY_RUN=0` goes live. Reads always execute regardless.

## .env

See `.env.example` for all required keys. Secrets (`*_TOKEN`, `*_SECRET`,
`*_API_KEY`) must live only in the gitignored `mcp/.env`.

| Variable | Used by |
|---|---|
| `PIPEDRIVE_API_TOKEN` | all `pipedrive_*` tools |
| `PIPEDRIVE_DOMAIN` | all `pipedrive_*` tools (e.g. `nanordica.pipedrive.com`) |
| `GRAPH_TENANT_ID` | `mail_*` tools |
| `GRAPH_CLIENT_ID` | `mail_*` tools |
| `GRAPH_CLIENT_SECRET` | `mail_*` tools |
| `GRAPH_SENDER` | `mail_send` (the from-address); `calendar_*` tools (organizer mailbox — events are created here) |
| `GRAPH_CALENDAR_USER` | `calendar_*` tools (whose free/busy is offered; invited to every booking) |
| `GRAPH_BOOK_LOCK_PATH` | `calendar_book_slot` flock file (default `./cache/calendar-book.lock`) |
| `WIX_API_KEY` | `wix_*` tools |
| `WIX_ACCOUNT_ID` | `wix_*` tools |
| `WIX_SITE_ID` | `wix_*` tools |
| `OMNIVA_CUSTOMER_CODE` | `omniva_*` tools (partner/AXA code, goes into request bodies) |
| `OMNIVA_API_USERNAME` | `omniva_*` tools (HTTP Basic) |
| `OMNIVA_API_PASSWORD` | `omniva_*` tools (HTTP Basic) |
| `OMNIVA_SENDER_*` | `omniva_create_shipment` sender block (NAME, PHONE, EMAIL, COUNTRY, POSTCODE, DELIVERYPOINT, STREET, HOUSE_NO) |
| `DRY_RUN` | all write tools (default `1`) |

## Claude Code integration

The server is registered in `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "ravimus": {
      "type": "http",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

Start the server (`python server.py` inside `mcp/`) before using any tool
from Claude Code. The server must be running for Claude Code to connect.
