#!/usr/bin/env python3
"""9B-joint-07: SFT mix po 4B v0.30 receptu (FC 410 2x-prio + AG 280 + BC 280 + SF 100 + THINK 50).
Sve kanonski messages[] (tool_calls strukturirani), deterministicki seed 37.
Upotreba: python scripts/build_joint07_9b.py (radi iz root-a repoa)
Izlaz: datasets/canonical/joint_train_v0.40.jsonl (~1120 uzoraka)
"""
import json
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAN = REPO / "datasets" / "canonical"
rng = random.Random(37)

FC_FILES = [f"function_calling_v0.{v}.jsonl" for v in ("2", "3", "4", "5")]
AG_FILES = [f"agentic_terminal_v0.{v}.jsonl" for v in ("1", "2", "3", "4", "5")]
BC_FILES = ["bosnian_core_v0.2.jsonl", "bosnian_core_v0.3.jsonl"]
SF_FILES = [f"safety_v0.{v}.jsonl" for v in ("3", "4", "5")]


def load(files):
    rows = []
    for f in files:
        p = CAN / f
        if p.exists():
            rows += [json.loads(l) for l in open(p) if l.strip()]
    return rows


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def pick(rows, n):
    rng.shuffle(rows)
    return rows[:n]


fc = [r for r in load(FC_FILES) if r.get("difficulty") in ("easy", "medium")]
fc = [r for r in fc if first_tool(r) not in (None, "terminal")]
ag = [r for r in load(AG_FILES) if r.get("difficulty") == "hard"]
ag_med = [r for r in load(AG_FILES) if r.get("difficulty") == "medium"]
bc = load(BC_FILES)
sf = load(SF_FILES)
think = [r for r in load(AG_FILES) if r.get("enable_thinking")]

sel_fc = pick(fc, 410)
sel_ag_hard = pick(ag, 200)
sel_ag = sel_ag_hard + pick([r for r in ag_med if r not in sel_ag_hard], 80)
sel_bc = pick(bc, 280)
sel_sf = pick(sf, 100)
sel_th = pick([r for r in think if r not in sel_ag], 50)

sel = sel_fc + sel_ag + sel_bc + sel_sf + sel_th
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati u mixu!"
rng.shuffle(sel)
outp = CAN / "joint_train_v0.40.jsonl"
outp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
print(f"joint-07-9b: {len(sel)} (FC {len(sel_fc)} + AG {len(sel_ag)} + BC {len(sel_bc)} + SF {len(sel_sf)} + THINK {len(sel_th)})")
