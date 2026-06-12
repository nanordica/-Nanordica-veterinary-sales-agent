"""wix-mcp live-kontroll: kontrollib serverit PÄRIS Wixi API vastu.

Jooksutatakse masinas, kus on Wixi võti (.env: WIX_API_KEY +
WIX_SITE_ID). Vaikimisi ainult loeb (list_orders). Lipuga --write
loob lisaks ühe selgelt märgistatud TEST-kupongi (1%, aegub 1 päevaga)
ja kontrollib selle leitavust — see on ainus kirjutus.

NB! See skript käivitab serveri DRY_RUN=0-ga, sest live-kontrolli
mõte ongi päris API-d puudutada. Ilma --write lipuga ühtegi kirjutavat
tööriista ei kutsuta, nii et pood jääb puutumata.

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

from server import _load_dotenv  # sama .env-laadur, mida server ise kasutab

SERVER = Path(__file__).parent / "server.py"


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
    _load_dotenv()
    if not (os.environ.get("WIX_API_KEY") and os.environ.get("WIX_SITE_ID")):
        raise CheckFailed(
            "VIGA: WIX_API_KEY ja WIX_SITE_ID puuduvad .env-ist.\n"
            "See kontroll käib päris Wixi vastu ja vajab võtit.")
    if write:
        print("NB: --write teeb ühe PÄRIS kirjutuse (TEST-kupong, 1%, "
              "aegub 1 päevaga).", file=sys.stderr)

    steps = 3 if write else 1
    env = {**os.environ, "DRY_RUN": "0"}
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER)], env=env)

    # Viga püütakse SIIN ja visatakse uuesti alles pärast task-group'ide
    # sulgumist, et see ei mattuks ExceptionGroup'i (ja skript töötaks
    # ka Python 3.10-l, kus except* puudub).
    failure = None
    async with stdio_client(params) as (read, stream_write):
        async with ClientSession(read, stream_write) as session:
            try:
                await session.initialize()

                orders = await call(session, "list_orders", {"limit": 5})
                if orders["mode"] != "live":
                    raise CheckFailed(
                        f"oodatud live-režiim, sain {orders['mode']} — "
                        "kas võti on .env-is?")
                n = len(orders["orders"])
                print(f"1/{steps} list_orders OK (live): {n} tellimust")
                if n:
                    o = orders["orders"][-1]
                    print(f"      värskeim: nr {o['number']}, "
                          f"{o['created_at']}, {o['total']} {o['currency']}")

                if write:
                    code = f"RVET-LIVECHECK-{secrets.token_hex(2).upper()}"
                    coupon = await call(session, "create_coupon", {
                        "deal_id": "TEST-LIVE", "percent_off": 1,
                        "name": "wp4 live-kontroll TEST, voib kustutada",
                        "code": code, "expires_days": 1,
                    })
                    if coupon["mode"] != "live":
                        raise CheckFailed(f"create_coupon ei läinud "
                                          f"live-režiimi: {coupon}")
                    print(f"2/{steps} create_coupon OK (live): {code}, "
                          "1%, aegub 1 p")

                    usage = await call(session, "check_coupon_usage",
                                       {"code": code})
                    if not usage.get("exists"):
                        raise CheckFailed("loodud kupongi ei leitud "
                                          f"query'ga: {usage}")
                    print(f"3/{steps} check_coupon_usage OK (live): "
                          "leitav, lunastamata")
            except CheckFailed as exc:
                failure = exc

    if failure:
        raise failure
    if write:
        print("LIVE-KONTROLL OK. TEST-kupong jäi poodi (aegub ise 1 "
              "päevaga; võib Wixi dashboardist kustutada).")
    else:
        print("LIVE-KONTROLL OK (ainult lugemine; kirjutuse kontrolliks "
              "lisa --write)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except CheckFailed as exc:
        print(f"\n{exc}", file=sys.stderr)
        print("\nKopeeri kogu väljund PR #6 kommentaari.", file=sys.stderr)
        sys.exit(1)
