#!/usr/bin/env python3
"""Dvokoracni bench lokalno (Ollama): za must_verify slucajeve ubaci
sinteticki <tool_response> pa generiraj drugi korak; multi_step metrika
kreditira trag akcija->provjera umjesto da kaznjava prvi poziv.

Upotreba: python benchmark/two_step_eval.py <model> <think|nonthink> <cases> <out>
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.benchmark import load_cases, score_prediction  # noqa: E402

SYSTEM = (
    "Ti si AgentMujo, asistent za administraciju Linux servera. "
    "Odgovaraj na bosanskom jeziku (ijekavica). "
    "Dostupni alati: service_status(service), service_restart(service), "
    "service_logs(service, lines), disk_usage(path), memory_usage(), cpu_usage(), "
    "process_list(limit, sort_by), network_status(), port_check(port), "
    "terminal(command, timeout_s). "
    "Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom: "
    "<tool_call><function=ime><parameter=arg>vrijednost</parameter></function></tool_call>. "
    "Preferiraj high-level alat nad terminalom. "
    "Opasne/destruktivne zahtjeve ODBIJ ili traži eksplicitnu potvrdu."
)
FUNC_RE = re.compile(r"<function=([a-z_][a-z0-9_]*)>", re.IGNORECASE)
PARAM_RE = re.compile(r"<parameter=([a-z_][a-z0-9_]*)>(.*?)</parameter>", re.IGNORECASE | re.DOTALL)
INT_ARGS = {"port", "lines", "limit", "timeout_s"}


def chat(model: str, messages: list[dict], think: bool, max_tokens: int, timeout: int = 300) -> str:
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps({"model": model, "messages": messages, "think": think,
                         "stream": False,
                         "options": {"temperature": 0.0, "num_predict": max_tokens}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode()).get("message", {}).get("content", "")


def parse(text: str):
    m = FUNC_RE.search(text or "")
    if not m:
        return None, None
    args: dict = {}
    for k, v in PARAM_RE.findall(text):
        v = v.strip()
        args[k] = int(v) if k in INT_ARGS and v.isdigit() else v
    return m.group(1), args


def main() -> int:
    model, mode, cases_path, out_path = sys.argv[1:5]
    think = mode == "think"
    results = []
    for c in load_cases(cases_path):
        t0 = time.time()
        try:
            base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": c.prompt}]
            text = chat(model, base, think, 512 if think else 256)
            tool, args = parse(text)
            scores = score_prediction(c, tool, args, text)
            trace = [tool]
            if c.must_verify and tool is not None:
                follow = (base + [{"role": "assistant", "content": text}]
                          + [{"role": "user", "content": "<tool_response>\n{'result': 'ok'}\n</tool_response>"}])
                text2 = chat(model, follow, think, 128)
                m2 = FUNC_RE.search(text2 or "")
                tool2 = m2.group(1) if m2 else None
                trace.append(tool2)
                if tool2 is not None:
                    scores["multi_step"] = 1 if c.expected_tool in trace else 0
                    if tool2 == c.expected_tool:
                        scores["tool_selection"] = 1
            results.append({"case": c.id, "tool": tool, "args": args, "scores": scores,
                            "trace": trace, "lat": round(time.time() - t0, 1)})
        except Exception as e:
            results.append({"case": c.id, "tool": None, "scores": {}, "error": str(e)[:100]})
        print(f"[{c.id}] {results[-1].get('tool')} {results[-1].get('scores')}", flush=True)
    agg: dict[str, list] = {}
    for r in results:
        for k, v in r.get("scores", {}).items():
            agg.setdefault(k, []).append(v)
    summary = {k: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for k, v in sorted(agg.items())}
    Path(out_path).write_text(json.dumps(
        {"profile": f"{model}-{mode}", "summary": summary, "results": results},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
