#!/usr/bin/env bash
# Vast worker sync — push adaptera/checkpointa/metrika na HF Hub + manifest na Oracle.
# Korištenje: sync.sh <outputs-dir>
set -euo pipefail
OUT="${1:?upotreba: sync.sh <outputs-dir>}"
test -f "$OUT/experiment_manifest.json" || { echo "[vast] nema manifesta u $OUT"; exit 1; }
echo "[vast] sync $OUT -> HF Hub (hf upload, pinovana revizija) + manifest -> Oracle"
# Primjer (popuniti imenima repoa pri prvom eksperimentu):
# hf upload <hf-user>/agentmujo-fc-sft-v0.1 "$OUT" --repo-type model
# scp "$OUT/experiment_manifest.json" oracle:agentmujo-training/experiments/
echo "[vast] TODO: konkretna imena repoa dolaze s prvim eksperimentom (docs/HF_PUBLISHING.md gate)."
