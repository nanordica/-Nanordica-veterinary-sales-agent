# Disain: e-maili turundusskill — Ravimus, Läti veterinaarturg

**Kuupäev:** 2026-06-12
**Autor:** Karmen + Claude
**Staatus:** ülevaatamisel

---

## Eesmärk

Anda Claude'ile oskus koostada e-maili turunduskampaaniaid, mis konverdivad
Läti veterinaararstid Ravimuse klientideks ja suunavad nad veebilehel toodet
ostma. Skill peab toetama funneli jälgimist (mis hetkel müük toimub), A/B
testimist (milline kiri töötab kõige paremini) ja **personaliseerimist** nii
segmendi kui ka iga kontakti tasandil.

**Tarne tüüp:** teadmiste-skill. E-kirjade saatmist skill ei tee — saatmine ja
päris andmete kogumine jääb kasutaja ESP-sse. Skill annab teadmised, töövoo ja
mallid.

---

## Sihtgrupp ja kontekst

| Parameeter | Väärtus |
|------------|---------|
| Bränd | **Ravimus** (tootja Nanordica Medical) |
| Toode | **RavimusVET** — steriilne haavaside |
| Sihtgrupp | Läti veterinaarkliinikud ja loomaarstid |
| Keel | **Läti keel** |
| Funneli eesmärk | Otsene ost veebilehel |
| CTA sihtleht | `https://www.nanordica.com/ravimus` (ingliskeelne leht) |
| Olemasolevad andmed | **E-posti aadressid + kaasatuse andmed** (avab / klikib / mitteaktiivne) |
| Juurde otsitavad andmed | Nimi, kliinik, loomatüüp, regioon — rikastatakse päringuga |
| Listi tüüp | **Külm prospekteerimine** (kontaktid pole nõusolekut andnud) |

### ⚠️ Külma listi tegelikkus (loe enne)

List on külm. See muudab kolme asja, mille kohta pean ausalt rääkima:

1. **Õiguslik.** EL-is reguleerib külmi turunduskirju ePrivacy-direktiiv +
   GDPR. B2B-le on Lätis õigustatud huvi vahel lubatud, aga see eeldab seost,
   selget opt-out'i igas kirjas ja andmetöötluse teavitust. Meditsiiniseadme
   külm turundus loomaarstidele vajab õiguslikku alust. **Ma pole jurist** —
   see on risk, mille pead enne saatmist kinnitama, mitte tehniline detail.
