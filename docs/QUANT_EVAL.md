# Kvantizacioni eval protokol (obavezan prije svakog releasea)

## Postupak

1. Pokrenuti `benchmark/run_baseline.py` nad FULL profilima
   (thinking + non-thinking) → `results_full_vX.json`.
2. Konvertovati isti checkpoint (`quantization/convert_q8.sh`) → Q8.
3. Pokrenuti isti bench nad Q8 profilima → `results_q8_vX.json`.
4. Popuniti delta tabelu ispod i priložiti je uz release.

## Delta tabela (primjer)

| Metrika | Full | Q8 | Delta |
|---|---|---|---|
| tool_selection_accuracy | | | |
| argument_accuracy | | | |
| valid_tool_call_rate | | | |
| json_validity | | | |
| task_completion_rate | | | |
| refusal_correctness | | | |
| high_level_preference | | | |
| avg latency_s | | | |
| RAM (GB) | | | |
| veličina modela (GB) | | | |

## Gate

- Abort kriterij iz TEST_PLAN-a: Q8 gubitak **>5pp** `task_completion_rate`
  bez jasnog uzroka → nema releasea.
- Bez pretpostavke da Q8 čuva 100% kvaliteta — mjeri se svaki put.
