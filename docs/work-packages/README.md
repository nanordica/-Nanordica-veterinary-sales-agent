# Tööpaketid: 3 tunni ehitus

Jagame [ravimus-lead-pipeline-design.md](../ravimus-lead-pipeline-design.md)
ehituse neljaks paketiks, üks inimese kohta. Iga pakett katab disaini
[ehitusjärjekorra](../ravimus-lead-pipeline-design.md#ehitusjärjekord)
kindlad sammud ja on eraldi verifitseeritav. Kõik ehitavad Claude Code'iga;
pakett määrab vastutuse ja valdkonna, mitte "kes oskab koodi".

## Paketid

| Pakett | Omanik | Disaini sammud | Sisu |
|---|---|---|---|
| [wp1-pipedrive-discovery](wp1-pipedrive-discovery/README.md) | Meelis Kadaja | 1, 2, 7 | Pipedrive'i alus, `lib/`, `pipedrive-mcp`, discovery-skriptid, `/tick` |
| [wp2-enrichment-qualification](wp2-enrichment-qualification/README.md) | Mart Roosimaa | 5 | enrichment- ja qualification-agendid, meditsiiniväidete kontroll |
| [wp3-outreach-inbox](wp3-outreach-inbox/README.md) | Annelis Rum | 3, 4 | `mail-mcp`, outreach-writer, keelekontroll, inbox-triage |
| [wp4-sales-detection-launch](wp4-sales-detection-launch/README.md) | Karmen Tigas | 6, 8 | `wix-mcp`, sales-detector, cron, testifaaside koordineerimine |

## Sõltuvused

`pipedrive-mcp` (wp1) on ainus plokk, mida kõik teised vajavad
integratsioonitestiks. Meelis ehitab selle esimese tunni jooksul; seni
saavad teised oma agente ja MCP servereid DRY_RUN-is ette valmistada,
sest mail-mcp ja wix-mcp Pipedrive'i ei vaja.

Saladused tulevad Mardilt `.env`-i (Pipedrive'i token, MS Graphi tokenid,
Wixi API võti + poe ID). Kuni võtmeid pole, töötab kõik `DRY_RUN=1`-ga;
see on disaini järgi nagunii kohustuslik esimene faas.

## Ajakava

| Tund | Meelis (wp1) | Mart (wp2) | Annelis (wp3) | Karmen (wp4) |
|---|---|---|---|---|
| 1 | Pipedrive'i pipeline + staadiumid + field'id; `lib/` + `pipedrive-mcp` + smoke-test | enrichment-agendi mustand, käsitsi proov 1–2 päris veti peal | `mail-mcp` DRY_RUN-is; outreach-writer + esimene lätikeelne kiri | `wix-mcp`: tellimuste loetelu + kupongi loomine, smoke-test |
| 2 | `registry.py` + `discovery.py`: register deal'idena sisse | qualification-agent + skoorimisrubriik; jooks päris Discovered deal'ide peal | keelekontrolli-subagent + inbox-triage | sales-detector; cron (tikk 30 min, discovery kord nädalas) |
| 3 | `/tick` skill: järjekord, voolupiirang, lukufail | meditsiiniväidete kontroll outreach'i faktiallikates | redel + A/B harud läbi DRY_RUN-logide | Faas 1: DRY_RUN-i ülevaatus; faas 2: sünteetiline lead (Karmen on "vet") |

Viimane pooltund on ühine: kõik vaatavad DRY_RUN-logid üle ja faas 2
jookseb otsast lõpuni (Discovered → Won ilma inimsekkumiseta). See on
disaini järgi projekti valmis-kontroll.
