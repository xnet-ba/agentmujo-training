#!/bin/bash
#SBATCH --job-name=amj-probe-m
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=amj-probem-%j.out
set -euo pipefail
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_PYTHONPATH="$PYLIBS:/repo/src"
srun singularity exec -B /scratch/project_465003647/agentmujo/repo:/repo -B /scratch:/scratch "$SIF" python -u /repo/workers/lumi/probe_merged.py /scratch/project_465003647/agentmujo/merged-09e /scratch/project_465003647/agentmujo/probe-merged-09e.json
