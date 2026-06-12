# Külm prospekteerimine meilboxist

Külma jada eriloogika. Vt ka `deliverability.md` (taristu) ja
`latvia-market.md` (õiguslik).

## Lähtekoht

- List on külm. Kasutaja on kinnitanud, et aadressid on saadud turvaliselt ja
  õiguslik alus on olemas (õigustatud huvi).
- Kirjad lähevad ettevõtte meilboxist üks-ühele, mail-merge tööriistaga.

## Saatja ja stiil

- Päris inimese nimi (vt `deliverability.md`).
- Lühike, tekstipõhine, tugevalt personaliseeritud.
- **Avarida = personaalne tähelepanek** kontakti kohta (kliinik / regioon /
  eriala), mitte toode.
- **Üks CTA** kirja kohta — see on alati toote/väärtuse CTA, mitte loobumine.

### Opt-out — diskreetne, mitte üleskutse

Seaduslik nõue: igas kirjas peab olema loobumisvõimalus. Aga **ära tee sellest
nähtavat üleskutset**, eriti esimestes kirjades — see kutsub varakult lahkuma.

- **Asukoht:** alati **kirja kõige lõpus**, allkirja järel, **CTA-st eraldi**.
  Mitte kunagi CTA kõrval ega kirja kehas.
- **Toon: sõbralik ja inimlik**, mitte ametlik "loobu siit". Näide (lv):
  *"Ja nevēlaties no manis vairāk saņemt vēstules, vienkārši pasakiet — es sapratīšu."*
  (eesti k mõte: "kui sa ei soovi minult enam kirju saada, ütle lihtsalt — ma saan aru.")
- **Esimesed kirjad (1–3):** hoia eriti vaikne, üks sõbralik rida lõpus.
- **Hilisemad / "breakup"-kiri:** sama sõbralik rida; breakup võib olla pisut
  selgem, aga ikka soe.

## Jada loogika

- **Jada jätkub kuni signaalini.** Lõpeta alles, kui tuleb:
  - vastus (ka "ei"),
  - opt-out,
  - bounce või blokk.
- **Iga kiri toob uut infot** — ära korda eelmist.
- **Värske haak igas kirjas:** uus teadusartikkel (enrichmenti kaudu), uus
  pakkumine, sooduskood, uus kasutusnäide. **Kui uut haaki pole, ära saada.**
- **Progressiivne ooteaeg** (vahe kasvab kirjade arvuga) — tabel
  `email-templates-lv.md`-s.

## Vastuse käsitlus

- **Vastus → inimene.** Kui keegi vastab, jada peatub ja inimene võtab
  vestluse üle (müük lõpetatakse käsitsi). See on skilli skoobist väljas, aga
  jada peab vastuse korral kindlasti peatuma.
- **"Ei"** → austa, eemalda jadast.
- **Opt-out / bounce** → eemalda kohe jadast ja listist.

## Mida vältida

- Mahukas HTML, palju pilte, palju linke (paistab kui masspostitus).
- Sama sõnumi kordamine uue pealkirja all.
- Surve ja "viimane võimalus" iga kirja juures.
