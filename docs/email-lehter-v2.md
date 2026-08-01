# Ravimus e-maili lehter v3 (A+D liidetud, kinnitusvärav, sooduskoodi loogika)

*Kanooniline allikas: Joplini märkus "Elnora – email-rajad v2 (A+D liidetud, ettepanek 2026-07-27)" (Nanordica → AI sales); see fail on selle repo-koopia seisuga 2026-07-28. Asendab v1 disaini kirjade-voo osa; v1 kirjakoopiad (LV mustandid) elavad Joplini v1 märkuses ja tuleb uue struktuuri järgi ümber jagada — keelekontrolli leiud: [email-rajad-review-findings.md](email-rajad-review-findings.md).*

**Numeratsioon:** K# = kiri (iga kiri eraldi kastis) · S# = seisund · T# = tick/deterministlik samm · V1 = veebikohtumine (varem C1) · W1 = valve. **Värv = vastutav roll, alati sama:** 🟢 outreach-writer (LLM-kirjad vetile) · 🟡 sales-detector / inbox-triage (signaalituvastus) · 🔵 enrichment + qualification · 🟣 inimene (Meelis) / kõne · 🟠 tick + omniva_* (firmasisene Omniva-plokk, sh K5) · 🔴 Lost · hall AINULT mitte-agentne lõpp-punkt.

## Vana → uus ID kaart

| Vana | Uus | | Vana | Uus |
|---|---|---|---|---|
| Q | S1 | | E5-B | K6 |
| AD / E1 | K1 | | fb-FU1 | K7 |
| FU1 | K2 | | fb-FU2 | K8 |
| FU2 | K3 | | D3 | S6 |
| E3-B | K4 | | D5 | K9 |
| E4-B | T1 + K5 | | S (Won) | S7 |
| D2 | S4 | | tänukiri | K10 |
| D2K | S5 | | F (Lost) | S8 |
| K (otsus) | — (kõnesamm eemaldatud 28.07) | | C1 | V1 |


## Muudatused v2 → v3 (2026-08-01)

1. **G1 + H1: genereerimine ja inimese kinnitus enne esimest saatmist.**
   Kirjad genereeritakse KÕIGILE saajatele korraga (G1 = outreach-writer +
   language-checker), inimene vaatab üle ja kinnitab (H1). Kinnituse järel
   jätkub saatmine automaatselt; kinnitamata kirju ei saadeta kunagi.
2. **K3 = "ehk ei ole õige inimene".** Kolm vaikset kirja tähendab sageli
   valet adressaati, mitte sobimatut toodet. K3 julgustab kirja edasi saatma
   kolleegile, kes saab soovi korral tasuta näidise. **Sooduskoodi K3-s EI
   OLE** — kood muudaks tagasihoidliku kirja müügikirjaks.
3. **K4 kaks varianti sama loogikaga.** K4a = sisemine soov (Vera → ravimus@,
   juba tööle rakendatud `omniva_mail_dispatch.py`-s). K4b = **vet ise
   kirjutab** ravimus@-le, et soovib näidist → täpsustuskäik on identne
   (puuduvad väljad küsitakse samasse lõime), toon on kliendile suunatud.
   Mõlemal juhul kannab silt kaasa **mida saata: 1 Ravimus haavaside**.
4. **K7 = akadeemia vorm.** Wixi leht "Haavaravi akadeemia vorm": video/piltide
   üleslaadimine + selgituse lahter (haigusjuhu kirjeldus). Link UTM-iga.
5. **Sooduskood täpselt üks kord.** K8: kui kontakt EI ole K3-e saanud, kasuta
   K3 sõnumit + ühekordset koodi; kui ON saanud, kasuta varuvarianti (uus
   sõnastus, mitte kordus). K9 annab koodi ainult siis, kui K8-s pole veel
   antud.
6. **Sooduskoodiga ost → S7 Won.** K3/K9 rajalt liigub deal ostu tuvastamisel
   otse Won'i (`sales-detector` koodi järgi).
7. **Sooduskoodi parameetrid:** 25%, ühekordne, 1 toode, tähtajaline
   (vaikimisi 30 p).
8. **Kõik lingid UTM-iga** — akadeemia, video, K7 vorm, pood. Ilma `utm_id`-ta
   on klikk anonüümne ja deal ei liigu.
9. **Inimloetav kokkuvõte:** `.claude/skills/lv-vet-email-funnel/README.md`.

## Muudatused v1 → v2

