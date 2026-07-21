"""Wix client: list orders, create coupon, check coupon usage.
Auth: raw Authorization header (no Bearer) + wix-site-id. Orders, Stores, and
Coupons are all site-level resources, so only wix-site-id is sent; including
wix-account-id alongside it triggers a METASITE_AND_ACCOUNT_MISMATCH error."""
import os
import json
import time
import urllib.request
import urllib.error

_BASE = "https://www.wixapis.com"


def _headers() -> dict | None:
    key, acct, site = (os.getenv("WIX_API_KEY"), os.getenv("WIX_ACCOUNT_ID"),
                       os.getenv("WIX_SITE_ID"))
    if not (key and acct and site):
        return None
    return {"Authorization": key, "wix-site-id": site,
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
    """Create a coupon. Default = 100% off, single-use (free sample coupon).
    Wix requires `startTime` as epoch milliseconds (a number), not an ISO string."""
    coupon = {"name": name, "code": code, "percentOffRate": percent_off,
              "usageLimit": usage_limit, "active": True,
              "startTime": int(time.time() * 1000),
              "scope": {"namespace": "stores"}}
    return _call("POST", "/stores/v2/coupons", {"specification": coupon})


def get_click_events(utm_content: str | None = None, since: str | None = None,
                     limit: int = 100) -> dict:
    """Query the `clickEvents` Wix Data collection (written by the masterPage.js
    Velo snippet on nanordica.com). `utm_content` filters to one hash exactly;
    `since` is ISO-8601 filtering on _createdDate >= since. Returns
    {"events": [...], "count": N} with snake_case fields, newest first."""
    query: dict = {"sort": [{"fieldName": "_createdDate", "order": "DESC"}],
                   "paging": {"limit": limit}}
    flt: dict = {}
    if utm_content:
        flt["utmContent"] = utm_content
    if since:
        # Date operands must be wrapped as {"$date": ...} — a bare ISO string
        # compares as a string against the date-typed column and matches nothing.
        flt["_createdDate"] = {"$gte": {"$date": since}}
    if flt:
        query["filter"] = flt
    res = _call("POST", "/wix-data/v2/items/query",
                {"dataCollectionId": "clickEvents", "query": query})
    if "error" in res:
        return res
    events = []
    for item in res.get("dataItems", []):
        d = item.get("data", {})
        created = d.get("_createdDate")
        events.append({
            "utm_content": d.get("utmContent"),
            "utm_source": d.get("utmSource"),
            "utm_medium": d.get("utmMedium"),
            "utm_campaign": d.get("utmCampaign"),
            "page_path": d.get("pagePath"),
            "referrer": d.get("referrer"),
            "clicked_at": created.get("$date") if isinstance(created, dict) else created,
        })
    return {"events": events, "count": len(events)}


def check_coupon_usage(code: str) -> dict:
    """Find a coupon by code and return its usage count + active flag.
    Wix Coupons v2 wants the filter as a JSON-encoded string and nests the
    coupon body under `specification`; usage count + id sit at the top level."""
    res = _call("POST", "/stores/v2/coupons/query",
                {"query": {"filter": json.dumps({"code": code})}})
    if "error" in res:
        return res
    coupons = res.get("coupons", [])
    if not coupons:
        return {"found": False, "code": code}
    c = coupons[0]
    spec = c.get("specification", {})
    return {"found": True, "code": code, "id": c.get("id"),
            "number_of_usages": c.get("numberOfUsages", 0),
            "active": spec.get("active")}
