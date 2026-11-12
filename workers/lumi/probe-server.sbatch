#!/bin/bash
#SBATCH --job-name=amj-srvprobe
#SBATCH --account=project_465003647
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=amj-srvprobe-%j.out
# Uporedba reasoning auto vs off na llama-serveru: 3 sonde, loop SYSTEM.
# Upotreba: sbatch probe-server.sbatch <model-q8.gguf> <reasoning:auto|off> <out.json>
set -euo pipefail
MODEL="${1:?upotreba: sbatch probe-server.sbatch <model> <auto|off> <out>}"
MODE="${2:?upotreba: sbatch probe-server.sbatch <model> <auto|off> <out>}"
OUT="${3:?upotreba: sbatch probe-server.sbatch <model> <auto|off> <out>}"
LLAMACPP_BIN=/scratch/project_465003647/agentmujo/gguf-09e/llama.cpp/build/bin
SYS="Ti si AgentMujo, asistent za administraciju Linux servera. Odgovaraj na bosanskom jeziku (ijekavica). Dostupni alati: service_status(service), service_restart(service), service_logs(service, lines), disk_usage(path), memory_usage(), cpu_usage(), process_list(limit, sort_by), network_status(), port_check(port), package_query(package), package_install(package), file_list(path), file_read(path, lines), terminal(command, timeout_s). Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom. Preferiraj high-level alat. Nikada ne pretpostavljaj uspjeh — verifikuj. Opasne zahtjeve odbij ili traži potvrdu."
if [ "$MODE" = "off" ]; then EXTRA="--reasoning off"; else EXTRA=""; fi
# shellcheck disable=SC2086
$LLAMACPP_BIN/llama-server -m "$MODEL" --port 8898 -c 4096 \
  $EXTRA --n-gpu-layers 0 -t 16 > "$(dirname "$OUT")/srvprobe_server.log" 2>&1 &
SRV=$!
for i in $(seq 1 60); do
  sleep 10
  if curl -sf http://127.0.0.1:8898/health > /dev/null 2>&1; then break; fi
  if [ "$i" = "60" ]; then echo "SERVER_NIJE_DIGAO"; kill $SRV 2>/dev/null || true; exit 1; fi
done
> "$OUT"
for P in "Da li je nginx servis trenutno aktivan?" "Prikaži zadnjih 20 linija nginx loga." "Ko slusa na portu 22?"; do
  python3 - "$SYS" "$P" "$OUT" <<'EOF' >> "$OUT"
import json, sys, urllib.request
SYS, P, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
body = {"messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": P}],
        "temperature": 0.0, "max_tokens": 200, "stream": False}
req = urllib.request.Request("http://127.0.0.1:8898/v1/chat/completions",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json"})
try:
    d = json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
    t = d["choices"][0]["message"]["content"]
except Exception as e:
    t = f"ERROR: {e}"
print(json.dumps({"prompt": P, "text": t[:1500]}, ensure_ascii=False))
EOF
done
kill $SRV 2>/dev/null || true
echo SRVPROBE_DONE
