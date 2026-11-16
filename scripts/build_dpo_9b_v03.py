#!/usr/bin/env python3
"""Build datasets/canonical/dpo_9b_v0.3.jsonl — 9B DPO-14 tool-calling mix.

Recept (lekcije 4B-dpo01 + 9B-dpo03, oba pobjednika istim hiperparametrima):
  DPO nad najnovijim SFT adapterom (joint07), lr 5e-6, beta 0.1, r16, 1 epoha.
Razlika prema plateau-runovima (dpo09-13, 131 par): OVOLIKO VECI skup —
samo parovi ciji chosen sadrzi <tool_call> (dijalekt!), prioritet FC-derivirani
(v0.7/v0.8: pogresan alat / izmisljen parametar / bez alata / rizicno bez
potvrde kao rejected) + AG-derivirani v0.9 + v0.6 tool-podskup + 9b v0.1/v0.2.
Cap 2000 (125 koraka uz 1x16 — staje u dev-g 1h); seed 37 deterministicki.
Ne dira postojece fajlove ni splits/.
"""
import json
import random
from pathlib import Path

RNG = random.Random(37)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "dpo_9b_v0.3.jsonl"
N_WANT = 2000


def load(name):
    p = CAN / name
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def has_tool(r):
    return "<tool_call>" in (r.get("chosen", "") + r.get("prompt", ""))


v07 = [r for r in load("dpo_v0.7.jsonl") if has_tool(r)]
v08 = [r for r in load("dpo_v0.8.jsonl") if has_tool(r)]
v09 = [r for r in load("dpo_v0.9.jsonl") if has_tool(r)]
v06 = [r for r in load("dpo_v0.6.jsonl") if has_tool(r)]
v9b = load("dpo_9b_v0.1.jsonl") + load("dpo_9b_v0.2.jsonl")

# Kvota po izvoru (diverzitet!): FC-jednokoracni + FC-visekoracni + AG + hibrid.
# v0.1/v0.2 izbaceni: legacy format bez kanonskih polja (27 REJECT) — ne kvare mix.
QUOTA = [(v07, 800), (v08, 650), (v09, 400), (v06, 150)]
pool = []
for rows, n in QUOTA:
    pool += rows[:n]
RNG.shuffle(pool)

seen, sel = set(), []
for r in pool:
    key = (r.get("prompt", "") + r.get("chosen", ""))[:500]
    if key in seen:
        continue
    seen.add(key)
    sel.append(r)
    if len(sel) >= N_WANT:
        break

ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati u mixu!"
assert all("<tool_call>" in (r.get("chosen", "") + r.get("prompt", "")) or r in v9b for r in sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
print(f"dpo-9b-v0.3: {len(sel)} (v0.7 {sum(1 for r in sel if r in v07)} + "
      f"v0.8 {sum(1 for r in sel if r in v08)} + v0.9 {sum(1 for r in sel if r in v09)} + "
      f"v0.6 {sum(1 for r in sel if r in v06)} + 9b-old {sum(1 for r in sel if r in v9b)})")
