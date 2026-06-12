# Ravimus lead-pipeline — variant A disain

*Seis: 2026-06-12. Põhineb failil
[ravimus-lead-pipeline-ideas.md](ravimus-lead-pipeline-ideas.md) —
valitud sai variant A: üks orkestraator-tikk + subagendid, Pipedrive
ainsa tõeallikana.*

## Ülevaade

Cron käivitab iga 30 minuti järel headless Claude Code sessiooni
("pipeline tick"). Tikk loeb Pipedrive'ist kogu pipeline'i seisu,
otsustab iga lead'i kohta järgmise sammu ja delegeerib töö
subagentidele. Kogu olek elab Pipedrive'is: deal'i staadium + custom
field'id. Tikk ise on olekuta — katkenud tikk ei riku midagi, järgmine
jätkab samast kohast.

```
cron (30 min)
   │
   ▼
pipeline tick (orkestraator)
   │
   ├─ 1. inbox-triage ──── MS Graph: loe vastused ─→ staadiumimuutused
   ├─ 2. sales-detector ── Wix Orders API ─────────→ Won + tänukiri
   ├─ 3. discovery ─────── registri CSV ──────────→ uued deal'id (kui partii < siht)
   ├─ 4. enrichment ────── veebiotsing ───────────→ Discovered → Enriched
   ├─ 5. qualification ─── hindamine ─────────────→ Enriched → Qualified/Lost
   └─ 6. outreach-writer ─ MS Graph: saada ───────→ esmakontakt / follow-up / vastus / pakkumine
```

Järjekord on oluline: kõigepealt sissetulev info (vastused, ostud),
siis alles väljaminev — nii ei saada tikk kirja lead'ile, kes juba
vastas või ostis.

## Pipedrive'i struktuur

### Staadiumid (üks pipeline: "ravimus-latvia-vets")

| # | Staadium | Tähendus | Kes liigutab sisse |
|---|---|---|---|
| 1 | Discovered | Registrist leitud, deal loodud | discovery |
| 2 | Enriched | E-post + kliiniku andmed olemas | enrichment |
| 3 | Qualified | Sobib sihtgruppi, valmis kontaktiks | qualification |
| 4 | Contacted | Esmakiri saadetud | outreach-writer |
| 5 | Engaged | Vastas / näitas huvi | inbox-triage |
| 6 | Offer | Ostulink + sooduskood saadetud | outreach-writer |
| 7 | Won | Wixi ost tuvastatud | sales-detector |
| 8 | Lost | Opt-out, bounce, ei sobi või follow-up'id ammendatud | mitu agenti |

### Custom field'id deal'il

- `registry_id` — vetiregistri unikaalne ID (duplikaatide vältimiseks)
- `email` — leitud/kinnitatud e-post
- `clinic` — kliiniku nimi ja asukoht
- `last_contact_at` — viimase saadetud kirja aeg
- `follow_up_count` — saadetud follow-up'ide arv
- `lost_reason` — miks Lost (opt-out / bounce / unqualified / no-reply)

Kogu kirjavahetus (saadetud ja saadud) logitakse deal'i note'idena —
auditeeritavus ja järgmise kirja kontekst.

## Subagendid

Iga subagent on `.claude/agents/` definitsioon. Agendid teevad
arutluse; API-kõned teevad deterministlikud Python-skriptid (vt
allpool), mida agendid Bashi kaudu käivitavad.

### discovery
Loeb `cache/registry.csv` (Läti vetiregister, laetud
`scripts/registry.py`-ga). Valib N uut vetti, keda Pipedrive'is veel
pole (`registry_id` järgi), ja loob person + deal staadiumis
Discovered. Käivitub ainult siis, kui aktiivseid deal'e on alla
partii sihi (vaikimisi 15).

### enrichment
Iga Discovered deal'i kohta: veebiotsing (kliiniku veebileht, e-post,
eriala, asukoht). Kirjutab custom field'id, liigutab → Enriched. Kui
e-posti ei leia, märgib deal'ile katsete arvu; 2 ebaõnnestunud tikki →
Lost (`lost_reason: no-email`).

