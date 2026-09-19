# AgentMujo Training Framework (v0.1)

[![CI](https://github.com/xnet-ba/agentmujo-training/actions/workflows/ci.yml/badge.svg)](https://github.com/xnet-ba/agentmujo-training/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Reproducibilan sistem za fine-tuning **malih bosanskojezičnih modela**
koji znaju koristiti alate, raditi višekoračne zadatke i provjeravati
rezultate — jezgra AgentMujo AI agenta.

> Status: **framework skeleton, BEZ treninga.** Prvi milestone dokazuje da
> format, tokenizer, chat template, tool calling, evaluator, benchmark i
> training pipeline rade — tek onda se širi dataset i pali GPU.

## Razumijevanje za 5 minuta

1. **Baza:** `alphaedge-ai/Qwen3.5-2B-bos-32768` (Apache-2.0, 1.77B, vokabular
   32k, nativni kontekst 262k). Bosanska adaptacija je gotova — ne trenirati
   jezik od nule dok benchmark ne pokaže potrebu.
2. **Thinking/non-thinking = JEDAN model.** `enable_thinking` zastavica chat
   templatea prebacuje režim; 4 deployment profila dijele iste težine.
3. **Alati:** `configs/tools.yaml` je Single Source of Truth (10 alata:
   `service_*`, `disk/memory/cpu`, `process_list`, `network_status`,
   `port_check`, `terminal` kao fallback). Model MORA preferirati
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
amj benchmark run --cases benchmark/cases_v0.1.jsonl
pytest -q                     # 9 testova
```

## Struktura

- `configs/` — project, models (pinovane revizije), datasets, tools, training
- `src/agentmujo_training/` — cli (`amj`), tools, datasets, benchmark,
  context, registry, policy (Policy Engine + Executor), training/, evaluation/
- `schemas/` — dataset, tool, experiment, model JSON Scheme
- `datasets/canonical/` — MVP uzorci (12 + 5); sirovi/veliki podaci idu na HF Hub
- `benchmark/` — AgentMujo-Bench (16 kategorija, 20 slučajeva v0.2)
- `quantization/` — GGUF Q8 pipeline (convert_q8.sh + protokol)
- `workers/vast/` — stateless GPU worker spec (startup/sync TODO do GPU faze)
- `deployment/` — Ollama Modelfile profili (thinking/non-thinking, zajednički GGUF)
- `docs/` — PROJECT_SPEC, TEST_PLAN, HF_PUBLISHING
- `tests/` — registry, validator (+safety), benchmark

## Pravila

- Bez tajni u gitu (`hf auth login`, env/credential storage).
- Bez treninga dok TEST_PLAN gate ne bude zelen (`amj train` je stub u v0.1).
- Kvalitet > količina: GOLD/SILVER/BRONZE/REJECT, bez leakagea train/test.

Detalji: `docs/PROJECT_SPEC.md` · Test gate: `docs/TEST_PLAN.md` ·
Sigurnost: `SECURITY.md` · Publish: `docs/HF_PUBLISHING.md`

## Objavljeno na Hugging Face Hubu

- Dataseti: [agentmujo-function-calling](https://huggingface.co/datasets/shaban2024/agentmujo-function-calling) ·
  [agentmujo-agentic-terminal](https://huggingface.co/datasets/shaban2024/agentmujo-agentic-terminal)
- Rezervisani model repoi (pune se iz releasea):
  [Non-Thinking](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Non-Thinking) ·
  [Q8-NonThinking](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Q8-NonThinking)
