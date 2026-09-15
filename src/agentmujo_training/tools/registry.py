"""Canonical Tool Registry — Single Source of Truth.

Učitava configs/tools.yaml i nudi validaciju tool poziva
(tool selection + arguments) za trening, dataset generation,
runtime, evaluaciju i benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ToolDef:
    name: str
    description: str
    policy: str  # allow | confirmation_required | deny
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def required(self) -> list[str]:
        return list(self.parameters.get("required", []))

    @property
    def properties(self) -> dict[str, Any]:
        return dict(self.parameters.get("properties", {}))


class ToolRegistry:
    def __init__(self, tools: dict[str, ToolDef]):
        self._tools = tools

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ToolRegistry":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        tools: dict[str, ToolDef] = {}
        for item in data.get("tools", []):
            tools[item["name"]] = ToolDef(
                name=item["name"],
                description=item["description"],
                policy=item["policy"],
                parameters=item.get("parameters", {}),
            )
        return cls(tools)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def validate_call(self, name: str, arguments: dict[str, Any]) -> list[str]:
        """Vrati listu grešaka (prazna = validno)."""
        errors: list[str] = []
        tool = self.get(name)
        if tool is None:
            return [f"unknown tool: {name}"]
        for req in tool.required:
            if req not in arguments:
                errors.append(f"missing required argument: {req}")
        for key in arguments:
            if key not in tool.properties:
                errors.append(f"unknown argument: {key}")
        # lagana provjera tipova za MVP (puni JSON Schema check dolazi u validatoru)
        for key, spec in tool.properties.items():
            if key in arguments and "type" in spec:
                expected = spec["type"]
                value = arguments[key]
                if expected == "string" and not isinstance(value, str):
                    errors.append(f"argument {key} mora biti string")
                elif expected == "integer" and not isinstance(value, int):
                    errors.append(f"argument {key} mora biti integer")
                elif expected == "object" and not isinstance(value, dict):
                    errors.append(f"argument {key} mora biti object")
        return errors
