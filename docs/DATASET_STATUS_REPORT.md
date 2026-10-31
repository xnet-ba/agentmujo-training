# DATASET_STATUS_REPORT — v0.2.0

**Datum:** 2026-10-31 · **Repo:** xnet-ba/agentmujo-training (PR #3) · **Testovi:** 46/46

## Release v0.2.0

- **Ukupno:** 3.716 redova, 9 datasetova, 12 kategorija.
- bosnian-language 1.178 · safety 20 · reasoning 75 · function-calling 1.364 · agentic-tasks 729 · bosnian-knowledge 100 · coding 30 · rag-memory 50 · preference-dpo 170.
- **Gap:** agentic-evaluation (odvojen benchmark; nije train).
- Cross-dataset dedup: 45 uklonjeno (nema curenja između datasetova).
- Manifesti + SHA256: `releases/v0.2.0/`, `RELEASE.json`, `DATASET_CARD.md`.

## Izvori i licence

- `wikipedia-bs` = **approved**, CC BY-SA 4.0; intro extracts, attribution URL u metadata.
- `own` = approved; coding iz vlastitog Apache-2.0 repo koda; interni preference podaci.
- HF/OSCAR/CulturaX/OPUS/Wikimedia(generic)/BigCode/BFCL = pending; nisu korišteni bez provjere.

## GPU / LUMI

- **GPU nije korišten** za obradu; sve na Contabo CPU.
- LUMI ostaje za CPU/Slurm streaming i opravdanu sintetičku generaciju/eval/trening.

## HF

- v0.1.0: https://huggingface.co/datasets/renatoschust/agentmujo-dataset-v0.1.0
- v0.2.0: objavljuje se pod `renatoschust/agentmujo-dataset-v0.2.0`.
