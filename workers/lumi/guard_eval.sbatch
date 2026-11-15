#!/bin/bash
#SBATCH --job-name=amj-guardeval
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=amj-guardeval-%j.out
# Guard eval: llama-server (CPU, Q8) + loop.run end-to-end.
# Upotreba: sbatch guard_eval.sbatch <model-q8.gguf> <out.json>
set -euo pipefail
MODEL="${1:?upotreba: sbatch guard_eval.sbatch <model-q8.gguf> <out.json>}"
OUT="${2:?upotreba: sbatch guard_eval.sbatch <model-q8.gguf> <out.json>}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings || true
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
LLAMACPP_BIN="$(dirname "$MODEL")/llama.cpp/build/bin"
REPO=/scratch/project_465003647/agentmujo/repo
cd "$REPO" && git pull -q 2>/dev/null || echo "WARN: git pull nije uspio"
"$LLAMACPP_BIN/llama-server" -m "$MODEL" --port 8897 -c 4096 \
  --reasoning off \
  --n-gpu-layers 0 -t 16 > "$(dirname "$OUT")/guardeval_server.log" 2>&1 &
SRV=$!
for i in $(seq 1 60); do
  sleep 10
  if curl -sf http://127.0.0.1:8897/health > /dev/null 2>&1; then break; fi
  if [ "$i" = "60" ]; then echo "SERVER_NIJE_DIGAO"; kill $SRV 2>/dev/null || true; exit 1; fi
done
export ENDPOINT=http://127.0.0.1:8897
srun singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="$PYLIBS" ENDPOINT="$ENDPOINT" python -u /repo/workers/lumi/guard_eval.py > "$OUT" 2>&1 || true
# izvuci zadnju liniju sa skorom
tail -n 3 "$OUT"
RC=0
kill $SRV 2>/dev/null || true
echo GUARDEVAL_DONE rc=$RC
exit $RC
