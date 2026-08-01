---
name: lv-vet-email-funnel
description: Use when composing cold email outreach for Ravimus / RavimusVET to Latvian veterinarians: wound-dressing sales sequences, per-contact personalization by animal species, deliverability from a company mailbox, funnel and A/B tracking. Produces Latvian-language emails that drive to the product page. Pairs with the email-marketing-bible skill for general email-marketing depth.
---

# RavimusVET külm e-maili funnel Läti veterinaaridele

See skill aitab koostada külma e-maili kampaaniaid, mis suunavad Läti
loomaarstid RavimusVET haavasidet veebilehelt ostma. Saatmine käib kasutaja
ettevõtte meilboxist üks-ühele (mail-merge jälgimistööriistaga). Skill ei
saada kirju; ta annab teadmised, jada-loogika ja valmis personaliseeritud
teksti.

Üldise e-maili turunduse sügavuse jaoks toetu kõrvalskillile
`email-marketing-bible`. See skill on kitsas: Ravimus + Läti vetiturg + külm.

## Konekst (alati arvesta)

- **Bränd:** Ravimus (tootja Nanordica Medical)
- **Toode:** RavimusVET, steriilne haavaside (vt `references/product-ravimus-vet.md`)
- **Sihtgrupp:** Läti veterinaarkliinikud ja loomaarstid
- **Keel:** läti. Tiimis pole natiivkõnelejat → **automaatne QA**, vt `references/latvian-qa.md`
- **CTA sihtleht:** https://www.nanordica.com/ravimus (ingliskeelne)
- **Eesmärk:** ost veebilehel; külmas jadas enne vastus/klikk, siis ost
- **Kanal:** ettevõtte **Outlook / Microsoft 365** meilbox + mail-merge tööriist (lemlist / Woodpecker vms)
- **List:** külm prospekteerimine; kasutaja kinnitanud õigusliku aluse

## Liides teistele agentidele

Seda skilli kutsuvad ka teised agendid (kui on kirjutamise aeg). Orkestraator
võib kutsuda otse nime järgi (`lv-vet-email-funnel`) või jätta mudeli enda
otsustada `description` põhjal.

### Sisend (mida kutsuv agent annab)

| Väli | Kohustuslik | Näide |
|------|-------------|-------|
| Kontakti e-post | jah | `anna@kakuklinika.lv` |
| Kaasatuse staatus | jah | vastas / klikkis / avas / kontakteerimata |
| Mitu kirja juba saadetud | jah | `0` (esimene), `3` jne |
| Eelmiste kirjade nurgad | kui >0 | "tutvustus, teadusartikkel" (et mitte korrata) |
| Juba teadaolevad andmed | ei | nimi, kliinik, loomaliik (säästab rikastamist) |

### Väljund (mida skill tagastab)

- Pealkiri + eelvaate-tekst
- Kirja tekst (läti, QA läbinud)
- Kohatäidetega versioon mail-merge tööriista jaoks
- UTM-märgistatud CTA-link
- Soovitatud ooteaeg järgmise kirjani (jada-tabeli järgi)
- QA staatus: `läbinud` või loend kahtlastest väidetest
- **Stopp-signaal**, kui kontakt vastas / opt-out / bounce (jada peatub)

### Raja-juhud kutsuvale agendile

- Kontakti ei leia rikastamisel → väljasta "rikastamata" + käitumispõhine kiri.
- Uut haaki ei leia → **ära väljasta kirja**, anna signaal "haaki pole".
- Staatus = vastas/opt-out/bounce → **ära genereeri**, anna stopp-signaal.

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
10. Läti QA: korrektuur + tagasitõlge + väite-kontroll (KOHUSTUSLIK enne
   valmis-märkimist)                → references/latvian-qa.md
```

## Kinnitusvärav (G1 → H1, v3)

Esimene saatmine EI toimu ilma inimese kinnituseta:
1. **G1** — genereeri kirjad KÕIGILE saajatele korraga (sh läti QA).
2. **H1** — anna komplekt inimesele üle vaatamiseks; oota selget kinnitust.
3. Kinnituse järel jätkub jada automaatselt (K2, K3, … taimerite järgi).
Kinnitamata kirju ei saadeta kunagi; paranduse korral genereeri uuesti.

## Sooduskood (v3)

25% · **ühekordne** · **1 toode** · tähtajaline (vaikimisi 30 p) ·
`wix_create_coupon` → deal'i `_state.discount_code`.
Väljastatakse **maksimaalselt üks kord kontakti kohta**: kas K8-s VÕI K9-s.
K3 on teadlikult **koodita** — tagasihoidlik toon, mitte müügikiri.
Sooduskoodiga ost → `sales-detector` → **S7 Won**.

## Raudreeglid

- **Ära mõtle välja** kontakti andmeid ega teadusviiteid. Leidmata andmed →
  märgi "rikastamata" ja kasuta käitumispõhist segmenti.
- **Iga kiri toob uut infot.** Kui uut haaki pole, ära saada.
- **Üks CTA kirja kohta.** Avarida = personaalne tähelepanek, mitte toode.
- **Vastus (ka "ei") → jada peatub**, inimene jätkab müüki.
- **Opt-out / bounce → eemalda kohe** jadast ja listist.
- **Meditsiiniseadme väited peavad olema tõendatud** (vt product-fail).
- **Iga läti kiri läbib automaatse QA** (`latvian-qa.md`) enne valmis-märkimist:
  korrektuur + tagasitõlge + väite-kontroll. Natiivkõnelejat tiimis pole.
- **Kogu genereeritud kirjakoopia järgib `stop-slop` skilli:** ei mõttekriipse,
  ei täitesõnu, aktiivne tegumood, konkreetne sõnastus. stop-slop kehtib
  alati ja käib selle skilliga koos.

## Viitefailid

Inimloetav ülevaade kirjade loogikast: **`README.md`** (samas kaustas).

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
| `references/latvian-qa.md` | Automaatne läti keele kvaliteedikontroll |
| `references/email-templates-lv.md` | Läti jada-nurgad, ooteajad, pealkirjad |
