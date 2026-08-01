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


# --- shipped notification ---------------------------------------------------

def test_build_shipped_notice():
    subj, body = od.build_shipped_notice(
        {"fields": {"name": "Mari Maasikas", "phone": "51234567"},
         "machine": {"name": "Viljandi Männimäe Selveri pakiautomaat"},
         "barcode": "CC123EE"})
    assert "Mari Maasikas" in subj and "Selveri" in subj
    assert "CC123EE" in body and "51234567" in body


def test_file_attachment_builds_base64(tmp_path):
    from lib import graph_client as gc
    p = tmp_path / "label.pdf"
    p.write_bytes(b"%PDF-1.4 test")
    att = gc.file_attachment(str(p))
    assert att["name"] == "label.pdf"
    assert att["contentType"] == "application/pdf"
    import base64
    assert base64.b64decode(att["contentBytes"]).startswith(b"%PDF")


# --- internal-domain guards -------------------------------------------------

def test_internal_domain_check():
    assert od._internal("vera@nanordica.com")
    assert not od._internal("vera@gmail.com")
    assert not od._internal("")


def test_shipped_notice_blocked_for_external_recipient(monkeypatch):
    monkeypatch.setenv("DISPATCH_NOTIFY_EMAIL", "keegi@gmail.com")

    def boom(*a, **kw):  # send_mail must never be reached
        raise AssertionError("send_mail called for external recipient")
    monkeypatch.setattr(od.gc, "send_mail", boom)
    res = od.send_shipped_notice({"fields": {}, "machine": {}, "barcode": "X"})
    assert "blocked" in res["error"]


def test_shipped_notice_goes_to_internal(monkeypatch):
    monkeypatch.setenv("DISPATCH_NOTIFY_EMAIL", "vera@nanordica.com")
    sent = {}

    def fake_send(to, subj, body, attachments=None):
        sent.update(to=to, attachments=attachments)
        return {"sent": True}
    monkeypatch.setattr(od.gc, "send_mail", fake_send)
    res = od.send_shipped_notice({"fields": {"name": "M"}, "machine": {},
                                  "barcode": "X", "label": "/tmp/x.pdf"})
    assert res == {"sent": True}
    assert sent["to"] == "vera@nanordica.com"
    assert sent["attachments"] == ["/tmp/x.pdf"]


# --- thread field inheritance -----------------------------------------------

REG = {"m1": {"conversationId": "c1", "ts": 1, "from": "vera@nanordica.com",
              "subject": "soovin saata paki",
              "fields": {"name": "Mari Maasikas", "phone": "51234567",
                         "address": "Viljandi Männimäe", "country": "EE"},
              "options": ["Viljandi Männimäe Maksimarketi pakiautomaat",
                          "Viljandi Männimäe Selveri pakiautomaat"]},
       "m2": {"conversationId": "c2", "ts": 2, "from": "teine@nanordica.com",
              "subject": "muu teema", "fields": {"name": "Keegi Muu"}}}


def test_inherit_context_by_conversation():
    f, opts, exc = od.inherit_context(REG, "c1", None, None)
    assert f["name"] == "Mari Maasikas" and len(opts) == 2
    assert od.inherit_context(REG, "puudub", None, None) == ({}, [], [])


def test_inherit_context_by_base_subject():
    # our clarification forked the thread: new conversationId, Re:-chained subject
    f, opts, exc = od.inherit_context(
        REG, "UUS-CONV", "vera@nanordica.com",
        "Re: Täpsustus vajalik: soovin saata paki")
    assert f["phone"] == "51234567" and len(opts) == 2


def test_base_subject_strips_prefixes():
    assert od._base_subject(
        "Re: Täpsustus vajalik: Re: Täpsustus vajalik: soovin saata paki"
    ) == "soovin saata paki"


def test_match_option_picks_unique_fragment():
    opts = ["Viljandi Männimäe Maksimarketi pakiautomaat",
            "Viljandi Männimäe Selveri pakiautomaat"]
    assert od.match_option("Palun Selveri automaati ssata.", opts) == opts[1]
    assert od.match_option("Maksimarket sobib", opts) == opts[0]
    assert od.match_option("ükskõik kumb", opts) is None
    assert od.match_option("Männimäe automaat", opts) is None  # shared word


def test_reply_completes_request_via_option_match(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "0")
    created = {}

    def fake_create(**kw):
        created.update(kw)
        return {"barcode": "CC9", "saved": [{"barcode": "CC9"}]}

    f, opts, _ = od.inherit_context(
        REG, None, "vera@nanordica.com", "Re: Täpsustus vajalik: soovin saata paki")
    res = od.process_message(_msg("Palun Selveri automaati ssata.\n"),
                             lookup=fake_lookup(AMBIG_MACHINES),
                             create=fake_create,
                             label=lambda b: {"barcode": b, "path": "/tmp/x.pdf"},
                             inherited=f, inherited_options=opts)
    assert res["status"] == "registered"
    assert created["pickup_point_id"] == "96063"  # Selver
    assert created["receiver_name"] == "Mari Maasikas"


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


