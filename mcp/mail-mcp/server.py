#!/usr/bin/env python3.12
"""
mail-mcp — MS Graph email MCP server.

Guardrails enforced here (not by the agent):
  - opt-out blocklist: permanent, checked before every send
  - ≤ 1 email per lead per 24 h
  - ≤ 5 emails per lead total
  - DRY_RUN=1 → logs action, does not send
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from lib.graph import GraphClient

server = Server("mail-mcp")
client = GraphClient()

CACHE = Path("cache")
BLOCKLIST_FILE = CACHE / "blocklist.txt"
SEND_LOG_FILE = CACHE / "send-log.json"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_blocklist() -> set[str]:
    if BLOCKLIST_FILE.exists():
        return {line.strip().lower() for line in BLOCKLIST_FILE.read_text().splitlines() if line.strip()}
    return set()


def load_send_log() -> dict:
    if SEND_LOG_FILE.exists():
        return json.loads(SEND_LOG_FILE.read_text())
    return {}


def save_send_log(log: dict) -> None:
    CACHE.mkdir(exist_ok=True)
    SEND_LOG_FILE.write_text(json.dumps(log, indent=2))


def add_to_blocklist(email: str) -> None:
    CACHE.mkdir(exist_ok=True)
    with BLOCKLIST_FILE.open("a") as f:
        f.write(email.lower().strip() + "\n")


def check_send_allowed(deal_id: int, to: str) -> dict | None:
    """Return error dict if send is blocked, None if allowed."""
    to = to.lower()
    if to in load_blocklist():
        return {"blocked": True, "reason": "opt-out"}

    log = load_send_log()
    key = str(deal_id)
    entry = log.get(key, {"count": 0, "last_sent": None})

    if entry["count"] >= 5:
        return {"blocked": True, "reason": "max-5-emails"}

    if entry["last_sent"]:
        last = datetime.fromisoformat(entry["last_sent"])
        if datetime.now(timezone.utc) - last < timedelta(hours=24):
            return {"blocked": True, "reason": "24h-limit",
                    "next_allowed": (last + timedelta(hours=24)).isoformat()}

    return None


def record_send(deal_id: int) -> None:
    log = load_send_log()
    key = str(deal_id)
    entry = log.get(key, {"count": 0, "last_sent": None})
    entry["count"] += 1
    entry["last_sent"] = datetime.now(timezone.utc).isoformat()
    log[key] = entry
    save_send_log(log)


# ── tool definitions ──────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="send_mail",
            description=(
                "Send an email to a lead. "
                "Enforces: opt-out blocklist, ≤1 email per lead per 24 h, ≤5 emails total. "
                "DRY_RUN=1 logs without sending."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "integer", "description": "Pipedrive deal ID (used for rate-limit tracking)"},
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string"},
                    "body": {"type": "string", "description": "HTML or plain-text body"},
                },
                "required": ["deal_id", "to", "subject", "body"],
            },
        ),
        Tool(
            name="list_new_messages",
            description="Return new inbox messages since last call (Graph delta token). Empty list in DRY_RUN.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="add_to_blocklist",
            description="Permanently add an email to the opt-out blocklist. Use on opt-out or 'no' reply.",
            inputSchema={
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            },
        ),
        Tool(
            name="get_send_status",
            description="Check how many emails have been sent to a deal and when the next one is allowed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "integer"},
                    "email": {"type": "string"},
                },
                "required": ["deal_id", "email"],
            },
        ),
    ]


# ── tool handler ──────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "send_mail":
            deal_id = arguments["deal_id"]
            to = arguments["to"]
            blocked = check_send_allowed(deal_id, to)
            if blocked:
                return [TextContent(type="text", text=json.dumps(blocked))]
            result = client.send_mail(to, arguments["subject"], arguments["body"])
            if not result.get("dry_run"):
                record_send(deal_id)
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "list_new_messages":
            msgs = client.list_new_messages()
            return [TextContent(type="text", text=json.dumps(msgs, ensure_ascii=False))]

        elif name == "add_to_blocklist":
            add_to_blocklist(arguments["email"])
            return [TextContent(type="text", text=json.dumps({"added": True, "email": arguments["email"]}))]

        elif name == "get_send_status":
            deal_id = arguments["deal_id"]
            email = arguments["email"].lower()
            log = load_send_log()
            entry = log.get(str(deal_id), {"count": 0, "last_sent": None})
            blocked = check_send_allowed(deal_id, email)
            return [TextContent(type="text", text=json.dumps({
                "deal_id": deal_id,
                "emails_sent": entry["count"],
                "last_sent": entry["last_sent"],
                "blocked": blocked,
            }))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
