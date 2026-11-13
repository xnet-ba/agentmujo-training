#!/bin/bash
#SBATCH --job-name=amj-probe
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=amj-probe-%j.out
# LUMI proba adaptera na GPU: format + ask-first + bosnian.
# Upotreba: sbatch probe.sbatch <adapter-dir> <out.json>
set -euo pipefail
ADAPTER="${1:?upotreba: sbatch probe.sbatch <adapter-dir> <out.json}"
OUT="${2:?upotreba: sbatch probe.sbatch <adapter-dir> <out.json}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_PYTHONPATH="$PYLIBS:/repo/src"
export SINGULARITYENV_HF_HUB_OFFLINE=0
export SINGULARITYENV_PROBE_THINKING="${PROBE_THINKING:-0}"
export SINGULARITYENV_PROBE_SYSTEM_FILE="${PROBE_SYSTEM_FILE:-}"
REPO=/scratch/project_465003647/agentmujo/repo
cd "$REPO" && git pull -q 2>/dev/null || true
srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  python -u /repo/workers/lumi/probe_lumi.py "$ADAPTER" "$OUT"
echo PROBE_DONE
