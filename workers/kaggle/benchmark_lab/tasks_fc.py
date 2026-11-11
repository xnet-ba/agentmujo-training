"""Function-calling benchmark kao Inspect task (nas bench v0.5 format).

Scorer: 1 ako model emituje <function=EXPECTED>, inace 0.
Cita cases_v0.5.jsonl iz repoa (ili put proslijedjen notebooku).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

FUNC_RE = re.compile(r"<function=([a-z_][a-z0-9_]*)>", re.IGNORECASE)


def load_fc_cases(cases_path: str | Path):
    out = []
    for line in Path(cases_path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        c = json.loads(line)
        if c.get("expected_tool"):
            out.append(c)
    return out


def fc_bench(cases_path: str = "benchmark/cases_v0.5.jsonl"):
    from inspect_ai import task, Task
    from inspect_ai.solver import generate
    from inspect_ai.scorer import Score, Target, scorer
    from inspect_ai.dataset import Sample

    cases = load_fc_cases(cases_path)
    samples = [Sample(input=c["prompt"], id=c["id"],
                      metadata={"expected_tool": c["expected_tool"]})
               for c in cases]

    @scorer(metrics=[])
    def fc_scorer():
        async def score(state, target: Target):
            text = state.output.completion or ""
            m = FUNC_RE.search(text)
            got = m.group(1).lower() if m else None
            exp = state.metadata["expected_tool"].lower()
            return Score(value=1 if got == exp else 0)
        return score

    @task
    def _t():
        return Task(dataset=samples, solver=[generate()],
                    scorer=fc_scorer())
    return _t
