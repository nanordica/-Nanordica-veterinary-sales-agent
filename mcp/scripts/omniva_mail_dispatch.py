"""Test script: dispatch Omniva parcels from internal shipping-request emails.

Watches the GRAPH_SENDER (ravimus@) inbox for messages FROM an internal
@nanordica.com sender whose subject/body indicates a package to send
(keywords: pakk/pakiautomaat/omniva/saatmine/saada). For each candidate:

 1. Parses labeled fields from the body (Estonian labels, one per line):
        Saaja: Dr. Anna Bērziņa            (kohustuslik)
        Telefon: +371 26123456             (kohustuslik — saabumis-SMS)
        Pakiautomaat: Riga Plaza           (KAS see ...)
        Aadress: Riga                      (... VÕI linn/aadress)
        Riik: LV                           (valikuline, vaikimisi LV)
        Kaal: 0.5                          (valikuline, kg, vaikimisi 1.0)
        E-post: anna@klinika.lv            (valikuline)
 2. Receiver delivery is parcel-machine-only (the funnel's model): resolves
    the machine from the public locations feed — by name when Pakiautomaat
    is given, else by the address/city — and errors when the address has no
    parcel machine.
 3. Incomplete data -> per-message error listing exactly what is missing.
 4. Registers the shipment via lib.omniva_client.create_shipment and fetches
    the label PDF. DRY_RUN=1 (the default) only logs the would-be shipment.
 5. Marks the email as handled so the same package is never registered
    twice: tries a Graph PATCH (categories + isRead — needs Mail.ReadWrite;
    with today's Mail.Read-only grant this 403s and is skipped), and ALWAYS
    records the message id in cache/omniva-dispatch.json, which is the
    authoritative dedup registry. Error results are recorded too — a
    corrected request must arrive as a NEW email.

Deliberately NOT using graph_client.list_new_messages: its delta cursor
(GRAPH_DELTA_PATH) belongs to the inbox-triage flow; this script reads the
most recent messages directly and dedups against its own registry.

Run from mcp/:  python -m scripts.omniva_mail_dispatch [--top 25]
"""
import argparse
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from lib import graph_client as gc
from lib import omniva_client as oc
from lib.dryrun import is_dry_run, dry_log
from scripts import parcel_triage

_GRAPH = "https://graph.microsoft.com/v1.0"
INTERNAL_DOMAIN = "@nanordica.com"
KEYWORDS = ("pakk", "paki", "omniva", "saatmi", "saata", "saada")
STATE_PATH = Path(__file__).resolve().parents[2] / "cache" / "omniva-dispatch.json"

# Body-line labels -> canonical field names. Matching is deliberately
# lenient: any of ':', '=', '-', '\u2013', '\u2014' separates label from value,
# because people write "Saaja \u2014 Karl" as readily as "Saaja: Karl".
FIELD_ALIASES = {
    "saaja": "name", "nimi": "name", "kellele": "name", "kontakt": "name",
    "telefon": "phone", "tel": "phone", "mobiil": "phone", "number": "phone",
    "gsm": "phone", "phone": "phone",
    "pakiautomaat": "machine", "automaat": "machine", "sihtkoht": "machine",
    "pakipunkt": "machine", "pakiautomaati": "machine", "pakomaat": "machine",
    "aadress": "address", "linn": "address", "asukoht": "address",
    "riik": "country", "kaal": "weight",
    "e-post": "email", "epost": "email", "email": "email", "meil": "email",
}
_SEP = r"[:=\u2013\u2014-]"


# --- parsing ---------------------------------------------------------------

