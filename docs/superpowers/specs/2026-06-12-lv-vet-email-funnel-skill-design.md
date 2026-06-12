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

**Tarne tüüp:** teadmiste-skill. E-kirjade saatmist skill ise ei tee. Kasutaja
saadab kirjad **ettevõtte meilboxist** üks-ühele. Skill annab teadmised,
töövoo, personaliseeritud kirjad ja jada-loogika.

---

## Sihtgrupp ja kontekst

| Parameeter | Väärtus |
|------------|---------|
| Bränd | **Ravimus** (tootja Nanordica Medical) |
| Toode | **RavimusVET** — steriilne haavaside |
| Sihtgrupp | Läti veterinaarkliinikud ja loomaarstid |
| Keel | **Läti keel** |
| Funneli eesmärk | Ost veebilehel (külmas jadas: enne vastus/klikk, siis ost) |
| CTA sihtleht | `https://www.nanordica.com/ravimus` (ingliskeelne leht) |
| Olemasolevad andmed | **E-posti aadressid + kaasatuse andmed** (avab / klikib / mitteaktiivne) |
| Juurde otsitavad andmed | Nimi, kliinik, loomaliik, regioon, värske teadusartikkel — rikastatakse päringuga |
| Listi tüüp | **Külm prospekteerimine.** Kasutaja kinnitab: aadressid saadud turvaliselt, õiguslik alus olemas |
| Saatmise kanal | **Ettevõtte meilbox** (üks-ühele stiil, mitte massi-ESP) |

### Külma prospekteerimise raamistik (meilboxist)

List on külm ja kirjad lähevad ettevõtte meilboxist üks-ühele. Kasutaja on
kinnitanud, et aadressid on saadud turvaliselt ja õiguslik alus on olemas
(õigustatud huvi, opt-out, teavitus). Sellest lähtub strateegia:

1. **Meilbox sobib külma jaoks hästi.** Üks-ühele, tekstipõhine, personaalne
   kiri pärisinimese aadressilt jõuab postkasti paremini kui massi-ESP saadetis.
   Hind: madal maht ja käsitsi/poolautomaatne saatmine.
