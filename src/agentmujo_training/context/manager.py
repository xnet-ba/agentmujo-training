"""Context Manager koncept (v0.1 skeleton).

Nikada ne slati beskonačnu historiju modelu. Budžet:
  system context + current task + recent actions (N) + relevant tool results
  + compressed historical state. Veliki terminalni outputi se skraćuju
  (tail + filter), tool scheme se prosljeđuju selektivno.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextBudget:
    max_chars_history: int = 6000
    max_chars_tool_output: int = 2000
    recent_actions: int = 5


def truncate_tool_output(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    tail = text[-limit:]
    return f"... [skraćeno, prikazan zadnji {limit} znakova] ...\n{tail}"


@dataclass
class AgentContext:
    system: str = ""
    task: str = ""
    actions: list[str] = field(default_factory=list)
    budget: ContextBudget = field(default_factory=ContextBudget)

    def render(self, tools: list[dict] | None = None) -> list[dict]:
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        if self.task:
            messages.append({"role": "user", "content": self.task})
        for a in self.actions[-self.budget.recent_actions:]:
            messages.append({"role": "user", "content": f"<tool_response>\n{a}\n</tool_response>"})
        return messages
