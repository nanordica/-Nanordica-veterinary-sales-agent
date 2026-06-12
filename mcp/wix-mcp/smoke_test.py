"""wix-mcp smoke-test: käivitab serveri MCP stdio kaudu ja kontrollib,
et tellimuste loetelu töötab ja 100% näidisekupong tekib test-deal'ile
(wp4 "Valmis, kui" punkt 1).

Jooksutamine repo juurest:
    .venv/bin/python mcp/wix-mcp/smoke_test.py
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SERVER = Path(__file__).parent / "server.py"


async def call(session: ClientSession, tool: str, args: dict) -> dict:
    result = await session.call_tool(tool, args)
    assert not result.isError, f"{tool} ebaõnnestus: {result.content}"
    return json.loads(result.content[0].text)


async def main() -> None:
    state_file = Path(tempfile.mkdtemp()) / "wix-mock.json"
    env = {
        **os.environ,
        "DRY_RUN": "1",
        "WIX_API_KEY": "",      # sunni mock-režiim ka võtme olemasolul
        "WIX_SITE_ID": "",
        "WIX_MOCK_FILE": str(state_file),
    }
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER)], env=env)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = {t.name for t in (await session.list_tools()).tools}
            assert tools == {"list_orders", "create_coupon",
                             "check_coupon_usage"}, tools
            print(f"1/5 tööriistad õiged: {sorted(tools)}")

            orders = await call(session, "list_orders", {})
            assert orders["mode"] == "mock" and orders["orders"] == []
            print("2/5 list_orders töötab (tühi mock)")

            coupon = await call(session, "create_coupon", {
                "deal_id": "TEST-1", "percent_off": 100,
                "name": "naidis test-deal TEST-1",
            })
            assert coupon["percent_off"] == 100 and coupon["dry_run"]
            code = coupon["code"]
            print(f"3/5 100% näidisekupong loodud: {code}")

            usage = await call(session, "check_coupon_usage",
                               {"code": code})
            assert usage["exists"] and not usage["used"]
            assert usage["deal_id"] == "TEST-1"
            print("4/5 kupong leitav, veel lunastamata")

            # Simuleeri lunastust: tellimus kupongiga otse olekufaili
            # (sama tee, mida päris Wix täidaks).
            state = json.loads(state_file.read_text())
            state["orders"].append({
                "order_id": "mock-1", "number": "10001",
                "created_at": "2026-06-12T12:00:00+00:00",
                "buyer_email": "karmen@kood.tech",
                "coupon_code": code, "total": "0",
                "currency": "EUR", "line_items": ["RavimusVET näidis"],
            })
            state["coupons"][code]["usage_count"] = 1
            state_file.write_text(json.dumps(state))

            usage = await call(session, "check_coupon_usage",
                               {"code": code})
            assert usage["used"] and usage["usage_count"] == 1
            orders = await call(session, "list_orders", {})
            assert orders["orders"][0]["coupon_code"] == code
            print("5/5 lunastus nähtav: tellimus + kasutatud kupong")

    dry_log = REPO_ROOT / "logs" / "dry-run-wix.md"
    assert dry_log.exists() and "create_coupon" in dry_log.read_text()
    print(f"DRY_RUN logi kirjutatud: {dry_log.relative_to(REPO_ROOT)}")
    print("SMOKE-TEST OK")


if __name__ == "__main__":
    asyncio.run(main())
