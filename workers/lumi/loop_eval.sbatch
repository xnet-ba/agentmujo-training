#!/bin/bash
#SBATCH --job-name=amj-loopeval
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=amj-loopeval-%j.out
# LUMI scored loop eval: llama-server (CPU, Q8) + benchmark/agent_eval.py.
# Upotreba: sbatch loop_eval.sbatch <model-q8.gguf> <cases.jsonl> <out.json>
# (agent_eval podrzava URL kao model: chat_llama fn.)
set -euo pipefail
MODEL="${1:?upotreba: sbatch loop_eval.sbatch <model-q8.gguf> <cases> <out>}"
CASES="${2:?upotreba: sbatch loop_eval.sbatch <model-q8.gguf> <cases> <out>}"
OUT="${3:?upotreba: sbatch loop_eval.sbatch <model-q8.gguf> <cases> <out> [profil]}"
PROFILE="${4:-}"  # npr. ask-first -> AGENTMJO_SYSTEM_EXTRA eksperiment (loop.py)
module purge
module load Local-LAIF lumi-aif-singularity-bindings || true
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export REPO=/scratch/project_465003647/agentmujo/repo
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export SINGULARITYENV_PYTHONPATH="$PYLIBS:/repo/src"
export SINGULARITYENV_AGENTMJO_SYSTEM_EXTRA="$PROFILE"
LLAMACPP_BIN="$(dirname "$MODEL")/llama.cpp/build/bin"
cd "$REPO" && git pull -q 2>/dev/null || echo "WARN: git pull nije uspio"
"$LLAMACPP_BIN/llama-server" -m "$MODEL" --port 8899 -c 4096 \
  --reasoning off \
  --n-gpu-layers 0 -t 32 > "$(dirname "$OUT")/loopeval_server.log" 2>&1 &
SRV=$!
for i in $(seq 1 60); do
  sleep 10
  if curl -sf http://127.0.0.1:8899/health > /dev/null 2>&1; then break; fi
  if [ "$i" = "60" ]; then echo "SERVER_NIJE_DIGAO"; kill $SRV 2>/dev/null || true; exit 1; fi
done
srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="$PYLIBS:/repo/src:/repo/benchmark" python -u /repo/benchmark/agent_eval.py \
    http://127.0.0.1:8899 nonthink "$CASES" "$OUT"
RC=$?
kill $SRV 2>/dev/null || true
echo LOOPEVAL_DONE rc=$RC
exit $RC
