# Personaliseerimine — kaks tasandit

## Tasand 1 — segment (käitumine)

Olemasolev kaasatuse-andmestik määrab lähenemise:

| Staatus | Lähenemine |
|---------|-----------|
| Kontakteerimata / pole avanud | Külm jada (`cold-outreach.md`) — esmane pöördumine, uus nurk igas kirjas |
| Avas / klikkis | Soe järelpöördumine + konkreetne pakkumine |
| Klikkis, aga ei ostnud | Otsene tootepakkumine + kliiniline tõend + sooduskood |
| Vastas | Jada peatub, inimene jätkab |

## Tasand 2 — kontakt (rikastatud)

Kasuta rikastatud andmeid (`contact-enrichment.md`):
- pöördumine **nime järgi**,
- **kliiniku mainimine** avareas,
- **konkreetse loomaliigi näide** kontakti eriala järgi.

### Loomaliigi-põhine näide (mitte üldine "väikeloom")

| Eriala | Haak |
|--------|------|
| Kassiarst | Atraumaatiline sidemevahetus rahutu kassi puhul — vähem stressi |
| Koeraarst | Kiirem paranemine + atraumaatiline vahetus aktiivse koera puhul |
| Hobusearst | Krooniliste haavandite kiirem paranemine, suuremad sidemed |
| Veisearst | Haavainfektsiooni kontroll karjas, tugev toime *S. aureus*'e vastu |
| Eksootilised | Õrn atraumaatiline vahetus tundlikul nahal |

## Renderdus

Kuna saadetakse meilboxist, kirjuta iga kontakti jaoks **valmis
personaliseeritud tekst**, mitte ainult mall. Kui kasutaja kasutab mail-merge
tööriista, anna **ka kohatäidetega versioon** (nt `{{eesnimi}}`,
`{{kliinik}}`, `{{loomaliik}}`), et tööriist saaks massiks kokku panna.

Hoiatus: kohatäide ilma rikastatud andmeta jätab kirja tühjaks ("Tere ,").
Kui andmed puuduvad, kirjuta neutraalne variant ilma kohatäiteta.
