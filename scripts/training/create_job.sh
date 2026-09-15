#!/usr/bin/env bash
# amj job create wrapper: scripts/training/create_job.sh --config <yaml> [--id <job_id>]
set -euo pipefail
exec python3 -m agentmujo_training.cli.main job create "$@"
