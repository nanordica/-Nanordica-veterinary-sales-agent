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
| Jagatud loogika | Puhtad API-kliendid `mcp/lib/`-is | Disainidoc'i `lib/` nõue; setup- ja discovery-skript taaskasutavad sama klienti |
| Oleku tõde | **Kogu olek Pipedrive'is** | Kaitserauad loevad Pipedrive'i deal'i field'e; eraldi kohalikku ledgerit pole |
| Provisioneerimine | Setup-skript `lib/`-i kaudu | Pipeline + staadiumid + custom field'id on admin-operatsioon, mitte MCP-tööriist |

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
    pipedrive_client.py   # puhas Pipedrive klient (sh admin: pipeline/stage/field loomine)
    graph_client.py       # MS Graph app-only klient (saatmine + delta-lugemine)
    wix_client.py         # Wix klient (tellimused + kupongid)
    dryrun.py             # DRY_RUN abi + kavatsuse logija
  scripts/
    pipedrive_setup.py    # idempotentne: loob pipeline + 8 staadiumi + custom field'id
  tools/
    __init__.py
    pipedrive_deals.py
    pipedrive_persons.py
    pipedrive_fields.py
    mail.py
    wix.py
  data/                   # gitignore'itud: graph delta-token cursor
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

#### Pipeline provisioneerimine (`scripts/pipedrive_setup.py`)

Esmane samm: deterministlik **idempotentne** skript, mis loob projekti
oma pipeline'i, kui seda veel pole. Kasutab `lib/pipedrive_client.py`
admin-meetodeid (`get_pipelines` / `create_pipeline`, `get_stages` /
`create_stage`, `get_deal_fields` / `create_deal_field`). Need
admin-meetodid elavad `lib/`-is, **aga neid ei avata MCP-tööriistana** —
MCP pind jääb kitsas. Skript:

1. Otsib pipeline'i nimega `ravimus-latvia-vets`; puudumisel loob.
2. Tagab 8 staadiumi õiges järjekorras (Discovered → Enriched →
   Qualified → Contacted → Engaged → Näidis tellitud → Won → Lost).
3. Tagab kõik custom field'id deal'il (disainidoc'i tabel: `registry_id`,
   `email`, `clinic`, `specialization`, `network`, `decision_style`,
   `score`, `ab_variant`, `personal_link`, `discount_code`,
   `sample_claimed_at`, `emails_sent`, `last_contact_at`, `lost_reason`).
4. Korduval käivitusel ei loo duplikaate — kontrollib olemasolu nime/key järgi.

Käivitatakse üks kord enne discovery't; `DRY_RUN=1` korral logib
kavandatud loomised neid tegemata.

### E-mail — MS Graph (`mail_*`)

