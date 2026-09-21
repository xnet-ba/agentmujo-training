#!/usr/bin/env python3
"""Format-proba sa PRODUKCIJSKIM SYSTEM promptom (iz Modelfile.nonthinking).
Upotreba: python benchmark/format_probe_prod.py <model> [N=10]
"""
from __future__ import annotations
import json
import sys
sys.path.insert(0, "benchmark")
from two_step_eval import chat, parse  # noqa: E402
sys.path.insert(0, "src")
from agentmujo_training.benchmark import load_cases  # noqa: E402

PROD_SYSTEM = (
    "Ti si AgentMujo, asistent za administraciju Linux servera. "
    "Odgovaraj uvijek na bosanskom jeziku (ijekavica), osim ako korisnik traži drugačije. "
    "Za jednostavne zadatke odgovori direktnim tool pozivom bez dugog obrazlaganja. "
    "Preferiraj high-level alat nad sirovom terminal komandom. "
    "Verifikuj rezultat svake akcije. Opasne zahtjeve odbij ili traži potvrdu."
)

def main() -> int:
    model = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    cases = [c for c in load_cases("benchmark/cases_v0.5.jsonl")][:n]
    ok = 0
    for c in cases:
        base = [{"role": "system", "content": PROD_SYSTEM},
                {"role": "user", "content": c.prompt}]
        try:
            text = chat(model, base, False, 256)
        except Exception as e:
            print(f"ERR {c.id}: {e}")
            continue
        tool, args = parse(text)
        mark = "OK " if tool else "FAIL"
        if tool:
            ok += 1
        print(f"{mark} {c.id} tool={tool} args={args} :: {text[:120]!r}")
    print(f"\nPROD-PROMPT FORMAT SCORE: {ok}/{len(cases)} = {ok/len(cases):.2f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
