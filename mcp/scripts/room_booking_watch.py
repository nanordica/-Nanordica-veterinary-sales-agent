"""Watcher: internal room-booking requests in the ravimus@ inbox.

Deterministic and cheap (no LLM) until a candidate appears: scans the newest
inbox messages, keeps ones FROM @nanordica.com whose text mentions booking a
room (ruum/bronee/seminar/lounge/koosolek), dedups via
cache/room-booking.json, writes the request to a spool JSON and hands it to a
headless Claude run of the repo's `/room-booking` skill, which drives the
Tehnopol booking page (code KVincubator, 0.00 € only) and replies in-thread.

The skill writes `<spool>.result.json`; only then is the message marked
processed. A missing result file leaves the message unmarked so the next
cycle retries it.

Run from mcp/:  python -m scripts.room_booking_watch [--top 25] [--dry]
Cron wraps it with flock; see crontab.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

from lib import graph_client as gc
from scripts.omniva_mail_dispatch import (
    INTERNAL_DOMAIN, _internal, list_recent_inbox, strip_html, strip_quoted)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = REPO_ROOT / "cache" / "room-booking.json"
SPOOL_DIR = REPO_ROOT / "cache" / "room-booking-spool"
KEYWORDS = ("ruum", "bronee", "seminar", "lounge", "koosolek")
CLAUDE_TIMEOUT_S = 15 * 60


def is_room_request(sender: str, own: str, *texts) -> bool:
    """Internal sender (not the mailbox itself) + room keyword anywhere."""
    s = (sender or "").lower()
    if not _internal(s) or s == (own or "").lower():
        return False
    blob = " ".join(t or "" for t in texts).lower()
    return any(k in blob for k in KEYWORDS)


def load_registry() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_registry(reg: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(reg, indent=1, ensure_ascii=False))


def run_booking_agent(spool: Path) -> dict | None:
    """Headless Claude executes the /room-booking skill on the spool file.
    Returns the parsed result JSON, or None when the agent produced none."""
    cmd = ["claude", "-p", f"/room-booking {spool}",
           "--dangerously-skip-permissions"]
    try:
        subprocess.run(cmd, cwd=REPO_ROOT, timeout=CLAUDE_TIMEOUT_S,
                       capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None
    result_path = spool.with_suffix(spool.suffix + ".result.json")
    try:
        return json.loads(result_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    p = argparse.ArgumentParser(description="Room-booking request watcher")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--dry", action="store_true",
                   help="detect + spool only; do not launch the booking agent")
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
        body = (msg.get("body") or {}).get("content", "") or msg.get("bodyPreview", "")
        if "<" in body:
            body = strip_html(body)
        body = strip_quoted(body)
        if not is_room_request(sender, own, msg.get("subject"), body):
            continue
        if msg["id"] in registry:
            continue

        SPOOL_DIR.mkdir(parents=True, exist_ok=True)
        spool = SPOOL_DIR / f"req-{int(time.time())}-{msg['id'][-8:]}.json"
        spool.write_text(json.dumps(
            {"id": msg["id"], "from": sender, "subject": msg.get("subject"),
             "received": msg.get("receivedDateTime"), "body_text": body},
            indent=1, ensure_ascii=False))

        if args.dry:
            results.append({"id": msg["id"], "from": sender,
                            "subject": msg.get("subject"),
                            "spool": str(spool), "status": "spooled-dry"})
            continue

        outcome = run_booking_agent(spool)
        entry = {"from": sender, "subject": msg.get("subject"),
                 "received": msg.get("receivedDateTime"),
                 "ts": int(time.time())}
        if outcome is None:
            # No result file: leave the message UNregistered so the next
            # cycle retries; surface the failure in the run output.
            results.append({"id": msg["id"], "status": "agent-no-result",
                            "spool": str(spool)} | entry)
            continue
        entry |= {"status": outcome.get("status"),
                  "room": outcome.get("room"),
                  "start": outcome.get("start"), "end": outcome.get("end")}
        registry[msg["id"]] = entry
        save_registry(registry)
        results.append({"id": msg["id"]} | entry)

    print(json.dumps({"scanned": len(inbox["messages"]),
                      "processed": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