1. **A+D liidetud**: esmakiri K1 = akadeemia tutvustus + info võimalusest akadeemiasse panustada + tasuta näidise pakkumine. Eraldi Rada A kaob.
2. **Redel lüheneb**: 5 kirja (3/5/8/13 p) → K1 + K2 (+7 p) + K3 (+14 p, breakup). K2 = osalemispakkumine akadeemias + näidisvideo + kutse kõnele (V1). K3 = meenutab eelmisi kirju, ütleb et rohkem ei kirjuta → Lost. **Klikk/vastus viib S2-sse ka K3-st** — breakup-kirja hiline vastus püütakse kinni.
3. **Kaasatus (klikk/vastus) → kohe näidiseni**: K4 (aadressi küsimine) → Omniva saatmine.
4. **T1–S5 = firmasisene Omniva-plokk, LLM-i pole**: silt, saatmine, tarne jälgimine on deterministlikud tick-sammud. **K5 = saatmisteade Nanordica töötajale (vera@nanordica.com)** — deterministlik mall (silt + jälgimisnumber + pakomaat), mitte outreach-writeri kiri; vetile eraldi saatmisteadet ei lähe. *(Realiseeritud: `mcp/scripts/omniva_mail_dispatch.py` + cron; e2e kinnitatud 28.07, saadetis CC467134858EE.)*
5. **Tagasiside otse kirjaga** (kõnesamm S5 ja K6 vahelt eemaldatud 28.07): näidis kohal (S5) → **+1 p → K6** tagasiside-küsimus. Tagasiside (S6) tuleb K6 (või K7/K8) vastusest. K6 vaikus → K7 (+7 p), K8 (+14 p). K8 = breakup + ühekordne 30-p sooduskood + akadeemia vorm: sooduskoodi ost → Won, vaikus → Lost.
6. **Tagasiside antud → K9** (personaalne sooduskood) → ost → Won. Ost tuvastatakse K9 koodi kaudu ("ost ilma koodita" ühendus eemaldatud — pole vajalik).
7. **V1 (veebikohtumine Meelisega) = valikuline kõrvalrada, järjekord kutse → valve → kohtumine**: kutse kõnele on kirjas K2-s ja K9-s → vastuse püüab **W1** (inbox-triage valvab kohtumissoovi IGAS vastuses, igal hetkel) → **V1 järgneb W1-le** (calendar_find_slots → calendar_book_slot). Pärast kõnet jätkab deal sealt, kus rada pooleli oli. Inimese (Meelise) samm on AINULT V1.

## Lehter v2 (graaf)

```mermaid
flowchart TD
    S1["S1 · Kvalifitseeritud kontaktid<br/>enrichment + qualification"] --> G1["G1 · Kirjade genereerimine<br/>KÕIGILE saajatele<br/>outreach-writer + language-checker"]
    G1 --> H1{"H1 · Inimese kinnitus<br/>kas kirjad sobivad?"}
    H1 -->|"ei / paranda"| G1
    H1 ==>|"KINNITATUD → edasi automaatselt"| K1["✉ K1 · esmakiri: akadeemia +<br/>panustamisvõimalus + tasuta näidis"]
    K1 -->|"vaikus +7 p"| K2["✉ K2 · järelkiri 1: osalemiskutse<br/>+ näidisvideo + kutse kõnele"]
    K2 -->|"vaikus +7 p (K1-st +14 p)"| K3["✉ K3 · järelkiri 2: 'ehk ei ole õige inimene'<br/>julgusta edasi saatma · kolleeg saab tasuta näidise<br/>TAGASIHOIDLIK — sooduskoodi EI OLE"]
    K3 -->|"vaikus"| S8["S8 · Lost (no-reply)"]
    K1 ==>|"klikk / vastus"| S2["S2 · Kaasatus tuvastatud<br/>sales-detector · inbox-triage"]
    K2 ==>|"klikk / vastus"| S2
    K3 ==>|"klikk / vastus / edasisaadetud kolleeg"| S2
    S2 --> K4["✉ K4 · näidise detailide täpsustus<br/>K4a sisemine soov (Vera) · K4b vet kirjutab ise<br/>sama täpsustusloogika mõlemal"]
    K4 -->|"andmed täis"| T1["T1 · Omniva silt + saatmine<br/>sisu: 1 Ravimus haavaside"]
    T1 --> K5["✉ K5 · saatmisteade kontorile (Vera)<br/>deterministlik mall, LLM-ita"]
    K5 --> S4["S4 · Näidis teel"]
    S4 -->|"tarne tuvastatud"| S5["S5 · Näidis kohal"]
    S5 -->|"+1 p"| K6["✉ K6 · tagasiside-küsimus"]
    K6 -->|"vastus"| S6["S6 · Tagasiside käes"]
    K6 -->|"vaikus +7 p"| K7["✉ K7 · meeldetuletus +<br/>AKADEEMIA VORM (Wix)<br/>video/pildid + haigusjuhu kirjeldus"]
    K7 -->|"vastus / vorm täidetud"| S6
    K7 -->|"vaikus +14 p"| K8["✉ K8 · breakup + ÜHEKORDNE SOODUSKOOD<br/>K3 saanud → varuvariant<br/>K3 pole saanud → K3 sõnum + kood"]
    K8 -->|"vaikus"| S8
    S6 --> K9["✉ K9 · sooduskood<br/>AINULT kui K8-s pole antud"]
    K8 ==>|"sooduskoodiga ost"| S7["S7 · Won<br/>sales-detector"]
    K9 ==>|"sooduskoodiga ost"| S7
    S7 --> K10["✉ K10 · tänukiri"]
    K10 --> L["valmis"]

    K2 -.->|"kutse kõnele"| W1(["W1 · inbox-triage valvab<br/>kohtumissoovi igas vastuses"])
    K9 -.->|"kutse kõnele"| W1
    W1 -.-> V1["V1 · veebikohtumine Meelisega<br/>calendar_find_slots / book_slot"]

    classDef ow fill:#c8e6c9,stroke:#43a047,color:#000
    classDef det fill:#fff9c4,stroke:#fbc02d,color:#000
    classDef enr fill:#bbdefb,stroke:#1976d2,color:#000
    classDef hum fill:#d1c4e9,stroke:#7e57c2,color:#000
    classDef tik fill:#ffe0b2,stroke:#fb8c00,color:#000
    classDef lost fill:#ffcdd2,stroke:#e53935,color:#000
    classDef base fill:#e0e0e0,stroke:#9e9e9e,color:#000

    class K1,K2,K3,K4,K6,K7,K8,K9,K10 ow
    class G1 enr
    class S2,S6,S7,W1 det
    class S1 enr
    class H1,V1 hum
    class T1,K5,S4,S5 tik
    class S8 lost
    class L base
```

