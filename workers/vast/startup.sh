#!/usr/bin/env bash
# Vast worker startup — stateless GPU run.
# Korištenje: startup.sh <experiment-manifest.json>
# Očekuje env: HF_TOKEN (iz secret storagea workera, NIKADA u gitu).
set -euo pipefail
MANIFEST="${1:?upotreba: startup.sh <experiment-manifest.json>}"
echo "[vast] manifest: $MANIFEST"
python3 -c "import json; m=json.load(open('$MANIFEST')); print('[vast] eksperiment:', m['experiment_id'], '| baza:', m['base_model'])"
pip install -q -e ".[train]"
# 1. Povuci pinovani dataset snapshot + bazni model (revizije iz manifesta).
#    hf download --revision <sha> ...  (konkretne putanje popunjava experiment)
# 2. Dry-run validacija prije GPU troška:
python3 training/training_run.py --config configs/training/sft_function_calling.yaml --out outputs/smoke --dry-run
# 3. Puni run (otkomentarisati na workeru):
# python3 training/training_run.py --config configs/training/sft_function_calling.yaml --out outputs/<experiment-id>
# 4. Sync artefakata:
bash workers/vast/sync.sh outputs/<experiment-id>
