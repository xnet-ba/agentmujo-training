# LUMI worker — AMD MI250X trening (verificirano 2026-11-08)

Pristup: **samo preko Oracle skočnog čvora** (`ubuntu@140.238.222.253`,
key `~/.ssh/agentmujo_pro`, `IdentitiesOnly=yes`). Direktan EFP treba
svjež cert (~10h) — skočni čvor ga ima gotovog (`~/lumi.sh` wrapper).

```bash
ssh -i ~/.ssh/agentmujo_pro -o IdentitiesOnly=yes ubuntu@140.238.222.253
~/lumi.sh "hostname"            # -> uan18
~/lumi.sh "squeue -u susterre"  # queue
~/lumi.sh "sinfo -p dev-g,small-g,standard-g"
```

Pravila: sa laptopa NIKAD direktno na LUMI; fajlovi idu stdin-forwardom
(`ssh oracle "~/lumi.sh 'cat > /scratch/.../f'" < lokalni-fajl`) ili
tar-streamom; ključevi i certovi NIKAD u git.

## Stack (kontejner `lumi-multitorch-latest.sif`, ROCm 7.2)

- torch 2.11+rocm7.2 (cuda True), python 3.12; MI250X GCD 64GB.
- Kontejner ima transformers 5.10.1 / trl 1.16.0 — NE koriste se;
  pinovi se instaliraju `pip install --target=$PYLIBS` (compute čvor
  ima internet: HF 200, PyPI 200) + `PYTHONPATH`. bitsandbytes se
  preskače (bf16 trening, ROCm ga ne podržava).
- HF cache: `/scratch/project_465003647/agentmujo/hfcache` (modeli su
  javni — token ne treba).

## Tok posla

1. `amj job create --config workers/lumi/lumi_<x>.yaml --job-id <id>`
2. tar-stream job dir + `workers/lumi/train.sbatch` na scratch.
3. `sbatch train.sbatch <job-dir>` (dev-g test / small-g produkcija).
4. `squeue` + citanje `.out` fajla; artefakti ostaju na scratchu,
   manifesti se vracaju lokalno (`amj artifacts fetch` rucno).

Particije: `dev-g` (test, max 1 job, 3h, 8 idle u novembru),
`small-g`/`standard-g` (produkcija, MI250X čvorovi).
Projekt: `project_465003647`, user `susterre`,
storage `/project/...` (trajno) i `/scratch/...` (poslovi).
EFP cert na Oracleu vazi ~10h — planirati poslove unutar prozora.
