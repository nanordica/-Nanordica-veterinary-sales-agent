"""Omniva client: parcel-machine lookup (public feed) + OMX shipment
registration, label PDF retrieval, and tracking (HTTP Basic auth).

API: modern OMX REST/JSON (https://developer.omniva.ee/), production host
https://omx.omniva.eu/api/v01/omx/. Auth = HTTP Basic from
OMNIVA_API_USERNAME/OMNIVA_API_PASSWORD; the account's partner (AXA) code
goes into request bodies as `customerCode` from OMNIVA_CUSTOMER_CODE.
Parcel machines come from the public https://www.omniva.ee/locations.json
feed (no auth, EE+LV+LT); a machine's ZIP is its id and is sent as
`receiverAddressee.address.offloadPostcode` at registration.

No public sandbox exists — DRY_RUN gates all writes until a real (cheap)
test shipment validates the request shape live."""
import os
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path

_OMX_BASE = "https://omx.omniva.eu/api/v01/omx"
_LOCATIONS_URL = "https://www.omniva.ee/locations.json"
_LOCATIONS_TTL = 24 * 3600  # feed is ~1-2 MB; cache in-process for a day
_locations_cache = {"data": None, "ts": 0.0}
_LABELS_DIR = Path(__file__).resolve().parents[2] / "cache" / "labels"


def _http_get_json(url: str) -> list | dict:
    """Plain unauthenticated GET returning parsed JSON (locations feed)."""
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Omniva HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def _headers() -> dict | None:
    user, pw = os.getenv("OMNIVA_API_USERNAME"), os.getenv("OMNIVA_API_PASSWORD")
    if not (user and pw):
        return None
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    headers = {"Authorization": f"Basic {token}",
               "Content-Type": "application/json"}
    # Optional per-docs integration id: "Developer_XXXXXX_YYYYYY".
    agent = os.getenv("OMNIVA_INTEGRATION_AGENT_ID")
    if agent:
        headers["X-Integration-Agent-Id"] = agent
    return headers


