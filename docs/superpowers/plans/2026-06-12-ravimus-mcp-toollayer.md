# Ravimus MCP Tool-Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-endpoint local MCP server at `mcp/` that exposes a narrow, guarded set of Pipedrive / MS Graph mail / Wix operations for the Ravimus lead pipeline, plus an idempotent Pipedrive provisioning script.

**Architecture:** One FastMCP instance serving all tools at `/mcp`, with `pipedrive_*` / `mail_*` / `wix_*` name prefixes. Pure API clients live in `mcp/lib/`; tool files are thin wrappers. All state-of-truth lives in Pipedrive (guardrails read/write deal fields). A global `DRY_RUN` switch routes every write through a logger that does not touch external APIs. Pure decision logic (DRY_RUN, send-guardrails, setup-planning, field-key mapping) is factored into testable functions; HTTP clients are smoke-tested.

**Tech Stack:** Python 3.11+, FastMCP (`fastmcp<3`), uvicorn/starlette, urllib (stdlib HTTP), pytest, Docker Compose. External APIs: Pipedrive v1, Microsoft Graph (app-only), Wix (ecom + coupons).

**Spec:** `docs/superpowers/specs/2026-06-12-ravimus-mcp-toollayer-design.md`

---

## Design decisions locked during planning (refinements over the spec)

- **No `server_registry.py` / sub-servers / aggregate.** Single endpoint means one FastMCP instance is enough (YAGNI). Spec listed `server_registry.py`; we drop it.
- **Custom fields are `varchar`/`text`/`double`, never `enum`.** Vocabulary fields (`ab_variant`, `decision_style`, `lost_reason`) store plain strings. This avoids Pipedrive enum option-ID indirection in every read/write and guardrail. Allowed values are documented, not enforced by Pipedrive.
- **`last_contact_at` / `sample_claimed_at` are `varchar` storing ISO-8601 UTC strings**, not Pipedrive `date` fields, so the 24h guardrail has time precision.
- **Friendly-name ↔ hashed-key mapping** persisted by the setup script to `data/field_keys.json`. Tools accept friendly field names and translate via `lib/field_map.py`.
- **`DRY_RUN` defaults to ON** (`"1"`) when unset — safe by default.

---

## File structure

```
mcp/
  .gitignore              # .env, data/, __pycache__
  .env.example            # placeholders only
  requirements.txt
  Dockerfile
  docker-compose.yaml
  README.md
  mcp_app.py              # the single FastMCP instance + SERVER_NAME
  server.py               # tool auto-loader + ping/server_info + uvicorn run
  conftest.py             # pytest: put mcp/ on sys.path
  lib/
    __init__.py
    dryrun.py             # is_dry_run(), dry_log()
    field_map.py          # load/save data/field_keys.json; resolve names<->keys
    guardrails.py         # pure evaluate_send_guardrails()
    setup_plan.py         # pure plan_setup() over existing pipeline/stage/field state
    constants.py          # PIPELINE_NAME, STAGES, CUSTOM_FIELDS
    pipedrive_client.py   # HTTP client (read/write + admin create_*)
    graph_client.py       # MS Graph app-only token + send + delta read
    wix_client.py         # Wix headers + orders + coupons
  scripts/
    __init__.py
    pipedrive_setup.py    # executes plan_setup against the live account, writes field_map
  tools/
    __init__.py
    pipedrive_deals.py
    pipedrive_persons.py
    pipedrive_fields.py
    mail.py
    wix.py
  tests/
    test_dryrun.py
    test_field_map.py
    test_guardrails.py
    test_setup_plan.py
    test_pipedrive_url.py
```

`.mcp.json` (repo root) registers the server for Claude Code.

---

## Task 1: Platform skeleton — FastMCP instance + ping at `/mcp`

**Files:**
- Create: `mcp/mcp_app.py`, `mcp/server.py`, `mcp/tools/__init__.py`, `mcp/lib/__init__.py`, `mcp/requirements.txt`, `mcp/.gitignore`, `mcp/conftest.py`

- [ ] **Step 1: Create `mcp/requirements.txt`**

```
fastmcp<3
uvicorn
starlette
pytest
```

- [ ] **Step 2: Create `mcp/.gitignore`**

```
.env
data/
__pycache__/
*.pyc
```

- [ ] **Step 3: Create `mcp/mcp_app.py`**

```python
"""The single FastMCP instance. All tool modules import `mcp` from here."""
import os
from fastmcp import FastMCP

SERVER_NAME = os.getenv("MCP_SERVER_NAME", "Ravimus MCP")
mcp = FastMCP(SERVER_NAME)
```

- [ ] **Step 4: Create `mcp/tools/__init__.py` and `mcp/lib/__init__.py`** (both empty files)

- [ ] **Step 5: Create `mcp/server.py`**

```python
"""Ravimus MCP — single-endpoint server.

Auto-discovers every flat .py in tools/ (each registers on the shared `mcp`
instance via `from mcp_app import mcp`) and serves them all at /mcp.
"""
import os
import sys
import logging
import importlib
from pathlib import Path

import uvicorn

from mcp_app import mcp, SERVER_NAME

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8765"))


@mcp.tool
def ping() -> str:
    """Health check - returns pong."""
    return "pong"


@mcp.tool
def server_info() -> dict:
    """Server name, transport, and endpoint."""
    return {"name": SERVER_NAME, "transport": "streamable-http",
            "host": HOST, "port": PORT, "endpoint": "/mcp"}


def load_tools() -> None:
    """Import every flat .py in tools/ so its @mcp.tool decorators run."""
    app_dir = Path(__file__).parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    tools_dir = app_dir / "tools"
    for file in sorted(tools_dir.glob("*.py")):
        if file.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"tools.{file.stem}")
            logger.info("Loaded tool module: tools.%s", file.stem)
        except Exception as e:
            logger.error("Failed to load tools.%s: %s", file.stem, e)


if __name__ == "__main__":
    load_tools()
    app = mcp.http_app(path="/mcp")
    logger.info("Starting %s on %s:%s/mcp", SERVER_NAME, HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT)
```

- [ ] **Step 6: Create `mcp/conftest.py`** (so tests can `import lib...`)

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

- [ ] **Step 7: Install and run the server**

Run: `cd mcp && python -m pip install -r requirements.txt && python server.py`
Expected: log line `Starting Ravimus MCP on 0.0.0.0:8765/mcp`, no tracebacks. Stop with Ctrl-C.