### qualification
Hindab Enriched deal'i sobivust: väikeloomapraksis (haavaside on
jaemüügitoode), aktiivne tegevusluba, e-post olemas. Tulemus →
Qualified või Lost (`lost_reason: unqualified`) koos põhjendusega
note'is.

### outreach-writer
Staadiumiteadlik kirjutaja, töötab läti keeles. Neli režiimi:

1. **Esmakontakt** (Qualified → Contacted): lühike tutvustus —
   Ravimus haavaside, väärtuspakkumine vetile, viide Wixi tootelehele.
2. **Follow-up** (Contacted, vastust pole ≥ 3 päeva,
   `follow_up_count` < 3): meeldetuletus uue nurga alt (kasutuslugu,
   omadus, küsimus).
3. **Vastus** (Engaged, triage tuvastas küsimuse/vastuväite): sisuline
   vastus deal'i note'ide konteksti põhjal.
4. **Pakkumine** (Engaged → Offer): personaalne ostulink +
   sooduskood, selge üleskutse osta Wixist.

Iga kiri: saadetakse `scripts/graph_mail.py` kaudu, logitakse note'ina,
uuendatakse `last_contact_at` ja `follow_up_count`. Iga kiri sisaldab
lätikeelset loobumisrida ("atrakstīties").

### inbox-triage
Loeb Graphi kaudu uued kirjad alates eelmisest tikist (delta-token
salvestatud `cache/`). Seob saatja e-posti deal'iga. Klassifitseerib:

