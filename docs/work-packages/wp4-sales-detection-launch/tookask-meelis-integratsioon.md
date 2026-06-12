# Töökäsk Meelisele: integratsioon võtmetega masinas

**Kellelt:** Karmen (wp4, testifaaside koordinaator) · **Aeg:** ~45 min
· **Kus:** sinu masin (võtmed on nüüd sinul) · **Raport:** issue #7

Kogu kood on main'is. Need sammud on ainsad, mis seisavad faasi 1
(DRY_RUN täisjooks) ees, ja nad käivad järjekorras.

## 1. Võtmed ja server (~15 min)

1. Täida oma `.env` (vt `mcp/.env.example`): `PIPEDRIVE_API_TOKEN`,
   `WIX_API_KEY`, `WIX_ACCOUNT_ID`, `WIX_SITE_ID`, MS Graphi muutujad.
   Jäta `DRY_RUN=1`. Võtmed EI lähe giti.
2. Käivita ravimus server (`mcp/README.md`) ja Claude Code repo
   juurest.
3. Jooksuta `pipedrive_setup` (`mcp/scripts/pipedrive_setup.py`) —
   loob pipeline'i, staadiumid ja stage-kaardi
   (`data/field_keys.json`). Ilma selleta keeldub `/tick` töötamast.
4. Lisa `mcp/lib/constants.py` `STATE_KEYS` loendisse kaks võtit:
   `sample_reminder_sent` ja `thanked_at` (tikk kasutab neid
   dedup-markeritena; vt PR #11).

## 2. Live-kontrollid (~15 min) — ainsad kohad, kus kood pole päris API-t näinud

Wix (raporteeri issue #7 alla):

- `wix_check_config` → kolm `true` (API-d ei puuduta).
- `wix_list_orders(limit=5)` → tagastab tellimused (ainult lugemine;
  tühi pood = tühi loend, OK).
- `wix_create_coupon(name="wp4 live-kontroll TEST", code="RVET-LIVECHECK-1", percent_off=1)`
  `DRY_RUN=1`-ga → peab andma `dry_log` kirje, MITTE päris kupongi.
- Päris kirjutus: hetkeks `DRY_RUN=0`, loo sama 1% TEST-kupong
  päriselt, `wix_check_coupon_usage("RVET-LIVECHECK-1")` → leitav,
  lunastamata. `DRY_RUN=1` tagasi; kupongi võid dashboardist
  kustutada.

Mail: `mail_check_config` → kõik seatud; saada `mail_send`-iga üks
testkiri iseendale (`DRY_RUN=0` hetkeks, oma aadress) ja kontrolli, et
see kohale jõuab.

Kui midagi kukub: kleebi TÄISVÄLJUND issue #7 alla (võtit väljundis
pole) — tõenäoline põhjus on Wixi/Graphi vastuse kuju
`mcp/lib/wix_client.py` / `mcp/lib/graph_client.py` failis.

## 3. Discovery päris registri peal (~15 min)

`mcp/scripts/registry.py` + `mcp/scripts/discovery.py` jooks: register
sisse, e-mailiga vetid deal'idena staadiumis Discovered. Kontrolli, et
duplikaate pole ja arv on mõistlik.

## Pärast sind

Faasi 1 koordineerib Karmen: cron (`scripts/install-cron.sh`) sinu
masinas käima, üks käsitsi `/tick`, kogu tiim loeb logid üle —
[launch-checklist.md](launch-checklist.md). Sales-detectori
deal'i-sidumise test: [sales-detector-integration-test.md](sales-detector-integration-test.md).
