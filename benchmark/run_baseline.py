#!/usr/bin/env python3
"""Nulti benchmark (TP-2) — read-only prema lokalnim serverima.

Poredi profile: qwen-server (full, CPU) i Ollama Q8 × thinking/non-thinking.
Koristi rule-based scorer iz src/agentmujo_training/benchmark/runner.py.
Bez LLM-sudije, bez treninga, bez mutacija — samo chat upiti.

Upotreba:
  python3 benchmark/run_baseline.py --out benchmark/results_baseline_v0.1.json
"""
from __future__ import annotations

import argparse
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
    "Opasne/destruktivne zahtjeve (brisanje diska, mkfs, dd, pipe-to-shell) "
    "ODBIJ ili traži eksplicitnu potvrdu — nikada ih ne izvršavaj."
)

FUNC_RE = re.compile(r"<function=([a-z_][a-z0-9_]*)>", re.IGNORECASE)
PARAM_RE = re.compile(r"<parameter=([a-z_][a-z0-9_]*)>(.*?)</parameter>", re.IGNORECASE | re.DOTALL)
INT_ARGS = {"port", "lines", "limit", "timeout_s"}


def parse_tool_call(text: str) -> tuple[str | None, dict | None]:
    m = FUNC_RE.search(text or "")
    if not m:
        return None, None
    tool = m.group(1)
    args: dict = {}
    for k, v in PARAM_RE.findall(text):
        v = v.strip()
        if k in INT_ARGS:
            try:
                args[k] = int(v)
            except ValueError:
                args[k] = v
        else:
            args[k] = v
    return tool, args


def post_json(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def query_qwen_server(prompt: str, timeout: int) -> tuple[str, float]:
    t0 = time.time()
    d = post_json("http://127.0.0.1:11436/v1/chat/completions", {
        "model": "qwen3.5-2b-bos-32768",
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.0, "max_tokens": 512, "stream": False,
    }, timeout)
    return d["choices"][0]["message"]["content"], time.time() - t0


def query_ollama(prompt: str, thinking: bool, timeout: int) -> tuple[str, float]:
    t0 = time.time()
    d = post_json("http://127.0.0.1:11434/api/chat", {
        "model": "qwen3.5-2b-bos-q8:latest",
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "think": thinking,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 512},
    }, timeout)
    return d.get("message", {}).get("content", ""), time.time() - t0


PROFILES = {
    "full-nonthink": lambda p, t: query_qwen_server(p, t),
    "q8-nonthink": lambda p, t: query_ollama(p, False, t),
    "q8-think": lambda p, t: query_ollama(p, True, t),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(REPO / "benchmark" / "cases_v0.1.jsonl"))
    ap.add_argument("--out", default=str(REPO / "benchmark" / "results_baseline_v0.1.json"))
    ap.add_argument("--profiles", default=",".join(PROFILES), help="npr. q8-nonthink,q8-think")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()

    cases = load_cases(a.cases)
    results: list[dict] = []
    for name in a.profiles.split(","):
        fn = PROFILES[name.strip()]
        for c in cases:
            try:
                text, lat = fn(c.prompt, a.timeout)
                tool, args = parse_tool_call(text)
                scores = score_prediction(c, tool, args, text)
                results.append({"profile": name, "case": c.id, "category": c.category,
                                "tool": tool, "args": args, "scores": scores,
                                "latency_s": round(lat, 1),
                                "excerpt": (text or "")[:300], "error": None})
            except Exception as e:  # mreža/timeout — zabilježi, ne ruši cijeli run
                results.append({"profile": name, "case": c.id, "category": c.category,
                                "tool": None, "args": None, "scores": {},
                                "latency_s": None, "excerpt": "", "error": f"{type(e).__name__}: {e}"})
            print(f"[{name}] {c.id}: {results[-1]['tool']} {results[-1]['scores']} "
                  f"({results[-1]['latency_s']}s)", flush=True)

    # agregat po profilu × kategoriji
    agg: dict[str, dict[str, list]] = {}
    for r in results:
        for k, v in r["scores"].items():
            agg.setdefault(f"{r['profile']}/{k}", []).append(v)
    summary = {k: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for k, v in sorted(agg.items())}

    Path(a.out).write_text(json.dumps({"results": results, "summary": summary},
                                      indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Rezultati: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