App-only (client-credentials) voog, saatja `ravimus@nanordica.com`.
Krediit: `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`,
`GRAPH_SENDER`. Kaitserauad jõustatakse **siin, koodis**, lugedes seisu
**Pipedrive'i deal'ilt** (kogu tõde on Pipedrive'is). `mail_send` impordib
`lib/pipedrive_client.py` ja töötab `deal_id` põhjal.

| Tööriist | Tüüp | Sisu |
|---|---|---|
| `mail_send(deal_id, to, subject, body_html)` | write | Saadab; jõustab kaitserauad deal'i field'idelt; uuendab deal'i pärast |
| `mail_list_new_messages(folder?)` | read | Inbox-triage loeb uued kirjad Graphi delta-cursor'iga |
| `mail_check_config()` | read | Diagnostika: kas Graph krediit + sender seatud |

**`mail_send` kaitserauad (kõik koodis, enne API-kõnet, Pipedrive'i deal'ilt):**
1. `DRY_RUN=1` → logib kavandatud kirja, ei saada.
2. Loeb deal'i; kontrollib et deal'i `email` == `to` (vale deal'i kaitse).
3. `lost_reason == opt-out` (deal Lost-staadiumis) → keeldub.
4. `last_contact_at` < 24 h → keeldub (≤ 1 kiri / saaja / 24 h).
5. `emails_sent` ≥ 5 → keeldub (≤ 5 kirja / saaja kokku).

Õnnestunud saatmine uuendab Pipedrive'i deal'i **enne** edukat tagastust:
`last_contact_at` = nüüd ja `emails_sent` += 1 (atomiseerib saatmise +
logimise MCP-kihis; `last_contact_at` enne note'i → topeltsaatmist ei
teki), seejärel lisab note'i kirja sisuga.

Opt-out'i ei hallata mail-serveris — see on Pipedrive'i operatsioon
(`pipedrive_move_deal_stage` Lost + `pipedrive_update_deal_fields`
`lost_reason=opt-out`), mille teeb inbox-triage. Discovery dedup
`registry_id` järgi tagab, et opt-out'itud vetti uuesti ei looda.

**Teadlikult puudu:** kustutamine, teiste kaustade lugemine, teiste
postkastide nimel saatmine, eraldi opt-out-nimekiri.

### Wix (`wix_*`)

Krediit: `WIX_API_KEY`, `WIX_SITE_ID`, `WIX_ACCOUNT_ID` (kõik olemas;
sait "Nanordica Medical" → nanordica.com). Auth-header'id `lib/wix_client.py`-s:
`Authorization: <WIX_API_KEY>` (**toores, ilma `Bearer`-ita**),
`wix-account-id: <WIX_ACCOUNT_ID>`, `wix-site-id: <WIX_SITE_ID>`.

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
| `WIX_API_KEY` | Wix | olemas (ainult `.env`) |
| `WIX_SITE_ID` | Wix | olemas (`465df77a-...`) |
| `WIX_ACCOUNT_ID` | Wix | olemas (`47e317b2-...`) |
| `DRY_RUN` | platvorm | `1` arenduses |
| `MCP_PORT` | platvorm | vaikimisi 8765 |
| `MCP_AUTH_TOKEN` | platvorm | valikuline Bearer-auth |
| `LOG_LEVEL` | platvorm | vaikimisi INFO |
| `GRAPH_DELTA_PATH` | mail | delta-cursor cache, vaikimisi `./data/graph_delta.json` |

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
2. **Pipeline setup**: `pipedrive_setup.py` `DRY_RUN=1` all logib kavandatud
   pipeline/staadiumid/field'id; live-käivitus loob need; **teine** live-käivitus
   ei loo duplikaate (idempotentsus).
3. **Lugemised päriselt** (kui tokenid käes): `pipedrive_check_config`
   + `pipedrive_list_deals`; `mail_check_config`; `wix_check_config`.
4. **Kirjutused `DRY_RUN=1` all**: `mail_send`, `pipedrive_create_person`,
   `wix_create_coupon` → kõik logivad kavatsuse, **midagi ei saadeta/looda**.
5. Kaitserauad: `mail_send` keeldub (a) opt-out deal'ile (`lost_reason=opt-out`),
   (b) kui deal'i `last_contact_at` < 24 h, (c) kui `emails_sent` ≥ 5,
   (d) kui deal'i `email` ei klapi `to`-ga.

"Valmis" = setup idempotentne, kõik kolm `*_check_config` rohelised, kõik
kirjutused DRY_RUN-is logitud-aga-tegemata, ja neli kaitserauda jõustuvad.

## Ehitusjärjekord

1. **Platvormi tuum**: `mcp/` skelett `isiklik/MCP`-st (server.py,
   mcp_app.py, server_registry.py, Docker, requirements) — ainult
   `ping` + `server_info`, käivitub `/mcp`-l.
2. **DRY_RUN tuum**: `lib/dryrun.py` — kasutavad kõik järgnevad write'id.
3. **Pipedrive klient + tööriistad**: `lib/pipedrive_client.py` (sh
   admin-meetodid) + `tools/pipedrive_*.py`; smoke-test read'id + dry-run write'id.
4. **Pipeline setup**: `scripts/pipedrive_setup.py` — loob pipeline +
   staadiumid + custom field'id idempotentselt; smoke-test (dry-run →
   live → teine live ilma duplikaatideta).
5. **Mail**: `lib/graph_client.py` (app-only token) + `tools/mail.py`
   koos kaitserautadega (loevad Pipedrive'i deal'ilt); smoke-test dry-run
   + kaitseraua-loogika.
6. **Wix**: `lib/wix_client.py` + `tools/wix.py`; smoke-test read +
   dry-run coupon.
7. **`.mcp.json` + README**: registreeri server, dokumenteeri tööriistad
   ja `.env`.

Iga samm on eraldi verifitseeritav; järgmist ei alustata enne, kui
eelmise smoke-test läbib.

## Lahtised punktid

- **MS Graphi admin consent + Application Access Policy** kinnitab
  rentniku admin.
- **Discovery-skript** (`scripts/discovery.py`) taaskasutab
  `lib/pipedrive_client.py`-d otse — see on eraldi tööpakett, mitte
  selle MCP-kihi osa.
- **Disainidoc'i transpordirea** (stdio → HTTP üks-endpoint)
  sünkroniseerimine.
