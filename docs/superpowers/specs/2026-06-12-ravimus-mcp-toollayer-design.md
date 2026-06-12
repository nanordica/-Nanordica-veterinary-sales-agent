# Ravimus tööriistakiht — MCP serveri disain

*Seis: 2026-06-12, v1. Realiseerib
[ravimus-lead-pipeline-design.md](../../ravimus-lead-pipeline-design.md)
jaotise "Tööriistakiht". Koodialus: `isiklik/MCP` (FastMCP
mitmikserver-platvorm). Krediidid hoitakse ainult gitignore'itud
`.env`-is.*

## Ülevaade

Pipeline'i agendid ei kutsu väliseid API-sid otse. Kogu Pipedrive'i,
e-maili (MS Graph) ja Wixi suhtlus käib läbi ühe kohaliku MCP serveri,
mis avab **ainult kitsa, lubatud operatsioonide pinna** ja jõustab
kaitserauad deterministlikult koodis. Live-süsteemi ohutus ei sõltu
agendi heast käitumisest.

Ehitatakse `isiklik/MCP` FastMCP-platvormi alusel, kuid kärbituna: alles
jäävad ainult platvormi tuum (`server.py` auto-loader, `mcp_app.py`,
`server_registry.py`, Docker) ja kolme süsteemi tööriistad. Kogu
isiklik-spetsiifika (NM ~40 tööriista, meditsiin, zotero,
financial_analyst, IBKR, files, notify) jäetakse välja.

## Arhitektuuriotsused

| Otsus | Valik | Põhjus |
|---|---|---|
| Transport | HTTP mitmikserver-platvorm | Peegeldab `isiklik/MCP` alust |
| Endpoint | **Üks `/mcp`** kõigile tööriistadele | Kasutaja soov: üks ühendus, üks `.mcp.json` kirje |
| Tööriistanimed | Prefiksitud: `pipedrive_*`, `mail_*`, `wix_*` | Selge päritolu ühel endpointil |
| Krediidid | `.env` keskkonnamuutujad | Üks rentnik (üks Ravimus pipeline); isikliku per-request header-mehhanismi pole vaja |
| Kood vs stub | Päris API-kliendid + `DRY_RUN` lüliti | Smoke-testitav niipea kui tokenid käes |
| Jagatud loogika | Puhtad API-kliendid `mcp/lib/`-is | Disainidoc'i `lib/` nõue; discovery-skript taaskasutab sama klienti |

**Kõrvalekalle disainidoc'ist:** "Tööriistakiht" kirjeldab servereid kui
stdio + `.mcp.json`. Siin valiti HTTP üks-endpoint. Disainidoc'i vastav
rida tuleb hiljem üle vaadata (selle ehituse skoobist väljas).

## Kaustastruktuur

```
mcp/
  README.md
  requirements.txt
  Dockerfile
  docker-compose.yaml
  .env.example            # ainult placeholder'id
  .gitignore              # .env, data/
  server.py               # mitmikserver-loader (kärbitud isiklik'ust)
  mcp_app.py              # default server + ping / server_info
  server_registry.py      # create_server + register
  lib/
    __init__.py
    pipedrive_client.py   # puhas Pipedrive klient (taaskasutab discovery.py)
    graph_client.py       # MS Graph app-only klient (saatmine + delta-lugemine)
    wix_client.py         # Wix klient (tellimused + kupongid)
    dryrun.py             # DRY_RUN abi + kavatsuse logija
    mail_ledger.py        # SQLite saatmislogi + opt-out blokeerimisnimekiri
  tools/
    __init__.py
    pipedrive_deals.py
    pipedrive_persons.py
    pipedrive_fields.py
    mail.py
    wix.py
  data/                   # gitignore'itud: mail_ledger.db, graph delta token
```

Kõik `tools/`-i lamefailid registreeruvad default serveril `/mcp`.
Tööriistafailid on **õhukesed mähised** `lib/`-i klientide ümber.

## Tööriistapind

### Pipedrive (`pipedrive_*`)

Lugemine + kitsad kirjutused. Krediit: `PIPEDRIVE_API_TOKEN` +
`PIPEDRIVE_DOMAIN`. Rate-limit'i käsitlus laenatakse isiklik
`NM/_api.py`-st (iga vastus sisaldab `_rate_limit` välja; 429 → struktuurne viga).

