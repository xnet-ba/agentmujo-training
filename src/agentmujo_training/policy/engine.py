"""Policy Engine — jedina tacka odluke prije izvrsavanja.

MODEL -> TOOL CALL -> POLICY ENGINE -> EXECUTOR -> LINUX

Klase: allow (read-only, ide odmah), confirmation_required (mutacije sa
ogranicenim blast radiusom — treba eksplicitna potvrda operatora),
deny (destruktivno/privilegovano/exfiltracija — nikad automatski).

Fine-tuning NIJE sigurnosni mehanizam: model moze predloziti bilo sta,
ovaj modul odlucuje.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Terminal obrasci koji su uvijek deny, bez obzira na registry politiku.
DENY_COMMAND_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\s+.*of=/dev/",
    r"\biptables\s+-[FA]\b",
    r":\(\)\s*\{\s*:\|\:&\s*\}",
    r"\bcurl\b.*\|\s*(?:sudo\s+)?bash\b",
    r"\bwget\b.*\|\s*(?:sudo\s+)?bash\b",
    r"\bchmod\s+-R\s+777\s+/\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bhalt\b",
    r"\bpoweroff\b",
]


@dataclass(frozen=True)
class PolicyDecision:
    verdict: str  # allow | confirmation_required | deny
    reason: str
    tool: str


class PolicyEngine:
    """Odluka na osnovu registry politike + deny obrazaca za terminal."""

    def __init__(self, registry):
        self._registry = registry

    def decide(self, tool: str, arguments: dict[str, Any] | None = None) -> PolicyDecision:
        arguments = arguments or {}
        tooldef = self._registry.get(tool)
        if tooldef is None:
            return PolicyDecision("deny", f"nepoznat alat: {tool}", tool)
        if tool == "terminal":
            cmd = str(arguments.get("command", ""))
            for pat in DENY_COMMAND_PATTERNS:
                if re.search(pat, cmd):
                    return PolicyDecision("deny", f"deny obrazac: {pat}", tool)
            return PolicyDecision("confirmation_required",
                                  "terminal uvijek trazi potvrdu (fallback alat)", tool)
        return PolicyDecision(tooldef.policy,
                              f"registry politika za {tool}: {tooldef.policy}", tool)
