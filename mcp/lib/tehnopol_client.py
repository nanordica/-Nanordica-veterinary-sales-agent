"""Tehnopol seminar-room booking client — pure stdlib HTTP, no browser.

Reverse-engineered from the tehnopol.ee theme (verified live 2026-08-01);
replaces the Steel/guided-browser recipe so booking works anywhere the repo
runs. Three layers are involved:

  1. WordPress admin-ajax (theme actions): `apply_coupon`,
     `room_availability`, `room_add_to_cart`. The page's `window.ballers.nonce`
     and the room's `data-product-id` are scraped from the room page.
  2. WooCommerce Store API (`/wp-json/wc/store/v1/...`): authoritative cart
     totals and order placement (`Nonce` response header must be echoed back).
  3. Session cookies tie the three together — always reuse one `Session`.

HARD RULE mirrored from the room-booking skill: an order is only ever placed
when the cart total is exactly 0 (KVincubator makes Mäealuse 2/1 rooms free).
Any non-zero total raises/returns an error instead of paying.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar
from datetime import datetime, timedelta

BASE = "https://www.tehnopol.ee"
AJAX = BASE + "/wp-admin/admin-ajax.php"
STORE = BASE + "/wp-json/wc/store/v1"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")
COUPON = "KVincubator"
OPEN_HOUR, CLOSE_HOUR = 9, 21  # calendar grid on the room page

# Mäealuse 2/1 rooms (KVincubator applies). Preference order is decided by
# the room-booking skill; this is just the catalog.
ROOMS = [
    {"slug": "kosmos", "name": "Kosmos", "capacity": 4},
    {"slug": "prototron", "name": "Prototron", "capacity": 4},
    {"slug": "ruutu6", "name": "Ruutu6", "capacity": 4},
    {"slug": "swedbank", "name": "Swedbank", "capacity": 7},
    {"slug": "investorlounge", "name": "Investor Lounge", "capacity": 10},
    {"slug": "uk-lounge", "name": "UK Lounge", "capacity": 30},
]


def room_by_slug(slug: str) -> dict | None:
    return next((r for r in ROOMS if r["slug"] == slug), None)


class Session:
    """One cookie jar across admin-ajax + Store API calls."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.opener.addheaders = [("User-Agent", UA)]
        self.nonce = None
        self.store_nonce = None

    # --- low level ---------------------------------------------------------

    def _open(self, req, timeout=30):
        with self.opener.open(req, timeout=timeout) as r:
            nonce = r.headers.get("Nonce")
            if nonce:
                self.store_nonce = nonce
            return r.status, r.read().decode()

    def get_html(self, url: str) -> str:
        return self._open(urllib.request.Request(url))[1]

    def ajax_post(self, data: dict) -> dict:
        req = urllib.request.Request(
            AJAX, data=urllib.parse.urlencode(data).encode(),
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": BASE})
        return json.loads(self._open(req)[1])

    def ajax_get(self, params: dict) -> dict:
        req = urllib.request.Request(
            AJAX + "?" + urllib.parse.urlencode(params),
            headers={"X-Requested-With": "XMLHttpRequest"})
        return json.loads(self._open(req)[1])

    def store_get(self, path: str) -> dict:
        return json.loads(self._open(urllib.request.Request(STORE + path))[1])

    def store_post(self, path: str, payload: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.store_nonce:
            headers["Nonce"] = self.store_nonce
        req = urllib.request.Request(STORE + path,
                                     data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        return json.loads(self._open(req)[1])


# --- steps ------------------------------------------------------------------

def open_room(session: Session, slug: str) -> dict:
    """Load a room page: scrapes the ajax nonce + product id + metadata."""
    html = session.get_html(f"{BASE}/ruum/{slug}/")
    m_nonce = re.search(r'"nonce":"([a-z0-9]+)"', html)
    m_pid = re.search(r'data-product-id="(\d+)"', html)
    if not (m_nonce and m_pid):
        return {"error": f"room page {slug}: nonce/product_id not found"}
    session.nonce = m_nonce.group(1)
    title = re.search(r'data-room-title="([^"]*)"', html)
    cap = re.search(r'data-room-capacity="(\d+)"', html)
    return {"slug": slug, "product_id": m_pid.group(1),
            "title": title.group(1) if title else slug,
            "capacity": int(cap.group(1)) if cap else None}


def apply_coupon(session: Session, product_id: str,
                 code: str = COUPON) -> dict:
    """Activate the client code; unlocks the calendar and zeroes the price."""
    res = session.ajax_post({"action": "apply_coupon",
                             "_wpnonce": session.nonce,
                             "coupon_code": code, "product_id": product_id})
    if not res.get("success"):
        return {"error": f"coupon '{code}' rejected", "raw": res}
    return res.get("data", {})


def availability(session: Session, product_id: str, date_from: str,
                 date_to: str | None = None) -> dict:
    """Existing bookings per date: {'2026-08-03': [{'start','end'}, ...]}."""
    res = session.ajax_get({"action": "room_availability",
                            "product_id": product_id,
                            "date_from": date_from,
                            "date_to": date_to or date_from})
    if not res.get("success"):
        return {"error": "room_availability failed", "raw": res}
    return res.get("data", {}).get("bookings", {})


def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")[:2]
    return int(h) * 60 + int(m)


def _hhmm(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"


def free_slots(bookings: list, duration_min: int = 60,
               open_hour: int = OPEN_HOUR, close_hour: int = CLOSE_HOUR,
               step_min: int = 30) -> list:
    """Free [start, end] windows of `duration_min` inside opening hours,
    given the day's existing bookings."""
    busy = sorted((_mins(b["start"]), _mins(b["end"])) for b in bookings)
    out, cur, end_of_day = [], open_hour * 60, close_hour * 60
    while cur + duration_min <= end_of_day:
        s, e = cur, cur + duration_min
        if not any(s < be and e > bs for bs, be in busy):
            out.append({"start": _hhmm(s), "end": _hhmm(e)})
        cur += step_min
    return out


def is_free(bookings: list, start: str, end: str) -> bool:
    s, e = _mins(start), _mins(end)
    return not any(s < _mins(b["end"]) and e > _mins(b["start"])
                   for b in bookings)


def add_to_cart(session: Session, product_id: str, date: str,
                start: str, end: str) -> dict:
    res = session.ajax_post({"action": "room_add_to_cart",
                             "_wpnonce": session.nonce,
                             "product_id": product_id, "booking_date": date,
                             "booking_start_time": start,
                             "booking_end_time": end})
    if not res.get("success"):
        return {"error": "room_add_to_cart failed", "raw": res}
    return res.get("data", {})


def cart_total(session: Session) -> dict:
    """Authoritative totals from the Store API. Returns
    {'total_minor': int, 'currency': str, 'items': [...]} — total_minor 0
    is the only value the booking gate accepts."""
    cart = session.store_get("/cart")
    totals = cart.get("totals", {})
    try:
        total_minor = int(totals.get("total_price", "0"))
    except (TypeError, ValueError):
        return {"error": "cart total unreadable", "raw": totals}
    return {"total_minor": total_minor,
            "currency": totals.get("currency_code", "EUR"),
            "items": [{"name": i.get("name"),
                       "meta": [d.get("value") for d in i.get("item_data", [])]}
                      for i in cart.get("items", [])]}


# WooCommerce validates address1/city/postcode even on a free order; the
# booking has no delivery, so the company's own address is used.
BILLING_ADDRESS = {"address_1": "Mäealuse 2/1", "city": "Tallinn",
                   "postcode": "12618", "country": "EE"}


def place_order(session: Session, first_name: str, last_name: str,
                email: str, phone: str = "", company: str = "") -> dict:
    """Place the (zero-total) order via the Store API. Caller MUST have
    verified cart_total()['total_minor'] == 0 first — book_room does."""
    billing = dict(BILLING_ADDRESS) | {"first_name": first_name,
                                       "last_name": last_name, "email": email}
    if phone:
        billing["phone"] = phone
    if company:
        billing["company"] = company
    payload = {"billing_address": billing, "shipping_address": dict(billing),
               "customer_note": "", "payment_method": ""}
    try:
        res = session.store_post("/checkout", payload)
    except urllib.error.HTTPError as e:
        return {"error": f"checkout HTTP {e.code}",
                "detail": e.read().decode()[:400]}
    if res.get("order_id"):
        return {"booked": True, "order_id": res.get("order_id"),
                "status": res.get("status"),
                "order_key": res.get("order_key")}
    return {"error": "checkout returned no order_id", "raw": res}


def book_room(slug: str, date: str, start: str, end: str, first_name: str,
              last_name: str, email: str, phone: str = "",
              company: str = "", dry_run: bool = True) -> dict:
    """Full flow: open room -> coupon -> availability -> cart -> 0-total
    gate -> order. Returns a dict describing what happened; never pays."""
    s = Session()
    room = open_room(s, slug)
    if "error" in room:
        return room
    coupon = apply_coupon(s, room["product_id"])
    if "error" in coupon:
        return coupon
    books = availability(s, room["product_id"], date)
    if isinstance(books, dict) and "error" in books:
        return books
    day = books.get(date, [])
    if not is_free(day, start, end):
        return {"error": "slot_taken", "room": room["title"], "date": date,
                "start": start, "end": end, "bookings": day,
                "free": free_slots(day, _mins(end) - _mins(start))}
    added = add_to_cart(s, room["product_id"], date, start, end)
    if "error" in added:
        return added
    total = cart_total(s)
    if "error" in total:
        return total
    if total["total_minor"] != 0:
        # HARD RULE: never pay. Leave the cart; caller reports the refusal.
        return {"error": "nonzero_total", "total_minor": total["total_minor"],
                "currency": total["currency"], "room": room["title"],
                "detail": "broneering EI tehtud — summa ei ole 0,00 €"}
    if dry_run:
        return {"dry_run": True, "room": room["title"], "date": date,
                "start": start, "end": end, "total_minor": 0,
                "cart": total["items"]}
    order = place_order(s, first_name, last_name, email, phone, company)
    if "error" in order:
        return order
    return order | {"room": room["title"], "date": date, "start": start,
                    "end": end, "total_minor": 0}


def find_free_rooms(date: str, start: str, end: str,
                    min_capacity: int = 1) -> list:
    """Which Mäealuse 2/1 rooms are free for [start,end] on `date`."""
    out = []
    for r in ROOMS:
        if r["capacity"] < min_capacity:
            continue
        s = Session()
        room = open_room(s, r["slug"])
        if "error" in room:
            out.append(r | {"error": room["error"]})
            continue
        apply_coupon(s, room["product_id"])
        books = availability(s, room["product_id"], date)
        day = books.get(date, []) if isinstance(books, dict) else []
        out.append(r | {"free": is_free(day, start, end), "bookings": day})
    return out
