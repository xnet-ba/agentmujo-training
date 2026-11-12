#!/bin/bash
#SBATCH --job-name=amj-bench
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=amj-bench-%j.out
# LUMI bench: llama-server (CPU, Q8) + benchmark/llama_bench.py.
# Upotreba: sbatch bench.sbatch <model-q8.gguf> <cases.jsonl> <out.json>
set -euo pipefail
MODEL="${1:?upotreba: sbatch bench.sbatch <model-q8.gguf> <cases> <out>}"
CASES="${2:?upotreba: sbatch bench.sbatch <model-q8.gguf> <cases> <out>}"
OUT="${3:?upotreba: sbatch bench.sbatch <model-q8.gguf> <cases> <out>}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings || true
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export REPO=/scratch/project_465003647/agentmujo/repo
LLAMACPP_BIN="$(dirname "$MODEL")/llama.cpp/build/bin"
cd "$REPO" && git pull -q 2>/dev/null || echo "WARN: git pull nije uspio"
"$LLAMACPP_BIN/llama-server" -m "$MODEL" --port 8899 -c 4096 \
  --reasoning off \
  --n-gpu-layers 0 -t 32 > "$(dirname "$OUT")/bench_server.log" 2>&1 &
SRV=$!
for i in $(seq 1 60); do
  sleep 10
  if curl -sf http://127.0.0.1:8899/health > /dev/null 2>&1; then break; fi
  if [ "$i" = "60" ]; then echo "SERVER_NIJE_DIGAO"; kill $SRV 2>/dev/null || true; exit 1; fi
done
srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="/repo/src:/repo/benchmark" python -u /repo/benchmark/llama_bench.py \
    http://127.0.0.1:8899 nonthink "$CASES" "$OUT"
RC=$?
kill $SRV 2>/dev/null || true
echo BENCH_DONE rc=$RC
exit $RC
