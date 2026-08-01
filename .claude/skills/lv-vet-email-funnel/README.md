# Kirjade loogika — RavimusVET lehter (inimesele loetav)

See fail kirjeldab **mis kiri millal välja läheb ja mis reeglid kehtivad**.
Agendile mõeldud juhis on `SKILL.md`; üksikasjad viitefailides
(`references/`). Voo-graaf ja Pipedrive'i ahel:
[docs/email-lehter-v2.md](../../../docs/email-lehter-v2.md).

Seis: v3, 2026-08-01. Avatud tööd: issue #11 (kirjade sisu) ja #12 (QA-augud).

---

## Põhimõtted

1. **Inimene kinnitab enne esimest saatmist.** Kirjad genereeritakse kõigile
   saajatele korraga (G1), inimene vaatab üle ja kinnitab (H1). Alles siis
   saadab süsteem edasi automaatselt. Kinnitamata kirju ei saadeta kunagi.
2. **Iga kiri toob uut infot.** Kordus ilma uue haagita jääb saatmata.
3. **Üks CTA kirja kohta.**
4. **Toon:** K3 ja K8 on tagasihoidlikud, mitte müügikirjad.
5. **Kõik lingid kannavad UTM-i** (vt allpool) — ilma selleta on klikk
   anonüümne ja deal ei liigu.
6. **Meditsiiniväited ainult tõendatud kujul** (`references/product-ravimus-vet.md`).
7. **Läti keel läbib QA** (`references/latvian-qa.md`) enne saatmist.

---

## Kirjad

| ID | Kiri | Käivitab | Toon / eesmärk |
|---|---|---|---|
| **K1** | Esmakiri: akadeemia + panustamisvõimalus + tasuta näidis | H1 kinnitatud | tutvustav |
| **K2** | Järelkiri 1: osalemiskutse + näidisvideo + kutse kõnele | vaikus +7 p | väärtust lisav |
| **K3** | Järelkiri 2: **"ehk ei ole õige inimene"** | vaikus +14 p (K1-st) | **tagasihoidlik** |
| **K4** | Näidise-soovi detailide täpsustus (2 varianti, vt allpool) | näidisesoov | asjalik |
| **K5** | Saatmisteade kontorile (Verale), silt + jälgimisnumber | Omniva silt loodud | sisemine, mallipõhine |
| **K6** | Tagasiside-küsimus | näidis kohal +1 p | huvitatud |
| **K7** | Tagasiside meeldetuletus + **akadeemia vorm** | vaikus +7 p | abistav |
| **K8** | Tagasiside-breakup + **ühekordne sooduskood** | vaikus +14 p | tagasihoidlik |
| **K9** | Sooduskood (kui K8-s pole veel antud) | tagasiside käes | tänulik |
| **K10** | Tänukiri | ost tuvastatud | soe |

### K3 — "ehk ei ole õige inimene"

Eeldus: kolm kirja vaikust tähendab sageli, et kirjutasime **valele
inimesele**, mitte et toode ei sobi. Seepärast K3:

- ütleb ausalt, et rohkem me ei kirjuta;
- **julgustab kirja edasi saatma** kolleegile, kes haavaraviga tegeleb —
  kolleeg saab soovi korral **tasuta näidise**;
- **EI sisalda sooduskoodi.** Kood muudaks tagasihoidliku kirja
  müügikirjaks ja kõlaks võltsilt. Sooduskood tuleb alles K8/K9-s.

### K4 — kaks varianti

Mõlemad lõpevad samas kohas: Omniva silt, mille juures on kirjas **mida
saata** (vaikimisi `1 Ravimus haavaside`).

- **K4a — sisemine soov.** Nanordica töötaja (nt Vera) kirjutab
  ravimus@-le. Töötleb `mcp/scripts/omniva_mail_dispatch.py`: mudel
  klassifitseerib + korjab saaja andmed, kood valideerib ja registreerib.
- **K4b — vet kirjutab ise.** K1/K2/K3 saaja vastab ravimus@-le, et soovib
  näidist. Täpsustuskäik on **täpselt sama** nagu sisemise soovi puhul:
  puudu olevad andmed (nimi, telefon, pakiautomaat) küsitakse vastusena
  samasse lõime, kuni komplekt on täis. Erinevus: saaja on väline vet, seega
  vastuskirja toon on kliendile suunatud, mitte kontorisisene.

### K7 — akadeemia vorm

Tagasiside jaoks tuleb Wixi leht **"Haavaravi akadeemia vorm"**:

- video ja/või fotode üleslaadimine (enne/pärast, sidemevahetus);
- **selgituse lahter**: haigusjuhu kirjeldus (loom, haava tüüp, kestus,
  tulemus);
- vormi link kannab UTM-i, et vastus seostuks deal'iga.

### K8 / K9 — sooduskood täpselt üks kord

| Olukord | K8 sisu |
|---|---|
| K3 **ei ole** saanud (jõudis näidiseni enne breakup'i) | K3 "ehk ei ole õige inimene" sõnum + ühekordne sooduskood |
| K3 **on** saanud | **varuvariant** — sama koodipakkumine, aga uue sõnastusega, et K3 teksti mitte korrata |

Meelise sõnastuse põhi (K8, LV mustand tuleb QA-st läbi lasta):

> Lisan ka ühekordse sooduskoodi {{sooduskood}}. Kasutage seda ise
> RavimusVET tellimuseks või andke edasi kolleegile, kellel seda rohkem
> vaja läheb:

**K9** annab koodi siis, kui K8-s seda veel ei antud (st tagasiside tuli
enne breakup'i). Kood väljastatakse **maksimaalselt üks kord kontakti
kohta** — kas K8-s või K9-s, mitte mõlemas.

---

## Sooduskood

| Omadus | Väärtus |
|---|---|
| Soodustus | **25%** |
| Kasutuskordi | **1** (ühekordne) |
| Tooteid | **1 tk** |
| Kehtivus | **tähtajaline** (vaikimisi 30 päeva väljastamisest) |
| Väljastaja | `wix_create_coupon`, kood deal'i `_state.discount_code` |

**Ostu tagajärg:** kui sooduskoodiga ost registreeritakse, liigub deal
Pipedrive'is K3/K9 rajalt otse **S7 = Won**. Ostu tuvastab `sales-detector`
koodi kaudu.

---

## UTM — kohustuslik igal lingil

```
?utm_source=mailbox&utm_medium=email
&utm_campaign=ravimusvet-<kampaania>      ← PEAB algama "ravimusvet-"
&utm_content=<kirja-id>-<utm_id>          ← nt k2-akadeemia-<utm_id>
```

`utm_id` on deal'i `_state.utm_id`; ilma selleta jääb klikk anonüümseks ja
`sales-detector` ei saa deal'i Engaged'iks liigutada. Kehtib **kõigile**
linkidele: akadeemia leht, näidisevideo, K7 vorm, sooduskoodi pood.
Vt `references/funnel-framework.md`.

---

## Enne saatmist (checklist)

- [ ] G1 genereerinud kirjad kõigile saajatele
- [ ] H1: inimene on kirjad üle vaadanud ja kinnitanud
- [ ] Läti QA tehtud (`references/latvian-qa.md`)
- [ ] Väited tõendatud kujul (`references/product-ravimus-vet.md`)
- [ ] Kõik lingid UTM-iga, `utm_id` deal'ist
- [ ] Opt-out rida igas kirjas
- [ ] Sooduskood ainult K8 **või** K9, mitte mõlemas
