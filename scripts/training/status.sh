#!/usr/bin/env bash
# Prikaz statusa joba: scripts/training/status.sh <job_id>
set -euo pipefail
exec python3 -m agentmujo_training.cli.main job status "$@"