- [ ] **Step 8: Verify `ping` over HTTP** (server running in another shell)

Run: `cd mcp && python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8765/mcp', timeout=5).status)"`
Expected: an HTTP status (e.g. `400`/`406` for a non-MCP GET is fine — it proves the endpoint is mounted; a `ConnectionRefused` would mean failure).

- [ ] **Step 9: Commit**

```bash
git add mcp/mcp_app.py mcp/server.py mcp/tools/__init__.py mcp/lib/__init__.py mcp/requirements.txt mcp/.gitignore mcp/conftest.py
git commit -m "feat(mcp): single-endpoint FastMCP skeleton with ping"
```

---

## Task 2: Docker packaging + `.env.example`

**Files:**
- Create: `mcp/Dockerfile`, `mcp/docker-compose.yaml`, `mcp/.env.example`

- [ ] **Step 1: Create `mcp/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8765
CMD ["python", "server.py"]
```

- [ ] **Step 2: Create `mcp/docker-compose.yaml`**

```yaml
services:
  ravimus-mcp:
    build: .
    ports:
      - "8765:8765"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

- [ ] **Step 3: Create `mcp/.env.example`** (placeholders only — never real secrets)

```bash
# --- Platform ---
MCP_SERVER_NAME=Ravimus MCP
MCP_PORT=8765
LOG_LEVEL=INFO
# Live-safety switch. 1 = log writes but do not perform them. Default ON.
DRY_RUN=1

# --- Pipedrive ---
PIPEDRIVE_API_TOKEN=
PIPEDRIVE_DOMAIN=nanordica.pipedrive.com

# --- MS Graph (app-only) ---
GRAPH_TENANT_ID=
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
GRAPH_SENDER=ravimus@nanordica.com
GRAPH_DELTA_PATH=./data/graph_delta.json

# --- Wix ---
WIX_API_KEY=
WIX_SITE_ID=
WIX_ACCOUNT_ID=
```

- [ ] **Step 4: Verify the compose file builds**

Run: `cd mcp && cp .env.example .env && docker compose build`
Expected: build succeeds (image built). (You may skip if Docker is unavailable; the server runs fine via `python server.py`.)

- [ ] **Step 5: Commit**

```bash
git add mcp/Dockerfile mcp/docker-compose.yaml mcp/.env.example
git commit -m "feat(mcp): Docker packaging and .env.example"
```

---

## Task 3: `lib/dryrun.py` — the write switch (TDD)

**Files:**
- Create: `mcp/lib/dryrun.py`, `mcp/tests/test_dryrun.py`

- [ ] **Step 1: Write the failing test — `mcp/tests/test_dryrun.py`**

```python
from lib import dryrun


