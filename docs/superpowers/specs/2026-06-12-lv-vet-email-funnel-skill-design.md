# Disain: e-maili turundusskill — Ravimus, Läti veterinaarturg

**Kuupäev:** 2026-06-12
**Autor:** Karmen + Claude
**Staatus:** kinnitatud — ehitamisel

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
| Saatmise kanal | **Ettevõtte Outlook / Microsoft 365 meilbox + mail-merge tööriist** (lemlist / Woodpecker / Mailshake / QuickMail) |

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
3. **Open rate'i mõõdab mail-merge tööriist.** Pärismeilbox üksi ei näita open
   rate'i. Lahendus: meilboxi peal jälgimisega mail-merge tööriist (Mailmeteor,
   GMass, YAMM vms). See saadab jada, paneb personaliseerimise kokku ja mõõdab
   open rate'i + klikki. Nii saab 25–35% sihti jälgida. NB: open rate on MPP
   tõttu ikka moonutatud — vastus ja klikk jäävad tõesemaks mõõdikuks.
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
    ├── latvian-qa.md             # AUTOMAATNE läti keele kvaliteedikontroll (pole natiivkõnelejat)
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
- **Saatja:** päris inimese nimi (nt "Karmen, Nanordica"), mitte `info@` ega
  `no-reply`. Nimeline saatja on külmas e-postis suur open-rate hoob.
- **Maht ja soojendus:** alusta ~10–20 kirja/päevas, kasva aeglaselt, hoia
  ~40–50/päevas lael ühe meilboxi kohta. Bounce alla 2–3%, spam-kaebused
  alla 0,1%. Üle selle = rämps + domeeni maine kahjustus.
- **Listi hügieen:** verifitseeri aadressid enne saatmist (bounce'id tapavad
  maine), eemalda kohe bounce'id ja opt-out'id.
- **Sisu:** lühike, tekstipõhine, väldi rämpssõnu ja liigseid linke/pilte.
- **Mõõtmine:** kasuta meilboxi peal jälgimisega mail-merge tööriista
  (Mailmeteor / GMass / YAMM), et näha open rate'i ja klikke. Sama tööriist
  saadab jada ja täidab merge-väljad. UTM jääb veebipoolse konversiooni jaoks.

