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
