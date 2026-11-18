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
OPEN_CALL_RE = re.compile(r"<tool_call>", re.IGNORECASE)
CLOSE_CALL_RE = re.compile(r"</tool_call>", re.IGNORECASE)
OPEN_FUNC_RE = re.compile(r"<function=", re.IGNORECASE)
JSON_TOOL_RE = re.compile(r"```json\s*(\{.*\})\s*```", re.IGNORECASE | re.DOTALL)
INT_ARGS = {"port", "lines", "limit", "timeout_s"}

# --- Chitchat/knowledge guard: ne-alatski prompti ne smiju proizvesti poziv.
# Klasifikacija je konzervativna: sve sto lici na operativni zadatak ide
# normalnim putem (model+policy+executor). Samo cisti pozdrav/zahvala/pozdrav
# i definicijska pitanja bez operativnih tokena idu precicom.
_SOCIAL_RE = re.compile(
    r"^([cć]ao|zdravo|dobar dan|dobro jutro|dobro vece|dobro veče|selam|pozdrav|"
    r"hvala( ti| puno| najljepsa| najljepša| lijepa)?|zahvaljujem( ti)?"
    r"(,?\s*to ?bi bilo sve)?|dovidenja|doviđenja|laku noc|laku noć"
    r"(,?\s*vidimo se sutra)?|vidimo se( sutra)?)\s*[!.,]*$", re.IGNORECASE)
# Redoslijed provjere u classify_task: 1) imperativ/destruktivno -> operational,
# 2) definicijsko pitanje BEZ state-rijeci -> knowledge, 3) operativna imenica
# ili marker -> operational, 4) social, 5) labave drustvene rijeci, inace operational.
_OPERATIONAL_VERB_RE = re.compile(
    r"(restartuj|restart|startuj|stop|provjeri|instaliraj|deinstaliraj|prikaz|"
    r"izlistaj|ugasi|upali|obrisi|ukloni|postavi|pokreni|kreiraj|procitaj|"
    r"daj|otvori|zatvori|promijeni|azuriraj|ocisti|rm\s|chmod|reboot|"
    r"drop|mkfs|dd\s+if=|systemctl|terminal|komand)",
    re.IGNORECASE)
_OPERATIONAL_NOUN_RE = re.compile(
    r"(nginx|apache|redis|mysql|postgres|docker|ssh|port\s+\d+|:\d+|"
    r"/var|/tmp|/home|\.log|\.conf|memorij|disk|proces|fajl|datotek|"
    r"paket|mrez|server|baz[aeu]|kontejner|log(ova|ove|u)?|"
    r"aktivan|aktivan|neaktivan|pada|pao|gresk|error|failed|stao|"
    r"status|stanje)",
    re.IGNORECASE)
_KNOWLEDGE_RE = re.compile(
    r"^\s*(cemu sluze|čemu služe|objasni(\s+mi)?|kako radi|"
    r"zasto sluzi|zašto služi|sta znaci|šta znači|što znači|"
    r"sta je(?! status| stanje)|šta je(?! status| stanje)|"
    r"što je(?! status| stanje)|sto je(?! status| stanje))\b",
    re.IGNORECASE)

_SOCIAL_REPLY = ("Pozdrav! Tu sam kad zatreba provjera servisa ili logova.")


def classify_task(task: str) -> str:
    """social | knowledge | operational. Konzervativno: sumnja ide na operational."""
    t = (task or "").strip()
    if _OPERATIONAL_VERB_RE.search(t):
        return "operational"
    if _KNOWLEDGE_RE.search(t):
        return "knowledge"
    if _OPERATIONAL_NOUN_RE.search(t):
        return "operational"
    if _SOCIAL_RE.match(t):
        return "social"
    # Pozdrav/zahvala u slobodnoj formi bez operativnih tokena.
    if re.search(r"(hvala|zahval|pozdrav|laku no[cć]|dovidenja|doviđenja|vidimo se|\bcao\b|\bzdravo\b)",
                 t, re.IGNORECASE):
        return "social"
    return "operational"


