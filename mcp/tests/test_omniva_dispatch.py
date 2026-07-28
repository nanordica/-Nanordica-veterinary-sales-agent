"""omniva_mail_dispatch tests: parsing, validation, machine resolution and
the DRY_RUN pipeline. Graph/OMX HTTP is never touched — the lookup/create
callables are injected fakes."""
import pytest

from scripts import omniva_mail_dispatch as od


PLAIN_BODY = """Tere!

Palun saada näidispakk.
Saaja: Dr. Anna Bērziņa
Tel: +371 26123456
Pakiautomaat: Riga Plaza
Kaal: 0,5
E-post: anna@klinika.lv

Aitäh!
"""

HTML_BODY = ("<html><body><p>Palun saada pakk</p>"
             "<div>Nimi: Dr. J&#257;nis Ozols</div>"
             "<div>Mobiil: +371 29876543</div>"
             "<div>Linn: Liepāja</div></body></html>")


def fake_lookup(points):
    def lookup(country="LV", query=None, limit=10):
        q = (query or "").lower()
        hits = [p for p in points
                if q in p["name"].lower() or q in p["address"].lower()]
        return {"points": hits[:limit], "count": len(hits[:limit])}
    return lookup


MACHINES = [
    {"zip": "9114", "name": "Rīgas T/C Riga Plaza pakomāts",
     "address": "Lielirbes iela 29, Rīga", "type": "parcel_machine"},
    {"zip": "9520", "name": "Rīgas T/C Galleria Riga pakomāts",
     "address": "Dzirnavu iela 67, Rīga", "type": "parcel_machine"},
    {"zip": "9601", "name": "Liepājas pasta nodaļa",
     "address": "Pasta iela 4, Liepāja", "type": "post_office"},
]


# --- parsing ----------------------------------------------------------------

def test_parse_plain_body_with_aliases():
    f = od.parse_dispatch_email(PLAIN_BODY)
    assert f["name"] == "Dr. Anna Bērziņa"
    assert f["phone"] == "+371 26123456"
    assert f["machine"] == "Riga Plaza"
    assert f["weight"] == "0,5"
    assert f["email"] == "anna@klinika.lv"


def test_parse_html_body():
    f = od.parse_dispatch_email(od.strip_html(HTML_BODY))
    assert f["name"] == "Dr. Jānis Ozols"
    assert f["phone"] == "+371 29876543"
    assert f["address"] == "Liepāja"


def test_first_value_wins():
    f = od.parse_dispatch_email("Saaja: A\nNimi: B\n")
    assert f["name"] == "A"


# --- validation -------------------------------------------------------------

def test_validate_all_missing_lists_each_problem():
    missing = od.validate_fields({})
    joined = " ".join(missing)
    assert len(missing) == 3
    assert "Saaja" in joined and "Telefon" in joined and "Sihtkoht" in joined


def test_validate_bad_phone_and_weight():
    missing = od.validate_fields(
        {"name": "X", "phone": "12", "machine": "Y", "weight": "raske"})
    assert any("Telefon" in m for m in missing)
    assert any("Kaal" in m for m in missing)


def test_validate_ok():
    assert od.validate_fields(
        {"name": "X", "phone": "+371 26123456", "address": "Riga"}) == []


# --- machine resolution -----------------------------------------------------

def test_resolve_by_machine_name():
    r = od.resolve_pickup_point({"machine": "Riga Plaza"},
                                lookup=fake_lookup(MACHINES))
    assert r["zip"] == "9114"


def test_resolve_by_address_prefers_parcel_machine():
    r = od.resolve_pickup_point({"address": "Rīga"},
                                lookup=fake_lookup(MACHINES))
    assert r["zip"] in ("9114", "9520") and r["alternatives"] == 1


def test_resolve_machine_not_found():
    r = od.resolve_pickup_point({"machine": "Olematu"},
                                lookup=fake_lookup(MACHINES))
    assert "ei leitud" in r["error"]


def test_resolve_address_with_only_post_office_errors():
    r = od.resolve_pickup_point({"address": "Liepāja"},
                                lookup=fake_lookup(MACHINES))
    assert "pakiautomaati" in r["error"]


# --- candidate filter -------------------------------------------------------

def test_candidate_filter():
    own = "ravimus@nanordica.com"
    assert od._is_dispatch_candidate("vera@nanordica.com", own,
                                     "Palun saada pakk", "")
    assert not od._is_dispatch_candidate("vet@klinika.lv", own,
                                         "Palun saada pakk", "")
    assert not od._is_dispatch_candidate("vera@nanordica.com", own,
                                         "Koosoleku protokoll", "")
    assert not od._is_dispatch_candidate(own, own, "pakk", "")


# --- DRY_RUN pipeline -------------------------------------------------------

def _msg(body, ctype="text"):
    return {"body": {"content": body, "contentType": ctype},
            "bodyPreview": body[:100]}


def test_process_message_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    res = od.process_message(_msg(PLAIN_BODY), lookup=fake_lookup(MACHINES))
    assert res["status"] == "dry_run"
    assert res["machine"]["zip"] == "9114"
    assert res["dry"]["dry_run"] is True


def test_process_message_missing_data(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    res = od.process_message(_msg("Palun saada pakk homme ära"),
                             lookup=fake_lookup(MACHINES))
    assert res["status"] == "error"
    assert len(res["missing"]) == 3


def test_process_message_live_registers(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "0")
    created = {}

    def fake_create(**kw):
        created.update(kw)
        return {"barcode": "CC123", "saved": [{"barcode": "CC123"}]}

    def fake_label(barcode):
        return {"barcode": barcode, "path": f"/tmp/{barcode}.pdf"}

    res = od.process_message(_msg(PLAIN_BODY), lookup=fake_lookup(MACHINES),
                             create=fake_create, label=fake_label)
    assert res["status"] == "registered" and res["barcode"] == "CC123"
    assert created["pickup_point_id"] == "9114"
    assert created["weight_kg"] == 0.5
    assert created["receiver_email"] == "anna@klinika.lv"
