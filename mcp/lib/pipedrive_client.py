"""Pipedrive v1 client. Read + narrow write + admin create_* (for setup).
Credentials from PIPEDRIVE_API_TOKEN / PIPEDRIVE_DOMAIN env vars.
Every response dict carries `_rate_limit` when the API provides it."""
import os
import json
import urllib.request
import urllib.parse
import urllib.error

_RATE_HEADERS = [
    ("x-ratelimit-limit", "limit"),
    ("x-ratelimit-remaining", "remaining"),
    ("x-ratelimit-reset", "reset"),
    ("x-daily-requests-left", "daily_requests_left"),
]


def _creds() -> tuple[str, str]:
    return os.getenv("PIPEDRIVE_API_TOKEN", ""), os.getenv("PIPEDRIVE_DOMAIN", "")


def _build_base(domain: str) -> str:
    if not domain:
        return ""
    if "." not in domain:
        return f"https://{domain}.pipedrive.com/v1"
    return f"https://{domain}/v1"


def _rate(headers) -> dict:
    info = {}
    for h, k in _RATE_HEADERS:
        v = headers.get(h)
        if v is not None:
            try:
                info[k] = int(v)
            except ValueError:
                info[k] = v
    return info


def _request(method: str, path: str, params: dict | None = None,
             body: dict | None = None) -> dict:
    token, domain = _creds()
    if not token:
        return {"error": "PIPEDRIVE_API_TOKEN not set"}
    if not domain:
        return {"error": "PIPEDRIVE_DOMAIN not set"}
    base = _build_base(domain)
    p = {"api_token": token}
    if params:
        p.update({k: v for k, v in params.items() if v is not None})
    url = f"{base}/{path}?{urllib.parse.urlencode(p, doseq=True)}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "ravimus-mcp/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read().decode())
            if isinstance(out, dict):
                out["_rate_limit"] = _rate(resp.headers)
            return out
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.readable() else ""
        rl = _rate(e.headers)
        if e.code == 429:
            return {"error": "Rate limit exceeded",
                    "retry_after_seconds": rl.get("reset"), "_rate_limit": rl}
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": detail, "_rate_limit": rl}
    except Exception as e:
        return {"error": str(e)}


def get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params)


def post(path: str, body: dict) -> dict:
    return _request("POST", path, body=body)


def put(path: str, body: dict) -> dict:
    return _request("PUT", path, body=body)
