#!/usr/bin/env bash
# Preuzimanje artefakata joba (očekuje manifest + adapter na HF ili lokalni paket).
# Upotreba: scripts/training/download_artifacts.sh <job_id> [--from-hf <repo>]
set -euo pipefail
exec python3 -m agentmujo_training.cli.main artifacts fetch "$@"
