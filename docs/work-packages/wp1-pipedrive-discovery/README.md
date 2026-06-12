# wp1: Pipedrive'i alus, discovery ja orkestraator

**Omanik:** Meelis Kadaja (Chief Business Officer)
**Disaini sammud:** 1, 2, 7 ([ehitusjärjekord](../../ravimus-lead-pipeline-design.md#ehitusjärjekord))

## Missioon

Ehita süsteemi selgroog: Pipedrive'i pipeline kogu olekuhoidjana,
discovery-skriptid, mis toovad Läti vetiregistri deal'idena sisse, ja
`/tick` orkestraator, mis iga 30 minuti tagant pipeline'i edasi liigutab.
Müügiprotsessi loogika (staadiumid, voolupiirang, pingerida) on sinu
valdkond; Claude Code kirjutab koodi sinu juhtimisel.

## Tulemid

- [ ] Pipedrive'i pipeline `ravimus-latvia-vets`: 8 staadiumit ja kõik
      custom field'id vastavalt disaini tabelitele
      ([staadiumid](../../ravimus-lead-pipeline-design.md#staadiumid-üks-pipeline-ravimus-latvia-vets),
      [field'id](../../ravimus-lead-pipeline-design.md#custom-fieldid-dealil))
- [ ] `lib/`: jagatud Pipedrive'i API-loogika, mida kasutavad nii MCP
      server kui discovery-skript
- [ ] `mcp/pipedrive-mcp/`: lugemine, staadiumimuutus, field'ide uuendus,
      note lisamine; kustutamist ja masskirjutust ei avata
      ([tööriistakiht](../../ravimus-lead-pipeline-design.md#tööriistakiht--kohalikud-mcp-serverid))
- [ ] Smoke-test: test-deal'i loomine ja liigutamine läbi MCP
- [ ] `scripts/registry.py` + `scripts/discovery.py`: registri laadimine,
      e-mailiga kirjete filter, dedup `registry_id` järgi, deal'id
      staadiumis Discovered
      ([discovery](../../ravimus-lead-pipeline-design.md#discovery--deterministlik-skript-mitte-agent))
- [ ] `/tick` skill: töötlusjärjekord (triage → sales → enrichment →
      outreach), voolupiirang Contacted < 20, lukufail
      ([orkestraator](../../ravimus-lead-pipeline-design.md#orkestraator-tick))

## Sõltuvused

Kõik teised paketid testivad `pipedrive-mcp` vastu: ehita see esimesena.
`/tick` (tund 3) vajab teiste agente, seega jäta see viimaseks. Läti
vetiregistri täpne URL selgub discovery-sammus; alusta registri
otsimisest, kui Pipedrive'i seadistus ootab API-võtit.

## Valmis, kui

1. Smoke-test loob ja liigutab test-deal'i läbi MCP.
2. Discovery jooks paneb kõik e-mailiga vetid Pipedrive'i, duplikaatideta.
3. `/tick` jookseb DRY_RUN-is otsast lõpuni ja kirjutab kokkuvõtte
   `logs/`-i.
