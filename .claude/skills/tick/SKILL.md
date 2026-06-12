---
name: tick
description: >
  Ravimus lead-pipeline'i orkestraator: üks töötsükkel (tikk), mille
  cron käivitab iga 30 min (claude -p "/tick") või kasutaja käsitsi.
  Loeb Pipedrive'i seisu, töötleb KÕIGEPEALT sissetuleva (vastused,
  ostud), siis väljamineva (enrichment, qualification, outreach),
  ja kirjutab kokkuvõtte logs/-i. Kasuta alati, kui on vaja pipeline
  edasi liigutada.
---

# /tick — pipeline'i orkestraator

Disain: `docs/ravimus-lead-pipeline-design.md` (peatükk "Orkestraator").
Järjekord on oluline: sissetulev enne väljaminevat, et süsteem ei
kirjutaks kunagi lead'ile, kes juba vastas või ostis. Sina oled
dirigent: delegeeri sisuline töö subagentidele (Agent tool), ära tee
seda ise. Kaitserauad (DRY_RUN, ≤1 kiri/24h, ≤5 kirja, opt-out) elavad
MCP-kihis — sina neid üle ei mängi ega "paranda".

## 0. Lukk (enne kõike muud)

Luku võtmine on atomaarne (`set -C` = O_EXCL; kaks samaaegset tikki ei
saa mõlemad lukku):

```sh
mkdir -p cache logs
if ( set -C; date -u +%FT%TZ > cache/tick.lock ) 2>/dev/null; then
  echo "lukk võetud"
elif [ -n "$(find cache/tick.lock -mmin +90 2>/dev/null)" ]; then
  date -u +%FT%TZ > cache/tick.lock
  echo "vana lukk (>90 min) üle võetud: eelmine tikk on katkenud"
else
  echo "SKIP: lukk on värske, eelmine tikk jookseb veel"
fi
```

- `SKIP` → LÕPETA kohe: raporteeri "tikk jäi vahele" ja **ära puutu
  lukku ega kirjuta kokkuvõtet** — lukk kuulub jooksvale tikile ja
  sammud 1–6 (sh luku eemaldus) kehtivad ainult tikile, kes luku sai.
- Luku saanud tikk: pärast IGA sammu (1–5) tee `touch cache/tick.lock`
  (südamelöök) — nii ei loe järgmine cron pikka, aga elusat tikki
  katkenuks. Lõpus (samm 6) eemalda lukk: `rm -f cache/tick.lock`.

## 1. Preflight

1. Leia Pipedrive'i tööriistad: ToolSearch
   `select:pipedrive_list_deals,pipedrive_move_deal_stage,pipedrive_update_deal_data,pipedrive_add_note`
   (ravimus-server). Kui neid pole, proovi üks märksõnaotsing
   ("pipedrive"). Kui tööriistu ikka pole: kirjuta kokkuvõte (samm 6)
   märkega "ravimus MCP server pole saadaval; käivita: vt
   mcp/README.md", eemalda lukk ja lõpeta. Asendustööriistu teistest
   serveritest ÄRA kasuta.
2. Staadiuminimed on `Discovered, Enriched, Qualified, Contacted,
   Engaged, Naidis tellitud, Won, Lost` — täpselt selles ASCII kujus
   (ilma õ/ä-ta), nagu serveri `resolve_stage_id` ootab
   (`mcp/lib/constants.py` on nimede ainuallikas). Kui
   `pipedrive_list_deals` vajab stage_id-d, loe nimi→id kaart failist
   `data/field_keys.json` (või `mcp/data/field_keys.json`). Kui
   kumbagi pole (nt server jookseb Dockeris või `pipedrive_setup` on
   jooksmata): kirjuta kokkuvõte märkega "stage-kaart puudub, jooksuta
   pipedrive_setup", eemalda lukk ja lõpeta. Kaardita EI tohi
   staadiume ära arvata.

## 2. Sissetulev

Käivita järjekorras kaks subagenti (Agent tool), kummalegi lihtne
korraldus — klassifitseerimisreeglid elavad agendi enda failis, ära
neid siin ümber jutusta:

1. **inbox-triage**: "Töötle uued saabunud kirjad."
2. **sales-detector**: "Kontrolli Wixi tellimusi ja kuponge."

Kui agenditüüpi pole registris või tema tööriistad puuduvad, jäta samm
vahele ja kirjuta põhjus kokkuvõttesse — ÄRA tee tema tööd ise.

## 3. Hetktõmmis ja profiilitöö

**Alles nüüd** (pärast sissetulevat, et tõmmis ei sisaldaks äsja
vastanud/ostnud lead'e vananenud staadiumis) loe pipeline'i seis:
kutsu `pipedrive_list_deals` IGA staadiumi kohta eraldi
(stage_id kaardist, limit 100). Kui mõni staadium tagastab täpselt
100 rida, on loend tõenäoliselt kärbitud — märgi see kokkuvõttesse
JA käsitle selle staadiumi arve alampiirina (vt voolupiirang all).

Kuupäevavõrdlusteks kasuta deterministlikku abikäsku, mitte peast
arvutamist (tagastab täispäevade arvu antud ISO-ajast praeguseni):

```sh
python3 -c "import sys;from datetime import datetime,timezone;print((datetime.now(timezone.utc)-datetime.fromisoformat(sys.argv[1].replace('Z','+00:00'))).days)" "<ISO-aeg>"
```

Profiilitöö (töömahu lagi: kummalegi agendile max 20 deal'i tiki
kohta; ülejäänu ootab järgmist tikki — 48 tikki päevas tühjendab
järjekorra niikuinii):

- **Discovered** deal'id → **enrichment** subagent (anna deal'i id-d
  ühe partiina).