| Tööriist | Tüüp | Sisu |
|---|---|---|
| `pipedrive_get_deal(deal_id)` | read | Üks deal koos custom field'idega |
| `pipedrive_list_deals(stage_id?, status?)` | read | Kompaktne deal'ide loend (tikk loeb pipeline'i seisu) |
| `pipedrive_search_persons(term, field?)` | read | Seo sissetulev e-mail / tellimus deal'iga |
| `pipedrive_get_deal_fields()` | read | Deal'i field'ide definitsioonid + enum option ID-d |
| `pipedrive_get_person_fields()` | read | Person'i field'ide definitsioonid + enum option ID-d |
| `pipedrive_create_person(name, email, custom_fields?)` | write | Discovery / uus kontakt |
| `pipedrive_update_person(person_id, fields)` | write | Enrichment täiendab kontakti |
| `pipedrive_create_deal(person_id, title, stage_id, custom_fields?)` | write | Uus deal |
| `pipedrive_update_deal_fields(deal_id, fields)` | write | score, ab_variant, emails_sent, last_contact_at jne |
| `pipedrive_move_deal_stage(deal_id, stage_id)` | write | Staadiumimuutus (eraldi tööriist → selgem kaitseraud) |
| `pipedrive_add_note(deal_id, content)` | write | Logi kirjavahetus deal'i note'ina |
| `pipedrive_check_config()` | read | Diagnostika: kas token/domain seatud |

**Teadlikult puudu:** kustutamine, masskirjutus, admin, toodete/hindade muutmine.

### E-mail — MS Graph (`mail_*`)

App-only (client-credentials) voog, saatja `ravimus@nanordica.com`.
Krediit: `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`,
`GRAPH_SENDER`. Kaitserauad jõustatakse **siin, koodis**, kohaliku
saatmislogi (`lib/mail_ledger.py`) põhjal — sõltumatu agendi/Pipedrive'i
korrektsusest.

| Tööriist | Tüüp | Sisu |
|---|---|---|
| `mail_send(to, subject, body_html)` | write | Saadab; jõustab kõik kaitserauad (vt all) |
| `mail_list_new_messages(folder?)` | read | Inbox-triage loeb uued kirjad delta-tokeniga |
| `mail_add_optout(email, reason?)` | write | Lisab aadressi püsivasse blokeerimisnimekirja |
| `mail_list_optouts()` | read | Blokeerimisnimekirja loend |
| `mail_check_config()` | read | Diagnostika: kas Graph krediit + sender seatud |

**`mail_send` kaitserauad (kõik koodis, enne API-kõnet):**
1. `DRY_RUN=1` → logib kavandatud kirja, ei saada.
2. Opt-out blokeerimisnimekirjas → keeldub.
3. Sama saaja viimane kiri < 24 h → keeldub (≤ 1 kiri / saaja / 24 h).
4. Saaja kirjade arv ≥ 5 → keeldub (≤ 5 kirja / saaja kokku).

Õnnestunud saatmine kirjutab saatmislogisse (timestamp + loendur)
**enne** edukat tagastust, et topeltsaatmist ei tekiks.

**Teadlikult puudu:** kustutamine, teiste kaustade lugemine, teiste postkastide nimel saatmine.

### Wix (`wix_*`)

Krediit: `WIX_API_KEY`, `WIX_SITE_ID`, `WIX_ACCOUNT_ID`.

| Tööriist | Tüüp | Sisu |
|---|---|---|
| `wix_list_orders(since?)` | read | Sales-detector pollib uusi tellimusi |
| `wix_create_coupon(name, code, type, value, ...)` | write | Personaalne kupong (sh 100% näidisekupong) |
| `wix_check_coupon_usage(code)` | read | Kupongi kasutuse kontroll |
| `wix_check_config()` | read | Diagnostika: kas API-võti + site/account seatud |

**Teadlikult puudu:** toodete/hindade muutmine, tagasimaksed.

## DRY_RUN — live-ohutuse lüliti

`DRY_RUN=1` (vaikimisi arenduses) korral suunatakse iga **kirjutav**
tööriist (`mail_send`, `pipedrive_create_*`, `pipedrive_update_*`,
`pipedrive_move_*`, `pipedrive_add_note`, `wix_create_coupon`) läbi
`lib/dryrun.py`, mis logib kavatsetud kõne ja tagastab simuleeritud
õnnestumise **ilma API-d puudutamata**. Lugemised käivad alati päriselt.
Üks keskkonnamuutuja viib kogu kihi live'i (disainidoc'i faas 1 nõue).

## Saatmislogi skeem (`lib/mail_ledger.py`, SQLite)

```sql
CREATE TABLE sent (
  recipient   TEXT NOT NULL,
  sent_at     TEXT NOT NULL,   -- ISO-8601 UTC
  subject     TEXT,
  dry_run     INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE optout (
  email       TEXT PRIMARY KEY,
  reason      TEXT,
  added_at    TEXT NOT NULL
);
```

`mail_send` küsib enne saatmist: `optout` sisaldab saajat? viimane
`sent.sent_at` < 24 h? `COUNT(sent)` saaja kohta ≥ 5? Asukoht:
`MAIL_LEDGER_DB` (vaikimisi `./data/mail_ledger.db`).

## `.env` muutujad

