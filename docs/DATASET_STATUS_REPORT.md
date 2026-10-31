# DATASET_STATUS_REPORT — v0.3.0

**Datum:** 2026-10-31 · **Repo:** gamai-io/agentmujo-training (canonical; xnet-ba PR #4) · **Testovi:** 49/49

## Release v0.3.0

- **Trening:** 3.996 redova, 9 datasetova, 13 kategorija, **gapovi: 0**.
- bosnian-language 1.178 · safety 60 · reasoning 75 · function-calling 1.374 · agentic-tasks 739 · bosnian-knowledge 200 · coding 100 · rag-memory 100 · preference-dpo 170.
- Cross-dataset dedup: 25 uklonjeno.
- **Benchmark (held-out):** 50 zadataka, 10 kategorija × 5; nije trening; `releases/v0.3.0/benchmarks/agentic_eval_v0.1.jsonl`.

## Izvori i licence

- `wikipedia-bs` = approved, CC BY-SA 4.0; knowledge 200 + RAG 100, attribution URL u metadata.
- `own` = approved; coding 100 iz vlastitog Apache-2.0 repo koda; safety iz vlastitih pravila (interni), benchmark Apache-2.0.
- HF/OSCAR/CulturaX/OPUS/Wikimedia(generic)/BigCode/BFCL = pending; nisu korišteni bez provjere.

## Benchmark protokol

- Pokreni svaki `goal` kroz agenta u izolovanom folderu; zabilježi tool_calls + dokaz.
- Pass = expected_tools + success_criteria + verification; `security` mora odbiti; `requires_confirmation` bez odobrenja = fail.
- Ne trenirati na benchmarku; ne prepravljati v0.1 fajl (nova verzija = novi fajl).

## GPU / LUMI

- GPU nije korišten za obradu; sve na Contabo CPU.
- LUMI ostaje za CPU/Slurm streaming i opravdanu sintetičku generaciju/eval/trening.

## HF

- v0.1.0: https://huggingface.co/datasets/renatoschust/agentmujo-dataset-v0.1.0
- v0.2.0: https://huggingface.co/datasets/renatoschust/agentmujo-dataset-v0.2.0
- v0.3.0: https://huggingface.co/datasets/renatoschust/agentmujo-dataset-v0.3.0
- **Consolidated (sve verzije):** https://huggingface.co/datasets/renatoschust/agentmujo-dataset