- Seejärel **Enriched** deal'id → **qualification** (samuti partiina).

## 4. Väljaminev post (voolupiirang SIIN, mitte agendis)

Värskenda enne seda sammu Contacted/Engaged/Naidis tellitud/Won
loendid uue `pipedrive_list_deals` kutsega (samm 3 võis staadiume
muuta). Reeglid (kõik päevavõrdlused: "≥ N päeva" = abikäsu tulemus
on N või rohkem):

- `contacted_active` = Contacted deal'id, kus `_state.emails_sent < 5`
  (ammendunud redeliga deal'id EI hõiva esmakirjade kvooti). Kui
  Contacted loend oli kärbitud (100 rida), käsitle kvooti täis.
- **Uued esmakirjad**: ainult kui `contacted_active < 20`. Qualified
  pingerida skoori järgi, anna outreach-writer'ile max
  `20 - contacted_active` esimest.
- **Follow-up'id**: Contacted, `emails_sent` 1–4 ja viimasest kirjast
  (`_state.last_contact_at`) on möödas redelivahe: 1 kiri → ≥3 päeva,
  2 → ≥5, 3 → ≥8, 4 → ≥13. (Vahed tulevad disaini "Kirjade redel"
  tabelist; kui tiim neid häälestab, muutub see rida JA
  outreach-writer.md — hoia sünkroonis.)
- **Redel ammendatud**: Contacted, `emails_sent >= 5` ja viimasest
  kirjast ≥13 päeva (redeli pikim vahe = vastamisaken; disain ütleb
  "5 kirja + vaikus → Lost", akna pikkus on meie valik) → liiguta
  Lost: `pipedrive_move_deal_stage` + `pipedrive_update_deal_data`
  (`lost_reason: "no-reply"`) + note. See on mehaaniline reegel, võid
  ise teha.
- **Engaged**: triage'i märkega vastamata küsimus → outreach-writer'ile
  sisuline vastus.
- **Naidis tellitud**: `_state.sample_claimed_at` ≥3 päeva,
  `_state.sample_reminder_sent` puudub → üks meeldetuletus. Kui
  `sample_reminder_sent` on olemas ja sellest ≥13 päeva vaikust
  (sama vastamisaken) → Lost (`lost_reason: "no-reply"`).
- **Won**: `_state.thanked_at` puudub → tänukiri.

Anna kogu väljaminev **ühe partiina** outreach-writer subagendile:
nimekiri (deal_id, tüüp: esmakiri/follow-up/vastus/meeldetuletus/
tänukiri, kontekst) ja NÕUA vastuseks iga kirje staatust
(saadetud / mail-kiht keeldus / viga). Alles raporteeritud "saadetud"
staatuse järel kirjuta olekusse `sample_reminder_sent` (meeldetuletus)
või `thanked_at` (tänukiri) — keeldumise/vea korral võtit EI kirjuta,
järgmine tikk proovib uuesti. (`sample_reminder_sent` ja `thanked_at`
tuleb lisada `STATE_KEYS`-i, `mcp/lib/constants.py` — vt PR #11
märkust Mardile.)

## 5. Veakäsitlus

- Subagendi/MCP viga: deal jääb puutumata, viga kokkuvõttesse ja
  `logs/errors.md`-sse (lisa rida kujul `- <ISO-aeg> tick: <viga>`),
  järgmine tikk proovib uuesti. Ära jää ühe sammu taha kinni — jätka
  järgmise sammuga.
- Staadiumimuutus ja olekuvõtmete kirjutus ainult pärast õnnestunud
  tegevust, mitte ette.

## 6. Kokkuvõte ja lukk lahti (luku omanikule alati, ka vigade korral)

Kirjuta `logs/tick-YYYYMMDD-HHMM.md` (UTC, nt `date -u +%Y%m%d-%H%M`):

```markdown
# tick <ISO-aeg> (DRY_RUN=<väärtus .env-ist või "seadmata">)
- inbox-triage: <n kirja / vahele jäetud: põhjus>
- sales-detector: <n tellimust, n Won, n näidist / vahele jäetud>
- enrichment: <n deal'i> · qualification: <n, neist Lost n>
- outreach: esmakirju <n> (contacted_active=<n>/20), follow-up'e <n>,
  vastuseid <n>, meeldetuletusi <n>, tänukirju <n>, Lost <n>
- kärbitud loendid: <staadiumid, kus tuli 100 rida, või "pole">
- vead: <loetelu või "pole">
```

Lõpuks `rm -f cache/tick.lock` ja raporteeri kasutajale sama
kokkuvõte ühe ekraanitäiega.
