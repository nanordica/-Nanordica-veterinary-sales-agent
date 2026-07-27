"""Omniva client + tool tests. All HTTP is mocked at the module boundary
(`_http_get_json` for the public locations feed, `_call` for the OMX API)."""
import base64

import pytest

from lib import omniva_client as oc


# Trimmed real rows from https://www.omniva.ee/locations.json (schema
# confirmed live 2026-07-21): ZIP is the machine id used as offloadPostcode,
# A0_NAME is the country code, TYPE "0" = parcel machine, "1" = post office.
FEED = [
    {"ZIP": "96331", "NAME": "Viru keskuse pakiautomaat", "TYPE": "0",
     "A0_NAME": "EE", "A1_NAME": "Harju maakond", "A2_NAME": "Tallinn",
     "A3_NAME": "Tallinn", "A5_NAME": "Viru väljak", "A7_NAME": "4"},
    {"ZIP": "9595", "NAME": "Aglonas TOP pakomāts", "TYPE": "0",
     "A0_NAME": "LV", "A1_NAME": "Preiļu novads", "A2_NAME": "Aglonas pagasts",
     "A3_NAME": "Aglona", "A5_NAME": "Somersētas iela", "A7_NAME": "33"},
    {"ZIP": "1010", "NAME": "Rīga Origo pakomāts", "TYPE": "0",
     "A0_NAME": "LV", "A1_NAME": "Rīga", "A3_NAME": "Rīga",
     "A5_NAME": "Stacijas laukums", "A7_NAME": "2"},
    {"ZIP": "2020", "NAME": "Rīgas pasta nodaļa", "TYPE": "1",
     "A0_NAME": "LV", "A1_NAME": "Rīga", "A3_NAME": "Rīga"},
    {"ZIP": "55555", "NAME": "Vilniaus paštomatas", "TYPE": "0",
     "A0_NAME": "LT", "A3_NAME": "Vilnius"},
]


@pytest.fixture
def feed_calls(monkeypatch):
    """Fresh cache + canned feed; returns the list of fetch invocations."""
    monkeypatch.setattr(oc, "_locations_cache", {"data": None, "ts": 0.0})
    calls = []

    def fake_get(url):
        calls.append(url)
        return [dict(r) for r in FEED]

    monkeypatch.setattr(oc, "_http_get_json", fake_get)
    return calls


@pytest.fixture
def omx_env(monkeypatch):
    monkeypatch.setenv("OMNIVA_CUSTOMER_CODE", "12345")
    monkeypatch.setenv("OMNIVA_API_USERNAME", "user")
    monkeypatch.setenv("OMNIVA_API_PASSWORD", "pass")
    monkeypatch.setenv("OMNIVA_SENDER_NAME", "Nanordica Medical OÜ")
    monkeypatch.setenv("OMNIVA_SENDER_PHONE", "+3725550000")
    monkeypatch.setenv("OMNIVA_SENDER_COUNTRY", "EE")
    monkeypatch.setenv("OMNIVA_SENDER_POSTCODE", "10111")


def _patch_call(monkeypatch, response):
    """Capture-helper: record every _call and return a canned response."""
    calls = []

    def fake_call(method, path, body=None):
        calls.append({"method": method, "path": path, "body": body})
        return response

    monkeypatch.setattr(oc, "_call", fake_call)
    return calls


# --- list_pickup_points ---------------------------------------------------

def test_country_filter(feed_calls):
    out = oc.list_pickup_points(country="LV")
    assert out["count"] == 3
    assert {p["zip"] for p in out["points"]} == {"9595", "1010", "2020"}


def test_country_filter_case_insensitive(feed_calls):
    out = oc.list_pickup_points(country="lv")
    assert out["count"] == 3


def test_query_filter(feed_calls):
    out = oc.list_pickup_points(country="LV", query="origo")
    assert out["count"] == 1
    assert out["points"][0]["zip"] == "1010"
    assert out["points"][0]["type"] == "parcel_machine"


def test_query_matches_address(feed_calls):
    out = oc.list_pickup_points(country="LV", query="somersētas")
    assert out["count"] == 1
    assert out["points"][0]["zip"] == "9595"


def test_limit(feed_calls):
    out = oc.list_pickup_points(country="LV", limit=1)
    assert out["count"] == 1
    assert len(out["points"]) == 1


def test_cache_reused_on_second_call(feed_calls):
    oc.list_pickup_points(country="LV")
    oc.list_pickup_points(country="EE")
    assert len(feed_calls) == 1


def test_feed_error_propagates(monkeypatch):
    monkeypatch.setattr(oc, "_locations_cache", {"data": None, "ts": 0.0})
    monkeypatch.setattr(oc, "_http_get_json", lambda url: {"error": "boom"})
    out = oc.list_pickup_points()
    assert "error" in out


# --- auth headers ---------------------------------------------------------

def test_basic_auth_header_shape(monkeypatch):
    monkeypatch.setenv("OMNIVA_API_USERNAME", "user")
    monkeypatch.setenv("OMNIVA_API_PASSWORD", "pass")
    monkeypatch.delenv("OMNIVA_INTEGRATION_AGENT_ID", raising=False)
    h = oc._headers()
    expected = "Basic " + base64.b64encode(b"user:pass").decode()
    assert h["Authorization"] == expected