`.env.example` sisaldab ainult placeholder'eid; päris väärtused
gitignore'itud `.env`-is.

| Muutuja | Süsteem | Märkus |
|---|---|---|
| `PIPEDRIVE_API_TOKEN` | Pipedrive | olemas |
| `PIPEDRIVE_DOMAIN` | Pipedrive | `nanordica.pipedrive.com` |
| `GRAPH_TENANT_ID` | MS Graph | olemas (API.zip) |
| `GRAPH_CLIENT_ID` | MS Graph | olemas (API.zip) |
| `GRAPH_CLIENT_SECRET` | MS Graph | olemas (API.zip) — ainult `.env` |
| `GRAPH_SENDER` | MS Graph | `ravimus@nanordica.com` |
| `WIX_API_KEY` | Wix | luuakse Wixi dashboardis |
| `WIX_SITE_ID` | Wix | Wixi saidi seaded |
| `WIX_ACCOUNT_ID` | Wix | Wixi konto seaded |
| `DRY_RUN` | platvorm | `1` arenduses |
| `MCP_PORT` | platvorm | vaikimisi 8765 |
| `MCP_AUTH_TOKEN` | platvorm | valikuline Bearer-auth |
| `LOG_LEVEL` | platvorm | vaikimisi INFO |
| `MAIL_LEDGER_DB` | mail | vaikimisi `./data/mail_ledger.db` |

## Välised ligipääsunõuded

### MS Graph (rentniku admin peab kinnitama)
- App'il **Application**-õigused `Mail.Send` + `Mail.Read`, **admin
  consent antud**.
- Soovitatud: **Application Access Policy** Exchange'is, mis piirab
  app'i ainult `ravimus@nanordica.com` postkastiga (ei saa teiste
  nimel saata/lugeda).

### Wix API-võti
| Operatsioon | Wix API | Õigus |
|---|---|---|
| `wix_list_orders` | eCommerce → Orders | Read Orders |
| `wix_create_coupon` | Marketing → Coupons | Manage Coupons |
| `wix_check_coupon_usage` | Marketing → Coupons | Read Coupons |

## Verifitseerimine — "valmis" definitsioon

Iga süsteemi smoke-test ilma live-kõrvalmõjudeta:

1. Stack püsti (`docker compose up`), `/mcp` `ping` → `pong`.
2. **Lugemised päriselt** (kui tokenid käes): `pipedrive_check_config`
   + `pipedrive_list_deals`; `mail_check_config`; `wix_check_config`.
3. **Kirjutused `DRY_RUN=1` all**: `mail_send`, `pipedrive_create_person`,
   `wix_create_coupon` → kõik logivad kavatsuse, **midagi ei saadeta/looda**.
4. Kaitserauad: `mail_send` keeldub (a) opt-out aadressile, (b) kui
   sama saaja sai < 24 h tagasi kirja, (c) kui saaja loendur ≥ 5.

"Valmis" = kõik kolm `*_check_config` rohelised, kõik kirjutused
DRY_RUN-is logitud-aga-tegemata, ja neli kaitserauda jõustuvad.

## Ehitusjärjekord

1. **Platvormi tuum**: `mcp/` skelett `isiklik/MCP`-st (server.py,
   mcp_app.py, server_registry.py, Docker, requirements) — ainult
   `ping` + `server_info`, käivitub `/mcp`-l.
2. **Pipedrive**: `lib/pipedrive_client.py` + `tools/pipedrive_*.py` +
   `DRY_RUN` mähis; smoke-test read'id + dry-run write'id.
3. **DRY_RUN tuum**: `lib/dryrun.py` (kasutab juba sammus 2).
4. **Mail**: `lib/graph_client.py` (app-only token) + `lib/mail_ledger.py`
   + `tools/mail.py` koos nelja kaitserauaga; smoke-test dry-run +
   ledger-loogika.
5. **Wix**: `lib/wix_client.py` + `tools/wix.py`; smoke-test read +
   dry-run coupon.
6. **`.mcp.json` + README**: registreeri server, dokumenteeri tööriistad
   ja `.env`.

Iga samm on eraldi verifitseeritav; järgmist ei alustata enne, kui
eelmise smoke-test läbib.

## Lahtised punktid

- **Wixi tokenid** (API-võti, Site/Account ID) tulevad kasutajalt;
  kuni siis arendame `DRY_RUN`-i ja read-config'iga.
- **MS Graphi admin consent + Application Access Policy** kinnitab
  rentniku admin.
- **Discovery-skript** (`scripts/discovery.py`) taaskasutab
  `lib/pipedrive_client.py`-d otse — see on eraldi tööpakett, mitte
  selle MCP-kihi osa.
- **Disainidoc'i transpordirea** (stdio → HTTP üks-endpoint)
  sünkroniseerimine.
