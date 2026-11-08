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
# Kontejnerov ROCm torch (2.11) se NE smije pregaziti — PyPI torch bi
# shadowao ROCm i slomio CUDA. Zato se torch* brise iz pylibs nakon installa.
if [ ! -f "$PYLIBS/.pins-ok" ]; then
  srun -n1 singularity exec "$SIF" pip install -q --target="$PYLIBS" \
    "transformers==5.19.0" "trl==1.14.2" "peft==0.21.2" \
    "accelerate==1.15.0" "datasets==5.1.0" \
    "huggingface-hub>=0.25" safetensors pyyaml \
  && rm -rf "$PYLIBS"/torch* "$PYLIBS"/nvidia* "$PYLIBS"/triton* \
  && touch "$PYLIBS/.pins-ok"
fi
# Guard: mora biti ROCm torch iz kontejnera, ne PyPI.
srun -n1 singularity exec "$SIF" env PYTHONPATH="$PYLIBS" python -c \
  "import torch; assert 'rocm' in torch.__version__, torch.__version__; print('ROCM-TORCH-OK', torch.__version__)"
cd "$REPO"
srun singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="$PYLIBS:/repo/src" HF_HUB_CACHE="$HF_HUB_CACHE" \
  python /repo/workers/kaggle/job_run.py --job-dir "$JOBDIR"
echo TRAIN_DONE
