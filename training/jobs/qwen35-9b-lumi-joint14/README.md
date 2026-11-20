# Job qwen35-9b-lumi-joint14 (SPEC — ceka dataset + GPU odobrenje)

Recept (nakon joint08 + rewrite freeze, joint09-13 REJECT):
- Baza: joint08 adapter (ne gold06, ne joint12/13).
- Mix v48: v0.41 (1850: FC 793 + AG 557 + safety 300 + BC 200)
  + ~200 confirmation (ask-first/confirm tokovi iz confirmation_v0.4,
  dedup vs v0.41, bez HL/prose-first uzoraka)
  + ~100 safety confirmation-edge (v06 failovi: refusal/confirmation granica).
  Cilj ~2150 redova. HL/prose-first se NE dodaje (rewrite to rjesava).
- Hiperparametri: lr 2e-5, r16, 1 epoha (stabilno za joint11-13).
- Gate: v0.6 single-shot (tool/conf/safety) + LOOP (tool/HL/task).
  Uspjeh = conf i safety gore BEZ pada tool ispod 0.853.

Koraci (tek uz eksplicitno GPU odobrenje):
1. `amj job validate qwen35-9b-lumi-joint14` (nakon builda v48 + leakage check)
2. Notebook na LUMI GPU: `training/notebooks/qwen35_2b_training.ipynb`
3. Merge + GGUF + bench (loop SYSTEM + v0.6 gate)

Status 2026-11-20: v48 IZGRADJEN lokalno (`scripts/build_joint14_9b.py`,
seed 47): 2150 redova (baza v0.41 1850 + conf-tool 200 + safety 100:
tool-poison 50 + multiturn-escalation 50), `amj dataset validate` cist
(GOLD 1923, SILVER 227, 0 gresaka), bez bench-overlapa, bez duplikata.
Preostalo prije GPU-a: kopirati v48 na
/scratch/project_465003647/agentmujo/joint_9b_v48.jsonl + pin dataset
revizije.
