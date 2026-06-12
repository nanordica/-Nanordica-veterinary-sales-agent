# Läti kirja-mallid ja jada-loogika

**Avatud külm jada**, läti keeles, tekstipõhine, CTA viib tootelehele.
Jada **ei lõpe fikseeritud arvu juures** — jätka kuni vastus (ka "ei"),
opt-out või bounce.

Kõik allolev läti tekst on **mustand — peab läbima automaatse QA värava**
(`latvian-qa.md`) enne valmis-märkimist. Natiivkõnelejat tiimis pole.

## Iga kirja reeglid

- **Avarida = personaalne tähelepanek** (kliinik / regioon / eriala), mitte toode.
- **Üks CTA** kirja kohta.
- Saatja päris inimese nimi.
- **Iga kiri toob uut infot** — ära korda eelmist. Kui uut haaki pole, ära saada.
- **Loobumine = sõbralik rida kirja kõige lõpus**, allkirja järel, CTA-st
  eraldi. Mitte üleskutse, mitte CTA kõrval (vt `cold-outreach.md`).
- Personaliseeri **konkreetse loomaliigi** järgi (`personalization.md`).

## Kirja-nurkade pank (uus haak igas kirjas)

1. **Esmane pöördumine** — üks konkreetne kasu kontakti loomaliigile
2. **Värske teadusartikkel** (enrichmenti kaudu), mis toetab kasutusjuhtu
3. **Juhtumi-näide** — atraumaatiline sidemevahetus loomaliigi kontekstis
4. **Pakkumine** — näidis / proovikomplekt
5. **Sooduskood** — ajaliselt piiratud
6. **Uus nurk** — kuluvõrdlus hõbesidemega, suuruste valik vm
7. **7+** — iga järgnev kiri uus haak; kui haaki pole, ära saada

## Progressiivne ooteaeg

| Saadetud kirju | Paus enne järgmist |
|----------------|--------------------|
| 1 → 2 | 3 päeva |
| 2 → 3 | 4 päeva |
| 3 → 4 | 7 päeva |
| 4 → 5 | 10 päeva |
| 5 → 6 | 14 päeva |
| 6+ | 21–30 päeva |

## Pealkiri + eelvaate-tekst

- Pealkiri lühike (~30–50 tähemärki), konkreetne kasu või uudishimu,
  personaliseeritud (kliinik / loomaliik), väldi rämpssõnu ja CAPS-i.
- Külm pealkiri olgu **vestluslik**, nagu üks-ühele kiri, mitte
  reklaamilöök.
- Eelvaate-tekst täiendab pealkirja, ei korda seda.
- Pealkiri on A/B esmane testimuutuja (`ab-testing.md`).

Pealkirja näited (lv, mustand):
- `{{eesnimi}}, ātrāka brūču dzīšana?`
- `Jautājums par pārsiešanu — {{kliinik}}`
- `Atraumatiska pārsēja maiņa nemierīgiem dzīvniekiem`

## Näidiskiri 1 — esmane pöördumine, kassiarst (lv mustand)

> **Pealkiri:** {{eesnimi}}, atraumatiska pārsiešana kaķiem?
>
> Labdien, {{eesnimi}}!
>
> Pamanīju, ka {{kliinik}} specializējas kaķu un suņu aprūpē.
>
> Esmu Karmen no Nanordica. Izstrādājām RavimusVET — sterilu brūču pārsēju ar
> zīda nanošķiedru un sudraba un vara nanodaļiņām. Klīniskā pētījumā brūces
> dzija gandrīz divreiz ātrāk nekā ar sudraba pārsējiem, un pārsēja maiņa ir
> atraumatiska — mazāk stresa nemierīgam kaķim.
>
> Vai būtu interese apskatīt? [CTA → tooteleht + UTM]
>
> Ar cieņu,
> Karmen, Nanordica
>
> _Jūsu kontaktu atradām publiskajā veterinārārstu reģistrā._
> _Ja nevēlaties no manis vairāk saņemt vēstules, vienkārši pasakiet — es sapratīšu._

Loobumine on **sõbralik rida kirja kõige lõpus**, allkirja järel, CTA-st
eraldi — mitte nähtav üleskutse kirja kehas (`cold-outreach.md`).

CTA-link tuleb märgistada UTM-iga (`funnel-framework.md`).

## Töövoog kirja koostamisel

1. Vaata kontakti staatust ja saadetud kirjade arvu.
2. Vali järgmine nurk pangast (ära korda eelmist).
3. Leia värske haak (`contact-enrichment.md`).
4. Kirjuta läti tekst, personaliseeri loomaliigi järgi.
5. Lisa UTM-link, opt-out, nimeline saatja.
6. **Läbi automaatne QA värav** (`latvian-qa.md`): korrektuur + tagasitõlge +
   väite-kontroll. Alles siis märgi valmis.
7. Anna ka kohatäidetega versioon mail-merge tööriista jaoks.
