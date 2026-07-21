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
  &utm_content=<kirja-nurk>-<utm_id>
```

- `utm_content` kaks osa, sidekriipsuga: **kirja-nurk** (jada-samm /
  A/B variant, nt `esmakiri-a`) + **utm_id** (deal'i `_state.utm_id`,
  per-vet unikaalne hex — outreach-writer genereerib ja salvestab).
  Nii saab võrrelda, milline nurk päriselt müüb, JA siduda kliki
  konkreetse vetiga: saidi Velo-snipet logib kliki `clickEvents`
  kollektsiooni ning sales-detector viib `utm_id` kaudu deal'i
  Engaged'iks. Ilma `utm_id`-ta on klikk anonüümne variandistatistika.
- `utm_campaign` PEAB algama `ravimusvet-` — saidi snipet logib ainult
  selle prefiksiga kampaaniad.

## Mida mõõta

- **Mail-merge tööriist** → open rate + klikk (Outlook / Microsoft 365, peamine
  kanal: lemlist / Woodpecker / Mailshake / QuickMail; Gmail: Mailmeteor / GMass / YAMM).
- **Vastuse-määr** → tugev kaasatuse-mõõdik meilboxi-jadas.
- **Veebianalüütika** (klikk → tootelehe vaade → ost) → leiab funneli
  pudelikaela.
- **Vastus → inimene:** vastuse korral jada peatub, inimene jätkab müüki.

## ⚠️ MPP hoiatus

Apple Mail eellaadib jälgimispiksleid, nii et ~pool "avamisi" pole päris
inimene. Open rate on moonutatud. Siht **25–35% open rate on suunis**, aga
**otsus tehakse vastuse, kliki ja ostu põhjal**, mitte avamise.
