#!/bin/bash
#SBATCH --job-name=amj-gguf
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=amj-gguf-%j.out
# LUMI GGUF: llama.cpp (pin) -> F16 --no-mtp -> Q8_0 -> smoke.
# Upotreba: sbatch gguf.sbatch <merged-dir> <out-dir>
set -euo pipefail
MERGED="${1:?upotreba: sbatch gguf.sbatch <merged-dir> <out-dir>}"
OUTDIR="${2:?upotreba: sbatch gguf.sbatch <merged-dir> <out-dir>}"
LLAMACPP_REF="${LLAMACPP_REF:-87f9c82}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings || true
# Sistemski GCC 7.5 ne moze kompajlirati novi llama.cpp (AVX intrinsics):
# native GCC 13.2 za CPU build.
module load gcc-native/13.2
# gcc-native daje gcc/g++ u PATH, ali cmake prvo trazi `cc` (sistemski 7.5):
# eksplicitno pinovati compiler.
export CC=gcc CXX=g++
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export REPO=/scratch/project_465003647/agentmujo/repo
mkdir -p "$OUTDIR"
cd "$REPO" && git pull -q 2>/dev/null || echo "WARN: git pull nije uspio"

if [ ! -d "$OUTDIR/llama.cpp" ]; then
  # Revizija je commit-hash, ne branch: puni clone (ggml-org, redirect
  # ggerganov radi ali ne za SHA-fetch) pa checkout tocno tog SHA.
  git clone --filter=blob:none https://github.com/ggml-org/llama.cpp.git "$OUTDIR/llama.cpp"
  (cd "$OUTDIR/llama.cpp" && git checkout "$LLAMACPP_REF")
fi
# Build van kontejnera (host toolchain + cmake). Build dir se uvijek cisti
# da cmake ne bi zadrzao stari compiler iz prethodnog pokusaja.
rm -rf "$OUTDIR/llama.cpp/build"
cmake -S "$OUTDIR/llama.cpp" -B "$OUTDIR/llama.cpp/build" \
  -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release > "$OUTDIR/cmake.log" 2>&1
cmake --build "$OUTDIR/llama.cpp/build" --config Release -j 32 \
  --target llama-quantize llama-server > "$OUTDIR/build.log" 2>&1
echo "BUILD_DONE llamacpp=$LLAMACPP_REF"

srun --unbuffered singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
  env PYTHONPATH="/repo/src" python -u "$OUTDIR/llama.cpp/convert_hf_to_gguf.py" \
    "$MERGED" --outfile "$OUTDIR/model-f16.gguf" --outtype f16 --no-mtp
echo "CONVERT_DONE"

# qwen3_5: konverter zna upisati block_count=25 (MTP), tenzora ima za 24.
# Provjeri pa patchuj po potrebi (locirano iz 4B lekcija).
pip install -q --target="$OUTDIR/pygguf" gguf 2>&1 | tail -1 || true
BC=$(PYTHONPATH="$OUTDIR/pygguf" python3 -c "
from gguf import GGUFReader
r = GGUFReader('$OUTDIR/model-f16.gguf')
print(r.fields['llm.block_count'].parts[-1][0])" 2>/dev/null || echo "unknown")
echo "block_count=$BC"
if [ "$BC" = "25" ]; then
  srun singularity exec -B "$REPO:/repo" -B /scratch:/scratch "$SIF" \
    env PYTHONPATH="/repo/src" python -u /repo/quantization/patch_gguf.py \
      "$OUTDIR/model-f16.gguf" --set-qwen35-block-count 24
  echo "PATCHED_TO_24"
fi

"$OUTDIR/llama.cpp/build/bin/llama-server" --help > /dev/null 2>&1 || true
"$OUTDIR/llama.cpp/build/bin/llama-quantize" "$OUTDIR/model-f16.gguf" \
  "$OUTDIR/model-q8.gguf" Q8_0
(cd "$OUTDIR" && sha256sum model-f16.gguf model-q8.gguf > SHA256SUMS)
echo "QUANT_DONE"

# Smoke: digni server na CPU (Q8), jedna generacija, ugasi.
"$OUTDIR/llama.cpp/build/bin/llama-server" -m "$OUTDIR/model-q8.gguf" \
  --port 8899 -c 2048 --n-gpu-layers 0 > "$OUTDIR/smoke_server.log" 2>&1 &
SRV=$!
for i in $(seq 1 60); do
  sleep 10
  if curl -sf http://127.0.0.1:8899/health > /dev/null 2>&1; then break; fi
  if [ "$i" = "60" ]; then echo "SMOKE_SERVER_NIJE_DIGAO"; kill $SRV 2>/dev/null || true; exit 1; fi
done
curl -sf http://127.0.0.1:8899/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"system","content":"Ti si AgentMujo."},{"role":"user","content":"Da li je nginx servis trenutno aktivan?"}],"temperature":0,"max_tokens":120,"stream":false}' \
  | tee "$OUTDIR/smoke_reply.json" | head -c 600
echo; kill $SRV 2>/dev/null || true
echo GGUF_DONE
