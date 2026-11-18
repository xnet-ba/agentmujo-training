#!/usr/bin/env python3
"""Build datasets/canonical/joint_train_v0.44.jsonl — 9B-joint-10 prose-first SFT.

Lekcije: joint08 (tool 0.867, safety-loop 1.0) + joint09 (HL 1.0, args 0.923,
ali refusal 0.0 — 31 override red prejak). Scorer audit: refusal liste
prosirene (rescore joint08 0.6->0.8); ostatak je check-first navika.
Joint10: joint08 formula + (a) prose-first: risky/ask-first promptovi ciji
PRVI asistent turn nema tool poziv (demonstracija, ne DPO), (b) HL micro-doza
od SAMO 12 override redova (umjesto 31). Baza: joint08 adapter (najcistiji).
Sastav ~2050: FC hard/med HL 700 + AG hard/med HL 400 + safety SFT 300 +
confirmation ask-first 400 + prose-first risky 100 + BC plain 200 +
override 12 + think 50. Seed 43. Deterministicki.
"""
import json
import random
from pathlib import Path

RNG = random.Random(43)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "joint_train_v0.44.jsonl"

FC_FILES = [f"function_calling_v0.{v}.jsonl" for v in ("2", "3", "4", "5")]
AG_FILES = [f"agentic_terminal_v0.{v}.jsonl" for v in ("1", "2", "3", "4", "5")]
BC_FILES = ["bosnian_core_v0.2.jsonl", "bosnian_core_v0.3.jsonl"]
SF_FILES = [f"safety_v0.{v}.jsonl" for v in ("3", "4", "5")]
CF_FILES = [f"confirmation_v0.{v}.jsonl" for v in ("1", "2", "3", "4")]
FC_ALL = FC_FILES + ["function_calling_v0.1.jsonl"]


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


def first_asst_no_tool(row):
    ms = [m for m in row.get("messages", []) if m.get("role") == "assistant"]
    if not ms:
        return False
    return not (ms[0].get("tool_calls") or [])


def mentions_terminal_request(row):
    t = first_user(row).lower()
    return ("terminal" in t or "kroz komand" in t or "komandom" in t
            or "preko terminala" in t)


def pick(rows, n, seen):
    # dedup i unutar kandidata (confirmation fajlovi recikliraju ID-eve)
    uniq, inlist = [], set()
    for r in rows:
        if ok_msg(r) and r["id"] not in seen and r["id"] not in inlist:
            inlist.add(r["id"])
            uniq.append(r)
    RNG.shuffle(uniq)
    out = uniq[:n]
    seen.update(r["id"] for r in out)
    return out


seen = set()
fc = [r for r in load(FC_FILES) if r.get("difficulty") in ("hard", "medium")]
fc = [r for r in fc if first_tool(r) not in (None, "terminal")]
ag = load(AG_FILES)
ag_hard = [r for r in ag if r.get("difficulty") == "hard"
           and first_tool(r) not in (None, "terminal")]
ag_med = [r for r in ag if r.get("difficulty") == "medium"
          and first_tool(r) not in (None, "terminal")]
override_pool = [r for r in load(FC_ALL) + ag
                 if mentions_terminal_request(r)
                 and first_tool(r) not in (None, "terminal")]
sf = load(SF_FILES)
cf = [r for r in load(CF_FILES) if first_tool(r) is None]
prose_risky = [r for r in sf + cf
               if first_asst_no_tool(r) and first_tool(r) in (None,)]
bc = [r for r in load(BC_FILES) if first_tool(r) is None]
think = [r for r in ag if r.get("enable_thinking")]

ov = pick(override_pool, 12, seen)
sel = (pick(fc, 700, seen) + pick(ag_hard, 280, seen)
       + pick(ag_med, 120, seen) + pick(sf, 300, seen)
       + pick(cf, 400, seen) + pick(prose_risky, 100, seen)
       + pick(bc, 200, seen) + pick(think, 50, seen) + ov)
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati u mixu!"
RNG.shuffle(sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
n_tool = sum(1 for r in sel if first_tool(r))
print(f"joint-10-9b: {len(sel)} (tool {n_tool}, override {len(ov)})")
