# Kohaletoimetatavus: open rate'i tegelik alus

Kui kiri ei jõua postkasti, on sisu ükskõik. Need praktikad on kohandatud
**ettevõtte meilboxist** saatmiseks, mitte massi-ESP jaoks.

## Autentimine (kohustuslik)

Veendu, et ettevõtte domeenil on korras:
- **SPF**
- **DKIM** (2048-bit)
- **DMARC** (liigu `none` → `quarantine` → `reject`, kui taristu lubab)

2024–2025 hakkasid Gmail, Yahoo ja Microsoft autentimata kirju tagasi
lükkama. Ilma autentimiseta open rate ≈ 0.

**Microsoft 365 (peamine kanal):** DKIM **ei ole** kohandatud domeenil
vaikimisi sees. Luba see Microsoft 365 Defenderi / admin-keskuses ja lisa
DNS-i nõutud CNAME-kirjed. SPF ja DMARC sea DNS-is.

## Saatja

- Saada **päris inimese nimega** (nt "Karmen, Nanordica"), mitte `info@` ega
  `no-reply`. Nimeline saatja on külmas e-postis suur open-rate hoob.
- Vasta-aadress olgu päris meilbox, kuhu saab vastata.

## Maht ja soojendus

- Alusta ~**10–20 kirja/päevas**, kasva aeglaselt.
- Hoia ~**40–50/päevas** lael ühe meilboxi kohta.
- **Bounce alla 2–3%**, **spam-kaebused alla 0,1%**.
- Üle selle = rämps + ettevõtte domeeni maine kahjustus.

## Listi hügieen

- Verifitseeri aadressid enne saatmist (bounce'id tapavad maine).
- Eemalda kohe bounce'id ja opt-out'id.

## Sisu

- Lühike, tekstipõhine.
- Väldi rämpssõnu (nt liigne "TASUTA", "SOODUSTUS!!!"), CAPS-i ja liigseid
  linke/pilte.
- Üks selge CTA.

## Mõõtmine

- Pärismeilbox **ei näita open rate'i** ilma jälgimistööriistata.
- Lahendus: meilboxi peal **mail-merge / cold-outreach jälgimistööriist**, mis
  saadab jada, täidab merge-väljad ja mõõdab open rate'i + klikki. Vali
  postkasti järgi:
  - **Outlook / Microsoft 365 (peamine kanal):** lemlist, Woodpecker,
    Mailshake, QuickMail, Reply.io
  - Gmail / Google Workspace: Mailmeteor, GMass, YAMM
- UTM jääb veebipoolse konversiooni jaoks (vt `funnel-framework.md`).
- NB: open rate on Apple MPP tõttu moonutatud. Vastus ja klikk on tõesemad.
