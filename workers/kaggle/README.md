# Kaggle worker — ephemeral free-GPU trening (v0.1)

Oracle = control plane / storage / orchestration.
Kaggle = zamjenjivi GPU worker (30 h/sedmično, sesija max 12 h, T4 x2 cilj;
P100 ugašen 2026-09-15). Hub = registry datasetova/modela/artefakata.

## Životni ciklus joba

1. Oracle: `amj job create --config configs/training/kaggle_dev.yaml`
   → `training/jobs/<job_id>/{config.yaml,metadata.json,README.md}`
2. Operator (ili API): notebook `training/notebooks/qwen35_2b_training.ipynb`
   na Kaggle GPU sesiji učita job spec (ručno ili `kaggle kernels push`).
3. Worker: `workers/kaggle/job_run.py --job-dir ...` — dataset sa Huba,
   baza `alphaedge-ai/Qwen3.5-2B-bos-32768` direktno sa Huba, LoRA SFT,
   eval → `metrics.json`, adapter → Hub (private repo) + manifest.
4. Oracle: `amj artifacts fetch` — manifest, metrike i logovi nazad;
   `status.json` je izvor istine o jobu.
5. Prekid sesije = ništa strašno: `resume_from_checkpoint` iz zadnjeg
   validnog checkpointa (vidi `docs/KAGGLE_WORKER.md`).

## Auth (nikada u gitu)

- Kaggle: `~/.kaggle/kaggle.json` (600) ili `KAGGLE_USERNAME`/`KAGGLE_KEY`.
- Hugging Face: `hf auth login` na workeru ili `HF_TOKEN` iz Kaggle Secrets.
- `amj doctor` provjerava oba mehanizma bez ispisa tajni.
