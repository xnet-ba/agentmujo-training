#!/usr/bin/env python3
"""9B-gold04: korekcija gold03 listing-biasa (dokaz: 8 flipanih slucajeva).
Gold03 gate: tool 0.633->0.50 — model naucio "uvijek prvo izlistaj"
(file_list/process_list-first dominacija) + 1 halucinirani alat
(bench-042 package_list). Popravka:
  - FC easy/medium HL-first NAZAD (~900, precizna selekcija),
  - file_list/process_list-first CAP 300 (anti listing-bias),
  - zadrzano: AG hard HL, AG med HL 400, verification/tool-selection/
    reasoning hard, 600 ask-first, 400 plain.
Deterministicki (seed 37).
Upotreba: python scripts/build_9b_gold04.py <joint_train.jsonl> <izlaz.jsonl>
"""
import json
import random
import sys
from collections import Counter

CONF_FILES = [
    "datasets/canonical/confirmation_v0.2.jsonl",
    "datasets/canonical/confirmation_v0.3.jsonl",
    "datasets/canonical/confirmation_v0.4.jsonl",
]

LISTING_TOOLS = {"file_list", "process_list"}
LISTING_CAP = 300


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def main(inp, outp):
    rng = random.Random(37)
    rows = [json.loads(l) for l in open(inp)]

    conf = []
    for f in CONF_FILES:
        conf += [json.loads(l) for l in open(f)]
    ask = [r for r in conf if r.get("difficulty") == "hard"
           and not any(m.get("tool_calls") for m in r["messages"])]
    act = [r for r in conf if r.get("difficulty") == "hard"
           and any(m.get("tool_calls") for m in r["messages"])]
    rng.shuffle(ask)
    rng.shuffle(act)
    keep_conf = ask[:500] + act[:100]
    cids = set(r["id"] for r in keep_conf)

    def pool(task, diffs, hl_only=True):
        pl = [r for r in rows if r.get("task") == task
              and r.get("difficulty") in diffs and r["id"] not in cids]
        if hl_only:
            pl = [r for r in pl if first_tool(r) not in (None, "terminal")]
        rng.shuffle(pl)
        return pl

    sel = (pool("agentic-terminal", ("hard",))
           + pool("agentic-terminal", ("medium",))[:400]
           + pool("function-calling", ("hard",))
           + pool("function-calling", ("easy", "medium"))[:900]
           + pool("verification", ("hard", "medium"))
           + pool("tool-selection", ("hard", "medium"))
           + pool("reasoning", ("hard", "medium"))
           + keep_conf)

    # Anti listing-bias: file_list/process_list-first max 300 ukupno.
    listing = [r for r in sel if first_tool(r) in LISTING_TOOLS]
    rest = [r for r in sel if first_tool(r) not in LISTING_TOOLS]
    rng.shuffle(listing)
    sel = rest + listing[:LISTING_CAP]

    plain = [r for r in rows if r.get("task") == "bosnian-core"
             and r.get("difficulty") == "easy"
             and not any(m.get("tool_calls") for m in r["messages"])
             and r["id"] not in cids]
    rng.shuffle(plain)
    sel += plain[:400]

    ids = [r["id"] for r in sel]
    assert len(ids) == len(set(ids)), "DUPLIKATI!"
    rng.shuffle(sel)
    with open(outp, "w") as f:
        for r in sel:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"gold04: {len(sel)} rows -> {outp}")
    print(Counter(first_tool(r) for r in sel).most_common(8))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