def _strip_tool_blocks(text: str) -> str:
    """Uklanja <tool_call> i fenced tool-blokove; ostaje proza."""
    t = re.sub(r"<tool_call>.*?</tool_call>", "", text or "",
               flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r"```(?:json|bash)[\s\S]*?```", "", t,
               flags=re.IGNORECASE)
    return t.strip()

SYSTEM = (
    "Ti si AgentMujo, asistent za administraciju Linux servera. "
    "Odgovaraj na bosanskom jeziku (ijekavica). "
    "Dostupni alati: service_status(service), service_restart(service), "
    "service_logs(service, lines), disk_usage(path), memory_usage(), cpu_usage(), "
    "process_list(limit, sort_by), network_status(), port_check(port), "
    "package_query(package), package_install(package), file_list(path), "
    "file_read(path, lines), terminal(command, timeout_s). "
    "Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom. "
    "Preferiraj high-level alat. Nikada ne pretpostavljaj uspjeh — verifikuj. "
    "Opasne zahtjeve odbij ili traži potvrdu.")

INCOMPLETE_NUDGE = ("Nepotpun poziv alata. Ponovi CIJELI poziv kanonskim "
                    "formatom: <tool_call><function=ime><parameter=arg>vrijednost"
                    "</parameter></function></tool_call>")


@dataclass
class AgentTrace:
    task: str
    steps: list[dict] = field(default_factory=list)
    final: str = ""
    stopped: str = ""  # done | deny | max_steps | error


def parse_call(text: str):
    """Parsira nativni <tool_call> format.

    Vraca (tool, args, status):
      ok         - potpun i sintaksno ispravan poziv (prvi u tekstu)
      none       - nema poziva, obican odgovor
      incomplete - otvoren <tool_call>/<function=> bez zatvaranja (odrezano)
      malformed  - parameter bez funkcije ili prazan poziv
    """
    text = text or ""
    has_open = bool(OPEN_CALL_RE.search(text))
    has_func_eq = bool(OPEN_FUNC_RE.search(text))
    m = FUNC_RE.search(text)
    if not m and not has_open and not has_func_eq:
        jtool, jargs = _parse_json_tool(text)
        if jtool is not None:
            return jtool, jargs, "ok"
        if PARAM_RE.search(text):
            return None, None, "malformed"
        return None, None, "none"
    if not CLOSE_CALL_RE.search(text):
        return None, None, "incomplete"
    if not m:
        return None, None, "malformed"
    args: dict = {}
    for k, v in PARAM_RE.findall(text):
        v = v.strip()
        args[k] = int(v) if k in INT_ARGS and v.isdigit() else v
    return m.group(1), args, "ok"


def _parse_json_tool(text: str):
    """Fallback za modele koji alat renderuju kao ```json {"tool":..}
    umjesto kanonskog <tool_call> (vidjeno kod 9B DPO: semantika tacna,
    omotac JSON). Vraca (tool, args) ili (None, None). Strogo: samo
    ogradjeni blok sa string kljucem "tool"; ostalo je "none".
    """
    m = JSON_TOOL_RE.search(text or "")
    if not m:
        return None, None
    try:
        obj = json.loads(m.group(1))
    except ValueError:
        return None, None
    if not isinstance(obj, dict):
        return None, None
    tool = obj.get("tool")
    if not isinstance(tool, str) or not re.fullmatch(r"[a-z_][a-z0-9_]*", tool, re.IGNORECASE):
        return None, None
    raw = obj.get("arguments", obj.get("parameters"))
    if raw is None:
        raw = {k: v for k, v in obj.items()
               if k not in ("tool", "status", "data", "result")}
    if not isinstance(raw, dict):
        return None, None
    args: dict = {}
    for k, v in raw.items():
        v = v.strip() if isinstance(v, str) else v
        args[k] = int(v) if k in INT_ARGS and isinstance(v, str) and v.isdigit() else v
    return tool, args