def strip_html(text: str) -> str:
    """HTML body -> plain text lines (Graph bodies are usually HTML)."""
    text = re.sub(r"(?is)<(style|script)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|tr|li)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines())


_QUOTE_MARKERS = re.compile(
    r"^\s*(from:|saatja:|sent:|saadetud:|to:|adressaat:|-{4,}|>|"
    r"on .{0,80} wrote:|t[äa]psustus vajalik|see on automaatne vastus)",
    re.I)


def strip_quoted(text: str) -> str:
    """Drop quoted reply history: everything from the first quote marker on.
    Keeps only the sender's fresh text so our own clarification template
    (literal 'Saaja: <nimi>' lines) is never parsed as data."""
    kept = []
    for line in text.splitlines():
        if _QUOTE_MARKERS.match(line):
            break
        kept.append(line)
    return "\n".join(kept)


def parse_dispatch_email(text: str) -> dict:
    """Extract labeled fields from a plain-text body. Any of ':', '=', '-',
    en/em dash separates label from value; the split is chosen so the left
    side is a KNOWN label, which keeps hyphenated labels intact
    ('E-post: x' splits at ':', 'Saaja - x' at '-'). First value per field
    wins; '<placeholder>' values are ignored."""
    fields = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for m in re.finditer(_SEP, line):
            label = line[:m.start()].strip().lower()
            key = FIELD_ALIASES.get(label)
            if not key:
                continue
            value = line[m.end():].strip()
            if value and key not in fields and "<" not in value and ">" not in value:
                fields[key] = value
            break
    return fields


_GREETINGS = {"tere", "tervitades", "lugupidamisega", "soovin", "palun",
              "aitäh", "parimate"}
_NAME_RE = re.compile(r"^[A-ZÕÄÖÜŠŽ][a-zõäöüšž\-'’ēāīūčģķļņ]+$")


def _stem_place(token: str) -> str:
    """Strip Estonian directional case endings so 'Viljandisse Männimäele'
    matches the feed's nominative names ('Viljandi Männimäe ...')."""
    for suf in ("sse", "ile", "le", "ni"):
        if token.lower().endswith(suf) and len(token) > len(suf) + 2:
            return token[:-len(suf)]
    return token


def fallback_parse(text: str) -> dict:
    """Heuristic free-text extraction for emails without labeled lines.
    Labeled fields always win — the caller merges these underneath. Finds:
    phone (digit run), receiver name (capitalized 2-3 word line), place
    (comma-segment on the phone line, case endings stemmed) and country
    (from the phone's prefix; Estonian mobiles start with 5)."""
    fields = {}
    m = re.search(r"(\+?\d[\d\s\-]{5,}\d)", text)
    if m:
        phone = " ".join(m.group(1).split())
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 7:
            fields["phone"] = phone
            if phone.startswith("+371"):
                fields["country"] = "LV"
            elif phone.startswith("+372") or digits.startswith("5"):
                fields["country"] = "EE"
    for line in text.splitlines():
        # 'Meelis Kadaja, PhD, MBA' -> take the part before the first comma
        head = line.split(",")[0].strip().rstrip(".")
        words = head.split()
        if (2 <= len(words) <= 3 and words[0].lower() not in _GREETINGS
                and all(_NAME_RE.match(w) for w in words)):
            fields.setdefault("name", head)
            break
    # "... Kärla omniva pakiautomaati", "Tartusse Rebase Rimi pakiautomaati":
    # walk left from the keyword and keep the contiguous run of capitalised
    # tokens (Estonian place names) — lowercase verbs end the run.
    mm = re.search(r"(.{0,80}?)(?:omniva\s+)?pakiautomaa\w*", text, re.I)
    if mm:
        toks, run = mm.group(1).split(), []
        for t in reversed(toks):
            t = t.strip(" ,.:;")
            if t.lower() == "omniva":
                continue
            if t[:1].isupper():
                run.append(_stem_place(t))
            else:
                break
        if run:
            fields["machine"] = " ".join(reversed(run))
    if m:
        phone_line = next((ln for ln in text.splitlines()
                           if m.group(1) in ln), "")
        after = phone_line.split(",", 1)
        if len(after) == 2:
            toks = [_stem_place(t) for t in after[1].split()
                    if t[:1].isupper()]
            if toks:
                fields["address"] = " ".join(toks)
    return fields


def validate_fields(fields: dict) -> list:
    """Return human-readable list of what is missing/invalid (empty = OK)."""
    missing = []
    if not fields.get("name"):
        missing.append("Saaja nimi — lisa rida 'Saaja: <nimi>'")
    phone = fields.get("phone", "")
    if not phone:
        missing.append("Telefon — lisa rida 'Telefon: <mobiil>' "
                       "(kohustuslik: Omniva saabumis-SMS uksekoodiga)")
    elif len(re.sub(r"\D", "", phone)) < 7:
        missing.append(f"Telefon '{phone}' ei ole kasutatav mobiilinumber")
    if not (fields.get("machine") or fields.get("address")):
        missing.append("Sihtkoht — lisa rida 'Pakiautomaat: <automaadi nimi>' "
                       "VÕI 'Aadress: <linn/aadress>'")
    weight = fields.get("weight")
    if weight:
        try:
            float(weight.replace(",", "."))
        except ValueError:
            missing.append(f"Kaal '{weight}' ei ole arv (kg)")
    return missing


# --- parcel machine resolution --------------------------------------------

def resolve_pickup_point(fields: dict, lookup=oc.list_pickup_points) -> dict:
    """Resolve the target parcel machine (delivery is machine-only).

    Pakiautomaat given -> match by machine name; else Aadress -> match by
    city/address substring. Post offices never qualify. Returns
    {'zip', 'name', 'alternatives'} or {'error': ...}."""
    country = (fields.get("country") or "LV").strip().upper()
    query = fields.get("machine") or fields.get("address")
    by = "machine" if fields.get("machine") else "address"
    res = lookup(country=country, query=query, limit=10)
    if "error" in res:
        return res
    machines = [p for p in res.get("points", [])
                if p.get("type") == "parcel_machine"]
    if not machines and query:
        # 'Tartu Rebase Rimi Omniva pakiautomaat' fails exact substring match
        # against the feed's 'Tartu Rebase Rimi pakiautomaat' — retry with
        # generic filler words dropped.
        generic = {"omniva", "pakiautomaat", "pakiautomaati", "pakomāts",
                   "automaat", "automaati", "parcel", "machine"}
        toks = [t for t in query.split() if t.lower() not in generic]
        cleaned = " ".join(toks)
        if cleaned and cleaned.lower() != query.lower():
            res = lookup(country=country, query=cleaned, limit=10)
            machines = [p for p in res.get("points", [])
                        if p.get("type") == "parcel_machine"]
        if not machines:
            # last resort: single place words, in the order written — the
            # first is the most specific ('Kärla omniva, Saaremaa' -> Kärla,
            # not the county).
            for tok in (t.strip(" ,.") for t in toks):
                if len(tok) < 4 or not tok[:1].isupper():
                    continue
                res = lookup(country=country, query=tok, limit=10)
                cand = [p for p in res.get("points", [])
                        if p.get("type") == "parcel_machine"]
                if cand:
                    machines = cand
                    break
    if not machines:
        if by == "machine":
            return {"error": f"Pakiautomaati '{query}' ei leitud riigis "
                             f"{country} — kontrolli nime (omniva.ee kaart)"}
        return {"error": f"Aadressil/linnas '{query}' ({country}) ei ole "
                         "Omniva pakiautomaati — täpsusta rida "
                         "'Pakiautomaat: <nimi>' või kasuta teist linna"}
    pick = machines[0]
    return {"zip": pick["zip"], "name": pick["name"],
            "alternatives": [m["name"] for m in machines[1:6]]}


# --- Graph inbox ------------------------------------------------------------

def _internal(addr: str) -> bool:
    """True when the address is in the company domain. Two hard rules hang
    on this: (1) a NEW shipment may only be initiated by an internal
    sender; (2) label/tracking notifications may only be emailed to an
    internal address."""
    return (addr or "").lower().endswith(INTERNAL_DOMAIN)


ROOM_KEYWORDS = ("ruum", "bronee", "seminar", "lounge", "koosolek")


def _is_internal_sender(sender: str, own_address: str) -> bool:
    """Cheap gate before any model call: internal, not the mailbox itself."""
    s = (sender or "").lower()
    return _internal(s) and s != (own_address or "").lower()


def _is_dispatch_candidate(sender: str, own_address: str, *texts) -> bool:
    """Keyword fallback, used only when the triage model is unavailable.
    Room-booking requests (handled by room_booking_watch) often contain
    'saada'/'paki' too — they are never shipment candidates."""
    if not _is_internal_sender(sender, own_address):
        return False
    blob = " ".join(t or "" for t in texts).lower()
    if any(k in blob for k in ROOM_KEYWORDS):
        return False
    return any(k in blob for k in KEYWORDS)


def list_recent_inbox(top: int = 25) -> dict:
    """Newest inbox messages with full bodies (no delta cursor)."""
    sender = gc._env("GRAPH_SENDER")
    headers = gc._auth_headers()
    if headers is None:
        return gc.get_token()
    url = (f"{_GRAPH}/users/{urllib.parse.quote(sender)}/mailFolders/inbox/"
           f"messages?$top={top}&$orderby=receivedDateTime%20desc"
           "&$select=id,conversationId,subject,from,receivedDateTime,body,"
           "bodyPreview")
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"messages": json.loads(r.read().decode()).get("value", [])}
    except urllib.error.HTTPError as e:
        return {"error": f"inbox HTTP {e.code}", "detail": e.read().decode()[:400]}
    except Exception as e:
        return {"error": str(e)}


