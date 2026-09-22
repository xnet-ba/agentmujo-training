# AgentMujo registar (generirano: `amj registry build`)

## Lineage adaptera

| Job | Baza/adapter | Dataset | Loss | Status |
|---|---|---|---|---|
| qwen35-ag-20260916-kaggle05 | adapter: ...n35-fc-20260916-kaggle04/outputs/adapter | agentmujo-agentic-terminal | 0.808 | done |
| qwen35-cf-20260918-kaggle09 | adapter: ...n35-jt-20260917-kaggle08/outputs/adapter | agentmujo-confirmation | 1.361 | done |
| qwen35-fc-20260915-kaggle01 | Qwen3.5-2B-bos-32768 | agentmujo-function-calling | - | done |
| qwen35-fc-20260915-kaggle02 | Qwen3.5-2B-bos-32768 | agentmujo-function-calling | - | failed |
| qwen35-fc-20260916-kaggle03 | Qwen3.5-2B-bos-32768 | agentmujo-function-calling | 0.736 | done |
| qwen35-fc-20260916-kaggle04 | Qwen3.5-2B-bos-32768 | agentmujo-function-calling | 0.735 | done |
| qwen35-jt-20260917-kaggle08 | adapter: ...n35-th-20260917-kaggle07/outputs/adapter | agentmujo-joint-01 | 0.639 | done |
| qwen35-jt10-20260920-kaggle18 | adapter: ...null | agentmujo-joint-01 | - | created |
| qwen35-jt11-20260920-kaggle19 | adapter: ...null | agentmujo-joint-01 | 1.224 | done |
| qwen35-jt12-20260921-kaggle20 | adapter: ...5-jt11-20260920-kaggle19/outputs/adapter | agentmujo-joint-01 | 0.894 | done |
| qwen35-jt13-20260921-kaggle21 | adapter: ...5-jt12-20260921-kaggle20/outputs/adapter | agentmujo-joint-01 | 0.791 | done |
| qwen35-jt14-20260921-kaggle22 | adapter: ...5-jt13-20260921-kaggle21/outputs/adapter | agentmujo-joint-01 | 0.719 | done |
| qwen35-jt15-20260921-kaggle23 | adapter: ...5-jt14-20260921-kaggle22/outputs/adapter | agentmujo-joint-01 | 0.654 | done |
| qwen35-jt16-20260921-kaggle24 | adapter: ...5-jt15-20260921-kaggle23/outputs/adapter | agentmujo-joint-01 | 0.584 | done |
| qwen35-jt17-20260921-kaggle25 | adapter: ...5-jt16-20260921-kaggle24/outputs/adapter | agentmujo-joint-01 | 0.549 | done |
| qwen35-jt18-20260921-kaggle26 | adapter: ...5-jt17-20260921-kaggle25/outputs/adapter | agentmujo-joint-01 | 0.514 | done |
| qwen35-jt19-20260922-kaggle27 | adapter: ...5-jt18-20260921-kaggle26/outputs/adapter | agentmujo-joint-01 | 0.475 | done |
| qwen35-jt2-20260918-kaggle10 | adapter: ...n35-jt-20260917-kaggle08/outputs/adapter | agentmujo-joint-01 | 0.576 | done |
| qwen35-jt20-20260922-kaggle28 | adapter: ...5-jt19-20260922-kaggle27/outputs/adapter | agentmujo-joint-01 | 0.445 | done |
| qwen35-jt3-20260918-kaggle11 | adapter: ...35-jt2-20260918-kaggle10/outputs/adapter | agentmujo-joint-01 | 0.471 | done |
| qwen35-jt4-20260918-kaggle12 | adapter: ...35-jt3-20260918-kaggle11/outputs/adapter | agentmujo-joint-01 | 0.365 | done |
| qwen35-jt5-20260918-kaggle13 | adapter: ...35-jt4-20260918-kaggle12/outputs/adapter | agentmujo-joint-01 | 0.326 | done |
| qwen35-jt6-20260919-kaggle14 | adapter: ...35-jt5-20260918-kaggle13/outputs/adapter | agentmujo-joint-01 | 0.289 | done |
| qwen35-jt7-20260919-kaggle15 | adapter: ...35-jt5-20260918-kaggle13/outputs/adapter | agentmujo-joint-01 | 0.289 | done |
| qwen35-jt8-20260919-kaggle16 | adapter: ...35-jt5-20260918-kaggle13/outputs/adapter | agentmujo-joint-01 | 0.386 | done |
| qwen35-jt9-20260920-kaggle17 | adapter: ...35-jt8-20260919-kaggle16/outputs/adapter | agentmujo-joint-01 | 0.304 | done |
| qwen35-rb-20260916-kaggle06 | adapter: ...n35-ag-20260916-kaggle05/outputs/adapter | agentmujo-rebalance-01 | 0.686 | done |
| qwen35-th-20260917-kaggle07 | adapter: ...n35-rb-20260916-kaggle06/outputs/adapter | agentmujo-thinking | 0.976 | done |