def test_dry_run_on_by_default(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    assert dryrun.is_dry_run() is True


def test_dry_run_off_when_zero(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "0")
    assert dryrun.is_dry_run() is False


def test_dry_run_on_when_one(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    assert dryrun.is_dry_run() is True


def test_dry_log_returns_marker():
    out = dryrun.dry_log("send_mail", to="a@b.c", subject="x")
    assert out["dry_run"] is True
    assert out["action"] == "send_mail"
    assert out["details"]["to"] == "a@b.c"
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd mcp && python -m pytest tests/test_dryrun.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'lib.dryrun'`).

- [ ] **Step 3: Implement `mcp/lib/dryrun.py`**

```python
"""Global DRY_RUN switch. When on, write tools log intent and skip the API."""
import os
import json
import logging

logger = logging.getLogger("ravimus.dryrun")


def is_dry_run() -> bool:
    """True unless DRY_RUN is explicitly 0/false/empty. Defaults to ON."""
    return os.getenv("DRY_RUN", "1").strip().lower() not in ("0", "false", "")


def dry_log(action: str, **details) -> dict:
    """Log a would-be write and return a simulated-success marker."""
    logger.info("DRY_RUN %s %s", action,
                json.dumps(details, ensure_ascii=False, default=str))
    return {"dry_run": True, "action": action, "details": details}
```

- [ ] **Step 4: Run tests — expect pass**

Run: `cd mcp && python -m pytest tests/test_dryrun.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add mcp/lib/dryrun.py mcp/tests/test_dryrun.py
git commit -m "feat(mcp): DRY_RUN switch with tests"
```

---

## Task 4: Pipedrive constants + `lib/field_map.py` (TDD)

**Files:**
- Create: `mcp/lib/constants.py`, `mcp/lib/field_map.py`, `mcp/tests/test_field_map.py`

- [ ] **Step 1: Create `mcp/lib/constants.py`**

```python
"""Pipeline shape for the Ravimus Latvia-vets pipeline (single source of truth
for the setup script). Field types are deliberately varchar/text/double — no
enums — to avoid Pipedrive option-ID indirection."""

PIPELINE_NAME = "ravimus-latvia-vets"

# Ordered stage names (order_nr = index + 1).
STAGES = [
    "Discovered",
    "Enriched",
    "Qualified",
    "Contacted",
    "Engaged",
    "Naidis tellitud",
    "Won",
    "Lost",
]

# Deal custom fields: (friendly_name, pipedrive_field_type).
# Allowed-value vocab is documented here but not enforced by Pipedrive.
CUSTOM_FIELDS = [
    ("registry_id", "varchar"),       # registry unique id (dedup)
    ("email", "varchar"),             # registry email
    ("clinic", "text"),               # clinic name/location/type
    ("specialization", "text"),       # animals / specialty
    ("network", "text"),              # links to other registry vets
    ("decision_style", "varchar"),    # facts/results/innovation/peers/welfare/business
    ("score", "double"),              # 0-100 qualification score
    ("ab_variant", "varchar"),        # "A" | "B"
    ("personal_link", "varchar"),     # personal Wix link
    ("discount_code", "varchar"),     # personal coupon code
    ("sample_claimed_at", "varchar"), # ISO-8601 UTC
    ("emails_sent", "double"),        # count, max 5
    ("last_contact_at", "varchar"),   # ISO-8601 UTC
    ("lost_reason", "varchar"),       # opt-out|bounce|said-no|unqualified|no-reply
]
```

- [ ] **Step 2: Write the failing test — `mcp/tests/test_field_map.py`**

```python
import json
from lib import field_map


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    data = {"pipeline_id": 7,
            "stage_ids": {"Discovered": 1, "Lost": 8},
            "field_keys": {"score": "abc123", "email": "def456"}}
    field_map.save_field_map(data)
    assert field_map.load_field_map() == data


def test_resolve_field_key(tmp_path, monkeypatch):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    field_map.save_field_map({"pipeline_id": 1, "stage_ids": {},
                              "field_keys": {"score": "hash_score"}})
    assert field_map.resolve_field_key("score") == "hash_score"


def test_translate_friendly_fields(tmp_path, monkeypatch):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    field_map.save_field_map({"pipeline_id": 1, "stage_ids": {},
                              "field_keys": {"score": "h1", "email": "h2"}})
    out = field_map.to_pipedrive_fields({"score": 80, "email": "x@y.z"})
    assert out == {"h1": 80, "h2": "x@y.z"}


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELD_MAP_PATH", str(tmp_path / "nope.json"))
    assert field_map.load_field_map() == {"pipeline_id": None, "stage_ids": {}, "field_keys": {}}
```

- [ ] **Step 3: Run it — expect failure**

Run: `cd mcp && python -m pytest tests/test_field_map.py -v`
Expected: FAIL (`No module named 'lib.field_map'`).

- [ ] **Step 4: Implement `mcp/lib/field_map.py`**

```python
"""Persisted map of friendly names -> Pipedrive hashed field keys and stage ids.
Written by scripts/pipedrive_setup.py, read by tools and guardrails."""
import os
import json
from pathlib import Path

_EMPTY = {"pipeline_id": None, "stage_ids": {}, "field_keys": {}}


def _path() -> Path:
    return Path(os.getenv("FIELD_MAP_PATH", "./data/field_keys.json"))


def load_field_map() -> dict:
    p = _path()
    if not p.exists():
        return dict(_EMPTY)
    return json.loads(p.read_text(encoding="utf-8"))


def save_field_map(data: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_field_key(name: str) -> str | None:
    return load_field_map().get("field_keys", {}).get(name)


def resolve_stage_id(name: str) -> int | None:
    return load_field_map().get("stage_ids", {}).get(name)


def to_pipedrive_fields(friendly: dict) -> dict:
    """Translate {friendly_name: value} -> {hashed_key: value}. Unknown names
    pass through unchanged (already a hashed key or a standard field)."""
    keys = load_field_map().get("field_keys", {})
    return {keys.get(k, k): v for k, v in friendly.items()}
```

- [ ] **Step 5: Run tests — expect pass**

Run: `cd mcp && python -m pytest tests/test_field_map.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add mcp/lib/constants.py mcp/lib/field_map.py mcp/tests/test_field_map.py
git commit -m "feat(mcp): pipeline constants and field-key map with tests"
```

---

## Task 5: `lib/pipedrive_client.py` — HTTP core (URL/cred unit test + smoke)

**Files:**
- Create: `mcp/lib/pipedrive_client.py`, `mcp/tests/test_pipedrive_url.py`

- [ ] **Step 1: Write the failing test — `mcp/tests/test_pipedrive_url.py`**

```python
from lib import pipedrive_client as pc


def test_base_url_full_domain():
    assert pc._build_base("nanordica.pipedrive.com") == "https://nanordica.pipedrive.com/v1"


def test_base_url_short_domain():
    assert pc._build_base("nanordica") == "https://nanordica.pipedrive.com/v1"


def test_missing_token_errors(monkeypatch):
    monkeypatch.delenv("PIPEDRIVE_API_TOKEN", raising=False)
    monkeypatch.setenv("PIPEDRIVE_DOMAIN", "nanordica.pipedrive.com")
    out = pc.get("deals/1")
    assert "error" in out and "PIPEDRIVE_API_TOKEN" in out["error"]
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd mcp && python -m pytest tests/test_pipedrive_url.py -v`
Expected: FAIL (`No module named 'lib.pipedrive_client'`).

- [ ] **Step 3: Implement `mcp/lib/pipedrive_client.py`**

```python
"""Pipedrive v1 client. Read + narrow write + admin create_* (for setup).
Credentials from PIPEDRIVE_API_TOKEN / PIPEDRIVE_DOMAIN env vars.
Every response dict carries `_rate_limit` when the API provides it."""
import os
import json
import urllib.request
import urllib.parse
import urllib.error

_RATE_HEADERS = [
    ("x-ratelimit-limit", "limit"),
    ("x-ratelimit-remaining", "remaining"),
    ("x-ratelimit-reset", "reset"),
    ("x-daily-requests-left", "daily_requests_left"),
]


def _creds() -> tuple[str, str]:
    return os.getenv("PIPEDRIVE_API_TOKEN", ""), os.getenv("PIPEDRIVE_DOMAIN", "")


def _build_base(domain: str) -> str:
    if not domain:
        return ""
    if "." not in domain:
        return f"https://{domain}.pipedrive.com/v1"
    return f"https://{domain}/v1"


def _rate(headers) -> dict:
    info = {}
    for h, k in _RATE_HEADERS:
        v = headers.get(h)
        if v is not None:
            try:
                info[k] = int(v)
            except ValueError:
                info[k] = v
    return info


def _request(method: str, path: str, params: dict | None = None,
             body: dict | None = None) -> dict:
    token, domain = _creds()
    if not token:
        return {"error": "PIPEDRIVE_API_TOKEN not set"}
    if not domain:
        return {"error": "PIPEDRIVE_DOMAIN not set"}
    base = _build_base(domain)
    p = {"api_token": token}
    if params:
        p.update({k: v for k, v in params.items() if v is not None})
    url = f"{base}/{path}?{urllib.parse.urlencode(p, doseq=True)}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "ravimus-mcp/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read().decode())
            if isinstance(out, dict):
                out["_rate_limit"] = _rate(resp.headers)
            return out
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.readable() else ""
        rl = _rate(e.headers)
        if e.code == 429:
            return {"error": "Rate limit exceeded",
                    "retry_after_seconds": rl.get("reset"), "_rate_limit": rl}
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": detail, "_rate_limit": rl}
    except Exception as e:
        return {"error": str(e)}


def get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params)


def post(path: str, body: dict) -> dict:
    return _request("POST", path, body=body)


def put(path: str, body: dict) -> dict:
    return _request("PUT", path, body=body)
```

- [ ] **Step 4: Run tests — expect pass**

Run: `cd mcp && python -m pytest tests/test_pipedrive_url.py -v`
Expected: 3 passed.

- [ ] **Step 5: Smoke-test live reads** (requires real `.env`)

Run: `cd mcp && python -c "import os; os.environ.setdefault('DRY_RUN','1'); from lib import pipedrive_client as pc; print(pc.get('pipelines').get('success'))"`
(Load `.env` first, e.g. `set -a; . ./.env; set +a` on bash.)
Expected: `True` (token + domain valid). If `error`, fix `.env` before continuing.

- [ ] **Step 6: Commit**

```bash
git add mcp/lib/pipedrive_client.py mcp/tests/test_pipedrive_url.py
git commit -m "feat(mcp): Pipedrive v1 HTTP client"
```

---

## Task 6: Pipedrive read tools

**Files:**
- Create: `mcp/tools/pipedrive_deals.py`, `mcp/tools/pipedrive_persons.py`, `mcp/tools/pipedrive_fields.py`

- [ ] **Step 1: Create `mcp/tools/pipedrive_fields.py`**

```python
"""Read-only Pipedrive field definitions and config diagnostics."""
import os
from mcp_app import mcp
from lib import pipedrive_client as pc


@mcp.tool
def pipedrive_check_config() -> dict:
    """Report whether Pipedrive token and domain are set (no API call)."""
    return {"token_set": bool(os.getenv("PIPEDRIVE_API_TOKEN")),
            "domain": os.getenv("PIPEDRIVE_DOMAIN", "")}


@mcp.tool
def pipedrive_get_deal_fields() -> dict:
    """All deal field definitions, including custom-field keys."""
    return pc.get("dealFields", {"limit": 500})


@mcp.tool
def pipedrive_get_person_fields() -> dict:
    """All person field definitions, including custom-field keys."""
    return pc.get("personFields", {"limit": 500})
```

- [ ] **Step 2: Create `mcp/tools/pipedrive_deals.py` (read tools only for now)**

```python
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
```

- [ ] **Step 3: Create `mcp/tools/pipedrive_persons.py` (read tool only for now)**

```python
"""Pipedrive person tools."""
from mcp_app import mcp
from lib import pipedrive_client as pc


@mcp.tool
def pipedrive_search_persons(term: str, fields: str = "email") -> dict:
    """Search persons by term in the given fields (default email).
    Used to bind an inbound email or order to its deal."""
    return pc.get("persons/search", {"term": term, "fields": fields})
```

- [ ] **Step 4: Verify the modules import and register**

Run: `cd mcp && python -c "import server; server.load_tools(); print('ok')"`
Expected: log lines `Loaded tool module: tools.pipedrive_deals` (and persons, fields), then `ok`, no errors.

- [ ] **Step 5: Smoke-test a read tool** (real `.env` loaded)

Run: `cd mcp && python -c "from lib import pipedrive_client as pc; r=pc.get('dealFields',{'limit':1}); print(r.get('success'))"`
Expected: `True`.

- [ ] **Step 6: Commit**

```bash
git add mcp/tools/pipedrive_deals.py mcp/tools/pipedrive_persons.py mcp/tools/pipedrive_fields.py
git commit -m "feat(mcp): Pipedrive read tools (deals, persons, fields, config)"
```

---

## Task 7: Pipedrive write tools (DRY_RUN-guarded)

**Files:**
- Modify: `mcp/tools/pipedrive_deals.py`, `mcp/tools/pipedrive_persons.py`

- [ ] **Step 1: Append write tools to `mcp/tools/pipedrive_persons.py`**

```python
from lib.dryrun import is_dry_run, dry_log
from lib.field_map import to_pipedrive_fields


@mcp.tool
def pipedrive_create_person(name: str, email: str,
                            custom_fields: dict | None = None) -> dict:
    """Create a person with primary email and optional custom fields
    (keyed by friendly name, translated to Pipedrive keys)."""
    body = {"name": name, "email": [{"value": email, "primary": True}]}
    if custom_fields:
        body.update(to_pipedrive_fields(custom_fields))
    if is_dry_run():
        return dry_log("pipedrive_create_person", body=body)
    return pc.post("persons", body)


@mcp.tool
def pipedrive_update_person(person_id: int, fields: dict) -> dict:
    """Update a person's fields (friendly names allowed)."""
    body = to_pipedrive_fields(fields)
    if is_dry_run():
        return dry_log("pipedrive_update_person", person_id=person_id, body=body)
    return pc.put(f"persons/{person_id}", body)
```

- [ ] **Step 2: Append write tools to `mcp/tools/pipedrive_deals.py`**

```python
from lib.dryrun import is_dry_run, dry_log
from lib.field_map import to_pipedrive_fields, resolve_stage_id


@mcp.tool
def pipedrive_create_deal(person_id: int, title: str, stage_id: int,
                          custom_fields: dict | None = None) -> dict:
    """Create a deal for a person in a given stage, with optional custom fields."""
    body = {"person_id": person_id, "title": title, "stage_id": stage_id}
    if custom_fields:
        body.update(to_pipedrive_fields(custom_fields))
    if is_dry_run():
        return dry_log("pipedrive_create_deal", body=body)
    return pc.post("deals", body)


@mcp.tool
def pipedrive_update_deal_fields(deal_id: int, fields: dict) -> dict:
    """Update a deal's fields (friendly names allowed): score, ab_variant,
    emails_sent, last_contact_at, lost_reason, etc."""
    body = to_pipedrive_fields(fields)
    if is_dry_run():
        return dry_log("pipedrive_update_deal_fields", deal_id=deal_id, body=body)
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
```

- [ ] **Step 2b: Add the missing import for `os` is not needed; verify imports load**

Run: `cd mcp && python -c "import server; server.load_tools(); print('ok')"`
Expected: `ok`, no ImportError.

- [ ] **Step 3: Smoke-test a write under DRY_RUN**

Run: `cd mcp && DRY_RUN=1 python -c "from tools.pipedrive_deals import *; print(pipedrive_add_note.fn(1,'hi'))"`
Expected: `{'dry_run': True, 'action': 'pipedrive_add_note', ...}` — nothing written.
(Note: `.fn` calls the underlying function past the FastMCP wrapper.)

- [ ] **Step 4: Commit**

```bash
git add mcp/tools/pipedrive_deals.py mcp/tools/pipedrive_persons.py
git commit -m "feat(mcp): Pipedrive write tools, DRY_RUN-guarded"
```

---

## Task 8: Setup planner `lib/setup_plan.py` (pure, TDD)

**Files:**
- Create: `mcp/lib/setup_plan.py`, `mcp/tests/test_setup_plan.py`

- [ ] **Step 1: Write the failing test — `mcp/tests/test_setup_plan.py`**

```python
from lib import setup_plan
from lib.constants import STAGES, CUSTOM_FIELDS


def test_plan_creates_everything_when_empty():
    plan = setup_plan.plan_setup(
        existing_pipelines=[], existing_stages=[], existing_fields=[])
    assert plan["create_pipeline"] is True
    assert [s["name"] for s in plan["create_stages"]] == STAGES
    assert {f["name"] for f in plan["create_fields"]} == {n for n, _ in CUSTOM_FIELDS}


def test_plan_idempotent_when_all_present():
    pipelines = [{"id": 5, "name": "ravimus-latvia-vets"}]
    stages = [{"name": n, "id": i + 1, "pipeline_id": 5} for i, n in enumerate(STAGES)]
    fields = [{"name": n, "key": f"k_{n}"} for n, _ in CUSTOM_FIELDS]
    plan = setup_plan.plan_setup(pipelines, stages, fields)
    assert plan["create_pipeline"] is False
    assert plan["pipeline_id"] == 5
    assert plan["create_stages"] == []
    assert plan["create_fields"] == []


def test_plan_adds_only_missing_stage():
    pipelines = [{"id": 5, "name": "ravimus-latvia-vets"}]
    stages = [{"name": n, "id": i + 1, "pipeline_id": 5}
              for i, n in enumerate(STAGES) if n != "Lost"]
    fields = [{"name": n, "key": f"k_{n}"} for n, _ in CUSTOM_FIELDS]
    plan = setup_plan.plan_setup(pipelines, stages, fields)
    assert [s["name"] for s in plan["create_stages"]] == ["Lost"]
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd mcp && python -m pytest tests/test_setup_plan.py -v`
Expected: FAIL (`No module named 'lib.setup_plan'`).

- [ ] **Step 3: Implement `mcp/lib/setup_plan.py`**

```python
"""Pure planner: given current Pipedrive state, decide what to create.
No I/O — the script in scripts/pipedrive_setup.py performs the actions."""
from lib.constants import PIPELINE_NAME, STAGES, CUSTOM_FIELDS


def plan_setup(existing_pipelines: list, existing_stages: list,
               existing_fields: list) -> dict:
    """Return a create-plan that is idempotent against the current state.

    existing_stages/existing_fields are matched by name (case-sensitive).
    Stages are only considered if they belong to the matched pipeline_id."""
    match = next((p for p in existing_pipelines if p.get("name") == PIPELINE_NAME), None)
    pipeline_id = match["id"] if match else None

    have_stage_names = {
        s["name"] for s in existing_stages
        if pipeline_id is None or s.get("pipeline_id") == pipeline_id
    }
    create_stages = [
        {"name": name, "order_nr": i + 1}
        for i, name in enumerate(STAGES)
        if name not in have_stage_names
    ]

    have_field_names = {f["name"] for f in existing_fields}
    create_fields = [
        {"name": name, "field_type": ftype}
        for name, ftype in CUSTOM_FIELDS
        if name not in have_field_names
    ]

    return {
        "create_pipeline": match is None,
        "pipeline_id": pipeline_id,
        "create_stages": create_stages,
        "create_fields": create_fields,
    }
```

- [ ] **Step 4: Run tests — expect pass**

Run: `cd mcp && python -m pytest tests/test_setup_plan.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add mcp/lib/setup_plan.py mcp/tests/test_setup_plan.py
git commit -m "feat(mcp): idempotent setup planner with tests"
```

---

## Task 9: Setup script `scripts/pipedrive_setup.py` (executes plan, writes field map)

**Files:**
- Create: `mcp/scripts/__init__.py`, `mcp/scripts/pipedrive_setup.py`

- [ ] **Step 1: Create `mcp/scripts/__init__.py`** (empty file)

- [ ] **Step 2: Create `mcp/scripts/pipedrive_setup.py`**

```python
"""Provision the Ravimus pipeline idempotently, then persist the field/stage map.

Usage:
    cd mcp && python -m scripts.pipedrive_setup        # honours DRY_RUN
Run twice live: the second run must create nothing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import pipedrive_client as pc
from lib.constants import PIPELINE_NAME, STAGES
from lib.setup_plan import plan_setup
from lib.field_map import save_field_map
from lib.dryrun import is_dry_run


def _fetch_state():
    pipelines = pc.get("pipelines").get("data") or []
    stages = pc.get("stages", {"limit": 500}).get("data") or []
    fields = pc.get("dealFields", {"limit": 500}).get("data") or []
    return pipelines, stages, fields


def main() -> int:
    dry = is_dry_run()
    pipelines, stages, fields = _fetch_state()
    plan = plan_setup(pipelines, stages, fields)
    print(f"DRY_RUN={dry} plan: pipeline={plan['create_pipeline']} "
          f"stages={[s['name'] for s in plan['create_stages']]} "
          f"fields={[f['name'] for f in plan['create_fields']]}")

    pipeline_id = plan["pipeline_id"]
    if plan["create_pipeline"]:
        if dry:
            print(f"[dry] create pipeline {PIPELINE_NAME}")
        else:
            res = pc.post("pipelines", {"name": PIPELINE_NAME})
            pipeline_id = res.get("data", {}).get("id")
            print(f"created pipeline id={pipeline_id}")

    for s in plan["create_stages"]:
        if dry:
            print(f"[dry] create stage {s['name']}")
        elif pipeline_id is not None:
            pc.post("stages", {"name": s["name"], "pipeline_id": pipeline_id,
                               "order_nr": s["order_nr"]})
            print(f"created stage {s['name']}")

    for f in plan["create_fields"]:
        if dry:
            print(f"[dry] create field {f['name']} ({f['field_type']})")
        else:
            pc.post("dealFields", {"name": f["name"], "field_type": f["field_type"]})
            print(f"created field {f['name']}")

    if dry:
        print("[dry] skipping field-map write")
        return 0

    # Re-fetch to capture ids/keys for everything (created + pre-existing).
    pipelines, stages, fields = _fetch_state()
    pipeline_id = next((p["id"] for p in pipelines if p["name"] == PIPELINE_NAME), None)
    stage_ids = {s["name"]: s["id"] for s in stages
                 if s.get("pipeline_id") == pipeline_id and s["name"] in STAGES}
    # Match created custom fields by name -> hashed key.
    from lib.constants import CUSTOM_FIELDS
    wanted = {n for n, _ in CUSTOM_FIELDS}
    field_keys = {f["name"]: f["key"] for f in fields if f["name"] in wanted}
    save_field_map({"pipeline_id": pipeline_id, "stage_ids": stage_ids,
                    "field_keys": field_keys})
    print(f"wrote field map: pipeline={pipeline_id} "
          f"stages={len(stage_ids)} fields={len(field_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Smoke-test under DRY_RUN** (real `.env` loaded)

Run: `cd mcp && DRY_RUN=1 python -m scripts.pipedrive_setup`
Expected: prints a plan and `[dry] create ...` lines for whatever is missing; ends without writing a field map. No tracebacks.

- [ ] **Step 4: Run live once** (creates the pipeline)

Run: `cd mcp && DRY_RUN=0 python -m scripts.pipedrive_setup`
Expected: `created pipeline ...`, `created stage ...` ×8, `created field ...` ×14 (or fewer if some pre-existed), then `wrote field map: pipeline=<id> stages=8 fields=14`. Verify `mcp/data/field_keys.json` exists and is populated.

- [ ] **Step 5: Run live again — verify idempotency**

Run: `cd mcp && DRY_RUN=0 python -m scripts.pipedrive_setup`
Expected: plan shows `pipeline=False stages=[] fields=[]`; no `created ...` lines; field map re-written identically.

- [ ] **Step 6: Commit**

```bash
git add mcp/scripts/__init__.py mcp/scripts/pipedrive_setup.py
git commit -m "feat(mcp): idempotent Pipedrive provisioning script"
```

---

## Task 10: Send guardrails `lib/guardrails.py` (pure, TDD)

**Files:**
- Create: `mcp/lib/guardrails.py`, `mcp/tests/test_guardrails.py`

- [ ] **Step 1: Write the failing test — `mcp/tests/test_guardrails.py`**

```python
from datetime import datetime, timezone, timedelta
from lib import guardrails as g

NOW = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)


def _deal(email="vet@clinic.lv", last=None, sent=0, lost=None):
    return {"email": email, "last_contact_at": last,
            "emails_sent": sent, "lost_reason": lost}


def test_allows_fresh_lead():
    assert g.evaluate_send_guardrails(_deal(), "vet@clinic.lv", NOW) is None


def test_blocks_email_mismatch():
    r = g.evaluate_send_guardrails(_deal(email="a@b.c"), "other@x.y", NOW)
    assert r == "email_mismatch"


def test_blocks_optout():
    r = g.evaluate_send_guardrails(_deal(lost="opt-out"), "vet@clinic.lv", NOW)
    assert r == "opt_out"


def test_blocks_within_24h():
    last = (NOW - timedelta(hours=5)).isoformat()
    r = g.evaluate_send_guardrails(_deal(last=last), "vet@clinic.lv", NOW)
    assert r == "too_soon"


def test_allows_after_24h():
    last = (NOW - timedelta(hours=25)).isoformat()
    assert g.evaluate_send_guardrails(_deal(last=last), "vet@clinic.lv", NOW) is None


def test_blocks_at_five_sent():
    r = g.evaluate_send_guardrails(_deal(sent=5), "vet@clinic.lv", NOW)
    assert r == "max_emails"


def test_email_compare_case_insensitive():
    assert g.evaluate_send_guardrails(_deal(email="Vet@Clinic.LV"), "vet@clinic.lv", NOW) is None
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd mcp && python -m pytest tests/test_guardrails.py -v`
Expected: FAIL (`No module named 'lib.guardrails'`).

- [ ] **Step 3: Implement `mcp/lib/guardrails.py`**

```python
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


def evaluate_send_guardrails(deal: dict, to: str, now: datetime) -> str | None:
    """Return None if allowed; else a reason:
    email_mismatch | opt_out | too_soon | max_emails."""
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
```

- [ ] **Step 4: Run tests — expect pass**

Run: `cd mcp && python -m pytest tests/test_guardrails.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add mcp/lib/guardrails.py mcp/tests/test_guardrails.py
git commit -m "feat(mcp): pure send-guardrails with tests"
```

---

## Task 11: `lib/graph_client.py` — MS Graph app-only (token + send + delta)

**Files:**
- Create: `mcp/lib/graph_client.py`

> **Note:** Mail send/read require the tenant admin to grant `Mail.Send` + `Mail.Read` Application permissions and admin consent. Until then these calls return 403; develop with `DRY_RUN=1`.

- [ ] **Step 1: Create `mcp/lib/graph_client.py`**

```python
"""Microsoft Graph app-only (client-credentials) client: token, sendMail,
inbox delta read. Sender mailbox = GRAPH_SENDER."""
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


def send_mail(to: str, subject: str, body_html: str) -> dict:
    """Send mail as GRAPH_SENDER. Returns {'sent': True} or {'error': ...}."""
    sender = _env("GRAPH_SENDER")
    headers = _auth_headers()
    if headers is None:
        return get_token()  # carries the error
    msg = {"message": {"subject": subject,
                       "body": {"contentType": "HTML", "content": body_html},
                       "toRecipients": [{"emailAddress": {"address": to}}]},
           "saveToSentItems": True}
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
    if delta_path.exists():
        url = json.loads(delta_path.read_text()).get("deltaLink")
    else:
        url = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/mailFolders/{folder}/messages/delta"
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
```

- [ ] **Step 2: Smoke-test token acquisition** (real `.env`)

Run: `cd mcp && python -c "from lib import graph_client as gc; t=gc.get_token(); print('token' in t, t.get('error'))"`
Expected: `True None` (token acquired). A `False`/error means `.env` Graph values are wrong.

- [ ] **Step 3: Commit**

```bash
git add mcp/lib/graph_client.py
git commit -m "feat(mcp): MS Graph app-only client (token, send, delta read)"
```

---

## Task 12: `tools/mail.py` — guarded send + inbox + config

**Files:**
- Create: `mcp/tools/mail.py`

- [ ] **Step 1: Create `mcp/tools/mail.py`**

```python
"""Mail tools (MS Graph). mail_send enforces all guardrails from the Pipedrive
deal (single source of truth) and writes the send back to the deal."""
import os
from datetime import datetime, timezone

from mcp_app import mcp
from lib import pipedrive_client as pc
from lib import graph_client as gc
from lib.guardrails import evaluate_send_guardrails
from lib.field_map import to_pipedrive_fields, load_field_map
from lib.dryrun import is_dry_run, dry_log


def _deal_friendly(deal_id: int) -> dict | None:
    """Fetch a deal and project its custom fields back to friendly names."""
    raw = pc.get(f"deals/{deal_id}")
    data = raw.get("data")
    if not data:
        return None
    keys = load_field_map().get("field_keys", {})
    inv = {v: k for k, v in keys.items()}
    out = {}
    for k, v in data.items():
        out[inv.get(k, k)] = v
    return out


@mcp.tool
def mail_check_config() -> dict:
    """Report whether Graph credentials and sender are set (no send)."""
    return {"tenant_set": bool(os.getenv("GRAPH_TENANT_ID")),
            "client_set": bool(os.getenv("GRAPH_CLIENT_ID")),
            "secret_set": bool(os.getenv("GRAPH_CLIENT_SECRET")),
            "sender": os.getenv("GRAPH_SENDER", "")}


@mcp.tool
def mail_send(deal_id: int, to: str, subject: str, body_html: str) -> dict:
    """Send an email to a lead. Enforces, from the Pipedrive deal:
    email match, opt-out, <=1 mail/24h, <=5 mails total. On success, updates
    last_contact_at + emails_sent on the deal and logs a note."""
    deal = _deal_friendly(deal_id)
    if deal is None:
        return {"error": f"deal {deal_id} not found"}
    now = datetime.now(timezone.utc)
    refusal = evaluate_send_guardrails(deal, to, now)
    if refusal:
        return {"refused": refusal, "deal_id": deal_id}

    if is_dry_run():
        return dry_log("mail_send", deal_id=deal_id, to=to, subject=subject)

    result = gc.send_mail(to, subject, body_html)
    if "error" in result:
        return result

    # last_contact_at BEFORE the note so a note failure cannot cause a resend.
    try:
        sent = int(float(deal.get("emails_sent") or 0))
    except (TypeError, ValueError):
        sent = 0
    pc.put(f"deals/{deal_id}", to_pipedrive_fields({
        "last_contact_at": now.isoformat(), "emails_sent": sent + 1}))
    pc.post("notes", {"deal_id": deal_id,
                      "content": f"<b>Sent:</b> {subject}<br>{body_html}"})
    return {"sent": True, "deal_id": deal_id, "emails_sent": sent + 1}


@mcp.tool
def mail_list_new_messages(folder: str = "inbox") -> dict:
    """List messages received since the last call (Graph delta cursor)."""
    return gc.list_new_messages(folder)
```

- [ ] **Step 2: Verify the module loads**

Run: `cd mcp && python -c "import server; server.load_tools(); print('ok')"`
Expected: `Loaded tool module: tools.mail` and `ok`.

- [ ] **Step 3: Smoke-test config + a refusal path** (real `.env`, DRY_RUN=1)

Run: `cd mcp && DRY_RUN=1 python -c "from tools.mail import mail_check_config; print(mail_check_config.fn())"`
Expected: dict with `tenant_set/client_set/secret_set` all `True`, sender `ravimus@nanordica.com`.

- [ ] **Step 4: Commit**

```bash
git add mcp/tools/mail.py
git commit -m "feat(mcp): mail tools with Pipedrive-sourced guardrails"
```

---

## Task 13: `lib/wix_client.py` — orders + coupons

**Files:**
- Create: `mcp/lib/wix_client.py`

> **Note:** Wix auth uses a **raw** `Authorization` header (no `Bearer`) plus `wix-account-id` / `wix-site-id`. Confirm exact request/response shapes against Wix docs (eCommerce Orders search, Coupons v2) at execution time via context7 if a call 4xxs.

- [ ] **Step 1: Create `mcp/lib/wix_client.py`**

```python
"""Wix client: list orders, create coupon, check coupon usage.
Auth: raw Authorization header (no Bearer) + wix-account-id + wix-site-id."""
import os
import json
import urllib.request
import urllib.error

_BASE = "https://www.wixapis.com"


def _headers() -> dict | None:
    key, acct, site = (os.getenv("WIX_API_KEY"), os.getenv("WIX_ACCOUNT_ID"),
                       os.getenv("WIX_SITE_ID"))
    if not (key and acct and site):
        return None
    return {"Authorization": key, "wix-account-id": acct, "wix-site-id": site,
            "Content-Type": "application/json"}


def _call(method: str, path: str, body: dict | None = None) -> dict:
    headers = _headers()
    if headers is None:
        return {"error": "WIX_API_KEY/ACCOUNT_ID/SITE_ID not all set"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{_BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Wix HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def list_orders(since: str | None = None, limit: int = 50) -> dict:
    """Search eCommerce orders, newest first. `since` is an ISO-8601 string
    filtering on createdDate >= since."""
    query = {"cursorPaging": {"limit": limit},
             "sort": [{"fieldName": "createdDate", "order": "DESC"}]}
    if since:
        query["filter"] = {"createdDate": {"$gte": since}}
    return _call("POST", "/ecom/v1/orders/search", {"search": query})


def create_coupon(name: str, code: str, percent_off: int = 100,
                  usage_limit: int = 1) -> dict:
    """Create a coupon. Default = 100% off, single-use (free sample coupon)."""
    coupon = {"name": name, "code": code, "percentOffRate": percent_off,
              "usageLimit": usage_limit, "active": True,
              "scope": {"namespace": "stores"}}
    return _call("POST", "/coupons/v2/coupons", {"specification": coupon})


def check_coupon_usage(code: str) -> dict:
    """Find a coupon by code and return its usage count + active flag."""
    res = _call("POST", "/coupons/v2/coupons/query",
                {"query": {"filter": {"code": code}}})
    if "error" in res:
        return res
    coupons = res.get("coupons", [])
    if not coupons:
        return {"found": False, "code": code}
    c = coupons[0]
    return {"found": True, "code": code, "id": c.get("id"),
            "number_of_usages": c.get("numberOfUsages", 0), "active": c.get("active")}
```

- [ ] **Step 2: Smoke-test orders read** (real `.env`)

Run: `cd mcp && python -c "from lib import wix_client as w; r=w.list_orders(limit=1); print('error' in r and r.get('error') or 'OK orders:', list(r)[:3])"`
Expected: either an `OK orders:` line with response keys, or a clear `Wix HTTP 4xx` to fix scopes. (Confirm the API key has *Read Orders*.)

- [ ] **Step 3: Commit**

```bash
git add mcp/lib/wix_client.py
git commit -m "feat(mcp): Wix client (orders, coupons)"
```

---

## Task 14: `tools/wix.py` — wrappers (DRY_RUN on create)

**Files:**
- Create: `mcp/tools/wix.py`

- [ ] **Step 1: Create `mcp/tools/wix.py`**

```python
"""Wix tools: poll orders, create personal coupons, check coupon usage."""
import os
from mcp_app import mcp
from lib import wix_client as w
from lib.dryrun import is_dry_run, dry_log


@mcp.tool
def wix_check_config() -> dict:
    """Report whether Wix key, account, and site are set (no API call)."""
    return {"key_set": bool(os.getenv("WIX_API_KEY")),
            "account_set": bool(os.getenv("WIX_ACCOUNT_ID")),
            "site_set": bool(os.getenv("WIX_SITE_ID"))}


@mcp.tool
def wix_list_orders(since: str | None = None, limit: int = 50) -> dict:
    """List recent store orders, optionally created on/after `since` (ISO-8601)."""
    return w.list_orders(since, limit)


@mcp.tool
def wix_create_coupon(name: str, code: str, percent_off: int = 100,
                      usage_limit: int = 1) -> dict:
    """Create a personal coupon (default 100% off, single-use sample coupon)."""
    if is_dry_run():
        return dry_log("wix_create_coupon", name=name, code=code,
                       percent_off=percent_off, usage_limit=usage_limit)
    return w.create_coupon(name, code, percent_off, usage_limit)


@mcp.tool
def wix_check_coupon_usage(code: str) -> dict:
    """Check how many times a coupon code has been used."""
    return w.check_coupon_usage(code)
```

- [ ] **Step 2: Verify module loads**

Run: `cd mcp && python -c "import server; server.load_tools(); print('ok')"`
Expected: `Loaded tool module: tools.wix` and `ok`.

- [ ] **Step 3: Smoke-test coupon create under DRY_RUN**

Run: `cd mcp && DRY_RUN=1 python -c "from tools.wix import wix_create_coupon; print(wix_create_coupon.fn('Sample','TEST100'))"`
Expected: `{'dry_run': True, 'action': 'wix_create_coupon', ...}` — nothing created.

- [ ] **Step 4: Commit**

```bash
git add mcp/tools/wix.py
git commit -m "feat(mcp): Wix tools, DRY_RUN-guarded coupon create"
```

---

## Task 15: `.mcp.json` registration + README + final verification

**Files:**
- Create: `.mcp.json` (repo root), `mcp/README.md`

- [ ] **Step 1: Create repo-root `.mcp.json`**

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

- [ ] **Step 2: Create `mcp/README.md`**

````markdown
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
DRY_RUN=1 python -m scripts.pipedrive_setup   # preview
DRY_RUN=0 python -m scripts.pipedrive_setup   # create pipeline + stages + fields
```

Writes `data/field_keys.json` (friendly-name -> Pipedrive key + stage ids),
used by every tool. Re-running creates nothing (idempotent).

## Tools

| Prefix | Tools |
|---|---|
| `pipedrive_` | get_deal, list_deals, search_persons, get_deal_fields, get_person_fields, create_person, update_person, create_deal, update_deal_fields, move_deal_stage, add_note, check_config |
| `mail_` | send, list_new_messages, check_config |
| `wix_` | list_orders, create_coupon, check_coupon_usage, check_config |

## Guardrails (enforced in code, read from the Pipedrive deal)

`mail_send` refuses when: recipient != deal email, `lost_reason == opt-out`,
`last_contact_at < 24h` ago, or `emails_sent >= 5`. On success it writes
`last_contact_at` + `emails_sent` back and logs a note.

## DRY_RUN

`DRY_RUN=1` (default) logs every write and skips the API. `DRY_RUN=0` goes
live. Reads always execute.

## .env

See `.env.example`. Secrets (`*_TOKEN`, `*_SECRET`, `*_API_KEY`) live only in
the gitignored `.env`.
````

- [ ] **Step 3: Run the full test suite**

Run: `cd mcp && python -m pytest -v`
Expected: all tests pass (dryrun 4, field_map 4, pipedrive_url 3, setup_plan 3, guardrails 7).

- [ ] **Step 4: Full DRY_RUN smoke across all three systems** (real `.env`, server not required)

Run:
```bash
cd mcp && DRY_RUN=1 python -c "
from tools.pipedrive_fields import pipedrive_check_config
from tools.mail import mail_check_config
from tools.wix import wix_check_config
print('pipedrive', pipedrive_check_config.fn())
print('mail', mail_check_config.fn())
print('wix', wix_check_config.fn())
"
```
Expected: all three configs show their secrets set (`True`) and identifiers populated.

- [ ] **Step 5: Verify Claude Code sees the server**

Run: `claude mcp list` (from repo root)
Expected: `ravimus` listed and reachable. (Start `python server.py` first.)

- [ ] **Step 6: Commit**

```bash
git add .mcp.json mcp/README.md
git commit -m "feat(mcp): register server in .mcp.json and document"
```

---

## Self-review notes (planner)

- **Spec coverage:** platform skeleton (T1-2) · DRY_RUN (T3) · field map (T4) · Pipedrive client/read/write (T5-7) · setup script with idempotency (T8-9) · mail guardrails reading Pipedrive + post-send write (T10-12) · Wix orders/coupons (T13-14) · `.mcp.json` + README + smoke (T15). All spec sections map to a task.
- **Out of scope (spec open points):** Graph admin consent (tenant admin action — see plan note in T11); the discovery script (`scripts/discovery.py`) reusing `lib/pipedrive_client.py` is a separate work package; syncing the parent design doc's transport line.
- **Type consistency:** `to_pipedrive_fields` / `resolve_stage_id` / `resolve_field_key` (field_map) used identically in T6-7, T9, T12. `evaluate_send_guardrails(deal, to, now)` signature consistent T10/T12. `pc.get/post/put` consistent across all Pipedrive callers.
- **Known risk:** exact Wix request/response shapes (orders search, coupons query) may need adjustment against live docs — flagged inline in T13; the `check_config` + DRY_RUN paths are unaffected.
```
