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
| `GRAPH_SENDER` | `mail_send` (the from-address) |
| `WIX_API_KEY` | `wix_*` tools |
| `WIX_ACCOUNT_ID` | `wix_*` tools |
| `WIX_SITE_ID` | `wix_*` tools |
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
