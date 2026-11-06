"""9B-gold subset: dialect-dense rows (tool_calls) iz joint v0.40 train.
Prioritet: AG hard/medium (multi-step ponasanje) + FC hard (preciznost alata)
+ verification/tool-selection/reasoning (sve). Bez BC/safety/rag/knowledge/coding.
Deterministicki (seed 37). Izlaz: jsonl + manifest sa IDs.
Upotreba: python scripts/build_9b_gold.py <ulaz.jsonl> <izlaz.jsonl>
"""
import json, random, sys

PLAN = [("agentic-terminal", "hard", None), ("agentic-terminal", "medium", 1200),
        ("function-calling", "hard", None), ("verification", None, None),
        ("tool-selection", None, None), ("reasoning", "hard", None)]

def main(inp, outp):
    rows = [json.loads(l) for l in open(inp)]
    dial = [r for r in rows if any(m.get("tool_calls") for m in r["messages"])]
    rng = random.Random(37)
    picked, seen = [], set()
    for task, diff, cap in PLAN:
        pool = [r for r in dial if r.get("task") == task
                and (diff is None or r.get("difficulty") == diff)
                and r["id"] not in seen]
        rng.shuffle(pool)
        take = pool if cap is None else pool[:cap]
        for r in take:
            seen.add(r["id"])
        picked.extend(take)
    rng.shuffle(picked)
    with open(outp, "w") as f:
        for r in picked:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(outp + ".manifest.json", "w") as f:
        json.dump({"input": inp, "n": len(picked),
                   "ids": [r["id"] for r in picked],
                   "plan": [list(p) for p in PLAN]}, f, ensure_ascii=False)
    print(f"gold: {len(picked)} rows -> {outp}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