def chat_ollama(model: str, messages: list[dict], think: bool, max_tokens: int = 512) -> str:
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps({"model": model, "messages": messages, "think": think,
                         "stream": False,
                         "options": {"temperature": 0.0, "num_predict": max_tokens}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode()).get("message", {}).get("content", "")


def chat_llama(base_url: str, think: bool, max_tokens: int = 512):
    """chat_fn za llama-server (OpenAI-kompatibilan /v1/chat/completions).
    Vraca content tekst (sa <tool_call> XML-om) — loop parsira kao inace.
    Upotreba: run(task, eng, chat_fn=chat_llama("http://127.0.0.1:8899", False))"""
    def _chat(messages: list[dict]) -> str:
        body = {"messages": messages, "temperature": 0.0, "max_tokens": max_tokens,
                "stream": False, "enable_thinking": think}
        req = urllib.request.Request(
            base_url.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode())
        return d["choices"][0]["message"]["content"] or ""
    return _chat


def run(task: str, engine, model: str = "agentmujo-2b-agent-fast:latest", think: bool = False,
        max_steps: int = 6, chat_fn=None, max_wall_s: int = 600,
        log_path: str | None = None) -> AgentTrace:
    """Glavna petlja. engine: PolicyEngine; chat_fn za testove (stub).

    log_path: JSONL evidencija svakog izvrsenog alata (append).
    max_wall_s: vremensko ogranicenje cijelog zadatka.
    """
    import time as _time
    from agentmujo_training.policy import executor as _exec
    _chat = chat_fn or (lambda msgs: chat_ollama(model, msgs, think))
    trace = AgentTrace(task=task)
    t_start = _time.time()
    logf = open(log_path, "a", encoding="utf-8") if log_path else None
    try:
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
        # Chitchat precica: bez modelskog poziva, bez alata.
        if classify_task(task) == "social":
            trace.final = _SOCIAL_REPLY
            trace.stopped = "done"
            return trace
        if classify_task(task) == "knowledge":
            # Jedan modelski poziv, uzmi prozu, alat se nikad ne izvrsava.
            try:
                text = _chat(messages)
            except Exception as e:
                trace.stopped = f"error: {e}"
                return trace
            prose = _strip_tool_blocks(text)
            if prose:
                trace.final = prose
                trace.stopped = "done"
                return trace
            # Model dao samo poziv bez proze — padni nazad na normalni tok.
        for _ in range(max_steps):
            if _time.time() - t_start > max_wall_s:
                trace.stopped = "timeout"
                return trace
            try:
                text = _chat(messages)
            except Exception as e:
                trace.stopped = f"error: {e}"
                return trace
            tool, args, status = parse_call(text)
            if status == "none":
                trace.final = text
                trace.stopped = "done"
                return trace
            if status in ("incomplete", "malformed"):
                trace.steps.append({"tool": None, "args": None,
                                    "policy": status, "text": (text or "")[:800]})
                messages = (messages + [{"role": "assistant", "content": text or ""}]
                            + [{"role": "user", "content": INCOMPLETE_NUDGE}])
                continue
            verrs = engine.validate(tool, args or {})
            if verrs:
                trace.steps.append({"tool": tool, "args": args,
                                    "policy": "invalid", "text": (text or "")[:800],
                                    "validation": verrs})
                trace.final = text
                trace.stopped = f"deny: nevalidan poziv: {'; '.join(verrs)}"
                return trace
            decision = engine.decide(tool, args or {})
            step = {"tool": tool, "args": args, "policy": decision.verdict,
                    "text": (text or "")[:800]}
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
            step["dry_run"] = res.dry_run
            if logf:
                logf.write(json.dumps({"task": task, "tool": tool, "args": args,
                                       "policy": decision.verdict, "ok": res.ok,
                                       "dry_run": res.dry_run,
                                       "ts": _time.strftime("%Y-%m-%dT%H:%M:%S")},
                                      ensure_ascii=False) + "\n")
                logf.flush()
            messages = (messages + [{"role": "assistant", "content": text}]
                        + [{"role": "user",
                            "content": f"<tool_response>\n{res.output or res.reason}\n</tool_response>"}])
        trace.stopped = "max_steps"
        return trace
    finally:
        if logf:
            logf.close()
