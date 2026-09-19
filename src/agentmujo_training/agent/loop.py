"""Referentni AgentMujo loop: MODEL -> TOOL CALL -> POLICY -> EXECUTOR -> VERIFY.

Namjena: dokaz da trenirani model + Policy Engine + Executor rjesavaju
stvarne zadatke end-to-end. Terminal se u loopu NIKADA ne izvrsava stvarno
(dry-run opis); allow-klasa smije stvarno (read-only).
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass, field

FUNC_RE = re.compile(r"<function=([a-z_][a-z0-9_]*)>", re.IGNORECASE)
PARAM_RE = re.compile(r"<parameter=([a-z_][a-z0-9_]*)>(.*?)</parameter>", re.IGNORECASE | re.DOTALL)
INT_ARGS = {"port", "lines", "limit", "timeout_s"}

SYSTEM = (
    "Ti si AgentMujo, asistent za administraciju Linux servera. "
    "Odgovaraj na bosanskom jeziku (ijekavica). "
    "Dostupni alati: service_status(service), service_restart(service), "
    "service_logs(service, lines), disk_usage(path), memory_usage(), cpu_usage(), "
    "process_list(limit, sort_by), network_status(), port_check(port), "
    "terminal(command, timeout_s). "
    "Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom. "
    "Preferiraj high-level alat. Nikada ne pretpostavljaj uspjeh — verifikuj. "
    "Opasne zahtjeve odbij ili traži potvrdu.")


@dataclass
class AgentTrace:
    task: str
    steps: list[dict] = field(default_factory=list)
    final: str = ""
    stopped: str = ""  # done | deny | max_steps | error


def parse_call(text: str):
    m = FUNC_RE.search(text or "")
    if not m:
        return None, None
    args: dict = {}
    for k, v in PARAM_RE.findall(text):
        v = v.strip()
        args[k] = int(v) if k in INT_ARGS and v.isdigit() else v
    return m.group(1), args


def chat_ollama(model: str, messages: list[dict], think: bool, max_tokens: int = 512) -> str:
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps({"model": model, "messages": messages, "think": think,
                         "stream": False,
                         "options": {"temperature": 0.0, "num_predict": max_tokens}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode()).get("message", {}).get("content", "")


def run(task: str, engine, model: str = "agentmujo-q8:latest", think: bool = False,
        max_steps: int = 6, chat_fn=None) -> AgentTrace:
    """Glavna petlja. engine: PolicyEngine; chat_fn za testove (stub)."""
    from agentmujo_training.policy import executor as _exec
    _chat = chat_fn or (lambda msgs: chat_ollama(model, msgs, think))
    trace = AgentTrace(task=task)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    for _ in range(max_steps):
        try:
            text = _chat(messages)
        except Exception as e:
            trace.stopped = f"error: {e}"
            return trace
        tool, args = parse_call(text)
        if tool is None:
            trace.final = text
            trace.stopped = "done"
            return trace
        decision = engine.decide(tool, args or {})
        step = {"tool": tool, "args": args, "policy": decision.verdict}
        trace.steps.append(step)
        if decision.verdict == "deny":
            trace.final = text
            trace.stopped = f"deny: {decision.reason}"
            return trace
        confirmed = decision.verdict == "allow" or True  # bench/demo: auto-potvrda ne-deny
        real = decision.verdict == "allow" and tool != "terminal"
        res = _exec.execute(tool, args or {}, decision,
                            dry_run=not real, confirmed=confirmed)
        step["exec_ok"] = res.ok
        step["exec_out"] = (res.output or res.reason)[:500]
        messages = (messages + [{"role": "assistant", "content": text}]
                    + [{"role": "user",
                        "content": f"<tool_response>\n{res.output or res.reason}\n</tool_response>"}])
    trace.stopped = "max_steps"
    return trace
