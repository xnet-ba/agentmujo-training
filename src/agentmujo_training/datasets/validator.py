"""Dataset validator: RAW -> ACCEPT/REJECT sa GOLD/SILVER/BRONZE/REJECT tierovima.

Provjere:
  schema -> conversation -> tool (registry) -> safety -> duplicate -> quality score
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Obrasci koji terminal uzorak čine automatskim REJECT (deny klasa).
DENY_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\s+.*of=/dev/",
    r"\biptables\s+-F\b",
    r":\(\)\s*\{\s*:\|\:&\s*\}",  # fork bomb
    r"\bcurl\b.*\|\s*(?:sudo\s+)?bash\b",
    r"\bwget\b.*\|\s*(?:sudo\s+)?bash\b",
    r"PASSPHRASE|AWS_SECRET|HF_TOKEN",
]

HIGH_LEVEL_TOOLS = {
    "service_status", "service_restart", "service_logs", "disk_usage",
    "memory_usage", "cpu_usage", "process_list", "network_status", "port_check",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def sample_hash(sample: dict[str, Any]) -> str:
    blob = json.dumps(sample.get("messages", []), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


@dataclass
class ValidationResult:
    sample_id: str
    verdict: str  # ACCEPT | REJECT
    tier: str     # GOLD | SILVER | BRONZE | REJECT
    score: float
    errors: list[str] = field(default_factory=list)


def validate_sample(
    sample: dict[str, Any],
    tool_names: set[str],
    seen_hashes: set[str],
    validate_args=None,
) -> ValidationResult:
    errors: list[str] = []
    sid = str(sample.get("id", "<bez-id>"))

    # 1. schema (lagana, puna JSON Schema validacija je u CI/testovima)
    for f in ("id", "version", "language", "task", "messages", "metadata"):
        if f not in sample:
            errors.append(f"nedostaje polje: {f}")
    msgs = sample.get("messages", [])
    if len(msgs) < 2:
        errors.append("premali broj poruka (min 2)")

    # 2. conversation: mora počinjati user porukom i imati assistant odgovor
    roles = [m.get("role") for m in msgs]
    if roles and roles[0] == "system":
        roles = roles[1:]
    if roles and roles[0] != "user":
        errors.append("konverzacija mora početi user porukom")
    if "assistant" not in roles:
        errors.append("nedostaje assistant poruka")

    # 3. tool validation
    score_bonus = 0.0
    for m in msgs:
        for tc in m.get("tool_calls", []) or []:
            name = tc.get("name", "")
            if name not in tool_names:
                errors.append(f"nepoznat tool: {name}")
                continue
            if validate_args is not None:
                arg_errors = validate_args(name, tc.get("arguments", {}) or {})
                errors.extend(f"tool {name}: {e}" for e in arg_errors)

    # 4. safety: DENY obrasci se traže samo u onome što MODEL predlaže
    # (assistant tool_calls + assistant tekst), NE u user porukama.
    # Korisnik smije tražiti opasnu stvar; uzorak je ispravan ako je
    # asistent odbije ili traži potvrdu umjesto da je izvrši.
    model_surface = json.dumps(
        [m for m in msgs if m.get("role") == "assistant"], ensure_ascii=False
    )
    for pat in DENY_PATTERNS:
        if re.search(pat, model_surface):
            return ValidationResult(sid, "REJECT", "REJECT", 0.0, [f"safety deny obrazac: {pat}"])

    # preferiranje high-level alata: terminal uz postojeći high-level izbor skida bodove
    used = {tc.get("name") for m in msgs for tc in (m.get("tool_calls", []) or [])}
    if "terminal" in used and used & HIGH_LEVEL_TOOLS:
        score_bonus -= 0.2

    # 5. duplicate detection
    h = sample_hash(sample)
    if h in seen_hashes:
        return ValidationResult(sid, "REJECT", "REJECT", 0.0, ["duplikat uzorka"])
    seen_hashes.add(h)

    # 6. quality scoring (MVP heuristika)
    score = 1.0 + score_bonus
    if sample.get("language") not in ("bs", "bs-ijekavica"):
        score -= 0.3
    if sample.get("task") == "agentic-terminal" and len(msgs) >= 6:
        score += 0.1  # multi-step se nagrađuje
    meta = sample.get("metadata", {})
    if meta.get("verification_status") == "human-reviewed":
        score += 0.1

    if errors:
        return ValidationResult(sid, "REJECT", "REJECT", 0.0, errors)
    tier = "GOLD" if score >= 1.0 else ("SILVER" if score >= 0.7 else "BRONZE")
    return ValidationResult(sid, "ACCEPT", tier, round(score, 2))


def validate_file(path: str | Path, tool_names: set[str], validate_args=None) -> dict[str, Any]:
    seen: set[str] = set()
    results: list[ValidationResult] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        sample = json.loads(line)
        results.append(validate_sample(sample, tool_names, seen, validate_args))
    tiers: dict[str, int] = {}
    for r in results:
        tiers[r.tier] = tiers.get(r.tier, 0) + 1
    return {
        "file": str(path),
        "total": len(results),
        "accepted": sum(1 for r in results if r.verdict == "ACCEPT"),
        "rejected": sum(1 for r in results if r.verdict == "REJECT"),
        "tiers": tiers,
        "errors": [{"id": r.sample_id, "errors": r.errors} for r in results if r.verdict == "REJECT"],
    }
