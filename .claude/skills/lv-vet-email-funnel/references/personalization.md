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
- **avarida = kõige konkreetsem tõde** kontaktist,
- **konkreetse loomaliigi näide** kontakti eriala järgi.

### Avarida — mida kitsam, seda parem

Enamik kontakte on väikeloomakliinikud, seega üldine "töötate kasside ja
koertega" **ei ole personaalne**. Liigu pingerea järgi alt üles, kasuta kõige
konkreetsemat leitud detaili:

| Eelistus | Avarea haak (näide) |
|----------|---------------------|
| 1. Tootega seotud teenus | "Nägin, et teie kliinik pakub kirurgiat ja operatsioonijärgset haavaravi" |
| 2. Konkreetne fookus / eriala | "Nägin, et tegelete palju dermatoloogia ja krooniliste haavadega" |
| 3. Nimeline detail / asukoht | "Nägin, et juhite [kliinik] Riias" |
| 4. Loomaliik (tagavara) | "Nägin, et tegelete peamiselt väikeloomadega" |

Vali kõrgeim, mille kohta on **päris, kontrollitud** info. Ära mõtle välja —
kui ainult liik on teada, kasuta tagavara, aga väldi tühja üldistust.

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
