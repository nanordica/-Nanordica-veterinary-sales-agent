"""Microsoft Graph app-only (client-credentials) client: token, sendMail,
inbox delta read. Sender mailbox = GRAPH_SENDER."""
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

_GRAPH = "https://graph.microsoft.com/v1.0"
_token_cache = {"value": None, "exp": 0.0}


def _env(name: str) -> str:
    return os.getenv(name, "")


def get_token() -> dict:
    """Return {'token': ...} or {'error': ...}. Caches until ~60s before expiry."""
    if _token_cache["value"] and time.time() < _token_cache["exp"] - 60:
        return {"token": _token_cache["value"]}
    tenant, client, secret = _env("GRAPH_TENANT_ID"), _env("GRAPH_CLIENT_ID"), _env("GRAPH_CLIENT_SECRET")
    if not (tenant and client and secret):
        return {"error": "GRAPH_TENANT_ID/CLIENT_ID/CLIENT_SECRET not all set"}
    data = urllib.parse.urlencode({
        "client_id": client, "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
            tok = json.loads(r.read().decode())
        _token_cache["value"] = tok["access_token"]
        _token_cache["exp"] = time.time() + tok.get("expires_in", 3600)
        return {"token": tok["access_token"]}
    except urllib.error.HTTPError as e:
        return {"error": f"token HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def _auth_headers() -> dict | None:
    t = get_token()
    if "error" in t:
        return None
    return {"Authorization": f"Bearer {t['token']}", "Content-Type": "application/json"}


def send_mail(to: str, subject: str, body_html: str) -> dict:
    """Send mail as GRAPH_SENDER. Returns {'sent': True} or {'error': ...}."""
    sender = _env("GRAPH_SENDER")
    headers = _auth_headers()
    if headers is None:
        return get_token()  # carries the error
    msg = {"message": {"subject": subject,
                       "body": {"contentType": "HTML", "content": body_html},
                       "toRecipients": [{"emailAddress": {"address": to}}]},
           "saveToSentItems": True}
    url = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/sendMail"
    req = urllib.request.Request(url, data=json.dumps(msg).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"sent": True, "status": r.status}
    except urllib.error.HTTPError as e:
        return {"error": f"sendMail HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def list_new_messages(folder: str = "inbox") -> dict:
    """Read new messages via the delta endpoint. Persists the deltaLink to
    GRAPH_DELTA_PATH so each call returns only messages since the last call."""
    sender = _env("GRAPH_SENDER")
    delta_path = Path(_env("GRAPH_DELTA_PATH") or "./data/graph_delta.json")
    headers = _auth_headers()
    if headers is None:
        return get_token()
    if delta_path.exists():
        url = json.loads(delta_path.read_text()).get("deltaLink")
    else:
        url = f"{_GRAPH}/users/{urllib.parse.quote(sender)}/mailFolders/{folder}/messages/delta"
    messages = []
    try:
        while url:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=30) as r:
                page = json.loads(r.read().decode())
            messages.extend(page.get("value", []))
            if "@odata.nextLink" in page:
                url = page["@odata.nextLink"]
            else:
                delta_path.parent.mkdir(parents=True, exist_ok=True)
                delta_path.write_text(json.dumps({"deltaLink": page.get("@odata.deltaLink")}))
                url = None
        return {"messages": [
            {"id": m.get("id"), "from": (m.get("from") or {}).get("emailAddress", {}).get("address"),
             "subject": m.get("subject"), "received": m.get("receivedDateTime"),
             "preview": m.get("bodyPreview")}
            for m in messages]}
    except urllib.error.HTTPError as e:
        return {"error": f"delta HTTP {e.code}", "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}
