"""Model-first triage for internal mail: is this a parcel request, and what
are the shipment details?

Why a model: internal mail arrives in free form and mostly on other topics.
Keyword rules produced both misses ("Saaja — Karl" dashes, prose requests)
and risky matches. The model answers two questions in one pass —
*is this a shipping request* and *what are the receiver's details* — and
the deterministic layer keeps the authority: every field it returns is
still validated by code, and the parcel machine is always resolved against
Omniva's public feed. The model never registers anything.

Runs headless Claude (`claude -p`) with a strict JSON contract, so the cron
stays a plain Python process. If the model is unavailable, callers fall
back to the regex parser (see omniva_mail_dispatch.fallback_parse).
"""
import json
import re
import subprocess

CLAUDE_TIMEOUT_S = 180

PROMPT = """Sa oled Nanordica sisemise postkasti (ravimus@nanordica.com) \
saatmiskorralduste triaaž. Sisend on ÜKS firmasisene e-kiri. Vasta AINULT \
JSON-objektiga, ilma selgituse ja koodiaia-märkideta.

Kaks ülesannet korraga:
1) Otsusta, kas kiri palub SAATA PAKI (näidis, tooted, sidemed vms) kellelegi \
   välja. Ruumibroneeringud, koosolekukutsed, arved, tavavestlus, \
   turundusteated jms EI OLE saatmiskorraldused.
2) Kui on, korja välja saaja andmed — nii siltidega ("Saaja: X") kui \
   vabatekstist ("saada Kärla pakiautomaati, Karl 5628...").

JSON-skeem (kõik võtmed kohustuslikud, tundmatu = null):
{
  "is_shipping_request": true|false,
  "confidence": 0.0-1.0,
  "reason": "<lühike põhjendus eesti keeles>",
  "name": "<saaja täisnimi või null>",
  "phone": "<saaja mobiil või null>",
  "machine": "<pakiautomaadi nimi nii nagu kirjas, või null>",
  "address": "<linn/aadress, kui automaati pole nimetatud, või null>",
  "country": "EE"|"LV"|"LT"|null,
  "weight": "<kg arvuna stringis või null>",
  "email": "<saaja e-post või null>",
  "contents": "<mida saata, tellija sõnadega, või null>"
}

Reeglid:
- Ära leiuta andmeid. Kui telefoni pole kirjas, siis null.
- Saaja on see, KELLELE pakk läheb — mitte kirja saatja, kui need erinevad.
- Allkirjaplokist võta telefon ainult siis, kui saaja on kirja saatja ise.
- Tsiteeritud vanu kirju (From:/Saatja: järel) arvesta ainult siis, kui \
  värskes osas andmeid pole.
- "machine" pane kirjapandud kujul; automaadi õigsust kontrollib kood.

E-kiri:
---
Saatja: __SENDER__
Teema: __SUBJECT__
Sisu:
__BODY__
---"""


def _run_claude(prompt: str) -> str:
    """Headless Claude call. Separated for test injection."""
    res = subprocess.run(["claude", "-p", prompt,
                          "--dangerously-skip-permissions"],
                         capture_output=True, text=True,
                         timeout=CLAUDE_TIMEOUT_S)
    return res.stdout


def _extract_json(text: str) -> dict | None:
    """First JSON object in the model's answer (tolerates stray prose)."""
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = fence.group(1) if fence else None
    if raw is None:
        start = text.find("{")
        if start < 0:
            return None
        depth, end = 0, None
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            return None
        raw = text[start:end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


_FIELD_KEYS = ("name", "phone", "machine", "address", "country", "weight",
               "email")


def triage(sender: str, subject: str, body: str, runner=_run_claude) -> dict:
    """{'ok', 'is_shipping_request', 'confidence', 'reason', 'fields',
    'contents'} — or {'ok': False, 'error': ...} when the model is
    unavailable/unparseable, so the caller can fall back to regex."""
    # str.format is unusable here: the JSON schema in PROMPT is full of
    # literal braces. Token replacement keeps the schema readable.
    prompt = (PROMPT.replace("__SENDER__", sender or "")
                    .replace("__SUBJECT__", subject or "")
                    .replace("__BODY__", (body or "")[:6000]))
    try:
        out = runner(prompt)
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "error": f"model unavailable: {e}"}
    data = _extract_json(out)
    if not isinstance(data, dict) or "is_shipping_request" not in data:
        return {"ok": False, "error": "model returned no usable JSON"}
    fields = {}
    for k in _FIELD_KEYS:
        v = data.get(k)
        if isinstance(v, (int, float)):
            v = str(v)
        if isinstance(v, str) and v.strip() and v.strip().lower() != "null":
            fields[k] = v.strip()
    if fields.get("country"):
        fields["country"] = fields["country"].upper()[:2]
    return {"ok": True,
            "is_shipping_request": bool(data.get("is_shipping_request")),
            "confidence": data.get("confidence"),
            "reason": data.get("reason"),
            "contents": data.get("contents"),
            "fields": fields}
