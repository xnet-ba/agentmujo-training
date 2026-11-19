#!/usr/bin/env python3
"""Build datasets/canonical/joint_train_v0.46.jsonl — 9B-joint-12 minimalni HL.

Lekcije: joint08 sampion (loop tool 0.867/safety 1.0); joint09/10 HL doza
(31 red + prose flood) lomi safety; joint10/11 "kolapsi" bili merge bug
(double-count), ne trening. Joint12 = joint08 mix + SAMO 12 override redova
(terminal->HL), bez prose flooda, lr 2e-5, baza joint08.
Cilj: HL gore, sve ostalo netaknuto (Pareto vs joint08 loop).
Seed 45. Deterministicki.
"""
import json
import random
from pathlib import Path

RNG = random.Random(45)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "joint_train_v0.46.jsonl"


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


def first_user(row):
    ms = row.get("messages", [])
    return next((m.get("content", "") for m in ms if m.get("role") == "user"), "")


base = [json.loads(l) for l in open(CAN / "joint_train_v0.41.jsonl") if l.strip()]
seen = set(r["id"] for r in base)
pool = [r for r in load(["function_calling_v0.1.jsonl"])
        if ok_msg(r) and "terminal" in first_user(r).lower()
        and first_tool(r) not in (None, "terminal")
        and r["id"] not in seen]
RNG.shuffle(pool)
ov = pool[:12]
sel = base + ov
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati!"
RNG.shuffle(sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
n_tool = sum(1 for r in sel if first_tool(r))
print(f"joint-12-9b: {len(sel)} (baza {len(base)} + override {len(ov)}, tool {n_tool})")