- huvi / küsimus / vastuväide → Engaged + ülesanne outreach-writer'ile
- ei-huvita / opt-out → Lost (`lost_reason: opt-out`)
- bounce → Lost (`lost_reason: bounce`)
- out-of-office → ignoreeri (follow-up'i taimer jookseb edasi)

Tundmatult aadressilt kiri → note üldisesse logisse, inimesele
vaatamiseks.

### sales-detector
Pollib Wix Orders API-t uute tellimuste osas. Seob ostja e-posti
deal'iga → Won. Outreach-writer saadab tänukirja. Tellimus, mis ei
seostu ühegi deal'iga, logitakse (orgaaniline müük).

## Integratsiooniskriptid

Kaust `scripts/`, Python, CLI-subkäskudega, secrets `.env`-ist.
Deterministlikud — kogu API-loogika on siin, mitte agentide peades.

| Skript | Vastutus |
|---|---|
| `scripts/pipedrive.py` | deal'ide/persons/note'ide CRUD, staadiumimuutused, custom field'id |
| `scripts/graph_mail.py` | MS Graph: kirja saatmine, uute kirjade lugemine delta-tokeniga |
| `scripts/wix_orders.py` | viimaste tellimuste loetelu |
| `scripts/registry.py` | Läti vetiregistri allalaadimine ja parsimine → `cache/registry.csv` |

Kõik skriptid toetavad `DRY_RUN=1` režiimi: trükivad, mida teeksid,
ilma saatmata/kirjutamata — testimiseks ja demo harjutamiseks.

## Orkestraator (tick)

Projekti skill / slash-käsk `/tick`, mida cron käivitab headless'ina
(`claude -p "/tick"`). Algoritm:

1. `inbox-triage` — töötle saabunud kirjad.
2. `sales-detector` — kontrolli Wixi tellimusi.
3. Loe Pipedrive'i seis. Kui aktiivseid deal'e < 15 → `discovery`.
4. Discovered deal'id → `enrichment`.
5. Enriched deal'id → `qualification`.
6. Väljaminev post ühe partiina → `outreach-writer`:
   - Qualified → esmakontakt
   - Contacted, vastuseta ≥ 3 päeva, follow_up_count < 3 → follow-up
   - Contacted, follow_up_count = 3 ja ≥ 3 päeva vaikust → Lost
   - Engaged (triage'i ülesanne ootel) → vastus ja/või pakkumine
   - Offer, ostu pole ≥ 3 päeva → üks meeldetuletus; veel 3 päeva
     vaikust → Lost (`lost_reason: no-reply`)
7. Kirjuta kokkuvõte `logs/tick-YYYYMMDD-HHMM.md` (mida tehti, mida
   saadeti, vead).

### Kaitserauad (guardrails)

- **≤ 10 kirja tiki kohta** — meiliserveri maine kaitseks.
- **≤ 1 kiri lead'ile 24 h jooksul** — `last_contact_at` kontroll.
- **≤ 3 follow-up'i**, siis Lost — me ei pommita.
- **Opt-out on lõplik**: Lost (`opt-out`) deal'ile ei kirjutata enam
  kunagi, ka mitte uue discovery-ringi kaudu (registry_id blokeerib).
- **Keelekontroll**: enne saatmist vaatab eraldi kontrolli-subagent
  lätikeelse kirja üle (toon, viisakusvormid, arusaadavus); kahtluse
  korral lihtsustab sõnastust.

## Veakäsitlus

- **Skripti viga** (API maas, token aegunud): agent raporteerib, deal
  jääb puutumata, järgmine tikk proovib uuesti. Staadiumimuutus tehakse
  alles pärast õnnestunud API-kõnet.
- **Saatmine õnnestus, logimine ebaõnnestus**: viga kirjutatakse
  `logs/errors.md`-sse; `last_contact_at` uuendatakse enne note'i, et
  topeltsaatmist ei juhtuks.
- **Duplikaadid**: discovery dedup'ib `registry_id` järgi; sama
  e-postiga teist deal'i ei looda.
- **Üheaegsed tikid**: lukufail `cache/tick.lock` — kui eelmine tikk
  veel jookseb, uus väljub kohe.

## Testimine ja "valmis" definitsioon

**Valmis-kontroll:** üks sünteetiline lead (tiimiliige "vetina" oma
e-postiga, lisatud registry CSV-sse) läbib täisautonoomselt kogu tee
Discovered → Won: saab lätikeelse esmakirja, vastab küsimusega, saab
sisulise vastuse ja pakkumise, sooritab Wixis ostu ja deal liigub
Won'i ilma ühegi inimsekkumiseta.

Lisaks:

- iga skripti smoke-test (test-deal'i loomine/lugemine, testkiri
  iseendale, Wixi tellimuste loetelu);
- `DRY_RUN=1` täistikk päris Pipedrive'i seisu peal — väljund üle
  vaadatav enne esimest päris jooksu;
- alles seejärel 5–20 päris vetti pipeline'i.

## Ehitusjärjekord

1. **Skelett**: `.env` võtmed, `scripts/pipedrive.py` + smoke-test;
   pipeline ja staadiumid Pipedrive'is üles.
2. **Discovery**: `scripts/registry.py` + discovery-agent → deal'id
   tekivad Pipedrive'i.
3. **Saatmine**: `scripts/graph_mail.py` + outreach-writer → esimene
   lätikeelne kiri testaadressile.
4. **Vastuvõtt**: inbox-triage + Graphi delta-lugemine.
5. **Kvalifitseerimine**: enrichment + qualification.
6. **Müügituvastus**: `scripts/wix_orders.py` + sales-detector.
7. **Orkestraator**: `/tick` skill + kaitserauad + lukufail.
8. **Ajastus ja lõpptest**: cron/Task Scheduler + sünteetilise lead'i
   täisring.

Iga samm on eraldi verifitseeritav — järgmist ei alustata enne, kui
eelmise kontroll läbib.

## Lahtised eeldused

- MS Graphi tokenid (Mail.Send, Mail.Read) tulevad kasutajalt; kuni
  siis arendame `DRY_RUN`-iga.
- Wix API võti ja poe ID tulevad kasutajalt.
- Läti vetiregistri täpne URL/formaat selgub discovery-sammus; kui
  avalik register on ainult HTML, parsime selle.
- Sooduskoodide loomine Wixis: kas käsitsi ette (lihtsam, soovitus)
  või API kaudu dünaamiliselt.