2. **Kaitse ettevõtte domeeni mainet.** Hoia päevamaht väike, kasva järk-järgult,
   verifitseeri aadressid enne saatmist (bounce'id rikuvad maine), eemalda
   kohe bounce'id ja opt-out'id. Kui maht kasvab suureks, kaalu eraldi
   saatmisdomeeni.
3. **Open rate'i mõõtmise lõks.** Pärismeilbox **ei näita open rate'i** ilma
   eraldi tööriistata (mail-merge / jälgimispiksel). Vastuse-määr ja klikk
   (UTM kaudu) on meilboxist tõesemad mõõdikud. 25–35% open rate'i sihiks
   seadmiseks on vaja jälgimisega mail-merge tööriista; muidu jälgi vastust.
4. **Maksimaalne ambitsioon = parimad praktikad.** Tugev personaliseerimine,
   värske info igas kirjas, hea pealkiri, progressiivne jada (vt allpool).

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
0. Taristu-kontroll: meilbox autenditud (SPF/DKIM/DMARC), maht väike,
   list verifitseeritud (deliverability.md, cold-outreach.md)
1. Sisend: kontakti e-post + kaasatuse andmed + mitu kirja juba saadetud
2. Rikasta: leia nimi, kliinik, loomaliik + värske teadusartikkel
   (contact-enrichment.md)
3. Segment: käitumise järgi (vastas / klikkis / avas / kontakteerimata)
4. Personaliseeri: segment + kontakti andmed + loomaliik → kohandatud kiri
5. Jada-samm: vali järgmine samm + ooteaeg saadetud kirjade arvu järgi
   (email-templates-lv.md). Jätka kuni vastus / opt-out / bounce.
6. Värske haak: iga kiri toob uut infot (artikkel / pakkumine / sooduskood)
7. Pealkiri: koosta + eelvaate-tekst (email-templates-lv.md)
8. UTM: märgista lingid (funnel-framework.md)
9. A/B: planeeri test (ab-testing.md)
```

### references/deliverability.md
Open rate'i tegelik alus. Kui kiri ei jõua postkasti, on kõik muu kasutu.
Kohandatud meilboxist saatmiseks.

- **Autentimine:** veendu, et ettevõtte domeenil on SPF, DKIM (2048-bit) ja
  DMARC korras. Ilma selleta lükkavad Gmail/Yahoo/Microsoft kirja tagasi.
- **Maht ja soojendus:** meilboxist väike päevamaht, kasva järk-järgult.
  Liiga palju korraga = rämps + domeeni maine kahjustus.
- **Listi hügieen:** verifitseeri aadressid enne saatmist (bounce'id tapavad
  maine), eemalda kohe bounce'id ja opt-out'id.
- **Sisu:** lühike, tekstipõhine, väldi rämpssõnu ja liigseid linke/pilte.
- **Mõõtmine:** pärismeilbox ei näita open rate'i ilma jälgimistööriistata.
  Kui open rate on vaja mõõta, lisa jälgimisega mail-merge tööriist; muidu
  jälgi vastust ja klikki (UTM).

### references/cold-outreach.md
Külma prospekteerimise eriloogika meilboxist (vt ka ülal "Külma
prospekteerimise raamistik"):

- **Õiguslik alus:** kasutaja kinnitanud. Iga kiri sisaldab opt-out'i ja
  selget saatja-identiteeti.
- **Taristu:** ettevõtte meilbox, väike päevamaht, aadresside verifitseerimine.
- **Jada jätkub kuni signaalini.** Lõpeta alles: vastus (ka "ei"), opt-out,
  bounce või blokk. Iga kiri toob **uut infot** — ära korda eelmist.
- **Värske haak igas kirjas:** uus teadusartikkel (enrichmenti kaudu), uus
  pakkumine, sooduskood, uus kasutusnäide. Kui uut haaki pole, ära saada.
- **Progressiivne ooteaeg** (parima praktika järgi vahe kasvab, vt tabel
  `email-templates-lv.md`-s): mida rohkem kirju juba läinud, seda pikem paus.
- **Stiil:** lühike, tekstipõhine, tugevalt personaliseeritud.
- **Lõpetamine:** "ei" → austa, eemalda jadast; opt-out / bounce → eemalda
  kohe ka listist.

### references/contact-enrichment.md
Töövoog, kuidas paljast e-posti aadressist arst/kliinik üles leida, sest
muud andmed kui e-post ja kaasatus on vaja juurde otsida:

- **E-posti domeen** → kliiniku tuvastus (nt `@kliinikunimi.lv`).
- **Avalikud allikad**: Läti veterinaarregister (Pārtikas un veterinārais
  dienests), Latvijas Veterinārārstu biedrība, kliiniku veebileht, Google.
- **Mida koguda** (andmemudel): eesnimi, kliiniku nimi, **konkreetne loomaliik
  / spetsialiseerumine** (nt kassid, koerad, hobused, veised, eksootilised),
  regioon, roll.
- **Värske sisu rikastamine (igale kirjale uus haak):** otsi kontaktile sobiv
  hiljutine teadusartikkel, mis toetab RavimusVET-i tema kasutusjuhul (nt
  hobuste krooniliste haavandite ravi). Lingi see kirja kui uus väärtus. Ainult
  päris, kontrollitud allikad — mitte väljamõeldud viited.
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
  mainimine ja **konkreetse loomaliigi näide** selle kontakti
  spetsialiseerumise järgi — kassiarstile kassi näide, hobusearstile hobuse
  kroonilise haavandi näide, veisearstile veise oma. Mitte üldine "väikeloom".
- **Renderdus:** kuna saadetakse meilboxist, kirjutab skill iga kontakti jaoks
  **valmis personaliseeritud teksti** (mitte ainult merge-mall). Kui kasutaja
  kasutab mail-merge tööriista, antakse ka kohatäidetega versioon.

### references/funnel-framework.md
Funneli etapid ja mida igal etapil mõõta:

```
Saadetud → Kohale toimetatud → (Avatud) → Vastus / Klikk → Tootelehe vaade → Ost
```

Meilboxist saatmise tegelikkus:
- **UTM-linkide** märgistamine (`utm_source`, `utm_medium=email`,
  `utm_campaign`, `utm_content` A/B variandi jaoks), et veebianalüütikas näeks,
  *milline kiri* müügi tõi ja *mis etapil* lehtrist välja kukutakse.
- **Vastuse-määr** on meilboxi-jada peamine kaasatuse-mõõdik (avamist sa ei näe).
- Veebianalüütika (klikk → tootelehe vaade → ost) leiab funneli pudelikaela.
- **⚠️ Open rate'i hoiatused:** (1) meilbox ei mõõda avamist ilma
  jälgimistööriistata; (2) ka tööriistaga moonutab Apple Mail (eellaadib
  pikslid, ~pool "avamisi" pole inimene). Seega: 25–35% open rate on suunis,
  aga **otsus tehakse vastuse, kliki ja ostu põhjal**.

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
**Avatud külm jada**, läti keeles, tekstipõhine, CTA viib tootelehele.
Jada **ei lõpe fikseeritud arvu juures** — jätka kuni vastus (ka "ei"),
opt-out või bounce. **Iga kiri toob uut infot** (artikkel, pakkumine,
sooduskood, uus nurk); ära korda eelmist. Iga kiri personaliseeritakse
kontakti **konkreetse loomaliigi** järgi (vt `personalization.md`).

Kirja-nurkade pank (kasuta järjest, uus haak igas kirjas):
1. Esmane pöördumine — üks konkreetne kasu kontakti loomaliigile
2. Värske teadusartikkel (enrichmenti kaudu leitud), mis toetab kasutusjuhtu
3. Juhtumi-näide / atraumaatiline sidemevahetus loomaliigi kontekstis
4. Pakkumine: näidis / proovikomplekt
5. Sooduskood (ajaliselt piiratud)
6. Uus nurk: kuluvõrdlus hõbesidemega, suuruste valik vm
7+ Iga järgnev kiri uus haak; kui uut haaki pole, ära saada

**Progressiivne ooteaeg** (vahe kasvab saadetud kirjade arvuga, parima
praktika järgi):

| Saadetud kirju | Paus enne järgmist |
|----------------|--------------------|
| 1 → 2          | 3 päeva            |
| 2 → 3          | 4 päeva            |
| 3 → 4          | 7 päeva            |
| 4 → 5          | 10 päeva           |
| 5 → 6          | 14 päeva           |
| 6+             | 21–30 päeva        |

**Pealkirja + eelvaate-teksti praktikad** (open rate'i sisuhoob):
- Pealkiri lühike (~30–50 tähemärki), konkreetne kasu või uudishimu,
  personaliseeritud (kliinik / loomaliik), väldi rämpssõnu ja CAPS-i.
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
2. **🟡 Õiguslik alus — kasutaja kinnitanud.** Kasutaja kinnitas, et aadressid
   on saadud turvaliselt ja õiguslik alus on olemas. Skill tagab opt-out'i ja
   selge saatja-identiteedi igas kirjas. Vastutus jääb kasutajale.
3. **🟠 Domeeni maine (meilbox).** Külma saatmine ettevõtte meilboxist võib
   `nanordica.com` mainet kahjustada, kui maht kasvab või tulevad kaebused.
   Maandus: väike maht, soojendus, verifitseeritud list, kohene bounce/opt-out
   eemaldamine. Suure mahu korral kaalu eraldi saatmisdomeeni.
4. **🟠 Open rate'i mõõtmine.** Meilbox ei näita avamist ilma
   jälgimistööriistata. 25–35% sihiks vajad mail-merge jälgimist; muidu on
   peamine mõõdik vastus ja klikk. MPP moonutab avamist niikuinii.
5. **Meditsiiniseadme reklaam** — väited peavad vastama Läti reklaaminõuetele.
6. **Rikastamise täpsus** — e-postist arsti leidmine ei õnnestu alati. Skill ei
   tohi andmeid ega teadusviiteid välja mõelda; leidmata kontakt läheb
   käitumispõhisesse segmenti. Ainult avalik, kontrollitud info.

---

## "Valmis" kriteerium

- `email-marketing-bible` paigaldatud ja Claude'ile nähtav.
- `lv-vet-email-funnel` paigaldatud, `SKILL.md` frontmatter korrektne.
- Test: küsin "koosta Ravimuse külm pöördumiskiri Läti vetile" ja saan läti
  keeles tekstipõhise kirja: hea pealkiri + eelvaade, üks konkreetne kasu,
  opt-out, CTA tootelehele + UTM-märgistus ja A/B soovitus pealkirjale.
- Personaliseerimise test: annan ühe kontakti e-posti + kaasatuse staatuse,
  Claude rikastab (või märgib "rikastamata"), valib segmendi ja annab selle
  kontakti jaoks kohandatud kirja **konkreetse loomaliigi** näitega.
- Jada-test: annan "see on 4. kiri sellele kontaktile, eelmised teemad olid X,
  Y, Z" ja saan uue nurgaga kirja (mitte kordus) + õige ooteaja (7 päeva).
- Värske haak: jada-kiri sisaldab uut elementi (päris teadusartikkel /
  sooduskood / pakkumine), mitte korratud sisu.
- Deliverability test: skill esitab meilboxi-kontrollnimekirja
  (SPF/DKIM/DMARC, väike maht, verifitseeritud list) ja selgitab open rate'i
  mõõtmise piirangut.
