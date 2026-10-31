# DATASET_STATUS_REPORT — v0.1.0

**Datum:** 2026-10-31 · **Repo:** xnet-ba/agentmujo-training (PR #2) · **Commit:** 70368ed

## Release v0.1.0

- **Ukupno:** 3.536 red
- bosnian-language 1.178 · function-calling 1.389 · agentic-tasks 749 · preference-dpo 170 · reasoning 50 · safety 0 (20/20 bili duplikati; kategorija je gap) · **45 preklapanja uklonjeno**
- Kategorije: agentic-tasks, bosnian-language, function-calling, instructions, linux-terminal, preference-dpo, reasoning, safety, tool-use-mcp
- **Gapovi:** knowledge, coding, rag-memory, safety; agentic-evaluation = odvojen benchmark (nije train)
- Manifesti + SHA256: `releases/v0.1.0/`, `RELEASE.json`, `DATASET_CARD.md`

## Testovi

- **45/45** (`pytest -q`)
- Popravljen `registry/index.py` (summary lista).

## Izvori

- `own` = approved (interne baze).
- HF, OSCAR, CulturaX, OPUS, Wikimedia, BigCode, BFCL = **pending** (provjera licence/dozvole prije ingestije).
- Nijedan pending izvor nije korišten za v0.1.0.

## LUMI / GPU

- **GPU nije korišten** za obradu podataka.
- Sljedeće: CPU/Slurm za streaming ingest i dedup; GPU samo za opravdanu sintetičku generaciju/eval/trening.

## Sljedeće

1. Knowledge/coding/rag izvori uz licence → v0.2.0.
2. 5-agentni pregled kvaliteta i gapova.
3. HF adapter (streaming) + governance evidencija.
