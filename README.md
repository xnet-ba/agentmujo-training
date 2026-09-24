# AgentMujo Training Framework

[![CI](https://github.com/xnet-ba/agentmujo-training/actions/workflows/ci.yml/badge.svg)](https://github.com/xnet-ba/agentmujo-training/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Reproducibilan sistem za fine-tuning **malih bosanskojezičnih modela**
koji znaju koristiti alate, raditi višekoračne zadatke i provjeravati
rezultate — jezgra AgentMujo AI agenta.

> Status: **v0.5 live (joint-23 Q8, gate 6W-2T nad v0.4).**
> Dataseti: 2911 uzoraka (FC 1252 + AG 541 + BC 1118 + thinking 45).
> Trening pauziran nakon 30 joint runova (eval 1.067→0.873);
> Svi testovi zeleni (37/37); think-profil ostaje v0.4.

## Razumijevanje za 5 minuta

1. **Baza:** `alphaedge-ai/Qwen3.5-2B-bos-32768` (Apache-2.0, 1.77B, vokabular
   32k, nativni kontekst 262k). Bosanska adaptacija je gotova — ne trenirati
   jezik od nule dok benchmark ne pokaže potrebu.
2. **Thinking/non-thinking = JEDAN model.** `enable_thinking` zastavica chat
   templatea prebacuje režim; 4 deployment profila dijele iste težine.
3. **Alati:** `configs/tools.yaml` je Single Source of Truth (14 alata:
   `service_*`, `disk/memory/cpu`, `process_list`, `network_status`,
   `port_check`, `package_*`, `file_*`, `terminal` kao fallback). Model MORA preferirati
   high-level alat nad sirovom terminal komandom.
4. **Sigurnost:** `MODEL → TOOL → POLICY ENGINE → LINUX`. Fine-tuning nije
   zaštita; `allow / confirmation_required / deny` odlučuje izvršavanje.
5. **Linija:** baza → Function-Calling SFT → Agentic SFT → Bench →
   najbolji adapter → Q8 → 4 profila.

## Brzi start

```bash
uv pip install -e ".[dev]"   # ili: pip install -e .
amj doctor                    # provjera okruženja (bez ispisa tajni)
amj model list                # pinovane revizije baze
amj tools validate            # 10 alata iz registryja
amj dataset validate --input datasets/canonical/function_calling_v0.1.jsonl
amj dataset validate --input datasets/canonical/agentic_terminal_v0.1.jsonl
amj benchmark run --cases benchmark/cases_v0.5.jsonl
amj registry build           # lineage + eval tablice u docs/REGISTRY.md
pytest -q                     # 37 testova
```

## Struktura

- `configs/` — project, models (pinovane revizije), datasets, tools, training
- `src/agentmujo_training/` — cli (`amj`), tools, datasets, benchmark,
  context, registry, policy (Policy Engine + Executor), training/, evaluation/
- `schemas/` — dataset, tool, experiment, model JSON Scheme
- `datasets/canonical/` — 1252 function-calling + 541 agentic-terminal +
  1118 bosnian-core + 45 thinking + DPO parovi; sirovi podaci na HF Hubu
- `datasets/splits/` — zamrznuti train/valid/test + leakage_report.json
- `benchmark/` — AgentMujo-Bench (16 kategorija, 48 slučajeva v0.5) + agent_eval.py + format-probe + bosanska proba
- `quantization/` — GGUF Q8 pipeline (convert --no-mtp + block_count patch protokol)
- `workers/kaggle/` — T4 worker (SFT + DPO + smoke), notebook generator, 40 jobova
- `deployment/` — Ollama Modelfile profili (thinking/non-thinking, zajednički GGUF)
- `docs/` — PROJECT_SPEC, TEST_PLAN, HF_PUBLISHING
- `tests/` — registry, validator (+safety), benchmark

## Pravila

- Bez tajni u gitu (`hf auth login`, env/credential storage).
- GPU runovi samo uz eksplicitno odobrenje (kvota!) i pinovane revizije.
- Kvalitet > količina: GOLD/SILVER/BRONZE/REJECT, bez leakagea train/test.
- Uske alignment nastavke ne objavljivati bez joint provjere (osciliraju).

Detalji: `docs/PROJECT_SPEC.md` · Test gate: `docs/TEST_PLAN.md` ·
Sigurnost: `SECURITY.md` · Publish: `docs/HF_PUBLISHING.md`

## Objavljeno na Hugging Face Hubu

- Dataseti: function-calling (1252) · agentic-terminal (541) ·
  bosnian-core (1118) · thinking (45) · dpo-01 (140 parova) ·
  joint-01 (mixevi) · svi pod `shaban2024/agentmujo-*`
- Modeli: [Q8 v0.5](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Q8-NonThinking)
  (joint-23, gate 6W-2T; v0.4 backup) · think-profil ostaje v0.4 ·
  [Non-Thinking full v0.1](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Non-Thinking)
