# Töökäsk Mardile: ravimus serveri wix-tööriistade live-kontroll

**Kellelt:** Karmen (wp4) · **Aeg:** ~10 min · **Kus:** sinu masin
(võtmed on sinul) · **Raport:** issue #7

## Miks

Sales-detector (PR #6) ja outreach-writer toetuvad ravimus serveri
tööriistadele `wix_list_orders`, `wix_create_coupon`,
`wix_check_coupon_usage` (`mcp/tools/wix.py` + `mcp/lib/wix_client.py`).
Neid pole päris Wixi API võtmega veel jooksutatud. Võti EI lähe giti:
see elab sinu lokaalses `.env`-is.

## Sammud

1. Täida oma `.env` (vt `mcp/.env.example`): `WIX_API_KEY`,
   `WIX_ACCOUNT_ID`, `WIX_SITE_ID`. Jäta `DRY_RUN=1`.
2. Käivita ravimus server (`mcp/README.md` järgi) ja Claude Code repo
   juurest.
3. Kontrollid, järjest:
   - `wix_check_config` → kõik kolm `true` (API-d ei puuduta).
   - `wix_list_orders(limit=5)` → tagastab tellimused (ainult
     lugemine; tühi pood = tühi loend, see on ka OK).
   - `wix_create_coupon(name="wp4 live-kontroll TEST", code="RVET-LIVECHECK-1", percent_off=1)`
     `DRY_RUN=1`-ga → peab tagastama `dry_log` kirje, MITTE päris
     kupongi looma.
   - Päris kirjutuse kontroll (ainult kui julged): sea hetkeks
     `DRY_RUN=0`, loo sama 1% TEST-kupong päriselt, kontrolli
     `wix_check_coupon_usage("RVET-LIVECHECK-1")` → leitav,
     lunastamata. Keera `DRY_RUN=1` tagasi. Kupongi võid Wixi
     dashboardist kustutada.

## Raporteeri

Kleebi iga kontrolli väljund issue #7 kommentaari (võtit väljundis
pole, kleepida on ohutu) ja sulge issue, kui kõik läbis. Kui midagi
kukub, kleebi täisväljund — Wixi vastuse kuju vajab siis
`mcp/lib/wix_client.py`-s parandust.
