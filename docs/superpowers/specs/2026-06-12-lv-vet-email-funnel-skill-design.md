# Disain: e-maili turundusskill — Ravimus, Läti veterinaarturg

**Kuupäev:** 2026-06-12
**Autor:** Karmen + Claude
**Staatus:** ülevaatamisel

---

## Eesmärk

Anda Claude'ile oskus koostada e-maili turunduskampaaniaid, mis konverdivad
Läti veterinaararstid Ravimuse klientideks ja suunavad nad veebilehel toodet
ostma. Skill peab toetama funneli jälgimist (mis hetkel müük toimub) ja A/B
testimist (milline kiri töötab kõige paremini).

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
    ├── funnel-framework.md       # funneli etapid + UTM + mõõdikud
    ├── ab-testing.md             # mida testida, kuidas võitja valida
    ├── latvia-market.md          # toon, GDPR/nõusolek, meditsiiniseadme reklaam
    └── email-templates-lv.md     # läti k mallid (5 tüüpi)
```

---

## Komponendid

### SKILL.md
Frontmatter `name` + `description` (käivitub, kui kasutaja koostab Ravimuse
e-maili kampaaniat Läti vetidele). Sisaldab: lühikonteksti, töövoo sammud
(eesmärk → segment → mall → UTM-märgistus → A/B plaan), ja viited
`references/` failidele.

### references/funnel-framework.md
Funneli etapid ja mida igal etapil mõõta:

```
Saadetud → Avatud → Klikitud → Tootelehe vaade → Ostukorv → Ost
```

Kuna tööriista-integratsiooni pole, õpetab:
- **UTM-linkide** märgistamine (`utm_source`, `utm_medium=email`,
  `utm_campaign`, `utm_content` A/B variandi jaoks), et veebianalüütikas näeks,
  *milline kiri* müügi tõi ja *mis etapil* lehtrist välja kukutakse.
- ESP raporti lugemine (open rate, CTR) + veebianalüütika (tootelehe →
  ost konversioon) kokku panemine, et leida funneli pudelikael.

### references/ab-testing.md
- Mida testida: pealkiri, eelvaate-tekst, CTA, saatmisaeg, pakkumine.
- **Üks muutuja korraga.**
- Kuidas lugeda tulemust: piisav valim, ei kuuluta poolikut testi võitjaks.
- Kuidas `utm_content`-iga A/B variante veebis lõpuni jälgida (mitte ainult
  avamise/kliki tasandil, vaid kuni ostuni).

### references/latvia-market.md
- Läti keele toon ja lokaliseerimine (mitte masintõlge eesti keelest).
- GDPR / nõusolek (B2B vetid).
- **Meditsiiniseadme reklaami nõuded** — RavimusVET on meditsiiniseade;
  väited paranemiskiiruse kohta peavad olema tõendatud (kliiniline uuring on
  olemas, viidata sellele korrektselt).

### references/email-templates-lv.md
Viis konversioonile suunatud malli, läti keeles, CTA viib tootelehele:
1. Tervitus / tutvustus (uus kontakt)
2. Toote tutvustus (müügiargumendid + kliiniline tõend)
3. Varu täienemine / korduvost (restock)
4. Win-back (mitteaktiivne kontakt)
5. Hariv (case study / atraumaatiline sidemevahetus kui kasu)

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
2. **Meditsiiniseadme reklaam** — väited peavad vastama Läti reklaaminõuetele.
3. **ESP valimata** — UTM ja A/B näited jäävad üldiseks, mitte konkreetse
   tööriista-spetsiifiliseks.

---

## "Valmis" kriteerium

- `email-marketing-bible` paigaldatud ja Claude'ile nähtav.
- `lv-vet-email-funnel` paigaldatud, `SKILL.md` frontmatter korrektne.
- Test: küsin Claude'ilt "koosta Ravimuse tutvustuskiri Läti vetidele" ja
  saan läti keeles kirja, mille CTA viib tootelehele + kaasas UTM-märgistuse
  ja A/B soovituse.
