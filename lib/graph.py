import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

MAIL_FROM = os.environ.get("MAIL_FROM", "ravimus@nanordica.com")
MS_GRAPH_TOKEN = os.environ.get("MS_GRAPH_TOKEN", "")
DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"

DELTA_TOKEN_FILE = Path("cache/graph-delta-token.json")
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self):
        self.dry_run = DRY_RUN
        self.headers = {"Authorization": f"Bearer {MS_GRAPH_TOKEN}",
                        "Content-Type": "application/json"}

    def send_mail(self, to: str, subject: str, body_html: str) -> dict:
        if self.dry_run:
            print(f"[DRY_RUN] send_mail to={to} | subject={subject[:60]}")
            return {"dry_run": True, "to": to, "subject": subject}

        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": True,
        }
        url = f"{GRAPH_BASE}/users/{MAIL_FROM}/sendMail"
        r = httpx.post(url, headers=self.headers, json=payload, timeout=30)
        r.raise_for_status()
        return {"sent": True, "to": to}

    def list_new_messages(self) -> list[dict]:
        """Return inbox messages since last call using delta token."""
        if self.dry_run:
            print("[DRY_RUN] list_new_messages — returning empty list")
            return []

        if DELTA_TOKEN_FILE.exists():
            delta_url = json.loads(DELTA_TOKEN_FILE.read_text()).get("token")
        else:
            delta_url = (
                f"{GRAPH_BASE}/users/{MAIL_FROM}/mailFolders/inbox/messages/delta"
                "?$select=subject,from,body,receivedDateTime,isRead"
            )

        messages = []
        url = delta_url
        while url:
            r = httpx.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            messages.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            next_delta = data.get("@odata.deltaLink")
            if next_delta:
                DELTA_TOKEN_FILE.parent.mkdir(exist_ok=True)
                DELTA_TOKEN_FILE.write_text(json.dumps({"token": next_delta}))
                break

        return messages
