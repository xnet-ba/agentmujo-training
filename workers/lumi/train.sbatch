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
# datasets-lib i tmp fajlovi NE smiju na Lustre-home (20G, puca kad se
# napuni tudjim keshevima): sve na scratch.
export HF_DATASETS_CACHE=/scratch/project_465003647/agentmujo/hfds
export TMPDIR=/scratch/project_465003647/agentmujo/tmp
# Triton/Inductor/XDG keševi NE smiju na Lustre-home (20G, pun tudjim keshevima):
# inace DPO/SFT padne sa "Disk quota exceeded: ~/.triton/cache" (vidjeno 2026-11-17).
export TRITON_CACHE_DIR=/scratch/project_465003647/agentmujo/tmp/triton
export TORCHINDUCTOR_CACHE_DIR=/scratch/project_465003647/agentmujo/tmp/inductor
export XDG_CACHE_HOME=/scratch/project_465003647/agentmujo/tmp/xdg
export SINGULARITYENV_TRITON_CACHE_DIR="$TRITON_CACHE_DIR"
export SINGULARITYENV_TORCHINDUCTOR_CACHE_DIR="$TORCHINDUCTOR_CACHE_DIR"
export SINGULARITYENV_XDG_CACHE_HOME="$XDG_CACHE_HOME"
export SINGULARITYENV_HF_DATASETS_CACHE="$HF_DATASETS_CACHE"
export SINGULARITYENV_TMPDIR="$TMPDIR"
# Kontejneru eksplicitno proslijediti env (SINGULARITYENV_*): obicni
# `env VAR=` prefix se ne prenosi pouzdano — bez ovoga HF skida 18GB model
# ispocetka u container-HOME i visi satima (vidjeno: 2.5h bez pomaka).
export SINGULARITYENV_HF_HUB_CACHE="$HF_HUB_CACHE"
export SINGULARITYENV_PYTHONPATH="$PYLIBS:/repo/src"
mkdir -p "$PYLIBS" "$HF_HUB_CACHE" "$HF_DATASETS_CACHE" "$TMPDIR"
# Pylibs (samo prvi put / kad se promijene pinovi):
# Kontejnerov ROCm torch (2.11) se NE smije pregaziti — PyPI torch bi
# shadowao ROCm i slomio CUDA. Zato se torch* brise iz pylibs nakon installa.
if [ ! -f "$PYLIBS/.pins-ok" ]; then
  srun -n1 singularity exec "$SIF" pip install -q --target="$PYLIBS" \
    "transformers==5.19.0" "trl==1.14.2" "peft==0.21.2" \
    "accelerate==1.15.0" "datasets==5.1.0" \
    "huggingface-hub>=0.25" safetensors pyyaml \
  && rm -rf "$PYLIBS"/torch* "$PYLIBS"/nvidia* "$PYLIBS"/triton* "$PYLIBS"/bitsandbytes* \
  && touch "$PYLIBS/.pins-ok"
fi
# Guard: mora biti ROCm torch iz kontejnera, ne PyPI.
srun -n1 singularity exec "$SIF" env PYTHONPATH="$PYLIBS" python -c \
  "import torch; assert 'rocm' in torch.__version__, torch.__version__; print('ROCM-TORCH-OK', torch.__version__)"
cd "$REPO"
# Uvijek svjež kod (LUMI klon inace zaostaje — vidjeno sa max_steps).
git pull -q 2>/dev/null || echo "WARN: git pull nije uspio, radim sa postojecim kodom"
srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  python -u /repo/workers/kaggle/job_run.py --job-dir "$JOBDIR"
echo TRAIN_DONE
