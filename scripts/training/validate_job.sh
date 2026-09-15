#!/usr/bin/env bash
# Validacija job direktorija: scripts/training/validate_job.sh <job_id>
set -euo pipefail
exec python3 -m agentmujo_training.cli.main job validate "$@"
