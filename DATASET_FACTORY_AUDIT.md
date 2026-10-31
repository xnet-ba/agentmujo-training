# DATASET_FACTORY_AUDIT.md — AgentMujo Dataset Factory

**Datum:** 2026-10-31 · **Repo:** gamai-io/agentmujo-training (fork: renatoschust-dot/agentmujo-training)
**Cilj:** proširiti postojeći framework u produkcijski Dataset Factory (ne paralelni sistem).

## 1. Baseline (stvarno stanje)

- Dataseti: 2.911 uzoraka (FC 1.252 · AG 541 · BC 1.118 · thinking 45).
- CLI `amj`: `doctor`, `model list`, `dataset validate|stats|split`, `tools validate`, `benchmark run`, `job create|status|validate`, `artifacts fetch`, `evaluate`, `registry build`, `policy check`, `train`, `experiment show`, `publish`, `model quantize`.
- Sheme: `schemas/dataset.schema.json`, `tool.schema.json`, `experiment.schema.json`, `model.schema.json`.
- Config: `configs/models.yaml`, `tools.yaml`, `datasets.yaml`, `project.yaml`.
- Dataseti/splitovi: `datasets/canonical/`, `datasets/splits/` (leakage report), `benchmark/` (AgentMujo-Bench).
- Testovi: **36/37 prolazi**; 1 stvarni bug: `registry/index.py` pretpostavlja da je `summary` dict, a jedan benchmark ima listu (`AttributeError: 'list' object has no attribute 'get'`). Popravljeno u ovom branchu.
- Radnici/kvantizacija: `workers/kaggle/`, `quantization/` (GGUF Q8, `--no-mtp`), `deployment/` (Ollama profili).

## 2. Šta se može ponovo koristiti

- Canonical JSONL šema + `datasets/validator.py` (validacija uzorka/alata).
- Deterministički split + leakage test (`datasets/splits`, `tests/test_leakage.py`).
- `configs/datasets.yaml` kao manifest/verzije; `configs/tools.yaml` kao single source of truth za alate.
- Benchmark i evaluacija (`benchmark/`, `evaluation/`).
- Registry (`registry/index.py`) i lineage; Kaggle worker i GGUF pipeline.

## 3. Šta nedostaje (gap)

1. **Source Registry** (arhitektura A) — ne postoji; sada dodat `configs/sources.yaml` + `amj dataset sources list|validate`.
2. **Ingestion** (B), **Cleaning** (D), **dedup**, **language ID** (E), **annotation** (F), **synthetic generation** (G), **build** (H), **export adapteri** (J), **compare/verify/release** — nema CLI komandi.
3. **Governance** (C): licenca/porijeklo/privatnost/dozvole po izvoru — nema evidencije.
4. **13 kategorija** iz plana: postoje samo 3 zaleđena dataseta + 8 `planned`; nema 13 zasebnih datasetova.
5. **Balancing** po modelu (2B/4B/9B/32B/35B) i model profili — nema.
6. **LUMI CPU pipeline** (streaming/ingest na Slurm CPU) — nema; GPU se ne smije trošiti na obradu podataka.
7. **v0.1.0 release** sa stvarnim brojevima (pronađeno/preuzeto/odobreno/odbačeno/sintetičko/provjereno/spremno) — nema.

## 4. Ciljna arhitektura → mapiranje

| Sloj | Postojeće | Akcija |
|---|---|---|
| A Source Registry | — | **novo** (configs/sources.yaml + sources.py + CLI) |
| B Ingestion | djelimično (HF datasets) | `amj dataset ingest` |
| C Governance | — | `DATA_GOVERNANCE.md` + polja u registryju |
| D Cleaning | validator | `amj dataset clean/deduplicate` |
| E Bosnian processing | benchmark probe | `amj dataset classify` (language/idiom) |
| F Annotation | — | `amj dataset annotate` |
| G Synthetic | — | `amj dataset synthetic generate` |
| H Building | split | `amj dataset build` |
| I Validation | validator | proširiti |
| J Export | — | Axolotl/TRL/Qwen adapteri |
| K Evaluation | benchmark | proširiti |
| L Registry | registry/index.py | proširiti na datasete |

## 5. Faze (iz maila)

1. Audit/dizajn (ovaj dokument) · 2. Dataset core (schema/registry/ingestion/validation/manifest/CLI) · 3. Bosnian data · 4. Agentic data (FC/MCP/tool/terminal/coding) · 5. Synthetic · 6. Preference/safety · 7. Export/eval · 8. Release v0.1.0.

## 6. Prvi release v0.1.0

Reprezentativni, provjereni uzorci iz prioritetnih kategorija; za svaki dataset stvarni brojevi: pronađeno, preuzeto, odobreno, odbačeno, sintetičko, provjereno, spremno za trening. Bez izmišljanja i bez popunjavanja kvota nekvalitetnim podacima.

## 7. Sljedeći korak

Phase 2 core: source registry (ovaj branch) → canonical schema/manifest → ingest/clean/dedup → CLI `amj dataset ...` → testovi. LUMI samo za CPU streaming obradu (Slurm), GPU tek za opravdanu sintetičku generaciju/eval/trening.
