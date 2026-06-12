# Funnel ja mõõtmine

## Funneli etapid

```
Saadetud → Kohale toimetatud → (Avatud) → Vastus / Klikk → Tootelehe vaade → Ost
```

`(Avatud)` on sulgudes, sest meilboxist on see kõige ebakindlam mõõdik
(vt MPP hoiatus allpool).

## UTM-märgistus (kohustuslik igal CTA-lingil)

Märgista tootelehe link, et veebianalüütikas näeks, milline kiri müügi tõi ja
mis etapil lehtrist välja kukutakse:

```
https://www.nanordica.com/ravimus
  ?utm_source=mailbox
  &utm_medium=email
  &utm_campaign=ravimusvet-cold-lv
  &utm_content=<kirja-nurk-või-AB-variant>
```

- `utm_content` eristab jada-sammu ja A/B varianti, nii saab võrrelda,
  milline nurk päriselt müüb.

## Mida mõõta

- **Mail-merge tööriist** → open rate + klikk (Gmail: Mailmeteor / GMass / YAMM;
  Outlook / Microsoft 365: Woodpecker / lemlist / Mailshake / QuickMail).
- **Vastuse-määr** → tugev kaasatuse-mõõdik meilboxi-jadas.
- **Veebianalüütika** (klikk → tootelehe vaade → ost) → leiab funneli
  pudelikaela.
- **Vastus → inimene:** vastuse korral jada peatub, inimene jätkab müüki.

## ⚠️ MPP hoiatus

Apple Mail eellaadib jälgimispiksleid, nii et ~pool "avamisi" pole päris
inimene. Open rate on moonutatud. Siht **25–35% open rate on suunis**, aga
**otsus tehakse vastuse, kliki ja ostu põhjal**, mitte avamise.
