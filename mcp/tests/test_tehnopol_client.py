"""tehnopol_client: slot maths + the zero-total booking gate. All HTTP is
faked at the module boundary — no network in tests."""
import pytest

from lib import tehnopol_client as tc


BOOKED = [{"start": "10:00", "end": "13:00"}]


# --- slot maths -------------------------------------------------------------

def test_is_free_detects_overlap():
    assert not tc.is_free(BOOKED, "12:00", "13:00")   # inside
    assert not tc.is_free(BOOKED, "09:30", "10:30")   # straddles start
    assert not tc.is_free(BOOKED, "12:30", "14:00")   # straddles end
    assert tc.is_free(BOOKED, "13:00", "14:00")       # touches end: free
    assert tc.is_free(BOOKED, "09:00", "10:00")       # touches start: free


def test_free_slots_skips_booked_window():
    slots = tc.free_slots(BOOKED, duration_min=60)
    starts = [s["start"] for s in slots]
    assert "09:00" in starts and "13:00" in starts
    assert not any("10:00" <= s < "13:00" for s in starts)
    assert slots[-1]["end"] == "21:00"  # closing hour respected


def test_free_slots_duration_respected():
    assert all(tc._mins(s["end"]) - tc._mins(s["start"]) == 90
               for s in tc.free_slots([], duration_min=90))


def test_room_catalog_lookup():
    assert tc.room_by_slug("swedbank")["capacity"] == 7
    assert tc.room_by_slug("puudub") is None


# --- booking gate -----------------------------------------------------------

class FakeSession:
    """Stands in for tehnopol_client.Session in book_room."""
    instances = []

    def __init__(self):
        FakeSession.instances.append(self)
        self.nonce = "n"


def _patch(monkeypatch, *, total_minor=0, day=None, order=None):
    monkeypatch.setattr(tc, "Session", FakeSession)
    monkeypatch.setattr(tc, "open_room", lambda s, slug: {
        "slug": slug, "product_id": "1", "title": "Investor Lounge",
        "capacity": 10})
    monkeypatch.setattr(tc, "apply_coupon", lambda s, pid, code=tc.COUPON: {
        "code": "kvincubator", "is_free": True})
    monkeypatch.setattr(tc, "availability",
                        lambda s, pid, d, d2=None: {d: day or []})
    monkeypatch.setattr(tc, "add_to_cart",
                        lambda s, pid, d, st, en: {"cart_count": 1})
    monkeypatch.setattr(tc, "cart_total", lambda s: {
        "total_minor": total_minor, "currency": "EUR", "items": []})
    placed = {}

    def fake_place(s, fn, ln, em, ph="", co=""):
        placed.update(first=fn, email=em)
        return order or {"booked": True, "order_id": 4242, "status": "processing"}
    monkeypatch.setattr(tc, "place_order", fake_place)
    return placed


def test_book_room_dry_run_does_not_order(monkeypatch):
    placed = _patch(monkeypatch)
    r = tc.book_room("investorlounge", "2026-08-03", "15:00", "16:00",
                     "Mart", "Kadaja", "mart@nanordica.com", dry_run=True)
    assert r["dry_run"] is True and r["total_minor"] == 0
    assert placed == {}  # place_order never reached


def test_book_room_places_zero_total_order(monkeypatch):
    placed = _patch(monkeypatch)
    r = tc.book_room("investorlounge", "2026-08-03", "15:00", "16:00",
                     "Mart", "Kadaja", "mart@nanordica.com", dry_run=False)
    assert r["booked"] is True and r["order_id"] == 4242
    assert r["room"] == "Investor Lounge" and r["total_minor"] == 0
    assert placed["email"] == "mart@nanordica.com"


def test_book_room_refuses_nonzero_total(monkeypatch):
    placed = _patch(monkeypatch, total_minor=4200)
    r = tc.book_room("investorlounge", "2026-08-03", "15:00", "16:00",
                     "Mart", "Kadaja", "mart@nanordica.com", dry_run=False)
    assert r["error"] == "nonzero_total" and r["total_minor"] == 4200
    assert placed == {}  # never pays


def test_book_room_reports_taken_slot_with_alternatives(monkeypatch):
    _patch(monkeypatch, day=BOOKED)
    r = tc.book_room("investorlounge", "2026-08-03", "11:00", "12:00",
                     "Mart", "Kadaja", "mart@nanordica.com", dry_run=False)
    assert r["error"] == "slot_taken"
    assert any(s["start"] == "13:00" for s in r["free"])
