"""Kanonski uzorak -> nativni Qwen3.5 chat format za SFT.

Naš kanonski JSONL drži tool_calls strukturno; model mora učiti NATIVNI
<tool_call><function=N><parameter=P>v</parameter></function></tool_call>
format + <tool_response> blokove. Ova funkcija je jedini most između
scheme i onoga što trener tokenizira.
"""
from __future__ import annotations

from typing import Any


def render_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
    parts = []
    for tc in tool_calls or []:
        lines = [f"<tool_call>\n<function={tc['name']}>"]
        for k, v in (tc.get("arguments") or {}).items():
            lines.append(f"<parameter={k}>\n{v}\n</parameter>")
        lines.append("</function>\n</tool_call>")
        parts.append("\n".join(lines))
    return "\n".join(parts)


def sample_to_text(sample: dict[str, Any]) -> str:
    """Assistant poruke dobijaju <tool_call> XML; tool poruke <tool_response>."""
    chunks = []
    for m in sample.get("messages", []):
        role, content = m.get("role", ""), m.get("content", "")
        if role == "assistant":
            if m.get("tool_calls"):
                tc = render_tool_calls(m["tool_calls"])
                content = f"{content}\n\n{tc}" if content.strip() else tc
            chunks.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        elif role == "tool":
            chunks.append(f"<|im_start|>user\n<tool_response>\n{content}\n</tool_response><|im_end|>")
        elif role in ("user", "system"):
            chunks.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    # Kompletne konverzacije: bez trailing generation prompta (labels pokrivaju sve).
    return "\n".join(chunks)


def sample_to_chatml(sample: dict[str, Any]) -> list[dict[str, str]]:
    """Isto, ali kao chatml messages (za tokenizer.apply_chat_template)."""
    out = []
    for m in sample.get("messages", []):
        role, content = m.get("role", ""), m.get("content", "")
        if role == "assistant":
            if m.get("tool_calls"):
                tc = render_tool_calls(m["tool_calls"])
                content = f"{content}\n\n{tc}" if content.strip() else tc
            out.append({"role": "assistant", "content": content})
        elif role == "tool":
            out.append({"role": "user",
                        "content": f"<tool_response>\n{content}\n</tool_response>"})
        elif role in ("user", "system"):
            out.append({"role": role, "content": content})
    return out
