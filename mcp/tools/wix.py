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


@mcp.tool
def wix_get_click_events(utm_content: str | None = None, since: str | None = None,
                         limit: int = 100) -> dict:
    """List Academy-link click events (clickEvents Wix Data collection, logged by
    the site's Velo snippet). Filter by exact utm_content hash and/or `since`
    (ISO-8601, on click time). Newest first. Read-only."""
    return w.get_click_events(utm_content, since, limit)
