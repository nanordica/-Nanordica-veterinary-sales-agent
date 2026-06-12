"""wix-mcp: kitsas MCP server Wixi poe jaoks (ravimus-lead-pipeline, wp4).

Avab AINULT kolm tööriista: tellimuste loetelu, personaalse kupongi
loomine, kupongi kasutuse kontroll. Toodete/hindade muutmist ja
tagasimakseid teadlikult EI avata (disain: tööriistakiht).

Režiim on ÜKS telg, et lugemised ja kirjutamised käiksid alati sama
salve vastu:

- **live**: WIX_API_KEY + WIX_SITE_ID olemas JA DRY_RUN=0 -> kõik
  kõned käivad päris Wixi REST API vastu.
- **mock**: võti puudub VÕI DRY_RUN=1 (vaikimisi 1, kui seadmata) ->
  kõik kõned käivad lokaalse olekufaili cache/wix-mock.json vastu;
  kirjutused logitakse lisaks faili logs/dry-run-wix.md. Nii on
  dry-run otsast lõpuni isekooskõlaline: create_coupon'iga loodud
  kupongi näeb check_coupon_usage samast salvest.

Iga vastus ütleb {"mode": "live"|"mock"}, et kutsuja teaks, kumb käis.
"""

import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# WIX_MOCK_FILE / WIX_DRY_RUN_LOG lubavad testidel kasutada
# isoleeritud faile, et päris cache/logid ei saastuks.
MOCK_STATE = Path(os.environ.get("WIX_MOCK_FILE",
                                 REPO_ROOT / "cache" / "wix-mock.json"))
DRY_RUN_LOG = Path(os.environ.get("WIX_DRY_RUN_LOG",
                                  REPO_ROOT / "logs" / "dry-run-wix.md"))
WIX_API = "https://www.wixapis.com"


def _load_dotenv() -> None:
    """Loe .env, et cron/headless jooks saaks samad võtmed kätte."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

WIX_API_KEY = os.environ.get("WIX_API_KEY", "")
WIX_SITE_ID = os.environ.get("WIX_SITE_ID", "")
# Ohutu vaikeväärtus: kui DRY_RUN on seadmata, käitume nagu DRY_RUN=1.
DRY_RUN = os.environ.get("DRY_RUN", "1") != "0"
LIVE = bool(WIX_API_KEY and WIX_SITE_ID) and not DRY_RUN

mcp = FastMCP("wix-mcp")

_client = httpx.AsyncClient(
    base_url=WIX_API,
    headers={
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    },
    timeout=30,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dt(value: str) -> datetime:
    """ISO-8601 -> datetime võrdluseks; talub 'Z' ja offset-vorme segamini."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _read_mock() -> dict:
    if MOCK_STATE.exists():
        return json.loads(MOCK_STATE.read_text())
    return {"orders": [], "coupons": {}}


def _write_mock(state: dict) -> None:
    MOCK_STATE.parent.mkdir(parents=True, exist_ok=True)
    MOCK_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def _log_dry_run(action: str, payload: dict) -> None:
    DRY_RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DRY_RUN_LOG.open("a") as f:
        f.write(f"- {_now()} **{action}** "
                f"`{json.dumps(payload, ensure_ascii=False)}`\n")


def _simplify_order(raw: dict) -> dict:
    """Wixi ecom-tellimusest sales-detectorile vajalik miinimum."""
    coupon = ""
    for discount in raw.get("appliedDiscounts") or []:
        code = (discount.get("coupon") or {}).get("code")
        if code:
            coupon = code
            break
    return {
        "order_id": raw.get("id", ""),
        "number": raw.get("number", ""),
        "created_at": raw.get("createdDate", ""),
        "buyer_email": (raw.get("buyerInfo") or {}).get("email", ""),
        "coupon_code": coupon,
        "total": ((raw.get("priceSummary") or {}).get("total")
                  or {}).get("amount", "0"),
        "currency": raw.get("currency", "EUR"),
        "line_items": [
            (li.get("productName") or {}).get("original", "")
            for li in raw.get("lineItems") or []
        ],
    }


@mcp.tool()
async def list_orders(since: str = "", limit: int = 50) -> str:
    """Loetle poe tellimused, VANIMAST uuemani (kursoritarbimiseks).

    Args:
        since: ISO-8601 ajatempel; tagasta ainult hilisemad tellimused.
            Tühi = kõik (kuni limit).
        limit: max tellimuste arv (1-100).

    Returns:
        JSON: {"mode": "live"|"mock", "has_more": bool, "orders":
        [{order_id, number, created_at, buyer_email, coupon_code,
        total, currency, line_items}]}. has_more=true tähendab, et
        partii sai täis ja hilisemaid tellimusi on veel: töötle see
        partii, liiguta kursor viimase töödeldud tellimuse peale ja
        küsi uuesti.
    """
    limit = max(1, min(limit, 100))
    if LIVE:
        body: dict = {"search": {
            "cursorPaging": {"limit": limit},
            "sort": [{"fieldName": "createdDate", "order": "ASC"}],
        }}
        if since:
            body["search"]["filter"] = {"createdDate": {"$gt": since}}
        resp = await _client.post("/ecom/v1/orders/search", json=body)
        resp.raise_for_status()
        orders = [_simplify_order(o) for o in resp.json().get("orders", [])]
        return json.dumps({"mode": "live",
                           "has_more": len(orders) >= limit,
                           "orders": orders}, ensure_ascii=False)

    state = _read_mock()
    orders = [o for o in state["orders"]
              if not since or _dt(o.get("created_at", "")) > _dt(since)]
    orders.sort(key=lambda o: _dt(o.get("created_at", "")))
    return json.dumps({"mode": "mock",
                       "has_more": len(orders) > limit,
                       "orders": orders[:limit]}, ensure_ascii=False)