2. **Tööriist.** Massi-ESP-d (Mailchimp jt) **keelavad** külma e-posti ja
   sulgevad konto. Külm vajab eraldi cold-outreach taristut: eraldi
   saatmisdomeen (kaitseb `nanordica.com` mainet), aeglane soojendus, väike
   päevamaht, aadresside verifitseerimine (bounce'id tapavad maine).
3. **Open rate.** 25–35% on külmal listil **ambitsioonikas**, mitte
   konservatiivne. Saavutatav ainult siis, kui list on verifitseeritud,
   personaliseerimine tugev, taristu korras ja pealkiri hea. Külm kukub
   kergesti rämpsu, kus open rate on ~0.

### Toote müügiargumendid (veebilehelt)

RavimusVET on steriilne haavaside, mis koosneb naturaalse siidi
nanokiudkihist antimikroobsete nanoosakestega (sünergiline hõbe + vask) ja
imavast tselluloosikihist.

Põhilubadused:
- **~2× kiirem paranemine** võrreldes hõbedapõhiste sidemetega (kliiniline uuring)
- Madalam tsütotoksilisus inimrakkudele kui konkureerivatel sidemetel
- Tugevaim antibakteriaalne toime *Staphylococcus aureus*'e vastu
- 20 aastat teadustööd, valideeritud RCT-ga Põhja-Eesti Meditsiinikeskuses
- Toetab haava paranemist, vähendab bakterite hulka, võimaldab
  **atraumaatilist sidemevahetust** (kasutaja rõhutas seda eraldi)
- Sobib krooniliste haavandite raviks
- Kolm suurust: 5×5 cm, 8×9 cm, 10×10 cm

---

## Arhitektuur: hübriid (kaks skilli)

**Mõlemad skillid lähevad team-17 reposse:** `.claude/skills/`. Nii on need
projektiga kaasas ja jagatav tiimiga (mitte ainult Karmeni masinas).

### Osa 1 — `email-marketing-bible` (valmis alus, muutmata)

Paigaldatakse käsuga:

```
git clone https://github.com/CosmoBlk/email-marketing-bible.git \
  .claude/skills/email-marketing-bible
rm -rf .claude/skills/email-marketing-bible/.git
```

`.git` eemaldatakse, et vältida pesastatud repo't — failid commit'itakse
team-17 ajalukku. Annab üldise e-maili turunduse sügavuse (strateegia,
deliverability, segmenteerimine, copywriting, analüütika). Neutraalne alus,
mida ei muudeta.

### Osa 2 — `lv-vet-email-funnel` (custom-kiht)

Asukoht: `.claude/skills/lv-vet-email-funnel/`

Õhuke, Ravimuse + Läti vetiturule suunatud kiht, mis tugineb alusele.

```
lv-vet-email-funnel/
├── SKILL.md                      # frontmatter + ülevaade + töövoog
└── references/
    ├── product-ravimus-vet.md    # toote faktid + müügiargumendid (läti k)
    ├── deliverability.md         # autentimine, soojendus, listi hügieen (open rate'i alus)
    ├── cold-outreach.md          # külma e-posti taristu, õiguslik alus, jada-loogika
    ├── contact-enrichment.md     # e-postist arsti/kliiniku leidmine + andmemudel
    ├── personalization.md        # 2-tasandi personaliseerimine: segment + kontakt
    ├── funnel-framework.md       # funneli etapid + UTM + mõõdikud + MPP hoiatus
    ├── ab-testing.md             # mida testida, kuidas võitja valida
    ├── latvia-market.md          # toon, GDPR/ePrivacy, meditsiiniseadme reklaam
    └── email-templates-lv.md     # läti k külm jada + pealkirja/eelvaate praktikad
```

---

## Komponendid

### SKILL.md
Frontmatter `name` + `description` (käivitub, kui kasutaja koostab Ravimuse
e-maili kampaaniat Läti vetidele). Sisaldab lühikonteksti, viited
`references/` failidele ja töövoo sammud:

```
0. Taristu-kontroll: domeen autenditud + soojendatud, list verifitseeritud,
   õiguslik alus olemas (deliverability.md, cold-outreach.md)
1. Sisend: kontakti e-post(id) + kaasatuse andmed
2. Rikasta: leia nimi, kliinik, loomatüüp (contact-enrichment.md)
3. Segment: käitumise järgi (kaasatud / vaibunud / kontakteerimata)
4. Personaliseeri: segment + kontakti andmed → kohandatud kiri
5. Jada/mall: vali õige samm külmas jadas (email-templates-lv.md)
6. Pealkiri: koosta + eelvaate-tekst (email-templates-lv.md)
7. UTM: märgista lingid (funnel-framework.md)
8. A/B: planeeri test (ab-testing.md)
```

### references/deliverability.md
Open rate'i tegelik alus. Kui kiri ei jõua postkasti, on kõik muu kasutu.

- **Autentimine:** SPF, DKIM (2048-bit), DMARC (`none` → `quarantine` →
  `reject`), one-click unsubscribe. 2024–2025 lükkavad Gmail/Yahoo/Microsoft
  autentimata masspostituse tagasi.
- **Domeeni soojendus:** maht järk-järgult üles, mitte 0-st tuhandeni.
- **Listi hügieen:** verifitseeri aadressid enne saatmist (bounce'id tapavad
  maine), eemalda korduvad mitte-avajad (sunset-poliitika).
- **Sisu:** väldi rämpssõnu ja liigseid linke/pilte, hoia tekst-pildi tasakaal.

### references/cold-outreach.md
Külma prospekteerimise eriloogika (vt ka ülal "Külma listi tegelikkus"):

- **Õiguslik alus:** ePrivacy + GDPR, B2B õigustatud huvi, opt-out igas
  kirjas, andmetöötluse teavitus. Märgitud riskina, mitte juriidilise nõuna.
- **Taristu:** eraldi saatmisdomeen (kaitseb `nanordica.com` mainet), aeglane
  soojendus, väike päevamaht, aadresside verifitseerimine. Massi-ESP ei sobi.
- **Jada (mitte üksik kiri):** külm ost ei tule esimesest kirjast. 4–5 sammu:
  esmane pöördumine → väärtus/tõend → juhtumi-näide → pakkumine → "breakup".
  Vahe-eesmärk on klikk/vastus, alles siis ost.
- **Stiil:** lühike, tekstipõhine, tugevalt personaliseeritud (külm nõuab
  rohkem personaliseerimist kui opt-in).

### references/contact-enrichment.md
Töövoog, kuidas paljast e-posti aadressist arst/kliinik üles leida, sest
muud andmed kui e-post ja kaasatus on vaja juurde otsida:

- **E-posti domeen** → kliiniku tuvastus (nt `@kliinikunimi.lv`).
- **Avalikud allikad**: Läti veterinaarregister (Pārtikas un veterinārais
  dienests), Latvijas Veterinārārstu biedrība, kliiniku veebileht, Google.
- **Mida koguda** (andmemudel): eesnimi, kliiniku nimi, loomatüüp
  (väikeloom / suurloom / segapraksis), regioon, roll.
- **Fallback**: kui kontakti ei leia, kasuta ainult käitumispõhist segmenti
  ja üldist vetisõnumit — ära genereeri välja mõeldud (hallutsineeritud)
  andmeid. Märgi kontakt "rikastamata".
- Privaatsus: ainult avalikult kättesaadav info; vt `latvia-market.md`.

### references/personalization.md
Kahe tasandi personaliseerimine:

- **Tasand 1 — segment (käitumine):** kontakteerimata / pole avanud → külm
  jada (cold-outreach.md); avas/klikkis → soe järelpöördumine ja pakkumine;
  klikkis aga ei ostnud → konkreetne tootepakkumine + tõend.
- **Tasand 2 — kontakt (rikastatud):** pöördumine nime järgi, kliiniku
  mainimine, ja **loomatüübi-põhised tingimusplokid** — väikeloomaarstile
  rahutu kassi/koera sidemevahetuse näide, suurloomaarstile hobuse/veise
  kroonilise haavandi näide.
- **Renderdus:** ESP merge-väljad (`{{eesnimi}}`, `{{kliinik}}`) +
  tingimuslik sisu. Skill annab teksti variandid; ESP paneb kokku.

### references/funnel-framework.md
Funneli etapid ja mida igal etapil mõõta:

```
Saadetud → Kohale toimetatud → Avatud → Klikitud → Tootelehe vaade → Ost
```

Kuna tööriista-integratsiooni pole, õpetab:
- **UTM-linkide** märgistamine (`utm_source`, `utm_medium=email`,
  `utm_campaign`, `utm_content` A/B variandi jaoks), et veebianalüütikas näeks,
  *milline kiri* müügi tõi ja *mis etapil* lehtrist välja kukutakse.
- ESP raporti lugemine (open rate, CTR) + veebianalüütika (tootelehe →
  ost konversioon) kokku panemine, et leida funneli pudelikael.
- **⚠️ MPP hoiatus:** Apple Mail eellaadib pikslid, nii et ~pool avamistest
  pole päris inimene. Open rate on moonutatud. Tõene mõõdik on **klikk ja
  ost**, mitte avamine. Sea see ka eesmärgiks: 25–35% open rate on suunis,
  aga otsus tehakse kliki ja konversiooni põhjal.

### references/ab-testing.md
- Mida testida: pealkiri, eelvaate-tekst, CTA, saatmisaeg, pakkumine.
- **Üks muutuja korraga.**
- Kuidas lugeda tulemust: piisav valim, ei kuuluta poolikut testi võitjaks.
- Kuidas `utm_content`-iga A/B variante veebis lõpuni jälgida (mitte ainult
  avamise/kliki tasandil, vaid kuni ostuni).

### references/latvia-market.md
- Läti keele toon ja lokaliseerimine (mitte masintõlge eesti keelest).
- GDPR + ePrivacy (külm B2B): õigustatud huvi, opt-out igas kirjas,
  andmetöötluse teavitus. Vt ka `cold-outreach.md`.
- **Meditsiiniseadme reklaami nõuded** — RavimusVET on meditsiiniseade;
  väited paranemiskiiruse kohta peavad olema tõendatud (kliiniline uuring on
  olemas, viidata sellele korrektselt).

### references/email-templates-lv.md
**Külm jada** (4–5 sammu), läti keeles, tekstipõhine, CTA viib tootelehele.
Iga samm sisaldab **merge-välju** (`{{eesnimi}}`, `{{kliinik}}`) ja
**loomatüübi tingimusplokke** (väikeloom / suurloom), et sama mall
personaliseeruks iga kontaktile (vt `personalization.md`):
1. Esmane pöördumine (lühike, personaalne, üks konkreetne kasu)
2. Väärtus + tõend (kliiniline uuring, ~2× kiirem paranemine)
3. Juhtumi-näide (atraumaatiline sidemevahetus loomatüübi järgi)
4. Pakkumine (näidis / proovikomplekt / sooduspakkumine)
5. "Breakup" (viimane kiri, madala surve väljumistee)

Lisaks **pealkirja + eelvaate-teksti praktikad** (open rate'i sisuhoob):
- Pealkiri lühike (~30–50 tähemärki), konkreetne kasu või uudishimu,
  personaliseeritud (`{{kliinik}}`), väldi rämpssõnu ja CAPS-i.
- Eelvaate-tekst täiendab pealkirja, ei korda seda.
- Pealkiri on A/B esmane testimuutuja (vt `ab-testing.md`).

---

## Mis EI ole skillis (YAGNI)

- Päris müügiandmete dashboard — käib ESP-st/veebianalüütikast, mitte
  teadmiste-skillist.
- E-kirjade saatmine / ESP-integratsioon.
- Tooteandmebaas — ainult `product-ravimus-vet.md`-s fikseeritud faktid.

---

## Riskid ja lahtised otsad

1. **🟠 Läti tootelehte pole.** `https://www.nanordica.com/lv/ravimus` annab
   404. CTA suunab praegu ingliskeelsele lehele
   (`https://www.nanordica.com/ravimus`). Läti arst saab inglise keeles lehe,
   mitte emakeelse. Ingliskeelne leht töötab, aga lätikeelne maandumisleht
   tõstaks konversiooni. Soovitus järgmiseks sammuks, mitte praegune blokeerija.
2. **🔴 Külm e-post + õiguslik alus.** ePrivacy + GDPR. Külm turundus
   loomaarstidele vajab õigustatud huvi alust, opt-out'i ja teavitust. Ma pole
   jurist. Kinnita see enne saatmist. Suurim risk kogu projektis.
3. **🔴 Massi-ESP keelab külma.** Mailchimp jt sulgevad konto külma listi
   peale. Vajad eraldi cold-outreach taristut + eraldi saatmisdomeeni, et mitte
   põletada `nanordica.com` maine.
4. **Meditsiiniseadme reklaam** — väited peavad vastama Läti reklaaminõuetele.
5. **Rikastamise täpsus ja privaatsus** — e-postist arsti leidmine ei õnnestu
   alati. Skill ei tohi andmeid välja mõelda; leidmata kontakt läheb
   käitumispõhisesse segmenti. Ainult avalik info.
6. **Open rate ootus** — 25–35% on külmal listil ambitsioonikas ja MPP tõttu
   moonutatud. Jälgi klikki ja ostu kui tõest mõõdikut.

---

## "Valmis" kriteerium

- `email-marketing-bible` paigaldatud ja Claude'ile nähtav.
- `lv-vet-email-funnel` paigaldatud, `SKILL.md` frontmatter korrektne.
- Test: küsin "koosta Ravimuse külm pöördumiskiri Läti vetile" ja saan läti
  keeles tekstipõhise kirja: hea pealkiri + eelvaade, üks konkreetne kasu,
  opt-out, CTA tootelehele + UTM-märgistus ja A/B soovitus pealkirjale.
- Personaliseerimise test: annan ühe kontakti e-posti + kaasatuse staatuse,
  Claude rikastab (või märgib "rikastamata"), valib segmendi ja annab selle
  kontakti jaoks kohandatud kirja loomatüübi-põhise plokiga.
- Deliverability test: skill esitab enne saatmist taristu-kontrollnimekirja
  (SPF/DKIM/DMARC, soojendus, verifitseeritud list, õiguslik alus).