def _call(method: str, path: str, body: dict | None = None) -> dict:
    headers = _headers()
    if headers is None:
        return {"error": "OMNIVA_API_USERNAME/OMNIVA_API_PASSWORD not all set"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{_OMX_BASE}{path}", data=data,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Omniva HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def _get_locations() -> list | dict:
    now = time.time()
    if (_locations_cache["data"] is not None
            and now - _locations_cache["ts"] < _LOCATIONS_TTL):
        return _locations_cache["data"]
    data = _http_get_json(_LOCATIONS_URL)
    if isinstance(data, dict):  # error dict; don't cache
        return data
    _locations_cache["data"] = data
    _locations_cache["ts"] = now
    return data


def _address_of(row: dict) -> str:
    """Human-readable address from the feed's A1..A7 name parts."""
    street = " ".join(p for p in (row.get("A5_NAME"), row.get("A7_NAME")) if p)
    town = row.get("A3_NAME") or row.get("A2_NAME") or ""
    region = row.get("A1_NAME") or ""
    return ", ".join(p for p in (street, town, region) if p)


def list_pickup_points(country: str = "LV", query: str | None = None,
                       limit: int = 20) -> dict:
    """Search Omniva pickup points (parcel machines + post offices) by
    country and optional name/address substring. The `zip` of a point is
    the id to pass to create_shipment as pickup_point_id."""
    feed = _get_locations()
    if isinstance(feed, dict):
        return feed
    cc = country.strip().upper()
    q = query.strip().lower() if query else None
    points = []
    for row in feed:
        if row.get("A0_NAME") != cc:
            continue
        name, addr = row.get("NAME", ""), _address_of(row)
        if q and q not in name.lower() and q not in addr.lower():
            continue
        points.append({"zip": row.get("ZIP"), "name": name, "address": addr,
                       "type": "parcel_machine" if row.get("TYPE") == "0"
                       else "post_office"})
        if len(points) >= limit:
            break
    return {"points": points, "count": len(points)}


def _sender_addressee() -> dict:
    address = {"country": os.getenv("OMNIVA_SENDER_COUNTRY", "EE")}
    for env, field in (("OMNIVA_SENDER_POSTCODE", "postcode"),
                       ("OMNIVA_SENDER_DELIVERYPOINT", "deliverypoint"),
                       ("OMNIVA_SENDER_STREET", "street"),
                       ("OMNIVA_SENDER_HOUSE_NO", "houseNo")):
        val = os.getenv(env)
        if val:
            address[field] = val
    sender = {"personName": os.getenv("OMNIVA_SENDER_NAME", ""),
              "address": address}
    phone = os.getenv("OMNIVA_SENDER_PHONE")
    if phone:
        sender["contactPhone"] = phone
    email = os.getenv("OMNIVA_SENDER_EMAIL")
    if email:
        sender["contactEmail"] = email
    return sender


def create_shipment(receiver_name: str, receiver_phone: str,
                    pickup_point_id: str, receiver_email: str | None = None,
                    receiver_country: str = "LV",
                    weight_kg: float | None = None) -> dict:
    """Register a business-to-client parcel-machine shipment via OMX
    POST /shipments/business-to-client. `pickup_point_id` is the machine's
    ZIP from the locations feed (sent as address.offloadPostcode). Mobile
    phone is mandatory — Omniva sends the arrival SMS with the door code."""
    if not (receiver_phone and receiver_phone.strip()):
        return {"error": "receiver_phone is mandatory for parcel machine "
                         "delivery (arrival SMS with door code)"}
    customer_code = os.getenv("OMNIVA_CUSTOMER_CODE")
    if not (customer_code and os.getenv("OMNIVA_API_USERNAME")
            and os.getenv("OMNIVA_API_PASSWORD")):
        return {"error": "OMNIVA_CUSTOMER_CODE/OMNIVA_API_USERNAME/"
                         "OMNIVA_API_PASSWORD not all set"}
    receiver = {"personName": receiver_name,
                "contactMobile": receiver_phone,
                "address": {"country": receiver_country.strip().upper(),
                            "offloadPostcode": str(pickup_point_id)}}
    if receiver_email:
        receiver["contactEmail"] = receiver_email
    shipment = {"mainService": "PARCEL",
                "deliveryChannel": "PARCEL_MACHINE",
                "receiverAddressee": receiver,
                "senderAddressee": _sender_addressee()}
    # Per the OMX manual, measurement (incl. weight) is optional for parcels —
    # parcel-machine pricing is size-based, so only send weight when known.
    if weight_kg is not None:
        shipment["measurement"] = {"weight": weight_kg}
    body = {"customerCode": customer_code,
            "fileId": f"ravimus-{int(time.time())}",
            "shipments": [shipment]}
    res = _call("POST", "/shipments/business-to-client", body)
    if "error" in res:
        return res
    saved = res.get("savedShipments") or []
    if not saved:
        return {"error": "shipment not registered",
                "failed": res.get("failedShipments", []), "raw": res}
    return {"barcode": saved[0].get("barcode"), "saved": saved, "raw": res}


def get_label(barcode: str) -> dict:
    """Fetch the label PDF via OMX POST /shipments/package-labels
    (sendAddressCardTo=RESPONSE -> base64 fileData), save it under
    cache/labels/<barcode>.pdf and return the path (binary stays on disk)."""
    customer_code = os.getenv("OMNIVA_CUSTOMER_CODE")
    if not customer_code:
        return {"error": "OMNIVA_CUSTOMER_CODE not set"}
    # OMX deserializes barcodes into BarcodeValueDto objects — a bare string
    # array fails with an HTTP 500 JSON parse error (verified live 2026-07-28).
    res = _call("POST", "/shipments/package-labels",
                {"customerCode": customer_code,
                 "barcodes": [{"barcode": barcode}],
                 "sendAddressCardTo": "RESPONSE"})
    if "error" in res:
        return res
    cards = res.get("successAddressCards") or []
    card = next((c for c in cards if c.get("barcode") == barcode),
                cards[0] if cards else None)
    if not card or not card.get("fileData"):
        return {"error": f"no label returned for {barcode}",
                "failed": res.get("failedAddressCards", [])}
    _LABELS_DIR.mkdir(parents=True, exist_ok=True)
    path = _LABELS_DIR / f"{barcode}.pdf"
    path.write_bytes(base64.b64decode(card["fileData"]))
    return {"barcode": barcode, "path": str(path)}


def track(barcode: str) -> dict:
    """Tracking events via OMX GET /shipments/{barcode} (same Basic auth —
    OMX has no public unauthenticated tracking endpoint)."""
    res = _call("GET", f"/shipments/{barcode}")
    if "error" in res:
        return res
    events = [{"code": e.get("eventCode"), "name": e.get("eventName"),
               "date": e.get("eventDate"),
               "location": (e.get("location") or {}).get("locationName")}
              for e in res.get("events", [])]
    return {"barcode": res.get("shipmentBarcode", barcode),
            "events": events, "count": len(events)}
