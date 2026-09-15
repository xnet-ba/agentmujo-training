# AgentMujo-Bench

Benchmark je **potpuno odvojen** od training datasetova.

- `cases_v0.1.jsonl` — ZAMRZNUTO: 8 slučajeva, historijski artefakt TP-2
  nultog benchmarka (`results_baseline_v0.1.json`).
- `cases_v0.2.jsonl` — AKTUELNO: 20 slučajeva, 16 kategorija.

## Kategorije (16)

| # | Kategorija | Od | Način ocjene v0.2 |
|---|---|---|---|
| 1 | bosnian_quality | v0.1 | manual / LLM-sudija (kasnije) |
| 2 | tool_selection | v0.1 | rule-based |
| 3 | argument_accuracy | v0.1 | rule-based |
| 4 | tool_call_validity | v0.1 | rule-based |
| 5 | json_validity | v0.1 | rule-based |
| 6 | multi_step | v0.1 | rule-based (početak traga) |
| 7 | terminal_accuracy | v0.1 | rule-based |
| 8 | verification | v0.1 | rule-based |
| 9 | safety | v0.1 | rule-based |
| 10 | task_success | v0.1 | manual / e2e (kasnije) |
| 11 | refusal_correctness | v0.2 | rule-based |
| 12 | confirmation_behavior | v0.2 | rule-based |
| 13 | high_level_preference | v0.2 | rule-based |
| 14 | no_tool_correctness | v0.2 | rule-based |
| 15 | diagnosis_quality | v0.2 | **manual-only** (nema automatskog scorera) |
| 16 | ijekavica_dialect | v0.2 | heuristika (ekavski markeri) |

## Pokretanje

```bash
amj benchmark run --cases benchmark/cases_v0.2.jsonl
python3 benchmark/run_baseline.py --profiles q8-nonthink --out benchmark/results_q8_v0.2.json
```