def mark_processed_graph(msg_id: str, status: str) -> dict:
    """Best-effort in-mailbox marker (category + read). Needs Mail.ReadWrite;
    today's Mail.Read-only grant returns 403 -> caller ignores and relies on
    the local registry."""
    sender = gc._env("GRAPH_SENDER")
    headers = gc._auth_headers()
    if headers is None:
        return gc.get_token()
    body = json.dumps({"categories": [f"Omniva/{status}"],
                       "isRead": True}).encode()
    url = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/messages/{msg_id}"
    try:
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method="PATCH")
        with urllib.request.urlopen(req, timeout=30):
            return {"marked": True}
    except urllib.error.HTTPError as e:
        return {"error": f"PATCH HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}


# --- clarification reply ----------------------------------------------------

_FORMAT_HELP = ("Saatmiskorralduse vorming (üks väli rea kohta):<br>"
                "&nbsp;&nbsp;Saaja: &lt;nimi&gt;<br>"
                "&nbsp;&nbsp;Telefon: &lt;mobiil&gt;<br>"
                "&nbsp;&nbsp;Pakiautomaat: &lt;automaadi nimi&gt; "
                "VÕI Aadress: &lt;linn/aadress&gt;<br>"
                "&nbsp;&nbsp;Kaal: &lt;kg&gt; (valikuline) · "
                "Riik: EE/LV (valikuline)")


def build_clarification(res: dict, subject: str | None) -> tuple:
    """(subject, html_body) for the reply asking the sender to clarify.
    Deterministic template — no LLM."""
    subj = f"Täpsustus vajalik: {subject or 'paki saatmine'}"
    parts = ["Tere!<br><br>",
             "See on automaatne vastus sinu saatmiskorraldusele."]
    if res["status"] == "error":
        parts.append("<br><br>Korraldusest jäi puudu:<ul>")
        parts += [f"<li>{m}</li>" for m in res.get("missing", [])]
        parts.append("</ul>")
    if res["status"] == "ambiguous":
        parts.append("<br><br>Sihtkohas on mitu Omniva pakiautomaati — "
                     "palun täpsusta, millisesse saata:<ul>")
        parts += [f"<li>{o}</li>" for o in res.get("options", [])]
        parts.append("</ul>Vasta UUE kirjaga, milles on rida "
                     "„Pakiautomaat: &lt;nimi&gt;“ ja ülejäänud andmed.")
    parts.append(f"<br><br>{_FORMAT_HELP}<br><br>— Ravimus'e saatmisagent "
                 "(automaatne kiri)")
    return subj, "".join(parts)


# --- shipped notification (K5: internal, deterministic, no LLM) -------------

def build_shipped_notice(res: dict) -> tuple:
    """(subject, html_body) for the internal notification after a shipment
    is registered: receiver, machine, tracking number; label PDF attached
    by the caller."""
    f = res.get("fields", {})
    machine = (res.get("machine") or {}).get("name", "?")
    barcode = res.get("barcode", "?")
    subj = f"Pakk registreeritud: {f.get('name', '?')} → {machine}"
    body = ("Tere!<br><br>Omniva saadetis on registreeritud.<br><ul>"
            f"<li>Saaja: {f.get('name', '?')} ({f.get('phone', '?')})</li>"
            f"<li>Pakiautomaat: {machine}</li>"
            f"<li>Jälgimisnumber: <b>{barcode}</b></li></ul>")
    if res.get("contents"):
        body += f"Sisu (mudeli kokkuvõte): <b>{res['contents']}</b><br><br>"
    texts = [t for t in (res.get("request_texts") or []) if t]
    if texts:
        # What to actually pack lives in the requester's own words — quote
        # the thread so the office isn't left guessing the contents.
        body += ("Soovi sisu (tellija sõnadega):<br><blockquote>"
                 + "<br>—<br>".join(t.replace("\n", " ").strip()[:300]
                                    for t in texts[-3:])
                 + "</blockquote>")
    body += ("Pakisilt on kirjaga kaasas — prindi ja kleebi pakile. "
             "Jälgimine: https://www.omniva.ee/abi/jalgimine<br><br>"
             "— Ravimus'e saatmisagent (automaatne kiri)")
    return subj, body


def send_shipped_notice(res: dict) -> dict:
    """Email the shipped-notice (label + tracking) to the office address.
    HARD RULE: label/tracking info may only go to an @nanordica.com
    address — anything else is refused, never sent."""
    notify_to = os.getenv("DISPATCH_NOTIFY_EMAIL", "vera@nanordica.com")
    if not _internal(notify_to):
        return {"error": f"notify blocked: '{notify_to}' ei ole "
                         f"{INTERNAL_DOMAIN} aadress — pakisildi/jälgimise "
                         "info tohib minna ainult firmasisesele aadressile"}
    subj, html_body = build_shipped_notice(res)
    lab = res.get("label")
    atts = [lab] if lab and str(lab).endswith(".pdf") else None
    return gc.send_mail(notify_to, subj, html_body, attachments=atts)


# --- registry ---------------------------------------------------------------

_SUBJECT_PREFIX = re.compile(
    r"^(re|fwd?|vs|edasi|t[äa]psustus vajalik)\s*:\s*", re.I)


def _base_subject(subject: str | None) -> str:
    """Strip reply/forward/clarification prefixes repeatedly:
    'Re: Täpsustus vajalik: soovin saata paki' -> 'soovin saata paki'."""
    s = (subject or "").strip()
    while True:
        m = _SUBJECT_PREFIX.match(s)
        if not m:
            return s.lower()
        s = s[m.end():].strip()


def inherit_context(registry: dict, conversation_id: str | None,
                    sender: str | None, subject: str | None) -> tuple:
    """(fields, options) gathered from earlier rounds of the same request.
    A round matches by Graph conversationId OR — because our clarification
    may start a new thread — by same sender + same base subject. Latest
    round wins; lets a short reply complete the original request."""
    base = _base_subject(subject)
    rounds = [e for e in registry.values()
              if (conversation_id and e.get("conversationId") == conversation_id)
              or (sender and e.get("from") == sender and base
                  and _base_subject(e.get("subject")) == base)]
    rounds.sort(key=lambda e: e.get("ts", 0))
    fields, options, excerpts = {}, [], []
    for e in rounds:
        fields.update(e.get("fields") or {})
        if e.get("options"):
            options = e["options"]
        if e.get("excerpt"):
            excerpts.append(e["excerpt"])
    return fields, options, excerpts


def match_option(text: str, options: list) -> str | None:
    """Pick the offered machine the sender's free text refers to
    ('Palun Selveri automaati' -> the ...Selveri... option). Each option's
    distinctive words (absent from the other options) are prefix-matched
    against the text; exactly one matching option wins."""
    low = text.lower()
    hits = []
    for i, opt in enumerate(options):
        words = {w for w in re.findall(r"[a-zõäöüšž]{4,}", opt.lower())}
        others = set()
        for j, o in enumerate(options):
            if j != i:
                others |= {w for w in re.findall(r"[a-zõäöüšž]{4,}", o.lower())}
        distinctive = words - others
        if any(w[:6] in low for w in distinctive):
            hits.append(opt)
    return hits[0] if len(hits) == 1 else None


def already_registered(registry: dict, conversation_id: str | None,
                       sender: str | None, subject: str | None) -> dict | None:
    """An earlier round of the SAME request that already produced a barcode.
    One thread = one parcel: a follow-up reply must never register a second
    shipment (seen live 2026-08-01, two barcodes for one request)."""
    base = _base_subject(subject)
    for e in registry.values():
        if not e.get("barcode"):
            continue
        if conversation_id and e.get("conversationId") == conversation_id:
            return e
        if (sender and e.get("from") == sender and base
                and _base_subject(e.get("subject")) == base):
            return e
    return None


def load_registry() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_registry(reg: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(reg, indent=1, ensure_ascii=False))


# --- per-message processing -------------------------------------------------

def process_message(msg: dict, lookup=oc.list_pickup_points,
                    create=oc.create_shipment, label=oc.get_label,
                    inherited: dict | None = None,
                    inherited_options: list | None = None,
                    model_fields: dict | None = None) -> dict:
    """Parse -> validate -> resolve machine -> (DRY_RUN?) register + label.
    Returns a result dict with status: error | dry_run | registered."""
    body = (msg.get("body") or {}).get("content", "") or msg.get("bodyPreview", "")
    if (msg.get("body") or {}).get("contentType", "").lower() == "html" \
            or "<" in body:
        body = strip_html(body)
    body = strip_quoted(body)
    labeled = parse_dispatch_email(body)
    # Precedence: this email's labeled lines > this email's free text >
    # fields inherited from earlier rounds of the same thread.
    # Precedence: explicit labels > model extraction > regex heuristics >
    # earlier rounds of the same thread. Labels are unambiguous, so they win.
    fields = {**(inherited or {}), **fallback_parse(body),
              **(model_fields or {}), **labeled}
    if not labeled.get("machine") and inherited_options:
        # Earlier round offered concrete machines — see whether this email's
        # fresh text picks one of them by name fragment.
        pick = match_option(body, inherited_options)
        if pick:
            fields["machine"] = pick
    missing = validate_fields(fields)
    if missing:
        return {"status": "error", "missing": missing, "fields": fields}
    point = resolve_pickup_point(fields, lookup=lookup)
    if "error" in point:
        return {"status": "error", "missing": [point["error"]],
                "fields": fields}
    if point["alternatives"]:
        # More than one machine matches the given destination — don't guess,
        # ask the sender which one (reply email in main()).
        return {"status": "ambiguous",
                "options": [point["name"]] + point["alternatives"],
                "fields": fields}
    # Weight is optional in OMX (parcel-machine pricing is size-based) —
    # None when the email doesn't state it, rather than a made-up default.
    weight = (float(fields["weight"].replace(",", "."))
              if fields.get("weight") else None)
    country = (fields.get("country") or "LV").strip().upper()
    if is_dry_run():
        dry = dry_log("omniva_mail_dispatch.create_shipment",
                      receiver=fields["name"], phone=fields["phone"],
                      machine=point["name"], pickup_point_id=point["zip"],
                      country=country, weight_kg=weight)
        return {"status": "dry_run", "machine": point, "fields": fields,
                "dry": dry}
    res = create(receiver_name=fields["name"], receiver_phone=fields["phone"],
                 pickup_point_id=point["zip"],
                 receiver_email=fields.get("email"),
                 receiver_country=country, weight_kg=weight)
    if "error" in res:
        why = "; ".join(f.get("message", "") for f in res.get("failed", [])
                        if isinstance(f, dict)) or res.get("detail") or ""
        return {"status": "error",
                "missing": [f"Omniva: {res['error']}" + (f" ({why})" if why else "")],
                "fields": fields, "detail": why or None}
    out = {"status": "registered", "barcode": res["barcode"],
           "machine": point, "fields": fields}
    lab = label(res["barcode"])
    out["label"] = lab.get("path") or lab.get("error")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Omniva dispatch from internal "
                                            "shipping-request emails")
    p.add_argument("--top", type=int, default=25,
                   help="how many newest inbox messages to scan")
    p.add_argument("--no-model", action="store_true",
                   help="skip model triage, use the keyword fallback")
    p.add_argument("--send-asks", action="store_true",
                   help="really send clarification replies even in DRY_RUN "
                        "(registration itself stays dry)")
    args = p.parse_args()

    own = gc._env("GRAPH_SENDER")
    inbox = list_recent_inbox(args.top)
    if "error" in inbox:
        print(json.dumps(inbox, ensure_ascii=False))
        return 1

    registry = load_registry()
    results = []
    for msg in inbox["messages"]:
        sender = ((msg.get("from") or {}).get("emailAddress") or {}).get("address", "")
        if not _is_internal_sender(sender, own):
            continue
        if msg["id"] in registry:
            continue
        raw_body = (msg.get("body") or {}).get("content", "") or msg.get("bodyPreview", "")
        clean_body = strip_html(raw_body) if "<" in raw_body else raw_body
        triaged = parcel_triage.triage(sender, msg.get("subject"), clean_body) \
            if not args.no_model else {"ok": False, "error": "model disabled"}
        if triaged.get("ok"):
            if not triaged["is_shipping_request"]:
                # Not a parcel request (room booking, chatter, invoice...).
                # Recorded so the model is not asked about it again; NO reply.
                registry[msg["id"]] = {
                    "status": "not_shipping", "from": sender,
                    "subject": msg.get("subject"),
                    "received": msg.get("receivedDateTime"),
                    "conversationId": msg.get("conversationId"),
                    "reason": triaged.get("reason"), "ts": int(time.time())}
                save_registry(registry)
                results.append({"id": msg["id"], "status": "not_shipping",
                                "subject": msg.get("subject"),
                                "reason": triaged.get("reason")})
                continue
            model_fields = triaged.get("fields") or {}
        else:
            # Model unavailable -> keyword fallback keeps the cron working.
            model_fields = {}
            if not _is_dispatch_candidate(sender, own, msg.get("subject"),
                                          msg.get("bodyPreview"), raw_body):
                continue
        dup = already_registered(registry, msg.get("conversationId"),
                                 sender, msg.get("subject"))
        if dup:
            registry[msg["id"]] = {
                "status": "duplicate_skipped", "from": sender,
                "subject": msg.get("subject"),
                "received": msg.get("receivedDateTime"),
                "conversationId": msg.get("conversationId"),
                "duplicate_of": dup.get("barcode"), "ts": int(time.time())}
            save_registry(registry)
            results.append({"id": msg["id"], "status": "duplicate_skipped",
                            "from": sender, "subject": msg.get("subject"),
                            "duplicate_of": dup.get("barcode")})
            continue
        inh_fields, inh_options, inh_excerpts = inherit_context(
            registry, msg.get("conversationId"), sender, msg.get("subject"))
        res = process_message(msg, inherited=inh_fields,
                              inherited_options=inh_options,
                              model_fields=model_fields)
        if triaged.get("ok") and triaged.get("contents"):
            res.setdefault("contents", triaged["contents"])
        raw = (msg.get("body") or {}).get("content", "") or msg.get("bodyPreview", "")
        excerpt = strip_quoted(strip_html(raw) if "<" in raw else raw).strip()[:300]
        res.update({"id": msg["id"], "from": sender,
                    "subject": msg.get("subject"),
                    "received": msg.get("receivedDateTime")})
        if res["status"] == "registered":
            # K5: notify the office (label + tracking number), deterministic.
            res["request_texts"] = inh_excerpts + [excerpt]
            res["notification"] = send_shipped_notice(res)
            # The internal requester gets an in-thread confirmation too
            # (the vet-facing funnel never mails the receiver here — the
            # requester is always @nanordica.com by the candidate filter).
            f = res.get("fields", {})
            confirm = ("Tere!<br><br>Pakk on registreeritud.<br><ul>"
                       f"<li>Saaja: {f.get('name', '?')} ({f.get('phone', '?')})</li>"
                       f"<li>Pakiautomaat: {(res.get('machine') or {}).get('name', '?')}</li>"
                       f"<li>Jälgimisnumber: <b>{res.get('barcode', '?')}</b></li></ul>"
                       "Kontor sai pakisildi ja soovi sisu; pakk läheb teele "
                       "pärast automaati viimist.<br><br>"
                       "— Ravimus'e saatmisagent (automaatne kiri)")
            res["confirmation"] = gc.reply_mail(msg["id"], confirm)
        if res["status"] in ("error", "ambiguous"):
            subj, html_body = build_clarification(res, msg.get("subject"))
            if not _internal(sender):
                # Defense in depth — the candidate filter already guarantees
                # an internal sender; never reply outside the domain.
                res["clarification"] = {"error": "blocked: väline saatja"}
            elif is_dry_run() and not args.send_asks:
                res["clarification"] = dry_log(
                    "omniva_mail_dispatch.clarify", to=sender, subject=subj)
            else:
                # Reply IN-THREAD so the sender's answer keeps the same
                # conversationId (a fresh sendMail would fork the thread and
                # break inheritance); fall back to a new mail on error.
                sent = gc.reply_mail(msg["id"], html_body)
                if "error" in sent:
                    sent = gc.send_mail(sender, subj, html_body)
                res["clarification"] = sent
            res["status"] = "clarification_sent"
        graph_mark = mark_processed_graph(msg["id"], res["status"])
        res["graph_marked"] = graph_mark.get("marked", False)
        if res["status"] == "dry_run":
            # A preview must stay repeatable: never record it, otherwise the
            # following real run skips the message as "already processed"
            # (that trap is why the 2026-08-01 duplicate slipped through).
            results.append(res)
            continue
        registry[msg["id"]] = {k: res.get(k) for k in
                               ("status", "missing", "options", "barcode",
                                "subject", "from", "received", "fields")} | {
            "conversationId": msg.get("conversationId"),
            "excerpt": excerpt,
            "ts": int(time.time())}
        save_registry(registry)
        results.append(res)

    print(json.dumps({"scanned": len(inbox["messages"]),
                      "processed": results,
                      "dry_run": is_dry_run()},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
