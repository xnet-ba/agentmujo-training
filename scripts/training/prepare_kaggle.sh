#!/usr/bin/env bash
# Priprema Kaggle workera: provjere + upute (ne lijepi tokene u shell history ako se može izbjeći).
# Upotreba: scripts/training/prepare_kaggle.sh
set -euo pipefail
echo "== Kaggle worker priprema =="
command -v kaggle >/dev/null && echo "PASS kaggle CLI ($(kaggle --version 2>/dev/null | head -n1))" || echo "WARN kaggle CLI nije na PATH (izolirani env je OK)"
if [ -n "${KAGGLE_API_TOKEN:-}" ] || [ -f "$HOME/.kaggle/access_token" ]; then
  echo "PASS Kaggle API token prisutan (vrijednost se ne ispisuje)"
elif [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "PASS ~/.kaggle/kaggle.json postoji (legacy)"
  chmod 600 "$HOME/.kaggle/kaggle.json" 2>/dev/null || true
elif [ -n "${KAGGLE_USERNAME:-}" ] && [ -n "${KAGGLE_KEY:-}" ]; then
  echo "PASS KAGGLE_USERNAME/KAGGLE_KEY iz env (legacy, vrijednosti se ne ispisuju)"
else
  echo "BLOCKED Kaggle auth — potrebno jedno od:"
  echo "  a) MODERNO: kaggle.com/settings/api → Generate New Token →"
  echo "     export KAGGLE_API_TOKEN=<token> ili ~/.kaggle/access_token (chmod 600)"
  echo "  b) LEGACY: kaggle.json u ~/.kaggle/kaggle.json (chmod 600)"
  echo "  NIKADA u git. Telefonska verifikacija za GPU: kaggle.com/settings/phone-verification"
fi
echo "Kvota: kaggle quota | Sesija: GPU notebook + job_run.py (vidi workers/kaggle/README.md)"
