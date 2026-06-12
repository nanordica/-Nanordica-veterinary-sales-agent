# Töökäsk Mardile: wix-mcp live-kontroll

**Kellelt:** Karmen (wp4) · **Aeg:** ~10 min · **Haru:**
`feature/wp4-sales-detection-launch` (PR #6)

## Miks sina

`wix-mcp` server on valmis ja mock-režiimis testitud, aga päris Wixi
API kõnesid pole kordagi jooksutatud, sest võti on ainult sinu
arvutis. Võti EI lähe giti: paned selle oma lokaalsesse `.env`-i, mis
on gitignore'itud, ja server loeb seda sealt.

## Eeldused

- Wixi API võti (scope: eCommerce read + Coupons manage) ja poe site ID
- `python3` (≥ 3.10) ja `git`/`gh` masinas olemas

NB: kontrolliskript käivitab wix-mcp serveri `DRY_RUN=0`-ga, sest
live-kontrolli mõte ongi päris API-d puudutada. Sinu `.env`-i
`DRY_RUN=1` jääb kehtima kõigele muule; ilma `--write` lipuga ei tee
skript ühtegi kirjutust.

## Sammud

```sh
cd <team-17 repo>
git fetch origin
git checkout feature/wp4-sales-detection-launch && git pull

python3 -m venv .venv
.venv/bin/pip install -r mcp/wix-mcp/requirements.txt

cp -n .env.template .env   # kui .env juba on, jäta vahele
```

Ava `.env` ja täida (jäta `DRY_RUN=1` nagu on):

```
WIX_API_KEY=<sinu võti>
WIX_SITE_ID=<poe site ID>
```

**Kontroll 1, ainult lugemine** (ei muuda poes midagi):

```sh
.venv/bin/python mcp/wix-mcp/live_check.py
```

Oodatav lõpp: `1/1 list_orders OK (live): N tellimust` ja
`LIVE-KONTROLL OK`.

**Kontroll 2, kirjutus** (loob poodi ÜHE test-kupongi: 1%, ühekordne,
nimi "wp4 live-kontroll TEST", aegub ise 1 päevaga; võid pärast Wixi
dashboardist kustutada):

```sh
.venv/bin/python mcp/wix-mcp/live_check.py --write
```

Oodatav lõpp: kolm `OK (live)` rida ja `LIVE-KONTROLL OK`.

## Raporteeri

Kleebi mõlema jooksu väljund PR #6 kommentaari:

```sh
gh pr comment 6 --body "live-kontroll: <kleebi väljund>"
```

(või GitHubi veebis). Võtit väljund ei sisalda, kleepida on ohutu.

## Kui kukub läbi

Kleebi KOGU veaväljund ikkagi PR #6 kommentaari. Tõenäoline põhjus:
Wixi vastuse täpne kuju erineb sellest, mida Karmen ilma võtmeta
kirjutas (endpoint'id `ecom/v1/orders/search`, `stores/v2/coupons`,
`stores/v2/coupons/query` failis `mcp/wix-mcp/server.py`). Kaks
võimalust:

1. jäta väljund PR-i ja Karmen parandab; või
2. lase oma Claude'il `server.py` ära parandada ja pushi samale
   harule — mock-režiimi regressiooni kontrollib
   `.venv/bin/python mcp/wix-mcp/smoke_test.py` (peab lõppema
   `SMOKE-TEST OK`).
