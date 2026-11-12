#!/bin/bash
#SBATCH --job-name=amj-merge
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=amj-merge-%j.out
# LUMI merge: baza (pinovana revizija, HF cache) + LoRA adapter -> pune tezine.
# Upotreba: sbatch merge.sbatch <adapter-dir> <revision> <out-dir>
set -euo pipefail
ADAPTER="${1:?upotreba: sbatch merge.sbatch <adapter-dir> <revision> <out-dir>}"
REVISION="${2:?upotreba: sbatch merge.sbatch <adapter-dir> <revision> <out-dir>}"
OUTDIR="${3:?upotreba: sbatch merge.sbatch <adapter-dir> <revision> <out-dir>}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export REPO=/scratch/project_465003647/agentmujo/repo
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_HF_HUB_CACHE="$HF_HUB_CACHE"
export SINGULARITYENV_PYTHONPATH="$PYLIBS:/repo/src"
cd "$REPO"
git pull -q 2>/dev/null || echo "WARN: git pull nije uspio"
srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="$PYLIBS" python -u /repo/quantization/merge_adapter.py \
    --base Qwen/Qwen3.5-9B --revision "$REVISION" \
    --adapter "$ADAPTER" --out "$OUTDIR"
echo MERGE_DONE
