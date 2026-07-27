"""Omniva tools: pickup-point search, sample-shipment registration, label
PDF retrieval, tracking. Physical sample dispatch to Latvian vets."""
import os
from mcp_app import mcp
from lib import omniva_client as o
from lib.dryrun import is_dry_run, dry_log


@mcp.tool
def omniva_check_config() -> dict:
    """Report whether Omniva customer code, username, and password are set
    (no API call)."""
    return {"customer_code_set": bool(os.getenv("OMNIVA_CUSTOMER_CODE")),
            "username_set": bool(os.getenv("OMNIVA_API_USERNAME")),
            "password_set": bool(os.getenv("OMNIVA_API_PASSWORD"))}


@mcp.tool
def omniva_list_pickup_points(country: str = "LV", query: str | None = None,
                              limit: int = 20) -> dict:
    """Search Omniva pickup points (public feed, no auth). Returned `zip`
    is the pickup_point_id for omniva_create_shipment."""
    return o.list_pickup_points(country, query, limit)


@mcp.tool
def omniva_create_shipment(deal_id: int, receiver_name: str,
                           receiver_phone: str, pickup_point_id: str,
                           receiver_email: str | None = None) -> dict:
    """Register a parcel-machine sample shipment (DRY_RUN-guarded).
    `deal_id` is context for the sales layer only — Pipedrive writes happen
    elsewhere. Mobile phone is mandatory (arrival SMS with door code)."""
    if is_dry_run():
        return dry_log("omniva_create_shipment", deal_id=deal_id,
                       receiver_name=receiver_name,
                       receiver_phone=receiver_phone,
                       pickup_point_id=pickup_point_id,
                       receiver_email=receiver_email)
    return o.create_shipment(receiver_name, receiver_phone, pickup_point_id,
                             receiver_email)


@mcp.tool
def omniva_get_label(barcode: str) -> dict:
    """Fetch the shipment label PDF to cache/labels/<barcode>.pdf and return
    the path (DRY_RUN-guarded: authenticated call + local file write)."""
    if is_dry_run():
        return dry_log("omniva_get_label", barcode=barcode)
    return o.get_label(barcode)


@mcp.tool
def omniva_track(barcode: str) -> dict:
    """Tracking events for a shipment barcode (read-only)."""
    return o.track(barcode)