**Legend (värv = roll, alati sama):** 🟢 roheline = outreach-writer — K1–K4, K6–K10 (LLM-kirjad vetile) · 🟠 oranž = tick + omniva_* — T1, **K5**, S4, S5 (firmasisene Omniva-plokk, LLM-ita) · 🟡 kollane = sales-detector / inbox-triage — S2, S6, S7, W1 · 🔵 sinine = enrichment + qualification — S1 · 🟣 lilla = inimene (Meelis) — V1 · 🔴 punane = Lost — S8 · hall = "valmis" (pole agent). Katkendjoon = valikuline kõrvalrada: kutse (K2/K9) → W1 valve → V1.

## Kirjade kaart v2

| Kiri | Vana ID | Saaja | Käivitab | Ajastus | Kes |
|---|---|---|---|---|---|
| **K1** akadeemia + panustamine + näidis | E1 | vet | Qualified | päev 0 | outreach-writer |
| **K2** osalemiskutse + näidisvideo + kutse kõnele | FU1 | vet | vaikus | +7 p | outreach-writer |
| **K3** "ehk ei ole õige inimene" + julgusta edasi saatma (kolleeg saab tasuta näidise); SOODUSKOODITA | FU2 | vet | vaikus | +14 p (K1-st) → Lost; klikk/vastus/edasisaatmine → S2 | outreach-writer |
| **K4a/K4b** näidise detailide täpsustus (a: sisemine soov, b: vet kirjutab ise) | E3-B | vet / kontor | klikk/vastus või vet'i soov | kohe | outreach-writer + omniva_mail_dispatch |
| **K5** saatmisteade (silt, jälgimisnumber, pakomaat) | E4-B | **vera@nanordica.com (firmasisene)** | T1 silt loodud | saatmisel | **tick · deterministlik mall, LLM-ita** |
| **K6** tagasiside-küsimus | E5-B | vet | näidis kohal (S5) | **+1 p pärast tarnet** (kinnitatud 29.07) | outreach-writer |
| **K7** tagasiside-meeldetuletus | fb-FU1 | vet | vaikus K6-le | +7 p | outreach-writer |
| **K8** tagasiside-breakup + sooduskood | fb-FU2 | vet | vaikus K7-le | +7 p; ost → Won, vaikus → Lost | outreach-writer |
| **K9** personaalne sooduskood + kutse kõnele | D5 | vet | tagasiside antud (S6) | kohe | outreach-writer + wix_create_coupon |
| **K10** tänukiri | — | vet | Wixi ost (S7) | kohe | outreach-writer |
| **V1** veebikohtumine | C1 | — | W1 tuvastab kohtumissoovi (kutsed K2-s/K9-s; valve igas vastuses) | kohe | inbox-triage → calendar_* + Meelis |

## Pipedrive ahel

**Staadiumid jäävad samaks** (8 tk, ASCII-nimed nagu koodis): `Discovered → Enriched → Qualified → Contacted → Engaged → Naidis tellitud → Won / Lost`. Alam-seisundid = custom-field'id; tick on olekuta ja loeb field'e.

