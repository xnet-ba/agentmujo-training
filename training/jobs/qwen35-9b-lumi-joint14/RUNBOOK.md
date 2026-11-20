# RUNBOOK — joint14 LUMI (pokrenuti tek uz eksplicitno GPU odobrenje)

Pristup samo preko Oracle skocnog cvora (vidi `workers/lumi/README.md`).
Pravilo spool zamke: prvo `git pull` na scratch repou, PA TEK ONDA `sbatch`.

## 1. Upload v48 dataseta na scratch

```bash
ssh -i ~/.ssh/agentmujo_pro -o IdentitiesOnly=yes ubuntu@140.238.222.253 \
  "~/lumi.sh 'cat > /scratch/project_465003647/agentmujo/joint_9b_v48.jsonl'" \
  < datasets/canonical/joint_train_v0.48.jsonl
```

## 2. Sync job dir + config (stdin-forward, jedan po fajl)

```bash
J=/scratch/project_465003647/agentmujo/training/jobs/qwen35-9b-lumi-joint14
ssh ... "~/lumi.sh 'mkdir -p $J && cat > $J/config.yaml'" < training/jobs/qwen35-9b-lumi-joint14/config.yaml
ssh ... "~/lumi.sh 'cat > $J/metadata.json'" < training/jobs/qwen35-9b-lumi-joint14/metadata.json
# workers/lumi/lumi_9b_joint14.yaml ide u repo; na scratchu: git pull (korak 3).
```

## 3. Scratch repo pull + submit (dev-g test, small-g produkcija)

```bash
ssh ... "~/lumi.sh 'cd /scratch/project_465003647/agentmujo/repo && git pull'"
ssh ... "~/lumi.sh 'cd /scratch/project_465003647/agentmujo/repo && sbatch workers/lumi/train.sbatch /scratch/project_465003647/agentmujo/training/jobs/qwen35-9b-lumi-joint14'"
```

## 4. Nadgledanje + pipeline

```bash
ssh ... "~/lumi.sh 'squeue -u susterre'"
# .out log u repou; zatim redom: merge.sbatch -> gguf.sbatch -> bench.sbatch
# (pin llama.cpp 87f9c82, --no-mtp, block-check 25->24; vidi lineage DPO-v09).
```

## 5. Fetch + gate (lokalno)

```bash
amj artifacts fetch qwen35-9b-lumi-joint14
# bench: v0.6 single-shot gate + LOOP; uspjeh = conf/safety gore, tool >= 0.853
```