def test_headers_none_when_env_unset(monkeypatch):
    monkeypatch.delenv("OMNIVA_API_USERNAME", raising=False)
    monkeypatch.delenv("OMNIVA_API_PASSWORD", raising=False)
    assert oc._headers() is None


# --- create_shipment ------------------------------------------------------

def test_create_shipment_builds_request(monkeypatch, omx_env):
    calls = _patch_call(monkeypatch, {"savedShipments": [{"barcode": "CC123"}]})
    out = oc.create_shipment("Dr. Liene Ozola", "+37129876543", "1010",
                             receiver_email="liene@vetclinic.lv")
    assert out["barcode"] == "CC123"
    assert len(calls) == 1
    c = calls[0]
    assert c["method"] == "POST"
    assert c["path"] == "/shipments/business-to-client"
    body = c["body"]
    assert body["customerCode"] == "12345"
    sh = body["shipments"][0]
    assert sh["mainService"] == "PARCEL"
    assert sh["deliveryChannel"] == "PARCEL_MACHINE"
    recv = sh["receiverAddressee"]
    assert recv["personName"] == "Dr. Liene Ozola"
    assert recv["contactMobile"] == "+37129876543"
    assert recv["contactEmail"] == "liene@vetclinic.lv"
    assert recv["address"]["offloadPostcode"] == "1010"
    assert recv["address"]["country"] == "LV"
    snd = sh["senderAddressee"]
    assert snd["personName"] == "Nanordica Medical OÜ"
    assert snd["address"]["country"] == "EE"


def test_create_shipment_missing_phone_no_call(monkeypatch, omx_env):
    calls = _patch_call(monkeypatch, {"savedShipments": []})
    out = oc.create_shipment("Dr. X", "", "1010")
    assert "error" in out and "phone" in out["error"].lower()
    assert calls == []


def test_create_shipment_env_unset(monkeypatch):
    for var in ("OMNIVA_CUSTOMER_CODE", "OMNIVA_API_USERNAME",
                "OMNIVA_API_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    calls = _patch_call(monkeypatch, {"savedShipments": []})
    out = oc.create_shipment("Dr. X", "+37120000000", "1010")
    assert "error" in out
    assert calls == []


def test_create_shipment_failed_shipment(monkeypatch, omx_env):
    _patch_call(monkeypatch, {"savedShipments": [],
                              "failedShipments": [{"messageCode": "ERR_1"}]})
    out = oc.create_shipment("Dr. X", "+37120000000", "1010")
    assert "error" in out


# --- get_label ------------------------------------------------------------

def test_get_label_writes_pdf(monkeypatch, tmp_path, omx_env):
    pdf = b"%PDF-1.4 fake label"
    _patch_call(monkeypatch, {"successAddressCards": [
        {"barcode": "CC123", "fileData": base64.b64encode(pdf).decode()}]})
    monkeypatch.setattr(oc, "_LABELS_DIR", tmp_path / "labels")
    out = oc.get_label("CC123")
    assert out["path"].endswith("CC123.pdf")
    assert (tmp_path / "labels" / "CC123.pdf").read_bytes() == pdf


def test_get_label_failure(monkeypatch, tmp_path, omx_env):
    _patch_call(monkeypatch, {"successAddressCards": [],
                              "failedAddressCards": [{"barcode": "CC123"}]})
    monkeypatch.setattr(oc, "_LABELS_DIR", tmp_path / "labels")
    out = oc.get_label("CC123")
    assert "error" in out


# --- track ----------------------------------------------------------------

def test_track_parses_events(monkeypatch, omx_env):
    calls = _patch_call(monkeypatch, {"shipmentBarcode": "CC123", "events": [
        {"eventCode": "ARRIVED_AT_APT", "eventName": "Arrived to parcel machine",
         "eventDate": "2026-07-22T10:00:00",
         "location": {"zip": "1010", "locationName": "Rīga Origo pakomāts"}}]})
    out = oc.track("CC123")
    assert calls[0]["method"] == "GET"
    assert calls[0]["path"] == "/shipments/CC123"
    assert out["count"] == 1
    ev = out["events"][0]
    assert ev["code"] == "ARRIVED_AT_APT"
    assert ev["name"] == "Arrived to parcel machine"
    assert ev["location"] == "Rīga Origo pakomāts"


# --- tools layer ----------------------------------------------------------

def test_tool_check_config_unset(monkeypatch):
    from tools.omniva import omniva_check_config
    for var in ("OMNIVA_CUSTOMER_CODE", "OMNIVA_API_USERNAME",
                "OMNIVA_API_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    out = omniva_check_config.fn()
    assert out == {"customer_code_set": False, "username_set": False,
                   "password_set": False}


def test_tool_create_shipment_dry_run(monkeypatch):
    from tools.omniva import omniva_create_shipment
    monkeypatch.delenv("DRY_RUN", raising=False)  # default = dry
    out = omniva_create_shipment.fn(42, "Dr. X", "+37120000000", "1010")
    assert out["dry_run"] is True
    assert out["details"]["deal_id"] == 42
    assert out["details"]["pickup_point_id"] == "1010"


def test_tool_get_label_dry_run(monkeypatch):
    from tools.omniva import omniva_get_label
    monkeypatch.delenv("DRY_RUN", raising=False)
    out = omniva_get_label.fn("CC123")
    assert out["dry_run"] is True