### references/cold-outreach.md
Külma prospekteerimise eriloogika meilboxist (vt ka ülal "Külma
prospekteerimise raamistik"):

- **Õiguslik alus:** kasutaja kinnitanud. Iga kiri sisaldab **sõbralikku
  loobumist kirja kõige lõpus** (allkirja järel, CTA-st eraldi, mitte
  üleskutse) ja selget saatja-identiteeti.
- **Taristu:** ettevõtte meilbox + mail-merge jälgimistööriist (Mailmeteor /
  GMass / YAMM) jada saatmiseks, personaliseerimiseks ja open/klikk-mõõtmiseks.
  Väike päevamaht, aadresside verifitseerimine.
- **Jada jätkub kuni signaalini.** Lõpeta alles: vastus (ka "ei"), opt-out,
  bounce või blokk. Iga kiri toob **uut infot** — ära korda eelmist.
- **Värske haak igas kirjas:** uus teadusartikkel (enrichmenti kaudu), uus
  pakkumine, sooduskood, uus kasutusnäide. Kui uut haaki pole, ära saada.
- **Progressiivne ooteaeg** (parima praktika järgi vahe kasvab, vt tabel
  `email-templates-lv.md`-s): mida rohkem kirju juba läinud, seda pikem paus.
- **Stiil:** lühike, tekstipõhine, tugevalt personaliseeritud. Avarida =
  personaalne tähelepanek kontakti kohta (kliinik / regioon / eriala), mitte
  toode. **Üks CTA kirja kohta.**
- **Vastus → inimene.** Kui keegi vastab, jada peatub ja inimene võtab vestluse
  üle (müük lõpetatakse käsitsi). See on skilli skoobist väljas, aga jada
  loogika peab vastuse korral selgelt peatuma.
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
- **Mail-merge tööriist** (Mailmeteor / GMass / YAMM) mõõdab open rate'i ja
  klikki; vastuse-määr on lisaks tugev kaasatuse-mõõdik.
- **Vastus → inimene:** vastuse korral jada peatub ja inimene jätkab müüki.
- Veebianalüütika (klikk → tootelehe vaade → ost) leiab funneli pudelikaela.
- **⚠️ MPP hoiatus:** Apple Mail eellaadib pikslid, ~pool "avamisi" pole
  inimene. 25–35% open rate on suunis, aga **otsus tehakse vastuse, kliki ja
  ostu põhjal**.

### references/ab-testing.md
- Mida testida: pealkiri, eelvaate-tekst, CTA, saatmisaeg, pakkumine.
- **Üks muutuja korraga.**
- **Väikese listi tegelikkus:** meilboxi-list on väike, statistiline olulisus
  on raskesti saavutatav. Testi **suuri erinevusi** (terve nurk või
  pealkirja-tüüp), mitte mikro-muudatusi. Loe tulemust suunisena, mitte
  tõestusena; ära kuuluta poolikut testi võitjaks.
- **Saatmisaja lähtehüpotees:** vetid on päeval hõivatud. Alusta T–N hommikul
  (enne kliinikupäeva) ja testi sealt edasi.
- Kuidas `utm_content`-iga A/B variante veebis lõpuni jälgida (mitte ainult
  avamise/kliki tasandil, vaid kuni ostuni).
- **Mis kiri töötab kõige paremini:** võrdle nurkade kaupa vastuse-määra +
  kliki + konversiooni, et leida võitev nurk (mitte ainult open rate).

### references/latvia-market.md
- Läti keele toon ja lokaliseerimine (mitte masintõlge eesti keelest).
  Kvaliteedikontroll on **automaatne** (tiimis pole natiivkõnelejat) —
  vt `latvian-qa.md`.
- GDPR + ePrivacy (külm B2B): õigustatud huvi, opt-out igas kirjas,
  andmetöötluse teavitus, **andmeallika avalikustamine** (kust kontakt saadi).
  Vt ka `cold-outreach.md`.

### references/latvian-qa.md
**Automaatne läti keele kvaliteedikontroll.** Tiimis pole natiivkõnelejat,
seega iga läti kiri läbib enne valmis-märkimist automaatse värava:

1. **Korrektuuri-pass:** Claude loeb teksti range korrektorina —
   käänded/pöörded, grammatika, loomulik sõnajärg, meditsiiniterminid.
2. **Tagasitõlke-värav:** tõlgi läti tekst tagasi eesti keelde ja võrdle
   algse briifi mõttega. Tähenduse triivi korral genereeri uuesti.
3. **Väited:** kontrolli, et meditsiiniseadme väited vastavad
   `product-ravimus-vet.md`-le (ei liialda).
4. **Valikuline väline tööriist:** LanguageTool (`lv`) või hunspell (`lv_LV`)
   spelling-kontroll kõva väravana.

**Aus piirang:** automaatne kontroll ei asenda täielikult natiivkõnelejat,
eriti väidete nüansis. Jääkrisk on dokumenteeritud (vt riskid).
- **Meditsiiniseadme reklaami nõuded** — RavimusVET on meditsiiniseade;
  väited paranemiskiiruse kohta peavad olema tõendatud (kliiniline uuring on
  olemas, viidata sellele korrektselt).

### references/email-templates-lv.md
**Avatud külm jada**, läti keeles, tekstipõhine, CTA viib tootelehele.
Jada **ei lõpe fikseeritud arvu juures** — jätka kuni vastus (ka "ei"),
opt-out või bounce. **Iga kiri toob uut infot** (artikkel, pakkumine,
sooduskood, uus nurk); ära korda eelmist. Iga kiri personaliseeritakse
kontakti **konkreetse loomaliigi** järgi (vt `personalization.md`).

Iga kirja reeglid: **avarida = personaalne tähelepanek** (kliinik / regioon /
eriala), **üks CTA**, saatja päris inimese nimi, opt-out lõpus.

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

1. **🟢 CTA-leht ingliskeelne (kasutaja otsus).** `/lv/ravimus` puudub; CTA
   läheb teadlikult ingliskeelsele lehele `https://www.nanordica.com/ravimus`.
   Aktsepteeritud, mitte risk.
2. **🟡 Õiguslik alus — kasutaja kinnitanud.** Kasutaja kinnitas, et aadressid
   on saadud turvaliselt ja õiguslik alus on olemas. Skill tagab opt-out'i ja
   selge saatja-identiteedi igas kirjas. Vastutus jääb kasutajale.
3. **🟠 Domeeni maine (meilbox).** Külma saatmine ettevõtte meilboxist võib
   `nanordica.com` mainet kahjustada, kui maht kasvab või tulevad kaebused.
   Maandus: väike maht, soojendus, verifitseeritud list, kohene bounce/opt-out
   eemaldamine. Suure mahu korral kaalu eraldi saatmisdomeeni.
4. **🟡 Open rate'i mõõtmine — lahendatud tööriistaga.** Open rate'i mõõdab
   meilboxi peal mail-merge jälgimistööriist (Mailmeteor / GMass / YAMM). MPP
   moonutab avamist ikka, seega vastus ja klikk jäävad tõesemaks mõõdikuks.
5. **Meditsiiniseadme reklaam** — väited peavad vastama Läti reklaaminõuetele.
6. **Rikastamise täpsus** — e-postist arsti leidmine ei õnnestu alati. Skill ei
   tohi andmeid ega teadusviiteid välja mõelda; leidmata kontakt läheb
   käitumispõhisesse segmenti. Ainult avalik, kontrollitud info.
7. **🟠 Läti QA jääkrisk.** Tiimis pole natiivkõnelejat, kontroll on automaatne
   (korrektuur + tagasitõlge). See püüab enamiku vigu, aga ei asenda täielikult
   natiivkõnelejat, eriti meditsiiniväidete nüansis. Maandus: tagasitõlke-värav
   + range väite-kontroll; valikuline LanguageTool/hunspell.

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
- Läti QA test: genereeritud läti kiri läbib automaatse värava — korrektuur,
  tagasitõlge eesti keelde (mõte säilib) ja väite-kontroll product-faili vastu.
