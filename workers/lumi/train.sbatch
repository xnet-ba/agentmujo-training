#!/bin/bash
#SBATCH --job-name=amj-train
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --output=amj-train-%j.out
# LUMI trening worker: ROCm kontejner + pip --target pylibs + job_run.py.
# Upotreba: sbatch train.sbatch <job-dir-na-scratchu>
# (job-dir sadrzi config.yaml + metadata.json; vidi amj job create)
set -euo pipefail
JOBDIR="${1:?upotreba: sbatch train.sbatch <job-dir>}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export REPO=/scratch/project_465003647/agentmujo/repo
export PYTHONPATH="$PYLIBS:${PYTHONPATH:-}"
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
mkdir -p "$PYLIBS" "$HF_HUB_CACHE"
# Pylibs (samo prvi put / kad se promijene pinovi):
if [ ! -f "$PYLIBS/.pins-ok" ]; then
  srun -n1 singularity exec "$SIF" pip install -q --target="$PYLIBS" \
    "transformers==5.19.0" "trl==1.14.2" "peft==0.21.2" \
    "accelerate==1.15.0" "datasets==5.1.0" \
    "huggingface-hub>=0.25" safetensors pyyaml \
  && touch "$PYLIBS/.pins-ok"
fi
cd "$REPO"
srun singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="$PYLIBS:/repo/src" HF_HUB_CACHE="$HF_HUB_CACHE" \
  python /repo/workers/kaggle/job_run.py --job-dir "$JOBDIR"
echo TRAIN_DONE