| Staadium | v2 sõlm(ed) | Sisenemine | Olek (field'id) |
|---|---|---|---|
| Qualified | S1 | skoor üle läve | score |
| Contacted | K1–K3 | K1 saadetud | emails_sent, last_contact_at (K2/K3 taimerid) |
| Engaged | S2, K4 | wix_get_click_events / inbox-triage (ka K3 hiline vastus) | engaged_at |
| Naidis tellitud | T1, K5, S4, S5 | aadress käes + Omniva silt; K5 teavitus Verale | **UUS:** shipped_at, tracking_barcode, pakomats_id, delivered_at |
| — (sama staadium) | K6–K8 | delivered_at + 1 p → K6 | **UUS:** feedback_at (K6/K7/K8 vastusest), fb_emails_sent |
| — (sama staadium) | S6 → K9 | feedback_at täidetud → kood | discount_code, valid_until |
| Won | S7 | Wixi ost K9 koodiga (sales-detector) | |
| Lost | S8 | K3 / K8 vaikus, opt-out, nē | lost_reason |
| (ristühendus) | W1 → V1 | kohtumissoov mis tahes staadiumis | **UUS:** meeting_at; Activity tüüp Meeting; staadium EI muutu |

**Tagasiside-redel:** tarne tuvastamisel (delivered_at) ootab tick 1 p ja saadab K6; vaikuse korral K7 (+7 p) ja K8 (+14 p, breakup + sooduskood). Sooduskoodi ost → Won, vaikus → Lost. Tagasiside (feedback_at) tekib K6/K7/K8 vastusest, mille inbox-triage klassifitseerib. Meelise ainus samm lehtris on V1.

**K5 / firmasisene Omniva-plokk (T1–S5):** kõik deterministlikud tick-sammud, LLM-i ei kasutata. K5 on mallipõhine teavitus vera@nanordica.com-ile: pakomaat, silt (PDF cache'ist), jälgimisnumber — saadetakse mail_send'iga otse tick'ist. **KÕVAD REEGLID:** pakisildi/jälgimise info tohib minna AINULT @nanordica.com aadressile; uue paki (mitte meie algatatud) saatmise võib käivitada AINULT @nanordica.com saatja. Vetile eraldi saatmisteadet ei saadeta; vet saab järgmise kontakti alles K6-s. *(Töötav teostus: `mcp/scripts/omniva_mail_dispatch.py`, tunnine cron.)*

**V1 kõrvalrada (kutse → valve → kohtumine):** kutsed kirjas K2-s ja K9-s; inbox-triage (W1) klassifitseerib IGA sissetuleva vastuse juures kohtumissoovi → tuvastamisel pakub outreach-writer calendar_find_slots ajad ja broneerib vastuse peale calendar_book_slot'iga → V1. Deal'i staadium ei muutu, kõne = Activity (Meeting) + meeting_at; pärast kõnet jätkab rada sealt, kus pooleli.

**Vajalikud muudatused koodis:** STATE_KEYS + uued field'id (shipped_at, tracking_barcode, pakomats_id, delivered_at, feedback_at, fb_emails_sent, meeting_at); tick'i sammud: omniva_track poll, K6 taimer (delivered_at + 1 p), K7/K8 redel; inbox-triage'i kategooriatesse "kohtumissoov"; K4 sõnastus klikkijale (kes pole veel "jah" öelnud); mail-mcp guardrail'id (≤1 kiri/24 h, max 5) kehtivad vetile — K5 (Verale) vajab sisemist erandit.

## Lahtised küsimused

1. ~~V1 (C1) ankrupunktid~~ — lahendatud 28.07: kutsed K2-s ja K9-s → W1 valve → V1.
2. **K8 = breakup + ühekordne 30-p sooduskood + akadeemia vorm** (kinnitatud 29.07): vaikus → Lost, sooduskoodi ost → Won, vormi/vastus → S6.
3. **A/B test:** v2-s on üks K1 — kas `ab_variant` (A: link / B: kupong) jääb ära või kolib subject-tasandile? Disainidokk vajab sama otsust.
4. **Klikk ilma vastuseta → K4** vajab pehmemat sõnastust (ta pole veel "jah" öelnud).
5. v1 kirjakoopiaid (LV mustandid) tuleb uue struktuuri järgi ümber jagada — [review-leiud](email-rajad-review-findings.md) kehtivad edasi; vana→uus ID kaart on üleval.
6. **Vera e-posti aadress** kinnitatud teostuses (vera@nanordica.com, `DISPATCH_NOTIFY_EMAIL` env).
7. **Orgaaniline ost ilma K9 koodita**: kas sales-detectori e-posti-järgi sidumine (v1 loogika) jääb koodi tasandile varuvõrguna alles?
8. **K6 ajastus** pärast tarnet: +1 p (kinnitatud 29.07).
