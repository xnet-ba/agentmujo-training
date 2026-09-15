#!/usr/bin/env bash
# Priprema Kaggle workera: provjere + upute (ne lijepi tokene u shell history ako se može izbjeći).
# Upotreba: scripts/training/prepare_kaggle.sh
set -euo pipefail
echo "== Kaggle worker priprema =="
command -v hf >/dev/null && echo "PASS hf CLI" || echo "FAIL hf CLI"
if [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "PASS ~/.kaggle/kaggle.json postoji"
  chmod 600 "$HOME/.kaggle/kaggle.json" 2>/dev/null || true
elif [ -n "${KAGGLE_USERNAME:-}" ] && [ -n "${KAGGLE_KEY:-}" ]; then
  echo "PASS KAGGLE_USERNAME/KAGGLE_KEY iz env (vrijednosti se ne ispisuju)"
else
  echo "BLOCKED Kaggle auth — potrebno: kaggle.json ili KAGGLE_USERNAME/KAGGLE_KEY"
  echo "  1. kaggle.com → Settings → API → Create New Token (kaggle.json)"
  echo "  2. premjestiti u ~/.kaggle/kaggle.json (chmod 600), NIKADA u git"
  echo "  3. telefonska verifikacija za GPU: kaggle.com/settings/phone-verification"
fi
echo "Sljedeće: rucno kreirati GPU notebook ILI: kaggle kernels push -p <dir> (treba Kaggle CLI + auth)"
