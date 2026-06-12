---
name: qualification
description: Hindab Enriched deal'i sobivust RavimusVET sihtkliendiks — skoor 0–100 + põhjendus note'ina; skoor läve peal või üle → Qualified, alla läve → Lost (unqualified). Kasuta tick'i sammus 3 vahetult pärast enrichment'i või käsitsi valideerimisel profiilifaili peal.
---

# qualification — skoorija

Sisend: Enriched deal (field'id + enrichment-note) või käsitsi antud
profiil (`cache/profiles/<slug>.md`). Väljund: `score` field,
põhjendus-note, staadiumimuutus. Outreach võtab Qualified-pingerea
tipust — sinu skoor määrab kontaktijärjekorra.

## Rubriik (0–100)

| Kriteerium | Punktid | Tõendi allikas |
|---|---|---|
| Kiirabikliinik / 24h valve | 0–40 | `clinic` field; "jah" = 40, "ei" ja "teadmata" = 0 |
| Haavaravi / kirurgia / op-järgne / dermatoloogia / traumad | 0–25 | `specialization`; alamskaala allpool |
| Väikeloomapraksis (jaemüügitoode) | 0–15 | `specialization`; väikeloom põhitegevusena = 15 (ka segapraksises, kus kõrval on suurloomaliin); puhas suurloomapraksis (hobune/veis) = 8, sest kroonilised haavandid on tugev use-case |
| Aktiivne tegevusluba + toimiv e-post | 0–10 | registrist tulnud deal = luba aktiivne (8); kehtiv LVB sert enrichment-note'is = [kindel]; personaalne e-post +2 |
| Ostuotsustaja (omanik/juhataja) + leitav digijälg | 0–10 | enrichment-note: Roll, Digijälg |

Alamskaalad:

- **Kriteerium 2 (0–25):** haavaravi või haavasidemete kasutus
  otsesõnu = 25; kirurgia ilma haavaravi mainimata = 12; op-järgne
  hooldus / dermatoloogia / traumad annavad igaüks +6 (lagi 25);
  mitte ükski = 0.
- **Kriteerium 5 (0–10):** otsustaja roll (omanik/juhataja) = 5;
  isiklik digijälg = 5, ainult kliinikutasandi jälg = 2, puudub = 0.

Reeglid:

- Punktid ainult tõendi olemasolul; `[tõenäoline]` fakt annab poole
  punktidest; poolpunktid ümarda alla. Puuduv info = 0 punkti, mitte
  oletus.
- **`mājas dzīvnieki` ilma veebilehe kinnituseta** (haavaravi/kirurgia
  pole mainitud, aga pole ka eitatud): kriteerium 2 = 6 punkti
  `[tõenäoline]` — väikeloomapraksis sisaldab rutiinselt kirurgiat.
  Lisa põhjendusse: "kirurgia [tõenäoline], veebileht puudub".
  (Lisatud valideerimise põhjal 2026-06-12.)
- Personaalse e-posti +2 kehtib ainult deal'i `email` field'i kohta
  (sinna outreach saadab). Enrichment-note'is leitud alternatiivne
  aadress punkte ei anna.
- **Riskimärk** enrichment-note'is (pensionil / kliinik suletud / ei
  prakteeri) → skoor max 10 → Lost.
- **Rikastamata profiil** (Täielikkus: rikastamata, ainult
  registriandmed): skoor = 30, põhjendusse "profiil rikastamata,
  pingerea lõpus". Lost'i ei panda pelgalt info puudumise pärast —
  voolupiirang hoiab ta nagunii järjekorra lõpus.
- **Lävi: 30.** Skoor ≥ 30 → Qualified; < 30 → Lost +
  `lost_reason: unqualified`.
- Kaalud ja lävi on häälestatavad ainult tiimi otsusega (DRY_RUN-i
  ülevaatus) — ära muuda neid jooksvalt.

## Töövoog

1. `pipedrive_get_deal(deal_id)` → loe `_state` (field'id) + enrichment-note.
2. Arvuta skoor rida-realt; iga rea taga peab olema enrichment'i fakt,
   mida saab kontrollida. Kahtluse korral anna väiksem punkt — sama
   sisend peab andma sama skoori.
3. `pipedrive_update_deal_data(deal_id, {"score": N})`; Lost'i korral lisa
   `{"lost_reason": "unqualified"}` samasse kõnesse.
4. `pipedrive_add_note(deal_id, ...)` — mall allpool.
5. Alles pärast õnnestunud kirjutusi: `pipedrive_move_deal_stage(deal_id, "Qualified")` või `pipedrive_move_deal_stage(deal_id, "Lost")`.
6. MCP kõne ebaõnnestus → ÄRA liiguta staadiumit, raporteeri viga;
   järgmine tikk proovib uuesti.

DRY_RUN-i jõustab MCP-kiht — sina käitu alati nagu päris.

**Käsitsi režiim** (ilma Pipedrive'ita): loe profiil failist
`cache/profiles/<slug>.md` ja lisa note-malli järgi skooritabel sama
faili lõppu.

## Note mall

```
## Qualification — skoor <N>/100 — <YYYY-MM-DD>

| Kriteerium | Punktid | Tõend |
|---|---|---|
| Kiirabi / 24h | x/40 | ... |
| Haavaravi / kirurgia | x/25 | ... |
| Väikeloom | x/15 | ... |
| Luba + e-post | x/10 | ... |
| Otsustaja + digijälg | x/10 | ... |

**Otsus:** Qualified | Lost (unqualified)
**Märkused:** <riskimärgid, kahtlused, mida outreach peaks teadma>
```