## Benchmark izvještaji

| Fajl | Profil | Ključne metrike |
|---|---|---|
| results_agentloop_jt19_nonthink.json | agentmujo-jt19-q8-nonthink-agentloop | tool=0.767 arg=1.0 safe=1.0 task=0.979 |
| results_agentloop_nonthink.json | agentmujo-q8:latest-nonthink-agentloop | tool=0.875 arg=1.0 safe=1.0 task=1.0 |
| results_agentloop_think.json | agentmujo-q8-think:latest-think-agentloop | tool=0.875 arg=1.0 safe=1.0 task=0.95 |
| results_agentmujo-q8-nonthink-v0.2.json | agentmujo-q8-nonthink-v0.2 | tool=0.833 arg=0.9 safe=1.0 task=- |
| results_agentmujo-q8-think-v0.2.json | agentmujo-q8-think-v0.2 | tool=0.833 arg=1.0 safe=0.667 task=- |
| results_agentmujo_q8_thinking.json | agentmujo-q8-think-v0.1 | tool=0.917 arg=1.0 safe=0.0 task=- |
| results_agentmujo_q8_v0.1.json | agentmujo-q8-nonthink-v0.1 | tool=0.833 arg=0.8 safe=1.0 task=- |
| results_agentmujo_q8_v03_nonthink.json | NON-THINK | tool=0.917 arg=0.9 safe=1.0 task=- |
| results_agentmujo_q8_v03_think.json | THINK | tool=0.833 arg=1.0 safe=0.667 task=- |
| results_agentmujo_q8_v04_nonthink.json | NON-THINK | tool=0.75 arg=1.0 safe=1.0 task=- |
| results_agentmujo_q8_v04_think.json | THINK | tool=0.917 arg=1.0 safe=1.0 task=- |
| results_agentmujo_q8_v05_nonthink.json | agentmujo-q8-v0.5-nonthink | tool=0.667 arg=0.7 safe=0.833 task=- |
| results_baseline_v0.1.json | ? | tool=- arg=- safe=- task=- |
| results_bosnian_probe.json | ? | tool=- arg=- safe=- task=- |
| results_bosnian_probe_v02.json | ? | tool=- arg=- safe=- task=- |
| results_deployed_q8_v04_nonthink.json | agentmujo-q8:latest-nonthink | tool=0.792 arg=0.8 safe=1.0 task=- |
| results_deployed_q8_v04_think.json | agentmujo-q8-think:latest-think | tool=0.875 arg=0.9 safe=1.0 task=- |
| results_jt13_q8_v06_nonthink.json | agentmujo-jt13-q8-nonthink | tool=0.267 arg=0.192 safe=0.714 task=- |
| results_jt16_prod_nonthink.json | agentmujo-jt16-q8-nonthink | tool=0.833 arg=0.846 safe=0.857 task=- |
| results_jt17_prod_nonthink.json | agentmujo-jt17-q8-nonthink | tool=0.8 arg=0.846 safe=0.857 task=- |
| results_jt18_prod_nonthink.json | agentmujo-jt18-q8-nonthink | tool=0.767 arg=0.769 safe=1.0 task=- |
| results_jt19_prod_nonthink.json | agentmujo-jt19-q8-nonthink | tool=0.867 arg=0.808 safe=1.0 task=- |
| results_jt19_prod_nonthink_rs06.json | agentmujo-jt19-q8-nonthink+rescored-v06 | tool=0.867 arg=0.808 safe=1.0 task=- |
| results_q8_v0.2.json | ? | tool=- arg=- safe=- task=- |
| results_q8_v0.3.json | ? | tool=- arg=- safe=- task=- |
| results_v04_prod_nonthink.json | agentmujo-q8-nonthink | tool=0.667 arg=0.731 safe=1.0 task=- |
| results_v04_q8_nonthink.json | V04 NON-THINK | tool=0.667 arg=0.9 safe=1.0 task=- |
| results_v04_q8_think.json | V04 THINK | tool=0.75 arg=0.9 safe=0.833 task=- |
| results_v05_q8_nonthink.json | V05 NON-THINK | tool=0.533 arg=0.538 safe=0.857 task=- |
| results_v05_q8_think.json | V05 THINK | tool=0.5 arg=0.577 safe=0.857 task=- |

## Hub pinovi (configs/models.yaml, datasets.yaml)

Dataset i model revizije su pinovane u configima; ovaj fajl se regenerira nakon svakog runa.
