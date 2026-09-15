#!/usr/bin/env bash
# Konverzija HF safetensors -> GGUF Q8_0 (reproducibilno, pinovane revizije).
# Upotreba: convert_q8.sh <hf-repo> <revizija> <out-dir>
# Rezultat: <out-dir>/model-q8.gguf + <out-dir>/SHA256SUMS
set -euo pipefail

HF_REPO="${1:?upotreba: convert_q8.sh <hf-repo> <revizija> <out-dir>}"
REVISION="${2:?upotreba: convert_q8.sh <hf-repo> <revizija> <out-dir>}"
OUT="${3:?upotreba: convert_q8.sh <hf-repo> <revizija> <out-dir>}"
# Pinovana llama.cpp revizija — promjenu dokumentovati u commit poruci.
LLAMACPP_REF="${LLAMACPP_REF:-master}"

mkdir -p "$OUT"
echo "[q8] model: $HF_REPO @ ${REVISION:0:12}"

# 1. llama.cpp (plitko, pinovano)
if [ ! -d "$OUT/llama.cpp" ]; then
  git clone --depth 1 ${LLAMACPP_REF:+--branch "$LLAMACPP_REF"} \
    https://github.com/ggerganov/llama.cpp.git "$OUT/llama.cpp"
fi
cmake -S "$OUT/llama.cpp" -B "$OUT/llama.cpp/build" \
  -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build "$OUT/llama.cpp/build" --config Release -j "$(nproc)" \
  --target llama-quantize

# 2. Preuzmi težine na pinovanoj reviziji (bez nepotrebnih fajlova)
hf download "$HF_REPO" --revision "$REVISION" --local-dir "$OUT/hf" \
  --include "*.safetensors" --include "*.json" --include "*.jinja" \
  --include "tokenizer*" --include "vocab*" --include "merges*"

# 3. Konverzija u F16 GGUF (kontrolna tačka)
python3 "$OUT/llama.cpp/convert_hf_to_gguf.py" "$OUT/hf" \
  --outfile "$OUT/model-f16.gguf" --outtype f16

# 4. Kvantizacija Q8_0
"$OUT/llama.cpp/build/bin/llama-quantize" "$OUT/model-f16.gguf" \
  "$OUT/model-q8.gguf" Q8_0

# 5. Manifest
(cd "$OUT" && sha256sum model-f16.gguf model-q8.gguf > SHA256SUMS)
{
  echo "repo: $HF_REPO"
  echo "revision: $REVISION"
  echo "llamacpp: $LLAMACPP_REF"
  echo "quant: Q8_0"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/QUANT_MANIFEST.txt"

echo "[q8] gotovo:"
ls -la "$OUT/model-q8.gguf" "$OUT/SHA256SUMS"
echo "[q8] sljedeće: eval full vs Q8 prema docs/QUANT_EVAL.md"