def test_room_requests_are_not_shipment_candidates():
    own = "ravimus@nanordica.com"
    assert not od._is_dispatch_candidate(
        "vera@nanordica.com", own,
        "Ruumi broneerimine", "Palun broneeri seminariruum ja saada kinnitus")
    # tavaline pakikiri jääb kandidaadiks
    assert od._is_dispatch_candidate("vera@nanordica.com", own,
                                     "soovin saata paki", "")


# --- sihtkoht alias + token-fallback resolve --------------------------------

TARTU_MACHINES = [
    {"zip": "96087", "name": "Tartu Rebase Rimi pakiautomaat",
     "address": "Rebase 10, Tartu", "type": "parcel_machine"},
]


def test_sihtkoht_label_maps_to_machine():
    f = od.parse_dispatch_email("Saaja: Meelis Kadaja\n"
                                "Sihtkoht: Tartu Rebase Rimi Omniva pakiautomaat\n")
    assert f["machine"] == "Tartu Rebase Rimi Omniva pakiautomaat"


def test_resolve_token_fallback_drops_generic_words():
    r = od.resolve_pickup_point(
        {"machine": "Tartu Rebase Rimi Omniva pakiautomaat", "country": "EE"},
        lookup=fake_lookup(TARTU_MACHINES))
    assert r["zip"] == "96087"


def test_shipped_notice_includes_request_texts(monkeypatch):
    monkeypatch.setenv("DISPATCH_NOTIFY_EMAIL", "vera@nanordica.com")
    sent = {}

    def fake_send(to, subj, body, attachments=None):
        sent["body"] = body
        return {"sent": True}
    monkeypatch.setattr(od.gc, "send_mail", fake_send)
    od.send_shipped_notice({"fields": {"name": "M"}, "machine": {},
                            "barcode": "X",
                            "request_texts": ["Palun saada 2 karpi 10x10"]})
    assert "2 karpi 10x10" in sent["body"]


# --- leebem parser: eraldajad, sildid, vabateksti automaadivihje ------------

KARLA_MACHINES = [
    {"zip": "96276", "name": "Kärla pakiautomaat", "address": "Kärla, Saaremaa",
     "type": "parcel_machine"},
    {"zip": "96199", "name": "Saaremaa Kaubamaja pakiautomaat",
     "address": "Tallinna 5, Kuressaare", "type": "parcel_machine"},
]


def test_dash_separators_and_hyphenated_labels():
    f = od.parse_dispatch_email(
        "Saaja — Karl Heinla\nTelefon — 56281454\n"
        "Pakiautomaat - Kärla omniva, Saaremaa.\nE-post: karl@example.ee\n")
    assert f["name"] == "Karl Heinla"
    assert f["phone"] == "56281454"
    assert f["machine"].startswith("Kärla")
    assert f["email"] == "karl@example.ee"   # hyphenated label survives


def test_freetext_machine_hint_from_sentence():
    f = od.fallback_parse(
        "Tere! Paki võib saata Kärla omniva pakiautomaati, Saaremaa.\n"
        "Karl Heinla\n56281454")
    assert f["machine"] == "Kärla"           # verb stops the capitalised run
    assert f["name"] == "Karl Heinla" and f["country"] == "EE"


def test_freetext_name_ignores_title_suffix():
    f = od.fallback_parse("Meelis Kadaja, PhD, MBA\n+372 5184872")
    assert f["name"] == "Meelis Kadaja"


def test_resolve_prefers_first_place_word_not_the_county():
    r = od.resolve_pickup_point({"machine": "Kärla omniva, Saaremaa",
                                 "country": "EE"},
                                lookup=fake_lookup(KARLA_MACHINES))
    assert r["zip"] == "96276"                # Kärla, mitte Saaremaa Kaubamaja


# --- üks lõim = üks pakk ----------------------------------------------------

REG_REGISTERED = {
    "m1": {"conversationId": "c9", "from": "vera@nanordica.com",
           "subject": "Paki saatmine", "barcode": "CC1EE", "ts": 1,
           "status": "registered"},
}


def test_already_registered_by_conversation():
    dup = od.already_registered(REG_REGISTERED, "c9", None, None)
    assert dup and dup["barcode"] == "CC1EE"


def test_already_registered_by_sender_and_base_subject():
    dup = od.already_registered(REG_REGISTERED, "UUS", "vera@nanordica.com",
                                "Re: Paki saatmine")
    assert dup and dup["barcode"] == "CC1EE"


def test_already_registered_ignores_other_threads():
    assert od.already_registered(REG_REGISTERED, "c1", "keegi@nanordica.com",
                                 "Muu teema") is None
