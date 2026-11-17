#!/usr/bin/env python3
"""Build datasets/canonical/joint_train_v0.41.jsonl — 9B-joint-08 safety-SFT.

Lekcije: DPO safety-mix rusi tool (2B: 0.8->0.0; 9B dpo14-16: safety zapeo
<=0.5, tool pao). DPO-preference mehanizam je problem, ne safety sadrzaj:
joint07 SFT (0 safety redova) drzao je safety 0.857 naslijedjem.
Zato: SFT DEMONSTRACIJE (messages[]), ne DPO parovi; safety 15% (granica),
tool-jedra 75%. Baza: gold06/dpo03 (cista, bez DPO bagaza).
Mix ~2000: FC hard 700 + AG hard/med 400 + safety SFT 300 +
confirmation ask-first 200 + BC plain 200 + think 50. Seed 41.
Deterministicki. Ne dira postojece fajlove ni splits/.
"""
import json
import random
from pathlib import Path

RNG = random.Random(41)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "joint_train_v0.41.jsonl"

FC_FILES = [f"function_calling_v0.{v}.jsonl" for v in ("2", "3", "4", "5")]
AG_FILES = [f"agentic_terminal_v0.{v}.jsonl" for v in ("1", "2", "3", "4", "5")]
BC_FILES = ["bosnian_core_v0.2.jsonl", "bosnian_core_v0.3.jsonl"]
SF_FILES = [f"safety_v0.{v}.jsonl" for v in ("3", "4", "5")]
CF_FILES = [f"confirmation_v0.{v}.jsonl" for v in ("1", "2", "3", "4")]


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


def pick(rows, n, seen):
    rows = [r for r in rows if ok_msg(r) and r["id"] not in seen]
    RNG.shuffle(rows)
    out = rows[:n]
    seen.update(r["id"] for r in out)
    return out


seen = set()
fc = [r for r in load(FC_FILES) if r.get("difficulty") in ("hard", "medium")]
fc = [r for r in fc if first_tool(r) not in (None, "terminal")]
ag_hard = [r for r in load(AG_FILES) if r.get("difficulty") == "hard"]
ag_med = [r for r in load(AG_FILES) if r.get("difficulty") == "medium"]
sf = load(SF_FILES)
cf = [r for r in load(CF_FILES) if first_tool(r) is None]  # ask-first, bez alata
bc = [r for r in load(BC_FILES) if first_tool(r) is None]  # plain tekst
think = [r for r in load(AG_FILES) if r.get("enable_thinking")]

sel = (pick(fc, 700, seen) + pick(ag_hard, 280, seen) + pick(ag_med, 120, seen)
       + pick(sf, 300, seen) + pick(cf, 200, seen) + pick(bc, 200, seen)
       + pick(think, 50, seen))
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati u mixu!"
RNG.shuffle(sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
n_tool = sum(1 for r in sel if first_tool(r))
print(f"joint-08-9b: {len(sel)} (tool {n_tool} + SAFETY/PLAIN {len(sel)-n_tool})")
