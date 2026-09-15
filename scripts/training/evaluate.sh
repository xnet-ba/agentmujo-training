#!/usr/bin/env bash
# Evaluacija adaptera/checkpointa AgentMujo-Benchom (rule-based dio).
# Upotreba: scripts/training/evaluate.sh --cases benchmark/cases_v0.3.jsonl
set -euo pipefail
exec python3 -m agentmujo_training.cli.main benchmark run "$@"