@mcp.tool()
async def create_coupon(deal_id: str, percent_off: int, name: str,
                        code: str = "", expires_days: int = 30) -> str:
    """Loo personaalne protsendikupong (100% = tasuta näidis).

    Kupong on alati ühekordne (usage_limit=1) ja personaalne. Muid
    kupongitüüpe (summa, tasuta saatmine) see server ei ava.

    Args:
        deal_id: Pipedrive'i deal'i ID, kellele kupong kuulub (läheb
            kupongi nimesse, et kasutus oleks seostatav).
        percent_off: allahindlus protsentides, 1-100. 100 = näidis.
        name: kupongi sisemine nimi, nt "naidis deal 42".
        code: soovitud kood; tühi = genereeritakse RVET-<deal>-XXXX.
        expires_days: aegumiseni jäävad päevad (vaikimisi 30).

    Returns:
        JSON: {"mode", "dry_run", "code", "percent_off", "expires_at"}
    """
    if not 1 <= percent_off <= 100:
        raise ValueError("percent_off peab olema 1-100")
    if not code:
        # deal_id võib sisaldada koodile keelatud märke; puhasta enne.
        safe = re.sub(r"[^A-Za-z0-9-]", "", deal_id)[:18]
        code = f"RVET-{safe}-{secrets.token_hex(2).upper()}".replace(
            "--", "-")
    if not re.fullmatch(r"[A-Za-z0-9-]{3,30}", code):
        raise ValueError("kood: ainult tähed/numbrid/sidekriipsud, 3-30")
    expires_at = (datetime.now(timezone.utc)
                  + timedelta(days=expires_days)).isoformat(timespec="seconds")
    record = {
        "code": code, "deal_id": deal_id, "percent_off": percent_off,
        "name": name, "expires_at": expires_at, "usage_count": 0,
        "created_at": _now(),
    }

    if not LIVE:
        _log_dry_run("create_coupon", record)
        state = _read_mock()
        if code in state["coupons"]:
            raise ValueError(f"kupong {code} on juba olemas")
        state["coupons"][code] = record
        _write_mock(state)
        return json.dumps({"mode": "mock", "dry_run": DRY_RUN, **record},
                          ensure_ascii=False)

    spec = {
        "name": name,
        "code": code,
        "usageLimit": 1,
        "expirationTime": expires_at,
        "scope": {"namespace": "stores"},
        "percentOffRate": percent_off,
    }
    resp = await _client.post("/stores/v2/coupons",
                              json={"specification": spec})
    resp.raise_for_status()
    return json.dumps({"mode": "live", "dry_run": False, **record},
                      ensure_ascii=False)


@mcp.tool()
async def check_coupon_usage(code: str) -> str:
    """Kontrolli, kas personaalne kupong on lunastatud.

    Args:
        code: kupongikood.

    Returns:
        JSON: {"mode", "code", "exists", "used", "usage_count",
        "percent_off", "deal_id"} (deal_id ainult mock-režiimis).
    """
    if LIVE:
        body = {"query": {"filter": json.dumps({"code": code})}}
        resp = await _client.post("/stores/v2/coupons/query", json=body)
        resp.raise_for_status()
        coupons = resp.json().get("coupons", [])
        if not coupons:
            return json.dumps({"mode": "live", "code": code,
                               "exists": False, "used": False,
                               "usage_count": 0})
        c = coupons[0]
        usage = int(c.get("numberOfUsages", 0))
        return json.dumps({
            "mode": "live", "code": code, "exists": True,
            "used": usage > 0, "usage_count": usage,
            "percent_off": (c.get("specification") or {})
            .get("percentOffRate", ""),
        })

    state = _read_mock()
    record = state["coupons"].get(code)
    if not record:
        return json.dumps({"mode": "mock", "code": code, "exists": False,
                           "used": False, "usage_count": 0})
    usage = int(record.get("usage_count", 0))
    return json.dumps({
        "mode": "mock", "code": code, "exists": True,
        "used": usage > 0, "usage_count": usage,
        "percent_off": record["percent_off"],
        "deal_id": record["deal_id"],
    }, ensure_ascii=False)


if __name__ == "__main__":
    print(f"wix-mcp: mode={'live' if LIVE else 'mock'} dry_run={DRY_RUN}",
          file=sys.stderr)
    mcp.run()
