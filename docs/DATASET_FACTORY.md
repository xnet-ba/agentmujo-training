# AgentMujo Dataset Factory

**Cilj:** produkcijski, ponovljiv i provjerljiv pipeline za prikupljanje, čišćenje, validaciju, verzioniranje i export datasetova za AgentMujo modele (2B/4B/9B/32B/35B). Bosanski, latinica, ijekavica. Ne pravi demo JSONL i ne izmišlja podatke.

## Arhitektura

| Sloj | Status | Gdje |
|---|---|---|
| A Source Registry | v0 | `configs/sources.yaml`, `datasets/sources.py`, `amj dataset sources list\|validate\|scan` |
| B Ingestion | v0 | `amj dataset ingest` (lokalni fajl; HF adapter slijedi) |
| C Governance | v0 | `DATA_GOVERNANCE.md` (slijedi), status/licenca po izvoru |
| D Cleaning | v0 | `amj dataset clean`, `deduplicate` |
| E Bosnian processing | djelimično | `docs/BOSNIAN_PROBE.md`, validator (latinica/ijekavica) |
| F Annotation | plan | metadata quality_tier |
| G Synthetic | plan | AITTA/LUMI, uz verifikaciju |
| H Building | v0 | `amj dataset build` + `manifest.json` |
| I Validation | v0 | `datasets/validator.py`, `amj dataset validate` |
| J Export | v0 | `amj dataset export --format openai\|canonical\|qwen` |
| K Evaluation | postojeće | `benchmark/`, odvojeno od treninga |
| L Registry | v0 | `configs/datasets.yaml`, `registry/index.py`, `releases/<ver>/RELEASE.json` |

## CLI

```bash
amj dataset sources list
amj dataset sources validate
amj dataset sources scan
amj dataset ingest --source own --input X.jsonl --output Y.jsonl --limit 100
amj dataset clean --input X --output Y
amj dataset dedup --input X --output Y
amj dataset build --input X --name agentmujo-x --version 0.1.0 --out-dir builds/x
amj dataset export --input X --output Y --format qwen
amj dataset release --version 0.1.0 --out-dir releases/v0.1.0
```

## Pravila

- Bez licence/dozvole nema ingestije; `pending` izvor nije `approved`.
- Bez LUMI GPU za običnu obradu podataka; CPU/streaming i Slurm CPU.
- Bez HF objave bez izričite dozvole.
- Svaki release nosi stvarne brojeve i gapove; nema lažnih kvota.
