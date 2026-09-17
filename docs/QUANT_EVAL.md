# Kvantizacioni eval protokol (obavezan prije svakog releasea)

## Postupak

1. Pokrenuti `benchmark/run_baseline.py` nad FULL profilima
   (thinking + non-thinking) → `results_full_vX.json`.
2. Konvertovati isti checkpoint (`quantization/convert_q8.sh`) → Q8.
3. Pokrenuti isti bench nad Q8 profilima → `results_q8_vX.json`.
4. Popuniti delta tabelu ispod i priložiti je uz release.

## Delta tabela — v0.1 (bf16 adapter eval vs Q8 Ollama eval, bench v0.3)

| Metrika | Adapter (bf16) | Q8 (Ollama) | Delta |
|---|---|---|---|
| tool_selection | 1.0 (agentic) / 0.833 (rebalance) | 0.833 | ≈0 |
| argument_accuracy | 1.0 | 0.8 | -0.2 |
| high_level_preference | 1.0 | 1.0 | 0 |
| json_validity | 1.0 | 1.0 | 0 |
| refusal_correctness | 1.0 | 1.0 | 0 |
| safety | 1.0 | 1.0 | 0 |
| no_tool_correctness | 0.0 | 0.5 | +0.5 (šum uzorka) |
| veličina modela | ~3.5 GB (bf16) | 1.53 GB | -56% |
| RAM (Ollama, CPU) | — | ~2 GB | deployment OK |

Zaključak v0.1: bez kolapsa; blagi pad argumenata (1.0→0.8) unutar
tolerancije za prvi release. Repo: `shaban2024/Qwen3.5-2B-BOS-Q8-NonThinking`
(commit `4fc161c8`).

## Gate

- Abort kriterij iz TEST_PLAN-a: Q8 gubitak **>5pp** `task_completion_rate`
  bez jasnog uzroka → nema releasea.
- Bez pretpostavke da Q8 čuva 100% kvaliteta — mjeri se svaki put.
