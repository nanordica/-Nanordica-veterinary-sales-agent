---
name: lv-vet-email-funnel
description: Use when composing cold email outreach for Ravimus / RavimusVET to Latvian veterinarians — wound-dressing sales sequences, per-contact personalization by animal species, deliverability from a company mailbox, funnel and A/B tracking. Produces Latvian-language emails that drive to the product page. Pairs with the email-marketing-bible skill for general email-marketing depth.
---

# RavimusVET — külm e-maili funnel Läti veterinaaridele

See skill aitab koostada külma e-maili kampaaniaid, mis suunavad Läti
loomaarstid RavimusVET haavasidet veebilehelt ostma. Saatmine käib kasutaja
ettevõtte meilboxist üks-ühele (mail-merge jälgimistööriistaga). Skill ei
saada kirju; ta annab teadmised, jada-loogika ja valmis personaliseeritud
teksti.

Üldise e-maili turunduse sügavuse jaoks toetu kõrvalskillile
`email-marketing-bible`. See skill on kitsas: Ravimus + Läti vetiturg + külm.

## Konekst (alati arvesta)

- **Bränd:** Ravimus (tootja Nanordica Medical)
- **Toode:** RavimusVET — steriilne haavaside (vt `references/product-ravimus-vet.md`)
- **Sihtgrupp:** Läti veterinaarkliinikud ja loomaarstid
- **Keel:** läti (emakeelne ülevaatus enne saatmist, vt `references/latvia-market.md`)
- **CTA sihtleht:** https://www.nanordica.com/ravimus (ingliskeelne)
- **Eesmärk:** ost veebilehel; külmas jadas enne vastus/klikk, siis ost
- **Kanal:** ettevõtte meilbox + mail-merge jälgimistööriist
- **List:** külm prospekteerimine; kasutaja kinnitanud õigusliku aluse

## Töövoog

Kui kasutaja palub koostada kirja või jada-sammu, järgi seda:

```
0. Taristu-kontroll: meilbox autenditud (SPF/DKIM/DMARC), maht väike,
   list verifitseeritud            → references/deliverability.md
1. Sisend: kontakti e-post + kaasatuse staatus + mitu kirja juba saadetud
2. Rikasta: nimi, kliinik, konkreetne loomaliik + värske teadusartikkel
                                    → references/contact-enrichment.md
3. Segment: vastas / klikkis / avas / kontakteerimata
                                    → references/personalization.md
4. Personaliseeri: segment + loomaliik → kohandatud kiri
5. Jada-samm: vali nurk + ooteaeg saadetud kirjade arvu järgi
   Jätka kuni vastus / opt-out / bounce → references/email-templates-lv.md
6. Värske haak: iga kiri toob uut infot (artikkel / pakkumine / sooduskood)
7. Pealkiri + eelvaade              → references/email-templates-lv.md
8. UTM: märgista CTA-link           → references/funnel-framework.md
9. A/B: planeeri test               → references/ab-testing.md
```

## Raudreeglid

- **Ära mõtle välja** kontakti andmeid ega teadusviiteid. Leidmata andmed →
  märgi "rikastamata" ja kasuta käitumispõhist segmenti.
- **Iga kiri toob uut infot.** Kui uut haaki pole, ära saada.
- **Üks CTA kirja kohta.** Avarida = personaalne tähelepanek, mitte toode.
- **Vastus (ka "ei") → jada peatub**, inimene jätkab müüki.
- **Opt-out / bounce → eemalda kohe** jadast ja listist.
- **Meditsiiniseadme väited peavad olema tõendatud** (vt product-fail).
- **Läti tekst vajab emakeelset ülevaatust** enne saatmist.

## Viitefailid

| Fail | Sisu |
|------|------|
| `references/product-ravimus-vet.md` | Toote faktid + müügiargumendid |
| `references/deliverability.md` | Autentimine, maht, listi hügieen, mõõtmine |
| `references/cold-outreach.md` | Külma jada loogika, saatja, vastuse käsitlus |
| `references/contact-enrichment.md` | E-postist arsti leidmine + artikli-rikastamine |
| `references/personalization.md` | Segment + loomaliigi-põhine personaliseerimine |
| `references/funnel-framework.md` | Funneli etapid, UTM, mõõdikud, MPP hoiatus |
| `references/ab-testing.md` | Mida testida, väikese listi tegelikkus |
| `references/latvia-market.md` | Läti toon, GDPR/ePrivacy, reklaaminõuded |
| `references/email-templates-lv.md` | Läti jada-nurgad, ooteajad, pealkirjad |
