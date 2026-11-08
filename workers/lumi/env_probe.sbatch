#!/bin/bash
#SBATCH --job-name=amj-probe
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=00:20:00
#SBATCH --output=amj-probe-%j.out
set -x
echo "=== GPU ==="
rocm-smi --showid --showproductname 2>&1 | head -6
echo "=== NET (compute) ==="
curl -s --max-time 10 -o /dev/null -w "HF:%{http_code}\n" https://huggingface.co
curl -s --max-time 10 -o /dev/null -w "PYPI:%{http_code}\n" https://pypi.org/simple/
echo "=== CONTAINER TORCH ==="
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
srun singularity exec "$SIF" python -c \
  "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'n', torch.cuda.device_count())"
echo PROBE_DONE
