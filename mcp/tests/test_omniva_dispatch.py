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
    assert r["zip"] in ("9114", "9520") and len(r["alternatives"]) == 1


def test_resolve_machine_not_found():
    r = od.resolve_pickup_point({"machine": "Olematu"},
                                lookup=fake_lookup(MACHINES))
    assert "ei leitud" in r["error"]


def test_resolve_address_with_only_post_office_errors():
    r = od.resolve_pickup_point({"address": "Liepāja"},
                                lookup=fake_lookup(MACHINES))
    assert "pakiautomaati" in r["error"]


# --- free-text fallback -----------------------------------------------------

FREETEXT_BODY = """
Mari Maasikas
51234567 , Viljandisse Männimäele


Soovin saata paki. Saadetis on paksem A4-formaadis ümbrik.


Tervitades,
Vera
"""

EE_MACHINES = MACHINES + [
    {"zip": "96284", "name": "Viljandi Männimäe Maksimarketi pakiautomaat",
     "address": "Riia mnt 35, Viljandi", "type": "parcel_machine"},
]


def test_fallback_parse_free_text():
    f = od.fallback_parse(FREETEXT_BODY)
    assert f["name"] == "Mari Maasikas"
    assert f["phone"] == "51234567"
    assert f["country"] == "EE"  # Estonian mobile prefix 5
    assert f["address"] == "Viljandi Männimäe"  # case endings stemmed


def test_fallback_lv_phone_sets_lv():
    assert od.fallback_parse("Zvaniet +371 26123456")["country"] == "LV"


def test_labeled_fields_win_over_fallback(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    body = FREETEXT_BODY + "\nSaaja: Teine Nimi\n"
    res = od.process_message(_msg(body), lookup=fake_lookup(EE_MACHINES))
    assert res["fields"]["name"] == "Teine Nimi"


def test_process_free_text_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    res = od.process_message(_msg(FREETEXT_BODY),
                             lookup=fake_lookup(EE_MACHINES))
    assert res["status"] == "dry_run"
    assert res["machine"]["zip"] == "96284"
    # no Kaal line -> no fabricated weight (OMX: measurement is optional)
    assert res["dry"]["details"]["weight_kg"] is None


# --- quoted-reply stripping -------------------------------------------------

REPLY_BODY = """Pakiautomaat: Viljandi Männimäe Selveri pakiautomaat
Saaja: Mari Maasikas
Telefon: 51234567

Saatja: ravimus@nanordica.com
Saadetud: esmaspäev
Tere! See on automaatne vastus sinu saatmiskorraldusele.
Saatmiskorralduse vorming (üks väli rea kohta):
Saaja: <nimi>
Telefon: <mobiil>
"""


def test_strip_quoted_drops_history_and_placeholders(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    res = od.process_message(_msg(REPLY_BODY),
                             lookup=fake_lookup(AMBIG_MACHINES))
    assert res["status"] == "dry_run"
    assert res["fields"]["name"] == "Mari Maasikas"  # not '<nimi>'
    assert res["machine"]["zip"] == "96063"  # Selver picked by name


def test_placeholder_values_ignored():
    f = od.parse_dispatch_email("Saaja: <nimi>\nSaaja: Päris Nimi\n")
    assert f["name"] == "Päris Nimi"


# --- ambiguity + clarification ----------------------------------------------

AMBIG_MACHINES = EE_MACHINES + [
    {"zip": "96063", "name": "Viljandi Männimäe Selveri pakiautomaat",
     "address": "Riia mnt 35, Viljandi", "type": "parcel_machine"},
]


def test_ambiguous_destination_asks_instead_of_guessing(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    res = od.process_message(_msg(FREETEXT_BODY),
                             lookup=fake_lookup(AMBIG_MACHINES))
    assert res["status"] == "ambiguous"
    assert len(res["options"]) == 2


def test_build_clarification_missing():
    subj, body = od.build_clarification(
        {"status": "error", "missing": ["Telefon — lisa rida"]}, "saada pakk")
    assert subj.startswith("Täpsustus vajalik")
    assert "Telefon" in body and "Saatmiskorralduse vorming" in body


def test_build_clarification_ambiguous():
    subj, body = od.build_clarification(
        {"status": "ambiguous", "options": ["A pakiautomaat",
                                            "B pakiautomaat"]}, None)
    assert "mitu Omniva pakiautomaati" in body
    assert "A pakiautomaat" in body and "B pakiautomaat" in body


# --- thread field inheritance -----------------------------------------------

def test_inherit_fields_merges_thread_rounds():
    reg = {"m1": {"conversationId": "c1", "ts": 1,
                  "fields": {"name": "Mari Maasikas", "phone": "51234567",
                             "address": "Viljandi Männimäe", "country": "EE"}},
           "m2": {"conversationId": "c2", "ts": 2,
                  "fields": {"name": "Keegi Muu"}}}
    assert od.inherit_fields(reg, "c1")["name"] == "Mari Maasikas"
    assert od.inherit_fields(reg, "puudub") == {}
    assert od.inherit_fields(reg, None) == {}


def test_short_reply_completes_via_inheritance(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    inherited = {"name": "Mari Maasikas", "phone": "51234567",
                 "address": "Viljandi Männimäe", "country": "EE"}
    res = od.process_message(
        _msg("Pakiautomaat: Viljandi Männimäe Selveri pakiautomaat\n"),
        lookup=fake_lookup(AMBIG_MACHINES), inherited=inherited)
    assert res["status"] == "dry_run"
    assert res["machine"]["zip"] == "96063"  # explicit machine beats address
    assert res["fields"]["name"] == "Mari Maasikas"


# --- candidate filter -------------------------------------------------------

def test_candidate_filter():
    own = "ravimus@nanordica.com"
    assert od._is_dispatch_candidate("vera@nanordica.com", own,
                                     "Palun saada pakk", "")
    assert od._is_dispatch_candidate("vera@nanordica.com", own,
                                     "soovin saata paki", "")
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
