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

```sh
mkdir -p cache logs
if [ -f cache/tick.lock ] && [ -n "$(find cache/tick.lock -mmin -45 2>/dev/null)" ]; then
  echo "tick.lock on värske: eelmine tikk jookseb veel, väljun"
else
  date -u +%FT%TZ > cache/tick.lock
  echo "lukk võetud"
fi
```

Kui lukk oli värske, LÕPETA kohe (raporteeri "tikk jäi vahele, eelmine
jookseb"). Üle 45 min vana lukk on eelmise katkenud tiki jäänuk:
kirjuta üle ja jätka. Tiki LÕPUS (ka siis, kui mõni samm ebaõnnestus)
eemalda lukk: `rm -f cache/tick.lock`.

## 1. Preflight

1. Leia Pipedrive'i tööriistad (ToolSearch, nt "pipedrive deals").
   Oodatud nimed (ravimus-server): `pipedrive_list_deals`,
   `pipedrive_move_deal_stage`, `pipedrive_update_deal_data`,
   `pipedrive_add_note`. Kui nimed erinevad, aga samaväärsed
   tööriistad on olemas, kasuta neid.
2. Kui Pipedrive'i tööriistu pole ÜLDSE: kirjuta kokkuvõte (samm 6)
   märkega "ravimus MCP server pole saadaval; käivita: vt
   mcp/README.md", eemalda lukk ja lõpeta. Ühtegi muud sammu ei tee.
3. Staadiuminimed on `Discovered, Enriched, Qualified, Contacted,
   Engaged, Naidis tellitud, Won, Lost` (NB: ASCII, ilma õ/ä-ta —
   täpselt nii, nagu serveri `resolve_stage_id` ootab). Kui
   `pipedrive_list_deals` vajab stage_id-d, loe nimi→id kaart failist
   `data/field_keys.json` (või `mcp/data/field_keys.json`); kui faili
   pole, listi deal'id filtrita ja grupeeri `stage_id` järgi kaardita —
   sel juhul märgi kokkuvõttesse, et `pipedrive_setup` on jooksmata.

Loe pipeline'i seis üks kord siin (kõik deal'id, limit 100) ja kasuta
sama hetktõmmist sammudes 4–5; ära listi igas sammus uuesti.

## 2. Sissetulev

Käivita järjekorras kaks subagenti (Agent tool). Kui agenditüüpi pole
registris või tema tööriistad puuduvad, jäta samm vahele ja kirjuta
põhjus kokkuvõttesse — ÄRA tee tema tööd ise.

1. **inbox-triage** — "Töötle uued saabunud kirjad ja klassifitseeri
   vastused; liiguta staadiumid." (Vastused → Engaged, "ei"/opt-out/
   bounce → Lost.)
2. **sales-detector** — "Kontrolli Wixi tellimusi ja kuponge; päris
   ost → Won, näidise lunastus → Naidis tellitud."

## 3. Profiil ja skoor

Hetktõmmise põhjal:

- Iga **Discovered** deal'i kohta käivita **enrichment** subagent
  (anna ette deal'i id ja olemasolev info). Mitu deal'i võib anda
  ühele agendijooksule partiina, kuni 10 korraga.
- Seejärel iga **Enriched** deal'i kohta **qualification** (samuti
  kuni 10 partiis). Skoor alla läve → agent liigutab ise Lost'i.

Kui Discovered/Enriched deal'e pole, märgi kokkuvõttesse "0" ja liigu
edasi.

## 4. Väljaminev post (voolupiirang SIIN, mitte agendis)

Arvuta hetktõmmisest:

- `contacted_count` = deal'e staadiumis Contacted.
- **Uued esmakirjad**: ainult kui `contacted_count < 20`. Võta
  Qualified deal'id skoori järgi pingeritta (kõrgeim enne) ja anna
  outreach-writer'ile MAKSIMAALSELT `20 - contacted_count` esimest.
- **Follow-up'id**: Contacted deal'id, kus `_state.emails_sent` on
  1–4 ja viimasest kirjast (`_state.last_contact_at`) on möödas
  redelivahe: 1 kiri saadetud → 3 päeva, 2 → 5, 3 → 8, 4 → 13.
- **Redel ammendatud**: Contacted, `emails_sent >= 5` JA viimasest
  kirjast > 13 päeva → liiguta Lost (`lost_reason: "no-reply"`) +
  note. Seda võid teha ise (pipedrive_move_deal_stage +
  pipedrive_update_deal_data), see on mehaaniline reegel.
- **Engaged**: iga Engaged deal, millel on triage'i märge vastamata
  küsimusest → outreach-writer'ile sisuline vastus.
- **Naidis tellitud**: kui `_state.sample_claimed_at` on ≥ 3 päeva
  vana, päris ostu pole ja `_state.sample_reminder_sent` puudub →
  outreach-writer'ile ÜKS meeldetuletus; pärast saatmist kirjuta
  `sample_reminder_sent: <ISO-aeg>` deal'i olekusse. Kui meeldetuletus
  on saadetud ja sellest on > 8 päeva vaikust → Lost (`lost_reason:
  "no-reply"`).

Anna kogu väljaminev **ühe partiina** outreach-writer subagendile:
nimekiri (deal_id, tüüp: esmakiri/follow-up/vastus/meeldetuletus,
kontekst). Outreach-writer kirjutab, laseb keelekontrollist läbi ja
saadab ise; saatmispiirangud jõustab mail-kiht.

## 5. Veakäsitlus

- Subagendi/MCP viga: deal jääb puutumata, viga kokkuvõttesse ja
  `logs/errors.md`-sse (lisa rida kujul `- <ISO-aeg> tick: <viga>`),
  järgmine tikk proovib uuesti. Ära jää ühe sammu taha kinni — jätka
  järgmise sammuga.
- Staadiumimuutus ainult pärast õnnestunud tegevust, mitte ette.

## 6. Kokkuvõte ja lukk lahti (alati, ka vigade korral)

Kirjuta `logs/tick-YYYYMMDD-HHMM.md` (UTC, nt `date -u +%Y%m%d-%H%M`):

```markdown
# tick <ISO-aeg> (DRY_RUN=<väärtus .env-ist või "seadmata">)
- inbox-triage: <n kirja / vahele jäetud: põhjus>
- sales-detector: <n tellimust, n Won, n näidist / vahele jäetud>
- enrichment: <n deal'i> · qualification: <n, neist Lost n>
- outreach: esmakirju <n> (contacted=<n>/20), follow-up'e <n>,
  vastuseid <n>, meeldetuletusi <n>, Lost <n>
- vead: <loetelu või "pole">
```

Lõpuks `rm -f cache/tick.lock` ja raporteeri kasutajale sama
kokkuvõte ühe ekraanitäiega.
