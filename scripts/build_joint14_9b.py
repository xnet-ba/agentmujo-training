#!/usr/bin/env python3
"""Build datasets/canonical/joint_train_v0.48.jsonl — 9B-joint-14 confirmation/safety.

Lekcije: joint08 sampion (v06 tool 0.853); joint09-13 REJECT (HL/prose
mikro-doze ruse safety/tool, prose-first truje tool trigger); runtime
rewrite rijesio HL (loop HL 1.0) bez tezina. Preostali gap joint08 v06:
conf 0.10 (9/10: model zove alat umjesto da pita) + safety 0.636
(shadow/poison failovi bench-047/059/063).
Pravila: (1) baza joint08 v0.41 (1850), NE joint12/13;
(2) SAMO confirmation/safety delta: 200 confirmation SA alatom
(ask + read-only check obrazac, ne prose-only) + 100 safety edge
(prioritet tool-poison + multiturn-escalation, v06 fail modovi);
(3) bez HL/prose-first uzoraka; lr 2e-5 nastavak.
Seed 47. Deterministicki.
"""
import json
import random
from pathlib import Path

RNG = random.Random(47)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "joint_train_v0.48.jsonl"

CF_FILES = [f"confirmation_v0.{v}.jsonl" for v in ("1", "2", "3", "4")]
SF_FILES = [f"safety_v0.{v}.jsonl" for v in ("3", "4", "5")]


def load(files):
    rows = []
    for f in files:
        p = CAN / f
        if p.exists():
            rows += [json.loads(l) for l in open(p) if l.strip()]
    return rows


def ok_msg(r):
    ms = r.get("messages")
    return bool(ms) and isinstance(ms, list) and len(ms) >= 2


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def safecat(r):
    return (r.get("metadata") or {}).get("safety_category", "?")


base = [json.loads(l) for l in open(CAN / "joint_train_v0.41.jsonl") if l.strip()]
seen = set(r["id"] for r in base)

# Confirmation SA alatom (ask + check), ne prose-only (joint13 lekcija).
cf_pool = [r for r in load(CF_FILES)
           if first_tool(r) is not None and r["id"] not in seen]
RNG.shuffle(cf_pool)
cf = cf_pool[:200]

# Safety edge: prioritet v06 fail modovi (tool-poison, escalation).
sf_pool = [r for r in load(SF_FILES) if r["id"] not in seen]
prio = [r for r in sf_pool if safecat(r) in ("agentic-tool-poison", "multiturn-escalation")]
rest = [r for r in sf_pool if safecat(r) not in ("agentic-tool-poison", "multiturn-escalation")]
RNG.shuffle(prio)
RNG.shuffle(rest)
sf = (prio + rest)[:100]

sel = base + cf + sf
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati!"
assert all(ok_msg(r) for r in sel)

# Leakage: bez doslovnog preklopa sa bench promptovima.
bench_prompts = set()
for v in ("0.1", "0.2", "0.3", "0.4", "0.5", "0.6"):
    p = ROOT / "benchmark" / f"cases_v{v}.jsonl"
    if p.exists():
        bench_prompts.update(json.loads(l)["prompt"] for l in open(p) if l.strip())


def first_user(row):
    ms = row.get("messages", [])
    return next((m.get("content", "") for m in ms if m.get("role") == "user"), "")


overlap = [r["id"] for r in sel if first_user(r) in bench_prompts]
assert not overlap, f"bench overlap: {overlap[:5]}"

RNG.shuffle(sel)
n_tool = sum(1 for r in sel if first_tool(r))
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
from collections import Counter
print(f"joint-14-9b: {len(sel)} (baza {len(base)} + conf-tool {len(cf)} + safety {len(sf)}, tool {n_tool})")
print("safety mix:", dict(Counter(safecat(r) for r in sf)))
