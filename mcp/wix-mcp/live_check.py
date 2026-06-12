"""wix-mcp live-kontroll: kontrollib serverit PÄRIS Wixi API vastu.

Jooksutatakse masinas, kus on Wixi võti (.env: WIX_API_KEY +
WIX_SITE_ID). Vaikimisi ainult loeb (list_orders). Lipuga --write
loob lisaks ühe selgelt märgistatud TEST-kupongi (1%, aegub 1 päevaga)
ja kontrollib selle leitavust — see on ainus kirjutus.

    .venv/bin/python mcp/wix-mcp/live_check.py           # ainult lugemine
    .venv/bin/python mcp/wix-mcp/live_check.py --write   # + TEST-kupong

Vea korral prinditakse API täisvastus: kopeeri kogu väljund PR #6
kommentaari, see on parandamiseks vajalik info.
"""

import asyncio
import json
import os
import secrets
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).parent / "server.py"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_dotenv() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class CheckFailed(Exception):
    """Kontroll kukkus läbi; sõnum prinditakse ilma traceback'ita."""


async def call(session: ClientSession, tool: str, args: dict) -> dict:
    result = await session.call_tool(tool, args)
    if result.isError:
        detail = "\n".join(getattr(b, "text", str(b))
                           for b in result.content)
        raise CheckFailed(f"VIGA tööriistas {tool}:\n{detail}")
    return json.loads(result.content[0].text)


async def main() -> None:
    write = "--write" in sys.argv
    load_dotenv()
    if not (os.environ.get("WIX_API_KEY") and os.environ.get("WIX_SITE_ID")):
        raise CheckFailed(
            "VIGA: WIX_API_KEY ja WIX_SITE_ID puuduvad .env-ist.\n"
            "See kontroll käib päris Wixi vastu ja vajab võtit.")

    steps = 3 if write else 1
    env = {**os.environ, "DRY_RUN": "0" if write else "1"}
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER)], env=env)

    async with stdio_client(params) as (read, stream_write):
        async with ClientSession(read, stream_write) as session:
            await session.initialize()

            orders = await call(session, "list_orders", {"limit": 5})
            assert orders["mode"] == "live", \
                f"oodatud live-režiim, sain {orders['mode']} — kas võti on .env-is?"
            n = len(orders["orders"])
            print(f"1/{steps} list_orders OK (live): {n} tellimust")
            if n:
                o = orders["orders"][0]
                print(f"      värskeim: nr {o['number']}, "
                      f"{o['created_at']}, {o['total']} {o['currency']}")

            if not write:
                print("LIVE-KONTROLL OK (ainult lugemine; kirjutuse "
                      "kontrolliks lisa --write)")
                return

            code = f"RVET-LIVECHECK-{secrets.token_hex(2).upper()}"
            coupon = await call(session, "create_coupon", {
                "deal_id": "TEST-LIVE", "percent_off": 1,
                "name": "wp4 live-kontroll TEST, voib kustutada",
                "code": code, "expires_days": 1,
            })
            assert coupon["mode"] == "live", coupon
            print(f"2/{steps} create_coupon OK (live): {code}, 1%, aegub 1 p")

            usage = await call(session, "check_coupon_usage", {"code": code})
            assert usage["mode"] == "live", usage
            assert usage["exists"], \
                f"loodud kupongi ei leitud query'ga: {usage}"
            assert not usage["used"]
            print(f"3/{steps} check_coupon_usage OK (live): leitav, "
                  "lunastamata")
            print(f"LIVE-KONTROLL OK. TEST-kupong {code} jäi poodi "
                  "(aegub ise 1 päevaga; võib Wixi dashboardist kustutada).")


def _leaves(exc: BaseException):
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            yield from _leaves(sub)
    else:
        yield exc


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except* CheckFailed as group:
        for exc in _leaves(group):
            print(f"\n{exc}", file=sys.stderr)
        print("\nKopeeri kogu väljund PR #6 kommentaari.", file=sys.stderr)
        sys.exit(1)
