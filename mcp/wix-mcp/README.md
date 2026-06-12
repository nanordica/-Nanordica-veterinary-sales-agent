# wix-mcp

Kitsas MCP server Wixi poe jaoks (wp4). Avab kolm tööriista:

| Tööriist | Mis teeb |
|---|---|
| `list_orders` | tellimuste loetelu (`since` + `limit`) |
| `create_coupon` | personaalne protsendikupong, alati ühekordne; 100% = tasuta näidis |
| `check_coupon_usage` | kas kood on lunastatud |

Toodete/hindade muutmist ja tagasimakseid teadlikult ei avata
(disain: [tööriistakiht](../../docs/ravimus-lead-pipeline-design.md#tööriistakiht--kohalikud-mcp-serverid)).

## Režiimid

- **Live**: `.env`-is on `WIX_API_KEY` + `WIX_SITE_ID` (Mardilt).
- **Mock**: võtmeta hoiab olekut failis `cache/wix-mock.json`, et
  sales-detectorit saaks testida ilma Wixita.
- **DRY_RUN** (`DRY_RUN=1`, vaikimisi sees): `create_coupon` logib
  kavandatud tegevuse faili `logs/dry-run-wix.md` ega puutu päris
  Wixi. Lugemised käivad live-režiimis ikka päris API vastu.

Live-režiimi Wixi kõnesid pole päris API võtmega veel jooksutatud.
Kontroll käib võtmega masinas (Mart):
`.venv/bin/python mcp/wix-mcp/live_check.py` (ainult lugemine) ja
`--write` lipuga lisaks üks TEST-kupong. Töökäsk:
[tookask-mart-wix-live-check.md](../../docs/work-packages/wp4-sales-detection-launch/tookask-mart-wix-live-check.md).

## Paigaldus ja test

```sh
python3 -m venv .venv
.venv/bin/pip install -r mcp/wix-mcp/requirements.txt
.venv/bin/python mcp/wix-mcp/smoke_test.py   # peab lõppema "SMOKE-TEST OK"
```

Server on registreeritud `.mcp.json`-is (teed on repo juure suhtes,
seega käivita Claude Code repo juurest).
