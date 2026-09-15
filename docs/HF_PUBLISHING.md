# HF publishing workflow (v0.1 specifikacija — bez uploadanja dok gate ne prođe)
#
# Objavljeno 2026-09-15 (nalog shaban2024, gate zadovoljen za MVP datasetove):
#   - https://huggingface.co/datasets/shaban2024/agentmujo-function-calling (v0.1.0, 36 uzoraka)
#   - https://huggingface.co/datasets/shaban2024/agentmujo-agentic-terminal (v0.1.0, 15 tragova)
# Rezervisano (prazno, puni se iz releasea):
#   - https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Non-Thinking
#   - https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Q8-NonThinking
#
#   amj dataset publish --dataset agentmujo-function-calling --version 0.1.0
#   amj model publish   --experiment amj-fc-sft-v0.1
#   amj benchmark publish --run <id>
#
# Gate prije BILO KAKVOG public pusha:
#  1. model/dataset manifest popunjen (base model, revizija, licence, metodologija)
#  2. dataset: validator ACCEPT, deduplikovan, train/valid/test split bez leakagea
#  3. model: benchmarkiran (base vs tuned vs Q8), limitations dokumentovane
#  4. provjera licence (Apache-2.0 baza + Qwen uslovi) i odsustvo tajni/privatnih podataka
#  5. model card + dataset card napisani
# Autentikacija: `hf auth login` (token u credential storageu, NIKADA u gitu).
