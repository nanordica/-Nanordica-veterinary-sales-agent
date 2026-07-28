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
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from lib import graph_client as gc
from lib import omniva_client as oc
from lib.dryrun import is_dry_run, dry_log

_GRAPH = "https://graph.microsoft.com/v1.0"
INTERNAL_DOMAIN = "@nanordica.com"
KEYWORDS = ("pakk", "pakiautomaat", "omniva", "saatmine", "saada")
STATE_PATH = Path(__file__).resolve().parents[2] / "cache" / "omniva-dispatch.json"

# Body-line labels -> canonical field names (case-insensitive, ':' or '=').
FIELD_ALIASES = {
    "saaja": "name", "nimi": "name",
    "telefon": "phone", "tel": "phone", "mobiil": "phone",
    "pakiautomaat": "machine", "automaat": "machine",
    "aadress": "address", "linn": "address",
    "riik": "country",
    "kaal": "weight",
    "e-post": "email", "epost": "email", "email": "email",
}


# --- parsing ---------------------------------------------------------------

def strip_html(text: str) -> str:
    """HTML body -> plain text lines (Graph bodies are usually HTML)."""
    text = re.sub(r"(?is)<(style|script)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|tr|li)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines())


def parse_dispatch_email(text: str) -> dict:
    """Extract labeled fields from plain-text body. First value per field wins."""
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-zÕÄÖÜõäöü\-]+)\s*[:=]\s*(.+?)\s*$", line)
        if not m:
            continue
        key = FIELD_ALIASES.get(m.group(1).lower())
        if key and key not in fields:
            fields[key] = m.group(2).strip()
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
    if not machines:
        if by == "machine":
            return {"error": f"Pakiautomaati '{query}' ei leitud riigis "
                             f"{country} — kontrolli nime (omniva.ee kaart)"}
        return {"error": f"Aadressil/linnas '{query}' ({country}) ei ole "
                         "Omniva pakiautomaati — täpsusta rida "
                         "'Pakiautomaat: <nimi>' või kasuta teist linna"}
    pick = machines[0]
    return {"zip": pick["zip"], "name": pick["name"],
            "alternatives": len(machines) - 1}


# --- Graph inbox ------------------------------------------------------------

def _is_dispatch_candidate(sender: str, own_address: str, *texts) -> bool:
    """Internal sender (not the mailbox itself) + shipping keyword anywhere."""
    s = (sender or "").lower()
    if not s.endswith(INTERNAL_DOMAIN) or s == (own_address or "").lower():
        return False
    blob = " ".join(t or "" for t in texts).lower()
    return any(k in blob for k in KEYWORDS)


def list_recent_inbox(top: int = 25) -> dict:
    """Newest inbox messages with full bodies (no delta cursor)."""
    sender = gc._env("GRAPH_SENDER")
    headers = gc._auth_headers()
    if headers is None:
        return gc.get_token()
    url = (f"{_GRAPH}/users/{urllib.parse.quote(sender)}/mailFolders/inbox/"
           f"messages?$top={top}&$orderby=receivedDateTime%20desc"
           "&$select=id,subject,from,receivedDateTime,body,bodyPreview")
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


# --- registry ---------------------------------------------------------------

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
                    create=oc.create_shipment, label=oc.get_label) -> dict:
    """Parse -> validate -> resolve machine -> (DRY_RUN?) register + label.
    Returns a result dict with status: error | dry_run | registered."""
    body = (msg.get("body") or {}).get("content", "") or msg.get("bodyPreview", "")
    if (msg.get("body") or {}).get("contentType", "").lower() == "html" \
            or "<" in body:
        body = strip_html(body)
    fields = parse_dispatch_email(body)
    missing = validate_fields(fields)
    if missing:
        return {"status": "error", "missing": missing, "fields": fields}
    point = resolve_pickup_point(fields, lookup=lookup)
    if "error" in point:
        return {"status": "error", "missing": [point["error"]],
                "fields": fields}
    weight = float(fields.get("weight", "1.0").replace(",", "."))
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
        return {"status": "error", "missing": [f"Omniva: {res['error']}"],
                "fields": fields, "detail": res.get("detail")}
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
        if not _is_dispatch_candidate(
                sender, own, msg.get("subject"), msg.get("bodyPreview"),
                (msg.get("body") or {}).get("content")):
            continue
        if msg["id"] in registry:
            continue
        res = process_message(msg)
        res.update({"id": msg["id"], "from": sender,
                    "subject": msg.get("subject"),
                    "received": msg.get("receivedDateTime")})
        graph_mark = mark_processed_graph(msg["id"], res["status"])
        res["graph_marked"] = graph_mark.get("marked", False)
        registry[msg["id"]] = {k: res.get(k) for k in
                               ("status", "missing", "barcode", "subject",
                                "from", "received")} | {"ts": int(time.time())}
        save_registry(registry)
        results.append(res)

    print(json.dumps({"scanned": len(inbox["messages"]),
                      "processed": results,
                      "dry_run": is_dry_run()},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
